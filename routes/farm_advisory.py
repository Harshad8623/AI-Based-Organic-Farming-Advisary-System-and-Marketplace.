"""From a farmer's own field observations to explained, saved next actions."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import re
import secrets
import unicodedata
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, redirect, render_template, request, session, url_for, current_app
from flask_login import current_user
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from advisory.catalog import CROPS, STAGES, SOILS, IRRIGATION, MISSING_DATA
from advisory.engine import analyze_context
from advisory.learning import retrieve_cases
from advisory.freshness import latest_report_keys, report_is_stale
from advisory_models import FarmField, FieldObservation, AdvisoryFollowup, AdvisoryTaskLink
from farm_tools_models import FarmTask
from models import db
from routes.farm_tools import farmer_required

farm_advisory_bp = Blueprint('farm_advisory', __name__, url_prefix='/my-farm')
MOISTURE = ('unknown', 'dry', 'balanced', 'wet')
SYMPTOMS = ('none', 'yellowing', 'spots', 'wilting', 'other')
AREA_FACTORS = {'m2': Decimal('1'), 'acre': Decimal('4046.8564224'), 'hectare': Decimal('10000')}


def _today():
    return datetime.now(ZoneInfo('Asia/Kolkata')).date()


def _token(kind):
    key = 'advisory_' + kind + '_token'
    if key not in session:
        session[key] = secrets.token_urlsafe(32)
    return session[key]


def _submission(model, kind):
    submitted = request.form.get('submission_id', '')
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}', submitted):
        raise ValueError('adf_error_expired')
    existing = model.query.filter_by(farmer_id=current_user.id, submission_id=submitted).first()
    if existing:
        return submitted, existing
    if not secrets.compare_digest(submitted, _token(kind)):
        raise ValueError('adf_error_expired')
    return submitted, None


def _digits(value):
    return ''.join(str(unicodedata.decimal(char)) if char.isdecimal() else char for char in value.strip())


def _decimal(value, upper, *, optional=True):
    value = _digits(value)
    if not value and optional:
        return None
    if not re.fullmatch(r'\d{1,10}(?:\.\d{1,4})?', value):
        raise ValueError('adf_error_number')
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise ValueError('adf_error_number') from None
    if not number.is_finite() or not 0 <= number <= upper:
        raise ValueError('adf_error_number')
    return number


def _date(value):
    if not value:
        return None
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('adf_error_date')
    try:
        result = date.fromisoformat(value)
    except ValueError:
        raise ValueError('adf_error_date') from None
    if result.year < 1900 or result > _today():
        raise ValueError('adf_error_date')
    return result


def _field_values():
    name = request.form.get('name', '').strip()
    location = request.form.get('location', '').strip()
    if not 2 <= len(name) <= 80 or len(location) > 120:
        raise ValueError('adf_error_field_name')
    values = {'name': name, 'location': location}
    for key, choices in [('crop', CROPS), ('stage', STAGES), ('soil', SOILS), ('irrigation', IRRIGATION)]:
        choice = request.form.get(key, '')
        if choice not in choices:
            raise ValueError('adf_error_choice')
        values[key] = choice
    area = _decimal(request.form.get('area_value', ''), Decimal('100000000'))
    unit = request.form.get('area_unit', 'acre')
    if unit not in AREA_FACTORS:
        raise ValueError('adf_error_number')
    area = area * AREA_FACTORS[unit] if area is not None else None
    if area is not None and not Decimal('0.01') <= area <= Decimal('100000000'):
        raise ValueError('adf_error_area')
    values['area_m2'] = area.quantize(Decimal('.01')) if area is not None else None
    values['planting_date'] = _date(request.form.get('planting_date', ''))
    return values


def _owned_field(field_id):
    return FarmField.query.filter_by(id=field_id, farmer_id=current_user.id).first_or_404()


def _owned_report(observation_id):
    return FieldObservation.query.filter_by(id=observation_id, farmer_id=current_user.id).first_or_404()


def _catalog():
    return dict(crops=CROPS, stages=STAGES, soils=SOILS, irrigation=IRRIGATION, today=_today())


def _field_form(field=None, error=None, status=200):
    values = request.form.to_dict() if request.method == 'POST' else (
        dict(name=field.name, location=field.location, crop=field.crop, stage=field.stage, soil=field.soil,
             irrigation=field.irrigation, planting_date=field.planting_date.isoformat() if field.planting_date else '',
             area_value=str(field.area_m2) if field.area_m2 is not None else '', area_unit='m2') if field else {})
    return render_template('advisory/field_form.html', field=field, values=values, error=error,
                           submission_id=_token('field'), **_catalog()), status


@farm_advisory_bp.get('')
@farm_advisory_bp.get('/')
@farmer_required
def index():
    archived = request.args.get('archived') == '1'
    fields = FarmField.query.filter_by(farmer_id=current_user.id, archived=archived).order_by(FarmField.name, FarmField.id).all()
    latest = {}
    if fields:
        # Fetch one report per field, rather than loading an unbounded history
        # of multilingual report JSON into a small hosting worker's memory.
        ranked = db.session.query(FieldObservation.id.label('id'), func.row_number().over(
            partition_by=FieldObservation.field_id,
            order_by=(FieldObservation.created_at.desc(), FieldObservation.id.desc())).label('position')).filter(
            FieldObservation.farmer_id == current_user.id,
            FieldObservation.field_id.in_([field.id for field in fields])).subquery()
        rows = FieldObservation.query.join(ranked, FieldObservation.id == ranked.c.id).filter(ranked.c.position == 1).all()
        latest = {row.field_id: row for row in rows}
    return render_template('advisory/index.html', fields=fields, archived=archived, latest=latest, **_catalog())


@farm_advisory_bp.get('/fields/new')
@farmer_required
def new_field():
    return _field_form()


@farm_advisory_bp.post('/fields')
@farmer_required
def create_field():
    try:
        token, previous = _submission(FarmField, 'field')
        if previous:
            return redirect(url_for('farm_advisory.field_detail', field_id=previous.id), code=303)
        values = _field_values()
        field = FarmField(farmer_id=current_user.id, submission_id=token, **values)
        db.session.add(field)
        db.session.commit()
        session.pop('advisory_field_token', None)
    except ValueError as error:
        return _field_form(error=str(error), status=400)
    except IntegrityError:
        db.session.rollback()
        field = FarmField.query.filter_by(farmer_id=current_user.id, submission_id=token).first()
        if not field:
            raise
    return redirect(url_for('farm_advisory.field_detail', field_id=field.id), code=303)


@farm_advisory_bp.route('/fields/<int:field_id>/edit', methods=['GET', 'POST'])
@farmer_required
def edit_field(field_id):
    field = _owned_field(field_id)
    if field.archived:
        abort(409)
    if request.method == 'GET':
        return _field_form(field)
    try:
        version = int(request.form.get('version', ''))
        values = _field_values()
    except (ValueError, TypeError) as error:
        return _field_form(field, str(error) if str(error).startswith('adf_') else 'adf_error_stale', 400)
    changed = FarmField.query.filter_by(id=field.id, farmer_id=current_user.id, version=version, archived=False).update(
        dict(**values, version=version+1, updated_at=datetime.now(timezone.utc)), synchronize_session=False)
    if not changed:
        db.session.rollback()
        return _field_form(field, 'adf_error_stale', 409)
    db.session.commit()
    return redirect(url_for('farm_advisory.field_detail', field_id=field.id), code=303)


@farm_advisory_bp.post('/fields/<int:field_id>/archive')
@farmer_required
def archive_field(field_id):
    field = _owned_field(field_id)
    state = request.form.get('archived')
    if state not in ('0', '1'):
        abort(400)
    field.archived = state == '1'
    field.version += 1
    db.session.commit()
    return redirect(url_for('farm_advisory.index', archived='1' if field.archived else None), code=303)


@farm_advisory_bp.get('/fields/<int:field_id>')
@farmer_required
def field_detail(field_id):
    field = _owned_field(field_id)
    try:
        page = max(1, int(request.args.get('page', '1')))
    except ValueError:
        page = 1
    query = FieldObservation.query.filter_by(field_id=field.id, farmer_id=current_user.id)
    pages = max(1, (query.count()+19)//20)
    page = min(page, pages)
    history = query.order_by(FieldObservation.created_at.desc(), FieldObservation.id.desc()).offset((page-1)*20).limit(20).all()
    return render_template('advisory/field_detail.html', field=field, history=history, page=page, pages=pages,
                           error=None, values={}, submission_id=_token('observation'), **_catalog())


def _observation_values():
    moisture = request.form.get('moisture', 'unknown')
    symptoms = request.form.get('leaf_symptoms', 'none')
    if moisture not in MOISTURE or symptoms not in SYMPTOMS:
        raise ValueError('adf_error_choice')
    values = {'moisture': moisture, 'leaf_symptoms': symptoms}
    for key in ('waterlogging', 'pest_present'):
        raw = request.form.get(key, '0')
        if raw not in ('0', '1'):
            raise ValueError('adf_error_choice')
        values[key] = raw == '1'
    for key in ('inspected_plants', 'affected_plants'):
        raw = _digits(request.form.get(key, ''))
        if raw and (not re.fullmatch(r'\d{1,5}', raw) or not 0 <= int(raw) <= 10000):
            raise ValueError('adf_error_counts')
        values[key] = int(raw) if raw else None
    inspected, affected = values['inspected_plants'], values['affected_plants']
    if (inspected is None) != (affected is None) or (inspected is not None and (inspected < 1 or affected > inspected)):
        raise ValueError('adf_error_counts')
    rain = _decimal(request.form.get('recent_rain_mm', ''), Decimal('1000'))
    values['recent_rain_mm'] = float(rain) if rain is not None else None
    notes = request.form.get('notes', '').strip()
    if len(notes) > 500:
        raise ValueError('adf_error_notes')
    values['notes'] = notes
    return values


@farm_advisory_bp.post('/fields/<int:field_id>/observe')
@farmer_required
def observe(field_id):
    field = _owned_field(field_id)
    if field.archived:
        abort(409)
    try:
        token, previous = _submission(FieldObservation, 'observation')
        if previous:
            if previous.field_id != field.id:
                raise ValueError('adf_error_expired')
            return redirect(url_for('farm_advisory.report', observation_id=previous.id), code=303)
        observation = _observation_values()
        context = field.context_snapshot()
        report_data = analyze_context(context, observation)
        row = FieldObservation(farmer_id=current_user.id, field_id=field.id, submission_id=token,
                               field_snapshot=context, observation_data=observation, report_data=report_data)
        db.session.add(row)
        db.session.commit()
        session.pop('advisory_observation_token', None)
        revision = request.form.get('draft_revision', '')
        session['advisory_saved_observation'] = {
            'observation_id': row.id, 'field_id': field.id,
            'draft_revision': revision if re.fullmatch(r'[A-Za-z0-9_-]{1,64}', revision) else ''}

    except ValueError as error:
        code = str(error) if str(error).startswith('adf_') else 'adf_error_observation'
        return render_template('advisory/field_detail.html', field=field, history=[], page=1, pages=1,
            error=code, values=request.form.to_dict(), submission_id=_token('observation'), **_catalog()), 400
    except IntegrityError:
        db.session.rollback()
        row = FieldObservation.query.filter_by(farmer_id=current_user.id, submission_id=token, field_id=field.id).first()
        if not row:
            raise
    return redirect(url_for('farm_advisory.report', observation_id=row.id), code=303)


def _report_stale(row):
    latest = latest_report_keys(current_user.id, [row.field_id]).get(row.field_id)
    return report_is_stale(row, _today(), latest)


def _render_report(row, notice=None, status=200):
    links = {link.action_code: link for link in AdvisoryTaskLink.query.filter_by(
        observation_id=row.id, farmer_id=current_user.id).all() if link.task is not None}
    history_rows = FieldObservation.query.options(joinedload(FieldObservation.followup)).filter_by(
        farmer_id=current_user.id).filter(or_(FieldObservation.created_at < row.created_at,
            and_(FieldObservation.created_at == row.created_at, FieldObservation.id < row.id))).order_by(
        FieldObservation.created_at.desc(), FieldObservation.id.desc()).limit(200).all()
    history = [{'id': item.id, 'field_context': item.field_snapshot,
                'observation': item.observation_data, 'report': item.report_data,
                'recorded_at': item.created_at.isoformat(),
                'verdict': item.followup.verdict if item.followup else None,
                'note': item.followup.note if item.followup else item.observation_data.get('notes', '')}
               for item in history_rows]
    try:
        learned = retrieve_cases(row.field_snapshot, row.observation_data, history, exclude_id=row.id)
    except (ImportError, ValueError, TypeError, RuntimeError) as error:
        current_app.logger.warning('Private case retrieval unavailable (%s)', type(error).__name__)
        learned = {'status': 'unavailable', 'cases': []}
    save_marker = session.get('advisory_saved_observation')
    clear_revision = ''
    if isinstance(save_marker, dict) and save_marker.get('observation_id') == row.id and save_marker.get('field_id') == row.field_id:
        clear_revision = save_marker.get('draft_revision', '')
        session.pop('advisory_saved_observation', None)
    return render_template('advisory/report.html', observation=row, field=row.field, learned=learned,
                           clear_draft_revision=clear_revision,
                           report=row.report_data, saved_actions=links, missing_catalog=MISSING_DATA,
                           stale=_report_stale(row), notice=notice, **_catalog()), status


@farm_advisory_bp.get('/reports/<int:observation_id>')
@farmer_required
def report(observation_id):
    return _render_report(_owned_report(observation_id), request.args.get('notice'))


@farm_advisory_bp.post('/reports/<int:observation_id>/actions/<code>')
@farmer_required
def save_action(observation_id, code):
    row = _owned_report(observation_id)
    if row.field.archived or _report_stale(row):
        return _render_report(row, 'stale_report', 409)
    priority = next((item for item in row.report_data.get('priorities', []) if item.get('code') == code), None)
    if not priority:
        abort(404)
    link = AdvisoryTaskLink.query.filter_by(observation_id=row.id, farmer_id=current_user.id, action_code=code).first()
    if link and link.task:
        return redirect(url_for('farm_advisory.report', observation_id=row.id, notice='task_saved'), code=303)
    language = request.form.get('language', 'en')
    if language not in ('en', 'hi', 'mr'):
        language = 'en'
    action = priority.get('localized', {}).get(language, {}).get('action') or priority.get('action', '')
    if not isinstance(action, str) or not action.strip():
        abort(400)
    try:
        offset = int(priority.get('due_in_days', 0))
    except (ValueError, TypeError):
        abort(400)
    if not 0 <= offset <= 7:
        abort(400)
    task_token = sha256(f'advisory:{current_user.id}:{row.id}:{code}'.encode()).hexdigest()
    task = FarmTask(farmer_id=current_user.id, title=action[:160], crop=row.field_snapshot.get('name', '')[:80],
                    due_date=_today()+timedelta(days=offset), submission_id=task_token)
    try:
        db.session.add(task)
        db.session.flush()
        if link:
            link.task_id = task.id
        else:
            db.session.add(AdvisoryTaskLink(farmer_id=current_user.id, observation_id=row.id, action_code=code, task_id=task.id))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = AdvisoryTaskLink.query.filter_by(observation_id=row.id, farmer_id=current_user.id, action_code=code).first()
        if not existing or not existing.task:
            raise
    return redirect(url_for('farm_advisory.report', observation_id=row.id, notice='task_saved'), code=303)


@farm_advisory_bp.post('/reports/<int:observation_id>/followup')
@farmer_required
def followup(observation_id):
    row = _owned_report(observation_id)
    verdict = request.form.get('verdict', '')
    note = request.form.get('note', '').strip()
    if verdict not in ('improved', 'unchanged', 'worse') or len(note) > 500:
        abort(400)
    existing = AdvisoryFollowup.query.filter_by(observation_id=row.id, farmer_id=current_user.id).first()
    try:
        if existing:
            existing.verdict, existing.note = verdict, note
            existing.updated_at = datetime.now(timezone.utc)
        else:
            db.session.add(AdvisoryFollowup(farmer_id=current_user.id, observation_id=row.id, verdict=verdict, note=note))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # A repeated result submission must not create another learning example.
        if not AdvisoryFollowup.query.filter_by(observation_id=row.id, farmer_id=current_user.id).first():
            raise
    return redirect(url_for('farm_advisory.report', observation_id=row.id, notice='followup_saved'), code=303)

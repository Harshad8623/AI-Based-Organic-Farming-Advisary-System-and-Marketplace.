"""Farmer-owned task planning and a manual INR income/expense journal."""

import calendar
import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from io import StringIO
import re
import secrets
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, redirect, render_template, request, Response, session, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from models import db
from farm_tools_models import FarmLedgerEntry, FarmTask


farm_tools_bp = Blueprint('farm_tools', __name__, url_prefix='/farm-tools')
CATEGORIES = ('seeds', 'soil_inputs', 'labour', 'water', 'equipment', 'transport', 'produce_sale', 'other')
AMOUNT_PATTERN = re.compile(r'^(?:0|[1-9]\d{0,7})(?:\.\d{1,2})?$')


def _today():
    return datetime.now(ZoneInfo('Asia/Kolkata')).date()


def farmer_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_farmer():
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def _token(kind):
    key = 'farm_tools_' + kind + '_token'
    if key not in session:
        session[key] = secrets.token_urlsafe(32)
    return session[key]


def _date(value):
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('farm_error_date')
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError('farm_error_date') from None
    if not 1900 <= parsed.year <= 2100:
        raise ValueError('farm_error_date')
    return parsed


def _month_range(value):
    if not re.fullmatch(r'\d{4}-\d{2}', value):
        raise ValueError('farm_error_month')
    try:
        first = _date(value + '-01')
        last = date(first.year, first.month, calendar.monthrange(first.year, first.month)[1])
    except ValueError:
        raise ValueError('farm_error_month') from None
    return first, last


def _ledger_query(month):
    first, last = _month_range(month)
    return FarmLedgerEntry.query.filter(
        FarmLedgerEntry.farmer_id == current_user.id,
        FarmLedgerEntry.entry_date >= first,
        FarmLedgerEntry.entry_date <= last,
    )


def _page_number(name):
    """Keep malformed query parameters from raising errors or expensive offsets."""
    try:
        number = int(request.args.get(name, '1'))
    except (ValueError, TypeError):
        return 1
    return max(1, number)


def _render(error=None, form_kind=None, values=None, status=200):
    today = _today()
    month = request.args.get('month', today.strftime('%Y-%m'))
    try:
        entries_query = _ledger_query(month)
    except ValueError:
        month = today.strftime('%Y-%m')
        entries_query = _ledger_query(month)
        error, status = 'farm_error_month', 400
    tasks_query = FarmTask.query.filter_by(farmer_id=current_user.id)
    open_count = tasks_query.filter_by(is_done=False).count()
    overdue_count = tasks_query.filter(FarmTask.is_done.is_(False), FarmTask.due_date < today).count()
    # SQLite stores NUMERIC values using binary floats. Sum individually
    # decoded two-decimal amounts in Python so journal totals stay exact.
    totals = {'income': Decimal('0.00'), 'expense': Decimal('0.00')}
    for kind, amount in entries_query.with_entities(FarmLedgerEntry.kind, FarmLedgerEntry.amount).yield_per(100):
        totals[kind] += amount
    income = totals.get('income', Decimal('0.00'))
    expense = totals.get('expense', Decimal('0.00'))
    tasks = tasks_query.order_by(FarmTask.is_done.asc(), FarmTask.due_date.asc(), FarmTask.id.asc())
    entries = entries_query.order_by(FarmLedgerEntry.entry_date.desc(), FarmLedgerEntry.id.desc())
    task_count = tasks_query.count()
    entry_count = entries_query.count()
    task_pages = max(1, (task_count + 99) // 100)
    ledger_pages = max(1, (entry_count + 99) // 100)
    task_page = min(_page_number('tasks_page'), task_pages)
    ledger_page = min(_page_number('ledger_page'), ledger_pages)

    def page_url(*, task=task_page, ledger=ledger_page, anchor):
        return url_for('farm_tools.index', month=month, tasks_page=task,
                       ledger_page=ledger, _anchor=anchor)

    return render_template(
        'farm_tools/index.html', today=today, month=month,
        tasks=tasks.offset((task_page - 1) * 100).limit(100).all(), task_count=task_count,
        entries=entries.offset((ledger_page - 1) * 100).limit(100).all(), entry_count=entry_count,
        task_page=task_page, task_pages=task_pages, ledger_page=ledger_page, ledger_pages=ledger_pages,
        task_previous=page_url(task=task_page - 1, anchor='farm-tasks') if task_page > 1 else None,
        task_next=page_url(task=task_page + 1, anchor='farm-tasks') if task_page < task_pages else None,
        ledger_previous=page_url(ledger=ledger_page - 1, anchor='farm-ledger') if ledger_page > 1 else None,
        ledger_next=page_url(ledger=ledger_page + 1, anchor='farm-ledger') if ledger_page < ledger_pages else None,
        open_count=open_count, overdue_count=overdue_count,
        income=income, expense=expense, balance=income - expense,
        task_token=_token('task'), ledger_token=_token('ledger'), categories=CATEGORIES,
        error=error, form_kind=form_kind, values=values or {},
    ), status


def _redirect(month=None):
    if month:
        try:
            _month_range(month)
        except ValueError:
            month = None
    return redirect(url_for('farm_tools.index', **({'month': month} if month else {})), code=303)


def _submission(model, kind):
    """Recognize a retried create request without creating duplicate records."""
    submitted = request.form.get('submission_id', '')
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}', submitted):
        raise ValueError('farm_error_expired_form')
    existing = model.query.filter_by(farmer_id=current_user.id, submission_id=submitted).first()
    if existing:
        return submitted, True
    if not secrets.compare_digest(submitted, _token(kind)):
        raise ValueError('farm_error_expired_form')
    return submitted, False


@farm_tools_bp.get('')
@farm_tools_bp.get('/')
@farmer_required
def index():
    return _render()


@farm_tools_bp.post('/tasks')
@farmer_required
def add_task():
    values = request.form.to_dict()
    try:
        submission, duplicate = _submission(FarmTask, 'task')
        if duplicate:
            return _redirect()
        title = request.form.get('title', '').strip()
        crop = request.form.get('crop', '').strip()
        if not 2 <= len(title) <= 160 or len(crop) > 80:
            raise ValueError('farm_error_task')
        due_date = _date(request.form.get('due_date', ''))
        task = FarmTask(farmer_id=current_user.id, title=title, crop=crop,
                        due_date=due_date, submission_id=submission)
        db.session.add(task)
        db.session.commit()
        session.pop('farm_tools_task_token', None)
    except ValueError as error:
        return _render(str(error), 'task', values, 400)
    except IntegrityError:
        db.session.rollback()
        if not FarmTask.query.filter_by(farmer_id=current_user.id, submission_id=submission).first():
            raise
    return _redirect()


@farm_tools_bp.post('/tasks/<int:task_id>/status')
@farmer_required
def task_status(task_id):
    task = FarmTask.query.filter_by(id=task_id, farmer_id=current_user.id).first_or_404()
    # Explicit desired state makes network retries idempotent.
    state = request.form.get('is_done')
    if state not in ('0', '1'):
        abort(400)
    task.is_done = state == '1'
    db.session.commit()
    return _redirect(request.form.get('month'))


@farm_tools_bp.post('/tasks/<int:task_id>/delete')
@farmer_required
def delete_task(task_id):
    task = FarmTask.query.filter_by(id=task_id, farmer_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return _redirect(request.form.get('month'))


@farm_tools_bp.post('/ledger')
@farmer_required
def add_entry():
    values = request.form.to_dict()
    try:
        submission, duplicate = _submission(FarmLedgerEntry, 'ledger')
        if duplicate:
            existing = FarmLedgerEntry.query.filter_by(farmer_id=current_user.id, submission_id=submission).first()
            return _redirect(existing.entry_date.strftime('%Y-%m'))
        kind = request.form.get('kind', '')
        category = request.form.get('category', '')
        note = request.form.get('note', '').strip()
        if kind not in ('income', 'expense') or category not in CATEGORIES or len(note) > 240:
            raise ValueError('farm_error_entry')
        amount_text = request.form.get('amount', '').strip()
        if not AMOUNT_PATTERN.fullmatch(amount_text):
            raise ValueError('farm_error_amount')
        amount = Decimal(amount_text)
        if not amount.is_finite() or amount <= 0 or amount > Decimal('99999999.99'):
            raise ValueError('farm_error_amount')
        entry_date = _date(request.form.get('entry_date', ''))
        if entry_date > _today():
            raise ValueError('farm_error_future_entry')
        entry = FarmLedgerEntry(farmer_id=current_user.id, kind=kind, category=category,
                                 note=note, amount=amount.quantize(Decimal('0.01')),
                                 entry_date=entry_date, submission_id=submission)
        db.session.add(entry)
        db.session.commit()
        session.pop('farm_tools_ledger_token', None)
    except (ValueError, InvalidOperation) as error:
        key = str(error) if isinstance(error, ValueError) else 'farm_error_amount'
        return _render(key, 'ledger', values, 400)
    except IntegrityError:
        db.session.rollback()
        existing = FarmLedgerEntry.query.filter_by(farmer_id=current_user.id, submission_id=submission).first()
        if not existing:
            raise
        entry_date = existing.entry_date
    return _redirect(entry_date.strftime('%Y-%m'))


@farm_tools_bp.post('/ledger/<int:entry_id>/delete')
@farmer_required
def delete_entry(entry_id):
    entry = FarmLedgerEntry.query.filter_by(id=entry_id, farmer_id=current_user.id).first_or_404()
    month = entry.entry_date.strftime('%Y-%m')
    db.session.delete(entry)
    db.session.commit()
    return _redirect(month)


def _csv_text(value):
    """Prevent spreadsheet formula execution, including whitespace-prefixed formulas."""
    text = str(value)
    if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r', '\n')):
        return "'" + text
    return text


@farm_tools_bp.get('/ledger.csv')
@farmer_required
def export_ledger():
    month = request.args.get('month', _today().strftime('%Y-%m'))
    try:
        query = _ledger_query(month)
    except ValueError:
        abort(400)
    output = StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(('Date (IST)', 'Type', 'Category', 'Amount (INR)', 'Note'))
    for entry in query.order_by(FarmLedgerEntry.entry_date, FarmLedgerEntry.id).yield_per(100):
        writer.writerow((entry.entry_date.isoformat(), entry.kind, entry.category,
                         format(entry.amount, '.2f'), _csv_text(entry.note)))
    return Response('\ufeff' + output.getvalue(), mimetype='text/csv; charset=utf-8', headers={
        'Content-Disposition': f'attachment; filename="farm-ledger-{month}.csv"',
        'Cache-Control': 'no-store',
    })

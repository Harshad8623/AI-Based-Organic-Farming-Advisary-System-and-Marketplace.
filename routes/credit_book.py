"""A private receive/pay notebook with exact, repeat-safe partial settlements."""
import csv
from datetime import date, datetime, timezone
from decimal import Decimal
from io import StringIO
import re
import secrets
import unicodedata
from zoneinfo import ZoneInfo

from flask import Blueprint, Response, abort, redirect, render_template, request, session, url_for
from flask_login import current_user
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError

from credit_models import CreditAccount, CreditPayment
from models import db
from routes.farm_tools import farmer_required

credit_book_bp = Blueprint('credit_book', __name__, url_prefix='/credit-book')


def _today():
    return datetime.now(ZoneInfo('Asia/Kolkata')).date()


def _digits(value):
    return ''.join(str(unicodedata.decimal(char)) if char.isdecimal() else char for char in value.strip())


def _amount(value):
    value = _digits(value)
    if not re.fullmatch(r'\d{1,8}(?:\.\d{1,2})?', value):
        raise ValueError('cb_error_amount')
    amount = Decimal(value)
    if not Decimal('0') < amount <= Decimal('99999999.99'):
        raise ValueError('cb_error_amount')
    return int(amount * 100)


def _date(value, *, optional=False):
    value = _digits(value)
    if not value and optional:
        return None
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('cb_error_date')
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError('cb_error_date') from None
    if not 1900 <= parsed.year <= 2100:
        raise ValueError('cb_error_date')
    return parsed


def _token(kind):
    key = 'credit_' + kind + '_token'
    if key not in session:
        session[key] = secrets.token_urlsafe(32)
    return session[key]


def _submission(model, kind):
    submitted = request.form.get('submission_id', '')
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}', submitted):
        raise ValueError('cb_error_expired')
    existing = model.query.filter_by(farmer_id=current_user.id, submission_id=submitted).first()
    if existing:
        return submitted, existing
    if not secrets.compare_digest(submitted, _token(kind)):
        raise ValueError('cb_error_expired')
    return submitted, None


def due_balances(farmer_id, today):
    """Return only amounts with a stated due date on/before today, in one query."""
    result = {'receive': Decimal('0.00'), 'pay': Decimal('0.00')}
    amounts = db.session.query(CreditAccount.direction, func.sum(
        CreditAccount.total_paise - CreditAccount.settled_paise)).filter(
        CreditAccount.farmer_id == farmer_id, CreditAccount.due_date <= today,
        CreditAccount.voided.is_(False),
        CreditAccount.settled_paise < CreditAccount.total_paise,
    ).group_by(CreditAccount.direction).all()
    for direction, paise in amounts:
        result[direction] = Decimal(paise) / 100
    return result


def _owned(account_id):
    return CreditAccount.query.filter_by(id=account_id, farmer_id=current_user.id).first_or_404()


def _page():
    try:
        return max(1, min(100000, int(request.args.get('page', '1'))))
    except ValueError:
        return 1


def _render_index(error=None, values=None, status=200):
    today = _today()
    view = request.args.get('view', 'open')
    if view not in ('open', 'due', 'settled', 'voided'):
        view = 'open'
    query = CreditAccount.query.filter_by(farmer_id=current_user.id)
    if view == 'voided':
        query = query.filter(CreditAccount.voided.is_(True))
    elif view == 'settled':
        query = query.filter(CreditAccount.voided.is_(False))
        query = query.filter(CreditAccount.settled_paise == CreditAccount.total_paise)
    else:
        query = query.filter(CreditAccount.voided.is_(False))
        query = query.filter(CreditAccount.settled_paise < CreditAccount.total_paise)
        if view == 'due':
            query = query.filter(CreditAccount.due_date <= today)
    count = query.count()
    pages = max(1, (count + 49) // 50)
    page = min(_page(), pages)
    accounts = query.order_by(CreditAccount.due_date.is_(None), CreditAccount.due_date,
        CreditAccount.id.desc()).offset((page - 1) * 50).limit(50).all()
    totals = {'receive': Decimal('0.00'), 'pay': Decimal('0.00')}
    for direction, paise in db.session.query(CreditAccount.direction, func.sum(
        CreditAccount.total_paise - CreditAccount.settled_paise)).filter(
            CreditAccount.farmer_id == current_user.id, CreditAccount.voided.is_(False)).group_by(CreditAccount.direction).all():
        totals[direction] = Decimal(paise) / 100
    return render_template('credit_book/index.html', accounts=accounts, totals=totals,
        due=due_balances(current_user.id, today), today=today, view=view, page=page, pages=pages,
        count=count, values=values or {}, error=error, submission_id=_token('account')), status


def _render_detail(account, error=None, values=None, status=200):
    query = CreditPayment.query.filter_by(account_id=account.id, farmer_id=current_user.id)
    pages = max(1, (query.count() + 99) // 100)
    page = min(_page(), pages)
    voided_at = account.voided_at
    if voided_at and voided_at.tzinfo is None:
        voided_at = voided_at.replace(tzinfo=timezone.utc)
    return render_template('credit_book/detail.html', account=account, today=_today(),
        voided_date=voided_at.astimezone(ZoneInfo('Asia/Kolkata')).date() if voided_at else None,
        payments=query.order_by(CreditPayment.id.desc()).offset((page - 1) * 100).limit(100).all(),
        page=page, pages=pages, error=error, values=values or {},
        submission_id=_token('payment')), status


@credit_book_bp.get('')
@credit_book_bp.get('/')
@farmer_required
def index():
    return _render_index()


@credit_book_bp.post('/accounts')
@farmer_required
def add_account():
    values = request.form.to_dict()
    try:
        submission, existing = _submission(CreditAccount, 'account')
        if existing:
            return redirect(url_for('credit_book.detail', account_id=existing.id), code=303)
        name = request.form.get('contact_name', '').strip()
        note = request.form.get('note', '').strip()
        direction = request.form.get('direction', '')
        if not 2 <= len(name) <= 100 or len(note) > 300 or direction not in ('receive', 'pay'):
            raise ValueError('cb_error_details')
        amount = _amount(request.form.get('amount', ''))
        entry_date = _date(request.form.get('entry_date', _today().isoformat()))
        due_date = _date(request.form.get('due_date', ''), optional=True)
        if entry_date > _today() or (due_date and due_date < entry_date):
            raise ValueError('cb_error_account_date')
        account = CreditAccount(farmer_id=current_user.id, contact_name=name, direction=direction,
            total_paise=amount, settled_paise=0, note=note, entry_date=entry_date,
            due_date=due_date, submission_id=submission)
        db.session.add(account)
        db.session.commit()
        account_id = account.id
        session.pop('credit_account_token', None)
    except ValueError as error:
        return _render_index(str(error), values, 400)
    except IntegrityError:
        db.session.rollback()
        existing = CreditAccount.query.filter_by(farmer_id=current_user.id, submission_id=submission).first()
        if not existing:
            raise
        account_id = existing.id
    return redirect(url_for('credit_book.detail', account_id=account_id), code=303)


@credit_book_bp.get('/accounts/<int:account_id>')
@farmer_required
def detail(account_id):
    return _render_detail(_owned(account_id))


@credit_book_bp.post('/accounts/<int:account_id>/payments')
@farmer_required
def add_payment(account_id):
    account = _owned(account_id)
    values = request.form.to_dict()
    try:
        submission, existing = _submission(CreditPayment, 'payment')
        if existing:
            if existing.account_id != account.id:
                session.pop('credit_payment_token', None)
                raise ValueError('cb_error_expired')
            return redirect(url_for('credit_book.detail', account_id=account.id), code=303)
        amount = _amount(request.form.get('amount', ''))
        entry_date = _date(request.form.get('entry_date', _today().isoformat()))
        note = request.form.get('note', '').strip()
        if entry_date > _today() or entry_date < account.entry_date:
            raise ValueError('cb_error_payment_date')
        if len(note) > 240:
            raise ValueError('cb_error_note')
        # A single conditional write reserves the balance. Two concurrent posts
        # cannot both spend the same remaining paise, even on SQLite.
        changed = db.session.execute(update(CreditAccount).where(
            CreditAccount.id == account.id, CreditAccount.farmer_id == current_user.id,
            CreditAccount.voided.is_(False),
            CreditAccount.settled_paise <= CreditAccount.total_paise - amount,
        ).values(settled_paise=CreditAccount.settled_paise + amount),
            execution_options={'synchronize_session': False}).rowcount
        if changed != 1:
            db.session.rollback()
            retried = CreditPayment.query.filter_by(farmer_id=current_user.id, submission_id=submission).first()
            if retried and retried.account_id == account_id:
                return redirect(url_for('credit_book.detail', account_id=account_id), code=303)
            account = _owned(account_id)
            raise ValueError('cb_error_voided' if account.voided else 'cb_error_overpayment')
        db.session.refresh(account)
        db.session.add(CreditPayment(account_id=account.id, farmer_id=current_user.id,
            amount_paise=amount, balance_after_paise=account.total_paise-account.settled_paise,
            entry_date=entry_date, note=note, submission_id=submission))
        db.session.commit()
        session.pop('credit_payment_token', None)
    except ValueError as error:
        return _render_detail(account, str(error), values, 400)
    except IntegrityError:
        db.session.rollback()
        existing = CreditPayment.query.filter_by(farmer_id=current_user.id, submission_id=submission).first()
        if not existing:
            raise
        if existing.account_id != account_id:
            session.pop('credit_payment_token', None)
            return _render_detail(_owned(account_id), 'cb_error_expired', values, 400)
    return redirect(url_for('credit_book.detail', account_id=account.id), code=303)


@credit_book_bp.post('/accounts/<int:account_id>/void')
@farmer_required
def void_account(account_id):
    account = _owned(account_id)
    if account.voided:
        return redirect(url_for('credit_book.detail', account_id=account_id), code=303)
    reason = request.form.get('void_reason', '').strip()
    if not 2 <= len(reason) <= 240:
        return _render_detail(account, 'cb_error_void_reason', request.form.to_dict(), 400)
    # Both this correction and a payment update the same row conditionally.
    # Whichever commits first makes the other operation ineligible.
    changed = db.session.execute(update(CreditAccount).where(
        CreditAccount.id == account.id, CreditAccount.farmer_id == current_user.id,
        CreditAccount.voided.is_(False), CreditAccount.settled_paise == 0,
    ).values(voided=True, void_reason=reason, voided_at=datetime.now(timezone.utc)),
        execution_options={'synchronize_session': False}).rowcount
    if changed != 1:
        db.session.rollback()
        account = _owned(account_id)
        if account.voided:
            return redirect(url_for('credit_book.detail', account_id=account_id), code=303)
        return _render_detail(account, 'cb_error_void_paid', request.form.to_dict(), 400)
    db.session.commit()
    return redirect(url_for('credit_book.detail', account_id=account_id), code=303)


def _cell(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else text


@credit_book_bp.get('/accounts/<int:account_id>/statement.csv')
@farmer_required
def statement(account_id):
    account = _owned(account_id)
    output = StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['Record', 'Date', 'Name', 'Direction', 'Amount INR', 'Remaining INR', 'Note'])
    writer.writerow(['Original amount', account.entry_date.isoformat(), _cell(account.contact_name),
        account.direction, format(account.total, '.2f'), format(account.total, '.2f'), _cell(account.note)])
    for payment in CreditPayment.query.filter_by(account_id=account.id, farmer_id=current_user.id).order_by(
            CreditPayment.id).yield_per(100):
        writer.writerow(['Settlement', payment.entry_date.isoformat(), _cell(account.contact_name),
            account.direction, format(payment.amount, '.2f'), format(payment.remaining, '.2f'), _cell(payment.note)])
    if account.voided:
        recorded = account.voided_at
        if recorded.tzinfo is None:
            recorded = recorded.replace(tzinfo=timezone.utc)
        writer.writerow(['Mistaken entry cancelled', recorded.astimezone(ZoneInfo('Asia/Kolkata')).date().isoformat(),
            _cell(account.contact_name), account.direction, '0.00', '0.00', _cell(account.void_reason)])
    return Response('\ufeff' + output.getvalue(), mimetype='text/csv', headers={
        'Content-Disposition': f'attachment; filename=credit-account-{account.id}.csv'})

"""Real private credit writes, exact paise and concurrent partial settlements."""
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from io import StringIO
from threading import Barrier

import pytest
from sqlalchemy.exc import IntegrityError

from credit_models import CreditAccount, CreditPayment
from farm_tools_models import FarmLedgerEntry
from models import User, db
from routes.credit_book import due_balances


@pytest.fixture
def people(app, monkeypatch):
    monkeypatch.setattr('routes.credit_book._today', lambda: date(2026,10,30))
    with app.app_context():
        records = [User(name='Farmer One', email='credit-one@example.com', password='unused', role='farmer'),
                   User(name='Farmer Two', email='credit-two@example.com', password='unused', role='farmer'),
                   User(name='Buyer', email='credit-buyer@example.com', password='unused', role='buyer')]
        db.session.add_all(records); db.session.commit()
        return [person.id for person in records]


def sign_in(client, person):
    with client.session_transaction() as session:
        session['_user_id'] = str(person)
        session['_fresh'] = True


def account_data(client, **changes):
    assert client.get('/credit-book').status_code == 200
    with client.session_transaction() as session:
        token = session['credit_account_token']
    return dict(submission_id=token, contact_name='Produce buyer', direction='receive',
                amount='100.50', entry_date='2026-10-20', due_date='2026-10-30', note='Tomato sale') | changes


def create_account(client, **changes):
    result = client.post('/credit-book/accounts', data=account_data(client, **changes))
    assert result.status_code == 303
    return int(result.location.rsplit('/',1)[-1])


def payment_data(client, account_id, **changes):
    assert client.get(f'/credit-book/accounts/{account_id}').status_code == 200
    with client.session_transaction() as session:
        token = session['credit_payment_token']
    return dict(submission_id=token, amount='40.25', entry_date='2026-10-30', note='Cash') | changes


def test_credit_book_requires_farmer_and_owner_on_every_route(app, client, people):
    assert client.get('/credit-book').status_code == 302
    sign_in(client, people[0]); account_id=create_account(client)
    sign_in(client, people[1])
    for method,path in [('get',f'/credit-book/accounts/{account_id}'),
                        ('post',f'/credit-book/accounts/{account_id}/payments'),
                        ('post',f'/credit-book/accounts/{account_id}/void'),
                        ('get',f'/credit-book/accounts/{account_id}/statement.csv')]:
        assert getattr(client,method)(path).status_code == 404
    assert b'Produce buyer' not in client.get('/credit-book').data
    sign_in(client, people[2])
    for method,path in [('get','/credit-book'),('post','/credit-book/accounts'),
                        ('get',f'/credit-book/accounts/{account_id}'),
                        ('post',f'/credit-book/accounts/{account_id}/payments'),
                        ('post',f'/credit-book/accounts/{account_id}/void'),
                        ('get',f'/credit-book/accounts/{account_id}/statement.csv')]:
        assert getattr(client,method)(path).status_code == 403


def test_credit_creation_partial_payments_retries_and_separate_diary(app, client, people):
    sign_in(client, people[0])
    data = account_data(client, contact_name='शेतमाल व्यापारी', amount='१००.५०')
    first = client.post('/credit-book/accounts', data=data)
    assert first.status_code == 303
    assert client.post('/credit-book/accounts', data=data).location == first.location
    account_id = int(first.location.rsplit('/',1)[-1])
    with app.app_context():
        assert CreditAccount.query.count() == 1
        assert db.session.get(CreditAccount,account_id).remaining == Decimal('100.50')
    payment = payment_data(client,account_id,amount='४०.२५')
    for _ in range(2):
        assert client.post(f'/credit-book/accounts/{account_id}/payments',data=payment).status_code == 303
    with app.app_context():
        row=db.session.get(CreditAccount,account_id)
        assert row.settled == Decimal('40.25') and row.remaining == Decimal('60.25')
        assert CreditPayment.query.count() == 1
        assert CreditPayment.query.one().remaining == Decimal('60.25')
        assert FarmLedgerEntry.query.count() == 0
    final=payment_data(client,account_id,amount='60.25')
    assert client.post(f'/credit-book/accounts/{account_id}/payments',data=final).status_code == 303
    assert b'credit-payment-form' not in client.get(f'/credit-book/accounts/{account_id}').data
    assert 'शेतमाल व्यापारी'.encode() not in client.get('/credit-book').data
    assert 'शेतमाल व्यापारी'.encode() in client.get('/credit-book?view=settled').data
    with app.app_context():
        assert db.session.get(CreditAccount,account_id).remaining == Decimal('0.00')
        assert CreditPayment.query.count() == 2


@pytest.mark.parametrize('amount', ['', '0','-1','NaN','Infinity','1e5','100000000','1.001','12,000','₹100'])
def test_rejects_invalid_amount_without_writes(app,client,people,amount):
    sign_in(client,people[0])
    assert client.post('/credit-book/accounts',data=account_data(client,amount=amount)).status_code == 400
    with app.app_context(): assert CreditAccount.query.count() == 0


@pytest.mark.parametrize('changes', [
    {'contact_name':'x'}, {'contact_name':'a'*101}, {'direction':'other'}, {'note':'x'*301},
    {'entry_date':'2026-11-01'}, {'entry_date':'not-a-date'}, {'entry_date':'1800-01-01'},
    {'due_date':'2026-10-19'}, {'due_date':'2101-01-01'}, {'submission_id':'made-up'},
])
def test_invalid_account_details_are_preserved_for_correction(app,client,people,changes):
    sign_in(client,people[0])
    response=client.post('/credit-book/accounts',data=account_data(client,**changes))
    assert response.status_code == 400
    with app.app_context(): assert CreditAccount.query.count() == 0


@pytest.mark.parametrize('changes', [
    {'amount':'100.51'}, {'amount':'0'}, {'amount':'-1'}, {'amount':'NaN'},
    {'entry_date':'2026-10-19'}, {'entry_date':'2026-10-31'}, {'note':'x'*241},
])
def test_invalid_settlement_keeps_balance_and_history(app,client,people,changes):
    sign_in(client,people[0]); account_id=create_account(client)
    response=client.post(f'/credit-book/accounts/{account_id}/payments',data=payment_data(client,account_id,**changes))
    assert response.status_code == 400
    with app.app_context():
        assert db.session.get(CreditAccount,account_id).remaining == Decimal('100.50')
        assert CreditPayment.query.count() == 0


def test_due_balances_are_exact_private_and_only_include_stated_due_dates(app,client,people):
    sign_in(client,people[0])
    a=create_account(client,amount='100.50',due_date='2026-10-29')
    client.post(f'/credit-book/accounts/{a}/payments',data=payment_data(client,a,amount='0.25'))
    create_account(client,direction='pay',amount='45.30',due_date='2026-10-30')
    create_account(client,amount='22',due_date='2026-10-31')
    create_account(client,amount='500',due_date='')
    sign_in(client,people[1]); create_account(client,amount='9999')
    with app.app_context():
        assert due_balances(people[0],date(2026,10,30)) == {'receive':Decimal('100.25'),'pay':Decimal('45.30')}
    sign_in(client,people[0])
    due=client.get('/credit-book?view=due')
    assert due.status_code == 200 and b'Overdue' in due.data


def test_payment_token_cannot_be_replayed_into_another_account(app,client,people):
    sign_in(client,people[0]); first=create_account(client); second=create_account(client)
    payment=payment_data(client,first)
    assert client.post(f'/credit-book/accounts/{first}/payments',data=payment).status_code == 303
    assert client.post(f'/credit-book/accounts/{second}/payments',data=payment).status_code == 400
    with app.app_context():
        assert db.session.get(CreditAccount,second).remaining == Decimal('100.50')


def test_full_csv_statement_is_private_exact_and_spreadsheet_safe(app,client,people):
    sign_in(client,people[0]); account_id=create_account(client,contact_name='=IMPORTDATA("bad")',note=' +SUM(1,2)')
    client.post(f'/credit-book/accounts/{account_id}/payments',data=payment_data(client,account_id,note='@cmd'))
    response=client.get(f'/credit-book/accounts/{account_id}/statement.csv')
    assert response.status_code == 200 and 'attachment' in response.headers['Content-Disposition']
    records=list(csv.reader(StringIO(response.data.decode('utf-8-sig'))))
    assert records[1][2].startswith("'=") and records[1][6] == "'+SUM(1,2)"
    assert records[2][4:6] == ['40.25','60.25'] and records[2][6] == "'@cmd"
    assert len(records) == 3


def test_real_csrf_required_for_credit_writes(app,client,people):
    app.config['CSRF_ENABLED']=True
    sign_in(client,people[0])
    data=account_data(client)
    assert client.post('/credit-book/accounts',data=data).status_code == 400
    with client.session_transaction() as session: data['csrf_token']=session['_csrf_token']
    response=client.post('/credit-book/accounts',data=data)
    assert response.status_code == 303
    account_id=int(response.location.rsplit('/',1)[-1])
    payment=payment_data(client,account_id)
    assert client.post(f'/credit-book/accounts/{account_id}/payments',data=payment).status_code == 400
    payment['csrf_token']=data['csrf_token']
    assert client.post(f'/credit-book/accounts/{account_id}/payments',data=payment).status_code == 303


@pytest.mark.parametrize('same_submission',[False,True])
def test_concurrent_payments_cannot_overdraw_or_duplicate(app,client,people,monkeypatch,same_submission):
    sign_in(client,people[0]); account_id=create_account(client,amount='100')
    first=app.test_client(); second=app.test_client()
    sign_in(first,people[0]); sign_in(second,people[0])
    a=payment_data(first,account_id,amount='70')
    b=payment_data(second,account_id,amount='70')
    if same_submission:
        b['submission_id']=a['submission_id']
        with second.session_transaction() as session: session['credit_payment_token']=a['submission_id']
    import routes.credit_book as route
    original=route._amount
    barrier=Barrier(2)
    def concurrent_amount(value):
        result=original(value)
        barrier.wait(timeout=10)
        return result
    monkeypatch.setattr(route,'_amount',concurrent_amount)
    def post(item):
        page,data=item
        return page.post(f'/credit-book/accounts/{account_id}/payments',data=data).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses=list(pool.map(post,[(first,a),(second,b)]))
    assert sorted(statuses) == ([303,303] if same_submission else [303,400])
    with app.app_context():
        assert db.session.get(CreditAccount,account_id).remaining == Decimal('30.00')
        assert CreditPayment.query.count() == 1


def test_credit_database_bounds_reject_corrupt_overpayment(app,client,people):
    sign_in(client,people[0]); account_id=create_account(client)
    with app.app_context():
        row=db.session.get(CreditAccount,account_id)
        row.settled_paise=row.total_paise+1
        with pytest.raises(IntegrityError): db.session.commit()
        db.session.rollback()


def test_two_account_tabs_with_same_payment_token_get_safe_conflict_not_500(app,client,people,monkeypatch):
    sign_in(client,people[0])
    ids=[create_account(client,amount='100'),create_account(client,amount='100')]
    first=app.test_client(); second=app.test_client()
    sign_in(first,people[0]); sign_in(second,people[0])
    a=payment_data(first,ids[0],amount='70')
    b=payment_data(second,ids[1],amount='70')
    b['submission_id']=a['submission_id']
    with second.session_transaction() as session: session['credit_payment_token']=a['submission_id']
    import routes.credit_book as route
    original=route._amount
    barrier=Barrier(2)
    def concurrent_amount(value):
        result=original(value); barrier.wait(timeout=10); return result
    monkeypatch.setattr(route,'_amount',concurrent_amount)
    def post(item):
        page,identifier,data=item
        return page.post(f'/credit-book/accounts/{identifier}/payments',data=data).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses=list(pool.map(post,[(first,ids[0],a),(second,ids[1],b)]))
    assert sorted(statuses) == [303,400]
    with app.app_context():
        assert sorted(db.session.get(CreditAccount,identifier).remaining for identifier in ids) == [Decimal('30'),Decimal('100')]
        assert CreditPayment.query.count() == 1


def test_mistaken_entry_void_preserves_record_reason_time_and_creates_no_payment(app,client,people):
    sign_in(client,people[0]); account_id=create_account(client)
    payment=payment_data(client,account_id)
    assert client.post(f'/credit-book/accounts/{account_id}/void',data={'void_reason':'Duplicate record'}).status_code == 303
    with app.app_context():
        row=db.session.get(CreditAccount,account_id)
        assert row.voided and row.void_reason=='Duplicate record' and row.voided_at is not None
        recorded_at=row.voided_at
        assert row.total == Decimal('100.50') and row.settled == Decimal('0') and row.remaining == Decimal('0')
        assert due_balances(people[0],date(2026,10,30)) == {'receive':Decimal('0'),'pay':Decimal('0')}
        assert CreditPayment.query.count() == FarmLedgerEntry.query.count() == 0
    assert client.post(f'/credit-book/accounts/{account_id}/void',data={'void_reason':'Overwrite attempt'}).status_code == 303
    assert client.post(f'/credit-book/accounts/{account_id}/payments',data=payment).status_code == 400
    with app.app_context():
        row=db.session.get(CreditAccount,account_id)
        assert row.void_reason=='Duplicate record' and row.voided_at==recorded_at
    assert b'Produce buyer' not in client.get('/credit-book').data
    assert b'Produce buyer' not in client.get('/credit-book?view=settled').data
    assert b'Produce buyer' in client.get('/credit-book?view=voided').data
    detail=client.get(f'/credit-book/accounts/{account_id}')
    assert b'cb_voided_notice' in detail.data and b'credit-payment-form' not in detail.data
    rows=list(csv.reader(StringIO(client.get(f'/credit-book/accounts/{account_id}/statement.csv').data.decode('utf-8-sig'))))
    assert rows[-1][0] == 'Mistaken entry cancelled' and rows[-1][-1] == 'Duplicate record'


def test_void_refuses_real_settlements_and_requires_a_reason(app,client,people):
    sign_in(client,people[0]); account_id=create_account(client)
    for reason in ['', 'x', 'x'*241]:
        assert client.post(f'/credit-book/accounts/{account_id}/void',data={'void_reason':reason}).status_code == 400
    client.post(f'/credit-book/accounts/{account_id}/payments',data=payment_data(client,account_id))
    assert client.post(f'/credit-book/accounts/{account_id}/void',data={'void_reason':'Wrong record'}).status_code == 400
    with app.app_context():
        assert not db.session.get(CreditAccount,account_id).voided and CreditPayment.query.count()==1


def test_void_requires_real_csrf(app,client,people):
    sign_in(client,people[0]); account_id=create_account(client)
    app.config['CSRF_ENABLED']=True
    assert client.post(f'/credit-book/accounts/{account_id}/void',data={'void_reason':'Duplicate record'}).status_code == 400
    client.get(f'/credit-book/accounts/{account_id}')
    with client.session_transaction() as session: token=session['_csrf_token']
    assert client.post(f'/credit-book/accounts/{account_id}/void',data={'void_reason':'Duplicate record','csrf_token':token}).status_code==303


def test_concurrent_void_and_payment_cannot_cancel_real_payment(app,client,people,monkeypatch):
    from sqlalchemy.sql.dml import Update
    import routes.credit_book as route
    sign_in(client,people[0]); account_id=create_account(client,amount='100')
    first=app.test_client(); second=app.test_client()
    sign_in(first,people[0]); sign_in(second,people[0])
    payment=payment_data(first,account_id,amount='70')
    original=route.db.session.execute
    barrier=Barrier(2)
    def concurrent_execute(statement,*args,**kwargs):
        if isinstance(statement,Update) and statement.table.name=='credit_accounts':
            barrier.wait(timeout=10)
        return original(statement,*args,**kwargs)
    monkeypatch.setattr(route.db.session,'execute',concurrent_execute)
    def post_payment():
        return first.post(f'/credit-book/accounts/{account_id}/payments',data=payment).status_code
    def post_void():
        return second.post(f'/credit-book/accounts/{account_id}/void',data={'void_reason':'Duplicate record'}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        a=pool.submit(post_payment); b=pool.submit(post_void)
        assert sorted([a.result(),b.result()])==[303,400]
    with app.app_context():
        row=db.session.get(CreditAccount,account_id)
        if row.voided:
            assert row.settled_paise==0 and CreditPayment.query.count()==0
        else:
            assert row.remaining==Decimal('30') and CreditPayment.query.count()==1

"""Dashboard counts must represent this farmer and this calendar month only."""
from datetime import date, datetime
from decimal import Decimal

from flask import template_rendered

from advisory_models import FarmField
from farm_tools_models import FarmTask, FarmLedgerEntry
from credit_models import CreditAccount
from models import db, User


def test_dashboard_uses_private_active_fields_open_work_and_exact_month_totals(app, client, monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 1, 1, tzinfo=tz)

    monkeypatch.setattr('routes.auth.datetime', Clock)
    with app.app_context():
        owner = User(name='Own farmer', email='one@example.com', password='unused', role='farmer')
        other = User(name='Other farmer', email='two@example.com', password='unused', role='farmer')
        db.session.add_all([owner, other]); db.session.flush()
        for number, person, archived in [(1,owner,False),(2,owner,False),(3,owner,True),(4,other,False)]:
            db.session.add(FarmField(farmer_id=person.id,name=f'Field {number}',crop='tomato',
                stage='vegetative',archived=archived,submission_id=f'field-{number}'))
        for number, person, due, done in [(1,owner,date(2026,9,30),False),
                (2,owner,date(2026,10,1),False),(3,owner,date(2026,9,30),True),
                (4,other,date(2026,9,30),False)]:
            db.session.add(FarmTask(farmer_id=person.id,title=f'Task {number}',due_date=due,
                                   is_done=done,submission_id=f'task-{number}'))
        for number, person, kind, amount, day in [(1,owner,'income','0.10',date(2026,10,1)),
                (2,owner,'income','0.20',date(2026,10,31)),(3,owner,'expense','0.05',date(2026,10,1)),
                (4,owner,'income','9999.00',date(2026,9,30)),(5,other,'income','8000.00',date(2026,10,1))]:
            db.session.add(FarmLedgerEntry(farmer_id=person.id,kind=kind,amount=Decimal(amount),
                category='other',entry_date=day,submission_id=f'money-{number}'))
        for number, person, direction, total, settled, due in [
                (1,owner,'receive',10010,201,date(2026,9,30)),
                (2,owner,'pay',500,100,date(2026,10,1)),
                (3,owner,'receive',999900,0,date(2026,10,2)),
                (4,other,'receive',888800,0,date(2026,9,30)),
                (5,owner,'receive',200,200,date(2026,9,30)),
                (6,owner,'pay',300,0,None)]:
            db.session.add(CreditAccount(farmer_id=person.id,contact_name=f'Contact {number}',
                direction=direction,total_paise=total,settled_paise=settled,entry_date=date(2026,9,1),
                due_date=due,submission_id=f'credit-{number}'))
        db.session.commit()
        owner_id = owner.id
    with client.session_transaction() as session:
        session['_user_id'] = str(owner_id)
        session['_fresh'] = True
    captured = []
    def capture(sender, template, context, **extra):
        captured.append(context)
    with template_rendered.connected_to(capture, app):
        response = client.get('/auth/farmer/dashboard')
    assert response.status_code == 200
    assert captured[-1]['farm_stats'] == {'fields_count':2,'open_tasks':2,'overdue_tasks':1,
        'monthly_income':Decimal('0.30'),'monthly_expenses':Decimal('0.05')}
    assert b'9999.00' not in response.data and b'8000.00' not in response.data
    daily = captured[-1]['daily_home']
    assert daily['today'] == date(2026,10,1)
    assert [task.title for task in daily['due_tasks']] == ['Task 1','Task 2']
    assert daily['receive_due'] == Decimal('98.09')
    assert daily['pay_due'] == Decimal('4.00')
    assert b'8888.00' not in response.data

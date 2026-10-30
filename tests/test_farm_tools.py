"""Planner regression tests use real SQLite writes and separate user sessions."""

import csv
from datetime import date
from decimal import Decimal
from io import StringIO
import secrets

import pytest
from flask import template_rendered

from farm_tools_models import FarmLedgerEntry, FarmTask
from models import User, db


@pytest.fixture
def farmers(app, monkeypatch):
    monkeypatch.setattr('routes.farm_tools._today', lambda: date(2026, 10, 28))
    with app.app_context():
        people = [User(name='Farmer One', email='one@example.com', password='unused', role='farmer'),
                  User(name='Farmer Two', email='two@example.com', password='unused', role='farmer'),
                  User(name='Buyer', email='buyer@example.com', password='unused', role='buyer')]
        db.session.add_all(people)
        db.session.commit()
        return [person.id for person in people]


def sign_in(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def token(client, kind):
    assert client.get('/farm-tools').status_code == 200
    with client.session_transaction() as session:
        return session[f'farm_tools_{kind}_token']


def task_data(client, **changes):
    data = {'submission_id': token(client, 'task'), 'title': 'Check irrigation',
            'crop': 'Tomato field', 'due_date': '2026-10-28'}
    return data | changes


def entry_data(client, **changes):
    data = {'submission_id': token(client, 'ledger'), 'kind': 'expense', 'category': 'seeds',
            'entry_date': '2026-10-28', 'amount': '25.50', 'note': 'October seeds'}
    return data | changes


def rendered_context(app, client, path):
    contexts = []

    def capture(sender, template, context, **extra):
        contexts.append(context)

    with template_rendered.connected_to(capture, app):
        response = client.get(path)
    assert response.status_code == 200
    return contexts[-1]


def test_planner_requires_farmer(app, client, farmers):
    assert client.get('/farm-tools').status_code == 302
    sign_in(client, farmers[2])
    for method, path in [('get', '/farm-tools'), ('get', '/farm-tools/ledger.csv'),
                         ('post', '/farm-tools/tasks'), ('post', '/farm-tools/ledger')]:
        assert getattr(client, method)(path).status_code == 403


def test_task_persists_retries_are_idempotent_and_status_can_reopen(app, client, farmers):
    sign_in(client, farmers[0])
    data = task_data(client, due_date='2026-10-27')
    assert client.post('/farm-tools/tasks', data=data).status_code == 303
    assert client.post('/farm-tools/tasks', data=data).status_code == 303
    with app.app_context():
        task = FarmTask.query.one()
        task_id = task.id
        assert task.title == 'Check irrigation'
        assert task.due_date == date(2026, 10, 27)
        assert not task.is_done

    context = rendered_context(app, client, '/farm-tools')
    assert context['open_count'] == context['overdue_count'] == 1
    for _ in range(2):
        assert client.post(f'/farm-tools/tasks/{task_id}/status', data={'is_done': '1'}).status_code == 303
    context = rendered_context(app, client, '/farm-tools')
    assert context['open_count'] == context['overdue_count'] == 0
    assert client.post(f'/farm-tools/tasks/{task_id}/status', data={'is_done': '0'}).status_code == 303
    second_session = app.test_client()
    sign_in(second_session, farmers[0])
    assert b'Check irrigation' in second_session.get('/farm-tools').data
    assert client.post(f'/farm-tools/tasks/{task_id}/delete').status_code == 303
    with app.app_context():
        assert FarmTask.query.count() == 0


@pytest.mark.parametrize('changes', [
    {'title': ''}, {'title': 'x'}, {'title': 'x' * 161}, {'crop': 'x' * 81},
    {'due_date': ''}, {'due_date': '2026-02-30'}, {'due_date': '2026-1-1'},
    {'due_date': '1899-12-31'}, {'due_date': '2101-01-01'},
    {'submission_id': 'forged-token'},
])
def test_task_validation_does_not_create_record(app, client, farmers, changes):
    sign_in(client, farmers[0])
    response = client.post('/farm-tools/tasks', data=task_data(client, **changes))
    assert response.status_code == 400
    with app.app_context():
        assert FarmTask.query.count() == 0


def test_private_records_are_not_readable_or_mutable_by_other_farmer(app, client, farmers):
    sign_in(client, farmers[0])
    assert client.post('/farm-tools/tasks', data=task_data(client, title='Private farm job')).status_code == 303
    assert client.post('/farm-tools/ledger', data=entry_data(client, note='Private farm expense')).status_code == 303
    with app.app_context():
        task_id = FarmTask.query.one().id
        entry_id = FarmLedgerEntry.query.one().id
    sign_in(client, farmers[1])
    page = client.get('/farm-tools').data
    assert b'Private farm job' not in page
    assert b'Private farm expense' not in page
    assert b'Private farm expense' not in client.get('/farm-tools/ledger.csv').data
    assert client.post(f'/farm-tools/tasks/{task_id}/status', data={'is_done': '1'}).status_code == 404
    assert client.post(f'/farm-tools/tasks/{task_id}/delete').status_code == 404
    assert client.post(f'/farm-tools/ledger/{entry_id}/delete').status_code == 404
    with app.app_context():
        assert not db.session.get(FarmTask, task_id).is_done
        assert db.session.get(FarmLedgerEntry, entry_id).amount == Decimal('25.50')


def test_replayed_token_cannot_create_different_record(app, client, farmers):
    sign_in(client, farmers[0])
    data = entry_data(client)
    assert client.post('/farm-tools/ledger', data=data).status_code == 303
    assert client.post('/farm-tools/ledger', data=data | {'amount': '500', 'note': 'Changed'}).status_code == 303
    with app.app_context():
        entry = FarmLedgerEntry.query.one()
        assert entry.amount == Decimal('25.50')
        assert entry.note == 'October seeds'


@pytest.mark.parametrize('amount', ['', '0', '-1', 'NaN', 'Infinity', 'inf', '1e3',
                                     '1.001', '100000000', '99999999.999', '01.20', '1,000.00'])
def test_invalid_money_never_reaches_journal(app, client, farmers, amount):
    sign_in(client, farmers[0])
    assert client.post('/farm-tools/ledger', data=entry_data(client, amount=amount)).status_code == 400
    with app.app_context():
        assert FarmLedgerEntry.query.count() == 0


def test_marathi_amount_and_ledger_redirect_keep_money_view(app, client, farmers):
    from urllib.parse import parse_qs, urlsplit
    sign_in(client, farmers[0])
    response = client.post('/farm-tools/ledger', data=entry_data(client, amount='१२५.५०'))
    assert response.status_code == 303
    assert parse_qs(urlsplit(response.location).query)['view'] == ['money']
    with app.app_context():
        entry = FarmLedgerEntry.query.one()
        assert entry.amount == Decimal('125.50')
        entry_id = entry.id
    response = client.post(f'/farm-tools/ledger/{entry_id}/delete')
    assert parse_qs(urlsplit(response.location).query)['view'] == ['money']


@pytest.mark.parametrize('changes', [{'entry_date': '2026-10-29'}, {'entry_date': '2025-02-29'},
                                    {'entry_date': '1899-01-01'}, {'kind': 'profit'},
                                    {'category': 'unknown'}, {'note': 'x' * 241}])
def test_journal_date_and_category_validation(app, client, farmers, changes):
    sign_in(client, farmers[0])
    assert client.post('/farm-tools/ledger', data=entry_data(client, **changes)).status_code == 400
    with app.app_context():
        assert FarmLedgerEntry.query.count() == 0


def test_monthly_totals_are_exact_private_and_include_all_entries(app, client, farmers):
    sign_in(client, farmers[0])
    with app.app_context():
        # More than a page of records still contributes to totals and export.
        entries = [FarmLedgerEntry(farmer_id=farmers[0], entry_date=date(2026, 10, 1), kind='income',
                                  category='produce_sale', amount=Decimal('0.10'), note='Sale',
                                  submission_id=secrets.token_urlsafe(32)) for _ in range(103)]
        entries.extend([
            FarmLedgerEntry(farmer_id=farmers[0], entry_date=date(2026, 10, 28), kind='expense',
                            category='seeds', amount=Decimal('0.20'), note='Seeds', submission_id=secrets.token_urlsafe(32)),
            FarmLedgerEntry(farmer_id=farmers[0], entry_date=date(2026, 9, 30), kind='income',
                            category='produce_sale', amount=Decimal('999.99'), note='Previous month', submission_id=secrets.token_urlsafe(32)),
            FarmLedgerEntry(farmer_id=farmers[1], entry_date=date(2026, 10, 1), kind='income',
                            category='produce_sale', amount=Decimal('999.99'), note='Other farmer', submission_id=secrets.token_urlsafe(32)),
        ])
        db.session.add_all(entries)
        db.session.commit()
    context = rendered_context(app, client, '/farm-tools?month=2026-10')
    assert context['income'] == Decimal('10.30')
    assert context['expense'] == Decimal('0.20')
    assert context['balance'] == Decimal('10.10')
    assert context['entry_count'] == 104
    assert len(context['entries']) == 100
    assert context['ledger_pages'] == 2
    assert context['ledger_page'] == 1
    second_page = rendered_context(app, client, '/farm-tools?month=2026-10&ledger_page=2')
    assert len(second_page['entries']) == 4
    assert second_page['income'] == Decimal('10.30')
    assert second_page['expense'] == Decimal('0.20')
    assert second_page['ledger_previous']
    assert not second_page['ledger_next']
    # Changing pages must neither leak the next month nor silently change totals.
    assert all(entry.entry_date.month == 10 for entry in second_page['entries'])
    exported = client.get('/farm-tools/ledger.csv?month=2026-10')
    rows = list(csv.reader(StringIO(exported.data.decode('utf-8-sig'))))
    assert len(rows) == 105
    assert b'Previous month' not in exported.data
    assert b'Other farmer' not in exported.data
    september = rendered_context(app, client, '/farm-tools?month=2026-09')
    assert september['income'] == Decimal('999.99')


def test_ledger_deletion_updates_totals_and_preserves_selected_month(app, client, farmers):
    sign_in(client, farmers[0])
    response = client.post('/farm-tools/ledger', data=entry_data(client, amount='99999999.99', entry_date='2026-09-15'))
    assert response.status_code == 303
    assert response.location.endswith('month=2026-09')
    with app.app_context():
        entry = FarmLedgerEntry.query.one()
        assert entry.amount == Decimal('99999999.99')
        entry_id = entry.id
    assert client.post(f'/farm-tools/ledger/{entry_id}/delete').location.endswith('month=2026-09')
    context = rendered_context(app, client, '/farm-tools?month=2026-09')
    assert context['expense'] == Decimal('0.00')


@pytest.mark.parametrize('note', ['=HYPERLINK("https://example.com")', '+1+1', '-1+1', '@SUM(1,2)', ' \t=1+1'])
def test_csv_prevents_formula_execution(app, client, farmers, note):
    sign_in(client, farmers[0])
    assert client.post('/farm-tools/ledger', data=entry_data(client, note=note)).status_code == 303
    response = client.get('/farm-tools/ledger.csv?month=2026-10')
    rows = list(csv.reader(StringIO(response.data.decode('utf-8-sig'))))
    assert rows[1][4].startswith("'")
    assert response.headers['Cache-Control'] == 'no-store'
    assert 'attachment;' in response.headers['Content-Disposition']


@pytest.mark.parametrize('month', ['2026-13', '2026-0', '2026-02-01', '1899-12', '../../etc/passwd'])
def test_invalid_month_cannot_expand_export_scope(client, farmers, month):
    sign_in(client, farmers[0])
    assert client.get('/farm-tools', query_string={'month': month}).status_code == 400
    assert client.get('/farm-tools/ledger.csv', query_string={'month': month}).status_code == 400


def test_task_title_and_ledger_notes_are_escaped(app, client, farmers):
    sign_in(client, farmers[0])
    script = '<script>alert(1)</script>'
    assert client.post('/farm-tools/tasks', data=task_data(client, title=script)).status_code == 303
    assert client.post('/farm-tools/ledger', data=entry_data(client, note=script)).status_code == 303
    page = client.get('/farm-tools').data
    assert script.encode() not in page
    assert b'&lt;script&gt;alert(1)&lt;/script&gt;' in page


def test_planner_translations_are_served_without_external_api(client, farmers):
    sign_in(client, farmers[0])
    assert b'js/farm-tools-i18n.js' in client.get('/farm-tools').data
    response = client.get('/static/js/farm-tools-i18n.js')
    assert response.status_code == 200
    for phrase in ['My farm planner', 'मेरे खेत की योजना', 'माझ्या शेतीचे नियोजन']:
        assert phrase.encode() in response.data


def test_task_pagination_keeps_all_records_accessible_and_counts_all_tasks(app, client, farmers):
    sign_in(client, farmers[0])
    with app.app_context():
        db.session.add_all([
            FarmTask(farmer_id=farmers[0], title=f'Task {index:03}', crop='',
                     due_date=date(2026, 10, 27), submission_id=secrets.token_urlsafe(32))
            for index in range(102)
        ])
        db.session.commit()
    first = rendered_context(app, client, '/farm-tools?month=2026-09')
    second = rendered_context(app, client, '/farm-tools?month=2026-09&tasks_page=2')
    assert first['open_count'] == second['overdue_count'] == 102
    assert first['task_pages'] == 2
    assert len(first['tasks']) == 100
    assert len(second['tasks']) == 2
    assert {item.id for item in first['tasks']}.isdisjoint({item.id for item in second['tasks']})
    assert 'month=2026-09' in second['task_previous']
    assert second['task_next'] is None
    assert first['ledger_page'] == second['ledger_page'] == 1


@pytest.mark.parametrize('page', ['0', '-1', 'not-a-page', '9' * 5000])
def test_malformed_page_numbers_do_not_break_planner(client, farmers, page):
    sign_in(client, farmers[0])
    assert client.get('/farm-tools', query_string={'tasks_page': page, 'ledger_page': page}).status_code == 200


def test_invalid_task_state_leaves_record_unchanged(app, client, farmers):
    sign_in(client, farmers[0])
    client.post('/farm-tools/tasks', data=task_data(client))
    with app.app_context():
        task_id = FarmTask.query.one().id
    assert client.post(f'/farm-tools/tasks/{task_id}/status', data={'is_done': 'yes'}).status_code == 400
    assert client.get(f'/farm-tools/tasks/{task_id}/delete').status_code == 405
    with app.app_context():
        assert not db.session.get(FarmTask, task_id).is_done


def advice_task(app, farmer_id, *, title='Original advisory task'):
    """Create a saved advice action without depending on browser form helpers."""
    from datetime import datetime, timezone
    from advisory.engine import analyze_context
    from advisory_models import FarmField, FieldObservation, AdvisoryTaskLink
    with app.app_context():
        field = FarmField(farmer_id=farmer_id, name='North field', crop='tomato',
            stage='vegetative', soil='loamy', irrigation='drip', submission_id=secrets.token_urlsafe(32))
        db.session.add(field); db.session.flush()
        checked = datetime(2026, 10, 28, 6, tzinfo=timezone.utc)
        observation = {'moisture':'dry','waterlogging':False,'pest_present':False,'leaf_symptoms':'none'}
        report = analyze_context(field.context_snapshot(), observation, now=checked)
        row = FieldObservation(farmer_id=farmer_id, field_id=field.id,
            field_snapshot=field.context_snapshot(), observation_data=observation, report_data=report,
            submission_id=secrets.token_urlsafe(32), created_at=checked)
        task = FarmTask(farmer_id=farmer_id, title=title, crop=field.name,
            due_date=date(2026,10,28), submission_id=secrets.token_urlsafe(32))
        db.session.add_all([row, task]); db.session.flush()
        db.session.add(AdvisoryTaskLink(farmer_id=farmer_id, observation_id=row.id,
            action_code='dry_soil', task_id=task.id))
        db.session.commit()
        return field.id, row.id, task.id


@pytest.mark.parametrize('hour,minute,expected_date', [(18,29,date(2026,10,28)), (18,30,date(2026,10,29))])
def test_advice_task_source_uses_indian_calendar_date(app, client, farmers, hour, minute, expected_date):
    from datetime import datetime, timezone
    from advisory_models import FieldObservation
    _, report_id, task_id = advice_task(app, farmers[0])
    with app.app_context():
        db.session.get(FieldObservation, report_id).created_at = datetime(2026,10,28,hour,minute,tzinfo=timezone.utc)
        db.session.commit()
    sign_in(client, farmers[0])
    context = rendered_context(app, client, '/farm-tools')
    assert context['task_advice'][task_id]['date'] == expected_date


def test_saved_advice_task_requires_review_after_new_wet_check_but_manual_work_unchanged(app, client, farmers):
    from datetime import datetime, timezone
    from advisory_models import FarmField, FieldObservation
    from advisory.engine import analyze_context
    field_id, report_id, task_id = advice_task(app, farmers[0])
    sign_in(client, farmers[0])
    manual = client.post('/farm-tools/tasks', data=task_data(client, title='Buy harvest bags'))
    assert manual.status_code == 303
    fresh = rendered_context(app, client, '/farm-tools')
    assert fresh['task_advice'][task_id]['stale'] is False
    fresh_page = client.get('/farm-tools')
    assert f'/my-farm/reports/{report_id}'.encode() in fresh_page.data
    assert b'data-advice-review-required' not in fresh_page.data
    # Full instructions are reachable; task labels never silently truncate them.
    with app.app_context():
        original = db.session.get(FieldObservation, report_id)
        full_action = next(p for p in original.report_data['priorities'] if p['code']=='dry_soil')['action']
        assert full_action.encode() in fresh_page.data
        field = db.session.get(FarmField, field_id)
        wet = {'moisture':'wet','waterlogging':True,'pest_present':False,'leaf_symptoms':'wilting'}
        later = FieldObservation(farmer_id=farmers[0], field_id=field_id,
            field_snapshot=field.context_snapshot(), observation_data=wet,
            report_data=analyze_context(field.context_snapshot(), wet),
            submission_id=secrets.token_urlsafe(32), created_at=datetime(2026,10,28,7,tzinfo=timezone.utc))
        db.session.add(later); db.session.commit(); latest_id = later.id
    context = rendered_context(app, client, '/farm-tools')
    assert context['task_advice'][task_id]['stale'] is True
    assert context['task_advice'][task_id]['latest_report_id'] == latest_id
    page = client.get('/farm-tools')
    assert b'data-advice-review-required' in page.data
    assert f'/my-farm/reports/{latest_id}'.encode() in page.data
    assert b'I already did this' in page.data
    assert b'Buy harvest bags' in page.data
    with app.app_context():
        assert FarmTask.query.count() == 2
        assert not db.session.get(FarmTask, task_id).is_done
    # Recording already-completed work remains possible without claiming the
    # outdated recommendation is a current instruction.
    assert client.post(f'/farm-tools/tasks/{task_id}/status', data={'is_done':'1'}).status_code == 303
    assert b'data-advice-review-required' not in client.get('/farm-tools').data
    with app.app_context():
        assert db.session.get(FarmTask, task_id).is_done
        assert FieldObservation.query.count() == 2


@pytest.mark.parametrize('change', ['profile', 'age', 'archive'])
def test_saved_advice_task_uses_same_profile_age_and_archive_freshness_as_report(app, client, farmers, change):
    from datetime import datetime, timezone
    from advisory_models import FarmField, FieldObservation
    from advisory.freshness import report_is_stale, latest_report_keys
    field_id, report_id, task_id = advice_task(app, farmers[0])
    sign_in(client, farmers[0])
    with app.app_context():
        field, report = db.session.get(FarmField, field_id), db.session.get(FieldObservation, report_id)
        if change == 'profile': field.stage = 'flowering'
        elif change == 'age': report.created_at = datetime(2026,10,18,6,tzinfo=timezone.utc)
        else: field.archived = True
        db.session.commit()
        assert report_is_stale(report, date(2026,10,28), latest_report_keys(farmers[0],[field_id])[field_id])
    context = rendered_context(app, client, '/farm-tools')
    assert context['task_advice'][task_id]['stale'] is True
    assert f'/my-farm/fields/{field_id}'.encode() in client.get('/farm-tools').data


def test_plan_metadata_never_exposes_another_farmers_report_even_with_corrupt_link(app, client, farmers):
    from advisory_models import AdvisoryTaskLink
    _, private_report, other_task = advice_task(app, farmers[1], title='Private other-farmer work')
    sign_in(client, farmers[0])
    client.post('/farm-tools/tasks', data=task_data(client, title='My ordinary task'))
    with app.app_context():
        own_task = FarmTask.query.filter_by(farmer_id=farmers[0]).one()
        db.session.add(AdvisoryTaskLink(farmer_id=farmers[0], observation_id=private_report,
            action_code='invalid-cross-owner-link', task_id=own_task.id))
        db.session.commit()
    context = rendered_context(app, client, '/farm-tools')
    assert context['task_advice'] == {}
    page = client.get('/farm-tools')
    assert b'My ordinary task' in page.data
    assert b'Private other-farmer work' not in page.data
    assert f'/my-farm/reports/{private_report}'.encode() not in page.data


def test_advice_task_provenance_uses_bulk_queries(app, client, farmers):
    from sqlalchemy import event
    for _ in range(5): advice_task(app, farmers[0])
    sign_in(client, farmers[0])
    statements = []
    def record(conn, cursor, statement, parameters, context, executemany):
        if 'advisory_task_links' in statement or 'field_observations' in statement:
            statements.append(statement)
    with app.app_context():
        engine = db.engine
        event.listen(engine, 'before_cursor_execute', record)
        try:
            response = client.get('/farm-tools')
        finally:
            event.remove(engine, 'before_cursor_execute', record)
    assert response.status_code == 200
    assert len(statements) == 2

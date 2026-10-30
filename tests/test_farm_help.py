"""Account-free practical checks must stay evidence-based and safe to submit."""
from flask import template_rendered
import pytest
from werkzeug.datastructures import MultiDict

from models import User, db


def data(**changes):
    return dict(problem='water', crop='other', moisture='unknown',
                waterlogging='unknown', leaf_symptoms='none', pest_present='unknown') | changes


def answer(app, client, values):
    contexts = []
    def capture(sender, template, context, **extra):
        contexts.append(context)
    with template_rendered.connected_to(capture, app):
        response = client.post('/farm-help', data=values)
    return response, contexts[-1]


@pytest.mark.parametrize('problem', ['water', 'plant', 'pest'])
def test_public_checks_work_without_login_or_api(client, problem):
    response = client.get('/farm-help?problem=' + problem)
    assert response.status_code == 200
    assert b'id="help-form"' in response.data
    assert b'name="csrf_token"' in response.data
    assert b'id="help-result"' not in response.data
    assert b'tel:18001801551' in response.data


@pytest.mark.parametrize('moisture,code', [
    ('unknown','check_moisture'), ('dry','dry_soil'),
    ('wet','wet_soil'), ('balanced','recheck_water'),
])
def test_water_check_changes_with_actual_root_moisture(app, client, moisture, code):
    response, context = answer(app, client, data(moisture=moisture, waterlogging='0'))
    assert response.status_code == 200
    assert context['primary']['code'] == code
    assert context['report']['facts']['weather'] is None
    assert context['report']['facts']['stage'] == 'unknown'
    assert context['report']['facts']['area_m2'] is None
    assert b'not a diagnosis or a water-dose prescription' in response.data


def test_wet_wilting_takes_priority_over_requested_pest_or_water_advice(app, client):
    for problem in ('water', 'plant', 'pest'):
        response, context = answer(app, client, data(problem=problem,
            moisture='wet', leaf_symptoms='wilting', waterlogging='0', pest_present='1'))
        assert response.status_code == 200
        assert context['primary']['code'] == 'wet_wilting'
        assert context['primary']['severity'] == 'urgent'
        assert 'does not prove the crop needs irrigation' in context['primary']['reason']
        assert context['primary']['localized']['mr']['action']
        assert context['primary']['localized']['hi']['action']


def test_standing_water_in_rice_uses_rice_context_not_generic_drainage(app, client):
    response, context = answer(app, client, data(crop='rice', moisture='wet', waterlogging='1'))
    assert response.status_code == 200
    assert context['primary']['code'] == 'paddy_excess_water'
    assert 'local rice guidance' in context['primary']['action']


@pytest.mark.parametrize('moisture',['dry','balanced','wet'])
def test_unchecked_standing_water_must_not_be_used_as_a_negative_water_observation(app, client, moisture):
    response, context = answer(app, client, data(moisture=moisture))
    assert response.status_code == 200
    assert context['primary']['code'] == 'check_standing_water'
    assert 'waterlogging' in context['unchecked']
    assert 'pest_present' in context['unchecked']
    assert 'moisture' not in context['unchecked']
    assert not {'dry_soil','wet_soil'} & {item['code'] for item in context['others']}
    assert b'data-help-unchecked' in response.data


@pytest.mark.parametrize('present,code', [('1','pest_scout'), ('0','inspect_pest'), ('unknown','inspect_pest')])
def test_pest_presence_never_implies_treatment_or_absence(app, client, present, code):
    response, context = answer(app, client, data(problem='pest', pest_present=present))
    assert response.status_code == 200
    assert context['primary']['code'] == code
    assert 'before' in context['primary']['action']
    if present != '1':
        assert 'does not establish that pests are absent' in context['primary']['reason']


def test_leaf_problem_asks_for_observation_before_naming_cause(app, client):
    response, context = answer(app, client, data(problem='plant', leaf_symptoms='yellowing'))
    assert response.status_code == 200
    assert context['primary']['code'] == 'leaf_check'
    assert 'does not identify a disease' in context['primary']['reason']
    _, empty = answer(app, client, data(problem='plant'))
    assert empty['primary']['code'] == 'inspect_plant'


@pytest.mark.parametrize('key,value', [
    ('problem','disease-diagnosis'), ('crop','banana'), ('moisture','NaN'),
    ('waterlogging','true'), ('leaf_symptoms','confirmed-blight'),
    ('pest_present','2'), ('crop','x'*5000),
])
def test_unlisted_answers_are_rejected(app, client, key, value):
    response, context = answer(app, client, data(**{key:value}))
    assert response.status_code == 400
    assert context['primary'] is None
    assert context['error'] == 'fh_invalid'


def test_duplicate_form_values_are_rejected_without_ambiguous_interpretation(client):
    payload = MultiDict(data().items())
    payload.add('moisture','wet')
    assert client.post('/farm-help',data=payload).status_code == 400


def test_problem_query_is_validated_and_html_is_not_executed(client):
    attack = '<img src=x onerror=alert(1)>'
    response = client.get('/farm-help', query_string={'problem':attack})
    assert response.status_code == 400
    assert attack.encode() not in response.data


def test_real_csrf_is_required_for_anonymous_help(app, client):
    app.config['CSRF_ENABLED'] = True
    assert client.post('/farm-help',data=data()).status_code == 400
    assert client.get('/farm-help').status_code == 200
    with client.session_transaction() as session:
        token = session['_csrf_token']
    response = client.post('/farm-help',data=data() | {'csrf_token':token})
    assert response.status_code == 200
    assert b'id="help-result"' in response.data


def test_help_does_not_create_accounts_or_field_records(app, client):
    from advisory_models import FarmField, FieldObservation
    response = client.post('/farm-help',data=data(moisture='dry'))
    assert response.status_code == 200
    with app.app_context():
        assert User.query.count() == 0
        assert FarmField.query.count() == 0
        assert FieldObservation.query.count() == 0


def test_saved_history_link_is_role_appropriate(app, client):
    for role in ('farmer','buyer'):
        with app.app_context():
            user = User(name=role, email=role+'@help.example', password='unused', role=role)
            db.session.add(user); db.session.commit(); user_id=user.id
        with client.session_transaction() as session:
            session['_user_id'] = str(user_id)
            session['_fresh'] = True
        response = client.post('/farm-help',data=data())
        assert response.status_code == 200
        if role == 'farmer':
            assert b'data-i18n="fh_save_history"' in response.data
        else:
            assert b'data-i18n="fh_save_history"' not in response.data

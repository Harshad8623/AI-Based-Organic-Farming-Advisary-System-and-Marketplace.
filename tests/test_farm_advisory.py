"""Real field/observation writes, privacy, snapshots and actionable reports."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import re

from flask import template_rendered
import pytest

from advisory_models import FarmField, FieldObservation, AdvisoryFollowup, AdvisoryTaskLink
from farm_tools_models import FarmTask
from models import User, db
from routes.farm_advisory import _today


@pytest.fixture
def people(app):
    with app.app_context():
        users = [User(name='First Farmer', email='first@field.example', password='unused', role='farmer'),
                 User(name='Second Farmer', email='second@field.example', password='unused', role='farmer'),
                 User(name='Buyer', email='buyer@field.example', password='unused', role='buyer')]
        db.session.add_all(users); db.session.commit()
        return [user.id for user in users]


def login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def field_data(client, **changes):
    assert client.get('/my-farm/fields/new').status_code == 200
    with client.session_transaction() as session:
        token = session['advisory_field_token']
    return {'name':'North tomato field', 'location':'Sambhajinagar', 'crop':'tomato',
            'stage':'vegetative', 'soil':'loamy', 'irrigation':'drip', 'area_value':'2.5',
            'area_unit':'acre', 'planting_date':(_today()-timedelta(days=20)).isoformat(),
            'submission_id':token} | changes


def create_field(app, client, **changes):
    response = client.post('/my-farm/fields', data=field_data(client, **changes))
    assert response.status_code == 303
    return int(response.location.rsplit('/',1)[1])


def observation_data(client, field_id, **changes):
    assert client.get(f'/my-farm/fields/{field_id}').status_code == 200
    with client.session_transaction() as session:
        token = session['advisory_observation_token']
    return {'submission_id':token, 'moisture':'dry', 'waterlogging':'0', 'pest_present':'0',
            'leaf_symptoms':'none', 'notes':'Dry root zone in north field'} | changes


def observe(client, field_id, **changes):
    data=observation_data(client, field_id, **changes)
    response=client.post(f'/my-farm/fields/{field_id}/observe',data=data)
    assert response.status_code==303
    return int(response.location.rsplit('/',1)[1])


def context(app, client, path):
    contexts=[]
    def capture(sender, template, context, **extra): contexts.append(context)
    with template_rendered.connected_to(capture,app):
        response=client.get(path)
    assert response.status_code==200
    return contexts[-1]


def test_farmer_only_and_owner_scoped_every_record(app,client,people):
    assert client.get('/my-farm').status_code==302
    login(client,people[2])
    assert client.get('/my-farm').status_code==403
    login(client,people[0])
    field_id=create_field(app,client)
    report_id=observe(client,field_id)
    login(client,people[1])
    for method,path in [('get',f'/my-farm/fields/{field_id}'),('get',f'/my-farm/fields/{field_id}/edit'),
                        ('post',f'/my-farm/fields/{field_id}/edit'),('post',f'/my-farm/fields/{field_id}/archive'),
                        ('post',f'/my-farm/fields/{field_id}/observe'),('get',f'/my-farm/reports/{report_id}'),
                        ('post',f'/my-farm/reports/{report_id}/followup'),
                        ('post',f'/my-farm/reports/{report_id}/actions/dry_soil')]:
        assert getattr(client,method)(path).status_code==404
    assert b'North tomato field' not in client.get('/my-farm').data
    with app.app_context(): assert AdvisoryFollowup.query.count()==0 and FarmTask.query.count()==0


def test_field_creation_conversion_retry_and_unknown_values(app,client,people):
    login(client,people[0]); data=field_data(client,area_value='२.५')
    first=client.post('/my-farm/fields',data=data)
    assert first.status_code==303
    assert client.post('/my-farm/fields',data=data).location==first.location
    with app.app_context():
        field=FarmField.query.one()
        assert field.area_m2==Decimal('10117.14')
        assert field.farmer_id==people[0]
    second=create_field(app,client,name='Unmeasured field',area_value='',planting_date='',soil='unknown',stage='unknown')
    with app.app_context(): assert db.session.get(FarmField,second).area_m2 is None


@pytest.mark.parametrize('changes',[
    {'name':'x'},{'name':'x'*81},{'location':'x'*121},{'crop':'imaginary'}, {'stage':'invalid'},
    {'soil':'invalid'},{'irrigation':'magic'},{'area_value':'NaN'},{'area_value':'inf'},
    {'area_value':'-2'},{'area_value':'0'},{'area_value':'1,5'},{'area_unit':'unknown'},
    {'planting_date':'2026-02-30'},{'planting_date':'2100-01-01'},{'submission_id':'forged'},
])
def test_bad_field_input_cannot_save(app,client,people,changes):
    login(client,people[0]); response=client.post('/my-farm/fields',data=field_data(client,**changes))
    assert response.status_code==400
    with app.app_context(): assert FarmField.query.count()==0


def test_edit_preserves_history_and_detects_conflicting_tab(app,client,people):
    login(client,people[0]); field_id=create_field(app,client)
    report_id=observe(client,field_id)
    values=field_data(client,crop='onion',version='1')
    assert client.post(f'/my-farm/fields/{field_id}/edit',data=values).status_code==303
    values['crop']='cotton'
    assert client.post(f'/my-farm/fields/{field_id}/edit',data=values).status_code==409
    assert client.post(f'/my-farm/fields/{field_id}/edit',data=values).status_code==409
    with app.app_context():
        assert db.session.get(FarmField,field_id).crop=='onion'
        assert db.session.get(FieldObservation,report_id).field_snapshot['crop']=='tomato'
    assert client.post(f'/my-farm/reports/{report_id}/actions/dry_soil').status_code==409
    with app.app_context(): assert FarmTask.query.count()==0


def test_archiving_preserves_reports_and_explicit_restore_is_repeat_safe(app,client,people):
    login(client,people[0]); field_id=create_field(app,client); report_id=observe(client,field_id)
    for _ in range(2): assert client.post(f'/my-farm/fields/{field_id}/archive',data={'archived':'1'}).status_code==303
    assert client.get(f'/my-farm/reports/{report_id}').status_code==200
    assert client.post(f'/my-farm/fields/{field_id}/observe',data={}).status_code==409
    assert client.post(f'/my-farm/reports/{report_id}/actions/dry_soil').status_code==409
    assert b'North tomato field' not in client.get('/my-farm').data
    assert b'North tomato field' in client.get('/my-farm?archived=1').data
    assert client.post(f'/my-farm/fields/{field_id}/archive',data={'archived':'0'}).status_code==303
    assert client.get(f'/my-farm/fields/{field_id}').status_code==200
    with app.app_context(): assert FieldObservation.query.count()==1


def test_observation_report_is_explained_persisted_and_retry_safe(app,client,people):
    login(client,people[0]); field_id=create_field(app,client)
    values=observation_data(client,field_id,inspected_plants='२०',affected_plants='५',pest_present='1',leaf_symptoms='spots')
    first=client.post(f'/my-farm/fields/{field_id}/observe',data=values)
    assert first.status_code==303
    assert client.post(f'/my-farm/fields/{field_id}/observe',data=values).location==first.location
    with app.app_context():
        row=FieldObservation.query.one()
        assert row.observation_data['inspected_plants']==20
        assert row.report_data['facts']['observation']['affected_percent']==25
        assert all(all(language in item['localized'] for language in ['en','hi','mr']) for item in row.report_data['priorities'])
        assert row.report_data['method']=='local_expert_system'
        json.dumps(row.report_data)
    response=client.get(first.location)
    assert response.status_code==200 and b'Observations used' in response.data
    assert b'farm-advisory-i18n.js' in response.data


@pytest.mark.parametrize('changes',[
    {'moisture':'madeup'},{'leaf_symptoms':'disease_name'},{'waterlogging':'yes'},
    {'pest_present':'true'},{'inspected_plants':'10'},{'affected_plants':'3'},
    {'inspected_plants':'10','affected_plants':'11'}, {'inspected_plants':'0','affected_plants':'0'},
    {'inspected_plants':'NaN','affected_plants':'0'},{'recent_rain_mm':'NaN'},
    {'recent_rain_mm':'-1'},{'recent_rain_mm':'1001'},{'notes':'n'*501},
    {'submission_id':'forged'},
])
def test_bad_observation_never_creates_report(app,client,people,changes):
    login(client,people[0]); field_id=create_field(app,client)
    response=client.post(f'/my-farm/fields/{field_id}/observe',data=observation_data(client,field_id,**changes))
    assert response.status_code==400
    with app.app_context(): assert FieldObservation.query.count()==0


def test_actions_use_server_snapshot_not_injected_text_and_do_not_duplicate(app,client,people):
    login(client,people[0]); field_id=create_field(app,client); report_id=observe(client,field_id)
    for _ in range(2):
        response=client.post(f'/my-farm/reports/{report_id}/actions/dry_soil',data={'title':'Injected order','due_date':'2100-01-01','language':'mr'})
        assert response.status_code==303
    with app.app_context():
        assert FarmTask.query.count()==AdvisoryTaskLink.query.count()==1
        row=db.session.get(FieldObservation,report_id)
        action=next(item for item in row.report_data['priorities'] if item['code']=='dry_soil')
        task=FarmTask.query.one()
        assert task.title==action['localized']['mr']['action'][:160]
        assert task.title!='Injected order' and task.due_date==_today()
    assert client.post(f'/my-farm/reports/{report_id}/actions/nonexistent').status_code==404


def test_old_report_cannot_create_new_tasks_and_offers_new_check(app,client,people):
    login(client,people[0]); field_id=create_field(app,client); report_id=observe(client,field_id)
    with app.app_context():
        row=db.session.get(FieldObservation,report_id)
        row.created_at=datetime.now(timezone.utc)-timedelta(days=10); db.session.commit()
    response=client.post(f'/my-farm/reports/{report_id}/actions/dry_soil')
    assert response.status_code==409 and b'Record a fresh field check' in response.data
    with app.app_context(): assert FarmTask.query.count()==0
    assert client.post(f'/my-farm/reports/{report_id}/followup',data={'verdict':'improved','note':'Observed later'}).status_code==303


def test_followup_is_personal_report_one_per_observation_and_editable(app,client,people):
    login(client,people[0]); field_id=create_field(app,client); report_id=observe(client,field_id)
    for verdict in ['improved','improved','unchanged']:
        assert client.post(f'/my-farm/reports/{report_id}/followup',data={'verdict':verdict,'note':'Checked again'}).status_code==303
    with app.app_context():
        assert AdvisoryFollowup.query.count()==1
        assert AdvisoryFollowup.query.one().verdict=='unchanged'
    assert client.post(f'/my-farm/reports/{report_id}/followup',data={'verdict':'cured','note':''}).status_code==400
    assert client.post(f'/my-farm/reports/{report_id}/followup',data={'verdict':'worse','note':'x'*501}).status_code==400


def test_case_history_excludes_future_and_other_owners(app,client,people,monkeypatch):
    login(client,people[0]); field_id=create_field(app,client)
    previous=observe(client,field_id)
    current=observe(client,field_id)
    later=observe(client,field_id)
    login(client,people[1]); otherfield=create_field(app,client); other=observe(client,otherfield)
    captured=[]
    def retrieve(context,observation,history,**kwargs):
        captured.extend(row['id'] for row in history)
        return {'status':'no_history','cases':[]}
    monkeypatch.setattr('routes.farm_advisory.retrieve_cases',retrieve)
    login(client,people[0])
    assert client.get(f'/my-farm/reports/{current}').status_code==200
    assert captured==[previous]
    assert later not in captured and other not in captured


def test_learning_failure_preserves_current_explanations(app,client,people,monkeypatch):
    login(client,people[0]); field_id=create_field(app,client); report_id=observe(client,field_id)
    def failure(*args,**kwargs): raise ImportError('optional scientific runtime unavailable')
    monkeypatch.setattr('routes.farm_advisory.retrieve_cases',failure)
    response=client.get(f'/my-farm/reports/{report_id}')
    assert response.status_code==200
    assert b'data-i18n="adf_cases_unavailable"' in response.data
    assert b'Observations used' in response.data


def test_csrf_and_html_escaping(app,client,people):
    login(client,people[0]); field_id=create_field(app,client,name='<script>bad()</script>')
    response=client.get(f'/my-farm/fields/{field_id}')
    assert b'<script>bad()</script>' not in response.data and b'&lt;script&gt;' in response.data
    app.config['CSRF_ENABLED']=True
    values=observation_data(client,field_id)
    assert client.post(f'/my-farm/fields/{field_id}/observe',data=values).status_code==400
    page=client.get(f'/my-farm/fields/{field_id}')
    values['csrf_token']=re.search(rb'name="csrf_token" value="([^"]+)"',page.data).group(1).decode()
    assert client.post(f'/my-farm/fields/{field_id}/observe',data=values).status_code==303


def test_only_new_save_redirect_has_one_shot_matching_draft_marker(app,client,people):
    login(client,people[0]); field_id=create_field(app,client)
    previous=observe(client,field_id)
    values=observation_data(client,field_id,draft_revision='submitted_revision_123')
    response=client.post(f'/my-farm/fields/{field_id}/observe',data=values)
    current=int(response.location.rsplit('/',1)[1])
    old_page=client.get(f'/my-farm/reports/{previous}')
    assert b'data-adf-saved-owner=' not in old_page.data
    with client.session_transaction() as session:
        assert session['advisory_saved_observation']['observation_id']==current
    saved_page=client.get(response.location)
    assert b'data-adf-saved-revision="submitted_revision_123"' in saved_page.data
    assert b'data-adf-saved-owner=' not in client.get(response.location).data
    assert client.post(f'/my-farm/fields/{field_id}/observe',data=values).status_code==303
    assert b'data-adf-saved-owner=' not in client.get(response.location).data


def test_field_pages_all_have_complete_local_translations():
    from pathlib import Path
    import subprocess
    script=r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const context=vm.createContext({TRANSLATIONS:{en:{},hi:{},mr:{}},document:{readyState:'loading',addEventListener(){}}});
vm.runInContext(fs.readFileSync('static/js/farm-advisory-i18n.js','utf8'),context);
const copy=vm.runInContext('TRANSLATIONS',context);
for(const filename of fs.readdirSync('templates/advisory').filter(x=>x.endsWith('.html'))){
  for(const match of fs.readFileSync('templates/advisory/'+filename,'utf8').matchAll(/data-i18n(?:-placeholder|-aria|-title)?="([^"{}]+)"/g)){
    for(const lang of ['en','hi','mr'])assert.ok(copy[lang][match[1]],filename+': '+lang+'/'+match[1]);
  }
}
'''
    result=subprocess.run(['node','-e',script],cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True,timeout=10)
    assert result.returncode==0,result.stderr


def test_index_uses_actual_latest_report_per_owned_field(app,client,people):
    login(client,people[0]); first=create_field(app,client); second=create_field(app,client,name='South field')
    older=observe(client,first); newest=observe(client,first); other=observe(client,second)
    ctx=context(app,client,'/my-farm')
    assert {key:value.id for key,value in ctx['latest'].items()}=={first:newest,second:other}
    with app.app_context():
        row=db.session.get(FieldObservation,older)
        row.created_at=datetime.now(timezone.utc)+timedelta(seconds=5);db.session.commit()
    ctx=context(app,client,'/my-farm')
    assert ctx['latest'][first].id==older


def test_new_field_check_supersedes_old_advice_even_on_same_day(app,client,people):
    login(client,people[0]); field_id=create_field(app,client)
    dry=observe(client,field_id,moisture='dry')
    wet=observe(client,field_id,moisture='wet',waterlogging='1',leaf_symptoms='wilting')
    assert client.post(f'/my-farm/reports/{dry}/actions/dry_soil').status_code==409
    with app.app_context(): assert FarmTask.query.count()==0
    assert client.get(f'/my-farm/reports/{wet}').status_code==200

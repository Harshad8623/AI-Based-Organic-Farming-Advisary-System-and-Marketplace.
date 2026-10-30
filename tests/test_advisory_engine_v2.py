"""Decision-support regressions for real observations, uncertainty and safety."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json

import pytest

from advisory.catalog import MESSAGES, MISSING_DATA, SOURCES
from advisory.engine import AdvisoryInputError, analyze_context, localize_priority

NOW = datetime(2026, 10, 28, 7, tzinfo=timezone.utc)
CONTEXT = {'crop':'tomato', 'stage':'flowering', 'soil':'loamy', 'irrigation':'drip',
           'area_m2':'4046.86', 'planting_date':'2026-09-28'}
OBSERVATION = {'moisture':'balanced', 'waterlogging':False, 'pest_present':False,
               'affected_plants':0, 'inspected_plants':20, 'leaf_symptoms':'none',
               'recent_rain_mm':0, 'notes':''}


def report(context=None, observation=None, weather=None, now=NOW):
    return analyze_context(CONTEXT | (context or {}), OBSERVATION | (observation or {}), weather, now=now)


def codes(value):
    return [item['code'] for item in value['priorities']]


def weather(**changes):
    return {'source':'OpenWeatherMap', 'observed_at':NOW.isoformat(), 'temp':36,
            'wind_speed':6, 'humidity':55} | changes


def test_observation_explains_next_actions_and_remains_json_safe():
    value = report(observation={'moisture':'dry', 'recent_rain_mm':Decimal('2.5')})
    assert 'dry_soil' in codes(value)
    assert value['facts']['days_since_planting'] == 30
    assert value['facts']['area_m2'] == 4046.86
    assert value['facts']['observation']['recent_rain_mm'] == 2.5
    assert value['next_review_days'] == 0
    assert value['method'] == 'local_expert_system'
    json.dumps(value, allow_nan=False)
    dry = next(item for item in value['priorities'] if item['code'] == 'dry_soil')
    assert any(fact['code'] == 'recent_rain_mm' and fact['value'] == 2.5 for fact in dry['facts'])
    assert all(set(item['localized']) == {'en','hi','mr'} for item in value['priorities'])


def test_waterlogging_wins_over_contradictory_dry_report():
    value = report(observation={'waterlogging':True, 'moisture':'dry'})
    assert codes(value)[0] == 'waterlogging'
    assert 'conflicting_moisture' in codes(value)
    assert 'dry_soil' not in codes(value)
    assert 'rainfed_dry' not in codes(value)
    assert value['priorities'][0]['severity'] == 'urgent'
    assert value['priorities'][0]['due_in_days'] == 0


def test_wilting_in_wet_soil_does_not_trigger_more_water_or_a_diagnosis():
    value = report(observation={'moisture':'wet','leaf_symptoms':'wilting', 'affected_plants':4})
    wilt = next(item for item in value['priorities'] if item['code'] == 'wet_wilting')
    assert wilt['severity'] == 'urgent'
    assert 'dry_soil' not in codes(value)
    assert 'does not prove' in wilt['reason']
    assert 'before treatment' in wilt['action']
    assert 'diagnosis' not in value['facts']


def test_managed_paddy_water_is_not_treated_as_unwanted_waterlogging():
    value = report(context={'crop':'rice','irrigation':'flood'}, observation={'moisture':'wet'})
    assert 'paddy_water_check' in codes(value)
    assert 'waterlogging' not in codes(value)
    assert 'wet_soil' not in codes(value)
    assert all(item['severity'] != 'urgent' for item in value['priorities'])
    excessive = report(context={'crop':'rice','irrigation':'flood'},
                       observation={'moisture':'wet','waterlogging':True})
    assert codes(excessive)[0] == 'paddy_excess_water'
    assert 'standing_water_depth' in excessive['missing_data']
    assert 'paddy_water_check' not in codes(excessive)


def test_rainfed_dry_field_does_not_assume_irrigation_is_available():
    value = report(context={'irrigation':'rainfed'}, observation={'moisture':'dry'})
    assert 'rainfed_dry' in codes(value) and 'dry_soil' not in codes(value)
    action = next(item['action'] for item in value['priorities'] if item['code']=='rainfed_dry')
    assert 'available' in action and 'local' in action


def test_missing_moisture_stage_and_date_are_reported_without_inventing_values():
    value = analyze_context({'crop':'other'}, {}, now=NOW)
    assert set(value['missing_data']) == {'planting_date','growth_stage','local_crop_guidance','moisture','current_weather'}
    assert value['facts']['stage'] == 'unknown'
    assert value['facts']['planting_date'] is None
    assert value['facts']['days_since_planting'] is None
    assert 'confirm_stage' in codes(value) and 'check_moisture' in codes(value)
    assert all(code in MISSING_DATA for code in value['missing_data'])


def test_affected_fraction_describes_inspected_sample_not_population_risk():
    value = report(observation={'affected_plants':3,'inspected_plants':12,'pest_present':True})
    assert value['facts']['observation']['affected_percent'] == 25.0
    item = next(item for item in value['priorities'] if item['code']=='pest_scout')
    fact = next(fact for fact in item['facts'] if fact['code']=='affected_percent')
    assert '3 of 12 inspected' in fact['localized']['en']
    assert fact['unit'] == '%'
    assert 'economic treatment threshold' in item['reason']
    assert 'risk_score' not in value and 'confidence' not in value


def test_zero_sample_and_unknown_sample_cannot_create_an_incidence_percentage():
    for observation in [{'affected_plants':0,'inspected_plants':0,'pest_present':True},
                        {'affected_plants':None,'inspected_plants':None,'leaf_symptoms':'spots'}]:
        value = report(observation=observation)
        assert value['facts']['observation']['affected_percent'] is None
        assert 'inspection_counts' in value['missing_data']
        assert not any(fact['code']=='affected_percent' for item in value['priorities'] for fact in item['facts'])


@pytest.mark.parametrize('changes,field,code', [
    ({'affected_plants':21}, 'inspection_counts','affected_exceeds_inspected'),
    ({'affected_plants':None}, 'inspection_counts','incomplete_counts'),
    ({'inspected_plants':None}, 'inspection_counts','incomplete_counts'),
    ({'affected_plants':-1}, 'affected_plants','invalid_count'),
    ({'affected_plants':'1.2'}, 'affected_plants','invalid_count'),
    ({'affected_plants':True}, 'affected_plants','invalid_count'),
    ({'affected_plants':1.0}, 'affected_plants','invalid_count'),
    ({'inspected_plants':1_000_001}, 'inspected_plants','out_of_range'),
    ({'waterlogging':'false'}, 'waterlogging','invalid_boolean'),
    ({'pest_present':1}, 'pest_present','invalid_boolean'),
    ({'moisture':'soaked'}, 'moisture','invalid_choice'),
    ({'leaf_symptoms':'late_blight'}, 'leaf_symptoms','invalid_choice'),
    ({'notes':3}, 'notes','invalid_text'),
    ({'notes':'a'*2001}, 'notes','invalid_text'),
])
def test_invalid_observations_cannot_generate_advice(changes, field, code):
    with pytest.raises(AdvisoryInputError) as error:
        report(observation=changes)
    assert error.value.field == field and error.value.code == code


@pytest.mark.parametrize('amount', ['NaN','Infinity','-Infinity',float('nan'),float('inf'),-0.1,1000.01,True,[]])
def test_rain_requires_bounded_finite_measurement(amount):
    with pytest.raises(AdvisoryInputError):
        report(observation={'recent_rain_mm':amount})


@pytest.mark.parametrize('amount', [None,'',0,'0',Decimal('1000')])
def test_unknown_and_boundary_rain_measurements(amount):
    value = report(observation={'recent_rain_mm':amount})
    assert value['facts']['observation']['recent_rain_mm'] is None if amount in (None,'') else value['facts']['observation']['recent_rain_mm'] == float(amount)


def test_fresh_sourced_weather_can_prompt_checks_but_not_water_or_yield_predictions():
    value = report(weather=weather())
    assert 'heat_check' in codes(value) and 'wind_check' in codes(value)
    assert not ({'current_weather','weather_refresh'} & set(value['missing_data']))
    assert value['facts']['weather']['source'] == 'OpenWeatherMap'
    heat = next(item for item in value['priorities'] if item['code']=='heat_check')
    assert 'not a crop-damage forecast' in heat['reason']
    assert all(item['code'] != 'dry_soil' for item in value['priorities'])
    assert value['facts']['observation']['recent_rain_mm'] == 0


@pytest.mark.parametrize('change', [
    {'source':''}, {'source':None}, {'observed_at':None},
    {'observed_at':'2026-10-28T07:00:00'},
    {'observed_at':(NOW-timedelta(hours=3, seconds=1)).isoformat()},
    {'observed_at':(NOW+timedelta(minutes=11)).isoformat()},
    {'temp':'NaN'}, {'temp':100}, {'wind_speed':float('inf')}, {'humidity':-1},
])
def test_stale_unattributed_and_malformed_weather_never_drives_heat_or_wind_advice(change):
    value = report(weather=weather(**change))
    assert not {'heat_check','wind_check'} & set(codes(value))
    assert value['facts']['weather'] is None
    assert 'weather_refresh' in value['missing_data']


def test_weather_trigger_boundaries_and_observation_age_are_explicit():
    low = report(weather=weather(temp=34.9,wind_speed=4.99))
    assert not {'heat_check','wind_check'} & set(codes(low))
    at = report(weather=weather(temp=35,wind_speed=5,observed_at=(NOW-timedelta(hours=3)).isoformat()))
    assert {'heat_check','wind_check'} <= set(codes(at))
    assert at['facts']['weather']['age_minutes'] == 180


def test_stage_work_changes_with_the_recorded_crop_stage():
    stage_codes = {'sowing':'establishment_check','vegetative':'growth_check','flowering':'flowering_check',
                   'fruiting':'fruiting_check','harvest':'harvest_plan','unknown':'confirm_stage'}
    for stage, expected in stage_codes.items():
        value = report(context={'stage':stage})
        assert expected in codes(value)
        assert not (set(stage_codes.values())-{expected}) & set(codes(value))
        assert all(0 <= item['due_in_days'] <= 7 for item in value['priorities'])


def test_planting_day_uses_indian_calendar_and_rejects_future_or_bad_dates():
    india_midnight = datetime(2026,10,27,19,tzinfo=timezone.utc)
    value = report(context={'planting_date':'2026-10-28'},now=india_midnight)
    assert value['facts']['days_since_planting'] == 0
    for invalid in ['2026-10-29','2026-02-30','28/10/2026']:
        with pytest.raises(AdvisoryInputError):
            report(context={'planting_date':invalid},now=india_midnight)


def test_input_and_catalog_values_cannot_be_mutated_by_reports_or_localization():
    context, observation = deepcopy(CONTEXT), deepcopy(OBSERVATION)
    before = deepcopy((context, observation))
    first = analyze_context(context,observation,now=NOW)
    assert (context,observation) == before
    original_title = first['priorities'][0]['localized']['mr']['title']
    first['priorities'][0]['localized']['mr']['title'] = 'Changed'
    first['evidence'][0]['localized_note']['mr'] = 'Changed'
    second = analyze_context(context,observation,now=NOW)
    assert second['priorities'][0]['localized']['mr']['title'] == original_title
    assert second['evidence'][0]['localized_note']['mr'] != 'Changed'
    localized = localize_priority(second['priorities'][0],'unsupported')
    assert localized == second['priorities'][0]['localized']['en']
    localized['title'] = 'Changed'
    assert second['priorities'][0]['title'] != 'Changed'


def test_same_inputs_have_deterministic_order_and_sources_are_valid_references():
    one = report(observation={'waterlogging':True,'moisture':'wet','pest_present':True,'leaf_symptoms':'wilting'},weather=weather())
    two = report(observation={'waterlogging':True,'moisture':'wet','pest_present':True,'leaf_symptoms':'wilting'},weather=weather())
    assert one == two
    assert len(codes(one)) == len(set(codes(one)))
    priorities = one['priorities']
    urgent_positions = [i for i,item in enumerate(priorities) if item['severity']=='urgent']
    assert urgent_positions == list(range(len(urgent_positions)))
    for item in priorities:
        assert set(item['sources']) <= SOURCES.keys()
        for language in ('en','hi','mr'):
            assert all(localize_priority(item,language).values())
    for message in MESSAGES.values():
        assert set(message) == {'en','hi','mr'}

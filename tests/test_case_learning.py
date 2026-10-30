"""Actual farmer history drives retrieval; no generated diagnoses or outcomes."""
from copy import deepcopy

import pytest

from advisory.learning import MAX_HISTORY, retrieve_cases


CONTEXT = {'crop': 'tomato', 'stage': 'flowering', 'soil': 'loamy', 'irrigation': 'drip'}
OBSERVATION = {'moisture': 'dry', 'pest_present': False, 'waterlogging': False,
               'leaf_symptoms': 'wilting', 'affected_plants': 5, 'inspected_plants': 50,
               'notes': 'Leaves wilt in the afternoon near the blocked drip line'}


def case(identifier, *, context=None, observation=None, verdict='improved', recorded_at=None):
    return {'id': identifier, 'field_context': context or deepcopy(CONTEXT),
            'observation': observation or deepcopy(OBSERVATION), 'verdict': verdict,
            'recorded_at': recorded_at or f'2026-10-{min(identifier, 28):02d}T12:00:00+00:00',
            'report': {'priorities': [{'code':'check_drip','title':'Check the drip line',
                                     'action':'Check for blockage', 'localized':{
                                         'mr': {'title':'ठिबक तपासा','reason':'पानांची पाहणी करा','action':'अडथळा तपासा'}}}]}}


def test_similar_real_case_ranks_above_unrelated_notes_and_conditions():
    unrelated = case(2, context=CONTEXT | {'stage':'harvest','soil':'clay'}, observation={
        'moisture':'wet','pest_present':True,'waterlogging':True,'leaf_symptoms':'spots',
        'notes':'Rain standing in the field and insects on damaged fruit'})
    matching = case(1)
    result = retrieve_cases(CONTEXT, OBSERVATION, [unrelated, matching])
    assert result['status'] == 'matched'
    assert result['cases'][0]['id'] == 1
    assert 'same_moisture' in result['cases'][0]['match_facts']
    assert result['cases'][0]['previous_actions'][0]['code'] == 'check_drip'
    assert result['cases'][0]['previous_actions'][0]['localized']['mr']['title'] == 'ठिबक तपासा'
    assert not any(key in result['cases'][0] for key in ('accuracy','confidence','diagnosis','prediction'))


@pytest.mark.parametrize('query,matching,other', [
    ('ठिबक नळी बंद पडली पानांना दुपारी मरगळ', 'ठिबक नळी बंद पडल्याने पानांना मरगळ', 'बाजारात टोमॅटो विक्री वाहतूक खर्च'),
    ('पत्तियाँ दोपहर में मुरझाती हैं पानी की नली बंद', 'पानी की नली बंद और पत्तियाँ मुरझाती हैं', 'टमाटर बिक्री और बाजार का खर्च'),
])
def test_multilingual_character_tfidf_learns_history_vocabulary(query, matching, other):
    context = {'crop':'tomato'}
    result = retrieve_cases(context, {'notes':query}, [
        case(1, context=context, observation={'notes':matching}),
        case(2, context=context, observation={'notes':other}),
    ])
    assert result['cases'][0]['id'] == 1
    assert 'similar_notes' in result['cases'][0]['match_facts']


def test_structured_context_works_without_notes_and_outcomes_do_not_bias_similarity():
    query = OBSERVATION | {'notes':''}
    result = retrieve_cases(CONTEXT, query, [
        case(1, observation=query, verdict='worse'),
        case(2, observation=query | {'moisture':'wet','leaf_symptoms':'spots'}, verdict='improved'),
    ])
    assert result['cases'][0]['id'] == 1
    assert result['cases'][0]['verdict'] == 'worse'
    assert result['cases'][0]['note'] == ''


def test_only_same_crop_actual_history_is_used_and_current_case_is_excluded():
    history = [case(1), case(2, context=CONTEXT | {'crop':'cotton'}), case(3)]
    result = retrieve_cases(CONTEXT, OBSERVATION, history, exclude_id=3)
    assert result['history_count'] == 1
    assert [record['id'] for record in result['cases']] == [1]


@pytest.mark.parametrize('history', [None, [], 'bad', {}, [None, 'bad', 5],
                                     [{'id':True,'field_context':CONTEXT,'observation':OBSERVATION}]])
def test_missing_or_malformed_history_never_generates_a_case(history):
    result = retrieve_cases(CONTEXT, OBSERVATION, history)
    assert result['status'] == 'no_history'
    assert result['cases'] == []


@pytest.mark.parametrize('context', [None, [], {}, {'crop':'other'}, {'crop':'unknown'}])
def test_crop_context_is_required(context):
    result = retrieve_cases(context, OBSERVATION, [case(1)])
    assert result['status'] == 'invalid_context'
    assert result['cases'] == []


def test_malformed_counts_and_empty_information_remain_safe():
    context = {'crop':'tomato'}
    query = {'affected_plants':float('nan'),'inspected_plants':float('inf'),'notes':None}
    result = retrieve_cases(context, query, [case(1, context=context, observation={
        'affected_plants':9,'inspected_plants':2,'notes':None})])
    assert result['status'] == 'no_matches'
    assert result['cases'] == []


def test_history_is_bounded_and_recent_cases_are_retained():
    history = [case(index, recorded_at=f'2026-10-28T12:{index//60%60:02d}:{index%60:02d}+00:00') for index in range(1, 701)]
    result = retrieve_cases(CONTEXT, OBSERVATION, history, limit=100)
    assert result['history_count'] == MAX_HISTORY
    assert len(result['cases']) == 5
    assert min(record['id'] for record in result['cases']) > 200


def test_retrieval_deduplicates_cases_and_leaves_input_unchanged():
    history = [case(1), case(1), case(2)]
    original = deepcopy(history)
    first = retrieve_cases(CONTEXT, OBSERVATION, history)
    second = retrieve_cases(CONTEXT, OBSERVATION, history)
    assert history == original
    assert first == second
    assert len({row['id'] for row in first['cases']}) == len(first['cases']) == 2


def test_incidence_similarity_is_context_evidence_not_a_disease_label():
    result = retrieve_cases(CONTEXT, OBSERVATION, [case(1, observation=OBSERVATION | {
        'affected_plants':10,'inspected_plants':100})])
    assert 'similar_incidence' in result['cases'][0]['match_facts']
    assert result['cases'][0]['verdict'] == 'improved'


@pytest.mark.parametrize('invalid', [float('nan'), float('inf'), 10 ** 1000, -1, True, '5', {'value': 5}])
def test_invalid_counts_never_become_zero_incidence_evidence(invalid):
    query = OBSERVATION | {'affected_plants': invalid}
    result = retrieve_cases(CONTEXT, query, [case(1)])
    assert result['cases'][0]['id'] == 1
    assert 'similar_incidence' not in result['cases'][0]['match_facts']


def test_tied_matches_prefer_recorded_recency_not_larger_identifier():
    result = retrieve_cases(CONTEXT, OBSERVATION, [
        case(99, recorded_at='2025-01-01T12:00:00Z'),
        case(1, recorded_at='2026-10-28T12:00:00Z'),
    ])
    assert result['cases'][0]['id'] == 1

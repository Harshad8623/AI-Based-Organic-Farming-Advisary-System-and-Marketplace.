"""Retrieve similar *recorded* farm cases locally, without inventing advice.

This is case-based retrieval, not a disease classifier or a prediction of whether
an action will work. The caller must supply only the current farmer's history.
Feedback is shown as that farmer's observation; it is never a training label for
agronomic efficacy and does not override the current expert-system priorities.
"""
from collections.abc import Mapping
from datetime import datetime, timezone
from itertools import islice
import math
import unicodedata


MAX_HISTORY = 500
MAX_SCAN = 2000
MAX_NOTE_LENGTH = 1000
_METHOD = 'tfidf_cosine_case_retrieval'
_UNKNOWN = {'', 'unknown', 'not_known'}
_WEIGHTS = {'stage': 2.0, 'soil': 1.0, 'irrigation': .8, 'moisture': 2.5,
            'pest_present': 1.8, 'waterlogging': 2.5, 'leaf_symptoms': 2.0}


def _text(value, length):
    return value.strip()[:length] if isinstance(value, str) else ''


def _category(value):
    value = ' '.join(unicodedata.normalize('NFKC', _text(value, 80)).casefold().split())
    return '' if value in _UNKNOWN else value


def _incidence(observation):
    values = []
    for name in ('affected_plants', 'inspected_plants'):
        value = observation.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        if not 0 <= value <= 1_000_000 or not math.isfinite(value) or not float(value).is_integer():
            return None
        values.append(value)
    affected, inspected = values
    return affected / inspected if inspected > 0 and affected <= inspected else None


def _values(context, observation):
    result = {name: _category(context.get(name)) for name in ('stage', 'soil', 'irrigation')}
    result.update({name: _category(observation.get(name)) for name in ('moisture', 'leaf_symptoms')})
    for name in ('pest_present', 'waterlogging'):
        value = observation.get(name)
        result[name] = ('yes' if value else 'no') if isinstance(value, bool) else ''
    result['incidence'] = _incidence(observation)
    return result


def _features(values):
    result = {f'{name}={values[name]}': weight for name, weight in _WEIGHTS.items() if values[name]}
    if values['incidence'] is not None:
        # Two complementary dimensions retain distance between low and high
        # incidence without inventing disease/severity cutoffs.
        result['affected_fraction'] = 2 * values['incidence']
        result['unaffected_fraction'] = 2 * (1 - values['incidence'])
    return result


def _recorded_at(value):
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and len(value) <= 50:
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return ''
    else:
        return ''
    try:
        return parsed.replace(tzinfo=timezone.utc).isoformat() if parsed.tzinfo is None else parsed.astimezone(timezone.utc).isoformat()
    except (ValueError, OverflowError):
        return ''


def _actions(report):
    if not isinstance(report, Mapping) or not isinstance(report.get('priorities'), list):
        return []
    result = []
    for priority in report['priorities'][:10]:
        if not isinstance(priority, Mapping) or not isinstance(priority.get('code'), str):
            continue
        item = {key: _text(priority.get(key), limit) for key, limit in
                [('code', 80), ('title', 200), ('action', 600)]}
        localized = priority.get('localized')
        item['localized'] = {
            lang: {key: _text(localized[lang].get(key), 600) for key in ('title', 'reason', 'action')}
            for lang in ('en', 'hi', 'mr')
            if isinstance(localized, Mapping) and isinstance(localized.get(lang), Mapping)
        }
        result.append(item)
        if len(result) == 3:
            break
    return result


def retrieve_cases(field_context, observation, history, limit=3, exclude_id=None):
    """Find up to five same-crop historical cases using local TF-IDF/cosine ML.

    ``history`` must already be owner-filtered and preferably newest first. At
    most 2,000 supplied records are inspected; the newest 500 valid same-crop
    records are used. The current observation must be excluded with its ID.
    The result contains only actual supplied case IDs, notes and prior actions.
    """
    output = {'method': _METHOD, 'status': 'invalid_context', 'history_count': 0, 'cases': []}
    if not isinstance(field_context, Mapping) or not isinstance(observation, Mapping):
        return output
    crop = _category(field_context.get('crop'))
    if not crop or crop == 'other':
        return output
    limit = min(5, max(1, limit)) if isinstance(limit, int) and not isinstance(limit, bool) else 3
    if isinstance(history, (str, bytes, Mapping)) or history is None:
        output['status'] = 'no_history'
        return output
    try:
        supplied = islice(iter(history), MAX_SCAN)
    except TypeError:
        output['status'] = 'no_history'
        return output
    records = {}
    for item in supplied:
        if not isinstance(item, Mapping):
            continue
        identifier = item.get('id')
        context, previous = item.get('field_context'), item.get('observation')
        if (isinstance(identifier, bool) or not isinstance(identifier, int) or identifier <= 0 or
                identifier == exclude_id or not isinstance(context, Mapping) or not isinstance(previous, Mapping) or
                _category(context.get('crop')) != crop):
            continue
        candidate = {'id': identifier, 'context': context, 'observation': previous,
                     'recorded_at': _recorded_at(item.get('recorded_at')),
                     'verdict': item.get('verdict') if item.get('verdict') in ('improved', 'unchanged', 'worse') else None,
                     'report': item.get('report')}
        if identifier not in records or candidate['recorded_at'] > records[identifier]['recorded_at']:
            records[identifier] = candidate
    records = sorted(records.values(), key=lambda row: (row['recorded_at'], row['id']), reverse=True)[:MAX_HISTORY]
    output['history_count'] = len(records)
    output['status'] = 'no_history'
    if not records:
        return output

    # Imports are deferred so showing an empty first-use page does not load the
    # scientific stack or require a model artifact/cache file.
    from scipy.sparse import csr_matrix, hstack
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import normalize

    current = _values(field_context, observation)
    values = [_values(record['context'], record['observation']) for record in records]
    structured = DictVectorizer().fit_transform([_features(current)] + [_features(value) for value in values])
    if structured.shape[1]:
        structured = normalize(structured) * .8
    notes = [_text(record['observation'].get('notes'), MAX_NOTE_LENGTH) for record in records]
    current_note = _text(observation.get('notes'), MAX_NOTE_LENGTH)
    text_features = csr_matrix((len(records) + 1, 0))
    note_similarities = [0.] * len(records)
    try:
        vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4),
                                     max_features=6000, sublinear_tf=True)
        historical_text = vectorizer.fit_transform(notes)
        target_text = vectorizer.transform([current_note])
        text_features = hstack([target_text.T, historical_text.T]).T.tocsr() * .65
        note_similarities = (historical_text @ target_text.T).toarray().ravel()
    except ValueError:
        # Empty/one-character notes leave structured-context retrieval usable.
        pass
    matrix = hstack([structured, text_features], format='csr')
    output['status'] = 'no_matches'
    if matrix.shape[1] == 0:
        return output
    matrix = normalize(matrix)
    nearest = NearestNeighbors(n_neighbors=len(records), metric='cosine', algorithm='brute')
    nearest.fit(matrix[1:])
    distances, indices = nearest.kneighbors(matrix[:1])
    ranked = sorted(zip(distances[0], indices[0]), key=lambda pair:
                    (round(float(pair[0]), 12), int(pair[1])))
    for distance, index in ranked:
        index = int(index)
        if not math.isfinite(float(distance)) or 1 - float(distance) < .25:
            continue
        record, previous = records[index], values[index]
        facts = ['same_crop']
        facts.extend('same_' + name for name in _WEIGHTS if current[name] and current[name] == previous[name])
        if current['incidence'] is not None and previous['incidence'] is not None and abs(current['incidence'] - previous['incidence']) <= .1:
            facts.append('similar_incidence')
        if float(note_similarities[index]) >= .2:
            facts.append('similar_notes')
        if len(facts) == 1:
            continue
        output['cases'].append({
            'id': record['id'], 'recorded_at': record['recorded_at'], 'verdict': record['verdict'],
            'match_facts': facts, 'note': _text(record['observation'].get('notes'), 240),
            'previous_actions': _actions(record['report']),
        })
        if len(output['cases']) == limit:
            break
    if output['cases']:
        output['status'] = 'matched'
    return output

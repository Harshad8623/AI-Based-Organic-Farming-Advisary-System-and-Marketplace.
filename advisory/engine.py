"""Explainable field checks from actual observations, without cloud inference.

This is a local expert system, not a trained crop diagnosis or yield model.
Observation review triggers (including heat/wind) are conservative application
prompts; they are not validated economic thresholds or treatment prescriptions.
"""
from collections.abc import Mapping
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import math
import re
from zoneinfo import ZoneInfo

from .catalog import CROPS, STAGES, SOILS, IRRIGATION, MOISTURE, LEAF_SYMPTOMS, SOURCES, priority_copy

VERSION = 'field-observation-rules-1'


class AdvisoryInputError(ValueError):
    def __init__(self, field, code='invalid_value'):
        self.field, self.code = field, code
        super().__init__(code)


def _choice(value, choices, field, default):
    if value is None or value == '':
        return default
    if not isinstance(value, str) or value not in choices:
        raise AdvisoryInputError(field, 'invalid_choice')
    return value


def _boolean(value, field):
    if not isinstance(value, bool):
        raise AdvisoryInputError(field, 'invalid_boolean')
    return value


def _number(value, field, lower, upper):
    if value is None or value == '':
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise AdvisoryInputError(field, 'invalid_number')
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise AdvisoryInputError(field, 'invalid_number') from None
    if not number.is_finite() or not Decimal(str(lower)) <= number <= Decimal(str(upper)):
        raise AdvisoryInputError(field, 'out_of_range')
    return float(number)


def _count(value, field):
    if value is None or value == '':
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not re.fullmatch(r'\d{1,7}', str(value)):
        raise AdvisoryInputError(field, 'invalid_count')
    value = int(value)
    if value > 1_000_000:
        raise AdvisoryInputError(field, 'out_of_range')
    return value


def _planting_date(value):
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError
        return date.fromisoformat(value)
    except ValueError:
        raise AdvisoryInputError('planting_date', 'invalid_date') from None


def _fact(code, value, en, hi, mr, unit=None):
    return {'code': code, 'value': value, 'unit': unit,
            'localized': {'en': en, 'hi': hi, 'mr': mr}}


def _weather(weather, now):
    if weather is None:
        return None, 'current_weather'
    try:
        if not isinstance(weather, Mapping):
            raise ValueError
        source = weather.get('source')
        if not isinstance(source, str) or not source.strip() or len(source) > 120:
            raise ValueError
        stamp = weather.get('observed_at')
        observed = datetime.fromisoformat(stamp.replace('Z', '+00:00')) if isinstance(stamp, str) else stamp
        if not isinstance(observed, datetime) or observed.tzinfo is None:
            raise ValueError
        age = (now - observed).total_seconds()
        if age < -600 or age > 10800:
            raise ValueError
        temp = _number(weather.get('temp'), 'weather.temp', -90, 65)
        if temp is None:
            raise ValueError
        wind = _number(weather.get('wind_speed'), 'weather.wind_speed', 0, 150)
        humidity = _number(weather.get('humidity'), 'weather.humidity', 0, 100)
        return {'temp': temp, 'wind_speed': wind, 'humidity': humidity,
                'source': source.strip(), 'observed_at': observed.isoformat(),
                'age_minutes': round(max(age, 0) / 60, 1)}, None
    except (ValueError, TypeError, OverflowError, AttributeError):
        return None, 'weather_refresh'


def localize_priority(priority, language='en'):
    """Return title/reason/action in a supported language, with English fallback."""
    selected = priority.get('localized', {}).get(language) or priority.get('localized', {}).get('en')
    return dict(selected) if selected else {key: priority.get(key, '') for key in ('title', 'reason', 'action')}


def analyze_context(field_context, observation, weather=None, *, now=None):
    if not isinstance(field_context, Mapping):
        raise AdvisoryInputError('field_context', 'invalid_object')
    if not isinstance(observation, Mapping):
        raise AdvisoryInputError('observation', 'invalid_object')
    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime):
        raise AdvisoryInputError('now', 'invalid_date')
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    today = now.astimezone(ZoneInfo('Asia/Kolkata')).date()
    crop = _choice(field_context.get('crop'), CROPS, 'crop', 'other')
    stage = _choice(field_context.get('stage'), STAGES, 'stage', 'unknown')
    soil = _choice(field_context.get('soil'), SOILS, 'soil', 'unknown')
    irrigation = _choice(field_context.get('irrigation'), IRRIGATION, 'irrigation', 'other')
    area = _number(field_context.get('area_m2'), 'area_m2', 0.01, 1_000_000_000)
    planted = _planting_date(field_context.get('planting_date'))
    if planted and planted > today:
        raise AdvisoryInputError('planting_date', 'future_date')
    moisture = _choice(observation.get('moisture'), MOISTURE, 'moisture', 'unknown')
    symptoms = _choice(observation.get('leaf_symptoms'), LEAF_SYMPTOMS, 'leaf_symptoms', 'none')
    waterlogging = _boolean(observation.get('waterlogging', False), 'waterlogging')
    pests = _boolean(observation.get('pest_present', False), 'pest_present')
    affected = _count(observation.get('affected_plants'), 'affected_plants')
    inspected = _count(observation.get('inspected_plants'), 'inspected_plants')
    if (affected is None) != (inspected is None):
        raise AdvisoryInputError('inspection_counts', 'incomplete_counts')
    if affected is not None and affected > inspected:
        raise AdvisoryInputError('inspection_counts', 'affected_exceeds_inspected')
    rain = _number(observation.get('recent_rain_mm'), 'recent_rain_mm', 0, 1000)
    notes = observation.get('notes', '')
    if not isinstance(notes, str) or len(notes) > 2000:
        raise AdvisoryInputError('notes', 'invalid_text')
    incidence = round(affected * 100 / inspected, 2) if inspected else None
    current_weather, weather_missing = _weather(weather, now)
    missing = []
    if not planted:
        missing.append('planting_date')
    if stage == 'unknown':
        missing.append('growth_stage')
    if crop == 'other':
        missing.append('local_crop_guidance')
    if moisture == 'unknown':
        missing.append('moisture')
    if (symptoms != 'none' or pests) and not inspected:
        missing.append('inspection_counts')
    if weather_missing:
        missing.append(weather_missing)
    if waterlogging and crop == 'rice':
        missing.append('standing_water_depth')

    common = [
        _fact('crop', crop, 'Crop: ' + CROPS[crop]['en'], 'फसल: ' + CROPS[crop]['hi'], 'पीक: ' + CROPS[crop]['mr']),
        _fact('stage', stage, 'Recorded stage: ' + STAGES[stage]['en'], 'दर्ज अवस्था: ' + STAGES[stage]['hi'], 'नोंदीतील अवस्था: ' + STAGES[stage]['mr']),
    ]
    moisture_fact = _fact('moisture', moisture, 'Reported soil: ' + MOISTURE[moisture]['en'],
                          'दर्ज मिट्टी: ' + MOISTURE[moisture]['hi'], 'नोंदीतील माती: ' + MOISTURE[moisture]['mr'])
    symptom_fact = _fact('leaf_symptoms', symptoms, 'Leaf observation: ' + LEAF_SYMPTOMS[symptoms]['en'],
                        'पत्तों की नोंद: ' + LEAF_SYMPTOMS[symptoms]['hi'], 'पानांची नोंद: ' + LEAF_SYMPTOMS[symptoms]['mr'])
    count_facts = []
    if incidence is not None:
        count_facts.append(_fact('affected_percent', incidence,
            f'{affected} of {inspected} inspected plants marked affected ({incidence:g}%).',
            f'जाँचे गए {inspected} पौधों में {affected} प्रभावित दर्ज ({incidence:g}%)।',
            f'तपासलेल्या {inspected} झाडांपैकी {affected} बाधित नोंदली ({incidence:g}%).', '%'))
    rain_facts = []
    if rain is not None:
        rain_facts.append(_fact('recent_rain_mm', rain,
            f'Recorded recent rain: {rain:g} mm; this is not a forecast.',
            f'दर्ज हाल का वर्षा मापन: {rain:g} mm; यह पूर्वानुमान नहीं है।',
            f'अलीकडील नोंदवलेला पाऊस: {rain:g} mm; हा अंदाज नाही.', 'mm'))
    priorities = []

    def add(code, severity, category, due, supporting, sources):
        copy = priority_copy(code)
        priorities.append({'code': code, 'severity': severity, 'category': category,
            'title_key': 'field_' + code + '_title', 'reason_key': 'field_' + code + '_reason',
            'action_key': 'field_' + code + '_action', **copy['en'], 'localized': copy,
            'facts': [*common, *supporting], 'due_in_days': due, 'sources': sources})

    if waterlogging:
        code = 'paddy_excess_water' if crop == 'rice' else 'waterlogging'
        add(code, 'urgent', 'water', 0, [moisture_fact, *rain_facts], ['fao_water', 'kvk'])
        if moisture == 'dry':
            add('conflicting_moisture', 'watch', 'observation', 0, [moisture_fact], ['kvk'])
    if symptoms == 'wilting' and (moisture == 'wet' or waterlogging):
        add('wet_wilting', 'urgent', 'crop_health', 0, [moisture_fact, symptom_fact, *count_facts], ['kvk'])
    elif symptoms != 'none':
        add('leaf_check', 'watch', 'crop_health', 1, [symptom_fact, *count_facts], ['kvk'])
    if not waterlogging:
        if moisture == 'unknown':
            add('check_moisture', 'watch', 'water', 0, [moisture_fact], ['fao_water'])
        elif moisture == 'dry':
            code = 'rainfed_dry' if irrigation == 'rainfed' else 'dry_soil'
            add(code, 'watch', 'water', 0, [moisture_fact, *rain_facts], ['fao_water', 'kvk'])
        elif moisture == 'wet':
            if crop == 'rice' and irrigation == 'flood':
                add('paddy_water_check', 'routine', 'water', 1, [moisture_fact], ['icar', 'kvk'])
            else:
                add('wet_soil', 'watch', 'water', 0, [moisture_fact, *rain_facts], ['fao_water'])
    if pests:
        add('pest_scout', 'watch', 'crop_health', 1, count_facts, ['icar', 'kvk'])
    elif affected and symptoms == 'none':
        add('unexplained_damage', 'watch', 'observation', 1, count_facts, ['kvk'])
    if current_weather:
        weather_facts = [_fact('weather_source', current_weather['source'],
            'Weather source: ' + current_weather['source'], 'मौसम स्रोत: ' + current_weather['source'], 'हवामान स्रोत: ' + current_weather['source']),
            _fact('weather_observed_at', current_weather['observed_at'],
                'Weather observed: ' + current_weather['observed_at'], 'मौसम मापन: ' + current_weather['observed_at'], 'हवामान मापन: ' + current_weather['observed_at'])]
        temp = current_weather['temp']
        if temp >= 35:
            add('heat_check', 'watch', 'weather', 0,
                [*weather_facts, _fact('temperature_c', temp, f'Observed temperature: {temp:g}°C', f'मापा तापमान: {temp:g}°C', f'मोजलेले तापमान: {temp:g}°C', '°C')], ['imd'])
        wind = current_weather['wind_speed']
        if wind is not None and wind >= 5:
            add('wind_check', 'watch', 'weather', 0,
                [*weather_facts, _fact('wind_m_s', wind, f'Observed wind: {wind:g} m/s', f'मापी हवा: {wind:g} m/s', f'मोजलेला वारा: {wind:g} m/s', 'm/s')], ['imd'])
    stage_code = {'sowing':'establishment_check', 'vegetative':'growth_check',
                  'flowering':'flowering_check', 'fruiting':'fruiting_check', 'harvest':'harvest_plan',
                  'unknown':'confirm_stage'}[stage]
    add(stage_code, 'watch' if stage == 'unknown' else 'routine', 'planning', 1 if stage == 'unknown' else 3,
        [], ['icar', 'kvk'] + (['imd'] if stage == 'harvest' else []))
    order = {'urgent': 0, 'watch': 1, 'routine': 2}
    priorities.sort(key=lambda item: (order[item['severity']], item['due_in_days'], item['code']))
    counts = {key: sum(item['severity'] == key for item in priorities) for key in order}
    summary = {
        'en': f"{len(priorities)} field checks: {counts['urgent']} urgent, {counts['watch']} to watch and {counts['routine']} routine. Based on your observations, not a confirmed diagnosis.",
        'hi': f"खेत की {len(priorities)} जाँचें: {counts['urgent']} जरूरी, {counts['watch']} निगरानी और {counts['routine']} नियमित। ये आपकी नोंदों पर आधारित हैं, पक्का निदान नहीं।",
        'mr': f"शेतातील {len(priorities)} पाहण्या: {counts['urgent']} तातडीच्या, {counts['watch']} लक्ष द्यायच्या व {counts['routine']} नेहमीच्या। या तुमच्या नोंदींवर आधारित आहेत, खात्रीचे निदान नाही.",
    }
    source_ids = list(dict.fromkeys(source for item in priorities for source in item['sources']))
    return {'version': VERSION, 'method': 'local_expert_system', 'priorities': priorities,
        'missing_data': list(dict.fromkeys(missing)), 'summary': summary['en'], 'localized_summary': summary,
        'next_review_days': min(item['due_in_days'] for item in priorities),
        'evidence': [{**SOURCES[source], 'localized_note': dict(SOURCES[source]['localized_note'])} for source in source_ids],
        'facts': {'crop': crop, 'stage': stage, 'soil': soil, 'irrigation': irrigation,
            'area_m2': area, 'planting_date': planted.isoformat() if planted else None,
            'days_since_planting': (today-planted).days if planted else None,
            'observation': {'moisture': moisture, 'waterlogging': waterlogging, 'pest_present': pests,
                'affected_plants': affected, 'inspected_plants': inspected, 'affected_percent': incidence,
                'leaf_symptoms': symptoms, 'recent_rain_mm': rain}, 'weather': current_weather}}

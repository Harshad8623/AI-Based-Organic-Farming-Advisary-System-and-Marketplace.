"""Agricultural guidance must be bounded, attributable and honest about availability."""
from datetime import datetime, timezone, timedelta
from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
import requests
from PIL import Image
from flask import template_rendered
from werkzeug.datastructures import MultiDict

from models import User, db
from routes import weather, crop_recommendation, disease_detection
from ml_models import disease_model, plant_disease_cnn


@pytest.fixture
def farmer(app, client):
    with app.app_context():
        user = User(name='Farmer', email='farmer@example.com', password='unused', role='farmer')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True
    return user_id


def image_bytes(size=(64, 64), fmt='PNG'):
    buffer = BytesIO()
    Image.new('RGB', size, (40, 140, 70)).save(buffer, format=fmt)
    buffer.seek(0)
    return buffer


def context_for(app, action):
    contexts = []
    def capture(sender, template, context, **extra):
        contexts.append(context)
    with template_rendered.connected_to(capture, app):
        response = action()
    assert contexts
    return response, contexts[-1]


def observation(**changes):
    payload = {
        'dt': datetime.now(timezone.utc).timestamp(), 'name': 'Aurangabad',
        'sys': {'country':'IN'}, 'main': {'temp':31, 'feels_like':32, 'humidity':81},
        'weather': [{'description':'light rain'}], 'wind':{'speed':6}, 'rain':{'1h':1.2},
    }
    payload.update(changes)
    return payload


class WeatherResponse:
    def __init__(self, data, status=200):
        self.data, self.status_code = data, status
    def json(self):
        return self.data
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError('upstream error')


def test_advisory_pages_require_login(client):
    for path in ['/weather/', '/crop/', '/disease/']:
        assert client.get(path).status_code == 302


def test_weather_without_key_never_calls_network_or_invents_values(app, client, farmer, monkeypatch):
    monkeypatch.setattr(weather.requests, 'get', lambda *a, **k: pytest.fail('No API key must not make requests'))
    response, context = context_for(app, lambda: client.get('/weather/?city=Pune'))
    assert response.status_code == 200
    assert context['weather'] is None
    assert context['weather_error'] == 'weather_unavailable'
    assert b'weather_unavailable' in response.data
    assert b'Rain Probability' not in response.data


def test_real_weather_has_units_source_timestamp_and_no_forecast(app, client, farmer, monkeypatch):
    app.config['OPENWEATHER_API_KEY'] = 'test-key'
    calls=[]
    def get(url, **kwargs):
        calls.append((url, kwargs))
        return WeatherResponse(observation())
    monkeypatch.setattr(weather.requests, 'get', get)
    response, context = context_for(app, lambda: client.get('/weather/?city=Sambhajinagar'))
    assert response.status_code == 200
    actual = context['weather']
    assert actual['temp'] == 31
    assert actual['rain_mm'] == 1.2
    assert actual['source'] == 'OpenWeatherMap'
    assert actual['observed_at']
    assert 'rain_probability' not in actual
    assert 'advice_wind' in context['tips']
    assert 'advice_humid' in context['tips']
    assert calls[0][1]['params']['q'] == 'Aurangabad,IN'
    assert calls[0][1]['params']['units'] == 'metric'
    assert calls[0][1]['timeout'] <= 12
    assert b'not a forecast or a rain probability' in response.data
    assert b'test-key' not in response.data


@pytest.mark.parametrize('bad_data', [None, [], {}, {'rain':[]}, {'rain':'none'},
    {'main': {'temp':'nan','feels_like':30,'humidity':50}},
    {'main': {'temp':25,'feels_like':30,'humidity':101}},
    {'wind':{'speed':float('inf')}}, {'weather':[]},
    {'dt': (datetime.now(timezone.utc)-timedelta(hours=5)).timestamp()},
    {'dt': (datetime.now(timezone.utc)+timedelta(hours=1)).timestamp()}])
def test_malformed_or_stale_weather_is_unavailable(app, client, farmer, monkeypatch, bad_data):
    app.config['OPENWEATHER_API_KEY'] = 'private-test-key'
    payload = observation(**bad_data) if isinstance(bad_data, dict) and bad_data else bad_data
    monkeypatch.setattr(weather.requests, 'get', lambda *a, **k: WeatherResponse(payload))
    response, context = context_for(app, lambda: client.get('/weather/?city=Pune'))
    assert response.status_code == 200
    assert context['weather'] is None
    assert context['weather_error'] == 'weather_request_failed'
    assert b'private-test-key' not in response.data


def test_weather_timeout_and_missing_city_recover(app, client, farmer, monkeypatch):
    app.config['OPENWEATHER_API_KEY']='test-key'
    def timeout(*a, **kw):
        raise requests.Timeout('https://upstream?appid=private-key')
    monkeypatch.setattr(weather.requests,'get',timeout)
    response, context = context_for(app, lambda: client.get('/weather/?city=Pune'))
    assert context['weather_error'] == 'weather_request_failed'
    assert b'private-key' not in response.data
    response, context = context_for(app, lambda: client.get('/weather/?city='+'x'*121))
    assert context['weather_error'] == 'weather_city_invalid'


BASE_INPUT = {'N':'80','P':'45','K':'40','temperature':'25','humidity':'65','ph':'6.5','rainfall':'150'}


@pytest.mark.parametrize('name,value', [('N','nan'),('N','inf'),('P','-1'),('K','301'),
    ('temperature','56'),('humidity','101'),('humidity','-1'),('ph','14.1'),('ph','-0.1'),
    ('rainfall','501'),('rainfall',''),('N','1'*31),('K','nonsense')])
def test_crop_validation_rejects_invalid_input_before_model(app, client, farmer, monkeypatch, name, value):
    monkeypatch.setattr(crop_recommendation,'_get_model',lambda:pytest.fail('Invalid input must not train or run a model'))
    response = client.post('/crop/',data=BASE_INPUT | {name:value})
    assert response.status_code == 400
    assert b'crop_invalid_values' in response.data


def test_crop_bounds_and_finite_validated_vector():
    lower = {name:str(minimum) for name,_,minimum,_,_ in crop_recommendation.INPUT_FIELDS}
    upper = {name:str(maximum) for name,_,_,maximum,_ in crop_recommendation.INPUT_FIELDS}
    for values in [lower,upper,BASE_INPUT]:
        array = crop_recommendation._validated_features(MultiDict(values))
        assert array.shape == (1,7)
        assert np.isfinite(array).all()


def test_crop_success_labels_demonstration_without_accuracy_claim(app, client, farmer, monkeypatch):
    class Model:
        def predict(self, features):
            assert features.shape == (1,7)
            return [0]
    class Encoder:
        def inverse_transform(self, labels):
            return ['rice']
    monkeypatch.setattr(crop_recommendation,'_get_model',lambda:(Model(),Encoder()))
    response = client.post('/crop/',data=BASE_INPUT)
    assert response.status_code == 200
    assert b'Rice' in response.data
    assert b'Learning tool' in response.data
    assert b'synthetic data' in response.data
    assert b'not verified field trials' in response.data
    assert b'95%' not in response.data
    assert b'99%' not in response.data


def test_crop_model_failure_is_recoverable(app, client, farmer, monkeypatch):
    def unavailable():
        raise RuntimeError('training failed')
    monkeypatch.setattr(crop_recommendation,'_get_model',unavailable)
    response = client.post('/crop/',data=BASE_INPUT)
    assert response.status_code == 503
    assert b'crop_temporarily_unavailable' in response.data


def test_demonstration_can_train_and_predict_with_installed_dependencies():
    # Exercises real pandas/scikit-learn dependencies while making no field-accuracy claim.
    model, encoder = crop_recommendation._get_model()
    features = crop_recommendation._validated_features(MultiDict(BASE_INPUT))
    label = str(encoder.inverse_transform(model.predict(features))[0])
    assert label in crop_recommendation.CROP_TIPS


@pytest.mark.parametrize('filename,content', [
    ('leaf.jpg',lambda:BytesIO(b'<script>alert(1)</script>')),
    ('leaf.png',lambda:BytesIO(b'not a PNG')),
    ('leaf.gif',lambda:image_bytes(fmt='GIF')),
    ('leaf.jpg',lambda:image_bytes(size=(8,8))),
    ('leaf.png',lambda:image_bytes(fmt='GIF')),
])
def test_leaf_rejects_fake_or_unsupported_images(app, client, farmer, monkeypatch, filename, content):
    monkeypatch.setattr(disease_model,'predict_disease',lambda *a,**k:pytest.fail('Invalid image must not reach predictor'))
    response = client.post('/disease/', data={'leaf_image':(content(),filename)},content_type='multipart/form-data')
    assert response.status_code == 200
    assert b'leaf_invalid_image' in response.data


def test_leaf_decodes_strips_metadata_and_removes_private_file(app, client, farmer, monkeypatch):
    captured=[]
    def predict(path, **kw):
        captured.append(path)
        with Image.open(path) as image:
            assert image.format == 'JPEG'
            assert image.mode == 'RGB'
            assert not image.getexif()
        return {'available':False,'confidence':None}
    monkeypatch.setattr(disease_model,'predict_disease',predict)
    response = client.post('/disease/', data={'leaf_image':(image_bytes(),'leaf.png')},content_type='multipart/form-data')
    assert response.status_code == 200
    assert b'No disease has been identified' in response.data
    assert b'data:image/jpeg;base64,' in response.data
    assert captured and not Path(captured[0]).exists()
    assert list(Path(app.config['UPLOAD_FOLDER']).iterdir()) == []


def test_leaf_cleans_up_even_if_analysis_fails(app, client, farmer, monkeypatch):
    captured=[]
    def predict(path, **kw):
        captured.append(path)
        raise RuntimeError('service unavailable')
    monkeypatch.setattr(disease_model,'predict_disease',predict)
    response = client.post('/disease/', data={'leaf_image':(image_bytes(),'leaf.webp')},content_type='multipart/form-data')
    assert b'leaf_service_error' in response.data
    assert captured and not Path(captured[0]).exists()


def test_leaf_limits_decoded_pixels_and_bytes(monkeypatch):
    monkeypatch.setattr(disease_detection,'MAX_PIXELS',1000)
    with pytest.raises(ValueError):
        disease_detection._validated_image(image_bytes())
    monkeypatch.setattr(disease_detection,'MAX_IMAGE_BYTES',10)
    with pytest.raises(ValueError):
        disease_detection._validated_image(image_bytes())


def test_unconfigured_disease_analysis_never_invents_label(tmp_path, monkeypatch):
    monkeypatch.setattr(plant_disease_cnn,'cnn_available',lambda:False)
    for name in ['leaf-one.jpg','leaf-two.jpg']:
        result = disease_model.predict_disease(str(tmp_path/name),api_key='')
        assert result['available'] is False
        assert result['name'] == 'Analysis unavailable'
        assert result['confidence'] is None
        assert result['severity'] == 'unknown'
    assert disease_model.get_disease_by_name('not a disease') is None


def test_disease_upstream_failure_never_leaks_secret_or_prescribes(tmp_path, monkeypatch):
    monkeypatch.setattr(plant_disease_cnn,'cnn_available',lambda:False)
    def timeout(*a,**kw):
        raise requests.Timeout('https://upstream?key=private-key')
    monkeypatch.setattr(disease_model,'_gemini_vision_predict',timeout)
    result=disease_model.predict_disease('unused.jpg',api_key='private-key')
    assert result['available'] is False
    assert 'private-key' not in str(result)


def test_disease_analysis_remains_tentative_and_uses_safe_triage(monkeypatch):
    monkeypatch.setattr(plant_disease_cnn,'cnn_available',lambda:False)
    monkeypatch.setattr(disease_model,'_gemini_vision_predict',lambda *a,**kw:{'name':'Late Blight','symptoms':'dark spots','organic_solutions':['invented dose'],'severity':'high'})
    result=disease_model.predict_disease('unused.jpg',api_key='test-key')
    assert result['available'] is True
    assert result['tentative'] is True
    assert result['engine'] == 'Gemini Vision'
    assert result['organic_solutions'] == disease_model.TRIAGE_STEPS
    assert 'invented dose' not in str(result)


def test_vision_request_is_bounded_and_malformed_text_is_unavailable(tmp_path,monkeypatch):
    file=tmp_path/'leaf.jpg'
    file.write_bytes(image_bytes(fmt='JPEG').read())
    calls=[]
    class Response:
        status_code=200
        def json(self):
            return {'candidates':[{'content':{'parts':[{'text':'unstructured provider garbage'}]}}]}
    def post(url,**kwargs):
        calls.append(kwargs)
        return Response()
    monkeypatch.setattr(requests,'post',post)
    monkeypatch.setattr(plant_disease_cnn,'cnn_available',lambda:False)
    result=disease_model.predict_disease(str(file),api_key='test-key')
    assert result['available'] is False
    assert len(calls) == 1
    assert calls[0]['timeout'] <= 12


@pytest.mark.parametrize('rain', [None, {}, {'3h': 6.5}])
def test_unreported_hourly_rain_is_unknown_not_zero(app, client, farmer, monkeypatch, rain):
    app.config['OPENWEATHER_API_KEY'] = 'test-key'
    monkeypatch.setattr(weather.requests, 'get', lambda *a, **k: WeatherResponse(observation(rain=rain)))
    response, context = context_for(app, lambda: client.get('/weather/?city=Pune'))
    assert context['weather']['rain_mm'] is None
    assert b'weather_not_reported' in response.data
    assert 'advice_rain' in context['tips']


def test_reported_zero_rain_is_distinct_from_missing_rain(app, client, farmer, monkeypatch):
    app.config['OPENWEATHER_API_KEY'] = 'test-key'
    monkeypatch.setattr(weather.requests, 'get', lambda *a, **k: WeatherResponse(observation(rain={'1h':0})))
    response, context = context_for(app, lambda: client.get('/weather/?city=Pune'))
    assert context['weather']['rain_mm'] == 0
    assert b'0.0 mm' in response.data
    assert b'weather_not_reported' not in response.data
    assert context['weather']['observed_label'].endswith('IST')


@pytest.mark.parametrize('change', [
    {'main':{'temp':True,'feels_like':25,'humidity':60}},
    {'wind':{'speed':False}}, {'rain':{'1h':True}}, {'name':None},
    {'sys':{'country':{}}}, {'weather':[{'description':''}]},
])
def test_boolean_measurements_and_invalid_weather_labels_are_rejected(app, client, farmer, monkeypatch, change):
    app.config['OPENWEATHER_API_KEY'] = 'test-key'
    monkeypatch.setattr(weather.requests, 'get', lambda *a, **k: WeatherResponse(observation(**change)))
    response, context = context_for(app, lambda: client.get('/weather/?city=Pune'))
    assert context['weather'] is None
    assert context['weather_error'] == 'weather_request_failed'


def test_empty_weather_search_is_a_visible_validation_error(app, client, farmer, monkeypatch):
    monkeypatch.setattr(weather.requests, 'get', lambda *a, **k: pytest.fail('Empty city must not call provider'))
    response, context = context_for(app, lambda: client.get('/weather/?city=%20%20'))
    assert context['weather_error'] == 'weather_city_invalid'
    assert b'weather_city_invalid' in response.data


def test_weather_location_error_can_be_translated_without_english_flash(app, client, farmer, monkeypatch):
    app.config['OPENWEATHER_API_KEY'] = 'test-key'
    monkeypatch.setattr(weather.requests, 'get', lambda *a, **k: WeatherResponse({}, status=404))
    response, context = context_for(app, lambda: client.get('/weather/?city=Unknown'))
    assert context['weather_detail'] == 'weather_city_not_found'
    assert b'data-i18n="weather_city_not_found"' in response.data
    assert b'City not found. Try' not in response.data


def test_crop_planning_is_primary_and_synthetic_model_is_optional(app, client, farmer):
    response = client.get('/crop/')
    assert response.status_code == 200
    assert b'href="/my-farm' in response.data
    assert b'href="/farm-decisions' in response.data
    assert b'<details class="card card-body" id="crop-demo" >' in response.data

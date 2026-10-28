"""Request-level regressions for farming guidance and provider failure paths."""

from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from models import User, db
from routes.chatbot import LOCAL_GUIDANCE, _gemini_response


@pytest.fixture
def chat_client(app, client):
    with app.app_context():
        user = User(name='Test Farmer', email='chat@example.test', password='not-used', role='farmer')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True
    return client


def test_chat_requires_authentication(client):
    assert client.get('/chatbot/').status_code == 302
    assert client.post('/chatbot/ask', json={'question': 'soil'}).status_code == 302


@pytest.mark.parametrize('payload', [None, [], 'soil', 4, {}, {'question': None},
                                     {'question': 1}, {'question': []}, {'question': True},
                                     {'question': ''}, {'question': '  '}, {'question': 'a' * 501}])
def test_invalid_questions_return_validation_error(chat_client, payload):
    response = chat_client.post('/chatbot/ask', json=payload)
    assert response.status_code == 400
    assert response.json['source'] == 'validation'
    assert response.json['answer']


def test_malformed_json_does_not_crash(chat_client):
    response = chat_client.post('/chatbot/ask', data='{broken', content_type='application/json')
    assert response.status_code == 400


@pytest.mark.parametrize(('lang', 'question', 'topic'), [
    ('en', 'How should I plan irrigation?', 'water'),
    ('hi', 'मिट्टी का स्वास्थ्य कैसे सुधारें?', 'soil'),
    ('mr', 'खत आणि कंपोस्टचा वापर कसा ठरवावा?', 'fertilizer'),
])
def test_local_guidance_needs_no_network(chat_client, monkeypatch, lang, question, topic):
    def unexpected_network(*args, **kwargs):
        pytest.fail('Offline guidance must not contact a provider')
    monkeypatch.setattr('routes.chatbot.requests.post', unexpected_network)
    response = chat_client.post('/chatbot/ask', json={'question': question, 'lang': lang})
    assert response.status_code == 200
    assert response.json == {'answer': LOCAL_GUIDANCE[lang]['intro'] + '\n\n' + LOCAL_GUIDANCE[lang][topic],
                             'source': 'fallback', 'lang': lang}


@pytest.mark.parametrize('lang', [None, [], {}, 'xx', 42])
def test_invalid_language_safely_uses_english(chat_client, lang):
    response = chat_client.post('/chatbot/ask', json={'question': 'soil', 'lang': lang})
    assert response.status_code == 200
    assert response.json['lang'] == 'en'


def test_english_topic_matching_does_not_treat_grain_as_rain(chat_client):
    response = chat_client.post('/chatbot/ask', json={'question': 'How do I store grain?'})
    assert response.json['answer'] == LOCAL_GUIDANCE['en']['default']
    response = chat_client.post('/chatbot/ask', json={'question': 'What is soil pH?'})
    assert LOCAL_GUIDANCE['en']['soil'] in response.json['answer']


def test_validation_uses_selected_language(chat_client):
    response = chat_client.post('/chatbot/ask', json={'question': '  ', 'lang': 'mr'})
    assert response.status_code == 400
    assert response.json['answer'] == LOCAL_GUIDANCE['mr']['empty']


def test_provider_timeout_falls_back_without_exposing_credentials(app, chat_client, monkeypatch):
    app.config['GEMINI_API_KEY'] = 'private-test-value'
    provider = Mock(side_effect=requests.Timeout('https://provider?key=private-test-value'))
    monkeypatch.setattr('routes.chatbot.requests.post', provider)
    response = chat_client.post('/chatbot/ask', json={'question': 'माती', 'lang': 'mr'})
    assert response.status_code == 200
    assert response.json['source'] == 'fallback'
    assert response.json['notice'] == LOCAL_GUIDANCE['mr']['unavailable']
    assert 'private-test-value' not in response.get_data(as_text=True)
    assert provider.call_count == 1
    assert provider.call_args.kwargs['timeout'] == (3, 12)


def test_provider_output_is_labelled_and_question_is_user_data(app, chat_client, monkeypatch):
    app.config['GEMINI_API_KEY'] = 'private-test-value'
    payload = '<img src=x onerror=alert(1)>'
    provider = Mock(return_value=Mock(json=lambda: {
        'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'text': 'private reasoning', 'thought': True}, {'text': payload}]}}]
    }))
    monkeypatch.setattr('routes.chatbot.requests.post', provider)
    response = chat_client.post('/chatbot/ask', json={'question': payload, 'lang': 'hi'})
    assert response.status_code == 200
    assert response.json['answer'] == payload
    assert response.json['source'] == 'gemini'
    assert response.json['notice'] == LOCAL_GUIDANCE['hi']['ai_notice']
    assert provider.call_args.kwargs['json']['contents'] == [
        {'role': 'user', 'parts': [{'text': payload}]}]
    assert 'Respond in Hindi.' in provider.call_args.kwargs['json']['systemInstruction']['parts'][0]['text']
    assert 'private-test-value' not in provider.call_args.args[0]


@pytest.mark.parametrize('data', [None, {}, {'candidates': []},
    {'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': [{'text': 'partial treatment'}]}}]},
    {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': ''}]}}]},
    {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [None]}}]},
    {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': 'a' * 12001}]}}]},
])
def test_malformed_or_incomplete_provider_answer_uses_local_guide(app, chat_client, monkeypatch, data):
    app.config['GEMINI_API_KEY'] = 'configured-test-value'
    monkeypatch.setattr('routes.chatbot.requests.post', Mock(return_value=Mock(json=lambda: data)))
    response = chat_client.post('/chatbot/ask', json={'question': 'soil'})
    assert response.status_code == 200
    assert response.json['source'] == 'fallback'
    assert LOCAL_GUIDANCE['en']['soil'] in response.json['answer']


def test_chat_page_has_accessible_composer_and_safe_rendering(chat_client):
    response = chat_client.get('/chatbot/')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'role="log"' in html
    assert 'maxlength="500"' in html
    assert 'body.textContent = String(text)' in html
    assert 'innerHTML' not in Path('templates/chatbot/chat.html').read_text()
    assert "signal: controller.signal" in html

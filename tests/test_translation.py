"""Translation API regression tests, independent of live credentials/providers."""

import json

import pytest
import requests
from flask import Flask
from flask_login import LoginManager, UserMixin

from routes import translate as translation


@pytest.fixture
def translation_client():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY='translation-test-secret', GEMINI_API_KEY='')
    app.register_blueprint(translation.translate_bp)
    manager = LoginManager(app)

    class TestUser(UserMixin):
        id = '1'

    @manager.user_loader
    def user_loader(user_id):
        return TestUser() if user_id == '1' else None

    with app.test_client() as client:
        with client.session_transaction() as session:
            session['_user_id'] = '1'
            session['_fresh'] = True
        yield client


@pytest.mark.parametrize('payload', [
    None, [], 'text', 2, {}, {'texts': []}, {'texts': 'soil'},
    {'texts': [123]}, {'texts': [None]}, {'texts': [['nested']]},
    {'texts': ['soil'], 'target': ['hi']}, {'texts': ['soil'], 'target': 'fr'},
    {'texts': ['x'] * 101}, {'texts': ['x' * 2001]},
    {'texts': ['x' * 2000] * 11},
])
def test_malformed_batches_are_rejected(translation_client, payload):
    response = translation_client.post('/api/translate', json=payload)
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_requires_login(translation_client):
    with translation_client.session_transaction() as session:
        session.clear()
    response = translation_client.post('/api/translate', json={'texts': ['Soil'], 'target': 'hi'})
    assert response.status_code == 401


def test_no_key_reports_original_language_without_network(translation_client, monkeypatch):
    def must_not_call(*args, **kwargs):
        raise AssertionError('No key must not trigger an external API request')
    monkeypatch.setattr(translation.requests, 'post', must_not_call)
    response = translation_client.post('/api/translate', json={'texts': ['Soil'], 'target': 'hi'})
    assert response.status_code == 200
    assert response.get_json() == {
        'translations': ['Soil'], 'translated': False, 'status': 'unavailable', 'target': 'hi'
    }


def test_english_and_blank_batches_do_not_call_provider(translation_client, monkeypatch):
    def must_not_call(*args, **kwargs):
        raise AssertionError('English or blank text needs no translation')
    monkeypatch.setattr(translation, '_gemini_translate', must_not_call)
    for payload in [{'texts': ['Soil'], 'target': 'en'}, {'texts': ['', '  '], 'target': 'mr'}]:
        response = translation_client.post('/api/translate', json=payload)
        assert response.get_json()['status'] == 'original'
        assert response.get_json()['translations'] == payload['texts']


def test_preserves_blank_positions(translation_client, monkeypatch):
    def fake_translate(texts, target):
        assert texts == ['Soil', 'Water']
        assert target == 'mr'
        return ['माती', 'पाणी']
    monkeypatch.setattr(translation, '_gemini_translate', fake_translate)
    response = translation_client.post('/api/translate', json={
        'texts': ['', 'Soil', '  ', 'Water'], 'target': 'mr'
    })
    assert response.get_json()['translations'] == ['', 'माती', '  ', 'पाणी']
    assert response.get_json()['translated'] is True


@pytest.mark.parametrize('provider_result', [None, ['माती'], ['माती', 4], ['', 'पाणी']])
def test_incomplete_provider_output_never_shifts_meanings(translation_client, monkeypatch, provider_result):
    monkeypatch.setattr(translation, '_gemini_translate', lambda *args: provider_result)
    response = translation_client.post('/api/translate', json={'texts': ['Soil', 'Water'], 'target': 'mr'})
    assert response.get_json()['status'] == 'unavailable'
    assert response.get_json()['translations'] == ['Soil', 'Water']


def test_provider_uses_bounded_timeout_and_validates_json(translation_client, monkeypatch):
    translation_client.application.config['GEMINI_API_KEY'] = 'test-key'

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {'candidates': [{'content': {'parts': [{'text': json.dumps(['माती'])}]}}]}

    def fake_post(url, **kwargs):
        assert 'test-key' not in url
        assert kwargs['headers']['x-goog-api-key'] == 'test-key'
        assert kwargs['timeout'] == (3, 12)
        assert kwargs['json']['generationConfig']['responseMimeType'] == 'application/json'
        return Response()

    monkeypatch.setattr(translation.requests, 'post', fake_post)
    response = translation_client.post('/api/translate', json={'texts': ['Soil'], 'target': 'mr'})
    assert response.get_json()['translations'] == ['माती']
    assert response.get_json()['status'] == 'translated'


def test_provider_timeout_keeps_readable_originals(translation_client, monkeypatch):
    translation_client.application.config['GEMINI_API_KEY'] = 'test-key'

    def fake_post(*args, **kwargs):
        raise requests.Timeout('provider unavailable')

    monkeypatch.setattr(translation.requests, 'post', fake_post)
    response = translation_client.post('/api/translate', json={'texts': ['Soil'], 'target': 'hi'})
    assert response.status_code == 200
    assert response.get_json()['translations'] == ['Soil']
    assert response.get_json()['translated'] is False


def test_client_preserves_markup_and_ignores_stale_language_responses():
    """Exercise the asynchronous client in Node without a browser or third-party DOM."""
    import pathlib
    import shutil
    import subprocess

    node = shutil.which('node')
    if not node:
        pytest.skip('Node is needed for the translation concurrency regression')
    script = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const pending = [];
const notice = {hidden: true, textContent: ''};
const text = {data: '  Soil  ', isConnected: true, parentElement: {closest: () => null}};
const staticText = {data: 'Static label', isConnected: true, parentElement: {closest: () => ({})}};
const child = {tagName: 'STRONG'};
const root = {children: [child], nodes: [text, staticText]};
const context = vm.createContext({
  document: {
    readyState: 'loading', addEventListener: () => {},
    getElementById: () => notice,
    querySelectorAll: () => [root],
    createTreeWalker: element => {
      let index = 0;
      return {nextNode: () => element.nodes[index++] || null};
    },
  },
  NodeFilter: {SHOW_TEXT: 4},
  localStorage: {getItem: () => {throw new Error('Storage disabled');},
    setItem: () => {throw new Error('Storage disabled');}},
  AbortController,
  I18n: {t: key => key},
  fetch: (url, options) => new Promise(resolve => pending.push({resolve, options})),
});
vm.runInContext(fs.readFileSync('static/js/translate.js', 'utf8'), context);
(async () => {
  const first = vm.runInContext('DynamicTranslator.translate("hi")', context);
  assert.equal(pending.length, 1);
  const second = vm.runInContext('DynamicTranslator.translate("mr")', context);
  assert.equal(pending[0].options.signal.aborted, true);
  assert.equal(pending.length, 2);
  pending[1].resolve({ok: true, json: async () => ({translated: true, target: 'mr', translations: ['माती']})});
  await second;
  assert.equal(text.data, '  माती  ');
  pending[0].resolve({ok: true, json: async () => ({translated: true, target: 'hi', translations: ['मिट्टी']})});
  await first;
  assert.equal(text.data, '  माती  ', 'An older Hindi request must not replace Marathi');
  assert.equal(root.children[0], child, 'Nested markup must be retained');
  assert.equal(staticText.data, 'Static label', 'Static translation nodes must not be sent');
  await vm.runInContext('DynamicTranslator.translate("en")', context);
  assert.equal(text.data, '  Soil  ');
  assert.equal(notice.hidden, true);
  const unavailable = vm.runInContext('DynamicTranslator.translate("hi")', context);
  pending[2].resolve({ok: true, json: async () => ({translated: false, target: 'hi', translations: ['Soil']})});
  await unavailable;
  assert.equal(text.data, '  Soil  ');
  assert.equal(notice.textContent, 'translation_unavailable');
})().catch(error => {console.error(error); process.exitCode = 1;});
'''
    result = subprocess.run(
        [node, '-e', script],
        cwd=pathlib.Path(__file__).resolve().parents[1],
        text=True, capture_output=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr


def test_static_language_switch_works_without_storage_and_covers_core_navigation():
    """A blocked storage API must not break the farmer's language controls."""
    import pathlib
    import shutil
    import subprocess

    node = shutil.which('node')
    if not node:
        pytest.skip('Node is needed for the built-in language regression')
    script = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('static/js/i18n.js', 'utf8');
function run(storage) {
  const label = {dataset: {i18n: 'nav_home'}, children: [], textContent: 'Home'};
  const unknown = {dataset: {i18n: 'page_extension_not_loaded'}, children: [], textContent: 'Readable fallback'};
  const field = {getAttribute: () => 'register_password_ph', setAttribute(name, value) {this[name] = value;}};
  const buttons = ['en', 'hi', 'mr'].map(lang => ({
    dataset: {lang}, attributes: {}, classList: {toggle() {}},
    setAttribute(name, value) { this.attributes[name] = value; }
  }));
  const document = {
    readyState: 'loading', addEventListener() {}, documentElement: {},
    querySelectorAll(selector) {
      if (selector === '[data-i18n]') return [label, unknown];
      if (selector === '[data-i18n-placeholder]') return [field];
      if (selector === '.lang-btn') return buttons;
      return [];
    }
  };
  const context = vm.createContext({document, window: {addEventListener() {}}, localStorage: storage});
  vm.runInContext(source, context);
  return {document, label, unknown, field, buttons, context};
}
const blocked = run({getItem() {throw Error('blocked');}, setItem() {throw Error('blocked');}});
vm.runInContext('I18n.setLang("mr")', blocked.context);
assert.equal(blocked.label.textContent, 'मुख्य पान');
assert.equal(blocked.document.documentElement.lang, 'mr');
assert.equal(blocked.buttons[2].attributes['aria-pressed'], 'true');
assert.equal(blocked.buttons[0].attributes['aria-pressed'], 'false');
assert.equal(blocked.field.placeholder, '8–128 अक्षरे');
assert.equal(blocked.unknown.textContent, 'Readable fallback');
vm.runInContext('I18n.setLang("hi")', blocked.context);
assert.equal(blocked.label.textContent, 'मुख्य पृष्ठ');
vm.runInContext('I18n.setLang("unsupported")', blocked.context);
assert.equal(blocked.document.documentElement.lang, 'hi');
const writes = [];
const saved = run({getItem: () => 'mr', setItem: (key, value) => writes.push([key, value])});
assert.equal(vm.runInContext('I18n.getLang()', saved.context), 'mr');
vm.runInContext('I18n.setLang("en")', saved.context);
assert.equal(saved.label.textContent, 'Home');
assert.deepEqual(writes, [['krishiai_lang', 'en']]);
const translations = vm.runInContext('TRANSLATIONS', saved.context);
for (const file of ['templates/base.html', 'templates/index.html', 'templates/farmer/dashboard.html', 'templates/buyer/dashboard.html']) {
  for (const match of fs.readFileSync(file, 'utf8').matchAll(/data-i18n(?:-placeholder|-aria|-title)?="([^"]+)"/g)) {
    // Commerce keys are supplied by the separately loaded commerce dictionary.
    if (match[1].startsWith('commerce_') || match[1].includes('{{')) continue;
    for (const lang of ['en', 'hi', 'mr']) assert.ok(translations[lang][match[1]], `${file}: ${lang}/${match[1]}`);
  }
}
'''
    result = subprocess.run(
        [node, '-e', script],
        cwd=pathlib.Path(__file__).resolve().parents[1],
        text=True, capture_output=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr

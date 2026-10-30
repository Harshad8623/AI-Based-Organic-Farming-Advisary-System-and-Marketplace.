"""Voice navigation must stay optional, localized and safe without a live microphone."""
from pathlib import Path
import shutil
import subprocess

import pytest


HARNESS = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('static/js/voice_assistant.js', 'utf8');
function setup({supported = true, role = 'farmer', lang = 'en'} = {}) {
  const nodes = [];
  class Element {
    constructor(tag) {
      this.tagName = tag.toUpperCase(); this.children = []; this.attributes = {};
      this.listeners = {}; this.style = {}; this.textContent = ''; this.disabled = false;
      nodes.push(this);
    }
    set innerHTML(value) { throw Error('HTML injection sink must not be used'); }
    setAttribute(name, value) { this.attributes[name] = value; }
    addEventListener(name, listener) { this.listeners[name] = listener; }
    append(...children) { this.children.push(...children); }
    appendChild(child) { this.children.push(child); return child; }
    click() { if (!this.disabled) this.listeners.click?.(); }
  }
  const footer = new Element('div');
  const recognitions = [], navigations = [], spoken = [], languageListeners = [], events = {};
  let starts = 0;
  class Recognition {
    constructor() { this.startCount = 0; this.abortCount = 0; this.stopCount = 0; recognitions.push(this); }
    start() { this.startCount++; starts++; }
    abort() { this.abortCount++; }
    stop() { this.stopCount++; }
    result(transcript) { this.onresult({results: [[{transcript}]]}); }
  }
  class Utterance { constructor(text) { this.text = text; } }
  const document = {
    readyState: 'complete', documentElement: {lang},
    getElementById(id) { return nodes.find(node => node.id === id); },
    createElement(tag) { return new Element(tag); },
    querySelector(selector) {
      if (selector === '.site-footer .container') return footer;
      if (selector === 'a[href="/auth/farmer/dashboard"]') return role === 'farmer' ? {} : null;
      if (selector === 'a[href="/auth/login"]') return role === 'guest' ? {} : null;
      if (selector === 'a[href="/orders/farmer"]') return role === 'farmer' ? {} : null;
      return null;
    }
  };
  const window = {
    SpeechRecognition: supported ? Recognition : undefined,
    SpeechSynthesisUtterance: Utterance,
    speechSynthesis: {cancel() {}, speak(utterance) { spoken.push(utterance); }},
    addEventListener(name, listener) { events[name] = listener; },
    location: {assign(path) {navigations.push(path);}}
  };
  const I18n = {getLang: () => lang, onLangChange(listener) {languageListeners.push(listener);}};
  const context = vm.createContext({document, window, I18n});
  vm.runInContext(source, context);
  return {
    context, footer, recognitions, navigations, spoken, document, events,
    button: document.getElementById('voice-navigation-button'),
    status: document.getElementById('voice-navigation-status'),
    starts: () => starts,
    setLang(value) {lang = value; languageListeners.forEach(listener => listener(value));}
  };
}
'''


def run_voice_assertions(assertions):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is needed for the mocked speech API regression')
    result = subprocess.run(
        [node, '-e', HARNESS + assertions],
        cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr


def test_microphone_starts_only_on_tap_and_stops_on_cancel_or_page_exit():
    run_voice_assertions(r'''
const app = setup();
assert.equal(app.starts(), 0);
assert.equal(app.recognitions.length, 0, 'Rendering a control must not request microphone access');
assert.equal(app.footer.children[0].id, 'voice-navigation');
app.button.click();
assert.equal(app.starts(), 1);
assert.equal(app.recognitions[0].lang, 'en-IN');
assert.equal(app.recognitions[0].continuous, false);
assert.equal(app.recognitions[0].interimResults, false);
assert.equal(app.button.attributes['aria-pressed'], 'true');
app.button.click();
assert.equal(app.starts(), 1, 'A second tap stops rather than starts duplicate recognition');
assert.equal(app.recognitions[0].abortCount, 1);
assert.equal(app.button.attributes['aria-pressed'], 'false');
app.recognitions[0].result('open marketplace');
assert.deepEqual(app.navigations, [], 'Results from a cancelled session must be ignored');
app.button.click();
assert.equal(app.starts(), 2);
app.events.pagehide();
assert.equal(app.recognitions[1].abortCount, 1);
''')


def test_native_commands_language_changes_and_role_aware_destinations():
    run_voice_assertions(r'''
const app = setup();
app.button.click();
const english = app.recognitions[0];
app.setLang('mr');
assert.equal(english.abortCount, 1);
english.result('open marketplace');
assert.deepEqual(app.navigations, []);
assert.ok(app.button.textContent.includes('मायक्रोफोन वापरा'));
app.button.click();
assert.equal(app.recognitions[1].lang, 'mr-IN');
app.recognitions[1].result('हवामान दाखवा');
assert.deepEqual(app.navigations, ['/weather/']);
assert.equal(app.spoken.at(-1).lang, 'mr-IN');
app.setLang('hi');
app.button.click();
assert.equal(app.recognitions[2].lang, 'hi-IN');
app.recognitions[2].result('बाज़ार खोलें');
assert.equal(app.navigations.at(-1), '/marketplace/');
assert.equal(app.spoken.at(-1).lang, 'hi-IN');
app.setLang('en');
app.button.click();
app.recognitions[3].result('my orders');
assert.equal(app.navigations.at(-1), '/orders/farmer');
const buyer = setup({role: 'buyer', lang: 'mr'});
buyer.button.click(); buyer.recognitions[0].result('माझ्या ऑर्डर');
assert.equal(buyer.navigations[0], '/orders/my');
buyer.button.click(); buyer.recognitions[1].result('शेतीचे नियोजन');
assert.equal(buyer.navigations.length, 1, 'A buyer must not be routed into a farmer-only 403');
assert.ok(buyer.status.textContent.includes('शेतकरी खात्यांसाठी'));
''')


def test_search_encodes_transcripts_and_unknown_text_is_never_rendered_as_html():
    run_voice_assertions(r'''
const app = setup({lang: 'mr'});
app.button.click(); app.recognitions[0].result('टोमॅटो शोधा');
assert.equal(app.navigations[0], '/marketplace/?search=' + encodeURIComponent('टोमॅटो'));
app.setLang('en');
app.button.click(); app.recognitions[1].result('<img src=x onerror=alert(1)>');
assert.equal(app.navigations.length, 1);
assert.ok(!app.status.textContent.includes('<img'));
app.button.click(); app.recognitions[2].result('search for <img src=x onerror=alert(1)>');
assert.equal(app.navigations.at(-1), '/marketplace/?search=' + encodeURIComponent('<img src=x onerror=alert(1)>'));
app.button.click(); app.recognitions[3].onresult({results: []});
assert.equal(app.navigations.length, 2);
app.button.click(); app.recognitions[4].result('help');
assert.equal(app.footer.children[0].children.at(-1).open, true);
''')


def test_unsupported_browser_and_permission_failure_leave_normal_navigation_available():
    run_voice_assertions(r'''
const unsupported = setup({supported: false, lang: 'hi'});
assert.equal(unsupported.button.disabled, true);
assert.ok(unsupported.status.textContent.includes('उपलब्ध नहीं'));
unsupported.button.click(); assert.equal(unsupported.starts(), 0);
unsupported.setLang('mr');
assert.ok(unsupported.status.textContent.includes('उपलब्ध नाही'));
const app = setup({lang: 'mr'});
app.button.click();
app.recognitions[0].onerror({error: 'not-allowed'});
assert.ok(app.status.textContent.includes('परवानगी मिळाली नाही'));
assert.equal(app.button.attributes['aria-pressed'], 'false');
app.recognitions[0].onend();
assert.ok(app.status.textContent.includes('परवानगी मिळाली नाही'), 'End must not erase a useful permission error');
app.button.click(); assert.equal(app.starts(), 2, 'A later explicit tap may retry');
app.recognitions[1].onerror({error: 'network'});
assert.ok(app.status.textContent.includes('इंटरनेट तपासा'));
assert.deepEqual(app.navigations, []);
''')


def test_field_advice_and_selling_tools_are_localized_and_farmer_only():
    run_voice_assertions(r'''
const app = setup({lang: 'mr'});
app.button.click(); app.recognitions[0].result('माझं शेत');
assert.equal(app.navigations.at(-1), '/my-farm');
app.button.click(); app.recognitions[1].result('विक्रीचा हिशेब');
assert.equal(app.navigations.at(-1), '/farm-decisions');
app.setLang('hi');
app.button.click(); app.recognitions[2].result('आज की सलाह');
assert.equal(app.navigations.at(-1), '/my-farm');
const buyer = setup({role: 'buyer'});
buyer.button.click(); buyer.recognitions[0].result('my farm');
buyer.button.click(); buyer.recognitions[1].result('farm calculations');
assert.equal(buyer.navigations.length, 0);
assert.ok(buyer.status.textContent.includes('farmer accounts'));
''')

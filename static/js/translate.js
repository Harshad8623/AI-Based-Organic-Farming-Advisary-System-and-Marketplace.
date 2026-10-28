/** Optional dynamic translations. Built-in interface translations never need an API. */
const DynamicTranslator = (() => {
  const CACHE_PREFIX = 'krishi_tx_v2_';
  const CACHE_TTL = 7 * 24 * 60 * 60 * 1000;
  const originals = new WeakMap();
  let revision = 0;
  let activeRequest = null;
  let initialized = false;

  function cacheKey(lang, texts) {
    const source = JSON.stringify(texts);
    let hash = 2166136261;
    for (let i = 0; i < source.length; i++) {
      hash = Math.imul(hash ^ source.charCodeAt(i), 16777619);
    }
    return CACHE_PREFIX + lang + '_' + (hash >>> 0).toString(36);
  }

  function validBatch(translations, texts) {
    return Array.isArray(translations) && translations.length === texts.length &&
      translations.every(text => typeof text === 'string' && text.trim() && text.length <= 6000);
  }

  function cacheGet(lang, texts) {
    try {
      const key = cacheKey(lang, texts);
      const value = JSON.parse(localStorage.getItem(key));
      if (!value || value.expires <= Date.now() ||
          JSON.stringify(value.source) !== JSON.stringify(texts) ||
          !validBatch(value.translations, texts)) return null;
      return value.translations;
    } catch (_) { return null; }
  }

  function cacheSet(lang, texts, translations) {
    try {
      localStorage.setItem(cacheKey(lang, texts), JSON.stringify({
        source: texts, translations, expires: Date.now() + CACHE_TTL
      }));
    } catch (_) { /* Private mode or full storage must not prevent translation. */ }
  }

  function notice(key) {
    const region = document.getElementById('translation-notice');
    if (!region) return;
    region.hidden = !key;
    if (key) {
      region.textContent = typeof I18n !== 'undefined' ? I18n.t(key) :
        (key === 'translation_loading' ? 'Translating page content…' :
          'Some content is shown in its original language. Translation is currently unavailable.');
    } else {
      region.textContent = '';
    }
  }

  // Translate text nodes rather than replacing innerHTML, retaining links, buttons,
  // emphasis, event handlers, and their exact original positions.
  function collect() {
    const seen = new Set();
    const entries = [];
    document.querySelectorAll('[data-translate]').forEach(root => {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        if (seen.has(node) || node.parentElement.closest(
          '[data-i18n],script,style,textarea,code,pre,[translate="no"]'
        )) continue;
        seen.add(node);
        if (!originals.has(node)) originals.set(node, node.data);
        const original = originals.get(node);
        if (!original.trim()) continue;
        const prefix = original.match(/^\s*/)[0];
        const suffix = original.match(/\s*$/)[0];
        entries.push({node, original, text: original.trim(), prefix, suffix});
      }
    });
    return entries;
  }

  async function translatePage(lang) {
    const currentRevision = ++revision;
    if (activeRequest) activeRequest.abort();
    activeRequest = null;
    const entries = collect();
    entries.forEach(entry => { entry.node.data = entry.original; });
    notice(null);
    if (!['hi', 'mr'].includes(lang) || !entries.length) return;

    const controller = new AbortController();
    activeRequest = controller;
    const supported = entries.filter(entry => entry.text.length <= 2000);
    const batches = [];
    let batch = [], length = 0;
    supported.forEach(entry => {
      if (batch.length >= 100 || length + entry.text.length > 20000) {
        batches.push(batch); batch = []; length = 0;
      }
      batch.push(entry); length += entry.text.length;
    });
    if (batch.length) batches.push(batch);
    notice('translation_loading');

    try {
      const results = [];
      for (const group of batches) {
        const texts = group.map(entry => entry.text);
        let translations = cacheGet(lang, texts);
        if (!translations) {
          const response = await fetch('/api/translate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({texts, target: lang}),
            signal: controller.signal
          });
          if (!response.ok) throw new Error('Translation unavailable');
          const data = await response.json();
          if (data.translated !== true || data.target !== lang ||
              !validBatch(data.translations, texts)) throw new Error('Translation unavailable');
          translations = data.translations;
          cacheSet(lang, texts, translations);
        }
        if (currentRevision !== revision) return;
        group.forEach((entry, index) => results.push({entry, text: translations[index]}));
      }
      if (currentRevision !== revision) return;
      results.forEach(({entry, text}) => {
        if (entry.node.isConnected) entry.node.data = entry.prefix + text + entry.suffix;
      });
      notice(supported.length < entries.length ? 'translation_unavailable' : null);
    } catch (error) {
      if (currentRevision === revision && error.name !== 'AbortError') notice('translation_unavailable');
    } finally {
      if (currentRevision === revision) activeRequest = null;
    }
  }

  return {
    init() {
      if (initialized) return;
      initialized = true;
      if (typeof I18n !== 'undefined') {
        translatePage(I18n.getLang());
        I18n.onLangChange(translatePage);
      }
    },
    translate: translatePage,
    clearCache() {
      try {
        Object.keys(localStorage).filter(key => key.startsWith('krishi_tx_'))
          .forEach(key => localStorage.removeItem(key));
      } catch (_) { /* Storage may be disabled. */ }
    }
  };
})();

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => DynamicTranslator.init());
} else {
  DynamicTranslator.init();
}

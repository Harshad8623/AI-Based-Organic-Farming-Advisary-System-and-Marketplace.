/* Optional voice navigation. Audio starts only after an explicit button press. */
(() => {
  'use strict';
  const copy = {
    en: {
      title: 'Voice navigation', start: 'Use microphone', stop: 'Stop listening',
      note: 'Optional: tap the microphone, then say a command. Your browser may send audio to its speech service. You can always use the page links instead.',
      unsupported: 'Voice recognition is not available in this browser. Use the page links to continue.',
      ready: 'Microphone is off.', listening: 'Listening for one command…', stopped: 'Microphone stopped.',
      help: 'Voice commands', examples: 'Try “open marketplace”, “my orders”, “farm planner”, “weather”, “go home”, or “search tomato”.',
      unknown: 'Command not recognised. Open Voice commands for examples, or use a page link.',
      denied: 'Microphone permission was not granted. Use the page links, or enable microphone access in your browser settings and try again.',
      noAudio: 'No microphone was found. Use the page links instead.',
      noSpeech: 'No speech was heard. Tap the microphone to try again.',
      network: 'The browser speech service could not connect. Check your connection, or use a page link.',
      failed: 'Voice recognition could not start. Try again, or use a page link.',
      unavailable: 'That tool is available to farmer accounts. Use your dashboard to continue.',
      opening: 'Opening', search: 'marketplace search',
      market: 'marketplace', cart: 'your cart', guides: 'crop guides', assistant: 'farming assistant',
      weather: 'weather', analytics: 'your farm insights', crop: 'crop options', health: 'plant health',
      home: 'home', orders: 'your orders', planner: 'farm planner'
    },
    hi: {
      title: 'बोलकर पृष्ठ खोलें', start: 'माइक्रोफ़ोन इस्तेमाल करें', stop: 'सुनना बंद करें',
      note: 'वैकल्पिक: माइक्रोफ़ोन दबाएँ, फिर निर्देश बोलें। आपका ब्राउज़र आवाज़ अपनी पहचान सेवा को भेज सकता है। आप पृष्ठ के लिंक भी इस्तेमाल कर सकते हैं।',
      unsupported: 'इस ब्राउज़र में आवाज़ पहचान उपलब्ध नहीं है। आगे बढ़ने के लिए पृष्ठ के लिंक इस्तेमाल करें।',
      ready: 'माइक्रोफ़ोन बंद है।', listening: 'एक निर्देश सुन रहे हैं…', stopped: 'माइक्रोफ़ोन बंद किया गया।',
      help: 'बोलने के उदाहरण', examples: 'कहें: “बाज़ार खोलें”, “मेरे ऑर्डर”, “खेती की योजना”, “मौसम दिखाओ”, “मुख्य पृष्ठ”, या “टमाटर खोजें”।',
      unknown: 'निर्देश समझ नहीं आया। बोलने के उदाहरण देखें या पृष्ठ का लिंक इस्तेमाल करें।',
      denied: 'माइक्रोफ़ोन की अनुमति नहीं मिली। पृष्ठ के लिंक इस्तेमाल करें या ब्राउज़र सेटिंग में अनुमति देकर फिर कोशिश करें।',
      noAudio: 'माइक्रोफ़ोन नहीं मिला। पृष्ठ के लिंक इस्तेमाल करें।',
      noSpeech: 'आवाज़ नहीं सुनाई दी। फिर कोशिश करने के लिए माइक्रोफ़ोन दबाएँ।',
      network: 'ब्राउज़र की आवाज़ सेवा से संपर्क नहीं हुआ। इंटरनेट जाँचें या पृष्ठ का लिंक इस्तेमाल करें।',
      failed: 'आवाज़ पहचान शुरू नहीं हुई। फिर कोशिश करें या पृष्ठ का लिंक इस्तेमाल करें।',
      unavailable: 'यह साधन किसान खातों के लिए है। अपने डैशबोर्ड से आगे बढ़ें।',
      opening: 'खोल रहे हैं:', search: 'बाज़ार में खोज',
      market: 'बाज़ार', cart: 'आपकी टोकरी', guides: 'फसल मार्गदर्शिका', assistant: 'खेती सहायक',
      weather: 'मौसम', analytics: 'आपकी खेती की जानकारी', crop: 'फसल के विकल्प', health: 'पौधों का स्वास्थ्य',
      home: 'मुख्य पृष्ठ', orders: 'आपके ऑर्डर', planner: 'खेती की योजना'
    },
    mr: {
      title: 'बोलून पान उघडा', start: 'मायक्रोफोन वापरा', stop: 'ऐकणे थांबवा',
      note: 'ऐच्छिक: मायक्रोफोन दाबा आणि सूचना बोला. तुमचा ब्राउझर आवाज त्याच्या ओळख सेवेकडे पाठवू शकतो. पानावरील दुवेही वापरता येतात.',
      unsupported: 'या ब्राउझरमध्ये आवाज ओळख उपलब्ध नाही. पुढे जाण्यासाठी पानावरील दुवे वापरा.',
      ready: 'मायक्रोफोन बंद आहे.', listening: 'एक सूचना ऐकत आहोत…', stopped: 'मायक्रोफोन बंद केला.',
      help: 'बोलण्याची उदाहरणे', examples: 'बोला: “बाजार उघडा”, “माझ्या ऑर्डर”, “शेतीचे नियोजन”, “हवामान दाखवा”, “मुख्य पान”, किंवा “टोमॅटो शोधा”.',
      unknown: 'सूचना समजली नाही. बोलण्याची उदाहरणे पाहा किंवा पानावरील दुवा वापरा.',
      denied: 'मायक्रोफोनची परवानगी मिळाली नाही. पानावरील दुवे वापरा किंवा ब्राउझरच्या सेटिंगमध्ये परवानगी देऊन पुन्हा प्रयत्न करा.',
      noAudio: 'मायक्रोफोन सापडला नाही. पानावरील दुवे वापरा.',
      noSpeech: 'आवाज ऐकू आला नाही. पुन्हा प्रयत्न करण्यासाठी मायक्रोफोन दाबा.',
      network: 'ब्राउझरच्या आवाज सेवेशी संपर्क झाला नाही. इंटरनेट तपासा किंवा पानावरील दुवा वापरा.',
      failed: 'आवाज ओळख सुरू झाली नाही. पुन्हा प्रयत्न करा किंवा पानावरील दुवा वापरा.',
      unavailable: 'हे साधन शेतकरी खात्यांसाठी आहे. आपल्या आढावा पानावरून पुढे जा.',
      opening: 'उघडत आहोत:', search: 'बाजारातील शोध',
      market: 'बाजार', cart: 'तुमची टोपली', guides: 'पीक मार्गदर्शिका', assistant: 'शेती सहाय्यक',
      weather: 'हवामान', analytics: 'तुमच्या शेतीची माहिती', crop: 'पिकांचे पर्याय', health: 'पिकांचे आरोग्य',
      home: 'मुख्य पान', orders: 'तुमच्या ऑर्डर', planner: 'शेतीचे नियोजन'
    }
  };
  const locales = {en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN'};
  const commands = [
    ['market', '/marketplace/', ['open marketplace', 'marketplace', 'open market', 'market', 'बाज़ार खोलें', 'बाजार खोलें', 'बाजार खोलो', 'बाज़ार', 'बाजार', 'मंडी', 'बाजार उघडा', 'शेतमाल बाजार']],
    ['cart', '/cart/', ['open cart', 'my cart', 'cart', 'shopping cart', 'मेरी टोकरी', 'टोकरी खोलें', 'टोकरी', 'माझी टोपली', 'टोपली उघडा', 'टोपली']],
    ['orders', null, ['my orders', 'orders', 'order status', 'मेरे ऑर्डर', 'ऑर्डर दिखाओ', 'ऑर्डर', 'माझ्या ऑर्डर', 'ऑर्डर दाखवा']],
    ['planner', '/farm-tools', ['farm planner', 'open farm planner', 'planner', 'tasks', 'खेती की योजना', 'खेत की योजना', 'शेतीचे नियोजन', 'कामाची यादी', 'शेतीची वही']],
    ['guides', '/roadmap/', ['open roadmap', 'roadmap', 'crop guides', 'farming guide', 'फसल मार्गदर्शिका', 'खेती की जानकारी', 'पीक मार्गदर्शिका', 'शेती मार्गदर्शक']],
    ['assistant', '/chatbot/', ['open chatbot', 'chatbot', 'farming assistant', 'assistant', 'खेती सहायक', 'मददगार', 'शेती सहाय्यक']],
    ['weather', '/weather/', ['weather', 'open weather', 'मौसम', 'मौसम दिखाओ', 'मौसम दिखाएं', 'हवामान', 'हवामान दाखवा']],
    ['analytics', '/analytics/', ['analytics', 'farm insights', 'खेती की जानकारी दिखाओ', 'शेतीची माहिती']],
    ['crop', '/crop/', ['crop options', 'crop recommendation', 'crop ai', 'फसल के विकल्प', 'पिकांचे पर्याय']],
    ['health', '/disease/', ['plant health', 'plant disease', 'disease detection', 'पौधों का स्वास्थ्य', 'फसल के रोग', 'पिकांचे आरोग्य', 'पीक रोग']],
    ['home', '/', ['go home', 'home', 'homepage', 'मुख्य पृष्ठ', 'घर', 'मुख्य पान', 'मुख्य पान उघडा']]
  ];
  let recognition = null;
  let elements = null;
  let statusKey = 'ready';
  const language = () => {
    const selected = typeof I18n !== 'undefined' ? I18n.getLang() : document.documentElement.lang;
    return copy[selected] ? selected : 'en';
  };
  const text = key => copy[language()][key] || copy.en[key] || '';
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  function render() {
    if (!elements) return;
    elements.title.textContent = text('title');
    elements.note.textContent = text('note');
    elements.button.textContent = '🎤 ' + text(recognition ? 'stop' : 'start');
    elements.button.setAttribute('aria-pressed', String(Boolean(recognition)));
    elements.summary.textContent = text('help');
    elements.examples.textContent = text('examples');
    elements.status.textContent = text(statusKey);
  }

  function speak(message) {
    if (!window.speechSynthesis || typeof window.SpeechSynthesisUtterance !== 'function') return;
    try {
      window.speechSynthesis.cancel();
      const utterance = new window.SpeechSynthesisUtterance(message);
      utterance.lang = locales[language()];
      window.speechSynthesis.speak(utterance);
    } catch (_) { /* Optional speech feedback must never block navigation. */ }
  }

  function stop() {
    const previous = recognition;
    recognition = null;
    if (previous) {
      try { previous.abort(); } catch (_) { /* It may already have ended. */ }
    }
  }

  function process(transcript) {
    if (typeof transcript !== 'string' || transcript.length > 300) {
      statusKey = 'unknown'; render(); return;
    }
    const command = transcript.normalize('NFC').trim().toLowerCase().replace(/[.!?।]+$/u, '').replace(/\s+/g, ' ');
    if (['help', 'commands', 'मदद', 'सहायता', 'मदत', 'उदाहरणे'].includes(command)) {
      elements.help.open = true;
      statusKey = 'examples'; render(); speak(text('examples')); return;
    }
    const search = command.match(/^(?:search(?: for)?|find|खोजें|खोजो|ढूंढो|ढूँढो|खोज|शोधा|शोध)\s+(.+)$/u)
      || command.match(/^(.+?)\s+(?:खोजें|खोजो|ढूंढो|ढूँढो|शोधा|शोध)$/u);
    if (search && search[1].trim()) {
      const message = text('opening') + ' ' + text('search');
      elements.status.textContent = message;
      speak(message);
      window.location.assign('/marketplace/?search=' + encodeURIComponent(search[1].trim().slice(0, 100)));
      return;
    }
    const match = commands.find(([, , phrases]) => phrases.includes(command));
    if (!match) { statusKey = 'unknown'; render(); return; }
    const [label, configuredPath] = match;
    if (label === 'planner' && !document.querySelector('a[href="/auth/farmer/dashboard"]') &&
        !document.querySelector('a[href="/auth/login"]')) {
      statusKey = 'unavailable'; render(); return;
    }
    const path = label === 'orders'
      ? (document.querySelector('a[href="/orders/farmer"]') ? '/orders/farmer' : '/orders/my')
      : configuredPath;
    const message = text('opening') + ' ' + text(label);
    elements.status.textContent = message;
    speak(message);
    window.location.assign(path);
  }

  function toggle() {
    if (recognition) {
      stop(); statusKey = 'stopped'; render(); return;
    }
    if (!SpeechRecognition) return;
    let current;
    try {
      current = new SpeechRecognition();
      current.lang = locales[language()];
      current.continuous = false;
      current.interimResults = false;
      current.maxAlternatives = 1;
      recognition = current;
      statusKey = 'listening'; render();
      current.onstart = () => { if (recognition === current) { statusKey = 'listening'; render(); } };
      current.onresult = event => {
        if (recognition !== current) return;
        const transcript = event.results?.[0]?.[0]?.transcript;
        recognition = null;
        try { current.stop(); } catch (_) {}
        render();
        process(transcript);
      };
      current.onerror = event => {
        if (recognition !== current) return;
        recognition = null;
        statusKey = ({'not-allowed': 'denied', 'service-not-allowed': 'denied',
          'audio-capture': 'noAudio', 'no-speech': 'noSpeech', 'network': 'network',
          'aborted': 'stopped'})[event.error] || 'failed';
        render();
      };
      current.onend = () => {
        if (recognition !== current) return;
        recognition = null;
        if (statusKey === 'listening') statusKey = 'noSpeech';
        render();
      };
      current.start();
    } catch (_) {
      if (recognition === current) recognition = null;
      statusKey = 'failed'; render();
    }
  }

  function createUI() {
    const footer = document.querySelector('.site-footer .container');
    if (!footer || document.getElementById('voice-navigation')) return;
    const section = document.createElement('section');
    section.id = 'voice-navigation';
    section.className = 'border-top mt-3 pt-3';
    section.setAttribute('aria-labelledby', 'voice-navigation-title');
    const title = document.createElement('h2');
    title.id = 'voice-navigation-title'; title.className = 'h6';
    const note = document.createElement('p'); note.className = 'small text-muted mb-2';
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'btn btn-outline-success btn-sm';
    button.id = 'voice-navigation-button';
    button.setAttribute('aria-describedby', 'voice-navigation-status');
    button.addEventListener('click', toggle);
    button.disabled = !SpeechRecognition;
    const status = document.createElement('p');
    status.id = 'voice-navigation-status'; status.className = 'small text-muted mt-2 mb-0';
    status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
    const help = document.createElement('details'); help.className = 'small mt-2';
    const summary = document.createElement('summary');
    summary.style.minHeight = '44px'; summary.style.display = 'flex'; summary.style.alignItems = 'center';
    const examples = document.createElement('p'); examples.className = 'text-muted mb-0';
    help.append(summary, examples);
    section.append(title, note, button, status, help);
    footer.appendChild(section);
    elements = {title, note, button, status, help, summary, examples};
    statusKey = SpeechRecognition ? 'ready' : 'unsupported';
    render();
    if (typeof I18n !== 'undefined') I18n.onLangChange(() => {
      stop(); statusKey = SpeechRecognition ? 'ready' : 'unsupported'; render();
      if (window.speechSynthesis) { try { window.speechSynthesis.cancel(); } catch (_) {} }
    });
    window.addEventListener('pagehide', stop);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', createUI);
  else createUI();
})();

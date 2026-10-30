/* Built-in farmer planner translations; no network or API key is needed. */
(() => {
  const copy = {
    farm_eyebrow: ['A little planning. A better season.', 'थोड़ी योजना, बेहतर मौसम।', 'थोडे नियोजन, चांगला हंगाम.'],
    farm_title: ['My farm planner', 'मेरे खेत की योजना', 'माझ्या शेतीचे नियोजन'],
    farm_subtitle: ['Keep your next task and your farm spending in one place.', 'अगला काम और खेती का खर्च एक जगह रखें।', 'पुढचे काम आणि शेतीचा खर्च एकाच ठिकाणी नोंदवा.'],
    farm_private: ['Private to your account. Dates follow India Standard Time.', 'केवल आपके खाते में दिखाई देता है। तारीखें भारतीय मानक समय के अनुसार हैं।', 'फक्त तुमच्या खात्यात दिसते. तारखा भारतीय प्रमाणवेळेनुसार आहेत.'],
    farm_go_tasks: ['Plan a task', 'काम की योजना बनाएँ', 'कामाचे नियोजन करा'],
    farm_go_ledger: ['Track money', 'हिसाब रखें', 'हिशेब ठेवा'],
    farm_tasks_title: ['What needs doing?', 'कौन से काम करने हैं?', 'कोणती कामे करायची आहेत?'],
    farm_open_tasks: ['open tasks', 'बाकी काम', 'बाकी कामे'],
    farm_overdue_tasks: ['overdue', 'तारीख बीत गई', 'मुदत उलटलेली'],
    farm_reminder_note: ['Check this planner for reminders; no SMS or notifications are sent.', 'याद रखने के लिए यह योजना देखें; SMS या सूचनाएँ नहीं भेजी जाती हैं।', 'आठवणीसाठी हे नियोजन पाहा; SMS किंवा सूचना पाठवल्या जात नाहीत.'],
    farm_new_task: ['Add a farm task', 'खेती का काम जोड़ें', 'शेतीचे काम जोडा'],
    farm_task_label: ['Task', 'काम', 'काम'],
    farm_task_placeholder: ['e.g. Check drip irrigation', 'जैसे: टपक सिंचाई जाँचें', 'उदा. ठिबक सिंचन तपासा'],
    farm_crop_label: ['Crop or field (optional)', 'फसल या खेत (वैकल्पिक)', 'पीक किंवा शेत (ऐच्छिक)'],
    farm_crop_placeholder: ['e.g. Tomato, east field', 'जैसे: टमाटर, पूर्व वाला खेत', 'उदा. टोमॅटो, पूर्वेकडील शेत'],
    farm_due_date: ['Due date', 'काम की तारीख', 'कामाची तारीख'],
    farm_save_task: ['Save task', 'काम सहेजें', 'काम जतन करा'],
    farm_done: ['Done', 'पूरा हुआ', 'पूर्ण झाले'],
    farm_overdue: ['Overdue', 'तारीख बीत गई', 'मुदत उलटली'],
    farm_today: ['Today', 'आज', 'आज'],
    farm_reopen: ['Reopen', 'फिर से बाकी रखें', 'पुन्हा बाकी ठेवा'],
    farm_page: ['Page', 'पृष्ठ', 'पान'],
    farm_previous: ['Previous', 'पिछला', 'मागील'],
    farm_next: ['Next', 'अगला', 'पुढील'],
    farm_task_pages: ['Task pages', 'काम के पृष्ठ', 'कामांची पाने'],
    farm_ledger_pages: ['Money record pages', 'हिसाब के पृष्ठ', 'हिशेबाची पाने'],
    farm_mark_done: ['Mark done', 'पूरा हुआ चुनें', 'पूर्ण झाले निवडा'],
    farm_delete: ['Delete', 'हटाएँ', 'काढून टाका'],
    farm_delete_task_confirm: ['Delete this task? This cannot be undone.', 'यह काम हटाएँ? इसे वापस नहीं लाया जा सकता।', 'हे काम काढून टाकायचे? ते पुन्हा मिळवता येणार नाही.'],
    farm_tasks_empty: ['Start with one small task', 'एक छोटे काम से शुरू करें', 'एका छोट्या कामापासून सुरुवात करा'],
    farm_tasks_empty_hint: ['Plan soil testing, irrigation checks, sowing or a market visit.', 'मिट्टी परीक्षण, सिंचाई जाँच, बुवाई या बाजार जाने की योजना बनाएँ।', 'माती परीक्षण, सिंचन तपासणी, पेरणी किंवा बाजारभेटीचे नियोजन करा.'],
    farm_ledger_title: ['Farm money diary', 'खेती की हिसाब डायरी', 'शेतीची हिशेब वही'],
    farm_manual_note: ['Your manual records only. Marketplace orders are not added automatically.', 'केवल आपके दर्ज किए गए हिसाब। बाजार के ऑर्डर अपने आप नहीं जुड़ते।', 'फक्त तुम्ही नोंदवलेला हिशेब. बाजारातील ऑर्डर आपोआप जोडल्या जात नाहीत.'],
    farm_month: ['View month', 'महीना देखें', 'महिना पाहा'],
    farm_show: ['Show', 'दिखाएँ', 'दाखवा'],
    farm_income_month: ['Income for selected month', 'चुने हुए महीने की आय', 'निवडलेल्या महिन्यातील उत्पन्न'],
    farm_expense_month: ['Expenses for selected month', 'चुने हुए महीने का खर्च', 'निवडलेल्या महिन्यातील खर्च'],
    farm_net_month: ['Net recorded amount', 'दर्ज हिसाब की शेष राशि', 'नोंदींनुसार निव्वळ रक्कम'],
    farm_net_hint: ['Income minus expenses for the selected month', 'चुने हुए महीने की आय में से खर्च घटाकर', 'निवडलेल्या महिन्यातील उत्पन्न वजा खर्च'],
    farm_new_entry: ['Add a money record', 'हिसाब की नोंद जोड़ें', 'हिशेबाची नोंद जोडा'],
    farm_type: ['Type', 'प्रकार', 'प्रकार'],
    farm_expense: ['Expense', 'खर्च', 'खर्च'],
    farm_income: ['Income', 'आय', 'उत्पन्न'],
    farm_amount: ['Amount (₹ INR)', 'राशि (₹ रुपये)', 'रक्कम (₹ रुपये)'],
    farm_entry_date: ['Date received or paid', 'पैसा मिलने या देने की तारीख', 'पैसे मिळाल्याची किंवा दिल्याची तारीख'],
    farm_category: ['Category', 'श्रेणी', 'प्रकार'],
    farm_category_seeds: ['Seeds', 'बीज', 'बियाणे'],
    farm_category_soil_inputs: ['Soil inputs', 'मिट्टी और खाद', 'माती व खते'],
    farm_category_labour: ['Labour', 'मजदूरी', 'मजुरी'],
    farm_category_water: ['Water', 'पानी', 'पाणी'],
    farm_category_equipment: ['Equipment', 'उपकरण', 'अवजारे'],
    farm_category_transport: ['Transport', 'परिवहन', 'वाहतूक'],
    farm_category_produce_sale: ['Produce sale', 'उपज की बिक्री', 'शेतमालाची विक्री'],
    farm_category_other: ['Other', 'अन्य', 'इतर'],
    farm_note: ['Note (optional)', 'टिप्पणी (वैकल्पिक)', 'टीप (ऐच्छिक)'],
    farm_note_placeholder: ['e.g. Seeds for the north field', 'जैसे: उत्तर वाले खेत के लिए बीज', 'उदा. उत्तरेकडील शेतासाठी बियाणे'],
    farm_save_entry: ['Save record', 'नोंद सहेजें', 'नोंद जतन करा'],
    farm_records: ['records in selected month', 'चुने हुए महीने की नोंदें', 'निवडलेल्या महिन्यातील नोंदी'],
    farm_export: ['Download month as CSV', 'महीने का CSV डाउनलोड करें', 'महिन्याची CSV डाउनलोड करा'],
    farm_delete_entry_confirm: ['Delete this money record? Your totals will change.', 'यह हिसाब हटाएँ? आपकी कुल राशि बदल जाएगी।', 'ही हिशेबाची नोंद काढून टाकायची? एकूण रक्कम बदलेल.'],
    farm_ledger_limit: ['Showing up to 100 records per page. Monthly totals and CSV include all records.', 'हर पृष्ठ पर अधिकतम 100 नोंदें दिखाई गई हैं। महीने के कुल हिसाब और CSV में सभी नोंदें शामिल हैं।', 'प्रत्येक पानावर जास्तीत जास्त 100 नोंदी दाखवल्या आहेत. महिन्याच्या एकूण हिशेबात आणि CSV मध्ये सर्व नोंदी आहेत.'],
    farm_ledger_empty: ['Know where your money goes', 'जानें आपका पैसा कहाँ जाता है', 'पैसे कुठे खर्च होतात ते पाहा'],
    farm_ledger_empty_hint: ['No records this month. Add the cost of seeds, labour or your latest produce sale.', 'इस महीने कोई नोंद नहीं है। बीज, मजदूरी का खर्च या उपज की बिक्री जोड़ें।', 'या महिन्यात नोंदी नाहीत. बियाणे, मजुरीचा खर्च किंवा शेतमालाची विक्री नोंदवा.'],
    farm_error_date: ['Enter a real date between 1900 and 2100.', '1900 से 2100 के बीच सही तारीख चुनें।', '1900 ते 2100 मधील योग्य तारीख निवडा.'],
    farm_error_month: ['Choose a valid month between 1900 and 2100.', '1900 से 2100 के बीच सही महीना चुनें।', '1900 ते 2100 मधील योग्य महिना निवडा.'],
    farm_error_task: ['Use 2–160 characters for the task and up to 80 for the crop or field.', 'काम में 2–160 अक्षर और फसल या खेत में अधिकतम 80 अक्षर लिखें।', 'कामासाठी 2–160 अक्षरे आणि पीक किंवा शेतासाठी जास्तीत जास्त 80 अक्षरे वापरा.'],
    farm_error_entry: ['Choose a type and category. Keep your note within 240 characters.', 'प्रकार और श्रेणी चुनें। टिप्पणी 240 अक्षरों तक रखें।', 'प्रकार निवडा. टीप जास्तीत जास्त 240 अक्षरांत लिहा.'],
    farm_error_amount: ['Enter a positive amount up to ₹99,999,999.99, with at most two decimal places.', '₹99,999,999.99 तक शून्य से अधिक राशि लिखें, दशमलव के बाद अधिकतम दो अंक रखें।', '₹99,999,999.99 पर्यंत शून्यापेक्षा मोठी रक्कम लिहा; दशांशानंतर जास्तीत जास्त दोन अंक ठेवा.'],
    farm_error_future_entry: ['Record money already received or paid. The date cannot be in the future.', 'मिल चुके या दिए गए पैसे ही दर्ज करें। भविष्य की तारीख नहीं चुनें।', 'मिळालेले किंवा दिलेले पैसेच नोंदवा. भविष्यातील तारीख निवडू नका.'],
    farm_error_expired_form: ['This form is out of date. Check your entries and submit again.', 'यह फॉर्म पुराना हो गया है। अपनी जानकारी जाँचकर फिर से जमा करें।', 'हा फॉर्म जुना झाला आहे. माहिती तपासा आणि पुन्हा जतन करा.'],
    farm_advice_source: ['Saved field check', 'सहेजी गई खेत जाँच', 'जतन केलेली शेतपाहणी'],
    farm_advice_review_title: ['Review needed before acting', 'काम से पहले फिर जाँचें', 'काम करण्यापूर्वी पुन्हा पाहा'],
    farm_advice_review_note: ['This task came from a field check that needs review. Check current field conditions before using the saved instructions.', 'यह काम ऐसी खेत जाँच से आया है जिसकी फिर समीक्षा जरूरी है। पुरानी सूचना इस्तेमाल करने से पहले खेत की वर्तमान स्थिति जाँचें।', 'हे काम पुन्हा पाहणी आवश्यक असलेल्या जुन्या नोंदीतून आले आहे. जतन केलेल्या सूचना वापरण्यापूर्वी शेताची सध्याची स्थिती तपासा.'],
    farm_advice_latest: ['Review latest plan', 'नवीनतम योजना देखें', 'नवीन योजना तपासा'],
    farm_advice_new_check: ['Record a fresh field check', 'खेत की नई जाँच दर्ज करें', 'शेताची नवी पाहणी नोंदवा'],
    farm_advice_field_history: ['Open field history', 'खेत की पिछली नोंदें देखें', 'शेताच्या मागील नोंदी पाहा'],
    farm_advice_saved_instructions: ['Read the saved instructions', 'सहेजी गई सूचना पढ़ें', 'जतन केलेल्या सूचना वाचा'],
    farm_advice_already_done: ['I already did this', 'यह काम मैंने पहले किया है', 'हे काम मी आधीच केले आहे'],
  };

  if (typeof TRANSLATIONS !== 'undefined') {
    ['en', 'hi', 'mr'].forEach((lang, index) => {
      TRANSLATIONS[lang] = TRANSLATIONS[lang] || {};
      Object.entries(copy).forEach(([key, values]) => { TRANSLATIONS[lang][key] = values[index]; });
    });
  }

  const currentLanguage = () => typeof I18n !== 'undefined' ? I18n.getLang() : 'en';
  function localizeDates() {
    const lang = currentLanguage();
    const formatter = new Intl.DateTimeFormat(`${lang}-IN`, {day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC'});
    document.querySelectorAll('#farm-tasks time[datetime], #farm-ledger time[datetime]').forEach(element => {
      const value = new Date(`${element.dateTime}T00:00:00Z`);
      if (!Number.isNaN(value.getTime())) element.textContent = formatter.format(value);
    });
    document.title = `${copy.farm_title[['en', 'hi', 'mr'].indexOf(lang)] || copy.farm_title[0]} — Dharti Rakshak`;
    document.querySelectorAll('[data-farm-localized]').forEach(element => {
      try {
        const localized = JSON.parse(element.dataset.farmLocalized);
        const value = localized[lang] || localized.en;
        if (typeof value === 'string') element.textContent = value;
      } catch (_) { /* A damaged optional label must not break task controls. */ }
    });
  }

  function initialize() {
    if (typeof I18n !== 'undefined') {
      I18n.apply();
      I18n.onLangChange(localizeDates);
    }
    localizeDates();
    document.querySelectorAll('form[data-farm-confirm]').forEach(form => {
      form.addEventListener('submit', event => {
        const key = form.dataset.farmConfirm;
        const message = typeof I18n !== 'undefined' ? I18n.t(key) : copy[key][0];
        if (!window.confirm(message)) event.preventDefault();
      });
    });
    document.getElementById('farm-form-error')?.focus();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
  else initialize();
})();

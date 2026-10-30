(() => {
  'use strict';
  const copy = {
    fh_title_water:['Should I water today?','आज पानी देना चाहिए?','आज पाणी द्यायचं का?'],
    fh_title_plant:['What happened to my plants?','पौधों को क्या हुआ?','झाडांना काय झालं?'],
    fh_title_pest:['I can see pests','कीट दिख रहे हैं','कीड दिसते आहे'],
    fh_intro:['A few observations. One clear next check.','कुछ जाँचें। आगे का एक स्पष्ट कदम।','थोडी पाहणी. पुढचं एक स्पष्ट काम.'],
    fh_choose_problem:['Choose your field problem','खेत की समस्या चुनें','शेतातील अडचण निवडा'],
    fh_tab_water:['Water','पानी','पाणी'],fh_tab_plant:['Leaves / plants','पत्ते / पौधे','पानं / झाडं'],fh_tab_pest:['Pests','कीट','कीड'],
    fh_soil:['How is the soil near the roots?','जड़ों के पास की मिट्टी कैसी है?','मुळांजवळची माती कशी आहे?'],
    fh_standing_water:['Is unwanted water collecting in the field?','खेत में अनचाहा पानी जमा है?','शेतात अनावश्यक पाणी साचलं आहे का?'],
    fh_yes:['Yes','हाँ','होय'],fh_no:['No','नहीं','नाही'],fh_not_checked:['Not checked','नहीं देखा','तपासलं नाही'],fh_not_sure:['Not sure','पता नहीं','माहीत नाही'],
    fh_leaf:['What can you see on the plants?','पौधों पर क्या दिख रहा है?','झाडांवर काय दिसतंय?'],
    fh_pest:['Did you see insects or fresh pest damage?','कीट या ताजा नुकसान दिखा?','किडी किंवा ताजं नुकसान दिसलं का?'],
    fh_optional:['Add crop or other observations (optional)','फसल या अन्य जानकारी जोड़ें (वैकल्पिक)','पीक किंवा आणखी माहिती जोडा (ऐच्छिक)'],
    fh_crop:['Crop','फसल','पीक'],fh_get_help:['Show my next step','अगला कदम दिखाएँ','पुढचं काम सांगा'],
    fh_no_account:['No account needed. These answers are not saved.','खाता जरूरी नहीं। ये उत्तर सहेजे नहीं जाते।','खातं गरजेचं नाही. ही उत्तरं जतन होत नाहीत.'],
    fh_next:['Do this first','पहले यह करें','आधी हे करा'],fh_why:['Why:','कारण:','कारण:'],
    fh_unchecked:['Still to check:','अभी देखना बाकी है:','अजून तपासायचं:'],
    fh_unchecked_moisture:['root-zone moisture','जड़ों के पास नमी','मुळांजवळचा ओलावा'],
    fh_unchecked_waterlogging:['standing water','जमा पानी','साचलेलं पाणी'],
    fh_unchecked_pest_present:['pests / fresh damage','कीट / ताजा नुकसान','कीड / ताजं नुकसान'],
    fh_more:['Other things to check','और क्या देखें','आणखी काय तपासायचं'],
    fh_scope:['Based on the answers you gave. This is not a diagnosis or a water-dose prescription.','आपके उत्तरों पर आधारित। यह पक्का निदान या सिंचाई की मात्रा नहीं है।','तुमच्या उत्तरांवर आधारित. हे निश्चित निदान किंवा पाण्याच्या मात्रेची शिफारस नाही.'],
    fh_save_history:['Keep a field history in My farm','मेरे खेत में जाँच का इतिहास रखें','माझं शेत मध्ये पाहणीची नोंद ठेवा'],
    fh_account_optional:['Want to keep a field history? Create an account','जाँच का इतिहास रखना है? खाता बनाएँ','पाहणीची नोंद ठेवायची? खातं तयार करा'],
    fh_print:['Print this check','यह जाँच प्रिंट करें','ही पाहणी प्रिंट करा'],
    fh_change_answers:['Change my answers','मेरे उत्तर बदलें','माझी उत्तरं बदला'],
    fh_need_help:['Need to talk to someone?','किसी से बात करनी है?','कुणाशी बोलायचं आहे?'],
    fh_call_note:['If damage is spreading or you cannot identify the cause, contact your local KVK or Kisan Call Centre.','नुकसान बढ़ रहा हो या कारण न समझ आए तो स्थानीय कृषि विज्ञान केंद्र या किसान कॉल सेंटर से संपर्क करें।','नुकसान वाढत असेल किंवा कारण समजत नसेल तर स्थानिक कृषी विज्ञान केंद्र किंवा किसान कॉल सेंटरशी संपर्क करा.'],
    fh_call:['Kisan Call Centre','किसान कॉल सेंटर','किसान कॉल सेंटर'],fh_official:['Official agriculture service information','सरकारी कृषि सेवा की जानकारी','अधिकृत कृषी सेवेची माहिती'],
    fh_invalid:['Choose one of the shown answers, then try again.','दिए गए उत्तरों में से चुनें, फिर कोशिश करें।','दाखवलेल्या उत्तरांपैकी निवडा आणि पुन्हा प्रयत्न करा.']
  };
  ['en','hi','mr'].forEach((language,index) => {
    TRANSLATIONS[language] = TRANSLATIONS[language] || {};
    Object.entries(copy).forEach(([key,values]) => { TRANSLATIONS[language][key]=values[index]; });
  });
  function apply() {
    I18n.apply();
    document.querySelectorAll('[data-help-localized]').forEach(element => {
      try {
        const values=JSON.parse(element.dataset.helpLocalized);
        let text=values[I18n.getLang()] || values.en;
        if(element.dataset.helpPart) text=text?.[element.dataset.helpPart];
        if(typeof text==='string') element.textContent=text;
      } catch (_) { /* Keep server-rendered copy if a value is unavailable. */ }
    });
  }
  function ready() {
    apply(); I18n.onLangChange(apply);
    document.querySelectorAll('[data-help-print]').forEach(button => button.addEventListener('click',()=>window.print()));
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',ready); else ready();
})();

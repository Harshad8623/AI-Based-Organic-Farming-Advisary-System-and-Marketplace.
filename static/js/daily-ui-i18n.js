/* Short, built-in labels for everyday farm work. */
(() => {
  'use strict';
  const copy = {
    daily_home: ['Home','घर','घर'],
    daily_fields: ['My fields','मेरे खेत','माझी शेते'],
    daily_money: ['Accounts','हिसाब','हिशेब'],
    daily_market: ['Market','बाज़ार','बाजार'],
    daily_more: ['More','और','इतर'],
    daily_other: ['Other work','बाकी काम','इतर कामे'],
    daily_need_help: ['What do you need to do?','क्या करना है?','काय करायचं आहे?'],
    daily_pick_work: ['Choose one task.','एक काम चुनें।','एक काम निवडा.'],
    daily_tasks_label: ['Everyday farm work','खेती के रोज़ के काम','शेतीची रोजची कामे'],
    daily_water: ['Should I water today?','आज पानी देना है?','आज पाणी द्यायचं का?'],
    daily_water_note: ['Check the soil before running the pump.','पंप चलाने से पहले मिट्टी जाँचें।','पंप सुरू करण्यापूर्वी माती पाहा.'],
    daily_plant: ['A problem with my crop','फसल में परेशानी है','पिकाला त्रास होतोय'],
    daily_plant_note: ['Yellow leaves, wilting or insects.','पीले पत्ते, मुरझाना या कीड़े।','पिवळी पाने, कोमेजणे किंवा कीड.'],
    daily_add_money: ['Write down a cost or sale','खर्च या बिक्री लिखें','खर्च किंवा विक्री नोंदवा'],
    daily_add_money_note: ['Seeds, labour, water and money received.','बीज, मजदूरी, पानी और मिले पैसे।','बियाणे, मजुरी, पाणी आणि मिळालेले पैसे.'],
    daily_credit: ['Money owed','उधार का हिसाब','उधारीची वही'],
    daily_credit_note: ['Who needs to pay? What do I owe?','किससे लेना है? किसे देना है?','कोणाकडून घ्यायचे? कोणाला द्यायचे?'],
    daily_sell_price: ['Check my selling price','बेचने का भाव जाँचें','विक्रीचा भाव तपासा'],
    daily_sell_note: ['What remains after transport and losses?','ढुलाई और नुकसान के बाद कितना बचेगा?','वाहतूक व नुकसान वजा करून किती उरेल?'],
    daily_public_help: ['Water and crop checks work without an account.','पानी और फसल की जाँच बिना खाते के करें।','पाणी व पिकाची मदत खात्याशिवाय मिळते.'],
    daily_login_records: ['Login to open my records','मेरी नोंदें खोलें','माझ्या नोंदी उघडा'],
    daily_create_account: ['Create account','खाता बनाएँ','खाते तयार करा'],
    daily_today_work: ["Today's work",'आज के काम','आजची कामे'],
    daily_waiting_orders: ['buyer orders to check','खरीदारों के ऑर्डर देखें','खरेदीदारांच्या मागण्या तपासा'],
    daily_due_receive: ['Due to receive','लेने की तारीख आ गई','घ्यायच्या पैशांची मुदत आली'],
    daily_due_pay: ['Due to pay','देने की तारीख आ गई','द्यायच्या पैशांची मुदत आली'],
    daily_saved_work: ['Work I wrote down','लिखे हुए काम','नोंदवलेली कामे'],
    daily_all_work: ['All work','सभी काम','सगळी कामे'],
    daily_no_work: ['No work due from your saved list. Add a task when you need a reminder.','आपकी सूची में आज का कोई काम बाकी नहीं है। याद रखने के लिए काम जोड़ें।','नोंदवलेल्या यादीत आजचं काम बाकी नाही. आठवणीसाठी काम नोंदवा.'],
    daily_review_work: ['Open the work list and check the latest field conditions before acting.','काम की सूची खोलें और काम से पहले खेत की ताज़ा स्थिति देखें।','कामाची यादी उघडा आणि काम करण्यापूर्वी शेताची सध्याची स्थिती पाहा.'],
    daily_review_field: ['Check this field again','खेत फिर जाँचें','या शेताची पुन्हा पाहणी करा'],
    daily_list_produce: ['List produce for sale','उपज बिक्री में डालें','माल विक्रीला ठेवा'],
    daily_my_produce: ['My produce','मेरी उपज','माझा विक्रीचा माल'],
    daily_incoming_orders: ['Buyer orders','खरीदारों के ऑर्डर','खरेदीदारांच्या मागण्या'],
    daily_leaf_photo: ['Check a leaf photo','पत्ते की फोटो जाँचें','पानाचा फोटो तपासा'],
    daily_buy: ['Buy farm produce','खेत की उपज खरीदें','शेतमाल खरेदी करा'],
    daily_buy_note: ['See the farmer, price and available stock.','किसान, भाव और उपलब्ध मात्रा देखें।','शेतकरी, भाव आणि उपलब्ध माल पाहा.'],
    daily_order_note: ['Check delivery or rate received produce.','डिलीवरी देखें या मिली उपज को रेटिंग दें।','पोहोचण्याची स्थिती पाहा किंवा मिळालेल्या मालाला रेटिंग द्या.'],
    daily_browse_market: ['Open the market','बाज़ार खोलें','बाजार उघडा'],
    daily_view_market: ['See all','सब देखें','सगळे पाहा'],
    daily_project_details: ['Project details','प्रोजेक्ट की जानकारी','प्रकल्पाची माहिती'],
    daily_voice_options: ['Use voice','बोलकर इस्तेमाल करें','बोलून वापरा']
  };
  if (typeof TRANSLATIONS !== 'undefined') {
    ['en','hi','mr'].forEach((lang, index) => {
      TRANSLATIONS[lang] = TRANSLATIONS[lang] || {};
      Object.entries(copy).forEach(([key, values]) => { TRANSLATIONS[lang][key] = values[index]; });
    });
  }
  function ready() { if (typeof I18n !== 'undefined') I18n.apply(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();

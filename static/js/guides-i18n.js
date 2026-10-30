Object.assign(TRANSLATIONS.en, {guide_limits: 'These are general educational crop guides. Seasons, days and yields vary by variety, location and management. Confirm soil amendments and plant treatments with your local Krishi Vigyan Kendra; follow product labels and organic certification rules.'});
Object.assign(TRANSLATIONS.hi, {guide_limits: 'ये सामान्य जानकारी के लिए फसल मार्गदर्शिकाएँ हैं। मौसम, दिन और उपज किस्म, स्थान और देखभाल के अनुसार बदलते हैं। मिट्टी के सुधार और पौधों के उपचार के लिए स्थानीय कृषि विज्ञान केंद्र से सलाह लें; उत्पाद के निर्देश और जैविक प्रमाणन नियम मानें।'});
Object.assign(TRANSLATIONS.mr, {guide_limits: 'हे सर्वसाधारण माहितीसाठी पीक मार्गदर्शक आहेत. हंगाम, दिवस आणि उत्पन्न वाण, ठिकाण आणि निगेनुसार बदलतात. माती सुधारणा आणि पीक उपचारासाठी स्थानिक कृषी विज्ञान केंद्राचा सल्ला घ्या; उत्पादनावरील सूचना आणि सेंद्रिय प्रमाणन नियम पाळा.'});
Object.assign(TRANSLATIONS.en, {guide_empty_hint: 'Crop guides are being prepared. Please check again later.'});
Object.assign(TRANSLATIONS.hi, {guide_empty_hint: 'फसल मार्गदर्शिकाएँ तैयार हो रही हैं। बाद में दोबारा देखें।'});
Object.assign(TRANSLATIONS.mr, {guide_empty_hint: 'पीक मार्गदर्शिका तयार होत आहेत. नंतर पुन्हा पाहा.'});
I18n.apply();

/* Curated background checklists, not field-specific prescriptions. */
(() => {
 const copy = {
  "guide_title": [
    "Crop guides",
    "फसल मार्गदर्शिका",
    "पीक मार्गदर्शिका"
  ],
  "guide_intro": [
    "Use these background checklists with your own field records.",
    "इन सामान्य सूचियों के साथ अपने खेत की नोंदें भी देखें।",
    "या सामान्य तपासणी याद्यांसोबत तुमच्या शेतातील नोंदीही वापरा."
  ],
  "guide_my_farm": [
    "Record my field conditions",
    "मेरे खेत की स्थिति दर्ज करें",
    "माझ्या शेताची परिस्थिती नोंदवा"
  ],
  "guide_costs": [
    "Check growing and selling costs",
    "खेती और बिक्री का खर्च जाँचें",
    "लागवड व विक्रीचा खर्च तपासा"
  ],
  "guide_general_checklist": [
    "General field checklist",
    "खेत की सामान्य जाँच सूची",
    "शेतातील सामान्य तपासणी यादी"
  ],
  "guide_filter": [
    "Show guides",
    "मार्गदर्शिका दिखाएँ",
    "मार्गदर्शिका दाखवा"
  ],
  "guide_read": [
    "Read checklist",
    "जाँच सूची पढ़ें",
    "तपासणी यादी वाचा"
  ],
  "guide_empty_hint": [
    "No guides match this season. Try all crops.",
    "इस मौसम की मार्गदर्शिका नहीं मिली। सभी फसलें देखें।",
    "या हंगामाची मार्गदर्शिका सापडली नाही. सर्व पिके पाहा."
  ],
  "guide_personal_title": [
    "What does your field need today?",
    "आज आपके खेत को क्या चाहिए?",
    "आज तुमच्या शेताला काय हवे आहे?"
  ],
  "guide_personal_note": [
    "A general guide cannot see your soil moisture or symptoms. Record an observation to get a checklist for your crop and stage, then record what changed.",
    "सामान्य मार्गदर्शिका आपकी मिट्टी या लक्षण नहीं देखती। फसल और अवस्था के अनुसार जाँच सूची पाने के लिए निरीक्षण दर्ज करें, फिर बदलाव लिखें।",
    "सामान्य मार्गदर्शिकेला तुमच्या मातीचा ओलावा किंवा लक्षणे दिसत नाहीत. पीक व अवस्थेनुसार यादी मिळवण्यासाठी पाहणी नोंदवा; नंतर झालेला बदल नोंदवा."
  ],
  "guide_original_reference": [
    "Original detailed reference (English)",
    "मूल विस्तृत संदर्भ (अंग्रेज़ी)",
    "मूळ सविस्तर संदर्भ (इंग्रजी)"
  ],
  "guide_reference_note": [
    "The original reference may include general schedules and estimated yields. They are not guarantees for your field. The concise checklist above is available in all three languages without an API.",
    "मूल संदर्भ में सामान्य समय और अनुमानित उपज हो सकती है। यह आपके खेत की गारंटी नहीं है। ऊपर की संक्षिप्त सूची तीनों भाषाओं में बिना API मिलती है।",
    "मूळ संदर्भातील वेळापत्रक व उत्पन्न हे सामान्य अंदाज आहेत; तुमच्या शेतासाठी हमी नाही. वरील छोटी यादी API शिवाय तिन्ही भाषांत उपलब्ध आहे."
  ],
  "guide_before": [
    "Before planting",
    "बुवाई से पहले",
    "लागवडीपूर्वी"
  ],
  "guide_soil_test": [
    "Use a recent soil test and local advice to plan inputs; record the report units.",
    "मिट्टी की नई जाँच और स्थानीय सलाह से खाद की योजना बनाएँ; रिपोर्ट की इकाइयाँ लिखें।",
    "अलीकडील माती परीक्षण व स्थानिक सल्ल्यावरून निविष्ठांचे नियोजन करा; अहवालातील एकके नोंदवा."
  ],
  "guide_water_plan": [
    "Check the water source and drainage before choosing the crop or planting date.",
    "फसल या बुवाई की तारीख चुनने से पहले पानी के स्रोत और निकासी को जाँचें।",
    "पीक किंवा लागवडीची तारीख ठरवण्यापूर्वी पाण्याचा स्रोत व निचरा तपासा."
  ],
  "guide_cost_plan": [
    "Estimate seed, labour, water and transport costs and find possible buyers.",
    "बीज, मज़दूरी, पानी और ढुलाई का खर्च निकालें और खरीदार खोजें।",
    "बियाणे, मजुरी, पाणी व वाहतुकीचा खर्च मोजा आणि संभाव्य खरेदीदार शोधा."
  ],
  "guide_establishment": [
    "After planting",
    "बुवाई के बाद",
    "लागवडीनंतर"
  ],
  "guide_planting_record": [
    "Record variety, planting date, field area and the crop stage you actually see.",
    "किस्म, बुवाई की तारीख, क्षेत्र और दिखाई देने वाली फसल की अवस्था लिखें।",
    "वाण, लागवडीची तारीख, शेताचे क्षेत्र व प्रत्यक्ष दिसणारी पिकाची अवस्था नोंदवा."
  ],
  "guide_emergence": [
    "Compare healthy and weak plants across the field; record uneven growth instead of guessing the cause.",
    "खेत के स्वस्थ और कमज़ोर पौधों की तुलना करें; कारण मानने के बजाय असमान बढ़वार दर्ज करें।",
    "शेतातील निरोगी व कमकुवत झाडांची तुलना करा; कारण गृहीत धरण्याऐवजी असमान वाढ नोंदवा."
  ],
  "guide_drainage": [
    "Look for standing water, blocked drains and damaged irrigation lines.",
    "जमा पानी, बंद नालियाँ और टूटी सिंचाई पाइप जाँचें।",
    "साचलेले पाणी, अडलेले नाले व खराब सिंचन नळ्या तपासा."
  ],
  "guide_growth": [
    "During growth",
    "बढ़वार के समय",
    "वाढीच्या काळात"
  ],
  "guide_scout": [
    "Inspect several places in the field. Count inspected and affected plants and photograph symptoms.",
    "खेत में कई जगह देखें। जाँचे गए और प्रभावित पौधे गिनें तथा लक्षणों की फोटो लें।",
    "शेतातील वेगवेगळ्या ठिकाणी पाहणी करा. पाहिलेली व बाधित झाडे मोजा आणि लक्षणांचे फोटो घ्या."
  ],
  "guide_root_moisture": [
    "Check moisture near the root zone and recent rainfall before deciding about irrigation.",
    "सिंचाई तय करने से पहले जड़ों के पास की नमी और हाल की बारिश देखें।",
    "पाणी देण्याचा निर्णय घेण्यापूर्वी मुळांजवळील ओलावा व अलीकडील पाऊस तपासा."
  ],
  "guide_record_inputs": [
    "Write down what you applied, the date and cost; compare the next observation before repeating it.",
    "क्या दिया, तारीख और खर्च लिखें; दोहराने से पहले अगला निरीक्षण देखें।",
    "काय दिले, तारीख व खर्च नोंदवा; पुन्हा देण्यापूर्वी पुढील पाहणीतील बदल तपासा."
  ],
  "guide_harvest": [
    "Before and after harvest",
    "कटाई से पहले और बाद में",
    "काढणीपूर्वी व नंतर"
  ],
  "guide_buyer_plan": [
    "Confirm buyer requirements, quantity, packing and transport; compare net returns.",
    "खरीदार की ज़रूरत, मात्रा, पैकिंग और ढुलाई तय करें; बची हुई राशि की तुलना करें।",
    "खरेदीदाराची गरज, प्रमाण, पॅकिंग व वाहतूक ठरवा; निव्वळ मिळणाऱ्या रकमेची तुलना करा."
  ],
  "guide_clean_harvest": [
    "Use clean tools and containers; keep damaged produce separate and follow local food-safety guidance.",
    "साफ औज़ार और डिब्बे इस्तेमाल करें; खराब उपज अलग रखें और स्थानीय खाद्य-सुरक्षा सलाह मानें।",
    "स्वच्छ अवजारे व डबे वापरा; खराब शेतमाल वेगळा ठेवा आणि स्थानिक अन्नसुरक्षा सूचना पाळा."
  ],
  "guide_review_outcomes": [
    "Record actual harvest, received price and costs, then review what worked before the next season.",
    "वास्तविक उपज, मिली कीमत और खर्च लिखें; अगले मौसम से पहले परिणाम देखें।",
    "प्रत्यक्ष शेतमाल, मिळालेला भाव व खर्च नोंदवा; पुढच्या हंगामापूर्वी काय उपयोगी पडले ते पाहा."
  ],
  "guide_season_kharif": [
    "Kharif",
    "खरीफ",
    "खरीप"
  ],
  "guide_season_rabi": [
    "Rabi",
    "रबी",
    "रब्बी"
  ],
  "guide_season_zaid": [
    "Summer / Zaid",
    "गर्मी / ज़ायद",
    "उन्हाळी"
  ],
  "guide_season_year_round": [
    "Year-round",
    "साल भर",
    "वर्षभर"
  ],
  "guide_crop_tomato": [
    "Tomato",
    "टमाटर",
    "टोमॅटो"
  ],
  "guide_crop_potato": [
    "Potato",
    "आलू",
    "बटाटा"
  ],
  "guide_crop_onion": [
    "Onion",
    "प्याज़",
    "कांदा"
  ],
  "guide_crop_rice": [
    "Rice",
    "धान",
    "भात"
  ],
  "guide_crop_wheat": [
    "Wheat",
    "गेहूँ",
    "गहू"
  ],
  "guide_crop_chilli": [
    "Chilli",
    "मिर्च",
    "मिरची"
  ],
  "guide_crop_brinjal": [
    "Brinjal",
    "बैंगन",
    "वांगी"
  ],
  "guide_crop_garlic": [
    "Garlic",
    "लहसुन",
    "लसूण"
  ],
  "guide_crop_cauliflower": [
    "Cauliflower",
    "फूलगोभी",
    "फुलकोबी"
  ],
  "guide_crop_spinach": [
    "Spinach",
    "पालक",
    "पालक"
  ],
  "guide_note_tomato": [
    "Check fruit support, leaf symptoms and water reaching the root zone; record damage before selecting a treatment.",
    "फलों का सहारा, पत्तों के लक्षण और जड़ों तक पानी जाँचें; उपचार चुनने से पहले नुकसान दर्ज करें।",
    "फळांना आधार, पानांवरील लक्षणे व मुळांपर्यंत पोहोचणारे पाणी तपासा; उपचार ठरवण्यापूर्वी नुकसान नोंदवा."
  ],
  "guide_note_potato": [
    "Check drainage and exposed or damaged tubers. Keep damaged produce separate and ask for local advice if symptoms spread.",
    "निकासी और खुले या खराब कंद जाँचें। खराब उपज अलग रखें; लक्षण बढ़ें तो स्थानीय सलाह लें।",
    "निचरा व उघडे किंवा खराब कंद तपासा. खराब माल वेगळा ठेवा; लक्षणे पसरल्यास स्थानिक सल्ला घ्या."
  ],
  "guide_note_onion": [
    "Check bulb-zone drainage and leaf symptoms. Plan harvest handling and storage for the variety and local conditions.",
    "कंद के पास निकासी और पत्तों के लक्षण देखें। किस्म और स्थानीय हालात के अनुसार कटाई और भंडारण तय करें।",
    "कंदाजवळील निचरा व पानांवरील लक्षणे पाहा. वाण व स्थानिक परिस्थितीनुसार काढणी व साठवण ठरवा."
  ],
  "guide_note_rice": [
    "Record field water conditions and crop stage. Water management depends on the variety, soil and local recommendations.",
    "खेत में पानी की स्थिति और फसल की अवस्था लिखें। पानी का प्रबंधन किस्म, मिट्टी और स्थानीय सलाह पर निर्भर है।",
    "शेतातील पाण्याची स्थिती व पिकाची अवस्था नोंदवा. पाणी व्यवस्थापन वाण, माती व स्थानिक सल्ल्यावर अवलंबून असते."
  ],
  "guide_note_wheat": [
    "Track crop stage, uneven growth and lodging. Compare moisture in healthy and affected parts before changing irrigation.",
    "फसल की अवस्था, असमान बढ़वार और गिरते पौधे देखें। सिंचाई बदलने से पहले स्वस्थ और प्रभावित हिस्सों की नमी की तुलना करें।",
    "पिकाची अवस्था, असमान वाढ व लोळलेले पीक पाहा. पाणी बदलण्यापूर्वी निरोगी व बाधित भागातील ओलाव्याची तुलना करा."
  ],
  "guide_note_chilli": [
    "Inspect leaves, flowers and fruits in several parts of the field. Count damage and confirm its cause before choosing treatment.",
    "खेत के कई हिस्सों में पत्ते, फूल और फल देखें। नुकसान गिनें और उपचार से पहले कारण की पुष्टि करें।",
    "शेतातील अनेक भागांत पाने, फुले व फळे तपासा. नुकसान मोजा व उपचारापूर्वी कारणाची खात्री करा."
  ],
  "guide_note_brinjal": [
    "Inspect growing shoots and fruits as well as leaves. Keep a dated record of damage and discuss spreading problems with an expert.",
    "पत्तों के साथ नई शाखाएँ और फल भी देखें। तारीख के साथ नुकसान लिखें और बढ़ती समस्या पर विशेषज्ञ से बात करें।",
    "पानांसोबत नवीन शेंडे व फळेही तपासा. तारीखवार नुकसान नोंदवा व पसरत असलेल्या समस्येसाठी तज्ज्ञांचा सल्ला घ्या."
  ],
  "guide_note_garlic": [
    "Look for water stagnation near bulbs and changes in the leaves. Plan curing and storage with local post-harvest advice.",
    "कंद के पास जमा पानी और पत्तों के बदलाव देखें। सुखाने और भंडारण के लिए स्थानीय कटाई-बाद की सलाह लें।",
    "कंदाजवळ साचलेले पाणी व पानांतील बदल पाहा. वाळवण व साठवणीसाठी स्थानिक काढणीनंतरचा सल्ला घ्या."
  ],
  "guide_note_cauliflower": [
    "Record leaf and head condition, planting date and weather changes. Variety and season affect head development.",
    "पत्ते और फूल की स्थिति, बुवाई की तारीख और मौसम के बदलाव लिखें। फूल की बढ़वार किस्म और मौसम पर निर्भर है।",
    "पाने व गड्ड्याची स्थिती, लागवडीची तारीख व हवामानातील बदल नोंदवा. गड्ड्याची वाढ वाण व हंगामावर अवलंबून असते."
  ],
  "guide_note_spinach": [
    "Pay attention to irrigation-water quality, clean harvest containers and leaf contamination. Follow local food-safety guidance.",
    "सिंचाई के पानी की गुणवत्ता, साफ डिब्बे और पत्तों की गंदगी पर ध्यान दें। स्थानीय खाद्य-सुरक्षा सलाह मानें।",
    "सिंचनाच्या पाण्याची गुणवत्ता, स्वच्छ डबे व पानांवरील दूषितपणा यांकडे लक्ष द्या. स्थानिक अन्नसुरक्षा सूचना पाळा."
  ]
};
 ["en","hi","mr"].forEach((lang,i) => Object.entries(copy).forEach(([key,text]) => { TRANSLATIONS[lang][key] = text[i]; }));
 I18n.apply();
})();

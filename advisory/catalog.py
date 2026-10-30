"""Reviewed interface copy and general reference sources for farm observations.

The linked organizations provide general principles. They do not validate this
application's rules, numeric triggers, diagnoses, crop suitability or yields.
"""

LANGUAGES = ('en', 'hi', 'mr')


def _labels(en, hi, mr):
    return dict(zip(LANGUAGES, (en, hi, mr)))


CROPS = {
    'tomato': _labels('Tomato', 'टमाटर', 'टोमॅटो'),
    'onion': _labels('Onion', 'प्याज', 'कांदा'),
    'soybean': _labels('Soybean', 'सोयाबीन', 'सोयाबीन'),
    'cotton': _labels('Cotton', 'कपास', 'कापूस'),
    'wheat': _labels('Wheat', 'गेहूँ', 'गहू'),
    'chickpea': _labels('Chickpea', 'चना', 'हरभरा'),
    'rice': _labels('Rice', 'धान', 'भात'),
    'other': _labels('Another crop', 'अन्य फसल', 'इतर पीक'),
}
STAGES = {
    'sowing': _labels('Sowing / establishment', 'बुवाई / अंकुरण', 'पेरणी / उगवण'),
    'vegetative': _labels('Leaf and stem growth', 'पत्ते और तने की वृद्धि', 'पाने व खोडाची वाढ'),
    'flowering': _labels('Flowering', 'फूल आना', 'फुलोरा'),
    'fruiting': _labels('Fruit / pod / grain development', 'फल / फली / दाना बनना', 'फळे / शेंगा / दाणे भरणे'),
    'harvest': _labels('Near harvest', 'कटाई के पास', 'काढणी जवळ'),
    'unknown': _labels('Not sure yet', 'अभी निश्चित नहीं', 'अजून खात्री नाही'),
}
SOILS = {
    'sandy': _labels('Sandy', 'रेतीली', 'वालुकामय'),
    'loamy': _labels('Loamy', 'दोमट', 'पोयट्याची'),
    'clay': _labels('Clay', 'चिकनी', 'चिकणमाती'),
    'unknown': _labels('Not sure', 'निश्चित नहीं', 'खात्री नाही'),
}
IRRIGATION = {
    'drip': _labels('Drip', 'टपक', 'ठिबक'),
    'flood': _labels('Surface / flood', 'सतही / बाढ़ विधि', 'पाट / प्रवाही'),
    'rainfed': _labels('Rainfed', 'वर्षा आधारित', 'पावसावर अवलंबून'),
    'other': _labels('Another method', 'अन्य तरीका', 'इतर पद्धत'),
}
MOISTURE = {
    'dry': _labels('Dry', 'सूखी', 'कोरडी'),
    'balanced': _labels('Moist, without standing water', 'नम, पानी जमा नहीं', 'ओलसर, पाणी साचलेले नाही'),
    'wet': _labels('Very wet', 'बहुत गीली', 'खूप ओली'),
    'unknown': _labels('Not checked', 'जाँच नहीं की', 'तपासलेली नाही'),
}
LEAF_SYMPTOMS = {
    'none': _labels('No visible leaf symptoms recorded', 'पत्तों पर लक्षण दर्ज नहीं', 'पानांवर लक्षणे नोंदवलेली नाहीत'),
    'yellowing': _labels('Yellowing', 'पीलापन', 'पिवळेपणा'),
    'spots': _labels('Spots', 'धब्बे', 'डाग'),
    'wilting': _labels('Wilting', 'मुरझाना', 'मरगळ'),
    'other': _labels('Other visible symptoms', 'अन्य दिखने वाले लक्षण', 'इतर दिसणारी लक्षणे'),
}
MISSING_DATA = {
    'moisture': _labels('Check moisture near the roots before deciding about water.', 'पानी का निर्णय लेने से पहले जड़ों के पास नमी जाँचें।', 'पाणी देण्याचा निर्णय घेण्यापूर्वी मुळांजवळील ओलावा तपासा.'),
    'inspection_counts': _labels('Count inspected and affected plants to track change.', 'बदलाव समझने के लिए जाँचे गए और प्रभावित पौधे गिनें।', 'बदल समजण्यासाठी तपासलेली व बाधित झाडे मोजा.'),
    'planting_date': _labels('A sowing or transplanting date will make the field history clearer.', 'बुवाई या रोपाई की तारीख से खेत का इतिहास स्पष्ट होगा।', 'पेरणी किंवा लागवडीची तारीख दिल्यास शेताची नोंद स्पष्ट होईल.'),
    'growth_stage': _labels('Confirm the current crop stage.', 'फसल की वर्तमान अवस्था की पुष्टि करें।', 'पिकाची सध्याची अवस्था निश्चित करा.'),
    'current_weather': _labels('No current local weather observation is attached.', 'वर्तमान स्थानीय मौसम का मापन जुड़ा नहीं है।', 'सध्याच्या स्थानिक हवामानाचे मापन जोडलेले नाही.'),
    'weather_refresh': _labels('The attached weather is incomplete or out of date; refresh it before using it.', 'जुड़ा मौसम अधूरा या पुराना है; उपयोग से पहले ताज़ा जानकारी लें।', 'जोडलेले हवामान अपुरे किंवा जुने आहे; वापरण्यापूर्वी ताजी माहिती घ्या.'),
    'local_crop_guidance': _labels('This crop needs local, crop-specific guidance.', 'इस फसल के लिए स्थानीय, फसल-विशेष सलाह लें।', 'या पिकासाठी स्थानिक, पीकनिहाय मार्गदर्शन घ्या.'),
    'standing_water_depth': _labels('Record the depth and duration of unwanted standing water.', 'अनचाहे जमा पानी की गहराई और अवधि दर्ज करें।', 'नको असलेल्या साचलेल्या पाण्याची खोली व कालावधी नोंदवा.'),
}

SOURCES = {
    'icar': {
        'id': 'icar', 'title': 'Indian Council of Agricultural Research',
        'url': 'https://icar.org.in/',
        'note': 'General crop and extension reference; individual field decisions require local guidance.',
        'localized_note': _labels('General crop reference; confirm advice for your field locally.', 'सामान्य फसल संदर्भ; अपने खेत के लिए स्थानीय पुष्टि लें।', 'सर्वसाधारण पीक संदर्भ; तुमच्या शेतासाठी स्थानिक खात्री करा.'),
    },
    'kvk': {
        'id': 'kvk', 'title': 'Krishi Vigyan Kendra network',
        'url': 'https://kvk.icar.gov.in/',
        'note': 'Local expert support for identifying field problems and adapting crop practices.',
        'localized_note': _labels('Local help to identify crop problems and choose appropriate action.', 'फसल की समस्या पहचानने और उचित कदम चुनने के लिए स्थानीय सहायता।', 'पिकाची अडचण ओळखण्यासाठी व योग्य कृती ठरवण्यासाठी स्थानिक मदत.'),
    },
    'fao_water': {
        'id': 'fao_water', 'title': 'FAO Land & Water',
        'url': 'https://www.fao.org/land-water/en/',
        'note': 'General soil-water management principles; this engine does not calculate crop water prescriptions.',
        'localized_note': _labels('Soil-water principles; the app does not prescribe an exact water quantity.', 'मिट्टी और पानी के सिद्धांत; ऐप पानी की सटीक मात्रा तय नहीं करता।', 'माती व पाणी व्यवस्थापनाची तत्त्वे; ॲप पाण्याचे अचूक प्रमाण ठरवत नाही.'),
    },
    'imd': {
        'id': 'imd', 'title': 'India Meteorological Department',
        'url': 'https://mausam.imd.gov.in/',
        'note': 'Check official local forecasts and warnings. Current observations are not forecasts.',
        'localized_note': _labels('Check official local forecasts and warnings before planning field work.', 'खेत का काम तय करने से पहले आधिकारिक स्थानीय पूर्वानुमान और चेतावनी देखें।', 'शेतीचे काम ठरवण्यापूर्वी अधिकृत स्थानिक अंदाज व सूचना पाहा.'),
    },
}

# Each tuple contains title, reason and a practical next action. Numeric app
# triggers are observation-review prompts, never validated disease cut-offs.
MESSAGES = {
    'waterlogging': {
        'en': ('Check unwanted standing water today', 'You reported waterlogging, so more water may worsen root-zone conditions.', 'Pause routine irrigation. Inspect safe drainage outlets and record where water is collecting. Ask the local KVK for help if plants remain stressed.'),
        'hi': ('आज अनचाहे जमा पानी की जाँच करें', 'आपने पानी जमा होना दर्ज किया है; और पानी देने से जड़ों की स्थिति बिगड़ सकती है।', 'नियमित सिंचाई रोकें। सुरक्षित निकास देखें और पानी जमा होने की जगह दर्ज करें। पौधे तनाव में रहें तो स्थानीय KVK से सलाह लें।'),
        'mr': ('आज नको असलेले साचलेले पाणी तपासा', 'तुम्ही पाणी साचल्याची नोंद केली आहे; आणखी पाणी दिल्यास मुळांजवळील स्थिती बिघडू शकते.', 'नेहमीचे पाणी देणे थांबवा. सुरक्षित निचऱ्याचे मार्ग आणि पाणी साचणाऱ्या जागा तपासा. झाडांची अडचण कायम असल्यास स्थानिक KVK चा सल्ला घ्या.'),
    },
    'paddy_excess_water': {
        'en': ('Check excess water in the rice field', 'You reported unwanted waterlogging; planned paddy water and excess flooding need different decisions.', 'Record water depth, how long it has stood, crop stage and plant condition. Inspect bunds and outlets safely; use local rice guidance before changing the water level.'),
        'hi': ('धान में अतिरिक्त पानी जाँचें', 'आपने अनचाहा पानी जमा होना दर्ज किया है; धान का नियोजित पानी और अतिरिक्त बाढ़ अलग स्थितियाँ हैं।', 'पानी की गहराई, अवधि, फसल अवस्था और पौधों की स्थिति दर्ज करें। मेड़ और निकास सुरक्षित ढंग से देखें; स्तर बदलने से पहले स्थानीय धान मार्गदर्शन लें।'),
        'mr': ('भातशेतीतील जास्त पाणी तपासा', 'तुम्ही नको असलेले पाणी साचल्याची नोंद केली आहे; भाताचे नियोजित पाणी व जास्त पूर यात फरक आहे.', 'पाण्याची खोली, कालावधी, पिकाची अवस्था व झाडांची स्थिती नोंदवा. बांध व निचरा सुरक्षितपणे पाहा; पाणीपातळी बदलण्यापूर्वी स्थानिक भात मार्गदर्शन घ्या.'),
    },
    'wet_wilting': {
        'en': ('Investigate wilting before adding more water', 'Wilting with wet soil can have several causes; it does not prove the crop needs irrigation.', 'Check roots, drainage and the spread of symptoms. Photograph affected and nearby healthy-looking plants and contact the local KVK before treatment.'),
        'hi': ('और पानी देने से पहले मुरझाने का कारण जाँचें', 'गीली मिट्टी में मुरझाने के कई कारण हो सकते हैं; इससे सिंचाई की जरूरत साबित नहीं होती।', 'जड़ें, निकास और लक्षणों का फैलाव देखें। प्रभावित और पास के सामान्य दिखने वाले पौधों की फोटो लेकर उपचार से पहले KVK से संपर्क करें।'),
        'mr': ('आणखी पाणी देण्यापूर्वी मरगळ तपासा', 'ओल्या मातीत मरगळ येण्याची अनेक कारणे असू शकतात; त्यामुळे पाणी हवेच आहे असे ठरत नाही.', 'मुळे, निचरा व लक्षणांचा प्रसार तपासा. बाधित व जवळच्या सामान्य दिसणाऱ्या झाडांचे फोटो काढा आणि उपचारापूर्वी KVK शी संपर्क साधा.'),
    },
    'conflicting_moisture': {
        'en': ('Recheck the soil observations', 'The report says both dry soil and waterlogging. Different parts or depths of the field may differ.', 'Check several locations near the root zone and record which area is dry or flooded. Use the local conditions rather than one overall label.'),
        'hi': ('मिट्टी की नोंद दोबारा जाँचें', 'रिपोर्ट में सूखी मिट्टी और पानी जमा होना दोनों हैं। अलग स्थान या गहराई की स्थिति अलग हो सकती है।', 'जड़ों के पास कई जगह जाँचकर सूखे और पानी भरे हिस्से अलग दर्ज करें। एक ही लेबल से पूरे खेत का निर्णय न लें।'),
        'mr': ('मातीची नोंद पुन्हा तपासा', 'अहवालात कोरडी माती व पाणी साचणे दोन्ही नोंदले आहे. वेगवेगळ्या जागी किंवा खोलीवर स्थिती वेगळी असू शकते.', 'मुळांजवळ अनेक ठिकाणी तपासून कोरडा व पाणी साचलेला भाग स्वतंत्र नोंदवा. एका नोंदीवरून संपूर्ण शेताचा निर्णय घेऊ नका.'),
    },
    'check_moisture': {
        'en': ('Check root-zone moisture first', 'Soil moisture was not checked, so there is not enough information for a water decision.', 'Inspect moisture below the surface at several representative spots. Record dry, moist or very wet, and look for waterlogging before scheduling irrigation.'),
        'hi': ('पहले जड़ों के पास नमी जाँचें', 'मिट्टी की नमी जाँची नहीं गई है; पानी का निर्णय लेने के लिए जानकारी पर्याप्त नहीं है।', 'कई प्रतिनिधि जगहों पर सतह के नीचे नमी देखें। सूखी, नम या बहुत गीली स्थिति दर्ज करें और सिंचाई तय करने से पहले जमा पानी देखें।'),
        'mr': ('आधी मुळांजवळील ओलावा तपासा', 'मातीचा ओलावा तपासलेला नाही; पाण्याचा निर्णय घेण्यासाठी माहिती अपुरी आहे.', 'अनेक प्रतिनिधिक जागी वरच्या थराखालील ओलावा तपासा. कोरडी, ओलसर किंवा खूप ओली स्थिती नोंदवा आणि पाणी देण्यापूर्वी पाणी साचले आहे का ते पाहा.'),
    },
    'dry_soil': {
        'en': ('Review the dry part of the field today', 'You recorded dry soil. The crop stage, root-zone moisture and available water all matter.', 'Confirm the dryness near roots and inspect plant stress. Check the water supply and local forecast, then decide with local crop guidance; no fixed water dose is calculated here.'),
        'hi': ('आज खेत के सूखे हिस्से की जाँच करें', 'आपने सूखी मिट्टी दर्ज की है। फसल अवस्था, जड़ों की नमी और उपलब्ध पानी सभी जरूरी हैं।', 'जड़ों के पास सूखापन और पौधों का तनाव जाँचें। पानी की उपलब्धता और स्थानीय पूर्वानुमान देखकर फसल-विशेष सलाह से निर्णय लें; यहाँ पानी की निश्चित मात्रा नहीं निकाली जाती।'),
        'mr': ('आज शेतातील कोरडा भाग तपासा', 'तुम्ही कोरडी माती नोंदवली आहे. पिकाची अवस्था, मुळांजवळील ओलावा व उपलब्ध पाणी महत्त्वाचे आहेत.', 'मुळांजवळचा कोरडेपणा व झाडांची स्थिती तपासा. पाणीपुरवठा आणि स्थानिक अंदाज पाहून पीकनिहाय सल्ल्याने निर्णय घ्या; येथे पाण्याचे निश्चित प्रमाण काढलेले नाही.'),
    },
    'rainfed_dry': {
        'en': ('Plan for dry conditions in the rainfed field', 'The field is rainfed and the soil was recorded as dry; irrigation may not be available.', 'Inspect root-zone moisture, conserve existing soil cover where suitable, and check a reliable local forecast. Discuss available protective irrigation or other options with local extension staff.'),
        'hi': ('वर्षा आधारित खेत में सूखे की योजना बनाएँ', 'खेत वर्षा आधारित है और मिट्टी सूखी दर्ज है; सिंचाई उपलब्ध हो यह जरूरी नहीं।', 'जड़ों की नमी देखें, उचित हो तो मिट्टी का आवरण बनाए रखें और भरोसेमंद स्थानीय पूर्वानुमान देखें। उपलब्ध सुरक्षात्मक सिंचाई या अन्य विकल्प स्थानीय कृषि अधिकारी से समझें।'),
        'mr': ('जिरायती शेतातील कोरड्या स्थितीचे नियोजन करा', 'शेत पावसावर अवलंबून आहे आणि माती कोरडी नोंदली आहे; सिंचन उपलब्ध असेलच असे नाही.', 'मुळांजवळील ओलावा पाहा, योग्य ठिकाणी जमिनीचे आच्छादन जपा आणि विश्वासार्ह स्थानिक अंदाज पाहा. उपलब्ध संरक्षित सिंचन किंवा इतर पर्यायांसाठी स्थानिक कृषी अधिकाऱ्याशी चर्चा करा.'),
    },
    'wet_soil': {
        'en': ('Recheck wet soil before the next irrigation', 'You recorded very wet soil, so a routine watering schedule may not fit today.', 'Check drainage and moisture near roots in several spots. Review the next irrigation rather than adding water only because it is the usual day.'),
        'hi': ('अगली सिंचाई से पहले गीली मिट्टी फिर जाँचें', 'मिट्टी बहुत गीली दर्ज है; नियमित पानी देने का समय आज सही हो यह जरूरी नहीं।', 'कई जगह जड़ों की नमी और निकास देखें। केवल तय दिन होने के कारण पानी देने के बजाय अगली सिंचाई की जरूरत फिर जाँचें।'),
        'mr': ('पुढील पाण्यापूर्वी ओली माती पुन्हा तपासा', 'माती खूप ओली नोंदली आहे; नेहमीचे पाण्याचे वेळापत्रक आज योग्य असेलच असे नाही.', 'अनेक जागी मुळांजवळील ओलावा व निचरा पाहा. फक्त नेहमीचा दिवस आहे म्हणून पाणी देण्याऐवजी पुढील पाण्याची गरज तपासा.'),
    },
    'paddy_water_check': {
        'en': ('Check the planned rice-field water level', 'Wet soil in a managed rice field does not by itself show harmful waterlogging.', 'Compare actual water depth, crop stage and bund condition with local rice guidance. Record unwanted excess water separately from planned paddy water.'),
        'hi': ('धान के नियोजित पानी का स्तर देखें', 'नियोजित धान के खेत में गीली मिट्टी से हानिकारक जलभराव साबित नहीं होता।', 'पानी की गहराई, फसल अवस्था और मेड़ की स्थिति स्थानीय धान मार्गदर्शन से मिलाएँ। अनचाहा अतिरिक्त पानी अलग दर्ज करें।'),
        'mr': ('भाताच्या नियोजित पाण्याची पातळी पाहा', 'व्यवस्थापित भातशेतीतील ओली माती म्हणजे हानिकारक पाणी साचणे असे ठरत नाही.', 'पाण्याची खोली, पिकाची अवस्था व बांधांची स्थिती स्थानिक भात मार्गदर्शनाशी तपासा. नको असलेले अतिरिक्त पाणी स्वतंत्र नोंदवा.'),
    },
    'leaf_check': {
        'en': ('Record the leaf symptoms before treatment', 'Visible leaf symptoms can come from several crop, water, nutrient or pest problems; this report does not identify a disease.', 'Check both sides of leaves, the stem and nearby plants. Record the pattern and take clear photos. Ask a local expert to identify the cause before choosing treatment.'),
        'hi': ('उपचार से पहले पत्तों के लक्षण दर्ज करें', 'दिखने वाले लक्षणों के कई कारण हो सकते हैं—पानी, पोषण या कीट भी। यह रिपोर्ट रोग की पहचान नहीं है।', 'पत्तों के दोनों तरफ, तना और आसपास के पौधे देखें। फैलाव दर्ज करें और साफ फोटो लें। उपचार चुनने से पहले स्थानीय विशेषज्ञ से कारण पहचानें।'),
        'mr': ('उपचारापूर्वी पानांवरील लक्षणे नोंदवा', 'दिसणाऱ्या लक्षणांची पाणी, अन्नद्रव्ये किंवा कीड अशी अनेक कारणे असू शकतात. हा अहवाल रोगाचे निदान नाही.', 'पानांच्या दोन्ही बाजू, खोड व जवळची झाडे पाहा. लक्षणांचा प्रसार नोंदवा व स्पष्ट फोटो घ्या. उपचार ठरवण्यापूर्वी स्थानिक तज्ज्ञांकडून कारण ओळखा.'),
    },
    'pest_scout': {
        'en': ('Scout the pest and its spread', 'You reported pests. Presence alone does not establish an economic treatment threshold.', 'Inspect several representative rows and leaf undersides. Count affected and inspected plants, note beneficial insects, and confirm the pest and crop stage before any treatment.'),
        'hi': ('कीट और उसका फैलाव देखें', 'आपने कीट दर्ज किए हैं। केवल मौजूदगी से आर्थिक उपचार सीमा तय नहीं होती।', 'कई प्रतिनिधि कतारों और पत्तों के नीचे देखें। प्रभावित व जाँचे गए पौधे गिनें, मित्र कीट दर्ज करें और उपचार से पहले कीट व फसल अवस्था की पुष्टि करें।'),
        'mr': ('कीड व तिचा प्रसार पाहा', 'तुम्ही कीड नोंदवली आहे. फक्त कीड दिसल्याने आर्थिक उपचार पातळी ठरत नाही.', 'अनेक प्रतिनिधिक ओळी व पानांच्या खालच्या बाजू पाहा. बाधित व तपासलेली झाडे मोजा, मित्रकीटक नोंदवा आणि उपचारापूर्वी कीड व पिकाची अवस्था निश्चित करा.'),
    },
    'unexplained_damage': {
        'en': ('Describe the affected plants', 'Some inspected plants were marked affected, but the visible problem was not described.', 'Record what changed on leaves, stems, roots or growth and where it occurs. Compare with nearby plants before assigning a cause.'),
        'hi': ('प्रभावित पौधों का विवरण जोड़ें', 'कुछ पौधे प्रभावित दर्ज हैं, लेकिन दिखने वाली समस्या का विवरण नहीं है।', 'पत्ते, तने, जड़ या बढ़वार में बदलाव और उसकी जगह दर्ज करें। कारण तय करने से पहले पास के पौधों से तुलना करें।'),
        'mr': ('बाधित झाडांचे वर्णन जोडा', 'काही तपासलेली झाडे बाधित नोंदली आहेत, पण दिसणाऱ्या समस्येचे वर्णन नाही.', 'पाने, खोड, मुळे किंवा वाढ यात झालेला बदल व जागा नोंदवा. कारण ठरवण्यापूर्वी जवळच्या झाडांशी तुलना करा.'),
    },
    'heat_check': {
        'en': ('Check crop and worker stress in the heat', 'A fresh, sourced weather observation is at least 35°C. This is a prompt to inspect conditions, not a crop-damage forecast.', 'Inspect plant stress and actual root-zone moisture. Plan strenuous work for a suitable cooler period, keep drinking water available and follow local heat warnings.'),
        'hi': ('गर्मी में पौधों और काम करने वालों की स्थिति देखें', 'ताज़ा स्रोतयुक्त मौसम मापन कम से कम 35°C है। यह जाँच का संकेत है, फसल नुकसान का पूर्वानुमान नहीं।', 'पौधों का तनाव और जड़ों की वास्तविक नमी देखें। भारी काम के लिए उचित ठंडा समय चुनें, पीने का पानी रखें और स्थानीय गर्मी चेतावनी मानें।'),
        'mr': ('उन्हात पीक व कामगारांची स्थिती तपासा', 'स्रोतासह ताजे तापमान किमान 35°C आहे. हा पाहणीचा संकेत आहे, पीक नुकसानाचा अंदाज नाही.', 'झाडांची स्थिती व मुळांजवळील प्रत्यक्ष ओलावा पाहा. जड कामासाठी योग्य थंड वेळ निवडा, पिण्याचे पाणी ठेवा आणि स्थानिक उष्णतेच्या सूचना पाळा.'),
    },
    'wind_check': {
        'en': ('Check conditions before any spraying', 'A fresh, sourced observation reports wind of at least 5 m/s. Conditions at the crop may differ.', 'Check wind in the field, product-label limits and the local forecast before any planned foliar application. Postpone work if drift or unsafe conditions are present.'),
        'hi': ('किसी भी छिड़काव से पहले स्थिति जाँचें', 'ताज़ा स्रोतयुक्त मापन में हवा कम से कम 5 m/s है। फसल के पास स्थिति अलग हो सकती है।', 'नियोजित पर्णीय छिड़काव से पहले खेत की हवा, उत्पाद के निर्देश और स्थानीय पूर्वानुमान देखें। बहाव या असुरक्षित स्थिति हो तो काम टालें।'),
        'mr': ('कोणत्याही फवारणीपूर्वी स्थिती तपासा', 'स्रोतासह ताज्या मापनात वारा किमान 5 m/s आहे. पिकाजवळची स्थिती वेगळी असू शकते.', 'नियोजित पर्णीय फवारणीपूर्वी शेतातील वारा, उत्पादनावरील मर्यादा व स्थानिक अंदाज पाहा. फवारा वाहून जाण्याचा किंवा असुरक्षित स्थितीचा धोका असल्यास काम पुढे ढकला.'),
    },
    'establishment_check': {
        'en': ('Check crop establishment', 'The field is recorded at sowing or establishment stage.', 'Walk representative rows, note germination gaps and crusting or standing water, and compare dates with the seed or nursery guidance before re-sowing.'),
        'hi': ('उगवण और पौध स्थापना देखें', 'खेत बुवाई या पौध स्थापना अवस्था में दर्ज है।', 'प्रतिनिधि कतारों में अंकुरण की खाली जगह, पपड़ी या जमा पानी देखें। दोबारा बुवाई से पहले बीज या नर्सरी के मार्गदर्शन से तारीख मिलाएँ।'),
        'mr': ('उगवण व रोपांची स्थापना पाहा', 'शेत पेरणी किंवा रोपांच्या स्थापनेच्या अवस्थेत नोंदले आहे.', 'प्रतिनिधिक ओळींत उगवणीतील रिकाम्या जागा, मातीचा पापुद्रा व साचलेले पाणी पाहा. दुबार पेरणीपूर्वी बीज किंवा रोपवाटिकेच्या मार्गदर्शनाशी तारखा तपासा.'),
    },
    'growth_check': {
        'en': ('Keep a growth and weed record', 'The crop is in its leaf and stem growth stage.', 'Inspect new growth and weed competition in a few marked spots. Record changes and previous inputs before planning another nutrient application.'),
        'hi': ('बढ़वार और खरपतवार की नोंद रखें', 'फसल पत्ते और तने की वृद्धि अवस्था में है।', 'कुछ तय जगहों पर नई बढ़वार और खरपतवार देखें। अगली पोषण सामग्री देने से पहले बदलाव और पिछला उपयोग दर्ज करें।'),
        'mr': ('वाढ व तणाची नोंद ठेवा', 'पीक पाने व खोडाच्या वाढीच्या अवस्थेत आहे.', 'काही ठरावीक जागी नवीन वाढ व तण पाहा. पुढील अन्नद्रव्ये देण्यापूर्वी बदल व आधी दिलेल्या निविष्ठा नोंदवा.'),
    },
    'flowering_check': {
        'en': ('Inspect flowering and field conditions', 'The field is recorded at flowering stage; variety and local conditions determine the correct practice.', 'Record flowering progress, plant stress and pest observations at marked spots. Check moisture and consult local crop guidance before changing inputs.'),
        'hi': ('फूल और खेत की स्थिति देखें', 'खेत फूल आने की अवस्था में है; सही तरीका किस्म और स्थानीय स्थिति पर निर्भर है।', 'तय जगहों पर फूल की बढ़त, पौधों का तनाव और कीट दर्ज करें। सामग्री बदलने से पहले नमी और स्थानीय फसल मार्गदर्शन देखें।'),
        'mr': ('फुलोरा व शेताची स्थिती पाहा', 'शेत फुलोऱ्याच्या अवस्थेत आहे; योग्य पद्धत वाण व स्थानिक स्थितीवर अवलंबून असते.', 'ठरावीक जागी फुलोऱ्याची प्रगती, झाडांची स्थिती व कीड नोंदवा. निविष्ठा बदलण्यापूर्वी ओलावा व स्थानिक पीक मार्गदर्शन तपासा.'),
    },
    'fruiting_check': {
        'en': ('Track fruit, pod or grain development', 'The crop is recorded at fruit, pod or grain development stage.', 'Record development and visible damage in the same marked spots. Review water availability and plan labour or picking needs from actual crop progress.'),
        'hi': ('फल, फली या दाने की बढ़त दर्ज करें', 'फसल फल, फली या दाना बनने की अवस्था में है।', 'वही तय जगहों पर बढ़त और दिखता नुकसान दर्ज करें। वास्तविक प्रगति के अनुसार पानी, मजदूर और तुड़ाई की जरूरत देखें।'),
        'mr': ('फळे, शेंगा किंवा दाणे भरण्याची नोंद ठेवा', 'पीक फळे, शेंगा किंवा दाणे भरण्याच्या अवस्थेत आहे.', 'त्याच ठरावीक जागी वाढ व दिसणारे नुकसान नोंदवा. प्रत्यक्ष प्रगतीनुसार पाणी, मजूर व तोडणीची गरज पाहा.'),
    },
    'harvest_plan': {
        'en': ('Plan harvest, handling and a buyer', 'The field is recorded near harvest; the calendar alone cannot confirm maturity.', 'Check crop maturity and a reliable local forecast. Confirm labour, clean packing, transport and a buyer; record expected costs before agreeing a sale.'),
        'hi': ('कटाई, संभाल और खरीदार की योजना बनाएँ', 'खेत कटाई के पास दर्ज है; केवल कैलेंडर से पकने की पुष्टि नहीं होती।', 'फसल का पकना और भरोसेमंद स्थानीय पूर्वानुमान देखें। मजदूर, साफ पैकिंग, परिवहन और खरीदार तय करें; बिक्री से पहले लागत लिखें।'),
        'mr': ('काढणी, हाताळणी व खरेदीदार ठरवा', 'शेत काढणीजवळ नोंदले आहे; फक्त दिनदर्शिकेवरून पक्वता ठरत नाही.', 'पिकाची पक्वता व विश्वासार्ह स्थानिक अंदाज पाहा. मजूर, स्वच्छ पॅकिंग, वाहतूक व खरेदीदार ठरवा; विक्री ठरवण्यापूर्वी खर्च नोंदवा.'),
    },
    'confirm_stage': {
        'en': ('Confirm the crop stage', 'The current crop stage was not recorded, so stage-specific work cannot be prioritized reliably.', 'Look at the crop and choose sowing, leaf growth, flowering, fruit or grain development, or near harvest. Ask locally if the stage is unclear.'),
        'hi': ('फसल की अवस्था तय करें', 'वर्तमान अवस्था दर्ज नहीं है, इसलिए अवस्था के काम भरोसे से तय नहीं हो सकते।', 'फसल देखकर बुवाई, पत्ती वृद्धि, फूल, फल या दाना बनना, या कटाई के पास चुनें। स्पष्ट न हो तो स्थानीय सहायता लें।'),
        'mr': ('पिकाची अवस्था ठरवा', 'सध्याची अवस्था नोंदलेली नाही; त्यामुळे अवस्थेनुसार कामांना योग्य प्राधान्य देता येत नाही.', 'पीक पाहून पेरणी, पानांची वाढ, फुलोरा, फळे किंवा दाणे भरणे किंवा काढणीजवळ ही अवस्था निवडा. खात्री नसल्यास स्थानिक मदत घ्या.'),
    },
}


def priority_copy(code):
    """Return fresh, JSON-serializable copy; callers cannot mutate the catalog."""
    return {language: dict(zip(('title', 'reason', 'action'), values))
            for language, values in MESSAGES[code].items()}

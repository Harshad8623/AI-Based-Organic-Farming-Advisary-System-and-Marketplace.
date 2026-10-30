/* Field checks, stored explanations and farmer records work without translation APIs. */
(() => {
  const copy = {
    adf_just_basics:['Name the field, choose the crop and water method. Other details can wait.','खेत का नाम, फसल और पानी का तरीका चुनें। बाकी जानकारी बाद में जोड़ सकते हैं।','शेताचे नाव, पीक आणि पाण्याची पद्धत निवडा. बाकी माहिती नंतर जोडता येईल.'],
    adf_choose_water:['Choose your water method','पानी का तरीका चुनें','पाण्याची पद्धत निवडा'],
    adf_more_field_details:['Add more field details (optional)','खेत की और जानकारी (वैकल्पिक)','शेताची अधिक माहिती (ऐच्छिक)'],
    adf_field_details:['Field details','खेत की जानकारी','शेताची माहिती'],
    adf_water_and_soil:['1. Water and soil','1. पानी और मिट्टी','१. पाणी आणि माती'],
    adf_plants_and_pests:['2. Plants and insects','2. पौधे और कीट','२. झाडे आणि किडी'],
    adf_field_options:['More field options','खेत के अन्य विकल्प','शेताचे इतर पर्याय'],
    adf_pick_field:["Choose a field for today's check.",'आज की जाँच के लिए खेत चुनें।','आजच्या पाहणीसाठी शेत निवडा.'],
    adf_simple_start:['Add a field once. Keep short checks as the season goes on.','खेत एक बार जोड़ें। मौसम के साथ छोटी जाँच दर्ज करते रहें।','शेत एकदा जोडा. हंगामभर छोटी पाहणी नोंदवत राहा.'],
    adf_private_short:['Only you can see your field records.','आपके खेत की नोंदें केवल आपको दिखती हैं।','तुमच्या शेताच्या नोंदी फक्त तुम्हालाच दिसतात.'],
    adf_first_step:['Start here','पहले यह करें','आधी हे करा'],
    adf_past_steps:['Previously suggested checks','पहले सुझाई गई जाँचें','मागे सुचवलेल्या तपासण्या'],
    adf_followup_short:['How is the field now?','खेत की हालत अब कैसी है?','आता शेताची स्थिती कशी आहे?'],
    adf_followup_simple:['After your next check, record what changed.','अगली जाँच के बाद बदलाव दर्ज करें।','पुढच्या पाहणीनंतर काय बदलले ते नोंदवा.'],
    adf_about_this_advice:['About this advice and your notes','इस सलाह के बारे में और आपकी नोंद','या सल्ल्याबद्दल आणि तुमच्या नोंदी'],
    adf_advice_limit:['These are checks based on your observations, not a confirmed disease diagnosis.','यह आपकी जानकारी पर आधारित जाँच है, रोग का पक्का निदान नहीं।','ही तुमच्या पाहणीनुसार सुचवलेली तपासणी आहे; रोगाचे निश्चित निदान नाही.'],
    adf_previous_suggestions:['Checks suggested at that time; completion is not verified.','उस समय सुझाई गई जाँचें; उनके किए जाने की पुष्टि नहीं है।','त्या वेळी सुचवलेल्या तपासण्या; त्या केल्या याची खात्री नाही.'],
    adf_stale_report:['This is a past plan or the field details changed. Record a fresh check before adding its actions.','यह पुरानी योजना है या खेत की जानकारी बदली है। काम जोड़ने से पहले नई जाँच करें।','हे जुने नियोजन आहे किंवा शेताची माहिती बदलली आहे. कामे जोडण्यापूर्वी नवीन पाहणी नोंदवा.'],
    adf_fresh_check:['Record a fresh field check','नई खेत जाँच करें','नवीन शेतपाहणी नोंदवा'],
    adf_cases_unavailable:['Past-case matching is unavailable. Your current explained plan is still shown above.','पुराने मामलों का मिलान अभी उपलब्ध नहीं है। वर्तमान योजना ऊपर दिखाई गई है।','मागील नोंदींचा साम्यशोध सध्या उपलब्ध नाही. तुमचे सध्याचे स्पष्टीकरणासह नियोजन वर दिसते.'],
    adf_title:['My fields','मेरे खेत','माझी शेती'],
    adf_intro:['Record what you see. Get a clear next step for each field.','जो दिखे वह दर्ज करें। हर खेत का अगला काम जानें।','जे दिसते ते नोंदवा. प्रत्येक शेतासाठी पुढचे काम जाणून घ्या.'],
    adf_add_field:['Add a field','खेत जोड़ें','शेत जोडा'],
    adf_active_fields:['Active fields','वर्तमान खेत','सध्याची शेते'],
    adf_archived_fields:['Archived fields','पुराने खेत','संग्रहित शेते'],
    adf_last_check:['Last check','पिछली जाँच','मागील पाहणी'],
    adf_no_checks:['No field checks recorded yet.','अभी खेत की जाँच दर्ज नहीं है।','अजून शेतपाहणीची नोंद नाही.'],
    adf_view_history:['View history','पुरानी नोंदें देखें','मागील नोंदी पाहा'],
    adf_check_field:['Check this field','इस खेत की जाँच करें','या शेताची पाहणी करा'],
    adf_no_archived:['No archived fields','कोई पुराना खेत नहीं','संग्रहित शेते नाहीत'],
    adf_first_field:['Start with your field','अपने खेत से शुरू करें','तुमच्या शेतापासून सुरुवात करा'],
    adf_first_hint:['Add the crop, growth stage and water method once. Each short field check then creates a saved action plan.','फसल, अवस्था और सिंचाई का तरीका एक बार जोड़ें। फिर छोटी जाँच से अगले कामों की नोंद बनती है।','पीक, वाढीची अवस्था आणि पाण्याची पद्धत एकदा जोडा. नंतर छोट्या पाहणीतून पुढच्या कामांची नोंद तयार होते.'],
    adf_private_note:['Your fields, observations and results are private to your account. Advice explains observations and limits; it does not confirm a disease or prescribe a chemical dose.','खेत, जाँच और परिणाम केवल आपके खाते में हैं। सलाह कारण और सीमाएँ बताती है; रोग की पुष्टि या रसायन की मात्रा नहीं बताती।','शेत, पाहणी आणि परिणाम फक्त तुमच्या खात्यात आहेत. सल्ल्यात कारणे आणि मर्यादा दिसतात; रोगाची खात्री किंवा रसायनाचा डोस दिला जात नाही.'],
    adf_back:['Back to my fields','मेरे खेत पर वापस','माझ्या शेतांकडे परत'],
    adf_edit_field:['Update field details','खेत की जानकारी बदलें','शेताची माहिती बदला'],
    adf_field_form_hint:['Enter what you know. Leave area and planting date blank if unknown.','जो पता है वही भरें। क्षेत्र और बुवाई की तारीख न पता हो तो खाली छोड़ें।','माहीत असलेली माहिती भरा. क्षेत्रफळ आणि पेरणीची तारीख माहीत नसल्यास रिकामी ठेवा.'],
    adf_field_name:['Field name','खेत का नाम','शेताचे नाव'],
    adf_name_placeholder:['e.g. North field','जैसे: उत्तर का खेत','उदा. उत्तरेकडील शेत'],
    adf_location:['Village or location (optional)','गाँव या जगह (वैकल्पिक)','गाव किंवा ठिकाण (ऐच्छिक)'],
    adf_crop:['Crop','फसल','पीक'], adf_stage:['Growth stage','फसल की अवस्था','वाढीची अवस्था'],
    adf_soil:['Soil type','मिट्टी का प्रकार','मातीचा प्रकार'], adf_irrigation:['Water method','पानी का तरीका','पाण्याची पद्धत'],
    adf_area:['Area (optional)','क्षेत्र (वैकल्पिक)','क्षेत्रफळ (ऐच्छिक)'],
    adf_decimal_help:['Use a dot for decimals, for example 2.5.','दशमलव के लिए बिंदु लगाएँ, जैसे 2.5।','दशांशासाठी टिंब वापरा, उदा. 2.5.'],
    adf_unit:['Unit','इकाई','एकक'], adf_unit_acre:['Acres','एकड़','एकर'], adf_unit_hectare:['Hectares','हेक्टेयर','हेक्टर'], adf_unit_m2:['Square metres (m²)','वर्ग मीटर (m²)','चौरस मीटर (m²)'],
    adf_planting:['Sowing or planting date (optional)','बुवाई या रोपाई की तारीख (वैकल्पिक)','पेरणी किंवा लागवडीची तारीख (ऐच्छिक)'],
    adf_save_field:['Save field','खेत सहेजें','शेत जतन करा'],
    adf_archive_notice:['This field is archived. Past reports remain available.','यह खेत पुरानी नोंद में है। पहले की रिपोर्ट उपलब्ध हैं।','हे शेत संग्रहित आहे. मागील अहवाल उपलब्ध आहेत.'],
    adf_restore_field:['Make field active','खेत फिर चालू करें','शेत पुन्हा सक्रिय करा'],
    adf_today_check:['What did you notice today?','आज खेत में क्या दिखा?','आज काय दिसले?'],
    adf_observation_hint:['Check different parts of the field. Choose only what you saw.','खेत के अलग हिस्से देखें। जो देखा वही चुनें।','शेताच्या वेगवेगळ्या भागांत पाहा. प्रत्यक्ष दिसले तेच निवडा.'],
    adf_moisture:['Soil near the roots','जड़ों के पास की मिट्टी','मुळांजवळची माती'],
    adf_moisture_unknown:['Not checked / unsure','नहीं जाँची / पता नहीं','तपासली नाही / माहीत नाही'],
    adf_moisture_dry:['Dry','सूखी','कोरडी'], adf_moisture_balanced:['Moist, not soggy','नम, पानी नहीं भरा','ओलसर, पण चिखल नाही'], adf_moisture_wet:['Wet / saturated','बहुत गीली','खूप ओली / पाण्याने भरलेली'],
    adf_symptoms:['Leaf or plant symptoms','पत्तियों या पौधे के लक्षण','पानांवर किंवा झाडावर लक्षणे'],
    adf_symptom_none:['None noticed','कोई नहीं दिखे','काही दिसली नाहीत'], adf_symptom_yellowing:['Yellowing','पीलापन','पिवळेपणा'], adf_symptom_spots:['Spots','धब्बे','डाग'], adf_symptom_wilting:['Wilting','मुरझाना','कोमेजणे'], adf_symptom_other:['Other symptoms','अन्य लक्षण','इतर लक्षणे'],
    adf_waterlogging:['Unexpected standing water?','अनचाहा पानी जमा है?','अनपेक्षित पाणी साचले आहे का?'],
    adf_pest:['Visible insects or fresh pest damage?','कीट या ताज़ा नुकसान दिख रहा है?','किडी किंवा ताजे नुकसान दिसते का?'],
    adf_yes:['Yes','हाँ','होय'], adf_no:['No','नहीं','नाही'],
    adf_optional_counts:['Add plant counts or measured rainfall (optional)','पौधों की गिनती या मापा बारिश जोड़ें (वैकल्पिक)','झाडांची संख्या किंवा मोजलेला पाऊस जोडा (ऐच्छिक)'],
    adf_inspected:['Plants checked','जाँचे गए पौधे','तपासलेली झाडे'],
    adf_affected:['Affected plants among those checked','उनमें प्रभावित पौधे','त्यांपैकी बाधित झाडे'],
    adf_recent_rain:['Measured rain in the last 24 hours (mm)','पिछले 24 घंटे में मापी बारिश (mm)','मागील 24 तासांत मोजलेला पाऊस (mm)'],
    adf_counts_hint:['Enter both plant counts, or leave both blank. Enter rain only if measured; blank means unknown.','पौधों की दोनों संख्या भरें या दोनों खाली छोड़ें। मापी बारिश ही लिखें; खाली का अर्थ अज्ञात है।','झाडांच्या दोन्ही संख्या भरा किंवा दोन्ही रिकाम्या ठेवा. पाऊस मोजला असेल तरच लिहा; रिकामे म्हणजे माहीत नाही.'],
    adf_notes:['Anything else? (optional)','और कुछ? (वैकल्पिक)','आणखी काही? (ऐच्छिक)'],
    adf_get_advice:['See what to do next','अगला काम देखें','पुढे काय करायचे ते पाहा'],
    adf_history:['Previous field checks','पिछली खेत जाँच','मागील शेतपाहण्या'], adf_open_report:['Open plan →','काम देखें →','नियोजन पाहा →'],
    adf_previous:['Previous','पिछला','मागील'], adf_next:['Next','अगला','पुढील'],
    adf_archive_field:['Archive field','खेत संग्रहित करें','शेत संग्रहित करा'],
    adf_archive_confirm:['Archive this field? All reports and results will remain available.','यह खेत संग्रहित करें? रिपोर्ट और परिणाम बने रहेंगे।','हे शेत संग्रहित करायचे? सर्व अहवाल आणि परिणाम उपलब्ध राहतील.'],
    adf_archive_hint:['Archiving keeps all past reports and results.','संग्रहित करने से पुराने अहवाल और परिणाम बने रहते हैं।','संग्रहित केल्यावर सर्व मागील अहवाल आणि परिणाम जपले जातात.'],
    adf_back_field:['Back to this field','इस खेत पर वापस','या शेताकडे परत'], adf_action_plan:['Field action plan','खेत के अगले काम','शेतासाठी पुढची कामे'],
    adf_print:['Print or save PDF','प्रिंट / PDF सहेजें','प्रिंट / PDF जतन करा'],
    adf_task_saved:['Added to your farm tasks.','आपके खेती के कामों में जोड़ा गया।','तुमच्या शेतीच्या कामांमध्ये जोडले.'],
    adf_followup_saved:['Your reported result is saved.','आपका बताया परिणाम सहेजा गया।','तुम्ही नोंदवलेला परिणाम जतन झाला.'],
    adf_engine_note:['Local decision rules explain your observations. Similar checks come from your own records. Neither is a confirmed diagnosis or a guarantee.','स्थानीय निर्णय नियम आपकी जाँच का कारण बताते हैं। समान मामले आपकी नोंदों से आते हैं। यह पक्का निदान या गारंटी नहीं है।','स्थानिक निर्णय नियम तुमच्या पाहणीचे स्पष्टीकरण देतात. समान पाहण्या तुमच्याच नोंदींतून येतात. हे निश्चित निदान किंवा हमी नाही.'],
    adf_missing_title:['Information to check next','आगे जाँचने की जानकारी','पुढे तपासायची माहिती'],
    adf_priorities:['Next steps, in order','पहले कौन सा काम करें','प्राधान्यानुसार पुढची कामे'],
    adf_severity_urgent:['Check today','आज जाँचें','आजच तपासा'], adf_severity_watch:['Watch closely','ध्यान रखें','लक्ष ठेवा'], adf_severity_routine:['Routine check','नियमित जाँच','नियमित पाहणी'],
    adf_why:['Why:','कारण:','कारण:'], adf_do_next:['Do next:','अगला काम:','पुढचे काम:'],
    adf_observations_used:['Observations used','किस जानकारी पर आधारित','कोणत्या नोंदींवर आधारित'],
    adf_task_already_saved:['Saved in my tasks','मेरे कामों में सहेजा है','माझ्या कामांमध्ये जतन आहे'], adf_save_action:['Add to my tasks','मेरे कामों में जोड़ें','माझ्या कामांमध्ये जोडा'],
    adf_no_priority:['No specific action could be derived. Add a clearer field check before making a decision.','अभी कोई खास काम नहीं सुझाया जा सका। निर्णय से पहले स्पष्ट जाँच दर्ज करें।','विशिष्ट काम ठरवता आले नाही. निर्णयापूर्वी स्पष्ट शेतपाहणी नोंदवा.'],
    adf_review_in:['Check this field again in','यह खेत फिर जाँचें,','या शेताची पुन्हा पाहणी करा:'], adf_days:['day(s)','दिन बाद','दिवसांनी'],
    adf_review_today:['Check this field again today.','इस खेत को आज फिर देखें।','या शेताची आजच पुन्हा पाहणी करा.'],
    adf_worsening_note:['If conditions worsen, contact your local KVK or extension officer sooner.','स्थिति बिगड़े तो स्थानीय कृषि विज्ञान केंद्र या अधिकारी से जल्दी संपर्क करें।','परिस्थिती बिघडल्यास स्थानिक कृषी विज्ञान केंद्र किंवा अधिकाऱ्याशी लवकर संपर्क करा.'],
    adf_cases_title:['From your previous field checks','आपकी पिछली खेत जाँच से','तुमच्या मागील शेतपाहण्यांमधून'],
    adf_cases_note:['Your past observations; a reported improvement does not prove a treatment worked.','आपकी पिछली जाँचें; सुधार दिखना उपचार का प्रमाण नहीं है।','तुमच्या मागील पाहण्या; सुधारणा नोंदवणे म्हणजे उपचाराचा परिणाम सिद्ध होत नाही.'],
    adf_cases_empty:['No sufficiently similar checks yet. Your own history will build this section.','अभी पर्याप्त मिलती-जुलती जाँच नहीं है। आपकी नोंदों से यह भाग बनेगा।','पुरेशा समान पाहण्या अजून नाहीत. तुमच्या नोंदींमधून हा भाग तयार होईल.'],
    adf_followup_title:['What happened after your next field check?','अगली जाँच के बाद क्या हुआ?','पुढच्या पाहणीनंतर काय झाले?'],
    adf_followup_note:['Record what you actually saw after acting or checking again. This is your report, not a verified treatment result.','काम या अगली जाँच के बाद वास्तव में क्या दिखा वह लिखें। यह आपका बताया परिणाम है, प्रमाणित उपचार परिणाम नहीं।','काम केल्यानंतर किंवा पुन्हा तपासल्यानंतर प्रत्यक्ष काय दिसले ते नोंदवा. हा तुमचा अनुभव आहे, पडताळलेला उपचार परिणाम नाही.'],
    adf_followup_verdict:['Field condition','खेत की स्थिति','शेताची स्थिती'], adf_choose_result:['Choose a result','परिणाम चुनें','परिणाम निवडा'],
    adf_verdict_improved:['Condition improved','स्थिति सुधरी','स्थिती सुधारली'], adf_verdict_unchanged:['No change noticed','बदलाव नहीं दिखा','बदल दिसला नाही'], adf_verdict_worse:['Condition worsened','स्थिति बिगड़ी','स्थिती बिघडली'],
    adf_followup_detail:['What changed, and what did you do? (optional)','क्या बदला और आपने क्या किया? (वैकल्पिक)','काय बदलले आणि तुम्ही काय केले? (ऐच्छिक)'], adf_save_result:['Save result','परिणाम सहेजें','परिणाम जतन करा'],
    adf_sources:['Guidance references','मार्गदर्शन के स्रोत','मार्गदर्शनाचे संदर्भ'],
    adf_source_limit:['References support general principles; they do not validate this app’s individual rules or diagnose your field.','स्रोत सामान्य सिद्धांत बताते हैं; वे इस ऐप के हर नियम को प्रमाणित नहीं करते या आपके खेत का निदान नहीं करते।','संदर्भ सर्वसाधारण तत्त्वांना आधार देतात; ते या ॲपचे स्वतंत्र नियम पडताळत नाहीत किंवा तुमच्या शेताचे निदान करत नाहीत.'],
    adf_your_notes:['Your recorded notes','आपकी नोंद','तुमच्या नोंदी'],
    adf_draft_saved:['Unsubmitted entries are saved temporarily on this device. Submit after reconnecting.','अधूरी जानकारी इस उपकरण पर कुछ समय रहती है। इंटरनेट जुड़ने पर जमा करें।','अपूर्ण माहिती या उपकरणावर तात्पुरती जतन होते. इंटरनेट जोडल्यावर पाठवा.'],
    adf_error_expired:['This form expired. Review the values and submit again.','यह फ़ॉर्म पुराना है। जानकारी जाँचकर फिर जमा करें।','हा फॉर्म कालबाह्य झाला. माहिती तपासून पुन्हा पाठवा.'],
    adf_error_number:['Enter a valid number within the shown range.','बताई सीमा में सही संख्या लिखें।','दिलेल्या मर्यादेत योग्य संख्या लिहा.'],
    adf_error_date:['Choose a valid planting date up to today.','आज तक की सही बुवाई तारीख चुनें।','आजपर्यंतची योग्य पेरणी तारीख निवडा.'],
    adf_error_field_name:['Use a field name of 2–80 characters and location up to 120 characters.','खेत का नाम 2–80 अक्षर और जगह अधिकतम 120 अक्षर रखें।','शेताचे नाव 2–80 अक्षरांचे आणि ठिकाण कमाल 120 अक्षरांचे ठेवा.'],
    adf_error_choice:['Choose one of the listed options.','दिए गए विकल्पों में से चुनें।','दिलेल्या पर्यायांपैकी निवडा.'],
    adf_error_area:['Enter a positive area, up to 100,000,000 m².','सकारात्मक क्षेत्र लिखें, अधिकतम 100,000,000 m²।','क्षेत्रफळ शून्यापेक्षा जास्त आणि कमाल 100,000,000 m² असावे.'],
    adf_error_stale:['This field changed in another page. Reload its details before saving again.','खेत की जानकारी दूसरे पृष्ठ पर बदली है। फिर सहेजने से पहले दोबारा खोलें।','शेताची माहिती दुसऱ्या पानावर बदलली आहे. पुन्हा जतन करण्यापूर्वी माहिती नव्याने उघडा.'],
    adf_error_counts:['Enter both counts: 1–10,000 checked plants, with affected plants between zero and the checked count.','दोनों संख्या लिखें: 1–10,000 जाँचे पौधे और उनमें प्रभावित पौधे।','दोन्ही संख्या लिहा: 1–10,000 तपासलेली झाडे, आणि त्यांपैकी शून्य ते तपासलेल्या संख्येइतकी बाधित झाडे.'],
    adf_error_notes:['Keep notes within 500 characters.','टिप्पणी 500 अक्षरों तक रखें।','नोंद 500 अक्षरांपर्यंत ठेवा.'],
    adf_error_observation:['These observations could not be interpreted. Check the field details and values.','इस जाँच को समझा नहीं जा सका। खेत की जानकारी और संख्या जाँचें।','या पाहणीचा अर्थ लावता आला नाही. शेताची माहिती आणि मूल्ये तपासा.']
  };
  ['en','hi','mr'].forEach((language,index) => Object.entries(copy).forEach(([key,values]) => TRANSLATIONS[language][key]=values[index]));
  const language = () => I18n.getLang();
  function apply() {
    I18n.apply();
    document.querySelectorAll('[data-localized]').forEach(element => {
      try {
        const values=JSON.parse(element.dataset.localized);
        let value=values[language()] || values.en;
        if (element.dataset.localizedPart) value=value?.[element.dataset.localizedPart];
        if (typeof value==='string' && value) element.textContent=value;
      } catch (_) { /* Preserve readable server-rendered text. */ }
    });
    document.querySelectorAll('[data-adf-language]').forEach(element => element.value=language());
    document.querySelectorAll('[data-adf-date]').forEach(element => {
      const raw=element.dataset.adfDate;
      const date=new Date(/[zZ]|[+-]\d{2}:\d{2}$/.test(raw) ? raw : raw+'Z');
      if (!Number.isNaN(date.getTime())) element.textContent=new Intl.DateTimeFormat(language()+'-IN',{day:'2-digit',month:'short',year:'numeric',timeZone:'Asia/Kolkata'}).format(date);
    });
  }
  function draftKey(owner,field) { return 'adf_draft_'+owner+'_'+field; }
  function ready() {
    apply(); I18n.onLangChange(apply);
    document.querySelectorAll('[data-adf-print]').forEach(button => button.addEventListener('click',()=>window.print()));
    let closedBeforePrint=[];
    window.addEventListener('beforeprint',()=>{
      closedBeforePrint=Array.from(document.querySelectorAll('details[data-adf-print-open]')).filter(details=>!details.open);
      closedBeforePrint.forEach(details=>{details.open=true;});
    });
    window.addEventListener('afterprint',()=>{
      closedBeforePrint.forEach(details=>{details.open=false;});
      closedBeforePrint=[];
    });
    document.querySelectorAll('[data-adf-confirm]').forEach(form => form.addEventListener('submit',event => {
      if (!window.confirm(I18n.t(form.dataset.adfConfirm))) event.preventDefault();
    }));
    const saved=document.querySelector('[data-adf-saved-owner]');
    if(saved) { try {
      const key=draftKey(saved.dataset.adfSavedOwner,saved.dataset.adfSavedField);
      const draft=JSON.parse(sessionStorage.getItem(key));
      // Visiting history must not erase a newer, unsubmitted field check.
      if(draft?.revision && draft.revision===saved.dataset.adfSavedRevision) sessionStorage.removeItem(key);
    } catch(_){} }
    const form=document.querySelector('[data-adf-draft-owner]');
    if(!form) return;
    const key=draftKey(form.dataset.adfDraftOwner,form.dataset.adfDraftField);
    const fields=['moisture','leaf_symptoms','waterlogging','pest_present','inspected_plants','affected_plants','recent_rain_mm','notes'];
    const status=document.getElementById('adf-draft-status');
    try {
      const savedDraft=JSON.parse(sessionStorage.getItem(key));
      if(savedDraft && Date.now()-savedDraft.at<2*60*60*1000 && savedDraft.at<=Date.now() && form.dataset.adfHasError!=='1') {
        fields.forEach(name => { const element=form.elements.namedItem(name); if(element && typeof savedDraft.values?.[name]==='string') element.value=savedDraft.values[name]; });
        form.elements.namedItem('draft_revision').value=savedDraft.revision || '';
        if(status) status.hidden=false;
      } else if(savedDraft) sessionStorage.removeItem(key);
    } catch(_){}
    function saveDraft() {
      const values={}; fields.forEach(name=>{const element=form.elements.namedItem(name);if(element) values[name]=element.value;});
      const revision=Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
      form.elements.namedItem('draft_revision').value=revision;
      try {sessionStorage.setItem(key,JSON.stringify({at:Date.now(),revision,values}));if(status)status.hidden=false;} catch(_){}
    }
    form.addEventListener('input',saveDraft); form.addEventListener('change',saveDraft);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',ready); else ready();
})();

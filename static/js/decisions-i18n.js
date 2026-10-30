/* Farmer-entered calculations stay available in English, Hindi and Marathi. */
(() => {
  const copy = {
    decision_title: ['Before you spend or sell', 'खर्च या बिक्री से पहले हिसाब करें', 'खर्च किंवा विक्रीपूर्वी हिशेब करा'],
    decision_intro: ['Use your own quantities, costs and quotes to compare options. These are calculations, not price or harvest forecasts.', 'अपनी मात्रा, खर्च और जाँचे हुए भाव से तुलना करें। ये गणनाएँ हैं, कीमत या उपज के पूर्वानुमान नहीं।', 'स्वतःचे प्रमाण, खर्च आणि तपासलेले दर वापरून तुलना करा. हे गणित आहे; भाव किंवा उत्पन्नाचा अंदाज वर्तवणारे मॉडेल नाही.'],
    decision_navigation: ['Calculations', 'गणनाएँ', 'हिशेबाचे पर्याय'],
    decision_sales_tab: ['Compare selling options', 'बिक्री के विकल्प देखें', 'विक्रीचे पर्याय तुलना करा'],
    decision_water_tab: ['Calculate a water volume', 'पानी की मात्रा निकालें', 'पाण्याचे प्रमाण मोजा'],
    decision_money_diary: ['My money diary', 'मेरी हिसाब डायरी', 'माझी हिशेब वही'],
    decision_sales_title: ['Farm pickup or a trip to market?', 'खेत पर बेचें या बाजार ले जाएँ?', 'शेतावर विकायचे की बाजारात न्यायचे?'],
    decision_sales_intro: ['A higher market price can leave less money after transport, fees and unsold produce.', 'बाजार का अधिक भाव भी परिवहन, शुल्क और न बिके माल के बाद कम पैसा दे सकता है।', 'बाजारात जास्त भाव असूनही वाहतूक, शुल्क आणि न विकलेला माल यामुळे कमी पैसे उरू शकतात.'],
    decision_produce_cost: ['1. Quantity and growing cost', '1. मात्रा और उत्पादन खर्च', '1. प्रमाण आणि उत्पादन खर्च'],
    decision_harvest: ['Harvest quantity', 'उपज की मात्रा', 'काढणीचे प्रमाण'],
    decision_weight_unit: ['Weight unit', 'वजन की इकाई', 'वजनाचे एकक'],
    decision_kg: ['kg', 'किलो', 'किलो'],
    decision_quintal: ['quintal (100 kg)', 'क्विंटल (100 किलो)', 'क्विंटल (100 किलो)'],
    decision_cost_source: ['Growing cost comes from', 'उत्पादन खर्च कहाँ से लें', 'उत्पादन खर्च कुठून घ्यायचा'],
    decision_manual_cost: ['An amount I enter', 'मैं राशि दर्ज करूँगा', 'मी रक्कम लिहितो'],
    decision_ledger_cost: ['My diary for one month', 'मेरी डायरी का एक महीना', 'माझ्या वहीतील एका महिन्याचा खर्च'],
    decision_growing_cost: ['Total growing cost (₹)', 'कुल उत्पादन खर्च (₹)', 'एकूण उत्पादन खर्च (₹)'],
    decision_cost_help: ['Include seeds, inputs, labour, rent and other costs you want to recover.', 'बीज, खाद, मजदूरी, किराया और वसूल करने वाले अन्य खर्च जोड़ें।', 'बियाणे, खते, मजुरी, भाडे आणि वसूल करायचे इतर खर्च समाविष्ट करा.'],
    decision_month: ['Diary month', 'डायरी का महीना', 'वहीतील महिना'],
    decision_ledger_help: ['Uses all your expense records for this month. Check that they belong to this harvest; they are not automatically crop-specific.', 'इस महीने के आपके सभी खर्च शामिल होंगे। जाँचें कि वे इसी उपज के हैं; वे अपने आप किसी एक फसल के नहीं होते।', 'या महिन्यातील तुमच्या सर्व खर्चाच्या नोंदी वापरल्या जातील. त्या याच काढणीच्या आहेत का ते तपासा; त्या आपोआप एका पिकाच्या नोंदी नसतात.'],
    decision_quotes: ['2. Your two price quotes', '2. आपके जाँचे हुए दो भाव', '2. तुम्ही तपासलेले दोन दर'],
    decision_farmgate_price: ['Farm pickup price (₹)', 'खेत पर मिलने वाला भाव (₹)', 'शेतावर मिळणारा दर (₹)'],
    decision_market_price: ['Market price (₹)', 'बाजार भाव (₹)', 'बाजारातील दर (₹)'],
    decision_price_per: ['Price per', 'भाव प्रति', 'दर प्रति'],
    decision_pickup_help: ['Farm pickup assumes the buyer collects everything and you pay no delivery charge.', 'खेत से बिक्री में खरीदार पूरा माल उठाता है और आप परिवहन खर्च नहीं देते, यह मान लिया गया है।', 'शेतावरील विक्रीत खरेदीदार सर्व माल उचलतो आणि तुम्हाला वाहतूक खर्च नाही, असे गृहीत धरले आहे.'],
    decision_quote_help: ['Enter a quote you checked yourself. Grade and payment terms can change the amount received.', 'स्वयं जाँचा हुआ भाव लिखें। गुणवत्ता और भुगतान की शर्तें मिलने वाली रकम बदल सकती हैं।', 'स्वतः खात्री केलेला दर लिहा. प्रतवारी आणि पैसे मिळण्याच्या अटींमुळे मिळणारी रक्कम बदलू शकते.'],
    decision_market_costs: ['3. Extra costs of selling at market', '3. बाजार में बेचने का अतिरिक्त खर्च', '3. बाजारात विक्रीचा अतिरिक्त खर्च'],
    decision_transport: ['Whole-trip transport (₹)', 'पूरे चक्कर का परिवहन (₹)', 'संपूर्ण फेरीचा वाहतूक खर्च (₹)'],
    decision_fees: ['Market fees and other charges (₹)', 'बाजार शुल्क और अन्य कटौती (₹)', 'बाजार शुल्क आणि इतर कपात (₹)'],
    decision_loss_percent: ['Unsold or damaged produce (%)', 'न बिका या खराब माल (%)', 'न विकलेला किंवा खराब माल (%)'],
    decision_loss_help: ['Loss means the share of this harvest you expect to remain unsold or damaged at market. Transport and fees apply once to the entire trip.', 'यह नुकसान बाजार में न बिकने या खराब होने वाली उपज का हिस्सा है। परिवहन और शुल्क पूरी फेरी के लिए एक बार घटेंगे।', 'नुकसान म्हणजे बाजारात न विकला जाणारा किंवा खराब होणारा या काढणीचा हिस्सा. वाहतूक आणि शुल्क संपूर्ण फेरीसाठी एकदाच वजा होतात.'],
    decision_compare: ['Compare my options', 'मेरे विकल्पों की तुलना करें', 'माझ्या पर्यायांची तुलना करा'],
    decision_result: ['Your calculation', 'आपका हिसाब', 'तुमचा हिशेब'],
    decision_estimate_notice: ['An estimate from your inputs. Actual harvest, buyer payment, quality and costs can differ. This calculation does not save income in your diary.', 'आपकी जानकारी पर आधारित अनुमान। वास्तविक उपज, भुगतान, गुणवत्ता और खर्च बदल सकते हैं। यह हिसाब डायरी में आय दर्ज नहीं करता।', 'तुमच्या माहितीवर आधारित अंदाज. प्रत्यक्ष काढणी, खरेदीदाराचे पैसे, गुणवत्ता आणि खर्च बदलू शकतात. हा हिशेब वहीत उत्पन्नाची नोंद करत नाही.'],
    decision_used_diary: ['Cost taken from your selected month’s expense records', 'चुने हुए महीने की खर्च नोंदों से ली गई राशि', 'निवडलेल्या महिन्यातील खर्चाच्या नोंदींमधून घेतलेली रक्कम'],
    decision_pickup: ['Buyer collects at farm', 'खरीदार खेत से उठाए', 'खरेदीदार शेतावरून माल उचलतो'],
    decision_market_trip: ['You take it to market', 'आप बाजार ले जाएँ', 'तुम्ही बाजारात माल नेता'],
    decision_gross: ['Sales value', 'बिक्री की रकम', 'विक्रीची रक्कम'],
    decision_less_growing_cost: ['Growing cost subtracted', 'घटाया गया उत्पादन खर्च', 'वजा केलेला उत्पादन खर्च'],
    decision_net: ['Estimated amount left', 'बचने वाली अनुमानित रकम', 'उरणाऱ्या रकमेचा अंदाज'],
    decision_sellable: ['Saleable quantity', 'बिकने योग्य मात्रा', 'विकता येणारे प्रमाण'],
    decision_trip_total: ['Transport + fees', 'परिवहन + शुल्क', 'वाहतूक + शुल्क'],
    decision_better_market: ['The market trip leaves more in this calculation.', 'इस हिसाब में बाजार ले जाने पर अधिक रकम बचती है।', 'या हिशेबात बाजारात नेल्यावर जास्त रक्कम उरते.'],
    decision_better_farmgate: ['Farm pickup leaves more in this calculation.', 'इस हिसाब में खेत से बेचने पर अधिक रकम बचती है।', 'या हिशेबात शेतावर विकल्यावर जास्त रक्कम उरते.'],
    decision_equal: ['Both options leave the same amount in this calculation.', 'इस हिसाब में दोनों विकल्पों में बराबर रकम बचती है।', 'या हिशेबात दोन्ही पर्यायांत सारखी रक्कम उरते.'],
    decision_difference: ['Difference', 'अंतर', 'फरक'],
    decision_choice_note: ['Also check the buyer’s reliability, grade deductions, time, and when you will receive payment before deciding.', 'फैसले से पहले खरीदार का भरोसा, गुणवत्ता की कटौती, समय और भुगतान की तारीख भी जाँचें।', 'निर्णयापूर्वी खरेदीदाराची विश्वासार्हता, प्रतवारीची कपात, लागणारा वेळ आणि पैसे कधी मिळतील हेही तपासा.'],
    decision_break_even_caption: ['Minimum selling price to cover the costs you included', 'शामिल किए खर्च की भरपाई के लिए न्यूनतम बिक्री भाव', 'समाविष्ट केलेला खर्च भरून निघण्यासाठी किमान विक्री दर'],
    decision_option: ['Option', 'विकल्प', 'पर्याय'],
    decision_break_even_kg: ['Break-even ₹/kg', 'खर्च निकलने का भाव ₹/किलो', 'खर्च भरून निघण्याचा दर ₹/किलो'],
    decision_break_even_quintal: ['Break-even ₹/quintal', 'खर्च निकलने का भाव ₹/क्विंटल', 'खर्च भरून निघण्याचा दर ₹/क्विंटल'],
    decision_effective_kg: ['Amount left per harvested kg', 'प्रति कटा किलो बची रकम', 'काढलेल्या प्रत्येक किलोमागे उरणारी रक्कम'],
    decision_sensitivity: ['What if harvest or prices are lower?', 'अगर उपज या भाव कम हो जाए?', 'काढणीचे प्रमाण किंवा दर कमी झाले तर?'],
    decision_sensitivity_note: ['These are stress tests, not forecasts. Growing cost, transport, fees and the loss percentage stay fixed. The price scenario reduces both quotes by 20%.', 'ये कठिन स्थिति के हिसाब हैं, पूर्वानुमान नहीं। उत्पादन खर्च, परिवहन, शुल्क और नुकसान का प्रतिशत वही रहता है। भाव वाले हिसाब में दोनों भाव 20% घटते हैं।', 'हे प्रतिकूल परिस्थितीचे हिशेब आहेत, भविष्यवाणी नाही. उत्पादन खर्च, वाहतूक, शुल्क आणि नुकसानीची टक्केवारी तीच राहते. दराच्या पर्यायात दोन्ही दर 20% कमी होतात.'],
    decision_scenario: ['Scenario', 'स्थिति', 'परिस्थिती'],
    decision_scenario_less_harvest: ['20% less harvest', '20% कम उपज', 'काढणीचे प्रमाण 20% कमी'],
    decision_scenario_less_price: ['Both prices 20% lower', 'दोनों भाव 20% कम', 'दोन्ही दर 20% कमी'],
    decision_scenario_both: ['Both harvest and prices 20% lower', 'उपज और दोनों भाव 20% कम', 'काढणीचे प्रमाण आणि दोन्ही दर 20% कमी'],
    decision_water_title: ['How much water does a chosen depth mean?', 'तय की गई गहराई के लिए कितना पानी होगा?', 'ठरवलेल्या खोलीसाठी किती पाणी लागेल?'],
    decision_water_intro: ['Convert your field area and a depth you already decided into litres. This tool does not decide whether irrigation is needed.', 'खेत का क्षेत्रफल और पहले से तय पानी की गहराई लीटर में बदलें। यह साधन सिंचाई की जरूरत तय नहीं करता।', 'शेताचे क्षेत्रफळ आणि आधी ठरवलेली पाण्याची खोली यांचे लिटरमध्ये रूपांतर करा. हे साधन पाणी देण्याची गरज ठरवत नाही.'],
    decision_area: ['Field area', 'खेत का क्षेत्रफल', 'शेताचे क्षेत्रफळ'],
    decision_area_unit: ['Area unit', 'क्षेत्रफल की इकाई', 'क्षेत्रफळाचे एकक'],
    decision_m2: ['m²', 'चौरस मीटर', 'चौरस मीटर'],
    decision_acre: ['acre', 'एकड़', 'एकर'],
    decision_hectare: ['hectare', 'हेक्टेयर', 'हेक्टर'],
    decision_guntha: ['guntha', 'गुंठा', 'गुंठा'],
    decision_depth: ['Chosen water depth (mm)', 'तय पानी की गहराई (mm)', 'ठरवलेली पाण्याची खोली (mm)'],
    decision_efficiency: ['Water delivery efficiency (%)', 'पानी पहुँचाने की दक्षता (%)', 'पाणी पोहोचवण्याची कार्यक्षमता (%)'],
    decision_efficiency_help: ['Your estimate of the percentage reaching the field. Do not assume 100% if delivery loses water.', 'खेत तक पहुँचने वाले पानी का आपका अनुमानित प्रतिशत। रास्ते में नुकसान हो तो 100% न मानें।', 'शेतापर्यंत पोहोचणाऱ्या पाण्याच्या प्रमाणाचा तुमचा अंदाज. पाणी वाया जात असल्यास 100% गृहीत धरू नका.'],
    decision_pump: ['Pump flow (litres/minute, optional)', 'पंप का बहाव (लीटर/मिनट, वैकल्पिक)', 'पंपाचा प्रवाह (लिटर/मिनिट, ऐच्छिक)'],
    decision_pump_help: ['Optional measured flow at this operating condition. Actual flow and efficiency can change.', 'इस स्थिति में मापा गया बहाव लिख सकते हैं। वास्तविक बहाव और दक्षता बदल सकते हैं।', 'या परिस्थितीत मोजलेला प्रवाह लिहू शकता. प्रत्यक्ष प्रवाह आणि कार्यक्षमता बदलू शकते.'],
    decision_area_note: ['Conversions: 1 acre = 4,046.8564224 m²; 1 hectare = 10,000 m²; 40 guntha = 1 acre.', 'रूपांतरण: 1 एकड़ = 4,046.8564224 m²; 1 हेक्टेयर = 10,000 m²; 40 गुंठा = 1 एकड़।', 'रूपांतरण: 1 एकर = 4,046.8564224 m²; 1 हेक्टर = 10,000 m²; 40 गुंठे = 1 एकर.'],
    decision_calculate_water: ['Calculate volume', 'पानी की मात्रा निकालें', 'पाण्याचे प्रमाण मोजा'],
    decision_water_result: ['Water calculation', 'पानी का हिसाब', 'पाण्याचा हिशेब'],
    decision_converted_area: ['Converted area', 'बदला हुआ क्षेत्रफल', 'रूपांतरित क्षेत्रफळ'],
    decision_net_water: ['Volume at the field', 'खेत पर पानी की मात्रा', 'शेतावरचे पाण्याचे प्रमाण'],
    decision_gross_water: ['Water to supply at your efficiency', 'आपकी दक्षता पर देना होगा', 'दिलेल्या कार्यक्षमतेनुसार पुरवायचे पाणी'],
    decision_pump_time: ['Calculated pump duration', 'गणना के अनुसार पंप का समय', 'हिशेबानुसार पंपाचा कालावधी'],
    decision_minutes: ['minutes', 'मिनट', 'मिनिटे'],
    decision_water_formula: ['Litres at the field = area in m² × depth in mm. Supply litres = field litres ÷ (efficiency ÷ 100). Pump minutes = supply litres ÷ measured litres per minute.', 'खेत पर लीटर = क्षेत्रफल m² × गहराई mm। देने वाला पानी = खेत के लीटर ÷ (दक्षता ÷ 100)। पंप के मिनट = देने वाला पानी ÷ मापा लीटर प्रति मिनट।', 'शेतावरचे लिटर = क्षेत्रफळ m² × खोली mm. पुरवायचे लिटर = शेतावरचे लिटर ÷ (कार्यक्षमता ÷ 100). पंपाची मिनिटे = पुरवायचे लिटर ÷ मोजलेले लिटर प्रति मिनिट.'],
    decision_water_caution: ['This arithmetic is not a watering prescription. Decide the required depth from root-zone moisture, crop stage, actual rain and qualified local advice. Stop if runoff or waterlogging occurs.', 'यह गणित पानी देने की सलाह नहीं है। जड़ के पास नमी, फसल की अवस्था, वास्तविक बारिश और स्थानीय विशेषज्ञ से गहराई तय करें। बहाव या जलभराव हो तो रोकें।', 'हे गणित म्हणजे पाणी देण्याची शिफारस नाही. मुळांजवळचा ओलावा, पिकाची अवस्था, प्रत्यक्ष पाऊस आणि स्थानिक तज्ज्ञांच्या सल्ल्याने खोली ठरवा. पाणी वाहून जात असेल किंवा साचत असेल तर थांबा.'],
    decision_error_number: ['Enter finite numbers using at most two decimal places.', 'अधिकतम दो दशमलव अंकों में सही संख्या लिखें।', 'जास्तीत जास्त दोन दशांश अंकांत योग्य संख्या लिहा.'],
    decision_error_quantity: ['Enter a positive harvest quantity, at most 10,000,000 kg after conversion, with up to four decimal places.', 'चार दशमलव अंकों तक शून्य से अधिक मात्रा लिखें; रूपांतरण के बाद अधिकतम 10,000,000 किलो।', 'चार दशांश अंकांपर्यंत शून्यापेक्षा जास्त प्रमाण लिहा; रूपांतरानंतर कमाल 10,000,000 किलो.'],
    decision_error_unit: ['Choose one of the units shown in the form.', 'फॉर्म में दी गई इकाई चुनें।', 'फॉर्ममध्ये दिलेले एकक निवडा.'],
    decision_error_cost_source: ['Choose manual cost or one month from your diary.', 'खुद दर्ज खर्च या डायरी का एक महीना चुनें।', 'स्वतः लिहिलेला खर्च किंवा वहीतील एक महिना निवडा.'],
    decision_error_cost: ['Enter costs from ₹0 to ₹999,999,999.99, with at most two decimal places.', '₹0 से ₹999,999,999.99 तक खर्च लिखें; अधिकतम दो दशमलव अंक।', '₹0 ते ₹999,999,999.99 पर्यंत खर्च लिहा; जास्तीत जास्त दोन दशांश अंक.'],
    decision_error_price: ['Enter a positive price up to ₹999,999,999.99, with at most two decimal places.', '₹999,999,999.99 तक शून्य से अधिक भाव लिखें; अधिकतम दो दशमलव अंक।', '₹999,999,999.99 पर्यंत शून्यापेक्षा जास्त दर लिहा; जास्तीत जास्त दोन दशांश अंक.'],
    decision_error_month: ['Choose a real month between 1900 and 2100.', '1900 से 2100 के बीच सही महीना चुनें।', '1900 ते 2100 मधील योग्य महिना निवडा.'],
    decision_error_empty_ledger: ['There are no expense records for your selected month. Choose another month or enter the growing cost yourself.', 'चुने महीने में आपके खर्च दर्ज नहीं हैं। दूसरा महीना चुनें या उत्पादन खर्च खुद लिखें।', 'निवडलेल्या महिन्यात तुमच्या खर्चाच्या नोंदी नाहीत. दुसरा महिना निवडा किंवा उत्पादन खर्च स्वतः लिहा.'],
    decision_error_spoilage: ['Enter a loss percentage from 0 to 99.99. A 100% loss leaves no saleable quantity.', 'नुकसान 0 से 99.99% तक लिखें। 100% नुकसान में बेचने योग्य मात्रा नहीं बचती।', 'नुकसान 0 ते 99.99% पर्यंत लिहा. 100% नुकसान झाल्यास विकण्यासाठी माल उरत नाही.'],
    decision_error_area: ['Enter a positive area with at most four decimal places; converted area must not exceed 100,000,000 m².', 'चार दशमलव अंकों तक शून्य से अधिक क्षेत्रफल लिखें; रूपांतरण के बाद अधिकतम 100,000,000 m²।', 'चार दशांश अंकांपर्यंत शून्यापेक्षा जास्त क्षेत्रफळ लिहा; रूपांतरानंतर कमाल 100,000,000 m².'],
    decision_error_depth: ['Enter a chosen depth greater than 0 and up to 500 mm, with at most two decimal places. This range is not a recommendation.', '0 से अधिक और 500 mm तक तय गहराई लिखें; अधिकतम दो दशमलव अंक। यह सीमा सलाह नहीं है।', '0 पेक्षा जास्त आणि 500 mm पर्यंत ठरवलेली खोली लिहा; जास्तीत जास्त दोन दशांश अंक. ही मर्यादा शिफारस नाही.'],
    decision_error_efficiency: ['Enter an efficiency greater than 0 and up to 100%, with at most two decimal places.', '0 से अधिक और 100% तक दक्षता लिखें; अधिकतम दो दशमलव अंक।', '0 पेक्षा जास्त आणि 100% पर्यंत कार्यक्षमता लिहा; जास्तीत जास्त दोन दशांश अंक.'],
    decision_error_pump: ['Leave pump flow blank, or enter a positive measured flow up to 1,000,000 litres/minute with at most two decimal places.', 'पंप बहाव खाली छोड़ें या 1,000,000 लीटर/मिनट तक शून्य से अधिक मापा बहाव लिखें; अधिकतम दो दशमलव अंक।', 'पंपाचा प्रवाह रिकामा ठेवा किंवा 1,000,000 लिटर/मिनिटपर्यंत शून्यापेक्षा जास्त मोजलेला प्रवाह लिहा; जास्तीत जास्त दोन दशांश अंक.'],
    decision_error_calculator: ['Choose a calculation shown on this page.', 'इस पृष्ठ की कोई गणना चुनें।', 'या पानावरील हिशेबाचा पर्याय निवडा.'],
  };
  if (typeof TRANSLATIONS !== 'undefined') {
    ['en', 'hi', 'mr'].forEach((lang, index) => {
      TRANSLATIONS[lang] = TRANSLATIONS[lang] || {};
      Object.entries(copy).forEach(([key, value]) => { TRANSLATIONS[lang][key] = value[index]; });
    });
  }
  function ready() {
    if (typeof I18n !== 'undefined') I18n.apply();
    const source = document.getElementById('decision-cost_source');
    function showCostSource() {
      document.querySelectorAll('[data-decision-cost]').forEach(element => {
        element.hidden = element.dataset.decisionCost !== source.value;
      });
      const manual = document.getElementById('decision-cultivation_cost');
      if (manual) manual.required = source.value === 'manual';
    }
    if (source) { source.addEventListener('change', showCostSource); showCostSource(); }
    const focus = document.getElementById('decision-error') || document.getElementById('sales-result') || document.getElementById('water-result');
    if (focus) focus.focus({preventScroll: false});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();

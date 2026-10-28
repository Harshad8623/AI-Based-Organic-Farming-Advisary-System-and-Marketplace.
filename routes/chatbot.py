"""Farming questions with a clearly labelled, multilingual offline fallback."""

import re
import requests
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')
SUPPORTED_LANGUAGES = ('en', 'hi', 'mr')
MAX_QUESTION_LENGTH = 500

# These are general educational steps, not crop-specific prescriptions.
# Match native-language questions even when a farmer has changed the UI language.
TOPIC_KEYWORDS = {
    'pest': ('pest', 'insect', 'aphid', 'whitefly', 'कीट', 'कीड', 'मावा', 'माशी'),
    'disease': ('disease', 'blight', 'rust', 'yellow leaf', 'रोग', 'करपा', 'बीमारी', 'पिवळ'),
    'fertilizer': ('fertiliz', 'fertilis', 'compost', 'manure', 'खाद', 'खत', 'कंपोस्ट', 'जीवामृत'),
    'water': ('water', 'irrigat', 'mulch', 'पानी', 'पाणी', 'सिंचन', 'सिंचाई', 'ठिबक'),
    'soil': ('soil', 'ph', 'मिट्टी', 'माती', 'मृदा'),
    'weather': ('weather', 'rain', 'forecast', 'मौसम', 'हवामान', 'पाऊस', 'बारिश'),
    'crop': ('crop', 'sow', 'seed', 'फसल', 'पीक', 'पिक', 'पेरणी', 'बुवाई', 'बीज'),
}

LOCAL_GUIDANCE = {
    'en': {
        'intro': 'General farming guidance. Confirm crop-specific decisions with your local Krishi Vigyan Kendra (KVK).',
        'pest': '• Inspect both sides of affected leaves and identify the pest before treatment.\n• Record which crop, growth stage and how many plants are affected.\n• Use suitable monitoring traps and protect beneficial insects.\n• If a treatment is needed, follow the registered product label and local advice; organic products also have precautions.',
        'disease': '• A photo or short description cannot confirm a disease. Note the crop, symptoms, recent rain and whether damage is spreading.\n• Avoid moving contaminated tools or affected planting material to healthy areas.\n• Ask your KVK or plant clinic to identify the cause before applying a treatment.\n• Nutrient stress and pests can look similar to disease.',
        'fertilizer': '• Use a recent soil test and crop requirements to plan nutrients.\n• Use mature, well-decomposed compost; nutrient content varies between materials.\n• Record applications in your farm notebook to avoid repeated or excessive inputs.\n• Ask your KVK for crop-specific amounts and safe handling advice.',
        'water': '• Check moisture in the crop root zone before watering; the surface alone can be misleading.\n• Consider crop stage, soil type and a reliable local forecast.\n• Inspect drip lines for leaks and blockages; use suitable mulch to reduce evaporation.\n• Avoid waterlogging and adjust irrigation after actual rainfall.',
        'soil': '• Collect a representative soil sample using your testing laboratory’s instructions.\n• Use the laboratory’s units and crop-specific interpretation for pH and nutrients.\n• Add suitable mature organic matter and protect soil from erosion.\n• Avoid working very wet soil and plan rotation with locally suitable crops.',
        'weather': '• Check an official local forecast and its update time before field work.\n• Current weather readings are not a forecast and do not provide a rain probability.\n• Combine rainfall observations with root-zone soil moisture before changing irrigation.\n• Follow local severe-weather alerts; do not spray in unsuitable wind or rain.',
        'crop': '• Compare crops using your location, season, irrigation, soil test, labour and local demand.\n• Ask your KVK about locally adapted varieties and sowing windows.\n• Plan rotation to reduce repeated pest and nutrient problems.\n• The crop suggestion tool is a demonstration model, not a field-validated planting recommendation.',
        'default': 'I can share basic guidance about soil, water, pests, diseases, nutrients and crop planning.\n\nChoose a topic below. For tailored advice, include your crop, location, crop age and what you observed. Offline guidance is a fixed topic guide and does not diagnose your field.',
        'empty': 'Please type a farming question.',
        'long': 'Please keep your question within 500 characters.',
        'invalid': 'Send a JSON object with a text question.',
        'unavailable': 'The AI service is unavailable. Here is the local topic guide instead.',
        'ai_notice': 'AI-generated guidance may be incorrect. Verify treatments and important decisions with your KVK.',
    },
    'hi': {
        'intro': 'यह खेती की सामान्य जानकारी है। फसल से जुड़े निर्णय अपने स्थानीय कृषि विज्ञान केंद्र (KVK) से जाँचें।',
        'pest': '• उपचार से पहले प्रभावित पत्तियों के दोनों ओर देखकर कीट पहचानें।\n• फसल, उसकी उम्र और प्रभावित पौधों की संख्या लिखें।\n• सही निगरानी जाल इस्तेमाल करें और लाभकारी कीटों की रक्षा करें।\n• उपचार जरूरी हो तो पंजीकृत उत्पाद का लेबल और स्थानीय सलाह मानें। जैविक उत्पादों में भी सावधानी जरूरी है।',
        'disease': '• केवल फोटो या छोटे विवरण से रोग की पुष्टि नहीं होती। फसल, लक्षण, हाल की बारिश और फैलाव की जानकारी लिखें।\n• दूषित औजार या प्रभावित पौधे स्वस्थ क्षेत्र में न ले जाएँ।\n• उपचार से पहले कृषि विज्ञान केंद्र या पौध रोग विशेषज्ञ से कारण जाँचें।\n• पोषक तत्वों की कमी और कीटों के लक्षण रोग जैसे दिख सकते हैं।',
        'fertilizer': '• हाल की मिट्टी जाँच और फसल की जरूरत के अनुसार पोषण की योजना बनाएँ।\n• अच्छी तरह सड़ी खाद लें; अलग-अलग खाद में पोषक मात्रा अलग होती है।\n• बार-बार या ज्यादा खाद डालने से बचने के लिए खेत की डायरी में उपयोग लिखें।\n• सही मात्रा और सुरक्षित उपयोग के लिए कृषि विज्ञान केंद्र से सलाह लें।',
        'water': '• सिंचाई से पहले जड़ क्षेत्र की नमी जाँचें; केवल ऊपरी मिट्टी देखकर निर्णय न लें।\n• फसल की अवस्था, मिट्टी का प्रकार और विश्वसनीय स्थानीय पूर्वानुमान देखें।\n• ड्रिप पाइप में रिसाव और रुकावट जाँचें; उपयुक्त मल्च से वाष्पीकरण कम करें।\n• जलभराव से बचें और हुई बारिश के अनुसार सिंचाई बदलें।',
        'soil': '• प्रयोगशाला के निर्देशों के अनुसार खेत से मिट्टी का प्रतिनिधि नमूना लें।\n• pH और पोषक तत्वों के लिए प्रयोगशाला की इकाइयाँ और फसल-विशेष सलाह मानें।\n• उपयुक्त सड़ी खाद मिलाएँ और मिट्टी का कटाव रोकें।\n• बहुत गीली मिट्टी में जुताई न करें और स्थानीय फसलों का चक्र बनाएँ।',
        'weather': '• खेत का काम करने से पहले आधिकारिक स्थानीय पूर्वानुमान और उसका समय देखें।\n• वर्तमान मौसम का मापन भविष्यवाणी या बारिश की संभावना नहीं है।\n• सिंचाई बदलने से पहले हुई बारिश और जड़ क्षेत्र की नमी देखें।\n• गंभीर मौसम की स्थानीय चेतावनी मानें; तेज हवा या बारिश में छिड़काव न करें।',
        'crop': '• स्थान, मौसम, पानी, मिट्टी जाँच, श्रम और स्थानीय माँग देखकर फसल चुनें।\n• उपयुक्त किस्म और बुवाई के समय के लिए कृषि विज्ञान केंद्र से पूछें।\n• कीट और पोषक समस्याएँ कम करने के लिए फसल चक्र बनाएँ।\n• फसल सुझाव का मॉडल केवल प्रदर्शन के लिए है; यह खेत में प्रमाणित बुवाई सलाह नहीं है।',
        'default': 'मैं मिट्टी, पानी, कीट, रोग, खाद और फसल नियोजन की सामान्य जानकारी दे सकता हूँ।\n\nनीचे विषय चुनें। व्यक्तिगत सलाह के लिए फसल, स्थान, उम्र और लक्षण बताएँ। ऑफलाइन जानकारी एक तय विषय मार्गदर्शिका है, खेत का निदान नहीं।',
        'empty': 'कृपया खेती का प्रश्न लिखें।',
        'long': 'कृपया प्रश्न 500 अक्षरों तक रखें।',
        'invalid': 'पाठ प्रश्न वाला JSON ऑब्जेक्ट भेजें।',
        'unavailable': 'AI सेवा उपलब्ध नहीं है। इसके बदले स्थानीय विषय मार्गदर्शिका दी गई है।',
        'ai_notice': 'AI की जानकारी गलत हो सकती है। उपचार और महत्वपूर्ण निर्णय कृषि विज्ञान केंद्र से जाँचें।',
    },
    'mr': {
        'intro': 'ही शेतीविषयक सामान्य माहिती आहे. पिकाबाबत निर्णय घेण्यापूर्वी स्थानिक कृषी विज्ञान केंद्राशी (KVK) चर्चा करा.',
        'pest': '• उपाय करण्यापूर्वी बाधित पानांच्या दोन्ही बाजू पाहून कीड ओळखा.\n• पीक, वाढीची अवस्था आणि बाधित झाडांची संख्या नोंदवा.\n• योग्य निरीक्षण सापळे वापरा आणि उपयुक्त कीटक जपा.\n• उपचार आवश्यक असल्यास नोंदणीकृत उत्पादनाचे लेबल आणि स्थानिक सल्ला पाळा. सेंद्रिय उत्पादनांसाठीही काळजी आवश्यक असते.',
        'disease': '• केवळ फोटो किंवा छोट्या वर्णनावरून रोगाची खात्री होत नाही. पीक, लक्षणे, अलीकडील पाऊस आणि प्रसार यांची नोंद करा.\n• दूषित अवजारे किंवा बाधित रोपे निरोगी भागात नेऊ नका.\n• उपचारापूर्वी कृषी विज्ञान केंद्र किंवा वनस्पती रोग तज्ज्ञांकडून कारण तपासा.\n• अन्नद्रव्यांची कमतरता आणि किडींची लक्षणे रोगासारखी दिसू शकतात.',
        'fertilizer': '• अलीकडील माती परीक्षण आणि पिकाची गरज पाहून अन्नद्रव्यांचे नियोजन करा.\n• पूर्ण कुजलेले कंपोस्ट वापरा; वेगवेगळ्या खतातील अन्नद्रव्यांचे प्रमाण बदलते.\n• वारंवार किंवा जास्त खत देणे टाळण्यासाठी शेतवहीत वापर नोंदवा.\n• योग्य प्रमाण आणि सुरक्षित वापरासाठी कृषी विज्ञान केंद्राचा सल्ला घ्या.',
        'water': '• पाणी देण्यापूर्वी मुळांच्या क्षेत्रातील ओलावा तपासा; केवळ वरची माती पाहू नका.\n• पिकाची अवस्था, मातीचा प्रकार आणि विश्वासार्ह स्थानिक अंदाज विचारात घ्या.\n• ठिबक नळ्यांतील गळती आणि अडथळे तपासा; योग्य आच्छादनाने बाष्पीभवन कमी करा.\n• पाणी साचू देऊ नका आणि प्रत्यक्ष पडलेल्या पावसानुसार सिंचन बदला.',
        'soil': '• प्रयोगशाळेच्या सूचनेनुसार शेतातील मातीचा प्रातिनिधिक नमुना घ्या.\n• pH आणि अन्नद्रव्यांसाठी प्रयोगशाळेची एकके आणि पिकानुसार सल्ला वापरा.\n• योग्य कुजलेले सेंद्रिय खत द्या आणि मातीची धूप थांबवा.\n• खूप ओल्या मातीत मशागत टाळा आणि स्थानिक पिकांची फेरपालट ठरवा.',
        'weather': '• शेतातील कामापूर्वी अधिकृत स्थानिक हवामान अंदाज आणि त्याची वेळ तपासा.\n• सध्याच्या हवामानाचे मापन म्हणजे भविष्याचा अंदाज किंवा पावसाची शक्यता नाही.\n• सिंचन बदलण्यापूर्वी प्रत्यक्ष पाऊस आणि मुळांजवळील ओलावा पाहा.\n• गंभीर हवामानाच्या स्थानिक सूचना पाळा; जोरदार वारा किंवा पावसात फवारणी टाळा.',
        'crop': '• स्थान, हंगाम, पाणी, माती परीक्षण, मजूर आणि स्थानिक मागणी यांचा विचार करून पीक निवडा.\n• योग्य वाण आणि पेरणीच्या कालावधीसाठी कृषी विज्ञान केंद्राला विचारा.\n• कीड आणि अन्नद्रव्यांच्या समस्या कमी करण्यासाठी पीक फेरपालट करा.\n• पीक सुचवणारे मॉडेल केवळ प्रात्यक्षिक आहे; शेतात पडताळलेला पेरणीचा सल्ला नाही.',
        'default': 'मी माती, पाणी, कीड, रोग, खत आणि पीक नियोजनाची सामान्य माहिती देऊ शकतो.\n\nखाली विषय निवडा. वैयक्तिक सल्ल्यासाठी पीक, स्थान, वय आणि लक्षणे सांगा. ऑफलाइन माहिती ही ठरलेली विषय मार्गदर्शिका आहे; शेताचे निदान नाही.',
        'empty': 'कृपया शेतीविषयक प्रश्न लिहा.',
        'long': 'कृपया प्रश्न 500 अक्षरांपर्यंत ठेवा.',
        'invalid': 'मजकूर प्रश्न असलेला JSON ऑब्जेक्ट पाठवा.',
        'unavailable': 'AI सेवा उपलब्ध नाही. त्याऐवजी स्थानिक विषय मार्गदर्शिका दिली आहे.',
        'ai_notice': 'AI ची माहिती चुकीची असू शकते. उपचार आणि महत्त्वाचे निर्णय कृषी विज्ञान केंद्राकडून तपासून घ्या.',
    },
}

SYSTEM_CONTEXT = (
    'You are a general farming information assistant for Indian farmers, not a plant diagnostician. '
    'Use plain language and short bullets, at most 200 words. Ask for crop, location and growth stage '
    'when needed. Distinguish uncertainty from facts. Do not invent weather, prices, yields, sources, '
    'accuracy claims or treatment doses. Do not recommend unverified home remedies, raw manure sprays, '
    'or blanket chemical or nutrient treatments. For treatment decisions recommend local KVK advice '
    'and registered product labels, including organic certification requirements. A crop demonstration '
    'model or leaf photo cannot establish the right planting or treatment decision. '
)


def _gemini_response(question, lang='en'):
    """One bounded request; do not leak credential-bearing provider errors."""
    api_key = (current_app.config.get('GEMINI_API_KEY') or '').strip()
    if not api_key:
        raise ValueError('AI service is not configured')
    language = {'en': 'English', 'hi': 'Hindi', 'mr': 'Marathi'}[lang]
    response = requests.post(
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent',
        headers={'x-goog-api-key': api_key},
        json={
            'systemInstruction': {'parts': [{'text': SYSTEM_CONTEXT + f'Respond in {language}.'}]},
            'contents': [{'role': 'user', 'parts': [{'text': question}]}],
            'generationConfig': {'maxOutputTokens': 1200},
        },
        timeout=(3, 12),
    )
    response.raise_for_status()
    data = response.json()
    try:
        candidate = data['candidates'][0]
        if candidate.get('finishReason') != 'STOP':
            raise ValueError('AI response was incomplete')
        parts = candidate['content']['parts']
        answer = '\n'.join(part['text'] for part in parts
                           if isinstance(part.get('text'), str) and not part.get('thought')).strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        raise ValueError('AI response was incomplete') from None
    if not answer or len(answer) > 12000:
        raise ValueError('AI response was empty or too long')
    return answer


def _fallback_response(question, lang='en'):
    """Deterministic educational guidance, with no network dependency."""
    messages = LOCAL_GUIDANCE.get(lang, LOCAL_GUIDANCE['en'])
    text = question.casefold()
    for topic, words in TOPIC_KEYWORDS.items():
        # English stems match only at a word boundary: “grain” must not be
        # classified as “rain”, while “irrigation” still matches “irrigat”.
        if any(re.search(r'\b' + re.escape(word), text) if word.isascii() else word in text
               for word in words):
            return messages['intro'] + '\n\n' + messages[topic]
    return messages['default']


@chatbot_bp.route('/')
@login_required
def chat():
    return render_template('chatbot/chat.html', gemini_active=bool((current_app.config.get('GEMINI_API_KEY') or '').strip()))


@chatbot_bp.route('/ask', methods=['POST'])
@login_required
def ask():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(answer=LOCAL_GUIDANCE['en']['invalid'], source='validation'), 400
    lang = data.get('lang', 'en')
    if not isinstance(lang, str) or lang not in SUPPORTED_LANGUAGES:
        lang = 'en'
    messages = LOCAL_GUIDANCE[lang]
    question = data.get('question')
    if not isinstance(question, str):
        return jsonify(answer=messages['invalid'], source='validation'), 400
    question = question.strip()
    if not question:
        return jsonify(answer=messages['empty'], source='validation'), 400
    if len(question) > MAX_QUESTION_LENGTH:
        return jsonify(answer=messages['long'], source='validation'), 400

    if (current_app.config.get('GEMINI_API_KEY') or '').strip():
        try:
            answer = _gemini_response(question, lang)
            return jsonify(answer=answer, source='gemini', notice=messages['ai_notice'], lang=lang)
        except (requests.RequestException, ValueError, TypeError, KeyError):
            # Never log exception strings: they may contain upstream URLs or credentials.
            current_app.logger.warning('Farming AI service unavailable; using local topic guidance.')
            return jsonify(answer=_fallback_response(question, lang), source='fallback',
                           notice=messages['unavailable'], lang=lang)
    return jsonify(answer=_fallback_response(question, lang), source='fallback', lang=lang)

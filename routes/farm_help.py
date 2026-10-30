"""Short, account-free checks for everyday field problems.

These checks deliberately do not save data or infer weather, diagnosis or a
water dose. The same observation engine used by saved field checks supplies
the explanation; unreported conditions remain unreported.
"""
from flask import Blueprint, render_template, request

from advisory.catalog import CROPS, MOISTURE, LEAF_SYMPTOMS
from advisory.engine import analyze_context


farm_help_bp = Blueprint('farm_help', __name__, url_prefix='/farm-help')
PROBLEMS = ('water', 'plant', 'pest')
UNKNOWN_CHOICES = ('unknown', '0', '1')


def _step(code, en, hi, mr):
    copy = {language: dict(zip(('title', 'reason', 'action'), values))
            for language, values in zip(('en', 'hi', 'mr'), (en, hi, mr))}
    return dict(code=code, severity='watch', localized=copy, **copy['en'])


RECHECK_WATER = _step('recheck_water',
    ('Recheck the roots before watering', 'You reported moist soil. A schedule alone does not show that the crop needs more water.', 'Check moisture below the surface in several parts of the field and look for standing water. Use crop-stage and local irrigation guidance before adding water.'),
    ('पानी देने से पहले जड़ों के पास फिर देखें', 'आपने मिट्टी में नमी बताई है। केवल तय समय से अतिरिक्त पानी की जरूरत नहीं पता चलती।', 'खेत की अलग जगहों पर सतह के नीचे नमी और जमा पानी देखें। अतिरिक्त पानी देने से पहले फसल की अवस्था और स्थानीय सिंचाई सलाह देखें।'),
    ('पाणी देण्याआधी मुळांजवळ पुन्हा तपासा', 'तुम्ही माती ओलसर असल्याचे सांगितले आहे. केवळ ठरलेली वेळ झाली म्हणून अधिक पाणी आवश्यक असतेच असे नाही.', 'शेताच्या वेगवेगळ्या भागांत पृष्ठभागाखालील ओलावा आणि साचलेले पाणी तपासा. अधिक पाणी देण्यापूर्वी पिकाची अवस्था आणि स्थानिक सिंचन मार्गदर्शन पाहा.'))
CHECK_STANDING = _step('check_standing_water',
    ('First check for unwanted standing water', 'Whether water is collecting has not been checked. Soil moisture alone is not enough for this water decision.', 'Walk through several parts of the field and check low spots and drainage safely. Record any unwanted standing water, then review the water decision with the crop stage and root-zone moisture.'),
    ('पहले जमा पानी देखें', 'पानी जमा है या नहीं, यह नहीं देखा गया। केवल मिट्टी की नमी से पानी का निर्णय पूरा नहीं होता।', 'खेत की अलग जगहों, निचले हिस्सों और निकास को सुरक्षित ढंग से देखें। अनचाहा जमा पानी दर्ज करें, फिर फसल की अवस्था और जड़ों के पास नमी के साथ निर्णय देखें।'),
    ('आधी साचलेलं पाणी तपासा', 'पाणी साचलं आहे का हे तपासलेलं नाही. फक्त मातीचा ओलावा पाण्याचा निर्णय घेण्यासाठी पुरेसा नाही.', 'शेताच्या वेगवेगळ्या भागांत, सखल जागी आणि निचऱ्याजवळ सुरक्षितपणे पाहा. अनावश्यक साचलेलं पाणी नोंदवा. त्यानंतर पिकाची अवस्था आणि मुळांजवळचा ओलावा धरून निर्णय तपासा.'))
INSPECT_PLANT = _step('inspect_plant',
    ('Look closely at a few affected plants', 'No specific leaf symptom was selected. A useful next step needs a clearer observation.', 'Compare affected and healthy plants in different parts of the field. Note whether leaves are yellow, spotted or wilted, check root-zone moisture, and take clear photos for your local KVK.'),
    ('कुछ प्रभावित पौधों को पास से देखें', 'कोई खास लक्षण नहीं चुना गया। अगला कदम तय करने के लिए स्पष्ट जाँच चाहिए।', 'खेत की अलग जगहों के प्रभावित और स्वस्थ पौधों की तुलना करें। पीलापन, धब्बे या मुरझाना और जड़ों के पास नमी देखें। स्थानीय कृषि विज्ञान केंद्र के लिए साफ फोटो लें।'),
    ('काही बाधित झाडे जवळून पाहा', 'ठरावीक लक्षण निवडलेले नाही. पुढचे काम ठरवण्यासाठी स्पष्ट पाहणी आवश्यक आहे.', 'शेताच्या वेगवेगळ्या भागांतील बाधित व निरोगी झाडांची तुलना करा. पिवळेपणा, डाग किंवा मरगळ आणि मुळांजवळचा ओलावा तपासा. स्थानिक कृषी विज्ञान केंद्रासाठी स्पष्ट फोटो घ्या.'))
INSPECT_PEST = _step('inspect_pest',
    ('Check for insects and fresh damage', 'Visible insects or fresh damage have not been confirmed. That does not establish that pests are absent.', 'Look under leaves, on new shoots and in several parts of the field. Record insects and fresh damage separately; keep clear photos or a safe sample for identification before choosing any treatment.'),
    ('कीट और ताजा नुकसान देखें', 'दिखने वाले कीट या ताजे नुकसान की पुष्टि नहीं हुई। इससे कीट न होने का निष्कर्ष नहीं निकलता।', 'पत्तियों के नीचे, नई बढ़वार पर और खेत की अलग जगहों पर देखें। कीट और ताजा नुकसान अलग लिखें; उपचार चुनने से पहले पहचान के लिए साफ फोटो या सुरक्षित नमूना रखें।'),
    ('कीड आणि ताजे नुकसान तपासा', 'दिसणारी कीड किंवा ताजे नुकसान याची खात्री झालेली नाही. याचा अर्थ कीड नाही असा होत नाही.', 'पानांच्या खाली, नवीन फुटव्यांवर आणि शेताच्या वेगवेगळ्या भागांत पाहा. कीड व ताजे नुकसान वेगवेगळे नोंदवा; उपाय निवडण्याआधी ओळख पटवण्यासाठी स्पष्ट फोटो किंवा सुरक्षित नमुना ठेवा.'))


def _values():
    source = request.form if request.method == 'POST' else request.args
    return {key: source.get(key, default) for key, default in (
        ('problem', 'water'), ('crop', 'other'), ('moisture', 'unknown'),
        ('waterlogging', 'unknown'), ('leaf_symptoms', 'none'),
        ('pest_present', 'unknown'))}


def _check(values):
    choices = {'problem': PROBLEMS, 'crop': CROPS, 'moisture': MOISTURE,
               'waterlogging': UNKNOWN_CHOICES, 'leaf_symptoms': LEAF_SYMPTOMS,
               'pest_present': UNKNOWN_CHOICES}
    return all(values[key] in allowed and len(request.form.getlist(key)) <= 1
               for key, allowed in choices.items())


def _answer(values):
    observation = {
        'moisture': values['moisture'],
        'waterlogging': values['waterlogging'] == '1',
        'leaf_symptoms': values['leaf_symptoms'],
        'pest_present': values['pest_present'] == '1',
    }
    report = analyze_context({'crop': values['crop']}, observation)
    priorities = report['priorities']
    urgent = [item for item in priorities if item['severity'] == 'urgent']
    specific = [item for item in priorities if item['category'] != 'planning']
    if values['waterlogging'] == 'unknown':
        # False is only the engine's absence-of-positive-report input; it is
        # never evidence that this farmer checked and found no standing water.
        specific = [item for item in specific if item['code'] not in
                    ('dry_soil', 'rainfed_dry', 'wet_soil', 'paddy_water_check')]
    if urgent:
        primary = urgent[0]
    elif values['problem'] == 'water':
        if values['waterlogging'] == 'unknown' and values['moisture'] != 'unknown':
            primary = CHECK_STANDING
        else:
            primary = next((item for item in specific if item['category'] == 'water'), RECHECK_WATER)
    elif values['problem'] == 'plant':
        primary = next((item for item in specific if item['category'] == 'crop_health'), INSPECT_PLANT)
    else:
        primary = next((item for item in specific if item['code'] == 'pest_scout'), INSPECT_PEST)
    others = [item for item in specific if item['code'] != primary['code']][:3]
    return primary, others, report


@farm_help_bp.route('', methods=['GET', 'POST'])
@farm_help_bp.route('/', methods=['GET', 'POST'])
def index():
    values = _values()
    error, primary, others, report = None, None, [], None
    status = 200
    if not _check(values):
        error, status = 'fh_invalid', 400
        # Never use untrusted labels as a title or a template branch.
        values['problem'] = values['problem'] if values['problem'] in PROBLEMS else 'water'
    elif request.method == 'POST':
        primary, others, report = _answer(values)
    return render_template('farm_help/index.html', values=values, error=error,
        primary=primary, others=others, report=report, crops=CROPS,
        moisture=MOISTURE, symptoms=LEAF_SYMPTOMS,
        unchecked=[key for key in ('moisture','waterlogging','pest_present')
                   if values[key]=='unknown']), status

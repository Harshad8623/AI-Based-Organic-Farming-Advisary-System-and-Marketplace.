"""
ml_models/disease_model.py
--------------------------
Plant disease knowledge base with organic solutions.
Used by the disease detection route to look up disease info.
"""

# ---------------------------------------------------------------------------
# Disease Database
# Each entry has:
#   name       — display name
#   crops      — commonly affected crops
#   symptoms   — visible symptoms description
#   cause      — pathogen / cause
#   organic_solutions — list of organic treatments
#   severity   — low | medium | high
# ---------------------------------------------------------------------------
DISEASE_DB = [
    {
        "name": "Early Blight",
        "crops": "Tomato, Potato",
        "symptoms": "Dark brown spots with concentric rings on lower leaves, yellowing around spots.",
        "cause": "Fungus (Alternaria solani)",
        "organic_solutions": [
            "Spray Neem oil solution (5 ml/L) every 7 days.",
            "Apply Bordeaux mixture (copper sulfate + lime).",
            "Remove and destroy affected leaves immediately.",
            "Maintain proper plant spacing for air circulation."
        ],
        "severity": "medium"
    },
    {
        "name": "Late Blight",
        "crops": "Tomato, Potato",
        "symptoms": "Water-soaked patches turning dark brown, white mold on leaf undersides.",
        "cause": "Oomycete (Phytophthora infestans)",
        "organic_solutions": [
            "Apply Copper-based fungicide (Tribasic copper sulfate).",
            "Spray Jeevamrutha (fermented cow dung + urine solution).",
            "Avoid overhead irrigation; use drip irrigation.",
            "Remove infected plants and do not compost them."
        ],
        "severity": "high"
    },
    {
        "name": "Powdery Mildew",
        "crops": "Wheat, Cucumber, Peas, Grapes",
        "symptoms": "White powdery coating on leaves and stems. Leaves curl and turn yellow.",
        "cause": "Fungus (Erysiphe / Podosphaera spp.)",
        "organic_solutions": [
            "Spray diluted milk (1:9 ratio with water) weekly.",
            "Apply baking soda solution (1 tsp/L water + few drops dish soap).",
            "Spray Neem oil every 5-7 days.",
            "Improve airflow by pruning dense foliage."
        ],
        "severity": "medium"
    },
    {
        "name": "Leaf Rust",
        "crops": "Wheat, Barley, Coffee",
        "symptoms": "Orange-red pustules on upper leaf surface; leaves turn yellow and die.",
        "cause": "Fungus (Puccinia spp.)",
        "organic_solutions": [
            "Apply Trichoderma viride bio-fungicide.",
            "Spray cow urine (diluted 1:10) as a preventive measure.",
            "Use resistant wheat varieties where available.",
            "Remove and burn infected stubble after harvest."
        ],
        "severity": "high"
    },
    {
        "name": "Bacterial Blight of Rice",
        "crops": "Rice",
        "symptoms": "Water-soaked leaf margins turning yellow, then white and dying.",
        "cause": "Bacteria (Xanthomonas oryzae pv. oryzae)",
        "organic_solutions": [
            "Seed treatment with hot water (52°C for 30 minutes).",
            "Spray Pseudomonas fluorescens bio-control agent.",
            "Avoid excessive nitrogen fertilizer.",
            "Drain fields properly to reduce humidity."
        ],
        "severity": "high"
    },
    {
        "name": "Yellow Mosaic Virus",
        "crops": "Soybean, Okra, Mung Bean",
        "symptoms": "Mosaic pattern of yellow and green patches on leaves; stunted growth.",
        "cause": "Begomovirus (transmitted by whiteflies)",
        "organic_solutions": [
            "Control whitefly vectors with yellow sticky traps.",
            "Spray Neem oil to repel whiteflies.",
            "Remove infected plants promptly to prevent spread.",
            "Use virus-resistant or tolerant varieties."
        ],
        "severity": "high"
    },
    {
        "name": "Fusarium Wilt",
        "crops": "Tomato, Banana, Chickpea, Cotton",
        "symptoms": "Yellowing of lower leaves, wilting of one side, brown discoloration inside stem.",
        "cause": "Fungus (Fusarium oxysporum)",
        "organic_solutions": [
            "Apply Trichoderma harzianum to soil before planting.",
            "Practice crop rotation (avoid same family for 3 years).",
            "Solarize soil in summer to reduce fungal load.",
            "Use Jeevamrutha soil drench to boost soil microbiome."
        ],
        "severity": "high"
    },
    {
        "name": "Anthracnose",
        "crops": "Mango, Papaya, Chilli, Beans",
        "symptoms": "Dark sunken lesions on fruits and leaves; pinkish spore masses.",
        "cause": "Fungus (Colletotrichum spp.)",
        "organic_solutions": [
            "Spray Bordeaux mixture (1%) at regular intervals.",
            "Apply Neem oil spray on fruits and leaves.",
            "Ensure proper field sanitation and remove fallen fruits.",
            "Post-harvest treatment with hot water (50°C, 10 min)."
        ],
        "severity": "medium"
    },
    {
        "name": "Downy Mildew",
        "crops": "Grapes, Cucumber, Spinach, Onion",
        "symptoms": "Pale yellow patches on upper leaves; gray-purple mold on undersides.",
        "cause": "Oomycete (Plasmopara / Peronospora spp.)",
        "organic_solutions": [
            "Apply Copper hydroxide spray preventively.",
            "Spray potassium bicarbonate solution.",
            "Avoid wetting foliage when irrigating.",
            "Improve plant spacing and prune for better air movement."
        ],
        "severity": "medium"
    },
    {
        "name": "Leaf Curl",
        "crops": "Chilli, Tomato, Papaya",
        "symptoms": "Leaves curl upward or downward, thicken and become brittle; stunted growth.",
        "cause": "Virus (Begomovirus) via thrips/whiteflies",
        "organic_solutions": [
            "Install blue/yellow sticky traps for thrips control.",
            "Spray Neem seed kernel extract (NSKE 5%).",
            "Intercrop with coriander or marigold to repel vectors.",
            "Remove and destroy heavily infected plants early."
        ],
        "severity": "medium"
    },
    {
        "name": "Rice Blast",
        "crops": "Rice",
        "symptoms": "Diamond-shaped lesions with gray centers on leaves; neck rot at panicle.",
        "cause": "Fungus (Magnaporthe oryzae)",
        "organic_solutions": [
            "Apply silicon-rich amendments (rice husk ash) to strengthen cell walls.",
            "Spray Pseudomonas fluorescens (10 g/L) at tillering stage.",
            "Avoid excess nitrogen fertilizer.",
            "Use blast-resistant rice varieties."
        ],
        "severity": "high"
    },
    {
        "name": "Brown Spot",
        "crops": "Rice",
        "symptoms": "Oval brown spots with yellow halo on leaves; grain discoloration.",
        "cause": "Fungus (Bipolaris oryzae)",
        "organic_solutions": [
            "Seed treatment with Trichoderma viride before sowing.",
            "Maintain adequate potassium levels in soil.",
            "Spray Jeevamrutha as foliar spray every 10 days.",
            "Ensure proper field drainage."
        ],
        "severity": "medium"
    },
    {
        "name": "Cercospora Leaf Spot",
        "crops": "Groundnut, Sugarcane, Tomato, Pepper",
        "symptoms": "Circular to irregular brown spots with darker border; premature leaf drop.",
        "cause": "Fungus (Cercospora spp.)",
        "organic_solutions": [
            "Spray Copper oxychloride (3 g/L) when spots first appear.",
            "Apply Neem cake in soil at sowing time.",
            "Practice crop rotation with non-host crops.",
            "Collect and destroy fallen leaves to reduce inoculant."
        ],
        "severity": "medium"
    },
    {
        "name": "Healthy Plant",
        "crops": "All",
        "symptoms": "No disease detected. Plant appears healthy.",
        "cause": "N/A",
        "organic_solutions": [
            "Continue regular crop monitoring every week.",
            "Apply Jeevamrutha (250 ml/L) as soil drench monthly.",
            "Mulch soil to conserve moisture and prevent soil splash.",
            "Maintain balanced organic fertilization."
        ],
        "severity": "none"
    },
]


def get_disease_by_name(name):
    """Find a disease entry by name (case-insensitive)."""
    name_lower = name.lower()
    for d in DISEASE_DB:
        if d['name'].lower() == name_lower:
            return d
    return None  # An unknown label must never become a healthy diagnosis.


def _gemini_vision_predict(image_path, api_key):
    """
    Use Gemini Vision to analyse the uploaded image.
    Returns a result dict matching DISEASE_DB structure.
    """
    import base64, requests

    # Encode image as base64
    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')

    # Detect MIME type from extension
    ext = image_path.rsplit('.', 1)[-1].lower()
    mime_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif'}
    mime = mime_map.get(ext, 'image/jpeg')

    prompt = """You help triage crop photographs. A photograph cannot confirm a diagnosis. Carefully look at this image. Do not claim certainty or prescribe chemical or homemade treatment doses.

STEP 1 — Is this a plant/leaf/crop image?
If NO (e.g. it's a person, animal, object, or non-plant photo), respond EXACTLY:
NOT_A_PLANT

If YES, analyse the disease and respond EXACTLY in this format (no extra text):
DISEASE_NAME: <exact disease name from list or 'Healthy Plant'>
CROPS: <affected crops>
CAUSE: <pathogen/cause>
SYMPTOMS: <visible symptoms in 1-2 sentences>
SEVERITY: <low|medium|high|none>
SOLUTION_1: <organic treatment 1>
SOLUTION_2: <organic treatment 2>
SOLUTION_3: <organic treatment 3>
SOLUTION_4: <organic treatment 4>

Known diseases: Early Blight, Late Blight, Powdery Mildew, Leaf Rust, Bacterial Blight of Rice, Yellow Mosaic Virus, Fusarium Wilt, Anthracnose, Downy Mildew, Leaf Curl, Rice Blast, Brown Spot, Cercospora Leaf Spot, Healthy Plant.
If uncertain or not matching a known disease, use 'Unable to identify'. Never force a closest match. Solutions must be observation, hygiene, or consulting a local agricultural expert; do not prescribe substances or doses."""

    # Try models in order
    models = ["gemini-2.5-flash"]
    last_error = None

    for model in models:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime, "data": img_b64}}
                ]
            }]
        }
        try:
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                text = resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()

                # Not a plant image
                if text == 'NOT_A_PLANT':
                    return {
                        "name": "❌ Not a Plant Image",
                        "crops": "N/A",
                        "symptoms": "The uploaded image does not appear to be a plant or leaf photo. Please upload a clear photo of a plant leaf or affected crop area.",
                        "cause": "Invalid image — not a plant",
                        "organic_solutions": [
                            "Upload a clear photo of the affected leaf or plant.",
                            "Take the photo in good daylight.",
                            "Focus on the leaf showing symptoms.",
                            "Avoid uploading personal photos or unrelated images."
                        ],
                        "severity": "none"
                    }

                # Parse structured response
                def parse_field(label, default=''):
                    for line in text.splitlines():
                        if line.startswith(f"{label}:"):
                            return line.split(':', 1)[1].strip()
                    return default

                solutions = [
                    parse_field('SOLUTION_1'),
                    parse_field('SOLUTION_2'),
                    parse_field('SOLUTION_3'),
                    parse_field('SOLUTION_4'),
                ]
                solutions = [s for s in solutions if s]  # remove empty

                disease_name = parse_field('DISEASE_NAME')
                symptoms = parse_field('SYMPTOMS')
                if not disease_name or not symptoms:
                    raise ValueError('Incomplete image analysis response')
                severity     = parse_field('SEVERITY', 'unknown').lower()
                if severity not in ('low', 'medium', 'high', 'none'):
                    severity = 'unknown'

                # Try to enrich with DB entry if name matches
                db_entry = get_disease_by_name(disease_name)
                if db_entry and db_entry['name'] != 'Healthy Plant':
                    # Use Gemini's analysis but supplement with DB solutions if needed
                    if not solutions:
                        solutions = db_entry['organic_solutions']

                return {
                    "name":              disease_name,
                    "crops":             parse_field('CROPS', db_entry.get('crops', 'Various crops') if db_entry else 'Various crops'),
                    "symptoms":          parse_field('SYMPTOMS', db_entry.get('symptoms', '') if db_entry else ''),
                    "cause":             parse_field('CAUSE', db_entry.get('cause', 'Unknown') if db_entry else 'Unknown'),
                    "organic_solutions": solutions or ["Consult a local agricultural expert."],
                    "severity":          severity,
                    "ai_powered":        True,
                }
            elif resp.status_code in (429, 503):
                last_error = f"{resp.status_code} on {model}"
                continue
            else:
                resp.raise_for_status()
        except requests.exceptions.Timeout:
            last_error = f"Timeout on {model}"
            continue

    raise RuntimeError(f"All Gemini models failed: {last_error}")


TRIAGE_STEPS = [
    "Photograph both sides of affected leaves and the whole plant in daylight.",
    "Record the crop, variety, affected area, symptoms, and when they started.",
    "Avoid moving affected planting material; clean tools between plants.",
    "Ask your local KVK or agricultural extension officer to confirm the cause before treatment. Follow the registered product label and organic certification rules.",
]


def predict_disease(image_path, api_key=None):
    """Return tentative model observations, or an explicit unavailable result.

    No arbitrary label is generated when both analysis engines are unavailable.
    Model scores are uncalibrated class scores, not diagnostic probabilities.
    """
    import logging
    result = None
    try:
        from ml_models.plant_disease_cnn import cnn_available, cnn_predict
        if cnn_available():
            result = cnn_predict(image_path)
    except Exception as exc:
        logging.getLogger(__name__).warning("Local image analysis unavailable (%s)", type(exc).__name__)

    if result is None and api_key:
        try:
            result = _gemini_vision_predict(image_path, api_key)
            result['engine'] = 'Gemini Vision'
        except Exception as exc:
            # Never log exception text: requests exceptions may contain the API key.
            logging.getLogger(__name__).warning("Remote image analysis unavailable (%s)", type(exc).__name__)

    if result is None:
        return {
            'name': 'Analysis unavailable', 'available': False,
            'symptoms': 'No image analysis service is available. No disease has been identified.',
            'organic_solutions': list(TRIAGE_STEPS), 'severity': 'unknown',
            'confidence': None, 'ai_powered': False, 'engine': None,
        }
    result['available'] = True
    result['tentative'] = True
    # Prevent a generated or mismatched knowledge-base prescription from becoming
    # treatment advice before a qualified person confirms the diagnosis.
    result['organic_solutions'] = list(TRIAGE_STEPS)
    result.setdefault('confidence', None)
    return result

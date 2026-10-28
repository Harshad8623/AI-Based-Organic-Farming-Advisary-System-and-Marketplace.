"""Educational crop explorer built from synthetic examples, not field validation."""

import math
from functools import lru_cache
import numpy as np
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for
from flask_login import login_required, current_user

crop_bp = Blueprint('crop', __name__, url_prefix='/crop')

# Labels map for display
CROP_TIPS = {
    'rice':        'Best grown in flooded fields. Requires abundant water.',
    'maize':       'Needs well-drained soil and full sun.',
    'chickpea':    'Drought-tolerant. Fix nitrogen naturally.',
    'kidneybeans': 'Rich in protein. Prefers slightly acidic soil.',
    'pigeonpeas':  'Drought-resistant legume, good for intercropping.',
    'mothbeans':   'Thrives in hot, dry climates.',
    'mungbean':    'Fast-growing, nitrogen-fixing crop.',
    'blackgram':   'Good for soil health. Grows in sandy-loam soil.',
    'lentil':      'Cool-season crop, excellent protein source.',
    'pomegranate': 'Fruiting tree suited to semi-arid regions.',
    'banana':      'Needs warm climate and fertile, well-watered soil.',
    'mango':       'Tropical fruit tree. Dislikes waterlogging.',
    'grapes':      'Grows in temperate climates with well-drained soil.',
    'watermelon':  'Loves heat. Requires sandy loam and full sun.',
    'muskmelon':   'Warm-season crop needing low humidity at harvest.',
    'apple':       'Grows well in cool temperate climates.',
    'orange':      'Subtropical fruit requiring frost-free winters.',
    'papaya':      'Fast-growing tropical fruit. Sensitive to frost.',
    'coconut':     'Thrives near coastlines in sandy tropical soil.',
    'cotton':      'Needs long frost-free period and sunny weather.',
    'jute':        'Grows in hot, humid climate with heavy rainfall.',
    'coffee':      'Shade-grown in tropical highlands.',
}


@lru_cache(maxsize=1)
def _get_model():
    """Build the deterministic demonstration model once per worker.

    Synthetic examples cannot establish farm accuracy. Keep this small model in
    memory instead of loading executable pickle files or racing to write a pair
    of cache artifacts on the first requests.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    import pandas as pd

    # Illustrative numeric cluster centers, not a validated agronomic dataset.
    CROPS = {
        'rice':        (80, 45, 40, 23, 82, 6.5, 200),
        'maize':       (77, 48, 20, 22, 65, 6.3, 85),
        'chickpea':    (40, 67, 80, 18, 16, 7.3, 80),
        'kidneybeans': (20, 67, 20, 19, 22, 5.7, 105),
        'pigeonpeas':  (20, 67, 20, 27, 48, 5.8, 149),
        'mothbeans':   (21, 48, 20, 28, 53, 6.9, 51),
        'mungbean':    (21, 47, 20, 28, 86, 6.7, 48),
        'blackgram':   (40, 50, 19, 29, 65, 7.2, 68),
        'lentil':      (18, 68, 19, 24, 64, 6.9, 46),
        'pomegranate': (18, 18, 40, 21, 90, 6.0, 107),
        'banana':      (100,75, 50, 27, 80, 5.7, 105),
        'mango':       (20, 27, 30, 31, 50, 5.7, 95),
        'grapes':      (23,132,200, 23, 82, 5.6, 69),
        'watermelon':  (99, 17, 50, 25, 85, 6.5, 51),
        'muskmelon':   (100,17, 50, 28, 92, 6.6, 25),
        'apple':       (21,134,199, 21, 92, 5.9, 112),
        'orange':      (20, 10, 10, 22, 92, 7.0, 110),
        'papaya':      (49, 59, 50, 33, 92, 6.8, 145),
        'coconut':     (21, 16, 30, 27, 94, 5.9, 175),
        'cotton':      (117,46, 19, 24, 79, 6.9, 81),
        'jute':        (78, 46, 40, 24, 79, 6.8, 174),
        'coffee':      (101,28, 29, 25, 58, 6.5, 159),
    }

    rng = np.random.default_rng(42)
    rows = []
    for crop, (N, P, K, T, H, pH, R) in CROPS.items():
        # 200 synthetic examples per crop with deterministic noise
        n = 200
        rows.append(pd.DataFrame({
            'N':         rng.normal(N,   N*0.1,  n).clip(0),
            'P':         rng.normal(P,   P*0.1,  n).clip(0),
            'K':         rng.normal(K,   K*0.1,  n).clip(0),
            'temperature': rng.normal(T, 2,      n),
            'humidity':  rng.normal(H,   5,      n).clip(0, 100),
            'ph':        rng.normal(pH,  0.3,    n).clip(3, 10),
            'rainfall':  rng.normal(R,   R*0.15, n).clip(0),
            'label':     crop
        }))

    df = pd.concat(rows, ignore_index=True)

    le = LabelEncoder()
    y  = le.fit_transform(df['label'])
    X  = df[['N','P','K','temperature','humidity','ph','rainfall']].values

    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=1)
    model.fit(X, y)
    return model, le


# Model exploration bounds, not recommended field or fertilizer values.
INPUT_FIELDS = [
    ('N', 'crop_demo_n', 0, 300, '80'),
    ('P', 'crop_demo_p', 0, 300, '45'),
    ('K', 'crop_demo_k', 0, 300, '40'),
    ('temperature', 'crop_temperature_label', -10, 55, '25'),
    ('humidity', 'crop_humidity_label', 0, 100, '65'),
    ('ph', 'crop_ph_label', 0, 14, '6.5'),
    ('rainfall', 'crop_rainfall_label', 0, 500, '150'),
]


def _validated_features(form):
    values = []
    for name, label, lower, upper, example in INPUT_FIELDS:
        raw = form.get(name, '')
        if not isinstance(raw, str) or not raw.strip() or len(raw) > 30:
            raise ValueError('Missing or invalid model input')
        value = float(raw)
        if not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError('Model input outside supported range')
        values.append(value)
    return np.array([values])


@crop_bp.route('/', methods=['GET', 'POST'])
@login_required
def recommend():
    if not current_user.is_farmer():
        flash('Crop exploration is a farmer tool.', 'info')
        return redirect(url_for('marketplace.listing'))
    prediction, tip, error, status = None, None, None, 200
    if request.method == 'POST':
        try:
            features = _validated_features(request.form)
        except (ValueError, TypeError, OverflowError):
            error, status = 'crop_invalid_values', 400
        else:
            try:
                model, encoder = _get_model()
                predicted = encoder.inverse_transform(model.predict(features))[0]
                prediction = str(predicted).title()
                tip = CROP_TIPS.get(str(predicted), '')
            except Exception as exc:
                current_app.logger.warning('Crop exploration unavailable (%s)', type(exc).__name__)
                error, status = 'crop_temporarily_unavailable', 503
    return render_template('crop/recommendation.html', prediction=prediction,
                           tip=tip, crop_error=error, input_fields=INPUT_FIELDS), status

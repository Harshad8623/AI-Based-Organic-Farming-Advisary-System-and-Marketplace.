"""
ml_models/plant_disease_cnn.py
-------------------------------
Inference module for the PlantVillage-trained CNN disease detector.

Priority chain:
  1. ONNX model  (plant_disease_model.onnx)  — fast, GPU/CPU, works offline
  2. Not available                            — caller uses Gemini or reports unavailable

Usage:
    from ml_models.plant_disease_cnn import CNNDiseasePredictor
    predictor = CNNDiseasePredictor()          # loads model once
    result    = predictor.predict("image.jpg") # returns dict

The result dict has:
    {
        'disease_name':   str,   # e.g. "Early Blight"
        'raw_class':      str,   # e.g. "Tomato___Early_blight"
        'confidence':     float, # 0.0 – 1.0
        'top3':           list,  # [(class, confidence), ...]
        'crops':          str,
        'symptoms':       str,
        'cause':          str,
        'organic_solutions': list[str],
        'severity':       str,
        'ai_powered':     True,
        'engine':         'CNN (PlantVillage)'
    }
"""

import os
import json
import numpy as np
from PIL import Image

# ─── PlantVillage class → our DISEASE_DB name mapping ───────────────────────
# IMPORTANT: These keys MUST exactly match the folder names in the dataset.
# This dataset (Kaggle/emmarex) has inconsistent underscores — carefully matched below.
PLANTVILLAGE_TO_DB = {
    'Pepper__bell___healthy': 'Healthy Plant',
    'Potato___Early_blight': 'Early Blight',
    'Potato___Late_blight': 'Late Blight',
    'Potato___healthy': 'Healthy Plant',
    'Tomato_Early_blight': 'Early Blight',
    'Tomato_Late_blight': 'Late Blight',
    'Tomato_healthy': 'Healthy Plant',
}

# Friendly display names for the Disease Detection result card
FRIENDLY_NAMES = {
    'Pepper__bell___Bacterial_spot':                     'Bell Pepper — Bacterial Spot',
    'Pepper__bell___healthy':                            'Bell Pepper — Healthy',
    'Potato___Early_blight':                             'Potato — Early Blight',
    'Potato___Late_blight':                              'Potato — Late Blight',
    'Potato___healthy':                                  'Potato — Healthy',
    'Tomato_Bacterial_spot':                             'Tomato — Bacterial Spot',
    'Tomato_Early_blight':                               'Tomato — Early Blight',
    'Tomato_Late_blight':                                'Tomato — Late Blight',
    'Tomato_Leaf_Mold':                                  'Tomato — Leaf Mold',
    'Tomato_Septoria_leaf_spot':                         'Tomato — Septoria Leaf Spot',
    'Tomato_Spider_mites_Two_spotted_spider_mite':       'Tomato — Spider Mite Damage',
    'Tomato__Target_Spot':                               'Tomato — Target Spot',
    'Tomato__Tomato_mosaic_virus':                       'Tomato — Mosaic Virus',
    'Tomato__Tomato_YellowLeaf__Curl_Virus':             'Tomato — Yellow Leaf Curl Virus',
    'Tomato_healthy':                                    'Tomato — Healthy',
}

# Extended disease info for classes not in DISEASE_DB
EXTENDED_DB = {
    'Apple Scab': {
        'crops': 'Apple',
        'symptoms': 'Olive-green or brown velvety spots on leaves and fruits; scab-like lesions.',
        'cause': 'Fungus (Venturia inaequalis)',
        'organic_solutions': [
            'Spray sulfur-based fungicide early in season.',
            'Apply Neem oil every 7-10 days during wet weather.',
            'Rake and destroy fallen leaves to break disease cycle.',
            'Prune for better air circulation.',
        ],
        'severity': 'medium'
    },
    'Apple Black Rot': {
        'crops': 'Apple',
        'symptoms': 'Brown to black rotting lesions on fruits; "frog-eye" leaf spots.',
        'cause': 'Fungus (Botryosphaeria obtusa)',
        'organic_solutions': [
            'Remove mummified fruits from tree and ground.',
            'Spray copper-based fungicide at bud break.',
            'Prune dead or diseased wood promptly.',
            'Apply Bordeaux mixture preventively.',
        ],
        'severity': 'high'
    },
}

IMG_SIZE  = 224   # Must match training IMG_SIZE
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

# ImageNet normalization (matches PyTorch training transforms)
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class CNNDiseasePredictor:
    """Loads and caches the ONNX model for fast offline inference."""

    def __init__(self):
        self._session   = None
        self._classes   = None
        self._available = False
        self._engine    = None
        self._load()

    def _load(self):
        """Try to load ONNX model (plant_disease_model.onnx)."""
        classes_path = os.path.join(MODEL_DIR, 'plant_disease_classes.json')
        onnx_path    = os.path.join(MODEL_DIR, 'plant_disease_model.onnx')

        if not os.path.exists(classes_path) or not os.path.exists(onnx_path):
            return   # Model not trained yet

        with open(classes_path) as f:
            self._classes = json.load(f)

        try:
            import onnxruntime as ort
            # Prefer GPU (CUDA) execution, fall back to CPU
            providers = []
            if 'CUDAExecutionProvider' in ort.get_available_providers():
                providers.append('CUDAExecutionProvider')
            providers.append('CPUExecutionProvider')

            self._session   = ort.InferenceSession(onnx_path, providers=providers)
            provider_used   = self._session.get_providers()[0]
            gpu_tag         = '· GPU' if 'CUDA' in provider_used else '· CPU'
            self._engine    = f'CNN (PlantVillage {gpu_tag})'
            self._available = True
            print(f"[CNN] ONNX model loaded — {self._engine} ({len(self._classes)} classes)")
        except ImportError:
            print("[CNN] onnxruntime not installed. Run: pip install onnxruntime")
        except Exception as e:
            print(f"[CNN] Failed to load ONNX model: {e}")

    @property
    def available(self):
        return self._available

    def _preprocess(self, image_path):
        """Load image and return (1, 3, 224, 224) float32 NCHW tensor — ONNX format."""
        img = Image.open(image_path).convert('RGB')
        # Resize to slightly larger then center-crop (matches val transforms in training)
        size = int(IMG_SIZE * 1.1)
        img  = img.resize((size, size), Image.LANCZOS)
        left = (size - IMG_SIZE) // 2
        img  = img.crop((left, left, left + IMG_SIZE, left + IMG_SIZE))
        arr  = np.array(img, dtype=np.float32) / 255.0          # [0, 1]
        arr  = (arr - _MEAN) / _STD                              # ImageNet normalize
        arr  = arr.transpose(2, 0, 1)                            # HWC -> CHW
        return np.expand_dims(arr, axis=0).astype(np.float32)    # (1, 3, 224, 224)

    def _softmax(self, logits):
        """Numerically stable softmax."""
        e = np.exp(logits - logits.max())
        return e / e.sum()

    def predict(self, image_path):
        """
        Predict plant disease from an image file.
        Returns a result dict compatible with disease_model.py format.
        """
        if not self._available:
            raise RuntimeError("CNN model not available. Run train_plant_disease.py first.")

        input_data = self._preprocess(image_path)

        # Run ONNX inference
        input_name = self._session.get_inputs()[0].name
        logits     = self._session.run(None, {input_name: input_data})[0][0]
        if (not self._classes or len(logits) != len(self._classes) or
                not np.isfinite(logits).all()):
            raise ValueError('Invalid model output or class mapping')
        probs      = self._softmax(logits)

        # Get top-3 predictions
        top3_idx  = np.argsort(probs)[::-1][:3]
        top3      = [(self._classes[i], float(probs[i])) for i in top3_idx]

        best_class = top3[0][0]
        confidence = top3[0][1]

        # Map to display name and disease info
        friendly   = FRIENDLY_NAMES.get(best_class, best_class.replace('___', ' — ').replace('_', ' '))
        db_name    = PLANTVILLAGE_TO_DB.get(best_class)

        # Get disease info from our database
        from ml_models.disease_model import get_disease_by_name, DISEASE_DB
        db_entry = get_disease_by_name(db_name) if db_name else None

        # Check extended DB if not found in main DB
        if db_entry is None or db_entry['name'] == 'Healthy Plant':
            db_entry = EXTENDED_DB.get(friendly, db_entry)
        db_entry = db_entry or {}

        return {
            'name':              friendly,
            'raw_class':         best_class,
            'confidence':        confidence,
            'top3':              top3,
            'crops':             db_entry.get('crops', 'Various crops'),
            'symptoms':          db_entry.get('symptoms', ''),
            'cause':             db_entry.get('cause', 'Unknown'),
            'organic_solutions': db_entry.get('organic_solutions', ['Consult an agricultural expert.']),
            'severity':          db_entry.get('severity', 'medium'),
            'ai_powered':        True,
            'engine':            self._engine,
        }


# ─── Singleton instance (loaded once at module import) ───────────────────────
# This avoids reloading the model on every request
_predictor = None

def get_predictor():
    """Return the singleton CNNDiseasePredictor (lazy-loaded)."""
    global _predictor
    if _predictor is None:
        _predictor = CNNDiseasePredictor()
    return _predictor


def cnn_predict(image_path):
    """
    Convenience function. Returns result dict or raises RuntimeError if
    model is not available.
    """
    return get_predictor().predict(image_path)


def cnn_available():
    """Returns True if the CNN model files are present and loadable."""
    return get_predictor().available

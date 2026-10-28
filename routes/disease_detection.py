"""Validated leaf-image upload and tentative visual crop-health analysis."""

import base64
import io
import os
import tempfile
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError
from flask import Blueprint, render_template, request, flash, current_app, redirect, url_for
from flask_login import login_required, current_user

disease_bp = Blueprint('disease', __name__, url_prefix='/disease')
ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}
MAX_PIXELS = 20_000_000
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED


def _validated_image(file):
    """Decode actual image bytes and strip metadata before analysis or preview."""
    data = file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError('Image too large')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data)) as candidate:
            if candidate.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValueError('Unsupported image format')
            if candidate.width * candidate.height > MAX_PIXELS or min(candidate.size) < 32:
                raise ValueError('Invalid image dimensions')
            candidate.verify()
        with Image.open(io.BytesIO(data)) as candidate:
            clean = ImageOps.exif_transpose(candidate).convert('RGB')
            clean.thumbnail((1600, 1600))
            output = io.BytesIO()
            clean.save(output, format='JPEG', quality=85)
    return output.getvalue()


@disease_bp.route('/', methods=['GET', 'POST'])
@login_required
def detect():
    if not current_user.is_farmer():
        flash('Leaf checks are a farmer tool.', 'info')
        return redirect(url_for('marketplace.listing'))
    result, image_url, error = None, None, None
    if request.method == 'POST':
        file = request.files.get('leaf_image')
        if not file or not file.filename:
            error = 'leaf_upload_required'
        elif not _allowed(file.filename):
            error = 'leaf_invalid_image'
        else:
            try:
                image_bytes = _validated_image(file)
            except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError,
                    Image.DecompressionBombWarning):
                error = 'leaf_invalid_image'
            else:
                # Use a private temporary file; no sensitive image or EXIF is left
                # in the publicly accessible uploads directory after the request.
                save_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as upload:
                        upload.write(image_bytes)
                        save_path = upload.name
                    from ml_models.disease_model import predict_disease
                    result = predict_disease(save_path, api_key=current_app.config.get('GEMINI_API_KEY', ''))
                    image_url = 'data:image/jpeg;base64,' + base64.b64encode(image_bytes).decode('ascii')
                except Exception as exc:
                    current_app.logger.warning('Leaf check unavailable (%s)', type(exc).__name__)
                    error = 'leaf_service_error'
                finally:
                    if save_path and os.path.exists(save_path):
                        os.remove(save_path)
    return render_template('disease/detection.html', result=result, image_url=image_url,
                           leaf_error=error)

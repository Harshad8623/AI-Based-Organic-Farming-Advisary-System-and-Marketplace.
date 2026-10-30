"""
routes/roadmap.py
-----------------
Crop Roadmap: Browse detailed organic farming guides per crop.
"""

import json
from flask import Blueprint, render_template, abort, request
from models import CropRoadmap

roadmap_bp = Blueprint('roadmap', __name__, url_prefix='/roadmap')
KNOWN_CROPS = {'tomato', 'potato', 'onion', 'rice', 'wheat', 'chilli', 'brinjal', 'garlic', 'cauliflower', 'spinach'}
SEASONS = ('Kharif', 'Rabi', 'Zaid', 'Year-round')
CHECKLIST = [('guide_before',
  'Before planting',
  [('guide_soil_test',
    'Use a recent soil test and local advice to plan inputs; record the report units.'),
   ('guide_water_plan',
    'Check the water source and drainage before choosing the crop or planting date.'),
   ('guide_cost_plan',
    'Estimate seed, labour, water and transport costs and find possible buyers.')]),
 ('guide_establishment',
  'After planting',
  [('guide_planting_record',
    'Record variety, planting date, field area and the crop stage you actually see.'),
   ('guide_emergence',
    'Compare healthy and weak plants across the field; record uneven growth instead of guessing '
    'the cause.'),
   ('guide_drainage', 'Look for standing water, blocked drains and damaged irrigation lines.')]),
 ('guide_growth',
  'During growth',
  [('guide_scout',
    'Inspect several places in the field. Count inspected and affected plants and photograph '
    'symptoms.'),
   ('guide_root_moisture',
    'Check moisture near the root zone and recent rainfall before deciding about irrigation.'),
   ('guide_record_inputs',
    'Write down what you applied, the date and cost; compare the next observation before repeating '
    'it.')]),
 ('guide_harvest',
  'Before and after harvest',
  [('guide_buyer_plan',
    'Confirm buyer requirements, quantity, packing and transport; compare net returns.'),
   ('guide_clean_harvest',
    'Use clean tools and containers; keep damaged produce separate and follow local food-safety '
    'guidance.'),
   ('guide_review_outcomes',
    'Record actual harvest, received price and costs, then review what worked before the next '
    'season.')])]


@roadmap_bp.route('/')
def index():
    """Browse all crop roadmaps."""
    selected = request.args.get('season', '')
    if selected and selected not in SEASONS:
        abort(400)
    query = CropRoadmap.query
    if selected:
        query = query.filter_by(season=selected)
    crops = query.order_by(CropRoadmap.crop_name).all()
    return render_template('roadmap/index.html', crops=crops, selected_season=selected,
                           seasons=SEASONS, known_crops=KNOWN_CROPS)


@roadmap_bp.route('/<slug>')
def detail(slug):
    """Detailed roadmap for a specific crop."""
    crop = CropRoadmap.query.filter_by(slug=slug).first_or_404()
    stages = []
    if crop.stages_json:
        try:
            loaded = json.loads(crop.stages_json)
            if isinstance(loaded, list):
                stages = [
                    {'stage': item['stage'].strip(), 'days': item.get('days', '') if isinstance(item.get('days'), str) else '',
                     'actions': [text for text in item.get('actions', []) if isinstance(text, str)] if isinstance(item.get('actions'), list) else [],
                     'tips': [text for text in item.get('tips', []) if isinstance(text, str)] if isinstance(item.get('tips'), list) else []}
                    for item in loaded if isinstance(item, dict) and isinstance(item.get('stage'), str) and item['stage'].strip()
                ]
        except (ValueError, TypeError):
            stages = []
    return render_template('roadmap/detail.html', crop=crop, stages=stages,
                           checklist=CHECKLIST, known_crop=crop.slug in KNOWN_CROPS)

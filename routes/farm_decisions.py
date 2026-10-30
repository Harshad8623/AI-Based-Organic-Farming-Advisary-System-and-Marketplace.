"""Private, transparent farm arithmetic: sales decisions and irrigation volumes.

These calculators use the farmer's inputs, not generated market prices, crop
prescriptions or predicted profits. No calculator submission changes the ledger.
"""
import calendar
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
import unicodedata
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, render_template, request
from flask_login import current_user, login_required

from farm_tools_models import FarmLedgerEntry

farm_decisions_bp = Blueprint('farm_decisions', __name__, url_prefix='/farm-decisions')

AREA_M2 = {'m2': Decimal('1'), 'acre': Decimal('4046.8564224'),
           'hectare': Decimal('10000'), 'guntha': Decimal('101.17141056')}
WEIGHT_KG = {'kg': Decimal('1'), 'quintal': Decimal('100')}
_NUMBER = re.compile(r'^(?:\d+(?:\.\d+)?|\.\d+)$')
_MAX_MONEY = Decimal('999999999.99')
_MAX_KG = Decimal('10000000')
FIELD_LABELS = {
    'decision_harvest':'Harvest quantity', 'decision_growing_cost':'Total growing cost (₹)',
    'decision_farmgate_price':'Farm pickup price (₹)', 'decision_market_price':'Market price (₹)',
    'decision_transport':'Whole-trip transport (₹)', 'decision_fees':'Market fees and other charges (₹)',
    'decision_loss_percent':'Unsold or damaged produce (%)', 'decision_area':'Field area',
    'decision_depth':'Chosen water depth (mm)', 'decision_efficiency':'Water delivery efficiency (%)',
    'decision_pump':'Pump flow (litres/minute, optional)',
}



class DecisionInputError(ValueError):
    def __init__(self, key):
        self.key = key
        super().__init__(key)


def _number(values, name, *, minimum=Decimal('0'), maximum=_MAX_MONEY,
            places=2, positive=False, optional=False, error='decision_error_number'):
    raw = values.get(name, '')
    if not isinstance(raw, str):
        raise DecisionInputError(error)
    raw = ''.join(str(unicodedata.decimal(char)) if char.isdecimal() else char for char in raw.strip())
    if not raw and optional:
        return None
    if not raw or len(raw) > 40 or not _NUMBER.fullmatch(raw):
        raise DecisionInputError(error)
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise DecisionInputError(error) from None
    if (not value.is_finite() or value < minimum or value > maximum or
            (positive and value <= 0) or -value.as_tuple().exponent > places):
        raise DecisionInputError(error)
    return value


def _unit(values, name, choices):
    unit = values.get(name, '')
    if not isinstance(unit, str) or unit not in choices:
        raise DecisionInputError('decision_error_unit')
    return unit


def _month_bounds(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}', value):
        raise DecisionInputError('decision_error_month')
    try:
        year, month = map(int, value.split('-'))
        if not 1900 <= year <= 2100:
            raise ValueError
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    except ValueError:
        raise DecisionInputError('decision_error_month') from None


def _ledger_cost(month):
    first, last = _month_bounds(month)
    entries = FarmLedgerEntry.query.filter(
        FarmLedgerEntry.farmer_id == current_user.id,
        FarmLedgerEntry.kind == 'expense',
        FarmLedgerEntry.entry_date >= first, FarmLedgerEntry.entry_date <= last,
    ).with_entities(FarmLedgerEntry.amount).all()
    if not entries:
        raise DecisionInputError('decision_error_empty_ledger')
    # Sum fixed-scale Decimal values rather than SQLite's binary-float SUM.
    total = sum((row.amount for row in entries), Decimal('0.00'))
    if total > _MAX_MONEY:
        raise DecisionInputError('decision_error_cost')
    return total, len(entries)


def _sales_row(quantity_kg, farmgate_price_kg, market_price_kg, cultivation_cost,
               transport_cost, market_fees, spoilage):
    saleable = quantity_kg * (Decimal('1') - spoilage / Decimal('100'))
    farmgate_gross = quantity_kg * farmgate_price_kg
    market_gross = saleable * market_price_kg
    farmgate_net = farmgate_gross - cultivation_cost
    market_net = market_gross - cultivation_cost - transport_cost - market_fees
    return {'quantity_kg': quantity_kg, 'saleable_kg': saleable,
            'farmgate_gross': farmgate_gross, 'market_gross': market_gross,
            'farmgate_net': farmgate_net, 'market_net': market_net,
            'difference': market_net - farmgate_net}


def sales_calculation(values):
    harvest_unit = _unit(values, 'harvest_unit', WEIGHT_KG)
    quantity = _number(values, 'harvest_quantity', positive=True, maximum=_MAX_KG,
                       places=4, error='decision_error_quantity') * WEIGHT_KG[harvest_unit]
    if quantity > _MAX_KG:
        raise DecisionInputError('decision_error_quantity')
    source = values.get('cost_source', 'manual')
    if source not in ('manual', 'ledger'):
        raise DecisionInputError('decision_error_cost_source')
    ledger_count = 0
    ledger_month = None
    if source == 'ledger':
        ledger_month = values.get('ledger_month', '')
        cost, ledger_count = _ledger_cost(ledger_month)
    else:
        cost = _number(values, 'cultivation_cost', error='decision_error_cost')
    farmgate_unit = _unit(values, 'farmgate_price_unit', WEIGHT_KG)
    market_unit = _unit(values, 'market_price_unit', WEIGHT_KG)
    farmgate_price = _number(values, 'farmgate_price', positive=True,
                            error='decision_error_price') / WEIGHT_KG[farmgate_unit]
    market_price = _number(values, 'market_price', positive=True,
                          error='decision_error_price') / WEIGHT_KG[market_unit]
    transport = _number(values, 'transport_cost', error='decision_error_cost')
    fees = _number(values, 'market_fees', error='decision_error_cost')
    spoilage = _number(values, 'spoilage_percent', maximum=Decimal('99.99'),
                       error='decision_error_spoilage')
    result = _sales_row(quantity, farmgate_price, market_price, cost, transport, fees, spoilage)
    result.update({'cost': cost, 'cost_source': source, 'ledger_count': ledger_count,
                   'ledger_month': ledger_month, 'farmgate_price_kg': farmgate_price,
                   'market_price_kg': market_price, 'transport': transport, 'fees': fees,
                   'spoilage_percent': spoilage,
                   'farmgate_break_even_kg': cost / quantity,
                   'market_break_even_kg': (cost + transport + fees) / result['saleable_kg'],
                   'farmgate_effective_kg': result['farmgate_net'] / quantity,
                   'market_effective_kg': result['market_net'] / quantity,
                   'better_key': 'decision_better_market' if result['difference'] > 0 else
                                 'decision_better_farmgate' if result['difference'] < 0 else 'decision_equal'})
    result['farmgate_break_even_quintal'] = result['farmgate_break_even_kg'] * Decimal('100')
    result['market_break_even_quintal'] = result['market_break_even_kg'] * Decimal('100')
    factor = Decimal('.8')
    result['scenarios'] = [
        dict(_sales_row(quantity * factor, farmgate_price, market_price, cost, transport, fees, spoilage),
             label_key='decision_scenario_less_harvest', label='20% less harvest'),
        dict(_sales_row(quantity, farmgate_price * factor, market_price * factor, cost, transport, fees, spoilage),
             label_key='decision_scenario_less_price', label='Both prices 20% lower'),
        dict(_sales_row(quantity * factor, farmgate_price * factor, market_price * factor, cost, transport, fees, spoilage),
             label_key='decision_scenario_both', label='Both harvest and prices 20% lower'),
    ]
    return result


def water_calculation(values):
    unit = _unit(values, 'area_unit', AREA_M2)
    area = _number(values, 'area_value', positive=True, maximum=Decimal('100000000'),
                   places=4, error='decision_error_area') * AREA_M2[unit]
    if area > Decimal('100000000'):
        raise DecisionInputError('decision_error_area')
    depth = _number(values, 'depth_mm', positive=True, maximum=Decimal('500'),
                    error='decision_error_depth')
    efficiency = _number(values, 'efficiency_percent', positive=True, maximum=Decimal('100'),
                         error='decision_error_efficiency')
    pump = _number(values, 'pump_lpm', positive=True, maximum=Decimal('1000000'),
                   optional=True, error='decision_error_pump')
    net = area * depth  # A 1 mm layer over 1 m² is exactly 1 litre.
    gross = net * Decimal('100') / efficiency
    return {'area_m2': area, 'area_hectare': area / AREA_M2['hectare'],
            'area_acre': area / AREA_M2['acre'], 'depth_mm': depth,
            'efficiency_percent': efficiency, 'net_litres': net,
            'gross_litres': gross, 'pump_lpm': pump,
            'pump_minutes': gross / pump if pump else None,
            'pump_hours': gross / pump / Decimal('60') if pump else None}


def _display(value):
    return f'{value.quantize(Decimal(".01"), rounding=ROUND_HALF_UP):,.2f}'


@farm_decisions_bp.route('', methods=['GET', 'POST'])
@farm_decisions_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if not current_user.is_farmer():
        abort(403)
    month = datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m')
    values = {'harvest_unit':'kg', 'cost_source':'manual', 'ledger_month':month,
              'farmgate_price_unit':'kg', 'market_price_unit':'kg', 'transport_cost':'0',
              'market_fees':'0', 'spoilage_percent':'0', 'area_unit':'acre'}
    selected = 'water' if request.args.get('tool') == 'water' else 'sales'
    sales, water, error, active, status = None, None, None, selected, 200
    if request.method == 'POST':
        values.update(request.form.to_dict())
        active = request.form.get('calculator', '')
        try:
            if active == 'sales':
                sales = sales_calculation(values)
            elif active == 'water':
                water = water_calculation(values)
            else:
                raise DecisionInputError('decision_error_calculator')
        except DecisionInputError as exc:
            error, status = exc.key, 400
    return render_template('decisions/index.html', values=values, sales=sales,
                           water=water, error=error, active=active, display=_display, labels=FIELD_LABELS), status

"""Farm decisions use actual inputs, exact units and only the owner's expenses."""
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest
from flask import template_rendered

from farm_tools_models import FarmLedgerEntry
from models import db, User
from routes.farm_decisions import (
    AREA_M2, DecisionInputError, farm_decisions_bp, sales_calculation, water_calculation,
)


def sales_values(**changes):
    return {'calculator':'sales', 'harvest_quantity':'1000', 'harvest_unit':'kg',
            'cost_source':'manual', 'cultivation_cost':'12000', 'ledger_month':'2026-10',
            'farmgate_price':'18', 'farmgate_price_unit':'kg', 'market_price':'22',
            'market_price_unit':'kg', 'transport_cost':'2000', 'market_fees':'1000',
            'spoilage_percent':'10'} | changes


def water_values(**changes):
    return {'calculator':'water', 'area_value':'1', 'area_unit':'acre', 'depth_mm':'10',
            'efficiency_percent':'80', 'pump_lpm':'100'} | changes


@pytest.fixture
def decision_users(app):
    # This blueprint can be exercised independently while other V2 features are
    # being integrated. In the finished app, registration is done by the factory.
    if 'farm_decisions' not in app.blueprints:
        app.register_blueprint(farm_decisions_bp)
    with app.app_context():
        users = [User(name='Farmer', email='farm@decisions.example', password='unused', role='farmer'),
                 User(name='Other farmer', email='other@decisions.example', password='unused', role='farmer'),
                 User(name='Buyer', email='buyer@decisions.example', password='unused', role='buyer')]
        db.session.add_all(users); db.session.commit()
        return [user.id for user in users]


def login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def calculate(app, client, values):
    contexts = []
    def capture(sender, template, context, **extra):
        contexts.append(context)
    with template_rendered.connected_to(capture, app):
        response = client.post('/farm-decisions', data=values)
    return response, contexts[-1]


def test_farmer_only_access(app, client, decision_users):
    assert client.get('/farm-decisions').status_code == 302
    assert client.post('/farm-decisions', data=sales_values()).status_code == 302
    login(client, decision_users[2])
    assert client.get('/farm-decisions').status_code == 403
    assert client.post('/farm-decisions', data=sales_values()).status_code == 403


def test_get_has_usable_forms_and_no_generated_prices(app, client, decision_users):
    login(client, decision_users[0])
    response = client.get('/farm-decisions')
    assert response.status_code == 200
    assert b'Farm pickup price' in response.data
    assert b'name="farmgate_price"' in response.data
    assert b'price or harvest forecasts' in response.data
    assert b'no-store' in response.headers['Cache-Control'].encode()


def test_higher_market_price_can_leave_less_after_costs():
    result = sales_calculation(sales_values())
    assert result['quantity_kg'] == Decimal('1000')
    assert result['saleable_kg'] == Decimal('900')
    assert result['farmgate_gross'] == Decimal('18000')
    assert result['market_gross'] == Decimal('19800')
    assert result['farmgate_net'] == Decimal('6000')
    assert result['market_net'] == Decimal('4800')
    assert result['difference'] == Decimal('-1200')
    assert result['better_key'] == 'decision_better_farmgate'
    assert result['farmgate_break_even_kg'] == Decimal('12')
    assert result['market_break_even_kg'] == Decimal('15000') / Decimal('900')
    assert result['farmgate_effective_kg'] == Decimal('6')
    assert result['market_effective_kg'] == Decimal('4.8')


def test_kg_and_quintal_price_and_weight_units_are_independent():
    base = sales_calculation(sales_values())
    converted = sales_calculation(sales_values(harvest_quantity='10', harvest_unit='quintal',
        farmgate_price='1800', farmgate_price_unit='quintal', market_price='2200', market_price_unit='quintal'))
    mixed = sales_calculation(sales_values(market_price='2200', market_price_unit='quintal'))
    assert converted == base == mixed


def test_equal_options_zero_cost_and_negative_net_are_reported():
    equal = sales_calculation(sales_values(harvest_quantity='100', cultivation_cost='0',
        farmgate_price='20', market_price='20', transport_cost='0', market_fees='0', spoilage_percent='0'))
    assert equal['better_key'] == 'decision_equal'
    assert equal['farmgate_break_even_kg'] == 0
    assert equal['farmgate_net'] == equal['market_net'] == Decimal('2000')
    loss = sales_calculation(sales_values(cultivation_cost='100000'))
    assert loss['farmgate_net'] < 0 and loss['market_net'] < 0


def test_sensitivity_changes_quantity_and_quotes_but_never_fixed_costs():
    result = sales_calculation(sales_values())
    assert result['scenarios'][0]['farmgate_net'] == Decimal('2400')
    assert result['scenarios'][0]['market_net'] == Decimal('840')
    assert result['scenarios'][1]['farmgate_net'] == Decimal('2400')
    assert result['scenarios'][1]['market_net'] == Decimal('840')
    assert result['scenarios'][2]['farmgate_net'] == Decimal('-480')
    assert result['scenarios'][2]['market_net'] == Decimal('-2328')


def test_saleable_fraction_never_divides_by_zero():
    result = sales_calculation(sales_values(spoilage_percent='99.99'))
    assert result['saleable_kg'] == Decimal('.1')
    assert result['market_break_even_kg'] == Decimal('150000')
    with pytest.raises(DecisionInputError):
        sales_calculation(sales_values(spoilage_percent='100'))


def test_devanagari_numbers_are_valid_finite_inputs():
    result = sales_calculation(sales_values(harvest_quantity='१०००', cultivation_cost='१२०००',
        farmgate_price='१८', market_price='२२', transport_cost='२०००', market_fees='१०००', spoilage_percent='१०'))
    assert result['farmgate_net'] == Decimal('6000')


@pytest.mark.parametrize('changes', [
    {'harvest_quantity':'0'}, {'harvest_quantity':'-1'}, {'harvest_quantity':'NaN'},
    {'harvest_quantity':'1e99999'}, {'harvest_quantity':'100001','harvest_unit':'quintal'},
    {'harvest_unit':'tonne'}, {'farmgate_price_unit':'tonne'}, {'market_price_unit':'wrong'},
    {'farmgate_price':'0'}, {'market_price':'Infinity'}, {'market_price':'1e5'},
    {'cultivation_cost':'-0.01'}, {'cultivation_cost':'0.001'}, {'cultivation_cost':'9999999999'},
    {'cultivation_cost':'9'*41}, {'transport_cost':'-1'}, {'market_fees':'NaN'},
    {'spoilage_percent':'100'}, {'spoilage_percent':'-1'}, {'spoilage_percent':'1.001'},
    {'cost_source':'other'}, {'market_price':''}, {'harvest_quantity':'1.00001'},
])
def test_invalid_sales_inputs_fail_without_any_saved_records(app, client, decision_users, changes):
    login(client, decision_users[0])
    response, context = calculate(app, client, sales_values(**changes))
    assert response.status_code == 400
    assert context['error'].startswith('decision_error_')
    assert context['sales'] is None
    with app.app_context():
        assert FarmLedgerEntry.query.count() == 0


def test_selected_month_uses_only_own_expenses_and_does_not_add_manual_cost(app, client, decision_users):
    with app.app_context():
        entries = [
            (decision_users[0], 'expense', date(2026,10,1), '.10'),
            (decision_users[0], 'expense', date(2026,10,31), '.20'),
            (decision_users[0], 'income', date(2026,10,2), '7000'),
            (decision_users[0], 'expense', date(2026,9,30), '500'),
            (decision_users[1], 'expense', date(2026,10,2), '9999'),
        ]
        for index, (owner, kind, day, amount) in enumerate(entries):
            db.session.add(FarmLedgerEntry(farmer_id=owner, kind=kind, category='other', entry_date=day,
                amount=Decimal(amount), submission_id=f'ledger-{index}'))
        db.session.commit()
    login(client, decision_users[0])
    response, context = calculate(app, client, sales_values(cost_source='ledger', cultivation_cost='800'))
    assert response.status_code == 200
    assert context['sales']['cost'] == Decimal('.30')
    assert context['sales']['ledger_count'] == 2
    assert context['sales']['ledger_month'] == '2026-10'
    assert context['sales']['farmgate_net'] == Decimal('17999.70')
    assert b'not automatically crop-specific' in response.data
    with app.app_context():
        assert FarmLedgerEntry.query.count() == 5


@pytest.mark.parametrize('month', ['2026-13','2026-00','2026-1','invalid','1899-12','2101-01',''])
def test_invalid_ledger_month_cannot_be_interpreted_as_zero_cost(app, client, decision_users, month):
    login(client, decision_users[0])
    response, context = calculate(app, client, sales_values(cost_source='ledger', ledger_month=month))
    assert response.status_code == 400
    assert context['error'] == 'decision_error_month'


def test_empty_selected_month_is_explicit_error(app, client, decision_users):
    login(client, decision_users[0])
    response, context = calculate(app, client, sales_values(cost_source='ledger'))
    assert response.status_code == 400
    assert context['error'] == 'decision_error_empty_ledger'


def test_water_uses_exact_area_depth_efficiency_and_flow():
    result = water_calculation(water_values())
    assert result['area_m2'] == Decimal('4046.8564224')
    assert result['net_litres'] == Decimal('40468.564224')
    assert result['gross_litres'] == Decimal('50585.70528')
    assert result['pump_minutes'] == Decimal('505.8570528')
    assert result['pump_hours'] == Decimal('505.8570528') / Decimal('60')


def test_guntha_acre_hectare_and_square_metres_do_not_mix_units():
    acre = water_calculation(water_values())
    guntha = water_calculation(water_values(area_value='40', area_unit='guntha'))
    assert guntha == acre
    hectare = water_calculation(water_values(area_unit='hectare', depth_mm='1', efficiency_percent='100', pump_lpm=''))
    metres = water_calculation(water_values(area_value='10000', area_unit='m2', depth_mm='1', efficiency_percent='100', pump_lpm=''))
    assert hectare == metres
    assert hectare['net_litres'] == hectare['gross_litres'] == Decimal('10000')
    assert hectare['pump_minutes'] is None
    assert AREA_M2['acre'] == AREA_M2['guntha'] * 40


@pytest.mark.parametrize('changes', [
    {'area_value':'0'}, {'area_value':'-1'}, {'area_value':'NaN'}, {'area_value':'1e20'},
    {'area_value':'100000001','area_unit':'m2'}, {'area_value':'100000000','area_unit':'acre'},
    {'area_unit':'feet'}, {'depth_mm':'0'}, {'depth_mm':'501'}, {'depth_mm':'Infinity'},
    {'efficiency_percent':'0'}, {'efficiency_percent':'100.01'}, {'efficiency_percent':'0.001'},
    {'pump_lpm':'0'}, {'pump_lpm':'-1'}, {'pump_lpm':'NaN'}, {'pump_lpm':'1000001'},
])
def test_invalid_water_values_cannot_produce_a_schedule(app, client, decision_users, changes):
    login(client, decision_users[0])
    response, context = calculate(app, client, water_values(**changes))
    assert response.status_code == 400
    assert context['water'] is None and context['sales'] is None
    assert context['error'].startswith('decision_error_')


def test_result_preserves_inputs_and_does_not_prescribe_water(app, client, decision_users):
    login(client, decision_users[0])
    response, context = calculate(app, client, water_values())
    assert response.status_code == 200
    assert context['values']['area_value'] == '1'
    assert context['values']['area_unit'] == 'acre'
    assert b'not a watering prescription' in response.data
    assert b'50,585.71 L' in response.data
    with app.app_context():
        assert FarmLedgerEntry.query.count() == 0


def test_bad_calculator_and_xss_are_rejected_and_escaped(app, client, decision_users):
    login(client, decision_users[0])
    response, context = calculate(app, client, {'calculator':'unknown'})
    assert response.status_code == 400 and context['error'] == 'decision_error_calculator'
    response, context = calculate(app, client, sales_values(cultivation_cost='"><img src=x onerror=alert(1)>'))
    assert response.status_code == 400
    assert b'<img src=x' not in response.data
    assert b'&lt;img src=x' in response.data


def test_calculator_requires_real_csrf_when_protection_enabled(app, client, decision_users):
    login(client, decision_users[0]); app.config['CSRF_ENABLED'] = True
    assert client.post('/farm-decisions', data=sales_values()).status_code == 400
    page = client.get('/farm-decisions')
    token = re.search(rb'name="csrf_token" value="([^"]+)"',page.data).group(1).decode()
    assert client.post('/farm-decisions',data=sales_values(csrf_token=token)).status_code == 200


def test_static_translations_cover_labels_errors_and_results_without_api():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is needed for the browser dictionary regression')
    root = Path(__file__).resolve().parents[1]
    source = (root/'routes/farm_decisions.py').read_text() + (root/'templates/decisions/index.html').read_text()
    keys = sorted(set(re.findall(r'[\'\"](decision_[a-z_]+)[\'\"]',source)))
    script = """
const assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm');
const dictionary={en:{},hi:{},mr:{}};
vm.runInNewContext(fs.readFileSync('static/js/decisions-i18n.js','utf8'), {
  TRANSLATIONS:dictionary, document:{readyState:'loading',addEventListener() {}}
});
for (const key of JSON.parse(process.argv[1])) {
  for (const lang of ['en','hi','mr']) assert.ok(dictionary[lang][key], `${lang}/${key}`);
}
"""
    result = subprocess.run([node,'-e',script,json.dumps(keys)],cwd=root,text=True,capture_output=True,timeout=10)
    assert result.returncode == 0, result.stderr

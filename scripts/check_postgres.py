"""Check real PostgreSQL startup and core writes in an isolated Docker database.

Run from an installed project venv. Requires a running Docker daemon; no Render
credentials are used, and only the container created by this command is removed.
"""
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from config import normalize_database_url
from database.seed import seed_roadmaps
from farm_tools_models import FarmLedgerEntry, FarmTask
from advisory_models import FarmField, FieldObservation, AdvisoryFollowup, AdvisoryTaskLink
from credit_models import CreditAccount, CreditPayment
from models import db, User, Product, Order, CheckoutAttempt, CropRoadmap


def main():
    container = 'organic-postgres-check-' + secrets.token_hex(6)
    password = secrets.token_urlsafe(32)
    environment = dict(os.environ, POSTGRES_PASSWORD=password)
    subprocess.run([
        'docker', 'run', '--detach', '--rm', '--name', container,
        '--publish', '127.0.0.1::5432', '--memory', '256m', '--cpus', '1',
        '--env', 'POSTGRES_PASSWORD', '--env', 'POSTGRES_DB=organic_farming_check',
        'postgres:16-alpine',
    ], env=environment, check=True, capture_output=True, text=True)
    application = None
    try:
        address = subprocess.check_output(['docker', 'port', container, '5432/tcp'], text=True).strip()
        uri = normalize_database_url(URL.create('postgresql', username='postgres', password=password,
            host='127.0.0.1', port=int(address.rsplit(':', 1)[1]), database='organic_farming_check',
            query={'connect_timeout': '2'}).render_as_string(hide_password=False))
        engine = create_engine(uri)
        deadline = time.monotonic() + 40
        while True:
            try:
                with engine.connect() as connection:
                    connection.execute(text('SELECT 1'))
                break
            except Exception:
                if time.monotonic() >= deadline:
                    raise RuntimeError('Temporary PostgreSQL did not become ready.') from None
                time.sleep(.25)
        engine.dispose()
        with tempfile.TemporaryDirectory(prefix='organic-postgres-uploads-') as directory:
            application = create_app({'TESTING': True, 'SECRET_KEY': secrets.token_hex(32),
                'SQLALCHEMY_DATABASE_URI': uri, 'UPLOAD_FOLDER': directory, 'CSRF_ENABLED': False,
                'SESSION_COOKIE_SECURE': False, 'GEMINI_API_KEY': '', 'OPENWEATHER_API_KEY': '',
                'RAZORPAY_KEY_ID': '', 'RAZORPAY_KEY_SECRET': ''})
            farmer, buyer = application.test_client(), application.test_client()
            for role, client in [('farmer', farmer), ('buyer', buyer)]:
                registration = client.post('/auth/register', data={'name': 'Postgres ' + role,
                    'email': role + '@postgres.example', 'password': 'Temporary-check-43!',
                    'confirm_password': 'Temporary-check-43!', 'role': role})
                assert registration.status_code == 302
                login = client.post('/auth/login', data={'email': role + '@postgres.example',
                    'password': 'Temporary-check-43!'})
                assert login.status_code == 302
            assert farmer.post('/marketplace/add', data={'name': 'Test tomatoes', 'price': '19.95',
                'quantity': '10 kg', 'category': 'Vegetables'}).status_code == 302
            with application.app_context():
                product_id = Product.query.one().id
                assert db.engine.dialect.driver == 'psycopg2'
                assert CropRoadmap.query.count() == 10
                assert seed_roadmaps() == 0
            assert buyer.post(f'/cart/add/{product_id}', data={'quantity': '2'}).status_code == 302
            cart = buyer.get('/cart/')
            token = re.search(rb'name="checkout_token" value="([^"]+)"', cart.data).group(1).decode()
            checkout = buyer.post('/cart/checkout', data={'checkout_token': token,
                'delivery_location': 'Test village, Sambhajinagar 431001'})
            assert checkout.status_code == 302 and checkout.location.endswith('/orders/my')
            with application.app_context():
                order = Order.query.one()
                order_id = order.id
                assert order.product_name == 'Test tomatoes' and order.quantity_unit == 'kg'
                assert Decimal(str(order.total_price)).quantize(Decimal('.01')) == Decimal('39.90')
                assert Product.query.one().quantity == '8 kg'
                assert CheckoutAttempt.query.one().status == 'complete'
            for status in ('accepted', 'shipped', 'delivered'):
                assert farmer.post(f'/orders/{order_id}/update', data={'status': status}).status_code == 302
            assert buyer.post(f'/orders/{order_id}/rate', data={'stars': '5', 'review': 'Fresh produce'}).status_code == 302
            today = datetime.now(ZoneInfo('Asia/Kolkata')).date().isoformat()
            assert farmer.get('/farm-tools').status_code == 200
            with farmer.session_transaction() as session:
                task_token = session['farm_tools_task_token']
            assert farmer.post('/farm-tools/tasks', data={'submission_id':task_token,
                'title':'Check irrigation','crop':'Tomato','due_date':today}).status_code == 303
            for kind, amount in [('expense','0.10'), ('income','0.30')]:
                farmer.get('/farm-tools')
                with farmer.session_transaction() as session:
                    ledger_token = session['farm_tools_ledger_token']
                assert farmer.post('/farm-tools/ledger', data={'submission_id':ledger_token,
                    'kind':kind,'amount':amount,'category':'other','entry_date':today}).status_code == 303
            with application.app_context():
                amounts = {entry.kind:entry.amount for entry in FarmLedgerEntry.query.all()}
                assert amounts['income'] - amounts['expense'] == Decimal('0.20')
                assert FarmTask.query.one().title == 'Check irrigation'
                assert User.query.count() == 2
                assert Order.query.one().rating.stars == 5
                db.create_all()
            assert b'0.30' in farmer.get('/farm-tools/ledger.csv?month=' + today[:7]).data
            # New field observations and advice snapshots must work with real JSON,
            # fixed-scale area values, ownership and foreign keys on PostgreSQL.
            assert farmer.get('/my-farm/fields/new').status_code == 200
            with farmer.session_transaction() as session:
                field_token = session['advisory_field_token']
            field_response = farmer.post('/my-farm/fields', data={'submission_id':field_token,
                'name':'North tomato field','crop':'tomato','stage':'vegetative','soil':'loamy',
                'irrigation':'drip','area_value':'1','area_unit':'acre','planting_date':today})
            assert field_response.status_code == 303
            field_id = int(field_response.location.rsplit('/',1)[1])
            report_ids = []
            for index in range(2):
                farmer.get(f'/my-farm/fields/{field_id}')
                with farmer.session_transaction() as session:
                    observation_token = session['advisory_observation_token']
                response = farmer.post(f'/my-farm/fields/{field_id}/observe',data={
                    'submission_id':observation_token,'moisture':'wet','waterlogging':'1',
                    'pest_present':'0','leaf_symptoms':'wilting','inspected_plants':'10',
                    'affected_plants':'2','notes':'पाणी साचले आहे आणि पाने कोमेजली आहेत'})
                assert response.status_code == 303
                report_id = int(response.location.rsplit('/',1)[1])
                report_ids.append(report_id)
                assert farmer.get(response.location).status_code == 200
                if index == 0:
                    with application.app_context():
                        row = db.session.get(FieldObservation,report_id)
                        action_code = row.report_data['priorities'][0]['code']
                    assert farmer.post(f'/my-farm/reports/{report_id}/actions/{action_code}',
                                       data={'language':'mr'}).status_code == 303
                    assert farmer.post(f'/my-farm/reports/{report_id}/followup',data={
                        'verdict':'improved','note':'निचरा तपासला'}).status_code == 303
            learned_report = farmer.get(f'/my-farm/reports/{report_ids[-1]}')
            assert f'href="/my-farm/reports/{report_ids[0]}"'.encode() in learned_report.data
            with application.app_context():
                assert FarmField.query.one().area_m2 == Decimal('4046.86')
                assert FieldObservation.query.count() == 2
                assert AdvisoryFollowup.query.one().verdict == 'improved'
                saved = AdvisoryTaskLink.query.one()
                assert saved.task is not None
                saved_task_id = saved.task_id
            assert farmer.post(f'/farm-tools/tasks/{saved_task_id}/delete').status_code == 303
            with application.app_context():
                assert AdvisoryTaskLink.query.one().task_id is None
                db.create_all()
            assert buyer.get(f'/my-farm/reports/{report_ids[0]}').status_code == 403
            economics = farmer.post('/farm-decisions',data={'calculator':'sales','harvest_quantity':'1000',
                'harvest_unit':'kg','cost_source':'manual','cultivation_cost':'12000',
                'farmgate_price':'18','farmgate_price_unit':'kg','market_price':'22',
                'market_price_unit':'kg','transport_cost':'3000','market_fees':'0','spoilage_percent':'10'})
            assert economics.status_code == 200 and b'6,000.00' in economics.data and b'4,800.00' in economics.data
            # Common-problem help works without an account or external provider.
            public = application.test_client()
            help_response = public.post('/farm-help', data={'problem':'water',
                'moisture':'wet','waterlogging':'1'})
            assert help_response.status_code == 200 and b'data-step="waterlogging"' in help_response.data
            assert farmer.get('/credit-book').status_code == 200
            with farmer.session_transaction() as session:
                credit_token = session['credit_account_token']
            created = farmer.post('/credit-book/accounts',data={'submission_id':credit_token,
                'direction':'receive','contact_name':'Test produce trader','amount':'१०००.५०',
                'entry_date':today,'due_date':today})
            assert created.status_code == 303
            credit_id = int(created.location.rsplit('/',1)[1])
            farmer.get(created.location)
            with farmer.session_transaction() as session:
                payment_token = session['credit_payment_token']
            payment = {'submission_id':payment_token,'amount':'२००.२५','entry_date':today}
            payment_path = f'/credit-book/accounts/{credit_id}/payments'
            assert farmer.post(payment_path,data=payment).status_code == 303
            assert farmer.post(payment_path,data=payment).status_code == 303
            with application.app_context():
                credit = db.session.get(CreditAccount,credit_id)
                assert credit.remaining == Decimal('800.25')
                assert CreditPayment.query.count() == 1
                assert FarmLedgerEntry.query.count() == 2
            farmer.get(created.location)
            with farmer.session_transaction() as session:
                next_payment = session['credit_payment_token']
            assert farmer.post(payment_path,data=payment | {'submission_id':next_payment,'amount':'801'}).status_code == 400
            assert b'800.25' in farmer.get('/auth/farmer/dashboard').data
            assert buyer.get(created.location).status_code == 403
            farmer.get('/credit-book')
            with farmer.session_transaction() as session:
                wrong_token = session['credit_account_token']
            mistaken = farmer.post('/credit-book/accounts',data={'submission_id':wrong_token,
                'direction':'pay','contact_name':'Mistaken test entry','amount':'100','entry_date':today})
            assert mistaken.status_code == 303
            wrong_id = int(mistaken.location.rsplit('/',1)[1])
            assert farmer.post(f'/credit-book/accounts/{wrong_id}/void',data={'void_reason':'Entered twice by mistake'}).status_code == 303
            with application.app_context():
                voided = db.session.get(CreditAccount,wrong_id)
                assert voided.voided and voided.remaining == 0
                assert CreditPayment.query.count() == 1
            print('PostgreSQL 16 checks passed: startup/schema, guides, accounts, orders/receipts/stock, ledger/CSV, field JSON snapshots, action/task links, outcomes, local ML, calculations, account-free help, exact credit settlements/retries, and mistaken-entry correction.')
    finally:
        if application:
            with application.app_context():
                db.session.remove()
                db.engine.dispose()
        subprocess.run(['docker','stop','--time','2',container],check=False,capture_output=True)


if __name__ == '__main__':
    main()

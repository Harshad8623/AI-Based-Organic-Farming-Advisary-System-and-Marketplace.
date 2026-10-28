"""Real request/database checks for marketplace and checkout invariants."""
import hashlib
import hmac
import io
import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image
from werkzeug.security import generate_password_hash

from commerce import parse_stock, price_paise, stock_text, MAX_TOTAL_PAISE
from models import db, User, Product, CartItem, Order, Rating, CheckoutAttempt, OrderReceipt


@pytest.fixture
def people(app):
    with app.app_context():
        users = [User(name=role.title(), email=f'{role}@example.test', role=role.split('_')[0],
                      password=generate_password_hash('test-password'))
                 for role in ('farmer', 'buyer', 'farmer_other', 'buyer_other')]
        db.session.add_all(users)
        db.session.flush()
        product = Product(farmer_id=users[0].id, name='Organic tomatoes', price=12.35,
                          quantity='10.5 kg', category='Vegetables')
        db.session.add(product)
        db.session.commit()
        return dict(zip(('farmer', 'buyer', 'other_farmer', 'other_buyer'), (u.id for u in users))), product.id


def login(client, user_id):
    with client.session_transaction() as session:
        session.clear()
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def add(client, product, quantity='2'):
    return client.post(f'/cart/add/{product}', data={'quantity': quantity})


def checkout(client, token=None):
    if token is None:
        assert client.get('/cart/').status_code == 200
        with client.session_transaction() as session:
            token = session['checkout_token']
    return client.post('/cart/checkout', data={'checkout_token': token,
                                              'delivery_location': 'Village Main Road, Sambhajinagar 431001'})


@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-1', '0', '0.001', '1000001', '1e100000', 'abc', None])
def test_invalid_money_is_rejected(value):
    with pytest.raises(ValueError):
        price_paise(value)


def test_decimal_stock_and_money_are_not_truncated():
    assert parse_stock('10.5 kg') == (Decimal('10.5'), 'kg')
    assert stock_text(Decimal('8.50'), 'kg') == '8.5 kg'
    assert price_paise('12.35') == 1235
    for text in ('5 x 10 kg', '-3 kg', 'NaN kg', '10.0001 kg', '1e4 kg'):
        with pytest.raises(ValueError):
            parse_stock(text)


@pytest.mark.parametrize('quantity', ['-1', '0', '1.5', 'NaN', '501', '11'])
def test_cart_rejects_invalid_or_excess_stock(app, client, people, quantity):
    users, product = people
    login(client, users['buyer'])
    add(client, product, quantity)
    with app.app_context():
        assert CartItem.query.count() == 0
        assert db.session.get(Product, product).quantity == '10.5 kg'


def test_cod_checkout_is_atomic_and_replay_safe(app, client, people):
    users, product = people
    login(client, users['buyer'])
    add(client, product, '3')
    assert client.get('/cart/').status_code == 200
    with client.session_transaction() as session:
        token = session['checkout_token']
    assert checkout(client, token).status_code == 302
    assert checkout(client, token).status_code == 302
    with app.app_context():
        order = Order.query.one()
        assert order.total_price == 37.05
        assert order.quantity_ordered == 3
        assert order.buyer_id == users['buyer']
        assert db.session.get(Product, product).quantity == '7.5 kg'
        assert CartItem.query.count() == 0
        assert CheckoutAttempt.query.one().status == 'complete'


def test_checkout_rechecks_all_stock_and_rolls_back(app, client, people):
    users, product = people
    login(client, users['buyer'])
    add(client, product, '3')
    with app.app_context():
        db.session.get(Product, product).quantity = '1 kg'
        db.session.commit()
    checkout(client)
    with app.app_context():
        assert Order.query.count() == 0
        assert CheckoutAttempt.query.count() == 0
        assert CartItem.query.one().quantity == 3
        assert db.session.get(Product, product).quantity == '1 kg'


def test_competing_buyers_cannot_oversell(app, client, people):
    users, product = people
    other = app.test_client()
    login(client, users['buyer'])
    login(other, users['other_buyer'])
    add(client, product, '8')
    add(other, product, '8')
    checkout(client)
    checkout(other)
    with app.app_context():
        assert Order.query.count() == 1
        assert db.session.get(Product, product).quantity == '2.5 kg'
        assert CartItem.query.filter_by(buyer_id=users['other_buyer']).one().quantity == 8


def test_checkout_rejects_malformed_unicode_token(app, client, people):
    users, product = people
    login(client, users['buyer'])
    add(client, product)
    assert checkout(client, 'अनधिकृत').status_code == 302
    with app.app_context():
        assert Order.query.count() == 0


def test_cart_owner_and_role_boundaries(app, client, people):
    users, product = people
    login(client, users['buyer'])
    add(client, product)
    with app.app_context():
        item_id = CartItem.query.one().id
    login(client, users['other_buyer'])
    assert client.post(f'/cart/update/{item_id}', data={'quantity': '1'}).status_code == 403
    assert client.post(f'/cart/remove/{item_id}').status_code == 403
    login(client, users['farmer'])
    assert add(client, product).status_code == 403
    assert client.get('/cart/').status_code == 403


def test_rejection_returns_stock_once_and_forbids_status_skips(app, client, people):
    users, product = people
    login(client, users['buyer'])
    add(client, product, '3')
    checkout(client)
    with app.app_context():
        order_id = Order.query.one().id
    login(client, users['other_farmer'])
    assert client.post(f'/orders/{order_id}/update', data={'status': 'rejected'}).status_code == 403
    login(client, users['farmer'])
    client.post(f'/orders/{order_id}/update', data={'status': 'delivered'})
    with app.app_context():
        assert db.session.get(Order, order_id).status == 'pending'
    client.post(f'/orders/{order_id}/update', data={'status': 'rejected'})
    client.post(f'/orders/{order_id}/update', data={'status': 'rejected'})
    with app.app_context():
        assert db.session.get(Order, order_id).status == 'rejected'
        assert db.session.get(Product, product).quantity == '10.5 kg'


def test_delivery_rating_and_history_survive_listing_removal(app, client, people):
    users, product = people
    login(client, users['buyer'])
    add(client, product)
    checkout(client)
    with app.app_context():
        order_id = Order.query.one().id
    client.post(f'/orders/{order_id}/rate', data={'stars': '5'})
    with app.app_context():
        assert Rating.query.count() == 0
    login(client, users['farmer'])
    client.post(f'/marketplace/delete/{product}')
    with app.app_context():
        assert db.session.get(Product, product) is not None
    for status in ('accepted', 'shipped', 'delivered'):
        client.post(f'/orders/{order_id}/update', data={'status': status})
    login(client, users['other_buyer'])
    assert client.post(f'/orders/{order_id}/rate', data={'stars': '5'}).status_code == 403
    login(client, users['buyer'])
    client.post(f'/orders/{order_id}/rate', data={'stars': '5', 'review': 'Fresh produce'})
    client.post(f'/orders/{order_id}/rate', data={'stars': '1'})
    with app.app_context():
        assert Rating.query.one().stars == 5
    login(client, users['farmer'])
    client.post(f'/marketplace/delete/{product}')
    with app.app_context():
        assert db.session.get(Product, product) is None
        assert db.session.get(Order, order_id).product_id is None
        assert Rating.query.one().product_id is None
    login(client, users['buyer'])
    assert client.get('/orders/my').status_code == 200


@pytest.mark.parametrize('price', ['nan', 'inf', '-2', '0.001'])
def test_listing_price_validation(app, client, people, price):
    users, _ = people
    login(client, users['farmer'])
    result = client.post('/marketplace/add', data={'name': 'Rice', 'price': price, 'quantity': '20 kg', 'category': 'Grains'})
    assert result.status_code == 400
    with app.app_context():
        assert Product.query.count() == 1


def test_listing_upload_verifies_real_bytes_and_preserves_input(app, client, people):
    users, _ = people
    login(client, users['farmer'])
    result = client.post('/marketplace/add', data={'name': 'Rice', 'price': '42.50', 'quantity': '20 kg', 'category': 'Grains',
                                                  'image': (io.BytesIO(b'<script>evil</script>'), 'rice.jpg')},
                         content_type='multipart/form-data')
    assert result.status_code == 400
    assert b'value="Rice"' in result.data
    assert not list(Path(app.config['UPLOAD_FOLDER']).iterdir())
    output = io.BytesIO()
    Image.new('RGB', (80, 40), 'green').save(output, 'PNG')
    output.seek(0)
    result = client.post('/marketplace/add', data={'name': 'Rice', 'price': '42.50', 'quantity': '20 kg', 'category': 'Grains',
                                                  'image': (output, 'rice.png')}, content_type='multipart/form-data')
    assert result.status_code == 302
    with app.app_context():
        rice = Product.query.filter_by(name='Rice').one()
        assert rice.price == 42.5
        image = Image.open(Path(app.config['UPLOAD_FOLDER']) / rice.image_filename)
        assert image.format == 'JPEG'


def test_listing_edits_are_owned_and_unit_changes_protected(app, client, people):
    users, product = people
    login(client, users['other_farmer'])
    assert client.get(f'/marketplace/edit/{product}').status_code == 403
    assert client.post(f'/marketplace/delete/{product}').status_code == 403
    login(client, users['buyer'])
    add(client, product)
    checkout(client)
    login(client, users['farmer'])
    result = client.post(f'/marketplace/edit/{product}', data={'name': 'Tomatoes', 'price': '12.35', 'quantity': '10 bags', 'category': 'Vegetables'})
    assert result.status_code == 400
    with app.app_context():
        assert db.session.get(Product, product).stock_unit == 'kg'


@pytest.fixture
def gateway(app, monkeypatch):
    app.config.update(RAZORPAY_KEY_ID='rzp_test_example', RAZORPAY_KEY_SECRET='test-gateway-key')
    state = {'requests': [], 'payments': {}}
    def create(payload, **kwargs):
        assert kwargs["timeout"] == (5, 15)
        state['requests'].append(payload)
        return {'id': f'order_{len(state["requests"])}'}
    fake = SimpleNamespace(order=SimpleNamespace(create=create), payment=SimpleNamespace(fetch=lambda key, **kwargs: state['payments'][key]))
    monkeypatch.setattr('routes.cart._razorpay_client', lambda: fake)
    return state


def begin_payment(client):
    return client.post('/cart/create-razorpay-order', json={'delivery_location': 'Main Road, village 431001'})


@pytest.mark.parametrize('method', ['cod', 'gateway'])
def test_checkout_accepts_exact_existing_total_limit(app, client, people, gateway, method):
    users, product_id = people
    with app.app_context():
        product = db.session.get(Product, product_id)
        product.price = 20000
        product.quantity = '500 kg'
        db.session.commit()
    login(client, users['buyer'])
    add(client, product_id, '500')
    if method == 'cod':
        assert checkout(client).status_code == 302
    else:
        result = begin_payment(client)
        assert result.status_code == 200
        assert result.get_json()['amount'] == MAX_TOTAL_PAISE
        assert gateway['requests'][0]['amount'] == MAX_TOTAL_PAISE
    with app.app_context():
        attempt = CheckoutAttempt.query.one()
        assert attempt.amount_paise == MAX_TOTAL_PAISE
        assert attempt.amount_paise <= 2147483647
        if method == 'cod':
            assert Order.query.one().total_price == 10000000
            assert db.session.get(Product, product_id).quantity == '0 kg'
            assert CartItem.query.count() == 0
        else:
            assert Order.query.count() == 0
            assert db.session.get(Product, product_id).quantity == '500 kg'
            assert CartItem.query.one().quantity == 500


@pytest.mark.parametrize('method', ['cod', 'gateway'])
@pytest.mark.parametrize('cart_shape', ['single_line', 'aggregate'])
def test_oversized_checkout_never_creates_attempt_or_changes_stock(app, client, people, gateway, method, cart_shape):
    users, product_id = people
    with app.app_context():
        product = db.session.get(Product, product_id)
        product.price = 20000.01 if cart_shape == 'single_line' else 20000
        product.quantity = '500 kg'
        db.session.commit()
    login(client, users['buyer'])
    add(client, product_id, '500')
    if cart_shape == 'aggregate':
        # The main line is within the cap; adding just one paise must reject
        # the complete cart before any order, gateway request or stock write.
        with app.app_context():
            extra = Product(farmer_id=users['farmer'], name='Extra produce', price=0.01,
                            quantity='1 kg', category='Vegetables')
            db.session.add(extra)
            db.session.commit()
            extra_id = extra.id
        add(client, extra_id, '1')
    if method == 'cod':
        response = checkout(client)
        assert response.status_code == 302
        assert response.location.endswith('/cart/')
        with client.session_transaction() as session:
            assert any('total is too large' in text for _, text in session['_flashes'])
    else:
        response = begin_payment(client)
        assert response.status_code == 400
        assert 'total is too large' in response.get_json()['error']
    assert gateway['requests'] == []
    with app.app_context():
        assert CheckoutAttempt.query.count() == 0
        assert Order.query.count() == 0
        assert db.session.get(Product, product_id).quantity == '500 kg'
        assert CartItem.query.filter_by(product_id=product_id).one().quantity == 500
        if cart_shape == 'aggregate':
            assert db.session.get(Product, extra_id).quantity == '1 kg'
            assert CartItem.query.filter_by(product_id=extra_id).one().quantity == 1


def confirm(client, gateway_id, payment_id='pay_1', signature=None):
    signature = signature or hmac.new(b'test-gateway-key', f'{gateway_id}|{payment_id}'.encode(), hashlib.sha256).hexdigest()
    return client.post('/cart/verify-payment', data={'razorpay_order_id': gateway_id,
                                                  'razorpay_payment_id': payment_id, 'razorpay_signature': signature})


def test_gateway_unavailable_does_not_pretend_payment(app, client, people):
    users, product = people
    login(client, users['buyer'])
    add(client, product)
    assert begin_payment(client).status_code == 503
    with app.app_context():
        assert Order.query.count() == CheckoutAttempt.query.count() == 0


def test_payment_snapshot_owner_capture_and_replay(app, client, people, gateway):
    users, product = people
    login(client, users['buyer'])
    add(client, product, '2')
    data = begin_payment(client).get_json()
    assert data['amount'] == 2470
    order_id = data['razorpay_order_id']
    gateway['payments']['pay_1'] = {'order_id': order_id, 'status': 'captured', 'amount': 2470, 'currency': 'INR'}
    login(client, users['other_buyer'])
    assert confirm(client, order_id).status_code == 400
    login(client, users['buyer'])
    assert confirm(client, order_id, signature='अवैध').status_code == 400
    # A later cart edit cannot inflate what was actually paid for.
    add(client, product, '1')
    assert confirm(client, order_id).status_code == 302
    assert confirm(client, order_id).status_code == 302
    with app.app_context():
        order = Order.query.one()
        assert order.quantity_ordered == 2 and order.total_price == 24.7
        assert order.razorpay_payment_id == 'pay_1'
        assert CartItem.query.one().quantity == 1
        assert db.session.get(Product, product).quantity == '8.5 kg'
        assert CheckoutAttempt.query.one().status == 'complete'
    login(client, users['farmer'])
    client.post(f'/orders/{order.id}/update', data={'status': 'rejected'})
    with app.app_context():
        assert Order.query.one().status == 'pending'  # Refunds are not falsely implied.


@pytest.mark.parametrize('patch', [{'status': 'authorized'}, {'amount': 1}, {'currency': 'USD'}, {'order_id': 'another'}])
def test_unconfirmed_or_mismatched_payment_cannot_fulfil(app, client, people, gateway, patch):
    users, product = people
    login(client, users['buyer'])
    add(client, product)
    order_id = begin_payment(client).get_json()['razorpay_order_id']
    gateway['payments']['pay_1'] = {'order_id': order_id, 'status': 'captured', 'amount': 2470, 'currency': 'INR', **patch}
    confirm(client, order_id)
    with app.app_context():
        assert Order.query.count() == 0
        assert db.session.get(Product, product).quantity == '10.5 kg'
        assert CheckoutAttempt.query.one().status == 'pending'


def test_payment_stock_conflict_keeps_reference_and_no_oversell(app, client, people, gateway):
    users, product = people
    login(client, users['buyer'])
    add(client, product)
    order_id = begin_payment(client).get_json()['razorpay_order_id']
    gateway['payments']['pay_1'] = {'order_id': order_id, 'status': 'captured', 'amount': 2470, 'currency': 'INR'}
    with app.app_context():
        db.session.get(Product, product).quantity = '1 kg'
        db.session.commit()
    confirm(client, order_id)
    with client.session_transaction() as session:
        assert any('pay_1' in message and 'do not pay again' in message for _, message in session['_flashes'])
    with app.app_context():
        assert Order.query.count() == 0
        assert db.session.get(Product, product).quantity == '1 kg'


def test_receipts_survive_listing_changes_and_all_order_pages_render(app, client, people):
    users, product_id = people
    login(client, users['buyer'])
    add(client, product_id, '2')
    checkout(client)
    assert client.get('/orders/my').status_code == 200
    with app.app_context():
        order_id = Order.query.one().id
        receipt = OrderReceipt.query.one()
        assert (receipt.product_name, receipt.unit, receipt.unit_price_paise) == ('Organic tomatoes', 'kg', 1235)
        db.session.get(Product, product_id).name = 'Renamed listing'
        db.session.commit()
    login(client, users['farmer'])
    for status in ('pending', 'accepted', 'shipped', 'delivered'):
        if status != 'pending':
            client.post(f'/orders/{order_id}/update', data={'status': status})
        page = client.get('/orders/farmer')
        assert page.status_code == 200
        assert b'Organic tomatoes' in page.data
    login(client, users['buyer'])
    assert client.get(f'/orders/{order_id}/rate').status_code == 200
    login(client, users['farmer'])
    client.post(f'/marketplace/delete/{product_id}')
    login(client, users['buyer'])
    page = client.get('/orders/my')
    assert page.status_code == 200
    assert b'Organic tomatoes' in page.data
    assert b'2 kg' in page.data
    with app.app_context():
        assert OrderReceipt.query.count() == 1
        assert Order.query.one().product_id is None


def test_legacy_ambiguous_stock_cannot_be_bought_or_invented_on_rejection(app, client, people):
    users, product_id = people
    with app.app_context():
        product = db.session.get(Product, product_id)
        product.quantity = '5 x 10 kg'
        legacy = Order(buyer_id=users['buyer'], farmer_id=users['farmer'], product_id=product_id,
                       quantity_ordered=2, total_price=24.7, delivery_location='Existing village address',
                       payment_method='cod', status='pending')
        db.session.add(legacy)
        db.session.commit()
        legacy_id = legacy.id
    login(client, users['buyer'])
    add(client, product_id)
    with app.app_context():
        assert CartItem.query.count() == 0
    login(client, users['farmer'])
    client.post(f'/orders/{legacy_id}/update', data={'status': 'rejected'})
    with app.app_context():
        assert db.session.get(Order, legacy_id).status == 'rejected'
        assert db.session.get(Product, product_id).quantity == '5 x 10 kg'
    with client.session_transaction() as session:
        assert any('Stock was left unchanged' in text for _, text in session['_flashes'])

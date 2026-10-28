from datetime import datetime, timezone

from database.seed import seed_roadmaps
from models import db, User, Product, Order, CropRoadmap
from routes.analytics import _month_starts


def sign_in(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def test_months_follow_calendar_without_duplicate_february():
    months = _month_starts(datetime(2024, 3, 31, tzinfo=timezone.utc))
    assert len({(month.year, month.month) for month in months}) == 12
    assert months[0] == datetime(2023, 4, 1, tzinfo=timezone.utc)
    assert months[-2:] == [datetime(2024, 2, 1, tzinfo=timezone.utc), datetime(2024, 3, 1, tzinfo=timezone.utc)]


def test_analytics_requires_login_and_contains_no_sample_data(app, client):
    assert client.get('/analytics/').status_code == 302
    with app.app_context():
        user = User(name='Farmer', email='farmer@example.com', password='unused', role='farmer')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    sign_in(client, user_id)
    response = client.get('/analytics/')
    assert response.status_code == 200
    assert b'No listings yet' in response.data
    assert b'Soil Fertility Index' not in response.data
    assert b'Average Yield Trend' not in response.data
    assert b'Avg. Price' not in response.data


def test_analytics_private_order_values_and_escaped_categories(app, client):
    with app.app_context():
        farmer = User(name='Farmer', email='farmer@example.com', password='unused', role='farmer')
        buyer = User(name='Buyer', email='buyer@example.com', password='unused', role='buyer')
        other = User(name='Other', email='other@example.com', password='unused', role='buyer')
        db.session.add_all([farmer, buyer, other]); db.session.flush()
        product = Product(farmer_id=farmer.id, name='Tomato', price=25, quantity='20 kg', category='</script><script>alert(1)</script>')
        db.session.add(product); db.session.flush()
        for user, amount in [(buyer, 25.50), (other, 9823.25)]:
            db.session.add(Order(buyer_id=user.id, farmer_id=farmer.id, product_id=product.id,
                total_price=amount, quantity_ordered=1, status='delivered', payment_method='cod', delivery_location='Test village'))
        db.session.commit()
        buyer_id = buyer.id
    sign_in(client, buyer_id)
    response = client.get('/analytics/')
    assert response.status_code == 200
    assert b'25.50' in response.data
    assert b'9823.25' not in response.data
    assert b'<script>alert(1)</script>' not in response.data
    assert b'&lt;/script&gt;' in response.data


def test_seed_guides_is_idempotent_and_never_creates_accounts(app, client):
    with app.app_context():
        assert seed_roadmaps() == 10
        assert seed_roadmaps() == 0
        assert CropRoadmap.query.count() == 10
        assert User.query.count() == 0
    assert client.get('/roadmap/').status_code == 200
    response = client.get('/roadmap/tomato')
    assert response.status_code == 200
    assert b'general educational crop guides' in response.data


def test_malformed_roadmap_stages_are_safe(app, client):
    payloads = ['invalid', '{}', 'null', '[null, 1, "text"]',
                '[{"stage":"Check soil","actions":null,"tips":5}]',
                '[{"stage":"Check soil","actions":["Safe",null,{}],"tips":"bad"}]']
    with app.app_context():
        for index, payload in enumerate(payloads):
            db.session.add(CropRoadmap(crop_name='Test', slug=f'test-{index}', stages_json=payload))
        db.session.commit()
    for index in range(len(payloads)):
        assert client.get(f'/roadmap/test-{index}').status_code == 200

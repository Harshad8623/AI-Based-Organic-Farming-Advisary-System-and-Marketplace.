import re

from models import db, User


def registration(**changes):
    values = dict(name='Test Farmer', email='farmer@example.com', password='Strong123!',
                  confirm_password='Strong123!', role='farmer', location='Sambhajinagar')
    values.update(changes)
    return values


def test_register_login_logout_and_duplicate_email(app, client):
    response = client.post('/auth/register', data=registration())
    assert response.status_code == 302
    with app.app_context():
        user = User.query.one()
        assert user.password != 'Strong123!'
        assert user.farmer_profile.farm_location == 'Sambhajinagar'
    client.post('/auth/register', data=registration(email='FARMER@example.com'))
    with app.app_context():
        assert User.query.count() == 1
    response = client.post('/auth/login', data={'email':'FARMER@example.com', 'password':'Strong123!'}, follow_redirects=True)
    assert response.status_code == 200
    assert client.get('/auth/logout').status_code == 405
    assert client.post('/auth/logout').status_code == 302
    assert client.get('/farm-tools').status_code == 302


def test_registration_rejects_invalid_role_and_overlong_fields(app, client):
    for values in [registration(role='admin'), registration(name='A'*101),
                   registration(email='x'*121+'@test.com'), registration(phone='not a phone'),
                   registration(password='short', confirm_password='short')]:
        client.post('/auth/register', data=values)
    with app.app_context():
        assert User.query.count() == 0


def test_login_redirect_rejects_external_targets(client):
    client.post('/auth/register', data=registration())
    for target in ['https://evil.example', '//evil.example', '/\\evil.example', '/\nevil.example']:
        response = client.post('/auth/login', data={'email':'farmer@example.com','password':'Strong123!','next':target})
        assert response.location.endswith('/auth/farmer/dashboard')
        client.post('/auth/logout')
    response = client.post('/auth/login', data={'email':'farmer@example.com','password':'Strong123!','next':'/farm-tools'})
    assert response.location == '/farm-tools'


def test_csrf_protects_registration_and_json(app, client):
    app.config['CSRF_ENABLED'] = True
    assert client.post('/auth/register', data=registration()).status_code == 400
    assert client.post('/chatbot/ask', json={'message':'hello'}).status_code == 400
    assert client.post('/auth/register', data=registration(csrf_token='मराठी')).status_code == 400
    page = client.get('/auth/register')
    token = re.search(rb'name="csrf_token" value="([^"]+)"', page.data).group(1).decode()
    assert client.post('/auth/register', data=registration(csrf_token=token)).status_code == 302
    with app.app_context():
        assert User.query.count() == 1


def test_no_demo_accounts_and_safe_error_pages(app, client):
    with app.app_context():
        assert User.query.count() == 0
    page = client.get('/missing-page')
    assert page.status_code == 404
    assert b'could not be found' in page.data
    assert page.headers['X-Content-Type-Options'] == 'nosniff'


def test_invalid_session_user_does_not_crash(client):
    with client.session_transaction() as session:
        session['_user_id'] = 'invalid'
    assert client.get('/auth/farmer/dashboard').status_code == 302


def test_auth_errors_have_offline_translation_keys(client):
    response = client.post('/auth/login', data={'email':'missing@example.com', 'password':'incorrect'})
    assert b'data-i18n="auth_invalid_login"' in response.data
    assert b'js/auth-i18n.js' in response.data


def test_every_template_compiles(app):
    for name in app.jinja_env.list_templates():
        app.jinja_env.get_template(name)

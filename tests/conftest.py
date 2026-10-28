import pytest
from app import create_app
from models import db


@pytest.fixture
def app(tmp_path):
    application = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-only-session-key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(tmp_path / 'test.db'),
        'UPLOAD_FOLDER': str(tmp_path / 'uploads'),
        'CSRF_ENABLED': False,
        'SEED_ROADMAPS': False,
        'GEMINI_API_KEY': '', 'OPENWEATHER_API_KEY': '',
        'RAZORPAY_KEY_ID': '', 'RAZORPAY_KEY_SECRET': '',
    })
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()

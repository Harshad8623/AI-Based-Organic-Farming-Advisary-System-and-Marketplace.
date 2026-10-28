"""Regression coverage for Render's PostgreSQL driver startup failure."""
import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

from config import normalize_database_url


@pytest.mark.parametrize('scheme', ['postgres', 'postgresql'])
def test_render_urls_select_installed_driver_without_altering_connection_details(scheme):
    remainder = 'farmer:p%40ss%3Aword@database.internal:5432/farm?sslmode=require&application_name=krishi'
    uri = normalize_database_url(scheme + '://' + remainder)
    assert uri == 'postgresql+psycopg2://' + remainder
    engine = create_engine(uri)
    assert engine.dialect.driver == 'psycopg2'
    assert engine.dialect.dbapi.__name__ == 'psycopg2'
    assert engine.url.username == 'farmer'
    assert engine.url.database == 'farm'
    assert engine.url.query['sslmode'] == 'require'
    engine.dispose()


@pytest.mark.parametrize('uri', [
    '', 'sqlite:///:memory:', 'sqlite:////tmp/farm.db',
    'postgresql+psycopg2://example@localhost/farm',
    'postgresql+psycopg://example@localhost/farm',
    'postgresql+asyncpg://example@localhost/farm',
])
def test_explicit_drivers_and_other_database_urls_remain_unchanged(uri):
    assert normalize_database_url(uri) == uri


@pytest.mark.parametrize('scheme', ['postgres', 'postgresql'])
def test_flask_sqlalchemy_can_initialize_render_engine_with_declared_dependencies(scheme):
    application = Flask(__name__)
    application.config['SQLALCHEMY_DATABASE_URI'] = normalize_database_url(
        scheme + '://example@localhost/farm?sslmode=require')
    database = SQLAlchemy()
    # This is the exact initialization stage that failed on Render. Engine
    # creation loads the real installed DBAPI without opening a connection.
    database.init_app(application)
    with application.app_context():
        assert database.engine.dialect.driver == 'psycopg2'
        assert database.engine.dialect.dbapi.__name__ == 'psycopg2'
        database.engine.dispose()

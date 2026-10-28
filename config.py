import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def normalize_database_url(database_url):
    """Bind driverless PostgreSQL URLs to the driver shipped by this project.

    SQLAlchemy 2.1 defaults to psycopg 3, while requirements.txt supplies
    psycopg2-binary. Preserve credentials, query options and explicit drivers.
    """
    scheme, separator, remainder = database_url.partition('://')
    if separator and scheme in ('postgres', 'postgresql'):
        return 'postgresql+psycopg2://' + remainder
    return database_url


class Config:
    CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('APP_ENV') == 'production'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = os.environ.get('APP_ENV') == 'production'
    SEED_ROADMAPS = True
    # -------------------------------------------------------
    # Security
    # -------------------------------------------------------
    # ⚠️  ALWAYS set SECRET_KEY in the environment — never rely on this fallback in production.
    # Generate a strong key: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.environ.get('SECRET_KEY') or (
        'krishi-ai-dev-only-' + os.urandom(16).hex()
    )

    # -------------------------------------------------------
    # Database — PostgreSQL on Render, SQLite locally
    # -------------------------------------------------------
    # On Render: set DATABASE_URL to your PostgreSQL connection string.
    # Render provides this automatically when you link a PostgreSQL service.
    # Locally: falls back to SQLite (no setup needed for development).
    #
    # Render supplies a driverless postgres:// or postgresql:// URL. Select the
    # installed psycopg2 driver explicitly, independent of SQLAlchemy defaults.
    _db_url = normalize_database_url(os.environ.get('DATABASE_URL', ''))

    SQLALCHEMY_DATABASE_URI = _db_url or (
        'sqlite:///' + os.path.join(BASE_DIR, 'database', 'farming.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------------------------------------
    # File Uploads
    # -------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024          # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}   # gif removed (confuses vision AI)

    # -------------------------------------------------------
    # API Keys  <-- set these in Render Environment Variables
    # -------------------------------------------------------
    GEMINI_API_KEY      = os.environ.get('GEMINI_API_KEY', '')        # https://aistudio.google.com
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')   # https://openweathermap.org/api

    # -------------------------------------------------------
    # Razorpay Payment Gateway (Test Mode)
    # -------------------------------------------------------
    RAZORPAY_KEY_ID     = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

    # -------------------------------------------------------
    # ML model paths
    # -------------------------------------------------------
    CROP_MODEL_PATH   = os.path.join(BASE_DIR, 'ml_models', 'crop_model.pkl')
    CROP_ENCODER_PATH = os.path.join(BASE_DIR, 'ml_models', 'crop_label_encoder.pkl')

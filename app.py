"""
app.py
------
Flask application factory — entry point for the Organic Farming Platform.
Run with:  python app.py
"""

import os
import hmac
import secrets
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, jsonify
from models import db, User, CartItem
from flask_login import LoginManager, current_user

# Load .env file before anything reads os.environ
load_dotenv()
from config import Config
from localization import MESSAGE_KEYS


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if os.environ.get('APP_ENV') == 'production' and not os.environ.get('SECRET_KEY') and not app.testing:
        raise RuntimeError('Set a stable SECRET_KEY in the production environment.')

    def csrf_token():
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_urlsafe(32)
        return session['_csrf_token']

    app.jinja_env.globals['csrf_token'] = csrf_token
    app.jinja_env.globals['message_key'] = MESSAGE_KEYS.get

    @app.before_request
    def protect_writes():
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE') or not app.config.get('CSRF_ENABLED', True):
            return None
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
        expected = session.get('_csrf_token', '')
        if not isinstance(expected, str) or not isinstance(token, str) or not expected or not token or not hmac.compare_digest(expected.encode('utf-8'), token.encode('utf-8')):
            message = 'Your session expired. Reload this page and try again.'
            if request.is_json:
                return jsonify(error=message), 400
            return render_template('error.html', code=400, message=message), 400

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        if current_user.is_authenticated or request.endpoint in ('auth.login', 'auth.register'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    def handle_http_error(error):
        messages = {400: 'Please check your input and try again.', 403: 'You do not have access to this action.',
                    404: 'This page or record could not be found.', 413: 'This file is too large. Choose a file smaller than 16 MB.'}
        message = messages.get(error.code, 'Something went wrong. Please try again.')
        if request.is_json:
            return jsonify(error=message), error.code
        return render_template('error.html', code=error.code, message=message), error.code

    for code in (400, 403, 404, 413):
        app.register_error_handler(code, handle_http_error)

    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'database'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'ml_models'), exist_ok=True)

    # -----------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------
    db.init_app(app)

    # -----------------------------------------------------------------------
    # Flask-Login
    # -----------------------------------------------------------------------
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # -----------------------------------------------------------------------
    # Template Globals (cart count injected to all templates)
    # -----------------------------------------------------------------------
    @app.context_processor
    def inject_cart_count():
        count = 0
        try:
            if current_user.is_authenticated and current_user.is_buyer():
                count = CartItem.query.filter_by(buyer_id=current_user.id).count()
        except Exception:
            pass
        return {'cart_count': count}

    # -----------------------------------------------------------------------
    # Register Blueprints
    # -----------------------------------------------------------------------
    from routes.auth               import auth_bp
    from routes.marketplace        import marketplace_bp
    from routes.crop_recommendation import crop_bp
    from routes.disease_detection  import disease_bp
    from routes.chatbot            import chatbot_bp
    from routes.weather            import weather_bp
    from routes.analytics          import analytics_bp
    from routes.roadmap            import roadmap_bp
    from routes.cart               import cart_bp
    from routes.orders             import orders_bp
    from routes.translate          import translate_bp
    from routes.farm_tools         import farm_tools_bp
    from routes.farm_advisory      import farm_advisory_bp
    from routes.farm_decisions     import farm_decisions_bp
    import farm_tools_models  # Register additive planner tables before create_all.
    import advisory_models  # Field contexts, observations, outcomes and action links.

    app.register_blueprint(auth_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(crop_bp)
    app.register_blueprint(disease_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(roadmap_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(translate_bp)
    app.register_blueprint(farm_tools_bp)
    app.register_blueprint(farm_advisory_bp)
    app.register_blueprint(farm_decisions_bp)

    # -----------------------------------------------------------------------
    # Home Route
    # -----------------------------------------------------------------------
    @app.route('/')
    def index():
        return render_template('index.html')

    # -----------------------------------------------------------------------
    # Create DB tables and auto-seed if empty on first run
    # -----------------------------------------------------------------------
    with app.app_context():
        db.create_all()
        if app.config.get('SEED_ROADMAPS', True):
            from database.seed import seed_roadmaps
            seed_roadmaps()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1', port=5000)

"""Spendly Flask Application Factory"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

def create_app(config_name=None):
    """Create and configure Flask application."""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from config import config
    app.config.from_object(config.get(config_name, config['default']))
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .routes import bp as main_bp
    from .auth import bp as auth_bp
    from .ai import bp as ai_bp
    from .expenses import bp as expenses_bp
    from .members import bp as members_bp
    from .analytics_routes import bp as analytics_bp
    from .settlements_routes import bp as settlements_bp
    from .settings_routes import bp as settings_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(settlements_bp)
    app.register_blueprint(settings_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('500.html'), 500
    
    # Jinja filters
    from .utils import format_currency
    @app.template_filter('currency')
    def currency_filter(amount):
        return format_currency(amount)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

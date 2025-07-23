"""
Flask API package for the multi-user trading platform.
"""

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from database import db
from .config import get_config


def create_app(config_name='development'):
    """
    Create and configure the Flask application.
    
    Args:
        config_name: Configuration environment name
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    JWTManager(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def register_blueprints(app):
    """Register all API blueprints."""
    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')


def register_error_handlers(app):
    """Register global error handlers."""
    from .utils import handle_error
    
    @app.errorhandler(400)
    def bad_request(error):
        return handle_error('Bad Request', 'Invalid request data', 400)
    
    @app.errorhandler(401)
    def unauthorized(error):
        return handle_error('Unauthorized', 'Authentication required', 401)
    
    @app.errorhandler(403)
    def forbidden(error):
        return handle_error('Forbidden', 'Insufficient permissions', 403)
    
    @app.errorhandler(404)
    def not_found(error):
        return handle_error('Not Found', 'Resource not found', 404)
    
    @app.errorhandler(500)
    def internal_error(error):
        return handle_error('Internal Server Error', 'An unexpected error occurred', 500) 
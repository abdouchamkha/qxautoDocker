"""
API routes package for the multi-user trading platform.
"""

from flask import Blueprint, jsonify
from datetime import datetime, timezone

# Create main API blueprint
api_bp = Blueprint('api', __name__)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'message': 'Multi-User Trading Platform API is running',
        'version': '1.0.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': 'healthy'
    })


@api_bp.route('/', methods=['GET'])
def api_info():
    """API information endpoint."""
    return jsonify({
        'success': True,
        'message': 'Multi-User Trading Platform API v1',
        'version': '1.0.0',
        'documentation': '/api/v1/docs',
        'endpoints': {
            'authentication': '/api/v1/auth/*',
            'users': '/api/v1/users/*',
            'accounts': '/api/v1/accounts/*',
            'sessions': '/api/v1/sessions/*',
            'trades': '/api/v1/trades/*',
            'subscriptions': '/api/v1/subscriptions/*'
        },
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


# Import route modules
from .auth import auth_bp
from .users import users_bp
from .subscriptions import subscriptions_bp

# Register sub-blueprints
api_bp.register_blueprint(auth_bp, url_prefix='/auth')
api_bp.register_blueprint(users_bp, url_prefix='/users')
api_bp.register_blueprint(subscriptions_bp, url_prefix='/subscriptions')

# Placeholder for future route modules (Phase 3+)
# from .accounts import accounts_bp
# from .sessions import sessions_bp
# from .trades import trades_bp

# Register future sub-blueprints when modules are created
# api_bp.register_blueprint(accounts_bp, url_prefix='/accounts')
# api_bp.register_blueprint(sessions_bp, url_prefix='/sessions')
# api_bp.register_blueprint(trades_bp, url_prefix='/trades') 
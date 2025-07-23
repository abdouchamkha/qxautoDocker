"""
Common decorators for the multi-user trading platform API.
"""

from functools import wraps
from flask import request, jsonify
from .auth import require_auth, require_active_subscription, validate_api_request


def auth_required(f):
    """
    Shorthand decorator for requiring authentication.
    """
    return require_auth(f)


def subscription_required(f):
    """
    Shorthand decorator for requiring active subscription.
    """
    @auth_required
    @require_active_subscription
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def json_required(required_fields=None, optional_fields=None):
    """
    Decorator that combines authentication and JSON validation.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
    """
    def decorator(f):
        @auth_required
        @validate_api_request(required_fields, optional_fields)
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def subscription_json_required(required_fields=None, optional_fields=None):
    """
    Decorator that combines subscription requirement and JSON validation.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
    """
    def decorator(f):
        @subscription_required
        @validate_api_request(required_fields, optional_fields)
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator 
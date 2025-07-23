"""
Authentication middleware and utilities for the multi-user trading platform.
"""

from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, create_access_token, create_refresh_token
from database.models import User, Subscription
from datetime import datetime, timezone
import re


def validate_password_strength(password):
    """
    Validate password strength requirements.
    
    Args:
        password: Password string to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Password must contain at least one special character"
    
    return True, None


def validate_email(email):
    """
    Validate email format.
    
    Args:
        email: Email string to validate
        
    Returns:
        bool: True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def authenticate_user(email, password):
    """
    Authenticate user with email and password.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        tuple: (user_object, error_message)
    """
    if not email or not password:
        return None, "Email and password are required"
    
    user = User.query.filter_by(email=email.lower().strip()).first()
    
    if not user:
        return None, "Invalid email or password"
    
    if not user.is_active:
        return None, "Account is disabled"
    
    if not user.check_password(password):
        return None, "Invalid email or password"
    
    return user, None


def create_user_tokens(user):
    """
    Create access and refresh tokens for user.
    
    Args:
        user: User object
        
    Returns:
        dict: Dictionary containing access and refresh tokens
    """
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer'
    }


def get_current_user():
    """
    Get the current authenticated user from JWT token.
    
    Returns:
        User object or None
    """
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        return User.query.get(user_id)
    except Exception:
        return None


def require_auth(f):
    """
    Decorator to require authentication for API endpoints.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user or not user.is_active:
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'message': 'Invalid or expired token'
                }), 401
            
            # Add user to request context
            request.current_user = user
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Authentication failed',
                'message': str(e)
            }), 401
    
    return decorated_function


def require_active_subscription(f):
    """
    Decorator to require active subscription for API endpoints.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(request, 'current_user', None)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please log in first'
            }), 401
        
        subscription = user.active_subscription
        
        if not subscription:
            return jsonify({
                'success': False,
                'error': 'Subscription required',
                'message': 'An active subscription is required to access this feature'
            }), 403
        
        if subscription.is_expired:
            return jsonify({
                'success': False,
                'error': 'Subscription expired',
                'message': 'Your subscription has expired. Please renew to continue.'
            }), 403
        
        # Add subscription to request context
        request.current_subscription = subscription
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_subscription_type(subscription_types):
    """
    Decorator to require specific subscription type(s).
    
    Args:
        subscription_types: String or list of subscription types
        
    Returns:
        Decorator function
    """
    if isinstance(subscription_types, str):
        subscription_types = [subscription_types]
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            subscription = getattr(request, 'current_subscription', None)
            
            if not subscription:
                return jsonify({
                    'success': False,
                    'error': 'Subscription required',
                    'message': 'This feature requires an active subscription'
                }), 403
            
            if subscription.subscription_type not in subscription_types:
                return jsonify({
                    'success': False,
                    'error': 'Subscription upgrade required',
                    'message': f'This feature requires a {" or ".join(subscription_types)} subscription'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def check_resource_limits(resource_type, current_count=None):
    """
    Check if user has reached resource limits based on subscription.
    
    Args:
        resource_type: Type of resource ('accounts', 'sessions')
        current_count: Current count of resources (if None, will be calculated)
        
    Returns:
        tuple: (can_create, error_message)
    """
    user = getattr(request, 'current_user', None)
    subscription = getattr(request, 'current_subscription', None)
    
    if not user or not subscription:
        return False, "Authentication and subscription required"
    
    if resource_type == 'accounts':
        if current_count is None:
            current_count = len(user.quotex_accounts)
        limit = subscription.max_accounts
        resource_name = "trading accounts"
    elif resource_type == 'sessions':
        if current_count is None:
            current_count = len([s for s in user.trading_sessions if s.is_active])
        limit = subscription.max_sessions
        resource_name = "active trading sessions"
    else:
        return False, "Unknown resource type"
    
    if current_count >= limit:
        return False, f"You have reached the maximum number of {resource_name} ({limit}) for your {subscription.subscription_type} subscription"
    
    return True, None


def validate_api_request(required_fields=None, optional_fields=None):
    """
    Decorator to validate API request data.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid request',
                    'message': 'Request body must contain valid JSON'
                }), 400
            
            # Check required fields
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data or data[field] is None or data[field] == '':
                        missing_fields.append(field)
                
                if missing_fields:
                    return jsonify({
                        'success': False,
                        'error': 'Missing required fields',
                        'message': f'Required fields: {", ".join(missing_fields)}'
                    }), 400
            
            # Add validated data to request context
            request.validated_data = data
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def rate_limit_by_user(requests_per_minute=60):
    """
    Decorator to implement rate limiting per user.
    
    Args:
        requests_per_minute: Maximum requests per minute per user
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple in-memory rate limiting (should use Redis in production)
            user = getattr(request, 'current_user', None)
            
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401
            
            # For now, just proceed without rate limiting
            # In production, implement proper rate limiting with Redis
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator 
"""
Authentication routes for the multi-user trading platform.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from database.models import db, User, Subscription
from api.auth import authenticate_user, validate_password_strength, validate_email, create_user_tokens
from api.utils import success_response, error_response, handle_exception
from datetime import datetime, timedelta, timezone

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Request body:
    {
        "username": "string",
        "email": "string", 
        "password": "string"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('Invalid Request', 'Request body must contain valid JSON', 400)
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return error_response(
                'Missing Fields', 
                f'Required fields: {", ".join(missing_fields)}', 
                400
            )
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate input
        if len(username) < 3 or len(username) > 50:
            return error_response('Invalid Username', 'Username must be between 3 and 50 characters', 400)
        
        if not validate_email(email):
            return error_response('Invalid Email', 'Please provide a valid email address', 400)
        
        is_valid_password, password_error = validate_password_strength(password)
        if not is_valid_password:
            return error_response('Weak Password', password_error, 400)
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return error_response('Username Taken', 'Username already exists', 409)
            else:
                return error_response('Email Taken', 'Email already registered', 409)
        
        # Create new user
        user = User(
            username=username,
            email=email,
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create basic subscription for new user (30 days free trial)
        subscription = Subscription(
            user_id=user.id,
            subscription_type='basic',
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True,
            max_accounts=2,
            max_sessions=1
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        # Create tokens
        tokens = create_user_tokens(user)
        
        response_data = {
            'user': user.to_dict(),
            'subscription': subscription.to_dict(),
            'tokens': tokens
        }
        
        return success_response(
            response_data,
            'User registered successfully',
            201
        )
        
    except Exception as e:
        db.session.rollback()
        return handle_exception(e, 'Registration failed')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return tokens.
    
    Request body:
    {
        "email": "string",
        "password": "string"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('Invalid Request', 'Request body must contain valid JSON', 400)
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return error_response('Missing Credentials', 'Email and password are required', 400)
        
        # Authenticate user
        user, auth_error = authenticate_user(email, password)
        
        if not user:
            return error_response('Authentication Failed', auth_error, 401)
        
        # Update last login time
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Create tokens
        tokens = create_user_tokens(user)
        
        # Get active subscription
        subscription = user.active_subscription
        
        response_data = {
            'user': user.to_dict(include_sensitive=True),
            'subscription': subscription.to_dict() if subscription else None,
            'tokens': tokens
        }
        
        return success_response(response_data, 'Login successful')
        
    except Exception as e:
        return handle_exception(e, 'Login failed')


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user (token will be handled by client-side removal).
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        # In a production environment, you might want to blacklist the token
        # For now, we'll just return a success response
        # The client should remove the token from storage
        
        return success_response(None, 'Logout successful')
        
    except Exception as e:
        return handle_exception(e, 'Logout failed')


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return error_response('Invalid User', 'User not found or inactive', 401)
        
        # Create new access token
        access_token = create_access_token(identity=user.id)
        
        response_data = {
            'access_token': access_token,
            'token_type': 'Bearer'
        }
        
        return success_response(response_data, 'Token refreshed successfully')
        
    except Exception as e:
        return handle_exception(e, 'Token refresh failed')


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Verify if the current token is valid and return user info.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return error_response('Invalid Token', 'Token is invalid or user is inactive', 401)
        
        # Get active subscription
        subscription = user.active_subscription
        
        response_data = {
            'user': user.to_dict(),
            'subscription': subscription.to_dict() if subscription else None,
            'token_valid': True
        }
        
        return success_response(response_data, 'Token is valid')
        
    except Exception as e:
        return handle_exception(e, 'Token verification failed')


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password.
    
    Request body:
    {
        "current_password": "string",
        "new_password": "string"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('Invalid Request', 'Request body must contain valid JSON', 400)
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return error_response('Missing Fields', 'Current password and new password are required', 400)
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        # Verify current password
        if not user.check_password(current_password):
            return error_response('Invalid Password', 'Current password is incorrect', 401)
        
        # Validate new password strength
        is_valid_password, password_error = validate_password_strength(new_password)
        if not is_valid_password:
            return error_response('Weak Password', password_error, 400)
        
        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return success_response(None, 'Password changed successfully')
        
    except Exception as e:
        db.session.rollback()
        return handle_exception(e, 'Password change failed') 
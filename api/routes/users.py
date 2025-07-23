"""
User management routes for the multi-user trading platform.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.models import db, User, QuotexAccount, TradingSession
from api.auth import validate_email
from api.utils import success_response, error_response, handle_exception, paginate_query
from api.decorators import auth_required
from datetime import datetime, timezone

users_bp = Blueprint('users', __name__)


@users_bp.route('/profile', methods=['GET'])
@auth_required
def get_profile():
    """
    Get user profile information including subscription and statistics.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        # Get active subscription
        subscription = user.active_subscription
        
        # Get account statistics
        total_accounts = len(user.quotex_accounts)
        active_sessions = len([s for s in user.trading_sessions if s.is_active])
        total_sessions = len(user.trading_sessions)
        
        # Calculate total trades and profit
        total_trades = sum(session.total_trades for session in user.trading_sessions)
        total_profit = sum(session.net_profit for session in user.trading_sessions)
        
        response_data = {
            'user': user.to_dict(),
            'subscription': subscription.to_dict() if subscription else None,
            'statistics': {
                'total_accounts': total_accounts,
                'active_sessions': active_sessions,
                'total_sessions': total_sessions,
                'total_trades': total_trades,
                'total_profit': total_profit
            }
        }
        
        return success_response(response_data, 'Profile retrieved successfully')
        
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve profile')


@users_bp.route('/profile', methods=['PUT'])
@auth_required
def update_profile():
    """
    Update user profile information.
    
    Request body:
    {
        "username": "string" (optional),
        "email": "string" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('Invalid Request', 'Request body must contain valid JSON', 400)
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        updated_fields = []
        
        # Update username if provided
        if 'username' in data:
            username = data['username'].strip()
            
            if len(username) < 3 or len(username) > 50:
                return error_response('Invalid Username', 'Username must be between 3 and 50 characters', 400)
            
            # Check if username is already taken by another user
            existing_user = User.query.filter(
                (User.username == username) & (User.id != user.id)
            ).first()
            
            if existing_user:
                return error_response('Username Taken', 'Username already exists', 409)
            
            user.username = username
            updated_fields.append('username')
        
        # Update email if provided
        if 'email' in data:
            email = data['email'].strip().lower()
            
            if not validate_email(email):
                return error_response('Invalid Email', 'Please provide a valid email address', 400)
            
            # Check if email is already taken by another user
            existing_user = User.query.filter(
                (User.email == email) & (User.id != user.id)
            ).first()
            
            if existing_user:
                return error_response('Email Taken', 'Email already registered', 409)
            
            user.email = email
            updated_fields.append('email')
        
        if updated_fields:
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            return success_response(
                {'user': user.to_dict(), 'updated_fields': updated_fields},
                'Profile updated successfully'
            )
        else:
            return success_response(
                {'user': user.to_dict()},
                'No changes made to profile'
            )
        
    except Exception as e:
        db.session.rollback()
        return handle_exception(e, 'Failed to update profile')


@users_bp.route('/account', methods=['DELETE'])
@auth_required
def delete_account():
    """
    Delete user account and all associated data.
    
    Request body:
    {
        "password": "string",
        "confirmation": "DELETE_MY_ACCOUNT"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('Invalid Request', 'Request body must contain valid JSON', 400)
        
        password = data.get('password', '')
        confirmation = data.get('confirmation', '')
        
        if not password:
            return error_response('Missing Password', 'Password is required for account deletion', 400)
        
        if confirmation != 'DELETE_MY_ACCOUNT':
            return error_response(
                'Invalid Confirmation',
                'Please type "DELETE_MY_ACCOUNT" to confirm account deletion',
                400
            )
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        # Verify password
        if not user.check_password(password):
            return error_response('Invalid Password', 'Password is incorrect', 401)
        
        # Delete user (cascades will handle related data)
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        return success_response(
            None,
            f'Account for user "{username}" has been permanently deleted'
        )
        
    except Exception as e:
        db.session.rollback()
        return handle_exception(e, 'Failed to delete account')


@users_bp.route('/statistics', methods=['GET'])
@auth_required
def get_user_statistics():
    """
    Get detailed user trading statistics.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        # Calculate detailed statistics
        total_accounts = len(user.quotex_accounts)
        demo_accounts = len([acc for acc in user.quotex_accounts if acc.account_type == 'demo'])
        real_accounts = len([acc for acc in user.quotex_accounts if acc.account_type == 'real'])
        
        active_sessions = [s for s in user.trading_sessions if s.is_active]
        inactive_sessions = [s for s in user.trading_sessions if not s.is_active]
        
        # Trading statistics
        total_trades = sum(session.total_trades for session in user.trading_sessions)
        total_winning_trades = sum(session.winning_trades for session in user.trading_sessions)
        total_losing_trades = sum(session.losing_trades for session in user.trading_sessions)
        
        overall_win_rate = (total_winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_profit = sum(session.net_profit for session in user.trading_sessions)
        
        # Session statistics
        session_stats = []
        for session in user.trading_sessions:
            session_stats.append({
                'session_id': session.id,
                'session_name': session.session_name,
                'account_type': session.account.account_type if session.account else 'unknown',
                'is_active': session.is_active,
                'total_trades': session.total_trades,
                'win_rate': session.win_rate,
                'net_profit': session.net_profit,
                'created_at': session.created_at.isoformat() if session.created_at else None
            })
        
        response_data = {
            'account_summary': {
                'total_accounts': total_accounts,
                'demo_accounts': demo_accounts,
                'real_accounts': real_accounts
            },
            'session_summary': {
                'active_sessions': len(active_sessions),
                'inactive_sessions': len(inactive_sessions),
                'total_sessions': len(user.trading_sessions)
            },
            'trading_summary': {
                'total_trades': total_trades,
                'winning_trades': total_winning_trades,
                'losing_trades': total_losing_trades,
                'overall_win_rate': round(overall_win_rate, 2),
                'total_profit': round(total_profit, 2)
            },
            'session_details': session_stats
        }
        
        return success_response(response_data, 'Statistics retrieved successfully')
        
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve statistics')


@users_bp.route('/activity', methods=['GET'])
@auth_required
def get_user_activity():
    """
    Get user activity log (recent sessions, trades, etc.).
    Supports pagination.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        # Get recent trading sessions
        recent_sessions_query = TradingSession.query.filter_by(
            user_id=user_id
        ).order_by(TradingSession.updated_at.desc())
        
        sessions_result = paginate_query(recent_sessions_query, per_page=10)
        
        # Get recent account activities
        recent_accounts = QuotexAccount.query.filter_by(
            user_id=user_id
        ).order_by(QuotexAccount.updated_at.desc()).limit(5).all()
        
        response_data = {
            'recent_sessions': sessions_result,
            'recent_accounts': [acc.to_dict() for acc in recent_accounts],
            'user_info': {
                'username': user.username,
                'email': user.email,
                'member_since': user.created_at.isoformat() if user.created_at else None,
                'last_updated': user.updated_at.isoformat() if user.updated_at else None
            }
        }
        
        return success_response(response_data, 'Activity log retrieved successfully')
        
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve activity log')


@users_bp.route('/settings', methods=['GET'])
@auth_required
def get_user_settings():
    """
    Get user application settings and preferences.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        subscription = user.active_subscription
        
        response_data = {
            'user_preferences': {
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active
            },
            'subscription_settings': {
                'type': subscription.subscription_type if subscription else None,
                'max_accounts': subscription.max_accounts if subscription else 0,
                'max_sessions': subscription.max_sessions if subscription else 0,
                'expires_at': subscription.end_date.isoformat() if subscription else None,
                'days_remaining': subscription.days_remaining if subscription else 0
            },
            'limits': {
                'current_accounts': len(user.quotex_accounts),
                'current_active_sessions': len([s for s in user.trading_sessions if s.is_active])
            }
        }
        
        return success_response(response_data, 'Settings retrieved successfully')
        
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve settings') 
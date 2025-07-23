"""
Subscription management routes for the multi-user trading platform.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.models import db, User, Subscription
from api.utils import success_response, error_response, handle_exception, paginate_query
from api.decorators import auth_required
from datetime import datetime, timedelta, timezone

subscriptions_bp = Blueprint('subscriptions', __name__)

# Subscription tier definitions
SUBSCRIPTION_TIERS = {
    'basic': {
        'name': 'Basic',
        'max_accounts': 2,
        'max_sessions': 1,
        'price_monthly': 0,
        'features': [
            'Up to 2 trading accounts',
            '1 active session',
            'Basic telegram signals',
            'Standard support'
        ]
    },
    'premium': {
        'name': 'Premium',
        'max_accounts': 5,
        'max_sessions': 3,
        'price_monthly': 29,
        'features': [
            'Up to 5 trading accounts',
            '3 active sessions',
            'Premium telegram signals',
            'Advanced analytics',
            'Priority support',
            'Custom trading strategies'
        ]
    },
    'vip': {
        'name': 'VIP',
        'max_accounts': 10,
        'max_sessions': 5,
        'price_monthly': 99,
        'features': [
            'Up to 10 trading accounts',
            '5 active sessions',
            'VIP telegram signals',
            'Advanced analytics',
            'Real-time monitoring',
            '24/7 priority support',
            'Custom trading strategies',
            'One-on-one consultation'
        ]
    }
}


@subscriptions_bp.route('/', methods=['GET'])
@auth_required
def get_user_subscriptions():
    """
    Get user's subscription history and current subscription.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        # Get all user subscriptions (with pagination)
        subscriptions_query = Subscription.query.filter_by(
            user_id=user_id
        ).order_by(Subscription.created_at.desc())
        
        subscriptions_result = paginate_query(subscriptions_query)
        
        # Get current active subscription
        active_subscription = user.active_subscription
        
        response_data = {
            'current_subscription': active_subscription.to_dict() if active_subscription else None,
            'subscription_history': subscriptions_result,
            'available_tiers': SUBSCRIPTION_TIERS
        }
        
        return success_response(response_data, 'Subscriptions retrieved successfully')
        
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve subscriptions')


@subscriptions_bp.route('/tiers', methods=['GET'])
def get_subscription_tiers():
    """
    Get available subscription tiers and their features.
    """
    try:
        return success_response(
            {'tiers': SUBSCRIPTION_TIERS},
            'Subscription tiers retrieved successfully'
        )
        
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve subscription tiers')


@subscriptions_bp.route('/', methods=['POST'])
@auth_required
def create_subscription():
    """
    Create a new subscription for the user.
    
    Request body:
    {
        "subscription_type": "basic|premium|vip",
        "duration_months": 1,
        "payment_method": "string" (optional),
        "payment_reference": "string" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('Invalid Request', 'Request body must contain valid JSON', 400)
        
        subscription_type = data.get('subscription_type', '').lower()
        duration_months = data.get('duration_months', 1)
        
        # Validate subscription type
        if subscription_type not in SUBSCRIPTION_TIERS:
            return error_response(
                'Invalid Subscription Type',
                f'Subscription type must be one of: {", ".join(SUBSCRIPTION_TIERS.keys())}',
                400
            )
        
        # Validate duration
        try:
            duration_months = int(duration_months)
            if duration_months < 1 or duration_months > 12:
                return error_response('Invalid Duration', 'Duration must be between 1 and 12 months', 400)
        except (ValueError, TypeError):
            return error_response('Invalid Duration', 'Duration must be a valid number', 400)
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        # Check if user has an active subscription
        current_subscription = user.active_subscription
        if current_subscription and not current_subscription.is_expired:
            return error_response(
                'Active Subscription Exists',
                'You already have an active subscription. Please wait for it to expire or contact support for upgrades.',
                409
            )
        
        # Get tier information
        tier_info = SUBSCRIPTION_TIERS[subscription_type]
        
        # Calculate subscription dates
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=duration_months * 30)  # Approximate month duration
        
        # Create new subscription
        subscription = Subscription(
            user_id=user.id,
            subscription_type=subscription_type,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            max_accounts=tier_info['max_accounts'],
            max_sessions=tier_info['max_sessions']
        )
        
        # Deactivate any existing subscriptions
        if current_subscription:
            current_subscription.is_active = False
        
        db.session.add(subscription)
        db.session.commit()
        
        response_data = {
            'subscription': subscription.to_dict(),
            'tier_info': tier_info,
            'duration_months': duration_months,
            'total_price': tier_info['price_monthly'] * duration_months
        }
        
        return success_response(
            response_data,
            f'{tier_info["name"]} subscription created successfully',
            201
        )
        
    except Exception as e:
        db.session.rollback()
        return handle_exception(e, 'Failed to create subscription')


@subscriptions_bp.route('/<int:subscription_id>', methods=['GET'])
@auth_required
def get_subscription_details(subscription_id):
    """
    Get details of a specific subscription.
    """
    try:
        user_id = get_jwt_identity()
        
        subscription = Subscription.query.filter_by(
            id=subscription_id,
            user_id=user_id
        ).first()
        
        if not subscription:
            return error_response('Subscription Not Found', 'Invalid subscription ID', 404)
        
        tier_info = SUBSCRIPTION_TIERS.get(subscription.subscription_type, {})
        
        response_data = {
            'subscription': subscription.to_dict(),
            'tier_info': tier_info
        }
        
        return success_response(response_data, 'Subscription details retrieved successfully')
        
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve subscription details')


@subscriptions_bp.route('/<int:subscription_id>', methods=['PUT'])
@auth_required
def update_subscription(subscription_id):
    """
    Update subscription (mainly for administrative purposes).
    
    Request body:
    {
        "end_date": "ISO datetime string" (optional),
        "is_active": boolean (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('Invalid Request', 'Request body must contain valid JSON', 400)
        
        user_id = get_jwt_identity()
        
        subscription = Subscription.query.filter_by(
            id=subscription_id,
            user_id=user_id
        ).first()
        
        if not subscription:
            return error_response('Subscription Not Found', 'Invalid subscription ID', 404)
        
        updated_fields = []
        
        # Update end date if provided
        if 'end_date' in data:
            try:
                end_date_str = data['end_date']
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                subscription.end_date = end_date
                updated_fields.append('end_date')
            except ValueError:
                return error_response('Invalid Date', 'End date must be a valid ISO datetime string', 400)
        
        # Update active status if provided
        if 'is_active' in data:
            is_active = data.get('is_active')
            if isinstance(is_active, bool):
                subscription.is_active = is_active
                updated_fields.append('is_active')
            else:
                return error_response('Invalid Status', 'is_active must be a boolean value', 400)
        
        if updated_fields:
            db.session.commit()
            
            return success_response(
                {
                    'subscription': subscription.to_dict(),
                    'updated_fields': updated_fields
                },
                'Subscription updated successfully'
            )
        else:
            return success_response(
                {'subscription': subscription.to_dict()},
                'No changes made to subscription'
            )
        
    except Exception as e:
        db.session.rollback()
        return handle_exception(e, 'Failed to update subscription')


@subscriptions_bp.route('/<int:subscription_id>', methods=['DELETE'])
@auth_required
def cancel_subscription(subscription_id):
    """
    Cancel a subscription (set as inactive).
    
    Request body:
    {
        "reason": "string" (optional)
    }
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'User requested cancellation')
        
        user_id = get_jwt_identity()
        
        subscription = Subscription.query.filter_by(
            id=subscription_id,
            user_id=user_id
        ).first()
        
        if not subscription:
            return error_response('Subscription Not Found', 'Invalid subscription ID', 404)
        
        if not subscription.is_active:
            return error_response('Subscription Inactive', 'Subscription is already inactive', 400)
        
        # Mark subscription as inactive
        subscription.is_active = False
        db.session.commit()
        
        response_data = {
            'subscription': subscription.to_dict(),
            'cancellation_reason': reason,
            'cancelled_at': datetime.now(timezone.utc).isoformat()
        }
        
        return success_response(
            response_data,
            'Subscription cancelled successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        return handle_exception(e, 'Failed to cancel subscription')


@subscriptions_bp.route('/current', methods=['GET'])
@auth_required
def get_current_subscription():
    """
    Get user's current active subscription with detailed information.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        subscription = user.active_subscription
        
        if not subscription:
            return error_response(
                'No Active Subscription',
                'You do not have an active subscription',
                404
            )
        
        tier_info = SUBSCRIPTION_TIERS.get(subscription.subscription_type, {})
        
        # Calculate usage statistics
        current_accounts = len(user.quotex_accounts)
        current_active_sessions = len([s for s in user.trading_sessions if s.is_active])
        
        response_data = {
            'subscription': subscription.to_dict(),
            'tier_info': tier_info,
            'usage': {
                'accounts': {
                    'current': current_accounts,
                    'limit': subscription.max_accounts,
                    'remaining': max(0, subscription.max_accounts - current_accounts)
                },
                'sessions': {
                    'current': current_active_sessions,
                    'limit': subscription.max_sessions,
                    'remaining': max(0, subscription.max_sessions - current_active_sessions)
                }
            }
        }
        
        return success_response(response_data, 'Current subscription retrieved successfully')
        
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve current subscription')


@subscriptions_bp.route('/check-limits', methods=['GET'])
@auth_required
def check_subscription_limits():
    """
    Check if user can create new accounts or sessions based on subscription limits.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User Not Found', 'Invalid user', 404)
        
        subscription = user.active_subscription
        
        if not subscription:
            return error_response(
                'No Active Subscription',
                'You need an active subscription to use this service',
                403
            )
        
        if subscription.is_expired:
            return error_response(
                'Subscription Expired',
                'Your subscription has expired. Please renew to continue.',
                403
            )
        
        # Calculate current usage
        current_accounts = len(user.quotex_accounts)
        current_active_sessions = len([s for s in user.trading_sessions if s.is_active])
        
        response_data = {
            'subscription_valid': True,
            'limits': {
                'accounts': {
                    'can_create': current_accounts < subscription.max_accounts,
                    'current': current_accounts,
                    'limit': subscription.max_accounts,
                    'remaining': max(0, subscription.max_accounts - current_accounts)
                },
                'sessions': {
                    'can_create': current_active_sessions < subscription.max_sessions,
                    'current': current_active_sessions,
                    'limit': subscription.max_sessions,
                    'remaining': max(0, subscription.max_sessions - current_active_sessions)
                }
            },
            'subscription_info': {
                'type': subscription.subscription_type,
                'expires_at': subscription.end_date.isoformat(),
                'days_remaining': subscription.days_remaining
            }
        }
        
        return success_response(response_data, 'Subscription limits checked successfully')
        
    except Exception as e:
        return handle_exception(e, 'Failed to check subscription limits') 
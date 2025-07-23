"""
Utility functions for the multi-user trading platform API.
"""

from flask import jsonify, request
from datetime import datetime, timezone
import traceback
import logging

logger = logging.getLogger(__name__)


def success_response(data=None, message="Success", status_code=200):
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Flask response object
    """
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code


def error_response(error, message="An error occurred", status_code=400, details=None):
    """
    Create a standardized error response.
    
    Args:
        error: Error type or name
        message: Error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        Flask response object
    """
    response = {
        'success': False,
        'error': error,
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code


def handle_error(error_type, message, status_code=500):
    """
    Handle and log errors with standardized response.
    
    Args:
        error_type: Type of error
        message: Error message
        status_code: HTTP status code
        
    Returns:
        Flask response object
    """
    logger.error(f"{error_type}: {message}")
    return error_response(error_type, message, status_code)


def handle_exception(e, message="Internal server error"):
    """
    Handle exceptions with logging and standardized response.
    
    Args:
        e: Exception object
        message: Custom error message
        
    Returns:
        Flask response object
    """
    logger.error(f"Exception: {str(e)}")
    logger.error(traceback.format_exc())
    
    return error_response(
        error="Internal Server Error",
        message=message,
        status_code=500,
        details=str(e) if request.environ.get('FLASK_ENV') == 'development' else None
    )


def paginate_query(query, page=None, per_page=None, max_per_page=100):
    """
    Paginate a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        per_page: Items per page
        max_per_page: Maximum items per page
        
    Returns:
        dict: Pagination result with items and metadata
    """
    try:
        page = int(request.args.get('page', page or 1))
        per_page = int(request.args.get('per_page', per_page or 20))
    except (ValueError, TypeError):
        page = 1
        per_page = 20
    
    # Enforce limits
    page = max(1, page)
    per_page = min(max(1, per_page), max_per_page)
    
    # Execute pagination
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        'items': [item.to_dict() if hasattr(item, 'to_dict') else item for item in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'next_page': pagination.next_num if pagination.has_next else None,
            'prev_page': pagination.prev_num if pagination.has_prev else None
        }
    }


def validate_pagination_params():
    """
    Validate and return pagination parameters from request.
    
    Returns:
        tuple: (page, per_page, sort_by, sort_order)
    """
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    
    try:
        per_page = min(max(1, int(request.args.get('per_page', 20))), 100)
    except (ValueError, TypeError):
        per_page = 20
    
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc').lower()
    
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'
    
    return page, per_page, sort_by, sort_order


def filter_dict(data, allowed_fields):
    """
    Filter dictionary to only include allowed fields.
    
    Args:
        data: Dictionary to filter
        allowed_fields: List of allowed field names
        
    Returns:
        dict: Filtered dictionary
    """
    return {k: v for k, v in data.items() if k in allowed_fields}


def format_datetime(dt):
    """
    Format datetime object to ISO string.
    
    Args:
        dt: datetime object
        
    Returns:
        str: ISO formatted datetime string
    """
    if dt is None:
        return None
    return dt.isoformat() if isinstance(dt, datetime) else str(dt)


def parse_datetime(dt_string):
    """
    Parse ISO datetime string to datetime object.
    
    Args:
        dt_string: ISO datetime string
        
    Returns:
        datetime: Parsed datetime object
    """
    if not dt_string:
        return None
    
    try:
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except ValueError:
        return None


def get_client_ip():
    """
    Get client IP address from request.
    
    Returns:
        str: Client IP address
    """
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ.get('REMOTE_ADDR', 'unknown')
    else:
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()


def log_api_request():
    """
    Log API request details for monitoring.
    """
    logger.info(f"API Request: {request.method} {request.url} from {get_client_ip()}")


def safe_float(value, default=0.0):
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        float: Converted value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """
    Safely convert value to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        int: Converted value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def calculate_percentage(part, total):
    """
    Calculate percentage with safe division.
    
    Args:
        part: Part value
        total: Total value
        
    Returns:
        float: Percentage (0-100)
    """
    if total == 0:
        return 0.0
    return (part / total) * 100


def format_currency(amount, symbol='$', decimals=2):
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        symbol: Currency symbol
        decimals: Number of decimal places
        
    Returns:
        str: Formatted currency string
    """
    if amount is None:
        return f"{symbol}0.00"
    
    return f"{symbol}{amount:,.{decimals}f}"


def generate_session_name(user, account_name=None):
    """
    Generate a default session name.
    
    Args:
        user: User object
        account_name: Account name (optional)
        
    Returns:
        str: Generated session name
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    account_part = f"_{account_name}" if account_name else ""
    return f"{user.username}{account_part}_{timestamp}"


def sanitize_string(value, max_length=None):
    """
    Sanitize string input.
    
    Args:
        value: String to sanitize
        max_length: Maximum length to truncate to
        
    Returns:
        str: Sanitized string
    """
    if not value:
        return ""
    
    # Basic sanitization
    sanitized = str(value).strip()
    
    if max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_subscription_limits(user, resource_type, current_count=None):
    """
    Validate subscription limits for resources.
    
    Args:
        user: User object
        resource_type: Type of resource ('accounts', 'sessions')
        current_count: Current resource count
        
    Returns:
        tuple: (is_valid, error_message)
    """
    subscription = user.active_subscription
    
    if not subscription:
        return False, "Active subscription required"
    
    if subscription.is_expired:
        return False, "Subscription has expired"
    
    if resource_type == 'accounts':
        limit = subscription.max_accounts
        current = current_count or len(user.quotex_accounts)
        resource_name = "trading accounts"
    elif resource_type == 'sessions':
        limit = subscription.max_sessions
        current = current_count or len([s for s in user.trading_sessions if s.is_active])
        resource_name = "active sessions"
    else:
        return False, "Unknown resource type"
    
    if current >= limit:
        return False, f"Maximum {resource_name} limit ({limit}) reached for {subscription.subscription_type} subscription"
    
    return True, None 
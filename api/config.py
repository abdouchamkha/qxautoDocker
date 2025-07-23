"""
Configuration management for the multi-user trading platform API.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BaseConfig:
    """Base configuration class with common settings."""
    
    # Basic Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///trading_platform.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    
    # CORS settings
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
    
    # Database encryption
    DATABASE_ENCRYPTION_KEY = os.getenv('DATABASE_ENCRYPTION_KEY')
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '-1002526280469')
    
    # Quotex settings
    QUOTEX_API_TIMEOUT = int(os.getenv('QUOTEX_API_TIMEOUT', '30'))
    QUOTEX_RECONNECT_ATTEMPTS = int(os.getenv('QUOTEX_RECONNECT_ATTEMPTS', '3'))
    
    # API settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '5000'))
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    
    # Pagination
    MAX_PER_PAGE = 100
    DEFAULT_PER_PAGE = 20
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def validate_config():
        """Validate that all required configuration is present."""
        required_vars = [
            'DATABASE_ENCRYPTION_KEY',
            'JWT_SECRET_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False
    
    # More permissive CORS for development
    CORS_ORIGINS = ['*']
    
    # Shorter token expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Logging
    LOG_LEVEL = 'DEBUG'


class TestingConfig(BaseConfig):
    """Testing configuration."""
    
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Short token expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    
    # Test encryption key
    DATABASE_ENCRYPTION_KEY = 'test-key-for-testing-only'


class ProductionConfig(BaseConfig):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Stricter CORS for production
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
    
    # Production database (PostgreSQL recommended)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/trading_platform')
    
    # Enhanced security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging
    LOG_LEVEL = 'WARNING'
    
    @staticmethod
    def init_app(app):
        """Initialize the app for production."""
        BaseConfig.validate_config()
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        
        handler = StreamHandler()
        handler.setLevel(logging.WARNING)
        app.logger.addHandler(handler)


class DockerConfig(ProductionConfig):
    """Docker deployment configuration."""
    
    # Docker-specific settings
    API_HOST = '0.0.0.0'
    API_PORT = 5000
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Log to stdout for Docker
        import logging
        import sys
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration class based on environment.
    
    Args:
        config_name: Configuration name or None to auto-detect
        
    Returns:
        Configuration class
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config_map.get(config_name, config_map['default'])


def get_database_url():
    """Get the database URL for the current environment."""
    return os.getenv('DATABASE_URL', 'sqlite:///trading_platform.db')


def is_production():
    """Check if running in production environment."""
    return os.getenv('FLASK_ENV') == 'production'


def is_testing():
    """Check if running in testing environment."""
    return os.getenv('FLASK_ENV') == 'testing' 
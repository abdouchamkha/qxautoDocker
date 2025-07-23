"""
Database initialization script for the multi-user trading platform.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from cryptography.fernet import Fernet
from flask import Flask
from .models import db, User, Subscription


def generate_encryption_key():
    """Generate a new encryption key for database encryption."""
    return Fernet.generate_key().decode()


def initialize_database(app: Flask, drop_existing=False):
    """
    Initialize the database with all tables.
    
    Args:
        app: Flask application instance
        drop_existing: Whether to drop existing tables before creating new ones
    """
    with app.app_context():
        if drop_existing:
            print("Dropping existing database tables...")
            db.drop_all()
        
        print("Creating database tables...")
        db.create_all()
        
        # Create indexes for better performance
        try:
            # Additional indexes can be added here if needed
            db.session.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);')
            db.session.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);')
            db.session.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_user_active ON subscriptions(user_id, is_active);')
            db.session.execute('CREATE INDEX IF NOT EXISTS idx_quotex_accounts_user ON quotex_accounts(user_id);')
            db.session.execute('CREATE INDEX IF NOT EXISTS idx_trading_sessions_user_active ON trading_sessions(user_id, is_active);')
            db.session.execute('CREATE INDEX IF NOT EXISTS idx_trades_session ON trades(session_id);')
            db.session.execute('CREATE INDEX IF NOT EXISTS idx_api_tokens_token ON api_tokens(token);')
            db.session.commit()
            print("Database indexes created successfully.")
        except Exception as e:
            print(f"Warning: Could not create some indexes: {e}")
        
        print("Database initialization completed successfully!")


def create_admin_user(app: Flask, username="admin", email="admin@trading-platform.com", password="admin123"):
    """
    Create an admin user with VIP subscription.
    
    Args:
        app: Flask application instance
        username: Admin username
        email: Admin email
        password: Admin password
    """
    with app.app_context():
        # Check if admin user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Admin user '{username}' already exists!")
            return existing_user
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            is_active=True
        )
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.flush()  # Get the user ID
        
        # Create VIP subscription for admin (1 year)
        admin_subscription = Subscription(
            user_id=admin_user.id,
            subscription_type='vip',
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=365),
            is_active=True,
            max_accounts=10,
            max_sessions=5
        )
        
        db.session.add(admin_subscription)
        db.session.commit()
        
        print(f"Admin user created successfully!")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Subscription: VIP (1 year)")
        print("Please change the admin password after first login!")
        
        return admin_user


def setup_environment_variables():
    """
    Set up required environment variables for the application.
    """
    env_vars = {
        'DATABASE_URL': 'sqlite:///trading_platform.db',
        'DATABASE_ENCRYPTION_KEY': generate_encryption_key(),
        'FLASK_ENV': 'development',
        'JWT_SECRET_KEY': Fernet.generate_key().decode(),
        'API_HOST': '0.0.0.0',
        'API_PORT': '5000'
    }
    
    env_file_path = '.env'
    env_exists = os.path.exists(env_file_path)
    
    if not env_exists:
        print("Creating .env file with default configuration...")
        with open(env_file_path, 'w') as f:
            f.write("# Multi-User Trading Platform Configuration\n")
            f.write("# Generated automatically - modify as needed\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        print(f".env file created at {os.path.abspath(env_file_path)}")
        print("Please review and modify the configuration as needed.")
    else:
        print(".env file already exists. Skipping creation.")


def create_sample_data(app: Flask):
    """
    Create sample data for testing purposes.
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        # Create a test user
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(
                username='testuser',
                email='test@example.com',
                is_active=True
            )
            test_user.set_password('test123')
            db.session.add(test_user)
            db.session.flush()
            
            # Create basic subscription for test user
            test_subscription = Subscription(
                user_id=test_user.id,
                subscription_type='basic',
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc) + timedelta(days=30),
                is_active=True,
                max_accounts=2,
                max_sessions=1
            )
            db.session.add(test_subscription)
            
            db.session.commit()
            print("Sample test user created (username: testuser, password: test123)")


def run_migrations(app: Flask):
    """
    Run any necessary database migrations.
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        # Future migrations can be added here
        print("No migrations to run.")


def full_setup(app: Flask, create_admin=True, create_samples=False, drop_existing=False):
    """
    Perform full database setup including initialization, admin user, and environment setup.
    
    Args:
        app: Flask application instance
        create_admin: Whether to create admin user
        create_samples: Whether to create sample data
        drop_existing: Whether to drop existing tables
    """
    print("Starting full database setup...")
    
    # Setup environment variables
    setup_environment_variables()
    
    # Initialize database
    initialize_database(app, drop_existing=drop_existing)
    
    # Create admin user
    if create_admin:
        create_admin_user(app)
    
    # Create sample data
    if create_samples:
        create_sample_data(app)
    
    # Run migrations
    run_migrations(app)
    
    print("Full database setup completed!")


if __name__ == "__main__":
    """
    Run database setup from command line.
    Usage: python -m database.init_db [--drop] [--admin] [--samples]
    """
    import argparse
    from flask import Flask
    from api.config import get_config
    
    parser = argparse.ArgumentParser(description='Initialize the trading platform database')
    parser.add_argument('--drop', action='store_true', help='Drop existing tables')
    parser.add_argument('--admin', action='store_true', default=True, help='Create admin user')
    parser.add_argument('--samples', action='store_true', help='Create sample data')
    
    args = parser.parse_args()
    
    # Create Flask app for database operations
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    db.init_app(app)
    
    full_setup(
        app, 
        create_admin=args.admin, 
        create_samples=args.samples, 
        drop_existing=args.drop
    ) 
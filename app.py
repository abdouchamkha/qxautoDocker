#!/usr/bin/env python3
"""
Main application entry point for the Multi-User Trading Platform.
"""

import os
import sys
from flask import Flask
from api import create_app
from database.init_db import full_setup
from api.config import get_config

def main():
    """Main application entry point."""
    # Get configuration
    config_name = os.getenv('FLASK_ENV', 'development')
    
    # Create Flask application
    app = create_app(config_name)
    
    # Check if we need to initialize database
    if '--init-db' in sys.argv:
        print("Initializing database...")
        full_setup(app, create_admin=True, create_samples='--samples' in sys.argv)
        print("Database initialization completed!")
        return
    
    # Get configuration
    config = get_config(config_name)
    
    # Run the application
    host = getattr(config, 'API_HOST', '0.0.0.0')
    port = getattr(config, 'API_PORT', 5000)
    debug = getattr(config, 'DEBUG', False)
    
    print(f"Starting Multi-User Trading Platform API...")
    print(f"Environment: {config_name}")
    print(f"Debug mode: {debug}")
    print(f"Server: http://{host}:{port}")
    print(f"API Base URL: http://{host}:{port}/api/v1")
    print("\nAvailable endpoints:")
    print(f"  • Health Check: http://{host}:{port}/api/v1/health")
    print(f"  • API Info: http://{host}:{port}/api/v1/")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 
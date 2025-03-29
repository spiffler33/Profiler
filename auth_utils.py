"""
Centralized Authentication Utility Module

This module provides a single, unified authentication system for the entire application.
It creates a shared HTTPBasicAuth instance that can be imported and used across
all modules, ensuring consistent authentication behavior.
"""

from flask_httpauth import HTTPBasicAuth
from config import Config
import logging
import os
import base64
from flask import request, g, Response

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='auth_debug.log'
)

# Create a single, shared auth instance that will be imported by other modules
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    """
    Central authentication verification function.
    In development mode, always return success.
    In production, check credentials against configuration.
    
    Args:
        username: The provided username
        password: The provided password
        
    Returns:
        Username string if authenticated, None otherwise
    """
    # Development mode always passes authentication
    dev_mode = getattr(Config, 'DEV_MODE', False)
    
    # Log authentication attempt
    logging.info(f"Auth attempt for path: {request.path}, username: {username}, DEV_MODE: {dev_mode}")
    
    if dev_mode:
        logging.info(f"DEV_MODE bypass for username: {username}")
        return "admin"  # Return any non-empty string to indicate success
    
    # Production authentication logic
    if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        logging.info(f"Production auth success for username: {username}")
        return username
    
    logging.warning(f"Auth failed for username: {username}")
    return None  # Authentication failed

@auth.error_handler
def auth_error():
    """Standard error handler for authentication failures"""
    path = request.path if hasattr(request, 'path') else 'unknown'
    logging.warning(f"Auth error for path: {path}")
    
    return Response(
        'Authentication required for this resource', 401,
        {'WWW-Authenticate': 'Basic realm="Admin Access"'}
    )

# Improved auth decorator with proper exemption handling and logging
def admin_required(view_function):
    """
    Decorator to protect admin routes, with DEV_MODE bypass and proper exemption handling.
    
    This decorator provides:
    1. Authentication bypass in development mode
    2. Proper handling of exempted paths
    3. Detailed logging for troubleshooting
    4. Consistent authentication across the application
    
    Usage:
        @admin_required
        def my_admin_endpoint():
            # Function implementation
    """
    import functools
    
    @functools.wraps(view_function)
    def wrapper(*args, **kwargs):
        # Get request details for logging
        path = request.path if hasattr(request, 'path') else 'unknown'
        method = request.method if hasattr(request, 'method') else 'unknown'
        
        # Check if path is explicitly exempted in the middleware
        exempt = False
        if hasattr(request, 'environ') and request.environ.get('AUTH_EXEMPT'):
            exempt = True
            logging.info(f"AUTH_EXEMPT flag found for {method} {path}")
            return view_function(*args, **kwargs)
        
        # Check if we're in DEV_MODE
        dev_mode = getattr(Config, 'DEV_MODE', False)
        if dev_mode:
            # Authentication bypass in development mode
            logging.info(f"DEV_MODE authentication bypass for {method} {path}")
            return view_function(*args, **kwargs)
        
        # Get authentication header for logging
        auth_header = request.headers.get('Authorization', 'None')
        has_auth = auth_header != 'None' and auth_header.startswith('Basic ')
        
        logging.info(f"Production mode auth check for {method} {path}, Has Auth Header: {has_auth}")
        
        # Use the standard auth system in production
        return auth.login_required(view_function)(*args, **kwargs)
    
    return wrapper
"""
Fixed implementation of rate limiting functionality.

This module provides an enhanced implementation of rate limiting
that properly handles window expiration and limits.
"""

import time
from flask import current_app, g, request
import logging

# Set up logging
logger = logging.getLogger(__name__)

# In-memory rate limiting storage with proper expiration
_rate_limit_store = {}

def _cleanup_expired_rate_limits():
    """Clean up expired rate limit windows."""
    now = time.time()
    expired_keys = []
    
    # Find expired windows
    for key, (request_count, window_start) in _rate_limit_store.items():
        if now - window_start > 60:
            expired_keys.append(key)
    
    # Remove expired windows
    for key in expired_keys:
        del _rate_limit_store[key]

def _check_rate_limit(client_ip, endpoint_type='default'):
    """
    Check if a client has exceeded their rate limit.
    
    Args:
        client_ip: The client's IP address
        endpoint_type: The type of endpoint ('default', 'admin', etc.)
        
    Returns:
        Dictionary with rate limit status
    """
    # Clean up expired rate limits occasionally
    if len(_rate_limit_store) > 100:  # Arbitrary threshold
        _cleanup_expired_rate_limits()
    
    # Get rate limit from config based on endpoint type
    if endpoint_type == 'admin':
        # Admin endpoints have a lower rate limit
        rate_limit = current_app.config.get('ADMIN_RATE_LIMIT', 20)
    else:
        # Regular endpoints have a higher rate limit
        rate_limit = current_app.config.get('API_RATE_LIMIT', 100)
    
    # Get current time
    now = time.time()
    
    # Create key for rate limit store
    key = f"{client_ip}:{endpoint_type}"
    
    # Get current request count and window start time
    if key in _rate_limit_store:
        request_count, window_start = _rate_limit_store[key]
        
        # Check if window has expired
        if now - window_start > 60:
            # Reset window
            _rate_limit_store[key] = (1, now)
            return {'limited': False, 'remaining': rate_limit - 1, 'limit': rate_limit, 'window_start': now}
        else:
            # Check if limit exceeded
            if request_count >= rate_limit:
                # Calculate retry after time
                retry_after = max(1, int(60 - (now - window_start)))
                return {'limited': True, 'retry_after': retry_after, 'limit': rate_limit}
            else:
                # Increment request count
                _rate_limit_store[key] = (request_count + 1, window_start)
                return {'limited': False, 'remaining': rate_limit - request_count - 1, 'limit': rate_limit}
    else:
        # First request in window
        _rate_limit_store[key] = (1, now)
        return {'limited': False, 'remaining': rate_limit - 1, 'limit': rate_limit, 'window_start': now}

def add_rate_limit_headers(response, client_ip, endpoint_type='default'):
    """
    Add rate limit headers to a response.
    
    Args:
        response: The Flask response object
        client_ip: The client's IP address
        endpoint_type: The type of endpoint
        
    Returns:
        The updated response object
    """
    rate_info = _check_rate_limit(client_ip, endpoint_type)
    
    # Add standard rate limit headers
    response.headers['X-RateLimit-Limit'] = str(rate_info.get('limit', 100))
    response.headers['X-RateLimit-Remaining'] = str(rate_info.get('remaining', 0))
    response.headers['X-RateLimit-Reset'] = str(int(time.time() + 60))
    
    # Add retry-after header if limited
    if rate_info.get('limited', False):
        response.headers['Retry-After'] = str(rate_info.get('retry_after', 60))
    
    return response

def rate_limit_middleware():
    """
    Middleware function to enforce rate limits.
    
    Returns:
        Response object if rate limited, otherwise None
    """
    from flask import jsonify
    
    client_ip = request.remote_addr
    endpoint_type = 'default'
    
    # Different limits for admin endpoints
    if '/admin/' in request.path:
        endpoint_type = 'admin'
    
    # Check for rate limiting
    rate_info = _check_rate_limit(client_ip, endpoint_type)
    
    # If rate limited, return 429 response
    if rate_info.get('limited', False):
        response = jsonify({
            'error': 'Rate limit exceeded',
            'message': f"Rate limit exceeded. Try again in {rate_info['retry_after']} seconds",
            'retry_after': rate_info['retry_after']
        })
        response.status_code = 429
        
        # Add rate limit headers
        add_rate_limit_headers(response, client_ip, endpoint_type)
        
        return response
    
    # Store rate info in flask.g for adding headers to response
    g.rate_info = rate_info
    g.rate_client_ip = client_ip
    g.rate_endpoint_type = endpoint_type
    
    return None
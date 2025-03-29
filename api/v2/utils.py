"""
Common utilities for API endpoints.

This module contains shared functions used across API endpoints to:
1. Handle caching
2. Implement rate limiting
3. Monitor performance
4. Format responses

By consolidating these functions in one place, we reduce code duplication
and ensure consistent behavior across all API endpoints.
"""

import time
import logging
import functools
import json
import uuid
from typing import Dict, Any, Optional, Tuple, Callable
from flask import jsonify, request, current_app, g

# Import the consolidated cache implementation
from models.monte_carlo.simulation import cache_response as simulation_cache_response

# Improved logging
logger = logging.getLogger('api')

# Import auth utilities
from auth_utils import admin_required

# In-memory rate limiting with token bucket algorithm
import threading
from collections import defaultdict

# Enhanced rate limiter using token bucket algorithm 
class TokenBucketRateLimiter:
    """
    Improved rate limiter using the token bucket algorithm
    
    This provides more flexibility and better handling of burst traffic.
    """
    def __init__(self, default_rate=60, admin_rate=30, window_seconds=60, burst_capacity=10):
        self.default_rate = default_rate  # Default requests per minute
        self.admin_rate = admin_rate      # Admin requests per minute 
        self.window_seconds = window_seconds  # Window size in seconds
        self.burst_capacity = burst_capacity  # Additional tokens for burst capacity
        
        # Token buckets for clients: client_id -> {tokens, last_refill, type}
        self.buckets = defaultdict(lambda: {'tokens': default_rate + burst_capacity,
                                          'last_refill': time.time(),
                                          'type': 'default'})
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'limited_requests': 0,
            'admin_requests': 0,
            'default_requests': 0
        }
        
    def _get_client_id(self, request):
        """Get client identifier (IP address or API key)"""
        # First try to use an API key if available
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return f"key_{api_key}"
            
        # Otherwise use IP address
        if request.headers.get('X-Forwarded-For'):
            # For requests behind a proxy
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return request.remote_addr
    
    def _get_endpoint_type(self, request):
        """Determine endpoint type from path"""
        if '/admin/' in request.path:
            return 'admin'
        return 'default'
        
    def check(self, request):
        """
        Check if request should be allowed based on rate limits
        
        Returns: (allowed, remaining, reset)
        """
        client_id = self._get_client_id(request)
        endpoint_type = self._get_endpoint_type(request)
        
        with self.lock:
            # Update statistics
            self.stats['total_requests'] += 1
            if endpoint_type == 'admin':
                self.stats['admin_requests'] += 1
            else:
                self.stats['default_requests'] += 1
                
            # Get or initialize bucket
            bucket = self.buckets[client_id]
            
            # Update bucket type if needed
            if bucket['type'] != endpoint_type:
                # If changing from default to admin or vice versa,
                # adjust rate but keep tokens proportional
                if endpoint_type == 'admin':
                    # Scale tokens when switching to admin (lower rate)
                    bucket['tokens'] = min(bucket['tokens'] * (self.admin_rate / self.default_rate),
                                          self.admin_rate + self.burst_capacity)
                else:
                    # Scale tokens when switching to default (higher rate)
                    bucket['tokens'] = min(bucket['tokens'] * (self.default_rate / self.admin_rate),
                                          self.default_rate + self.burst_capacity)
                bucket['type'] = endpoint_type
            
            # Calculate tokens to add based on time elapsed
            now = time.time()
            time_elapsed = now - bucket['last_refill']
            
            # Get rate based on endpoint type
            rate = self.admin_rate if endpoint_type == 'admin' else self.default_rate
            
            # Calculate tokens to add and refill
            tokens_to_add = time_elapsed * (rate / self.window_seconds)
            max_tokens = rate + self.burst_capacity
            bucket['tokens'] = min(bucket['tokens'] + tokens_to_add, max_tokens)
            bucket['last_refill'] = now
            
            # Check if we have enough tokens
            if bucket['tokens'] >= 1:
                # Allow request and consume one token
                bucket['tokens'] -= 1
                remaining = bucket['tokens']
                
                # Calculate when bucket will be full again
                reset = now + (max_tokens - bucket['tokens']) * (self.window_seconds / rate)
                
                return True, remaining, reset
            else:
                # Rate limited
                self.stats['limited_requests'] += 1
                
                # Calculate time until one token is available
                reset = now + (1 - bucket['tokens']) * (self.window_seconds / rate)
                retry_after = max(1, int(reset - now))
                
                return False, 0, reset
    
    def get_stats(self):
        """Get rate limiter statistics"""
        with self.lock:
            stats = self.stats.copy()
            stats['active_clients'] = len(self.buckets)
            return stats

# Create global rate limiter instance
rate_limiter = TokenBucketRateLimiter()


def rate_limit_decorator(f):
    """
    Decorator to apply rate limiting to API endpoints
    
    This uses the token bucket algorithm for more flexible rate limiting.
    
    Usage:
        @app.route('/api/v2/endpoint')
        @rate_limit_decorator
        def my_endpoint():
            # Function implementation
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip rate limiting in development mode
        if current_app.config.get('DEV_MODE', False):
            return f(*args, **kwargs)
            
        # Check rate limit
        allowed, remaining, reset_time = rate_limiter.check(request)
        
        # If not allowed, return rate limit error
        if not allowed:
            response = jsonify({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests, please try again later',
                'retry_after': max(1, int(reset_time - time.time()))
            }), 429
            
            # Log rate limit event
            logger.warning(f"Rate limit exceeded for {request.remote_addr} on {request.path}")
        else:
            # Process the request
            response = f(*args, **kwargs)
            
        # Add rate limit headers if we have a response object
        if hasattr(response, 'headers'):
            response.headers['X-RateLimit-Limit'] = str(rate_limiter.default_rate)
            response.headers['X-RateLimit-Remaining'] = str(int(remaining))
            response.headers['X-RateLimit-Reset'] = str(int(reset_time))
            
        return response
    
    return decorated_function


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
    rate_info = check_rate_limit(client_ip, endpoint_type)
    
    # Add standard rate limit headers
    response.headers['X-RateLimit-Limit'] = str(rate_info.get('limit', 100))
    response.headers['X-RateLimit-Remaining'] = str(rate_info.get('remaining', 0))
    response.headers['X-RateLimit-Reset'] = str(int(time.time() + 60))
    
    # Add retry-after header if limited
    if rate_info.get('limited', False):
        response.headers['Retry-After'] = str(rate_info.get('retry_after', 60))
    
    return response


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

def check_rate_limit(client_ip, endpoint_type='default'):
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
            return {'limited': False, 'remaining': rate_limit - 1, 'limit': rate_limit, 'window_start': now, 'retry_after': 0}
        else:
            # Check if limit exceeded
            if request_count >= rate_limit:
                # Calculate retry after time
                retry_after = max(1, int(60 - (now - window_start)))
                return {'limited': True, 'retry_after': retry_after, 'limit': rate_limit, 'remaining': 0}
            else:
                # Increment request count
                _rate_limit_store[key] = (request_count + 1, window_start)
                return {'limited': False, 'remaining': rate_limit - request_count - 1, 'limit': rate_limit, 'retry_after': 0}
    else:
        # First request in window
        _rate_limit_store[key] = (1, now)
        return {'limited': False, 'remaining': rate_limit - 1, 'limit': rate_limit, 'window_start': now, 'retry_after': 0}

def rate_limit_middleware():
    """
    Middleware function to enforce rate limits.
    
    Returns:
        Response object if rate limited, otherwise None
    """
    client_ip = request.remote_addr
    endpoint_type = 'admin' if '/admin/' in request.path else 'default'
    
    # Check for rate limiting
    rate_info = check_rate_limit(client_ip, endpoint_type)
    
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


def check_cache(key):
    """
    Check if a response is in the cache and return it if found.
    
    Args:
        key: Cache key to check
        
    Returns:
        Cached response or None if not found
    """
    # Use the global cache object directly
    from models.monte_carlo.cache import _cache
    cached_data = _cache.get(key)
    if cached_data is not None:
        return jsonify(cached_data), 200
    return None


def cache_response(key, data, ttl=3600):
    """
    Cache a response for future requests.
    
    Args:
        key: Cache key
        data: Data to cache
        ttl: Time-to-live in seconds (default: 1 hour)
    """
    # Skip caching if disabled in config
    if not current_app.config.get('API_CACHE_ENABLED', True):
        return
        
    # Get TTL from config if not specified
    if ttl is None:
        ttl = current_app.config.get('API_CACHE_TTL', 3600)
        
    # Use the consolidated implementation
    simulation_cache_response(key, data, ttl)


def monitor_performance(f):
    """
    Decorator to monitor endpoint performance metrics.
    
    This decorator:
    1. Times the execution of API endpoints
    2. Adds performance metrics to the response
    3. Logs errors with timing information
    4. Includes request tracking details and debugging info
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        g.cache_status = "BYPASS"  # Default status
        
        # Generate unique request ID for tracking
        request_id = f"req_{time.time():.0f}_{hash(request.path) % 10000:04d}"
        g.request_id = request_id
        
        # Log detailed request info for debugging
        try:
            # Get request headers (redact sensitive information)
            headers = dict(request.headers)
            if 'Authorization' in headers:
                headers['Authorization'] = 'Bearer [REDACTED]'
            if 'Cookie' in headers:
                headers['Cookie'] = '[REDACTED]'
                
            # Get request body for debugging
            body = None
            if request.method in ['POST', 'PUT'] and request.is_json:
                try:
                    body = request.get_json(cache=True, silent=True)
                    if body and isinstance(body, dict):
                        # Remove sensitive fields from logs
                        log_body = body.copy()
                        for field in ['password', 'token', 'key', 'secret']:
                            if field in log_body:
                                log_body[field] = '[REDACTED]'
                        body = log_body
                except:
                    body = "(failed to parse JSON)"
                    
            # Log complete request info
            request_info = {
                'id': request_id,
                'method': request.method,
                'url': request.url,
                'path': request.path,
                'query': dict(request.args),
                'body': body,
                'ip': request.remote_addr,
                'headers': headers
            }
            
            logger.info(f"[{request_id}] API Request: {json.dumps(request_info, default=str)}")
        except Exception as log_error:
            logger.error(f"Error logging request details: {str(log_error)}")
        
        try:
            result = f(*args, **kwargs)
            
            # Calculate performance metrics
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)
            
            # Log successful response
            logger.info(f"[{request_id}] Success: {request.method} {request.path} ({duration_ms:.2f}ms, cache:{getattr(g, 'cache_status', 'BYPASS')})")
            
            # If response is a tuple (data, status code), get the data
            response_data = result[0] if isinstance(result, tuple) else result
            status_code = result[1] if isinstance(result, tuple) and len(result) > 1 else 200
            
            # If the response is a Flask response object
            if hasattr(response_data, 'get_json'):
                data = response_data.get_json()
                if isinstance(data, dict):
                    # Add performance and request tracking info
                    data['performance'] = {
                        'duration_ms': duration_ms,
                        'endpoint': request.path,
                        'method': request.method,
                        'cache_status': getattr(g, 'cache_status', "BYPASS"),
                        'request_id': request_id
                    }
                    response_data.set_data(json.dumps(data))
            
            # If the response is a regular JSON object
            elif hasattr(response_data, 'data'):
                try:
                    data = json.loads(response_data.data)
                    if isinstance(data, dict):
                        # Add performance and request tracking info
                        data['performance'] = {
                            'duration_ms': duration_ms,
                            'endpoint': request.path,
                            'method': request.method,
                            'cache_status': getattr(g, 'cache_status', "BYPASS"),
                            'request_id': request_id
                        }
                        response_data.data = json.dumps(data).encode('utf-8')
                except (ValueError, AttributeError):
                    pass
            
            # Add request ID to response headers for client-side debugging
            if hasattr(response_data, 'headers'):
                response_data.headers['X-Request-ID'] = request_id
                response_data.headers['X-Response-Time'] = f"{duration_ms}ms"
                response_data.headers['X-Cache-Status'] = getattr(g, 'cache_status', "BYPASS")
            
            return result
        
        except Exception as e:
            # Log performance even for errors
            duration = time.time() - start_time
            logger.warning(f"[{request_id}] Error in {request.path} [{request.method}]: {str(e)} (took {duration:.3f}s)")
            
            # Create JSON-serializable error details
            error_details = {
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'error': str(e),
                'error_class': e.__class__.__name__,
                'duration_ms': round(duration * 1000, 2)
            }
            
            # Log detailed error information
            logger.error(f"[{request_id}] Detailed error: {json.dumps(error_details)}")
            
            # Re-raise the exception
            raise
    
    return wrapper


def admin_api_required(f):
    """
    Combined decorator for admin API endpoints
    
    This decorator:
    1. Applies admin authentication (using admin_required)
    2. Adds enhanced logging for admin operations
    3. Adds detailed documentation for admin API endpoints
    
    Usage:
        @app.route('/api/v2/admin/endpoint')
        @admin_required  # Authentication
        @admin_api_required  # Documentation and tracking
        def my_admin_endpoint():
            # Function implementation
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Log admin API access with detailed info
        client_id = request.remote_addr
        logger.info(f"Admin API access: {request.method} {request.path} by {client_id}")
        
        # Add request information to result
        result = f(*args, **kwargs)
        
        # If we have a response, enhance it with admin info
        if isinstance(result, tuple) and len(result) >= 1:
            response, *rest = result
            if hasattr(response, 'json'):
                try:
                    data = response.json
                    if callable(data):
                        data = data()
                    if isinstance(data, dict):
                        # Add admin API metadata
                        data['admin'] = {
                            'timestamp': datetime.now().isoformat(),
                            'api_version': 'v2',
                            'environment': 'development' if current_app.config.get('DEV_MODE', False) else 'production'
                        }
                        # Update response with enhanced data
                        response = jsonify(data)
                        return (response,) + tuple(rest)
                except Exception as e:
                    logger.warning(f"Error enhancing admin response: {str(e)}")
        
        return result
    
    # Mark the function as an admin API endpoint
    decorated_function.is_admin_api = True
    return decorated_function

def check_admin_access():
    """
    Check if the current request has admin access.
    
    Returns:
        True if admin access is granted, False otherwise
    """
    # First check DEV_MODE - admin access is always granted in dev mode
    if current_app.config.get('DEV_MODE', False):
        return True
        
    # Get admin key from header
    admin_key = request.headers.get('X-Admin-Key')
    
    # Compare with configured admin key
    return admin_key == current_app.config.get('ADMIN_API_KEY')


def create_error_response(message, status_code=400, error_type="validation_error", details=None):
    """
    Create a standardized error response with enhanced debugging information.
    
    Args:
        message: The error message
        status_code: The HTTP status code
        error_type: The type of error
        details: Additional error details for debugging (optional)
        
    Returns:
        Tuple of (response, status_code)
    """
    # Get request ID from g if available
    request_id = getattr(g, 'request_id', None)
    
    # Create base error response
    response = {
        "error": {
            "type": error_type,
            "message": message,
            "status": status_code,
            "timestamp": time.time()
        },
        "success": False
    }
    
    # Add request ID if available
    if request_id:
        response["error"]["request_id"] = request_id
    
    # Add request path for easier troubleshooting
    response["error"]["path"] = request.path
    
    # Add additional details if provided and we're in development/debug mode
    if details and current_app.config.get('DEBUG', False):
        response["error"]["details"] = details
    
    # Log the error for server-side troubleshooting
    logger.error(f"[{request_id or 'unknown'}] Error response ({error_type}): {message}")
    
    return jsonify(response), status_code
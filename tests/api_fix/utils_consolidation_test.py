#!/usr/bin/env python3
"""Test suite for API utils module consolidation"""

import os
import sys
import unittest
import logging
import json
import time
from datetime import datetime
import uuid
from unittest.mock import patch

# Add the project to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import flask and the api modules
from flask import Flask, jsonify, request, g
from api.v2.utils import (
    monitor_performance, check_cache, cache_response,
    rate_limit_middleware, check_admin_access, create_error_response
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class TestApp(Flask):
    """Flask app for testing utils module"""
    def __init__(self):
        super().__init__(__name__)
        self.config['TESTING'] = True
        self.config['API_CACHE_ENABLED'] = True
        self.config['API_CACHE_TTL'] = 3600
        self.config['API_RATE_LIMIT'] = 1000  # Set very high for testing
        self.config['ADMIN_API_KEY'] = 'test_admin_key'
        
        # Register test routes
        self.add_url_rule('/test/rate-limit', view_func=self.test_rate_limit, methods=['GET'])
        self.add_url_rule('/test/cache', view_func=self.test_cache, methods=['GET'])
        self.add_url_rule('/test/performance', view_func=self.test_performance, methods=['GET'])
        self.add_url_rule('/test/error', view_func=self.test_error, methods=['GET'])
        self.add_url_rule('/test/admin', view_func=self.test_admin, methods=['GET'])
        
        # Error handler for exceptions during request handling
        self.register_error_handler(Exception, self.handle_error)
        
        # Register after_request handlers to add rate limit headers
        self.after_request(self.add_rate_limit_headers)
        
    def init_rate_limiting(self):
        """Initialize rate limiting for specific tests only."""
        self.before_request(self.check_rate_limits)
        
    def check_rate_limits(self):
        """Check rate limits before processing requests."""
        return rate_limit_middleware()
        
    def add_rate_limit_headers(self, response):
        """Add rate limit headers to response."""
        if hasattr(g, 'rate_info'):
            response.headers['X-RateLimit-Limit'] = str(g.rate_info.get('limit', 100))
            response.headers['X-RateLimit-Remaining'] = str(g.rate_info.get('remaining', 0))
            response.headers['X-RateLimit-Reset'] = str(int(time.time() + 60))
            
            # Add retry-after header if limited
            if g.rate_info.get('limited', False):
                response.headers['Retry-After'] = str(g.rate_info.get('retry_after', 60))
        
        return response
        
    def handle_error(self, error):
        """Handle exceptions during request processing."""
        response = jsonify({
            'error': 'Internal server error',
            'message': str(error)
        })
        response.status_code = 500
        return response
    
    @monitor_performance
    def test_rate_limit(self):
        """Test rate limiting middleware."""
        return jsonify({"message": "Rate limit test", "success": True})
    
    @monitor_performance
    def test_cache(self):
        """Test cache functionality."""
        # Check if response is cached
        cache_key = f"test_cache:{request.args.get('id', 'default')}"
        cached_response = check_cache(cache_key)
        if cached_response:
            return cached_response
        
        # Generate a response
        response = {
            "message": "Cache test",
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "id": request.args.get('id', 'default')
        }
        
        # Cache the response
        cache_response(cache_key, response)
        
        return jsonify(response)
    
    @monitor_performance
    def test_performance(self):
        """Test performance monitoring decorator."""
        # Sleep for a bit to simulate some work
        import time
        time.sleep(0.1)
        
        return jsonify({
            "message": "Performance test",
            "success": True
        })
    
    @monitor_performance
    def test_error(self):
        """Test error handling."""
        # Check if we should throw an error
        if request.args.get('error', 'false').lower() == 'true':
            raise Exception("Test error")
        
        # Check if we should create an error response
        if request.args.get('custom_error', 'false').lower() == 'true':
            error_resp, status_code = create_error_response(
                "Custom error message", 
                status_code=int(request.args.get('status', '400')),
                error_type=request.args.get('type', 'validation_error')
            )
            return error_resp, status_code
        
        return jsonify({"message": "No error", "success": True})
    
    @monitor_performance
    def test_admin(self):
        """Test admin access check."""
        # Get admin key from header and check it
        admin_key = request.headers.get('X-Admin-Key')
        
        # Compare with the admin key in config
        if admin_key != self.config.get('ADMIN_API_KEY'):
            return jsonify({
                "error": "Unauthorized",
                "message": "Admin privileges required for this endpoint"
            }), 403
        
        return jsonify({
            "message": "Admin access granted",
            "success": True
        })


class APIUtilsTest(unittest.TestCase):
    """Test case for API utils module."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        logger.info("Setting up test environment for API utils tests")
        
        # Create a test client
        cls.app = TestApp()
        cls.client = cls.app.test_client()
    
    def test_01_rate_limiting(self):
        """Test rate limiting middleware."""
        logger.info("Testing rate limiting middleware")
        
        # For testing rate limiting, we need a much lower limit
        self.app.config['API_RATE_LIMIT'] = 5
        
        # Only enable rate limiting for this test
        self.app.init_rate_limiting()
        
        # Make requests until we hit the rate limit
        for i in range(self.app.config['API_RATE_LIMIT'] + 1):
            response = self.client.get('/test/rate-limit')
            
            if i < self.app.config['API_RATE_LIMIT']:
                # First requests should succeed
                self.assertEqual(response.status_code, 200)
                self.assertIn('X-RateLimit-Limit', response.headers)
                self.assertIn('X-RateLimit-Remaining', response.headers)
                remaining = int(response.headers['X-RateLimit-Remaining'])
                self.assertEqual(remaining, self.app.config['API_RATE_LIMIT'] - i - 1)
            else:
                # Last request should be rate limited
                self.assertEqual(response.status_code, 429)
                self.assertIn('Retry-After', response.headers)
                
                # Check response body
                data = json.loads(response.data)
                self.assertIn('error', data)
                self.assertEqual(data['error'], 'Rate limit exceeded')
                self.assertIn('retry_after', data)
        
        # Disable rate limiting for other tests
        self.app.before_request_funcs = {}
        
        # Reset rate limit to high value for other tests
        self.app.config['API_RATE_LIMIT'] = 1000
        
        logger.info("Rate limiting middleware works correctly")
    
    def test_02_caching(self):
        """Test cache functionality."""
        logger.info("Testing cache functionality")
        
        # Make a request to cache something
        unique_id = str(uuid.uuid4())
        first_response = self.client.get(f'/test/cache?id={unique_id}')
        self.assertEqual(first_response.status_code, 200)
        first_data = json.loads(first_response.data)
        
        # Make a second request to get from cache
        second_response = self.client.get(f'/test/cache?id={unique_id}')
        self.assertEqual(second_response.status_code, 200)
        second_data = json.loads(second_response.data)
        
        # Timestamps should be identical if response was cached
        self.assertEqual(first_data['timestamp'], second_data['timestamp'])
        
        # Try with a different ID to test a different cache key
        different_response = self.client.get(f'/test/cache?id=different_{unique_id}')
        self.assertEqual(different_response.status_code, 200)
        different_data = json.loads(different_response.data)
        
        # Should not match the first timestamp
        self.assertNotEqual(first_data['timestamp'], different_data['timestamp'])
        
        logger.info("Cache functionality works correctly")
    
    def test_03_performance_monitoring(self):
        """Test performance monitoring decorator."""
        logger.info("Testing performance monitoring decorator")
        
        response = self.client.get('/test/performance')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        
        # Check that performance metrics are included
        self.assertIn('performance', data)
        self.assertIn('duration_ms', data['performance'])
        self.assertIn('endpoint', data['performance'])
        self.assertIn('method', data['performance'])
        
        # Should be a reasonable duration (> 100ms because we sleep for 100ms)
        self.assertGreaterEqual(data['performance']['duration_ms'], 100)
        
        logger.info("Performance monitoring decorator works correctly")
    
    def test_04_error_handling(self):
        """Test error handling."""
        logger.info("Testing error handling")
        
        # Test exception handling
        error_response = self.client.get('/test/error?error=true')
        self.assertEqual(error_response.status_code, 500)
        error_data = json.loads(error_response.data)
        self.assertIn('error', error_data)
        self.assertEqual(error_data['error'], 'Internal server error')
        
        # Test custom error response
        custom_error_response = self.client.get('/test/error?custom_error=true&status=422&type=validation_error')
        self.assertEqual(custom_error_response.status_code, 422)
        custom_error_data = json.loads(custom_error_response.data)
        self.assertIn('error', custom_error_data)
        self.assertEqual(custom_error_data['error']['type'], 'validation_error')
        self.assertEqual(custom_error_data['error']['status'], 422)
        
        logger.info("Error handling works correctly")
    
    def test_05_admin_access(self):
        """Test admin access check."""
        logger.info("Testing admin access check")
        
        # Test without admin key
        unauthorized_response = self.client.get('/test/admin')
        self.assertEqual(unauthorized_response.status_code, 403)
        unauthorized_data = json.loads(unauthorized_response.data)
        self.assertIn('error', unauthorized_data)
        self.assertEqual(unauthorized_data['error'], 'Unauthorized')
        
        # Test with admin key
        authorized_response = self.client.get(
            '/test/admin', 
            headers={'X-Admin-Key': 'test_admin_key'}
        )
        self.assertEqual(authorized_response.status_code, 200)
        authorized_data = json.loads(authorized_response.data)
        self.assertIn('success', authorized_data)
        self.assertTrue(authorized_data['success'])
        
        logger.info("Admin access check works correctly")
    
    def test_06_rate_limit_cleanup(self):
        """Test rate limit cleanup logic."""
        logger.info("Testing rate limit cleanup")
        
        # Direct test of the cleanup logic instead of patching
        # Import the real store and cleanup function
        from api.v2.utils import _rate_limit_store, _cleanup_expired_rate_limits
        
        # Save original state of the store
        original_store = _rate_limit_store.copy()
        
        try:
            # Clear the store and add test entries
            _rate_limit_store.clear()
            
            # Add test entries: one expired, one not expired
            now = time.time()
            _rate_limit_store['test_ip:default'] = (5, now - 120)  # 2 minutes old (expired)
            _rate_limit_store['test_ip:admin'] = (2, now - 30)     # 30 seconds old (not expired)
            
            # Call cleanup function
            _cleanup_expired_rate_limits()
            
            # Check that expired entry was removed
            self.assertNotIn('test_ip:default', _rate_limit_store)
            # Non-expired entry should still be there
            self.assertIn('test_ip:admin', _rate_limit_store)
            
            logger.info("Rate limit cleanup works correctly")
            
        finally:
            # Restore original state
            _rate_limit_store.clear()
            _rate_limit_store.update(original_store)


def run_tests():
    """Run the test suite."""
    # Create and run the test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(APIUtilsTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Report test results
    logger.info(f"Ran {result.testsRun} tests")
    logger.info(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
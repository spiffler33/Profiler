"""
Cache Management API Test Script

This script tests the functionality of the cache management API endpoints:
- /api/v2/admin/cache/stats
- /api/v2/admin/cache/entries/{type}
- /api/v2/admin/cache/invalidate
- /api/v2/admin/cache/refresh

Usage: python -m tests.api_fix.cache_api_test
"""

import os
import sys
import json
import time
import unittest
import requests
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class CacheApiTest(unittest.TestCase):
    """Test cases for Cache Management API endpoints"""
    
    BASE_URL = "http://localhost:5432/api/v2/admin/cache"
    
    def setUp(self):
        """Set up test environment"""
        # Make sure test server is running before these tests
        try:
            # Check if server is running by sending a simple request
            response = requests.get("http://localhost:5432/")
            if response.status_code != 200:
                self.skipTest("Server is not running at http://localhost:5432")
        except requests.exceptions.ConnectionError:
            self.skipTest("Server is not running at http://localhost:5432")
    
    def test_01_cache_stats_endpoint(self):
        """Test the cache stats endpoint returns proper structure"""
        print("\n--- Testing /api/v2/admin/cache/stats API ---")
        
        # Make request to stats endpoint
        response = requests.get(f"{self.BASE_URL}/stats")
        
        # Verify response code
        self.assertEqual(response.status_code, 200, f"Expected 200 response, got {response.status_code}")
        
        # Parse response data
        data = response.json()
        print(f"Response data structure: {json.dumps(data, indent=2)[:500]}...")
        
        # Verify response structure
        self.assertIn('version', data, "Response missing 'version' field")
        self.assertIn('timestamp', data, "Response missing 'timestamp' field")
        self.assertIn('caches', data, "Response missing 'caches' field")
        
        # Verify cache data
        caches = data.get('caches', {})
        self.assertIn('monte_carlo', caches, "Response missing 'monte_carlo' cache stats")
        
        # Verify performance data if present
        if 'performance' in data:
            performance = data['performance']
            self.assertIn('hit_rate', performance, "Performance data missing 'hit_rate'")
        
        print("✅ Cache stats endpoint returns proper data structure")
        return data
    
    def test_02_cache_entries_endpoint(self):
        """Test the cache entries endpoint for all types"""
        print("\n--- Testing /api/v2/admin/cache/entries/{type} API ---")
        
        # Test monte_carlo cache type
        response = requests.get(f"{self.BASE_URL}/entries/monte_carlo")
        
        # Verify response code
        self.assertEqual(response.status_code, 200, f"Expected 200 response, got {response.status_code}")
        
        # Parse response data
        entries = response.json()
        print(f"Found {len(entries)} monte_carlo cache entries")
        
        # If entries exist, verify structure
        if entries:
            entry = entries[0]
            expected_fields = ['key', 'created', 'expires', 'size', 'type', 'value_preview']
            for field in expected_fields:
                self.assertIn(field, entry, f"Entry missing '{field}' field")
            
            print(f"Sample entry structure: {json.dumps(entry, indent=2)}")
        
        # Test parameter cache type
        response = requests.get(f"{self.BASE_URL}/entries/parameter")
        self.assertEqual(response.status_code, 200, f"Expected 200 response for parameter cache, got {response.status_code}")
        
        parameter_entries = response.json()
        print(f"Found {len(parameter_entries)} parameter cache entries")
        
        # Test 'all' cache type
        response = requests.get(f"{self.BASE_URL}/entries/all")
        self.assertEqual(response.status_code, 200, f"Expected 200 response for all caches, got {response.status_code}")
        
        all_entries = response.json()
        print(f"Found {len(all_entries)} entries across all caches")
        
        # Test invalid cache type
        response = requests.get(f"{self.BASE_URL}/entries/invalid_type")
        self.assertEqual(response.status_code, 400, f"Expected 400 response for invalid cache type, got {response.status_code}")
        
        print("✅ Cache entries endpoint functions correctly for all cache types")
        return entries
    
    def test_03_cache_invalidate_endpoint(self):
        """Test the cache invalidation endpoint"""
        print("\n--- Testing /api/v2/admin/cache/invalidate API ---")
        
        # First get stats to compare before/after
        before_stats = requests.get(f"{self.BASE_URL}/stats").json()
        if 'caches' not in before_stats or 'monte_carlo' not in before_stats['caches']:
            self.skipTest("Cache stats endpoint not returning proper data for comparison")
        
        monte_carlo_before = before_stats['caches']['monte_carlo']
        print(f"Monte Carlo cache size before: {monte_carlo_before.get('size', 'N/A')}")
        
        # Populate cache with a test entry if needed
        self._populate_test_cache_entry()
        
        # Get all monte carlo entries before invalidation
        entries_before = requests.get(f"{self.BASE_URL}/entries/monte_carlo").json()
        
        # Test invalid request (no cache type)
        response = requests.post(f"{self.BASE_URL}/invalidate", json={})
        self.assertEqual(response.status_code, 400, "Expected 400 response for missing cache type")
        
        # If there are entries, test invalidating a specific entry
        test_key = None
        if entries_before:
            test_key = entries_before[0]['key']
            print(f"Testing invalidation of specific key: {test_key}")
            
            response = requests.post(f"{self.BASE_URL}/invalidate", 
                                   json={"type": "monte_carlo", "key": test_key})
            
            self.assertEqual(response.status_code, 200, f"Expected 200 response, got {response.status_code}")
            
            result = response.json()
            self.assertTrue(result.get('success', False), "Invalidation request failed")
            print(f"Invalidation result: {result}")
            
            # Verify entry was removed
            entries_after = requests.get(f"{self.BASE_URL}/entries/monte_carlo").json()
            keys_after = [e['key'] for e in entries_after]
            self.assertNotIn(test_key, keys_after, "Entry was not properly invalidated")
        
        # Test pattern-based invalidation
        response = requests.post(f"{self.BASE_URL}/invalidate", 
                               json={"type": "monte_carlo", "pattern": "test"})
        
        self.assertEqual(response.status_code, 200, f"Expected 200 response, got {response.status_code}")
        
        # Test complete invalidation of monte carlo cache
        response = requests.post(f"{self.BASE_URL}/invalidate", 
                               json={"type": "monte_carlo"})
        
        self.assertEqual(response.status_code, 200, f"Expected 200 response, got {response.status_code}")
        
        # Get stats after invalidation
        after_stats = requests.get(f"{self.BASE_URL}/stats").json()
        monte_carlo_after = after_stats['caches']['monte_carlo']
        print(f"Monte Carlo cache size after: {monte_carlo_after.get('size', 'N/A')}")
        
        print("✅ Cache invalidation endpoint functions correctly")
    
    def test_04_cache_refresh_endpoint(self):
        """Test the cache refresh endpoint"""
        print("\n--- Testing /api/v2/admin/cache/refresh API ---")
        
        # First invalidate all caches to start fresh
        requests.post(f"{self.BASE_URL}/invalidate", json={"type": "all"})
        
        # Populate cache with a test entry
        self._populate_test_cache_entry()
        
        # Call the refresh endpoint
        response = requests.post(f"{self.BASE_URL}/refresh")
        
        # Verify response code
        self.assertEqual(response.status_code, 200, f"Expected 200 response, got {response.status_code}")
        
        # Parse response data
        result = response.json()
        print(f"Refresh result: {result}")
        
        # Verify success
        self.assertTrue(result.get('success', False), "Cache refresh request failed")
        
        print("✅ Cache refresh endpoint functions correctly")
    
    def _populate_test_cache_entry(self):
        """Helper method to populate a test cache entry if needed"""
        # This is a bit of a hack, but we'll just use monte_carlo/simulation.py 
        # to populate the cache with a test entry
        try:
            # Import monte_carlo simulation module
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from models.monte_carlo.cache import _cache
            
            # Add a test entry
            test_key = f"test_key_{int(time.time())}"
            test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
            _cache.set(test_key, test_value)
            
            print(f"Added test cache entry with key: {test_key}")
        except Exception as e:
            print(f"Warning: Could not populate test cache entry: {e}")

if __name__ == "__main__":
    print("Starting Cache Management API Tests")
    print("Note: Make sure the Flask application is running")
    print("      before executing these tests (python app.py)")
    print("=" * 70)
    
    test_loader = unittest.TestLoader()
    test_loader.sortTestMethodsUsing = lambda x, y: (
        1 if x.split('_')[1] > y.split('_')[1] else
        -1 if x.split('_')[1] < y.split('_')[1] else 0
    )
    
    test_suite = test_loader.loadTestsFromTestCase(CacheApiTest)
    unittest.TextTestRunner(verbosity=2).run(test_suite)
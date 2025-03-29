"""
Manual API Test Script

This script provides a command-line interface for testing API endpoints,
particularly the Cache Management API endpoints.

Usage: python -m tests.api_fix.api_test_manual [command]

Commands:
  stats               - Test /api/v2/admin/cache/stats
  entries <type>      - Test /api/v2/admin/cache/entries/{type} (monte_carlo, parameter, all)
  invalidate <type>   - Test /api/v2/admin/cache/invalidate with type
  invalidate_key <t> <k> - Test invalidating a specific key in cache type
  refresh             - Test /api/v2/admin/cache/refresh
  all                 - Run all tests in sequence
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class ApiTester:
    """API testing utility class"""
    
    def __init__(self, base_url="http://localhost:5432"):
        self.base_url = base_url
        self.auth = None
    
    def test_connection(self):
        """Test if the server is reachable"""
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                print("✅ Server is running")
                return True
            else:
                print(f"❌ Server returned status code {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to server at {self.base_url}")
            return False
    
    def test_cache_stats(self):
        """Test the cache stats endpoint"""
        print("\n=== Testing Cache Stats API ===")
        
        try:
            response = requests.get(f"{self.base_url}/api/v2/admin/cache/stats")
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2)[:1000] + "..." if len(json.dumps(data)) > 1000 else json.dumps(data, indent=2))
            
            if 'caches' in data and 'monte_carlo' in data['caches']:
                mc_stats = data['caches']['monte_carlo']
                print(f"\nMonte Carlo Cache Stats:")
                print(f"- Size: {mc_stats.get('size', 'N/A')}")
                print(f"- Hits: {mc_stats.get('hits', 'N/A')}")
                print(f"- Misses: {mc_stats.get('misses', 'N/A')}")
                print(f"- Hit Rate: {mc_stats.get('hit_rate', 'N/A')}")
            
            print("\n✅ Cache stats endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing cache stats: {e}")
            return False
    
    def test_cache_entries(self, cache_type="monte_carlo"):
        """Test the cache entries endpoint"""
        print(f"\n=== Testing Cache Entries API for {cache_type} ===")
        
        try:
            response = requests.get(f"{self.base_url}/api/v2/admin/cache/entries/{cache_type}")
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            entries = response.json()
            print(f"Found {len(entries)} entries")
            
            if entries:
                print("\nSample Entry:")
                print(json.dumps(entries[0], indent=2))
                
                # Print just the keys for all entries
                print("\nAll Entry Keys:")
                for entry in entries:
                    print(f"- {entry.get('key', 'N/A')}")
            
            print("\n✅ Cache entries endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing cache entries: {e}")
            return False
    
    def test_cache_invalidate(self, cache_type="monte_carlo", key=None, pattern=None):
        """Test the cache invalidation endpoint"""
        print(f"\n=== Testing Cache Invalidate API ===")
        print(f"Type: {cache_type}" + (f", Key: {key}" if key else "") + (f", Pattern: {pattern}" if pattern else ""))
        
        try:
            # Prepare request data
            data = {"type": cache_type}
            if key:
                data["key"] = key
            if pattern:
                data["pattern"] = pattern
            
            # Get stats before
            before_response = requests.get(f"{self.base_url}/api/v2/admin/cache/stats")
            if before_response.status_code == 200:
                before_stats = before_response.json()
                if 'caches' in before_stats and cache_type in before_stats['caches']:
                    before_size = before_stats['caches'][cache_type].get('size', 'N/A')
                    print(f"Cache size before: {before_size}")
            
            # Send invalidation request
            response = requests.post(
                f"{self.base_url}/api/v2/admin/cache/invalidate",
                json=data
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Get stats after
            after_response = requests.get(f"{self.base_url}/api/v2/admin/cache/stats")
            if after_response.status_code == 200:
                after_stats = after_response.json()
                if 'caches' in after_stats and cache_type in after_stats['caches']:
                    after_size = after_stats['caches'][cache_type].get('size', 'N/A')
                    print(f"Cache size after: {after_size}")
            
            print("\n✅ Cache invalidation endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing cache invalidation: {e}")
            return False
    
    def test_cache_refresh(self):
        """Test the cache refresh endpoint"""
        print(f"\n=== Testing Cache Refresh API ===")
        
        try:
            response = requests.post(f"{self.base_url}/api/v2/admin/cache/refresh")
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            print("\n✅ Cache refresh endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing cache refresh: {e}")
            return False
    
    def populate_test_cache(self):
        """Populate the cache with test data for testing"""
        print("\n=== Populating Cache with Test Data ===")
        
        try:
            # Import monte carlo cache module
            from models.monte_carlo.cache import _cache
            
            # Add some test entries
            num_entries = 5
            for i in range(num_entries):
                key = f"test_key_{i}_{int(time.time())}"
                value = {
                    "test": f"data_{i}",
                    "timestamp": datetime.now().isoformat(),
                    "random_value": hash(key) % 10000
                }
                _cache.set(key, value)
                print(f"Added test entry: {key}")
            
            print(f"✅ Added {num_entries} test entries to cache")
            return True
            
        except Exception as e:
            print(f"❌ Error populating cache: {e}")
            print("Make sure you're running this from the project root directory")
            return False

def main():
    """Main function to handle command-line arguments"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    tester = ApiTester()
    
    if not tester.test_connection():
        print("Please make sure the Flask server is running (python app.py)")
        return
    
    command = sys.argv[1]
    
    if command == "stats":
        tester.test_cache_stats()
    
    elif command == "entries":
        cache_type = "monte_carlo"
        if len(sys.argv) > 2:
            cache_type = sys.argv[2]
        tester.test_cache_entries(cache_type)
    
    elif command == "invalidate":
        cache_type = "monte_carlo"
        if len(sys.argv) > 2:
            cache_type = sys.argv[2]
        tester.test_cache_invalidate(cache_type)
    
    elif command == "invalidate_key":
        if len(sys.argv) < 4:
            print("Usage: invalidate_key <cache_type> <key>")
            return
        cache_type = sys.argv[2]
        key = sys.argv[3]
        tester.test_cache_invalidate(cache_type, key=key)
    
    elif command == "invalidate_pattern":
        if len(sys.argv) < 4:
            print("Usage: invalidate_pattern <cache_type> <pattern>")
            return
        cache_type = sys.argv[2]
        pattern = sys.argv[3]
        tester.test_cache_invalidate(cache_type, pattern=pattern)
    
    elif command == "refresh":
        tester.test_cache_refresh()
    
    elif command == "populate":
        tester.populate_test_cache()
    
    elif command == "all":
        # Populate cache first
        tester.populate_test_cache()
        
        # Run all tests
        tester.test_cache_stats()
        tester.test_cache_entries("monte_carlo")
        tester.test_cache_entries("parameter")
        tester.test_cache_entries("all")
        
        # Test pattern invalidation
        tester.test_cache_invalidate("monte_carlo", pattern="test")
        
        # Test cache refresh
        tester.test_cache_refresh()
        
        # Test complete invalidation
        tester.test_cache_invalidate("monte_carlo")
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()
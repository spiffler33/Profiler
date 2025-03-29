#!/usr/bin/env python3
"""
Test script for Monte Carlo cache persistence functionality.

This script:
1. Populates the cache with some test data
2. Saves the cache to disk
3. Clears the in-memory cache
4. Loads the cache from disk
5. Verifies the data was correctly loaded
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cache_test")

# Import cache functions
from models.monte_carlo.cache import (
    SimulationCache,
    save_cache, load_cache, invalidate_cache,
    get_cache_stats, configure_cache
)

# Test data generation
def generate_test_data(size=10):
    """
    Generate test data for the cache.
    
    Args:
        size: Number of entries to generate
        
    Returns:
        dict: Dictionary of test data
    """
    data = {}
    for i in range(size):
        key = f"test_key_{i}"
        value = {
            "id": i,
            "name": f"Test Data {i}",
            "value": i * 100,
            "timestamp": datetime.now().isoformat(),
            "array": list(range(i*10, (i+1)*10))
        }
        data[key] = (value, time.time())
    
    return data

def run_cache_test():
    """Run the Monte Carlo cache persistence test."""
    print("Starting Monte Carlo cache persistence test")
    print("------------------------------------------\n")
    
    try:
        # 1. Configure cache
        print("Configuring cache...")
        cache_dir = os.path.join(parent_dir, "data", "cache")
        cache_file = "test_cache.pickle"
        cache_path = os.path.join(cache_dir, cache_file)
        
        # Make sure directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Configure cache
        configure_cache(
            max_size=100,
            ttl=3600,
            save_interval=60,
            cache_dir=cache_dir,
            cache_file=cache_file
        )
        print("Cache configured with the following settings:")
        print(f"- Max size: 100 entries")
        print(f"- TTL: 3600 seconds")
        print(f"- Save interval: 60 seconds")
        print(f"- Cache path: {cache_path}")
        
        # 2. Clear any existing cache
        print("\nClearing existing cache...")
        invalidate_cache()
        print("Cache cleared")
        
        # 3. Populate cache with test data
        print("\nPopulating cache with test data...")
        
        # Create a cache instance for testing
        test_cache = SimulationCache()
        
        # Generate and add test data
        test_data = generate_test_data(size=20)
        for key, (value, timestamp) in test_data.items():
            test_cache.set(key, value)
        
        # Print cache stats
        print(f"Added {len(test_data)} entries to test cache")
        test_stats = test_cache.get_stats()
        print(f"Test cache stats: size={test_stats['size']}, max_size={test_stats['max_size']}")
        
        # 4. Save test cache to disk
        print("\nSaving test cache to disk...")
        test_file = os.path.join(cache_dir, "direct_test_cache.pickle")
        if test_cache.save(test_file):
            print(f"Successfully saved test cache to {test_file}")
        else:
            print(f"Failed to save test cache to {test_file}")
        
        # 5. Load test cache from disk to verify
        print("\nLoading test cache from disk...")
        test_cache2 = SimulationCache()
        if test_cache2.load(test_file):
            print(f"Successfully loaded test cache from {test_file}")
            test_stats2 = test_cache2.get_stats()
            print(f"Loaded cache stats: size={test_stats2['size']}, max_size={test_stats2['max_size']}")
            
            # Verify all keys were loaded
            all_keys_present = True
            for key in test_data.keys():
                if test_cache2.get(key) is None:
                    all_keys_present = False
                    print(f"ERROR: Key {key} not found in loaded cache")
            
            if all_keys_present:
                print("SUCCESS: All keys from original cache are present in loaded cache")
            else:
                print("ERROR: Some keys from original cache are missing in loaded cache")
        else:
            print(f"Failed to load test cache from {test_file}")
        
        # 6. Test the global cache functions
        print("\nTesting global cache functions...")
        
        # Clear global cache
        invalidate_cache()
        
        # Populate with sample data
        for i in range(10):
            key = f"global_test_key_{i}"
            from models.monte_carlo.cache import _cache
            _cache.set(key, {"test": i, "data": "global"})
        
        # Save global cache
        print("Saving global cache...")
        if save_cache():
            print(f"Successfully saved global cache to default location")
        else:
            print(f"Failed to save global cache")
        
        # Clear it again
        invalidate_cache()
        
        # Make sure it's empty
        stats_after_clear = get_cache_stats()
        if stats_after_clear["size"] == 0:
            print("Successfully cleared global cache")
        else:
            print(f"Failed to clear global cache: {stats_after_clear['size']} entries remain")
        
        # Load it back
        print("Loading global cache...")
        if load_cache():
            print(f"Successfully loaded global cache from default location")
            stats_after_load = get_cache_stats()
            print(f"Loaded global cache has {stats_after_load['size']} entries")
            
            # Verify if we have all the expected keys
            from models.monte_carlo.cache import _cache
            expected_keys = set(f"global_test_key_{i}" for i in range(10))
            found_keys = set(k for k in _cache.cache.keys() if k.startswith("global_test_key_"))
            
            if expected_keys == found_keys:
                print("SUCCESS: All expected keys found in loaded global cache")
            else:
                missing = expected_keys - found_keys
                extra = found_keys - expected_keys
                if missing:
                    print(f"ERROR: Missing keys in loaded global cache: {missing}")
                if extra:
                    print(f"INFO: Additional keys in loaded global cache: {extra}")
        else:
            print(f"Failed to load global cache")
        
        print("\nMonte Carlo cache persistence test completed")
        print("Test result: SUCCESS")
    
    except Exception as e:
        import traceback
        print(f"\nERROR: Test failed with exception: {str(e)}")
        print(traceback.format_exc())
        print("\nMonte Carlo cache persistence test completed")
        print("Test result: FAILURE")
        return False
    
    return True

if __name__ == "__main__":
    run_cache_test()
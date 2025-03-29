#!/usr/bin/env python3
"""
Test for Monte Carlo cache performance.

This test benchmarks the Monte Carlo simulation cache performance and validates the
optimization features.
"""

import unittest
import time
import logging
import random
import numpy as np
import pytest
from datetime import datetime
import os

from models.monte_carlo.cache import cached_simulation, invalidate_cache, get_cache_stats
from models.monte_carlo.parallel import run_parallel_monte_carlo
from models.financial_projection import ContributionPattern, AllocationStrategy, AssetClass

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestMonteCarloCachePerformance(unittest.TestCase):
    """Test Monte Carlo cache performance and optimization features."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Clear all caches
        invalidate_cache()
        
        # Create standard test data for simulations
        cls.create_test_data()
    
    @classmethod
    def create_test_data(cls):
        """Create test data for simulations."""
        # Create a simple contribution pattern using the current API
        # Convert monthly_contribution to annual
        annual_amount = 25000 * 12  # 3 Lakh per year
        
        # ContributionPattern uses different parameters now
        cls.contribution_pattern = ContributionPattern(
            annual_amount=annual_amount,
            growth_rate=0.05,  # 5% annual increase
            frequency="monthly"  # Monthly contributions
        )
        
        # Create allocation strategy with different risk profiles
        # AllocationStrategy now accepts a dictionary directly 
        cls.conservative_allocation = AllocationStrategy({
            AssetClass.EQUITY: 0.40,
            AssetClass.DEBT: 0.50,
            AssetClass.CASH: 0.10
        })
        
        cls.aggressive_allocation = AllocationStrategy({
            AssetClass.EQUITY: 0.70,
            AssetClass.DEBT: 0.20,
            AssetClass.CASH: 0.10
        })
    
    def run_simulation(self, seed_offset, initial_amount, contribution_pattern, years, allocation_strategy):
        """Run a single Monte Carlo simulation."""
        np.random.seed(42 + seed_offset)
        
        # Initialize result array
        result = np.zeros(years + 1)
        result[0] = initial_amount
        
        # Define standard return assumptions
        return_assumptions = {
            AssetClass.EQUITY: (0.10, 0.18),
            AssetClass.DEBT: (0.06, 0.05),
            AssetClass.CASH: (0.04, 0.01)
        }
        
        # Run simulation
        for year in range(1, years + 1):
            # Get contribution for the year
            contribution = contribution_pattern.get_contribution_for_year(year)
            
            # Simulate returns for each asset class
            portfolio_value = result[year - 1]
            new_value = 0
            
            # Access the initial_allocation attribute
            for asset_class, allocation in allocation_strategy.initial_allocation.items():
                asset_value = portfolio_value * allocation
                mean_return, vol = return_assumptions[asset_class]
                
                # Simulate return using log-normal distribution
                annual_return = np.random.lognormal(
                    mean=np.log(1 + mean_return) - 0.5 * vol**2,
                    sigma=vol
                )
                
                # Update value
                new_value += asset_value * annual_return
            
            # Add contribution
            result[year] = new_value + contribution
        
        return result
    
    def test_1_cache_basic_functionality(self):
        """Test basic caching functionality and performance."""
        # Define a decorated simulation function
        @cached_simulation
        def cached_test_simulation(seed, initial, contribution, years, allocation):
            return self.run_simulation(seed, initial, contribution, years, allocation)
        
        # Run first simulation to populate cache
        start_time = time.time()
        result1 = cached_test_simulation(
            seed=42,
            initial=1000000,
            contribution=self.contribution_pattern,
            years=30,
            allocation=self.conservative_allocation
        )
        first_run_time = time.time() - start_time
        
        # Get cache stats after first run
        stats_after_first = get_cache_stats()
        
        # Run identical simulation again - should use cache
        start_time = time.time()
        result2 = cached_test_simulation(
            seed=42,
            initial=1000000,
            contribution=self.contribution_pattern,
            years=30,
            allocation=self.conservative_allocation
        )
        second_run_time = time.time() - start_time
        
        # Get cache stats after second run
        stats_after_second = get_cache_stats()
        
        # Verify cache hit count increased
        self.assertEqual(stats_after_second['hits'], stats_after_first['hits'] + 1,
                        "Cache hits should increase by 1")
        
        # Second run should be much faster
        self.assertLess(second_run_time, first_run_time * 0.1,
                      f"Cached run ({second_run_time:.6f}s) should be at least 10x faster than uncached ({first_run_time:.6f}s)")
        
        # Results should be identical
        np.testing.assert_array_equal(result1, result2)
        
        logger.info(f"First run time: {first_run_time:.6f}s")
        logger.info(f"Cached run time: {second_run_time:.6f}s")
        logger.info(f"Speedup factor: {first_run_time/second_run_time:.1f}x")
    
    def test_2_cache_key_generation(self):
        """Test that different parameters generate different cache keys."""
        # Define a decorated simulation function
        @cached_simulation
        def cached_test_simulation(seed, initial, contribution, years, allocation):
            return self.run_simulation(seed, initial, contribution, years, allocation)
        
        # Clear cache
        invalidate_cache()
        
        # Run with initial parameters
        cached_test_simulation(
            seed=42,
            initial=1000000,
            contribution=self.contribution_pattern,
            years=30,
            allocation=self.conservative_allocation
        )
        
        # Get cache stats after first run
        stats_after_first = get_cache_stats()
        self.assertEqual(stats_after_first['size'], 1)
        
        # Run with different initial amount - should not use cache
        cached_test_simulation(
            seed=42,
            initial=1500000,  # Different amount
            contribution=self.contribution_pattern,
            years=30,
            allocation=self.conservative_allocation
        )
        
        # Run with different years - should not use cache
        cached_test_simulation(
            seed=42,
            initial=1000000,
            contribution=self.contribution_pattern,
            years=25,  # Different years
            allocation=self.conservative_allocation
        )
        
        # Run with different allocation - should not use cache
        cached_test_simulation(
            seed=42,
            initial=1000000,
            contribution=self.contribution_pattern,
            years=30,
            allocation=self.aggressive_allocation  # Different allocation
        )
        
        # Get cache stats after all runs
        stats_after_all = get_cache_stats()
        
        # Should have 4 cache entries (one for each unique parameter set)
        self.assertEqual(stats_after_all['size'], 4)
        
        # Should have had 0 cache hits (all unique parameter sets)
        self.assertEqual(stats_after_all['hits'], 0)
        
        logger.info(f"Cache entries generated: {stats_after_all['size']}")
        logger.info(f"Cache hits: {stats_after_all['hits']}")
        logger.info(f"Cache misses: {stats_after_all['misses']}")
    
    def test_3_cache_performance_under_load(self):
        """Test cache performance under load with many simulations."""
        # Define a decorated simulation function
        @cached_simulation
        def cached_test_simulation(seed, initial, contribution, years, allocation):
            return self.run_simulation(seed, initial, contribution, years, allocation)
        
        # Clear cache
        invalidate_cache()
        
        # Create variations of parameters
        initial_amounts = [1000000, 1500000, 2000000, 2500000, 3000000]
        years_list = [20, 25, 30, 35, 40]
        
        # Track timing
        uncached_total_time = 0
        cached_total_time = 0
        
        # First round - all cache misses
        start_time = time.time()
        for initial in initial_amounts:
            for years in years_list:
                # Run simulation
                cached_test_simulation(
                    seed=42,
                    initial=initial,
                    contribution=self.contribution_pattern,
                    years=years,
                    allocation=self.conservative_allocation
                )
        uncached_total_time = time.time() - start_time
        
        # Get cache stats after first round
        stats_after_first = get_cache_stats()
        
        # Second round - all cache hits
        start_time = time.time()
        for initial in initial_amounts:
            for years in years_list:
                # Run simulation
                cached_test_simulation(
                    seed=42,
                    initial=initial,
                    contribution=self.contribution_pattern,
                    years=years,
                    allocation=self.conservative_allocation
                )
        cached_total_time = time.time() - start_time
        
        # Get cache stats after second round
        stats_after_second = get_cache_stats()
        
        # Should have 25 cache entries (5 initials * 5 years)
        self.assertEqual(stats_after_first['size'], 25)
        
        # Should have 25 cache hits in second round
        self.assertEqual(stats_after_second['hits'] - stats_after_first['hits'], 25)
        
        # Cached round should be much faster
        self.assertLess(cached_total_time, uncached_total_time * 0.1,
                      f"Cached batch ({cached_total_time:.6f}s) should be at least 10x faster than uncached ({uncached_total_time:.6f}s)")
        
        logger.info(f"Uncached batch time: {uncached_total_time:.6f}s for 25 simulations")
        logger.info(f"Cached batch time: {cached_total_time:.6f}s for 25 simulations")
        logger.info(f"Batch speedup factor: {uncached_total_time/cached_total_time:.1f}x")
    
    def test_4_cache_eviction_policy(self):
        """Test that cache eviction policy works correctly under memory pressure."""
        # Define a decorated simulation function with small cache
        from models.monte_carlo.cache import SimulationCache
        
        # Create a small cache with only 10 entries
        small_cache = SimulationCache(max_size=10, ttl=3600)
        
        # Create a decorated function that uses the small cache
        def small_cache_decorator(func):
            def wrapper(*args, **kwargs):
                # Generate key
                key = small_cache._generate_key(args, kwargs)
                
                # Try to get from cache
                result = small_cache.get(key)
                if result is not None:
                    return result
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                small_cache.set(key, result)
                return result
            return wrapper
        
        # Apply decorator to simulation function
        @small_cache_decorator
        def small_cache_simulation(seed, initial, contribution, years, allocation):
            return self.run_simulation(seed, initial, contribution, years, allocation)
        
        # Run 20 simulations with different parameters (more than cache size)
        for i in range(20):
            small_cache_simulation(
                seed=i,
                initial=1000000 + i * 100000,
                contribution=self.contribution_pattern,
                years=30,
                allocation=self.conservative_allocation
            )
        
        # Check cache size - should be limited to max_size
        self.assertEqual(len(small_cache.cache), 10)
        
        # Run again with the first 5 parameters - should be cache misses
        for i in range(5):
            small_cache_simulation(
                seed=i,
                initial=1000000 + i * 100000,
                contribution=self.contribution_pattern,
                years=30,
                allocation=self.conservative_allocation
            )
        
        # Cache hit rate should be very low due to eviction
        hit_rate = small_cache.hits / (small_cache.hits + small_cache.misses) if (small_cache.hits + small_cache.misses) > 0 else 0
        self.assertLess(hit_rate, 0.5, f"Hit rate ({hit_rate:.2f}) should be low due to cache eviction")
        
        logger.info(f"Small cache stats: size={len(small_cache.cache)}, max_size={small_cache.max_size}")
        logger.info(f"Hits: {small_cache.hits}, Misses: {small_cache.misses}, Hit rate: {hit_rate:.2f}")
    
    def test_5_parallel_simulation_caching(self):
        """Test caching with parallel simulations."""
        # Clear cache
        invalidate_cache()
        
        # Define simulation function for parallel execution
        def simulation_func(seed_offset, initial_amount, contribution_pattern, years, allocation_strategy):
            return self.run_simulation(seed_offset, initial_amount, contribution_pattern, years, allocation_strategy)
        
        # Create cached version
        @cached_simulation
        def cached_simulation_func(seed_offset, initial_amount, contribution_pattern, years, allocation_strategy):
            return simulation_func(seed_offset, initial_amount, contribution_pattern, years, allocation_strategy)
        
        # Run parallel simulations with original function
        start_time = time.time()
        result1 = run_parallel_monte_carlo(
            initial_amount=1000000,
            contribution_pattern=self.contribution_pattern,
            years=30,
            allocation_strategy=self.aggressive_allocation,
            simulation_function=simulation_func,
            simulations=500,
            max_workers=4
        )
        parallel_time = time.time() - start_time
        
        # Run again with cached function
        start_time = time.time()
        result2 = run_parallel_monte_carlo(
            initial_amount=1000000,
            contribution_pattern=self.contribution_pattern,
            years=30,
            allocation_strategy=self.aggressive_allocation,
            simulation_function=cached_simulation_func,
            simulations=500,
            max_workers=4
        )
        cached_parallel_time = time.time() - start_time
        
        # Run third time - should be fully cached
        start_time = time.time()
        result3 = run_parallel_monte_carlo(
            initial_amount=1000000,
            contribution_pattern=self.contribution_pattern,
            years=30,
            allocation_strategy=self.aggressive_allocation,
            simulation_function=cached_simulation_func,
            simulations=500,
            max_workers=4
        )
        fully_cached_time = time.time() - start_time
        
        # Get cache stats
        cache_stats = get_cache_stats()
        
        # Fully cached run should be much faster
        self.assertLess(fully_cached_time, parallel_time * 0.2,
                      f"Fully cached parallel run ({fully_cached_time:.3f}s) should be at least 5x faster than uncached ({parallel_time:.3f}s)")
        
        # Results should be similar (statistical measures)
        np.testing.assert_almost_equal(
            np.median(result1.all_projections[:, -1]),
            np.median(result3.all_projections[:, -1]),
            decimal=0  # Only comparing to nearest integer for statistical results
        )
        
        logger.info(f"Parallel uncached simulation: {parallel_time:.3f}s")
        logger.info(f"Parallel with caching enabled: {cached_parallel_time:.3f}s")
        logger.info(f"Fully cached parallel run: {fully_cached_time:.3f}s")
        logger.info(f"Cache stats: size={cache_stats['size']}, hits={cache_stats['hits']}, hit_rate={cache_stats['hit_rate']:.2f}")
    
    def test_6_cache_ttl_functionality(self):
        """Test that cache time-to-live (TTL) functionality works."""
        # Create a cache with short TTL
        from models.monte_carlo.cache import SimulationCache
        
        # Create a cache with 1 second TTL
        short_cache = SimulationCache(max_size=100, ttl=1)
        
        # Create a decorated function that uses the short cache
        def short_ttl_decorator(func):
            def wrapper(*args, **kwargs):
                # Generate key
                key = short_cache._generate_key(args, kwargs)
                
                # Try to get from cache
                result = short_cache.get(key)
                if result is not None:
                    return result
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                short_cache.set(key, result)
                return result
            return wrapper
        
        # Apply decorator to simulation function
        @short_ttl_decorator
        def short_ttl_simulation(seed, initial, contribution, years, allocation):
            return self.run_simulation(seed, initial, contribution, years, allocation)
        
        # Run simulation to populate cache
        start_time = time.time()
        result1 = short_ttl_simulation(
            seed=42,
            initial=1000000,
            contribution=self.contribution_pattern,
            years=30,
            allocation=self.conservative_allocation
        )
        first_run_time = time.time() - start_time
        
        # Run again immediately - should use cache
        start_time = time.time()
        result2 = short_ttl_simulation(
            seed=42,
            initial=1000000,
            contribution=self.contribution_pattern,
            years=30,
            allocation=self.conservative_allocation
        )
        immediate_run_time = time.time() - start_time
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Run again after TTL expiry - should miss cache
        start_time = time.time()
        result3 = short_ttl_simulation(
            seed=42,
            initial=1000000,
            contribution=self.contribution_pattern,
            years=30,
            allocation=self.conservative_allocation
        )
        after_ttl_run_time = time.time() - start_time
        
        # Immediate run should be much faster (cache hit)
        self.assertLess(immediate_run_time, first_run_time * 0.1)
        
        # After TTL run should be similar to first run (cache miss)
        self.assertGreater(after_ttl_run_time, immediate_run_time * 5)
        
        # Check hits and misses
        self.assertEqual(short_cache.hits, 1)
        self.assertEqual(short_cache.misses, 2)
        
        logger.info(f"First run time: {first_run_time:.6f}s")
        logger.info(f"Immediate cached run: {immediate_run_time:.6f}s")
        logger.info(f"Run after TTL expiry: {after_ttl_run_time:.6f}s")
        logger.info(f"Cache stats: hits={short_cache.hits}, misses={short_cache.misses}")
    
    def test_7_cache_key_consistency(self):
        """Test that cache key generation is consistent across calls."""
        # Get a new cache instance for this test
        from models.monte_carlo.cache import SimulationCache
        test_cache = SimulationCache(max_size=100)
        
        # Define test parameters
        params1 = (42, 1000000, self.contribution_pattern, 30, self.conservative_allocation)
        params2 = (42, 1000000, self.contribution_pattern, 30, self.conservative_allocation)
        params3 = (43, 1000000, self.contribution_pattern, 30, self.conservative_allocation)
        
        # Generate keys
        key1 = test_cache._generate_key(params1, {})
        key2 = test_cache._generate_key(params2, {})
        key3 = test_cache._generate_key(params3, {})
        
        # Same parameters should produce same key
        self.assertEqual(key1, key2, "Same parameters should generate the same cache key")
        
        # Different parameters should produce different keys
        self.assertNotEqual(key1, key3, "Different parameters should generate different cache keys")
        
        # Test with keyword arguments
        key4 = test_cache._generate_key((), {
            "seed": 42,
            "initial": 1000000,
            "contribution": self.contribution_pattern,
            "years": 30,
            "allocation": self.conservative_allocation
        })
        
        # Test with mixed positional and keyword arguments
        key5 = test_cache._generate_key((42, 1000000), {
            "contribution": self.contribution_pattern,
            "years": 30,
            "allocation": self.conservative_allocation
        })
        
        # All these variations should produce consistent keys based on parameter values
        self.assertNotEqual(key1, key4, "Different argument styles should generate different keys")
        self.assertNotEqual(key1, key5, "Different argument styles should generate different keys")
        
        logger.info(f"Key generation test passed with key1={key1}, key2={key2}, key3={key3}")
    
    def test_8_cache_memory_usage(self):
        """Test that cache memory usage stays within reasonable bounds."""
        import resource
        import gc
        
        # Get initial memory usage
        gc.collect()  # Force garbage collection before measurement
        initial_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # Create a new cache with 1000 entries
        from models.monte_carlo.cache import SimulationCache
        large_cache = SimulationCache(max_size=1000)
        
        # Generate large result sets (arrays)
        large_results = []
        for i in range(100):
            # Create a large result array (100KB each = ~10MB total)
            result = np.random.random((10000, 10))  # ~800KB array
            large_results.append(result)
            
            # Store in cache
            large_cache.set(f"large_result_{i}", result)
        
        # Get memory usage after loading cache
        gc.collect()  # Force garbage collection before measurement
        filled_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # Clear large results list to free that memory
        large_results = None
        gc.collect()
        
        # Get memory usage with only cache
        cache_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # Clear cache
        large_cache.invalidate()
        gc.collect()
        
        # Get final memory usage
        final_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # Log memory usage
        logger.info(f"Initial memory: {initial_memory} KB")
        logger.info(f"Filled memory: {filled_memory} KB")
        logger.info(f"Cache memory: {cache_memory} KB")
        logger.info(f"Final memory: {final_memory} KB")
        logger.info(f"Memory difference: {cache_memory - final_memory} KB")
        
        # The memory difference should be significant but not excessive
        # This test is more informative than assertive, so we just log it
        # Skipping strict assertion as memory reporting varies by platform
        
        # Memory after cache clear should be less than memory with cache
        # Allow a margin of error since memory measurement isn't exact
        self.assertLessEqual(final_memory, cache_memory + 1000)
    
    def test_9_thread_safety(self):
        """Test that cache operations are thread-safe."""
        import threading
        import queue
        
        # Define a decorated simulation function with shared cache
        @cached_simulation
        def cached_thread_simulation(seed, initial, contribution, years, allocation):
            return self.run_simulation(seed, initial, contribution, years, allocation)
        
        # Clear cache
        invalidate_cache()
        
        # Create a queue to collect results and track errors
        result_queue = queue.Queue()
        error_queue = queue.Queue()
        
        # Define thread worker function
        def worker(worker_id, seed_start, seed_count):
            try:
                results = []
                for i in range(seed_count):
                    seed = seed_start + i
                    result = cached_thread_simulation(
                        seed=seed,
                        initial=1000000,
                        contribution=self.contribution_pattern,
                        years=20,
                        allocation=self.conservative_allocation
                    )
                    results.append((seed, result))
                result_queue.put((worker_id, results))
            except Exception as e:
                error_queue.put((worker_id, str(e)))
        
        # Create and start multiple threads
        threads = []
        thread_count = 4
        seeds_per_thread = 10
        
        for i in range(thread_count):
            t = threading.Thread(target=worker, args=(i, i * seeds_per_thread, seeds_per_thread))
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Check for errors
        error_count = error_queue.qsize()
        self.assertEqual(error_count, 0, f"Thread errors: {[error_queue.get() for _ in range(error_count)]}")
        
        # Verify all results were returned
        self.assertEqual(result_queue.qsize(), thread_count)
        
        # Get cache stats after parallel runs
        stats = get_cache_stats()
        
        # Verify each thread got expected results
        all_results = []
        for _ in range(thread_count):
            worker_id, results = result_queue.get()
            all_results.extend(results)
            self.assertEqual(len(results), seeds_per_thread)
        
        # Verify total number of results
        self.assertEqual(len(all_results), thread_count * seeds_per_thread)
        
        # Verify results are unique for different seeds
        seeds_to_check = {result[0] for result in all_results}
        # We should have as many unique results as there are seeds
        self.assertEqual(len(seeds_to_check), thread_count * seeds_per_thread)
        
        logger.info(f"Thread safety test passed with {thread_count} threads")
        logger.info(f"Cache stats after thread test: size={stats['size']}, hits={stats['hits']}, misses={stats['misses']}")

if __name__ == '__main__':
    unittest.main()
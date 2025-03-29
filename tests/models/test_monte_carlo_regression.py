"""
Tests for detecting Monte Carlo simulation performance regressions.

This test suite is designed to catch performance regressions by comparing
current performance against established baselines.
"""

import unittest
import numpy as np
import time
import os
import logging
import json
from unittest.mock import MagicMock, patch

from models.monte_carlo.cache import cached_simulation, invalidate_cache, get_cache_stats
from models.monte_carlo.parallel import run_parallel_monte_carlo
from models.monte_carlo.test_helpers import (
    MockAllocationStrategy, 
    MockContributionPattern,
    simple_simulation_function,
    BenchmarkTracker,
    benchmark,
    assert_execution_time,
    track_memory_usage
)

# Configure logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestMonteCarloRegressionDetection(unittest.TestCase):
    """Test suite for detecting performance regressions in Monte Carlo simulations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Clear cache to ensure clean testing environment
        invalidate_cache()
        
        # Set up standard test parameters
        cls.standard_initial_amount = 1000000
        cls.standard_years = 30
        cls.standard_contribution = MockContributionPattern(monthly_amount=2000, years=cls.standard_years)
        cls.standard_allocation = MockAllocationStrategy(expected_return=0.08, volatility=0.12)
        
        # Create a benchmark tracker for all tests
        cls.tracker = BenchmarkTracker()
        
        # Load or create baseline benchmarks if they don't exist
        cls.ensure_baseline_exists()
    
    @classmethod
    def ensure_baseline_exists(cls):
        """Ensure that baseline benchmarks exist for comparison."""
        # If we don't have any history, create initial benchmarks
        if not cls.tracker.history:
            logger.info("No benchmark history found. Creating initial benchmarks...")
            
            # Run standard benchmarks to create baseline
            cls._run_standard_benchmark_suite()
            
            logger.info("Initial benchmarks created. These will be used as a baseline for future tests.")
    
    @classmethod
    def _run_standard_benchmark_suite(cls):
        """Run a standard set of benchmarks to establish a baseline."""
        # Basic simulation benchmarks
        cls._benchmark_simple_simulation()
        cls._benchmark_cached_simulation()
        cls._benchmark_parallel_simulation()
        
        # Edge case benchmarks
        cls._benchmark_long_timeframe()
        cls._benchmark_large_portfolio()
        cls._benchmark_complex_allocation()
    
    @classmethod
    def _benchmark_simple_simulation(cls):
        """Benchmark a simple uncached simulation."""
        start_time = time.time()
        
        # Run 10 simulations to get a good average
        for i in range(10):
            simple_simulation_function(
                seed_offset=i,
                initial_amount=cls.standard_initial_amount,
                contribution_pattern=cls.standard_contribution,
                years=cls.standard_years,
                allocation_strategy=cls.standard_allocation
            )
        
        duration = time.time() - start_time
        
        # Create result
        result = {
            'name': 'simple_simulation',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'duration': duration / 10,  # Average per simulation
            'success': True,
            'cache': {'hits': 0, 'misses': 10, 'hit_rate': 0, 'size': 0}
        }
        
        cls.tracker.history.append(result)
        cls.tracker._save_history()
        
        logger.info(f"Created baseline for simple_simulation: {duration/10:.4f}s per run")
    
    @classmethod
    def _benchmark_cached_simulation(cls):
        """Benchmark a cached simulation."""
        invalidate_cache()
        
        # Define a cached function
        @cached_simulation
        def cached_test_simulation(seed, initial, contribution, years, allocation):
            return simple_simulation_function(
                seed_offset=seed,
                initial_amount=initial,
                contribution_pattern=contribution,
                years=years,
                allocation_strategy=allocation
            )
        
        # First run to populate cache
        for i in range(5):
            cached_test_simulation(
                seed=i,
                initial=cls.standard_initial_amount,
                contribution=cls.standard_contribution,
                years=cls.standard_years,
                allocation=cls.standard_allocation
            )
        
        # Clear timing stats
        cache_stats_before = get_cache_stats()
        
        # Run with all cache hits to measure cached performance
        start_time = time.time()
        for i in range(5):
            cached_test_simulation(
                seed=i,
                initial=cls.standard_initial_amount,
                contribution=cls.standard_contribution,
                years=cls.standard_years,
                allocation=cls.standard_allocation
            )
        duration = time.time() - start_time
        
        cache_stats_after = get_cache_stats()
        cache_hits = cache_stats_after['hits'] - cache_stats_before['hits']
        
        # Create result
        result = {
            'name': 'cached_simulation',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'duration': duration / 5,  # Average per simulation
            'success': True,
            'cache': {'hits': cache_hits, 'misses': 0, 'hit_rate': 1.0, 'size': 5}
        }
        
        cls.tracker.history.append(result)
        cls.tracker._save_history()
        
        logger.info(f"Created baseline for cached_simulation: {duration/5:.4f}s per run")
    
    @classmethod
    def _benchmark_parallel_simulation(cls):
        """Benchmark a parallel simulation."""
        start_time = time.time()
        
        result = run_parallel_monte_carlo(
            initial_amount=cls.standard_initial_amount,
            contribution_pattern=cls.standard_contribution,
            years=cls.standard_years,
            allocation_strategy=cls.standard_allocation,
            simulation_function=simple_simulation_function,
            simulations=200,
            max_workers=4
        )
        
        duration = time.time() - start_time
        
        # Create result
        result = {
            'name': 'parallel_simulation',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'duration': duration,
            'success': True,
            'cache': {'hits': 0, 'misses': 0, 'hit_rate': 0, 'size': 0},
            'metadata': {'simulations': 200, 'workers': 4}
        }
        
        cls.tracker.history.append(result)
        cls.tracker._save_history()
        
        logger.info(f"Created baseline for parallel_simulation: {duration:.4f}s")
    
    @classmethod
    def _benchmark_long_timeframe(cls):
        """Benchmark a simulation with a long timeframe."""
        long_years = 50
        long_contribution = MockContributionPattern(monthly_amount=2000, years=long_years)
        
        start_time = time.time()
        
        # Run 5 simulations to get a good average
        for i in range(5):
            simple_simulation_function(
                seed_offset=i,
                initial_amount=cls.standard_initial_amount,
                contribution_pattern=long_contribution,
                years=long_years,
                allocation_strategy=cls.standard_allocation
            )
        
        duration = time.time() - start_time
        
        # Create result
        result = {
            'name': 'long_timeframe_simulation',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'duration': duration / 5,  # Average per simulation
            'success': True,
            'cache': {'hits': 0, 'misses': 5, 'hit_rate': 0, 'size': 0},
            'metadata': {'years': long_years}
        }
        
        cls.tracker.history.append(result)
        cls.tracker._save_history()
        
        logger.info(f"Created baseline for long_timeframe_simulation: {duration/5:.4f}s per run")
    
    @classmethod
    def _benchmark_large_portfolio(cls):
        """Benchmark a simulation with a large initial portfolio."""
        large_amount = 10000000  # 10 million
        
        start_time = time.time()
        
        # Run 5 simulations to get a good average
        for i in range(5):
            simple_simulation_function(
                seed_offset=i,
                initial_amount=large_amount,
                contribution_pattern=cls.standard_contribution,
                years=cls.standard_years,
                allocation_strategy=cls.standard_allocation
            )
        
        duration = time.time() - start_time
        
        # Create result
        result = {
            'name': 'large_portfolio_simulation',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'duration': duration / 5,  # Average per simulation
            'success': True,
            'cache': {'hits': 0, 'misses': 5, 'hit_rate': 0, 'size': 0},
            'metadata': {'initial_amount': large_amount}
        }
        
        cls.tracker.history.append(result)
        cls.tracker._save_history()
        
        logger.info(f"Created baseline for large_portfolio_simulation: {duration/5:.4f}s per run")
    
    @classmethod
    def _benchmark_complex_allocation(cls):
        """Benchmark a simulation with a complex allocation strategy."""
        # Create a more complex allocation strategy with more asset classes
        complex_allocation = MockAllocationStrategy(expected_return=0.085, volatility=0.13)
        complex_allocation.initial_allocation = {
            'us_equity': 0.30,
            'intl_equity': 0.20,
            'emerging_markets': 0.10,
            'govt_bonds': 0.15,
            'corp_bonds': 0.10,
            'high_yield': 0.05,
            'reits': 0.05,
            'commodities': 0.03,
            'cash': 0.02
        }
        
        start_time = time.time()
        
        # Run 5 simulations to get a good average
        for i in range(5):
            simple_simulation_function(
                seed_offset=i,
                initial_amount=cls.standard_initial_amount,
                contribution_pattern=cls.standard_contribution,
                years=cls.standard_years,
                allocation_strategy=complex_allocation
            )
        
        duration = time.time() - start_time
        
        # Create result
        result = {
            'name': 'complex_allocation_simulation',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'duration': duration / 5,  # Average per simulation
            'success': True,
            'cache': {'hits': 0, 'misses': 5, 'hit_rate': 0, 'size': 0},
            'metadata': {'asset_classes': len(complex_allocation.initial_allocation)}
        }
        
        cls.tracker.history.append(result)
        cls.tracker._save_history()
        
        logger.info(f"Created baseline for complex_allocation_simulation: {duration/5:.4f}s per run")
    
    def setUp(self):
        """Set up each test."""
        # Clear cache before each test
        invalidate_cache()
    
    # === Standard Benchmark Tests ===
    
    @benchmark("simple_simulation_regression", threshold=0.2)
    def test_simple_simulation_performance(self):
        """Test if basic simulation performance meets baseline expectations."""
        # Run multiple simulations to get a good average
        for i in range(10):
            simple_simulation_function(
                seed_offset=i,
                initial_amount=self.standard_initial_amount,
                contribution_pattern=self.standard_contribution,
                years=self.standard_years,
                allocation_strategy=self.standard_allocation
            )
    
    @benchmark("cached_simulation_regression", threshold=0.2)
    def test_cached_simulation_performance(self):
        """Test if cached simulation performance meets baseline expectations."""
        @cached_simulation
        def cached_test_simulation(seed, initial, contribution, years, allocation):
            return simple_simulation_function(
                seed_offset=seed,
                initial_amount=initial,
                contribution_pattern=contribution,
                years=years,
                allocation_strategy=allocation
            )
        
        # First run to populate cache
        for i in range(5):
            cached_test_simulation(
                seed=i,
                initial=self.standard_initial_amount,
                contribution=self.standard_contribution,
                years=self.standard_years,
                allocation=self.standard_allocation
            )
        
        # Run again - this time all from cache
        for i in range(5):
            cached_test_simulation(
                seed=i,
                initial=self.standard_initial_amount,
                contribution=self.standard_contribution,
                years=self.standard_years,
                allocation=self.standard_allocation
            )
    
    @benchmark("parallel_simulation_regression", threshold=0.25)
    def test_parallel_simulation_performance(self):
        """Test if parallel simulation performance meets baseline expectations."""
        run_parallel_monte_carlo(
            initial_amount=self.standard_initial_amount,
            contribution_pattern=self.standard_contribution,
            years=self.standard_years,
            allocation_strategy=self.standard_allocation,
            simulation_function=simple_simulation_function,
            simulations=200,
            max_workers=4
        )
    
    # === Edge Case Benchmark Tests ===
    
    @benchmark("long_timeframe_regression", threshold=0.2)
    def test_long_timeframe_performance(self):
        """Test performance with long timeframes."""
        long_years = 50
        long_contribution = MockContributionPattern(monthly_amount=2000, years=long_years)
        
        for i in range(5):
            simple_simulation_function(
                seed_offset=i,
                initial_amount=self.standard_initial_amount,
                contribution_pattern=long_contribution,
                years=long_years,
                allocation_strategy=self.standard_allocation
            )
    
    @benchmark("large_portfolio_regression", threshold=0.2)
    def test_large_portfolio_performance(self):
        """Test performance with large portfolio values."""
        large_amount = 10000000  # 10 million
        
        for i in range(5):
            simple_simulation_function(
                seed_offset=i,
                initial_amount=large_amount,
                contribution_pattern=self.standard_contribution,
                years=self.standard_years,
                allocation_strategy=self.standard_allocation
            )
    
    @benchmark("complex_allocation_regression", threshold=0.2)
    def test_complex_allocation_performance(self):
        """Test performance with complex allocation strategies."""
        # Create a more complex allocation strategy with more asset classes
        complex_allocation = MockAllocationStrategy(expected_return=0.085, volatility=0.13)
        complex_allocation.initial_allocation = {
            'us_equity': 0.30,
            'intl_equity': 0.20,
            'emerging_markets': 0.10,
            'govt_bonds': 0.15,
            'corp_bonds': 0.10,
            'high_yield': 0.05,
            'reits': 0.05,
            'commodities': 0.03,
            'cash': 0.02
        }
        
        for i in range(5):
            simple_simulation_function(
                seed_offset=i,
                initial_amount=self.standard_initial_amount,
                contribution_pattern=self.standard_contribution,
                years=self.standard_years,
                allocation_strategy=complex_allocation
            )
    
    # === Memory Usage Tests ===
    
    @track_memory_usage()
    def test_memory_usage_simulation(self):
        """Test memory usage during simulation."""
        for i in range(5):
            simple_simulation_function(
                seed_offset=i,
                initial_amount=self.standard_initial_amount,
                contribution_pattern=self.standard_contribution,
                years=self.standard_years,
                allocation_strategy=self.standard_allocation
            )
    
    @track_memory_usage()
    def test_memory_usage_parallel(self):
        """Test memory usage during parallel simulation."""
        run_parallel_monte_carlo(
            initial_amount=self.standard_initial_amount,
            contribution_pattern=self.standard_contribution,
            years=self.standard_years,
            allocation_strategy=self.standard_allocation,
            simulation_function=simple_simulation_function,
            simulations=200,
            max_workers=4
        )
    
    # === Cache Performance Tests ===
    
    def test_cache_hit_rate(self):
        """Test that cache hit rate meets performance expectations."""
        @cached_simulation
        def cached_test_simulation(seed, initial, contribution, years, allocation):
            return simple_simulation_function(
                seed_offset=seed,
                initial_amount=initial,
                contribution_pattern=contribution,
                years=years,
                allocation_strategy=allocation
            )
        
        # First run to populate cache with varied parameters
        for i in range(5):
            for initial in [1000000, 2000000]:
                cached_test_simulation(
                    seed=i,
                    initial=initial,
                    contribution=self.standard_contribution,
                    years=self.standard_years,
                    allocation=self.standard_allocation
                )
        
        # Now run exactly the same parameters
        cache_stats_before = get_cache_stats()
        
        for i in range(5):
            for initial in [1000000, 2000000]:
                cached_test_simulation(
                    seed=i,
                    initial=initial,
                    contribution=self.standard_contribution,
                    years=self.standard_years,
                    allocation=self.standard_allocation
                )
        
        cache_stats_after = get_cache_stats()
        
        # Calculate hit rate
        hits = cache_stats_after['hits'] - cache_stats_before['hits']
        total_ops = 10  # We expect 10 operations (5 seeds * 2 initials)
        hit_rate = hits / total_ops if total_ops > 0 else 0
        
        # Should have a perfect hit rate for identical parameters
        self.assertEqual(hit_rate, 1.0, f"Expected 100% hit rate, got {hit_rate:.2%}")

if __name__ == '__main__':
    unittest.main()
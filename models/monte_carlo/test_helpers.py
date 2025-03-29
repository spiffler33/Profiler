"""
Testing helper classes and functions for Monte Carlo simulations.

This module provides mock implementations of classes needed for testing
as well as utilities for performance benchmarking and test assertions.
"""

import numpy as np
import time
import logging
import json
import os
from typing import Dict, List, Tuple, Optional, Any, Callable
from functools import wraps
from datetime import datetime

from models.monte_carlo.cache import get_cache_stats, invalidate_cache

logger = logging.getLogger(__name__)

class MockAllocationStrategy:
    """Mock implementation of AllocationStrategy for testing."""
    
    def __init__(self, expected_return: float = 0.08, volatility: float = 0.12):
        """Initialize with expected return and volatility."""
        self._expected_return = expected_return
        self._volatility = volatility
        self.initial_allocation = {
            'equity': 0.6,
            'debt': 0.3,
            'gold': 0.05,
            'cash': 0.05
        }
        
    def get_expected_return(self) -> float:
        """Get the expected return for this allocation."""
        return self._expected_return
        
    def get_volatility(self) -> float:
        """Get the volatility for this allocation."""
        return self._volatility
        
class MockContributionPattern:
    """Mock implementation of ContributionPattern for testing."""
    
    def __init__(self, monthly_amount: float, years: int):
        """Initialize with monthly contribution amount and timeframe."""
        self.monthly_amount = monthly_amount
        self.years = years
        
    def get_contribution_for_year(self, year: int) -> float:
        """Get the annual contribution for a specific year."""
        if year <= self.years:
            return self.monthly_amount * 12
        return 0.0

class MockProjectionResult:
    """Mock implementation of ProjectionResult for testing."""
    
    def __init__(self, 
                 years: List[int],
                 projected_values: np.ndarray,
                 contributions: List[float],
                 growth: List[float],
                 confidence_intervals: Dict[str, np.ndarray],
                 volatility: float):
        """Initialize with projection results."""
        self.years = years
        self.projected_values = projected_values
        self.contributions = contributions
        self.growth = growth
        self.confidence_intervals = confidence_intervals
        self.volatility = volatility
        self.all_projections = None  # Will be set by caller
        self.yearly_contributions = None  # Will be set by caller

def simple_simulation_function(
    seed_offset: int,
    initial_amount: float,
    contribution_pattern: Any,
    years: int,
    allocation_strategy: Any
) -> np.ndarray:
    """
    A simple simulation function for testing that can be used with multiprocessing.
    
    This is a standalone function (not a class method) so it can be pickled.
    
    Args:
        seed_offset: Offset for random seed to ensure independent simulations
        initial_amount: Starting amount for the simulation
        contribution_pattern: Pattern of contributions over time
        years: Number of years to simulate
        allocation_strategy: Strategy for asset allocation
        
    Returns:
        Array of simulated values for each year
    """
    # Set the seed for this simulation
    np.random.seed(42 + seed_offset)
    
    # Initialize the result array
    result = np.zeros(years + 1)
    result[0] = initial_amount
    
    # Expected return and volatility from allocation strategy
    expected_return = allocation_strategy.get_expected_return()
    volatility = allocation_strategy.get_volatility()
    
    # Run simulation
    current_amount = initial_amount
    for year in range(1, years + 1):
        # Get contribution for this year
        contribution = contribution_pattern.get_contribution_for_year(year)
        
        # Generate random return for this year
        annual_return = np.random.normal(expected_return, volatility)
        
        # Update amount (apply return and add contribution)
        current_amount = current_amount * (1 + annual_return) + contribution
        result[year] = current_amount
        
    return result

# ----- Performance Benchmarking Utilities -----

class BenchmarkTracker:
    """Tracks and stores benchmark results for Monte Carlo simulations."""
    
    def __init__(self, save_path: str = None):
        """Initialize the benchmark tracker.
        
        Args:
            save_path: Optional path to save benchmark results
        """
        self.benchmarks = {}
        self.save_path = save_path or os.path.join(
            os.path.dirname(__file__), 
            "../../tests/models/benchmark_results.json"
        )
        self.load_history()
    
    def load_history(self):
        """Load historical benchmark data if available."""
        self.history = []
        try:
            if os.path.exists(self.save_path):
                with open(self.save_path, 'r') as f:
                    self.history = json.load(f)
                logger.info(f"Loaded {len(self.history)} historical benchmark records")
        except Exception as e:
            logger.warning(f"Failed to load benchmark history: {str(e)}")
    
    def start_benchmark(self, name: str):
        """Start a new benchmark measurement.
        
        Args:
            name: Name of the benchmark
        """
        self.benchmarks[name] = {
            'start_time': time.time(),
            'cache_before': get_cache_stats()
        }
    
    def end_benchmark(self, name: str, success: bool = True, metadata: Dict[str, Any] = None):
        """End a benchmark measurement and record results.
        
        Args:
            name: Name of the benchmark
            success: Whether the benchmark completed successfully
            metadata: Additional metadata to store with the benchmark
        
        Returns:
            Dict with benchmark results
        """
        if name not in self.benchmarks:
            logger.warning(f"Benchmark '{name}' was not started")
            return None
        
        benchmark = self.benchmarks[name]
        end_time = time.time()
        duration = end_time - benchmark['start_time']
        
        cache_after = get_cache_stats()
        
        # Calculate cache metrics
        cache_hits_delta = cache_after['hits'] - benchmark['cache_before']['hits']
        cache_misses_delta = cache_after['misses'] - benchmark['cache_before']['misses']
        total_ops = cache_hits_delta + cache_misses_delta
        hit_rate = cache_hits_delta / total_ops if total_ops > 0 else 0
        
        # Store results
        result = {
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'success': success,
            'cache': {
                'hits': cache_hits_delta,
                'misses': cache_misses_delta,
                'hit_rate': hit_rate,
                'size': cache_after['size']
            }
        }
        
        # Add metadata if provided
        if metadata:
            result['metadata'] = metadata
        
        # Add to history
        self.history.append(result)
        
        # Save updated history
        self._save_history()
        
        # Log result
        logger.info(f"Benchmark '{name}': {duration:.4f}s, cache hit rate: {hit_rate:.2%}")
        
        return result
    
    def _save_history(self):
        """Save benchmark history to disk."""
        try:
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            with open(self.save_path, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save benchmark history: {str(e)}")
    
    def get_baseline(self, name: str, limit: int = 5) -> Dict[str, Any]:
        """Get baseline performance for a specific benchmark.
        
        Args:
            name: Name of the benchmark
            limit: Number of historical records to use for baseline
            
        Returns:
            Dict with baseline metrics
        """
        # Filter history for this benchmark
        relevant = [r for r in self.history if r['name'] == name and r.get('success', True)]
        
        # Sort by timestamp (newest first)
        relevant.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Take most recent records up to limit
        recent = relevant[:limit]
        
        if not recent:
            logger.warning(f"No historical data for benchmark '{name}'")
            return {
                'name': name,
                'available': False
            }
        
        # Calculate average metrics
        durations = [r['duration'] for r in recent]
        hit_rates = [r['cache'].get('hit_rate', 0) for r in recent]
        
        return {
            'name': name,
            'available': True,
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'avg_hit_rate': sum(hit_rates) / len(hit_rates),
            'sample_size': len(recent)
        }
    
    def check_regression(self, name: str, current: Dict[str, Any], threshold: float = 0.15) -> Dict[str, Any]:
        """Check if current benchmark shows regression compared to baseline.
        
        Args:
            name: Name of the benchmark
            current: Current benchmark result
            threshold: Threshold for detecting regression (e.g., 0.15 = 15% slower)
            
        Returns:
            Dict with regression analysis
        """
        baseline = self.get_baseline(name)
        
        if not baseline.get('available', False):
            return {
                'name': name,
                'has_baseline': False,
                'is_regression': False
            }
        
        # Calculate percentage slowdown
        slowdown = (current['duration'] - baseline['avg_duration']) / baseline['avg_duration']
        
        # Determine if this is a regression
        is_regression = slowdown > threshold
        
        return {
            'name': name,
            'has_baseline': True,
            'is_regression': is_regression,
            'slowdown': slowdown,
            'current_duration': current['duration'],
            'baseline_duration': baseline['avg_duration'],
            'threshold': threshold,
            'baseline_sample_size': baseline['sample_size']
        }


def benchmark(name: str, track: bool = True, check_regression: bool = True, threshold: float = 0.15):
    """Decorator for benchmarking functions.
    
    Args:
        name: Name of the benchmark
        track: Whether to track and save benchmark results
        check_regression: Whether to check for performance regression
        threshold: Threshold for detecting regression
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create tracker if tracking is enabled
            tracker = BenchmarkTracker() if track else None
            
            # Start benchmark
            if tracker:
                tracker.start_benchmark(name)
            
            start_time = time.time()
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                # Record exception but re-raise it
                success = False
                logger.error(f"Benchmark '{name}' failed: {str(e)}")
                raise
            finally:
                # Record timing regardless of success
                duration = time.time() - start_time
                
                # Only save benchmark if tracking is enabled
                if tracker:
                    # Create metadata from args/kwargs (be careful not to include too much)
                    metadata = {
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                    
                    # Add function-specific metadata if available
                    if hasattr(func, 'get_benchmark_metadata'):
                        metadata.update(func.get_benchmark_metadata(*args, **kwargs))
                    
                    # End benchmark
                    benchmark_result = tracker.end_benchmark(name, success, metadata)
                    
                    # Check for regression if enabled
                    if check_regression and success:
                        regression = tracker.check_regression(name, benchmark_result, threshold)
                        if regression.get('is_regression', False):
                            logger.warning(
                                f"PERFORMANCE REGRESSION: {name} is {regression['slowdown']:.1%} slower than baseline "
                                f"({benchmark_result['duration']:.4f}s vs {regression['baseline_duration']:.4f}s)"
                            )
            
            # Return original function's result
            return result
        
        return wrapper
    
    return decorator


# ----- Testing Assertion Utilities -----

def verify_simulation_consistency(results: List[np.ndarray], threshold: float = 0.05) -> bool:
    """Verify that multiple simulation runs produce consistent results.
    
    Args:
        results: List of simulation result arrays
        threshold: Maximum allowable percentage deviation in key metrics
        
    Returns:
        bool: True if results are consistent, False otherwise
    """
    if not results or len(results) < 2:
        logger.warning("Cannot verify consistency with fewer than 2 result sets")
        return True
    
    # Extract final values from each simulation
    final_values = [result[-1] for result in results]
    
    # Calculate statistics
    mean_final = np.mean(final_values)
    std_final = np.std(final_values)
    
    # Calculate coefficient of variation (relative standard deviation)
    cv = std_final / mean_final if mean_final > 0 else 0
    
    # Check if variation is below threshold
    is_consistent = cv <= threshold
    
    if not is_consistent:
        logger.warning(
            f"Simulation inconsistency detected: coefficient of variation {cv:.2%} "
            f"exceeds threshold {threshold:.2%}"
        )
    
    return is_consistent


def create_cache_assertions(test_case):
    """Create cache-related test assertions for a unittest.TestCase.
    
    Args:
        test_case: unittest.TestCase instance
        
    Returns:
        Dict of assertion functions
    """
    def assert_cache_hit_rate(function, args=None, kwargs=None, min_rate=0.9, setup=None):
        """Assert that a function achieves a minimum cache hit rate.
        
        Args:
            function: Function to test
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            min_rate: Minimum acceptable hit rate
            setup: Optional setup function to run first
        """
        args = args or []
        kwargs = kwargs or {}
        
        # Run setup if provided
        if setup:
            setup()
        
        # Clear cache to start fresh
        invalidate_cache()
        
        # Get initial cache stats
        before = get_cache_stats()
        
        # Run function once to populate cache
        function(*args, **kwargs)
        
        # Get intermediate stats
        after_first = get_cache_stats()
        
        # First run should be a cache miss
        test_case.assertEqual(
            after_first['misses'] - before['misses'], 
            1, 
            "First run should result in exactly one cache miss"
        )
        
        # Run function again with same parameters
        function(*args, **kwargs)
        
        # Get final stats
        after_second = get_cache_stats()
        
        # Second run should be a cache hit
        test_case.assertEqual(
            after_second['hits'] - after_first['hits'], 
            1, 
            "Second run should result in exactly one cache hit"
        )
        
        # Run multiple times to get a meaningful hit rate
        for _ in range(8):
            function(*args, **kwargs)
        
        # Get final stats
        final = get_cache_stats()
        
        # Calculate hit rate for all runs after the first
        hits = final['hits'] - after_first['hits']
        misses = final['misses'] - after_first['misses']
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0
        
        # Assert minimum hit rate
        test_case.assertGreaterEqual(
            hit_rate, 
            min_rate, 
            f"Cache hit rate {hit_rate:.2%} is below minimum {min_rate:.2%}"
        )
        
        return hit_rate
    
    def assert_cache_invalidation(function, invalidator, args=None, kwargs=None):
        """Assert that a cache invalidation function properly clears the cache.
        
        Args:
            function: Function that uses cache
            invalidator: Function that should invalidate the cache
            args: Positional arguments for the functions
            kwargs: Keyword arguments for the functions
        """
        args = args or []
        kwargs = kwargs or {}
        
        # Clear cache to start fresh
        invalidate_cache()
        
        # Run function to populate cache
        function(*args, **kwargs)
        
        # Get stats after first run
        after_first = get_cache_stats()
        
        # Run function again - should be a cache hit
        function(*args, **kwargs)
        
        # Get stats after second run
        after_second = get_cache_stats()
        
        # Verify it was a cache hit
        test_case.assertEqual(
            after_second['hits'] - after_first['hits'], 
            1, 
            "Second run should have been a cache hit"
        )
        
        # Run invalidator
        invalidator(*args, **kwargs)
        
        # Get stats after invalidation
        after_invalidation = get_cache_stats()
        
        # Run function again - should be a cache miss if invalidation worked
        function(*args, **kwargs)
        
        # Get final stats
        final = get_cache_stats()
        
        # Verify it was a cache miss
        test_case.assertEqual(
            final['misses'] - after_invalidation['misses'], 
            1, 
            "Run after invalidation should be a cache miss"
        )
    
    def assert_cache_key_uniqueness(function, param_sets):
        """Assert that different parameter sets generate different cache keys.
        
        Args:
            function: Function that uses cache
            param_sets: List of parameter sets, each a tuple of (args, kwargs)
        """
        # Clear cache to start fresh
        invalidate_cache()
        
        for args, kwargs in param_sets:
            # Get cache size before
            before = get_cache_stats()['size']
            
            # Run function with this parameter set
            function(*args, **kwargs)
            
            # Get cache size after
            after = get_cache_stats()['size']
            
            # Cache size should increase by 1 for each unique parameter set
            test_case.assertEqual(
                after - before, 
                1, 
                f"Cache size should increase by 1 for parameter set {args}, {kwargs}"
            )
    
    return {
        'assert_cache_hit_rate': assert_cache_hit_rate,
        'assert_cache_invalidation': assert_cache_invalidation,
        'assert_cache_key_uniqueness': assert_cache_key_uniqueness
    }


def assert_execution_time(func, max_time, args=None, kwargs=None, retries=1):
    """Assert that a function executes within a maximum time.
    
    Args:
        func: Function to test
        max_time: Maximum allowed execution time in seconds
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        retries: Number of retries before failing
        
    Returns:
        Execution time
    """
    args = args or []
    kwargs = kwargs or {}
    
    # Run multiple times and take the best time
    times = []
    
    for _ in range(retries):
        start = time.time()
        func(*args, **kwargs)
        execution_time = time.time() - start
        times.append(execution_time)
    
    # Take the minimum time (to account for system noise)
    min_time = min(times)
    
    # Assert the function executes within the specified time
    if min_time > max_time:
        raise AssertionError(
            f"Function {func.__name__} execution time {min_time:.4f}s exceeds maximum {max_time:.4f}s"
        )
    
    return min_time


# ----- Memory Usage Tracking -----

def track_memory_usage():
    """Track peak memory usage during a function call.
    
    Returns:
        Decorator function
    """
    try:
        import resource
        import gc
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Force garbage collection to get accurate baseline
                gc.collect()
                
                # Get initial memory usage
                initial_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Force garbage collection again to clean up
                gc.collect()
                
                # Get peak memory usage
                peak_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                
                # Calculate memory used by the function
                memory_used = peak_usage - initial_usage
                
                # Log memory usage
                logger.info(f"Function {func.__name__} used {memory_used} KB of memory")
                
                return result
            
            return wrapper
        
        return decorator
    
    except ImportError:
        # resource module not available (e.g., on Windows)
        logger.warning("Memory tracking not available: resource module not found")
        
        def identity_decorator(func):
            return func
        
        return identity_decorator
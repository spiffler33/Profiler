"""
Test for the goal probability compatibility module.

This test has been deprecated since we're now using models.goal_probability
as the compatibility layer instead of a separate module.
"""

import unittest
import sys

class TestGoalProbabilityCompatibility(unittest.TestCase):
    """Test the backward compatibility of the goal probability module."""
    
    def test_import_from_compatibility_layer(self):
        """Test that all classes and functions can be imported from the compatibility layer."""
        # Import all components from the compatibility module
        from models.goal_probability import (
            ProbabilityResult,
            GoalOutcomeDistribution,
            GoalProbabilityAnalyzer,
            to_scalar,
            safe_array_compare,
            safe_median,
            safe_array_to_bool,
            run_parallel_monte_carlo,
            run_simulation_batch,
            cached_simulation,
            invalidate_cache,
            get_cache_stats
        )
        
        # Test that classes can be instantiated
        result = ProbabilityResult()
        self.assertIsInstance(result, ProbabilityResult)
        
        distribution = GoalOutcomeDistribution()
        self.assertIsInstance(distribution, GoalOutcomeDistribution)
        
        # Test importing analyzer (don't instantiate as it requires services)
        self.assertTrue(callable(GoalProbabilityAnalyzer))
        
        # Test that functions are callable
        self.assertTrue(callable(to_scalar))
        self.assertTrue(callable(safe_array_compare))
        self.assertTrue(callable(safe_median))
        self.assertTrue(callable(safe_array_to_bool))
        self.assertTrue(callable(run_parallel_monte_carlo))
        self.assertTrue(callable(run_simulation_batch))
        self.assertTrue(callable(cached_simulation))
        self.assertTrue(callable(invalidate_cache))
        self.assertTrue(callable(get_cache_stats))
        
if __name__ == '__main__':
    unittest.main()
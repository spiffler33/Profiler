"""
Test backward compatibility with the original goal_probability module.

This test ensures that the compatibility layer in goal_probability.py
correctly re-exports all the necessary classes and functions from the
new modular structure.
"""

import unittest
import sys
from unittest.mock import MagicMock, patch

class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with the original goal_probability module."""
    
    def test_compatibility_imports(self):
        """Test that imports from goal_probability still work correctly."""
        # Import classes from original module path
        from models.goal_probability import (
            ProbabilityResult,
            GoalOutcomeDistribution,
            GoalProbabilityAnalyzer,
            run_parallel_monte_carlo,
            cached_simulation,
            invalidate_cache,
            get_cache_stats,
            to_scalar,
            safe_array_compare,
            safe_median,
            safe_array_to_bool
        )
        
        # Test that instances can be created
        result = ProbabilityResult()
        distribution = GoalOutcomeDistribution()
        
        # Verify that the instances have the expected methods and properties
        self.assertTrue(hasattr(result, 'success_metrics'))
        self.assertTrue(hasattr(result, 'to_dict'))
        self.assertTrue(hasattr(result, 'get_safe_success_probability'))
        
        self.assertTrue(hasattr(distribution, 'add_simulation_result'))
        self.assertTrue(hasattr(distribution, 'percentile'))
        self.assertTrue(hasattr(distribution, 'success_probability'))
        
    def test_api_compatibility(self):
        """Test that the API functionality works through the compatibility layer."""
        # Import from original module path
        from models.goal_probability import (
            ProbabilityResult,
            GoalOutcomeDistribution,
            GoalProbabilityAnalyzer
        )
        
        # Create instances
        result = ProbabilityResult(success_metrics={"success_probability": 0.75})
        distribution = GoalOutcomeDistribution([100, 200, 300])
        
        # Test functionality
        self.assertEqual(result.success_probability, 0.75)
        self.assertEqual(distribution.mean, 200)
        
        # Test with mock parameter service
        mock_param_service = MagicMock()
        mock_param_service.get.return_value = 0.06
        
        # Create analyzer with mock
        analyzer = GoalProbabilityAnalyzer(financial_parameter_service=mock_param_service)
        
        # Test that interface methods are available
        self.assertTrue(hasattr(analyzer, 'calculate_probability'))
        self.assertTrue(hasattr(analyzer, 'get_parameter'))
        
    def test_dependent_code_example(self):
        """Test realistic example of dependent code using the compatibility layer."""
        # Import as dependent code would
        from models.goal_probability import GoalProbabilityAnalyzer, ProbabilityResult
        
        # Create mock for financial_parameter_service
        mock_param_service = MagicMock()
        
        # Example goal data
        goal_data = {
            'id': 'test-goal',
            'goal_type': 'retirement',
            'target_amount': 1000000,
            'current_amount': 100000,
            'monthly_contribution': 10000,
            'timeframe': 25
        }
        
        # Create analyzer with mock
        analyzer = GoalProbabilityAnalyzer(financial_parameter_service=mock_param_service)
        
        # Mock calculate_probability to avoid actually running simulations
        original_calculate = analyzer.calculate_probability
        analyzer.calculate_probability = MagicMock()
        
        # Set return value
        mock_result = ProbabilityResult(success_metrics={"success_probability": 0.8})
        analyzer.calculate_probability.return_value = mock_result
        
        # Call method as dependent code would
        result = analyzer.calculate_probability(goal_data)
        
        # Verify
        self.assertEqual(result.success_probability, 0.8)
        
        # Reset mock
        analyzer.calculate_probability = original_calculate
        
if __name__ == '__main__':
    unittest.main()
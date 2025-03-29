"""
Unit tests for the Monte Carlo probability components.

Tests the modularized Monte Carlo probability system, including the
ProbabilityResult, GoalOutcomeDistribution, and array fix integration.
"""

import unittest
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock, patch

from models.monte_carlo.probability.result import ProbabilityResult
from models.monte_carlo.probability.distribution import GoalOutcomeDistribution
from models.monte_carlo.array_fix import to_scalar, safe_array_compare, safe_median, safe_array_to_bool

class TestMonteCarloProbabilityModularization(unittest.TestCase):
    """
    Test the modularized Monte Carlo probability system.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create sample simulation results
        np.random.seed(42)  # Ensure deterministic test results
        self.sim_results = np.random.normal(10000000, 2000000, 1000)
        
        # Success threshold
        self.target_amount = 10000000
        
        # Create sample goal
        self.test_goal = {
            'id': 'test-goal-1',
            'title': 'Test Retirement Goal',
            'target_amount': self.target_amount,
            'current_amount': 1000000,
            'monthly_contribution': 20000,
            'timeframe': (datetime.now().year + 25),
            'allocation': {
                'equity': 0.6,
                'debt': 0.3,
                'gold': 0.05,
                'cash': 0.05
            }
        }
    
    def test_probability_result(self):
        """Test the ProbabilityResult class."""
        # Create a simple probability result
        result = ProbabilityResult(
            success_metrics={
                'success_probability': 0.75,
                'failure_probability': 0.25,
                'shortfall_risk': 0.15
            },
            distribution_data={
                'percentiles': {
                    '10': 6000000,
                    '50': 10500000,
                    '90': 15000000
                }
            }
        )
        
        # Test basic properties
        self.assertEqual(result.success_metrics['success_probability'], 0.75)
        self.assertEqual(result.distribution_data['percentiles']['50'], 10500000)
        
        # Test serialization
        serialized = result.to_dict()
        self.assertIsInstance(serialized, dict)
        self.assertEqual(serialized['success_metrics']['success_probability'], 0.75)
        
        # Test from_dict method
        new_result = ProbabilityResult.from_dict(serialized)
        self.assertEqual(new_result.success_metrics['success_probability'], 0.75)
        
        # Test safe_success_probability method
        self.assertEqual(result.get_safe_success_probability(), 0.75)
        
        # Test with missing probability
        result2 = ProbabilityResult()
        self.assertEqual(result2.get_safe_success_probability(), 0.0)
        
        # Test with numpy array probability
        result3 = ProbabilityResult(success_metrics={'success_probability': np.array([0.85])})
        self.assertEqual(to_scalar(result3.get_safe_success_probability()), 0.85)
    
    def test_goal_outcome_distribution(self):
        """Test the GoalOutcomeDistribution class."""
        # Create a distribution
        distribution = GoalOutcomeDistribution()
        
        # Test adding simulation results
        distribution.add_simulation_results(self.sim_results)
        self.assertEqual(len(distribution.simulation_values), len(self.sim_results))
        
        # Test basic statistics
        self.assertAlmostEqual(distribution.mean, np.mean(self.sim_results), delta=1.0)
        self.assertAlmostEqual(distribution.median, np.median(self.sim_results), delta=1.0)
        
        # Test percentiles
        p50 = distribution.percentile(0.5)
        self.assertAlmostEqual(p50, np.median(self.sim_results), delta=1.0)
        
        p90 = distribution.percentile(0.9)
        sorted_results = sorted(self.sim_results)
        expected_p90 = sorted_results[int(0.9 * len(sorted_results))]
        self.assertAlmostEqual(p90, expected_p90, delta=100000)
        
        # Test success probability
        success_ratio = np.mean(self.sim_results >= self.target_amount)
        calculated_prob = distribution.success_probability(self.target_amount)
        self.assertAlmostEqual(calculated_prob, success_ratio, delta=0.1)
        
        # Test histogram calculation
        histogram = distribution.calculate_histogram(bins=10)
        self.assertEqual(len(histogram['bin_edges']), 11)  # bins + 1 for edges
        self.assertEqual(len(histogram['bin_counts']), 10)
        
        # Test with empty distribution
        empty_dist = GoalOutcomeDistribution()
        self.assertEqual(empty_dist.success_probability(self.target_amount), 0.0)
        self.assertEqual(empty_dist.mean, 0.0)
    
    def test_array_fix_integration(self):
        """Test integration with array fix utilities."""
        # Create a scenario with numpy arrays
        array_scenario = {
            'outcomes': np.random.normal(10000000, 2000000, 100),
            'success_count': np.sum(np.random.normal(10000000, 2000000, 100) >= 10000000)
        }
        
        # Test with ProbabilityResult
        result = ProbabilityResult(success_metrics={
            'success_probability': array_scenario['success_count'] / 100,
            'raw_outcomes': array_scenario['outcomes']
        })
        
        # Test safe scalar conversion
        prob = to_scalar(result.get_safe_success_probability())
        self.assertIsInstance(prob, float)
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)
        
        # Test safe array comparison
        is_above_target = safe_array_compare(array_scenario['outcomes'], 10000000, 'gt')
        self.assertIsInstance(is_above_target, bool)
        
        # Test safe median
        median_outcome = safe_median(array_scenario['outcomes'])
        self.assertIsInstance(median_outcome, float)
        
        # Test safe array to bool
        has_successful_outcomes = safe_array_to_bool(array_scenario['outcomes'] >= 10000000, 'any')
        self.assertIsInstance(has_successful_outcomes, bool)
        
        # Test error cases to ensure proper handling
        distribution = GoalOutcomeDistribution()
        distribution.add_simulation_results(array_scenario['outcomes'])
        
        # Test with None and empty arrays
        self.assertEqual(to_scalar(None), 0.0)
        self.assertEqual(safe_median(np.array([])), 0.0)
        self.assertFalse(safe_array_compare(None, 1000, 'gt'))
        self.assertFalse(safe_array_to_bool(None))

if __name__ == '__main__':
    unittest.main()
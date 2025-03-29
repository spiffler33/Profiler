"""
Integration tests for modularized Monte Carlo goal probability system.

This test ensures that the modularized version maintains the same behavior
as the original monolithic implementation for typical use cases.
"""

import unittest
import numpy as np
from datetime import datetime, timedelta
import json

# Import from original module for comparison
from models.goal_probability import ProbabilityResult as OriginalProbabilityResult
from models.goal_probability import GoalOutcomeDistribution as OriginalDistribution
from models.goal_probability import GoalProbabilityAnalyzer as OriginalAnalyzer

# Import from new modular structure
from models.monte_carlo.probability import (
    ProbabilityResult,
    GoalOutcomeDistribution,
    GoalProbabilityAnalyzer
)

class TestGoalProbabilityIntegration(unittest.TestCase):
    """Test that modularized goal probability components maintain same behavior."""
    
    def setUp(self):
        """Set up test data."""
        # Create sample goal data
        self.test_goal = {
            'id': 'test-goal-1',
            'goal_type': 'retirement',
            'title': 'Test Retirement Goal',
            'target_amount': 10000000,
            'current_amount': 1000000,
            'monthly_contribution': 20000,
            'timeframe': '2050-01-01',  # or just use 25 (years)
            'allocation': {
                'equity': 0.6,
                'debt': 0.3,
                'gold': 0.05,
                'real_estate': 0.0,
                'cash': 0.05
            },
            'contribution_frequency': 'monthly'
        }
        
        # Create simulated distribution data
        np.random.seed(42)  # For reproducibility
        self.simulation_values = np.random.normal(12000000, 3000000, 1000).tolist()
        
    def test_probability_result_equivalence(self):
        """Test that ProbabilityResult behaves the same in both implementations."""
        # Create original result
        orig_result = OriginalProbabilityResult(
            success_metrics={"success_probability": 0.75, "shortfall_risk": 0.25},
            time_based_metrics={"years_to_90pct": 15, "timeline": {5: 0.3, 10: 0.5, 15: 0.7, 20: 0.9}},
            distribution_data={"percentiles": {"25": 8000000, "50": 10000000, "75": 12000000}}
        )
        
        # Create new modular result with same data
        new_result = ProbabilityResult(
            success_metrics={"success_probability": 0.75, "shortfall_risk": 0.25},
            time_based_metrics={"years_to_90pct": 15, "timeline": {5: 0.3, 10: 0.5, 15: 0.7, 20: 0.9}},
            distribution_data={"percentiles": {"25": 8000000, "50": 10000000, "75": 12000000}}
        )
        
        # Test property access
        self.assertEqual(orig_result.success_probability, new_result.success_probability)
        self.assertEqual(orig_result.get_safe_success_probability(), new_result.get_safe_success_probability())
        
        # Test dictionary conversion
        orig_dict = orig_result.to_dict()
        new_dict = new_result.to_dict()
        self.assertEqual(orig_dict["success_metrics"], new_dict["success_metrics"])
        self.assertEqual(orig_dict["time_based_metrics"], new_dict["time_based_metrics"])
        self.assertEqual(orig_dict["distribution_data"], new_dict["distribution_data"])
        
        # Test backward compatibility with time_metrics field
        self.assertEqual(orig_result.time_metrics, new_result.time_metrics)
        self.assertEqual(orig_dict["time_metrics"], new_dict["time_metrics"])
    
    def test_distribution_equivalence(self):
        """Test that GoalOutcomeDistribution behaves the same in both implementations."""
        # Create instances with same data
        orig_dist = OriginalDistribution(self.simulation_values)
        new_dist = GoalOutcomeDistribution(self.simulation_values)
        
        # Test basic statistical methods
        self.assertEqual(orig_dist.mean, new_dist.mean)
        self.assertEqual(orig_dist.median, new_dist.median)
        self.assertEqual(orig_dist.std_dev, new_dist.std_dev)
        
        # Test percentile calculations
        for p in [0.1, 0.25, 0.5, 0.75, 0.9]:
            self.assertEqual(orig_dist.percentile(p), new_dist.percentile(p))
        
        # Test success probability
        target = 10000000
        orig_prob = orig_dist.success_probability(target)
        new_prob = new_dist.success_probability(target)
        self.assertAlmostEqual(orig_prob, new_prob, places=6)
        
        # Test shortfall risk
        orig_risk = orig_dist.shortfall_risk(target, 0.8)
        new_risk = new_dist.shortfall_risk(target, 0.8)
        self.assertEqual(orig_risk, new_risk)
        
        # Test histograms
        orig_hist = orig_dist.calculate_histogram(bins=10)
        new_hist = new_dist.calculate_histogram(bins=10)
        
        # Check bin counts (should be identical)
        np.testing.assert_array_equal(orig_hist["bin_counts"], new_hist["bin_counts"])
        
        # Check bin edges (may have tiny floating point differences)
        np.testing.assert_allclose(orig_hist["bin_edges"], new_hist["bin_edges"])
    
    def test_advanced_integration(self):
        """Test advanced integration between components."""
        # Test adding simulation results and recalculating
        orig_dist = OriginalDistribution(self.simulation_values[:500])
        new_dist = GoalOutcomeDistribution(self.simulation_values[:500])
        
        # Add more results and verify they behave the same
        orig_dist.add_simulation_results(self.simulation_values[500:])
        new_dist.add_simulation_results(self.simulation_values[500:])
        
        # Verify key statistics remain in sync
        stats = ["mean", "median", "std_dev"]
        for stat in stats:
            self.assertEqual(getattr(orig_dist, stat), getattr(new_dist, stat))
        
        # Test calculate_key_statistics method
        target = 10000000
        orig_stats = orig_dist.calculate_key_statistics(target)
        new_stats = new_dist.calculate_key_statistics(target)
        
        # Check each key statistic
        for key in orig_stats:
            if isinstance(orig_stats[key], float):
                self.assertAlmostEqual(orig_stats[key], new_stats[key], places=6, 
                                    msg=f"Mismatch in {key}: {orig_stats[key]} vs {new_stats[key]}")
            else:
                self.assertEqual(orig_stats[key], new_stats[key],
                               msg=f"Mismatch in {key}: {orig_stats[key]} vs {new_stats[key]}")

    def test_serialization_compatibility(self):
        """Test serialization compatibility between old and new implementations."""
        # Create results
        orig_result = OriginalProbabilityResult(
            success_metrics={"success_probability": 0.75},
            time_based_metrics={"years_to_90pct": 15},
            distribution_data={"percentiles": {"50": 10000000}}
        )
        
        new_result = ProbabilityResult(
            success_metrics={"success_probability": 0.75},
            time_based_metrics={"years_to_90pct": 15},
            distribution_data={"percentiles": {"50": 10000000}}
        )
        
        # Convert to JSON
        orig_json = json.dumps(orig_result.to_dict())
        new_json = json.dumps(new_result.to_dict())
        
        # Deserialize with opposite class
        orig_from_new = OriginalProbabilityResult.from_dict(json.loads(new_json))
        new_from_orig = ProbabilityResult.from_dict(json.loads(orig_json))
        
        # Verify they're equivalent
        self.assertEqual(orig_from_new.success_probability, 0.75)
        self.assertEqual(new_from_orig.success_probability, 0.75)
        self.assertEqual(orig_from_new.time_based_metrics["years_to_90pct"], 15)
        self.assertEqual(new_from_orig.time_based_metrics["years_to_90pct"], 15)

if __name__ == '__main__':
    unittest.main()
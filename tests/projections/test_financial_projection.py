"""
Tests for the financial projection module.
"""

import unittest
import numpy as np
import pandas as pd
from models.financial_projection import (
    AssetProjection, 
    AssetClass, 
    ContributionPattern,
    AllocationStrategy,
    ProjectionResult
)

class TestAssetProjection(unittest.TestCase):
    """Test cases for the AssetProjection class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a projection with deterministic seed for reproducible tests
        self.projection = AssetProjection(seed=42)
        
        # Basic test inputs
        self.initial_amount = 10000
        self.years = 10
        
        # Simple allocation (60/40 portfolio)
        self.allocation = AllocationStrategy(
            initial_allocation={
                AssetClass.EQUITY: 0.6,
                AssetClass.DEBT: 0.4
            }
        )
        
        # Simple contribution pattern
        self.contributions = ContributionPattern(
            annual_amount=1000,
            growth_rate=0.03  # 3% annual growth in contributions
        )

    def test_project_asset_growth_basic(self):
        """Test basic asset growth projection"""
        result = self.projection.project_asset_growth(
            initial_amount=self.initial_amount,
            contribution_pattern=self.contributions,
            years=self.years,
            allocation_strategy=self.allocation
        )
        
        # Check result structure
        self.assertIsInstance(result, ProjectionResult)
        self.assertEqual(len(result.years), self.years + 1)  # +1 for initial year
        self.assertEqual(len(result.projected_values), self.years + 1)
        self.assertEqual(len(result.contributions), self.years + 1)
        self.assertEqual(len(result.growth), self.years + 1)
        
        # Verify initial values
        self.assertEqual(result.projected_values[0], self.initial_amount)
        self.assertEqual(result.contributions[0], 0)  # No contribution at start
        self.assertEqual(result.growth[0], 0)  # No growth at start
        
        # Verify growth is occurring (final value should be greater than initial + contributions)
        total_contributions = sum(result.contributions)
        self.assertGreater(result.projected_values[-1], self.initial_amount + total_contributions)
        
        # Verify we can convert to DataFrame
        df = result.to_dataframe()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), self.years + 1)

    def test_monte_carlo_simulation(self):
        """Test Monte Carlo simulation for projections"""
        result = self.projection.project_with_monte_carlo(
            initial_amount=self.initial_amount,
            contribution_pattern=self.contributions,
            years=self.years,
            allocation_strategy=self.allocation,
            simulations=100,  # Reduced for test speed
            confidence_levels=[0.1, 0.5, 0.9]
        )
        
        # Check result structure
        self.assertIsInstance(result, ProjectionResult)
        self.assertIsNotNone(result.confidence_intervals)
        self.assertIsNotNone(result.volatility)
        
        # Check confidence intervals
        self.assertIn("P10", result.confidence_intervals)
        self.assertIn("P50", result.confidence_intervals)
        self.assertIn("P90", result.confidence_intervals)
        
        # P90 should be higher than P50, which should be higher than P10
        self.assertGreater(result.confidence_intervals["P90"][-1], 
                          result.confidence_intervals["P50"][-1])
        self.assertGreater(result.confidence_intervals["P50"][-1], 
                          result.confidence_intervals["P10"][-1])
        
        # Check volatility is positive
        self.assertGreater(result.volatility, 0)

    def test_inflation_adjustment(self):
        """Test inflation adjustment of projections"""
        # Create a projection with a specific inflation rate
        projection = AssetProjection(inflation_rate=0.04, seed=42)  # 4% inflation
        
        # Generate nominal projection
        nominal_result = projection.project_asset_growth(
            initial_amount=self.initial_amount,
            contribution_pattern=self.contributions,
            years=self.years,
            allocation_strategy=self.allocation
        )
        
        # Apply inflation adjustment
        real_result = projection.apply_inflation_adjustment(nominal_result)
        
        # Check that real values are less than nominal values
        for i in range(1, self.years + 1):  # Starting from year 1
            self.assertLess(real_result.projected_values[i], nominal_result.projected_values[i])

    def test_glide_path(self):
        """Test allocation glide path functionality"""
        # Create a glide path allocation (shifting from 80/20 to 40/60 over 5 years)
        glide_path_allocation = AllocationStrategy(
            initial_allocation={
                AssetClass.EQUITY: 0.8,
                AssetClass.DEBT: 0.2
            },
            target_allocation={
                AssetClass.EQUITY: 0.4,
                AssetClass.DEBT: 0.6
            },
            glide_path_years=5
        )
        
        # Project with glide path
        result = self.projection.project_asset_growth(
            initial_amount=self.initial_amount,
            contribution_pattern=self.contributions,
            years=10,
            allocation_strategy=glide_path_allocation
        )
        
        # We can't directly test the internal allocations, but we can test
        # that the projection completes successfully
        self.assertEqual(len(result.projected_values), 11)  # 10 years + initial

    def test_irregular_contributions(self):
        """Test irregular contribution patterns"""
        # Create an irregular contribution pattern
        irregular_contributions = ContributionPattern(
            annual_amount=1000,
            irregular_schedule={
                2: 5000,  # Extra contribution in year 2
                5: 10000  # Extra contribution in year 5
            }
        )
        
        # Project with irregular contributions
        result = self.projection.project_asset_growth(
            initial_amount=self.initial_amount,
            contribution_pattern=irregular_contributions,
            years=10,
            allocation_strategy=self.allocation
        )
        
        # Check irregular contributions are applied
        self.assertEqual(result.contributions[2], 5000)
        self.assertEqual(result.contributions[5], 10000)
        
        # Other years should have the default contribution
        self.assertEqual(result.contributions[1], 1000)
        self.assertEqual(result.contributions[3], 1000)

    def test_volatility_metrics(self):
        """Test calculation of volatility metrics"""
        metrics = self.projection.calculate_volatility_metrics(
            allocation=self.allocation.initial_allocation,
            time_horizon=self.years
        )
        
        # Check required metrics are present
        self.assertIn("annual_volatility", metrics)
        self.assertIn("worst_case_annual", metrics)
        self.assertIn("max_drawdown_estimate", metrics)
        self.assertIn("horizon_volatility", metrics)
        self.assertIn("probability_of_loss", metrics)
        
        # Check values are reasonable
        self.assertGreater(metrics["annual_volatility"], 0)
        self.assertLess(metrics["probability_of_loss"], 0.5)  # Should be low for 10-year horizon
        
        # Horizon volatility should be less than annual volatility
        self.assertLess(metrics["horizon_volatility"], metrics["annual_volatility"])


if __name__ == "__main__":
    unittest.main()
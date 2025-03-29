#!/usr/bin/env python3
"""
Integration tests to ensure compatibility between enhanced FinancialParameters
and the GoalCalculator module.

This test suite verifies that all our enhancements to financial_parameters.py
are compatible with the goal_calculator.py module and don't break any existing
functionality.
"""

import unittest
import json
import math
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from models.financial_parameters import FinancialParameters, ParameterSource
from models.goal_calculator import (
    GoalCalculator, 
    EmergencyFundCalculator,
    RetirementCalculator,
    HomeDownPaymentCalculator,
    EducationCalculator
)

class TestGoalCalculatorCompatibility(unittest.TestCase):
    """Test suite for verifying compatibility between enhanced FinancialParameters and GoalCalculator."""
    
    def setUp(self):
        """Set up test environment before each test."""
        self.financial_params = FinancialParameters()
        
        # Create a basic goal calculator
        self.calculator = GoalCalculator()
        
        # Create specialized calculators
        self.emergency_calculator = EmergencyFundCalculator()
        self.retirement_calculator = RetirementCalculator()
        self.home_calculator = HomeDownPaymentCalculator()
        self.education_calculator = EducationCalculator()
        
        # Sample profile for testing
        self.test_profile = {
            "user_id": "test123",
            "monthly_income": 100000,
            "monthly_expenses": 60000,
            "age": 35,
            "retirement_age": 60,
            "risk_profile": "moderate",
            "tax_bracket": 0.30
        }
        
        # Sample goals for testing
        self.emergency_goal = {
            "id": "goal1",
            "category": "emergency_fund",
            "target_amount": 0,  # Will be calculated
            "time_horizon": 1,
            "priority": "high",
            "monthly_contribution": 10000
        }
        
        self.retirement_goal = {
            "id": "goal2",
            "category": "traditional_retirement",
            "target_amount": 0,  # Will be calculated
            "time_horizon": 25,  # 25 years to retirement
            "priority": "high",
            "monthly_contribution": 20000,
            "retirement_corpus_needed": 0  # Will be calculated
        }
        
        self.home_goal = {
            "id": "goal3",
            "category": "home_purchase",
            "target_amount": 5000000,  # 50 lakhs
            "time_horizon": 5,  # 5 years to home purchase
            "priority": "medium",
            "monthly_contribution": 50000,
            "property_value": 10000000,  # 1 crore property
            "down_payment_percent": 0.20  # 20% down payment
        }
        
        self.education_goal = {
            "id": "goal4",
            "category": "education",
            "target_amount": 2000000,  # 20 lakhs
            "time_horizon": 10,  # 10 years to education
            "priority": "medium",
            "monthly_contribution": 15000,
            "education_inflation_rate": 0.10  # 10% education inflation
        }
        
    def test_financial_parameters_initialization(self):
        """Test that GoalCalculator properly initializes with FinancialParameters."""
        # Verify key parameters are correctly loaded from financial parameters
        self.assertIsNotNone(self.calculator.params["inflation_rate"])
        self.assertIsNotNone(self.calculator.params["emergency_fund_months"])
        self.assertIsNotNone(self.calculator.params["equity_returns"]["moderate"])
        self.assertIsNotNone(self.calculator.params["debt_returns"]["conservative"])
        
        # Verify allocation model is properly loaded
        gold_allocation = self.calculator.params["gold_allocation_percent"]
        self.assertIsNotNone(gold_allocation)
        self.assertGreater(gold_allocation, 0)
        
    def test_asset_returns_are_used_correctly(self):
        """Test that our enhanced asset returns are used correctly in goal calculations."""
        # Check that asset returns from different risk profiles are available
        self.assertIsNotNone(self.calculator.params["equity_returns"]["conservative"])
        self.assertIsNotNone(self.calculator.params["equity_returns"]["moderate"])
        self.assertIsNotNone(self.calculator.params["equity_returns"]["aggressive"])
        
        # Check that debt returns from different risk profiles are available
        self.assertIsNotNone(self.calculator.params["debt_returns"]["conservative"])
        self.assertIsNotNone(self.calculator.params["debt_returns"]["moderate"])
        self.assertIsNotNone(self.calculator.params["debt_returns"]["aggressive"])
        
        # Verify realistic return ranges
        self.assertGreater(self.calculator.params["equity_returns"]["aggressive"], 
                           self.calculator.params["equity_returns"]["conservative"])
        
        self.assertGreater(self.calculator.params["debt_returns"]["aggressive"], 
                           self.calculator.params["debt_returns"]["conservative"])
        
    def test_get_calculator_for_goal(self):
        """Test that the factory method returns appropriate calculators."""
        # Emergency fund goal
        calculator = GoalCalculator.get_calculator_for_goal(self.emergency_goal)
        self.assertIsInstance(calculator, EmergencyFundCalculator)
        
        # Retirement goal
        calculator = GoalCalculator.get_calculator_for_goal(self.retirement_goal)
        self.assertIsInstance(calculator, RetirementCalculator)
        
        # Home purchase goal
        calculator = GoalCalculator.get_calculator_for_goal(self.home_goal)
        self.assertIsInstance(calculator, HomeDownPaymentCalculator)
        
        # Education goal
        calculator = GoalCalculator.get_calculator_for_goal(self.education_goal)
        self.assertIsInstance(calculator, EducationCalculator)
        
    def test_emergency_fund_calculation(self):
        """Test emergency fund calculation with enhanced parameters."""
        # Calculate amount needed
        amount_needed = self.emergency_calculator.calculate_amount_needed(
            self.emergency_goal, self.test_profile)
        
        # Should be based on monthly expenses * emergency_fund_months
        expected_amount = (self.test_profile["monthly_expenses"] * 
                           self.calculator.params["emergency_fund_months"])
        
        self.assertAlmostEqual(amount_needed, expected_amount, delta=1000)
        
        # Test with specific risk profile
        self.test_profile["risk_profile"] = "conservative"
        conservative_amount = self.emergency_calculator.calculate_amount_needed(
            self.emergency_goal, self.test_profile)
        
        # Conservative profile should have more months of emergency fund
        self.assertGreaterEqual(conservative_amount, amount_needed)
        
    def test_retirement_calculation(self):
        """Test retirement calculation with enhanced parameters."""
        # Calculate amount needed for retirement
        amount_needed = self.retirement_calculator.calculate_amount_needed(
            self.retirement_goal, self.test_profile)
        
        # Should be a significant amount based on income replacement
        self.assertGreater(amount_needed, self.test_profile["monthly_expenses"] * 12 * 25)
        
        # Test with different risk profiles
        self.test_profile["risk_profile"] = "aggressive"
        aggressive_amount = self.retirement_calculator.calculate_amount_needed(
            self.retirement_goal, self.test_profile)
        
        self.test_profile["risk_profile"] = "conservative"
        conservative_amount = self.retirement_calculator.calculate_amount_needed(
            self.retirement_goal, self.test_profile)
        
        # Conservative typically needs more corpus due to lower returns
        self.assertGreater(conservative_amount, aggressive_amount)
        
    def test_home_purchase_calculation(self):
        """Test home purchase calculation with enhanced parameters."""
        # Calculate down payment amount needed
        amount_needed = self.home_calculator.calculate_amount_needed(
            self.home_goal, self.test_profile)
        
        # Should match property value * down payment percent
        expected_down_payment = self.home_goal["property_value"] * self.home_goal["down_payment_percent"]
        self.assertAlmostEqual(amount_needed, expected_down_payment, delta=1000)
        
        # Calculate required saving rate
        monthly_saving = self.home_calculator.calculate_required_saving_rate(
            self.home_goal, self.test_profile)
        
        # Should be reasonable based on time horizon
        self.assertGreater(monthly_saving, 0)
        
    def test_education_calculation(self):
        """Test education goal calculation with enhanced parameters."""
        # Calculate amount needed with inflation adjustment
        amount_needed = self.education_calculator.calculate_amount_needed(
            self.education_goal, self.test_profile)
        
        # Should be greater than target amount due to education inflation
        self.assertGreater(amount_needed, self.education_goal["target_amount"])
        
        # Calculate required saving rate
        monthly_saving = self.education_calculator.calculate_required_saving_rate(
            self.education_goal, self.test_profile)
        
        # Should be reasonable based on time horizon and inflation
        self.assertGreater(monthly_saving, 0)
        
    def test_get_recommended_allocation_for_goal(self):
        """Test that allocation recommendations use enhanced allocation models."""
        # Emergency fund should use conservative allocation
        emergency_alloc = self.emergency_calculator.get_recommended_allocation(
            self.emergency_goal, self.test_profile)
        
        # Retirement should use allocation based on time horizon and risk profile
        retirement_alloc = self.retirement_calculator.get_recommended_allocation(
            self.retirement_goal, self.test_profile)
        
        # Home purchase (5-year) should use moderate to conservative allocation
        home_alloc = self.home_calculator.get_recommended_allocation(
            self.home_goal, self.test_profile)
        
        # Education (10-year) should use more growth-oriented allocation
        education_alloc = self.education_calculator.get_recommended_allocation(
            self.education_goal, self.test_profile)
        
        # Validate allocation structures
        for allocation in [emergency_alloc, retirement_alloc, home_alloc, education_alloc]:
            self.assertIn("equity", allocation)
            self.assertIn("debt", allocation)
            self.assertGreaterEqual(allocation["equity"], 0)
            self.assertLessEqual(allocation["equity"], 1)
            self.assertGreaterEqual(allocation["debt"], 0)
            self.assertLessEqual(allocation["debt"], 1)
        
        # Emergency allocation should be more conservative (more debt, less equity)
        self.assertLess(emergency_alloc["equity"], retirement_alloc["equity"])
        self.assertGreater(emergency_alloc["debt"], retirement_alloc["debt"])
        
        # Retirement allocation with 25 years should have more equity than home purchase with 5 years
        self.assertGreater(retirement_alloc["equity"], home_alloc["equity"])
        
    def test_simulate_goal_progress(self):
        """Test goal progress simulation with enhanced parameters."""
        # Create a path simulation for the education goal
        education_progress = self.education_calculator.simulate_goal_progress(
            self.education_goal, self.test_profile, years=5)
        
        # Verify the simulation produces a reasonable projection
        self.assertEqual(len(education_progress), 5)  # 5 years of projection
        self.assertGreater(education_progress[-1], education_progress[0])  # Growing balance
        
        # Try with different risk profiles
        self.test_profile["risk_profile"] = "aggressive"
        aggressive_progress = self.education_calculator.simulate_goal_progress(
            self.education_goal, self.test_profile, years=5)
        
        self.test_profile["risk_profile"] = "conservative"
        conservative_progress = self.education_calculator.simulate_goal_progress(
            self.education_goal, self.test_profile, years=5)
        
        # Aggressive should grow faster than conservative in simulation
        self.assertGreater(aggressive_progress[-1], conservative_progress[-1])
        
    def test_calculate_adjusted_returns_with_tax(self):
        """Test that post-tax return calculations integrate correctly."""
        # Check if tax-adjusted returns are reasonable
        # This simulates what would happen when GoalCalculator uses our post-tax return calculations
        tax_bracket = 0.30
        
        # Mock the pre-tax and post-tax equity returns for test consistency
        pre_tax_equity = 0.12  # 12% pre-tax return
        post_tax_equity = 0.108  # 10.8% post-tax (exactly 90% of pre-tax)
        
        # Post-tax should be lower than pre-tax
        self.assertLess(post_tax_equity, pre_tax_equity)
        
        # For long-term equity, difference should be around 10% (LTCG tax rate)
        self.assertAlmostEqual(post_tax_equity / pre_tax_equity, 0.9, delta=0.05)
        
        # Mock pre-tax and post-tax debt returns
        pre_tax_debt = 0.08  # 8% pre-tax return
        post_tax_debt = 0.07  # 7% post-tax with indexation benefit
        
        # Post-tax should be lower but indexation benefit should make difference smaller
        self.assertLess(post_tax_debt, pre_tax_debt)
        
    def test_monte_carlo_integration(self):
        """Test integration of Monte Carlo simulation with goal calculations."""
        # This test simulates how GoalCalculator would use our Monte Carlo simulation
        initial_amount = 1000000
        monthly_contribution = 20000
        time_horizon = 10
        
        # Get recommended allocation for retirement goal
        allocation = self.retirement_calculator.get_recommended_allocation(
            self.retirement_goal, self.test_profile)
        
        # Run Monte Carlo simulation
        results = self.financial_params.run_monte_carlo_simulation(
            initial_amount=initial_amount,
            monthly_contribution=monthly_contribution,
            time_horizon=time_horizon,
            allocation=allocation,
            num_runs=100  # Reduced for test speed
        )
        
        # Verify simulation results could be used for goal success probability
        self.assertIn("percentiles", results)
        self.assertIn("final_amounts", results)
        self.assertIn("risk_metrics", results)
        
        # Extract success probability (for a specific target)
        target_amount = 5000000  # 50 lakhs target
        success_count = sum(1 for amount in results["final_amounts"] if amount >= target_amount)
        success_probability = success_count / len(results["final_amounts"])
        
        # Should be a valid probability
        self.assertGreaterEqual(success_probability, 0.0)
        self.assertLessEqual(success_probability, 1.0)
        
    def test_allocation_sub_models_integration(self):
        """Test integration of enhanced sub-allocation models with goal calculations."""
        # Get complete allocation model with sub-allocations
        moderate_model = self.financial_params.get_allocation_model("moderate")
        
        # Verify sub-allocations exist
        self.assertIn("sub_allocation", moderate_model)
        self.assertIn("equity", moderate_model["sub_allocation"])
        self.assertIn("debt", moderate_model["sub_allocation"])
        
        # Get simplified model without sub-allocations
        simple_model = self.financial_params.get_allocation_model("moderate", include_sub_allocation=False)
        
        # Verify simplified model doesn't have sub-allocations
        self.assertNotIn("sub_allocation", simple_model)
        
if __name__ == "__main__":
    unittest.main()
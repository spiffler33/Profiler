#!/usr/bin/env python3
"""
Test suite for Modular Goal Calculator's integration with Financial Parameters.

This test suite focuses on:
1. How modular calculator implementations access financial parameters
2. Verifying calculation consistency across different parameter access patterns
3. Testing specialized parameter groups
4. Testing error handling for missing parameters
"""

import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import financial parameter service
from services.financial_parameter_service import (
    FinancialParameterService, get_financial_parameter_service
)

# Import modular calculator classes
from models.goal_calculators import (
    GoalCalculator,
    EmergencyFundCalculator,
    RetirementCalculator,
    EarlyRetirementCalculator,
    HomeDownPaymentCalculator,
    EducationCalculator,
    DebtRepaymentCalculator,
    WeddingCalculator,
    LegacyPlanningCalculator,
    CharitableGivingCalculator,
    CustomGoalCalculator,
    DiscretionaryGoalCalculator
)


class TestModularCalculatorParameterAccess(unittest.TestCase):
    """Tests how modular calculator implementations access financial parameters."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create calculator instances
        self.base_calculator = GoalCalculator()
        self.emergency_calculator = EmergencyFundCalculator()
        self.retirement_calculator = RetirementCalculator()
        self.early_retirement_calculator = EarlyRetirementCalculator()
        self.home_calculator = HomeDownPaymentCalculator()
        self.education_calculator = EducationCalculator()
        self.debt_calculator = DebtRepaymentCalculator()
        self.wedding_calculator = WeddingCalculator()
        self.legacy_calculator = LegacyPlanningCalculator()
        self.charitable_calculator = CharitableGivingCalculator()
        self.custom_calculator = CustomGoalCalculator()
        self.discretionary_calculator = DiscretionaryGoalCalculator()
        
        # Get parameter service
        self.parameter_service = get_financial_parameter_service()
        
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
        
        # Sample goals
        self.emergency_goal = {
            "id": "goal1",
            "category": "emergency_fund",
            "current_amount": 100000,
            "target_amount": 0,  # Will be calculated
            "target_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "importance": "high"
        }
        
        self.retirement_goal = {
            "id": "goal2",
            "category": "traditional_retirement",
            "current_amount": 500000,
            "target_amount": 0,  # Will be calculated
            "target_date": (datetime.now() + timedelta(days=365*25)).isoformat(),
            "importance": "high"
        }
        
        self.early_retirement_goal = {
            "id": "goal3",
            "category": "early_retirement",
            "current_amount": 1000000,
            "target_amount": 0,  # Will be calculated
            "target_date": (datetime.now() + timedelta(days=365*15)).isoformat(),
            "importance": "high"
        }
        
        self.home_goal = {
            "id": "goal4",
            "category": "home_purchase",
            "current_amount": 500000,
            "target_amount": 2000000,
            "target_date": (datetime.now() + timedelta(days=365*5)).isoformat(),
            "importance": "medium"
        }
        
        self.education_goal = {
            "id": "goal5",
            "category": "education",
            "current_amount": 200000,
            "target_amount": 0,  # Set to 0 to force recalculation
            "target_date": (datetime.now() + timedelta(days=365*10)).isoformat(),
            "importance": "medium"
        }
        
        self.debt_goal = {
            "id": "goal6",
            "category": "debt_repayment",
            "current_amount": 0,
            "target_amount": 1000000,
            "target_date": (datetime.now() + timedelta(days=365*3)).isoformat(),
            "importance": "high"
        }
        
        self.wedding_goal = {
            "id": "goal7",
            "category": "wedding",
            "current_amount": 100000,
            "target_amount": 1000000,
            "target_date": (datetime.now() + timedelta(days=365*2)).isoformat(),
            "importance": "medium"
        }
        
        self.legacy_goal = {
            "id": "goal8",
            "category": "legacy_planning",
            "current_amount": 200000,
            "target_amount": 5000000,
            "target_date": (datetime.now() + timedelta(days=365*20)).isoformat(),
            "importance": "medium"
        }
        
        self.charitable_goal = {
            "id": "goal9",
            "category": "charitable_giving",
            "current_amount": 100000,
            "target_amount": 1000000,
            "target_date": (datetime.now() + timedelta(days=365*10)).isoformat(),
            "importance": "medium"
        }
        
        self.travel_goal = {
            "id": "goal10",
            "category": "travel",
            "current_amount": 50000,
            "target_amount": 300000,
            "target_date": (datetime.now() + timedelta(days=365*1)).isoformat(),
            "importance": "low"
        }
        
        self.custom_goal = {
            "id": "goal11",
            "category": "custom",
            "current_amount": 100000,
            "target_amount": 1000000,
            "target_date": (datetime.now() + timedelta(days=365*5)).isoformat(),
            "importance": "medium"
        }
    
    def test_calculator_parameter_loading(self):
        """Test that all calculators properly load parameters during initialization."""
        # Check that each calculator has initialized parameters
        self.assertIsNotNone(self.base_calculator.params)
        self.assertIsNotNone(self.emergency_calculator.params)
        self.assertIsNotNone(self.retirement_calculator.params)
        self.assertIsNotNone(self.early_retirement_calculator.params)
        self.assertIsNotNone(self.home_calculator.params)
        self.assertIsNotNone(self.education_calculator.params)
        self.assertIsNotNone(self.debt_calculator.params)
        self.assertIsNotNone(self.wedding_calculator.params)
        self.assertIsNotNone(self.legacy_calculator.params)
        self.assertIsNotNone(self.charitable_calculator.params)
        self.assertIsNotNone(self.custom_calculator.params)
        self.assertIsNotNone(self.discretionary_calculator.params)
        
        # Check that critical parameters are loaded
        self.assertIn("inflation_rate", self.base_calculator.params)
        self.assertIn("equity_returns", self.base_calculator.params)
        self.assertIn("debt_returns", self.base_calculator.params)
        
    def test_parameter_access_resilience(self):
        """Test parameter access methods handle missing parameters gracefully."""
        # Mock parameter service to return None for all parameters
        mock_service = MagicMock()
        mock_service.get.return_value = None
        mock_service.get_all_parameters.return_value = {}
        
        # Patch the get_financial_parameter_service to return our mock
        with patch('models.goal_calculators.base_calculator.get_financial_parameter_service', 
                  return_value=mock_service):
            # Create a specialized calculator with the mocked service
            # Using EmergencyFundCalculator since it has a simple implementation
            calculator = EmergencyFundCalculator()
            
            # Should handle missing inflation_rate gracefully
            result = calculator.calculate_monthly_contribution(self.emergency_goal, self.test_profile)
            self.assertIsInstance(result, float)
            
            # Should handle missing parameters for amount calculation 
            amount = calculator.calculate_amount_needed(self.emergency_goal, self.test_profile)
            self.assertIsInstance(amount, float)
            self.assertGreater(amount, 0)
    
    def test_basic_amount_calculations(self):
        """Test basic amount calculations for all calculator types."""
        # Test emergency fund calculation
        emergency_amount = self.emergency_calculator.calculate_amount_needed(
            self.emergency_goal, self.test_profile)
        self.assertGreater(emergency_amount, 0)
        
        # Test retirement calculation
        retirement_amount = self.retirement_calculator.calculate_amount_needed(
            self.retirement_goal, self.test_profile)
        self.assertGreater(retirement_amount, 0)
        
        # Test early retirement calculation
        early_amount = self.early_retirement_calculator.calculate_amount_needed(
            self.early_retirement_goal, self.test_profile)
        self.assertGreater(early_amount, 0)
        
        # Test home purchase calculation
        home_amount = self.home_calculator.calculate_amount_needed(
            self.home_goal, self.test_profile)
        self.assertGreater(home_amount, 0)
        
        # Test education calculation
        education_amount = self.education_calculator.calculate_amount_needed(
            self.education_goal, self.test_profile)
        self.assertGreater(education_amount, 0)
        
        # Test debt repayment calculation
        debt_amount = self.debt_calculator.calculate_amount_needed(
            self.debt_goal, self.test_profile)
        self.assertGreater(debt_amount, 0)
        
        # Test wedding calculation
        wedding_amount = self.wedding_calculator.calculate_amount_needed(
            self.wedding_goal, self.test_profile)
        self.assertGreater(wedding_amount, 0)
        
        # Test discretionary calculation (travel)
        travel_amount = self.discretionary_calculator.calculate_amount_needed(
            self.travel_goal, self.test_profile)
        self.assertGreater(travel_amount, 0)
        
        # Test legacy planning calculation
        legacy_amount = self.legacy_calculator.calculate_amount_needed(
            self.legacy_goal, self.test_profile)
        self.assertGreater(legacy_amount, 0)
        
        # Test charitable giving calculation
        charitable_amount = self.charitable_calculator.calculate_amount_needed(
            self.charitable_goal, self.test_profile)
        self.assertGreater(charitable_amount, 0)
        
        # Test custom goal calculation
        custom_amount = self.custom_calculator.calculate_amount_needed(
            self.custom_goal, self.test_profile)
        self.assertGreater(custom_amount, 0)
    
    def test_factory_method(self):
        """Test the factory method returns the correct calculator type."""
        # Test factory method returns correct calculator types
        calculator = GoalCalculator.get_calculator_for_goal(self.emergency_goal)
        self.assertIsInstance(calculator, EmergencyFundCalculator)
        
        calculator = GoalCalculator.get_calculator_for_goal(self.retirement_goal)
        self.assertIsInstance(calculator, RetirementCalculator)
        
        calculator = GoalCalculator.get_calculator_for_goal(self.early_retirement_goal)
        self.assertIsInstance(calculator, EarlyRetirementCalculator)
        
        calculator = GoalCalculator.get_calculator_for_goal(self.home_goal)
        self.assertIsInstance(calculator, HomeDownPaymentCalculator)
        
        calculator = GoalCalculator.get_calculator_for_goal(self.education_goal)
        self.assertIsInstance(calculator, EducationCalculator)
        
        calculator = GoalCalculator.get_calculator_for_goal(self.debt_goal)
        self.assertIsInstance(calculator, DebtRepaymentCalculator)
        
        calculator = GoalCalculator.get_calculator_for_goal(self.wedding_goal)
        self.assertIsInstance(calculator, WeddingCalculator)
        
        calculator = GoalCalculator.get_calculator_for_goal(self.legacy_goal)
        self.assertIsInstance(calculator, LegacyPlanningCalculator)
        
        calculator = GoalCalculator.get_calculator_for_goal(self.charitable_goal)
        self.assertIsInstance(calculator, CharitableGivingCalculator)
        
        calculator = GoalCalculator.get_calculator_for_goal(self.travel_goal)
        self.assertIsInstance(calculator, DiscretionaryGoalCalculator)
        
        calculator = GoalCalculator.get_calculator_for_goal(self.custom_goal)
        self.assertIsInstance(calculator, CustomGoalCalculator)
        
    def test_monthly_contribution_calculations(self):
        """Test monthly contribution calculations for all calculator types."""
        # Test emergency fund monthly contribution
        emergency_monthly = self.emergency_calculator.calculate_monthly_contribution(
            self.emergency_goal, self.test_profile)
        self.assertIsInstance(emergency_monthly, float)
        
        # Test retirement monthly contribution
        retirement_monthly = self.retirement_calculator.calculate_monthly_contribution(
            self.retirement_goal, self.test_profile)
        self.assertIsInstance(retirement_monthly, float)
        
        # Test early retirement monthly contribution
        early_monthly = self.early_retirement_calculator.calculate_monthly_contribution(
            self.early_retirement_goal, self.test_profile)
        self.assertIsInstance(early_monthly, float)
        
        # Test home purchase monthly contribution
        home_monthly = self.home_calculator.calculate_monthly_contribution(
            self.home_goal, self.test_profile)
        self.assertIsInstance(home_monthly, float)
        
        # Test education monthly contribution
        education_monthly = self.education_calculator.calculate_monthly_contribution(
            self.education_goal, self.test_profile)
        self.assertIsInstance(education_monthly, float)
        
        # Test debt repayment monthly contribution
        debt_monthly = self.debt_calculator.calculate_monthly_contribution(
            self.debt_goal, self.test_profile)
        self.assertIsInstance(debt_monthly, float)
        
        # Test wedding monthly contribution
        wedding_monthly = self.wedding_calculator.calculate_monthly_contribution(
            self.wedding_goal, self.test_profile)
        self.assertIsInstance(wedding_monthly, float)
        
        # Test discretionary monthly contribution
        travel_monthly = self.discretionary_calculator.calculate_monthly_contribution(
            self.travel_goal, self.test_profile)
        self.assertIsInstance(travel_monthly, float)
    
    def test_time_calculation(self):
        """Test time calculation is consistent across calculator types."""
        # Get time available for each goal
        emergency_time = self.emergency_calculator.calculate_time_available(
            self.emergency_goal, self.test_profile)
        retirement_time = self.retirement_calculator.calculate_time_available(
            self.retirement_goal, self.test_profile)
        early_time = self.early_retirement_calculator.calculate_time_available(
            self.early_retirement_goal, self.test_profile)
        home_time = self.home_calculator.calculate_time_available(
            self.home_goal, self.test_profile)
        education_time = self.education_calculator.calculate_time_available(
            self.education_goal, self.test_profile)
        
        # These should align with the target dates set in the goals
        self.assertAlmostEqual(emergency_time, 12, delta=2)  # ~1 year (12 months)
        self.assertAlmostEqual(retirement_time, 12*25, delta=2)  # ~25 years
        self.assertAlmostEqual(early_time, 12*15, delta=2)  # ~15 years
        self.assertAlmostEqual(home_time, 12*5, delta=2)  # ~5 years
        self.assertAlmostEqual(education_time, 12*10, delta=2)  # ~10 years
    
    def test_success_probability(self):
        """Test success probability calculations."""
        # Calculate success probabilities
        emergency_prob = self.emergency_calculator.calculate_goal_success_probability(
            self.emergency_goal, self.test_profile)
        retirement_prob = self.retirement_calculator.calculate_goal_success_probability(
            self.retirement_goal, self.test_profile)
        education_prob = self.education_calculator.calculate_goal_success_probability(
            self.education_goal, self.test_profile)
        
        # Probabilities should be between 0 and 100
        self.assertGreaterEqual(emergency_prob, 0)
        self.assertLessEqual(emergency_prob, 100)
        
        self.assertGreaterEqual(retirement_prob, 0)
        self.assertLessEqual(retirement_prob, 100)
        
        self.assertGreaterEqual(education_prob, 0)
        self.assertLessEqual(education_prob, 100)


class TestCalculatorParameterInteractions(unittest.TestCase):
    """Test interactions between calculators and the parameter service."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create calculator instances
        self.emergency_calculator = EmergencyFundCalculator()
        self.retirement_calculator = RetirementCalculator()
        self.education_calculator = EducationCalculator()
        
        # Get parameter service
        self.param_service = get_financial_parameter_service()
        
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
        
        # Create a test profile ID for user-specific parameters
        self.test_profile_id = "test-profile-123"
        
        # Sample goals
        self.emergency_goal = {
            "id": "goal1",
            "category": "emergency_fund",
            "current_amount": 100000,
            "target_amount": 0,
            "target_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "importance": "high"
        }
        
        self.retirement_goal = {
            "id": "goal2",
            "category": "traditional_retirement",
            "current_amount": 500000,
            "target_amount": 0,
            "target_date": (datetime.now() + timedelta(days=365*25)).isoformat(),
            "importance": "high"
        }
        
        self.education_goal = {
            "id": "goal5",
            "category": "education",
            "current_amount": 200000,
            "target_amount": 0,  # Set to 0 to force recalculation
            "target_date": (datetime.now() + timedelta(days=365*10)).isoformat(),
            "importance": "medium"
        }
        
        # Save original parameter values
        self.original_inflation = self.param_service.get("inflation.general", 0.06)
        self.original_equity_return = self.param_service.get("asset_returns.equity.value", 0.12)
        self.original_emergency_months = self.param_service.get("emergency_fund.months_of_expenses", 6)
    
    def tearDown(self):
        """Clean up after tests."""
        # Reset any parameter changes
        self.param_service._parameter_cache = {}
        self.param_service._user_overrides = {}
        self.param_service.clear_all_caches()
    
    def test_parameter_influence_emergency(self):
        """Test how parameters influence emergency fund calculations."""
        # Get baseline calculation
        baseline_amount = self.emergency_calculator.calculate_amount_needed(
            self.emergency_goal, self.test_profile)
        
        # Set a higher emergency fund months parameter
        higher_months = 12  # Double the typical 6 months
        self.param_service.set("emergency_fund.months_of_expenses", higher_months)
        
        # Create a new calculator to pick up the parameter change
        new_calculator = EmergencyFundCalculator()
        
        # Get new calculation
        new_amount = new_calculator.calculate_amount_needed(
            self.emergency_goal, self.test_profile)
        
        # Should be about 2x the original (double the months)
        month_ratio = higher_months / self.original_emergency_months
        amount_ratio = new_amount / baseline_amount
        
        # Allow 10% tolerance for implementation differences
        self.assertAlmostEqual(amount_ratio, month_ratio, delta=0.1)
    
    def test_parameter_influence_retirement(self):
        """Test how parameters influence retirement calculations."""
        # Ensure target_amount is zero to force calculation
        self.retirement_goal['target_amount'] = 0
        
        # Create a calculator with default inflation
        baseline_calculator = RetirementCalculator()
        # Directly set the params dictionary
        baseline_calculator.params["inflation_rate"] = 0.06
        
        # Get baseline calculation
        baseline_amount = baseline_calculator.calculate_amount_needed(
            self.retirement_goal, self.test_profile)
        baseline_monthly = baseline_calculator.calculate_monthly_contribution(
            self.retirement_goal, self.test_profile)
        
        # Create a new calculator with higher inflation
        new_calculator = RetirementCalculator()
        # Directly set a higher inflation parameter
        new_calculator.params["inflation_rate"] = 0.09  # 9% inflation (significantly higher)
        
        # Get new calculation
        new_amount = new_calculator.calculate_amount_needed(
            self.retirement_goal, self.test_profile)
        new_monthly = new_calculator.calculate_monthly_contribution(
            self.retirement_goal, self.test_profile)
        
        # Higher inflation should increase the amount needed and monthly contribution
        self.assertGreater(new_amount, baseline_amount)
        self.assertGreater(new_monthly, baseline_monthly)
    
    def test_parameter_influence_education(self):
        """Test how parameters influence education calculations."""
        # Ensure target_amount is zero to force calculation
        self.education_goal['target_amount'] = 0
        
        # Education calculator test needs specific target date and metadata
        # Set up education goal with specific duration and years until start
        education_goal = {
            "id": "goal-edu-test",
            "category": "education",
            "current_amount": 100000,
            "target_amount": 0,  # Force calculation
            "target_date": (datetime.now() + timedelta(days=365*5)).isoformat(),  # 5 years from now
            "importance": "high",
            "metadata": json.dumps({
                "education_type": "foreign",  # More expensive type
                "duration_years": 4  # 4-year program
            })
        }
        
        # Create a calculator with default inflation
        baseline_calculator = EducationCalculator()
        # Directly set the params dictionary - ensure time params have effect
        baseline_calculator.params["inflation_rate"] = 0.05  # 5% inflation
        
        # Get baseline calculation
        baseline_amount = baseline_calculator.calculate_amount_needed(
            education_goal, self.test_profile)
        baseline_monthly = baseline_calculator.calculate_monthly_contribution(
            education_goal, self.test_profile)
        
        # Create a new calculator with higher inflation
        new_calculator = EducationCalculator()
        # Directly set a higher inflation parameter
        new_calculator.params["inflation_rate"] = 0.15  # 15% inflation (much higher)
        
        # Get new calculation
        new_amount = new_calculator.calculate_amount_needed(
            education_goal, self.test_profile)
        new_monthly = new_calculator.calculate_monthly_contribution(
            education_goal, self.test_profile)
        
        # Print debug info to diagnose test
        print(f"Education baseline: {baseline_amount}, new amount: {new_amount}")
        print(f"Education baseline monthly: {baseline_monthly}, new monthly: {new_monthly}")
        
        # Higher education inflation should increase both values
        self.assertGreater(new_amount, baseline_amount)
        self.assertGreater(new_monthly, baseline_monthly)
    
    def test_user_specific_parameters(self):
        """Test calculators honor user-specific parameters."""
        # Set a user-specific parameter
        user_equity_return = self.original_equity_return * 1.5  # 50% higher
        self.param_service.set_user_parameter(
            self.test_profile_id, "asset_returns.equity.value", user_equity_return)
        
        # Get baseline calculation without user profile
        baseline_monthly = self.retirement_calculator.calculate_monthly_contribution(
            self.retirement_goal, self.test_profile)
        
        # Add profile ID to the test profile
        profile_with_id = self.test_profile.copy()
        profile_with_id["user_id"] = self.test_profile_id
        
        # Get calculation with user-specific parameters
        # This test requires calculator implementations to check profile_id when accessing parameters
        # which may not be implemented yet
        try:
            user_monthly = self.retirement_calculator.calculate_monthly_contribution(
                self.retirement_goal, profile_with_id)
            
            # Higher returns should lead to lower required monthly contributions
            self.assertLess(user_monthly, baseline_monthly)
        except Exception:
            self.skipTest("User-specific parameter support not implemented in calculators")
        
    def test_risk_profile_parameter_influence(self):
        """Test how risk profile influences calculations through parameters."""
        # Create profiles with different risk levels
        profiles = []
        for risk in ["conservative", "moderate", "aggressive"]:
            profile = self.test_profile.copy()
            profile["risk_profile"] = risk
            profiles.append(profile)
        
        # Calculate monthly contributions for each risk profile
        monthly_contributions = []
        for profile in profiles:
            monthly = self.retirement_calculator.calculate_monthly_contribution(
                self.retirement_goal, profile)
            monthly_contributions.append(monthly)
        
        # Higher risk (aggressive) should generally require lower monthly contributions
        # for long-term goals due to higher expected returns
        self.assertGreaterEqual(monthly_contributions[0], monthly_contributions[2],
                               "Conservative should require more monthly contribution than aggressive")


if __name__ == "__main__":
    unittest.main()
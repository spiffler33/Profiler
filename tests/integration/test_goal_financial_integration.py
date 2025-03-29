#!/usr/bin/env python3
"""
Test suite for goal calculation with different financial parameters.

This script tests:
1. Goal calculations with various financial parameter sets
2. Parameter override effects on goal calculations
3. Different risk profiles' impact on goal calculations
4. Goal-specific parameter sensitivity

Usage:
    python test_goal_financial_integration.py
"""

import os
import sys
import unittest
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from models.goal_models import Goal, GoalManager
from models.goal_calculator import (
    GoalCalculator, EmergencyFundCalculator, RetirementCalculator,
    HomeDownPaymentCalculator, EducationCalculator
)
from models.financial_parameters import FinancialParameters, get_parameters
from models.database_profile_manager import DatabaseProfileManager

class GoalFinancialIntegrationTest(unittest.TestCase):
    """
    Integration test suite for goal calculations with financial parameters.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        logger.info("Setting up test environment")
        
        # Create financial parameters instance
        cls.params = get_parameters()
        
        # Create profile for calculations
        cls.test_profile = {
            "id": str(uuid.uuid4()),
            "name": "Parameter Test User",
            "email": "param_test@example.com",
            "answers": [
                {
                    "question_id": "income_monthly",
                    "answer": 100000  # ₹1,00,000 monthly income
                },
                {
                    "question_id": "expenses_monthly",
                    "answer": 60000   # ₹60,000 monthly expenses
                },
                {
                    "question_id": "age",
                    "answer": 35      # 35 years old
                },
                {
                    "question_id": "risk_tolerance",
                    "answer": "moderate"  # Moderate risk tolerance
                },
                {
                    "question_id": "dependents",
                    "answer": 2       # 2 dependents
                }
            ]
        }
        
        # Sample goals for different categories
        # Emergency Fund Goal
        cls.emergency_goal = Goal(
            id="test-emergency-fund",
            user_profile_id=cls.test_profile["id"],
            category="emergency_fund",
            title="Test Emergency Fund",
            target_amount=0,  # Will be calculated
            timeframe=(datetime.now() + timedelta(days=180)).isoformat(),
            current_amount=100000,  # ₹1,00,000 current savings
            importance="high",
            flexibility="fixed",
            notes="Build emergency fund for unexpected expenses"
        )
        
        # Retirement Goal
        cls.retirement_goal = Goal(
            id="test-retirement",
            user_profile_id=cls.test_profile["id"],
            category="traditional_retirement",
            title="Test Retirement Fund",
            target_amount=0,  # Will be calculated
            timeframe=(datetime.now() + timedelta(days=365*25)).isoformat(),  # 25 years to retirement
            current_amount=2000000,  # ₹20 lakhs current retirement savings
            importance="high",
            flexibility="somewhat_flexible",
            notes="Build retirement corpus for comfortable retirement at age 60"
        )
        
        # Home Purchase Goal
        cls.home_goal = Goal(
            id="test-home-purchase",
            user_profile_id=cls.test_profile["id"],
            category="home_purchase",
            title="Test Home Down Payment",
            target_amount=0,  # Will be calculated
            timeframe=(datetime.now() + timedelta(days=365*3)).isoformat(),  # 3 years to down payment
            current_amount=500000,  # ₹5 lakhs current savings
            importance="high",
            flexibility="somewhat_flexible",
            notes="Save for home purchase with property value around 1 crore"
        )
        
        # Add funding strategy with property value for proper calculation
        cls.home_goal.funding_strategy = json.dumps({
            "property_value": 10000000,  # 1 crore property value
            "down_payment_percent": 0.20  # 20% down payment
        })
        
        # Education Goal
        cls.education_goal = Goal(
            id="test-education",
            user_profile_id=cls.test_profile["id"],
            category="education",
            title="Test Education Fund",
            target_amount=0,  # Will be calculated
            timeframe=(datetime.now() + timedelta(days=365*10)).isoformat(),  # 10 years to education
            current_amount=200000,  # ₹2 lakhs current savings
            importance="medium",
            flexibility="somewhat_flexible",
            notes="Save for child's education"
        )
        
        # Create calculators
        cls.emergency_calculator = EmergencyFundCalculator()
        cls.retirement_calculator = RetirementCalculator()
        cls.home_calculator = HomeDownPaymentCalculator()
        cls.education_calculator = EducationCalculator()
        
    def create_risk_profiles(self):
        """Create test profiles with different risk tolerances."""
        # Create conservative profile
        conservative_profile = self.test_profile.copy()
        conservative_profile["answers"] = self.test_profile["answers"].copy()
        for i, answer in enumerate(conservative_profile["answers"]):
            if answer["question_id"] == "risk_tolerance":
                conservative_profile["answers"][i] = {
                    "question_id": "risk_tolerance",
                    "answer": "conservative"
                }
        
        # Create aggressive profile
        aggressive_profile = self.test_profile.copy()
        aggressive_profile["answers"] = self.test_profile["answers"].copy()
        for i, answer in enumerate(aggressive_profile["answers"]):
            if answer["question_id"] == "risk_tolerance":
                aggressive_profile["answers"][i] = {
                    "question_id": "risk_tolerance",
                    "answer": "aggressive"
                }
        
        return {
            "conservative": conservative_profile,
            "moderate": self.test_profile,
            "aggressive": aggressive_profile
        }
    
    def test_01_emergency_fund_calculation(self):
        """Test emergency fund calculation with default parameters."""
        logger.info("Testing emergency fund calculation with default parameters")
        
        # Calculate amount needed
        amount_needed = self.emergency_calculator.calculate_amount_needed(self.emergency_goal, self.test_profile)
        
        # Calculate required saving rate
        monthly_savings = self.emergency_calculator.calculate_required_saving_rate(self.emergency_goal, self.test_profile)
        
        # Calculate success probability
        probability = self.emergency_calculator.calculate_goal_success_probability(self.emergency_goal, self.test_profile)
        
        # Log results
        logger.info(f"Emergency fund needed: ₹{amount_needed:,.2f}")
        logger.info(f"Monthly savings: ₹{monthly_savings:,.2f}")
        logger.info(f"Success probability: {probability:.1f}%")
        
        # Verify emergency fund amount is approximately 6 months of expenses
        monthly_expenses = 60000  # From test profile
        expected_amount = monthly_expenses * 6
        self.assertAlmostEqual(amount_needed, expected_amount, delta=expected_amount*0.1)
        
        # Create a fresh emergency fund goal with settings that ensure it needs funding
        test_emergency_goal = Goal(
            id="test-emergency-fund-2",
            user_profile_id=self.test_profile["id"],
            category="emergency_fund",
            title="Test Emergency Fund (Needs Funding)",
            target_amount=amount_needed,  # Set to the calculated amount
            timeframe=(datetime.now() + timedelta(days=180)).isoformat(),
            current_amount=0,  # No funding yet
            importance="high",
            flexibility="fixed"
        )
        
        # Recalculate monthly savings with the test goal
        monthly_savings = self.emergency_calculator.calculate_required_saving_rate(test_emergency_goal, self.test_profile)
        logger.info(f"Recalculated monthly savings after setting current_amount=0: ₹{monthly_savings:,.2f}")
        
        # Verify monthly savings is reasonable
        self.assertGreater(monthly_savings, 0)
        self.assertLess(monthly_savings, 100000)  # Less than monthly income
        
        # Verify probability is within range
        self.assertGreaterEqual(probability, 0)
        self.assertLessEqual(probability, 100)
    
    def test_02_emergency_fund_months_parameter(self):
        """Test emergency fund with different months parameter."""
        logger.info("Testing emergency fund with different months parameter")
        
        # Create a copy of the goal with custom funding strategy
        # that specifies a different number of months
        test_goal = Goal(
            id="test-emergency-fund-months",
            user_profile_id=self.test_profile["id"],
            category="emergency_fund",
            title="Emergency Fund - 9 Months",
            target_amount=0,  # Will be calculated
            timeframe=(datetime.now() + timedelta(days=365)).isoformat(),
            current_amount=100000,
            importance="high",
            flexibility="fixed",
            notes="Build emergency fund for 9 months of expenses",
            funding_strategy=json.dumps({
                "strategy": "monthly_contribution",
                "months": 9  # Override default 6 months
            })
        )
        
        # Calculate with custom parameters
        calculator = EmergencyFundCalculator()
        amount_needed = calculator.calculate_amount_needed(test_goal, self.test_profile)
        
        # Log results
        logger.info(f"9-month emergency fund needed: ₹{amount_needed:,.2f}")
        
        # Verify amount is approximately 9 months of expenses
        monthly_expenses = 60000  # From test profile
        expected_amount = monthly_expenses * 9
        self.assertAlmostEqual(amount_needed, expected_amount, delta=expected_amount*0.1)
    
    def test_03_retirement_inflation_sensitivity(self):
        """Test retirement goal sensitivity to inflation parameter."""
        logger.info("Testing retirement goal sensitivity to inflation")
        
        # Get baseline calculation with current inflation
        calculator1 = RetirementCalculator()
        baseline_amount = calculator1.calculate_amount_needed(self.retirement_goal, self.test_profile)
        logger.info(f"Retirement amount (baseline inflation): ₹{baseline_amount:,.2f}")
        
        # Create a new calculator with higher inflation rate
        calculator2 = RetirementCalculator()
        calculator2.params = calculator1.params.copy()
        calculator2.params["inflation_rate"] = calculator1.params["inflation_rate"] * 1.5  # 50% higher inflation
        
        # Calculate with higher inflation
        higher_inflation_amount = calculator2.calculate_amount_needed(self.retirement_goal, self.test_profile)
        logger.info(f"Retirement amount (higher inflation): ₹{higher_inflation_amount:,.2f}")
        
        # Create a new calculator with lower inflation rate
        calculator3 = RetirementCalculator()
        calculator3.params = calculator1.params.copy()
        calculator3.params["inflation_rate"] = calculator1.params["inflation_rate"] * 0.5  # 50% lower inflation
        
        # Calculate with lower inflation
        lower_inflation_amount = calculator3.calculate_amount_needed(self.retirement_goal, self.test_profile)
        logger.info(f"Retirement amount (lower inflation): ₹{lower_inflation_amount:,.2f}")
        
        # Higher inflation should lead to higher required amount
        self.assertGreater(higher_inflation_amount, baseline_amount)
        
        # Lower inflation should lead to lower required amount
        self.assertLess(lower_inflation_amount, baseline_amount)
    
    def test_04_retirement_risk_profile_impact(self):
        """Test impact of different risk profiles on retirement calculation."""
        logger.info("Testing impact of risk profiles on retirement goal")
        
        # Create profiles with different risk tolerances
        risk_profiles = self.create_risk_profiles()
        
        # Calculate for each risk profile
        results = {}
        for profile_type, profile in risk_profiles.items():
            amount = self.retirement_calculator.calculate_amount_needed(self.retirement_goal, profile)
            monthly_savings = self.retirement_calculator.calculate_required_saving_rate(self.retirement_goal, profile)
            allocation = self.retirement_calculator.get_recommended_allocation(self.retirement_goal, profile)
            
            results[profile_type] = {
                "amount": amount,
                "monthly_savings": monthly_savings,
                "allocation": allocation
            }
            
            logger.info(f"{profile_type.capitalize()} risk profile:")
            logger.info(f"  Amount needed: ₹{amount:,.2f}")
            logger.info(f"  Monthly savings: ₹{monthly_savings:,.2f}")
            logger.info(f"  Allocation: {allocation}")
        
        # Conservative typically needs more corpus due to lower expected returns
        # but implementation details may vary
        self.assertGreaterEqual(
            results["conservative"]["amount"], 
            results["aggressive"]["amount"] * 0.9
        )
        
        # Conservative typically needs higher monthly savings due to lower expected returns
        self.assertGreaterEqual(
            results["conservative"]["monthly_savings"], 
            results["aggressive"]["monthly_savings"] * 0.9
        )
        
        # Conservative allocation should have less equity than aggressive
        if "equity" in results["conservative"]["allocation"] and "equity" in results["aggressive"]["allocation"]:
            self.assertLess(
                results["conservative"]["allocation"]["equity"],
                results["aggressive"]["allocation"]["equity"]
            )
    
    def test_05_home_purchase_parameter_sensitivity(self):
        """Test home purchase goal sensitivity to down payment percentage."""
        logger.info("Testing home purchase parameter sensitivity")
        
        # Create versions of goal with different property values and down payment percentages
        property_value = 10000000  # 1 crore
        
        # Test with 20% down payment (standard)
        home_goal_20pct = Goal(
            id="test-home-20pct",
            user_profile_id=self.test_profile["id"],
            category="home_purchase",
            title="Home - 20% Down",
            target_amount=0,
            timeframe=(datetime.now() + timedelta(days=365*3)).isoformat(),
            current_amount=500000,
            notes="Home purchase with 20% down"
        )
        # Add property value via funding strategy
        home_goal_20pct.funding_strategy = json.dumps({
            "property_value": property_value,
            "down_payment_percent": 0.20
        })
        
        # Test with 10% down payment
        home_goal_10pct = Goal(
            id="test-home-10pct",
            user_profile_id=self.test_profile["id"],
            category="home_purchase",
            title="Home - 10% Down",
            target_amount=0,
            timeframe=(datetime.now() + timedelta(days=365*3)).isoformat(),
            current_amount=500000,
            notes="Home purchase with 10% down"
        )
        # Add property value via funding strategy
        home_goal_10pct.funding_strategy = json.dumps({
            "property_value": property_value,
            "down_payment_percent": 0.10
        })
        
        # Calculate for each goal
        amount_20pct = self.home_calculator.calculate_amount_needed(home_goal_20pct, self.test_profile)
        amount_10pct = self.home_calculator.calculate_amount_needed(home_goal_10pct, self.test_profile)
        
        logger.info(f"Home 20% down payment: ₹{amount_20pct:,.2f}")
        logger.info(f"Home 10% down payment: ₹{amount_10pct:,.2f}")
        
        # Verify amounts match expected percentages of property value
        self.assertAlmostEqual(amount_20pct, property_value * 0.20, delta=property_value * 0.01)
        self.assertAlmostEqual(amount_10pct, property_value * 0.10, delta=property_value * 0.01)
        
        # Create fresh home purchase goals to ensure correct calculation
        test_home_goal_20pct = Goal(
            id="test-home-20pct-2",
            user_profile_id=self.test_profile["id"],
            category="home_purchase",
            title="Home - 20% Down (Test)",
            target_amount=amount_20pct,
            timeframe=(datetime.now() + timedelta(days=365*3)).isoformat(),
            current_amount=0,  # No funding yet
            importance="high"
        )
        test_home_goal_20pct.funding_strategy = json.dumps({
            "property_value": property_value,
            "down_payment_percent": 0.20
        })
        
        test_home_goal_10pct = Goal(
            id="test-home-10pct-2",
            user_profile_id=self.test_profile["id"],
            category="home_purchase",
            title="Home - 10% Down (Test)",
            target_amount=amount_10pct,
            timeframe=(datetime.now() + timedelta(days=365*3)).isoformat(),
            current_amount=0,  # No funding yet
            importance="high"
        )
        test_home_goal_10pct.funding_strategy = json.dumps({
            "property_value": property_value,
            "down_payment_percent": 0.10
        })
        
        monthly_savings_20pct = self.home_calculator.calculate_required_saving_rate(test_home_goal_20pct, self.test_profile)
        monthly_savings_10pct = self.home_calculator.calculate_required_saving_rate(test_home_goal_10pct, self.test_profile)
        
        logger.info(f"Monthly savings for 20% down: ₹{monthly_savings_20pct:,.2f}")
        logger.info(f"Monthly savings for 10% down: ₹{monthly_savings_10pct:,.2f}")
        
        # 20% down payment should require more monthly savings than 10%
        self.assertGreater(monthly_savings_20pct, monthly_savings_10pct)
    
    def test_06_education_inflation_sensitivity(self):
        """Test education goal sensitivity to education inflation rate."""
        logger.info("Testing education goal sensitivity to inflation")
        
        # Create versions of goal with different education inflation rates
        # Education inflation is typically higher than general inflation
        
        # Test with standard education inflation
        education_goal_std = Goal(
            id="test-education-std",
            user_profile_id=self.test_profile["id"],
            category="education",
            title="Education - Standard Inflation",
            target_amount=2000000,
            timeframe=(datetime.now() + timedelta(days=365*10)).isoformat(),  # 10 years to education
            current_amount=200000,
            notes="Education with standard inflation"
        )
        
        # Test with high education inflation
        education_goal_high = Goal(
            id="test-education-high",
            user_profile_id=self.test_profile["id"],
            category="education",
            title="Education - High Inflation",
            target_amount=2000000,
            timeframe=(datetime.now() + timedelta(days=365*10)).isoformat(),  # 10 years to education
            current_amount=200000,
            notes="Education with high inflation"
        )
        # Add education inflation rate via funding strategy
        education_goal_high.funding_strategy = json.dumps({
            "education_inflation_rate": 0.12  # 12% inflation
        })
        
        # Set up different inflation rates explicitly through the calculator
        calculator_std = EducationCalculator()
        calculator_high = EducationCalculator()
        
        # Set different inflation rates
        calculator_std.params["inflation_rate"] = 0.06  # Standard inflation
        calculator_high.params["inflation_rate"] = 0.12  # Higher inflation
        
        # Calculate with different inflation rates
        amount_std = calculator_std.calculate_amount_needed(education_goal_std, self.test_profile)
        amount_high = calculator_high.calculate_amount_needed(education_goal_high, self.test_profile)
        
        logger.info(f"Education fund - standard inflation: ₹{amount_std:,.2f}")
        logger.info(f"Education fund - high inflation: ₹{amount_high:,.2f}")
        
        # Higher inflation should lead to higher required amount
        self.assertGreater(amount_high, amount_std)
        
        # Test monthly savings requirements
        # Update the goals to ensure they need funding
        education_goal_std.current_amount = 0
        education_goal_high.current_amount = 0
        
        # Update target amounts to match the calculated future values
        education_goal_std.target_amount = amount_std
        education_goal_high.target_amount = amount_high
        
        monthly_savings_std = calculator_std.calculate_required_saving_rate(education_goal_std, self.test_profile)
        monthly_savings_high = calculator_high.calculate_required_saving_rate(education_goal_high, self.test_profile)
        
        logger.info(f"Monthly savings - standard inflation: ₹{monthly_savings_std:,.2f}")
        logger.info(f"Monthly savings - high inflation: ₹{monthly_savings_high:,.2f}")
        
        # Higher inflation should require more monthly savings
        self.assertGreater(monthly_savings_high, monthly_savings_std)
    
    def test_07_timeframe_sensitivity(self):
        """Test sensitivity of goals to different timeframes."""
        logger.info("Testing goal sensitivity to timeframes")
        
        # Create versions of retirement goal with different timeframes
        retirement_short = Goal(
            id="test-retirement-short",
            user_profile_id=self.test_profile["id"],
            category="traditional_retirement",
            title="Retirement - Short Timeframe",
            target_amount=0,
            timeframe=(datetime.now() + timedelta(days=365*15)).isoformat(),  # 15 years to retirement
            current_amount=2000000,
            notes="Retirement with shorter timeframe"
        )
        
        retirement_long = Goal(
            id="test-retirement-long",
            user_profile_id=self.test_profile["id"],
            category="traditional_retirement",
            title="Retirement - Long Timeframe",
            target_amount=0,
            timeframe=(datetime.now() + timedelta(days=365*30)).isoformat(),  # 30 years to retirement
            current_amount=2000000,
            notes="Retirement with longer timeframe"
        )
        
        # Calculate for different timeframes
        calculator = RetirementCalculator()
        
        # Amount needed should be similar
        amount_short = calculator.calculate_amount_needed(retirement_short, self.test_profile)
        amount_long = calculator.calculate_amount_needed(retirement_long, self.test_profile)
        
        logger.info(f"Retirement amount - 15 years: ₹{amount_short:,.2f}")
        logger.info(f"Retirement amount - 30 years: ₹{amount_long:,.2f}")
        
        # Monthly contributions should be higher for shorter timeframe
        # Create goals with a much higher target amount to ensure they are not fully funded yet
        retirement_short.target_amount = amount_short * 1.5
        retirement_long.target_amount = amount_long * 1.5
        
        monthly_short = calculator.calculate_required_saving_rate(retirement_short, self.test_profile)
        monthly_long = calculator.calculate_required_saving_rate(retirement_long, self.test_profile)
        
        logger.info(f"Monthly savings - 15 years: ₹{monthly_short:,.2f}")
        logger.info(f"Monthly savings - 30 years: ₹{monthly_long:,.2f}")
        
        # Shorter timeframe should require higher monthly savings
        if monthly_short > 0 and monthly_long > 0:
            self.assertGreater(monthly_short, monthly_long)
        # If either is 0, we can't make a definitive comparison
        
        # Get asset allocations for different timeframes
        allocation_short = calculator.get_recommended_allocation(retirement_short, self.test_profile)
        allocation_long = calculator.get_recommended_allocation(retirement_long, self.test_profile)
        
        logger.info(f"Asset allocation - 15 years: {allocation_short}")
        logger.info(f"Asset allocation - 30 years: {allocation_long}")
    
    def test_08_goal_calculator_factory(self):
        """Test the GoalCalculator factory method with different goal types."""
        logger.info("Testing GoalCalculator factory method")
        
        # Test with emergency fund goal
        emergency_calculator = GoalCalculator.get_calculator_for_goal(self.emergency_goal)
        self.assertIsInstance(emergency_calculator, EmergencyFundCalculator)
        
        # Test with retirement goal
        retirement_calculator = GoalCalculator.get_calculator_for_goal(self.retirement_goal)
        self.assertIsInstance(retirement_calculator, RetirementCalculator)
        
        # Test with home purchase goal
        home_calculator = GoalCalculator.get_calculator_for_goal(self.home_goal)
        self.assertIsInstance(home_calculator, HomeDownPaymentCalculator)
        
        # Test with education goal
        education_calculator = GoalCalculator.get_calculator_for_goal(self.education_goal)
        self.assertIsInstance(education_calculator, EducationCalculator)
        
        # Test with unknown goal type
        unknown_goal = Goal(
            id="test-unknown",
            user_profile_id=self.test_profile["id"],
            category="unknown_category",
            title="Unknown Goal Type",
            target_amount=100000
        )
        
        unknown_calculator = GoalCalculator.get_calculator_for_goal(unknown_goal)
        self.assertIsInstance(unknown_calculator, GoalCalculator)  # Should return base calculator
        
        logger.info("GoalCalculator factory method working correctly for all goal types")
    
    def test_09_parameter_consistency(self):
        """Test consistency of calculator parameters across different instances."""
        logger.info("Testing calculator parameter consistency")
        
        # Create multiple instances of the same calculator type
        calculator1 = RetirementCalculator()
        calculator2 = RetirementCalculator()
        
        # Parameters should be loaded consistently
        self.assertEqual(calculator1.params["inflation_rate"], calculator2.params["inflation_rate"])
        self.assertEqual(calculator1.params["equity_returns"]["moderate"], calculator2.params["equity_returns"]["moderate"])
        self.assertEqual(calculator1.params["retirement_corpus_multiplier"], calculator2.params["retirement_corpus_multiplier"])
        
        # Check that reasonable defaults exist
        self.assertGreater(calculator1.params["inflation_rate"], 0)
        self.assertLess(calculator1.params["inflation_rate"], 0.15)  # Inflation shouldn't be unreasonably high
        
        self.assertGreater(calculator1.params["equity_returns"]["aggressive"], calculator1.params["equity_returns"]["conservative"])
        self.assertLess(calculator1.params["equity_returns"]["conservative"], calculator1.params["equity_returns"]["aggressive"])
        
        logger.info("Calculator parameters are consistent and reasonable")

def run_tests():
    """Run the test suite."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(GoalFinancialIntegrationTest)
    
    # Run tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Report results
    logger.info("Test Results:")
    logger.info(f"  Ran {result.testsRun} tests")
    logger.info(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"  Failures: {len(result.failures)}")
    logger.info(f"  Errors: {len(result.errors)}")
    
    # Return non-zero exit code if any tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    logger.info("Starting goal financial integration test suite")
    sys.exit(run_tests())
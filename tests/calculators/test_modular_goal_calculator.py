#!/usr/bin/env python3
"""
Test script for the modular GoalCalculator implementation.

This script validates that:
1. The factory method returns correct calculator types
2. All calculator implementations are accessible 
3. All calculators implement required methods
4. Basic calculator functionality works as expected

Usage:
    python test_modular_goal_calculator.py
"""

import unittest
import json
from models.goal_calculator import get_calculator_for_goal
from models.goal_calculators import (
    GoalCalculator,
    EmergencyFundCalculator, 
    RetirementCalculator,
    EarlyRetirementCalculator,
    EducationCalculator,
    HomeDownPaymentCalculator,
    DebtRepaymentCalculator,
    DiscretionaryGoalCalculator,
    WeddingCalculator,
    LegacyPlanningCalculator,
    CharitableGivingCalculator,
    CustomGoalCalculator
)

class TestModularGoalCalculator(unittest.TestCase):
    """Test the modular goal calculator implementation"""
    
    def setUp(self):
        """Set up test data"""
        # Sample profile
        self.profile = {
            "age": 35,
            "income": 75000,  # Annual income
            "expenses": 4000,  # Monthly expenses
            "risk_profile": "moderate"
        }
        
        # Sample goals
        self.emergency_goal = {
            "id": "1",
            "category": "emergency_fund",
            "title": "Emergency Fund",
            "target_amount": 0,  # Let calculator determine this
            "current_amount": 5000,
            "timeframe": "2025-12-31",
            "importance": "high",
            "flexibility": "fixed",
            "notes": "Build 6-month emergency fund"
        }
        
        self.retirement_goal = {
            "id": "2",
            "category": "retirement",
            "title": "Retirement at 65",
            "target_amount": 0,  # Let calculator determine this
            "current_amount": 100000,
            "timeframe": "2050-01-01",
            "importance": "high",
            "flexibility": "somewhat_flexible",
            "notes": "Retire comfortably at 65"
        }
        
        self.education_goal = {
            "id": "3",
            "category": "education",
            "title": "College Fund for Child",
            "target_amount": 75000,
            "current_amount": 15000,
            "timeframe": "2028-08-01",
            "importance": "high",
            "flexibility": "somewhat_flexible",
            "notes": "College fund for 4-year degree"
        }
        
        self.home_goal = {
            "id": "4",
            "category": "home_purchase",
            "title": "Buy a Home",
            "target_amount": 60000,  # Down payment
            "current_amount": 30000,
            "timeframe": "2026-06-01",
            "importance": "high",
            "flexibility": "somewhat_flexible",
            "notes": "20% down payment on a $300,000 home"
        }
        
        self.debt_goal = {
            "id": "5",
            "category": "debt_repayment",
            "title": "Pay off Student Loans",
            "target_amount": 35000,
            "current_amount": 5000,
            "timeframe": "2026-12-31",
            "importance": "high",
            "flexibility": "fixed",
            "notes": "Pay off student loan debt at 6.8% interest"
        }
        
        self.discretionary_goal = {
            "id": "6",
            "category": "travel",
            "title": "European Vacation",
            "target_amount": 10000,
            "current_amount": 2000,
            "timeframe": "2025-07-01",
            "importance": "medium",
            "flexibility": "very_flexible",
            "notes": "Two-week trip to Europe"
        }
        
        self.wedding_goal = {
            "id": "7",
            "category": "wedding",
            "title": "Wedding Fund",
            "target_amount": 25000,
            "current_amount": 5000,
            "timeframe": "2026-09-15",
            "importance": "high",
            "flexibility": "somewhat_flexible",
            "notes": "Save for wedding and honeymoon"
        }
        
        self.charitable_goal = {
            "id": "8",
            "category": "charitable_giving",
            "title": "Annual Charity Donation",
            "target_amount": 5000,
            "current_amount": 1000,
            "timeframe": "2025-12-31",
            "importance": "medium",
            "flexibility": "somewhat_flexible",
            "notes": "Annual charitable donation"
        }
        
        self.custom_goal = {
            "id": "9",
            "category": "custom",
            "title": "Start a Business",
            "target_amount": 50000,
            "current_amount": 10000,
            "timeframe": "2027-06-01",
            "importance": "high",
            "flexibility": "somewhat_flexible",
            "notes": "Seed money to start a small business"
        }
    
    def test_factory_method(self):
        """Test that factory method returns the correct calculator classes"""
        # Test emergency fund goal
        calculator = get_calculator_for_goal(self.emergency_goal)
        self.assertIsInstance(calculator, EmergencyFundCalculator)
        
        # Test retirement goal
        calculator = get_calculator_for_goal(self.retirement_goal)
        self.assertIsInstance(calculator, RetirementCalculator)
        
        # Test education goal
        calculator = get_calculator_for_goal(self.education_goal)
        self.assertIsInstance(calculator, EducationCalculator)
        
        # Test home purchase goal
        calculator = get_calculator_for_goal(self.home_goal)
        self.assertIsInstance(calculator, HomeDownPaymentCalculator)
        
        # Test debt repayment goal
        calculator = get_calculator_for_goal(self.debt_goal)
        self.assertIsInstance(calculator, DebtRepaymentCalculator)
        
        # Test discretionary goal (travel)
        calculator = get_calculator_for_goal(self.discretionary_goal)
        self.assertIsInstance(calculator, DiscretionaryGoalCalculator)
        
        # Test wedding goal
        calculator = get_calculator_for_goal(self.wedding_goal)
        self.assertIsInstance(calculator, WeddingCalculator)
        
        # Test charitable giving goal
        calculator = get_calculator_for_goal(self.charitable_goal)
        self.assertIsInstance(calculator, CharitableGivingCalculator)
        
        # Test custom goal
        calculator = get_calculator_for_goal(self.custom_goal)
        self.assertIsInstance(calculator, CustomGoalCalculator)
    
    def test_emergency_fund_calculator(self):
        """Test emergency fund calculator"""
        # Get calculator for emergency fund goal
        calculator = get_calculator_for_goal(self.emergency_goal)
        
        # Calculate amount needed
        amount_needed = calculator.calculate_amount_needed(self.emergency_goal, self.profile)
        
        # Test that amount is based on 6 months of expenses (default)
        expected_amount = self.profile["expenses"] * 6
        self.assertEqual(amount_needed, expected_amount)
        
        # Calculate monthly contribution
        monthly_contribution = calculator.calculate_monthly_contribution(self.emergency_goal, self.profile)
        
        # Verify contribution is positive
        self.assertGreater(monthly_contribution, 0)
    
    def test_home_purchase_calculator(self):
        """Test home purchase calculator"""
        # Get calculator for home purchase goal
        calculator = get_calculator_for_goal(self.home_goal)
        
        # Test the analyze_rent_vs_buy method
        analysis = calculator.analyze_rent_vs_buy(self.home_goal, self.profile)
        
        # Verify analysis contains expected keys
        expected_keys = ['monthly_rent', 'monthly_mortgage_payment', 'payment_breakdown', 
                         'total_upfront_costs', '5_year_rent_cost', '5_year_ownership_cost', 
                         '5_year_equity_buildup', 'breakeven_years', 'recommendation']
                         
        for key in expected_keys:
            self.assertIn(key, analysis)
    
    def test_education_calculator(self):
        """Test education calculator"""
        # Get calculator for education goal
        calculator = get_calculator_for_goal(self.education_goal)
        
        # Test monthly contribution calculation
        monthly_contribution = calculator.calculate_monthly_contribution(self.education_goal, self.profile)
        
        # Verify contribution is positive
        self.assertGreater(monthly_contribution, 0)
        
    def test_retirement_calculator(self):
        """Test retirement calculator"""
        # Get calculator for retirement goal
        calculator = get_calculator_for_goal(self.retirement_goal)
        
        # Calculate amount needed
        amount_needed = calculator.calculate_amount_needed(self.retirement_goal, self.profile)
        
        # Verify it's a reasonable retirement amount (more than income * 10)
        self.assertGreater(amount_needed, self.profile["income"] * 10)
        
        # Test monthly contribution
        monthly_contribution = calculator.calculate_monthly_contribution(self.retirement_goal, self.profile)
        
        # Verify contribution is positive
        self.assertGreater(monthly_contribution, 0)
        
    def test_debt_repayment_calculator(self):
        """Test debt repayment calculator"""
        # Get calculator for debt goal
        calculator = get_calculator_for_goal(self.debt_goal)
        
        # Test monthly contribution
        monthly_contribution = calculator.calculate_monthly_contribution(self.debt_goal, self.profile)
        
        # Verify contribution is positive
        self.assertGreater(monthly_contribution, 0)
        
    def test_wedding_calculator(self):
        """Test wedding calculator"""
        # Get calculator for wedding goal
        calculator = get_calculator_for_goal(self.wedding_goal)
        
        # Test monthly contribution
        monthly_contribution = calculator.calculate_monthly_contribution(self.wedding_goal, self.profile)
        
        # Verify contribution is positive
        self.assertGreater(monthly_contribution, 0)
    
    def test_priority_scores(self):
        """Test priority score calculations across different goal types"""
        # Calculate priority scores for all goals
        goals = [
            self.emergency_goal,
            self.retirement_goal,
            self.education_goal,
            self.home_goal,
            self.debt_goal,
            self.discretionary_goal,
            self.wedding_goal,
            self.charitable_goal,
            self.custom_goal
        ]
        
        # Calculate priority scores
        scores = {}
        for goal in goals:
            calculator = get_calculator_for_goal(goal)
            scores[goal["id"]] = calculator.calculate_priority_score(goal, self.profile)
        
        # Verify all scores are between 0 and 100
        for goal_id, score in scores.items():
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)
        
        # Verify emergency fund has higher priority than discretionary goals
        self.assertGreater(scores[self.emergency_goal["id"]], scores[self.discretionary_goal["id"]])
        
        # Verify debt repayment has higher priority than charitable giving
        self.assertGreater(scores[self.debt_goal["id"]], scores[self.charitable_goal["id"]])

    def test_required_methods(self):
        """Test that all calculators implement required methods"""
        # List of all calculator classes
        calculator_classes = [
            EmergencyFundCalculator,
            RetirementCalculator,
            EarlyRetirementCalculator,
            EducationCalculator,
            HomeDownPaymentCalculator,
            DebtRepaymentCalculator,
            DiscretionaryGoalCalculator,
            WeddingCalculator,
            LegacyPlanningCalculator, 
            CharitableGivingCalculator,
            CustomGoalCalculator
        ]
        
        # Required methods that all calculators should implement
        required_methods = [
            'calculate_amount_needed',
            'calculate_monthly_contribution',
            'calculate_time_available',
            'calculate_priority_score'
        ]
        
        # Verify each calculator implements required methods
        for calculator_class in calculator_classes:
            calculator = calculator_class()
            for method_name in required_methods:
                self.assertTrue(hasattr(calculator, method_name), 
                               f"{calculator_class.__name__} missing required method: {method_name}")

if __name__ == '__main__':
    unittest.main()
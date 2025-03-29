import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
from datetime import datetime, timedelta

# Add project root to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.goal_adjustment_service import GoalAdjustmentService

class TestSIPRecommendations(unittest.TestCase):
    """
    Test Systematic Investment Plan (SIP) recommendation methods in the GoalAdjustmentService.
    
    These tests focus on India-specific SIP recommendations that don't require 
    the GoalProbabilityAnalyzer to be fully implemented.
    """
    
    def setUp(self):
        # Create mocks for the dependencies
        self.probability_analyzer_mock = MagicMock()
        self.gap_analyzer_mock = MagicMock()
        self.adjustment_recommender_mock = MagicMock()
        self.param_service_mock = MagicMock()
        
        # Initialize the service with the mocks
        self.adjustment_service = GoalAdjustmentService(
            goal_probability_analyzer=self.probability_analyzer_mock,
            goal_adjustment_recommender=self.adjustment_recommender_mock,
            gap_analyzer=self.gap_analyzer_mock,
            param_service=self.param_service_mock
        )
        
        # Test profile with various income levels
        self.test_profiles = {
            "medium_income": {
                "id": "profile-1",
                "annual_income": 1200000,  # ₹12L
                "monthly_income": 100000,  # ₹1L per month
                "risk_tolerance": "moderate",
                "age": 35
            },
            "high_income": {
                "id": "profile-2",
                "annual_income": 3000000,  # ₹30L
                "monthly_income": 250000,  # ₹2.5L per month
                "risk_tolerance": "aggressive",
                "age": 40
            }
        }
        
        # Test goals for different categories and time horizons
        self.test_goals = {
            "retirement_long_term": {
                "id": "retirement-goal-1",
                "category": "retirement",
                "type": "retirement",
                "title": "Retirement",
                "target_amount": 30000000,  # ₹3 crore
                "current_amount": 5000000,  # ₹50 lakh
                "monthly_contribution": 30000,  # ₹30,000
                "target_date": (datetime.now() + timedelta(days=365*20)).strftime("%Y-%m-%d"),
                "description": "Retirement planning"
            },
            "education_medium_term": {
                "id": "education-goal-1",
                "category": "education",
                "type": "education",
                "title": "Child's Education",
                "target_amount": 5000000,  # ₹50 lakh
                "current_amount": 1000000,  # ₹10 lakh
                "monthly_contribution": 15000,  # ₹15,000
                "target_date": (datetime.now() + timedelta(days=365*10)).strftime("%Y-%m-%d"),
                "description": "Child's college education in India"
            },
            "home_short_term": {
                "id": "home-goal-1",
                "category": "home",
                "type": "home",
                "title": "Home Purchase",
                "target_amount": 10000000,  # ₹1 crore
                "current_amount": 2000000,  # ₹20 lakh
                "monthly_contribution": 25000,  # ₹25,000
                "target_date": (datetime.now() + timedelta(days=365*3)).strftime("%Y-%m-%d"),
                "description": "Home purchase in suburban area"
            },
            "emergency_fund": {
                "id": "emergency-goal-1",
                "category": "emergency_fund",
                "type": "emergency_fund",
                "title": "Emergency Fund",
                "target_amount": 600000,  # ₹6 lakh
                "current_amount": 100000,  # ₹1 lakh
                "monthly_contribution": 10000,  # ₹10,000
                "target_date": (datetime.now() + timedelta(days=365*1)).strftime("%Y-%m-%d"),
                "description": "Emergency fund for 6 months of expenses"
            }
        }
    
    def test_generate_sip_recommendations_retirement(self):
        """Test SIP recommendations for retirement goals."""
        # Test retirement goal (long-term horizon)
        retirement_goal = self.test_goals["retirement_long_term"]
        profile = self.test_profiles["medium_income"]
        
        # Generate SIP recommendations
        sip_recommendations = self.adjustment_service._generate_sip_recommendations(
            30000,  # ₹30,000 monthly contribution
            retirement_goal,
            profile
        )
        
        # Verify structure
        self.assertIsNotNone(sip_recommendations)
        self.assertIn("allocations", sip_recommendations)
        self.assertIn("monthly_amounts", sip_recommendations)
        self.assertIn("tax_saving_options", sip_recommendations)
        
        # Verify allocations
        allocations = sip_recommendations["allocations"]
        self.assertIsInstance(allocations, dict)
        self.assertGreater(len(allocations), 0)
        
        # Retirement allocations should favor equity for long-term growth
        if "equity_funds" in allocations:
            self.assertGreaterEqual(allocations["equity_funds"], 0.5)
            
        # Verify monthly amounts
        monthly_amounts = sip_recommendations["monthly_amounts"]
        self.assertIsInstance(monthly_amounts, dict)
        self.assertEqual(sum(monthly_amounts.values()), 30000)
        
        # Check tax saving options for retirement
        tax_options = sip_recommendations["tax_saving_options"]
        self.assertIsInstance(tax_options, dict)
        
        # ELSS should be recommended for retirement
        if "elss_funds" in tax_options:
            self.assertGreater(tax_options["elss_funds"], 0)
    
    def test_generate_sip_recommendations_education(self):
        """Test SIP recommendations for education goals."""
        # Test education goal (medium-term horizon)
        education_goal = self.test_goals["education_medium_term"]
        profile = self.test_profiles["medium_income"]
        
        # Generate SIP recommendations
        sip_recommendations = self.adjustment_service._generate_sip_recommendations(
            15000,  # ₹15,000 monthly contribution
            education_goal,
            profile
        )
        
        # Verify structure
        self.assertIsNotNone(sip_recommendations)
        self.assertIn("allocations", sip_recommendations)
        self.assertIn("monthly_amounts", sip_recommendations)
        
        # Verify allocations
        allocations = sip_recommendations["allocations"]
        self.assertIsInstance(allocations, dict)
        self.assertGreater(len(allocations), 0)
        
        # Education allocations should be balanced for medium-term
        if "equity_funds" in allocations and "debt_funds" in allocations:
            self.assertLessEqual(allocations["equity_funds"], 0.7)
            self.assertGreaterEqual(allocations["debt_funds"], 0.2)
            
        # Verify monthly amounts
        monthly_amounts = sip_recommendations["monthly_amounts"]
        self.assertIsInstance(monthly_amounts, dict)
        self.assertEqual(sum(monthly_amounts.values()), 15000)
    
    def test_generate_sip_recommendations_emergency_fund(self):
        """Test SIP recommendations for emergency fund goals."""
        # Test emergency fund goal (short-term, liquid)
        emergency_goal = self.test_goals["emergency_fund"]
        profile = self.test_profiles["medium_income"]
        
        # Generate SIP recommendations
        sip_recommendations = self.adjustment_service._generate_sip_recommendations(
            10000,  # ₹10,000 monthly contribution
            emergency_goal,
            profile
        )
        
        # Verify structure
        self.assertIsNotNone(sip_recommendations)
        self.assertIn("allocations", sip_recommendations)
        self.assertIn("monthly_amounts", sip_recommendations)
        
        # Verify allocations
        allocations = sip_recommendations["allocations"]
        self.assertIsInstance(allocations, dict)
        self.assertGreater(len(allocations), 0)
        
        # Emergency fund should be in liquid options
        if "liquid_funds" in allocations:
            self.assertGreaterEqual(allocations["liquid_funds"], 0.3)
            
        # Emergency funds should not be in equity
        if "equity_funds" in allocations:
            self.assertLessEqual(allocations["equity_funds"], 0.2)
            
        # Verify monthly amounts
        monthly_amounts = sip_recommendations["monthly_amounts"]
        self.assertIsInstance(monthly_amounts, dict)
        self.assertEqual(sum(monthly_amounts.values()), 10000)
        
        # Emergency funds don't have tax advantages
        self.assertEqual(sip_recommendations["tax_saving_options"], {})
    
    def test_generate_sip_recommendations_higher_amount(self):
        """Test SIP recommendations with higher contribution amount."""
        # Test with higher contribution amount
        retirement_goal = self.test_goals["retirement_long_term"]
        profile = self.test_profiles["high_income"]
        
        # Generate SIP recommendations
        sip_recommendations = self.adjustment_service._generate_sip_recommendations(
            100000,  # ₹1L monthly contribution
            retirement_goal,
            profile
        )
        
        # Verify monthly amounts scale correctly
        monthly_amounts = sip_recommendations["monthly_amounts"]
        self.assertEqual(sum(monthly_amounts.values()), 100000)
        
        # High contribution should have more tax-saving options
        tax_options = sip_recommendations["tax_saving_options"]
        if "elss_funds" in tax_options:
            self.assertGreaterEqual(tax_options["elss_funds"], 10000)
    
    def test_recommend_india_specific_funds(self):
        """Test recommendations for specific Indian mutual fund types."""
        # Test with retirement goal and various allocations
        retirement_goal = self.test_goals["retirement_long_term"]
        profile = self.test_profiles["medium_income"]
        
        # Test allocation with all asset classes
        test_allocation = {
            "equity": 0.6,
            "debt": 0.25,
            "hybrid": 0.1,
            "gold": 0.05,
            "cash": 0.0
        }
        
        # Get fund recommendations
        fund_recommendations = self.adjustment_service._recommend_india_specific_funds(
            test_allocation,
            retirement_goal,
            profile
        )
        
        # Verify structure
        self.assertIsNotNone(fund_recommendations)
        self.assertIn("equity", fund_recommendations)
        self.assertIn("debt", fund_recommendations)
        self.assertIn("hybrid", fund_recommendations)
        self.assertIn("other", fund_recommendations)
        
        # Verify equity recommendations
        equity_recs = fund_recommendations["equity"]
        self.assertIsInstance(equity_recs, list)
        self.assertGreater(len(equity_recs), 0)
        
        # Check specific fund types for long-term horizon
        equity_fund_types = [rec["type"].lower() for rec in equity_recs]
        debt_fund_types = [rec["type"].lower() for rec in fund_recommendations["debt"]]
        
        # For retirement, expect index funds and large cap funds
        self.assertTrue(
            any("index" in fund_type for fund_type in equity_fund_types) or
            any("large cap" in fund_type for fund_type in equity_fund_types)
        )
        
        # For retirement debt, expect government securities
        if debt_fund_types:
            self.assertTrue(
                any("government" in fund_type for fund_type in debt_fund_types) or
                any("corporate bond" in fund_type for fund_type in debt_fund_types)
            )
    
    def test_recommend_india_specific_funds_short_term(self):
        """Test fund recommendations for short-term goals."""
        # Test with home goal (short time horizon)
        home_goal = self.test_goals["home_short_term"]
        profile = self.test_profiles["medium_income"]
        
        # Test allocation with all asset classes
        test_allocation = {
            "equity": 0.3,
            "debt": 0.6,
            "hybrid": 0.05,
            "gold": 0.0,
            "cash": 0.05
        }
        
        # Get fund recommendations
        fund_recommendations = self.adjustment_service._recommend_india_specific_funds(
            test_allocation,
            home_goal,
            profile
        )
        
        # Verify structure for all categories
        self.assertIsNotNone(fund_recommendations)
        
        # For short term goals, verify debt recommendations
        if "debt" in fund_recommendations:
            debt_recs = fund_recommendations["debt"]
            debt_fund_types = [rec["type"].lower() for rec in debt_recs]
            
            # Should recommend short duration funds for shorter time horizons
            self.assertTrue(
                any("short" in fund_type for fund_type in debt_fund_types) or
                any("ultra" in fund_type for fund_type in debt_fund_types) or
                any("liquid" in fund_type for fund_type in debt_fund_types)
            )
    
    def test_calculate_goal_time_horizon(self):
        """Test calculation of goal time horizon in years."""
        # Test with goals having different time horizons
        for goal_name, goal in self.test_goals.items():
            with self.subTest(goal_name=goal_name):
                horizon = self.adjustment_service._calculate_goal_time_horizon(goal)
                
                # Verify reasonable time horizon
                self.assertIsInstance(horizon, int)
                self.assertGreaterEqual(horizon, 0)
                
                # Verify specific horizons
                if goal_name == "retirement_long_term":
                    self.assertGreater(horizon, 15)
                elif goal_name == "education_medium_term":
                    self.assertTrue(5 <= horizon <= 15)
                elif goal_name == "home_short_term":
                    self.assertTrue(1 <= horizon <= 5)
                elif goal_name == "emergency_fund":
                    self.assertLessEqual(horizon, 2)
    
    def test_allocation_recommendations_by_goal_type(self):
        """Test that allocation recommendations are appropriate for goal type."""
        # Test various goals to ensure recommendations match goal type
        goals_to_test = [
            ("retirement_long_term", 0.7, 0.2, 0.1),  # (goal_name, min_equity, min_debt, max_other)
            ("education_medium_term", 0.5, 0.3, 0.2),
            ("home_short_term", 0.3, 0.5, 0.2),
            ("emergency_fund", 0.0, 0.4, 0.6)
        ]
        
        for goal_name, min_equity, min_debt, max_other in goals_to_test:
            with self.subTest(goal_name=goal_name):
                goal = self.test_goals[goal_name]
                profile = self.test_profiles["medium_income"]
                
                # Generate SIP recommendations
                sip_recommendations = self.adjustment_service._generate_sip_recommendations(
                    20000,  # ₹20,000 monthly contribution
                    goal,
                    profile
                )
                
                # Get allocations
                allocations = sip_recommendations["allocations"]
                
                # Calculate equity, debt and other allocations
                equity_funds = sum(v for k, v in allocations.items() if "equity" in k.lower())
                debt_funds = sum(v for k, v in allocations.items() if "debt" in k.lower())
                other_funds = 1.0 - equity_funds - debt_funds
                
                # Verify allocations by goal type
                if goal_name == "retirement_long_term":
                    self.assertGreaterEqual(equity_funds, min_equity)
                    self.assertGreaterEqual(debt_funds, min_debt)
                elif goal_name == "education_medium_term":
                    self.assertGreaterEqual(equity_funds, min_equity)
                    self.assertGreaterEqual(debt_funds, min_debt)
                elif goal_name == "home_short_term":
                    self.assertLessEqual(equity_funds, 0.4)
                    self.assertGreaterEqual(debt_funds, min_debt)
                elif goal_name == "emergency_fund":
                    self.assertLessEqual(equity_funds, 0.2)
                    other_components = 1.0 - equity_funds - debt_funds
                    self.assertGreaterEqual(other_components, max_other - 0.1)


if __name__ == '__main__':
    unittest.main()
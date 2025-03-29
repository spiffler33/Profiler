import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
from datetime import datetime, timedelta

# Add project root to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.goal_adjustment_service import GoalAdjustmentService
from models.goal_models import Goal

class TestGoalAdjustmentParameterExtraction(unittest.TestCase):
    """
    Test parameter extraction methods in the GoalAdjustmentService.
    
    These tests focus on methods that extract data from goal and profile objects,
    which don't depend on the GoalProbabilityAnalyzer to be fully implemented.
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
        
        # Sample test profile data
        self.test_profile = {
            "id": "profile-1",
            "name": "Test User",
            "email": "test@example.com",
            "annual_income": "₹12,00,000",  # Using Indian format
            "monthly_income": "₹1,00,000",
            "age": 35,
            "risk_tolerance": "moderate",
            "answers": [
                {"question_id": "financial_basics_annual_income", "answer": "₹12L"},
                {"question_id": "monthly_income", "answer": "₹1L"},
                {"question_id": "monthly_expenses", "answer": "₹60,000"},
                {"question_id": "risk_profile", "answer": "moderate"}
            ]
        }
        
        # Sample test goal data
        self.test_goal_dict = {
            "id": "goal-1",
            "title": "Retirement",
            "category": "retirement",
            "target_amount": "₹3Cr",
            "current_amount": "₹50L",
            "monthly_contribution": "₹30,000",
            "target_date": (datetime.now() + timedelta(days=365*20)).strftime("%Y-%m-%d"),
            "importance": "high",
            "flexibility": "medium",
            "notes": "Retire by 55",
            "asset_allocation": json.dumps({
                "equity": 0.7,
                "debt": 0.2,
                "gold": 0.05,
                "cash": 0.05
            }),
            "funding_strategy": json.dumps({
                "primary": "monthly_contribution",
                "tax_efficiency": "maximize",
                "rebalancing": "yearly"
            })
        }
        
        # Create a Goal object for testing
        self.test_goal_obj = MagicMock(spec=Goal)
        for key, value in self.test_goal_dict.items():
            setattr(self.test_goal_obj, key, value)
    
    def test_ensure_goal_dict_with_dict(self):
        """Test conversion when goal is already a dictionary."""
        result = self.adjustment_service._ensure_goal_dict(self.test_goal_dict)
        
        # Verify the result is a dict
        self.assertIsInstance(result, dict)
        
        # Verify it's the same dict (unchanged)
        self.assertIs(result, self.test_goal_dict)
    
    def test_ensure_goal_dict_with_object(self):
        """Test conversion from Goal object to dictionary."""
        result = self.adjustment_service._ensure_goal_dict(self.test_goal_obj)
        
        # Verify the result is a dict
        self.assertIsInstance(result, dict)
        
        # Verify key fields are present
        self.assertEqual(result['id'], self.test_goal_obj.id)
        self.assertEqual(result['title'], self.test_goal_obj.title)
        self.assertEqual(result['target_amount'], self.test_goal_obj.target_amount)
        
        # Check JSON deserialization
        # Asset allocation should be deserialized from JSON string to dict
        self.assertIn('asset_allocation', result)
        asset_allocation = result['asset_allocation']
        self.assertIsInstance(asset_allocation, dict)
        self.assertIn('equity', asset_allocation)
        
        # Funding strategy should be deserialized from JSON string to dict
        self.assertIn('funding_strategy', result)
        funding_strategy = result['funding_strategy']
        self.assertIsInstance(funding_strategy, dict)
        self.assertIn('primary', funding_strategy)
    
    def test_get_annual_income(self):
        """Test annual income extraction from profile."""
        # Test with string formatted income
        result = self.adjustment_service._get_annual_income(self.test_profile)
        
        # Verify correct value (₹12L = 1,200,000)
        self.assertEqual(result, 1200000)
        
        # Test with numeric income
        numeric_profile = {"annual_income": 1500000}
        result = self.adjustment_service._get_annual_income(numeric_profile)
        self.assertEqual(result, 1500000)
        
        # Test with annual income in answers
        answers_profile = {
            "answers": [
                {"question_id": "financial_basics_annual_income", "answer": "₹15L"}
            ]
        }
        result = self.adjustment_service._get_annual_income(answers_profile)
        self.assertEqual(result, 1500000)
        
        # Test with monthly income conversion
        monthly_profile = {"monthly_income": 100000}
        result = self.adjustment_service._get_annual_income(monthly_profile)
        self.assertEqual(result, 1200000)
    
    def test_get_monthly_income(self):
        """Test monthly income extraction from profile."""
        # Test with string formatted income
        result = self.adjustment_service._get_monthly_income(self.test_profile)
        
        # Verify correct value (₹1L = 100,000)
        self.assertEqual(result, 100000)
        
        # Test with numeric income
        numeric_profile = {"monthly_income": 125000}
        result = self.adjustment_service._get_monthly_income(numeric_profile)
        self.assertEqual(result, 125000)
        
        # Test with monthly income in answers
        answers_profile = {
            "answers": [
                {"question_id": "monthly_income", "answer": "₹1.25L"}
            ]
        }
        result = self.adjustment_service._get_monthly_income(answers_profile)
        self.assertEqual(result, 125000)
        
        # Test with annual income conversion
        annual_profile = {"annual_income": 1800000}
        result = self.adjustment_service._get_monthly_income(annual_profile)
        self.assertEqual(result, 150000)
    
    def test_apply_recommendation_to_goal(self):
        """Test application of recommendation to goal."""
        # Test contribution recommendation
        contribution_rec = {
            "type": "contribution",
            "value": 40000  # Increase to ₹40,000
        }
        
        result = self.adjustment_service._apply_recommendation_to_goal(
            self.test_goal_dict, contribution_rec
        )
        
        # Verify the result contains the updated value
        self.assertEqual(result["monthly_contribution"], 40000)
        
        # Test target amount recommendation
        target_rec = {
            "type": "target_amount",
            "value": 25000000  # Reduce to ₹2.5Cr
        }
        
        result = self.adjustment_service._apply_recommendation_to_goal(
            self.test_goal_dict, target_rec
        )
        
        # Verify the result contains the updated value
        self.assertEqual(result["target_amount"], 25000000)
        
        # Test timeframe recommendation
        future_date = (datetime.now() + timedelta(days=365*25)).strftime("%Y-%m-%d")
        timeframe_rec = {
            "type": "timeframe",
            "value": future_date
        }
        
        result = self.adjustment_service._apply_recommendation_to_goal(
            self.test_goal_dict, timeframe_rec
        )
        
        # Verify the result contains the updated value
        self.assertEqual(result["target_date"], future_date)
        
        # Test allocation recommendation
        new_allocation = {
            "equity": 0.6,
            "debt": 0.3,
            "gold": 0.05,
            "cash": 0.05
        }
        
        allocation_rec = {
            "type": "allocation",
            "value": new_allocation
        }
        
        result = self.adjustment_service._apply_recommendation_to_goal(
            self.test_goal_dict, allocation_rec
        )
        
        # Verify the result contains the updated value
        self.assertEqual(result["asset_allocation"], new_allocation)
        
        # Test tax recommendation (should not modify goal)
        tax_rec = {
            "type": "tax",
            "description": "Optimize tax saving"
        }
        
        result = self.adjustment_service._apply_recommendation_to_goal(
            self.test_goal_dict, tax_rec
        )
        
        # Verify the goal is unchanged
        self.assertEqual(result["monthly_contribution"], self.test_goal_dict["monthly_contribution"])
        self.assertEqual(result["target_amount"], self.test_goal_dict["target_amount"])
        self.assertEqual(result["target_date"], self.test_goal_dict["target_date"])
    
    def test_calculate_goal_time_horizon(self):
        """Test calculation of goal time horizon in years."""
        # Test with a future date
        future_date = (datetime.now() + timedelta(days=365*10)).strftime("%Y-%m-%d")
        goal_with_date = {
            "target_date": future_date
        }
        
        result = self.adjustment_service._calculate_goal_time_horizon(goal_with_date)
        
        # Should be approximately 10 years
        self.assertTrue(9 <= result <= 10)
        
        # Test with an explicit timeframe
        goal_with_timeframe = {
            "timeframe": 15
        }
        
        result = self.adjustment_service._calculate_goal_time_horizon(goal_with_timeframe)
        self.assertEqual(result, 15)
        
        # Test with a string timeframe
        goal_with_string_timeframe = {
            "timeframe": "20"
        }
        
        result = self.adjustment_service._calculate_goal_time_horizon(goal_with_string_timeframe)
        self.assertEqual(result, 20)
        
        # Test with no date or timeframe
        goal_without_date = {}
        
        result = self.adjustment_service._calculate_goal_time_horizon(goal_without_date)
        # Should return default value
        self.assertEqual(result, 7)
    
    def test_parse_currency_edge_cases(self):
        """Test edge cases in currency parsing."""
        # Test with extremely large values
        result = self.adjustment_service._parse_currency_value("₹100Cr")
        self.assertEqual(result, 1000000000)  # 100 crores = 1 billion
        
        # Test with mixed notation
        result = self.adjustment_service._parse_currency_value("₹1.5Cr and 50L")
        self.assertEqual(result, 15000000)  # Should parse just the first part
        
        # Test with invalid input
        result = self.adjustment_service._parse_currency_value("Not a number")
        self.assertIsNone(result)
        
        # Test with None
        result = self.adjustment_service._parse_currency_value(None)
        self.assertIsNone(result)
        
        # Test with empty string
        result = self.adjustment_service._parse_currency_value("")
        self.assertIsNone(result)
        
        # Test with mixed characters (changed from "₹500k" since we now support 'k' notation)
        result = self.adjustment_service._parse_currency_value("₹500xyz")  # Random letters after number
        self.assertIsNone(result)
    
    def test_determine_difficulty(self):
        """Test calculation of implementation difficulty."""
        # Mock option objects
        def create_mock_option(adj_type, adj_value, prev_value=None):
            option = MagicMock()
            option.adjustment_type = adj_type
            option.adjustment_value = adj_value
            option.previous_value = prev_value
            return option
        
        # Test target amount reduction (should be easy)
        target_option = create_mock_option("target_amount", 2500000)
        result = self.adjustment_service._determine_difficulty(target_option)
        self.assertEqual(result, "easy")
        
        # Test small contribution increase
        small_increase = create_mock_option("contribution", 33000, 30000)  # 10% increase
        result = self.adjustment_service._determine_difficulty(small_increase)
        self.assertEqual(result, "easy")
        
        # Test moderate contribution increase
        moderate_increase = create_mock_option("contribution", 37500, 30000)  # 25% increase
        result = self.adjustment_service._determine_difficulty(moderate_increase)
        self.assertEqual(result, "moderate")
        
        # Test large contribution increase
        large_increase = create_mock_option("contribution", 45000, 30000)  # 50% increase
        result = self.adjustment_service._determine_difficulty(large_increase)
        self.assertEqual(result, "difficult")
        
        # Test timeframe extension
        timeframe_option = create_mock_option("timeframe", datetime.now() + timedelta(days=365*25))
        result = self.adjustment_service._determine_difficulty(timeframe_option)
        self.assertEqual(result, "easy")
        
        # Test allocation change
        allocation_option = create_mock_option("allocation", {"equity": 0.6, "debt": 0.4})
        result = self.adjustment_service._determine_difficulty(allocation_option)
        self.assertEqual(result, "moderate")


if __name__ == '__main__':
    unittest.main()
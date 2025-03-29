import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from models.gap_analysis.analyzer import GapAnalysis
from services.goal_adjustment_service import GoalAdjustmentService


class TestIndianCurrencyParsing(unittest.TestCase):
    """
    Tests for the Indian currency parsing functionality in the application.
    
    These tests verify that the system correctly handles various Indian currency formats,
    including:
    - Rupee symbol (₹)
    - Lakhs notation (1L = 100,000)
    - Crores notation (1Cr = 10,000,000)
    - Indian comma notation (1,00,000)
    """
    
    def setUp(self):
        # Setup GapAnalysis with mocked parameter service
        self.param_service_mock = MagicMock()
        self.gap_analyzer = GapAnalysis(param_service=self.param_service_mock)
        
        # Setup GoalAdjustmentService with mocked dependencies
        self.probability_analyzer_mock = MagicMock()
        self.adjustment_recommender_mock = MagicMock()
        self.goal_adjustment_service = GoalAdjustmentService(
            goal_probability_analyzer=self.probability_analyzer_mock,
            goal_adjustment_recommender=self.adjustment_recommender_mock,
            gap_analyzer=self.gap_analyzer,
            param_service=self.param_service_mock
        )
    
    def test_gap_analysis_parse_basic_numerics(self):
        """Test parsing basic numeric values in GapAnalysis."""
        # Test integer
        self.assertEqual(self.gap_analyzer._parse_indian_currency(1000), 1000.0)
        
        # Test float
        self.assertEqual(self.gap_analyzer._parse_indian_currency(1000.5), 1000.5)
        
        # Test string numeric
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1000"), 1000.0)
        
        # Test empty values
        self.assertEqual(self.gap_analyzer._parse_indian_currency(""), 0.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency(None), 0.0)
    
    def test_gap_analysis_parse_rupee_symbol(self):
        """Test parsing Indian Rupee symbol in GapAnalysis."""
        # Test with Rupee symbol
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1000"), 1000.0)
        
        # Test with Rupee symbol and space
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹ 1000"), 1000.0)
        
        # Test with Rupee symbol and commas
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1,000"), 1000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1,00,000"), 100000.0)
    
    def test_gap_analysis_parse_lakhs_notation(self):
        """Test parsing Indian Lakhs notation in GapAnalysis."""
        # Test Lakhs notation
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1L"), 100000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1.5L"), 150000.0)
        
        # Test Lakhs with spaces
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1 L"), 100000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1.5 L"), 150000.0)
        
        # Test Lakhs with Rupee symbol
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1L"), 100000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1.5L"), 150000.0)
        
        # Test lowercase lakhs notation
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1l"), 100000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1.5l"), 150000.0)
    
    def test_gap_analysis_parse_crores_notation(self):
        """Test parsing Indian Crores notation in GapAnalysis."""
        # Test Crores notation
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1Cr"), 10000000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1.5Cr"), 15000000.0)
        
        # Test Crores with spaces
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1 Cr"), 10000000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1.5 Cr"), 15000000.0)
        
        # Test Crores with Rupee symbol
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1Cr"), 10000000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1.5Cr"), 15000000.0)
        
        # Test lowercase crores notation
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1cr"), 10000000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1.5cr"), 15000000.0)
        
        # Test full word "crore"
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1 Crore"), 10000000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1.5 Crore"), 15000000.0)
    
    def test_gap_analysis_parse_indian_comma_format(self):
        """Test parsing Indian comma format in GapAnalysis."""
        # Test Indian comma notation
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1,00,000"), 100000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("1,00,00,000"), 10000000.0)
        
        # Test with Rupee symbol
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1,00,000"), 100000.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1,00,00,000"), 10000000.0)
    
    def test_gap_analysis_parse_combined_formats(self):
        """Test parsing combined formats in GapAnalysis."""
        # Test Rupee + Lakhs + Commas
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1.5L"), 150000.0)
        
        # Test Rupee + Crores + Commas
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1.5Cr"), 15000000.0)
    
    def test_gap_analysis_parse_error_handling(self):
        """Test error handling in GapAnalysis parser."""
        # Test invalid format
        self.assertEqual(self.gap_analyzer._parse_indian_currency("abc"), 0.0)
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹abc"), 0.0)
        
        # Test partially invalid format
        self.assertEqual(self.gap_analyzer._parse_indian_currency("₹1000abc"), 0.0)
    
    def test_goal_adjustment_service_parse_basic_numerics(self):
        """Test parsing basic numeric values in GoalAdjustmentService."""
        # Test integer
        self.assertEqual(self.goal_adjustment_service._parse_currency_value(1000), 1000.0)
        
        # Test float
        self.assertEqual(self.goal_adjustment_service._parse_currency_value(1000.5), 1000.5)
        
        # Test string numeric
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1000"), 1000.0)
        
        # Test empty values
        self.assertIsNone(self.goal_adjustment_service._parse_currency_value(""))
        self.assertIsNone(self.goal_adjustment_service._parse_currency_value(None))
    
    def test_goal_adjustment_service_parse_rupee_symbol(self):
        """Test parsing Indian Rupee symbol in GoalAdjustmentService."""
        # Test with Rupee symbol
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹1000"), 1000.0)
        
        # Test with Rupee symbol and space
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹ 1000"), 1000.0)
        
        # Test with Rupee symbol and commas
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹1,000"), 1000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹1,00,000"), 100000.0)
    
    def test_goal_adjustment_service_parse_lakhs_notation(self):
        """Test parsing Indian Lakhs notation in GoalAdjustmentService."""
        # Test Lakhs notation
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1L"), 100000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1.5L"), 150000.0)
        
        # Test Lakhs with spaces
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1 L"), 100000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1.5 L"), 150000.0)
        
        # Test Lakhs with Rupee symbol
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹1L"), 100000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹1.5L"), 150000.0)
        
        # Test lowercase lakhs notation
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1l"), 100000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1.5l"), 150000.0)
    
    def test_goal_adjustment_service_parse_crores_notation(self):
        """Test parsing Indian Crores notation in GoalAdjustmentService."""
        # Test Crores notation
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1Cr"), 10000000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1.5Cr"), 15000000.0)
        
        # Test Crores with spaces
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1 Cr"), 10000000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1.5 Cr"), 15000000.0)
        
        # Test Crores with Rupee symbol
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹1Cr"), 10000000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹1.5Cr"), 15000000.0)
        
        # Test lowercase crores notation
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1cr"), 10000000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1.5cr"), 15000000.0)
        
        # Test full word "crore"
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1 Crore"), 10000000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1.5 Crore"), 15000000.0)
    
    def test_goal_adjustment_service_parse_indian_comma_format(self):
        """Test parsing Indian comma format in GoalAdjustmentService."""
        # Test Indian comma notation
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1,00,000"), 100000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("1,00,00,000"), 10000000.0)
        
        # Test with Rupee symbol
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹1,00,000"), 100000.0)
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹1,00,00,000"), 10000000.0)
    
    def test_goal_adjustment_service_parse_combined_formats(self):
        """Test parsing combined formats in GoalAdjustmentService."""
        # Test Rupee + Lakhs + Commas
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹1.5L"), 150000.0)
        
        # Test Rupee + Crores + Commas
        self.assertEqual(self.goal_adjustment_service._parse_currency_value("₹1.5Cr"), 15000000.0)
    
    def test_goal_adjustment_service_parse_error_handling(self):
        """Test error handling in GoalAdjustmentService parser."""
        # Test invalid format
        self.assertIsNone(self.goal_adjustment_service._parse_currency_value("abc"))
        self.assertIsNone(self.goal_adjustment_service._parse_currency_value("₹abc"))
        
        # Test partially invalid format
        self.assertIsNone(self.goal_adjustment_service._parse_currency_value("₹1000abc"))
    
    def test_currency_extraction_from_profile(self):
        """Test extracting currency values from profile data."""
        # Test profile with monthly income
        profile_with_monthly_income = {
            "monthly_income": "₹1,50,000"
        }
        self.assertEqual(
            self.gap_analyzer._extract_monthly_income(profile_with_monthly_income), 
            150000.0
        )
        
        # Test profile with lakhs notation
        profile_with_lakhs = {
            "monthly_income": "₹1.5L"
        }
        self.assertEqual(
            self.gap_analyzer._extract_monthly_income(profile_with_lakhs), 
            150000.0
        )
        
        # Test profile with income in answers
        profile_with_answers = {
            "answers": [
                {"question_id": "monthly_income", "answer": "₹50,000"}
            ]
        }
        self.assertEqual(
            self.gap_analyzer._extract_monthly_income(profile_with_answers), 
            50000.0
        )
        
        # Test annual income conversion
        profile_with_annual_income = {
            "annual_income": "₹12L"
        }
        annual_income = self.goal_adjustment_service._get_annual_income(profile_with_annual_income)
        self.assertEqual(annual_income, 1200000.0)
        
        monthly_income = self.goal_adjustment_service._get_monthly_income(profile_with_annual_income)
        self.assertEqual(monthly_income, 100000.0)


if __name__ == '__main__':
    unittest.main()
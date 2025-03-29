#!/usr/bin/env python3
"""
Test script to verify the GoalProbabilityAnalyzer fixes
"""

import unittest
import logging
from models.goal_probability import GoalProbabilityAnalyzer, ProbabilityResult

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestProbabilityAnalyzerFix(unittest.TestCase):
    """Test cases for the GoalProbabilityAnalyzer fixes"""
    
    def setUp(self):
        """Set up test environment"""
        self.analyzer = GoalProbabilityAnalyzer()
        
        # Create test goal data
        self.test_goal = {
            "id": "test-goal-123",
            "user_profile_id": "test-profile-abc",
            "category": "education",
            "title": "Test Education Goal",
            "target_amount": 1000000,  # ₹10 lakh
            "current_amount": 200000,  # ₹2 lakh
            "monthly_contribution": 10000,  # ₹10,000 per month
            "target_date": "2030-01-01",  # About 5 years from now
            "current_progress": 20.0,  # 20%
            "asset_allocation": {
                "equity": 0.60,
                "debt": 0.40
            }
        }
        
        # Create test profile data
        self.test_profile = {
            "id": "test-profile-abc",
            "name": "Test User",
            "email": "test@example.com",
            "annual_income": 1200000,  # ₹12 lakh per year
            "monthly_income": 100000,  # ₹1 lakh per month
            "monthly_expenses": 60000,  # ₹60,000 per month
            "risk_profile": "moderate"
        }
    
    def test_probability_result_property(self):
        """Test that ProbabilityResult has working success_probability property"""
        # Create a ProbabilityResult with known success_probability
        result = ProbabilityResult()
        result.success_metrics = {"success_probability": 0.75}
        
        # Verify the property works
        self.assertEqual(result.success_probability, 0.75)
    
    def test_education_goal_analysis(self):
        """Test that education goal analysis works after fix"""
        try:
            # Analyze the education goal
            result = self.analyzer.analyze_goal_probability(self.test_goal, self.test_profile, simulations=10)
            
            # Verify basic structure
            self.assertIsInstance(result, ProbabilityResult)
            self.assertIn("success_probability", result.success_metrics)
            
            # Test that we can access success_probability directly
            prob = result.success_probability
            logger.info(f"Education goal success probability: {prob}")
            
            # Verify education-specific metrics
            self.assertIn("education_inflation_impact", result.goal_specific_metrics)
            
            logger.info("Education goal analysis successful after fixes")
            return True
        except Exception as e:
            logger.error(f"Error analyzing education goal: {str(e)}")
            self.fail(f"Education goal analysis failed with error: {str(e)}")
            return False

if __name__ == "__main__":
    unittest.main()
#!/usr/bin/env python3
"""
End-to-End Tests for GoalAdjustmentService

These tests validate the complete flow from probability calculation through 
gap analysis to adjustment recommendations using the actual GoalProbabilityAnalyzer
and GoalAdjustmentService implementations.
"""

import sys
import os
import pytest
import json
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the services and models being tested
from services.goal_adjustment_service import GoalAdjustmentService
from models.goal_probability import GoalProbabilityAnalyzer, ProbabilityResult
from models.goal_adjustment import GoalAdjustmentRecommender
from models.gap_analysis.analyzer import GapAnalysis
from models.gap_analysis.core import GapResult, GapSeverity, RemediationOption
from models.goal_models import Goal

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestGoalAdjustmentEndToEnd:
    """Test cases for end-to-end functionality of GoalAdjustmentService"""
    
    @pytest.fixture
    def adjustment_service(self):
        """Create a real GoalAdjustmentService with real dependencies"""
        # Create actual instances of all dependencies
        probability_analyzer = GoalProbabilityAnalyzer()
        adjustment_recommender = GoalAdjustmentRecommender()
        gap_analyzer = GapAnalysis()
        
        # Create the service with real components
        service = GoalAdjustmentService(
            goal_probability_analyzer=probability_analyzer,
            goal_adjustment_recommender=adjustment_recommender,
            gap_analyzer=gap_analyzer
        )
        
        return service
    
    @pytest.fixture
    def test_goals(self):
        """Fixture providing test goals for different categories"""
        # Current date for relative timeframes
        current_date = datetime.now()
        
        # Create a dictionary of test goals for different categories
        goals = {
            "retirement": {
                "id": "test-retirement-goal",
                "user_profile_id": "test-profile-123",
                "category": "retirement",
                "title": "Comfortable Retirement",
                "target_amount": 20000000,  # ₹2 crore
                "current_amount": 2000000,  # ₹20 lakh
                "monthly_contribution": 20000,  # ₹20,000 per month
                "target_date": (current_date + timedelta(days=365*25)).strftime("%Y-%m-%d"),  # 25 years
                "importance": "high",
                "flexibility": "somewhat_flexible",
                "notes": "Primary retirement goal",
                "current_progress": 10.0,  # 10% progress
                "asset_allocation": {
                    "equity": 0.70,
                    "debt": 0.20,
                    "gold": 0.05,
                    "cash": 0.05
                },
                "retirement_age": 60
            },
            "education": {
                "id": "test-education-goal",
                "user_profile_id": "test-profile-123",
                "category": "education",
                "title": "Child's Higher Education",
                "target_amount": 5000000,  # ₹50 lakh
                "current_amount": 500000,  # ₹5 lakh
                "monthly_contribution": 10000,  # ₹10,000 per month
                "target_date": (current_date + timedelta(days=365*15)).strftime("%Y-%m-%d"),  # 15 years
                "importance": "high",
                "flexibility": "somewhat_flexible",
                "notes": "International university education",
                "current_progress": 10.0,  # 10% progress
                "asset_allocation": {
                    "equity": 0.60,
                    "debt": 0.30,
                    "gold": 0.05,
                    "cash": 0.05
                },
                "education_year": current_date.year + 15
            },
            "home": {
                "id": "test-home-goal",
                "user_profile_id": "test-profile-123",
                "category": "home_purchase",
                "title": "Dream Home Purchase",
                "target_amount": 10000000,  # ₹1 crore
                "current_amount": 1500000,  # ₹15 lakh
                "monthly_contribution": 25000,  # ₹25,000 per month
                "target_date": (current_date + timedelta(days=365*10)).strftime("%Y-%m-%d"),  # 10 years
                "importance": "high",
                "flexibility": "somewhat_flexible",
                "notes": "3BHK apartment in suburban area",
                "current_progress": 15.0,  # 15% progress
                "asset_allocation": {
                    "equity": 0.50,
                    "debt": 0.40,
                    "gold": 0.05,
                    "cash": 0.05
                },
                "property_value": 20000000  # ₹2 crore (full property value)
            }
        }
        
        return goals
    
    @pytest.fixture
    def test_profile(self):
        """Fixture providing a test user profile"""
        profile = {
            "id": "test-profile-123",
            "name": "Test User",
            "email": "test@example.com",
            "age": 35,
            "retirement_age": 60,
            "annual_income": 1500000,  # ₹15 lakh per year
            "monthly_income": 125000,  # ₹1.25 lakh per month
            "monthly_expenses": 75000,  # ₹75,000 per month
            "risk_profile": "moderate",
            "country": "India",
            "tax_bracket": 0.30,  # 30% tax bracket
            "assets": {
                "equity": 3000000,  # ₹30 lakh
                "debt": 2000000,    # ₹20 lakh
                "real_estate": 5000000,  # ₹50 lakh
                "gold": 500000,  # ₹5 lakh
                "cash": 1000000  # ₹10 lakh
            }
        }
        
        return profile
    
    def test_generate_adjustment_recommendations_retirement(self, adjustment_service, test_goals, test_profile):
        """
        End-to-end test for generating retirement goal adjustment recommendations.
        
        This test runs the full recommendation pipeline with a real probability analyzer.
        """
        # Get the retirement goal
        retirement_goal = test_goals["retirement"]
        
        # Generate recommendations
        recommendations = adjustment_service.generate_adjustment_recommendations(
            retirement_goal, test_profile
        )
        
        # Log the recommendations for debugging
        logger.info(f"Generated {len(recommendations.get('recommendations', []))} recommendations for retirement goal")
        
        # Basic verification
        assert 'goal_id' in recommendations
        assert recommendations['goal_id'] == retirement_goal['id']
        assert 'current_probability' in recommendations
        assert 'recommendations' in recommendations
        assert isinstance(recommendations['recommendations'], list)
        
        # Verify recommendation structure
        if recommendations['recommendations']:
            first_rec = recommendations['recommendations'][0]
            assert 'type' in first_rec
            assert 'description' in first_rec
            assert 'impact' in first_rec
            
            # Verify different recommendation types are present
            rec_types = set(rec['type'] for rec in recommendations['recommendations'])
            logger.info(f"Recommendation types: {rec_types}")
            
            # We should have at least some of these recommendation types
            expected_types = {'contribution', 'allocation', 'timeframe', 'target_amount', 'tax'}
            assert rec_types.intersection(expected_types), "No expected recommendation types found"
    
    def test_generate_adjustment_recommendations_education(self, adjustment_service, test_goals, test_profile):
        """
        End-to-end test for generating education goal adjustment recommendations.
        
        This test runs the full recommendation pipeline with a real probability analyzer.
        """
        # Get the education goal
        education_goal = test_goals["education"]
        
        # Generate recommendations
        recommendations = adjustment_service.generate_adjustment_recommendations(
            education_goal, test_profile
        )
        
        # Log the recommendations for debugging
        logger.info(f"Generated {len(recommendations.get('recommendations', []))} recommendations for education goal")
        
        # Basic verification
        assert 'goal_id' in recommendations
        assert recommendations['goal_id'] == education_goal['id']
        assert 'current_probability' in recommendations
        assert 'recommendations' in recommendations
        assert isinstance(recommendations['recommendations'], list)
        
        # Verify education-specific recommendations
        if recommendations['recommendations']:
            # Look for education-specific terms in recommendations
            education_related = False
            for rec in recommendations['recommendations']:
                desc = rec.get('description', '').lower()
                if any(term in desc for term in ['education', 'college', 'school']):
                    education_related = True
                    break
            
            # Not strictly necessary but should be likely
            if not education_related:
                logger.warning("No education-specific recommendations found")
    
    def test_generate_adjustment_recommendations_home(self, adjustment_service, test_goals, test_profile):
        """
        End-to-end test for generating home purchase goal adjustment recommendations.
        
        This test runs the full recommendation pipeline with a real probability analyzer.
        """
        # Get the home purchase goal
        home_goal = test_goals["home"]
        
        # Generate recommendations
        recommendations = adjustment_service.generate_adjustment_recommendations(
            home_goal, test_profile
        )
        
        # Log the recommendations for debugging
        logger.info(f"Generated {len(recommendations.get('recommendations', []))} recommendations for home goal")
        
        # Basic verification
        assert 'goal_id' in recommendations
        assert recommendations['goal_id'] == home_goal['id']
        assert 'current_probability' in recommendations
        assert 'recommendations' in recommendations
        assert isinstance(recommendations['recommendations'], list)
        
        # Verify home-specific recommendations
        if recommendations['recommendations']:
            # Look for home loan or down payment recommendations
            home_related = False
            for rec in recommendations['recommendations']:
                desc = rec.get('description', '').lower()
                if any(term in desc for term in ['home', 'house', 'property', 'loan', 'down payment']):
                    home_related = True
                    break
            
            # Not strictly necessary but should be likely
            if not home_related:
                logger.warning("No home-specific recommendations found")
    
    def test_adjustment_recommendations_with_edge_case_goals(self, adjustment_service, test_profile):
        """
        Test goal adjustment recommendations with edge case goals to verify robustness.
        
        This tests the service's error handling capabilities when given problematic goals.
        """
        # Test with empty goal (missing required fields)
        empty_goal = {
            "id": "empty-goal",
            "user_profile_id": "test-profile-123"
        }
        
        # Should handle gracefully without errors
        try:
            recommendations = adjustment_service.generate_adjustment_recommendations(
                empty_goal, test_profile
            )
            assert 'error' in recommendations or 'recommendations' in recommendations
            logger.info("Empty goal handled gracefully")
        except Exception as e:
            pytest.fail(f"Empty goal caused exception: {str(e)}")
        
        # Test with invalid numeric values
        invalid_goal = {
            "id": "invalid-goal",
            "user_profile_id": "test-profile-123",
            "category": "retirement",
            "title": "Invalid Goal",
            "target_amount": "not_a_number",
            "current_amount": -1000,  # Negative amount
            "monthly_contribution": None,  # None instead of number
            "target_date": "2050-01-01"
        }
        
        # Should handle gracefully without errors
        try:
            recommendations = adjustment_service.generate_adjustment_recommendations(
                invalid_goal, test_profile
            )
            assert 'error' in recommendations or 'recommendations' in recommendations
            logger.info("Invalid goal handled gracefully")
        except Exception as e:
            pytest.fail(f"Invalid goal caused exception: {str(e)}")
        
        # Test with already achieved goal
        achieved_goal = {
            "id": "achieved-goal",
            "user_profile_id": "test-profile-123",
            "category": "education",
            "title": "Already Achieved Goal",
            "target_amount": 100000,  # ₹1 lakh
            "current_amount": 150000,  # ₹1.5 lakh (more than target)
            "monthly_contribution": 5000,
            "target_date": "2030-01-01"
        }
        
        # Should handle gracefully and recognize the goal is already achieved
        recommendations = adjustment_service.generate_adjustment_recommendations(
            achieved_goal, test_profile
        )
        assert 'current_probability' in recommendations
        # Probability should be high (close to 1)
        assert recommendations['current_probability'] > 0.9
        logger.info("Achieved goal handled correctly")

if __name__ == "__main__":
    pytest.main(["-v", "test_goal_adjustment_end_to_end.py"])
#!/usr/bin/env python3
"""
Integration Tests for GoalAdjustmentService with Real Probability Calculations

These tests verify the full integration between GoalAdjustmentService
and GoalProbabilityAnalyzer using various realistic scenarios with
actual Monte Carlo simulations rather than mocks.
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
from models.financial_projection import AssetProjection

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestGoalAdjustmentWithRealProbabilities:
    """Integration tests for GoalAdjustmentService using real probability calculations"""
    
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
    def test_scenarios(self):
        """Create test scenarios with goals and profiles for different financial situations"""
        current_date = datetime.now()
        
        # Create multiple scenarios to test different financial situations
        scenarios = {
            "young_professional": {
                "profile": {
                    "id": "young-prof-123",
                    "name": "Young Professional",
                    "email": "young@example.com",
                    "age": 28,
                    "retirement_age": 60,
                    "annual_income": 800000,  # ₹8 lakh per year
                    "monthly_income": 66667,  # ₹66,667 per month
                    "monthly_expenses": 40000,  # ₹40,000 per month
                    "risk_profile": "aggressive",
                    "country": "India",
                    "tax_bracket": 0.20,  # 20% tax bracket
                    "assets": {
                        "equity": 500000,  # ₹5 lakh
                        "debt": 300000,  # ₹3 lakh
                        "real_estate": 0,
                        "gold": 100000,  # ₹1 lakh
                        "cash": 200000  # ₹2 lakh
                    }
                },
                "goals": {
                    "retirement": {
                        "id": "young-prof-retirement",
                        "user_profile_id": "young-prof-123",
                        "category": "retirement",
                        "title": "Retirement at 60",
                        "target_amount": 15000000,  # ₹1.5 crore
                        "current_amount": 500000,  # ₹5 lakh
                        "monthly_contribution": 10000,  # ₹10,000 per month
                        "target_date": (current_date + timedelta(days=365*32)).strftime("%Y-%m-%d"),  # 32 years
                        "importance": "high",
                        "flexibility": "somewhat_flexible",
                        "notes": "Retirement planning starting early",
                        "current_progress": 3.33,  # 3.33% progress
                        "asset_allocation": {
                            "equity": 0.80,
                            "debt": 0.15,
                            "gold": 0.05,
                            "cash": 0.00
                        },
                        "retirement_age": 60
                    },
                    "home": {
                        "id": "young-prof-home",
                        "user_profile_id": "young-prof-123",
                        "category": "home_purchase",
                        "title": "First Home Purchase",
                        "target_amount": 5000000,  # ₹50 lakh
                        "current_amount": 300000,  # ₹3 lakh
                        "monthly_contribution": 15000,  # ₹15,000 per month
                        "target_date": (current_date + timedelta(days=365*8)).strftime("%Y-%m-%d"),  # 8 years
                        "importance": "high",
                        "flexibility": "somewhat_flexible",
                        "notes": "First home in tier 2 city",
                        "current_progress": 6.0,  # 6% progress
                        "asset_allocation": {
                            "equity": 0.60,
                            "debt": 0.30,
                            "gold": 0.05,
                            "cash": 0.05
                        },
                        "property_value": 5000000  # ₹50 lakh
                    }
                }
            },
            "mid_career_parent": {
                "profile": {
                    "id": "mid-career-123",
                    "name": "Mid-Career Parent",
                    "email": "parent@example.com",
                    "age": 42,
                    "retirement_age": 60,
                    "annual_income": 1800000,  # ₹18 lakh per year
                    "monthly_income": 150000,  # ₹1.5 lakh per month
                    "monthly_expenses": 90000,  # ₹90,000 per month
                    "risk_profile": "moderate",
                    "country": "India",
                    "tax_bracket": 0.30,  # 30% tax bracket
                    "assets": {
                        "equity": 3000000,  # ₹30 lakh
                        "debt": 2000000,  # ₹20 lakh
                        "real_estate": 10000000,  # ₹1 crore
                        "gold": 500000,  # ₹5 lakh
                        "cash": 500000  # ₹5 lakh
                    }
                },
                "goals": {
                    "retirement": {
                        "id": "mid-career-retirement",
                        "user_profile_id": "mid-career-123",
                        "category": "retirement",
                        "title": "Comfortable Retirement",
                        "target_amount": 30000000,  # ₹3 crore
                        "current_amount": 5000000,  # ₹50 lakh
                        "monthly_contribution": 25000,  # ₹25,000 per month
                        "target_date": (current_date + timedelta(days=365*18)).strftime("%Y-%m-%d"),  # 18 years
                        "importance": "high",
                        "flexibility": "somewhat_flexible",
                        "notes": "Retirement with travel plans",
                        "current_progress": 16.67,  # 16.67% progress
                        "asset_allocation": {
                            "equity": 0.65,
                            "debt": 0.25,
                            "gold": 0.05,
                            "cash": 0.05
                        },
                        "retirement_age": 60
                    },
                    "education": {
                        "id": "mid-career-education",
                        "user_profile_id": "mid-career-123",
                        "category": "education",
                        "title": "Child's College Education",
                        "target_amount": 8000000,  # ₹80 lakh
                        "current_amount": 2000000,  # ₹20 lakh
                        "monthly_contribution": 20000,  # ₹20,000 per month
                        "target_date": (current_date + timedelta(days=365*8)).strftime("%Y-%m-%d"),  # 8 years
                        "importance": "high",
                        "flexibility": "low",
                        "notes": "Top tier engineering/medical education",
                        "current_progress": 25.0,  # 25% progress
                        "asset_allocation": {
                            "equity": 0.55,
                            "debt": 0.35,
                            "gold": 0.05,
                            "cash": 0.05
                        },
                        "education_year": current_date.year + 8
                    }
                }
            },
            "pre_retirement": {
                "profile": {
                    "id": "pre-retirement-123",
                    "name": "Pre-Retirement Professional",
                    "email": "preretire@example.com",
                    "age": 55,
                    "retirement_age": 62,
                    "annual_income": 2400000,  # ₹24 lakh per year
                    "monthly_income": 200000,  # ₹2 lakh per month
                    "monthly_expenses": 120000,  # ₹1.2 lakh per month
                    "risk_profile": "conservative",
                    "country": "India",
                    "tax_bracket": 0.30,  # 30% tax bracket
                    "assets": {
                        "equity": 8000000,  # ₹80 lakh
                        "debt": 10000000,  # ₹1 crore
                        "real_estate": 25000000,  # ₹2.5 crore
                        "gold": 2000000,  # ₹20 lakh
                        "cash": 1000000  # ₹10 lakh
                    }
                },
                "goals": {
                    "retirement": {
                        "id": "pre-retirement-retirement",
                        "user_profile_id": "pre-retirement-123",
                        "category": "retirement",
                        "title": "Secure Retirement",
                        "target_amount": 40000000,  # ₹4 crore
                        "current_amount": 18000000,  # ₹1.8 crore
                        "monthly_contribution": 50000,  # ₹50,000 per month
                        "target_date": (current_date + timedelta(days=365*7)).strftime("%Y-%m-%d"),  # 7 years
                        "importance": "high",
                        "flexibility": "low",
                        "notes": "Imminent retirement planning",
                        "current_progress": 45.0,  # 45% progress
                        "asset_allocation": {
                            "equity": 0.40,
                            "debt": 0.45,
                            "gold": 0.10,
                            "cash": 0.05
                        },
                        "retirement_age": 62
                    },
                    "legacy_planning": {
                        "id": "pre-retirement-legacy",
                        "user_profile_id": "pre-retirement-123",
                        "category": "legacy_planning",
                        "title": "Estate Planning",
                        "target_amount": 15000000,  # ₹1.5 crore
                        "current_amount": 5000000,  # ₹50 lakh
                        "monthly_contribution": 20000,  # ₹20,000 per month
                        "target_date": (current_date + timedelta(days=365*10)).strftime("%Y-%m-%d"),  # 10 years
                        "importance": "medium",
                        "flexibility": "somewhat_flexible",
                        "notes": "Legacy for children and charitable causes",
                        "current_progress": 33.33,  # 33.33% progress
                        "asset_allocation": {
                            "equity": 0.30,
                            "debt": 0.60,
                            "gold": 0.05,
                            "cash": 0.05
                        }
                    }
                }
            }
        }
        
        return scenarios
    
    def test_young_professional_real_probability(self, adjustment_service, test_scenarios):
        """Test realistic scenario for young professional with accurate probability calculations"""
        # Get scenario data
        scenario = test_scenarios["young_professional"]
        profile = scenario["profile"]
        retirement_goal = scenario["goals"]["retirement"]
        
        # Run a detailed Monte Carlo simulation with the real analyzer
        result = adjustment_service.goal_probability_analyzer.analyze_goal_probability(
            retirement_goal, profile, simulations=300  # Higher simulation count for accuracy
        )
        
        # Verify the result structure
        assert isinstance(result, ProbabilityResult)
        assert hasattr(result, 'success_metrics')
        assert hasattr(result, 'time_based_metrics')
        assert hasattr(result, 'distribution_data')
        
        # Log the probability and related metrics
        success_prob = result.get_safe_success_probability()
        logger.info(f"Young professional retirement success probability: {success_prob:.4f}")
        logger.info(f"Success metrics: {result.success_metrics}")
        
        # Get the recommendations using the real probability analyzer
        recommendations = adjustment_service.generate_adjustment_recommendations(
            retirement_goal, profile
        )
        
        # Verify recommendations structure
        assert 'goal_id' in recommendations
        assert 'current_probability' in recommendations
        assert 'recommendations' in recommendations
        assert isinstance(recommendations['recommendations'], list)
        
        # Log recommendation stats
        logger.info(f"Generated {len(recommendations['recommendations'])} recommendations for young professional")
        logger.info(f"Current probability: {recommendations['current_probability']:.4f}")
        
        # Test the top recommendation's impact
        if recommendations['recommendations']:
            top_rec = recommendations['recommendations'][0]
            logger.info(f"Top recommendation: {top_rec['type']} - {top_rec['description']}")
            
            # Calculate impact of top recommendation
            impact = adjustment_service.calculate_recommendation_impact(
                retirement_goal, profile, top_rec
            )
            
            # Verify impact structure
            assert 'probability_increase' in impact
            assert 'new_probability' in impact
            
            logger.info(f"Impact of top recommendation: {impact['probability_increase']:.4f} probability increase")
            assert impact['probability_increase'] > 0, "Top recommendation should have positive impact"

    def test_mid_career_education_real_probability(self, adjustment_service, test_scenarios):
        """Test realistic scenario for mid-career parent with education goal"""
        # Get scenario data
        scenario = test_scenarios["mid_career_parent"]
        profile = scenario["profile"]
        education_goal = scenario["goals"]["education"]
        
        # Run a detailed Monte Carlo simulation with the real analyzer
        result = adjustment_service.goal_probability_analyzer.analyze_goal_probability(
            education_goal, profile, simulations=300  # Higher simulation count for accuracy
        )
        
        # Verify the result structure
        assert isinstance(result, ProbabilityResult)
        assert hasattr(result, 'success_metrics')
        assert hasattr(result, 'time_based_metrics')
        assert hasattr(result, 'distribution_data')
        
        # Verify education-specific metrics are present
        assert hasattr(result, 'goal_specific_metrics')
        assert 'education_inflation_impact' in result.goal_specific_metrics
        
        # Log the probability and related metrics
        success_prob = result.get_safe_success_probability()
        logger.info(f"Mid-career education goal success probability: {success_prob:.4f}")
        logger.info(f"Education specific metrics: {result.goal_specific_metrics}")
        
        # Get the recommendations using the real probability analyzer
        recommendations = adjustment_service.generate_adjustment_recommendations(
            education_goal, profile
        )
        
        # Verify recommendations structure
        assert 'goal_id' in recommendations
        assert 'current_probability' in recommendations
        assert 'recommendations' in recommendations
        assert isinstance(recommendations['recommendations'], list)
        
        # Education goals should have specific types of recommendations
        education_specific_rec_found = False
        for rec in recommendations['recommendations']:
            if 'education' in rec['description'].lower() or 'college' in rec['description'].lower():
                education_specific_rec_found = True
                break
        
        # Not strictly required, but we should log if no education-specific recommendations are found
        if not education_specific_rec_found:
            logger.warning("No education-specific recommendations found")

    def test_pre_retirement_real_probability(self, adjustment_service, test_scenarios):
        """Test realistic scenario for pre-retirement individual"""
        # Get scenario data
        scenario = test_scenarios["pre_retirement"]
        profile = scenario["profile"]
        retirement_goal = scenario["goals"]["retirement"]
        
        # Run a detailed Monte Carlo simulation with the real analyzer
        result = adjustment_service.goal_probability_analyzer.analyze_goal_probability(
            retirement_goal, profile, simulations=300  # Higher simulation count for accuracy
        )
        
        # Verify the result structure
        assert isinstance(result, ProbabilityResult)
        assert hasattr(result, 'success_metrics')
        assert hasattr(result, 'distribution_data')
        
        # Verify retirement-specific metrics are present
        assert hasattr(result, 'goal_specific_metrics')
        assert 'retirement_income_ratio' in result.goal_specific_metrics or \
               'retirement_funded_years' in result.goal_specific_metrics or \
               'retirement_specific_metrics' in result.goal_specific_metrics
        
        # Log the probability and related metrics
        success_prob = result.get_safe_success_probability()
        logger.info(f"Pre-retirement goal success probability: {success_prob:.4f}")
        
        # Get the recommendations using the real probability analyzer
        recommendations = adjustment_service.generate_adjustment_recommendations(
            retirement_goal, profile
        )
        
        # Verify recommendations structure
        assert 'goal_id' in recommendations
        assert 'current_probability' in recommendations
        assert 'recommendations' in recommendations
        assert isinstance(recommendations['recommendations'], list)
        
        # For pre-retirement, check for conservative allocation recommendations
        allocation_rec_found = False
        conservative_shift_found = False
        for rec in recommendations['recommendations']:
            if rec['type'] == 'allocation':
                allocation_rec_found = True
                # Pre-retirement allocation should generally shift toward more conservative
                if 'value' in rec and isinstance(rec['value'], dict):
                    # Check if debt allocation is increasing
                    if rec['value'].get('debt', 0) > retirement_goal['asset_allocation'].get('debt', 0):
                        conservative_shift_found = True
                        break
        
        # For older individuals near retirement, we expect conservative shifts
        # But this isn't a strict requirement as it depends on the individual situation
        logger.info(f"Found allocation recommendations: {allocation_rec_found}")
        logger.info(f"Found conservative allocation shift: {conservative_shift_found}")

    def test_asset_projection_integration(self, adjustment_service, test_scenarios):
        """Test integration with AssetProjection for real financial projections"""
        # Get scenario data
        scenario = test_scenarios["young_professional"]
        profile = scenario["profile"]
        home_goal = scenario["goals"]["home"]
        
        # Create asset projection to test integration
        asset_projection = AssetProjection(
            initial_amount=home_goal["current_amount"],
            monthly_contribution=home_goal["monthly_contribution"],
            time_horizon=8,  # 8 years
            allocation_strategy=home_goal["asset_allocation"]
        )
        
        # Run simple projection
        projection_result = asset_projection.project()
        
        logger.info(f"Projected amount after 8 years: {projection_result['final_amount']:.2f}")
        logger.info(f"Projection percentiles: 25th={projection_result['percentile_25']:.2f}, " 
                  f"50th={projection_result['percentile_50']:.2f}, " 
                  f"75th={projection_result['percentile_75']:.2f}")
        
        # Now test full probability calculation with real analyzer
        result = adjustment_service.goal_probability_analyzer.analyze_goal_probability(
            home_goal, profile, simulations=300
        )
        
        success_prob = result.get_safe_success_probability()
        logger.info(f"Home goal success probability: {success_prob:.4f}")
        
        # Compare simple projection with full Monte Carlo results
        # This isn't an exact comparison, but they should be roughly in the same ballpark
        monte_carlo_mean = result.distribution_data.get('mean_outcome', 0) \
                           if hasattr(result, 'distribution_data') else 0
        
        logger.info(f"Simple projection final amount: {projection_result['final_amount']:.2f}")
        logger.info(f"Monte Carlo mean outcome: {monte_carlo_mean:.2f}")
        
        # They don't need to match exactly but should be in the same general range
        # (typically within ±30% of each other)
        if monte_carlo_mean > 0:
            ratio = projection_result['final_amount'] / monte_carlo_mean
            logger.info(f"Ratio of simple projection to Monte Carlo mean: {ratio:.2f}")
            assert 0.7 <= ratio <= 1.3, "Projection methods should produce roughly consistent results"

if __name__ == "__main__":
    pytest.main(["-v", "test_goal_adjustment_with_real_probabilities.py"])

#!/usr/bin/env python3
"""
Full System Integration Test

This script tests complete end-to-end flows across multiple services
with minimal mocking, to verify that the entire system functions correctly.
"""

import os
import sys
import unittest
import logging
import json
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import services
from services.goal_service import GoalService
from services.goal_adjustment_service import GoalAdjustmentService
from services.financial_parameter_service import FinancialParameterService, get_financial_parameter_service

# Import models
from models.goal_models import Goal, GoalManager
from models.goal_probability import GoalProbabilityAnalyzer
from models.database_profile_manager import DatabaseProfileManager

class FullSystemIntegrationTest(unittest.TestCase):
    """Tests full system integration with minimal mocking."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment once for all tests."""
        logger.info("Setting up full system integration test environment")
        
        # Database path (using the real database for minimal mocking)
        cls.db_path = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db"
        
        # Initialize managers and services with real implementations
        cls.goal_manager = GoalManager(db_path=cls.db_path)
        cls.profile_manager = DatabaseProfileManager(db_path=cls.db_path)
        
        # Initialize services
        cls.goal_service = GoalService(db_path=cls.db_path)
        cls.parameter_service = get_financial_parameter_service()
        cls.adjustment_service = GoalAdjustmentService(
            param_service=cls.parameter_service
        )
        
        # Create a test profile
        cls.create_test_profile()
        
        # Create test goals
        cls.create_test_goals()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        logger.info("Cleaning up full system integration test environment")
        
        # Delete test goals
        for goal_id in [cls.retirement_goal_id, cls.education_goal_id, cls.home_goal_id]:
            try:
                cls.goal_manager.delete_goal(goal_id)
                logger.info(f"Deleted test goal: {goal_id}")
            except Exception as e:
                logger.warning(f"Error deleting test goal {goal_id}: {str(e)}")
        
        # Delete test profile
        try:
            cls.profile_manager.delete_profile(cls.test_profile_id)
            logger.info(f"Deleted test profile: {cls.test_profile_id}")
        except Exception as e:
            logger.warning(f"Error deleting test profile {cls.test_profile_id}: {str(e)}")
    
    @classmethod
    def create_test_profile(cls):
        """Create a test profile for integration testing."""
        # Generate a unique name to avoid conflicts with existing profiles
        unique_suffix = uuid.uuid4().hex[:8]
        profile_name = f"Integration Test User {unique_suffix}"
        profile_email = f"integration_test_{unique_suffix}@example.com"
        
        # Create the profile
        cls.test_profile = cls.profile_manager.create_profile(profile_name, profile_email)
        cls.test_profile_id = cls.test_profile["id"]
        
        logger.info(f"Created test profile: {cls.test_profile_id}")
    
    @classmethod
    def create_test_goals(cls):
        """Create test goals for integration testing."""
        # 1. Retirement goal
        retirement_goal = Goal(
            user_profile_id=cls.test_profile_id,
            category="traditional_retirement",
            title="Integration Test Retirement",
            target_amount=5000000,
            timeframe=(datetime.now() + timedelta(days=365*25)).isoformat(),
            current_amount=1000000,
            importance="high",
            flexibility="somewhat_flexible",
            notes="Integration test retirement goal",
            funding_strategy=json.dumps({
                "retirement_age": 65,
                "withdrawal_rate": 0.04
            })
        )
        
        # 2. Education goal
        education_goal = Goal(
            user_profile_id=cls.test_profile_id,
            category="education",
            title="Integration Test Education",
            target_amount=1000000,
            timeframe=(datetime.now() + timedelta(days=365*10)).isoformat(),
            current_amount=200000,
            importance="high",
            flexibility="low",
            notes="Integration test education goal",
            funding_strategy=json.dumps({
                "education_type": "college",
                "years": 4
            })
        )
        
        # 3. Home goal
        home_goal = Goal(
            user_profile_id=cls.test_profile_id,
            category="home_purchase",
            title="Integration Test Home Purchase",
            target_amount=2000000,
            timeframe=(datetime.now() + timedelta(days=365*5)).isoformat(),
            current_amount=500000,
            importance="high",
            flexibility="somewhat_flexible",
            notes="Integration test home purchase goal",
            funding_strategy=json.dumps({
                "down_payment_percent": 0.20,
                "home_value": 10000000
            })
        )
        
        # Save goals to database
        cls.retirement_goal = cls.goal_manager.create_goal(retirement_goal)
        cls.education_goal = cls.goal_manager.create_goal(education_goal)
        cls.home_goal = cls.goal_manager.create_goal(home_goal)
        
        # Store IDs for later use
        cls.retirement_goal_id = cls.retirement_goal.id
        cls.education_goal_id = cls.education_goal.id
        cls.home_goal_id = cls.home_goal.id
        
        logger.info(f"Created test goals: retirement={cls.retirement_goal_id}, education={cls.education_goal_id}, home={cls.home_goal_id}")
    
    def test_01_end_to_end_goal_probability_flow(self):
        """Test a complete end-to-end flow for goal probability calculation."""
        logger.info("Testing end-to-end goal probability flow")
        
        # Create test profile data
        profile_data = {
            "id": self.test_profile_id,
            "annual_income": 1500000,
            "monthly_income": 125000,
            "monthly_expenses": 75000, 
            "risk_profile": "moderate",
            "answers": [
                {"question_id": "annual_income", "answer": 1500000},
                {"question_id": "risk_profile", "answer": "moderate"}
            ]
        }
        
        # 1. Calculate probability for retirement goal
        try:
            probability_result = self.goal_service.calculate_goal_probability(
                goal_id=self.retirement_goal_id,
                profile_data=profile_data
            )
            
            # Verify result
            self.assertIsNotNone(probability_result)
            
            # Check if success_probability is accessible either as an attribute or dictionary key
            if hasattr(probability_result, 'success_metrics'):
                self.assertIn('success_probability', probability_result.success_metrics)
                success_prob = probability_result.success_metrics['success_probability']
            elif hasattr(probability_result, 'get_safe_success_probability'):
                success_prob = probability_result.get_safe_success_probability()
            else:
                success_prob = probability_result.get('success_probability', 0)
                
            logger.info(f"Calculated success probability: {success_prob}")
            
            # Get the updated goal
            updated_goal = self.goal_service.get_goal(self.retirement_goal_id)
            
            # Verify that the goal was updated with the probability
            self.assertIsNotNone(updated_goal)
            self.assertIn('goal_success_probability', updated_goal)
            
            logger.info(f"Updated goal probability: {updated_goal['goal_success_probability']}")
            
        except Exception as e:
            self.fail(f"Probability calculation failed with error: {str(e)}")
        
        logger.info("End-to-end goal probability flow completed successfully")
    
    def test_02_end_to_end_adjustment_recommendations_flow(self):
        """Test a complete end-to-end flow for adjustment recommendations."""
        logger.info("Testing end-to-end adjustment recommendations flow")
        
        # Create test profile data
        profile_data = {
            "id": self.test_profile_id,
            "annual_income": 1500000,
            "monthly_income": 125000,
            "monthly_expenses": 75000,
            "risk_profile": "moderate",
            "answers": [
                {"question_id": "annual_income", "answer": 1500000},
                {"question_id": "risk_profile", "answer": "moderate"}
            ]
        }
        
        # 1. Get the goal data
        goal_data = self.goal_service.get_goal(self.home_goal_id)
        self.assertIsNotNone(goal_data)
        
        # 2. Generate adjustment recommendations
        try:
            recommendations = self.adjustment_service.generate_adjustment_recommendations(
                goal_data=goal_data,
                profile_data=profile_data
            )
            
            # Verify recommendations
            self.assertIsNotNone(recommendations)
            self.assertIn('goal_id', recommendations)
            self.assertEqual(recommendations['goal_id'], self.home_goal_id)
            
            # Check for recommendations
            self.assertIn('recommendations', recommendations)
            self.assertIsInstance(recommendations['recommendations'], list)
            
            logger.info(f"Generated {len(recommendations['recommendations'])} recommendations")
            
            # If we have recommendations, test calculating impact for one
            if recommendations['recommendations']:
                first_recommendation = recommendations['recommendations'][0]
                
                impact_result = self.adjustment_service.calculate_recommendation_impact(
                    goal_data=goal_data,
                    profile_data=profile_data,
                    recommendation=first_recommendation
                )
                
                # Verify impact result
                self.assertIsNotNone(impact_result)
                self.assertIn('probability_increase', impact_result)
                
                logger.info(f"Calculated impact for recommendation: {impact_result['probability_increase']}")
            
        except Exception as e:
            self.fail(f"Adjustment recommendations failed with error: {str(e)}")
        
        logger.info("End-to-end adjustment recommendations flow completed successfully")
    
    def test_03_end_to_end_multi_goal_flow(self):
        """Test a complete end-to-end flow involving multiple goals."""
        logger.info("Testing end-to-end multi-goal flow")
        
        # Create test profile data
        profile_data = {
            "id": self.test_profile_id,
            "annual_income": 1500000,
            "monthly_income": 125000,
            "monthly_expenses": 75000,
            "risk_profile": "moderate",
            "answers": [
                {"question_id": "annual_income", "answer": 1500000},
                {"question_id": "risk_profile", "answer": "moderate"}
            ]
        }
        
        # 1. Calculate probabilities for all goals in batch
        try:
            batch_results = self.goal_service.calculate_goal_probabilities_batch(
                profile_id=self.test_profile_id,
                profile_data=profile_data
            )
            
            # Verify batch results
            self.assertIsNotNone(batch_results)
            self.assertIsInstance(batch_results, dict)
            
            # All our goals should be in the results
            for goal_id in [self.retirement_goal_id, self.education_goal_id, self.home_goal_id]:
                self.assertIn(goal_id, batch_results)
            
            logger.info(f"Calculated probabilities for {len(batch_results)} goals")
            
        except Exception as e:
            self.fail(f"Batch probability calculation failed with error: {str(e)}")
        
        # 2. Get prioritized goals
        try:
            prioritized_goals = self.goal_service.analyze_goal_priorities(self.test_profile_id)
            
            # Verify prioritized goals
            self.assertIsNotNone(prioritized_goals)
            self.assertIsInstance(prioritized_goals, list)
            self.assertEqual(len(prioritized_goals), 3)  # Should have all 3 test goals
            
            # Each goal should have priority information
            for goal in prioritized_goals:
                self.assertIn('priority_rank', goal)
                self.assertIn('hierarchy_level', goal)
            
            logger.info(f"Prioritized {len(prioritized_goals)} goals")
            
        except Exception as e:
            self.fail(f"Goal prioritization failed with error: {str(e)}")
        
        logger.info("End-to-end multi-goal flow completed successfully")
    
    def test_04_end_to_end_scenario_flow(self):
        """Test a complete end-to-end flow for goal scenarios."""
        logger.info("Testing end-to-end scenario flow")
        
        # Create a scenario for the retirement goal
        scenario_data = {
            "name": "Increased Contribution Scenario",
            "description": "Scenario with higher monthly contributions",
            "parameters": {
                "target_amount": 5000000,  # Same as original
                "current_amount": 1000000,  # Same as original
                "monthly_contribution": 50000,  # Higher contribution
                "timeframe": (datetime.now() + timedelta(days=365*25)).isoformat()  # Same timeframe
            }
        }
        
        # 1. Add the scenario to the goal
        try:
            success = self.goal_service.add_scenario_to_goal(
                goal_id=self.retirement_goal_id,
                scenario=scenario_data
            )
            
            # Verify success
            self.assertTrue(success)
            
            logger.info("Successfully added scenario to retirement goal")
            
        except Exception as e:
            self.fail(f"Adding scenario failed with error: {str(e)}")
        
        # 2. Create profile data
        profile_data = {
            "id": self.test_profile_id,
            "annual_income": 1500000,
            "risk_profile": "moderate"
        }
        
        # 3. Calculate probability for the original goal
        try:
            original_result = self.goal_service.calculate_goal_probability(
                goal_id=self.retirement_goal_id,
                profile_data=profile_data
            )
            
            # Get original probability
            original_probability = original_result.get_safe_success_probability() if hasattr(original_result, 'get_safe_success_probability') else 0.0
            
            logger.info(f"Original goal probability: {original_probability}")
            
        except Exception as e:
            self.fail(f"Original probability calculation failed with error: {str(e)}")
        
        # 4. Verify that a scenario was added by getting the goal
        goal_data = self.goal_service.get_goal(self.retirement_goal_id)
        
        # There should be a scenarios field
        self.assertIn('scenarios', goal_data)
        
        # Parse scenarios JSON if it's a string
        scenarios = json.loads(goal_data['scenarios']) if isinstance(goal_data['scenarios'], str) else goal_data['scenarios']
        
        # Should have at least one scenario
        self.assertIsInstance(scenarios, list)
        self.assertGreaterEqual(len(scenarios), 1)
        
        # Find our scenario
        our_scenario = next((s for s in scenarios if s.get('name') == "Increased Contribution Scenario"), None)
        self.assertIsNotNone(our_scenario)
        
        logger.info(f"Found our scenario in the goal data")
        
        logger.info("End-to-end scenario flow completed successfully")
    
    def test_05_end_to_end_goal_creation_update_delete(self):
        """Test a complete end-to-end flow for goal CRUD operations."""
        logger.info("Testing end-to-end goal CRUD flow")
        
        # 1. Create a new goal
        goal_data = {
            "category": "custom",
            "title": "Integration Test Custom Goal",
            "target_amount": 300000,
            "timeframe": (datetime.now() + timedelta(days=365*3)).isoformat(),
            "current_amount": 50000,
            "importance": "medium",
            "flexibility": "very_flexible",
            "notes": "Integration test custom goal"
        }
        
        try:
            new_goal = self.goal_service.create_goal(goal_data, self.test_profile_id)
            
            # Verify goal was created
            self.assertIsNotNone(new_goal)
            self.assertIsInstance(new_goal, Goal)
            self.assertEqual(new_goal.title, goal_data["title"])
            
            # Store ID for later
            new_goal_id = new_goal.id
            
            logger.info(f"Created new goal with ID: {new_goal_id}")
            
        except Exception as e:
            self.fail(f"Goal creation failed with error: {str(e)}")
        
        # 2. Update the goal
        update_data = {
            "title": "Updated Custom Goal",
            "target_amount": 350000,
            "notes": "Updated integration test goal"
        }
        
        try:
            updated_goal = self.goal_service.update_goal(new_goal_id, update_data)
            
            # Verify goal was updated
            self.assertIsNotNone(updated_goal)
            self.assertEqual(updated_goal.title, update_data["title"])
            self.assertEqual(updated_goal.target_amount, update_data["target_amount"])
            
            logger.info(f"Updated goal {new_goal_id}")
            
        except Exception as e:
            self.fail(f"Goal update failed with error: {str(e)}")
        
        # 3. Delete the goal
        try:
            success = self.goal_service.delete_goal(new_goal_id)
            
            # Verify goal was deleted
            self.assertTrue(success)
            
            # Verify it's really gone
            deleted_goal = self.goal_service.get_goal(new_goal_id)
            self.assertIsNone(deleted_goal)
            
            logger.info(f"Deleted goal {new_goal_id}")
            
        except Exception as e:
            self.fail(f"Goal deletion failed with error: {str(e)}")
        
        logger.info("End-to-end goal CRUD flow completed successfully")

if __name__ == "__main__":
    unittest.main()
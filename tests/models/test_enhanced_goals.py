#!/usr/bin/env python3
"""
Test script for the enhanced Goal model with new fields and functionality.

This script:
1. Creates test goals with different priority levels
2. Tests the priority scoring algorithm
3. Verifies the goals_by_priority sorting
4. Tests calculating current progress
5. Tests the new fields and their serialization

Usage:
    python test_enhanced_goals.py
"""

import os
import sys
import logging
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from models.goal_models import Goal, GoalManager
from models.database_profile_manager import DatabaseProfileManager

def create_test_profile():
    """Create a test profile for goal testing"""
    db_path = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db"
    profile_manager = DatabaseProfileManager(db_path=db_path)
    
    # Create a test profile with random name and email
    test_profile_name = f"Test User {uuid.uuid4().hex[:6]}"
    test_profile_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    
    logger.info(f"Creating test profile: {test_profile_name} <{test_profile_email}>")
    profile = profile_manager.create_profile(test_profile_name, test_profile_email)
    
    return profile["id"]

def test_goal_priority_scoring():
    """Test the priority scoring algorithm with different goal types"""
    goal_mgr = GoalManager()
    profile_id = create_test_profile()
    
    try:
        # Create goals with different priority characteristics
        
        # 1. High priority: High importance, near-term timeframe, fixed flexibility
        high_priority_goal = Goal(
            user_profile_id=profile_id,
            category="emergency_fund",
            title="Emergency Fund",
            target_amount=100000,
            timeframe=(datetime.now() + timedelta(days=30)).isoformat(),
            current_amount=20000,
            importance="high",
            flexibility="fixed",
            notes="Build emergency fund ASAP"
        )
        
        # 2. Medium priority: Medium importance, mid-term timeframe, somewhat flexible
        medium_priority_goal = Goal(
            user_profile_id=profile_id,
            category="home_purchase",
            title="Home Down Payment",
            target_amount=1000000,
            timeframe=(datetime.now() + timedelta(days=365)).isoformat(),
            current_amount=200000,
            importance="medium",
            flexibility="somewhat_flexible",
            notes="Save for home down payment"
        )
        
        # 3. Low priority: Low importance, long-term timeframe, very flexible
        low_priority_goal = Goal(
            user_profile_id=profile_id,
            category="travel",
            title="Dream Vacation",
            target_amount=200000,
            timeframe=(datetime.now() + timedelta(days=1825)).isoformat(),
            current_amount=20000,
            importance="low",
            flexibility="very_flexible",
            notes="Save for dream vacation"
        )
        
        # Force calculation of priority scores
        high_priority_goal.calculate_priority_score()
        medium_priority_goal.calculate_priority_score()
        low_priority_goal.calculate_priority_score()
        
        # Log priority scores
        logger.info("Priority Scores:")
        logger.info(f"  High Priority Goal ({high_priority_goal.title}): {high_priority_goal.priority_score}")
        logger.info(f"  Medium Priority Goal ({medium_priority_goal.title}): {medium_priority_goal.priority_score}")
        logger.info(f"  Low Priority Goal ({low_priority_goal.title}): {low_priority_goal.priority_score}")
        
        # Verify that high priority > medium priority > low priority
        assert high_priority_goal.priority_score > medium_priority_goal.priority_score, "High priority goal should have higher score than medium priority goal"
        assert medium_priority_goal.priority_score > low_priority_goal.priority_score, "Medium priority goal should have higher score than low priority goal"
        
        # Add more test fields
        high_priority_goal.additional_funding_sources = "Year-end bonus"
        high_priority_goal.goal_success_probability = 90.0
        high_priority_goal.adjustments_required = False
        high_priority_goal.funding_strategy = '{"strategy": "monthly_contribution", "amount": 10000}'
        
        # Save goals to database
        saved_goals = []
        for goal in [high_priority_goal, medium_priority_goal, low_priority_goal]:
            saved_goal = goal_mgr.create_goal(goal)
            if saved_goal:
                saved_goals.append(saved_goal)
                logger.info(f"Saved goal: {saved_goal.id} - {saved_goal.title}")
            else:
                logger.error(f"Failed to save goal: {goal.title}")
        
        # Test retrieving goals by priority
        logger.info("\nRetrieving goals by priority:")
        priority_goals = goal_mgr.get_goals_by_priority(profile_id)
        
        for i, goal in enumerate(priority_goals):
            logger.info(f"  {i+1}. {goal.title} (Score: {goal.priority_score}, Importance: {goal.importance})")
        
        # Verify the order of priority goals
        if len(priority_goals) >= 3:
            assert priority_goals[0].id == high_priority_goal.id, "High priority goal should be first"
            assert priority_goals[1].id == medium_priority_goal.id, "Medium priority goal should be second"
            assert priority_goals[2].id == low_priority_goal.id, "Low priority goal should be third"
            
            logger.info("Priority ordering verified correctly")
        
        # Test current_progress calculation
        for goal in priority_goals:
            expected_progress = min(100.0, (goal.current_amount / goal.target_amount) * 100.0)
            logger.info(f"Goal {goal.title}: Current progress {goal.current_progress:.1f}% (Expected: {expected_progress:.1f}%)")
            assert abs(goal.current_progress - expected_progress) < 0.1, "Current progress calculation is incorrect"
        
        # Test to_dict serialization with new fields
        logger.info("\nTesting to_dict serialization with new fields:")
        goal_dict = high_priority_goal.to_dict()
        
        for field in ['current_progress', 'priority_score', 'additional_funding_sources',
                     'goal_success_probability', 'adjustments_required', 'funding_strategy']:
            logger.info(f"  {field}: {goal_dict.get(field)}")
            assert field in goal_dict, f"Field {field} missing from goal dict"
        
        logger.info("All tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        # Clean up - delete test goals and profile
        try:
            # Delete all test goals
            for goal in goal_mgr.get_profile_goals(profile_id):
                goal_mgr.delete_goal(goal.id)
                
            # Delete test profile
            db_path = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db"
            profile_manager = DatabaseProfileManager(db_path=db_path)
            profile_manager.delete_profile(profile_id)
            logger.info(f"Cleaned up test profile and goals")
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting enhanced goal model test")
    success = test_goal_priority_scoring()
    if success:
        logger.info("Enhanced goal model test completed successfully")
        sys.exit(0)
    else:
        logger.error("Enhanced goal model test failed")
        sys.exit(1)
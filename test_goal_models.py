#!/usr/bin/env python3
"""
Test script for validating Goal and GoalCategory models implementation.
This script tests basic CRUD operations and verifies foreign key relationships.
"""

import os
import sys
import logging
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import models
from models.database_profile_manager import DatabaseProfileManager
from models.goal_models import GoalManager, Goal, GoalCategory

def test_goals_implementation():
    """Test all aspects of the goals implementation"""
    logger.info("Starting goal models validation test")

    # Initialize managers
    db_path = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db"
    profile_manager = DatabaseProfileManager(db_path=db_path)
    goal_manager = GoalManager(db_path=db_path)

    # Step 1: Create a test profile
    test_profile_name = f"Test User {uuid.uuid4().hex[:6]}"
    test_profile_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    
    logger.info(f"Creating test profile: {test_profile_name} <{test_profile_email}>")
    profile = profile_manager.create_profile(test_profile_name, test_profile_email)
    profile_id = profile["id"]
    
    logger.info(f"Created test profile with ID: {profile_id}")

    try:
        # Step 2: Verify goal categories exist
        logger.info("Retrieving goal categories...")
        categories = goal_manager.get_all_categories()
        
        if not categories:
            logger.error("No goal categories found. There might be an issue with category initialization.")
            return False
        
        logger.info(f"Found {len(categories)} goal categories")
        for category in categories[:3]:  # Show just a few for brevity
            logger.info(f"  - {category.name}: {category.description} (foundation: {category.is_foundation})")

        # Step 3: Create test goals
        logger.info("Creating test goals...")
        
        # Emergency fund goal
        emergency_fund_category = goal_manager.get_category_by_name("emergency_fund")
        if not emergency_fund_category:
            logger.error("Emergency fund category not found")
            return False
            
        emergency_fund_goal = Goal(
            user_profile_id=profile_id,
            category="emergency_fund",
            title="My Emergency Fund",
            target_amount=50000,
            timeframe="2024-12-31",
            current_amount=10000,
            importance="high",
            flexibility="somewhat_flexible",
            notes="Build up 6 months of expenses"
        )
        created_emergency_goal = goal_manager.create_goal(emergency_fund_goal)
        logger.info(f"Created emergency fund goal with ID: {created_emergency_goal.id}")
        
        # Retirement goal
        retirement_goal = Goal(
            user_profile_id=profile_id,
            category="traditional_retirement",
            title="Retirement Savings",
            target_amount=5000000,
            timeframe="2045-01-01",
            current_amount=500000,
            importance="high",
            flexibility="very_flexible",
            notes="Long-term retirement nest egg"
        )
        created_retirement_goal = goal_manager.create_goal(retirement_goal)
        logger.info(f"Created retirement goal with ID: {created_retirement_goal.id}")
        
        # Travel goal
        travel_goal = Goal(
            user_profile_id=profile_id,
            category="travel",
            title="European Vacation",
            target_amount=200000,
            timeframe="2025-06-01",
            current_amount=50000,
            importance="medium",
            flexibility="fixed",
            notes="Trip to France, Italy, and Spain"
        )
        created_travel_goal = goal_manager.create_goal(travel_goal)
        logger.info(f"Created travel goal with ID: {created_travel_goal.id}")
        
        # Step 4: Retrieve goals by profile
        logger.info(f"Retrieving goals for profile: {profile_id}")
        profile_goals = goal_manager.get_profile_goals(profile_id)
        
        if len(profile_goals) != 3:
            logger.error(f"Expected 3 goals, but found {len(profile_goals)}")
            return False
            
        logger.info(f"Successfully retrieved {len(profile_goals)} goals:")
        for goal in profile_goals:
            logger.info(f"  - {goal.title} ({goal.category}): ₹{goal.target_amount:,.2f}")
        
        # Step 5: Update a goal
        logger.info(f"Updating travel goal: {created_travel_goal.id}")
        original_amount = created_travel_goal.target_amount
        created_travel_goal.target_amount = 250000
        created_travel_goal.notes = "Updated: Trip to France, Italy, Spain and Germany"
        
        updated_goal = goal_manager.update_goal(created_travel_goal)
        if not updated_goal:
            logger.error("Failed to update goal")
            return False
            
        # Verify update worked
        retrieved_goal = goal_manager.get_goal(created_travel_goal.id)
        if retrieved_goal.target_amount != 250000:
            logger.error(f"Goal update failed. Expected 250000, but found {retrieved_goal.target_amount}")
            return False
            
        logger.info(f"Successfully updated goal. Target amount changed from {original_amount:,.2f} to {retrieved_goal.target_amount:,.2f}")
        
        # Step 6: Delete a goal
        logger.info(f"Deleting travel goal: {created_travel_goal.id}")
        if not goal_manager.delete_goal(created_travel_goal.id):
            logger.error("Failed to delete goal")
            return False
            
        # Verify deletion worked
        remaining_goals = goal_manager.get_profile_goals(profile_id)
        if len(remaining_goals) != 2:
            logger.error(f"Expected 2 goals after deletion, but found {len(remaining_goals)}")
            return False
            
        # Verify deleted goal doesn't exist
        deleted_goal = goal_manager.get_goal(created_travel_goal.id)
        if deleted_goal:
            logger.error(f"Goal still exists after deletion: {deleted_goal.id}")
            return False
            
        logger.info("Successfully deleted goal")
        
        # Step 7: Test foreign key constraints by deleting the profile
        logger.info(f"Testing cascade delete by removing profile: {profile_id}")
        if not profile_manager.delete_profile(profile_id):
            logger.error("Failed to delete profile")
            return False
            
        # Verify cascade delete worked for goals
        orphaned_goals = goal_manager.get_profile_goals(profile_id)
        if orphaned_goals:
            logger.error(f"Found {len(orphaned_goals)} goals after profile deletion, expected 0")
            return False
            
        logger.info("Foreign key constraint test passed: all goals deleted with profile")
        
        logger.info("All tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return False
    finally:
        # Cleanup in case test failed before profile deletion
        try:
            profile_manager.delete_profile(profile_id)
        except:
            pass

if __name__ == "__main__":
    success = test_goals_implementation()
    if not success:
        logger.error("Goal models validation test failed")
        sys.exit(1)
    logger.info("Goal models validation test completed successfully")
    sys.exit(0)
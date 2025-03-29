#!/usr/bin/env python3
"""
Test script for the goal service compatibility layer
This script tests the core functionality of the GoalService class
to verify that it correctly handles both simple and enhanced parameters.
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta
from services.goal_service import GoalService
from models.goal_models import Goal, GoalCategory, GoalManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to database
DB_PATH = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db"

# Global test profile ID to be set in main()
test_profile_id = None

def create_test_profile():
    """Create a test user profile in the database"""
    try:
        # Generate a UUID for the profile
        profile_id = str(uuid.uuid4())
        
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the user_profiles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
        if not cursor.fetchone():
            logger.info("Creating user_profiles table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
        
        # Insert a test profile
        current_time = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO user_profiles (id, name, email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (profile_id, "Test User", "test@example.com", current_time, current_time))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created test profile with ID: {profile_id}")
        return profile_id
    
    except Exception as e:
        logger.error(f"Error creating test profile: {str(e)}")
        return None

def test_goal_creation_compatibility():
    """Test goal creation with both simple and enhanced parameters"""
    logger.info("Testing goal creation compatibility...")
    
    # Initialize the service
    service = GoalService()
    
    # Test with legacy parameters
    legacy_goal_data = {
        "category": "emergency_fund",
        "title": "Emergency Fund",
        "target_value": 500000,  # Legacy field
        "time_horizon": 2,       # Legacy field (years)
        "priority": "high",      # Legacy field
        "description": "Fund for unexpected expenses"  # Legacy field
    }
    
    # Create the goal
    profile_id = test_profile_id
    legacy_goal = service.create_goal(legacy_goal_data, profile_id)
    
    if legacy_goal:
        logger.info("✅ Legacy goal created successfully")
        logger.info(f"  ID: {legacy_goal.id}")
        logger.info(f"  Target amount: {legacy_goal.target_amount}")
        logger.info(f"  Timeframe: {legacy_goal.timeframe}")
        logger.info(f"  Importance: {legacy_goal.importance}")
        logger.info(f"  Notes: {legacy_goal.notes}")
    else:
        logger.error("❌ Failed to create legacy goal")
    
    # Test with enhanced parameters
    enhanced_goal_data = {
        "category": "early_retirement",
        "title": "Early Retirement",
        "target_amount": 10000000,
        "timeframe": (datetime.now() + timedelta(days=365*15)).isoformat(),
        "current_amount": 2000000,
        "importance": "high",
        "flexibility": "somewhat_flexible",
        "notes": "Retire by 45",
        "current_progress": 20.0,
        "additional_funding_sources": "Rental income",
        "funding_strategy": json.dumps({"retirement_age": 45, "withdrawal_rate": 0.035})
    }
    
    # Create the goal
    enhanced_goal = service.create_goal(enhanced_goal_data, profile_id)
    
    if enhanced_goal:
        logger.info("✅ Enhanced goal created successfully")
        logger.info(f"  ID: {enhanced_goal.id}")
        logger.info(f"  Target amount: {enhanced_goal.target_amount}")
        logger.info(f"  Current progress: {enhanced_goal.current_progress}")
        logger.info(f"  Additional funding sources: {enhanced_goal.additional_funding_sources}")
        logger.info(f"  Funding strategy: {enhanced_goal.funding_strategy}")
    else:
        logger.error("❌ Failed to create enhanced goal")
    
    return legacy_goal, enhanced_goal

def test_goal_retrieval_compatibility(legacy_goal_id, enhanced_goal_id):
    """Test goal retrieval with both legacy and modern formatting"""
    logger.info("Testing goal retrieval compatibility...")
    
    # Initialize the service
    service = GoalService()
    
    # Retrieve legacy goal in legacy format
    legacy_goal_legacy_format = service.get_goal(legacy_goal_id, legacy_mode=True)
    
    if legacy_goal_legacy_format:
        logger.info("✅ Retrieved legacy goal in legacy format")
        # Verify legacy fields are present
        legacy_fields = ["priority", "time_horizon", "target_value", "description"]
        missing_fields = [f for f in legacy_fields if f not in legacy_goal_legacy_format]
        if missing_fields:
            logger.warning(f"⚠️ Missing legacy fields: {missing_fields}")
        else:
            logger.info("  All legacy fields present")
    else:
        logger.error("❌ Failed to retrieve legacy goal in legacy format")
    
    # Retrieve enhanced goal in modern format
    enhanced_goal_modern_format = service.get_goal(enhanced_goal_id, legacy_mode=False)
    
    if enhanced_goal_modern_format:
        logger.info("✅ Retrieved enhanced goal in modern format")
        # Verify enhanced fields are present
        enhanced_fields = ["current_progress", "additional_funding_sources", 
                         "goal_success_probability", "funding_strategy"]
        missing_fields = [f for f in enhanced_fields if f not in enhanced_goal_modern_format]
        if missing_fields:
            logger.warning(f"⚠️ Missing enhanced fields: {missing_fields}")
        else:
            logger.info("  All enhanced fields present")
    else:
        logger.error("❌ Failed to retrieve enhanced goal in modern format")
    
    # Retrieve enhanced goal in legacy format (for compatibility)
    enhanced_goal_legacy_format = service.get_goal(enhanced_goal_id, legacy_mode=True)
    
    if enhanced_goal_legacy_format:
        logger.info("✅ Retrieved enhanced goal in legacy format")
        # Verify legacy compatibility fields
        if "priority" in enhanced_goal_legacy_format:
            logger.info(f"  Priority (from importance): {enhanced_goal_legacy_format['priority']}")
        else:
            logger.warning("⚠️ Missing legacy compatibility field: priority")
    else:
        logger.error("❌ Failed to retrieve enhanced goal in legacy format")

def test_category_specific_handling():
    """Test category-specific handling for different goal types"""
    logger.info("Testing category-specific goal handling...")
    
    # Initialize the service
    service = GoalService()
    profile_id = test_profile_id
    
    # Test different goal categories
    categories = [
        "emergency_fund",      # Security
        "home_purchase",       # Essential 
        "traditional_retirement",  # Retirement
        "travel",              # Lifestyle
        "charitable_giving"    # Legacy
    ]
    
    for category in categories:
        # Create minimal goal data
        goal_data = {
            "category": category,
            "title": f"Test {category.replace('_', ' ').title()}",
        }
        
        # Create the goal with category-specific handling
        goal = service.create_goal(goal_data, profile_id)
        
        if goal:
            logger.info(f"✅ Created {category} goal")
            # Check for funding strategy with category-specific data
            if goal.funding_strategy:
                try:
                    strategy = json.loads(goal.funding_strategy)
                    logger.info(f"  Funding strategy: {strategy}")
                except:
                    logger.warning(f"⚠️ Invalid funding strategy format for {category}")
            else:
                logger.warning(f"⚠️ No funding strategy for {category}")
        else:
            logger.error(f"❌ Failed to create {category} goal")

def test_calculation_services():
    """Test calculation services for goals"""
    logger.info("Testing goal calculation services...")
    
    # Initialize the service
    service = GoalService()
    profile_id = test_profile_id
    
    # Create a test profile with financial information
    profile_data = {
        "answers": [
            {"question_id": "monthly_income", "answer": 100000},
            {"question_id": "monthly_expenses", "answer": 60000},
            {"question_id": "risk_profile", "answer": "moderate"}
        ],
        "monthly_income": 100000,  # For direct access in calculators
        "monthly_expenses": 60000,  # For direct access in calculators
        "risk_profile": "moderate"  # For direct access in calculators
    }
    
    # Get all goals for the profile
    goals = service.get_profile_goals(profile_id)
    
    if goals:
        # Calculate amounts and savings rates
        calculated_goals = service.calculate_goal_amounts(profile_id, profile_data)
        
        if calculated_goals:
            logger.info("✅ Calculated goal amounts")
            logger.info(f"  Calculated {len(calculated_goals)} goals")
            
            # Check for category-specific calculations
            for goal in calculated_goals:
                category = goal.get("category")
                logger.info(f"  {category}: Target: {goal.get('target_amount')}, "
                           f"Monthly savings: {goal.get('required_monthly_savings')}")
                
                # Check for special fields
                if "recommended_allocation" in goal:
                    logger.info(f"    Recommended allocation: {goal['recommended_allocation']}")
                
                if "projection_5yr" in goal:
                    logger.info(f"    5-year projection available")
        else:
            logger.warning("⚠️ No calculated goals returned")
    else:
        logger.warning("⚠️ No goals found for testing calculations")
    
    # Test priority analysis
    prioritized_goals = service.analyze_goal_priorities(profile_id)
    
    if prioritized_goals:
        logger.info("✅ Analyzed goal priorities")
        logger.info(f"  Prioritized {len(prioritized_goals)} goals")
        
        # Show prioritization
        for goal in prioritized_goals:
            logger.info(f"  Rank {goal.get('priority_rank')}: {goal.get('title')} "
                       f"(Score: {goal.get('priority_score')})")
    else:
        logger.warning("⚠️ No prioritized goals returned")

def main():
    """Run all tests"""
    logger.info("Starting goal service compatibility tests")
    
    try:
        # First ensure we have goal categories initialized
        goal_manager = GoalManager()
        goal_manager.initialize_predefined_categories()
        
        # Create a test profile to avoid foreign key constraints
        profile_id = create_test_profile()
        if not profile_id:
            logger.error("Failed to create test profile. Tests cannot continue.")
            return
            
        # Update test functions to use the real profile ID
        global test_profile_id
        test_profile_id = profile_id
        
        # Run compatibility tests
        legacy_goal, enhanced_goal = test_goal_creation_compatibility()
        
        if legacy_goal and enhanced_goal:
            test_goal_retrieval_compatibility(legacy_goal.id, enhanced_goal.id)
        
        # Test category-specific handling
        test_category_specific_handling()
        
        # Test calculation services
        test_calculation_services()
        
        logger.info("All tests completed")
    
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
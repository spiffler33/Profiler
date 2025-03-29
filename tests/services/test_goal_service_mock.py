#!/usr/bin/env python3
"""
Mock test script for the goal service compatibility layer

This script tests the functionality of the GoalService class using mocks
rather than actual database operations to verify compatibility with
both simple and enhanced goal parameters.
"""

import json
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from services.goal_service import GoalService
from models.goal_models import Goal, GoalCategory

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_goal_creation_compatibility():
    """Test goal creation with both simple and enhanced parameters"""
    logger.info("Testing goal creation compatibility...")
    
    # Create a mock Goal instance for the goal_manager to return
    mock_legacy_goal = MagicMock(spec=Goal)
    mock_legacy_goal.id = "test-legacy-goal-123"
    mock_legacy_goal.target_amount = 500000
    mock_legacy_goal.timeframe = (datetime.now() + timedelta(days=365*2)).isoformat()
    mock_legacy_goal.importance = "high"
    mock_legacy_goal.notes = "Fund for unexpected expenses"
    
    mock_enhanced_goal = MagicMock(spec=Goal)
    mock_enhanced_goal.id = "test-enhanced-goal-123"
    mock_enhanced_goal.target_amount = 10000000
    mock_enhanced_goal.timeframe = (datetime.now() + timedelta(days=365*15)).isoformat()
    mock_enhanced_goal.current_amount = 2000000
    mock_enhanced_goal.importance = "high"
    mock_enhanced_goal.flexibility = "somewhat_flexible"
    mock_enhanced_goal.notes = "Retire by 45"
    mock_enhanced_goal.current_progress = 20.0
    mock_enhanced_goal.additional_funding_sources = "Rental income"
    mock_enhanced_goal.funding_strategy = json.dumps({"retirement_age": 45, "withdrawal_rate": 0.035})
    
    # Create mock for GoalManager
    mock_goal_manager = MagicMock()
    mock_goal_manager.create_goal.side_effect = [mock_legacy_goal, mock_enhanced_goal]
    
    # Patch the GoalManager in GoalService
    with patch('services.goal_service.GoalManager', return_value=mock_goal_manager):
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
        legacy_goal = service.create_goal(legacy_goal_data, "test-profile-123")
        
        if legacy_goal:
            logger.info("✅ Legacy goal created successfully")
            logger.info(f"  ID: {legacy_goal.id}")
            
            # Check if legacy fields were properly mapped
            first_call_args = mock_goal_manager.create_goal.call_args_list[0][0][0]
            logger.info("Checking if legacy fields were properly mapped:")
            
            if hasattr(first_call_args, 'target_amount') and first_call_args.target_amount == 500000:
                logger.info("  ✅ target_value -> target_amount: OK")
            else:
                logger.warning("  ❌ target_value -> target_amount: Failed")
                
            if hasattr(first_call_args, 'importance') and first_call_args.importance == "high":
                logger.info("  ✅ priority -> importance: OK")
            else:
                logger.warning("  ❌ priority -> importance: Failed")
                
            if hasattr(first_call_args, 'notes') and first_call_args.notes == "Fund for unexpected expenses":
                logger.info("  ✅ description -> notes: OK")
            else:
                logger.warning("  ❌ description -> notes: Failed")
                
            # Check timeframe conversion 
            if hasattr(first_call_args, 'timeframe') and first_call_args.timeframe:
                logger.info("  ✅ time_horizon -> timeframe: OK")
            else:
                logger.warning("  ❌ time_horizon -> timeframe: Failed")
                
        else:
            logger.error("❌ Legacy goal creation failed")
        
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
        enhanced_goal = service.create_goal(enhanced_goal_data, "test-profile-123")
        
        if enhanced_goal:
            logger.info("✅ Enhanced goal created successfully")
            logger.info(f"  ID: {enhanced_goal.id}")
            
            # Check if enhanced fields were preserved
            second_call_args = mock_goal_manager.create_goal.call_args_list[1][0][0]
            logger.info("Checking if enhanced fields were preserved:")
            
            if hasattr(second_call_args, 'current_progress') and second_call_args.current_progress == 20.0:
                logger.info("  ✅ current_progress: OK")
            else:
                logger.warning("  ❌ current_progress: Failed")
                
            if hasattr(second_call_args, 'additional_funding_sources') and second_call_args.additional_funding_sources == "Rental income":
                logger.info("  ✅ additional_funding_sources: OK")
            else:
                logger.warning("  ❌ additional_funding_sources: Failed")
                
            if hasattr(second_call_args, 'funding_strategy') and "retirement_age" in second_call_args.funding_strategy:
                logger.info("  ✅ funding_strategy: OK")
            else:
                logger.warning("  ❌ funding_strategy: Failed")
        else:
            logger.error("❌ Enhanced goal creation failed")
    
    return mock_legacy_goal, mock_enhanced_goal

def test_goal_retrieval_compatibility():
    """Test goal retrieval with both legacy and modern formatting"""
    logger.info("Testing goal retrieval compatibility...")
    
    # Create a mock Goal instance for the goal_manager to return
    mock_goal = MagicMock(spec=Goal)
    mock_goal.id = "test-goal-123"
    mock_goal.user_profile_id = "test-profile-123"
    mock_goal.category = "early_retirement"
    mock_goal.title = "Early Retirement"
    mock_goal.target_amount = 10000000
    mock_goal.timeframe = (datetime.now() + timedelta(days=365*15)).isoformat()
    mock_goal.current_amount = 2000000
    mock_goal.importance = "high"
    mock_goal.flexibility = "somewhat_flexible"
    mock_goal.notes = "Retire by 45"
    mock_goal.created_at = datetime.now().isoformat()
    mock_goal.updated_at = datetime.now().isoformat()
    mock_goal.current_progress = 20.0
    mock_goal.additional_funding_sources = "Rental income"
    mock_goal.goal_success_probability = 75.0
    mock_goal.funding_strategy = json.dumps({"retirement_age": 45, "withdrawal_rate": 0.035})
    
    # Set up the legacy_mode behavior on to_dict
    mock_goal.to_dict = MagicMock()
    mock_goal.to_dict.side_effect = lambda legacy_mode=False: (
        # Legacy mode dictionary
        {
            "id": mock_goal.id,
            "profile_id": mock_goal.user_profile_id,  # Legacy field
            "category": mock_goal.category,
            "title": mock_goal.title,
            "target_value": mock_goal.target_amount,  # Legacy field
            "time_horizon": 15.0,  # Legacy field
            "current_value": mock_goal.current_amount,  # Legacy field
            "priority": mock_goal.importance,  # Legacy field
            "description": mock_goal.notes,  # Legacy field
            "created_at": mock_goal.created_at,
            "updated_at": mock_goal.updated_at
        } if legacy_mode else
        # Modern mode dictionary
        {
            "id": mock_goal.id,
            "user_profile_id": mock_goal.user_profile_id,
            "category": mock_goal.category,
            "title": mock_goal.title,
            "target_amount": mock_goal.target_amount,
            "timeframe": mock_goal.timeframe,
            "current_amount": mock_goal.current_amount,
            "importance": mock_goal.importance,
            "flexibility": mock_goal.flexibility,
            "notes": mock_goal.notes,
            "created_at": mock_goal.created_at,
            "updated_at": mock_goal.updated_at,
            "current_progress": mock_goal.current_progress,
            "additional_funding_sources": mock_goal.additional_funding_sources,
            "goal_success_probability": mock_goal.goal_success_probability,
            "funding_strategy": mock_goal.funding_strategy
        }
    )
    
    # Create mock for GoalManager
    mock_goal_manager = MagicMock()
    mock_goal_manager.get_goal.return_value = mock_goal
    
    # Patch the GoalManager in GoalService
    with patch('services.goal_service.GoalManager', return_value=mock_goal_manager):
        # Initialize the service
        service = GoalService()
        
        # Retrieve goal in modern format
        goal_data_modern = service.get_goal("test-goal-123", legacy_mode=False)
        
        if goal_data_modern:
            logger.info("✅ Retrieved goal in modern format")
            if "current_progress" in goal_data_modern and "additional_funding_sources" in goal_data_modern:
                logger.info("  ✅ Enhanced fields present in modern format")
            else:
                logger.warning("  ❌ Enhanced fields missing in modern format")
        else:
            logger.error("❌ Failed to retrieve goal in modern format")
        
        # Retrieve goal in legacy format
        goal_data_legacy = service.get_goal("test-goal-123", legacy_mode=True)
        
        if goal_data_legacy:
            logger.info("✅ Retrieved goal in legacy format")
            legacy_fields = ["profile_id", "target_value", "time_horizon", "current_value", "priority", "description"]
            missing_fields = [f for f in legacy_fields if f not in goal_data_legacy]
            
            if not missing_fields:
                logger.info("  ✅ All legacy fields present")
            else:
                logger.warning(f"  ❌ Missing legacy fields: {missing_fields}")
        else:
            logger.error("❌ Failed to retrieve goal in legacy format")

def test_category_specific_handling():
    """Test category-specific handling for different goal types"""
    logger.info("Testing category-specific goal handling...")
    
    # Create mock goals for each category type
    mock_goals = {}
    
    categories = [
        "emergency_fund",      # Security
        "home_purchase",       # Essential 
        "traditional_retirement",  # Retirement
        "travel",              # Lifestyle
        "charitable_giving"    # Legacy
    ]
    
    # Set up side effect for create_goal to return different mock goals for each category
    def create_goal_side_effect(goal):
        category = goal.category
        mock_goal = MagicMock(spec=Goal)
        mock_goal.id = f"test-{category}-123"
        mock_goal.category = category
        mock_goal.title = f"Test {category.replace('_', ' ').title()}"
        mock_goal.importance = goal.importance
        mock_goal.flexibility = goal.flexibility
        mock_goal.funding_strategy = goal.funding_strategy
        mock_goals[category] = mock_goal
        return mock_goal
    
    # Create mock for GoalManager
    mock_goal_manager = MagicMock()
    mock_goal_manager.create_goal.side_effect = create_goal_side_effect
    
    # Patch the GoalManager in GoalService
    with patch('services.goal_service.GoalManager', return_value=mock_goal_manager):
        # Initialize the service
        service = GoalService()
        
        # Test with minimal data for each category
        for category in categories:
            # Create minimal goal data
            goal_data = {
                "category": category,
                "title": f"Test {category.replace('_', ' ').title()}",
            }
            
            # Create the goal
            goal = service.create_goal(goal_data, "test-profile-123")
            
            if goal:
                logger.info(f"✅ Created {category} goal")
                
                # Check category-specific fields based on category type
                call_args = None
                for call in mock_goal_manager.create_goal.call_args_list:
                    if call[0][0].category == category:
                        call_args = call[0][0]
                        break
                
                if call_args:
                    # Check importance and flexibility based on category
                    if category in ["emergency_fund", "home_purchase", "traditional_retirement"]:
                        if call_args.importance == "high":
                            logger.info(f"  ✅ {category} has high importance as expected")
                        else:
                            logger.warning(f"  ❌ {category} should have high importance, but has {call_args.importance}")
                    
                    if category == "emergency_fund" and call_args.flexibility == "fixed":
                        logger.info(f"  ✅ {category} has fixed flexibility as expected")
                    
                    if category == "charitable_giving" and call_args.flexibility == "very_flexible":
                        logger.info(f"  ✅ {category} has very_flexible flexibility as expected")
                    
                    # Check if funding strategy was created with appropriate data
                    if call_args.funding_strategy:
                        try:
                            strategy = json.loads(call_args.funding_strategy)
                            logger.info(f"  ✅ {category} has funding strategy: {strategy}")
                            
                            # Check category-specific strategy elements
                            if category == "emergency_fund" and "months" in strategy:
                                logger.info(f"  ✅ emergency_fund has months parameter: {strategy['months']}")
                                
                            if category == "home_purchase" and "down_payment_percent" in strategy:
                                logger.info(f"  ✅ home_purchase has down_payment_percent: {strategy['down_payment_percent']}")
                                
                            if category == "traditional_retirement" and "retirement_age" in strategy:
                                logger.info(f"  ✅ traditional_retirement has retirement_age: {strategy['retirement_age']}")
                                
                        except json.JSONDecodeError:
                            logger.warning(f"  ❌ {category} has invalid funding strategy format")
                    else:
                        logger.warning(f"  ❌ {category} has no funding strategy")
            else:
                logger.error(f"❌ Failed to create {category} goal")

def test_calculation_services():
    """Test calculation services for goals"""
    logger.info("Testing goal calculation services...")
    
    # Mock goals for testing calculations
    mock_goals = [
        MagicMock(spec=Goal, 
                 id="goal1", 
                 category="emergency_fund",
                 title="Emergency Fund",
                 target_amount=500000,
                 current_amount=100000),
        MagicMock(spec=Goal, 
                 id="goal2", 
                 category="traditional_retirement",
                 title="Retirement",
                 target_amount=10000000,
                 current_amount=2000000)
    ]
    
    # Mock calculation results
    mock_calculated_results = [
        {
            "id": "goal1",
            "category": "emergency_fund",
            "title": "Emergency Fund",
            "target_amount": 500000,
            "current_amount": 100000,
            "required_monthly_savings": 10000,
            "current_progress": 20.0,
            "goal_success_probability": 80.0,
            "recommended_allocation": {
                "cash": 0.70,
                "debt": 0.30,
                "equity": 0.00,
                "alternative": 0.00
            }
        },
        {
            "id": "goal2",
            "category": "traditional_retirement",
            "title": "Retirement",
            "target_amount": 10000000,
            "current_amount": 2000000,
            "required_monthly_savings": 50000,
            "current_progress": 20.0,
            "goal_success_probability": 60.0,
            "recommended_allocation": {
                "equity": 0.60,
                "debt": 0.30,
                "alternative": 0.10,
                "cash": 0.00
            },
            "projection_5yr": [2500000, 3100000, 3800000, 4600000, 5500000]
        }
    ]
    
    # Mock prioritized goals
    mock_prioritized_goals = [
        {
            "id": "goal1",
            "category": "emergency_fund",
            "title": "Emergency Fund",
            "target_amount": 500000,
            "priority_score": 80.5,
            "priority_rank": 1,
            "hierarchy_level": 1,
            "is_foundation": True
        },
        {
            "id": "goal2",
            "category": "traditional_retirement",
            "title": "Retirement",
            "target_amount": 10000000,
            "priority_score": 65.2,
            "priority_rank": 2,
            "hierarchy_level": 3,
            "is_foundation": False
        }
    ]
    
    # Create mock for GoalManager
    mock_goal_manager = MagicMock()
    mock_goal_manager.get_profile_goals.return_value = mock_goals
    mock_goal_manager.get_goals_by_priority.return_value = mock_goals
    
    # Create mock for GoalCalculator
    mock_calculator = MagicMock()
    mock_calculator.calculate_amount_needed.side_effect = [500000, 10000000]
    mock_calculator.calculate_required_saving_rate.side_effect = [10000, 50000]
    mock_calculator.calculate_goal_success_probability.side_effect = [80.0, 60.0]
    
    # Patch the dependencies
    with patch('services.goal_service.GoalManager', return_value=mock_goal_manager), \
         patch('services.goal_service.GoalCalculator.get_calculator_for_goal', return_value=mock_calculator), \
         patch('models.goal_models.Goal.to_dict') as mock_to_dict, \
         patch('services.goal_service.GoalService._add_category_specific_calculations') as mock_add_calc:
        
        # Set up side effects for to_dict
        mock_to_dict.side_effect = [
            {"id": "goal1", "category": "emergency_fund", "title": "Emergency Fund", "target_amount": 500000},
            {"id": "goal2", "category": "traditional_retirement", "title": "Retirement", "target_amount": 10000000}
        ]
        
        # Set up side effects for _add_category_specific_calculations
        mock_add_calc.side_effect = mock_calculated_results
        
        # Initialize the service
        service = GoalService()
        
        # Test goal amount calculations
        profile_data = {
            "answers": [
                {"question_id": "monthly_income", "answer": 100000},
                {"question_id": "risk_profile", "answer": "moderate"}
            ]
        }
        
        calculated_goals = service.calculate_goal_amounts("test-profile-123", profile_data)
        
        if calculated_goals:
            logger.info("✅ Goal amount calculations successful")
            logger.info(f"  Calculated {len(calculated_goals)} goals")
            
            # Check if the results have the expected calculation fields
            for goal in calculated_goals:
                logger.info(f"  Goal: {goal['title']}")
                logger.info(f"    Required monthly savings: {goal['required_monthly_savings']}")
                logger.info(f"    Success probability: {goal.get('goal_success_probability')}")
                
                if "recommended_allocation" in goal:
                    logger.info(f"    Has recommended allocation")
                    
                if "projection_5yr" in goal:
                    logger.info(f"    Has 5-year projection")
        else:
            logger.error("❌ Goal amount calculations failed")
        
        # Test goal prioritization
        # Replace the mock_to_dict side effects
        mock_to_dict.side_effect = [
            {"id": "goal1", "category": "emergency_fund", "title": "Emergency Fund", "priority_score": 80.5},
            {"id": "goal2", "category": "traditional_retirement", "title": "Retirement", "priority_score": 65.2}
        ]
        
        # Mock get_category_by_name
        mock_goal_manager.get_category_by_name.side_effect = [
            MagicMock(hierarchy_level=1, is_foundation=True),
            MagicMock(hierarchy_level=3, is_foundation=False)
        ]
        
        prioritized_goals = service.analyze_goal_priorities("test-profile-123")
        
        if prioritized_goals:
            logger.info("✅ Goal prioritization successful")
            logger.info(f"  Prioritized {len(prioritized_goals)} goals")
            
            # Check if the results have the expected prioritization fields
            for i, goal in enumerate(prioritized_goals):
                logger.info(f"  Goal: {goal['title']}")
                logger.info(f"    Priority score: {goal.get('priority_score')}")
                logger.info(f"    Priority rank: {goal.get('priority_rank')}")
                logger.info(f"    Hierarchy level: {goal.get('hierarchy_level')}")
        else:
            logger.error("❌ Goal prioritization failed")

def main():
    """Run all tests"""
    logger.info("Starting goal service compatibility mock tests")
    
    try:
        # Run tests
        test_goal_creation_compatibility()
        test_goal_retrieval_compatibility()
        test_category_specific_handling()
        test_calculation_services()
        
        logger.info("All tests completed")
    
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
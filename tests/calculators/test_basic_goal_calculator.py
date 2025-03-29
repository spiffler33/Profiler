#!/usr/bin/env python3
"""
Basic test script for the GoalCalculator and FinancialParameters integration.

This script tests core functionality of goal calculators and financial parameters
without requiring all advanced features to be implemented.

Usage:
    python test_basic_goal_calculator.py
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
from models.goal_models import Goal
from models.goal_calculator import GoalCalculator
from models.financial_parameters import get_parameters

def test_basic_goal_calculator():
    """Basic test for GoalCalculator functionality"""
    logger.info("Testing basic GoalCalculator functionality...")
    
    # Test profile data structure
    profile = {
        "id": "test-profile-123",
        "name": "Test User",
        "email": "test@example.com",
        "answers": [
            {
                "question_id": "income_monthly",
                "answer": 100000  # ₹1,00,000 monthly income
            },
            {
                "question_id": "expenses_monthly",
                "answer": 60000   # ₹60,000 monthly expenses
            },
            {
                "question_id": "age",
                "answer": 35      # 35 years old
            }
        ]
    }
    
    # Create test goals for different categories
    
    # 1. Emergency fund goal
    emergency_fund = Goal(
        category="emergency_fund",
        title="Emergency Fund",
        target_amount=360000,      # ₹3.6 lakhs (6 months of expenses)
        timeframe=(datetime.now() + timedelta(days=180)).isoformat(),
        current_amount=120000,     # ₹1.2 lakhs current savings
        importance="high",
        flexibility="fixed"
    )
    
    # 2. Retirement goal
    retirement = Goal(
        category="traditional_retirement",
        title="Retirement",
        target_amount=20000000,    # ₹2 crore
        timeframe=(datetime.now() + timedelta(days=365*25)).isoformat(),  # 25 years from now
        current_amount=1000000,    # ₹10 lakhs saved so far
        importance="high",
        flexibility="somewhat_flexible"
    )
    
    # 3. Home purchase goal
    home_purchase = Goal(
        category="home_purchase",
        title="Home Down Payment",
        target_amount=2000000,     # ₹20 lakhs for down payment
        timeframe=(datetime.now() + timedelta(days=365*3)).isoformat(),  # 3 years from now
        current_amount=500000,     # ₹5 lakhs saved so far
        importance="medium",
        flexibility="somewhat_flexible"
    )
    
    # 4. Travel goal
    travel = Goal(
        category="travel",
        title="International Vacation",
        target_amount=500000,      # ₹5 lakhs
        timeframe=(datetime.now() + timedelta(days=365)).isoformat(),  # 1 year from now
        current_amount=100000,     # ₹1 lakh saved so far
        importance="low",
        flexibility="very_flexible"
    )
    
    # Create a list of test goals
    test_goals = [emergency_fund, retirement, home_purchase, travel]
    
    # Get appropriate calculators for each goal
    calculators = []
    for goal in test_goals:
        calculator = GoalCalculator.get_calculator_for_goal(goal)
        calculators.append(calculator)
        logger.info(f"Selected {calculator.__class__.__name__} for goal '{goal.title}'")
    
    # Test accessing financial parameters
    params = get_parameters()
    inflation = params.get("inflation.general")
    logger.info(f"Using inflation rate: {inflation:.1%}")
    
    # Test basic calculation methods for each goal
    for i, goal in enumerate(test_goals):
        calculator = calculators[i]
        
        # Calculate amount needed
        amount_needed = calculator.calculate_amount_needed(goal, profile)
        logger.info(f"Goal '{goal.title}' amount needed: ₹{amount_needed:,.2f}")
        
        # Calculate required saving rate
        monthly_savings, annual_savings = calculator.calculate_required_saving_rate(goal, profile)
        logger.info(f"Goal '{goal.title}' monthly savings: ₹{monthly_savings:,.2f}")
        
        # Calculate success probability
        probability = calculator.calculate_goal_success_probability(goal, profile)
        logger.info(f"Goal '{goal.title}' success probability: {probability:.1f}%")
        
        # Calculate time available
        months = calculator.calculate_time_available(goal, profile)
        logger.info(f"Goal '{goal.title}' time available: {months} months")
        
        # Validate the calculations
        if amount_needed <= 0:
            logger.warning(f"Goal '{goal.title}' has invalid amount needed: {amount_needed}")
        
        if goal.current_amount < goal.target_amount and monthly_savings <= 0:
            logger.warning(f"Goal '{goal.title}' has invalid monthly savings: {monthly_savings}")
        
        if not (0 <= probability <= 100):
            logger.warning(f"Goal '{goal.title}' has invalid success probability: {probability}")
    
    logger.info("Basic goal calculator tests completed")
    return True

if __name__ == "__main__":
    logger.info("Starting basic GoalCalculator tests")
    try:
        success = test_basic_goal_calculator()
        if success:
            logger.info("All basic tests completed successfully!")
            sys.exit(0)
        else:
            logger.error("Some basic tests failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
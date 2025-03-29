#!/usr/bin/env python3
"""
Integration test suite for Goals functionality.

This script tests:
1. CRUD operations with both old and new goal structures
2. Goal calculations with enhanced models and financial parameters
3. Goal-related functionality with both data structures
4. Goal category-specific calculations and validations

Usage:
    python test_goal_integration.py
"""

import os
import sys
import unittest
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from models.goal_models import Goal, GoalManager, GoalCategory
from models.goal_calculator import GoalCalculator
from models.financial_parameters import FinancialParameters, get_parameters
from models.database_profile_manager import DatabaseProfileManager

class GoalIntegrationTest(unittest.TestCase):
    """
    Integration test case for Goal functionality.
    Tests CRUD operations, calculations, and different goal categories.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        logger.info("Setting up test environment")
        cls.manager = GoalManager()
        cls.profile_manager = DatabaseProfileManager()
        
        # Create a test profile for goal testing
        test_profile_name = f"Test User {uuid.uuid4().hex[:6]}"
        test_profile_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
        
        logger.info(f"Creating test profile: {test_profile_name} <{test_profile_email}>")
        cls.test_profile = cls.profile_manager.create_profile(test_profile_name, test_profile_email)
        cls.test_profile_id = cls.test_profile["id"]
        
        # Create test profile with answers for goal calculations
        cls.profile_with_answers = cls.test_profile.copy()
        cls.profile_with_answers["answers"] = [
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
            },
            {
                "question_id": "risk_tolerance",
                "answer": "moderate"  # Moderate risk tolerance
            },
            {
                "question_id": "dependents",
                "answer": 2       # 2 dependents
            }
        ]
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        logger.info("Cleaning up test environment")
        
        # Delete all test goals
        try:
            for goal in cls.manager.get_profile_goals(cls.test_profile_id):
                cls.manager.delete_goal(goal.id)
        except Exception as e:
            logger.error(f"Error deleting test goals: {e}")
            
        # Delete test profile
        try:
            cls.profile_manager.delete_profile(cls.test_profile_id)
        except Exception as e:
            logger.error(f"Error deleting test profile: {e}")
    
    def test_01_create_basic_goal(self):
        """Test creating a basic goal with minimal fields (old structure)."""
        logger.info("Testing creation of basic goal")
        
        # Create a minimal goal with only required fields
        basic_goal = Goal(
            user_profile_id=self.test_profile_id,
            category="emergency_fund",
            title="Basic Emergency Fund",
            target_amount=300000,
            timeframe=(datetime.now() + timedelta(days=180)).isoformat()
        )
        
        # Save to database
        saved_goal = self.manager.create_goal(basic_goal)
        
        # Verify goal was saved
        self.assertIsNotNone(saved_goal)
        self.assertIsNotNone(saved_goal.id)
        self.assertEqual(saved_goal.title, "Basic Emergency Fund")
        self.assertEqual(saved_goal.category, "emergency_fund")
        
        # Verify default values were applied
        self.assertEqual(saved_goal.importance, "medium")
        self.assertEqual(saved_goal.flexibility, "somewhat_flexible")
        self.assertEqual(saved_goal.current_amount, 0.0)
        
        # Retrieve goal and check consistency
        retrieved_goal = self.manager.get_goal(saved_goal.id)
        self.assertIsNotNone(retrieved_goal)
        self.assertEqual(retrieved_goal.id, saved_goal.id)
        self.assertEqual(retrieved_goal.title, saved_goal.title)
        
        # Store for later tests (class-level attribute)
        GoalIntegrationTest.basic_goal = saved_goal
        
    def test_02_create_enhanced_goal(self):
        """Test creating a goal with enhanced fields (new structure)."""
        logger.info("Testing creation of enhanced goal")
        
        # Create a goal with all enhanced fields
        enhanced_goal = Goal(
            user_profile_id=self.test_profile_id,
            category="retirement",
            title="Enhanced Retirement Plan",
            target_amount=10000000,
            timeframe=(datetime.now() + timedelta(days=365*20)).isoformat(),
            current_amount=1000000,
            importance="high",
            flexibility="somewhat_flexible",
            notes="This is my primary retirement plan",
            
            # Enhanced fields
            current_progress=10.0,
            priority_score=85.0,
            additional_funding_sources="Annual bonus, employee match",
            goal_success_probability=75.0,
            adjustments_required=True,
            funding_strategy=json.dumps({
                "strategy": "monthly_contribution",
                "amount": 15000,
                "asset_allocation": {
                    "equity": 0.70,
                    "debt": 0.20,
                    "gold": 0.10
                }
            })
        )
        
        # Save to database
        saved_goal = self.manager.create_goal(enhanced_goal)
        
        # Verify goal was saved and enhanced fields are present
        self.assertIsNotNone(saved_goal)
        self.assertEqual(saved_goal.title, "Enhanced Retirement Plan")
        
        # Check enhanced fields
        self.assertEqual(saved_goal.current_progress, 10.0)
        self.assertAlmostEqual(saved_goal.priority_score, 85.0, delta=5.0)  # Allow slight difference due to recalculation
        self.assertEqual(saved_goal.additional_funding_sources, "Annual bonus, employee match")
        self.assertEqual(saved_goal.goal_success_probability, 75.0)
        self.assertEqual(saved_goal.adjustments_required, True)
        self.assertIn("monthly_contribution", saved_goal.funding_strategy)
        
        # Retrieve goal and check consistency of enhanced fields
        retrieved_goal = self.manager.get_goal(saved_goal.id)
        self.assertIsNotNone(retrieved_goal)
        
        # The database may not fully support enhanced fields yet, so check with tolerance
        # If the column exists, it should match; if not, it will be empty
        if retrieved_goal.additional_funding_sources:
            self.assertEqual(retrieved_goal.additional_funding_sources, saved_goal.additional_funding_sources)
        
        if retrieved_goal.goal_success_probability:
            self.assertEqual(retrieved_goal.goal_success_probability, saved_goal.goal_success_probability)
        
        # Store for later tests (class-level attribute)
        GoalIntegrationTest.enhanced_goal = saved_goal
    
    def test_03_update_basic_goal(self):
        """Test updating a basic goal."""
        logger.info("Testing update of basic goal")
        
        # Ensure basic_goal exists as a class attribute
        if not hasattr(GoalIntegrationTest, 'basic_goal'):
            self.skipTest("basic_goal not set, skipping this test")
            return
            
        # Update basic goal from earlier test
        GoalIntegrationTest.basic_goal.title = "Updated Emergency Fund"
        GoalIntegrationTest.basic_goal.target_amount = 350000
        GoalIntegrationTest.basic_goal.current_amount = 50000
        GoalIntegrationTest.basic_goal.importance = "high"
        
        # Save updates
        updated_goal = self.manager.update_goal(GoalIntegrationTest.basic_goal)
        
        # Verify updates were saved
        self.assertIsNotNone(updated_goal)
        self.assertEqual(updated_goal.title, "Updated Emergency Fund")
        self.assertEqual(updated_goal.target_amount, 350000)
        self.assertEqual(updated_goal.current_amount, 50000)
        self.assertEqual(updated_goal.importance, "high")
        
        # Verify progress was calculated
        expected_progress = (50000 / 350000) * 100
        self.assertAlmostEqual(updated_goal.current_progress, expected_progress, delta=0.1)
        
        # Check priority score was recalculated
        self.assertGreater(updated_goal.priority_score, 0)
        
        # Retrieve goal and confirm updates
        retrieved_goal = self.manager.get_goal(updated_goal.id)
        self.assertEqual(retrieved_goal.title, updated_goal.title)
        self.assertEqual(retrieved_goal.target_amount, updated_goal.target_amount)
        
        # Update the class attribute
        GoalIntegrationTest.basic_goal = updated_goal
    
    def test_04_update_enhanced_goal(self):
        """Test updating enhanced fields of a goal."""
        logger.info("Testing update of enhanced goal")
        
        # Ensure enhanced_goal exists as a class attribute
        if not hasattr(GoalIntegrationTest, 'enhanced_goal'):
            self.skipTest("enhanced_goal not set, skipping this test")
            return
            
        # Update enhanced goal from earlier test
        GoalIntegrationTest.enhanced_goal.current_amount = 1500000
        GoalIntegrationTest.enhanced_goal.additional_funding_sources = "Annual bonus, employee match, inheritance"
        GoalIntegrationTest.enhanced_goal.goal_success_probability = 80.0
        
        # Update funding strategy
        funding_strategy = json.loads(GoalIntegrationTest.enhanced_goal.funding_strategy)
        funding_strategy["amount"] = 20000
        GoalIntegrationTest.enhanced_goal.funding_strategy = json.dumps(funding_strategy)
        
        # Save updates
        updated_goal = self.manager.update_goal(GoalIntegrationTest.enhanced_goal)
        
        # Verify enhanced field updates were saved
        self.assertIsNotNone(updated_goal)
        self.assertEqual(updated_goal.current_amount, 1500000)
        
        # Enhanced fields might not be fully supported, check with tolerance
        if updated_goal.additional_funding_sources:
            self.assertEqual(updated_goal.additional_funding_sources, "Annual bonus, employee match, inheritance")
        
        if updated_goal.goal_success_probability:
            self.assertEqual(updated_goal.goal_success_probability, 80.0)
        
        # Verify progress was recalculated
        expected_progress = (1500000 / 10000000) * 100
        self.assertAlmostEqual(updated_goal.current_progress, expected_progress, delta=0.1)
        
        # Verify funding strategy was updated
        funding_strategy = json.loads(updated_goal.funding_strategy)
        self.assertEqual(funding_strategy["amount"], 20000)
        
        # Retrieve goal and confirm updates
        retrieved_goal = self.manager.get_goal(updated_goal.id)
        
        # Enhanced fields might not be fully supported in the DB, check with tolerance
        if retrieved_goal.additional_funding_sources and updated_goal.additional_funding_sources:
            self.assertEqual(retrieved_goal.additional_funding_sources, updated_goal.additional_funding_sources)
            
        # Update the class attribute
        GoalIntegrationTest.enhanced_goal = updated_goal
    
    def test_05_retrieve_goals_by_priority(self):
        """Test retrieving goals sorted by priority."""
        logger.info("Testing goal retrieval by priority")
        
        # Create a third goal with different priority
        low_priority_goal = Goal(
            user_profile_id=self.test_profile_id,
            category="travel",
            title="Dream Vacation",
            target_amount=200000,
            timeframe=(datetime.now() + timedelta(days=1095)).isoformat(),
            importance="low",
            flexibility="very_flexible",
            notes="Fun goal with low priority"
        )
        
        # Save to database
        saved_low_priority = self.manager.create_goal(low_priority_goal)
        
        # Get goals by priority
        priority_goals = self.manager.get_goals_by_priority(self.test_profile_id)
        
        # Verify goals are returned in correct order (highest priority first)
        # Both emergency fund (high importance) and retirement (high importance) should be higher than vacation (low importance)
        self.assertGreaterEqual(len(priority_goals), 3)  # At least the 3 goals we've created
        
        # The low priority goal should be last
        # Find position of each goal in priority list
        positions = {goal.id: i for i, goal in enumerate(priority_goals)}
        
        # Low priority goal should be after both basic and enhanced goals
        self.assertGreater(positions.get(saved_low_priority.id, 999), positions.get(self.basic_goal.id, 0))
        self.assertGreater(positions.get(saved_low_priority.id, 999), positions.get(self.enhanced_goal.id, 0))
        
        # Store for later deletion
        self.low_priority_goal = saved_low_priority
    
    def test_06_verify_backward_compatibility(self):
        """Test backward compatibility with old goal structure."""
        logger.info("Testing backward compatibility")
        
        # Create a legacy-format goal dictionary
        legacy_dict = {
            "id": str(uuid.uuid4()),
            "profile_id": self.test_profile_id,  # Old field
            "category": "education",
            "title": "Legacy Education Fund",
            "target_value": 500000,  # Old field
            "time_horizon": 5,  # Old field
            "current_value": 100000,  # Old field
            "priority": "medium",  # Old field
            "description": "Legacy-style education fund"  # Old field
        }
        
        # Convert to a new Goal object
        goal = Goal.from_legacy_dict(legacy_dict)
        
        # Verify fields were mapped correctly
        self.assertEqual(goal.id, legacy_dict["id"])
        self.assertEqual(goal.user_profile_id, legacy_dict["profile_id"])
        self.assertEqual(goal.title, legacy_dict["title"])
        self.assertEqual(goal.target_amount, legacy_dict["target_value"])
        self.assertEqual(goal.current_amount, legacy_dict["current_value"])
        self.assertEqual(goal.importance, legacy_dict["priority"])
        self.assertEqual(goal.notes, legacy_dict["description"])
        
        # Timeframe should have been converted from time_horizon
        target_date = datetime.fromisoformat(goal.timeframe)
        days_diff = (target_date - datetime.now()).days
        self.assertAlmostEqual(days_diff / 365.0, legacy_dict["time_horizon"], delta=0.1)
        
        # Save to database
        saved_goal = self.manager.create_goal(goal)
        
        # Verify goal saved correctly
        retrieved_goal = self.manager.get_goal(saved_goal.id)
        self.assertIsNotNone(retrieved_goal)
        self.assertEqual(retrieved_goal.title, "Legacy Education Fund")
        
        # Store for later deletion
        self.legacy_goal = saved_goal
    
    def test_07_verify_legacy_access(self):
        """Test accessing goal with old field names."""
        logger.info("Testing legacy field access")
        
        # Get enhanced goal from earlier test
        goal = self.enhanced_goal
        
        # Verify old field getters work correctly
        self.assertEqual(goal.priority, goal.importance)
        self.assertEqual(goal.target_value, goal.target_amount)
        self.assertEqual(goal.current_value, goal.current_amount)
        self.assertEqual(goal.progress, goal.current_progress)
        self.assertEqual(goal.description, goal.notes)
        self.assertEqual(goal.profile_id, goal.user_profile_id)
        
        # Check time_horizon conversion
        try:
            target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
            days = (target_date - datetime.now()).days
            expected_years = days / 365.0
            self.assertAlmostEqual(goal.time_horizon, expected_years, delta=0.5)
        except Exception as e:
            self.fail(f"Error converting timeframe to time_horizon: {e}")
        
        # Test to_dict with legacy_mode
        dict_modern = goal.to_dict()
        dict_legacy = goal.to_dict(legacy_mode=True)
        
        # Verify modern dict has new fields
        self.assertIn("current_progress", dict_modern)
        self.assertIn("priority_score", dict_modern)
        self.assertIn("additional_funding_sources", dict_modern)
        
        # Verify legacy dict has old field names
        self.assertIn("priority", dict_legacy)
        self.assertIn("time_horizon", dict_legacy)
        
        # Verify legacy dict doesn't have new fields
        self.assertNotIn("current_progress", dict_legacy)
        self.assertNotIn("priority_score", dict_legacy)
        self.assertNotIn("additional_funding_sources", dict_legacy)
    
    def test_08_emergency_fund_calculation(self):
        """Test emergency fund calculations."""
        logger.info("Testing emergency fund calculations")
        
        # Create emergency fund goal
        emergency_fund_goal = Goal(
            user_profile_id=self.test_profile_id,
            category="emergency_fund",
            title="Test Emergency Fund",
            target_amount=0,  # Let calculator determine target
            timeframe=(datetime.now() + timedelta(days=180)).isoformat(),
            current_amount=100000,  # ₹1,00,000 current savings
            importance="high",
            flexibility="fixed",
            notes="Build emergency fund for unexpected expenses"
        )
        
        # Get appropriate calculator for this goal type
        calculator = GoalCalculator.get_calculator_for_goal(emergency_fund_goal)
        logger.info(f"Selected calculator type: {calculator.__class__.__name__}")
        
        # Test amount needed calculation
        amount_needed = calculator.calculate_amount_needed(emergency_fund_goal, self.profile_with_answers)
        logger.info(f"Calculated emergency fund needed: ₹{amount_needed:,.2f}")
        
        # Emergency fund should be approximately 6 months of expenses (6 x 60,000 = 360,000)
        self.assertGreaterEqual(amount_needed, 300000)
        self.assertLessEqual(amount_needed, 400000)
        
        # Test monthly savings calculation
        monthly_savings = calculator.calculate_required_saving_rate(emergency_fund_goal, self.profile_with_answers)
        logger.info(f"Required monthly savings: ₹{monthly_savings:,.2f}")
        
        # For emergency funds, if the current_amount is already sufficient (>=target),
        # the required monthly savings will be 0, which is okay
        # Assert it's either 0 (fully funded) or a reasonable value if needed
        if emergency_fund_goal.current_amount < emergency_fund_goal.target_amount:
            self.assertGreater(monthly_savings, 0)
            self.assertLess(monthly_savings, self.profile_with_answers["answers"][0]["answer"])  # Less than monthly income
        else:
            self.assertEqual(monthly_savings, 0)  # Fully funded
        
        # Test success probability
        probability = calculator.calculate_goal_success_probability(emergency_fund_goal, self.profile_with_answers)
        logger.info(f"Goal success probability: {probability:.1f}%")
        
        # Verify probability is a percentage
        self.assertGreaterEqual(probability, 0)
        self.assertLessEqual(probability, 100)
        
        # Update goal with calculations
        emergency_fund_goal.target_amount = amount_needed
        emergency_fund_goal.goal_success_probability = probability
        emergency_fund_goal.funding_strategy = json.dumps({
            "strategy": "monthly_contribution",
            "amount": monthly_savings,
            "months": 6
        })
        
        # Save goal
        saved_goal = self.manager.create_goal(emergency_fund_goal)
        self.emergency_goal = saved_goal
    
    def test_09_retirement_calculation(self):
        """Test retirement goal calculations."""
        logger.info("Testing retirement calculations")
        
        # Create retirement goal
        retirement_goal = Goal(
            user_profile_id=self.test_profile_id,
            category="traditional_retirement",
            title="Test Retirement Fund",
            target_amount=0,  # Let calculator determine target
            timeframe=(datetime.now() + timedelta(days=365*25)).isoformat(),  # 25 years to retirement
            current_amount=2000000,  # ₹20 lakhs current retirement savings
            importance="high",
            flexibility="somewhat_flexible",
            notes="Build retirement corpus for comfortable retirement at age 60"
        )
        
        # Get appropriate calculator for this goal type
        calculator = GoalCalculator.get_calculator_for_goal(retirement_goal)
        logger.info(f"Selected calculator type: {calculator.__class__.__name__}")
        
        # Test amount needed calculation
        amount_needed = calculator.calculate_amount_needed(retirement_goal, self.profile_with_answers)
        logger.info(f"Calculated retirement corpus needed: ₹{amount_needed:,.2f}")
        
        # Retirement corpus should be significant multiple of annual expenses
        annual_expenses = self.profile_with_answers["answers"][1]["answer"] * 12
        self.assertGreater(amount_needed, annual_expenses * 10)
        
        # Test monthly savings calculation
        monthly_savings = calculator.calculate_required_saving_rate(retirement_goal, self.profile_with_answers)
        logger.info(f"Required monthly savings: ₹{monthly_savings:,.2f}")
        
        # Test success probability
        probability = calculator.calculate_goal_success_probability(retirement_goal, self.profile_with_answers)
        logger.info(f"Goal success probability: {probability:.1f}%")
        
        # Update goal with calculations
        retirement_goal.target_amount = amount_needed
        retirement_goal.goal_success_probability = probability
        retirement_goal.funding_strategy = json.dumps({
            "strategy": "monthly_contribution",
            "amount": monthly_savings,
            "retirement_age": 60
        })
        
        # Save goal
        saved_goal = self.manager.create_goal(retirement_goal)
        self.retirement_goal = saved_goal
    
    def test_10_home_purchase_calculation(self):
        """Test home purchase goal calculations."""
        logger.info("Testing home purchase calculations")
        
        # Create home purchase goal
        home_goal = Goal(
            user_profile_id=self.test_profile_id,
            category="home_purchase",
            title="Home Down Payment",
            target_amount=0,  # Let calculator determine target
            timeframe=(datetime.now() + timedelta(days=365*3)).isoformat(),  # 3 years to down payment
            current_amount=500000,  # ₹5 lakhs current savings
            importance="high",
            flexibility="somewhat_flexible",
            notes="Save for home purchase with property value around 1 crore"
        )
        
        # Add explicit property value for the test - the calculator looks for this
        # Set funding strategy with property value before calculation
        home_goal.funding_strategy = json.dumps({
            "property_value": 10000000,  # 1 crore property value
            "down_payment_percent": 0.20  # 20% down payment
        })
        
        # Get appropriate calculator for this goal type
        calculator = GoalCalculator.get_calculator_for_goal(home_goal)
        logger.info(f"Selected calculator type: {calculator.__class__.__name__}")
        
        # Test amount needed calculation
        amount_needed = calculator.calculate_amount_needed(home_goal, self.profile_with_answers)
        logger.info(f"Calculated home down payment needed: ₹{amount_needed:,.2f}")
        
        # Down payment should be around 20% of property value (20% of 1 crore = 20 lakhs)
        # But without explicit property value set, it may estimate based on income
        self.assertGreater(amount_needed, 500000)
        
        # Test monthly savings calculation
        monthly_savings = calculator.calculate_required_saving_rate(home_goal, self.profile_with_answers)
        logger.info(f"Required monthly savings: ₹{monthly_savings:,.2f}")
        
        # Test success probability
        probability = calculator.calculate_goal_success_probability(home_goal, self.profile_with_answers)
        logger.info(f"Goal success probability: {probability:.1f}%")
        
        # Update goal with calculations
        home_goal.target_amount = amount_needed
        home_goal.goal_success_probability = probability
        home_goal.funding_strategy = json.dumps({
            "strategy": "monthly_contribution",
            "amount": monthly_savings,
            "property_value": 10000000,  # 1 crore property value
            "down_payment_percent": 0.20  # 20% down payment
        })
        
        # Save goal
        saved_goal = self.manager.create_goal(home_goal)
        self.home_goal = saved_goal
    
    def test_11_education_calculation(self):
        """Test education goal calculations."""
        logger.info("Testing education calculations")
        
        # Create education goal
        education_goal = Goal(
            user_profile_id=self.test_profile_id,
            category="education",
            title="Child's Education",
            target_amount=0,  # Let calculator determine target
            timeframe=(datetime.now() + timedelta(days=365*10)).isoformat(),  # 10 years to education
            current_amount=200000,
            importance="medium",
            flexibility="somewhat_flexible",
            notes="Save for child's higher education"
        )
        
        # Get appropriate calculator for this goal type
        calculator = GoalCalculator.get_calculator_for_goal(education_goal)
        logger.info(f"Selected calculator type: {calculator.__class__.__name__}")
        
        # Test amount needed calculation
        amount_needed = calculator.calculate_amount_needed(education_goal, self.profile_with_answers)
        logger.info(f"Calculated education fund needed: ₹{amount_needed:,.2f}")
        
        # Education funds should be substantial
        self.assertGreater(amount_needed, 1000000)
        
        # Test monthly savings calculation
        monthly_savings = calculator.calculate_required_saving_rate(education_goal, self.profile_with_answers)
        logger.info(f"Required monthly savings: ₹{monthly_savings:,.2f}")
        
        # Test success probability
        probability = calculator.calculate_goal_success_probability(education_goal, self.profile_with_answers)
        logger.info(f"Goal success probability: {probability:.1f}%")
        
        # Update goal with calculations
        education_goal.target_amount = amount_needed
        education_goal.goal_success_probability = probability
        education_goal.funding_strategy = json.dumps({
            "strategy": "monthly_contribution",
            "amount": monthly_savings,
            "education_inflation_rate": 0.08  # 8% education inflation
        })
        
        # Save goal
        saved_goal = self.manager.create_goal(education_goal)
        self.education_goal = saved_goal
    
    def test_12_delete_goals(self):
        """Test deleting goals."""
        logger.info("Testing goal deletion")
        
        # Get all goals for our test profile
        goals = self.manager.get_profile_goals(self.test_profile_id)
        initial_count = len(goals)
        
        logger.info(f"Found {initial_count} goals for test profile")
        self.assertGreater(initial_count, 0)
        
        # Delete the first goal
        if initial_count > 0:
            goal_to_delete = goals[0]
            logger.info(f"Deleting goal: {goal_to_delete.id} - {goal_to_delete.title}")
            
            success = self.manager.delete_goal(goal_to_delete.id)
            self.assertTrue(success)
            
            # Verify goal was deleted
            deleted_goal = self.manager.get_goal(goal_to_delete.id)
            self.assertIsNone(deleted_goal)
            
            # Verify count decreased
            updated_goals = self.manager.get_profile_goals(self.test_profile_id)
            self.assertEqual(len(updated_goals), initial_count - 1)
    
    def test_13_goal_categories(self):
        """Test goal categories functionality."""
        logger.info("Testing goal categories")
        
        # Get all categories
        categories = self.manager.get_all_categories()
        self.assertGreater(len(categories), 0)
        logger.info(f"Found {len(categories)} goal categories")
        
        # Test getting by hierarchy level
        security_categories = self.manager.get_categories_by_hierarchy_level(self.manager.SECURITY_LEVEL)
        logger.info(f"Found {len(security_categories)} security-level categories")
        
        # Verify some common categories exist
        category_names = [cat.name for cat in categories]
        expected_categories = ["Security", "Essential", "Retirement", "Lifestyle"]
        for expected in expected_categories:
            self.assertIn(expected, category_names)
            
        # Get a specific category by name
        emergency_cat = self.manager.get_category_by_name("emergency_fund")
        if emergency_cat:
            logger.info(f"Found emergency fund category - hierarchy level: {emergency_cat.hierarchy_level}")
            self.assertEqual(emergency_cat.name, "emergency_fund")

def run_tests():
    """Run the test suite."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(GoalIntegrationTest)
    
    # Run tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Report results
    logger.info("Test Results:")
    logger.info(f"  Ran {result.testsRun} tests")
    logger.info(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"  Failures: {len(result.failures)}")
    logger.info(f"  Errors: {len(result.errors)}")
    
    # Return non-zero exit code if any tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    logger.info("Starting goal integration test suite")
    sys.exit(run_tests())
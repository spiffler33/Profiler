#!/usr/bin/env python3
"""
Test suite for Goal Management API V2.

This script tests the new and enhanced API endpoints in version 2 of the 
goal management API, including:
1. API versioning mechanisms (path and header-based)
2. Enhanced goal fields in responses
3. Category-specific endpoints
4. New simulation and funding strategy endpoints

Usage:
    python test_goal_api_v2.py
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
from models.database_profile_manager import DatabaseProfileManager
from flask import Flask
from app import app as flask_app

class GoalAPIV2Test(unittest.TestCase):
    """
    Test case for Goal API V2 functionality.
    Tests the new and enhanced API endpoints for goal management.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        logger.info("Setting up test environment for API V2 testing")
        
        # Create a test client
        flask_app.config['TESTING'] = True
        cls.client = flask_app.test_client()
        
        # Use the regular database for testing since we want to test the actual implementation
        cls.manager = GoalManager()
        cls.profile_manager = DatabaseProfileManager()
        
        # Create a test profile for goal testing
        test_profile_name = f"API V2 Test User {uuid.uuid4().hex[:6]}"
        test_profile_email = f"api_v2_test_{uuid.uuid4().hex[:6]}@example.com"
        
        logger.info(f"Creating test profile: {test_profile_name} <{test_profile_email}>")
        cls.test_profile = cls.profile_manager.create_profile(test_profile_name, test_profile_email)
        cls.test_profile_id = cls.test_profile["id"]
        
        # Create test goals
        cls.create_test_goals()
    
    @classmethod
    def create_test_goals(cls):
        """Create test goals for API testing."""
        # Create a basic security goal (emergency fund)
        security_goal = Goal(
            user_profile_id=cls.test_profile_id,
            category="emergency_fund",
            title="API V2 Test Emergency Fund",
            target_amount=30000,
            timeframe=(datetime.now() + timedelta(days=180)).isoformat(),
            current_amount=5000,
            importance="high",
            flexibility="fixed",
            
            # Enhanced fields
            current_progress=16.7,
            priority_score=95.0,
            additional_funding_sources="Tax refund",
            goal_success_probability=65.0,
            adjustments_required=True,
            funding_strategy=json.dumps({
                "months": 6,
                "is_foundation": True,
                "monthly_expenses": 5000
            })
        )
        
        # Save to database
        cls.security_goal = cls.manager.create_goal(security_goal)
        
        # Create a retirement goal
        retirement_goal = Goal(
            user_profile_id=cls.test_profile_id,
            category="traditional_retirement",
            title="API V2 Test Retirement",
            target_amount=2000000,
            timeframe=(datetime.now() + timedelta(days=365*25)).isoformat(),
            current_amount=400000,
            importance="high",
            flexibility="somewhat_flexible",
            notes="API V2 test retirement goal",
            
            # Enhanced fields
            current_progress=20.0,
            priority_score=80.0,
            additional_funding_sources="401k employer match, Roth IRA",
            goal_success_probability=70.0,
            adjustments_required=False,
            funding_strategy=json.dumps({
                "retirement_age": 65,
                "withdrawal_rate": 0.04,
                "yearly_expenses": 80000
            })
        )
        
        # Save to database
        cls.retirement_goal = cls.manager.create_goal(retirement_goal)
        
        # Create a lifestyle goal
        lifestyle_goal = Goal(
            user_profile_id=cls.test_profile_id,
            category="travel",
            title="API V2 Test Travel Fund",
            target_amount=15000,
            timeframe=(datetime.now() + timedelta(days=365)).isoformat(),
            current_amount=3000,
            importance="medium",
            flexibility="very_flexible",
            notes="Dream vacation fund",
            
            # Enhanced fields
            current_progress=20.0,
            priority_score=45.0,
            additional_funding_sources="Side gig income",
            goal_success_probability=80.0,
            adjustments_required=False,
            funding_strategy=json.dumps({
                "travel_type": "vacation",
                "recommended_priority": 4
            })
        )
        
        # Save to database
        cls.lifestyle_goal = cls.manager.create_goal(lifestyle_goal)
        
        logger.info(f"Created test goals: security={cls.security_goal.id}, retirement={cls.retirement_goal.id}, lifestyle={cls.lifestyle_goal.id}")
    
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
    
    def setUp(self):
        """Set up test case."""
        # Configure Flask session for our test profile
        with self.client.session_transaction() as session:
            session['profile_id'] = self.test_profile_id
    
    # API Versioning Tests
    
    def test_01_api_versioning_path(self):
        """Test API versioning through URL path prefix."""
        logger.info("Testing API versioning through URL path")
        
        # Call the v2 goals endpoint
        response = self.client.get('/api/v2/goals')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify version field is included
        self.assertIn('version', data)
        self.assertEqual(data['version'], 'v2')
        
        # Verify metadata field is included
        self.assertIn('metadata', data)
        self.assertIn('timestamp', data['metadata'])
        
        # Verify data field is included
        self.assertIn('data', data)
        
        logger.info(f"V2 API returned properly structured response with {len(data['data'])} goals")
    
    def test_02_api_versioning_header(self):
        """Test API versioning through API-Version header."""
        logger.info("Testing API versioning through header")
        
        # Call the goals priority endpoint with API-Version header
        response = self.client.get(
            '/api/goals/priority',
            headers={'API-Version': 'v2'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify version field is included
        self.assertIn('version', data)
        self.assertEqual(data['version'], 'v2')
        
        # Verify metadata field is included
        self.assertIn('metadata', data)
        
        # Verify data field is included
        self.assertIn('data', data)
        
        logger.info(f"API with version header returned properly structured response")
    
    # Core Goal Operations Tests
    
    def test_03_get_all_goals(self):
        """Test getting all goals with V2 endpoint."""
        logger.info("Testing GET /api/v2/goals")
        
        # Call the v2 goals endpoint
        response = self.client.get('/api/v2/goals')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify our test goals are included
        goals = data['data']
        goal_ids = [goal['id'] for goal in goals]
        
        self.assertIn(self.security_goal.id, goal_ids)
        self.assertIn(self.retirement_goal.id, goal_ids)
        self.assertIn(self.lifestyle_goal.id, goal_ids)
        
        # Verify enhanced fields are included
        for goal in goals:
            if goal['id'] == self.retirement_goal.id:
                self.assertIn('priority_score', goal)
                self.assertIn('current_progress', goal)
                self.assertIn('goal_success_probability', goal)
                self.assertIn('additional_funding_sources', goal)
                self.assertIn('funding_strategy', goal)
        
        logger.info(f"Found {len(goals)} goals with enhanced fields")
    
    def test_04_get_specific_goal(self):
        """Test getting a specific goal with V2 endpoint."""
        logger.info("Testing GET /api/v2/goals/:goal_id")
        
        # Call the v2 goal detail endpoint
        response = self.client.get(f'/api/v2/goals/{self.retirement_goal.id}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify correct goal is returned
        goal = data['data']
        self.assertEqual(goal['id'], self.retirement_goal.id)
        self.assertEqual(goal['title'], "API V2 Test Retirement")
        
        # Verify enhanced fields are included
        self.assertIn('priority_score', goal)
        self.assertIn('current_progress', goal)
        self.assertIn('goal_success_probability', goal)
        self.assertIn('additional_funding_sources', goal)
        self.assertIn('funding_strategy', goal)
        
        logger.info(f"Successfully retrieved goal with enhanced fields")
    
    def test_05_create_goal(self):
        """Test creating a goal with V2 endpoint."""
        logger.info("Testing POST /api/v2/goals")
        
        # Create a new goal via the API
        new_goal = {
            'category': 'education',
            'title': 'API V2 Test Education',
            'target_amount': 50000.0,
            'timeframe': (datetime.now() + timedelta(days=1825)).isoformat(),
            'current_amount': 10000.0,
            'importance': 'high',
            'flexibility': 'somewhat_flexible',
            'notes': 'College fund',
            'additional_funding_sources': '529 plan, grandparent contributions',
            'funding_strategy': json.dumps({
                'education_type': 'college',
                'years': 4,
                'yearly_cost': 25000
            })
        }
        
        # Call the create endpoint
        response = self.client.post(
            '/api/v2/goals', 
            json=new_goal,
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        
        # Verify goal was created
        created_goal = data['data']
        self.assertEqual(created_goal['title'], new_goal['title'])
        self.assertEqual(created_goal['category'], new_goal['category'])
        
        # Save ID for cleanup
        self.education_goal_id = created_goal['id']
        
        logger.info(f"Successfully created new goal with ID {self.education_goal_id}")
    
    def test_06_update_goal(self):
        """Test updating a goal with V2 endpoint."""
        logger.info("Testing PUT /api/v2/goals/:goal_id")
        
        # Update the lifestyle goal
        updates = {
            'title': 'Updated Travel Fund',
            'target_amount': 20000.0,
            'current_amount': 5000.0,
            'additional_funding_sources': 'Side gig income, overtime pay'
        }
        
        # Call the update endpoint
        response = self.client.put(
            f'/api/v2/goals/{self.lifestyle_goal.id}', 
            json=updates,
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify goal was updated
        updated_goal = data['data']
        self.assertEqual(updated_goal['title'], updates['title'])
        self.assertEqual(updated_goal['target_amount'], updates['target_amount'])
        self.assertEqual(updated_goal['current_amount'], updates['current_amount'])
        self.assertEqual(updated_goal['additional_funding_sources'], updates['additional_funding_sources'])
        
        logger.info(f"Successfully updated goal")
    
    def test_07_delete_goal(self):
        """Test deleting a goal with V2 endpoint."""
        logger.info("Testing DELETE /api/v2/goals/:goal_id")
        
        # First, verify the education goal exists
        if hasattr(self, 'education_goal_id'):
            # Call the delete endpoint
            response = self.client.delete(f'/api/v2/goals/{self.education_goal_id}')
            
            # Check response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Verify deletion was successful
            self.assertTrue(data['data']['success'])
            
            # Verify goal is actually deleted
            goal = self.manager.get_goal(self.education_goal_id)
            self.assertIsNone(goal)
            
            logger.info(f"Successfully deleted goal")
        else:
            logger.warning("Skipping deletion test: no education goal ID found")
            self.skipTest("No education goal ID found")
    
    # Category-Specific Operations Tests
    
    def test_08_get_goal_categories(self):
        """Test getting all goal categories."""
        logger.info("Testing GET /api/v2/goal-categories")
        
        # Call the categories endpoint
        response = self.client.get('/api/v2/goal-categories')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify categories are returned
        categories = data['data']
        self.assertGreater(len(categories), 0)
        
        # Verify category fields
        for category in categories:
            self.assertIn('name', category)
            self.assertIn('description', category)
            self.assertIn('hierarchy_level', category)
        
        # Test without subcategories
        response = self.client.get('/api/v2/goal-categories?include_subcategories=false')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        parent_categories = data['data']
        
        # Should be fewer categories without subcategories
        self.assertLessEqual(len(parent_categories), len(categories))
        
        logger.info(f"Found {len(categories)} categories total, {len(parent_categories)} parent categories")
    
    def test_09_get_goals_by_hierarchy(self):
        """Test getting goals by hierarchy level."""
        logger.info("Testing GET /api/v2/goal-categories/:hierarchy_level")
        
        # Call the hierarchy endpoint for security level (1)
        response = self.client.get('/api/v2/goal-categories/1')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify security goals are returned
        goals = data['data']
        security_goal_found = any(goal['id'] == self.security_goal.id for goal in goals)
        self.assertTrue(security_goal_found, "Security goal should be in hierarchy level 1")
        
        # Call the hierarchy endpoint for retirement level (3)
        response = self.client.get('/api/v2/goal-categories/3')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify retirement goals are returned
        goals = data['data']
        retirement_goal_found = any(goal['id'] == self.retirement_goal.id for goal in goals)
        self.assertTrue(retirement_goal_found, "Retirement goal should be in hierarchy level 3")
        
        logger.info(f"Successfully filtered goals by hierarchy levels")
    
    def test_10_get_goals_by_category(self):
        """Test getting goals by category name."""
        logger.info("Testing GET /api/v2/goals/category/:category_name")
        
        # Call the category endpoint for travel
        response = self.client.get('/api/v2/goals/category/travel')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify travel goals are returned
        goals = data['data']
        lifestyle_goal_found = any(goal['id'] == self.lifestyle_goal.id for goal in goals)
        self.assertTrue(lifestyle_goal_found, "Travel goal should be in travel category")
        
        logger.info(f"Successfully filtered goals by category name")
    
    # Enhanced Goal Operations Tests
    
    def test_11_goal_simulation(self):
        """Test goal progress simulation endpoint."""
        logger.info("Testing GET /api/v2/goals/simulation/:goal_id")
        
        # Call the simulation endpoint for retirement goal
        response = self.client.get(f'/api/v2/goals/simulation/{self.retirement_goal.id}?years=10')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify simulation data is returned
        simulation = data['data']
        self.assertIsNotNone(simulation)
        
        logger.info(f"Successfully simulated goal progress")
    
    def test_12_goal_funding_strategy(self):
        """Test goal funding strategy endpoint."""
        logger.info("Testing GET /api/v2/goals/funding-strategy/:goal_id")
        
        # Call the funding strategy endpoint for security goal
        response = self.client.get(f'/api/v2/goals/funding-strategy/{self.security_goal.id}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify funding strategy data is returned
        strategy = data['data']
        self.assertIn('months', strategy)
        self.assertIn('is_foundation', strategy)
        self.assertTrue(strategy['is_foundation'])
        
        logger.info(f"Successfully retrieved funding strategy")

def run_tests():
    """Run the test suite."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(GoalAPIV2Test)
    
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
    logger.info("Starting Goal API V2 test suite")
    sys.exit(run_tests())
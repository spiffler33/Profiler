#!/usr/bin/env python3
"""
Progressive API Test Suite.

This script runs tests for the API endpoints in a progressive manner,
starting with the most basic functionality and progressing to more complex features.
"""

import os
import sys
import json
import uuid
import logging
import unittest
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:5432"  # Adjust as needed

class ProgressiveAPITest(unittest.TestCase):
    """Test case for progressive API testing."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        logger.info("Setting up test environment")
        
        # Create a test profile
        cls.profile_id = "test_profile_id"  # Adjust as needed
        
        # Use a test session
        cls.session = requests.Session()
        cls.session.cookies.set("profile_id", cls.profile_id)
        
        # Create a test goal if needed
        cls.goal_id = cls.create_test_goal() if not hasattr(cls, 'goal_id') else cls.goal_id
    
    @classmethod
    def create_test_goal(cls):
        """Create a test goal for API testing."""
        # Create a new goal
        goal_data = {
            "category": "education",
            "title": "API Test Education Goal",
            "target_amount": 50000.0,
            "timeframe": (datetime.now().isoformat()),
            "current_amount": 10000.0,
            "importance": "high",
            "flexibility": "somewhat_flexible",
            "notes": "Test goal for API testing",
            "additional_funding_sources": "Test funding sources"
        }
        
        response = cls.session.post(
            f"{BASE_URL}/api/v2/goals",
            json=goal_data
        )
        
        if response.status_code == 201:
            data = response.json()
            return data.get("data", {}).get("id")
        else:
            logger.error(f"Failed to create test goal: {response.status_code} {response.text}")
            return None
    
    def test_01_get_goal_categories(self):
        """Test getting goal categories."""
        logger.info("Testing GET /api/v2/goal-categories")
        
        response = self.session.get(f"{BASE_URL}/api/v2/goal-categories")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify data structure
        self.assertIn("data", data)
        self.assertIsInstance(data["data"], list)
        self.assertGreater(len(data["data"]), 0)
        
        logger.info("Goal categories endpoint working")
    
    def test_02_get_goals(self):
        """Test getting all goals."""
        logger.info("Testing GET /api/v2/goals")
        
        response = self.session.get(f"{BASE_URL}/api/v2/goals")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify data structure
        self.assertIn("data", data)
        self.assertIsInstance(data["data"], list)
        
        logger.info(f"Goals endpoint working, found {len(data['data'])} goals")
    
    def test_03_get_specific_goal(self):
        """Test getting a specific goal."""
        if not hasattr(self, 'goal_id') or not self.goal_id:
            logger.warning("Skipping test_03_get_specific_goal: No goal ID available")
            self.skipTest("No goal ID available")
            
        logger.info(f"Testing GET /api/v2/goals/{self.goal_id}")
        
        response = self.session.get(f"{BASE_URL}/api/v2/goals/{self.goal_id}")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify data structure
        self.assertIn("data", data)
        self.assertEqual(data["data"]["id"], self.goal_id)
        
        logger.info("Specific goal endpoint working")
    
    def test_04_get_goal_probability(self):
        """Test getting goal probability."""
        if not hasattr(self, 'goal_id') or not self.goal_id:
            logger.warning("Skipping test_04_get_goal_probability: No goal ID available")
            self.skipTest("No goal ID available")
            
        logger.info(f"Testing GET /api/v2/goals/{self.goal_id}/probability")
        
        response = self.session.get(f"{BASE_URL}/api/v2/goals/{self.goal_id}/probability")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify data structure
        self.assertIn("goal_id", data)
        self.assertEqual(data["goal_id"], self.goal_id)
        self.assertIn("success_probability", data)
        
        logger.info("Goal probability endpoint working")
    
    def test_05_get_goal_adjustments(self):
        """Test getting goal adjustments."""
        if not hasattr(self, 'goal_id') or not self.goal_id:
            logger.warning("Skipping test_05_get_goal_adjustments: No goal ID available")
            self.skipTest("No goal ID available")
            
        logger.info(f"Testing GET /api/v2/goals/{self.goal_id}/adjustments")
        
        response = self.session.get(f"{BASE_URL}/api/v2/goals/{self.goal_id}/adjustments")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify data structure
        self.assertIn("goal_id", data)
        self.assertEqual(data["goal_id"], self.goal_id)
        self.assertIn("adjustments", data)
        
        logger.info("Goal adjustments endpoint working")
    
    def test_06_get_goal_scenarios(self):
        """Test getting goal scenarios."""
        if not hasattr(self, 'goal_id') or not self.goal_id:
            logger.warning("Skipping test_06_get_goal_scenarios: No goal ID available")
            self.skipTest("No goal ID available")
            
        logger.info(f"Testing GET /api/v2/goals/{self.goal_id}/scenarios")
        
        response = self.session.get(f"{BASE_URL}/api/v2/goals/{self.goal_id}/scenarios")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify data structure
        self.assertIn("goal_id", data)
        self.assertEqual(data["goal_id"], self.goal_id)
        self.assertIn("scenarios", data)
        
        logger.info("Goal scenarios endpoint working")
    
    def test_07_calculate_goal_probability(self):
        """Test calculating goal probability."""
        if not hasattr(self, 'goal_id') or not self.goal_id:
            logger.warning("Skipping test_07_calculate_goal_probability: No goal ID available")
            self.skipTest("No goal ID available")
            
        logger.info(f"Testing POST /api/v2/goals/{self.goal_id}/probability/calculate")
        
        # Request data
        request_data = {
            "update_goal": False
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/v2/goals/{self.goal_id}/probability/calculate",
            json=request_data
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify data structure
        self.assertIn("goal_id", data)
        self.assertEqual(data["goal_id"], self.goal_id)
        self.assertIn("success_probability", data)
        
        logger.info("Goal probability calculation endpoint working")
    
    def test_08_create_goal_scenario(self):
        """Test creating a goal scenario."""
        if not hasattr(self, 'goal_id') or not self.goal_id:
            logger.warning("Skipping test_08_create_goal_scenario: No goal ID available")
            self.skipTest("No goal ID available")
            
        logger.info(f"Testing POST /api/v2/goals/{self.goal_id}/scenarios")
        
        # Request data
        request_data = {
            "name": "Test Scenario",
            "description": "Test scenario created by API test",
            "parameters": {
                "target_amount": 60000.0,
                "current_amount": 15000.0,
                "monthly_contribution": 500.0
            }
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/v2/goals/{self.goal_id}/scenarios",
            json=request_data
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Verify data structure
        self.assertIn("id", data)
        self.assertIn("name", data)
        self.assertEqual(data["name"], request_data["name"])
        
        # Save scenario ID for later tests
        self.scenario_id = data["id"]
        
        logger.info(f"Goal scenario creation endpoint working, created scenario {self.scenario_id}")
    
    def test_09_get_specific_scenario(self):
        """Test getting a specific scenario."""
        if not hasattr(self, 'goal_id') or not self.goal_id or not hasattr(self, 'scenario_id') or not self.scenario_id:
            logger.warning("Skipping test_09_get_specific_scenario: No goal ID or scenario ID available")
            self.skipTest("No goal ID or scenario ID available")
            
        logger.info(f"Testing GET /api/v2/goals/{self.goal_id}/scenarios/{self.scenario_id}")
        
        response = self.session.get(f"{BASE_URL}/api/v2/goals/{self.goal_id}/scenarios/{self.scenario_id}")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify data structure
        self.assertIn("id", data)
        self.assertEqual(data["id"], self.scenario_id)
        
        logger.info("Specific scenario endpoint working")
    
    def test_10_admin_cache_api(self):
        """Test admin cache API."""
        logger.info("Testing GET /api/v2/admin/cache_stats")
        
        # Admin key header
        headers = {"X-Admin-Key": "test_admin_key"}
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/admin/cache_stats",
            headers=headers
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify data structure
        self.assertIn("size", data)
        self.assertIn("hit_rate", data)
        
        logger.info("Admin cache API endpoint working")
    
    def test_11_goal_simulation(self):
        """Test goal simulation endpoint."""
        if not hasattr(self, 'goal_id') or not self.goal_id:
            logger.warning("Skipping test_11_goal_simulation: No goal ID available")
            self.skipTest("No goal ID available")
            
        logger.info(f"Testing GET /api/v2/goals/simulation/{self.goal_id}")
        
        response = self.session.get(f"{BASE_URL}/api/v2/goals/simulation/{self.goal_id}?years=10")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify data structure
        self.assertIn("data", data)
        self.assertIn("goal_id", data["data"])
        self.assertEqual(data["data"]["goal_id"], self.goal_id)
        
        logger.info("Goal simulation endpoint working")
    
    def test_12_rate_limiting(self):
        """Test rate limiting functionality."""
        logger.info("Testing rate limiting")
        
        # Make multiple requests to trigger rate limiting
        max_requests = 5
        for i in range(max_requests):
            response = self.session.get(f"{BASE_URL}/api/v2/goals")
            self.assertEqual(response.status_code, 200)
            
            # Check for rate limit headers
            self.assertIn("X-RateLimit-Limit", response.headers)
            self.assertIn("X-RateLimit-Remaining", response.headers)
            
            logger.info(f"Request {i+1}/{max_requests} - Remaining: {response.headers.get('X-RateLimit-Remaining', 'Unknown')}")
        
        logger.info("Rate limiting headers present")
    
    def test_13_delete_scenario(self):
        """Test deleting a scenario."""
        if not hasattr(self, 'goal_id') or not self.goal_id or not hasattr(self, 'scenario_id') or not self.scenario_id:
            logger.warning("Skipping test_13_delete_scenario: No goal ID or scenario ID available")
            self.skipTest("No goal ID or scenario ID available")
            
        logger.info(f"Testing DELETE /api/v2/goals/{self.goal_id}/scenarios/{self.scenario_id}")
        
        response = self.session.delete(f"{BASE_URL}/api/v2/goals/{self.goal_id}/scenarios/{self.scenario_id}")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify data structure
        self.assertIn("message", data)
        self.assertIn("scenario_id", data)
        self.assertEqual(data["scenario_id"], self.scenario_id)
        
        logger.info("Scenario deletion endpoint working")

def run_tests():
    """Run the test suite."""
    suite = unittest.TestLoader().loadTestsFromTestCase(ProgressiveAPITest)
    
    # Run tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Report results
    logger.info("Test Results:")
    logger.info(f"  Ran {result.testsRun} tests")
    logger.info(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"  Failures: {len(result.failures)}")
    logger.info(f"  Errors: {len(result.errors)}")
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    logger.info("Starting Progressive API Test Suite")
    sys.exit(run_tests())
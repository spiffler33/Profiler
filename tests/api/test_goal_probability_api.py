#!/usr/bin/env python3
"""Tests for the goal probability API endpoints"""

import os
import sys
import unittest
import json
import uuid
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import required modules
from models.goal_models import Goal, GoalManager
from models.goal_probability import GoalProbabilityAnalyzer
from models.database_profile_manager import DatabaseProfileManager
from flask import Flask
from app import app as flask_app

class GoalProbabilityAPITest(unittest.TestCase):
    """Test case for Goal Probability API endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        logger.info("Setting up test environment for goal probability API tests")
        
        # Create a test client
        flask_app.config['TESTING'] = True
        flask_app.config['API_CACHE_ENABLED'] = True
        flask_app.config['API_CACHE_TTL'] = 3600
        flask_app.config['API_RATE_LIMIT'] = 100
        flask_app.config['ADMIN_API_KEY'] = 'test_admin_key'
        flask_app.config['FEATURE_GOAL_PROBABILITY_API'] = True
        flask_app.config['FEATURE_ADMIN_CACHE_API'] = True
        cls.client = flask_app.test_client()
        
        # Initialize managers
        cls.db_path = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db"
        cls.goal_manager = GoalManager(db_path=cls.db_path)
        cls.profile_manager = DatabaseProfileManager(db_path=cls.db_path)
        
        # Create a test profile
        test_profile_name = f"API Probability Test User {uuid.uuid4().hex[:6]}"
        test_profile_email = f"api_prob_test_{uuid.uuid4().hex[:6]}@example.com"
        
        logger.info(f"Creating test profile: {test_profile_name} <{test_profile_email}>")
        cls.test_profile = cls.profile_manager.create_profile(test_profile_name, test_profile_email)
        cls.test_profile_id = cls.test_profile["id"]
        
        # Set up test goals
        cls.create_test_goals()
        
        # Patch the app context to inject our test services
        cls.probability_analyzer_patcher = patch('app.GoalProbabilityAnalyzer', return_value=GoalProbabilityAnalyzer())
        cls.probability_analyzer_mock = cls.probability_analyzer_patcher.start()
        
        cls.goal_service_patcher = patch('app.GoalService')
        cls.goal_service_mock = cls.goal_service_patcher.start()
        cls.goal_service_mock.return_value.get_goal.side_effect = lambda goal_id: next(
            (g for g in [cls.education_goal, cls.retirement_goal, cls.wedding_goal] if g.id == goal_id), 
            None
        )
    
    @classmethod
    def create_test_goals(cls):
        """Create test goals with probability data for API testing."""
        
        # 1. Education Goal
        education_goal = Goal(
            user_profile_id=cls.test_profile_id,
            category="education",
            title="Child's Education Fund",
            target_amount=2000000,  # 20 lakh
            timeframe=(datetime.now() + timedelta(days=1825)).isoformat(),  # ~5 years
            current_amount=500000,  # 5 lakh
            importance="high",
            flexibility="somewhat_flexible",
            notes="Higher education fund for child",
            
            # Probability fields
            goal_success_probability=0.75,
            simulation_data=json.dumps({
                "success_probability": 0.75,
                "median_outcome": 2000000,
                "percentile_10": 1700000,
                "percentile_25": 1850000,
                "percentile_50": 2000000,
                "percentile_75": 2150000,
                "percentile_90": 2300000,
                "simulation_count": 1000,
                "use_indian_format": True,
                "median_outcome_formatted": "₹20.00 L"
            }),
            adjustments=json.dumps([
                {
                    "id": str(uuid.uuid4()),
                    "type": "contribution_increase",
                    "description": "Increase monthly SIP by ₹5,000",
                    "impact": 0.15,
                    "monthly_amount": 5000,
                    "implementation_steps": [
                        "Set up additional SIP with your bank",
                        "Consider tax-saving ELSS funds for 80C benefits"
                    ],
                    "tax_benefits": {
                        "80C": 60000  # Annual 80C benefit
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "timeframe_extension",
                    "description": "Extend goal timeframe by 12 months",
                    "impact": 0.10,
                    "extend_months": 12,
                    "implementation_steps": [
                        "Update your goal target date",
                        "Continue current contributions"
                    ]
                }
            ]),
            scenarios=json.dumps([
                {
                    "id": "baseline_scenario",
                    "name": "Current Plan",
                    "description": "Your current financial plan with no changes",
                    "created_at": datetime.now().isoformat(),
                    "probability": 0.75,
                    "parameters": {
                        "target_amount": 2000000,
                        "current_amount": 500000,
                        "monthly_contribution": 15000,
                        "timeframe": "2028-01-01"
                    },
                    "is_baseline": True
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Aggressive Saving",
                    "description": "Increase monthly contributions significantly",
                    "created_at": datetime.now().isoformat(),
                    "probability": 0.88,
                    "parameters": {
                        "target_amount": 2000000,
                        "current_amount": 500000,
                        "monthly_contribution": 25000,
                        "timeframe": "2028-01-01"
                    },
                    "is_baseline": False
                }
            ]),
            funding_strategy=json.dumps({
                "education_type": "undergraduate",
                "years": 4,
                "yearly_cost": 500000,  # 5 lakh per year
                "monthly_contribution": 15000,  # 15k monthly SIP
                "sip_details": {
                    "amount": 15000,
                    "frequency": "monthly",
                    "step_up_rate": 0.1  # 10% annual increase
                }
            })
        )
        
        # 2. Retirement Goal
        retirement_goal = Goal(
            user_profile_id=cls.test_profile_id,
            category="traditional_retirement",
            title="Retirement Corpus",
            target_amount=30000000,  # 3 crore
            timeframe=(datetime.now() + timedelta(days=365*25)).isoformat(),  # 25 years
            current_amount=5000000,  # 50 lakh
            importance="high",
            flexibility="somewhat_flexible",
            notes="Primary retirement fund with tax benefits",
            
            # Probability fields
            goal_success_probability=0.82,
            simulation_data=json.dumps({
                "success_probability": 0.82,
                "median_outcome": 30000000,
                "percentile_10": 24000000,
                "percentile_25": 27000000,
                "percentile_50": 30000000,
                "percentile_75": 33000000,
                "percentile_90": 36000000,
                "simulation_count": 1000,
                "use_indian_format": True,
                "median_outcome_formatted": "₹3.00 Cr"
            }),
            adjustments=json.dumps([
                {
                    "id": str(uuid.uuid4()),
                    "type": "contribution_increase",
                    "description": "Increase monthly SIP by ₹10,000",
                    "impact": 0.1,
                    "monthly_amount": 10000,
                    "tax_benefits": {
                        "80C": 120000,  # 1.2 lakh 80C benefit
                        "80CCD": 50000  # 50k NPS benefit
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "allocation_change",
                    "description": "Increase equity allocation by 10%",
                    "impact": 0.08,
                    "allocation_change": 0.1
                }
            ]),
            scenarios=json.dumps([
                {
                    "id": "baseline_scenario",
                    "name": "Current Plan",
                    "description": "Your current financial plan with no changes",
                    "created_at": datetime.now().isoformat(),
                    "probability": 0.82,
                    "parameters": {
                        "target_amount": 30000000,
                        "current_amount": 5000000,
                        "monthly_contribution": 40000,
                        "timeframe": "2048-01-01"
                    },
                    "is_baseline": True
                }
            ]),
            funding_strategy=json.dumps({
                "retirement_age": 60,
                "withdrawal_rate": 0.04,
                "yearly_expenses": 1200000,  # 12 lakh per year
                "monthly_contribution": 40000,  # 40k monthly
                "sip_details": {
                    "amount": 40000,
                    "frequency": "monthly",
                    "step_up_rate": 0.05  # 5% annual increase
                }
            })
        )
        
        # 3. Wedding Goal
        wedding_goal = Goal(
            user_profile_id=cls.test_profile_id,
            category="wedding",
            title="Daughter's Wedding Fund",
            target_amount=3000000,  # 30 lakh
            timeframe=(datetime.now() + timedelta(days=1460)).isoformat(),  # ~4 years
            current_amount=1000000,  # 10 lakh
            importance="high",
            flexibility="somewhat_flexible",
            notes="Wedding and associated expenses",
            
            # Probability fields
            goal_success_probability=0.70,
            simulation_data=json.dumps({
                "success_probability": 0.70,
                "median_outcome": 3000000,
                "percentile_10": 2400000,
                "percentile_25": 2700000,
                "percentile_50": 3000000,
                "percentile_75": 3300000,
                "percentile_90": 3600000,
                "simulation_count": 1000,
                "use_indian_format": True,
                "median_outcome_formatted": "₹30.00 L"
            }),
            adjustments=json.dumps([
                {
                    "id": str(uuid.uuid4()),
                    "type": "target_reduction",
                    "description": "Reduce wedding budget by ₹5 lakh",
                    "impact": 0.18,
                    "target_reduction": 500000
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "lump_sum",
                    "description": "Add lump sum of ₹5 lakh",
                    "impact": 0.15,
                    "lump_sum_amount": 500000
                }
            ]),
            scenarios=json.dumps([
                {
                    "id": "baseline_scenario",
                    "name": "Current Plan",
                    "created_at": datetime.now().isoformat(),
                    "probability": 0.70,
                    "parameters": {
                        "target_amount": 3000000,
                        "current_amount": 1000000,
                        "monthly_contribution": 25000,
                        "timeframe": "2027-01-01"
                    },
                    "is_baseline": True
                }
            ]),
            funding_strategy=json.dumps({
                "event_date": "2027-01-01",
                "guest_count": 300,
                "per_guest_cost": 7000,
                "monthly_contribution": 25000,  # 25k monthly
                "sip_details": {
                    "amount": 25000,
                    "frequency": "monthly"
                }
            })
        )
        
        # Save goals to database
        cls.education_goal = cls.goal_manager.create_goal(education_goal)
        cls.retirement_goal = cls.goal_manager.create_goal(retirement_goal)
        cls.wedding_goal = cls.goal_manager.create_goal(wedding_goal)
        
        logger.info(f"Created test goals - Education: {cls.education_goal.id}, Retirement: {cls.retirement_goal.id}, Wedding: {cls.wedding_goal.id}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        logger.info("Cleaning up test environment")
        
        # Stop patchers
        cls.probability_analyzer_patcher.stop()
        cls.goal_service_patcher.stop()
        
        # Delete test goals
        try:
            cls.goal_manager.delete_goal(cls.education_goal.id)
            cls.goal_manager.delete_goal(cls.retirement_goal.id)
            cls.goal_manager.delete_goal(cls.wedding_goal.id)
        except Exception as e:
            logger.error(f"Error deleting test goals: {e}")
        
        # Delete test profile
        try:
            cls.profile_manager.delete_profile(cls.test_profile_id)
        except Exception as e:
            logger.error(f"Error deleting test profile: {e}")
    
    def setUp(self):
        """Set up for each test."""
        # Configure Flask session for our test profile
        with self.client.session_transaction() as session:
            session['profile_id'] = self.test_profile_id
    
    def test_01_get_goal_probability(self):
        """Test getting probability data for a goal."""
        logger.info("Testing GET /api/v2/goals/<goal_id>/probability")
        
        # Call the API endpoint
        response = self.client.get(f'/api/v2/goals/{self.education_goal.id}/probability')
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response structure and content
        self.assertIn('goal_id', data)
        self.assertEqual(data['goal_id'], self.education_goal.id)
        
        self.assertIn('success_probability', data)
        self.assertIsInstance(data['success_probability'], (int, float))
        
        self.assertIn('probability_metrics', data)
        self.assertIn('simulation_summary', data)
        
        # Verify simulation summary
        self.assertIn('target_amount', data['simulation_summary'])
        self.assertIn('median_outcome', data['simulation_summary'])
        
        logger.info("Successfully retrieved goal probability data")
    
    def test_02_calculate_goal_probability(self):
        """Test calculating probability for a goal."""
        logger.info("Testing POST /api/v2/goals/<goal_id>/probability/calculate")
        
        # Request data for calculation
        request_data = {
            'update_goal': True
        }
        
        # Call the API endpoint
        response = self.client.post(
            f'/api/v2/goals/{self.retirement_goal.id}/probability/calculate',
            json=request_data,
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response structure and content
        self.assertIn('goal_id', data)
        self.assertEqual(data['goal_id'], self.retirement_goal.id)
        
        self.assertIn('success_probability', data)
        self.assertIsInstance(data['success_probability'], (int, float))
        
        self.assertIn('calculation_time', data)
        self.assertIn('goal_updated', data)
        self.assertTrue(data['goal_updated'])
        
        # Test with custom parameters
        custom_params_request = {
            'update_goal': False,
            'parameters': {
                'target_amount': 35000000,  # 3.5 crore
                'monthly_contribution': 50000  # 50k monthly
            }
        }
        
        # Call the API endpoint with custom parameters
        custom_response = self.client.post(
            f'/api/v2/goals/{self.retirement_goal.id}/probability/calculate',
            json=custom_params_request,
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(custom_response.status_code, 200)
        
        # Parse response
        custom_data = json.loads(custom_response.data)
        
        # Verify response for custom parameters
        self.assertIn('success_probability', custom_data)
        self.assertIn('goal_updated', custom_data)
        self.assertFalse(custom_data['goal_updated'])
        
        logger.info("Successfully calculated goal probability")
    
    def test_03_get_goal_adjustments(self):
        """Test getting adjustment recommendations."""
        logger.info("Testing GET /api/v2/goals/<goal_id>/adjustments")
        
        # Call the API endpoint
        response = self.client.get(f'/api/v2/goals/{self.wedding_goal.id}/adjustments')
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response structure and content
        self.assertIn('goal_id', data)
        self.assertEqual(data['goal_id'], self.wedding_goal.id)
        
        self.assertIn('current_probability', data)
        self.assertIn('adjustments', data)
        self.assertIsInstance(data['adjustments'], list)
        
        # Verify adjustments content
        self.assertGreater(len(data['adjustments']), 0)
        for adjustment in data['adjustments']:
            self.assertIn('id', adjustment)
            self.assertIn('type', adjustment)
            self.assertIn('description', adjustment)
            self.assertIn('impact', adjustment)
            
        # Find target reduction adjustment
        target_reduction = next((adj for adj in data['adjustments'] if adj['type'] == 'target_reduction'), None)
        if target_reduction:
            self.assertEqual(target_reduction['description'], "Reduce wedding budget by ₹5 lakh")
        
        logger.info("Successfully retrieved goal adjustments")
    
    def test_04_get_goal_scenarios(self):
        """Test getting all scenarios for a goal."""
        logger.info("Testing GET /api/v2/goals/<goal_id>/scenarios")
        
        # Call the API endpoint
        response = self.client.get(f'/api/v2/goals/{self.education_goal.id}/scenarios')
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response structure and content
        self.assertIn('goal_id', data)
        self.assertEqual(data['goal_id'], self.education_goal.id)
        
        self.assertIn('scenarios', data)
        self.assertIsInstance(data['scenarios'], list)
        
        # Verify scenarios content
        self.assertGreaterEqual(len(data['scenarios']), 2)
        
        # Check for baseline scenario
        baseline = next((s for s in data['scenarios'] if s.get('is_baseline')), None)
        self.assertIsNotNone(baseline)
        
        # Check for aggressive scenario
        aggressive = next((s for s in data['scenarios'] if s.get('name') == 'Aggressive Saving'), None)
        self.assertIsNotNone(aggressive)
        
        logger.info("Successfully retrieved goal scenarios")
    
    def test_05_create_goal_scenario(self):
        """Test creating a new scenario for a goal."""
        logger.info("Testing POST /api/v2/goals/<goal_id>/scenarios")
        
        # Scenario creation request
        scenario_request = {
            'name': 'Extended Timeline with Higher Equity',
            'description': 'Extend time by 1 year and increase equity allocation',
            'parameters': {
                'target_amount': 3000000,  # Same target
                'current_amount': 1000000,  # Same current amount
                'monthly_contribution': 25000,  # Same contribution
                'timeframe': (datetime.now() + timedelta(days=1825)).isoformat(),  # +1 year
                'equity_allocation': 0.8  # Higher equity
            }
        }
        
        # Call the API endpoint
        response = self.client.post(
            f'/api/v2/goals/{self.wedding_goal.id}/scenarios',
            json=scenario_request,
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(response.status_code, 201)
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response structure and content
        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertEqual(data['name'], 'Extended Timeline with Higher Equity')
        self.assertIn('probability', data)
        self.assertIn('parameters', data)
        self.assertFalse(data['is_baseline'])
        
        # Save scenario ID for retrieval test
        self.created_scenario_id = data['id']
        
        logger.info(f"Successfully created scenario with ID: {self.created_scenario_id}")
    
    def test_06_get_specific_scenario(self):
        """Test getting a specific scenario for a goal."""
        logger.info("Testing GET /api/v2/goals/<goal_id>/scenarios/<scenario_id>")
        
        # Create a scenario first to ensure we have one to retrieve
        # This makes the test independent of previous tests
        # Using a simplified parameter set to avoid Monte Carlo simulation errors
        scenario_request = {
            'name': 'Independent Test Scenario',
            'description': 'Created specifically for test_06_get_specific_scenario',
            'parameters': {
                'target_amount': 3000000,
                'current_amount': 500000,
                'monthly_contribution': 25000,
                'timeframe': '2030-01-01'
            }
        }
        
        # Call the API endpoint to create a scenario
        create_response = self.client.post(
            f'/api/v2/goals/{self.wedding_goal.id}/scenarios',
            json=scenario_request,
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(create_response.status_code, 201)
        
        # Parse response to get scenario ID
        scenario_data = json.loads(create_response.data)
        self.assertIn('id', scenario_data)
        scenario_id = scenario_data['id']
        
        # Call the API endpoint to get the scenario
        response = self.client.get(f'/api/v2/goals/{self.wedding_goal.id}/scenarios/{scenario_id}')
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response structure and content
        self.assertIn('id', data)
        self.assertEqual(data['id'], scenario_id)
        self.assertIn('name', data)
        self.assertEqual(data['name'], 'Independent Test Scenario')
        
        # Test retrieving baseline scenario
        baseline_response = self.client.get(f'/api/v2/goals/{self.education_goal.id}/scenarios/baseline_scenario')
        
        # Check response status
        self.assertEqual(baseline_response.status_code, 200)
        
        # Parse response
        baseline_data = json.loads(baseline_response.data)
        
        # Verify baseline scenario
        self.assertTrue(baseline_data['is_baseline'])
        
        # Save scenario ID for other tests if needed
        self.created_scenario_id = scenario_id
        
        logger.info("Successfully retrieved specific scenarios")
    
    def test_07_delete_scenario(self):
        """Test deleting a scenario."""
        logger.info("Testing DELETE /api/v2/goals/<goal_id>/scenarios/<scenario_id>")
        
        # Create a scenario first to ensure we have one to delete
        # This makes the test independent of previous tests
        # Using a simplified parameter set to avoid Monte Carlo simulation errors
        scenario_request = {
            'name': 'Scenario To Delete',
            'description': 'Created specifically for test_07_delete_scenario',
            'parameters': {
                'target_amount': 2500000,
                'current_amount': 300000,
                'monthly_contribution': 20000,
                'timeframe': '2028-06-30'
            }
        }
        
        # Call the API endpoint to create a scenario
        create_response = self.client.post(
            f'/api/v2/goals/{self.wedding_goal.id}/scenarios',
            json=scenario_request,
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(create_response.status_code, 201)
        
        # Parse response to get scenario ID
        scenario_data = json.loads(create_response.data)
        self.assertIn('id', scenario_data)
        scenario_id = scenario_data['id']
        
        # Call the API endpoint to delete the scenario
        response = self.client.delete(f'/api/v2/goals/{self.wedding_goal.id}/scenarios/{scenario_id}')
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        data = json.loads(response.data)
        
        # Verify response structure and content
        self.assertIn('message', data)
        self.assertIn('scenario_id', data)
        self.assertEqual(data['scenario_id'], scenario_id)
        
        # Verify deletion by trying to retrieve the deleted scenario
        get_response = self.client.get(f'/api/v2/goals/{self.wedding_goal.id}/scenarios/{scenario_id}')
        self.assertEqual(get_response.status_code, 404)
        
        logger.info("Successfully deleted scenario")
    
    def test_08_error_cases(self):
        """Test error cases and validation failures."""
        logger.info("Testing error cases and validation")
        
        # Test invalid goal ID
        invalid_id_response = self.client.get('/api/v2/goals/invalid-id/probability')
        self.assertEqual(invalid_id_response.status_code, 400)
        
        # Test non-existent goal ID
        nonexistent_id = str(uuid.uuid4())
        nonexistent_response = self.client.get(f'/api/v2/goals/{nonexistent_id}/probability')
        self.assertEqual(nonexistent_response.status_code, 404)
        
        # Test invalid scenario creation (missing required fields)
        invalid_scenario = {
            'description': 'Missing name and parameters'
        }
        invalid_scenario_response = self.client.post(
            f'/api/v2/goals/{self.education_goal.id}/scenarios',
            json=invalid_scenario,
            content_type='application/json'
        )
        self.assertEqual(invalid_scenario_response.status_code, 400)
        
        # Test deleting baseline scenario (should fail)
        delete_baseline_response = self.client.delete(
            f'/api/v2/goals/{self.education_goal.id}/scenarios/baseline_scenario'
        )
        self.assertEqual(delete_baseline_response.status_code, 400)
        
        logger.info("Error cases handled correctly")
    
    def test_09_indian_specific_scenarios(self):
        """Test India-specific scenarios with SIP data and tax benefits."""
        logger.info("Testing India-specific scenarios")
        
        # Test calculating probability with Indian-specific parameters
        indian_params = {
            'update_goal': False,
            'parameters': {
                'target_amount': 2500000,  # 25 lakh
                'current_amount': 500000,  # 5 lakh
                'monthly_contribution': 20000,  # 20k SIP
                'timeframe': (datetime.now() + timedelta(days=1825)).isoformat(),
                'use_indian_format': True,
                'funding_strategy': json.dumps({
                    'education_type': 'undergraduate',
                    'years': 4,
                    'yearly_cost': 625000,  # 6.25 lakh per year
                    'sip_details': {
                        'amount': 20000,
                        'frequency': 'monthly',
                        'tax_saving': True
                    },
                    'tax_benefits': {
                        '80C': 150000  # 1.5 lakh 80C limit
                    }
                })
            }
        }
        
        # Call the calculation API with Indian parameters
        indian_response = self.client.post(
            f'/api/v2/goals/{self.education_goal.id}/probability/calculate',
            json=indian_params,
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(indian_response.status_code, 200)
        
        # Parse response
        indian_data = json.loads(indian_response.data)
        
        # Verify Indian-specific formatting in the response
        if 'simulation_summary' in indian_data:
            for key in ['target_amount', 'median_outcome']:
                if f'{key}_formatted' in indian_data['simulation_summary']:
                    formatted = indian_data['simulation_summary'][f'{key}_formatted']
                    self.assertTrue(formatted.startswith('₹'))
                    self.assertTrue('L' in formatted or 'Cr' in formatted)
        
        # Test creating a scenario with Indian wedding details
        wedding_scenario = {
            'name': 'Destination Wedding',
            'description': 'Plan for a destination wedding with fewer guests',
            'parameters': {
                'target_amount': 2000000,  # 20 lakh
                'monthly_contribution': 30000,  # 30k SIP
                'funding_strategy': json.dumps({
                    'event_date': '2027-01-01',
                    'guest_count': 150,  # fewer guests
                    'per_guest_cost': 10000,  # higher per-guest cost
                    'venue_type': 'destination',
                    'sip_details': {
                        'amount': 30000,
                        'frequency': 'monthly'
                    }
                })
            }
        }
        
        # Call the scenario creation API
        wedding_scenario_response = self.client.post(
            f'/api/v2/goals/{self.wedding_goal.id}/scenarios',
            json=wedding_scenario,
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(wedding_scenario_response.status_code, 201)
        
        logger.info("Successfully tested India-specific scenarios")
        
    def test_10_admin_cache_api(self):
        """Test admin cache statistics API."""
        logger.info("Testing admin cache API endpoints")
        
        # Temporarily disable DEV_MODE to test admin auth
        original_dev_mode = flask_app.config.get('DEV_MODE', True)
        flask_app.config['DEV_MODE'] = False
        
        # Set admin key header
        admin_headers = {'X-Admin-Key': 'test_admin_key'}
        
        # Test getting cache statistics
        stats_response = self.client.get(
            '/api/v2/admin/cache_stats',
            headers=admin_headers
        )
        
        # Check response status
        self.assertEqual(stats_response.status_code, 200)
        
        # Parse response
        stats_data = json.loads(stats_response.data)
        
        # Verify response structure
        self.assertIn('size', stats_data)
        self.assertIn('hit_count', stats_data)
        self.assertIn('miss_count', stats_data)
        self.assertIn('hit_rate', stats_data)
        self.assertIn('hit_rate_percentage', stats_data)
        self.assertIn('cache_type', stats_data)
        self.assertIn('uptime', stats_data)
        self.assertIn('enabled', stats_data)
        self.assertIn('default_ttl', stats_data)
        
        # Test cache invalidation
        invalidate_response = self.client.post(
            '/api/v2/admin/cache/invalidate',
            json={'pattern': 'goal:*', 'reason': 'Test invalidation'},
            headers=admin_headers,
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(invalidate_response.status_code, 200)
        
        # Parse response
        invalidate_data = json.loads(invalidate_response.data)
        
        # Verify response structure
        self.assertIn('invalidated_entries', invalidate_data)
        self.assertIn('pattern', invalidate_data)
        self.assertIn('timestamp', invalidate_data)
        self.assertIn('audit_id', invalidate_data)
        
        # Test performance metrics
        perf_response = self.client.get(
            '/api/v2/admin/performance',
            headers=admin_headers
        )
        
        # Check response status
        self.assertEqual(perf_response.status_code, 200)
        
        # Parse response
        perf_data = json.loads(perf_response.data)
        
        # Verify response structure
        self.assertIn('cache', perf_data)
        self.assertIn('simulation_times', perf_data)
        self.assertIn('resource_usage', perf_data)
        self.assertIn('api_metrics', perf_data)
        self.assertIn('metadata', perf_data)
        self.assertIn('rate_limits', perf_data)
        
        # Test unauthorized access
        unauth_response = self.client.get('/api/v2/admin/cache_stats')
        self.assertEqual(unauth_response.status_code, 403)
        
        # Restore original DEV_MODE setting
        flask_app.config['DEV_MODE'] = original_dev_mode
        
        logger.info("Successfully tested admin cache API endpoints")
        
    def test_11_rate_limiting(self):
        """Test rate limiting functionality."""
        logger.info("Testing rate limiting functionality")
        
        # Reset rate limit store to ensure clean test
        import sys
        from api.v2.utils import _rate_limit_store
        _rate_limit_store.clear()
        
        # Temporarily set a very low rate limit for testing
        flask_app.config['API_RATE_LIMIT'] = 3
        
        # Make repeated requests to trigger rate limiting
        endpoint = f'/api/v2/goals/{self.education_goal.id}/probability'
        
        # First requests should succeed
        for i in range(3):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            
        # Next request should be rate limited
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 429)
        
        # Verify rate limit response contains required fields
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Rate limit exceeded')
        self.assertIn('retry_after', data)
        
        # Reset rate limit to normal
        flask_app.config['API_RATE_LIMIT'] = 100
        
        # Clear the rate limit store for other tests
        _rate_limit_store.clear()
        
        logger.info("Successfully tested rate limiting functionality")

def run_tests():
    """Run the test case."""
    logger.info("Running Goal Probability API tests")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(GoalProbabilityAPITest)
    
    # Run tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Report results and return appropriate exit code
    logger.info(f"Ran {result.testsRun} tests")
    logger.info(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())
"""
Flask integration tests for Monte Carlo simulations.

This module tests the integration between the Monte Carlo simulation system
and the Flask web application, testing actual HTTP routes through the full stack.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
import tempfile
import os
import re

from app import app as flask_app
from models.monte_carlo.cache import invalidate_cache
from models.monte_carlo.array_fix import to_scalar


@pytest.fixture(scope="function")
def client():
    """Create a test client for the Flask app."""
    # Configure the app for testing
    flask_app.config['TESTING'] = True
    flask_app.config['SERVER_NAME'] = 'localhost'
    
    # Use a separate test database
    test_db_fd, test_db_path = tempfile.mkstemp()
    flask_app.config['TEST_DATABASE'] = test_db_path
    
    # Flask provides a test client that simulates HTTP requests
    with flask_app.test_client() as client:
        # Establish an application context
        with flask_app.app_context():
            yield client
    
    # Clean up
    os.close(test_db_fd)
    os.unlink(test_db_path)


class TestMonteCarloFlaskIntegration:
    """Flask integration tests for Monte Carlo simulations."""
    
    def test_api_probability_endpoint(self, client):
        """Test the API endpoint for calculating goal probability."""
        # Create a test profile
        profile_data = {
            "name": "Test User",
            "email": "test@example.com",
            "monthly_income": 150000,
            "monthly_expenses": 80000,
            "total_assets": 10000000,
            "risk_profile": "aggressive"
        }
        
        # First create a profile
        profile_response = client.post(
            '/api/v2/profile',
            data=json.dumps(profile_data),
            content_type='application/json'
        )
        
        # Check profile creation
        assert profile_response.status_code == 200
        profile_result = json.loads(profile_response.data)
        assert 'id' in profile_result
        profile_id = profile_result['id']
        
        # Create a goal
        goal_data = {
            "category": "retirement",
            "title": "API Test Retirement",
            "target_amount": 50000000,
            "current_amount": 10000000,
            "timeframe": (datetime.now() + timedelta(days=365*20)).isoformat(),
            "monthly_contribution": 50000,
            "allocation": {
                "equity": 0.6,
                "debt": 0.3,
                "gold": 0.05,
                "cash": 0.05
            }
        }
        
        goal_response = client.post(
            f'/api/v2/goals/{profile_id}',
            data=json.dumps(goal_data),
            content_type='application/json'
        )
        
        # Check goal creation
        assert goal_response.status_code == 200
        goal_result = json.loads(goal_response.data)
        assert 'id' in goal_result
        goal_id = goal_result['id']
        
        # Now call the probability calculation endpoint
        # Clear cache first
        invalidate_cache()
        
        # Call the probability API endpoint
        probability_response = client.post(
            f'/api/v2/goal/{goal_id}/probability',
            data=json.dumps({
                "force_recalculate": True,
                "iterations": 1000
            }),
            content_type='application/json'
        )
        
        # Check probability response
        assert probability_response.status_code == 200
        probability_result = json.loads(probability_response.data)
        
        # Verify result structure
        assert 'success_probability' in probability_result
        assert 'goal_id' in probability_result
        assert probability_result['goal_id'] == goal_id
        
        # Check probability is in valid range
        probability = probability_result['success_probability']
        assert 0 <= probability <= 1
        
        # Verify goal details are included
        assert 'goal_details' in probability_result
        assert 'target_amount' in probability_result['goal_details']
        assert probability_result['goal_details']['target_amount'] == goal_data['target_amount']
        
        # Make a second call to test caching
        probability_response2 = client.post(
            f'/api/v2/goal/{goal_id}/probability',
            data=json.dumps({
                "force_recalculate": False
            }),
            content_type='application/json'
        )
        
        # Check second probability response
        assert probability_response2.status_code == 200
        probability_result2 = json.loads(probability_response2.data)
        
        # Should be the same probability (from cache)
        assert abs(probability_result2['success_probability'] - probability) < 0.01
    
    def test_goal_batch_probability_endpoint(self, client):
        """Test the API endpoint for calculating multiple goal probabilities."""
        # Create a test profile
        profile_data = {
            "name": "Batch Test User",
            "email": "batch_test@example.com",
            "monthly_income": 150000,
            "monthly_expenses": 80000,
            "total_assets": 10000000,
            "risk_profile": "aggressive"
        }
        
        # First create a profile
        profile_response = client.post(
            '/api/v2/profile',
            data=json.dumps(profile_data),
            content_type='application/json'
        )
        
        # Check profile creation
        profile_result = json.loads(profile_response.data)
        profile_id = profile_result['id']
        
        # Create multiple goals
        goal_ids = []
        
        # Retirement goal
        retirement_data = {
            "category": "retirement",
            "title": "API Test Retirement",
            "target_amount": 50000000,
            "current_amount": 10000000,
            "timeframe": (datetime.now() + timedelta(days=365*20)).isoformat(),
            "monthly_contribution": 50000,
            "allocation": {"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05}
        }
        
        # Education goal
        education_data = {
            "category": "education",
            "title": "API Test Education",
            "target_amount": 5000000,
            "current_amount": 1000000,
            "timeframe": (datetime.now() + timedelta(days=365*10)).isoformat(),
            "monthly_contribution": 20000,
            "allocation": {"equity": 0.5, "debt": 0.4, "gold": 0.05, "cash": 0.05}
        }
        
        # Create both goals
        for goal_data in [retirement_data, education_data]:
            goal_response = client.post(
                f'/api/v2/goals/{profile_id}',
                data=json.dumps(goal_data),
                content_type='application/json'
            )
            goal_result = json.loads(goal_response.data)
            goal_ids.append(goal_result['id'])
        
        # Call the batch probability API endpoint
        batch_response = client.post(
            f'/api/v2/goals/probability',
            data=json.dumps({
                "goal_ids": goal_ids,
                "force_recalculate": True,
                "iterations": 1000
            }),
            content_type='application/json'
        )
        
        # Check batch response
        assert batch_response.status_code == 200
        batch_result = json.loads(batch_response.data)
        
        # Verify each goal has a probability
        for goal_id in goal_ids:
            assert goal_id in batch_result
            assert 'success_probability' in batch_result[goal_id]
            probability = batch_result[goal_id]['success_probability']
            assert 0 <= probability <= 1
    
    def test_client_side_visualization_data(self, client):
        """Test the API endpoint for visualization data used by client-side charts."""
        # Create a test profile
        profile_response = client.post(
            '/api/v2/profile',
            data=json.dumps({
                "name": "Viz Test User",
                "email": "viz_test@example.com",
                "monthly_income": 150000,
                "monthly_expenses": 80000,
                "total_assets": 10000000,
                "risk_profile": "aggressive"
            }),
            content_type='application/json'
        )
        
        profile_result = json.loads(profile_response.data)
        profile_id = profile_result['id']
        
        # Create a retirement goal
        goal_response = client.post(
            f'/api/v2/goals/{profile_id}',
            data=json.dumps({
                "category": "retirement",
                "title": "Viz Test Retirement",
                "target_amount": 50000000,
                "current_amount": 10000000,
                "timeframe": (datetime.now() + timedelta(days=365*20)).isoformat(),
                "monthly_contribution": 50000,
                "allocation": {"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05}
            }),
            content_type='application/json'
        )
        
        goal_result = json.loads(goal_response.data)
        goal_id = goal_result['id']
        
        # First calculate probability
        client.post(
            f'/api/v2/goal/{goal_id}/probability',
            data=json.dumps({"force_recalculate": True, "iterations": 1000}),
            content_type='application/json'
        )
        
        # Now get visualization data
        viz_response = client.get(f'/api/v2/goal/{goal_id}/visualization')
        
        # Check visualization response
        assert viz_response.status_code == 200
        viz_result = json.loads(viz_response.data)
        
        # Check for visualization data structures
        assert 'probability_distribution' in viz_result
        assert 'timeline_projection' in viz_result
        assert 'sensitivity_analysis' in viz_result
        
        # Verify probability distribution has data points
        assert 'data_points' in viz_result['probability_distribution']
        assert len(viz_result['probability_distribution']['data_points']) > 0
        
        # Verify timeline has years and values
        assert 'years' in viz_result['timeline_projection']
        assert 'projected_values' in viz_result['timeline_projection']
        assert len(viz_result['timeline_projection']['years']) > 0
        assert len(viz_result['timeline_projection']['projected_values']) > 0
    
    def test_full_stack_monte_carlo_adjustments(self, client):
        """Test the full stack from web UI to database with Monte Carlo adjustments."""
        # Create a test profile
        profile_response = client.post(
            '/api/v2/profile',
            data=json.dumps({
                "name": "Full Stack Test User",
                "email": "full_stack@example.com",
                "monthly_income": 150000,
                "monthly_expenses": 80000,
                "total_assets": 10000000,
                "risk_profile": "aggressive"
            }),
            content_type='application/json'
        )
        
        profile_result = json.loads(profile_response.data)
        profile_id = profile_result['id']
        
        # Create a retirement goal
        goal_response = client.post(
            f'/api/v2/goals/{profile_id}',
            data=json.dumps({
                "category": "retirement",
                "title": "Full Stack Test Retirement",
                "target_amount": 100000000,  # 1 crore
                "current_amount": 10000000,  # 10 lakh
                "timeframe": (datetime.now() + timedelta(days=365*20)).isoformat(),
                "monthly_contribution": 50000,
                "allocation": {"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05}
            }),
            content_type='application/json'
        )
        
        goal_result = json.loads(goal_response.data)
        goal_id = goal_result['id']
        
        # Calculate initial probability
        prob_response1 = client.post(
            f'/api/v2/goal/{goal_id}/probability',
            data=json.dumps({"force_recalculate": True, "iterations": 1000}),
            content_type='application/json'
        )
        
        prob_result1 = json.loads(prob_response1.data)
        initial_probability = prob_result1['success_probability']
        
        # Now adjust the goal to make it more achievable
        adjustment_response = client.put(
            f'/api/v2/goal/{goal_id}',
            data=json.dumps({
                # Lower the target
                "target_amount": 80000000,  # 80 lakh (reduced from 1 crore)
                # Increase the monthly contribution
                "monthly_contribution": 70000  # Increased from 50k
            }),
            content_type='application/json'
        )
        
        assert adjustment_response.status_code == 200
        
        # Calculate new probability
        prob_response2 = client.post(
            f'/api/v2/goal/{goal_id}/probability',
            data=json.dumps({"force_recalculate": True, "iterations": 1000}),
            content_type='application/json'
        )
        
        prob_result2 = json.loads(prob_response2.data)
        adjusted_probability = prob_result2['success_probability']
        
        # The adjustment should improve the probability
        assert adjusted_probability > initial_probability, "Goal adjustments should improve probability"
        
        # Check that both the database and API are consistent
        goal_response = client.get(f'/api/v2/goal/{goal_id}')
        goal_data = json.loads(goal_response.data)
        
        assert 'goal_success_probability' in goal_data
        assert abs(goal_data['goal_success_probability'] - adjusted_probability) < 0.05
    
    def test_web_ui_integration(self, client):
        """Test the Monte Carlo integration in the web UI."""
        # First create a test profile directly
        profile_response = client.post(
            '/api/v2/profile',
            data=json.dumps({
                "name": "Web UI Test",
                "email": "webui@example.com",
                "monthly_income": 150000,
                "monthly_expenses": 80000,
                "total_assets": 10000000,
                "risk_profile": "aggressive"
            }),
            content_type='application/json'
        )
        
        profile_result = json.loads(profile_response.data)
        profile_id = profile_result['id']
        
        # Create a goal
        goal_response = client.post(
            f'/api/v2/goals/{profile_id}',
            data=json.dumps({
                "category": "retirement",
                "title": "Web UI Test Retirement",
                "target_amount": 50000000,
                "current_amount": 10000000,
                "timeframe": (datetime.now() + timedelta(days=365*20)).isoformat(),
                "monthly_contribution": 50000,
                "allocation": {"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05}
            }),
            content_type='application/json'
        )
        
        goal_result = json.loads(goal_response.data)
        goal_id = goal_result['id']
        
        # Calculate the goal probability
        client.post(
            f'/api/v2/goal/{goal_id}/probability',
            data=json.dumps({"force_recalculate": True}),
            content_type='application/json'
        )
        
        # Now test the HTML UI endpoint that would show the goal with probability
        ui_response = client.get(f'/goals/{profile_id}')
        
        # Check for a valid HTML response
        assert ui_response.status_code == 200
        html_content = ui_response.data.decode('utf-8')
        
        # Check that the goal title appears in the HTML
        assert "Web UI Test Retirement" in html_content
        
        # Check for probability visualization elements
        # These might be divs with specific IDs, data attributes, or other markers
        assert 'goal-probability-chart' in html_content or 'probability-visualization' in html_content
        
        # Check for probability percentage in the HTML (should be 0-100%)
        # This uses a regex to find percentage patterns like "85%" or "probability: 85%"
        probability_patterns = [
            r'(\d{1,3})%',  # Pattern for "85%"
            r'probability:\s*(\d{1,3})%',  # Pattern for "probability: 85%"
            r'success probability:\s*(\d{1,3})%'  # Pattern for "success probability: 85%"
        ]
        
        probability_found = False
        for pattern in probability_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                for match in matches:
                    percentage = int(match)
                    # Verify it's a reasonable percentage
                    if 0 <= percentage <= 100:
                        probability_found = True
                        break
            if probability_found:
                break
        
        assert probability_found, "Could not find probability percentage in HTML response"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
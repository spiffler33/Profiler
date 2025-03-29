"""
Test access to key routes in the Flask application
"""

import unittest
from app import app
import logging
import json

class RouteAccessTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.config['TESTING'] = True
        logging.basicConfig(level=logging.INFO)
    
    def test_inline_test_route(self):
        """Test access to the inline test route"""
        logging.info("Testing /inline_test route...")
        response = self.app.get('/inline_test')
        logging.info(f"  Status code: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, 
                       f"Failed to access /inline_test: {response.status_code}")
        self.assertIn('Inline Test Page', response.data.decode(),
                     "Response doesn't contain expected content")
        self.assertIn('<script>', response.data.decode(),
                    "Response doesn't contain JavaScript")
    
    def test_loading_state_manager_js_route(self):
        """Test access to the LoadingStateManager.js route"""
        logging.info("Testing /loading_state_manager_js route...")
        response = self.app.get('/loading_state_manager_js')
        logging.info(f"  Status code: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, 
                       f"Failed to access /loading_state_manager_js: {response.status_code}")
        self.assertIn('LoadingStateManager', response.data.decode(),
                    "Response doesn't contain expected content")
    
    def test_goal_form_probability_js_route(self):
        """Test access to the goal_form_probability_js route"""
        logging.info("Testing /goal_form_probability_js route...")
        response = self.app.get('/goal_form_probability_js')
        logging.info(f"  Status code: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, 
                       f"Failed to access /goal_form_probability_js: {response.status_code}")
        self.assertIn('GoalFormProbability', response.data.decode(),
                    "Response doesn't contain expected content")
    
    def test_test_frontend_components_route(self):
        """Test access to the test_frontend_components route"""
        logging.info("Testing /test_frontend_components route...")
        response = self.app.get('/test_frontend_components')
        logging.info(f"  Status code: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, 
                       f"Failed to access /test_frontend_components: {response.status_code}")
        
        # Parse JSON response
        data = json.loads(response.data.decode())
        logging.info(f"  Response data: {data}")
        
        self.assertEqual(data['status'], 'success', 
                       "Response doesn't indicate success")
        self.assertIn('files_checked', data, 
                    "Response doesn't include files_checked")

if __name__ == '__main__':
    unittest.main()
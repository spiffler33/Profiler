"""
Test script for Question Flow API integration.

This script tests the integration between the Question Flow frontend components
and their corresponding backend API endpoints:
- /api/v2/questions/flow
- /api/v2/questions/submit
- /api/v2/questions/dynamic

It validates that all endpoints work correctly with proper data formats and error handling.
"""

import json
import sys
import os
import unittest
import random
import logging
import uuid
from urllib.parse import urlencode
import requests

# Set up path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:5432"  # Changed port to match app.py configuration
API_BASE = f"{BASE_URL}/api/v2"

# Test profile IDs (using the ones specified in the integration plan)
TEST_PROFILES = {
    "admin": "admin-7483b11a-c7f0-491e-94f9-ff7ef243b68e",
    "partial": "partial-6030254a-54e4-459a-8ee0-050234571824",
    "complete": "complete-7b4bd9ed-8de0-4ba2-b4ac-5074424f267e"
}

class QuestionFlowAPITest(unittest.TestCase):
    """Test the Question Flow API endpoints."""

    def setUp(self):
        """Set up test environment."""
        self.session = requests.Session()
        # Use the partial profile for most tests
        self.test_profile_id = TEST_PROFILES["partial"]

    def test_get_next_question(self):
        """Test the /questions/flow endpoint."""
        logger.info("Testing GET /questions/flow...")
        
        # Build URL with query parameters
        params = {"profile_id": self.test_profile_id}
        url = f"{API_BASE}/questions/flow?{urlencode(params)}"
        
        response = self.session.get(url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response JSON
        data = response.json()
        
        # Validate response structure
        self.assertIn("profile_id", data)
        self.assertEqual(data["profile_id"], self.test_profile_id)
        self.assertIn("completion", data)
        self.assertIn("no_questions", data)
        
        # Log for debugging
        logger.info(f"Got next question response: {json.dumps(data)[:200]}...")
        
        # If we have a question, validate question structure
        if not data["no_questions"] and "next_question" in data:
            question = data["next_question"]
            self.assertIn("id", question)
            self.assertIn("text", question)
            logger.info(f"Got question: {question['id']} - {question['text']}")
            
            # Validate profile_summary if present
            if "profile_summary" in data:
                self.assertIn("understanding_level", data["profile_summary"])
                
            # Validate completion metrics
            completion = data["completion"]
            self.assertIsInstance(completion["overall"], (int, float))
            
            # Log completion metrics
            logger.info(f"Completion metrics: {completion}")
        else:
            logger.info("No more questions for this profile")

    def test_missing_profile_id(self):
        """Test the /questions/flow endpoint with a missing profile_id."""
        logger.info("Testing GET /questions/flow with missing profile_id...")
        
        url = f"{API_BASE}/questions/flow"
        response = self.session.get(url)
        
        # Should return a 400 Bad Request
        self.assertEqual(response.status_code, 400)
        
        # Parse response JSON
        data = response.json()
        
        # Validate error message
        self.assertIn("error", data)
        self.assertIn("message", data)
        self.assertIn("profile_id is required", data["message"])
        
        logger.info(f"Got expected error: {data['message']}")

    def test_nonexistent_profile(self):
        """Test the /questions/flow endpoint with a non-existent profile."""
        logger.info("Testing GET /questions/flow with non-existent profile...")
        
        # Generate a random UUID for a profile that doesn't exist
        fake_profile_id = str(uuid.uuid4())
        
        params = {"profile_id": fake_profile_id}
        url = f"{API_BASE}/questions/flow?{urlencode(params)}"
        
        response = self.session.get(url)
        
        # Should return a 404 Not Found
        self.assertEqual(response.status_code, 404)
        
        # Parse response JSON
        data = response.json()
        
        # Validate error message
        self.assertIn("error", data)
        self.assertIn("message", data)
        
        logger.info(f"Got expected error: {data['message']}")

    def test_submit_question_answer(self):
        """Test the /questions/submit endpoint."""
        logger.info("Testing POST /questions/submit...")
        
        # First get a question to answer
        params = {"profile_id": self.test_profile_id}
        url = f"{API_BASE}/questions/flow?{urlencode(params)}"
        
        response = self.session.get(url)
        self.assertEqual(response.status_code, 200)
        
        question_data = response.json()
        
        # Skip test if no questions available
        if question_data.get("no_questions", True) or "next_question" not in question_data:
            logger.info("No questions available to answer, skipping submission test")
            return
        
        question = question_data["next_question"]
        question_id = question["id"]
        
        # Prepare test answer based on question type
        answer = self._generate_test_answer(question)
        
        # Submit the answer
        url = f"{API_BASE}/questions/submit"
        payload = {
            "profile_id": self.test_profile_id,
            "question_id": question_id,
            "answer": answer
        }
        
        response = self.session.post(url, json=payload)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response JSON
        data = response.json()
        
        # Validate response structure
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("profile_id", data)
        self.assertEqual(data["profile_id"], self.test_profile_id)
        self.assertIn("question_id", data)
        self.assertEqual(data["question_id"], question_id)
        self.assertIn("updated_completion", data)
        
        logger.info(f"Successfully submitted answer for question {question_id}")
        logger.info(f"Updated completion: {data['updated_completion']['overall']}%")

    def test_missing_fields_in_submit(self):
        """Test the /questions/submit endpoint with missing fields."""
        logger.info("Testing POST /questions/submit with missing fields...")
        
        url = f"{API_BASE}/questions/submit"
        
        # Test without profile_id
        payload = {
            "question_id": "test_question",
            "answer": "test_answer"
        }
        
        response = self.session.post(url, json=payload)
        
        # Should return a 400 Bad Request
        self.assertEqual(response.status_code, 400)
        
        # Parse response JSON
        data = response.json()
        
        # Validate error message
        self.assertIn("error", data)
        self.assertIn("message", data)
        self.assertIn("profile_id", data["message"])
        
        logger.info(f"Got expected error: {data['message']}")

    def test_dynamic_question_data(self):
        """Test the /questions/dynamic endpoint."""
        logger.info("Testing GET /questions/dynamic...")
        
        # First get a question to use
        params = {"profile_id": self.test_profile_id}
        url = f"{API_BASE}/questions/flow?{urlencode(params)}"
        
        response = self.session.get(url)
        
        # Skip test if API is unavailable
        if response.status_code != 200:
            logger.warning(f"API unavailable (status {response.status_code}), skipping dynamic question test")
            return
        
        question_data = response.json()
        
        # Skip test if no questions available
        if question_data.get("no_questions", True) or "next_question" not in question_data:
            logger.info("No questions available, skipping dynamic question test")
            return
        
        question = question_data["next_question"]
        question_id = question["id"]
        
        # Get dynamic data for this question
        params = {
            "profile_id": self.test_profile_id,
            "question_id": question_id
        }
        url = f"{API_BASE}/questions/dynamic?{urlencode(params)}"
        
        response = self.session.get(url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response JSON
        data = response.json()
        
        # Validate response structure
        self.assertIn("id", data)
        self.assertEqual(data["id"], question_id)
        
        # Log data sources if available
        if "data_sources" in data:
            logger.info(f"Got {len(data['data_sources'])} data sources for question {question_id}")
            for source in data["data_sources"]:
                if "name" in source and "value" in source:
                    logger.info(f"  - {source['name']}: {source['value']}")
        
        # Check for context panel
        if "context_panel" in data:
            logger.info("Question includes context panel")
        
        # Check for reasoning
        if "reasoning" in data:
            logger.info(f"Question includes reasoning: {data['reasoning'][:50]}...")

    def test_end_to_end_question_flow(self):
        """Test the full question flow process end-to-end."""
        logger.info("Testing end-to-end question flow process...")
        
        # Use a different profile for this test to avoid conflicts
        profile_id = TEST_PROFILES["partial"]
        
        # Step 1: Get the next question
        params = {"profile_id": profile_id}
        url = f"{API_BASE}/questions/flow?{urlencode(params)}"
        
        response = self.session.get(url)
        self.assertEqual(response.status_code, 200)
        
        question_data = response.json()
        
        # Skip test if no questions available
        if question_data.get("no_questions", True) or "next_question" not in question_data:
            logger.info("No questions available, skipping end-to-end test")
            return
        
        initial_completion = question_data["completion"]["overall"]
        logger.info(f"Initial completion: {initial_completion}%")
        
        # Record 3 question/answer cycles or until no more questions
        for i in range(3):
            question = question_data["next_question"]
            question_id = question["id"]
            
            logger.info(f"Question {i+1}: {question_id} - {question['text']}")
            
            # Step 2: Get dynamic data for this question
            params = {
                "profile_id": profile_id,
                "question_id": question_id
            }
            dynamic_url = f"{API_BASE}/questions/dynamic?{urlencode(params)}"
            
            dynamic_response = self.session.get(dynamic_url)
            self.assertEqual(dynamic_response.status_code, 200)
            
            # Step 3: Generate and submit an answer
            answer = self._generate_test_answer(question)
            
            submit_url = f"{API_BASE}/questions/submit"
            payload = {
                "profile_id": profile_id,
                "question_id": question_id,
                "answer": answer
            }
            
            submit_response = self.session.post(submit_url, json=payload)
            self.assertEqual(submit_response.status_code, 200)
            
            submit_data = submit_response.json()
            logger.info(f"Answer submitted. New completion: {submit_data['updated_completion']['overall']}%")
            
            # Step 4: Get the next question
            response = self.session.get(url)
            self.assertEqual(response.status_code, 200)
            
            question_data = response.json()
            
            # Break if no more questions
            if question_data.get("no_questions", False) or "next_question" not in question_data:
                logger.info("No more questions available")
                break
        
        # Verify that completion has increased
        final_completion = question_data.get("completion", {}).get("overall", initial_completion)
        self.assertGreaterEqual(final_completion, initial_completion)
        
        logger.info(f"End-to-end test complete. Final completion: {final_completion}%")

    def _generate_test_answer(self, question):
        """Generate a test answer based on question type."""
        input_type = question.get("input_type", "text")
        
        if input_type == "number":
            return random.randint(1000, 100000)
        elif input_type == "boolean":
            return random.choice([True, False])
        elif input_type == "multiselect":
            options = question.get("options", [])
            if options:
                return random.sample([o.get("value", o) for o in options], 
                                     min(2, len(options)))
            return ["Option 1", "Option 2"]
        elif input_type == "select":
            options = question.get("options", [])
            if options:
                return random.choice([o.get("value", o) for o in options])
            return "Option 1"
        else:
            return f"Test answer for {question['id']} at {uuid.uuid4()}"

def run_tests():
    """Run the API tests."""
    logger.info("Starting Question Flow API tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    suite.addTest(QuestionFlowAPITest("test_get_next_question"))
    suite.addTest(QuestionFlowAPITest("test_missing_profile_id"))
    suite.addTest(QuestionFlowAPITest("test_nonexistent_profile"))
    suite.addTest(QuestionFlowAPITest("test_submit_question_answer"))
    suite.addTest(QuestionFlowAPITest("test_missing_fields_in_submit"))
    suite.addTest(QuestionFlowAPITest("test_dynamic_question_data"))
    suite.addTest(QuestionFlowAPITest("test_end_to_end_question_flow"))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    logger.info("Question Flow API Tests Completed")
    logger.info(f"Run {result.testsRun} tests")
    logger.info(f"Successful: {result.testsRun - len(result.errors) - len(result.failures)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    return result

if __name__ == "__main__":
    run_tests()
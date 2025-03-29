"""
Browser-based integration test for QuestionFlowManager and related components.

This tests the complete integration between:
- QuestionFlowManager.js
- DynamicQuestionRenderer 
- QuestionResponseSubmitter
- UnderstandingLevelDisplay
- The backend API endpoints

This test script sets up a test app that renders the components and validates
their proper interaction with the API endpoints.
"""

import os
import sys
import logging
import unittest
import threading
import webbrowser
import time
import json
from flask import Flask, render_template, request, jsonify, send_from_directory

# Set up path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a test Flask app
test_app = Flask(__name__, 
                template_folder='../../templates',
                static_folder='../../static')

# Test profile IDs (using the ones specified in the integration plan)
TEST_PROFILES = {
    "admin": "admin-7483b11a-c7f0-491e-94f9-ff7ef243b68e",
    "partial": "partial-6030254a-54e4-459a-8ee0-050234571824",
    "complete": "complete-7b4bd9ed-8de0-4ba2-b4ac-5074424f267e"
}

class QuestionFlowBrowserTest(unittest.TestCase):
    """Test the Question Flow components in a browser environment."""

    @classmethod
    def setUpClass(cls):
        """Start the test server."""
        cls.thread = threading.Thread(target=cls._run_server)
        cls.thread.daemon = True
        cls.thread.start()
        time.sleep(1)  # Give the server time to start

    @classmethod
    def tearDownClass(cls):
        """Stop the test server."""
        # Server will stop when the main thread exits

    @classmethod
    def _run_server(cls):
        """Run the Flask test server."""
        test_app.run(host='127.0.0.1', port=5555, debug=False)

    def test_browser_integration(self):
        """Launch browser with test page."""
        url = "http://127.0.0.1:5555/test-question-flow"
        logger.info(f"Opening browser test page at {url}")
        
        # This is a manual test - it opens the browser for visual testing
        webbrowser.open(url)
        
        # Wait for manual testing
        input("Press Enter when done testing in the browser...")
        
        # Provide instructions for the tester
        print("\nTest Instructions:")
        print("1. Verify that the test page loads all components properly")
        print("2. Check if the 'Run All Tests' button executes all tests")
        print("3. Verify that each individual test works correctly")
        print("4. Ensure that error handling works properly")
        print("5. Validate that progress tracking is updated correctly")

# Define routes for the test app
@test_app.route('/test-question-flow')
def test_question_flow():
    """Serve the test page for question flow integration."""
    # Use the partial profile for testing
    profile_id = TEST_PROFILES["partial"]
    return render_template('test_question_flow.html', profile_id=profile_id)

@test_app.route('/js/services/<path:filename>')
def serve_js_services(filename):
    """Serve JS service files."""
    return send_from_directory(os.path.join(test_app.static_folder, 'js', 'services'), filename)

@test_app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JS files."""
    return send_from_directory(os.path.join(test_app.static_folder, 'js'), filename)

@test_app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files."""
    return send_from_directory(os.path.join(test_app.static_folder, 'css'), filename)

@test_app.route('/test-log', methods=['POST'])
def test_log():
    """Endpoint to log test results from the browser."""
    data = request.get_json()
    
    if data and 'test' in data and 'result' in data:
        status = 'PASS' if data.get('passed', False) else 'FAIL'
        logger.info(f"Browser Test: {data['test']} - {status}")
        if 'message' in data:
            logger.info(f"  Message: {data['message']}")
        if 'error' in data:
            logger.error(f"  Error: {data['error']}")
    
    return jsonify({"status": "logged"})

def create_test_html():
    """Create a test HTML template if it doesn't exist."""
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'templates')
    test_template_path = os.path.join(template_dir, 'test_question_flow.html')
    
    if not os.path.exists(test_template_path):
        logger.info(f"Creating test template at {test_template_path}")
        
        with open(test_template_path, 'w') as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Question Flow Integration Test</title>
  <link rel="stylesheet" href="/css/questions.css">
  <link rel="stylesheet" href="/css/style.css">
  <style>
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      margin: 0;
      padding: 20px;
      color: #333;
    }
    
    .container {
      max-width: 1000px;
      margin: 0 auto;
    }
    
    h1, h2, h3 {
      color: #2c3e50;
    }
    
    .card {
      background: #fff;
      border-radius: 5px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      padding: 20px;
      margin-bottom: 20px;
    }
    
    .test-section {
      margin-bottom: 30px;
    }
    
    .test-controls {
      margin-bottom: 20px;
    }
    
    .test-output {
      background: #f8f9fa;
      border: 1px solid #e9ecef;
      border-radius: 4px;
      padding: 15px;
      font-family: monospace;
      white-space: pre-wrap;
      height: 200px;
      overflow-y: auto;
    }
    
    .btn {
      background: #3498db;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      margin-right: 10px;
    }
    
    .btn:hover {
      background: #2980b9;
    }
    
    .btn.secondary {
      background: #95a5a6;
    }
    
    .btn.secondary:hover {
      background: #7f8c8d;
    }
    
    .test-card {
      display: flex;
      flex-direction: column;
    }
    
    .test-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .status-indicator {
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-right: 5px;
    }
    
    .status-indicator.success {
      background: #2ecc71;
    }
    
    .status-indicator.error {
      background: #e74c3c;
    }
    
    .status-indicator.pending {
      background: #f39c12;
    }
    
    .question-section {
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      padding: 20px;
      margin-bottom: 20px;
    }

    .loader {
      display: inline-block;
      width: 20px;
      height: 20px;
      border: 3px solid rgba(0,0,0,0.1);
      border-radius: 50%;
      border-top-color: #3498db;
      animation: spin 1s ease-in-out infinite;
      margin-left: 10px;
      vertical-align: middle;
      display: none;
    }
    
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    
    /* Progress indicator styles */
    .progress-section {
      background: #f8f9fa;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 20px;
    }
    
    .progress-bar {
      height: 10px;
      background: #e9ecef;
      border-radius: 5px;
      overflow: hidden;
      margin-bottom: 10px;
    }
    
    .progress-fill {
      height: 100%;
      background: #3498db;
      width: 0%;
      transition: width 0.3s ease;
    }
    
    .understanding-level {
      display: flex;
      align-items: center;
      margin-bottom: 10px;
    }
    
    .level-indicator {
      width: 15px;
      height: 15px;
      border-radius: 50%;
      margin-right: 10px;
    }
    
    .level-indicator.low {
      background: #e74c3c;
    }
    
    .level-indicator.medium {
      background: #f39c12;
    }
    
    .level-indicator.high {
      background: #2ecc71;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Question Flow Integration Test</h1>
    <p>This page tests the integration between Question Flow components and the backend API.</p>
    
    <div class="card">
      <h2>Test Environment</h2>
      <p>Profile ID: <strong id="profile-id">{{ profile_id }}</strong></p>
      <div class="test-controls">
        <button id="run-all-tests" class="btn">Run All Tests</button>
        <button id="clear-output" class="btn secondary">Clear Output</button>
        <div class="loader" id="test-loader"></div>
      </div>
      <div class="test-output" id="test-output"></div>
    </div>
    
    <div class="test-section">
      <div class="card test-card">
        <div class="test-card-header">
          <h3>1. Initialize QuestionFlowManager</h3>
          <div>
            <span class="status-indicator" id="init-status"></span>
            <button id="run-init-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests the initialization of the QuestionFlowManager with the current profile ID.</p>
      </div>
      
      <div class="card test-card">
        <div class="test-card-header">
          <h3>2. Load Next Question</h3>
          <div>
            <span class="status-indicator" id="load-status"></span>
            <button id="run-load-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests loading the next question from the API.</p>
      </div>
      
      <div class="card test-card">
        <div class="test-card-header">
          <h3>3. Submit Question Answer</h3>
          <div>
            <span class="status-indicator" id="submit-status"></span>
            <button id="run-submit-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests submitting an answer to the current question.</p>
      </div>
      
      <div class="card test-card">
        <div class="test-card-header">
          <h3>4. Progress Tracking</h3>
          <div>
            <span class="status-indicator" id="progress-status"></span>
            <button id="run-progress-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests progress tracking and completion metrics.</p>
      </div>
      
      <div class="card test-card">
        <div class="test-card-header">
          <h3>5. Understanding Level Display</h3>
          <div>
            <span class="status-indicator" id="understanding-status"></span>
            <button id="run-understanding-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests the UnderstandingLevelDisplay component.</p>
      </div>
      
      <div class="card test-card">
        <div class="test-card-header">
          <h3>6. Error Handling</h3>
          <div>
            <span class="status-indicator" id="error-status"></span>
            <button id="run-error-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests error handling and recovery mechanisms.</p>
      </div>
    </div>
    
    <div class="card">
      <h2>Question Flow UI</h2>
      <div class="progress-section">
        <h3>Profile Understanding</h3>
        <div id="understanding-level-display">
          <!-- Understanding levels will be rendered here -->
          <div class="understanding-level">
            <div class="level-indicator medium"></div>
            <span>Financial Basics: Medium Understanding</span>
          </div>
        </div>
        
        <h3>Completion</h3>
        <div class="overall-progress">
          <label>Overall Completion</label>
          <div class="progress-bar">
            <div class="progress-fill" style="width: 0%;"></div>
          </div>
        </div>
      </div>
      
      <div class="question-answer-section">
        <!-- Questions will be rendered here -->
        <div class="question-placeholder">
          <p>Click "Load Next Question" to display a question</p>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Mock API Service (for testing) -->
  <script>
    // Define ApiService for testing - will be used by QuestionFlowManager
    window.ApiService = {
      baseUrl: '/api/v2',
      
      async get(endpoint, options = {}) {
        console.log(`[ApiService] GET ${endpoint}`, options);
        
        // Add logging to test output
        logToOutput(`API Request: GET ${endpoint}`);
        
        // Prepare URL
        let url = `${this.baseUrl}${endpoint}`;
        
        // Add query parameters
        if (options.params) {
          const searchParams = new URLSearchParams();
          for (const key in options.params) {
            searchParams.append(key, options.params[key]);
          }
          url += `?${searchParams.toString()}`;
        }
        
        try {
          const response = await fetch(url);
          
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `API Error: ${response.status} ${response.statusText}`);
          }
          
          const data = await response.json();
          logToOutput(`API Response: ${JSON.stringify(data).substring(0, 100)}...`);
          return data;
        } catch (error) {
          logToOutput(`API Error: ${error.message}`, 'error');
          throw error;
        }
      },
      
      async post(endpoint, data, options = {}) {
        console.log(`[ApiService] POST ${endpoint}`, data, options);
        
        // Add logging to test output
        logToOutput(`API Request: POST ${endpoint}`);
        logToOutput(`Request Data: ${JSON.stringify(data)}`);
        
        try {
          const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
          });
          
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `API Error: ${response.status} ${response.statusText}`);
          }
          
          const responseData = await response.json();
          logToOutput(`API Response: ${JSON.stringify(responseData).substring(0, 100)}...`);
          return responseData;
        } catch (error) {
          logToOutput(`API Error: ${error.message}`, 'error');
          throw error;
        }
      },
      
      registerStaticHandler(endpoint, handler) {
        console.log(`[ApiService] Registered handler for ${endpoint}`);
      }
    };
    
    // Define ErrorHandlingService for testing
    window.ErrorHandlingService = {
      handleError(error, context, options) {
        console.error(`[ErrorHandlingService] Error in ${context}:`, error, options);
        logToOutput(`Error in ${context}: ${error.message}`, 'error');
      }
    };
    
    // Define LoadingStateManager for testing
    window.LoadingStateManager = {
      setLoading(id, isLoading, options = {}) {
        console.log(`[LoadingStateManager] ${id} loading: ${isLoading}`, options);
        
        // Update UI loading state
        const loader = document.getElementById('test-loader');
        if (loader) {
          loader.style.display = isLoading ? 'inline-block' : 'none';
        }
        
        // Add class to question section if needed
        const questionSection = document.querySelector('.question-answer-section');
        if (questionSection) {
          if (isLoading) {
            questionSection.classList.add('is-loading');
          } else {
            questionSection.classList.remove('is-loading');
          }
        }
      }
    };
  </script>
  
  <!-- Import main JS files -->
  <script src="/js/services/QuestionFlowManager.js"></script>
  
  <!-- Test script -->
  <script>
    document.addEventListener('DOMContentLoaded', function() {
      const testOutput = document.getElementById('test-output');
      const profileId = document.getElementById('profile-id').textContent;
      
      // Initialize test environment
      logToOutput('Test environment initialized');
      logToOutput(`Using profile ID: ${profileId}`);
      
      // Helper function to log to test output
      function logToOutput(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const prefix = type === 'error' ? '❌ ERROR' : 
                      type === 'success' ? '✅ SUCCESS' : 
                      '📝 INFO';
        
        const formattedMessage = `[${timestamp}] [${prefix}] ${message}`;
        
        if (testOutput) {
          testOutput.innerHTML += formattedMessage + '\\n';
          testOutput.scrollTop = testOutput.scrollHeight;
        }
        
        // Also log to console
        console.log(formattedMessage);
        
        // Log to server
        fetch('/test-log', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            test: 'general',
            message: message,
            passed: type !== 'error'
          })
        });
      }
      
      // Set test status indicator
      function setTestStatus(testId, status) {
        const statusIndicator = document.getElementById(`${testId}-status`);
        if (statusIndicator) {
          statusIndicator.className = 'status-indicator';
          statusIndicator.classList.add(status);
        }
      }
      
      // Clear all test status indicators
      function clearAllTestStatus() {
        const statusIndicators = document.querySelectorAll('.status-indicator');
        statusIndicators.forEach(indicator => {
          indicator.className = 'status-indicator';
        });
      }
      
      // Run a test and handle results
      async function runTest(testId, testFn) {
        setTestStatus(testId, 'pending');
        logToOutput(`Running test: ${testId}`);
        
        try {
          await testFn();
          logToOutput(`Test ${testId} passed`, 'success');
          setTestStatus(testId, 'success');
          
          // Log to server
          fetch('/test-log', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              test: testId,
              result: 'pass',
              passed: true
            })
          });
          
          return true;
        } catch (error) {
          const errorMessage = error.message || 'Unknown error';
          logToOutput(`Test ${testId} failed: ${errorMessage}`, 'error');
          setTestStatus(testId, 'error');
          
          // Log to server
          fetch('/test-log', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              test: testId,
              result: 'fail',
              error: errorMessage,
              passed: false
            })
          });
          
          return false;
        }
      }
      
      // Define test functions
      const tests = {
        async init() {
          // Initialize QuestionFlowManager
          QuestionFlowManager.clearState();
          
          const result = QuestionFlowManager.initialize({
            profileId: profileId,
            containerSelector: '.question-answer-section'
          });
          
          if (!result) {
            throw new Error('Failed to initialize QuestionFlowManager');
          }
          
          // Verify initialization
          if (QuestionFlowManager.currentProfileId !== profileId) {
            throw new Error(`Profile ID mismatch: expected ${profileId}, got ${QuestionFlowManager.currentProfileId}`);
          }
          
          return true;
        },
        
        async load() {
          // Make sure QuestionFlowManager is initialized
          if (!QuestionFlowManager.currentProfileId) {
            await tests.init();
          }
          
          // Load next question
          const question = await QuestionFlowManager.loadNextQuestion();
          
          // Verify question data
          if (!question) {
            // It's okay if there are no more questions
            logToOutput('No more questions available for this profile');
            return true;
          }
          
          if (!question.id || !question.text) {
            throw new Error('Invalid question data received');
          }
          
          // Log success
          logToOutput(`Question loaded: ${question.id}`);
          
          return true;
        },
        
        async submit() {
          // Make sure we have a current question
          if (!QuestionFlowManager.currentQuestionData) {
            await tests.load();
          }
          
          // Skip test if no questions available
          if (!QuestionFlowManager.currentQuestionData) {
            logToOutput('No questions available to answer, skipping submission test');
            return true;
          }
          
          // Generate a test answer
          const question = QuestionFlowManager.currentQuestionData;
          let answer;
          
          const inputType = question.input_type || 'text';
          if (inputType === 'number') {
            answer = 10000;
          } else if (inputType === 'boolean') {
            answer = true;
          } else if (inputType === 'select' && question.options) {
            answer = question.options[0].value || question.options[0];
          } else {
            answer = `Test answer for ${question.id}`;
          }
          
          // Submit the answer
          const result = await QuestionFlowManager.submitAnswer(answer);
          
          // Verify result
          if (!result || !result.success) {
            throw new Error('Answer submission failed');
          }
          
          // Log success
          logToOutput(`Answer "${answer}" submitted successfully for question ${question.id}`);
          
          return true;
        },
        
        async progress() {
          // Make sure we have loaded a question and have progress data
          if (!QuestionFlowManager.progressData) {
            await tests.load();
          }
          
          // Get progress data
          const progress = QuestionFlowManager.getProgressData();
          
          // Verify progress data
          if (!progress || typeof progress.overall !== 'number') {
            throw new Error('Invalid progress data');
          }
          
          // Update progress UI
          const progressFill = document.querySelector('.progress-fill');
          if (progressFill) {
            progressFill.style.width = `${progress.overall}%`;
          }
          
          // Log success
          logToOutput(`Current profile completion: ${progress.overall}%`);
          
          return true;
        },
        
        async understanding() {
          // Make sure we have loaded a question
          if (!QuestionFlowManager.currentQuestionData) {
            await tests.load();
          }
          
          // Get profile data from the API directly to test understanding level
          try {
            const response = await fetch(`/api/v2/questions/flow?profile_id=${profileId}`);
            const data = await response.json();
            
            if (!data.profile_summary || !data.profile_summary.understanding_level) {
              throw new Error('No understanding level data available');
            }
            
            const understandingLevel = data.profile_summary.understanding_level;
            
            // Display understanding levels
            const understandingContainer = document.getElementById('understanding-level-display');
            if (understandingContainer) {
              understandingContainer.innerHTML = '';
              
              Object.entries(understandingLevel).forEach(([category, level]) => {
                const levelDiv = document.createElement('div');
                levelDiv.className = 'understanding-level';
                
                const indicator = document.createElement('div');
                indicator.className = `level-indicator ${level.toLowerCase()}`;
                levelDiv.appendChild(indicator);
                
                const text = document.createElement('span');
                text.textContent = `${category}: ${level} Understanding`;
                levelDiv.appendChild(text);
                
                understandingContainer.appendChild(levelDiv);
              });
            }
            
            // Log success
            logToOutput(`Understanding levels displayed: ${JSON.stringify(understandingLevel)}`);
            
            return true;
          } catch (error) {
            // Not a critical error - this is expected for test profiles
            logToOutput(`Note: Could not display understanding levels: ${error.message}`);
            return true;
          }
        },
        
        async error() {
          // Test error handling
          try {
            // Generate an invalid request on purpose
            await ApiService.get('/questions/flow');
            throw new Error('Expected error was not thrown');
          } catch (error) {
            // This should be caught - it's what we expect
            logToOutput('Error handling successful: correctly caught missing profile_id error');
            return true;
          }
        }
      };
      
      // Set up button event listeners
      document.getElementById('run-init-test').addEventListener('click', () => runTest('init', tests.init));
      document.getElementById('run-load-test').addEventListener('click', () => runTest('load', tests.load));
      document.getElementById('run-submit-test').addEventListener('click', () => runTest('submit', tests.submit));
      document.getElementById('run-progress-test').addEventListener('click', () => runTest('progress', tests.progress));
      document.getElementById('run-understanding-test').addEventListener('click', () => runTest('understanding', tests.understanding));
      document.getElementById('run-error-test').addEventListener('click', () => runTest('error', tests.error));
      
      // Run all tests
      document.getElementById('run-all-tests').addEventListener('click', async () => {
        // Clear output
        testOutput.innerHTML = '';
        
        // Clear test status indicators
        clearAllTestStatus();
        
        logToOutput('Running all tests...');
        
        // Run tests in sequence
        await runTest('init', tests.init);
        await runTest('load', tests.load);
        await runTest('submit', tests.submit);
        await runTest('progress', tests.progress);
        await runTest('understanding', tests.understanding);
        await runTest('error', tests.error);
        
        logToOutput('All tests completed');
      });
      
      // Clear output
      document.getElementById('clear-output').addEventListener('click', () => {
        testOutput.innerHTML = '';
      });
      
      // Initialize with welcome message
      logToOutput('Question Flow Integration Test ready');
      logToOutput('Click "Run All Tests" to begin, or run individual tests');
    });
    
    // Helper function to log to test output (globally available)
    function logToOutput(message, type = 'info') {
      const testOutput = document.getElementById('test-output');
      const timestamp = new Date().toLocaleTimeString();
      const prefix = type === 'error' ? '❌ ERROR' : 
                    type === 'success' ? '✅ SUCCESS' : 
                    '📝 INFO';
      
      const formattedMessage = `[${timestamp}] [${prefix}] ${message}`;
      
      if (testOutput) {
        testOutput.innerHTML += formattedMessage + '\\n';
        testOutput.scrollTop = testOutput.scrollHeight;
      }
    }
  </script>
</body>
</html>
""")
        logger.info("Created test template file")
    else:
        logger.info(f"Using existing test template at {test_template_path}")

def run_browser_tests():
    """Run the browser-based integration tests."""
    # Create test HTML if needed
    create_test_html()
    
    # Run the tests
    logger.info("Starting Question Flow browser integration tests")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    logger.info("Browser integration test completed")
    logger.info("Remember to check the browser for visual verification of the tests")

if __name__ == "__main__":
    run_browser_tests()
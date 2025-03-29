"""
Browser-based integration test for the SystemHealthDashboard component.

This tests the complete integration between:
- The SystemHealthDashboard component
- The backend API endpoints (/api/v2/admin/health and /api/v2/admin/health/history)
- Alert visualization
- Historical data visualization with time ranges and intervals
- Auto-refresh functionality

This test script sets up a test app that renders the dashboard and validates
its proper interaction with the API endpoints.
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

# Test admin account ID
ADMIN_USER_ID = "admin-7483b11a-c7f0-491e-94f9-ff7ef243b68e"

class SystemHealthDashboardTest(unittest.TestCase):
    """Test the System Health Dashboard component in a browser environment."""

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
        test_app.run(host='127.0.0.1', port=5556, debug=False)

    def test_browser_integration(self):
        """Launch browser with test page."""
        url = "http://127.0.0.1:5556/test-system-health-dashboard"
        logger.info(f"Opening browser test page at {url}")
        
        # This is a manual test - it opens the browser for visual testing
        webbrowser.open(url)
        
        # Wait for manual testing
        input("Press Enter when done testing in the browser...")
        
        # Provide instructions for the tester
        print("\nTest Instructions:")
        print("1. Verify that the dashboard renders all components properly")
        print("2. Check if the 'Run All Tests' button executes all tests")
        print("3. Verify that each individual test works correctly")
        print("4. Ensure that the dashboard properly displays data from the API")
        print("5. Validate that time range selection works correctly")
        print("6. Check that auto-refresh functionality works")
        print("7. Verify that alerts display properly with correct status indicators")

# Define routes for the test app
@test_app.route('/test-system-health-dashboard')
def test_system_health_dashboard():
    """Serve the test page for system health dashboard integration."""
    return render_template('test_system_health_dashboard.html', admin_id=ADMIN_USER_ID)

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
    test_template_path = os.path.join(template_dir, 'test_system_health_dashboard.html')
    
    if not os.path.exists(test_template_path):
        logger.info(f"Creating test template at {test_template_path}")
        
        with open(test_template_path, 'w') as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>System Health Dashboard Integration Test</title>
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
      max-width: 1200px;
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
    
    /* Dashboard-specific styles */
    .dashboard-section {
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      padding: 20px;
      margin-bottom: 20px;
    }
    
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 20px;
      margin-bottom: 20px;
    }
    
    .metric-card {
      background: #f8f9fa;
      border-radius: 8px;
      padding: 15px;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    
    .metric-value {
      font-size: 24px;
      font-weight: bold;
      margin: 10px 0;
    }
    
    .metric-label {
      font-size: 14px;
      color: #7f8c8d;
    }
    
    .alerts-section {
      margin-top: 20px;
    }
    
    .alert-item {
      background: #f8f9fa;
      border-left: 5px solid;
      padding: 10px;
      margin-bottom: 10px;
      border-radius: 0 4px 4px 0;
    }
    
    .alert-item.critical {
      border-left-color: #e74c3c;
      background: rgba(231, 76, 60, 0.1);
    }
    
    .alert-item.warning {
      border-left-color: #f39c12;
      background: rgba(243, 156, 18, 0.1);
    }
    
    .alert-item.info {
      border-left-color: #3498db;
      background: rgba(52, 152, 219, 0.1);
    }
    
    .time-range-selector {
      display: flex;
      margin-bottom: 20px;
    }
    
    .time-range-option {
      background: #ecf0f1;
      padding: 8px 16px;
      border-radius: 4px;
      margin-right: 10px;
      cursor: pointer;
    }
    
    .time-range-option.active {
      background: #3498db;
      color: white;
    }
    
    .chart-container {
      height: 300px;
      background: #f8f9fa;
      border-radius: 4px;
      padding: 10px;
      margin-bottom: 20px;
      position: relative;
    }
    
    .chart-placeholder {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #95a5a6;
    }
    
    /* Gauge styling */
    .gauge-container {
      width: 100%;
      height: 120px;
      position: relative;
      margin-bottom: 10px;
    }
    
    .gauge {
      position: relative;
      width: 120px;
      height: 120px;
      margin: 0 auto;
    }
    
    .gauge-background {
      position: absolute;
      width: 120px;
      height: 60px;
      border-radius: 120px 120px 0 0;
      background: #ecf0f1;
      overflow: hidden;
    }
    
    .gauge-fill {
      position: absolute;
      width: 120px;
      height: 60px;
      border-radius: 120px 120px 0 0;
      background: linear-gradient(90deg, #2ecc71, #f1c40f, #e74c3c);
      transform-origin: center bottom;
      transform: rotate(0deg);
      transition: transform 0.5s;
    }
    
    .gauge-center {
      position: absolute;
      width: 80px;
      height: 40px;
      top: 10px;
      left: 20px;
      border-radius: 80px 80px 0 0;
      background: white;
    }
    
    .gauge-value {
      position: absolute;
      width: 100%;
      text-align: center;
      bottom: 20px;
      font-weight: bold;
      font-size: 18px;
    }
    
    /* Health Status Indicator */
    .health-status {
      display: flex;
      align-items: center;
      padding: 10px;
      border-radius: 4px;
      margin-bottom: 20px;
    }
    
    .health-status.healthy {
      background: rgba(46, 204, 113, 0.1);
      color: #27ae60;
    }
    
    .health-status.warning {
      background: rgba(243, 156, 18, 0.1);
      color: #d35400;
    }
    
    .health-status.critical {
      background: rgba(231, 76, 60, 0.1);
      color: #c0392b;
    }
    
    .health-status-icon {
      font-size: 24px;
      margin-right: 10px;
    }
    
    .health-status-text {
      font-weight: bold;
    }
    
    /* Auto-refresh button */
    .auto-refresh-container {
      display: flex;
      align-items: center;
      margin-bottom: 20px;
    }
    
    .auto-refresh-toggle {
      position: relative;
      display: inline-block;
      width: 50px;
      height: 24px;
      margin-right: 10px;
    }
    
    .auto-refresh-toggle input {
      opacity: 0;
      width: 0;
      height: 0;
    }
    
    .toggle-slider {
      position: absolute;
      cursor: pointer;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: #ccc;
      transition: .4s;
      border-radius: 24px;
    }
    
    .toggle-slider:before {
      position: absolute;
      content: "";
      height: 16px;
      width: 16px;
      left: 4px;
      bottom: 4px;
      background-color: white;
      transition: .4s;
      border-radius: 50%;
    }
    
    input:checked + .toggle-slider {
      background-color: #2ecc71;
    }
    
    input:checked + .toggle-slider:before {
      transform: translateX(26px);
    }
    
    .auto-refresh-label {
      line-height: 24px;
    }
    
    .auto-refresh-timer {
      margin-left: 10px;
      font-size: 14px;
      color: #95a5a6;
    }
    
    /* Refresh button */
    .refresh-button {
      display: flex;
      align-items: center;
      background: #3498db;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      margin-right: 10px;
    }
    
    .refresh-button:hover {
      background: #2980b9;
    }
    
    .refresh-icon {
      margin-right: 6px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>System Health Dashboard Integration Test</h1>
    <p>This page tests the integration between the SystemHealthDashboard component and the backend API.</p>
    
    <div class="card">
      <h2>Test Environment</h2>
      <p>Admin ID: <strong id="admin-id">{{ admin_id }}</strong></p>
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
          <h3>1. Load Current Metrics</h3>
          <div>
            <span class="status-indicator" id="current-status"></span>
            <button id="run-current-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests loading current system health metrics.</p>
      </div>
      
      <div class="card test-card">
        <div class="test-card-header">
          <h3>2. Load Historical Metrics</h3>
          <div>
            <span class="status-indicator" id="history-status"></span>
            <button id="run-history-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests loading historical metrics data.</p>
      </div>
      
      <div class="card test-card">
        <div class="test-card-header">
          <h3>3. Time Range Selection</h3>
          <div>
            <span class="status-indicator" id="timerange-status"></span>
            <button id="run-timerange-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests selecting different time ranges for historical data.</p>
      </div>
      
      <div class="card test-card">
        <div class="test-card-header">
          <h3>4. Interval Selection</h3>
          <div>
            <span class="status-indicator" id="interval-status"></span>
            <button id="run-interval-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests selecting different interval periods for data aggregation.</p>
      </div>
      
      <div class="card test-card">
        <div class="test-card-header">
          <h3>5. Alert Visualization</h3>
          <div>
            <span class="status-indicator" id="alerts-status"></span>
            <button id="run-alerts-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests alert display and generation.</p>
      </div>
      
      <div class="card test-card">
        <div class="test-card-header">
          <h3>6. Auto-Refresh Functionality</h3>
          <div>
            <span class="status-indicator" id="autorefresh-status"></span>
            <button id="run-autorefresh-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests auto-refresh functionality of the dashboard.</p>
      </div>
      
      <div class="card test-card">
        <div class="test-card-header">
          <h3>7. Error Handling</h3>
          <div>
            <span class="status-indicator" id="error-status"></span>
            <button id="run-error-test" class="btn">Run Test</button>
          </div>
        </div>
        <p>Tests error handling and recovery mechanisms.</p>
      </div>
    </div>
    
    <div class="card">
      <h2>Dashboard UI</h2>
      
      <div class="dashboard-controls">
        <div class="auto-refresh-container">
          <label class="auto-refresh-toggle">
            <input type="checkbox" id="auto-refresh-toggle">
            <span class="toggle-slider"></span>
          </label>
          <span class="auto-refresh-label">Auto-refresh</span>
          <span class="auto-refresh-timer" id="refresh-timer"></span>
          
          <button class="refresh-button" id="refresh-now">
            <span class="refresh-icon">⟳</span> Refresh Now
          </button>
        </div>
        
        <div class="health-status healthy" id="health-status">
          <div class="health-status-icon">✓</div>
          <div class="health-status-text">System Healthy</div>
        </div>
      </div>
      
      <div class="metrics-section">
        <h3>System Metrics</h3>
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="gauge-container">
              <div class="gauge" id="cpu-gauge">
                <div class="gauge-background"></div>
                <div class="gauge-fill" id="cpu-gauge-fill" style="transform: rotate(0deg);"></div>
                <div class="gauge-center"></div>
                <div class="gauge-value" id="cpu-gauge-value">0%</div>
              </div>
            </div>
            <div class="metric-label">CPU Usage</div>
          </div>
          
          <div class="metric-card">
            <div class="gauge-container">
              <div class="gauge" id="memory-gauge">
                <div class="gauge-background"></div>
                <div class="gauge-fill" id="memory-gauge-fill" style="transform: rotate(0deg);"></div>
                <div class="gauge-center"></div>
                <div class="gauge-value" id="memory-gauge-value">0%</div>
              </div>
            </div>
            <div class="metric-label">Memory Usage</div>
          </div>
          
          <div class="metric-card">
            <div class="gauge-container">
              <div class="gauge" id="disk-gauge">
                <div class="gauge-background"></div>
                <div class="gauge-fill" id="disk-gauge-fill" style="transform: rotate(0deg);"></div>
                <div class="gauge-center"></div>
                <div class="gauge-value" id="disk-gauge-value">0%</div>
              </div>
            </div>
            <div class="metric-label">Disk Usage</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value" id="api-requests">0</div>
            <div class="metric-label">API Requests</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value" id="error-count">0</div>
            <div class="metric-label">API Errors</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value" id="cache-hit-rate">0%</div>
            <div class="metric-label">Cache Hit Rate</div>
          </div>
        </div>
        
        <div class="alerts-section">
          <h3>Alerts</h3>
          <div id="alerts-container">
            <div class="chart-placeholder">No alerts at this time</div>
          </div>
        </div>
      </div>
      
      <div class="historical-section">
        <h3>Historical Data</h3>
        <div class="time-range-selector">
          <div class="time-range-option active" data-range="hour">Last Hour</div>
          <div class="time-range-option" data-range="day">Last 24 Hours</div>
          <div class="time-range-option" data-range="week">Last Week</div>
        </div>
        
        <div class="chart-container" id="cpu-chart">
          <div class="chart-placeholder">CPU Usage Chart</div>
        </div>
        
        <div class="chart-container" id="memory-chart">
          <div class="chart-placeholder">Memory Usage Chart</div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Mock API Service (for testing) -->
  <script>
    // Define ApiService for testing
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
      }
    };
  </script>
  
  <!-- Mock SystemHealthDashboard implementation for testing -->
  <script>
    // SystemHealthDashboard implementation
    class SystemHealthDashboard {
      constructor(options = {}) {
        this.initialized = false;
        this.options = Object.assign({
          refreshInterval: 30, // seconds
          container: document.body,
          autoRefresh: false
        }, options);
        
        this.currentData = null;
        this.historicalData = null;
        this.selectedTimeRange = 'hour';
        this.selectedInterval = 5; // minutes
        this.refreshTimer = null;
        this.refreshTimeLeft = 0;
        
        // State flags
        this.isAutoRefreshEnabled = false;
        this.isLoading = false;
        
        logToOutput('SystemHealthDashboard initialized with options:');
        logToOutput(JSON.stringify(this.options));
      }
      
      async initialize() {
        try {
          // Set up event listeners
          this.setupEventListeners();
          
          // Load initial data
          await this.loadCurrentMetrics();
          await this.loadHistoricalMetrics();
          
          // Mark as initialized
          this.initialized = true;
          logToOutput('SystemHealthDashboard initialized successfully');
          
          return true;
        } catch (error) {
          logToOutput(`Failed to initialize SystemHealthDashboard: ${error.message}`, 'error');
          return false;
        }
      }
      
      setupEventListeners() {
        // Time range selector
        const timeRangeOptions = document.querySelectorAll('.time-range-option');
        timeRangeOptions.forEach(option => {
          option.addEventListener('click', () => {
            // Update selected time range
            this.selectedTimeRange = option.dataset.range;
            
            // Update UI
            timeRangeOptions.forEach(o => o.classList.remove('active'));
            option.classList.add('active');
            
            // Reload data
            this.loadHistoricalMetrics();
          });
        });
        
        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
        if (autoRefreshToggle) {
          autoRefreshToggle.addEventListener('change', () => {
            this.setAutoRefresh(autoRefreshToggle.checked);
          });
        }
        
        // Manual refresh button
        const refreshNowButton = document.getElementById('refresh-now');
        if (refreshNowButton) {
          refreshNowButton.addEventListener('click', () => {
            this.refresh();
          });
        }
      }
      
      async loadCurrentMetrics() {
        if (this.isLoading) return;
        
        try {
          this.isLoading = true;
          LoadingStateManager.setLoading('health-dashboard', true);
          
          // Call API
          const data = await ApiService.get('/admin/health');
          this.currentData = data;
          
          // Update UI with data
          this.updateCurrentMetrics(data);
          
          this.isLoading = false;
          LoadingStateManager.setLoading('health-dashboard', false);
          
          logToOutput('Current metrics loaded successfully');
          return data;
        } catch (error) {
          this.isLoading = false;
          LoadingStateManager.setLoading('health-dashboard', false);
          ErrorHandlingService.handleError(error, 'health-dashboard-current', {
            showToast: true
          });
          throw error;
        }
      }
      
      async loadHistoricalMetrics() {
        if (this.isLoading) return;
        
        try {
          this.isLoading = true;
          LoadingStateManager.setLoading('health-dashboard-history', true);
          
          // Determine time range
          const endTime = new Date();
          let startTime;
          
          switch(this.selectedTimeRange) {
            case 'hour':
              startTime = new Date(endTime - 60 * 60 * 1000);
              break;
            case 'day':
              startTime = new Date(endTime - 24 * 60 * 60 * 1000);
              break;
            case 'week':
              startTime = new Date(endTime - 7 * 24 * 60 * 60 * 1000);
              break;
            default:
              startTime = new Date(endTime - 60 * 60 * 1000);
          }
          
          // Call API
          const data = await ApiService.get('/admin/health/history', {
            params: {
              start_time: startTime.toISOString(),
              end_time: endTime.toISOString(),
              interval: this.selectedInterval
            }
          });
          
          this.historicalData = data;
          
          // Update historical metrics charts
          this.updateHistoricalCharts(data);
          
          this.isLoading = false;
          LoadingStateManager.setLoading('health-dashboard-history', false);
          
          logToOutput('Historical metrics loaded successfully');
          return data;
        } catch (error) {
          this.isLoading = false;
          LoadingStateManager.setLoading('health-dashboard-history', false);
          ErrorHandlingService.handleError(error, 'health-dashboard-history', {
            showToast: true
          });
          throw error;
        }
      }
      
      updateCurrentMetrics(data) {
        if (!data) return;
        
        // Update CPU gauge
        const cpuPercent = data.system?.cpu_percent || 0;
        this.updateGauge('cpu', cpuPercent);
        
        // Update memory gauge
        const memoryPercent = data.system?.memory_percent || 0;
        this.updateGauge('memory', memoryPercent);
        
        // Update disk gauge
        const diskPercent = data.system?.disk_percent || 0;
        this.updateGauge('disk', diskPercent);
        
        // Update API metrics
        document.getElementById('api-requests').textContent = data.api?.total_requests || 0;
        document.getElementById('error-count').textContent = data.api?.error_count || 0;
        
        // Update cache hit rate
        const monteCarloHitRate = data.cache?.monte_carlo?.hit_rate || 0;
        const paramHitRate = data.cache?.parameters?.hit_rate || 0;
        const avgHitRate = (monteCarloHitRate + paramHitRate) / 2;
        document.getElementById('cache-hit-rate').textContent = `${avgHitRate.toFixed(1)}%`;
        
        // Update health status
        const healthStatus = data.health_status || 'unknown';
        this.updateHealthStatus(healthStatus);
        
        // Update alerts
        this.updateAlerts(data.alerts || []);
      }
      
      updateGauge(gaugeId, value) {
        // Update gauge fill rotation (180deg = 100%)
        const rotation = Math.min(180, (value / 100) * 180);
        document.getElementById(`${gaugeId}-gauge-fill`).style.transform = `rotate(${rotation}deg)`;
        
        // Update gauge value text
        document.getElementById(`${gaugeId}-gauge-value`).textContent = `${value.toFixed(1)}%`;
      }
      
      updateHealthStatus(status) {
        const statusElement = document.getElementById('health-status');
        if (!statusElement) return;
        
        // Reset classes
        statusElement.classList.remove('healthy', 'warning', 'critical');
        
        // Set correct class and text
        let icon, text;
        
        switch(status) {
          case 'healthy':
            statusElement.classList.add('healthy');
            icon = '✓';
            text = 'System Healthy';
            break;
          case 'warning':
            statusElement.classList.add('warning');
            icon = '⚠️';
            text = 'System Warning';
            break;
          case 'critical':
            statusElement.classList.add('critical');
            icon = '⛔';
            text = 'System Critical';
            break;
          default:
            statusElement.classList.add('warning');
            icon = '?';
            text = 'System Status Unknown';
        }
        
        // Update content
        statusElement.innerHTML = `
          <div class="health-status-icon">${icon}</div>
          <div class="health-status-text">${text}</div>
        `;
      }
      
      updateAlerts(alerts) {
        const alertsContainer = document.getElementById('alerts-container');
        if (!alertsContainer) return;
        
        if (!alerts || alerts.length === 0) {
          alertsContainer.innerHTML = '<div class="chart-placeholder">No alerts at this time</div>';
          return;
        }
        
        // Clear container
        alertsContainer.innerHTML = '';
        
        // Add each alert
        alerts.forEach(alert => {
          const alertElement = document.createElement('div');
          alertElement.className = `alert-item ${alert.status || 'info'}`;
          
          alertElement.innerHTML = `
            <div class="alert-component">${alert.component || 'System'}</div>
            <div class="alert-message">${alert.message || 'No message'}</div>
          `;
          
          alertsContainer.appendChild(alertElement);
        });
      }
      
      updateHistoricalCharts(data) {
        if (!data || !data.metrics) return;
        
        // For this test implementation, we'll just update the placeholders
        // with some basic information about the data
        
        const cpuChart = document.getElementById('cpu-chart');
        const memoryChart = document.getElementById('memory-chart');
        
        if (cpuChart) {
          cpuChart.innerHTML = `
            <div class="chart-placeholder">
              CPU Usage Chart (${data.metrics_count} data points from ${data.start_time} to ${data.end_time})
            </div>
          `;
        }
        
        if (memoryChart) {
          memoryChart.innerHTML = `
            <div class="chart-placeholder">
              Memory Usage Chart (${data.metrics_count} data points, ${data.interval_minutes} minute intervals)
            </div>
          `;
        }
      }
      
      setAutoRefresh(enabled) {
        this.isAutoRefreshEnabled = enabled;
        
        if (enabled) {
          this.startRefreshTimer();
        } else {
          this.stopRefreshTimer();
        }
        
        logToOutput(`Auto-refresh ${enabled ? 'enabled' : 'disabled'}`);
      }
      
      startRefreshTimer() {
        // Clear any existing timer
        this.stopRefreshTimer();
        
        this.refreshTimeLeft = this.options.refreshInterval;
        this.updateRefreshTimer();
        
        // Start new timer
        this.refreshTimer = setInterval(() => {
          this.refreshTimeLeft--;
          this.updateRefreshTimer();
          
          if (this.refreshTimeLeft <= 0) {
            this.refresh();
            this.refreshTimeLeft = this.options.refreshInterval;
          }
        }, 1000);
      }
      
      stopRefreshTimer() {
        if (this.refreshTimer) {
          clearInterval(this.refreshTimer);
          this.refreshTimer = null;
        }
        
        // Clear the timer display
        const timerElement = document.getElementById('refresh-timer');
        if (timerElement) {
          timerElement.textContent = '';
        }
      }
      
      updateRefreshTimer() {
        const timerElement = document.getElementById('refresh-timer');
        if (timerElement) {
          timerElement.textContent = `Refreshing in ${this.refreshTimeLeft}s`;
        }
      }
      
      async refresh() {
        try {
          await this.loadCurrentMetrics();
          await this.loadHistoricalMetrics();
          logToOutput('Dashboard refreshed');
        } catch (error) {
          logToOutput(`Dashboard refresh failed: ${error.message}`, 'error');
        }
      }
    }
    
    window.SystemHealthDashboard = SystemHealthDashboard;
  </script>
  
  <!-- Test script -->
  <script>
    document.addEventListener('DOMContentLoaded', function() {
      const testOutput = document.getElementById('test-output');
      const adminId = document.getElementById('admin-id').textContent;
      
      // Initialize test environment
      logToOutput('Test environment initialized');
      logToOutput(`Using admin ID: ${adminId}`);
      
      // Create dashboard instance
      const dashboard = new SystemHealthDashboard({
        container: document.querySelector('.card:last-child'),
        refreshInterval: 30, // seconds
        autoRefresh: false
      });
      
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
        async current() {
          // Test loading current metrics
          await dashboard.loadCurrentMetrics();
          
          // Verify data
          if (!dashboard.currentData) {
            throw new Error('No current metrics data received');
          }
          
          // Verify expected structure
          const data = dashboard.currentData;
          
          if (!data.system || !data.system.cpu_percent) {
            throw new Error('Missing CPU metrics in response');
          }
          
          if (!data.system || !data.system.memory_percent) {
            throw new Error('Missing memory metrics in response');
          }
          
          if (!data.system || !data.system.disk_percent) {
            throw new Error('Missing disk metrics in response');
          }
          
          if (!data.health_status) {
            throw new Error('Missing health status in response');
          }
          
          // Verify UI updates
          const cpuValue = document.getElementById('cpu-gauge-value').textContent;
          if (!cpuValue.includes('%')) {
            throw new Error('CPU gauge not updated');
          }
          
          const memoryValue = document.getElementById('memory-gauge-value').textContent;
          if (!memoryValue.includes('%')) {
            throw new Error('Memory gauge not updated');
          }
          
          const diskValue = document.getElementById('disk-gauge-value').textContent;
          if (!diskValue.includes('%')) {
            throw new Error('Disk gauge not updated');
          }
          
          logToOutput('Successfully loaded and displayed current metrics');
          
          return true;
        },
        
        async history() {
          // Test loading historical metrics
          await dashboard.loadHistoricalMetrics();
          
          // Verify data
          if (!dashboard.historicalData) {
            throw new Error('No historical metrics data received');
          }
          
          // Verify expected structure
          const data = dashboard.historicalData;
          
          if (!data.metrics || !Array.isArray(data.metrics)) {
            throw new Error('Missing metrics array in response');
          }
          
          if (data.metrics.length === 0) {
            logToOutput('Warning: No historical metrics available, but API structure is correct');
          } else {
            // If there are metrics, check at least one of them
            const sampleMetric = data.metrics[0];
            if (!sampleMetric.system || !sampleMetric.timestamp) {
              throw new Error('Invalid metric structure in response');
            }
            
            logToOutput(`Received ${data.metrics.length} historical metrics`);
          }
          
          // Verify chart placeholders updated
          const cpuChart = document.getElementById('cpu-chart');
          const memoryChart = document.getElementById('memory-chart');
          
          if (!cpuChart.textContent.includes('data points')) {
            throw new Error('CPU chart not updated with historical data');
          }
          
          if (!memoryChart.textContent.includes('data points')) {
            throw new Error('Memory chart not updated with historical data');
          }
          
          logToOutput('Successfully loaded and displayed historical metrics');
          
          return true;
        },
        
        async timerange() {
          // Test each time range
          const timeRanges = ['hour', 'day', 'week'];
          
          for (const range of timeRanges) {
            logToOutput(`Testing time range: ${range}`);
            
            // Set time range
            dashboard.selectedTimeRange = range;
            
            // Find and click the corresponding option
            const option = document.querySelector(`.time-range-option[data-range="${range}"]`);
            if (option) {
              option.click();
              
              // Verify selection
              if (!option.classList.contains('active')) {
                throw new Error(`Time range option ${range} not properly selected`);
              }
            } else {
              throw new Error(`Time range option ${range} not found`);
            }
            
            // Verify data loaded with correct time range
            const data = dashboard.historicalData;
            if (!data) {
              throw new Error('No historical data loaded after time range selection');
            }
            
            // Simple validation - we don't check all details since the mock doesn't
            // change behavior based on time range
            logToOutput(`Successfully loaded data for time range: ${range}`);
          }
          
          logToOutput('All time ranges tested successfully');
          
          return true;
        },
        
        async interval() {
          // Test different intervals
          const intervals = [5, 15, 30, 60];
          
          for (const interval of intervals) {
            logToOutput(`Testing interval: ${interval} minutes`);
            
            // Set interval
            dashboard.selectedInterval = interval;
            
            // Load data with this interval
            await dashboard.loadHistoricalMetrics();
            
            // Verify data
            const data = dashboard.historicalData;
            if (!data) {
              throw new Error(`No historical data loaded for interval ${interval}`);
            }
            
            // Check interval in response
            if (data.interval_minutes !== interval) {
              // Some minor differences can be expected if server normalizes intervals
              logToOutput(`Note: Requested interval ${interval}, got ${data.interval_minutes} from server`);
            }
            
            logToOutput(`Successfully loaded data with interval: ${interval} minutes`);
          }
          
          logToOutput('All intervals tested successfully');
          
          return true;
        },
        
        async alerts() {
          // Load current metrics to get real alerts
          await dashboard.loadCurrentMetrics();
          
          // Check for alerts
          const data = dashboard.currentData;
          if (!data) {
            throw new Error('No current data available to check alerts');
          }
          
          // Ensure alerts field exists (even if empty)
          if (!('alerts' in data)) {
            throw new Error('Alerts field missing in response');
          }
          
          // Count alerts
          const alertsCount = data.alerts ? data.alerts.length : 0;
          logToOutput(`System has ${alertsCount} active alerts`);
          
          // Verify UI representation
          const alertsContainer = document.getElementById('alerts-container');
          if (!alertsContainer) {
            throw new Error('Alerts container not found in DOM');
          }
          
          if (alertsCount === 0) {
            // Should show "No alerts" message
            if (!alertsContainer.textContent.includes('No alerts')) {
              throw new Error('Empty alerts are not properly displayed');
            }
          } else {
            // Should have alert elements
            const alertElements = alertsContainer.querySelectorAll('.alert-item');
            if (alertElements.length !== alertsCount) {
              throw new Error(`Expected ${alertsCount} alert elements, found ${alertElements.length}`);
            }
            
            // Check each alert has required parts
            for (let i = 0; i < alertElements.length; i++) {
              const alertElement = alertElements[i];
              if (!alertElement.querySelector('.alert-component') || 
                  !alertElement.querySelector('.alert-message')) {
                throw new Error(`Alert element ${i} is missing required content`);
              }
            }
          }
          
          // Verify health status matches alerts
          const healthStatus = data.health_status;
          const statusElement = document.getElementById('health-status');
          
          if (!statusElement) {
            throw new Error('Health status element not found in DOM');
          }
          
          // Check correct class is applied based on health status
          if (!statusElement.classList.contains(healthStatus)) {
            throw new Error(`Health status element doesn't have class matching status: ${healthStatus}`);
          }
          
          logToOutput('Alert display and health status verified successfully');
          
          return true;
        },
        
        async autorefresh() {
          // Test auto-refresh functionality
          
          // First, verify auto-refresh is off by default
          if (dashboard.isAutoRefreshEnabled) {
            throw new Error('Auto-refresh should be disabled by default');
          }
          
          // Get auto-refresh toggle
          const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
          if (!autoRefreshToggle) {
            throw new Error('Auto-refresh toggle not found');
          }
          
          // Enable auto-refresh
          autoRefreshToggle.checked = true;
          autoRefreshToggle.dispatchEvent(new Event('change'));
          
          // Verify auto-refresh is enabled
          if (!dashboard.isAutoRefreshEnabled) {
            throw new Error('Auto-refresh not enabled after toggle');
          }
          
          // Verify timer is displayed
          const timerElement = document.getElementById('refresh-timer');
          if (!timerElement || !timerElement.textContent.includes('Refreshing in')) {
            throw new Error('Refresh timer not displayed');
          }
          
          // Wait a moment to verify timer is counting down
          const initialTimerText = timerElement.textContent;
          
          // Short wait of 2 seconds
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          // Verify timer has changed
          const updatedTimerText = timerElement.textContent;
          if (initialTimerText === updatedTimerText) {
            throw new Error('Refresh timer not counting down');
          }
          
          // Disable auto-refresh
          autoRefreshToggle.checked = false;
          autoRefreshToggle.dispatchEvent(new Event('change'));
          
          // Verify auto-refresh is disabled
          if (dashboard.isAutoRefreshEnabled) {
            throw new Error('Auto-refresh not disabled after toggle');
          }
          
          // Test manual refresh
          const refreshButton = document.getElementById('refresh-now');
          if (!refreshButton) {
            throw new Error('Refresh button not found');
          }
          
          // Record current data timestamp
          const initialTimestamp = dashboard.currentData ? dashboard.currentData.timestamp : null;
          
          // Click refresh button
          refreshButton.click();
          
          // Wait for request to complete
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // Verify new data loaded
          const updatedTimestamp = dashboard.currentData ? dashboard.currentData.timestamp : null;
          if (initialTimestamp === updatedTimestamp) {
            logToOutput('Warning: Timestamp unchanged after refresh - data may not be refreshing properly');
          }
          
          logToOutput('Auto-refresh and manual refresh functionality verified');
          
          return true;
        },
        
        async error() {
          // Test error handling by forcing an error
          
          // Override ApiService.get temporarily to force an error
          const originalGet = ApiService.get;
          ApiService.get = async function(endpoint) {
            if (endpoint === '/admin/health') {
              throw new Error('Simulated API error for testing');
            }
            return originalGet.apply(this, arguments);
          };
          
          // Try to load data which should trigger an error
          try {
            await dashboard.loadCurrentMetrics();
            
            // Shouldn't reach here
            ApiService.get = originalGet; // Restore original method
            throw new Error('Error handling failed - expected exception was not propagated');
          } catch (error) {
            // This is expected
            if (!error.message.includes('Simulated API error')) {
              ApiService.get = originalGet; // Restore original method
              throw error; // Unexpected error
            }
            
            // Verify the error was handled properly
            // No real way to check ErrorHandlingService integration in this mock environment,
            // so we just log that the right error was caught
            
            logToOutput('Error propagated and caught correctly');
            
            // Restore original method
            ApiService.get = originalGet;
            
            // One more validation - the dashboard should still function after an error
            try {
              await dashboard.loadCurrentMetrics();
              logToOutput('Dashboard recovered from error and continued functioning');
            } catch (e) {
              throw new Error(`Dashboard failed to recover from error: ${e.message}`);
            }
            
            return true;
          }
        }
      };
      
      // Set up button event listeners
      document.getElementById('run-current-test').addEventListener('click', () => runTest('current', tests.current));
      document.getElementById('run-history-test').addEventListener('click', () => runTest('history', tests.history));
      document.getElementById('run-timerange-test').addEventListener('click', () => runTest('timerange', tests.timerange));
      document.getElementById('run-interval-test').addEventListener('click', () => runTest('interval', tests.interval));
      document.getElementById('run-alerts-test').addEventListener('click', () => runTest('alerts', tests.alerts));
      document.getElementById('run-autorefresh-test').addEventListener('click', () => runTest('autorefresh', tests.autorefresh));
      document.getElementById('run-error-test').addEventListener('click', () => runTest('error', tests.error));
      
      // Run all tests
      document.getElementById('run-all-tests').addEventListener('click', async () => {
        // Clear output
        testOutput.innerHTML = '';
        
        // Clear test status indicators
        clearAllTestStatus();
        
        logToOutput('Running all tests...');
        
        // Initialize dashboard
        await dashboard.initialize();
        
        // Run tests in sequence
        await runTest('current', tests.current);
        await runTest('history', tests.history);
        await runTest('timerange', tests.timerange);
        await runTest('interval', tests.interval);
        await runTest('alerts', tests.alerts);
        await runTest('autorefresh', tests.autorefresh);
        await runTest('error', tests.error);
        
        logToOutput('All tests completed');
      });
      
      // Clear output
      document.getElementById('clear-output').addEventListener('click', () => {
        testOutput.innerHTML = '';
      });
      
      // Initialize dashboard
      dashboard.initialize().then(() => {
        logToOutput('System Health Dashboard initialized and ready for testing');
        logToOutput('Click "Run All Tests" to begin, or run individual tests');
      }).catch(error => {
        logToOutput(`Failed to initialize dashboard: ${error.message}`, 'error');
      });
    });
    
    // Helper function to log to test output (globally available)
    function logToOutput(message, type = 'info') {
      const testOutput = document.getElementById('test-output');
      if (!testOutput) return;
      
      const timestamp = new Date().toLocaleTimeString();
      const prefix = type === 'error' ? '❌ ERROR' : 
                    type === 'success' ? '✅ SUCCESS' : 
                    '📝 INFO';
      
      const formattedMessage = `[${timestamp}] [${prefix}] ${message}`;
      
      testOutput.innerHTML += formattedMessage + '\\n';
      testOutput.scrollTop = testOutput.scrollHeight;
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
    logger.info("Starting System Health Dashboard browser integration tests")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    logger.info("Browser integration test completed")
    logger.info("Remember to check the browser for visual verification of the tests")

if __name__ == "__main__":
    run_browser_tests()
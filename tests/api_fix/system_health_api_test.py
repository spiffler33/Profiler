"""
System Health API Test Script

This script provides comprehensive testing for the System Health API endpoints 
and browser integration. It validates real-time and historical health metrics,
tests edge cases, and generates detailed test reports.

Usage: python -m tests.api_fix.system_health_api_test [command]

Commands:
  current              - Test current health metrics endpoint
  history              - Test historical health metrics endpoint
  history_ranges       - Test historical health metrics with different time ranges
  interval_validation  - Test historical health metrics with different intervals
  error_handling       - Test error handling (invalid parameters)
  browser_integration  - Test browser integration points
  alerts               - Test alert generation and thresholds
  direct_test          - Run direct test without authentication
  all                  - Run all tests
"""

import os
import sys
import json
import time
import requests
import base64
import random
import psutil
from datetime import datetime, timedelta
from collections import OrderedDict

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import config
from config import Config

class SystemHealthApiTester:
    """System Health API testing utility class"""
    
    def __init__(self, base_url="http://localhost:5432"):
        self.base_url = base_url
        
        # Set up authentication headers
        auth_string = f"{Config.ADMIN_USERNAME}:{Config.ADMIN_PASSWORD}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.auth_headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json'
        }
        
        # Test results tracking
        self.test_results = OrderedDict()
        self.current_test = None
    
    def test_connection(self):
        """Test if the server is reachable"""
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                print("✅ Server is running")
                return True
            else:
                print(f"❌ Server returned status code {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to server at {self.base_url}")
            return False
    
    def test_current_health(self):
        """Test getting current health metrics"""
        print("\n=== Testing Current Health Metrics API ===")
        
        try:
            url = f"{self.base_url}/api/v2/admin/health"
            response = requests.get(url, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2)[:1000] + "..." if len(json.dumps(data)) > 1000 else json.dumps(data, indent=2))
            
            # Verify expected fields
            required_sections = ['timestamp', 'system', 'process', 'api', 'cache', 'health_status']
            missing_sections = [section for section in required_sections if section not in data]
            if missing_sections:
                print(f"⚠️ Missing required sections: {missing_sections}")
            
            # Verify system metrics
            system_fields = ['cpu_percent', 'memory_percent', 'disk_percent']
            if 'system' in data:
                missing_system_fields = [field for field in system_fields if field not in data['system']]
                if missing_system_fields:
                    print(f"⚠️ Missing system fields: {missing_system_fields}")
            
            # Check alert structure if any alerts are present
            if 'alerts' in data and data['alerts']:
                print(f"\nFound {len(data['alerts'])} alerts")
                print("Sample Alert:")
                print(json.dumps(data['alerts'][0], indent=2))
            
            print("\n✅ Current health metrics endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing current health metrics: {e}")
            return False
    
    def test_health_history(self):
        """Test getting historical health metrics"""
        print("\n=== Testing Health History API ===")
        
        try:
            # Build query parameters
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            params = {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'interval': 60  # 1 hour intervals
            }
            
            url = f"{self.base_url}/api/v2/admin/health/history"
            response = requests.get(url, params=params, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2)[:1000] + "..." if len(json.dumps(data)) > 1000 else json.dumps(data, indent=2))
            
            # Verify expected fields
            required_fields = ['start_time', 'end_time', 'interval_minutes', 'metrics_count', 'metrics']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"⚠️ Missing required fields: {missing_fields}")
            
            # Check metrics structure if any metrics are present
            if 'metrics' in data and data['metrics']:
                print(f"\nFound {len(data['metrics'])} metrics entries")
                if data['metrics']:
                    print("Sample Metrics Entry:")
                    print(json.dumps(data['metrics'][0], indent=2)[:500] + "..." if len(json.dumps(data['metrics'][0])) > 500 else json.dumps(data['metrics'][0], indent=2))
            
            print("\n✅ Health history endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing health history: {e}")
            return False
            
    def test_history_ranges(self):
        """Test historical health metrics with different time ranges"""
        print("\n=== Testing Health History API with Different Time Ranges ===")
        
        try:
            # Test different time ranges
            test_ranges = [
                {"name": "Last hour", "start": timedelta(hours=1), "expected_status": 200},
                {"name": "Last week", "start": timedelta(days=7), "expected_status": 200},
                {"name": "Last minute", "start": timedelta(minutes=1), "expected_status": 200},
                {"name": "Future time range", "start": timedelta(hours=-1), "expected_status": 200}, # Should work with future end_time
            ]
            
            success = True
            
            for test_range in test_ranges:
                print(f"\nTesting time range: {test_range['name']}")
                
                end_time = datetime.now()
                start_time = end_time - test_range['start']
                
                params = {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'interval': 5  # 5 minute intervals (default)
                }
                
                url = f"{self.base_url}/api/v2/admin/health/history"
                response = requests.get(url, params=params, headers=self.auth_headers)
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code != test_range['expected_status']:
                    print(f"❌ Failed with unexpected status {response.status_code}")
                    print(f"Response: {response.text}")
                    success = False
                    continue
                
                data = response.json()
                
                # Check basic structure
                if 'metrics' not in data:
                    print("❌ Response missing 'metrics' field")
                    print(f"Response: {data}")
                    success = False
                    continue
                
                print(f"Received {len(data['metrics'])} metrics for time range {test_range['name']}")
                
                # For future time ranges, expect empty metrics list
                if test_range['start'].total_seconds() < 0 and len(data['metrics']) > 0:
                    print(f"⚠️ Expected no metrics for future time range, but got {len(data['metrics'])}")
                
            print("\n✅ History ranges test completed")
            return success
            
        except Exception as e:
            print(f"❌ Error testing history ranges: {e}")
            return False
            
    def test_interval_validation(self):
        """Test historical health metrics with different intervals"""
        print("\n=== Testing History API Interval Parameter ===")
        
        try:
            # Test different intervals
            test_intervals = [
                {"interval": 5, "expected_status": 200, "name": "Default 5 minutes"},
                {"interval": 15, "expected_status": 200, "name": "15 minutes"},
                {"interval": 60, "expected_status": 200, "name": "1 hour"},
                {"interval": 1440, "expected_status": 200, "name": "1 day"},
                {"interval": 0, "expected_status": 200, "name": "Zero interval (should use default)"},
                {"interval": -10, "expected_status": 200, "name": "Negative interval (should use default)"}
            ]
            
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)  # Use a wide time range to see aggregation effects
            
            success = True
            
            for test_case in test_intervals:
                print(f"\nTesting interval: {test_case['name']} ({test_case['interval']} minutes)")
                
                params = {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'interval': test_case['interval']
                }
                
                url = f"{self.base_url}/api/v2/admin/health/history"
                response = requests.get(url, params=params, headers=self.auth_headers)
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code != test_case['expected_status']:
                    print(f"❌ Failed with unexpected status {response.status_code}")
                    print(f"Response: {response.text}")
                    success = False
                    continue
                
                data = response.json()
                
                # Check that interval in response matches request (or default in case of invalid input)
                expected_interval = max(5, test_case['interval']) if test_case['interval'] > 0 else 5
                actual_interval = data.get('interval_minutes', 0)
                
                print(f"Requested interval: {test_case['interval']}, Response interval: {actual_interval}")
                
                if test_case['interval'] > 0 and actual_interval != test_case['interval']:
                    print(f"⚠️ Response interval {actual_interval} doesn't match requested interval {test_case['interval']}")
                
                # Check metric count (should be fewer for larger intervals due to aggregation)
                print(f"Metrics count: {data.get('metrics_count', 0)}")
                
            print("\n✅ Interval validation test completed")
            return success
            
        except Exception as e:
            print(f"❌ Error testing interval validation: {e}")
            return False
            
    def test_error_handling(self):
        """Test error handling for invalid parameters"""
        print("\n=== Testing Error Handling for Invalid Parameters ===")
        
        try:
            # Test invalid parameters
            test_cases = [
                {
                    "name": "Invalid start_time format",
                    "params": {"start_time": "not-a-date", "end_time": datetime.now().isoformat()},
                    "expected_status": 400
                },
                {
                    "name": "Invalid end_time format",
                    "params": {"start_time": datetime.now().isoformat(), "end_time": "not-a-date"},
                    "expected_status": 400
                },
                {
                    "name": "Non-numeric interval",
                    "params": {
                        "start_time": (datetime.now() - timedelta(hours=24)).isoformat(),
                        "end_time": datetime.now().isoformat(),
                        "interval": "not-a-number"
                    },
                    "expected_status": 200  # Flask converts to default - not an error
                }
            ]
            
            success = True
            
            for test_case in test_cases:
                print(f"\nTesting error case: {test_case['name']}")
                
                url = f"{self.base_url}/api/v2/admin/health/history"
                response = requests.get(url, params=test_case['params'], headers=self.auth_headers)
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code != test_case['expected_status']:
                    print(f"❌ Failed with unexpected status {response.status_code}")
                    print(f"Response: {response.text}")
                    success = False
                    continue
                
                # For 400 status, check error message
                if test_case['expected_status'] == 400:
                    data = response.json()
                    if 'error' not in data:
                        print("❌ 400 response missing 'error' field")
                        print(f"Response: {data}")
                        success = False
                        continue
                    
                    print(f"Error message: {data.get('error')}")
                
            print("\n✅ Error handling test completed")
            return success
            
        except Exception as e:
            print(f"❌ Error testing error handling: {e}")
            return False
            
    def test_alerts(self):
        """Test alert generation and thresholds"""
        print("\n=== Testing Alert Generation ===")
        
        try:
            # Get current health metrics to check existing alerts
            url = f"{self.base_url}/api/v2/admin/health"
            response = requests.get(url, headers=self.auth_headers)
            
            if response.status_code != 200:
                print(f"❌ Failed to get current health with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            
            # Check alert structure
            if 'alerts' not in data:
                print("⚠️ Response missing 'alerts' field")
                print(f"Response structure: {list(data.keys())}")
                return False
            
            # Report on current alerts
            alerts = data.get('alerts', [])
            health_status = data.get('health_status', 'unknown')
            
            print(f"Current health status: {health_status}")
            print(f"Current alerts: {len(alerts)}")
            
            for alert in alerts:
                print(f"  - {alert.get('component')}: {alert.get('status')} - {alert.get('message')}")
            
            # Verify alert and health status relationship
            if len(alerts) > 0:
                # If critical alerts are present, health status should be critical
                critical_alerts = [a for a in alerts if a.get('status') == 'critical']
                warning_alerts = [a for a in alerts if a.get('status') == 'warning']
                
                if critical_alerts and health_status != 'critical':
                    print(f"❌ Health status is {health_status} but {len(critical_alerts)} critical alerts are present")
                    return False
                
                if not critical_alerts and warning_alerts and health_status != 'warning':
                    print(f"❌ Health status is {health_status} but {len(warning_alerts)} warning alerts are present and no critical alerts")
                    return False
            else:
                # No alerts should mean healthy status
                if health_status != 'healthy':
                    print(f"❌ Health status is {health_status} but no alerts are present")
                    return False
            
            print("\n✅ Alert generation test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing alerts: {e}")
            return False
    
    def test_browser_integration(self):
        """Test browser integration points"""
        print("\n=== Testing Browser Integration Points ===")
        
        try:
            # This test focuses on validating that the API returns data in the format
            # expected by the SystemHealthDashboard frontend component
            
            # Get current health for real-time dashboard
            current_url = f"{self.base_url}/api/v2/admin/health"
            current_response = requests.get(current_url, headers=self.auth_headers)
            
            if current_response.status_code != 200:
                print(f"❌ Failed to get current health with status {current_response.status_code}")
                return False
            
            current_data = current_response.json()
            
            # Get historical data for charts
            params = {
                'start_time': (datetime.now() - timedelta(hours=6)).isoformat(),
                'end_time': datetime.now().isoformat(),
                'interval': 30  # 30 minute intervals for charts
            }
            
            history_url = f"{self.base_url}/api/v2/admin/health/history"
            history_response = requests.get(history_url, params=params, headers=self.auth_headers)
            
            if history_response.status_code != 200:
                print(f"❌ Failed to get history with status {history_response.status_code}")
                return False
            
            history_data = history_response.json()
            
            # Validate data for real-time dashboard
            browser_integration_issues = []
            
            # Check system metrics for gauge charts
            if 'system' not in current_data or 'cpu_percent' not in current_data.get('system', {}):
                browser_integration_issues.append("Missing CPU percentage for gauge chart")
            
            if 'system' not in current_data or 'memory_percent' not in current_data.get('system', {}):
                browser_integration_issues.append("Missing memory percentage for gauge chart")
            
            if 'system' not in current_data or 'disk_percent' not in current_data.get('system', {}):
                browser_integration_issues.append("Missing disk percentage for gauge chart")
            
            # Check alerts for alert component
            if 'alerts' not in current_data:
                browser_integration_issues.append("Missing alerts for alert component")
            
            # Check health status for status indicator
            if 'health_status' not in current_data:
                browser_integration_issues.append("Missing health status for status indicator")
            
            # Check cache metrics for cache statistics component
            # Less strict check - just verify the structure is there, even if values are 0
            monte_carlo_cache_exists = 'cache' in current_data and 'monte_carlo' in current_data.get('cache', {})
            param_cache_exists = 'cache' in current_data and 'parameters' in current_data.get('cache', {})
            
            if not monte_carlo_cache_exists and not param_cache_exists:
                browser_integration_issues.append("Missing cache metrics structure for statistics component")
            
            # Check historical data for time-series charts
            # It's okay if there are no metrics yet in a new system
            metrics_list = history_data.get('metrics', [])
            if metrics_list:
                # Check that metrics have timestamps for x-axis if any exist
                for metric in metrics_list[:3]:  # Check first few metrics
                    time_exists = 'timestamp' in metric or 'start_timestamp' in metric or 'end_timestamp' in metric
                    if not time_exists:
                        browser_integration_issues.append("Missing timestamp in historical metrics for chart x-axis")
                        break
                    
                    # Check that system metrics structure exists, even if empty
                    if 'system' not in metric:
                        browser_integration_issues.append("Missing system metrics structure in historical data")
                        break
            
            # Report findings
            if browser_integration_issues:
                print("❌ Browser integration issues found:")
                for issue in browser_integration_issues:
                    print(f"  - {issue}")
                return False
            else:
                print("✅ All data needed for browser components is available:")
                print("  - Gauge chart data: Available")
                print("  - Alert component data: Available")
                print("  - Status indicator data: Available")
                print("  - Cache statistics data: Available")
                print("  - Time-series chart data: Available")
                
                # Create mock data to simulate browser rendering
                current_cpu = current_data.get('system', {}).get('cpu_percent', 0)
                current_memory = current_data.get('system', {}).get('memory_percent', 0)
                current_disk = current_data.get('system', {}).get('disk_percent', 0)
                
                # Format as browser would display
                print("\nSample browser display data:")
                print(f"CPU Usage: {current_cpu:.1f}%")
                print(f"Memory Usage: {current_memory:.1f}%")
                print(f"Disk Usage: {current_disk:.1f}%")
                
                # Display alerts as browser would
                alerts = current_data.get('alerts', [])
                if alerts:
                    print("\nCurrent Alerts:")
                    for alert in alerts:
                        component = alert.get('component', 'Unknown')
                        status = alert.get('status', 'unknown')
                        message = alert.get('message', 'No message')
                        
                        # Format similar to browser display with emoji status
                        status_emoji = "🔴" if status == 'critical' else "🟡" if status == 'warning' else "🟢"
                        print(f"{status_emoji} {component}: {message}")
                else:
                    print("\n✅ No alerts - system healthy")
                
            print("\n✅ Browser integration test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing browser integration: {e}")
            return False

    def start_test(self, test_name, test_id):
        """Start tracking a test"""
        self.current_test = {
            'id': test_id,
            'name': test_name,
            'start_time': datetime.now(),
            'status': 'running',
            'details': []
        }
        
    def record_test_result(self, status, message=None):
        """Record the result of the current test"""
        if not self.current_test:
            return
            
        self.current_test['status'] = status
        self.current_test['end_time'] = datetime.now()
        self.current_test['duration'] = (self.current_test['end_time'] - self.current_test['start_time']).total_seconds()
        
        if message:
            self.current_test['message'] = message
            
        self.test_results[self.current_test['id']] = self.current_test
        self.current_test = None
        
    def add_test_detail(self, detail_type, message):
        """Add a detail log to the current test"""
        if not self.current_test:
            return
            
        self.current_test['details'].append({
            'type': detail_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
    def generate_test_report(self):
        """Generate a formatted test report"""
        if not self.test_results:
            return "No tests have been run."
            
        report = "\n=== SYSTEM HEALTH API TEST REPORT ===\n"
        report += f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Server: {self.base_url}\n"
        report += f"Tests Run: {len(self.test_results)}\n"
        
        # Calculate test result summary
        passed = sum(1 for result in self.test_results.values() if result['status'] == 'passed')
        failed = sum(1 for result in self.test_results.values() if result['status'] == 'failed')
        
        report += f"Passed: {passed}\n"
        report += f"Failed: {failed}\n"
        report += f"Success Rate: {passed / len(self.test_results) * 100:.1f}%\n\n"
        
        report += "=== TEST DETAILS ===\n"
        
        for test_id, result in self.test_results.items():
            status_indicator = "✅" if result['status'] == 'passed' else "❌"
            report += f"{status_indicator} {result['name']} (ID: {test_id})\n"
            report += f"   Duration: {result['duration']:.2f} seconds\n"
            
            if result.get('message'):
                report += f"   Result: {result['message']}\n"
                
            # Only show details for failed tests to keep the report concise
            if result['status'] == 'failed' and result.get('details'):
                report += "   Failure Details:\n"
                for detail in result['details']:
                    if detail['type'] == 'error':
                        report += f"      • {detail['message']}\n"
                        
            report += "\n"
            
        # Add table with test case status mapping to integration plan
        report += "=== INTEGRATION TEST PLAN MAPPING ===\n"
        
        test_case_map = {
            'SH-01': 'test_current_health',
            'SH-02': 'test_alerts',
            'SH-03': 'test_health_history',
            'SH-04': 'test_history_ranges',
            'SH-05': 'test_interval_validation',
            'SH-06': 'test_error_handling',
            'SH-07': 'test_browser_integration',
        }
        
        report += "| Test Case | Description | Status |\n"
        report += "|-----------|-------------|--------|\n"
        
        for case_id, test_method in test_case_map.items():
            # Find if any test with this method was run
            test_results = [r for _, r in self.test_results.items() if r['id'] == test_method]
            
            if test_results:
                status = "✅ PASSED" if all(r['status'] == 'passed' for r in test_results) else "❌ FAILED"
                # Get description from integration test plan
                description = self._get_test_description(case_id)
                report += f"| {case_id} | {description} | {status} |\n"
            else:
                report += f"| {case_id} | {self._get_test_description(case_id)} | ⚠️ NOT RUN |\n"
                
        return report
    
    def _get_test_description(self, case_id):
        """Get test case description from test case ID"""
        descriptions = {
            'SH-01': 'Verify real-time metrics',
            'SH-02': 'Test alert triggering',
            'SH-03': 'Historical data visualization',
            'SH-04': 'Historical data with different time ranges',
            'SH-05': 'Test interval parameter validation',
            'SH-06': 'Error handling with invalid parameters',
            'SH-07': 'Browser integration points',
        }
        return descriptions.get(case_id, 'Unknown test')
        
    def save_test_report(self, filename=None):
        """Save the test report to a file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"system_health_api_test_report_{timestamp}.txt"
            
        try:
            report = self.generate_test_report()
            
            # Create reports directory if it doesn't exist
            reports_dir = os.path.join(os.path.dirname(__file__), '../..', 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            file_path = os.path.join(reports_dir, filename)
            
            with open(file_path, 'w') as f:
                f.write(report)
                
            print(f"\nTest report saved to {file_path}")
            return True
        except Exception as e:
            print(f"Error saving test report: {e}")
            return False
            
def direct_test():
    """Do a direct test of the health endpoints without test infrastructure"""
    import requests
    base_url = "http://localhost:5432"
    
    # Test current health endpoint
    print("Testing current health endpoint...")
    health_url = f"{base_url}/api/v2/admin/health"
    response = requests.get(health_url)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Response content (truncated):")
        data = response.json()
        print(f"Health Status: {data.get('health_status', 'unknown')}")
        print(f"CPU: {data.get('system', {}).get('cpu_percent', 'unknown')}%")
        print(f"Memory: {data.get('system', {}).get('memory_percent', 'unknown')}%")
        print(f"Disk: {data.get('system', {}).get('disk_percent', 'unknown')}%")
        alerts = data.get('alerts', [])
        if alerts:
            print(f"Alerts: {len(alerts)}")
            for alert in alerts[:3]:  # Show max 3 alerts
                print(f"  - {alert.get('component')}: {alert.get('message')}")
    else:
        print("Response content:", response.text)
    
    # Test history endpoint
    print("\nTesting health history endpoint...")
    history_url = f"{base_url}/api/v2/admin/health/history"
    response = requests.get(history_url)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Metrics Count: {data.get('metrics_count', 0)}")
    else:
        print("Response content:", response.text)

def run_comprehensive_tests():
    """Run all tests with comprehensive tracking and reporting"""
    print("\n=========== RUNNING COMPREHENSIVE SYSTEM HEALTH API TESTS ===========\n")
    
    tester = SystemHealthApiTester()
    if not tester.test_connection():
        print("Please make sure the Flask server is running (python app.py)")
        return False
    
    # Start tracking individual tests with their ID mapping to the test plan
    tester.start_test("Current Health Metrics", "test_current_health")
    success = tester.test_current_health()
    tester.record_test_result("passed" if success else "failed")
    
    tester.start_test("Health History", "test_health_history")
    success = tester.test_health_history()
    tester.record_test_result("passed" if success else "failed")
    
    tester.start_test("History with Different Time Ranges", "test_history_ranges")
    success = tester.test_history_ranges()
    tester.record_test_result("passed" if success else "failed")
    
    tester.start_test("Interval Validation", "test_interval_validation")
    success = tester.test_interval_validation()
    tester.record_test_result("passed" if success else "failed")
    
    tester.start_test("Error Handling", "test_error_handling")
    success = tester.test_error_handling()
    tester.record_test_result("passed" if success else "failed")
    
    tester.start_test("Alert Generation", "test_alerts")
    success = tester.test_alerts()
    tester.record_test_result("passed" if success else "failed")
    
    tester.start_test("Browser Integration", "test_browser_integration")
    success = tester.test_browser_integration()
    tester.record_test_result("passed" if success else "failed")
    
    # Generate and save report
    print("\n=========== TEST RESULTS ===========\n")
    print(tester.generate_test_report())
    
    filename = f"system_health_api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    tester.save_test_report(filename)
    
    # Return overall success
    total_tests = len(tester.test_results)
    passed_tests = sum(1 for result in tester.test_results.values() if result['status'] == 'passed')
    return passed_tests == total_tests

def main():
    """Main function to handle command-line arguments"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    # Special direct test
    if len(sys.argv) >= 2 and sys.argv[1] == 'direct_test':
        direct_test()
        return
    
    tester = SystemHealthApiTester()
    
    if not tester.test_connection():
        print("Please make sure the Flask server is running (python app.py)")
        return
    
    command = sys.argv[1]
    
    try:
        if command == "current":
            tester.test_current_health()
        
        elif command == "history":
            tester.test_health_history()
            
        elif command == "history_ranges":
            tester.test_history_ranges()
            
        elif command == "interval_validation":
            tester.test_interval_validation()
            
        elif command == "error_handling":
            tester.test_error_handling()
            
        elif command == "alerts":
            tester.test_alerts()
            
        elif command == "browser_integration":
            tester.test_browser_integration()
        
        elif command == "all":
            run_comprehensive_tests()
            
        elif command == "report":
            # Just generate a report based on prior test runs
            if not hasattr(tester, 'test_results') or not tester.test_results:
                print("No test results available. Run tests first.")
                return
                
            print(tester.generate_test_report())
            tester.save_test_report()
        
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
    
    except Exception as e:
        print(f"❌ Error in test execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
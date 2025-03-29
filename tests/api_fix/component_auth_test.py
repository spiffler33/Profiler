"""
Component Authentication Integration Test

This script tests specific frontend components with authentication to verify they handle:
1. Authentication requirements properly
2. Authentication error states correctly
3. Session management within component context
4. Cross-component authentication state sharing

Usage: python -m tests.api_fix.component_auth_test [options]

Options:
  --browser    - Browser to use (chrome, firefox, safari) [default: safari]
  --headless   - Run in headless mode (not applicable for Safari)
  --url        - Base URL for testing [default: http://localhost:5432]

Components tested:
  - Admin Dashboard (Health, Cache, Parameters)
  - Goal Management with authentication
  - Parameter Management with authentication
  - Profile Management with authentication
"""

import os
import sys
import json
import time
import base64
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from selenium.webdriver.common.keys import Keys
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not available. Please install with: pip install selenium")
    class MockClass:
        def __init__(self, *args, **kwargs):
            pass
    By = type('MockBy', (), {'ID': 'id', 'CSS_SELECTOR': 'css', 'XPATH': 'xpath', 'TAG_NAME': 'tag'})
    webdriver = type('MockWebdriver', (), {'Chrome': MockClass, 'Firefox': MockClass, 'Safari': MockClass})
    WebDriverWait = MockClass
    TimeoutException = Exception
    NoSuchElementException = Exception
    Keys = type('MockKeys', (), {'RETURN': '\n', 'ESCAPE': '\x1b'})
    EC = type('MockEC', (), {
        'visibility_of_element_located': lambda x: x,
        'presence_of_element_located': lambda x: x
    })

# Import config
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='component_auth_test.log'
)
logger = logging.getLogger('component_auth_test')

# Test results storage
TEST_RESULTS = {
    "dashboard": {"total": 0, "passed": 0, "failed": 0, "tests": []},
    "goals": {"total": 0, "passed": 0, "failed": 0, "tests": []},
    "parameters": {"total": 0, "passed": 0, "failed": 0, "tests": []},
    "profiles": {"total": 0, "passed": 0, "failed": 0, "tests": []}
}

def record_test_result(category: str, test_id: str, test_name: str, passed: bool, error: Optional[str] = None) -> None:
    """Record test result for reporting"""
    TEST_RESULTS[category]["total"] += 1
    if passed:
        TEST_RESULTS[category]["passed"] += 1
    else:
        TEST_RESULTS[category]["failed"] += 1

    result = "PASS" if passed else "FAIL"

    TEST_RESULTS[category]["tests"].append({
        "id": test_id,
        "name": test_name,
        "result": result,
        "error": error if error else None
    })

def generate_report() -> str:
    """Generate a test report"""
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": sum(TEST_RESULTS[c]["total"] for c in TEST_RESULTS),
            "passed": sum(TEST_RESULTS[c]["passed"] for c in TEST_RESULTS),
            "failed": sum(TEST_RESULTS[c]["failed"] for c in TEST_RESULTS)
        },
        "categories": TEST_RESULTS
    }

    # Calculate pass percentage
    total = report_data["summary"]["total_tests"]
    if total > 0:
        report_data["summary"]["pass_percentage"] = round(report_data["summary"]["passed"] / total * 100, 1)
    else:
        report_data["summary"]["pass_percentage"] = 0

    # Create reports directory if it doesn't exist
    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../reports'))
    os.makedirs(reports_dir, exist_ok=True)

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save report to file
    report_file = os.path.join(reports_dir, f"component_auth_test_report_{timestamp}.txt")

    with open(report_file, 'w') as f:
        f.write(f"# Component Authentication Integration Test Report\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write(f"## Summary\n\n")
        f.write(f"Total Tests: {report_data['summary']['total_tests']}\n")
        f.write(f"Passed: {report_data['summary']['passed']}\n")
        f.write(f"Failed: {report_data['summary']['failed']}\n")
        f.write(f"Pass Percentage: {report_data['summary']['pass_percentage']}%\n\n")

        for category, results in TEST_RESULTS.items():
            if results["total"] > 0:
                passed = results["passed"]
                failed = results["failed"]

                f.write(f"## {category.capitalize()} Component Tests\n\n")
                f.write(f"Tests: {results['total']}, Passed: {passed}, Failed: {failed}\n\n")

                f.write("| Test ID | Test Name | Result | Error |\n")
                f.write("|---------|-----------|--------|-------|\n")

                for test in results["tests"]:
                    error = test["error"] if test["error"] else ""
                    f.write(f"| {test['id']} | {test['name']} | {test['result']} | {error} |\n")

                f.write("\n")

    logger.info(f"Test report saved to: {report_file}")
    return report_file


class ComponentAuthTest:
    """Base class for component authentication integration tests"""

    def __init__(self, browser_type="chrome", headless=True, base_url="http://localhost:5432"):
        self.browser_type = browser_type
        self.headless = headless
        self.base_url = base_url
        self.driver = None
        self.admin_credentials = {
            'username': Config.ADMIN_USERNAME,
            'password': Config.ADMIN_PASSWORD
        }

    def setup(self):
        """Set up WebDriver"""
        try:
            # Initialize the appropriate WebDriver
            if self.browser_type == "chrome":
                options = webdriver.ChromeOptions()
                if self.headless:
                    options.add_argument("--headless")
                self.driver = webdriver.Chrome(options=options)
            elif self.browser_type == "firefox":
                options = webdriver.FirefoxOptions()
                if self.headless:
                    options.add_argument("--headless")
                self.driver = webdriver.Firefox(options=options)
            elif self.browser_type == "safari":
                # Safari does not support headless mode
                self.driver = webdriver.Safari()
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")

            # Set window size
            self.driver.set_window_size(1366, 768)
            logger.info(f"Browser session started using: {self.browser_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            return False

    def teardown(self):
        """Clean up resources"""
        if self.driver:
            # Clear all local storage to reset state
            try:
                self.driver.execute_script("localStorage.clear();")
                self.driver.execute_script("sessionStorage.clear();")
            except:
                pass
            
            self.driver.quit()
            logger.info("Browser session ended")

    def navigate_to(self, path):
        """Navigate to a specific page"""
        url = f"{self.base_url}{path}"
        logger.info(f"Navigating to: {url}")
        self.driver.get(url)
        return url

    def wait_for_element(self, by, value, timeout=10, condition="visibility"):
        """Wait for an element to be visible or present"""
        try:
            if condition == "visibility":
                wait_condition = EC.visibility_of_element_located((by, value))
            else:  # presence
                wait_condition = EC.presence_of_element_located((by, value))

            element = WebDriverWait(self.driver, timeout).until(wait_condition)
            return element
        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {by}={value}")
            return None

    def is_element_present(self, by, value):
        """Check if an element is present in the DOM"""
        try:
            self.driver.find_element(by, value)
            return True
        except NoSuchElementException:
            return False

    def take_screenshot(self, name):
        """Take a screenshot"""
        if not self.driver:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"component_auth_{name}_{timestamp}.png"

        # Create screenshots directory if it doesn't exist
        screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../reports/screenshots'))
        os.makedirs(screenshots_dir, exist_ok=True)

        file_path = os.path.join(screenshots_dir, filename)
        self.driver.save_screenshot(file_path)
        logger.info(f"Screenshot saved to: {file_path}")
        return file_path

    def login(self, username, password, remember_me=False):
        """Perform login through the UI"""
        # Navigate to login page
        self.navigate_to("/login")
        
        # Wait for login form to appear
        username_field = self.wait_for_element(By.ID, "username")
        password_field = self.wait_for_element(By.ID, "password")
        login_button = self.wait_for_element(By.ID, "login-button")
        
        if not all([username_field, password_field, login_button]):
            logger.error("Login form elements not found")
            return False
            
        # Fill in login form
        username_field.clear()
        username_field.send_keys(username)
        
        password_field.clear()
        password_field.send_keys(password)
        
        # Set remember me if requested
        if remember_me:
            remember_checkbox = self.wait_for_element(By.ID, "remember-me")
            if remember_checkbox and not remember_checkbox.is_selected():
                remember_checkbox.click()
                
        # Click login button
        login_button.click()
        
        # Wait for redirect or error
        time.sleep(2)
        
        # Check for login errors
        error_div = self.is_element_present(By.ID, "login-error")
        if error_div and self.driver.find_element(By.ID, "login-error").is_displayed():
            error_text = self.driver.find_element(By.ID, "login-error").text
            logger.warning(f"Login failed with error: {error_text}")
            return False
            
        # Check if we were redirected away from login page
        return "/login" not in self.driver.current_url
    
    def logout(self):
        """Perform logout through the UI"""
        try:
            # Find and click the logout link
            logout_link = self.wait_for_element(By.CSS_SELECTOR, ".logout-link")
            if logout_link:
                logout_link.click()
                time.sleep(1)
                return True
        except:
            logger.warning("Could not find logout link")
            
        return False
            
    def inject_auth_token(self, username, password):
        """Programmatically inject auth token into localStorage"""
        # Create the auth token (Base64 encoded username:password)
        auth_string = f"{username}:{password}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        # Set the auth token in localStorage
        script = f'localStorage.setItem("auth_token", "{encoded_auth}");'
        self.driver.execute_script(script)
        
        # Setting auth_token_expiry to 1 day from now (in ms since epoch)
        expiry = int(time.time() * 1000) + (24 * 60 * 60 * 1000)
        script = f'localStorage.setItem("auth_token_expiry", "{expiry}");'
        self.driver.execute_script(script)
        
        # Set minimal user data
        user_data = {
            "username": username,
            "roles": ["admin"]
        }
        user_json = json.dumps(user_data)
        script = f'localStorage.setItem("auth_user", JSON.stringify({json.dumps(user_data)}));'
        self.driver.execute_script(script)
        
        # Return success
        return True

    def invalidate_auth_token(self):
        """Invalidate the current auth token to simulate expiry"""
        # Set the expiry to a time in the past
        script = 'localStorage.setItem("auth_token_expiry", "1");'
        self.driver.execute_script(script)
        return True

    def run_all_tests(self):
        """Run all component authentication tests"""
        try:
            self.setup()
            
            # Admin Dashboard Tests
            self.test_dashboard_unauthenticated()
            self.test_dashboard_authenticated()
            self.test_dashboard_session_expired()
            
            # Goals Component Tests
            self.test_goals_auth_integration()
            self.test_goals_api_auth()
            
            # Parameters Component Tests
            self.test_parameters_auth_unauthenticated()
            self.test_parameters_auth_authenticated()
            
            # Profile Component Tests
            self.test_profile_auth_integration()
            
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
        finally:
            self.teardown()

    # DASHBOARD TESTS
    def test_dashboard_unauthenticated(self):
        """Test accessing dashboard without authentication"""
        test_id = "DASH-01"
        test_name = "Dashboard Access Unauthenticated"
        
        try:
            # Clear any auth data
            self.navigate_to("/")
            self.driver.execute_script("localStorage.clear(); sessionStorage.clear();")
            
            # Try to access admin dashboard
            self.navigate_to("/admin/health")
            
            # Check if we're redirected to login page
            dev_mode = getattr(Config, 'DEV_MODE', False)
            
            if dev_mode:
                # In dev mode, we should be able to access the dashboard without auth
                dashboard_loaded = self.is_element_present(By.CSS_SELECTOR, ".admin-content")
                passed = dashboard_loaded
                
                # Take screenshot
                self.take_screenshot("dashboard_dev_mode_access")
            else:
                # In production mode, we should be redirected to login
                on_login_page = "/login" in self.driver.current_url
                passed = on_login_page
                
                # Take screenshot
                self.take_screenshot("dashboard_auth_redirect")
            
            record_test_result("dashboard", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("dashboard", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_dashboard_authenticated(self):
        """Test accessing dashboard with authentication"""
        test_id = "DASH-02"
        test_name = "Dashboard Access Authenticated"
        
        try:
            # Login first
            self.navigate_to("/login")
            login_success = self.login(
                self.admin_credentials['username'], 
                self.admin_credentials['password']
            )
            
            if not login_success:
                # Try injecting token directly if UI login fails
                self.navigate_to("/")
                self.inject_auth_token(
                    self.admin_credentials['username'],
                    self.admin_credentials['password']
                )
                
            # Try to access admin dashboard
            self.navigate_to("/admin/health")
            
            # Check if dashboard loaded
            time.sleep(2)
            dashboard_loaded = self.is_element_present(By.CSS_SELECTOR, ".admin-content")
            
            # Check specific dashboard components
            status_indicators = self.is_element_present(By.CSS_SELECTOR, ".status-indicator")
            system_metrics = self.is_element_present(By.ID, "system-metrics")
            
            # Take screenshot
            self.take_screenshot("dashboard_authenticated_access")
            
            passed = dashboard_loaded and status_indicators and system_metrics
            
            record_test_result("dashboard", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("dashboard", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_dashboard_session_expired(self):
        """Test dashboard behavior when session expires"""
        test_id = "DASH-03"
        test_name = "Dashboard Session Expiry"
        
        try:
            # Login first
            self.navigate_to("/login")
            login_success = self.login(
                self.admin_credentials['username'], 
                self.admin_credentials['password']
            )
            
            if not login_success:
                # Try injecting token directly if UI login fails
                self.navigate_to("/")
                self.inject_auth_token(
                    self.admin_credentials['username'],
                    self.admin_credentials['password']
                )
                
            # Access admin dashboard
            self.navigate_to("/admin/health")
            
            # Verify we can access the dashboard
            dashboard_loaded = self.is_element_present(By.CSS_SELECTOR, ".admin-content")
            
            if not dashboard_loaded:
                record_test_result("dashboard", test_id, test_name, False, "Failed to load dashboard with auth")
                return False
                
            # Invalidate token to simulate session expiry
            self.invalidate_auth_token()
            
            # Trigger session check
            self.driver.execute_script("""
            if (window.AuthenticationService) {
                window.AuthenticationService.getTokenExpiry();
            }
            """)
            
            # Now try to make an API request from the dashboard (trigger refresh)
            self.driver.execute_script("""
            if (document.getElementById('refresh-health-data')) {
                document.getElementById('refresh-health-data').click();
            }
            """)
            
            # Wait for auth error handler
            time.sleep(2)
            
            # Check for session expired dialog or auth error container
            session_dialog = self.is_element_present(By.ID, "session-expiry-dialog")
            auth_error = self.is_element_present(By.ID, "auth-error-container")
            
            # Take screenshot
            self.take_screenshot("dashboard_session_expired")
            
            passed = session_dialog or auth_error
            
            record_test_result("dashboard", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("dashboard", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    # GOALS COMPONENT TESTS
    def test_goals_auth_integration(self):
        """Test goals component with authentication integration"""
        test_id = "GOALS-01"
        test_name = "Goals Auth Integration"
        
        try:
            # Login first
            self.navigate_to("/login")
            login_success = self.login(
                self.admin_credentials['username'], 
                self.admin_credentials['password']
            )
            
            if not login_success:
                # Try injecting token directly if UI login fails
                self.navigate_to("/")
                self.inject_auth_token(
                    self.admin_credentials['username'],
                    self.admin_credentials['password']
                )
                
            # Navigate to goals page
            self.navigate_to("/goals")
            
            # Check if goals page loaded without redirecting to login
            not_on_login = "/login" not in self.driver.current_url
            
            # More specific check to see if we have a goal-related content
            has_goal_content = (
                self.is_element_present(By.ID, "goals-container") or
                self.is_element_present(By.CSS_SELECTOR, ".goal-card") or
                self.is_element_present(By.ID, "goal-form")
            )
            
            # Take screenshot
            self.take_screenshot("goals_authenticated")
            
            passed = not_on_login and has_goal_content
            
            record_test_result("goals", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("goals", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_goals_api_auth(self):
        """Test goals component API auth handling"""
        test_id = "GOALS-02"
        test_name = "Goals API Auth Integration"
        
        try:
            # Login first
            self.navigate_to("/")
            self.inject_auth_token(
                self.admin_credentials['username'],
                self.admin_credentials['password']
            )
                
            # Navigate to goals page
            self.navigate_to("/goals")
            
            # Wait for page to load
            time.sleep(2)
            
            # Invalidate token to simulate session expiry
            self.invalidate_auth_token()
            
            # Try to trigger an API call (like submitting a form or expanding a goal)
            try:
                # Try to find and click expand buttons
                expand_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".goal-expand-button")
                if expand_buttons and len(expand_buttons) > 0:
                    expand_buttons[0].click()
                else:
                    # If no expand buttons, try to find and click action buttons
                    action_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".action-button, .btn-primary")
                    if action_buttons and len(action_buttons) > 0:
                        action_buttons[0].click()
            except:
                # If all else fails, execute a simple API request
                self.driver.execute_script("""
                fetch('/api/v2/goals', {
                    headers: {
                        'Authorization': 'Bearer ' + localStorage.getItem('auth_token')
                    }
                });
                """)
            
            # Wait for auth error handler
            time.sleep(2)
            
            # Check for session expired dialog or auth error container
            session_dialog = self.is_element_present(By.ID, "session-expiry-dialog")
            auth_error = self.is_element_present(By.ID, "auth-error-container")
            
            # Take screenshot
            self.take_screenshot("goals_session_expired")
            
            passed = session_dialog or auth_error
            
            record_test_result("goals", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("goals", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    # PARAMETERS COMPONENT TESTS
    def test_parameters_auth_unauthenticated(self):
        """Test parameter admin without authentication"""
        test_id = "PARAMS-01"
        test_name = "Parameters Access Unauthenticated"
        
        try:
            # Clear any auth data
            self.navigate_to("/")
            self.driver.execute_script("localStorage.clear(); sessionStorage.clear();")
            
            # Try to access parameter admin
            self.navigate_to("/admin/parameters")
            
            # Check if we're redirected to login page
            dev_mode = getattr(Config, 'DEV_MODE', False)
            
            if dev_mode:
                # In dev mode, we should be able to access the parameters page without auth
                params_loaded = self.is_element_present(By.ID, "parameter-list-container")
                passed = params_loaded
                
                # Take screenshot
                self.take_screenshot("parameters_dev_mode_access")
            else:
                # In production mode, we should be redirected to login
                on_login_page = "/login" in self.driver.current_url
                passed = on_login_page
                
                # Take screenshot
                self.take_screenshot("parameters_auth_redirect")
            
            record_test_result("parameters", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("parameters", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_parameters_auth_authenticated(self):
        """Test parameter admin with authentication"""
        test_id = "PARAMS-02"
        test_name = "Parameters Access Authenticated"
        
        try:
            # Login first
            self.navigate_to("/login")
            login_success = self.login(
                self.admin_credentials['username'], 
                self.admin_credentials['password']
            )
            
            if not login_success:
                # Try injecting token directly if UI login fails
                self.navigate_to("/")
                self.inject_auth_token(
                    self.admin_credentials['username'],
                    self.admin_credentials['password']
                )
                
            # Try to access parameter admin
            self.navigate_to("/admin/parameters")
            
            # Wait for parameters page to load
            time.sleep(2)
            
            # Check if parameters page loaded
            params_container = self.is_element_present(By.ID, "parameter-list-container")
            params_tree = self.is_element_present(By.ID, "parameter-tree-container")
            params_details = self.is_element_present(By.ID, "parameter-details-container")
            
            # Take screenshot
            self.take_screenshot("parameters_authenticated")
            
            passed = params_container and params_tree and params_details
            
            record_test_result("parameters", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("parameters", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    # PROFILE COMPONENT TESTS
    def test_profile_auth_integration(self):
        """Test profile component with authentication integration"""
        test_id = "PROFILE-01"
        test_name = "Profile Auth Integration"
        
        try:
            # Login first
            self.navigate_to("/login")
            login_success = self.login(
                self.admin_credentials['username'], 
                self.admin_credentials['password']
            )
            
            if not login_success:
                # Try injecting token directly if UI login fails
                self.navigate_to("/")
                self.inject_auth_token(
                    self.admin_credentials['username'],
                    self.admin_credentials['password']
                )
                
            # Navigate to profile page or creation
            self.navigate_to("/create_profile")
            
            # Check if profile page loaded without redirecting to login
            not_on_login = "/login" not in self.driver.current_url
            
            # More specific check for profile-related content
            has_profile_content = (
                self.is_element_present(By.ID, "profile-form") or
                self.is_element_present(By.CSS_SELECTOR, ".profile-container") or
                self.is_element_present(By.ID, "profile-wizard")
            )
            
            # Take screenshot
            self.take_screenshot("profile_authenticated")
            
            passed = not_on_login and has_profile_content
            
            record_test_result("profiles", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("profiles", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Component Authentication Integration Test')
    parser.add_argument('--browser', default='safari', choices=['chrome', 'firefox', 'safari'],
                        help='Browser to use for testing')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--url', default='http://localhost:5432', help='Base URL for testing')
    
    args = parser.parse_args()
    
    print("\n=== Component Authentication Integration Test ===\n")
    print(f"Browser: {args.browser}")
    if args.browser == 'safari' and args.headless:
        print("Note: Safari does not support headless mode. Ignoring --headless flag.")
        args.headless = False
    print(f"Headless mode: {'Yes' if args.headless else 'No'}")
    print(f"Base URL: {args.url}")
    
    # Check if Selenium is available
    if not SELENIUM_AVAILABLE:
        print("\n⚠️ ERROR: Selenium WebDriver is not available.")
        print("These tests require Selenium to run proper browser tests.")
        print("Install selenium package using: pip install selenium\n")
        return
    
    # Run tests
    test = ComponentAuthTest(args.browser, args.headless, args.url)
    test.run_all_tests()
    
    # Generate report
    report_file = generate_report()
    
    print("\n=== Component Authentication Integration Test Complete ===\n")

if __name__ == "__main__":
    main()
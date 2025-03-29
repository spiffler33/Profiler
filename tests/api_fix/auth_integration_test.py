"""
Authentication Integration Test

This script tests the authentication integration across frontend components. It verifies:
1. Authentication flow between components
2. Error handling for authentication failures
3. Session management across different views
4. Authentication integration with the API services

Usage: python -m tests.api_fix.auth_integration_test [options]

Options:
  --browser    - Browser to use (chrome, firefox, safari) [default: safari]
  --headless   - Run in headless mode (not applicable for Safari)
  --url        - Base URL for testing [default: http://localhost:5432]

Requirements:
  - Selenium WebDriver (for browser testing)
  - Running Flask server on port 5432
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
    filename='auth_integration_test.log'
)
logger = logging.getLogger('auth_integration_test')

# Test results storage
TEST_RESULTS = {
    "login": {"total": 0, "passed": 0, "failed": 0, "tests": []},
    "auth_errors": {"total": 0, "passed": 0, "failed": 0, "tests": []},
    "session": {"total": 0, "passed": 0, "failed": 0, "tests": []},
    "api": {"total": 0, "passed": 0, "failed": 0, "tests": []}
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
    report_file = os.path.join(reports_dir, f"auth_integration_test_report_{timestamp}.txt")

    with open(report_file, 'w') as f:
        f.write(f"# Authentication Integration Test Report\n\n")
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

                f.write(f"## {category.capitalize()} Tests\n\n")
                f.write(f"Tests: {results['total']}, Passed: {passed}, Failed: {failed}\n\n")

                f.write("| Test ID | Test Name | Result | Error |\n")
                f.write("|---------|-----------|--------|-------|\n")

                for test in results["tests"]:
                    error = test["error"] if test["error"] else ""
                    f.write(f"| {test['id']} | {test['name']} | {test['result']} | {error} |\n")

                f.write("\n")

    logger.info(f"Test report saved to: {report_file}")
    return report_file

class AuthIntegrationTest:
    """Base class for authentication integration tests"""

    def __init__(self, browser_type="chrome", headless=True, base_url="http://localhost:5432"):
        self.browser_type = browser_type
        self.headless = headless
        self.base_url = base_url
        self.driver = None
        self.admin_credentials = {
            'username': Config.ADMIN_USERNAME,
            'password': Config.ADMIN_PASSWORD
        }
        self.initial_location = None

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
            
            # Record initial location
            self.initial_location = self.driver.get_window_position()
            
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
        filename = f"auth_test_{name}_{timestamp}.png"

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
    
    def check_authenticated_state(self):
        """Check if the current UI shows we're authenticated"""
        try:
            login_link = self.driver.find_element(By.CSS_SELECTOR, ".login-link")
            logout_link = self.driver.find_element(By.CSS_SELECTOR, ".logout-link")
            
            # If login is hidden and logout is visible, we're authenticated
            return (not login_link.is_displayed()) and logout_link.is_displayed()
        except:
            logger.warning("Could not find auth state indicators in UI")
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
        
        # Return success
        return True
        
    def api_request(self, endpoint, method="GET", data=None, auth=True):
        """Make an API request using JavaScript fetch through the browser"""
        # Construct the fetch request
        url = f"{self.base_url}/api/v2{endpoint}"
        
        fetch_script = f"""
        async function makeRequest() {{
            try {{
                const response = await fetch("{url}", {{
                    method: "{method}",
                    headers: {{
                        "Content-Type": "application/json",
                        {'"Authorization": "Bearer " + localStorage.getItem("auth_token"),' if auth else ''}
                    }},
                    {f'body: JSON.stringify({json.dumps(data)}),' if data else ''}
                }});
                
                if (response.ok) {{
                    const contentType = response.headers.get("content-type");
                    if (contentType && contentType.includes("application/json")) {{
                        return await response.json();
                    }} else {{
                        return await response.text();
                    }}
                }} else {{
                    // Try to get JSON error response
                    try {{
                        const errorJson = await response.json();
                        return {{ 
                            __error__: true, 
                            status: response.status,
                            data: errorJson
                        }};
                    }} catch (e) {{
                        // Fallback to text error
                        const errorText = await response.text();
                        return {{ 
                            __error__: true, 
                            status: response.status,
                            data: errorText
                        }};
                    }}
                }}
            }} catch (error) {{
                return {{ 
                    __error__: true, 
                    message: error.toString(),
                    type: "network"
                }};
            }}
        }}
        
        return makeRequest();
        """
        
        try:
            result = self.driver.execute_script(fetch_script)
            return result
        except Exception as e:
            logger.error(f"Error executing API request: {str(e)}")
            return {"__error__": True, "message": str(e), "type": "script"}

    def run_all_tests(self):
        """Run all authentication integration tests"""
        try:
            self.setup()
            
            # Test login functionality
            self.test_login_success()
            self.test_login_invalid_credentials()
            self.test_login_remember_me()
            
            # Test authentication error handling
            self.test_auth_error_display()
            self.test_session_expired_handling()
            
            # Test session persistence
            self.test_session_persistence()
            self.test_logout_functionality()
            
            # Test API integration with authentication
            self.test_api_authenticated_requests()
            self.test_api_unauthenticated_requests()
            
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
        finally:
            self.teardown()

    def test_login_success(self):
        """Test successful login flow"""
        test_id = "LOGIN-01"
        test_name = "Successful Login Flow"
        
        try:
            # Navigate to login page
            self.navigate_to("/login")
            
            # Get screenshot before login
            self.take_screenshot("before_login")
            
            # Attempt login with valid credentials
            success = self.login(self.admin_credentials['username'], self.admin_credentials['password'])
            
            # Get screenshot after login
            self.take_screenshot("after_login")
            
            # Verify login state in UI
            is_authenticated = self.check_authenticated_state()
            
            # Check for admin link visibility
            admin_link_visible = self.is_element_present(By.CSS_SELECTOR, ".admin-link") and self.driver.find_element(By.CSS_SELECTOR, ".admin-link").is_displayed()
            
            passed = success and is_authenticated and admin_link_visible
            
            record_test_result("login", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            # Logout for next test
            self.logout()
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("login", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        test_id = "LOGIN-02"
        test_name = "Invalid Credentials Error Handling"
        
        try:
            # Navigate to login page
            self.navigate_to("/login")
            
            # Attempt login with invalid credentials
            self.login("invalid_user", "wrong_password")
            
            # Check for error message
            error_div = self.wait_for_element(By.ID, "login-error")
            has_error = error_div is not None and error_div.is_displayed()
            
            # Verify we're still on login page
            on_login_page = "/login" in self.driver.current_url
            
            # Take screenshot of error
            self.take_screenshot("login_error")
            
            passed = has_error and on_login_page
            
            record_test_result("login", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("login", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_login_remember_me(self):
        """Test login with remember me functionality"""
        test_id = "LOGIN-03"
        test_name = "Remember Me Functionality"
        
        try:
            # First login with remember me checked
            self.navigate_to("/login")
            login_success = self.login(
                self.admin_credentials['username'], 
                self.admin_credentials['password'],
                remember_me=True
            )
            
            if not login_success:
                record_test_result("login", test_id, test_name, False, "Initial login failed")
                return False
            
            # Check localStorage for persistent token
            has_token = self.driver.execute_script('return localStorage.getItem("auth_token") !== null')
            
            # Close and reopen browser session to simulate browser restart
            current_url = self.driver.current_url
            self.driver.quit()
            
            # Start a new session
            if not self.setup():
                record_test_result("login", test_id, test_name, False, "Failed to restart browser session")
                return False
                
            # Go back to the site
            self.navigate_to("/")
            
            # Check if still logged in
            still_authenticated = self.check_authenticated_state()
            
            passed = has_token and still_authenticated
            
            record_test_result("login", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            # Logout for next test
            self.logout()
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("login", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_auth_error_display(self):
        """Test authentication error displays"""
        test_id = "AUTH-ERR-01"
        test_name = "Authentication Error UI Display"
        
        try:
            # Navigate to home page
            self.navigate_to("/")
            
            # Trigger auth error through JavaScript
            self.driver.execute_script("""
            if (window.AuthErrorHandler) {
                window.AuthErrorHandler.showError(
                    'Authentication failed: Your session has expired',
                    'authentication_error'
                );
            }
            """)
            
            # Wait for error to display
            time.sleep(1)
            
            # Check for error container
            error_container = self.wait_for_element(By.ID, "auth-error-container")
            has_error_ui = error_container is not None and error_container.is_displayed()
            
            # Take screenshot
            self.take_screenshot("auth_error_display")
            
            passed = has_error_ui
            
            record_test_result("auth_errors", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("auth_errors", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_session_expired_handling(self):
        """Test session expired handling"""
        test_id = "AUTH-ERR-02"
        test_name = "Session Expired Dialog"
        
        try:
            # Navigate to home page
            self.navigate_to("/")
            
            # Trigger session expiry through JavaScript
            self.driver.execute_script("""
            if (window.AuthErrorHandler) {
                window.AuthErrorHandler.showSessionExpired();
            }
            """)
            
            # Wait for dialog to display
            time.sleep(1)
            
            # Check for session expiry dialog
            dialog = self.wait_for_element(By.ID, "session-expiry-dialog")
            has_dialog = dialog is not None and dialog.is_displayed()
            
            # Check for login button in dialog
            login_button = None
            if has_dialog:
                login_button = dialog.find_element(By.CSS_SELECTOR, ".session-expiry-login-btn")
            
            has_login_button = login_button is not None and login_button.is_displayed()
            
            # Take screenshot
            self.take_screenshot("session_expired_dialog")
            
            passed = has_dialog and has_login_button
            
            record_test_result("auth_errors", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("auth_errors", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_session_persistence(self):
        """Test session persistence across pages"""
        test_id = "SESSION-01"
        test_name = "Session Persistence Across Pages"
        
        try:
            # Login first
            self.navigate_to("/login")
            login_success = self.login(
                self.admin_credentials['username'], 
                self.admin_credentials['password']
            )
            
            if not login_success:
                record_test_result("session", test_id, test_name, False, "Initial login failed")
                return False
                
            # Navigate to different pages and check auth state
            pages = ["/", "/admin/health", "/admin/parameters"]
            auth_states = []
            
            for page in pages:
                self.navigate_to(page)
                auth_states.append(self.check_authenticated_state())
                
            # All pages should show authenticated state
            all_authenticated = all(auth_states)
            
            passed = all_authenticated
            
            record_test_result("session", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            # Logout for next test
            self.logout()
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("session", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_logout_functionality(self):
        """Test logout functionality"""
        test_id = "SESSION-02"
        test_name = "Logout Functionality"
        
        try:
            # Login first
            self.navigate_to("/login")
            login_success = self.login(
                self.admin_credentials['username'], 
                self.admin_credentials['password']
            )
            
            if not login_success:
                record_test_result("session", test_id, test_name, False, "Initial login failed")
                return False
                
            # Verify we're logged in
            before_logout = self.check_authenticated_state()
            
            # Perform logout
            logout_success = self.logout()
            
            # Verify we're logged out
            after_logout = not self.check_authenticated_state()
            
            # Check localStorage and sessionStorage are cleared
            token_cleared = not self.driver.execute_script(
                'return localStorage.getItem("auth_token") !== null || sessionStorage.getItem("auth_token") !== null'
            )
            
            passed = before_logout and logout_success and after_logout and token_cleared
            
            record_test_result("session", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("session", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_api_authenticated_requests(self):
        """Test authenticated API requests"""
        test_id = "API-01"
        test_name = "Authenticated API Requests"
        
        try:
            # Navigate to home page
            self.navigate_to("/")
            
            # Inject auth token
            self.inject_auth_token(
                self.admin_credentials['username'],
                self.admin_credentials['password']
            )
            
            # Try accessing an admin endpoint
            result = self.api_request("/admin/health")
            
            # Take screenshot
            self.take_screenshot("authenticated_api_request")
            
            # Check if request was successful (no __error__ property)
            request_success = not result.get("__error__", False)
            
            passed = request_success
            
            record_test_result("api", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("api", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

    def test_api_unauthenticated_requests(self):
        """Test unauthenticated API requests"""
        test_id = "API-02"
        test_name = "Unauthenticated API Requests"
        
        try:
            # Navigate to home page and clear any auth tokens
            self.navigate_to("/")
            self.driver.execute_script("localStorage.clear(); sessionStorage.clear();")
            
            # Try accessing an admin endpoint without auth
            result = self.api_request("/admin/health", auth=False)
            
            # Take screenshot
            self.take_screenshot("unauthenticated_api_request")
            
            # This should fail with 401 (unless in DEV_MODE)
            dev_mode = getattr(Config, 'DEV_MODE', False)
            
            if dev_mode:
                # In dev mode, it should succeed even without auth
                request_success = not result.get("__error__", False)
                passed = request_success
            else:
                # In production mode, it should fail with 401
                has_error = result.get("__error__", False)
                status_401 = result.get("status", 0) == 401
                passed = has_error and status_401
            
            record_test_result("api", test_id, test_name, passed)
            print(f"Test {test_id} - {test_name}: {'PASS' if passed else 'FAIL'}")
            
            return passed
        except Exception as e:
            error_msg = str(e)
            record_test_result("api", test_id, test_name, False, error_msg)
            print(f"Test {test_id} - {test_name}: FAIL - {error_msg}")
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Authentication Integration Test')
    parser.add_argument('--browser', default='safari', choices=['chrome', 'firefox', 'safari'],
                        help='Browser to use for testing')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--url', default='http://localhost:5432', help='Base URL for testing')
    
    args = parser.parse_args()
    
    print("\n=== Authentication Integration Test ===\n")
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
    test = AuthIntegrationTest(args.browser, args.headless, args.url)
    test.run_all_tests()
    
    # Generate report
    report_file = generate_report()
    
    print("\n=== Authentication Integration Test Complete ===\n")

if __name__ == "__main__":
    main()
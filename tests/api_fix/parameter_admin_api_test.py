"""
Parameter Admin API Test Script

This script provides a command-line interface for testing Parameter Admin API endpoints.
It ensures the frontend component integration can successfully connect to the backend API.

Usage: python -m tests.api_fix.parameter_admin_api_test [command]

Commands:
  list                      - Test /api/v2/admin/parameters 
  details <path>            - Test /api/v2/admin/parameters/{path}
  history <path>            - Test /api/v2/admin/parameters/history/{path}
  impact <path>             - Test /api/v2/admin/parameters/impact/{path}
  related <path>            - Test /api/v2/admin/parameters/related/{path}
  audit                     - Test /api/v2/admin/parameters/audit
  profiles                  - Test /api/v2/admin/profiles
  user_params <profile_id>  - Test /api/v2/admin/parameters/user/{profile_id}
  create                    - Test parameter creation
  update <path>             - Test parameter update
  delete <path>             - Test parameter deletion
  all                       - Run all tests in sequence
  pytest                    - Run comprehensive pytest-based tests
  direct_test               - Run basic connectivity tests directly without test infrastructure
"""

import os
import sys
import json
import time
import requests
import uuid
import base64
from datetime import datetime
from collections import OrderedDict

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import config
from config import Config

# Default test parameter path and profile ID
TEST_PARAMETER_PATH = "test.admin.api.parameter"
TEST_PROFILE_ID = "test-profile-12345"  # Should be replaced with a real profile ID from your system

class ParameterAdminApiTester:
    """Parameter Admin API testing utility class"""
    
    def __init__(self, base_url="http://localhost:5432"):
        self.base_url = base_url
        
        # Set up authentication headers
        auth_string = f"{Config.ADMIN_USERNAME}:{Config.ADMIN_PASSWORD}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.auth_headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json'
        }
        
        self.test_parameter_path = TEST_PARAMETER_PATH + "." + str(uuid.uuid4())[:8]
        self.created_parameters = []
        
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
    
    def test_list_parameters(self, search=None, category=None):
        """Test getting all parameters"""
        print("\n=== Testing Parameter List API ===")
        
        try:
            url = f"{self.base_url}/api/v2/admin/parameters"
            params = {}
            if search:
                params['search'] = search
            if category:
                params['category'] = category
            
            response = requests.get(url, params=params, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
            
            if 'parameters' in data:
                print(f"\nFound {len(data['parameters'])} parameters")
                if len(data['parameters']) > 0:
                    print("\nSample Parameter:")
                    print(json.dumps(data['parameters'][0], indent=2))
            
            if 'tree' in data:
                print("\nParameter Tree Structure Example:")
                # Extract a small sample from the tree
                tree_sample = {k: v for i, (k, v) in enumerate(data['tree'].items()) if i < 3}
                print(json.dumps(tree_sample, indent=2))
            
            print("\n✅ Parameter list endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing parameter list: {e}")
            return False
    
    def test_parameter_details(self, path):
        """Test getting parameter details"""
        print(f"\n=== Testing Parameter Details API for '{path}' ===")
        
        try:
            url = f"{self.base_url}/api/v2/admin/parameters/{path}"
            response = requests.get(url, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code not in [200, 404]:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            if response.status_code == 404:
                print(f"Parameter '{path}' does not exist")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2))
            
            # Verify expected fields
            required_fields = ['path', 'value', 'description', 'source', 'last_updated']
            missing_fields = [field for field in required_fields if field not in data.get('parameter', {})]
            if missing_fields:
                print(f"⚠️ Missing required fields: {missing_fields}")
            
            print("\n✅ Parameter details endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing parameter details: {e}")
            return False
    
    def test_parameter_history(self, path):
        """Test getting parameter history"""
        print(f"\n=== Testing Parameter History API for '{path}' ===")
        
        try:
            url = f"{self.base_url}/api/v2/admin/parameters/history/{path}"
            response = requests.get(url, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code not in [200, 404]:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            if response.status_code == 404:
                print(f"Parameter '{path}' does not exist")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
            
            if 'history' in data:
                print(f"\nFound {len(data['history'])} history entries")
                if len(data['history']) > 0:
                    print("\nSample History Entry:")
                    print(json.dumps(data['history'][0], indent=2))
            
            print("\n✅ Parameter history endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing parameter history: {e}")
            return False
    
    def test_parameter_impact(self, path):
        """Test getting parameter impact"""
        print(f"\n=== Testing Parameter Impact API for '{path}' ===")
        
        try:
            url = f"{self.base_url}/api/v2/admin/parameters/impact/{path}"
            response = requests.get(url, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code not in [200, 404]:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            if response.status_code == 404:
                print(f"Parameter '{path}' does not exist")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2))
            
            # Expected impact fields
            expected_fields = ['dependent_parameters', 'calculators', 'models']
            missing_fields = [field for field in expected_fields if field not in data]
            if missing_fields:
                print(f"⚠️ Missing impact fields: {missing_fields}")
            
            print("\n✅ Parameter impact endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing parameter impact: {e}")
            return False
    
    def test_related_parameters(self, path):
        """Test getting related parameters"""
        print(f"\n=== Testing Related Parameters API for '{path}' ===")
        
        try:
            url = f"{self.base_url}/api/v2/admin/parameters/related/{path}"
            response = requests.get(url, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code not in [200, 404]:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            if response.status_code == 404:
                print(f"Parameter '{path}' does not exist")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
            
            if 'related_parameters' in data:
                print(f"\nFound {len(data['related_parameters'])} related parameters")
                if len(data['related_parameters']) > 0:
                    print("\nSample Related Parameter:")
                    print(json.dumps(data['related_parameters'][0], indent=2))
            
            print("\n✅ Related parameters endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing related parameters: {e}")
            return False
    
    def test_audit_log(self, search=None, action=None):
        """Test getting audit log"""
        print("\n=== Testing Audit Log API ===")
        
        try:
            url = f"{self.base_url}/api/v2/admin/parameters/audit"
            params = {}
            if search:
                params['search'] = search
            if action:
                params['action'] = action
            
            response = requests.get(url, params=params, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
            
            if 'audit_log' in data:
                print(f"\nFound {len(data['audit_log'])} audit log entries")
                if len(data['audit_log']) > 0:
                    print("\nSample Audit Log Entry:")
                    print(json.dumps(data['audit_log'][0], indent=2))
            
            print("\n✅ Audit log endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing audit log: {e}")
            return False
    
    def test_get_profiles(self):
        """Test getting profiles"""
        print("\n=== Testing Profiles API ===")
        
        try:
            url = f"{self.base_url}/api/v2/admin/profiles"
            response = requests.get(url, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
            
            if 'profiles' in data:
                print(f"\nFound {len(data['profiles'])} profiles")
                if len(data['profiles']) > 0:
                    print("\nSample Profile:")
                    print(json.dumps(data['profiles'][0], indent=2))
                    
                    # Get a real profile ID for further testing
                    if data['profiles'][0].get('id'):
                        global TEST_PROFILE_ID
                        TEST_PROFILE_ID = data['profiles'][0]['id']
                        print(f"\nUsing profile ID for testing: {TEST_PROFILE_ID}")
            
            print("\n✅ Profiles endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing profiles: {e}")
            return False
    
    def test_user_parameters(self, profile_id):
        """Test getting user parameter overrides"""
        print(f"\n=== Testing User Parameters API for profile '{profile_id}' ===")
        
        try:
            url = f"{self.base_url}/api/v2/admin/parameters/user/{profile_id}"
            response = requests.get(url, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code not in [200, 404]:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            if response.status_code == 404:
                print(f"Profile '{profile_id}' does not exist")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
            
            if 'user_parameters' in data:
                print(f"\nFound {len(data['user_parameters'])} user parameter overrides")
                if len(data['user_parameters']) > 0:
                    print("\nSample User Parameter Override:")
                    print(json.dumps(data['user_parameters'][0], indent=2))
            
            print("\n✅ User parameters endpoint test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing user parameters: {e}")
            return False
    
    def test_create_parameter(self):
        """Test creating a new parameter"""
        print("\n=== Testing Parameter Creation API ===")
        
        try:
            # Generate a unique parameter path to avoid conflicts
            param_path = self.test_parameter_path
            
            param_data = {
                "path": param_path,
                "value": 12345.67,
                "description": "Test parameter created through API test",
                "source": "api_test",
                "is_editable": True
            }
            
            url = f"{self.base_url}/api/v2/admin/parameters"
            response = requests.post(url, json=param_data, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 201:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2))
            
            if data.get('success'):
                print(f"✅ Successfully created parameter '{param_path}'")
                self.created_parameters.append(param_path)
                return True
            else:
                print(f"❌ Failed to create parameter: {data.get('message', 'Unknown error')}")
                return False
            
        except Exception as e:
            print(f"❌ Error creating parameter: {e}")
            return False
    
    def test_update_parameter(self, path=None):
        """Test updating a parameter"""
        path = path or self.test_parameter_path
        print(f"\n=== Testing Parameter Update API for '{path}' ===")
        
        try:
            # First check if the parameter exists
            check_url = f"{self.base_url}/api/v2/admin/parameters/{path}"
            check_response = requests.get(check_url, headers=self.auth_headers)
            
            if check_response.status_code == 404:
                print(f"Parameter '{path}' does not exist, creating it first")
                if not self.test_create_parameter():
                    return False
                path = self.test_parameter_path
            
            # Now update it
            update_data = {
                "value": 98765.43,
                "description": "Updated test parameter",
                "source": "api_test_update"
            }
            
            url = f"{self.base_url}/api/v2/admin/parameters/{path}"
            response = requests.put(url, json=update_data, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2))
            
            if data.get('success'):
                print(f"✅ Successfully updated parameter '{path}'")
                
                # Verify update
                check_response = requests.get(check_url, headers=self.auth_headers)
                if check_response.status_code == 200:
                    check_data = check_response.json()
                    actual_value = check_data.get('parameter', {}).get('value')
                    expected_value = update_data['value']
                    
                    if actual_value == expected_value:
                        print(f"✅ Verified update: value is now {actual_value}")
                    else:
                        print(f"⚠️ Update verification failed: expected {expected_value}, got {actual_value}")
                
                return True
            else:
                print(f"❌ Failed to update parameter: {data.get('message', 'Unknown error')}")
                return False
            
        except Exception as e:
            print(f"❌ Error updating parameter: {e}")
            return False
    
    def test_delete_parameter(self, path=None):
        """Test deleting a parameter"""
        path = path or self.test_parameter_path
        print(f"\n=== Testing Parameter Deletion API for '{path}' ===")
        
        try:
            # First check if the parameter exists
            check_url = f"{self.base_url}/api/v2/admin/parameters/{path}"
            check_response = requests.get(check_url, headers=self.auth_headers)
            
            if check_response.status_code == 404:
                print(f"Parameter '{path}' does not exist, creating it first")
                if not self.test_create_parameter():
                    return False
                path = self.test_parameter_path
            
            # Now delete it
            url = f"{self.base_url}/api/v2/admin/parameters/{path}"
            response = requests.delete(url, headers=self.auth_headers)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            print(f"Response Structure:")
            print(json.dumps(data, indent=2))
            
            if data.get('success'):
                print(f"✅ Successfully deleted parameter '{path}'")
                if path in self.created_parameters:
                    self.created_parameters.remove(path)
                
                # Verify deletion
                check_response = requests.get(check_url, headers=self.auth_headers)
                if check_response.status_code == 404:
                    print("✅ Verified deletion: parameter no longer exists")
                else:
                    print("⚠️ Deletion verification failed: parameter still exists")
                
                return True
            else:
                print(f"❌ Failed to delete parameter: {data.get('message', 'Unknown error')}")
                return False
            
        except Exception as e:
            print(f"❌ Error deleting parameter: {e}")
            return False
    
    def test_update_user_parameter(self, profile_id, path=None):
        """Test updating a user parameter override"""
        path = path or self.test_parameter_path
        print(f"\n=== Testing User Parameter Update API for profile '{profile_id}', parameter '{path}' ===")
        
        try:
            # First ensure the parameter exists
            check_url = f"{self.base_url}/api/v2/admin/parameters/{path}"
            check_response = requests.get(check_url, headers=self.auth_headers)
            
            if check_response.status_code == 404:
                print(f"Parameter '{path}' does not exist, creating it first")
                if not self.test_create_parameter():
                    return False
                path = self.test_parameter_path
                
                # Store the global value for reference
                check_response = requests.get(check_url, headers=self.auth_headers)
                if check_response.status_code == 200:
                    global_value = check_response.json().get('parameter', {}).get('value')
                    print(f"Global parameter value: {global_value}")
            
            # Try three different values to ensure the updates work consistently
            test_values = [54321.98, 12345.67, 98765.43]
            
            for i, test_value in enumerate(test_values):
                print(f"\nTest #{i+1}: Setting user parameter to {test_value}")
                
                # Set user parameter override
                param_data = {
                    "path": path,
                    "value": test_value,
                    "reason": f"Test update #{i+1} via API test"
                }
                
                url = f"{self.base_url}/api/v2/admin/parameters/user/{profile_id}"
                response = requests.post(url, json=param_data, headers=self.auth_headers)
                
                print(f"Status Code: {response.status_code}")
                if response.status_code not in [200, 201]:
                    print(f"❌ Failed with status {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                
                data = response.json()
                print(f"Response Structure:")
                print(json.dumps(data, indent=2))
                
                # Verify the operation was successful
                if not data.get('success', False):
                    print(f"❌ API reported failure: {data.get('error', 'Unknown error')}")
                    return False
                
                # Verify user parameter was set correctly
                verify_url = f"{self.base_url}/api/v2/admin/parameters/user/{profile_id}"
                verify_response = requests.get(verify_url, headers=self.auth_headers)
                
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    user_params = verify_data.get('user_parameters', [])
                    found = False
                    
                    for param in user_params:
                        if param.get('path') == path:
                            found = True
                            actual_value = param.get('value')
                            expected_value = param_data['value']
                            
                            if actual_value == expected_value:
                                print(f"✅ Verified user parameter: value is now {actual_value}")
                            else:
                                print(f"⚠️ User parameter verification failed: expected {expected_value}, got {actual_value}")
                                return False
                    
                    if not found:
                        print("⚠️ User parameter was not found after setting")
                        return False
                else:
                    print(f"❌ Failed to verify user parameter: GET request returned status {verify_response.status_code}")
                    return False
                
                # Sleep briefly between tests to ensure timestamps are different
                time.sleep(0.5)
            
            print("\n✅ All user parameter update tests passed")
            return True
            
        except Exception as e:
            print(f"❌ Error updating user parameter: {e}")
            return False
    
    def test_reset_user_parameter(self, profile_id, path=None):
        """Test resetting a user parameter override"""
        path = path or self.test_parameter_path
        print(f"\n=== Testing User Parameter Reset API for profile '{profile_id}', parameter '{path}' ===")
        
        try:
            # First ensure the parameter exists
            check_url = f"{self.base_url}/api/v2/admin/parameters/{path}"
            check_response = requests.get(check_url, headers=self.auth_headers)
            
            if check_response.status_code == 404:
                print(f"Parameter '{path}' does not exist, creating it first")
                if not self.test_create_parameter():
                    return False
                path = self.test_parameter_path
            
            # Store the global parameter value for verification later
            global_response = requests.get(check_url, headers=self.auth_headers)
            if global_response.status_code != 200:
                print(f"❌ Failed to get global parameter value: {global_response.status_code}")
                return False
                
            global_data = global_response.json()
            global_value = global_data.get('parameter', {}).get('value')
            print(f"Global parameter value: {global_value}")
            
            # Create a user override first
            print("\nSetting up user parameter override...")
            test_override_value = 33333.33  # Value different from global
            param_data = {
                "path": path,
                "value": test_override_value,
                "reason": "Test override for reset test"
            }
            
            set_url = f"{self.base_url}/api/v2/admin/parameters/user/{profile_id}"
            set_response = requests.post(set_url, json=param_data, headers=self.auth_headers)
            
            if set_response.status_code not in [200, 201]:
                print(f"❌ Failed to set up user override: {set_response.status_code}")
                print(set_response.text)
                return False
                
            # Verify the override was set
            verify_url = f"{self.base_url}/api/v2/admin/parameters/user/{profile_id}"
            verify_response = requests.get(verify_url, headers=self.auth_headers)
            
            if verify_response.status_code != 200:
                print(f"❌ Failed to verify user override: {verify_response.status_code}")
                return False
                
            verify_data = verify_response.json()
            user_params = verify_data.get('user_parameters', [])
            override_found = False
            
            for param in user_params:
                if param.get('path') == path:
                    override_found = True
                    override_value = param.get('value')
                    
                    if override_value == test_override_value:
                        print(f"✅ User override verified: value is {override_value}")
                    else:
                        print(f"⚠️ User override verification failed: expected {test_override_value}, got {override_value}")
                        return False
            
            if not override_found:
                print("❌ User override was not found before reset")
                return False
                
            # Now reset the user parameter override
            print("\nResetting user parameter override...")
            reset_data = {
                "path": path,
                "reason": "Test reset via API test"
            }
            
            reset_url = f"{self.base_url}/api/v2/admin/parameters/user/{profile_id}/reset"
            reset_response = requests.post(reset_url, json=reset_data, headers=self.auth_headers)
            
            print(f"Reset Status Code: {reset_response.status_code}")
            if reset_response.status_code != 200:
                print(f"❌ Failed reset with status {reset_response.status_code}")
                print(f"Response: {reset_response.text}")
                return False
            
            reset_data = reset_response.json()
            print(f"Reset Response Structure:")
            print(json.dumps(reset_data, indent=2))
            
            # Verify the reset was successful in the response
            if not reset_data.get('success'):
                print(f"❌ API reported failure in reset: {reset_data.get('error', 'Unknown error')}")
                return False
                
            # Verify the override was actually removed
            print("\nVerifying user parameter was reset...")
            verify_after_reset_response = requests.get(verify_url, headers=self.auth_headers)
            
            if verify_after_reset_response.status_code != 200:
                print(f"❌ Failed to verify after reset: {verify_after_reset_response.status_code}")
                return False
                
            after_reset_data = verify_after_reset_response.json()
            after_user_params = after_reset_data.get('user_parameters', [])
            
            # Parameter should be removed or reset to global value
            for param in after_user_params:
                if param.get('path') == path:
                    print(f"⚠️ User parameter still exists after reset with value: {param.get('value')}")
                    
                    # In some implementations, reset might not remove the parameter but set it to the global value
                    if param.get('value') == global_value:
                        print("✅ However, value is reset to global value, which is acceptable")
                    else:
                        print(f"❌ Value still overridden: {param.get('value')} !== global value {global_value}")
                        return False
            
            print("\n✅ User parameter reset test passed")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting user parameter: {e}")
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
            
        report = "\n=== PARAMETER ADMIN API TEST REPORT ===\n"
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
            'PA-01': 'test_list_parameters',
            'PA-02': 'test_parameter_details',
            'PA-03': 'test_create_parameter',
            'PA-04': 'test_update_parameter',
            'PA-05': 'test_delete_parameter',
            'PA-06': 'test_parameter_history',
            'PA-07': 'test_parameter_impact',
            'PA-08': 'test_related_parameters',
            'PA-09': 'test_audit_log',
            'PA-10': 'test_get_profiles',
            'PA-11': 'test_user_parameters',
            'PA-12': 'test_update_user_parameter',
            'PA-13': 'test_reset_user_parameter',
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
            'PA-01': 'List parameters with search and filtering',
            'PA-02': 'Get parameter details',
            'PA-03': 'Create a new parameter',
            'PA-04': 'Update an existing parameter',
            'PA-05': 'Delete a parameter',
            'PA-06': 'Get parameter history',
            'PA-07': 'Get parameter impact analysis',
            'PA-08': 'Get related parameters',
            'PA-09': 'Get audit log with filtering',
            'PA-10': 'Get profiles for user management',
            'PA-11': 'Get user parameter overrides',
            'PA-12': 'Set user parameter override',
            'PA-13': 'Reset user parameter override',
        }
        return descriptions.get(case_id, 'Unknown test')
        
    def save_test_report(self, filename=None):
        """Save the test report to a file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"parameter_admin_api_test_report_{timestamp}.txt"
            
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
            
    def clean_up(self):
        """Clean up by removing test parameters"""
        print("\n=== Cleaning Up Test Parameters ===")
        
        success = True
        for path in self.created_parameters:
            try:
                url = f"{self.base_url}/api/v2/admin/parameters/{path}"
                response = requests.delete(url, headers=self.auth_headers)
                
                if response.status_code == 200:
                    print(f"✅ Removed test parameter '{path}'")
                else:
                    print(f"⚠️ Failed to remove test parameter '{path}'")
                    success = False
            except Exception as e:
                print(f"⚠️ Error removing test parameter '{path}': {e}")
                success = False
        
        if success:
            self.created_parameters = []
        
        return success

def direct_test():
    """Do a direct test of the admin endpoints without test infrastructure"""
    import requests
    base_url = "http://localhost:5432"
    
    # Just make a basic request
    print("Testing basic endpoint...")
    profile_url = f"{base_url}/api/v2/admin/profiles"
    response = requests.get(profile_url)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Response content:", response.text[:100])
    else:
        print("Response content:", response.text)

    # Test another endpoint
    print("\nTesting parameters endpoint...")
    params_url = f"{base_url}/api/v2/admin/parameters"
    response = requests.get(params_url)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Response content:", response.text[:100])
    else:
        print("Response content:", response.text)
    
    # At this point, we can use curl to test directly
    print("\nYou can also test directly with curl:")
    print(f"curl -X GET {base_url}/api/v2/admin/profiles")

def run_pytest_tests():
    """Run the comprehensive pytest-based tests"""
    print("\n=========== RUNNING COMPREHENSIVE PARAMETER ADMIN API PYTEST TESTS ===========\n")
    
    # Import pytest and run the tests
    import pytest
    import os
    
    # Get the absolute path to the test file
    test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_admin_parameters.py'))
    
    # Run pytest programmatically
    exit_code = pytest.main(['-v', test_file])
    
    if exit_code == 0:
        print("\n✅ All pytest parameter admin API tests PASSED")
        return True
    else:
        print(f"\n❌ Some tests FAILED (exit code: {exit_code})")
        return False

def main():
    """Main function to handle command-line arguments"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    # Special direct test
    if len(sys.argv) >= 2 and sys.argv[1] == 'direct_test':
        direct_test()
        return
    
    # Run pytest tests
    if len(sys.argv) >= 2 and sys.argv[1] == 'pytest':
        run_pytest_tests()
        return
    
    tester = ParameterAdminApiTester()
    
    if not tester.test_connection():
        print("Please make sure the Flask server is running (python app.py)")
        return
    
    command = sys.argv[1]
    
    try:
        if command == "list":
            tester.test_list_parameters()
        
        elif command == "details":
            path = sys.argv[2] if len(sys.argv) > 2 else TEST_PARAMETER_PATH
            tester.test_parameter_details(path)
        
        elif command == "history":
            path = sys.argv[2] if len(sys.argv) > 2 else TEST_PARAMETER_PATH
            tester.test_parameter_history(path)
        
        elif command == "impact":
            path = sys.argv[2] if len(sys.argv) > 2 else TEST_PARAMETER_PATH
            tester.test_parameter_impact(path)
        
        elif command == "related":
            path = sys.argv[2] if len(sys.argv) > 2 else TEST_PARAMETER_PATH
            tester.test_related_parameters(path)
        
        elif command == "audit":
            tester.test_audit_log()
        
        elif command == "profiles":
            tester.test_get_profiles()
        
        elif command == "user_params":
            profile_id = sys.argv[2] if len(sys.argv) > 2 else TEST_PROFILE_ID
            tester.test_user_parameters(profile_id)
        
        elif command == "create":
            tester.test_create_parameter()
        
        elif command == "update":
            path = sys.argv[2] if len(sys.argv) > 2 else None
            tester.test_update_parameter(path)
        
        elif command == "delete":
            path = sys.argv[2] if len(sys.argv) > 2 else None
            tester.test_delete_parameter(path)
        
        elif command == "user_update":
            profile_id = sys.argv[2] if len(sys.argv) > 2 else TEST_PROFILE_ID
            path = sys.argv[3] if len(sys.argv) > 3 else None
            tester.test_update_user_parameter(profile_id, path)
        
        elif command == "user_reset":
            profile_id = sys.argv[2] if len(sys.argv) > 2 else TEST_PROFILE_ID
            path = sys.argv[3] if len(sys.argv) > 3 else None
            tester.test_reset_user_parameter(profile_id, path)
        
        elif command == "all":
            print("\n=========== RUNNING ALL PARAMETER ADMIN API TESTS ===========\n")
            
            # First, get a valid profile ID
            tester.start_test("Get Profiles", "test_get_profiles")
            success = tester.test_get_profiles()
            tester.record_test_result("passed" if success else "failed", 
                                     "Successfully retrieved profiles" if success else "Failed to retrieve profiles")
            
            # Test basic parameter operations
            tester.start_test("List Parameters", "test_list_parameters")
            success = tester.test_list_parameters()
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully listed parameters" if success else "Failed to list parameters")
            
            tester.start_test("Create Parameter", "test_create_parameter")
            success = tester.test_create_parameter()
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully created parameter" if success else "Failed to create parameter")
            
            path = tester.test_parameter_path
            
            tester.start_test("Parameter Details", "test_parameter_details")
            success = tester.test_parameter_details(path)
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully retrieved parameter details" if success else "Failed to retrieve parameter details")
            
            tester.start_test("Update Parameter", "test_update_parameter")
            success = tester.test_update_parameter(path)
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully updated parameter" if success else "Failed to update parameter")
            
            tester.start_test("Parameter History", "test_parameter_history")
            success = tester.test_parameter_history(path)
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully retrieved parameter history" if success else "Failed to retrieve parameter history")
            
            tester.start_test("Parameter Impact", "test_parameter_impact")
            success = tester.test_parameter_impact(path)
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully retrieved parameter impact" if success else "Failed to retrieve parameter impact")
            
            tester.start_test("Related Parameters", "test_related_parameters")
            success = tester.test_related_parameters(path)
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully retrieved related parameters" if success else "Failed to retrieve related parameters")
            
            # Test user parameter operations
            profile_id = TEST_PROFILE_ID
            
            tester.start_test("User Parameters", "test_user_parameters")
            success = tester.test_user_parameters(profile_id)
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully retrieved user parameters" if success else "Failed to retrieve user parameters")
            
            tester.start_test("Update User Parameter", "test_update_user_parameter")
            success = tester.test_update_user_parameter(profile_id, path)
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully updated user parameter" if success else "Failed to update user parameter")
            
            tester.start_test("Reset User Parameter", "test_reset_user_parameter")
            success = tester.test_reset_user_parameter(profile_id, path)
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully reset user parameter" if success else "Failed to reset user parameter")
            
            # Test audit log
            tester.start_test("Audit Log", "test_audit_log")
            success = tester.test_audit_log()
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully retrieved audit log" if success else "Failed to retrieve audit log")
            
            # Delete the parameter at the end
            tester.start_test("Delete Parameter", "test_delete_parameter")
            success = tester.test_delete_parameter(path)
            tester.record_test_result("passed" if success else "failed",
                                     "Successfully deleted parameter" if success else "Failed to delete parameter")
            
            # Generate and save the test report
            print("\n=== Generating Test Report ===")
            tester.save_test_report()
            
            # Print a summary of the results
            print("\n=== Test Results Summary ===")
            passed = sum(1 for result in tester.test_results.values() if result['status'] == 'passed')
            failed = sum(1 for result in tester.test_results.values() if result['status'] == 'failed')
            total = len(tester.test_results)
            
            print(f"Total Tests: {total}")
            print(f"Passed: {passed}")
            print(f"Failed: {failed}")
            print(f"Success Rate: {passed / total * 100:.1f}%")
            
            print("\n✅ All parameter admin API tests completed")
            
            # Optionally run the comprehensive pytest tests as well
            print("\nWould you like to run the comprehensive pytest tests as well? (y/n)")
            choice = input().strip().lower()
            if choice in ['y', 'yes']:
                run_pytest_tests()
        
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
    
    finally:
        # Always clean up
        tester.clean_up()

if __name__ == "__main__":
    main()
"""
Test script for the standalone auth test app
"""

import requests
import base64
import json
import time

# Base URL for standalone test app
BASE_URL = "http://localhost:5050"

def test_public_endpoint():
    """Test the public endpoint"""
    print("Testing public endpoint...")
    response = requests.get(f"{BASE_URL}/api/public")
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text}")
    print()

def test_dev_auth_endpoint():
    """Test the dev auth endpoint"""
    print("Testing dev auth endpoint without credentials...")
    response = requests.get(f"{BASE_URL}/api/dev-auth")
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text}")
    
    print("\nTesting dev auth endpoint with credentials...")
    username = "admin"
    password = "admin"
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_auth}'}
    
    response = requests.get(f"{BASE_URL}/api/dev-auth", headers=headers)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text}")
    print()

def test_protected_endpoint():
    """Test the protected endpoint"""
    print("Testing protected endpoint without credentials...")
    response = requests.get(f"{BASE_URL}/api/protected")
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text}")
    
    print("\nTesting protected endpoint with credentials...")
    username = "admin"
    password = "admin"
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_auth}'}
    
    response = requests.get(f"{BASE_URL}/api/protected", headers=headers)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text}")
    print()

def main():
    """Run all tests"""
    print("==================================================")
    print("Standalone Auth Test App - Test Script")
    print("==================================================")
    
    # Wait for server to start
    time.sleep(1)
    
    test_public_endpoint()
    test_dev_auth_endpoint()
    test_protected_endpoint()

if __name__ == "__main__":
    main()
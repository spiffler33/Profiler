"""
Authentication Test Script

This script tests the centralized authentication system to verify it's working properly.
It tests both with and without proper authentication headers to verify behavior.

Usage: python -m tests.api_fix.auth_test
"""

import requests
import base64
import json
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import config
from config import Config

def check_auth_debug():
    """Check the authentication debug endpoint"""
    print("=== Authentication Debug Information ===")

    url = "http://localhost:5432/api/v2/test/auth_headers"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print(f"DEV_MODE: {data.get('dev_mode', False)}")
        print(f"Auth Header: {data.get('auth_header', 'None')}")
        print(f"Has Valid Format: {data.get('has_valid_format', False)}")
        print(f"Auth Configured: {data.get('auth_configured', False)}")
        print(f"Timestamp: {data.get('timestamp')}")
        if 'request_headers' in data:
            print("\nRequest Headers:")
            for key, value in data['request_headers'].items():
                print(f"  {key}: {value}")
    else:
        print(f"Error: Status code {response.status_code}")
        print(f"Response: {response.text}")

    print("\n")

def test_endpoints_without_auth():
    """Test endpoints without authentication"""
    print("=== Testing Endpoints Without Authentication ===")

    # List of endpoints to test
    endpoints = [
        '/api/v2/admin/test',
        '/api/v2/admin/health',
        '/api/v2/admin/parameters'
    ]

    for endpoint in endpoints:
        url = f"http://localhost:5432{endpoint}"
        print(f"Testing: {url}")

        response = requests.get(url)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("Success! Endpoint accessible without auth (DEV_MODE is likely enabled)")
            try:
                data = response.json()
                if isinstance(data, dict):
                    print(f"Response data keys: {list(data.keys())}")
            except:
                print("Response is not JSON")
        elif response.status_code in [401, 403]:
            print("Authentication required (expected in PRODUCTION mode)")
        else:
            print(f"Unexpected status code. Response: {response.text[:100]}...")

        print("")

    print("\n")

def test_endpoints_with_auth():
    """Test endpoints with authentication"""
    print("=== Testing Endpoints With Authentication ===")

    # Set up authentication headers
    username = Config.ADMIN_USERNAME
    password = Config.ADMIN_PASSWORD
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_auth}'}

    print(f"Using credentials - Username: {username}, Password: {'*' * len(password)}")

    # List of endpoints to test
    endpoints = [
        '/api/v2/admin/test',
        '/api/v2/admin/health',
        '/api/v2/admin/parameters'
    ]

    for endpoint in endpoints:
        url = f"http://localhost:5432{endpoint}"
        print(f"Testing: {url}")

        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("Success! Endpoint accessible with auth")
            try:
                data = response.json()
                if isinstance(data, dict):
                    print(f"Response data keys: {list(data.keys())}")
            except:
                print("Response is not JSON")
        else:
            print(f"Failed. Response: {response.text[:100]}...")

        print("")

    print("\n")

def main():
    """Main function to run all tests"""
    print("===============================================")
    print("Authentication System Test")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("===============================================\n")

    # First check the auth debug information
    check_auth_debug()

    # Test without authentication
    test_endpoints_without_auth()

    # Test with authentication
    test_endpoints_with_auth()

    print("===============================================")
    print("Authentication Testing Complete")
    print("===============================================")

if __name__ == "__main__":
    main()

"""
Updated diagnostic script for debugging the fixed authentication system
"""

import requests
import base64
import json
import sys

def test_all_endpoints():
    """Test all endpoints with and without auth"""
    # Create auth headers
    username = "admin"
    password = "admin"
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_auth}'}

    # List of endpoints to test
    endpoints = [
        # Debug endpoints
        '/api/v2/test/auth_headers',
        '/api/v2/public/debug',
        '/api/v2/direct-auth-test',

        # Admin endpoints
        '/api/v2/admin/test',
    ]

    for endpoint in endpoints:
        print(f"\n=== Testing: {endpoint} ===")
        url = f"http://localhost:5432{endpoint}"

        # Test without auth
        print("Without authentication:")
        response = requests.get(url)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response summary: {data.get('message', 'No message')}")
            print(f"  DEV_MODE: {data.get('dev_mode', 'Not specified')}")

        # Test with auth
        print("\nWith authentication:")
        response = requests.get(url, headers=headers)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response summary: {data.get('message', 'No message')}")
            print(f"  DEV_MODE: {data.get('dev_mode', 'Not specified')}")

    print("\nTesting complete!")

if __name__ == "__main__":
    test_all_endpoints()

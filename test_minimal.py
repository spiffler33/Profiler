"""
Test script for minimal auth app
"""

import requests
import base64
import json

def test_endpoints():
    """Test all endpoints with and without auth"""
    # Create auth headers
    username = "admin"
    password = "admin"
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_auth}'}
    
    # Base URL
    base_url = "http://localhost:5050"
    
    # List of endpoints to test
    endpoints = [
        '/public',
        '/admin',
        '/auth-debug'
    ]
    
    for endpoint in endpoints:
        print(f"\n=== Testing: {endpoint} ===")
        url = f"{base_url}{endpoint}"
        
        # Test without auth
        print("Without authentication:")
        try:
            response = requests.get(url)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2)}")
            else:
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {str(e)}")
        
        # Test with auth
        print("\nWith authentication:")
        try:
            response = requests.get(url, headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2)}")
            else:
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {str(e)}")
    
    print("\nTesting complete!")

if __name__ == "__main__":
    test_endpoints()
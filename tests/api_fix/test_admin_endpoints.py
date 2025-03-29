"""
Simple test script to directly test admin API endpoints
"""

import requests
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_admin_test_endpoint():
    """Test the simple admin test endpoint"""
    url = "http://localhost:5432/api/v2/admin/test"
    print(f"Testing endpoint: {url}")
    
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("Response body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
    else:
        print(f"Error response: {response.text}")
    
    print("-" * 50)

def test_admin_parameters_endpoint():
    """Test the admin parameters endpoint"""
    url = "http://localhost:5432/api/v2/admin/parameters/test"  # Using test endpoint without auth
    print(f"Testing endpoint: {url}")
    
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("Response body (truncated):")
        try:
            data = response.json()
            print(f"Found {len(data.get('parameters', []))} parameters")
            print(json.dumps(data, indent=2)[:500] + "...")
        except:
            print(response.text[:500] + "...")
    else:
        print(f"Error response: {response.text}")
    
    print("-" * 50)

def test_admin_profiles_endpoint():
    """Test the admin profiles endpoint"""
    url = "http://localhost:5432/api/v2/admin/profiles/test"  # Using test endpoint without auth
    print(f"Testing endpoint: {url}")
    
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("Response body:")
        try:
            data = response.json()
            print(f"Found {len(data.get('profiles', []))} profiles")
            print(json.dumps(data, indent=2))
        except:
            print(response.text)
    else:
        print(f"Error response: {response.text}")
    
    print("-" * 50)

def main():
    """Run all tests"""
    print("=== Testing Admin API Endpoints ===\n")
    
    test_admin_test_endpoint()
    test_admin_parameters_endpoint()
    test_admin_profiles_endpoint()
    
    print("All tests completed.")

if __name__ == "__main__":
    main()
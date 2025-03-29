"""
Test script for testing authentication in production mode (DEV_MODE=False)
"""

import requests
import base64
import json
import os
import time

# Ensure DEV_MODE is False for this test
os.environ['DEV_MODE'] = 'False'

# Base URL for the API
BASE_URL = "http://localhost:5432"

def test_without_auth():
    """Test admin endpoints without authentication (should fail)"""
    print("\n=== Testing Without Authentication ===")
    
    endpoints = [
        '/api/v2/admin/test',
        '/api/v2/admin/health',
        '/api/v2/admin/parameters'
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"Testing: {url}")
        
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [401, 403]:
            print("✅ Authentication required (expected in PRODUCTION mode)")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
        
        print("")

def test_with_auth():
    """Test admin endpoints with authentication (should succeed)"""
    print("\n=== Testing With Authentication ===")
    
    # Create auth headers
    username = "admin"
    password = "admin"
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_auth}'}
    
    endpoints = [
        '/api/v2/admin/test',
        '/api/v2/admin/health',
        '/api/v2/admin/parameters'
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"Testing: {url}")
        
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
        
        print("")

def test_public_endpoints():
    """Test public endpoints (should be accessible without auth)"""
    print("\n=== Testing Public Endpoints ===")
    
    endpoints = [
        '/api/v2/public/debug',  # Our public debug endpoint
        '/api/v2/test/auth_headers'  # Auth headers endpoint
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"Testing: {url}")
        
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Public endpoint accessible")
        else:
            print(f"❌ Public endpoint inaccessible: {response.status_code}")
        
        print("")

def test_rate_limiting():
    """Test rate limiting (make rapid requests to see if rate limits are enforced)"""
    print("\n=== Testing Rate Limiting ===")
    
    # Use the public debug endpoint for testing
    url = f"{BASE_URL}/api/v2/public/debug"
    print(f"Making rapid requests to: {url}")
    
    # Make 40 rapid requests
    responses = []
    for i in range(40):
        response = requests.get(url)
        responses.append(response.status_code)
        time.sleep(0.1)  # Small delay to avoid overwhelming the server
    
    # Count status codes
    success_count = responses.count(200)
    limited_count = responses.count(429)
    
    print(f"Made 40 rapid requests:")
    print(f"  Success responses (200): {success_count}")
    print(f"  Rate limited responses (429): {limited_count}")
    print(f"  Other responses: {len(responses) - success_count - limited_count}")
    
    if limited_count > 0:
        print("✅ Rate limiting is working")
    else:
        print("⚠️ Rate limiting might not be active")

def main():
    """Run all tests"""
    print("=== Production Authentication Tests ===")
    print("Testing with DEV_MODE=False")
    print("=====================================")
    
    test_without_auth()
    test_with_auth()
    test_public_endpoints()
    test_rate_limiting()
    
    print("\nTests completed!")

if __name__ == "__main__":
    main()
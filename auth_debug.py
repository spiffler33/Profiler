"""
Simple diagnostic script for debugging authentication issues
"""

import requests
import base64
import json

def debug_public_endpoint():
    print("Testing public debug endpoint...")
    response = requests.get("http://localhost:5432/api/v2/public/debug")

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text}")

def debug_direct_auth_test():
    print("\nTesting direct auth test endpoint without credentials...")
    response = requests.get("http://localhost:5432/api/v2/direct-auth-test")

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text}")

    print("\nTesting direct auth test endpoint with credentials...")
    username = "admin"
    password = "admin"
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_auth}'}

    response = requests.get("http://localhost:5432/api/v2/direct-auth-test", headers=headers)

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text}")

def debug_auth_headers():
    print("\nTesting authentication endpoint without credentials...")
    response = requests.get("http://localhost:5432/api/v2/test/auth_headers")

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text}")

    print("\nTesting with authentication headers...")
    username = "admin"
    password = "admin"
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_auth}'}

    response = requests.get("http://localhost:5432/api/v2/test/auth_headers", headers=headers)

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text}")

def test_admin_endpoint():
    print("\nTesting admin endpoint with authentication...")
    username = "admin"
    password = "admin"
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_auth}'}

    response = requests.get("http://localhost:5432/api/v2/admin/test", headers=headers)

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text}")

if __name__ == "__main__":
    debug_public_endpoint()
    debug_direct_auth_test()
    debug_auth_headers()
    test_admin_endpoint()

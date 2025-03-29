"""
Test script for admin API endpoints. 
Note: Authentication issues need to be resolved before these tests will pass.
"""

import requests

print("Testing /api/v2/admin/test endpoint...")
response = requests.get("http://localhost:5432/api/v2/admin/test")
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

print("Authentication needs to be fixed to properly test admin endpoints.")
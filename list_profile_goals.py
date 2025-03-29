import sys
import requests
import json

# Check args
if len(sys.argv) < 2:
    print("Usage: python list_profile_goals.py <profile_id>")
    sys.exit(1)

profile_id = sys.argv[1]
base_url = "http://127.0.0.1:5000"

try:
    # Get all goals for profile
    url = f"{base_url}/api/v2/debug/goals?profile_id={profile_id}"
    print(f"Requesting: {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        goals = response.json()
        print(f"Found {len(goals)} goals for profile {profile_id}:")
        for i, goal in enumerate(goals, 1):
            print(f"\n--- Goal {i} ---")
            print(f"ID: {goal.get('goal_id')}")
            print(f"Title: {goal.get('goal_title')}")
            print(f"Category: {goal.get('goal_category')}")
            print(f"Probability: {goal.get('goal_success_probability')}")
            print(f"Probability Type: {goal.get('goal_success_probability_type')}")
            print(f"Has Probability: {goal.get('has_probability')}")
            print(f"Has Non-None Probability: {goal.get('has_probability_not_none')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error making request: {e}")

import sys
import requests
import json

# Check args
if len(sys.argv) < 2:
    print("Usage: python check_goal_prob.py <goal_id>")
    sys.exit(1)

goal_id = sys.argv[1]
base_url = "http://127.0.0.1:5000"  # Use 127.0.0.1 instead of localhost

try:
    # Get goal probability
    url = f"{base_url}/api/v2/debug/goal_probability/{goal_id}"
    print(f"Requesting: {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("Goal Probability Data:")
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error making request: {e}")

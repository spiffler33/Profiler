import sys
import requests
import json

# Check args
if len(sys.argv) < 2:
    print("Usage: python recalculate_goal_prob.py <goal_id>")
    sys.exit(1)

goal_id = sys.argv[1]
base_url = "http://127.0.0.1:5000"

try:
    # First get current probability
    url = f"{base_url}/api/v2/debug/goal_probability/{goal_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("Current Probability Data:")
        print(f"Goal ID: {data.get('goal_id')}")
        print(f"Title: {data.get('goal_title')}")
        print(f"Current Probability: {data.get('goal_success_probability')}")
        print(f"Probability Type: {data.get('goal_success_probability_type')}")
        
        # Now recalculate
        print("\nRecalculating probability...")
        recalc_url = f"{base_url}/api/v2/debug/recalculate/{goal_id}"
        recalc_response = requests.post(recalc_url)
        
        if recalc_response.status_code == 200:
            recalc_data = recalc_response.json()
            print("Recalculation Result:")
            print(f"Before: {recalc_data.get('before_probability')}")
            print(f"After: {recalc_data.get('after_probability')}")
            print(f"Success: {recalc_data.get('calculation_success')}")
            
            # Get updated data
            response = requests.get(url)
            data = response.json()
            print("\nUpdated Probability Data:")
            print(f"Current Probability: {data.get('goal_success_probability')}")
            print(f"Probability Type: {data.get('goal_success_probability_type')}")
        else:
            print(f"Error recalculating: {recalc_response.status_code}")
            print(recalc_response.text)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error making request: {e}")

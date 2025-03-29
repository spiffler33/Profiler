#\!/bin/bash

# Debug script to monitor goal probability values

# Base URL
BASE_URL="http://localhost:5000"

# Check if profile ID is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <profile_id>"
  exit 1
fi

PROFILE_ID="$1"

# Get all goals for the profile
echo "Fetching goals for profile $PROFILE_ID..."
curl -s "${BASE_URL}/api/v2/debug/goals?profile_id=${PROFILE_ID}" | jq .

# Loop through each goal and get detailed information
echo "Press any key to check a specific goal, or Ctrl+C to exit..."
read

# Get goal ID
echo "Enter goal ID to inspect:"
read GOAL_ID

# Get goal probability details
echo "Fetching probability details for goal $GOAL_ID..."
curl -s "${BASE_URL}/api/v2/debug/goal_probability/${GOAL_ID}" | jq .

# Option to recalculate
echo "Recalculate probability? (y/n)"
read RECALC

if [[ "$RECALC" == "y" ]]; then
  echo "Recalculating probability for goal $GOAL_ID..."
  curl -s -X POST "${BASE_URL}/api/v2/debug/recalculate/${GOAL_ID}" | jq .
  
  # Get updated details
  echo "Updated probability details:"
  curl -s "${BASE_URL}/api/v2/debug/goal_probability/${GOAL_ID}" | jq .
fi

echo "Done\!"

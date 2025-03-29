# Goal Model Examples

This document provides examples of working with the enhanced Goal model, including both new and legacy access patterns.

## Creating Goals

### Creating Goals with New Fields

```python
from models.goal_models import Goal
from datetime import datetime, timedelta

# Create a goal with all new fields
retirement_goal = Goal(
    user_profile_id="user-1234",
    category="traditional_retirement",
    title="Retirement Fund",
    target_amount=10000000.0,  
    timeframe=(datetime.now() + timedelta(days=365*25)).isoformat(),  # 25 years from now
    current_amount=1500000.0,
    importance="high",  
    flexibility="somewhat_flexible",
    notes="Main retirement corpus",
    additional_funding_sources="Company pension, PPF",
    goal_success_probability=75.0  # 75% success probability
)

# Access new fields
progress = retirement_goal.current_progress  # Calculated percentage
priority = retirement_goal.priority_score    # Calculated priority
strategy = retirement_goal.funding_strategy  # Empty string initially
```

### Creating Goals with Legacy Data

```python
# Legacy data format from old code or API
legacy_data = {
    "profile_id": "user-1234",
    "category": "education",
    "title": "College Fund",
    "target_value": 2500000.0,  # Using legacy field name
    "time_horizon": 10,         # Years instead of ISO date
    "current_value": 500000.0,  # Using legacy field name
    "priority": "medium",       # Using legacy field name
    "description": "Child's education fund"  # Using legacy field name
}

# Create a Goal from legacy data
education_goal = Goal.from_legacy_dict(legacy_data)

# New fields are automatically populated with defaults
print(education_goal.current_progress)  # Calculated as 20%
print(education_goal.priority_score)    # Calculated based on importance
```

## Accessing Goal Data

### Modern Field Access

```python
# Modern field access (preferred)
goal_id = education_goal.id
profile_id = education_goal.user_profile_id
title = education_goal.title
target = education_goal.target_amount
current = education_goal.current_amount
importance = education_goal.importance
timeframe = education_goal.timeframe  # ISO date string
notes = education_goal.notes
```

### Legacy Field Access (Backward Compatible)

```python
# Legacy field access (still works)
profile_id = education_goal.profile_id      # Maps to user_profile_id
target = education_goal.target_value        # Maps to target_amount
current = education_goal.current_value      # Maps to current_amount
priority = education_goal.priority          # Maps to importance
years = education_goal.time_horizon         # Converted from timeframe to years
description = education_goal.description    # Maps to notes
```

## Serializing Goals

### Modern Serialization

```python
# Serialize with all fields (default)
goal_data = education_goal.to_dict()

# goal_data includes all modern fields:
# {
#   "id": "abc123...",
#   "user_profile_id": "user-1234",
#   "category": "education",
#   "title": "College Fund",
#   "target_amount": 2500000.0,
#   "timeframe": "2033-03-19T12:34:56",
#   "current_amount": 500000.0,
#   "importance": "medium",
#   "flexibility": "somewhat_flexible",
#   "notes": "Child's education fund",
#   "created_at": "2023-03-19T12:34:56",
#   "updated_at": "2023-03-19T12:34:56",
#   "current_progress": 20.0,
#   "priority_score": 45.75,
#   "additional_funding_sources": "",
#   "goal_success_probability": 0.0,
#   "adjustments_required": false,
#   "funding_strategy": ""
# }
```

### Legacy Serialization

```python
# Serialize to legacy format for backward compatibility
legacy_goal_data = education_goal.to_dict(legacy_mode=True)

# legacy_goal_data includes only legacy fields:
# {
#   "id": "abc123...",
#   "user_profile_id": "user-1234",
#   "category": "education",
#   "title": "College Fund",
#   "target_amount": 2500000.0,
#   "timeframe": "2033-03-19T12:34:56",
#   "current_amount": 500000.0,
#   "importance": "medium",
#   "flexibility": "somewhat_flexible",
#   "notes": "Child's education fund",
#   "created_at": "2023-03-19T12:34:56",
#   "updated_at": "2023-03-19T12:34:56",
#   "priority": "medium",
#   "time_horizon": 10.0
# }
```

## Using Goal Manager

```python
from models.goal_models import GoalManager

# Create a goal manager
manager = GoalManager()

# Create and save a goal
new_goal = Goal(
    user_profile_id="user-1234",
    category="emergency_fund",
    title="Emergency Fund",
    target_amount=600000.0,
    timeframe=(datetime.now() + timedelta(days=365*1)).isoformat(),  # 1 year
    current_amount=100000.0,
    importance="high"
)

# Save to database
saved_goal = manager.create_goal(new_goal)

# Retrieve goals for a profile
profile_goals = manager.get_profile_goals("user-1234")

# Get goals by priority
priority_goals = manager.get_goals_by_priority("user-1234")

# Get goal categories by hierarchy level
security_categories = manager.get_categories_by_hierarchy_level(1)  # Level 1 = Security
```

## Goal Calculator Integration

```python
from models.goal_calculator import GoalCalculator
from models.goal_models import Goal

# Create a goal
home_goal = Goal(
    user_profile_id="user-1234",
    category="home_purchase",
    title="Home Down Payment",
    target_amount=3000000.0,
    timeframe=(datetime.now() + timedelta(days=365*3)).isoformat(),  # 3 years
    current_amount=500000.0,
    importance="high"
)

# Profile information
profile = {
    "monthly_income": 150000,
    "monthly_expenses": 90000,
    "age": 32,
    "risk_profile": "moderate"
}

# Get specialized calculator for this goal type
calculator = GoalCalculator.get_calculator_for_goal(home_goal)

# Calculate using goal object directly
required_monthly_savings = calculator.calculate_required_saving_rate(home_goal, profile)
success_probability = calculator.calculate_goal_success_probability(home_goal, profile)

# Calculator can also work with dictionary representation
goal_dict = home_goal.to_dict()
savings_from_dict = calculator.calculate_required_saving_rate(goal_dict, profile)
```
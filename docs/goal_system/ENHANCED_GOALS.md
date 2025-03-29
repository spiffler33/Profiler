# Enhanced Goal Model

This document provides an overview of the enhanced Goal model in the Profiler4 application, which adds additional fields and functionality for improved goal tracking and prioritization.

## Overview

The enhanced Goal model includes:

1. **Automated Priority Scoring**: Goals are now automatically scored and prioritized based on importance, timeframe, flexibility, and progress.
2. **Progress Tracking**: Goals track percentage progress toward completion.
3. **Advanced Planning**: New fields for funding sources, success probability, and adjustment requirements.
4. **Funding Strategy**: Structured storage of recommended funding approaches.

## New Fields

The following fields have been added to the Goal model:

- **current_progress** (float): Percentage (0.0 to 100.0) of goal completion
- **priority_score** (float): Calculated score (0.0 to 100.0) for automated prioritization
- **additional_funding_sources** (string): Other planned sources of funding
- **goal_success_probability** (float): Calculated probability (0.0 to 100.0) of achieving the goal
- **adjustments_required** (boolean): Flag indicating if goal adjustments are needed
- **funding_strategy** (string): JSON or text storing the recommended funding approach

## Migration

To add these new fields to your existing database, run the migration script:

```bash
python migrate_goals_table.py
```

The script will:
1. Back up your existing database
2. Add the new columns to the goals table
3. Calculate initial values for current_progress and priority_score
4. Update existing goals

To verify the migration, run the test script:

```bash
python test_enhanced_goals.py
```

## Using the Enhanced Goal Model

### Creating Goals with New Fields

```python
from models.goal_models import Goal, GoalManager

# Create a new goal with enhanced fields
goal = Goal(
    user_profile_id="user123",
    category="emergency_fund",
    title="Emergency Fund",
    target_amount=100000,
    current_amount=25000,  # priority_score and current_progress will be auto-calculated
    timeframe="2024-12-31",
    importance="high",
    flexibility="fixed",
    notes="6 months of expenses",
    
    # New fields (optional - will be calculated if not provided)
    additional_funding_sources="Year-end bonus, Tax refund",
    goal_success_probability=85.0,
    adjustments_required=False,
    funding_strategy='{"strategy": "monthly_contribution", "amount": 10000}'
)

# Save the goal
goal_manager = GoalManager()
saved_goal = goal_manager.create_goal(goal)
```

### Getting Goals by Priority

```python
from models.goal_models import GoalManager

goal_manager = GoalManager()

# Get all goals for a user, sorted by priority
priority_goals = goal_manager.get_goals_by_priority("user123")

# First goal is highest priority
top_priority_goal = priority_goals[0]

print(f"Top priority: {top_priority_goal.title} (Score: {top_priority_goal.priority_score})")
```

### Understanding Priority Scores

Priority scores (0-100) are calculated based on:

- **Importance** (0-50 points):
  - High importance: 50 points
  - Medium importance: 30 points
  - Low importance: 10 points

- **Urgency** (0-30 points):
  - Based on timeframe, with nearer deadlines receiving more points
  - Overdue: 30 points
  - Within 1 month: 25-30 points
  - Within 1 year: 15-25 points
  - Within 5 years: 5-15 points
  - Beyond 5 years: 0-5 points

- **Flexibility** (0-20 points):
  - Fixed goals: 20 points
  - Somewhat flexible: 10 points
  - Very flexible: 5 points

- **Progress Bonus** (0-5 points):
  - Small bonus for partially completed goals (to avoid abandonment)
  - Maximum 5 points at 50% progress

## Backwards Compatibility

The enhanced Goal model maintains full backwards compatibility with existing code. If your database hasn't been migrated yet, the model will still work with the original fields only.
# Goal Model Compatibility Layer

## Overview

The Goal model has been enhanced with additional fields and features to support richer functionality. To ensure smooth transition and backward compatibility, a compatibility layer has been implemented that allows:

1. Access to data through both new and legacy field names
2. Creation of Goal objects from both new and legacy data structures
3. Serialization to both new and legacy formats
4. Sensible defaults for all new fields

## Key Features

### Property Getters for Legacy Field Names

The Goal class now provides property getters that map new field names to old ones:

```python
# New field access pattern
goal.importance    # "high", "medium", "low"
goal.timeframe     # ISO date string
goal.target_amount # Numeric amount
goal.current_amount # Numeric amount
goal.notes         # Text notes
goal.user_profile_id # Profile ID string

# Legacy field access pattern (maps to same data)
goal.priority      # Maps to goal.importance 
goal.time_horizon  # Maps to goal.timeframe (converted to years)
goal.target_value  # Maps to goal.target_amount
goal.current_value # Maps to goal.current_amount
goal.description   # Maps to goal.notes
goal.profile_id    # Maps to goal.user_profile_id
```

### Enhanced to_dict() Method

The `to_dict()` method now accepts a `legacy_mode` parameter to control serialization format:

```python
# Modern format with all fields
data = goal.to_dict()  # Default: legacy_mode=False

# Legacy format with only legacy fields
legacy_data = goal.to_dict(legacy_mode=True)
```

### from_legacy_dict() Method

A new class method `from_legacy_dict()` allows creation of Goal objects from legacy data structures:

```python
# Legacy data format
legacy_data = {
    "profile_id": "user-123",
    "title": "My Goal",
    "target_value": 100000,
    "time_horizon": 3,  # 3 years
    "priority": "high",
    "description": "Goal description"
}

# Create a Goal from legacy data
goal = Goal.from_legacy_dict(legacy_data)
```

### Enhanced from_row() Method

The `from_row()` method has been enhanced to handle both modern and legacy database schemas:

- For modern schemas, all fields are loaded
- For legacy schemas, the method falls back to core fields and adds sensible defaults

## Migration Guide

### For New Code

New code should use the modern field names and patterns:

```python
# Creating goals with new fields
goal = Goal(
    user_profile_id="user-123",
    category="education",
    title="College Fund",
    target_amount=500000.0,
    timeframe="2030-01-01",
    current_amount=50000.0, 
    importance="high",
    flexibility="somewhat_flexible",
    notes="Fund for child's education",
    additional_funding_sources="Tax refunds",
    goal_success_probability=85.0
)

# Accessing data with modern field names
timeframe = goal.timeframe
importance = goal.importance
target = goal.target_amount
```

### For Legacy Code

Legacy code will continue to work through the compatibility layer:

```python
# Legacy pattern still works
priority = goal.priority
years = goal.time_horizon
target = goal.target_value

# Legacy serialization
legacy_dict = goal.to_dict(legacy_mode=True)
```

### Migrating Legacy Code

When you're ready to migrate legacy code:

1. Replace property access with modern field names:
   - `goal.priority` → `goal.importance`
   - `goal.time_horizon` → `goal.timeframe` (with appropriate date handling)
   - `goal.target_value` → `goal.target_amount`
   - `goal.current_value` → `goal.current_amount`
   - `goal.description` → `goal.notes`
   - `goal.profile_id` → `goal.user_profile_id`

2. Update serialization calls:
   - Replace custom serialization with `goal.to_dict()`
   - Remove any manual field mapping

3. Update creation from dictionaries:
   - Replace custom dictionary parsing with `Goal.from_dict()`
   - For legacy dictionaries, use `Goal.from_legacy_dict()`

## New Features

The compatibility layer also enables access to new features:

```python
# Access to new fields
progress = goal.current_progress  # % complete (0-100)
priority = goal.priority_score    # Calculated priority (0-100)
probability = goal.goal_success_probability  # Success probability
funding = goal.additional_funding_sources  # Additional funding info
strategy = goal.funding_strategy  # JSON or text with funding strategy
```

## Testing

To ensure backward compatibility, run the test suite:

```bash
python test_goal_backward_compatibility.py
```

This suite verifies all compatibility features and ensures that legacy code paths continue to work correctly.
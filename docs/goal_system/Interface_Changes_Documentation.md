# Interface Changes and Backward Compatibility

## Overview

This document outlines all interface changes implemented in the system and describes how backward compatibility is maintained.

## Goal Model Interface Changes

### Field Name Changes

| Legacy Field | New Field | Description |
|-------------|-----------|-------------|
| `priority` | `importance` | Goal importance level (high, medium, low) |
| `time_horizon` | `timeframe` | Changed from years (numeric) to ISO date string |
| `target_value` | `target_amount` | Monetary value target |
| `current_value` | `current_amount` | Current progress amount |
| `description` | `notes` | Descriptive text about the goal |
| `profile_id` | `user_profile_id` | Link to user profile |

### New Fields Added

| Field | Type | Description | Default |
|-------|------|-------------|--------|
| `current_progress` | Float | Percentage complete (0-100) | Calculated from amounts |
| `priority_score` | Float | Calculated priority (0-100) | Based on importance/timeframe |
| `additional_funding_sources` | String | Other funding sources | Empty string |
| `goal_success_probability` | Float | Success likelihood (0-100) | 0.0 |
| `adjustments_required` | Boolean | Indicates adjustments needed | False |
| `funding_strategy` | String | JSON-encoded funding approach | Empty string |

### Compatibility Features

1. **Property Getters**: Legacy fields are available as properties
   ```python
   # Both work the same
   goal.importance    # New field
   goal.priority      # Legacy field (maps to importance)
   ```

2. **Serialization Options**: `to_dict()` method supports both formats
   ```python
   # New format
   goal.to_dict()
   
   # Legacy format
   goal.to_dict(legacy_mode=True)
   ```

3. **Creation from Legacy Data**: `from_legacy_dict()` method converts old formats
   ```python
   legacy_data = {"priority": "high", "time_horizon": 5}
   Goal.from_legacy_dict(legacy_data)
   ```

## Financial Parameters Interface Changes

### Parameter Path Structure

Parameters now use a hierarchical dot-notation path system:

| Legacy Key | New Hierarchical Path |
|------------|------------------------|
| `inflation_rate` | `inflation.general` |
| `equity_return` | `asset_returns.equity.moderate` |
| `debt_return` | `asset_returns.debt.moderate` |
| `gold_return` | `asset_returns.alternative.gold.physical` |
| `retirement_corpus_multiplier` | `retirement.corpus_multiplier` |

### Compatibility Layer

The `ParameterCompatibilityAdapter` provides backward compatibility:

```python
# Both work the same
params.get("inflation_rate")         # Legacy key
params.get("inflation.general")      # New path
```

### New Parameter Access Methods

```python
# Specialized asset return accessor
params.get_asset_return("equity", "large_cap", "moderate")

# Allocation model accessor
params.get_allocation_model("conservative")

# Risk profile accessor
params.get_risk_profile("moderate")
```

## Goal Calculator Interface

The calculator supports both object and dictionary inputs:

```python
# Object-based access (preferred)
calculator.calculate_amount_needed(goal_object, profile)

# Dictionary-based access (legacy but still supported)
calculator.calculate_amount_needed({"target_amount": 1000000}, profile)
```

The calculator automatically handles conversion between:
- `time_horizon` (years) and `timeframe` (ISO date string)
- Legacy and modern field names

## Migration Testing

Comprehensive tests ensure compatibility:

- `test_goal_backward_compatibility.py`
- `test_parameter_compatibility.py`
- `test_goal_calculator_compatibility.py`

Run them to verify your code works with both old and new interfaces.

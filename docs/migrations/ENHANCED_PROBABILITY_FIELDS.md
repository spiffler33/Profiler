# Enhanced Goal Probability Fields Migration

## Overview

This document provides details on the migration that enhances goals with additional probability fields to support Monte Carlo simulations and scenario analysis. The migration adds new database fields, indexes, and methods to the `Goal` model to better track and manage goal success probabilities.

## New Database Fields

The migration adds the following fields to the `goals` table:

| Field | Type | Description |
|-------|------|-------------|
| `simulation_data` | TEXT | JSON-serialized Monte Carlo simulation results, including SIP information |
| `scenarios` | TEXT | JSON-serialized alternative scenarios for the goal |
| `adjustments` | TEXT | JSON-serialized recommended adjustments to improve success probability |
| `last_simulation_time` | TIMESTAMP | When the simulation was last run |
| `simulation_parameters_json` | TEXT | Parameters used for the simulation |
| `probability_partial_success` | FLOAT | Probability (0.0-100.0) of reaching at least 80% of target |
| `simulation_iterations` | INTEGER | Number of Monte Carlo iterations used (default 1000) |
| `simulation_path_data` | TEXT | JSON-serialized percentile paths for visualization (10th, 25th, 50th, 75th, 90th) |
| `monthly_sip_recommended` | FLOAT | SIP amount needed for higher success probability |
| `probability_metrics` | TEXT | JSON-serialized additional metrics like volatility, max drawdown, Sharpe ratio |
| `success_threshold` | FLOAT | User-defined threshold for "success" (default 0.8) |

## Database Indexes

The migration creates the following indexes for improved query performance:

1. `idx_goals_success_probability` - Index on `goal_success_probability` for faster sorting and filtering
2. `idx_goals_last_simulation_time` - Index on `last_simulation_time` for timestamp-based queries
3. `idx_goals_category_probability` - Composite index on `category` and `goal_success_probability` for category-based filtering

## Goal Model Enhancements

The `Goal` class has been enhanced with the following methods:

1. `get_simulation_data()` / `set_simulation_data(data)` - Manage Monte Carlo simulation results
2. `get_scenarios()` / `set_scenarios(data)` - Manage alternative financial scenarios
3. `get_adjustments()` / `set_adjustments(data)` - Manage recommended goal adjustments
4. `get_simulation_parameters()` / `set_simulation_parameters(data)` - Manage simulation parameters
5. `update_simulation_time()` - Update the last simulation timestamp to current time
6. `get_sip_details()` - Helper method to extract SIP (Systematic Investment Plan) details from simulation data
7. `get_probability_metrics()` / `set_probability_metrics(data)` - Manage probability metrics like volatility
8. `get_simulation_paths()` / `set_simulation_paths(data)` - Manage path data for visualizations

## Default Values

The migration automatically populates sensible default values for all existing goals, including:

1. `simulation_data` - Default Monte Carlo simulation data with a success rate matching the goal's `goal_success_probability`
2. `scenarios` - Default conservative, moderate, and aggressive financial scenarios
3. `adjustments` - Default adjustment recommendations if `adjustments_required` is true
4. `last_simulation_time` - Set to the current timestamp during migration
5. `simulation_parameters_json` - Default parameters based on goal category

## Indian Financial Context

The migration includes specific adaptations for the Indian financial context:

1. SIP (Systematic Investment Plan) details within the simulation data
2. Tax benefits under Section 80C and 80D for relevant goal categories
3. Indian currency formatting with lakhs and crores
4. Asset allocation models appropriate for Indian markets

## Running the Migration

Run the migration using the following command:

```bash
python migrations/runners/run_goal_probability_migration.py
```

### Command Line Options

- `--dry-run` - Run the migration in simulation mode without saving changes
- `--categories CATEGORY1,CATEGORY2` - Migrate only specific goal categories
- `--backup-only` - Create a backup without performing migration
- `--validate-only` - Only run validation queries, don't migrate
- `--rollback TIMESTAMP` - Rollback to a specified backup timestamp (YYYYMMDD_HHMMSS)

## Backward Compatibility

The migration ensures backward compatibility in several ways:

1. All new fields have default values, so older code that doesn't use these fields will still work
2. The `Goal` class maintains all existing methods and properties
3. The `to_dict()` method has a `legacy_mode` parameter to return only fields expected by legacy code
4. Database queries using the old schema will continue to work

## Validation Checks

The migration includes validation checks to ensure data integrity:

1. Verification of NULL values in all new columns
2. Validation of JSON data structure in all JSON fields
3. Checking for goals with complete vs. incomplete data
4. Verification of index creation

## Post-Migration Steps

After running the migration, you should:

1. Review the validation results to ensure data integrity
2. Run tests to verify that existing functionality continues to work
3. Update application code to use the new probability fields

## Example Usage

### Accessing Simulation Data
```python
goal = goal_manager.get_goal(goal_id)
simulation_data = goal.get_simulation_data()
success_rate = simulation_data.get('monte_carlo', {}).get('success_rate', 0)
```

### Accessing SIP Details
```python
goal = goal_manager.get_goal(goal_id)
sip_details = goal.get_sip_details()
monthly_amount = sip_details.get('monthly_amount', 0)
```

### Accessing Scenario Data
```python
goal = goal_manager.get_goal(goal_id)
scenarios = goal.get_scenarios()
conservative_probability = scenarios.get('conservative', {}).get('success_probability', 0)
```

### Updating Simulation Parameters
```python
goal = goal_manager.get_goal(goal_id)
params = goal.get_simulation_parameters()
params['expected_return'] = 10.0
goal.set_simulation_parameters(params)
goal.update_simulation_time()
goal_manager.update_goal(goal)
```

### Accessing Probability Metrics
```python
goal = goal_manager.get_goal(goal_id)
metrics = goal.get_probability_metrics()
volatility = metrics.get('volatility', 0)
max_drawdown = metrics.get('max_drawdown', 0)
sharpe_ratio = metrics.get('sharpe_ratio', 0)
```

### Accessing Simulation Paths for Visualization
```python
goal = goal_manager.get_goal(goal_id)
path_data = goal.get_simulation_paths()
percentiles = path_data.get('percentiles', {})
median_path = percentiles.get('50', [])
time_points = path_data.get('time_points', [])

# This can be used to plot a fan chart of possible outcomes
```

### Setting a Custom Success Threshold
```python
goal = goal_manager.get_goal(goal_id)
# Set a more conservative success threshold
goal.success_threshold = 0.9
goal_manager.update_goal(goal)
```
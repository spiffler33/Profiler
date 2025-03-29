# Parameter Access Patterns Guide

## Overview

This document demonstrates the various parameter access patterns supported by the system, with examples that work with both old and new code. It also provides standardized approaches for accessing financial parameters across all goal calculators in the system.

## IMPLEMENTATION STATUS

The standardized parameter access pattern has been successfully implemented in the following calculators:
- ✅ EducationCalculator
- ✅ EmergencyFundCalculator
- ✅ HomeDownPaymentCalculator 
- ✅ CharitableGivingCalculator
- ✅ RetirementCalculator
- ✅ EarlyRetirementCalculator 
- ✅ DebtRepaymentCalculator
- ✅ WeddingCalculator
- ✅ LegacyPlanningCalculator
- ✅ DiscretionaryGoalCalculator
- ✅ CustomGoalCalculator

## Standardized Calculator Parameter Access

All goal calculators should use a consistent approach to parameter access through the `get_parameter` method defined in the base `GoalCalculator` class.

### Core Principles

1. **Uniform Access Method**: Use `get_parameter` method from the base `GoalCalculator` class.
2. **Parameter Path Notation**: Use dot notation for hierarchical parameter paths.
3. **Fallback Chain**: Implement proper fallback chains to ensure resilience.
4. **User-Specific Parameters**: Enable user-specific parameter overrides where appropriate.
5. **Type Safety**: Validate and convert parameter values to appropriate types.

### Standard Parameter Access Pattern

```python
def some_calculation_method(self, goal, profile):
    # Get user ID for personalized parameters
    user_id = profile.get('user_id') if isinstance(profile, dict) else None
    
    # Get parameter with proper fallback
    parameter_value = self.get_parameter(
        "parameter.path",     # Primary parameter path
        default_value,        # Default value if not found
        user_id               # User ID for personalized parameters
    )
    
    # Use parameter value in calculation
    result = some_formula(parameter_value)
    return result
```

### Parameter Fallback Chain

The `get_parameter` method implements the following fallback chain:

1. Try to get user-specific parameter from service (if profile_id provided)
2. Try to get standard parameter from service
3. Try parameter aliases if primary path not found
4. Fall back to local params dictionary
5. Use provided default if all else fails

### Parameter Alias Mappings

The following parameter aliases are defined for backward compatibility:

```python
aliases = {
    "inflation.general": ["inflation_rate"],
    "emergency_fund.months_of_expenses": ["emergency_fund_months"],
    "retirement.corpus_multiplier": ["retirement_corpus_multiplier"],
    "retirement.life_expectancy": ["life_expectancy"],
    "housing.down_payment_percent": ["home_down_payment_percent"],
    "debt.high_interest_threshold": ["high_interest_debt_threshold"],
    "asset_returns.equity.value": ["equity_returns.moderate"],
    "asset_returns.bond.value": ["debt_returns.moderate"],
    "asset_returns.gold.value": ["gold_returns"]
}
```

## Basic Parameter Access

### Legacy Key Access (Backward Compatible)

```python
from models.financial_parameters import get_parameters

params = get_parameters()

# Basic parameter access with legacy keys
inflation = params.get("inflation_rate")
equity_return = params.get("equity_return")
debt_return = params.get("debt_return")
emergency_months = params.get("emergency_fund_months")
```

### Hierarchical Path Access (Recommended)

```python
from models.financial_parameters import get_parameters

params = get_parameters()

# Hierarchical path access - preferred approach
inflation = params.get("inflation.general")
equity_return = params.get("asset_returns.equity.moderate")
debt_return = params.get("asset_returns.debt.moderate") 
emergency_months = params.get("rules_of_thumb.emergency_fund.general")
```

## Specialized Parameter Access Methods

### Asset Returns

```python
# Access asset returns with different risk profiles
conservative_equity = params.get_asset_return("equity", None, "conservative")
moderate_equity = params.get_asset_return("equity", None, "moderate")
aggressive_equity = params.get_asset_return("equity", None, "aggressive")

# Access specific sub-asset class returns 
large_cap_return = params.get_asset_return("equity", "large_cap")
small_cap_return = params.get_asset_return("equity", "small_cap")
government_bond_return = params.get_asset_return("debt", "government")
```

### Allocation Models

```python
# Get predefined allocation models
conservative_model = params.get_allocation_model("conservative")
moderate_model = params.get_allocation_model("moderate")
aggressive_model = params.get_allocation_model("aggressive")

# Access allocation percentages
equity_allocation = conservative_model.get("equity", 0.0)
debt_allocation = conservative_model.get("debt", 0.0)
gold_allocation = conservative_model.get("gold", 0.0)

# Access sub-allocations if available
if "sub_allocation" in conservative_model:
    sub_allocations = conservative_model["sub_allocation"]
    large_cap_alloc = sub_allocations.get("equity.large_cap", 0.0)
```

### Inflation Rates

```python
# Access different inflation categories
general_inflation = params.get("inflation.general")
education_inflation = params.get("inflation.education.college")
medical_inflation = params.get("inflation.medical.general")
housing_inflation = params.get("inflation.housing.metro")
```

### Retirement Parameters

```python
# Access retirement-specific parameters
corpus_multiplier = params.get("retirement.corpus_multiplier")
life_expectancy = params.get("retirement.life_expectancy.general")
withdrawal_rate = params.get("retirement.withdrawal_rate.standard")
```

## Parameter Updates and Overrides

### Updating Parameters

```python
from models.financial_parameters import get_parameters, ParameterSource

params = get_parameters()

# Update a parameter with source and optional reason
params.update_parameter(
    "inflation.general", 
    0.07,  # 7% inflation  
    source=ParameterSource.USER_SPECIFIC,
    reason="User override based on recent market conditions"
)
```

### Temporary Parameter Overrides

```python
# Create a context with temporary parameter values
with params.override_context({
    "inflation.general": 0.08,
    "asset_returns.equity.moderate": 0.13
}):
    # Code in this block will use the overridden values
    inflation = params.get("inflation.general")  # Returns 0.08
    equity_return = params.get("asset_returns.equity.moderate")  # Returns 0.13
    
# Outside the context, original values are restored
inflation = params.get("inflation.general")  # Returns original value
```

## Bulk Parameter Operations

### Getting Multiple Parameters

```python
# Get multiple parameters at once
parameters = params.get_many([
    "inflation.general",
    "asset_returns.equity.moderate",
    "asset_returns.debt.moderate"
])

# Process results
inflation = parameters["inflation.general"]
equity_return = parameters["asset_returns.equity.moderate"]
```

### Parameter Export and Import

```python
# Export parameters to JSON
export_data = params.export_parameters()

# Save to file
with open("parameters_export.json", "w") as f:
    json.dump(export_data, f, indent=2)
    
# Import parameters from JSON
with open("parameters_import.json", "r") as f:
    import_data = json.load(f)
    
params.import_parameters(import_data)
```

## Using Parameters with Goal Calculator

### Simple Usage Pattern

```python
from models.goal_calculator import GoalCalculator
from models.goal_models import Goal

# Create a calculator
calculator = GoalCalculator()

# The calculator automatically uses financial parameters
amount_needed = calculator.calculate_amount_needed(goal, profile)
monthly_savings = calculator.calculate_required_saving_rate(goal, profile)
probability = calculator.calculate_goal_success_probability(goal, profile)
```

### Calculator-Specific Parameter Groups

Different goal calculators use specific parameter groups:

#### Emergency Fund Calculator
- `emergency_fund.months_of_expenses` (alias: `emergency_fund_months`)
- `emergency_fund.additional_cushion_percent`

#### Retirement Calculator
- `retirement.corpus_multiplier` (alias: `retirement_corpus_multiplier`)
- `retirement.life_expectancy` (alias: `life_expectancy`)
- `retirement.inflation_adjustment_factor`
- `retirement.pension_adjustment_percent`
- `inflation.general` (alias: `inflation_rate`)
- `asset_returns.equity.value` (by risk profile)
- `asset_returns.bond.value` (by risk profile)

#### Education Calculator 
- `education.cost_increase_rate` (with fallback to `inflation.general`)
- `education.annual_tuition.{education_type}`
- `education.annual_expenses.{education_type}`
- `education.loan_interest_rate.{education_type}`
- `education.loan_term_years.{education_type}`
- `education.years_until_start`

#### Home Purchase Calculator
- `housing.down_payment_percent` (alias: `home_down_payment_percent`)
- `housing.price_appreciation_rate`
- `housing.additional_costs_percent`

#### Debt Repayment Calculator
- `debt.high_interest_threshold` (alias: `high_interest_debt_threshold`)
- `debt.default_interest_rate` (default: 0.08)
- `debt.small_debt_threshold` (default: 1000)
- `debt.min_payment_percent` (default: 0.03)
- `debt.min_payment_amount` (default: 300)
- `debt.default_monthly_payment` (default: 500)
- `debt.default_min_payment` (default: 50)
- `debt.avalanche_threshold` (default: 500)

### Parameter Influence Testing

When writing tests that verify parameter influence on calculations:

```python
# Create a calculator with default inflation
baseline_calculator = EducationCalculator()
baseline_calculator.params["inflation_rate"] = 0.05

# Get baseline calculation
baseline_amount = baseline_calculator.calculate_amount_needed(education_goal, profile)

# Create a new calculator with higher inflation
new_calculator = EducationCalculator()
new_calculator.params["inflation_rate"] = 0.15

# Get new calculation
new_amount = new_calculator.calculate_amount_needed(education_goal, profile)

# Higher inflation should increase the amount needed
self.assertGreater(new_amount, baseline_amount)
```

### Real-World Example: Education Calculator

The education calculator provides a comprehensive example of proper parameter access:

```python
# Try education-specific inflation first, then fall back to general inflation
inflation_rate = self.get_parameter("education.cost_increase_rate", 
                                  None, 
                                  profile.get('user_id') if isinstance(profile, dict) else None)

# If education-specific inflation not found, use general inflation
if inflation_rate is None:
    inflation_rate = self.get_parameter("inflation.general", 0.06, 
                                      profile.get('user_id') if isinstance(profile, dict) else None)

# Get education costs from parameters
tuition_param = f"education.annual_tuition.{education_type}"
expenses_param = f"education.annual_expenses.{education_type}"

# Try to get tuition and expenses from parameters with fallback to defaults
annual_tuition = self.get_parameter(tuition_param, None, user_id)
if annual_tuition is None:
    # Fall back to default values
    annual_tuition = default_annual_tuition_values.get(education_type, 400000)
```
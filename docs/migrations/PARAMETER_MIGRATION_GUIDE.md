# Parameter System Migration Guide

## Introduction

This document provides guidance on transitioning from the old parameter key system to the new hierarchical parameter system.

The application now uses a compatibility layer that allows existing code to continue working while developers gradually update to the new system. This approach ensures:

1. No immediate breakage of existing functionality
2. Deprecation warnings to identify code that needs updates
3. A clear path to fully adopting the new parameter system

## Key Benefits of the New Hierarchical Parameter System

- **Improved Organization**: Parameters are logically grouped by domain and function
- **Better Discoverability**: Intuitive dot-notation makes finding related parameters easier
- **Contextual Relationships**: Parameter hierarchy shows relationships between values
- **Easier Maintenance**: Adding new parameters in the right context is more straightforward
- **Enhanced Documentation**: Path names are self-documenting about parameter purpose

## How to Migrate

### Step 1: Understanding the Compatibility Layer

The `ParameterCompatibilityAdapter` provides a bridge between old and new parameter access patterns:

```python
# Old way (still works but logs deprecation warnings)
inflation = financial_params.get("inflation_rate")

# New way (preferred)
inflation = financial_params.get("inflation.general")
```

### Step 2: Identifying Code to Update

Check deprecation logs or run the analysis script to identify code using legacy parameter keys:

```bash
python analyze_parameter_usage.py --create-report
```

This will generate a report showing:
- Which legacy keys are being used
- How frequently each key is accessed
- The new hierarchical path to use instead
- Recommended migration priorities

### Step 3: Migrating Parameter Access

For each instance of legacy parameter access, replace with the new dot-notation:

```python
# Before
equity_return = financial_params.get("equity_return")
debt_return = financial_params.get("debt_return_conservative")

# After
equity_return = financial_params.get("asset_returns.equity.moderate")
debt_return = financial_params.get("asset_returns.debt.conservative")
```

### Step 4: Testing Your Changes

After updating parameter access in a module:

1. Run the unit tests for that module
2. Check logs for any remaining deprecation warnings
3. Verify that the functionality works as expected

## Common Parameter Mappings

Below are the most commonly used parameter mappings:

| Legacy Key | New Hierarchical Path |
|------------|------------------------|
| inflation_rate | inflation.general |
| equity_return | asset_returns.equity.moderate |
| debt_return | asset_returns.debt.moderate |
| gold_return | asset_returns.alternative.gold.physical |
| equity_return_conservative | asset_returns.equity.conservative |
| equity_return_moderate | asset_returns.equity.moderate |
| equity_return_aggressive | asset_returns.equity.aggressive |
| retirement_corpus_multiplier | retirement.corpus_multiplier |
| life_expectancy | retirement.life_expectancy.general |
| emergency_fund_months | rules_of_thumb.emergency_fund.general |

## Specialized Parameter Access Methods

In addition to the basic `get()` method, remember these specialized methods:

```python
# Getting asset returns with risk profiles
equity_return = financial_params.get_asset_return("equity", None, "conservative")
large_cap_return = financial_params.get_asset_return("equity", "large_cap")

# Getting allocation models
allocation = financial_params.get_allocation_model("moderate")
```

## Disabling the Compatibility Layer

Once all code has been migrated to the new parameter system, you can disable the compatibility layer:

1. Set `LEGACY_ACCESS_ENABLED = False` in `financial_parameters.py`
2. Run the application and tests to ensure nothing breaks
3. If all tests pass, the migration is complete!

## Need Help?

If you encounter any issues during migration or have questions about which parameter path to use, refer to:

1. The parameter definition in `financial_parameters.py`
2. The test case examples in `test_financial_parameters.py`
3. The HTML report from the analysis script for specific recommendations

## Timeline

It's recommended to complete this migration within the next [TIME_PERIOD] to ensure all code is using the new parameter system before the compatibility layer is removed in a future release.
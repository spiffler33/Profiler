# Goal Calculator Base Class Enhancements

## Overview

This document outlines the changes needed to enhance the `GoalCalculator` base class to standardize parameter access patterns across all calculator implementations. These enhancements will ensure consistent handling of parameters, improve error resilience, and provide better integration with the `FinancialParameterService`.

## Current Issues

The current `GoalCalculator` base class:

1. Loads parameters in `__init__` but has limited error handling
2. Doesn't provide robust parameter access methods for subclasses
3. Contains a mix of direct dictionary access and conditional checks
4. Doesn't support hierarchical parameter paths consistently
5. Has minimal type checking and validation for parameters

## Proposed Enhancements

### 1. Enhanced Parameter Loading

Improve the parameter loading in `__init__` to handle more edge cases:

```python
def __init__(self):
    """Initialize the calculator with parameters from FinancialParameterService"""
    # Get financial parameter service
    self.param_service = get_financial_parameter_service()
    
    # Initialize params dictionary with default values
    self.params = self._get_default_parameters()
    
    # Load parameters from service if available
    if self.param_service:
        try:
            # Try to get calculator-specific parameters first
            calculator_name = self.__class__.__name__.lower()
            if calculator_name.endswith('calculator'):
                calculator_name = calculator_name[:-10]  # Remove 'calculator' suffix
                
            # Get parameters for this calculator type
            calculator_params = {}
            if hasattr(self.param_service, 'get_calculator_parameters'):
                calculator_params = self.param_service.get_calculator_parameters(calculator_name)
            
            # Also get all parameters as fallback
            service_params = self.param_service.get_all_parameters()
            
            # Merge parameters, with calculator-specific taking precedence
            self._update_params(service_params)
            self._update_params(calculator_params)
                
        except Exception as e:
            logger.error(f"Error loading parameters from service: {str(e)}")
            # Continue with default parameters
```

### 2. Standardized Parameter Access Methods

Add robust parameter access methods:

```python
def get_parameter(self, path, default=None, profile_id=None):
    """
    Get a parameter with consistent error handling and logging.
    
    Args:
        path: Parameter path in dot notation
        default: Default value if parameter not found
        profile_id: Optional profile ID for personalized parameters
        
    Returns:
        Parameter value or default
    """
    # Try from parameter service first if available
    if self.param_service:
        try:
            return self.param_service.get(path, default, profile_id)
        except Exception as e:
            logger.warning(f"Error getting parameter {path} from service: {str(e)}")
    
    # Try from local params dictionary
    try:
        current = self.params
        parts = path.split('.')
        
        for i, part in enumerate(parts):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # Path not found in local params
                return default
                
        return current
    except Exception as e:
        logger.warning(f"Error accessing parameter {path} in local params: {str(e)}")
        return default

def get_numeric_parameter(self, path, default=0.0, profile_id=None, min_value=None, max_value=None):
    """
    Get a numeric parameter with validation.
    
    Args:
        path: Parameter path in dot notation
        default: Default numeric value if parameter not found
        profile_id: Optional profile ID for personalized parameters
        min_value: Optional minimum value for validation
        max_value: Optional maximum value for validation
        
    Returns:
        Numeric parameter value with validation applied
    """
    value = self.get_parameter(path, default, profile_id)
    
    # Convert to numeric if it's a string
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            logger.warning(f"Parameter {path} is not a valid number: {value}")
            return default
    
    # Ensure numeric type
    if not isinstance(value, (int, float)):
        logger.warning(f"Parameter {path} is not numeric: {value}")
        return default
        
    # Apply validation if specified
    if min_value is not None and value < min_value:
        logger.warning(f"Parameter {path} value {value} below minimum {min_value}")
        return min_value
        
    if max_value is not None and value > max_value:
        logger.warning(f"Parameter {path} value {value} above maximum {max_value}")
        return max_value
        
    return value

def get_string_parameter(self, path, default="", profile_id=None):
    """
    Get a string parameter with validation.
    
    Args:
        path: Parameter path in dot notation
        default: Default string value if parameter not found
        profile_id: Optional profile ID for personalized parameters
        
    Returns:
        String parameter value
    """
    value = self.get_parameter(path, default, profile_id)
    
    # Convert to string if it's not already
    if not isinstance(value, str):
        value = str(value)
        
    return value

def get_boolean_parameter(self, path, default=False, profile_id=None):
    """
    Get a boolean parameter with validation.
    
    Args:
        path: Parameter path in dot notation
        default: Default boolean value if parameter not found
        profile_id: Optional profile ID for personalized parameters
        
    Returns:
        Boolean parameter value
    """
    value = self.get_parameter(path, default, profile_id)
    
    # Convert string to boolean if needed
    if isinstance(value, str):
        return value.lower() in ['true', 'yes', '1', 't', 'y']
        
    # Ensure boolean type
    return bool(value)

def get_list_parameter(self, path, default=None, profile_id=None):
    """
    Get a list parameter with validation.
    
    Args:
        path: Parameter path in dot notation
        default: Default list value if parameter not found
        profile_id: Optional profile ID for personalized parameters
        
    Returns:
        List parameter value
    """
    if default is None:
        default = []
        
    value = self.get_parameter(path, default, profile_id)
    
    # Convert to list if it's a string (comma-separated)
    if isinstance(value, str):
        return [item.strip() for item in value.split(',')]
        
    # Ensure list type
    if not isinstance(value, (list, tuple)):
        logger.warning(f"Parameter {path} is not a list: {value}")
        return default
        
    return value

def get_dict_parameter(self, path, default=None, profile_id=None):
    """
    Get a dictionary parameter with validation.
    
    Args:
        path: Parameter path in dot notation
        default: Default dict value if parameter not found
        profile_id: Optional profile ID for personalized parameters
        
    Returns:
        Dictionary parameter value
    """
    if default is None:
        default = {}
        
    value = self.get_parameter(path, default, profile_id)
    
    # Ensure dictionary type
    if not isinstance(value, dict):
        logger.warning(f"Parameter {path} is not a dictionary: {value}")
        return default
        
    return value
```

### 3. Helper Methods for Parameter Updates

Add helper methods for parameter management:

```python
def _get_default_parameters(self):
    """
    Get default parameters for this calculator.
    
    Returns:
        Dict: Default parameters dictionary
    """
    return {
        "inflation_rate": 0.06,  # Default: 6% annual inflation
        "emergency_fund_months": 6,  # Default: 6 months of expenses
        "high_interest_debt_threshold": 0.10,  # 10% interest rate threshold
        "gold_allocation_percent": 0.15,  # Default gold allocation
        "savings_rate_base": 0.20,  # Default savings rate: 20% of income
        "equity_returns": {
            "conservative": 0.09,  # 9% for conservative equity returns
            "moderate": 0.12,      # 12% for moderate equity returns
            "aggressive": 0.15     # 15% for aggressive equity returns
        },
        "debt_returns": {
            "conservative": 0.06,  # 6% for conservative debt returns
            "moderate": 0.07,      # 7% for moderate debt returns
            "aggressive": 0.08     # 8% for aggressive debt returns
        },
        "gold_returns": 0.08,      # 8% gold returns
        "real_estate_appreciation": 0.09,  # 9% real estate appreciation
        "retirement_corpus_multiplier": 25,  # 25x annual expenses for retirement
        "life_expectancy": 85,     # Life expectancy of 85 years
        "home_down_payment_percent": 0.20  # 20% down payment for home purchase
    }

def _update_params(self, new_params):
    """
    Update params dictionary with new values, preserving nested structure.
    
    Args:
        new_params: Dictionary of new parameters to merge
    """
    if not isinstance(new_params, dict):
        return
        
    def _merge_dicts(d1, d2):
        """Recursive dict merge"""
        for k, v in d2.items():
            if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                _merge_dicts(d1[k], v)
            else:
                d1[k] = v
    
    _merge_dicts(self.params, new_params)
```

### 4. Enhanced Calculation Methods

Improve base calculation methods for clearer parameter handling:

```python
def calculate_monthly_contribution(self, goal, profile: Dict[str, Any]) -> float:
    """
    Calculate recommended monthly contribution for a goal.
    
    Args:
        goal: The goal to calculate for
        profile: User profile
        
    Returns:
        float: Calculated monthly contribution
    """
    # Get current amount and target amount
    if isinstance(goal, dict):
        current_amount = goal.get('current_amount', 0)
        target_amount = goal.get('target_amount', 0)
    else:
        current_amount = getattr(goal, 'current_amount', 0)
        target_amount = getattr(goal, 'target_amount', 0)
        
    # If target amount is not set, calculate it
    if target_amount <= 0:
        target_amount = self.calculate_amount_needed(goal, profile)
    
    # Calculate time available in months
    months = self.calculate_time_available(goal, profile)
    
    # If no time constraint or already achieved, return 0
    if months <= 0 or current_amount >= target_amount:
        return 0.0
    
    # Calculate simple monthly contribution (no growth)
    amount_needed = target_amount - current_amount
    simple_monthly = amount_needed / months
    
    # Get risk profile
    risk_profile = self._get_risk_profile(profile)
    
    # Get expected return based on risk profile
    expected_return = self.get_numeric_parameter(
        f"equity_returns.{risk_profile}",
        default=0.08,  # 8% annual return
        min_value=0.01,  # Minimum 1% return
        max_value=0.25   # Maximum 25% return
    )
        
    # Calculate monthly contribution with compound growth
    # Formula: PMT = (FV - PV * (1 + r)^n) / (((1 + r)^n - 1) / r)
    # Where r is monthly rate, n is number of months
    monthly_rate = expected_return / 12
    
    if monthly_rate > 0:
        contribution = (target_amount - current_amount * ((1 + monthly_rate) ** months)) / (((1 + monthly_rate) ** months - 1) / monthly_rate)
    else:
        contribution = simple_monthly
    
    # Make sure contribution is positive
    return max(0, contribution)
```

### 5. Type Hints for Better IDE Support

Add comprehensive type hints:

```python
from typing import Dict, Any, List, Optional, Tuple, Union, TypeVar, cast

# Type variables
T = TypeVar('T')

def get_parameter(self, path: str, default: T = None, profile_id: Optional[str] = None) -> T:
    """Get parameter with proper type hinting"""
    # Implementation as above, with return type T

def get_numeric_parameter(self, 
                         path: str, 
                         default: float = 0.0, 
                         profile_id: Optional[str] = None,
                         min_value: Optional[float] = None, 
                         max_value: Optional[float] = None) -> float:
    """Get numeric parameter with proper type hinting"""
    # Implementation as above, with return type float
```

## Implementation Steps

1. **Update Base Calculator Class**:
   - Add enhanced parameter loading in `__init__`
   - Add standardized parameter access methods
   - Add helper methods for parameter updates
   - Add type hints for better IDE support

2. **Update Core Calculation Methods**:
   - Enhance `calculate_monthly_contribution`
   - Enhance `calculate_goal_success_probability`
   - Ensure consistent parameter access pattern

3. **Documentation**:
   - Add docstrings explaining parameter access patterns
   - Document expected parameter paths and types
   - Add examples of parameter usage

4. **Deprecation Warnings**:
   - Add warnings for direct dictionary access
   - Encourage use of standard access methods

## Expected Benefits

1. **Consistency**: All calculators will use the same parameter access pattern
2. **Resilience**: Better error handling for missing parameters
3. **Type Safety**: Proper validation for numeric, string, and boolean parameters
4. **Readability**: Clearer intention with specific getter methods
5. **Maintenance**: Easier to update parameter names or structures
6. **Testing**: Easier to mock parameters for testing
7. **IDE Support**: Better autocomplete and type checking with type hints

## Example Usage

In calculator implementations:

```python
def calculate_amount_needed(self, goal, profile: Dict[str, Any]) -> float:
    """Calculate emergency fund amount needed."""
    # Get monthly expenses
    monthly_expenses = self._get_monthly_expenses(profile)
    
    # Get months of expenses parameter
    months = self.get_numeric_parameter(
        "emergency_fund.months_of_expenses", 
        default=6,
        min_value=3,
        max_value=12
    )
    
    # Get minimum recommended amount
    minimum_amount = self.get_numeric_parameter(
        "emergency_fund.minimum_recommended", 
        default=50000
    )
    
    # Calculate required amount
    required_amount = monthly_expenses * months
    
    # Ensure at least the minimum recommended amount
    return max(required_amount, minimum_amount)
```
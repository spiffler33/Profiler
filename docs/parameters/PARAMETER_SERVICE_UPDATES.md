# Financial Parameter Service Updates

## Overview

This document outlines the specific changes needed to update the `FinancialParameterService` to properly support the modular goal calculator architecture. These changes will focus on improving parameter group definitions, adding calculator-specific access methods, and ensuring consistent parameter access patterns.

## Required Changes

### 1. Update Parameter Groups

Add the following parameter groups to `FinancialParameterService.__init__`:

```python
# Update parameter_groups dictionary with new groups for goal calculators
self._parameter_groups.update({
    'emergency_fund': [
        'emergency_fund.months_of_expenses',
        'emergency_fund.target_multiplier',
        'emergency_fund.minimum_recommended',
        'emergency_fund.cash_allocation',
        'emergency_fund.liquid_allocation'
    ],
    'retirement': [
        'retirement.withdrawal_rate',
        'retirement.life_expectancy',
        'retirement.replacement_ratio',
        'retirement.corpus_multiplier',
        'retirement.traditional.allocation.equity',
        'retirement.traditional.allocation.debt',
        'retirement.traditional.allocation.gold',
        'retirement.inflation_adjustment',
        'social_security.replacement_rate'
    ],
    'early_retirement': [
        'early_retirement.withdrawal_rate',
        'early_retirement.years_to_traditional_retirement',
        'early_retirement.corpus_multiplier',
        'early_retirement.allocation.equity',
        'early_retirement.allocation.debt',
        'early_retirement.allocation.gold',
        'early_retirement.coast_fire_threshold',
        'early_retirement.lean_fire_multiplier',
        'early_retirement.fat_fire_multiplier'
    ],
    'education': [
        'education.cost_increase_rate',
        'education.loan_interest_rate',
        'education.average_college_cost',
        'education.graduate_school_cost',
        'education.local_school_cost',
        'education.international_school_cost',
        'education.loan_interest_rates.subsidized',
        'education.loan_interest_rates.unsubsidized',
        'education.loan_interest_rates.private',
        'education.undergraduate_cost.tier1',
        'education.undergraduate_cost.tier2',
        'education.undergraduate_cost.tier3',
        'education.graduate_cost.tier1',
        'education.graduate_cost.tier2',
        'education.graduate_cost.tier3',
        'education.international_cost.us',
        'education.international_cost.uk',
        'education.international_cost.europe',
        'education.international_cost.asia'
    ],
    'home_purchase': [
        'housing.mortgage_rate',
        'housing.mortgage_rates.excellent_credit',
        'housing.mortgage_rates.good_credit',
        'housing.mortgage_rates.fair_credit',
        'housing.mortgage_rates.poor_credit',
        'housing.down_payment_percent',
        'housing.loan_terms',
        'housing.property_tax_rate',
        'housing.insurance_rate',
        'housing.pmi_rate',
        'housing.maintenance_cost_percent',
        'housing.closing_cost_percent',
        'housing.appreciation_rate',
        'housing.rent_vs_buy_threshold'
    ],
    'debt_repayment': [
        'debt.high_interest_threshold',
        'debt.priority_order',
        'debt.snowball_factor',
        'debt.avalanche_factor',
        'debt.consolidation_threshold',
        'debt.refinance_threshold',
        'debt.minimum_payment_percent',
        'debt.recommended_allocation'
    ],
    'wedding': [
        'wedding.average_cost',
        'wedding.guest_cost_factor',
        'wedding.venue_cost_percent',
        'wedding.inflation_factor',
        'wedding.food_cost_percent',
        'wedding.decoration_cost_percent',
        'wedding.attire_cost_percent'
    ],
    'discretionary': [
        'discretionary.travel.average_cost',
        'discretionary.travel.international_multiplier',
        'discretionary.vehicle.average_cost',
        'discretionary.vehicle.luxury_multiplier',
        'discretionary.vehicle.depreciation_rate',
        'discretionary.home_improvement.average_cost',
        'discretionary.home_improvement.value_return_rate'
    ],
    'legacy_planning': [
        'legacy.estate_tax_threshold',
        'legacy.inheritance_planning_cost',
        'legacy.trust_setup_cost',
        'legacy.will_cost',
        'legacy.recommended_allocation'
    ],
    'charitable_giving': [
        'charitable.tax_deduction_limit',
        'charitable.recommended_allocation',
        'charitable.gift_matching_factor',
        'charitable.donation_frequency'
    ]
})
```

### 2. Add Specialized Parameter Access Methods

Add the following methods to `FinancialParameterService`:

```python
@lru_cache(maxsize=16)
def get_emergency_fund_parameters(self, profile_id=None):
    """
    Get all emergency fund related parameters.
    
    Args:
        profile_id (str, optional): User profile ID for personalized parameters
        
    Returns:
        Dict[str, Any]: Dictionary of emergency fund parameters
    """
    return self.get_parameter_group('emergency_fund', profile_id)

@lru_cache(maxsize=16)
def get_early_retirement_parameters(self, profile_id=None):
    """
    Get all early retirement related parameters.
    
    Args:
        profile_id (str, optional): User profile ID for personalized parameters
        
    Returns:
        Dict[str, Any]: Dictionary of early retirement parameters
    """
    return self.get_parameter_group('early_retirement', profile_id)

@lru_cache(maxsize=16)
def get_home_purchase_parameters(self, profile_id=None):
    """
    Get all home purchase related parameters.
    
    Args:
        profile_id (str, optional): User profile ID for personalized parameters
        
    Returns:
        Dict[str, Any]: Dictionary of home purchase parameters
    """
    return self.get_parameter_group('home_purchase', profile_id)

@lru_cache(maxsize=16)
def get_debt_repayment_parameters(self, profile_id=None):
    """
    Get all debt repayment related parameters.
    
    Args:
        profile_id (str, optional): User profile ID for personalized parameters
        
    Returns:
        Dict[str, Any]: Dictionary of debt repayment parameters
    """
    return self.get_parameter_group('debt_repayment', profile_id)

@lru_cache(maxsize=16)
def get_wedding_parameters(self, profile_id=None):
    """
    Get all wedding related parameters.
    
    Args:
        profile_id (str, optional): User profile ID for personalized parameters
        
    Returns:
        Dict[str, Any]: Dictionary of wedding parameters
    """
    return self.get_parameter_group('wedding', profile_id)

@lru_cache(maxsize=16)
def get_discretionary_parameters(self, profile_id=None):
    """
    Get all discretionary goal related parameters.
    
    Args:
        profile_id (str, optional): User profile ID for personalized parameters
        
    Returns:
        Dict[str, Any]: Dictionary of discretionary goal parameters
    """
    return self.get_parameter_group('discretionary', profile_id)

@lru_cache(maxsize=16)
def get_legacy_planning_parameters(self, profile_id=None):
    """
    Get all legacy planning related parameters.
    
    Args:
        profile_id (str, optional): User profile ID for personalized parameters
        
    Returns:
        Dict[str, Any]: Dictionary of legacy planning parameters
    """
    return self.get_parameter_group('legacy_planning', profile_id)

@lru_cache(maxsize=16)
def get_charitable_giving_parameters(self, profile_id=None):
    """
    Get all charitable giving related parameters.
    
    Args:
        profile_id (str, optional): User profile ID for personalized parameters
        
    Returns:
        Dict[str, Any]: Dictionary of charitable giving parameters
    """
    return self.get_parameter_group('charitable_giving', profile_id)

@lru_cache(maxsize=16)
def get_calculator_parameters(self, calculator_type, profile_id=None):
    """
    Get all parameters for a specific calculator type.
    
    Args:
        calculator_type (str): The calculator type (e.g. 'emergency_fund', 'retirement')
        profile_id (str, optional): User profile ID for personalized parameters
        
    Returns:
        Dict[str, Any]: Dictionary of parameters for the specified calculator type
    """
    # Map calculator types to parameter groups
    calculator_map = {
        'emergency_fund': 'emergency_fund',
        'retirement': 'retirement',
        'early_retirement': 'early_retirement',
        'education': 'education',
        'home_purchase': 'home_purchase',
        'debt_repayment': 'debt_repayment',
        'wedding': 'wedding',
        'travel': 'discretionary',
        'vehicle': 'discretionary',
        'home_improvement': 'discretionary',
        'legacy_planning': 'legacy_planning',
        'charitable_giving': 'charitable_giving'
    }
    
    # Look up parameter group for this calculator type
    group = calculator_map.get(calculator_type)
    if not group:
        logger.warning(f"No parameter group defined for calculator type: {calculator_type}")
        return {}
        
    # Get parameters for this group
    return self.get_parameter_group(group, profile_id)
```

### 3. Update Cache Clearing Method

Update the `clear_all_caches` method to include new cache-clearing calls:

```python
def clear_all_caches(self) -> None:
    """
    Clear all parameter caches.
    """
    # Clear all in-memory caches
    self._parameter_cache = {}
    self._parameter_cache_timestamps = {}
    self._parameter_group_cache = {}
    
    # Clear lru_cache for methods
    self.get_market_assumptions.cache_clear()
    self.get_retirement_parameters.cache_clear()
    self.get_education_parameters.cache_clear()
    self.get_housing_parameters.cache_clear()
    self.get_tax_parameters.cache_clear()
    self.get_risk_profile.cache_clear()
    
    # Clear new calculator-specific caches
    self.get_emergency_fund_parameters.cache_clear()
    self.get_early_retirement_parameters.cache_clear()
    self.get_home_purchase_parameters.cache_clear()
    self.get_debt_repayment_parameters.cache_clear()
    self.get_wedding_parameters.cache_clear()
    self.get_discretionary_parameters.cache_clear()
    self.get_legacy_planning_parameters.cache_clear()
    self.get_charitable_giving_parameters.cache_clear()
    self.get_calculator_parameters.cache_clear()
    
    logger.info("All parameter caches cleared")
```

### 4. Update User Cache Clearing Method

Update the `_clear_user_caches` method to include new cache-clearing calls:

```python
def _clear_user_caches(self, profile_id: str) -> None:
    """
    Clear all caches related to a specific user.
    
    Args:
        profile_id (str): User profile ID
    """
    # Clear group caches for this user
    keys_to_remove = []
    for cache_key in self._parameter_group_cache:
        if f":{profile_id}" in cache_key:
            keys_to_remove.append(cache_key)
    
    for key in keys_to_remove:
        if key in self._parameter_group_cache:
            del self._parameter_group_cache[key]
            
    # Clear lru_cache for methods
    self.get_market_assumptions.cache_clear()
    self.get_retirement_parameters.cache_clear()
    self.get_education_parameters.cache_clear()
    self.get_housing_parameters.cache_clear()
    self.get_tax_parameters.cache_clear()
    self.get_risk_profile.cache_clear()
    
    # Clear new calculator-specific caches
    self.get_emergency_fund_parameters.cache_clear()
    self.get_early_retirement_parameters.cache_clear()
    self.get_home_purchase_parameters.cache_clear()
    self.get_debt_repayment_parameters.cache_clear()
    self.get_wedding_parameters.cache_clear()
    self.get_discretionary_parameters.cache_clear()
    self.get_legacy_planning_parameters.cache_clear()
    self.get_charitable_giving_parameters.cache_clear()
    self.get_calculator_parameters.cache_clear()
```

## Implementation Strategy

1. Make changes to `FinancialParameterService` class in `financial_parameter_service.py`
2. Add the new parameter groups to the init method
3. Add the new parameter access methods
4. Update cache clearing methods

## Testing

After implementing these changes, we need to:

1. Verify all parameter groups are correctly registered
2. Test access to each parameter group with and without profile_id
3. Ensure cache clearing correctly handles all parameter types
4. Test backward compatibility with existing code
5. Verify integration with all calculator types

## Next Steps

After implementing these changes to the `FinancialParameterService`, we will need to:

1. Update `GoalCalculator` base class to use the new parameter access methods
2. Modify individual calculator implementations to use the standard parameter access pattern
3. Move hard-coded values to the `FinancialParameters.BASE_PARAMETERS` structure
4. Create integration tests for parameter access in each calculator
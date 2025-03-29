"""Validation utilities for enhanced probability-related goal fields"""

import re
import json
import logging
from typing import Dict, List, Any, Union, Optional, Tuple
from datetime import datetime

# Initialize logging
logger = logging.getLogger(__name__)

# Constants for validation
PROBABILITY_RANGE = (0.0, 1.0)
MIN_SIP_VALUE = 500  # Minimum SIP in INR
MAX_SIP_VALUE = 10000000  # Maximum SIP in INR (1 crore)
SECTION_80C_LIMIT = 150000  # Section 80C limit - 1.5L
SECTION_80D_LIMIT = 100000  # Section 80D limit - 1L
INDIAN_GOAL_TYPES = ['education', 'wedding', 'retirement', 'home_purchase', 'emergency_fund', 
                   'debt_repayment', 'charitable_giving', 'legacy_planning', 'tax_optimization']

# Currency conversion constants
LAKH = 100000
CRORE = 10000000


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_probability_value(probability: float, name: str = "success_probability") -> Tuple[bool, str]:
    """
    Validate that a probability value is between 0 and 1.
    
    Args:
        probability: The probability value to validate
        name: Name of the probability field for error messaging
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(probability, (int, float)):
        return False, f"{name} must be a number"
        
    if probability < PROBABILITY_RANGE[0] or probability > PROBABILITY_RANGE[1]:
        return False, f"{name} must be between {PROBABILITY_RANGE[0]} and {PROBABILITY_RANGE[1]}"
        
    return True, ""


def validate_simulation_data(simulation_data: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
    """
    Validate the structure and content of Monte Carlo simulation results.
    
    Args:
        simulation_data: Dictionary containing simulation results
        
    Returns:
        Tuple of (is_valid, error_message, warnings)
    """
    warnings = []
    
    # Check if simulation_data is a dictionary
    if not isinstance(simulation_data, dict):
        return False, "simulation_data must be a dictionary", warnings
    
    # Required fields for simulation data
    required_fields = ['median_outcome', 'success_probability']
    missing_fields = [field for field in required_fields if field not in simulation_data]
    
    if missing_fields:
        return False, f"Missing required simulation data fields: {', '.join(missing_fields)}", warnings
    
    # Check success_probability
    prob_valid, prob_error = validate_probability_value(
        simulation_data.get('success_probability', -1), 
        "simulation_data.success_probability"
    )
    if not prob_valid:
        return False, prob_error, warnings
    
    # Check percentile values if they exist
    percentile_fields = ['percentile_10', 'percentile_25', 'percentile_50', 
                         'percentile_75', 'percentile_90']
    
    for field in percentile_fields:
        if field in simulation_data:
            if not isinstance(simulation_data[field], (int, float)) or simulation_data[field] < 0:
                return False, f"{field} must be a non-negative number", warnings
    
    # Validate that percentiles are in ascending order if all are present
    if all(field in simulation_data for field in percentile_fields):
        percentiles = [
            simulation_data['percentile_10'],
            simulation_data['percentile_25'],
            simulation_data['percentile_50'],
            simulation_data['percentile_75'],
            simulation_data['percentile_90']
        ]
        
        if not all(percentiles[i] <= percentiles[i+1] for i in range(len(percentiles)-1)):
            return False, "Percentile values must be in ascending order", warnings
    
    # Optional fields with their expected types
    optional_fields = {
        'simulation_count': int,
        'simulation_time_ms': (int, float),
        'confidence_interval': list,
        'distribution_type': str,
        'mean_outcome': (int, float),
        'standard_deviation': (int, float)
    }
    
    for field, expected_type in optional_fields.items():
        if field in simulation_data:
            if not isinstance(simulation_data[field], expected_type):
                type_name = expected_type.__name__ if not isinstance(expected_type, tuple) else \
                            " or ".join([t.__name__ for t in expected_type])
                return False, f"{field} must be of type {type_name}", warnings
    
    # Check for unexpected large values that could indicate errors
    numeric_fields = ['median_outcome', 'mean_outcome'] + percentile_fields
    for field in numeric_fields:
        if field in simulation_data and isinstance(simulation_data[field], (int, float)):
            if simulation_data[field] > 1000000000000:  # Greater than 1 trillion
                warnings.append(f"Warning: {field} has an unusually large value: {simulation_data[field]}")
    
    return True, "", warnings


def validate_adjustment_recommendation(adjustment: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single adjustment recommendation structure.
    
    Args:
        adjustment: Dictionary containing adjustment recommendation data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if adjustment is a dictionary
    if not isinstance(adjustment, dict):
        return False, "Adjustment must be a dictionary"
    
    # Required fields
    required_fields = ['type', 'description', 'impact']
    missing_fields = [field for field in required_fields if field not in adjustment]
    
    if missing_fields:
        return False, f"Missing required adjustment fields: {', '.join(missing_fields)}"
    
    # Validate adjustment type
    valid_types = ['contribution_increase', 'timeframe_extension', 'target_reduction', 
                   'allocation_change', 'lump_sum', 'tax_optimization', 'expense_reduction']
    
    if adjustment['type'] not in valid_types:
        return False, f"Invalid adjustment type: {adjustment['type']}. Valid types: {', '.join(valid_types)}"
    
    # Validate impact structure
    impact = adjustment.get('impact', {})
    
    # Impact can be a number or a dictionary
    if isinstance(impact, (int, float)):
        # Direct numeric impact should be a probability value
        prob_valid, prob_error = validate_probability_value(impact, "adjustment.impact")
        if not prob_valid:
            return False, prob_error
    elif isinstance(impact, dict):
        # Impact dictionary should have probability_change or new_probability
        if 'probability_change' not in impact and 'new_probability' not in impact:
            return False, "Impact dictionary must contain probability_change or new_probability"
        
        # Validate probability_change if present
        if 'probability_change' in impact:
            if not isinstance(impact['probability_change'], (int, float)):
                return False, "impact.probability_change must be a number"
        
        # Validate new_probability if present
        if 'new_probability' in impact:
            prob_valid, prob_error = validate_probability_value(
                impact.get('new_probability', -1), 
                "impact.new_probability"
            )
            if not prob_valid:
                return False, prob_error
    else:
        return False, "Impact must be a number or a dictionary"
    
    # Type-specific validations
    if adjustment['type'] == 'contribution_increase' and 'monthly_amount' in adjustment:
        if not isinstance(adjustment['monthly_amount'], (int, float)) or adjustment['monthly_amount'] <= 0:
            return False, "monthly_amount must be a positive number"
        
        # Validate SIP value range
        if adjustment['monthly_amount'] < MIN_SIP_VALUE:
            return False, f"monthly_amount must be at least ₹{MIN_SIP_VALUE}"
        if adjustment['monthly_amount'] > MAX_SIP_VALUE:
            return False, f"monthly_amount exceeds maximum value of ₹{MAX_SIP_VALUE}"
    
    if adjustment['type'] == 'timeframe_extension' and 'extend_months' in adjustment:
        if not isinstance(adjustment['extend_months'], int) or adjustment['extend_months'] <= 0:
            return False, "extend_months must be a positive integer"
    
    # Tax benefit validations
    if 'tax_benefits' in adjustment and isinstance(adjustment['tax_benefits'], dict):
        for section, amount in adjustment['tax_benefits'].items():
            if not isinstance(amount, (int, float)) or amount < 0:
                return False, f"Tax benefit amount for {section} must be a non-negative number"
            
            # Validate section-specific limits
            if section == '80C' and amount > SECTION_80C_LIMIT:
                return False, f"80C benefit exceeds limit of ₹{SECTION_80C_LIMIT}"
            if section == '80D' and amount > SECTION_80D_LIMIT:
                return False, f"80D benefit exceeds limit of ₹{SECTION_80D_LIMIT}"
    
    return True, ""


def validate_adjustment_recommendations(adjustments: List[Dict[str, Any]]) -> Tuple[bool, str, List[str]]:
    """
    Validate a list of adjustment recommendations.
    
    Args:
        adjustments: List of adjustment recommendation dictionaries
        
    Returns:
        Tuple of (is_valid, error_message, warnings)
    """
    warnings = []
    
    # Check if adjustments is a list
    if not isinstance(adjustments, list):
        return False, "Adjustments must be a list", warnings
    
    # Empty list is valid, but generate a warning
    if not adjustments:
        warnings.append("Warning: Empty list of adjustments")
        return True, "", warnings
    
    # Validate each adjustment
    for i, adjustment in enumerate(adjustments):
        valid, error = validate_adjustment_recommendation(adjustment)
        if not valid:
            return False, f"Invalid adjustment at index {i}: {error}", warnings
    
    # Check for duplicate adjustment types
    adjustment_types = [adj['type'] for adj in adjustments]
    if len(adjustment_types) != len(set(adjustment_types)):
        warnings.append("Warning: Multiple adjustments of the same type found")
    
    return True, "", warnings


def validate_scenario(scenario: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single scenario structure.
    
    Args:
        scenario: Dictionary containing scenario data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if scenario is a dictionary
    if not isinstance(scenario, dict):
        return False, "Scenario must be a dictionary"
    
    # Required fields
    required_fields = ['id', 'name', 'probability', 'parameters']
    missing_fields = [field for field in required_fields if field not in scenario]
    
    if missing_fields:
        return False, f"Missing required scenario fields: {', '.join(missing_fields)}"
    
    # Validate scenario ID format (should be UUID or string with baseline indicator)
    scenario_id = scenario.get('id', '')
    if not isinstance(scenario_id, str) or not scenario_id:
        return False, "Scenario ID must be a non-empty string"
    
    # Validate probability
    prob_valid, prob_error = validate_probability_value(
        scenario.get('probability', -1), 
        "scenario.probability"
    )
    if not prob_valid:
        return False, prob_error
    
    # Validate parameters
    parameters = scenario.get('parameters', {})
    if not isinstance(parameters, dict):
        return False, "Scenario parameters must be a dictionary"
    
    # Validate is_baseline field if present
    if 'is_baseline' in scenario and not isinstance(scenario['is_baseline'], bool):
        return False, "is_baseline must be a boolean"
    
    # Validate created_at field if present
    if 'created_at' in scenario:
        created_at = scenario['created_at']
        if not isinstance(created_at, str):
            return False, "created_at must be a string"
        
        # Try to parse as ISO format date
        try:
            datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError:
            return False, "created_at must be in ISO format (YYYY-MM-DDTHH:MM:SS.sssZ)"
    
    return True, ""


def validate_scenarios(scenarios: List[Dict[str, Any]], goal_id: str = None) -> Tuple[bool, str, List[str]]:
    """
    Validate a list of scenarios and their relationships.
    
    Args:
        scenarios: List of scenario dictionaries
        goal_id: Optional goal ID to validate scenario relationships
        
    Returns:
        Tuple of (is_valid, error_message, warnings)
    """
    warnings = []
    
    # Check if scenarios is a list
    if not isinstance(scenarios, list):
        return False, "Scenarios must be a list", warnings
    
    # Empty list is valid, but generate a warning
    if not scenarios:
        warnings.append("Warning: Empty list of scenarios")
        return True, "", warnings
    
    # Validate each scenario
    scenario_ids = set()
    baseline_scenarios = []
    
    for i, scenario in enumerate(scenarios):
        valid, error = validate_scenario(scenario)
        if not valid:
            return False, f"Invalid scenario at index {i}: {error}", warnings
        
        # Check for duplicate scenario IDs
        if scenario['id'] in scenario_ids:
            return False, f"Duplicate scenario ID: {scenario['id']}", warnings
        scenario_ids.add(scenario['id'])
        
        # Track baseline scenarios
        if scenario.get('is_baseline', False):
            baseline_scenarios.append(scenario)
    
    # Validate baseline scenarios
    if len(baseline_scenarios) > 1:
        return False, "Multiple baseline scenarios found. There should be at most one.", warnings
    
    # If goal_id is provided, validate that baseline scenario ID follows convention
    if goal_id and baseline_scenarios:
        expected_baseline_id = f"{goal_id}_baseline"
        if baseline_scenarios[0]['id'] != expected_baseline_id:
            warnings.append(f"Warning: Baseline scenario ID '{baseline_scenarios[0]['id']}' does not match expected format '{expected_baseline_id}'")
    
    # Check for consistent parameter structure across scenarios
    if len(scenarios) > 1:
        parameter_keys = [set(scenario.get('parameters', {}).keys()) for scenario in scenarios]
        if not all(keys == parameter_keys[0] for keys in parameter_keys):
            warnings.append("Warning: Inconsistent parameter structure across scenarios")
    
    return True, "", warnings


def validate_sip_value(sip_value: float) -> Tuple[bool, str]:
    """
    Validate that a SIP (Systematic Investment Plan) value is within valid range.
    
    Args:
        sip_value: The SIP amount to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(sip_value, (int, float)):
        return False, "SIP value must be a number"
        
    if sip_value < MIN_SIP_VALUE:
        return False, f"SIP value must be at least ₹{MIN_SIP_VALUE}"
        
    if sip_value > MAX_SIP_VALUE:
        return False, f"SIP value exceeds maximum value of ₹{MAX_SIP_VALUE}"
        
    return True, ""


def validate_tax_benefit_calculation(tax_benefits: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
    """
    Validate tax benefit calculations for compliance with Indian tax regulations.
    
    Args:
        tax_benefits: Dictionary of tax benefit calculations
        
    Returns:
        Tuple of (is_valid, error_message, warnings)
    """
    warnings = []
    
    # Check if tax_benefits is a dictionary
    if not isinstance(tax_benefits, dict):
        return False, "Tax benefits must be a dictionary", warnings
    
    # Empty dictionary is valid, but generate a warning
    if not tax_benefits:
        warnings.append("Warning: Empty tax benefits dictionary")
        return True, "", warnings
    
    # Validate known tax deduction sections
    valid_sections = {'80C', '80CCC', '80CCD', '80D', '80E', '80EE', '80G', '24'}
    unknown_sections = [section for section in tax_benefits.keys() if section not in valid_sections]
    
    if unknown_sections:
        warnings.append(f"Warning: Unknown tax sections: {', '.join(unknown_sections)}")
    
    # Validate section-specific limits
    if '80C' in tax_benefits:
        amount = tax_benefits['80C']
        if not isinstance(amount, (int, float)) or amount < 0:
            return False, "80C benefit must be a non-negative number", warnings
        if amount > SECTION_80C_LIMIT:
            return False, f"80C benefit exceeds limit of ₹{SECTION_80C_LIMIT}", warnings
    
    if '80D' in tax_benefits:
        amount = tax_benefits['80D']
        if not isinstance(amount, (int, float)) or amount < 0:
            return False, "80D benefit must be a non-negative number", warnings
        if amount > SECTION_80D_LIMIT:
            return False, f"80D benefit exceeds limit of ₹{SECTION_80D_LIMIT}", warnings
    
    # Validate total benefits don't exceed reasonable limits
    total_benefits = sum(amount for amount in tax_benefits.values() if isinstance(amount, (int, float)))
    if total_benefits > 500000:  # 5 lakh
        warnings.append(f"Warning: Total tax benefits (₹{total_benefits}) exceed ₹500,000, verify calculations")
    
    return True, "", warnings


def validate_indian_currency_format(value: str) -> Tuple[bool, float, str]:
    """
    Validate and parse an Indian currency format string (with lakhs and crores).
    
    Args:
        value: String representation of currency value (e.g. "5 lakh", "1.2 Cr")
        
    Returns:
        Tuple of (is_valid, numeric_value, error_message)
    """
    if not isinstance(value, str):
        return False, 0, "Currency value must be a string"
    
    # Remove any currency symbols and whitespace
    value = value.replace('₹', '').replace('Rs.', '').replace('Rs', '').strip()
    
    # Try to match lakh/crore format
    lakh_pattern = re.compile(r'^([\d,]+(?:\.\d+)?)\s*(?:lakh|lacs|lac|l|lk)s?$', re.IGNORECASE)
    crore_pattern = re.compile(r'^([\d,]+(?:\.\d+)?)\s*(?:crore|cr|c)s?$', re.IGNORECASE)
    
    lakh_match = lakh_pattern.match(value)
    crore_match = crore_pattern.match(value)
    
    if lakh_match:
        try:
            # Remove commas and convert to float
            amount_str = lakh_match.group(1).replace(',', '')
            amount = float(amount_str)
            return True, amount * LAKH, ""
        except ValueError:
            return False, 0, f"Could not parse lakh value: {value}"
    
    if crore_match:
        try:
            # Remove commas and convert to float
            amount_str = crore_match.group(1).replace(',', '')
            amount = float(amount_str)
            return True, amount * CRORE, ""
        except ValueError:
            return False, 0, f"Could not parse crore value: {value}"
    
    # Try direct numeric parsing
    try:
        # Remove commas and convert to float
        amount = float(value.replace(',', ''))
        return True, amount, ""
    except ValueError:
        return False, 0, f"Invalid currency format: {value}"


def validate_india_specific_goal_type(goal_type: str, goal_data: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
    """
    Validate India-specific goal types and their parameters.
    
    Args:
        goal_type: The type/category of the goal
        goal_data: Dictionary containing goal data
        
    Returns:
        Tuple of (is_valid, error_message, warnings)
    """
    warnings = []
    
    if goal_type not in INDIAN_GOAL_TYPES:
        # Not an India-specific goal type, so it's valid by default
        return True, "", warnings
    
    # Validation for education goal
    if goal_type == 'education':
        if 'funding_strategy' not in goal_data:
            return False, "Education goal requires funding_strategy", warnings
            
        strategy = goal_data.get('funding_strategy', {})
        if isinstance(strategy, str):
            try:
                strategy = json.loads(strategy)
            except json.JSONDecodeError:
                return False, "Invalid funding_strategy format", warnings
        
        if not isinstance(strategy, dict):
            return False, "funding_strategy must be a dictionary", warnings
            
        # Validate education-specific fields
        required_fields = ['education_type', 'years', 'yearly_cost']
        missing_fields = [field for field in required_fields if field not in strategy]
        
        if missing_fields:
            return False, f"Missing required education strategy fields: {', '.join(missing_fields)}", warnings
            
        # Validate education type
        valid_edu_types = ['school', 'college', 'graduate', 'postgraduate', 'overseas']
        if strategy['education_type'] not in valid_edu_types:
            return False, f"Invalid education type: {strategy['education_type']}", warnings
            
        # Validate years
        if not isinstance(strategy['years'], (int, float)) or strategy['years'] <= 0:
            return False, "Years must be a positive number", warnings
            
        # Validate yearly cost
        if not isinstance(strategy['yearly_cost'], (int, float)) or strategy['yearly_cost'] <= 0:
            return False, "Yearly cost must be a positive number", warnings
    
    # Validation for marriage goal
    elif goal_type == 'marriage':
        # Add India-specific marriage goal validations here
        pass
    
    # Validation for retirement goal
    elif goal_type == 'retirement':
        if 'funding_strategy' not in goal_data:
            return False, "Retirement goal requires funding_strategy", warnings
            
        strategy = goal_data.get('funding_strategy', {})
        if isinstance(strategy, str):
            try:
                strategy = json.loads(strategy)
            except json.JSONDecodeError:
                return False, "Invalid funding_strategy format", warnings
        
        if not isinstance(strategy, dict):
            return False, "funding_strategy must be a dictionary", warnings
            
        # Validate retirement-specific fields
        if 'retirement_age' in strategy and (not isinstance(strategy['retirement_age'], int) or 
                                            strategy['retirement_age'] < 45 or 
                                            strategy['retirement_age'] > 80):
            return False, "Retirement age must be between 45 and 80", warnings
            
        if 'withdrawal_rate' in strategy and (not isinstance(strategy['withdrawal_rate'], (int, float)) or 
                                            strategy['withdrawal_rate'] <= 0 or 
                                            strategy['withdrawal_rate'] > 0.1):
            return False, "Withdrawal rate must be between 0 and 0.1 (10%)", warnings
    
    # Validation for home purchase goal
    elif goal_type == 'home_purchase':
        if 'funding_strategy' not in goal_data:
            return False, "Home purchase goal requires funding_strategy", warnings
            
        strategy = goal_data.get('funding_strategy', {})
        if isinstance(strategy, str):
            try:
                strategy = json.loads(strategy)
            except json.JSONDecodeError:
                return False, "Invalid funding_strategy format", warnings
        
        if not isinstance(strategy, dict):
            return False, "funding_strategy must be a dictionary", warnings
            
        # Validate home purchase-specific fields
        if 'property_value' in strategy and (not isinstance(strategy['property_value'], (int, float)) or 
                                           strategy['property_value'] <= 0):
            return False, "Property value must be a positive number", warnings
            
        if 'down_payment_percent' in strategy and (not isinstance(strategy['down_payment_percent'], (int, float)) or 
                                                 strategy['down_payment_percent'] <= 0 or 
                                                 strategy['down_payment_percent'] > 1):
            return False, "Down payment percentage must be between 0 and 1", warnings
    
    return True, "", warnings


def format_error_messages(errors: List[str]) -> str:
    """
    Format a list of error messages into a single, readable string.
    
    Args:
        errors: List of error messages
        
    Returns:
        Formatted error message string
    """
    if not errors:
        return ""
    
    if len(errors) == 1:
        return errors[0]
    
    return "Multiple validation errors:\n" + "\n".join(f"- {error}" for error in errors)


def convert_validation_errors_to_api_response(errors: List[str], warnings: List[str] = None) -> Dict[str, Any]:
    """
    Convert validation errors to a standardized API response format.
    
    Args:
        errors: List of error messages
        warnings: Optional list of warning messages
        
    Returns:
        API response dictionary
    """
    if warnings is None:
        warnings = []
    
    response = {
        'errors': errors,
        'warnings': warnings,
        'is_valid': len(errors) == 0
    }
    
    if errors:
        response['message'] = format_error_messages(errors)
        response['status_code'] = 400  # Bad Request
    else:
        response['message'] = "Validation successful" + (f" with {len(warnings)} warnings" if warnings else "")
        response['status_code'] = 200  # OK
    
    return response


def batch_validate_goal_fields(goal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate multiple goal fields in a single call.
    
    Args:
        goal_data: Dictionary containing all goal data to validate
        
    Returns:
        Dictionary with validation results for each field
    """
    results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'field_results': {}
    }
    
    # Validate probability if present
    if 'success_probability' in goal_data:
        valid, error = validate_probability_value(goal_data['success_probability'])
        results['field_results']['success_probability'] = {
            'is_valid': valid,
            'error': error
        }
        if not valid:
            results['is_valid'] = False
            results['errors'].append(error)
    
    # Validate simulation data if present
    if 'simulation_data' in goal_data:
        valid, error, warnings = validate_simulation_data(goal_data['simulation_data'])
        results['field_results']['simulation_data'] = {
            'is_valid': valid,
            'error': error,
            'warnings': warnings
        }
        if not valid:
            results['is_valid'] = False
            results['errors'].append(error)
        results['warnings'].extend(warnings)
    
    # Validate adjustments if present
    if 'adjustments' in goal_data:
        valid, error, warnings = validate_adjustment_recommendations(goal_data['adjustments'])
        results['field_results']['adjustments'] = {
            'is_valid': valid,
            'error': error,
            'warnings': warnings
        }
        if not valid:
            results['is_valid'] = False
            results['errors'].append(error)
        results['warnings'].extend(warnings)
    
    # Validate scenarios if present
    if 'scenarios' in goal_data:
        valid, error, warnings = validate_scenarios(
            goal_data['scenarios'], 
            goal_data.get('id')
        )
        results['field_results']['scenarios'] = {
            'is_valid': valid,
            'error': error,
            'warnings': warnings
        }
        if not valid:
            results['is_valid'] = False
            results['errors'].append(error)
        results['warnings'].extend(warnings)
    
    # Validate India-specific fields if applicable
    if 'category' in goal_data and goal_data['category'] in INDIAN_GOAL_TYPES:
        valid, error, warnings = validate_india_specific_goal_type(
            goal_data['category'], 
            goal_data
        )
        results['field_results']['india_specific'] = {
            'is_valid': valid,
            'error': error,
            'warnings': warnings
        }
        if not valid:
            results['is_valid'] = False
            results['errors'].append(error)
        results['warnings'].extend(warnings)
    
    # If SIP values are present, validate them
    if 'monthly_contribution' in goal_data:
        valid, error = validate_sip_value(goal_data['monthly_contribution'])
        results['field_results']['monthly_contribution'] = {
            'is_valid': valid,
            'error': error
        }
        if not valid:
            results['is_valid'] = False
            results['errors'].append(error)
    
    # If tax benefits are present, validate them
    if 'tax_benefits' in goal_data:
        valid, error, warnings = validate_tax_benefit_calculation(goal_data['tax_benefits'])
        results['field_results']['tax_benefits'] = {
            'is_valid': valid,
            'error': error,
            'warnings': warnings
        }
        if not valid:
            results['is_valid'] = False
            results['errors'].append(error)
        results['warnings'].extend(warnings)
    
    return results
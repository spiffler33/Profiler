"""
Core Monte Carlo simulation functionality.

This module provides the core implementation for Monte Carlo simulations,
including parameter validation, data preparation, and error handling.
It consolidates functionality from various fix modules to create a unified interface.
"""

import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import traceback

# Import local modules
from models.monte_carlo.cache import _cache
from models.monte_carlo.array_fix import to_scalar, safe_array_compare

# Set up logging
logger = logging.getLogger(__name__)

# Re-export core functionality from fix modules
def validate_simulation_parameters(parameters: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate simulation parameters.
    
    Args:
        parameters: The simulation parameters to validate
        
    Returns:
        Dictionary of validation errors, empty if no errors
    """
    errors = {}
    
    # Required parameters
    required = ["target_amount", "current_amount", "monthly_contribution"]
    for param in required:
        if param not in parameters:
            errors[param] = f"Missing required parameter: {param}"
    
    # Numeric parameters
    numeric_params = ["target_amount", "current_amount", "monthly_contribution", "annual_return"]
    for param in numeric_params:
        if param in parameters:
            try:
                float(parameters[param])
            except (ValueError, TypeError):
                errors[param] = f"{param} must be a number"
    
    # Range validations
    if "annual_return" in parameters and not errors.get("annual_return"):
        annual_return = float(parameters["annual_return"])
        if annual_return < -1.0 or annual_return > 1.0:
            errors["annual_return"] = "annual_return must be between -1.0 and 1.0"
    
    return errors

def prepare_simulation_data(goal: Dict[str, Any], years: int = 5) -> Dict[str, Any]:
    """
    Prepare simulation data for a goal.
    
    Args:
        goal: The goal data
        years: Number of years to simulate
        
    Returns:
        Dictionary with simulation data
    """
    # Extract base parameters
    try:
        # Handle different data types for target_amount
        target_amount = float(goal.get("target_amount", 0))
        current_amount = float(goal.get("current_amount", 0))
        monthly_contribution = float(goal.get("monthly_contribution", 0))
        
        # Get annual return from funding strategy if available
        annual_return = 0.07  # Default
        funding_strategy = goal.get("funding_strategy", {})
        if isinstance(funding_strategy, str):
            try:
                funding_strategy = json.loads(funding_strategy)
            except json.JSONDecodeError:
                funding_strategy = {}
        
        if isinstance(funding_strategy, dict):
            annual_return = float(funding_strategy.get("annual_return", 0.07))
        
        # Generate simulation data
        sim_data = []
        current_value = current_amount
        
        for year in range(years + 1):
            year_data = {
                "year": year,
                "value": round(current_value, 2),
                "target": target_amount,
                "progress_pct": min(100, round(current_value / target_amount * 100, 1)) if target_amount > 0 else 0
            }
            sim_data.append(year_data)
            
            # Calculate growth for next year
            annual_contribution = monthly_contribution * 12
            growth = current_value * annual_return
            current_value = current_value + growth + annual_contribution
        
        return {
            "simulation_id": str(uuid.uuid4()),
            "goal_id": goal.get("id", ""),
            "goal_category": goal.get("category", ""),
            "timeframe_years": years,
            "target_amount": target_amount,
            "annual_return": annual_return,
            "monthly_contribution": monthly_contribution,
            "data": sim_data,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "parameters_used": {
                    "target_amount": target_amount,
                    "current_amount": current_amount,
                    "monthly_contribution": monthly_contribution,
                    "annual_return": annual_return
                }
            }
        }
    
    except Exception as e:
        # Log error and return minimal valid data
        logger.error(f"Error in prepare_simulation_data: {str(e)}")
        return {
            "simulation_id": str(uuid.uuid4()),
            "goal_id": goal.get("id", ""),
            "goal_category": goal.get("category", ""),
            "timeframe_years": years,
            "error": str(e),
            "data": [{"year": 0, "value": float(goal.get("current_amount", 0)), "target": float(goal.get("target_amount", 0)), "progress_pct": 0}],
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "error_occurred": True
            }
        }

def safely_get_simulation_data(goal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely extract simulation data from a goal.
    
    Args:
        goal: The goal object or dictionary
        
    Returns:
        Dictionary with simulation data
    """
    simulation_data = {}
    
    # Try to get simulation_data from goal
    if hasattr(goal, 'simulation_data') or (isinstance(goal, dict) and 'simulation_data' in goal):
        # Get the simulation_data attribute
        sim_data_raw = goal.simulation_data if hasattr(goal, 'simulation_data') else goal.get('simulation_data')
        
        # Handle string or dict
        if isinstance(sim_data_raw, str):
            try:
                simulation_data = json.loads(sim_data_raw)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse simulation_data JSON for goal {goal.get('id', 'unknown')}")
                simulation_data = {}
        elif isinstance(sim_data_raw, dict):
            simulation_data = sim_data_raw
    
    # Ensure we have minimal valid simulation data
    if not simulation_data:
        # Create default simulation data
        simulation_data = {
            "success_probability": goal.get("goal_success_probability", 0.0),
            "median_outcome": goal.get("target_amount", 0),
            "percentile_10": 0,
            "percentile_25": 0,
            "percentile_50": goal.get("target_amount", 0),
            "percentile_75": 0,
            "percentile_90": 0,
            "simulation_count": 1000
        }
    
    return simulation_data

def safely_get_scenarios(goal: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Safely extract scenarios from a goal.
    
    Args:
        goal: The goal object or dictionary
        
    Returns:
        List of scenario dictionaries
    """
    scenarios = []
    
    # Try to get scenarios from goal
    if hasattr(goal, 'scenarios') or (isinstance(goal, dict) and 'scenarios' in goal):
        # Get the scenarios attribute
        scenarios_raw = goal.scenarios if hasattr(goal, 'scenarios') else goal.get('scenarios')
        
        # Handle string or list
        if isinstance(scenarios_raw, str):
            try:
                scenarios = json.loads(scenarios_raw)
                if not isinstance(scenarios, list):
                    scenarios = []
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse scenarios JSON for goal {goal.get('id', 'unknown')}")
                scenarios = []
        elif isinstance(scenarios_raw, list):
            scenarios = scenarios_raw
    
    return scenarios

def safely_get_adjustments(goal: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Safely extract adjustments from a goal.
    
    Args:
        goal: The goal object or dictionary
        
    Returns:
        List of adjustment dictionaries
    """
    adjustments = []
    
    # Try to get adjustments from goal
    if hasattr(goal, 'adjustments') or (isinstance(goal, dict) and 'adjustments' in goal):
        # Get the adjustments attribute
        adjustments_raw = goal.adjustments if hasattr(goal, 'adjustments') else goal.get('adjustments')
        
        # Handle string or list
        if isinstance(adjustments_raw, str):
            try:
                adjustments = json.loads(adjustments_raw)
                if not isinstance(adjustments, list):
                    adjustments = []
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse adjustments JSON for goal {goal.get('id', 'unknown')}")
                adjustments = []
        elif isinstance(adjustments_raw, list):
            adjustments = adjustments_raw
    
    return adjustments

def ensure_attributes_exist(probability_result: Any) -> Dict[str, Any]:
    """
    Ensure that probability result has all required attributes.
    
    Args:
        probability_result: The probability result object
        
    Returns:
        Updated probability result with all required attributes
    """
    # Ensure it's a dict or object we can work with
    if probability_result is None:
        probability_result = {}
    
    # Expected attributes and their default values
    expected_attributes = {
        "probability": 0.0,
        "simulation_count": 1000,
        "confidence_interval": [],
        "convergence_rate": 0.98,
        "simulation_results": {}
    }
    
    # If it's a dict, ensure all expected attributes exist
    if isinstance(probability_result, dict):
        for attr, default in expected_attributes.items():
            if attr not in probability_result:
                probability_result[attr] = default
    else:
        # Try to convert to a dict
        try:
            result_dict = {}
            for attr, default in expected_attributes.items():
                if hasattr(probability_result, attr):
                    result_dict[attr] = getattr(probability_result, attr)
                else:
                    result_dict[attr] = default
            probability_result = result_dict
        except Exception as e:
            logger.error(f"Error converting probability result to dict: {str(e)}")
            probability_result = expected_attributes
    
    return probability_result

def create_error_response(error_message: str, goal_id: str = None) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_message: The error message
        goal_id: Optional goal ID
        
    Returns:
        Error response dictionary
    """
    response = {
        "error": True,
        "error_message": error_message,
        "timestamp": datetime.now().isoformat()
    }
    
    if goal_id:
        response["goal_id"] = goal_id
        
    return response

def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format a currency amount based on locale.
    
    Args:
        amount: The amount to format
        currency: The currency code (default: USD)
        
    Returns:
        Formatted currency string
    """
    if currency == "INR":
        # Format for Indian Rupees (lakhs)
        if abs(amount) >= 100000:
            return f"₹{amount/100000:.2f} L"
        else:
            return f"₹{amount:,.2f}"
    else:
        # Default formatting
        return f"${amount:,.2f}"

def cache_response(key: str, data: Any, ttl: int = None) -> None:
    """
    Cache a response for future requests.
    
    Args:
        key: Cache key
        data: Data to cache
        ttl: Optional time-to-live in seconds
    """
    try:
        # Try to set with TTL
        if ttl is not None:
            _cache.set(key, data, ttl=ttl)
        else:
            _cache.set(key, data)
    except (TypeError, AttributeError) as e:
        # Fall back to simple set if ttl not supported
        logger.warning(f"Error setting cache with TTL: {str(e)}")
        _cache.set(key, data)
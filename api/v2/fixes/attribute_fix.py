"""
Fixed implementation for safer attribute access in probability results.

This module provides helper functions for accessing attributes safely.
"""

def get_probability_result_attribute(result, attr_name, default=None):
    """
    Safely get an attribute from a probability result object.
    
    Args:
        result: The probability result object
        attr_name: The name of the attribute to retrieve
        default: The default value to return if the attribute is not found
        
    Returns:
        The attribute value or the default value
    """
    # Handle both object attribute access and dictionary key access
    try:
        if hasattr(result, attr_name):
            value = getattr(result, attr_name, default)
        elif isinstance(result, dict) and attr_name in result:
            value = result[attr_name]
        else:
            return default
            
        # Validate numeric values
        if attr_name in ('probability', 'success_probability') and (value is None or not isinstance(value, (int, float))):
            return default
            
        return value
    except Exception:
        return default

def get_simulation_metrics(result):
    """
    Extract simulation metrics from a probability result.
    
    Args:
        result: The probability result object
        
    Returns:
        Dictionary with simulation metrics
    """
    # Base metrics
    metrics = {
        "simulation_count": get_probability_result_attribute(result, "simulation_count", 1000),
        "confidence_interval": get_probability_result_attribute(result, "confidence_interval", []),
        "convergence_rate": get_probability_result_attribute(result, "convergence_rate", 0.98)
    }
    
    # Add additional metrics if available
    for attr in ["percentile_10", "percentile_25", "percentile_50", "percentile_75", "percentile_90", "median_outcome"]:
        metrics[attr] = get_probability_result_attribute(result, attr, 0)
        
    return metrics
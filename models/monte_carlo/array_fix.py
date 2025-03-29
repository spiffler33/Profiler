"""
Fixes for array truth value errors in NumPy operations.

This module provides utility functions to handle the "truth value of an array is ambiguous" error
that occurs when a NumPy array is used in a boolean context.
"""

import numpy as np
import functools
import logging
from typing import Union, Any, Callable

logger = logging.getLogger(__name__)

def safe_array_compare(array: Union[np.ndarray, float, None], value: float, comparison: str = 'gt') -> bool:
    """
    Safely compare a NumPy array with a scalar value.
    
    Args:
        array: NumPy array to compare
        value: Scalar value to compare against
        comparison: Type of comparison ('gt', 'lt', 'ge', 'le', 'eq', 'ne')
    
    Returns:
        Boolean result of the comparison
    """
    if array is None:
        return False
        
    if not isinstance(array, np.ndarray):
        # Handle scalar case
        if comparison == 'gt':
            return array > value
        elif comparison == 'lt':
            return array < value
        elif comparison == 'ge':
            return array >= value
        elif comparison == 'le':
            return array <= value
        elif comparison == 'eq':
            return array == value
        elif comparison == 'ne':
            return array != value
        else:
            raise ValueError(f"Unsupported comparison: {comparison}")
    
    # Handle array case using appropriate NumPy function
    if comparison == 'gt':
        return np.any(array > value)
    elif comparison == 'lt':
        return np.any(array < value)
    elif comparison == 'ge':
        return np.any(array >= value)
    elif comparison == 'le':
        return np.any(array <= value)
    elif comparison == 'eq':
        return np.any(array == value)
    elif comparison == 'ne':
        return np.any(array != value)
    else:
        raise ValueError(f"Unsupported comparison: {comparison}")

def to_scalar(value: Union[np.ndarray, float, int, None]) -> float:
    """
    Convert a NumPy array or scalar to a Python scalar.
    
    Args:
        value: NumPy array or scalar value
        
    Returns:
        Python scalar (float)
    """
    if value is None:
        return 0.0
        
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return 0.0
        elif value.size == 1:
            # Single-element array
            return float(value.item())
        else:
            # Multi-element array, use mean
            return float(np.mean(value))
    
    # Handle other numpy types like np.float64
    if hasattr(value, 'item') and callable(getattr(value, 'item')):
        return float(value.item())
        
    # Already a scalar
    return float(value)

def safe_median(array: Union[np.ndarray, float, int, None]) -> float:
    """
    Safely calculate the median of an array and convert to scalar.
    
    Args:
        array: NumPy array or scalar value
        
    Returns:
        Median value as a Python float
    """
    if array is None:
        return 0.0
        
    if not isinstance(array, np.ndarray):
        # If it's a scalar, return it directly
        return to_scalar(array)
        
    if array.size == 0:
        return 0.0
        
    median_value = np.median(array)
    return to_scalar(median_value)

def safe_array_to_bool(array: Union[np.ndarray, bool, None], operation: str = 'any') -> bool:
    """
    Safely convert array comparison result to boolean.
    
    Args:
        array: NumPy array of boolean values or a scalar boolean
        operation: Operation to apply ('any' or 'all')
        
    Returns:
        Boolean result
    """
    if array is None:
        return False
        
    if not isinstance(array, np.ndarray):
        return bool(array)
        
    if operation == 'any':
        return np.any(array)
    elif operation == 'all':
        return np.all(array)
    else:
        raise ValueError(f"Unsupported operation: {operation}")

def with_numpy_error_handled(func: Callable) -> Callable:
    """
    Decorator to handle common NumPy errors.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            if "truth value of an array" in str(e):
                # Log a warning about the array truth value error
                logger.warning(f"Array truth value error in {func.__name__}: {e}")
                
                # Try to recover by converting arrays to scalars
                new_args = []
                for arg in args:
                    if isinstance(arg, np.ndarray):
                        new_args.append(to_scalar(arg))
                    else:
                        new_args.append(arg)
                        
                for key, value in kwargs.items():
                    if isinstance(value, np.ndarray):
                        kwargs[key] = to_scalar(value)
                
                # Retry with converted arguments
                return func(*new_args, **kwargs)
            else:
                # Re-raise other ValueError exceptions
                raise
    
    return wrapper
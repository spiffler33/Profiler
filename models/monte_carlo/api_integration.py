"""
API integration for Monte Carlo simulations.

This module provides API endpoint functions for Monte Carlo simulations.
It connects the Monte Carlo simulation system to the Flask API layer.
"""

import json
import logging
import time
import traceback
from typing import Dict, Any, List, Optional, Callable
import uuid
from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, request, current_app

# Import local modules
from models.monte_carlo.simulation import (
    validate_simulation_parameters,
    prepare_simulation_data,
    safely_get_simulation_data,
    safely_get_scenarios,
    safely_get_adjustments,
    ensure_attributes_exist,
    create_error_response,
    format_currency,
    cache_response
)
from models.monte_carlo.array_fix import to_scalar, safe_array_compare
from models.monte_carlo.cache import invalidate_cache, get_cache_stats

logger = logging.getLogger(__name__)

def validate_api_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate parameters for simulation endpoints.
    
    Args:
        params: Parameters to validate
        
    Returns:
        Dict containing validation results and sanitized parameters
    """
    errors = []
    sanitized = {}
    
    # Check required parameters
    required_params = ['goal_id']
    for param in required_params:
        if param not in params:
            errors.append(f"Missing required parameter: {param}")
        
    # Validate goal_id
    goal_id = params.get('goal_id', '')
    if not goal_id:
        errors.append("goal_id cannot be empty")
    else:
        sanitized['goal_id'] = goal_id
        
    # Validate optional parameters
    if 'force_recalculate' in params:
        if isinstance(params['force_recalculate'], bool):
            sanitized['force_recalculate'] = params['force_recalculate']
        else:
            # Try to convert string to bool
            force_val = params['force_recalculate']
            if isinstance(force_val, str):
                if force_val.lower() in ['true', '1', 'yes']:
                    sanitized['force_recalculate'] = True
                elif force_val.lower() in ['false', '0', 'no']:
                    sanitized['force_recalculate'] = False
                else:
                    errors.append("Invalid value for force_recalculate. Use true/false.")
            else:
                errors.append("Invalid type for force_recalculate. Must be boolean.")
    
    # Validate simulation_iterations
    if 'simulation_iterations' in params:
        try:
            iterations = int(params['simulation_iterations'])
            if iterations < 100:
                errors.append("simulation_iterations must be at least 100")
            elif iterations > 10000:
                errors.append("simulation_iterations cannot exceed 10,000")
            else:
                sanitized['simulation_iterations'] = iterations
        except (ValueError, TypeError):
            errors.append("simulation_iterations must be a valid integer")
            
    # Return validation results and sanitized parameters
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'sanitized': sanitized
    }

def prepare_api_response(simulation_data: Dict[str, Any], goal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare simulation data for API response, handling both formats.
    
    Args:
        simulation_data: Raw simulation data
        goal_data: Goal data with metadata
        
    Returns:
        Prepared simulation data dictionary with consistent fields
    """
    try:
        # Initialize with defaults
        response_data = {
            'success_probability': to_scalar(simulation_data.get('success_probability', 0.0)),
            'goal_id': goal_data.get('id', ''),
            'target_amount': goal_data.get('target_amount', 0),
            'current_amount': goal_data.get('current_amount', 0),
            'time_horizon': goal_data.get('timeframe_years', 0),
            'percentiles': {}
        }
        
        # Extract percentiles if available
        if 'percentiles' in simulation_data:
            for p in ['10', '25', '50', '75', '90']:
                if p in simulation_data['percentiles']:
                    response_data['percentiles'][p] = to_scalar(simulation_data['percentiles'][p])
        else:
            # Try to extract individual percentile fields
            for p in ['10', '25', '50', '75', '90']:
                key = f'percentile_{p}'
                if key in simulation_data:
                    response_data['percentiles'][p] = to_scalar(simulation_data[key])
                    
        # If we have median but no percentile_50, use median
        if 'median_outcome' in simulation_data and '50' not in response_data['percentiles']:
            response_data['percentiles']['50'] = to_scalar(simulation_data['median_outcome'])
            
        # Add other metadata if available
        if 'simulation_count' in simulation_data:
            response_data['simulation_count'] = simulation_data['simulation_count']
            
        # Add time metrics if available
        if 'time_metrics' in simulation_data:
            response_data['time_metrics'] = simulation_data['time_metrics']
            
        return response_data
    
    except Exception as e:
        logger.error(f"Error preparing API response: {str(e)}")
        traceback.print_exc()
        return {
            'success_probability': to_scalar(simulation_data.get('success_probability', 0.0)),
            'goal_id': goal_data.get('id', ''),
            'error': f"Error preparing API response: {str(e)}"
        }

def monitor_performance(f):
    """Decorator to monitor API endpoint performance."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log performance data
            logger.info(f"API call to {f.__name__} completed in {duration:.3f}s")
            
            # Add performance header to response if it's a tuple with response object
            if isinstance(result, tuple) and len(result) >= 1 and hasattr(result[0], 'headers'):
                result[0].headers['X-API-Response-Time'] = f"{duration:.3f}s"
                
            return result
            
        except Exception as e:
            # Log exception with timing
            duration = time.time() - start_time
            logger.exception(f"Error in {f.__name__} after {duration:.3f}s: {str(e)}")
            
            # Re-raise exception
            raise
            
    return decorated_function

def create_simulation_endpoint(goal_service):
    """
    Factory function to create a simulation endpoint.
    
    Args:
        goal_service: The goal service to use
        
    Returns:
        A Flask view function for the simulation endpoint
    """
    @monitor_performance
    def simulation_endpoint(goal_id):
        """API endpoint for goal probability simulation."""
        try:
            # Parse request parameters
            params = request.args.to_dict()
            params['goal_id'] = goal_id
            
            # Validate parameters
            validation = validate_api_parameters(params)
            if not validation['is_valid']:
                return jsonify({
                    'error': 'Invalid parameters',
                    'message': 'The provided parameters contain errors',
                    'validation_errors': validation['errors']
                }), 400
                
            sanitized = validation['sanitized']
            force_recalculate = sanitized.get('force_recalculate', False)
            
            # Check cache first if not forcing recalculation
            if not force_recalculate:
                cache_key = f"goal_probability_{goal_id}"
                # Try to get from cache
                from models.monte_carlo.cache import _cache
                cached_data = _cache.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"Cache hit for goal probability {goal_id}")
                    return jsonify(cached_data), 200
            
            # Get goal from service
            goal = goal_service.get_goal(goal_id)
            if not goal:
                return jsonify({
                    'error': 'Goal not found',
                    'message': f'No goal found with ID {goal_id}'
                }), 404
                
            # Get or create simulation data
            simulation_data = safely_get_simulation_data(goal)
            
            # Prepare response data
            response = prepare_api_response(simulation_data, goal)
            
            # Cache response
            cache_key = f"goal_probability_{goal_id}"
            cache_response(cache_key, response)
            
            return jsonify(response), 200
            
        except Exception as e:
            logger.exception(f"Error in simulation endpoint: {str(e)}")
            return jsonify(create_error_response(str(e), goal_id)), 500
    
    return simulation_endpoint

def create_cache_clear_endpoint():
    """
    Factory function to create a cache clear endpoint.
    
    Returns:
        A Flask view function for the cache clear endpoint
    """
    @monitor_performance
    def cache_clear_endpoint():
        """API endpoint to clear simulation cache."""
        try:
            # Parse request parameters
            pattern = request.args.get('pattern')
            reason = request.args.get('reason', 'Manual invalidation')
            
            # Validate admin access
            admin_key = request.headers.get('X-Admin-Key')
            if admin_key != current_app.config.get('ADMIN_API_KEY'):
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Admin API key required'
                }), 403
                
            # Invalidate cache
            count = invalidate_cache(pattern)
            
            return jsonify({
                'message': f'Cache invalidated successfully',
                'invalidated_entries': count,
                'pattern': pattern or 'all entries',
                'timestamp': datetime.now().isoformat()
            }), 200
            
        except Exception as e:
            logger.exception(f"Error clearing cache: {str(e)}")
            return jsonify(create_error_response(str(e))), 500
    
    return cache_clear_endpoint
"""API endpoint for providing visualization data and probability calculations for goals.

This module provides API endpoints for:
1. Retrieving all visualization-related data needed by React components in a single request
2. Real-time goal probability calculations for form inputs

It includes:
- Monte Carlo simulation results for the ProbabilisticGoalVisualizer
- Adjustment recommendations for the AdjustmentImpactPanel
- Scenario comparison data for the ScenarioComparisonChart
- Real-time probability calculations for the goal form

These endpoints are designed to provide both complete visualization data and
lightweight real-time probability calculations.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from flask import Blueprint, jsonify, request, current_app, g
import json
from datetime import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import relevant models and services
from models.goal_models import Goal, GoalManager
from models.goal_probability import GoalProbabilityAnalyzer, ProbabilityResult
from models.goal_adjustment import GoalAdjustmentRecommender, AdjustmentType
from models.gap_analysis.scenarios import GoalScenarioComparison
from services.goal_service import GoalService
from services.goal_adjustment_service import GoalAdjustmentService
from models.monte_carlo.cache import cached_simulation, get_cache_stats, invalidate_cache

# Import common API utilities
from api.v2.utils import (
    monitor_performance, check_cache, cache_response,
    rate_limit_middleware, check_admin_access, create_error_response
)

# Initialize logging
logger = logging.getLogger(__name__)

# Create Blueprint for API routes
visualization_api = Blueprint('visualization_api', __name__)

# Cache key generator for visualization-specific operations
def generate_visualization_cache_key(goal_id, operation, params=None):
    """Generate a cache key for a specific visualization operation."""
    if params:
        param_str = json.dumps(params, sort_keys=True)
        return f"visualization:{goal_id}:{operation}:{hash(param_str)}"
    return f"visualization:{goal_id}:{operation}"

@visualization_api.route('/goals/<goal_id>/visualization-data', methods=['GET'])
@monitor_performance
def get_visualization_data(goal_id: str):
    """
    Get all visualization data for a goal in a single API call.
    
    This endpoint retrieves and returns:
    - Monte Carlo simulation results (probabilistic outcomes)
    - Adjustment recommendations
    - Scenario comparison data
    
    It's designed to provide all the data needed by the front-end visualization
    components in a single request to minimize API calls.
    
    Args:
        goal_id: The UUID of the goal to retrieve data for
        
    Returns:
        JSON response with all visualization data
    """
    try:
        # Validate goal_id format
        try:
            uuid_obj = uuid.UUID(goal_id)
        except ValueError:
            return jsonify({
                'error': 'Invalid goal ID format',
                'message': 'Goal ID must be a valid UUID'
            }), 400
            
        # Try to get from cache first
        cache_key = generate_visualization_cache_key(goal_id, "visualization_data")
        cached_response = check_cache(cache_key)
        if cached_response:
            g.cache_status = "HIT"
            return cached_response
        
        g.cache_status = "MISS"
            
        # Access services
        goal_service = current_app.config.get('goal_service', GoalService())
        goal_manager = current_app.config.get('goal_manager', GoalManager())
        profile_manager = current_app.config.get('profile_manager')
        
        # Get goal data
        goal = goal_service.get_goal(goal_id)
        if not goal:
            return jsonify({
                'error': 'Goal not found',
                'message': f'No goal found with ID {goal_id}'
            }), 404
            
        # Get current profile ID from goal
        profile_id = goal.get('profile_id')
        if not profile_id:
            return jsonify({
                'error': 'Profile information missing',
                'message': 'Goal is not associated with a profile'
            }), 400
            
        # Get profile data if profile_manager is available
        profile_data = {}
        if profile_manager:
            profile_data = profile_manager.get_profile(profile_id) or {}
        
        # Optimize data retrieval using parallel processing
        monte_carlo_data = None
        adjustment_data = None
        scenario_data = None
        
        # Use ThreadPoolExecutor to run data retrievals in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tasks to executor
            monte_carlo_future = executor.submit(get_monte_carlo_data, goal, profile_data)
            adjustment_future = executor.submit(get_adjustment_data, goal, profile_data)
            scenario_future = executor.submit(get_scenario_data, goal, profile_data)
            
            # Get results as they complete
            for future in as_completed([monte_carlo_future, adjustment_future, scenario_future]):
                try:
                    result = future.result()
                    if future == monte_carlo_future:
                        monte_carlo_data = result
                    elif future == adjustment_future:
                        adjustment_data = result
                    elif future == scenario_future:
                        scenario_data = result
                except Exception as e:
                    logger.warning(f"Error in parallel data retrieval: {str(e)}")
        
        # Make sure we have values for all data types, even if they failed
        monte_carlo_data = monte_carlo_data or get_monte_carlo_data_fallback(goal)
        adjustment_data = adjustment_data or get_adjustment_data_fallback(goal)
        scenario_data = scenario_data or get_scenario_data_fallback(goal)
            
        # Prepare response structure with optimized data
        response = {
            'goal_id': goal_id,
            'probabilisticGoalData': monte_carlo_data,
            'adjustmentImpactData': adjustment_data,
            'scenarioComparisonData': scenario_data,
            'dataSources': {
                'monte_carlo': monte_carlo_data.get('source', 'generated'),
                'adjustments': adjustment_data.get('source', 'generated'),
                'scenarios': scenario_data.get('source', 'generated')
            }
        }
        
        # Optimize response size by removing unnecessary nested data
        response = _optimize_response_size(response)
        
        # Cache the response
        cache_response(cache_key, response)
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.exception(f"Error retrieving visualization data: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@visualization_api.route('/goals/<goal_id>/projection-data', methods=['GET'])
@monitor_performance
def get_goal_projection_data(goal_id: str):
    """
    Get projection data for a specific goal type.
    
    This endpoint provides optimized projection data for visualizations.
    It supports filtering to return only the data needed for specific
    chart types.
    
    Args:
        goal_id: The UUID of the goal to get projection data for
        
    Query Parameters:
        - type: Projection type ('timeline', 'allocation', 'probability', 'all')
        - resolution: Data resolution ('high', 'medium', 'low')
        
    Returns:
        JSON response with projection data filtered by type and resolution
    """
    try:
        # Validate goal_id format
        try:
            uuid_obj = uuid.UUID(goal_id)
        except ValueError:
            return jsonify({
                'error': 'Invalid goal ID format',
                'message': 'Goal ID must be a valid UUID'
            }), 400
            
        # Get query parameters for filtering
        projection_type = request.args.get('type', 'all')
        resolution = request.args.get('resolution', 'medium')
        
        # Generate cache key including query parameters
        cache_params = {'type': projection_type, 'resolution': resolution}
        cache_key = generate_visualization_cache_key(goal_id, "projection_data", cache_params)
        cached_response = check_cache(cache_key)
        if cached_response:
            g.cache_status = "HIT"
            return cached_response
            
        g.cache_status = "MISS"
            
        # Access services
        goal_service = current_app.config.get('goal_service', GoalService())
        
        # Get goal data
        goal = goal_service.get_goal(goal_id)
        if not goal:
            return jsonify({
                'error': 'Goal not found',
                'message': f'No goal found with ID {goal_id}'
            }), 404
            
        # Determine goal type for specialized projections
        goal_type = goal.get('category', '').lower()
        
        # Get projection data based on goal type and requested projection type
        projection_data = {}
        
        if projection_type in ['timeline', 'all']:
            # Time-based projection showing growth over time
            projection_data['timeline'] = _get_timeline_projection(goal, resolution)
            
        if projection_type in ['allocation', 'all']:
            # Asset allocation projection
            projection_data['allocation'] = _get_allocation_projection(goal, resolution)
            
        if projection_type in ['probability', 'all']:
            # Probability distribution projection
            projection_data['probability'] = _get_probability_projection(goal, resolution)
            
        if goal_type == 'retirement' and (projection_type in ['retirement', 'all']):
            # Retirement-specific projections (income vs. expenses in retirement)
            projection_data['retirement'] = _get_retirement_projection(goal, resolution)
            
        if goal_type == 'education' and (projection_type in ['education', 'all']):
            # Education-specific projections (funding by year of education)
            projection_data['education'] = _get_education_projection(goal, resolution)
            
        if goal_type == 'home_purchase' and (projection_type in ['mortgage', 'all']):
            # Home purchase/mortgage projections
            projection_data['mortgage'] = _get_mortgage_projection(goal, resolution)
            
        # Prepare full response
        response = {
            'goal_id': goal_id,
            'goal_type': goal_type,
            'projections': projection_data,
            'metadata': {
                'resolution': resolution,
                'currency': goal.get('currency', 'INR'),
                'use_indian_format': goal.get('use_indian_format', False)
            }
        }
        
        # Cache the response
        cache_response(cache_key, response)
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.exception(f"Error retrieving goal projection data: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@visualization_api.route('/goals/portfolio-data', methods=['GET'])
@monitor_performance
def get_portfolio_data():
    """
    Get aggregate portfolio data across all goals.
    
    This endpoint provides dashboard-level aggregate data for all goals,
    allowing visualization of the entire goal portfolio.
    
    Query Parameters:
        - user_id: User profile ID
        - include_inactive: Whether to include inactive goals (default: false)
        
    Returns:
        JSON response with portfolio-level aggregated data
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id')
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        if not user_id:
            return jsonify({
                'error': 'Missing parameter',
                'message': 'user_id is required'
            }), 400
            
        # Generate cache key
        cache_params = {'user_id': user_id, 'include_inactive': include_inactive}
        cache_key = generate_visualization_cache_key('portfolio', "portfolio_data", cache_params)
        cached_response = check_cache(cache_key)
        if cached_response:
            g.cache_status = "HIT"
            return cached_response
            
        g.cache_status = "MISS"
            
        # Access services
        goal_service = current_app.config.get('goal_service', GoalService())
        
        # Get all goals for the user
        goals = goal_service.get_goals_for_user(user_id)
        if not goals:
            return jsonify({
                'error': 'No goals found',
                'message': f'No goals found for user ID {user_id}'
            }), 404
            
        # Filter inactive goals if not included
        if not include_inactive:
            goals = [g for g in goals if g.get('status', 'active') == 'active']
            
        # Process goals to create portfolio-level data
        
        # 1. Aggregate goals by category
        categories = {}
        for goal in goals:
            category = goal.get('category', 'other')
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'total_target': 0,
                    'total_current': 0,
                    'avg_probability': 0,
                    'goals': []
                }
                
            categories[category]['count'] += 1
            categories[category]['total_target'] += goal.get('target_amount', 0)
            categories[category]['total_current'] += goal.get('current_amount', 0)
            categories[category]['avg_probability'] += goal.get('success_probability', 0)
            
            # Add simplified goal data
            categories[category]['goals'].append({
                'id': goal.get('id', ''),
                'title': goal.get('title', ''),
                'target_amount': goal.get('target_amount', 0),
                'current_amount': goal.get('current_amount', 0),
                'success_probability': goal.get('success_probability', 0),
                'timeframe': goal.get('timeframe', '')
            })
            
        # Calculate average probabilities
        for category, data in categories.items():
            if data['count'] > 0:
                data['avg_probability'] /= data['count']
        
        # 2. Create timeline projection across goals
        timeline_projection = _generate_portfolio_timeline(goals)
        
        # 3. Calculate overall portfolio metrics
        total_target = sum(goal.get('target_amount', 0) for goal in goals)
        total_current = sum(goal.get('current_amount', 0) for goal in goals)
        progress_percent = (total_current / total_target * 100) if total_target > 0 else 0
        
        # Calculate funding gap across all goals
        total_monthly_contribution = sum(goal.get('monthly_contribution', 0) for goal in goals)
        total_required_contribution = sum(goal.get('required_monthly_contribution', 0) for goal in goals)
        monthly_gap = total_required_contribution - total_monthly_contribution
        
        # 4. Calculate goal health distribution
        health_distribution = {
            'healthy': len([g for g in goals if g.get('success_probability', 0) >= 0.75]),
            'at_risk': len([g for g in goals if 0.5 <= g.get('success_probability', 0) < 0.75]),
            'critical': len([g for g in goals if g.get('success_probability', 0) < 0.5])
        }
        
        # Prepare portfolio response
        response = {
            'user_id': user_id,
            'goal_count': len(goals),
            'categories': categories,
            'timeline_projection': timeline_projection,
            'portfolio_metrics': {
                'total_target_amount': total_target,
                'total_current_amount': total_current,
                'overall_progress_percent': progress_percent,
                'monthly_contribution': total_monthly_contribution,
                'monthly_funding_gap': monthly_gap,
                'goal_health': health_distribution
            }
        }
        
        # Cache the response
        cache_response(cache_key, response)
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.exception(f"Error retrieving portfolio data: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

# This endpoint has been moved to goal_probability_api.py to avoid route conflicts
# The implementation is now in calculate_probability_frontend_compatible()
# @visualization_api.route('/goals/calculate-probability', methods=['POST'])
# @monitor_performance
# def calculate_goal_probability():
#     """
#     Calculate probability for goal parameters in real-time.
#     
#     This endpoint is designed for the goal form to get quick probability
#     calculations as the user changes parameters. It accepts all goal parameters
#     and returns a probability calculation along with potential adjustments.
#     
#     Request Body:
#         JSON object containing goal parameters:
#         - category: Goal category (e.g., 'emergency_fund', 'retirement')
#         - target_amount: Goal target amount
#         - current_amount: Current saved amount
#         - timeframe: Target date (ISO format)
#         - months_remaining: Months between now and target date
#         - importance: Goal importance ('high', 'medium', 'low')
#         - flexibility: Goal flexibility ('fixed', 'somewhat_flexible', 'very_flexible')
#         - Additional category-specific parameters
    
#     Returns:
#         JSON response with:
#         - success_probability: Calculated probability (0-100)
#         - adjustments: Array of potential adjustments to improve probability
#         - simulation_data: Basic simulation data for visualization
#     """
#     try:
#         # Get and validate request data
#         data = request.get_json()
#         if not data:
#             return jsonify({
#                 'error': 'Invalid request',
#                 'message': 'Request body must contain valid JSON'
#             }), 400
#         
#         # Validate required fields
#         required_fields = ['category', 'target_amount', 'timeframe']
#         missing_fields = [field for field in required_fields if field not in data]
#         if missing_fields:
#             return jsonify({
#                 'error': 'Missing required fields',
#                 'message': f'The following fields are required: {", ".join(missing_fields)}'
#             }), 400
        
#         # Generate cache key for request parameters
#         cache_key = generate_visualization_cache_key('calculation', 'probability', data)
#         cached_response = check_cache(cache_key)
#         if cached_response:
#             g.cache_status = "HIT"
#             return cached_response
#             
#         g.cache_status = "MISS"
#         
#         # Access services for probability calculation
#         goal_service = current_app.config.get('goal_service', GoalService())
#         goal_probability_analyzer = current_app.config.get('goal_probability_analyzer', GoalProbabilityAnalyzer())
#         goal_adjustment_service = current_app.config.get('goal_adjustment_service', GoalAdjustmentService())
#         
#         # Prepare parameters for calculation
#         category = data.get('category', '')
#         target_amount = float(data.get('target_amount', 0))
#         current_amount = float(data.get('current_amount', 0))
#         timeframe = data.get('timeframe', '')
#         
#         # Create a temporary goal object for probability calculation
#         temp_goal = {
#             'id': data.get('goal_id', str(uuid.uuid4())),
#             'category': category,
#             'target_amount': target_amount,
#             'current_amount': current_amount,
#             'timeframe': timeframe,
#             'importance': data.get('importance', 'medium'),
#             'flexibility': data.get('flexibility', 'somewhat_flexible')
#         }
        
#         # Add category-specific parameters to the goal
#         if category == 'emergency_fund':
#             temp_goal['funding_strategy'] = json.dumps({
#                 'months': data.get('emergency_fund_months', 6),
#                 'monthly_expenses': data.get('monthly_expenses', 0)
#             })
#         elif category in ['traditional_retirement', 'early_retirement']:
#             temp_goal['funding_strategy'] = json.dumps({
#                 'retirement_age': data.get('retirement_age', 65),
#                 'withdrawal_rate': data.get('withdrawal_rate', 0.04),
#                 'yearly_expenses': data.get('yearly_expenses', 0)
#             })
#         elif category == 'education':
#             temp_goal['funding_strategy'] = json.dumps({
#                 'education_type': data.get('education_type', 'college'),
#                 'years': data.get('education_years', 4),
#                 'yearly_cost': data.get('yearly_cost', 0)
#             })
#         elif category == 'home_purchase':
#             temp_goal['funding_strategy'] = json.dumps({
#                 'property_value': data.get('property_value', 0),
#                 'down_payment_percent': data.get('down_payment_percent', 0.2)
#             })
#         
#         # Calculate probability
#         start_time = time.time()
#         success_probability = 0
#         
#         try:
#             # Calculate initial success probability
#             probability_result = goal_probability_analyzer.calculate_probability(temp_goal)
#             calculation_time = time.time() - start_time
#             success_probability = probability_result.probability * 100  # Convert to percentage
#             
#             # Generate potential adjustments if probability is below threshold
#             adjustments = []
#             if success_probability < 80:
#                 adjustment_options = goal_adjustment_service.recommend_adjustments(temp_goal)
#                 # Convert adjustments to the expected format
#                 for adj in adjustment_options:
#                     adjustment_type = adj.get('type', '')
#                     impact = adj.get('impact', 0)
#                     adjustments.append({
#                         'description': adj.get('description', ''),
#                         'impact_metrics': {
#                             'probability_increase': impact / 100,  # Convert to decimal
#                             'new_probability': min(success_probability + impact, 100) / 100
#                         }
#                     })
            
#             # Create basic simulation data optimized for visualization
#             # We reduce payload size by limiting data points and precision
#             simulation_data = _create_optimized_simulation_data(
#                 temp_goal, 
#                 probability_result, 
#                 resolution='low'  # Use low resolution for form visualization
#             )
#             
#             # Prepare response
#             response = {
#                 'success_probability': success_probability,
#                 'adjustments': adjustments,
#                 'simulation_data': simulation_data,
#                 'calculation_metadata': {
#                     'calculation_time_ms': round(calculation_time * 1000, 2),
#                     'simulation_count': getattr(probability_result, 'simulation_count', 1000),
#                     'confidence_interval': getattr(probability_result, 'confidence_interval', []),
#                     'is_estimate': False
#                 }
#             }
#             
#             # Cache the response
#             cache_response(cache_key, response, ttl=1800)  # 30 minute TTL for real-time calcs
#             
#             return jsonify(response), 200
#             
#         except Exception as calc_error:
#             # Calculate time spent even for errors
#             calculation_time = time.time() - start_time
#             logger.warning(f"Error in probability calculation (took {calculation_time:.3f}s): {str(calc_error)}")
#             
#             # Fallback to basic probability calculation if the analyzer fails
#             success_probability = calculate_fallback_probability(data)
#             
#             # Create a simplified response with the fallback probability
#             response = {
#                 'success_probability': success_probability,
#                 'adjustments': [],
#                 'simulation_data': {
#                     'successProbability': success_probability
#                 },
#                 'calculation_metadata': {
#                     'calculation_time_ms': round(calculation_time * 1000, 2),
#                     'is_estimate': True,
#                     'estimation_method': 'fallback_calculator',
#                     'error': str(calc_error)
#                 }
#             }
#             
#             # Cache even the fallback response
#             cache_response(cache_key, response, ttl=1800)  # 30 minute TTL for real-time calcs
#             
#             return jsonify(response), 200
#             
#     except Exception as e:
#         logger.exception(f"Error calculating goal probability: {str(e)}")
#         return jsonify({
#             'error': 'Internal server error',
#             'message': str(e)
#         }), 500

# Note: This function is not currently used but kept for potential future use
def calculate_fallback_probability(data):
    """Fallback probability calculation when the analyzer fails.
    
    This implements a basic calculation algorithm to ensure the frontend
    always gets some probability value.
    
    Args:
        data: Goal parameter data from request
        
    Returns:
        Calculated probability value (0-100)
    """
    try:
        # Base probability
        probability = 50
        
        # Time horizon impact
        months_remaining = data.get('months_remaining', 0)
        if months_remaining <= 0:
            probability = 0  # Past due date
        elif months_remaining < 12:
            probability -= (12 - months_remaining) * 2  # Short timeline penalty
        elif months_remaining > 60:
            probability += 15  # Long timeline bonus
        else:
            probability += 5  # Moderate timeline bonus
        
        # Current progress impact
        target_amount = float(data.get('target_amount', 0))
        current_amount = float(data.get('current_amount', 0))
        if target_amount > 0:
            progress_percent = (current_amount / target_amount) * 100
            if progress_percent >= 50:
                probability += 20  # On track bonus
            elif progress_percent >= 25:
                probability += 10  # Some progress bonus
        
        # Goal category impact
        category = data.get('category', '')
        if category in ['emergency_fund', 'health_insurance']:
            probability += 10  # Essential goals bonus
        elif category in ['travel', 'vehicle', 'custom']:
            probability -= 5  # Discretionary goals penalty
        
        # Importance/flexibility impact
        importance = data.get('importance', 'medium')
        flexibility = data.get('flexibility', 'somewhat_flexible')
        if importance == 'high' and flexibility == 'fixed':
            probability -= 10  # High priority, inflexible goals are harder
        elif importance == 'low' and flexibility == 'very_flexible':
            probability += 10  # Low priority, flexible goals are easier
        
        # Ensure probability is within 0-100 range
        return max(0, min(100, probability))
    
    except Exception as e:
        logger.warning(f"Error in fallback probability calculation: {str(e)}")
        return 50  # Return default probability on error

# Helper functions have been moved to api.v2.utils

def _optimize_response_size(response):
    """Optimize response size by reducing precision and unnecessary data."""
    # For numeric values, limit decimal precision
    if 'probabilisticGoalData' in response:
        data = response['probabilisticGoalData']
        if 'simulationOutcomes' in data and 'percentiles' in data['simulationOutcomes']:
            # Round percentile values to nearest 100
            percentiles = data['simulationOutcomes']['percentiles']
            for key in percentiles:
                if isinstance(percentiles[key], (int, float)):
                    percentiles[key] = round(percentiles[key], -2)
        
        # Remove detailed time-based data if it's large
        if 'timeBasedMetrics' in data and 'probabilityOverTime' in data['timeBasedMetrics']:
            metrics = data['timeBasedMetrics']['probabilityOverTime']
            # If there are many data points, reduce resolution
            if 'values' in metrics and len(metrics['values']) > 10:
                # Take fewer data points for trend visualization
                values = metrics['values']
                labels = metrics.get('labels', [])
                
                if len(values) > 20:
                    # For long arrays, take points at regular intervals
                    step = len(values) // 10
                    response['probabilisticGoalData']['timeBasedMetrics']['probabilityOverTime'] = {
                        'values': values[::step],
                        'labels': labels[::step] if len(labels) == len(values) else []
                    }
    
    return response

def get_monte_carlo_data(goal: Dict[str, Any], profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get Monte Carlo simulation data for ProbabilisticGoalVisualizer.
    
    Args:
        goal: Goal data dictionary
        profile_data: Profile data dictionary
        
    Returns:
        Dictionary with structured Monte Carlo simulation data
    """
    try:
        # Try to get existing simulation data from goal if available
        if isinstance(goal.get('simulation_data'), dict):
            return {**goal['simulation_data'], 'source': 'goal_data'}
        elif isinstance(goal.get('simulation_data'), str):
            try:
                simulation_data = json.loads(goal['simulation_data'])
                return {**simulation_data, 'source': 'goal_data'}
            except:
                pass
            
        # If goal has probability results but no simulation data, create a basic structure
        probability = goal.get('success_probability', 0)
        if not isinstance(probability, (int, float)):
            probability = 0
            
        # Create basic simulation data with target, timeframe and probability
        target_amount = goal.get('target_amount', 0)
        timeframe = goal.get('timeframe', '')
        if isinstance(timeframe, str) and 'T' in timeframe:
            timeframe = timeframe.split('T')[0]  # Extract date part only
            
        # Build minimal simulation data for the visualizer
        simulation_data = {
            'goalId': goal.get('id', ''),
            'targetAmount': target_amount,
            'timeframe': timeframe,
            'successProbability': probability,
            'simulationOutcomes': {
                'median': target_amount,
                'percentiles': {
                    '10': target_amount * 0.7,
                    '25': target_amount * 0.85,
                    '50': target_amount,
                    '75': target_amount * 1.15,
                    '90': target_amount * 1.3
                }
            },
            'timeBasedMetrics': {
                'probabilityOverTime': {
                    'labels': ['Start', '25%', '50%', '75%', 'End'],
                    'values': [0, probability * 0.4, probability * 0.6, probability * 0.8, probability]
                }
            },
            'source': 'generated'
        }
        
        return simulation_data
        
    except Exception as e:
        logger.warning(f"Error generating Monte Carlo data: {str(e)}")
        # Return basic structure on error
        return get_monte_carlo_data_fallback(goal)

def get_monte_carlo_data_fallback(goal: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback function for Monte Carlo data when the primary function fails."""
    return {
        'goalId': goal.get('id', ''),
        'targetAmount': goal.get('target_amount', 0),
        'successProbability': goal.get('success_probability', 0),
        'simulationOutcomes': {},
        'source': 'fallback'
    }

def get_adjustment_data(goal: Dict[str, Any], profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get adjustment recommendations data for AdjustmentImpactPanel.
    
    Args:
        goal: Goal data dictionary
        profile_data: Profile data dictionary
        
    Returns:
        Dictionary with structured adjustment recommendations
    """
    try:
        # Try to get existing adjustment data from goal if available
        if isinstance(goal.get('adjustments'), list):
            return {
                'goalId': goal.get('id', ''),
                'currentProbability': goal.get('success_probability', 0),
                'adjustments': goal['adjustments'],
                'source': 'goal_data'
            }
        elif isinstance(goal.get('adjustments'), str):
            try:
                adjustments = json.loads(goal['adjustments'])
                if isinstance(adjustments, list):
                    return {
                        'goalId': goal.get('id', ''),
                        'currentProbability': goal.get('success_probability', 0),
                        'adjustments': adjustments,
                        'source': 'goal_data'
                    }
            except:
                pass
            
        # If goal has no adjustment recommendations, create a basic structure
        # with sample recommendations
        goal_id = goal.get('id', '')
        target_amount = goal.get('target_amount', 0)
        timeframe = goal.get('timeframe', '')
        current_probability = goal.get('success_probability', 0)
        goal_type = goal.get('type', 'custom')
        
        # Create sample adjustments based on goal type
        adjustments = []
        
        # Sample contribution increase adjustment
        if target_amount > 0:
            contrib_increase = min(target_amount * 0.05, 5000)  # 5% or max ₹5,000
            adjustments.append({
                'id': f"{goal_id}_contrib_adj",
                'goalId': goal_id,
                'adjustmentType': 'contribution',
                'description': f"Increase monthly contribution by ₹{int(contrib_increase):,}",
                'adjustmentValue': contrib_increase,
                'originalValue': goal.get('current_contribution', 0),
                'impactMetrics': {
                    'probabilityIncrease': 0.08,
                    'newProbability': min(current_probability + 0.08, 1.0)
                },
                'implementationSteps': [
                    "Set up additional SIP to increase monthly contribution",
                    "Reduce discretionary expenses to fund increased contribution"
                ],
                'suitabilityScore': 0.85
            })
        
        # Sample timeframe extension adjustment
        if timeframe:
            extend_months = 6  # 6 months extension
            adjustments.append({
                'id': f"{goal_id}_time_adj",
                'goalId': goal_id,
                'adjustmentType': 'timeframe',
                'description': f"Extend goal timeframe by {extend_months} months",
                'adjustmentValue': extend_months,
                'originalValue': 0,  # Original months extension
                'impactMetrics': {
                    'probabilityIncrease': 0.12,
                    'newProbability': min(current_probability + 0.12, 1.0)
                },
                'implementationSteps': [
                    "Adjust target date in your financial plan",
                    "Maintain current contribution level"
                ],
                'suitabilityScore': 0.75
            })
            
        # Sample allocation adjustment for long-term goals
        if goal_type in ['retirement', 'education', 'home_purchase']:
            adjustments.append({
                'id': f"{goal_id}_alloc_adj",
                'goalId': goal_id,
                'adjustmentType': 'allocation',
                'description': "Increase equity allocation by 10%",
                'adjustmentValue': 0.1,
                'originalValue': goal.get('equity_allocation', 0.5),
                'impactMetrics': {
                    'probabilityIncrease': 0.07,
                    'newProbability': min(current_probability + 0.07, 1.0)
                },
                'implementationSteps': [
                    "Rebalance portfolio to increase equity allocation",
                    "Consider index funds or diversified equity mutual funds"
                ],
                'suitabilityScore': 0.7
            })
            
        return {
            'goalId': goal_id,
            'currentProbability': current_probability,
            'adjustments': adjustments,
            'source': 'generated'
        }
        
    except Exception as e:
        logger.warning(f"Error generating adjustment data: {str(e)}")
        # Return basic structure on error
        return get_adjustment_data_fallback(goal)

def get_adjustment_data_fallback(goal: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback function for adjustment data when the primary function fails."""
    return {
        'goalId': goal.get('id', ''),
        'currentProbability': goal.get('success_probability', 0),
        'adjustments': [],
        'source': 'fallback'
    }

def get_scenario_data(goal: Dict[str, Any], profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get scenario comparison data for ScenarioComparisonChart.
    
    Args:
        goal: Goal data dictionary
        profile_data: Profile data dictionary
        
    Returns:
        Dictionary with structured scenario comparison data
    """
    try:
        # Try to get existing scenario data from goal if available
        if isinstance(goal.get('scenarios'), list):
            return {
                'goalId': goal.get('id', ''),
                'scenarios': goal['scenarios'],
                'source': 'goal_data'
            }
        elif isinstance(goal.get('scenarios'), str):
            try:
                scenarios = json.loads(goal['scenarios'])
                if isinstance(scenarios, list):
                    return {
                        'goalId': goal.get('id', ''),
                        'scenarios': scenarios,
                        'source': 'goal_data'
                    }
            except:
                pass
            
        # If goal has no scenario data, create a basic structure with
        # sample scenario comparisons
        goal_id = goal.get('id', '')
        target_amount = goal.get('target_amount', 0)
        timeframe = goal.get('timeframe', '')
        current_probability = goal.get('success_probability', 0)
        
        # Create sample scenarios
        scenarios = []
        
        # Baseline scenario (current plan)
        scenarios.append({
            'id': f"{goal_id}_baseline",
            'name': "Current Plan",
            'description': "Your current financial plan with no changes",
            'probability': current_probability,
            'metrics': {
                'monthlyContribution': goal.get('required_monthly_savings', 0),
                'targetAmount': target_amount,
                'timeframe': timeframe
            },
            'isBaseline': True
        })
        
        # Aggressive contribution scenario
        contrib_increase = min(target_amount * 0.1, 10000)  # 10% or max ₹10,000
        agg_contrib_probability = min(current_probability + 0.15, 1.0)
        scenarios.append({
            'id': f"{goal_id}_aggressive",
            'name': "Aggressive Saving",
            'description': "Increase monthly contributions significantly",
            'probability': agg_contrib_probability,
            'metrics': {
                'monthlyContribution': goal.get('required_monthly_savings', 0) + contrib_increase,
                'targetAmount': target_amount,
                'timeframe': timeframe
            },
            'isBaseline': False
        })
        
        # Extended timeline scenario
        extend_probability = min(current_probability + 0.18, 1.0)
        scenarios.append({
            'id': f"{goal_id}_extended",
            'name': "Extended Timeline",
            'description': "Extend goal timeframe by 1 year",
            'probability': extend_probability,
            'metrics': {
                'monthlyContribution': goal.get('required_monthly_savings', 0),
                'targetAmount': target_amount,
                'timeframe': "Extended by 12 months"  # Would be actual date in real implementation
            },
            'isBaseline': False
        })
        
        # Balanced approach combining moderate changes
        balanced_probability = min(current_probability + 0.21, 1.0)
        scenarios.append({
            'id': f"{goal_id}_balanced",
            'name': "Balanced Approach",
            'description': "Moderate contribution increase with 6-month extension",
            'probability': balanced_probability,
            'metrics': {
                'monthlyContribution': goal.get('required_monthly_savings', 0) + (contrib_increase / 2),
                'targetAmount': target_amount,
                'timeframe': "Extended by 6 months"  # Would be actual date in real implementation
            },
            'isBaseline': False
        })
        
        return {
            'goalId': goal_id,
            'scenarios': scenarios,
            'source': 'generated'
        }
        
    except Exception as e:
        logger.warning(f"Error generating scenario data: {str(e)}")
        # Return basic structure on error
        return get_scenario_data_fallback(goal)

def get_scenario_data_fallback(goal: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback function for scenario data when the primary function fails."""
    return {
        'goalId': goal.get('id', ''),
        'scenarios': [{
            'id': f"{goal.get('id', '')}_baseline",
            'name': "Current Plan",
            'description': "Your current financial plan with no changes",
            'probability': goal.get('success_probability', 0),
            'isBaseline': True
        }],
        'source': 'fallback'
    }

def _create_optimized_simulation_data(goal, probability_result, resolution='medium'):
    """Create optimized simulation data for visualizations with reduced payload size."""
    goal_id = goal.get('id', '')
    target_amount = goal.get('target_amount', 0)
    
    # Get simulation results from probability result
    simulation_results = {}
    if hasattr(probability_result, 'simulation_results') and probability_result.simulation_results:
        if isinstance(probability_result.simulation_results, dict):
            simulation_results = probability_result.simulation_results
    
    # Get percentiles from simulation results or create defaults
    percentiles = simulation_results.get('percentiles', {})
    if not percentiles:
        percentiles = {
            '10': target_amount * 0.7,
            '25': target_amount * 0.85,
            '50': target_amount,
            '75': target_amount * 1.15,
            '90': target_amount * 1.3
        }
    
    # Round values based on resolution to reduce payload size
    if resolution == 'low':
        # Round to nearest 1000 for low resolution
        for key in percentiles:
            percentiles[key] = round(percentiles[key], -3)
    elif resolution == 'medium':
        # Round to nearest 100 for medium resolution
        for key in percentiles:
            percentiles[key] = round(percentiles[key], -2)
    
    # Optimized simulation data structure
    return {
        'goalId': goal_id,
        'targetAmount': target_amount,
        'successProbability': probability_result.probability,
        'percentiles': percentiles,
        'resolution': resolution
    }

def _get_timeline_projection(goal, resolution):
    """Get time-based projection data for a goal."""
    # Implementation would vary based on goal type
    # This is a simplified example
    timeframe = goal.get('timeframe', '')
    target_date = None
    
    try:
        if isinstance(timeframe, str) and timeframe:
            target_date = datetime.fromisoformat(timeframe.split('T')[0] if 'T' in timeframe else timeframe)
    except:
        # Use current date + 5 years as fallback
        target_date = datetime.now().replace(year=datetime.now().year + 5)
    
    if not target_date:
        target_date = datetime.now().replace(year=datetime.now().year + 5)
    
    # Calculate years between now and target date
    years = max(1, (target_date.year - datetime.now().year))
    
    # Determine number of data points based on resolution
    if resolution == 'high':
        points = min(years * 12, 60)  # Monthly for up to 5 years
    elif resolution == 'medium':
        points = min(years * 4, 20)  # Quarterly for up to 5 years
    else:  # 'low'
        points = min(years, 10)  # Yearly for up to 10 years
    
    # Generate time labels
    start_date = datetime.now()
    labels = []
    for i in range(points + 1):
        if resolution == 'high':
            # Monthly intervals
            d = start_date.replace(month=((start_date.month - 1 + i) % 12) + 1)
            if (start_date.month - 1 + i) // 12 > 0:
                d = d.replace(year=d.year + (start_date.month - 1 + i) // 12)
            labels.append(d.strftime('%b %Y'))
        elif resolution == 'medium':
            # Quarterly intervals
            month = ((start_date.month - 1 + i * 3) % 12) + 1
            year = start_date.year + (start_date.month - 1 + i * 3) // 12
            labels.append(f"Q{(month-1)//3+1} {year}")
        else:  # 'low'
            # Yearly intervals
            labels.append(str(start_date.year + i))
    
    # Create projected values
    current_amount = goal.get('current_amount', 0)
    target_amount = goal.get('target_amount', 0)
    monthly_contribution = goal.get('monthly_contribution', 0)
    
    # Simple linear projection as fallback
    value_gap = target_amount - current_amount
    values = []
    
    for i in range(points + 1):
        if points > 0:
            # Simple linear growth plus contributions
            progress = i / points
            contribution_amount = 0
            
            if resolution == 'high':
                # Monthly contributions
                contribution_amount = monthly_contribution * i
            elif resolution == 'medium':
                # Quarterly contributions
                contribution_amount = monthly_contribution * 3 * i
            else:  # 'low'
                # Yearly contributions
                contribution_amount = monthly_contribution * 12 * i
            
            projected_value = current_amount + (value_gap * progress) + contribution_amount
            values.append(round(projected_value, -2))  # Round to nearest 100
        else:
            values.append(current_amount)
    
    return {
        'labels': labels,
        'values': values,
        'resolution': resolution
    }

def _get_allocation_projection(goal, resolution):
    """Get asset allocation projection data for a goal."""
    # Implementation would generate allocation data
    # This is a simplified example
    
    # Get allocation from goal data or use defaults
    allocation = {}
    try:
        if isinstance(goal.get('asset_allocation'), dict):
            allocation = goal.get('asset_allocation')
        elif isinstance(goal.get('asset_allocation'), str):
            allocation = json.loads(goal.get('asset_allocation', '{}'))
    except:
        pass
    
    # Use default allocation if none found
    if not allocation:
        # Default allocation based on goal type
        goal_type = goal.get('category', '').lower()
        
        if goal_type in ['retirement', 'education']:
            # Long-term goals have higher equity
            allocation = {
                'equity': 0.6,
                'debt': 0.25,
                'gold': 0.1,
                'cash': 0.05
            }
        elif goal_type in ['emergency_fund', 'short_term']:
            # Short-term goals have higher debt/cash
            allocation = {
                'equity': 0.2,
                'debt': 0.5,
                'gold': 0.1,
                'cash': 0.2
            }
        else:
            # Default moderate allocation
            allocation = {
                'equity': 0.5,
                'debt': 0.3,
                'gold': 0.1,
                'cash': 0.1
            }
    
    # Remove tiny allocations for visualization simplicity
    simplified_allocation = {k: v for k, v in allocation.items() if v >= 0.05}
    
    # If the sum isn't close to 1.0, normalize it
    total = sum(simplified_allocation.values())
    if abs(total - 1.0) > 0.01:
        simplified_allocation = {k: v/total for k, v in simplified_allocation.items()}
    
    # Format for chart visualization
    allocation_data = {
        'labels': list(simplified_allocation.keys()),
        'values': [simplified_allocation[k] for k in simplified_allocation.keys()],
        'colors': _get_allocation_colors(list(simplified_allocation.keys()))
    }
    
    return allocation_data

def _get_allocation_colors(asset_classes):
    """Get standard colors for asset classes."""
    color_map = {
        'equity': '#4285F4',  # Blue
        'debt': '#34A853',    # Green
        'gold': '#FBBC05',    # Yellow
        'cash': '#EA4335',    # Red
        'real_estate': '#8F44AD',  # Purple
        'alternative': '#F39C12',  # Orange
        'bonds': '#27AE60',   # Dark Green
        'international': '#3498DB'  # Light Blue
    }
    
    return [color_map.get(asset.lower(), '#CCCCCC') for asset in asset_classes]

def _get_probability_projection(goal, resolution):
    """Get probability distribution projection data for a goal."""
    # Implementation would generate probability distribution data
    # This is a simplified example
    
    # Get probability from goal
    probability = goal.get('success_probability', 0)
    target_amount = goal.get('target_amount', 0)
    
    # Create a basic normal distribution around the target
    if resolution == 'high':
        points = 50
    elif resolution == 'medium':
        points = 20
    else:  # 'low'
        points = 10
    
    # Create x-axis values (possible outcome amounts)
    min_value = target_amount * 0.5
    max_value = target_amount * 1.5
    step = (max_value - min_value) / points
    
    x_values = [min_value + i * step for i in range(points + 1)]
    
    # Create y-axis values (probability density)
    # Center of distribution depends on success probability
    mean = target_amount * (0.8 + 0.4 * probability)
    stddev = target_amount * 0.2
    
    import math
    y_values = []
    for x in x_values:
        # Simplified normal distribution formula
        y = (1 / (stddev * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mean) / stddev) ** 2)
        y_values.append(y)
    
    # Normalize y values to make area = 1
    total = sum(y_values) * step
    y_values = [y / total for y in y_values]
    
    # Determine target line position (where x = target_amount)
    target_position = min(points, max(0, int((target_amount - min_value) / step)))
    
    return {
        'x': x_values,
        'y': y_values,
        'target': target_amount,
        'target_position': target_position,
        'probability': probability,
        'resolution': resolution
    }

def _get_retirement_projection(goal, resolution):
    """Get retirement-specific projection data."""
    # Implementation would generate retirement-specific projection
    # This is a simplified example
    
    # Extract retirement parameters
    funding_strategy = {}
    try:
        if isinstance(goal.get('funding_strategy'), dict):
            funding_strategy = goal.get('funding_strategy')
        elif isinstance(goal.get('funding_strategy'), str):
            funding_strategy = json.loads(goal.get('funding_strategy', '{}'))
    except:
        pass
    
    retirement_age = funding_strategy.get('retirement_age', 65)
    withdrawal_rate = funding_strategy.get('withdrawal_rate', 0.04)
    yearly_expenses = funding_strategy.get('yearly_expenses', 0)
    
    # Create retirement income projection
    current_age = 30  # Default assumption
    years_to_retirement = max(1, retirement_age - current_age)
    projection_years = min(30, years_to_retirement + 25)  # Project 25 years into retirement
    
    target_amount = goal.get('target_amount', 0)
    
    # Labels for years
    labels = [str(current_age + i) for i in range(projection_years)]
    
    # Income values before and during retirement
    income_values = []
    expense_values = []
    
    for i in range(projection_years):
        age = current_age + i
        if age < retirement_age:
            # Pre-retirement income (simplified)
            income_values.append(yearly_expenses * 1.5)  # Assuming income is 1.5x expenses
            expense_values.append(yearly_expenses)
        else:
            # Retirement income from corpus
            retirement_income = target_amount * withdrawal_rate
            income_values.append(retirement_income)
            expense_values.append(yearly_expenses * (1 + 0.03) ** (i - years_to_retirement))  # 3% inflation
    
    return {
        'labels': labels,
        'income': income_values,
        'expenses': expense_values,
        'retirement_age': retirement_age,
        'withdrawal_rate': withdrawal_rate,
        'resolution': resolution
    }

def _get_education_projection(goal, resolution):
    """Get education-specific projection data."""
    # Implementation would generate education-specific projection
    # This is a simplified example
    
    # Extract education parameters
    funding_strategy = {}
    try:
        if isinstance(goal.get('funding_strategy'), dict):
            funding_strategy = goal.get('funding_strategy')
        elif isinstance(goal.get('funding_strategy'), str):
            funding_strategy = json.loads(goal.get('funding_strategy', '{}'))
    except:
        pass
    
    education_type = funding_strategy.get('education_type', 'college')
    years = funding_strategy.get('years', 4)
    yearly_cost = funding_strategy.get('yearly_cost', 0)
    
    # Get timeframe
    timeframe = goal.get('timeframe', '')
    education_start = None
    
    try:
        if isinstance(timeframe, str) and timeframe:
            education_start = datetime.fromisoformat(timeframe.split('T')[0] if 'T' in timeframe else timeframe)
    except:
        # Use current date + 5 years as fallback
        education_start = datetime.now().replace(year=datetime.now().year + 5)
    
    if not education_start:
        education_start = datetime.now().replace(year=datetime.now().year + 5)
    
    # Create education cost projection by year
    education_years = [education_start.year + i for i in range(years)]
    costs = []
    
    for i in range(years):
        # Assume some inflation in yearly costs
        inflation_factor = (1 + 0.08) ** i  # 8% education inflation
        yearly_expense = yearly_cost * inflation_factor
        costs.append(round(yearly_expense, -2))  # Round to nearest 100
    
    # Add labels for education years
    if education_type == 'undergraduate':
        labels = [f"Year {i+1} (UG)" for i in range(years)]
    elif education_type == 'graduate':
        labels = [f"Year {i+1} (PG)" for i in range(years)]
    else:
        labels = [f"Year {i+1}" for i in range(years)]
    
    return {
        'years': education_years,
        'labels': labels,
        'costs': costs,
        'education_type': education_type,
        'total_years': years,
        'resolution': resolution
    }

def _get_mortgage_projection(goal, resolution):
    """Get mortgage/home purchase specific projection data."""
    # Implementation would generate mortgage-specific projection
    # This is a simplified example
    
    # Extract home purchase parameters
    funding_strategy = {}
    try:
        if isinstance(goal.get('funding_strategy'), dict):
            funding_strategy = goal.get('funding_strategy')
        elif isinstance(goal.get('funding_strategy'), str):
            funding_strategy = json.loads(goal.get('funding_strategy', '{}'))
    except:
        pass
    
    property_value = funding_strategy.get('property_value', 0)
    down_payment_percent = funding_strategy.get('down_payment_percent', 0.2)
    loan_term_years = funding_strategy.get('loan_term_years', 20)
    interest_rate = funding_strategy.get('interest_rate', 0.08)  # 8%
    
    # Calculate loan details
    down_payment = property_value * down_payment_percent
    loan_amount = property_value - down_payment
    monthly_payment = _calculate_mortgage_payment(loan_amount, interest_rate, loan_term_years)
    
    # Create amortization schedule
    remaining_principal = []
    interest_paid = []
    principal_paid = []
    
    current_loan = loan_amount
    total_interest = 0
    total_principal = 0
    
    # Determine data points based on resolution
    if resolution == 'high':
        intervals = min(loan_term_years * 12, 360)  # Monthly for up to 30 years
        labels = [f"Month {i+1}" for i in range(intervals)]
    elif resolution == 'medium':
        intervals = min(loan_term_years, 30)  # Yearly for up to 30 years
        labels = [f"Year {i+1}" for i in range(intervals)]
    else:  # 'low'
        intervals = min(loan_term_years // 5 + (1 if loan_term_years % 5 else 0), 6)  # Every 5 years
        labels = [f"Year {(i+1)*5}" for i in range(intervals)]
    
    # Calculate amortization values at each interval
    for i in range(intervals):
        if resolution == 'high':
            # Monthly calculation
            monthly_interest = current_loan * interest_rate / 12
            monthly_principal = monthly_payment - monthly_interest
            
            total_interest += monthly_interest
            total_principal += monthly_principal
            current_loan -= monthly_principal
            
            remaining_principal.append(current_loan)
            interest_paid.append(total_interest)
            principal_paid.append(total_principal)
        elif resolution == 'medium':
            # Yearly calculation (simplified)
            year_interest = 0
            year_principal = 0
            
            for m in range(12):
                month_interest = current_loan * interest_rate / 12
                month_principal = monthly_payment - month_interest
                
                year_interest += month_interest
                year_principal += month_principal
                current_loan -= month_principal
            
            total_interest += year_interest
            total_principal += year_principal
            
            remaining_principal.append(current_loan)
            interest_paid.append(total_interest)
            principal_paid.append(total_principal)
        else:  # 'low'
            # Every 5 years (simplified)
            five_year_interest = 0
            five_year_principal = 0
            
            for y in range(5):
                for m in range(12):
                    month_interest = current_loan * interest_rate / 12
                    month_principal = monthly_payment - month_interest
                    
                    five_year_interest += month_interest
                    five_year_principal += month_principal
                    current_loan -= month_principal
            
            total_interest += five_year_interest
            total_principal += five_year_principal
            
            remaining_principal.append(current_loan)
            interest_paid.append(total_interest)
            principal_paid.append(total_principal)
    
    return {
        'labels': labels,
        'remaining_principal': remaining_principal,
        'interest_paid': interest_paid,
        'principal_paid': principal_paid,
        'property_value': property_value,
        'down_payment': down_payment,
        'loan_amount': loan_amount,
        'monthly_payment': monthly_payment,
        'loan_term_years': loan_term_years,
        'interest_rate': interest_rate,
        'resolution': resolution
    }

def _calculate_mortgage_payment(loan_amount, annual_interest_rate, loan_term_years):
    """Calculate monthly mortgage payment using standard formula."""
    monthly_rate = annual_interest_rate / 12
    num_payments = loan_term_years * 12
    
    if monthly_rate == 0:
        return loan_amount / num_payments
    
    payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
    return payment

def _generate_portfolio_timeline(goals):
    """Generate timeline projection across all goals."""
    # Sort goals by timeframe
    sorted_goals = sorted(goals, key=lambda g: g.get('timeframe', '9999-12-31'))
    
    # Get earliest and latest timeframes
    earliest = None
    latest = None
    
    for goal in sorted_goals:
        timeframe = goal.get('timeframe', '')
        if timeframe:
            try:
                goal_date = datetime.fromisoformat(timeframe.split('T')[0] if 'T' in timeframe else timeframe)
                if earliest is None or goal_date < earliest:
                    earliest = goal_date
                if latest is None or goal_date > latest:
                    latest = goal_date
            except:
                pass
    
    # If no valid dates found, use defaults
    if earliest is None:
        earliest = datetime.now()
    if latest is None:
        latest = datetime.now().replace(year=datetime.now().year + 10)
    
    # Ensure at least 1 year difference
    if (latest - earliest).days < 365:
        latest = earliest.replace(year=earliest.year + 1)
    
    # Generate timeline with years as labels
    start_year = earliest.year
    end_year = latest.year
    years = end_year - start_year + 1
    
    # Create timeline data for up to 10 years (consolidate if more)
    if years > 10:
        # Group by multiple years
        step = years // 10 + (1 if years % 10 else 0)
        labels = [str(start_year + i * step) for i in range(min(10, years // step + (1 if years % step else 0)))]
    else:
        # One entry per year
        labels = [str(start_year + i) for i in range(years)]
    
    # Create goal events on timeline
    events = []
    
    for goal in sorted_goals:
        timeframe = goal.get('timeframe', '')
        if not timeframe:
            continue
            
        try:
            goal_date = datetime.fromisoformat(timeframe.split('T')[0] if 'T' in timeframe else timeframe)
            goal_year = goal_date.year
            
            # Find position in timeline
            if years > 10:
                # Grouped years
                position = (goal_year - start_year) // step
            else:
                # One per year
                position = goal_year - start_year
            
            # Create event entry
            if position >= 0 and position < len(labels):
                events.append({
                    'goal_id': goal.get('id', ''),
                    'title': goal.get('title', ''),
                    'year': goal_year,
                    'position': position,
                    'amount': goal.get('target_amount', 0),
                    'category': goal.get('category', 'other')
                })
        except:
            pass
    
    return {
        'labels': labels,
        'events': events,
        'start_year': start_year,
        'end_year': end_year
    }
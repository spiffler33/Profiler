"""API endpoints for the question flow feature.

This module provides API endpoints for:
1. Retrieving the next question in a flow
2. Submitting answers to questions
3. Getting dynamic question data with enhanced content

These endpoints support the frontend QuestionFlowManager, QuestionResponseSubmitter
and DynamicQuestionRenderer components.
"""

import logging
import time
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from flask import Blueprint, jsonify, request, current_app, g

# Import relevant models and services
from services.question_service import QuestionService, QuestionLogger
from models.profile_understanding import ProfileUnderstandingCalculator
from models.question_generator import QuestionGenerator

# Import common API utilities
from api.v2.utils import (
    monitor_performance, check_cache, cache_response,
    rate_limit_middleware, check_admin_access, create_error_response
)

# Initialize logging
logger = logging.getLogger(__name__)

# Create Blueprint for API routes
question_flow_api = Blueprint('question_flow_api', __name__)

# Cache key generator for question flow operations
def generate_question_flow_cache_key(profile_id, operation, params=None):
    """Generate a cache key for a specific question flow operation."""
    if params:
        param_str = json.dumps(params, sort_keys=True)
        return f"question_flow:{profile_id}:{operation}:{hash(param_str)}"
    return f"question_flow:{profile_id}:{operation}"

@question_flow_api.route('/questions/flow', methods=['GET'])
@monitor_performance
def get_next_question():
    """
    Get the next question in the flow for a profile.
    
    This endpoint retrieves the next question to be displayed based on
    the profile's current state and question flow logic.
    
    Query Parameters:
        - profile_id: The ID of the profile to get the next question for
        
    Returns:
        JSON response with the next question and completion metrics
    """
    try:
        # Get profile ID from query parameters
        profile_id = request.args.get('profile_id')
        
        if not profile_id:
            return jsonify({
                'error': 'Missing parameter',
                'message': 'profile_id is required'
            }), 400
            
        # Try to get from cache first, but with short TTL since questions change
        cache_key = generate_question_flow_cache_key(profile_id, "next_question")
        cached_response = check_cache(cache_key)
        if cached_response:
            g.cache_status = "HIT"
            logger.info(f"Cache hit for next question for profile {profile_id}")
            return cached_response
            
        g.cache_status = "MISS"
            
        # Get services
        question_service = _get_question_service()
        if not question_service:
            return jsonify({
                'error': 'Service unavailable',
                'message': 'Question service is not available'
            }), 503
            
        # Get the next question
        next_question, profile = question_service.get_next_question(profile_id)
        
        if not profile:
            return jsonify({
                'error': 'Profile not found',
                'message': f'No profile found with ID {profile_id}'
            }), 404
            
        # Get completion metrics
        completion_metrics = question_service.get_profile_completion(profile)
        
        # Build response
        response = {
            'profile_id': profile_id,
            'completion': completion_metrics,
            'no_questions': next_question is None,
            'next_question': next_question
        }
        
        # Add additional profile context if available
        if profile:
            response['profile_summary'] = {
                'name': profile.get('name', ''),
                'understanding_level': profile.get('understanding_level', {}),
                'answered_questions': len(profile.get('answers', []))
            }
            
        # Cache the response, but only briefly as questions change with answers
        cache_response(cache_key, response, ttl=60)  # Cache for 1 minute
        
        # Log that the question was displayed to the user
        if next_question:
            question_logger = QuestionLogger()
            question_logger.log_question_displayed(profile_id, next_question.get('id'), next_question)
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.exception(f"Error retrieving next question: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@question_flow_api.route('/questions/submit', methods=['POST'])
@monitor_performance
def submit_question_answer():
    """
    Submit an answer to a question.
    
    This endpoint records the user's answer to a specific question and
    updates their profile accordingly.
    
    Request Body:
        JSON object containing:
        - profile_id: ID of the profile
        - question_id: ID of the question being answered
        - answer: The answer value (can be string, number, or array)
        
    Returns:
        JSON response with submission status and updated completion metrics
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must contain valid JSON'
            }), 400
            
        # Validate required fields
        required_fields = ['profile_id', 'question_id', 'answer']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'message': f'The following fields are required: {", ".join(missing_fields)}'
            }), 400
            
        # Get services
        question_service = _get_question_service()
        if not question_service:
            return jsonify({
                'error': 'Service unavailable',
                'message': 'Question service is not available'
            }), 503
            
        # Extract data
        profile_id = data.get('profile_id')
        question_id = data.get('question_id')
        answer = data.get('answer')
        
        # Create answer data structure
        answer_data = {
            'question_id': question_id,
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save the answer
        result = question_service.save_question_answer(profile_id, answer_data)
        
        if not result:
            return jsonify({
                'error': 'Failed to save answer',
                'message': 'Unable to save the answer to the profile'
            }), 500
            
        # Get updated completion metrics
        updated_metrics = question_service.get_profile_completion(profile_id)
        
        # Build response
        response = {
            'success': True,
            'profile_id': profile_id,
            'question_id': question_id,
            'updated_completion': updated_metrics
        }
        
        # Invalidate the next question cache for this profile
        cache_key = generate_question_flow_cache_key(profile_id, "next_question")
        _invalidate_cache(cache_key)
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.exception(f"Error submitting question answer: {str(e)}")
        # Include more detailed error information for debugging
        error_type = type(e).__name__
        error_details = {
            'error': 'Internal server error',
            'message': str(e),
            'error_type': error_type,
            'timestamp': datetime.now().isoformat()
        }
        # Log the full error details for server-side troubleshooting
        logger.error(f"Detailed error info: {json.dumps(error_details)}")
        return jsonify(error_details), 500

@question_flow_api.route('/questions/dynamic', methods=['GET'])
@monitor_performance
def get_dynamic_question_data():
    """
    Get enhanced data for a dynamic question.
    
    This endpoint provides additional context, data sources, and content
    for dynamic questions that adapt to the user's profile.
    
    Query Parameters:
        - profile_id: ID of the profile
        - question_id: ID of the question to get dynamic data for
        
    Returns:
        JSON response with enhanced question data
    """
    try:
        # Get query parameters
        profile_id = request.args.get('profile_id')
        question_id = request.args.get('question_id')
        
        if not profile_id or not question_id:
            return jsonify({
                'error': 'Missing parameters',
                'message': 'Both profile_id and question_id are required'
            }), 400
            
        # Try to get from cache first
        cache_key = generate_question_flow_cache_key(
            profile_id, f"dynamic_question_{question_id}"
        )
        cached_response = check_cache(cache_key)
        if cached_response:
            g.cache_status = "HIT"
            return cached_response
            
        g.cache_status = "MISS"
        
        # Get services
        question_service = _get_question_service()
        if not question_service:
            return jsonify({
                'error': 'Service unavailable',
                'message': 'Question service is not available'
            }), 503
            
        # Get the profile first
        profile = question_service.profile_manager.get_profile(profile_id)
        if not profile:
            return jsonify({
                'error': 'Profile not found',
                'message': f'No profile found with ID {profile_id}'
            }), 404
            
        # Get dynamic question data
        dynamic_data = _get_dynamic_question_data(question_id, profile, question_service)
        
        if not dynamic_data:
            return jsonify({
                'error': 'Question data not found',
                'message': f'No dynamic data found for question {question_id}'
            }), 404
            
        # Cache the response
        cache_response(cache_key, dynamic_data, ttl=300)  # Cache for 5 minutes
        
        return jsonify(dynamic_data), 200
        
    except Exception as e:
        logger.exception(f"Error retrieving dynamic question data: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

def _get_question_service():
    """Get the question service from current app config or create a new one."""
    question_service = current_app.config.get('question_service')
    
    if not question_service:
        # Try to create a new question service
        question_repository = current_app.config.get('question_repository')
        profile_manager = current_app.config.get('profile_manager')
        llm_service = current_app.config.get('llm_service')
        
        if question_repository and profile_manager:
            question_service = QuestionService(
                question_repository, 
                profile_manager,
                llm_service
            )
    
    return question_service

def _get_dynamic_question_data(question_id, profile, question_service):
    """
    Get enhanced data for a dynamic question.
    
    Args:
        question_id: ID of the question
        profile: User profile
        question_service: Question service instance
        
    Returns:
        Dict with enhanced question data
    """
    # Check if this is a dynamically generated question
    is_generated = question_id.startswith('gen_question_')
    
    # Look for the question in the repository
    question = None
    
    if is_generated:
        # For generated questions, look in cache or answers
        if hasattr(question_service, 'dynamic_questions_cache'):
            question = question_service.dynamic_questions_cache.get(question_id)
            
        if not question:
            # Try to find in previous answers
            for answer in profile.get('answers', []):
                if answer.get('question_metadata', {}).get('id') == question_id:
                    question = answer.get('question_metadata')
                    break
    else:
        # For regular questions, check the repository
        repo = question_service.question_repository
        all_questions = repo.get_all_questions()
        
        for q in all_questions:
            if q.get('id') == question_id:
                question = q
                break
    
    if not question:
        # If still not found, return minimal data
        return {
            'id': question_id,
            'is_dynamic': True,
            'data_sources': []
        }
    
    # Check to see if it's an emergency fund question
    if "emergency_fund" in question_id:
        try:
            # Calculate emergency fund recommendations
            emergency_fund_data = question_service._calculate_emergency_fund_recommendations(profile)
            if emergency_fund_data:
                # Add enhanced content
                question = question_service._add_emergency_fund_calculations(
                    question, 
                    emergency_fund_data
                )
        except Exception as e:
            logger.error(f"Error adding emergency fund calculations: {str(e)}")
    
    # Add data sources if not present
    if 'data_sources' not in question:
        question['data_sources'] = _extract_data_sources(profile, question_id)
    
    # Add reasoning if not present
    if 'reasoning' not in question and is_generated:
        question['reasoning'] = "This question was generated based on your profile information to better understand your financial situation."
    
    # Add context panel if not present
    if 'context_panel' not in question:
        question['context_panel'] = _generate_context_panel(profile, question)
    
    # Return the enhanced question data
    return question

def _extract_data_sources(profile, question_id):
    """
    Extract data sources from the profile that are relevant to a question.
    
    Args:
        profile: User profile
        question_id: ID of the question
        
    Returns:
        List of data sources
    """
    data_sources = []
    
    # Map of keywords to profile data
    keyword_mappings = {
        'income': ['financial_basics_annual_income', 'financial_basics_monthly_income'],
        'expense': ['financial_basics_monthly_expenses'],
        'saving': ['financial_basics_savings_rate', 'financial_basics_monthly_savings'],
        'emergency': ['goals_emergency_fund_exists', 'goals_emergency_fund_amount'],
        'retirement': ['goals_retirement_age', 'goals_retirement_corpus'],
        'investment': ['assets_debts_investments', 'next_level_investment_'],
        'debt': ['assets_debts_loans', 'goals_debt_repayment'],
        'home': ['goals_home_purchase', 'assets_debts_real_estate'],
        'education': ['goals_education', 'next_level_education_']
    }
    
    # Find which keywords appear in the question ID
    relevant_keywords = []
    for keyword in keyword_mappings:
        if keyword in question_id.lower():
            relevant_keywords.append(keyword)
    
    # If no keywords matched, use some defaults
    if not relevant_keywords:
        if question_id.startswith('gen_question_'):
            relevant_keywords = ['income', 'expense', 'saving']
        else:
            # Return empty data sources for non-matched questions
            return []
    
    # Extract relevant answers from the profile
    for keyword in relevant_keywords:
        question_ids = keyword_mappings[keyword]
        for q_id in question_ids:
            for answer in profile.get('answers', []):
                if answer.get('question_id', '').startswith(q_id):
                    answer_value = answer.get('answer')
                    formatted_value = _format_answer_value(answer_value)
                    
                    # Get question text if available
                    question_text = answer.get('question_text', q_id.replace('_', ' ').title())
                    
                    data_sources.append({
                        'name': question_text,
                        'value': formatted_value,
                        'question_id': answer.get('question_id')
                    })
    
    # Limit to 5 most relevant sources
    return data_sources[:5]

def _format_answer_value(value):
    """Format an answer value for display."""
    if isinstance(value, (int, float)):
        if value >= 1000:
            return f"₹{value:,.0f}"
        return str(value)
    elif isinstance(value, list):
        return ", ".join(str(v) for v in value)
    elif isinstance(value, bool):
        return "Yes" if value else "No"
    elif value is None:
        return "Not provided"
    return str(value)

def _generate_context_panel(profile, question):
    """
    Generate a context panel explaining why this question is being asked.
    
    Args:
        profile: User profile
        question: Question data
        
    Returns:
        HTML string with context explanation
    """
    question_id = question.get('id', '')
    question_category = question.get('category', '')
    
    # Default context panel
    context = "<p>This question helps us understand your financial situation better.</p>"
    
    # Add category-specific context
    if 'retirement' in question_id or 'retirement' in question_category:
        context = """
        <p>This question helps us understand your retirement goals and planning.</p>
        <p>Retirement planning is crucial in India, where formal pension systems are limited.
        The earlier you start planning, the more secure your retirement will be.</p>
        """
    elif 'emergency' in question_id or 'emergency' in question_category:
        context = """
        <p>This question helps us understand your emergency fund preparedness.</p>
        <p>Financial experts in India typically recommend maintaining 6-9 months of expenses
        as an emergency fund to handle unexpected situations.</p>
        """
    elif 'investment' in question_id or 'investment' in question_category:
        context = """
        <p>This question helps us understand your investment strategy and preferences.</p>
        <p>A diversified investment approach typically includes a mix of equity, debt,
        and other asset classes based on your goals and risk tolerance.</p>
        """
    elif 'tax' in question_id or 'tax' in question_category:
        context = """
        <p>This question helps us understand your tax planning strategy.</p>
        <p>Effective tax planning is important for maximizing your investments and
        ensuring compliance with Indian tax regulations.</p>
        """
    elif 'education' in question_id or 'education' in question_category:
        context = """
        <p>This question helps us understand your education funding goals.</p>
        <p>Education costs in India have been rising faster than inflation, making
        early planning essential for higher education goals.</p>
        """
    
    # Find related goals to add to context
    related_goals = _find_related_goals(profile, question)
    
    return context

def _find_related_goals(profile, question):
    """
    Find goals in the profile that are related to this question.
    
    Args:
        profile: User profile
        question: Question data
        
    Returns:
        List of related goals
    """
    related_goals = []
    question_id = question.get('id', '')
    question_category = question.get('category', '')
    
    # Extract keywords from question
    keywords = set()
    for text in [question_id, question_category, question.get('text', '')]:
        text = text.lower()
        for keyword in ['retirement', 'emergency', 'education', 'home', 'debt', 'investment', 'saving']:
            if keyword in text:
                keywords.add(keyword)
    
    # Look for matching goals in profile
    for answer in profile.get('answers', []):
        if not answer.get('question_id', '').startswith('goals_'):
            continue
            
        # Check if this answer represents a goal
        goal_match = False
        goal_text = ""
        goal_value = None
        
        # Extract goal text and check for keyword match
        if 'question_text' in answer:
            goal_text = answer['question_text']
            goal_value = answer.get('answer')
            
            # Check if any keyword matches
            for keyword in keywords:
                if keyword in goal_text.lower():
                    goal_match = True
                    break
        
        # Add to related goals if matched
        if goal_match and goal_value:
            # Format the goal value
            if isinstance(goal_value, (int, float)) and goal_value > 1000:
                formatted_value = f"₹{goal_value:,.0f}"
            else:
                formatted_value = str(goal_value)
                
            related_goals.append({
                'title': goal_text,
                'value': formatted_value,
                'question_id': answer.get('question_id')
            })
    
    return related_goals

def _invalidate_cache(cache_key):
    """Invalidate a cache entry."""
    # Import the cache directly
    try:
        # Try to get the cache from the configured app
        cache = current_app.config.get('response_cache')
        if cache:
            # Use the cache's delete method
            cache.delete(cache_key)
            logger.info(f"Cache key invalidated: {cache_key}")
        else:
            # Try the monte carlo cache as fallback
            from models.monte_carlo.cache import _cache
            if hasattr(_cache, 'delete'):
                _cache.delete(cache_key)
                logger.info(f"Monte Carlo cache key invalidated: {cache_key}")
            else:
                logger.warning(f"No cache available to invalidate key: {cache_key}")
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        # Don't raise - cache invalidation is background operation
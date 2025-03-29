"""
Mock API endpoints for testing frontend components
"""

import json
import random
import time
from flask import Blueprint, jsonify, request, abort

mock_api = Blueprint('mock_api', __name__, url_prefix='/api/v2')

# Sample mock data
MOCK_PROFILES = {
    'test-profile-123': {
        'id': 'test-profile-123',
        'name': 'Test User',
        'email': 'test@example.com',
        'created_at': '2025-01-15T10:30:00Z',
        'updated_at': '2025-03-25T14:22:15Z'
    }
}

MOCK_OVERVIEW = {
    'profile': {
        'id': 'test-profile-123',
        'name': 'Test User',
        'createdAt': '2025-01-15T10:30:00Z',
        'updatedAt': '2025-03-25T14:22:15Z'
    },
    'summary': {
        'netWorth': 4528000,
        'monthlyIncome': 187500,
        'monthlyExpenses': 105000,
        'monthlySavings': 82500,
        'goalSuccessRate': 72.5
    },
    'assets': {
        'allocation': [
            {'name': 'Equity', 'percentage': 45, 'color': '#4F46E5'},
            {'name': 'Debt', 'percentage': 25, 'color': '#2563EB'},
            {'name': 'Real Estate', 'percentage': 15, 'color': '#0EA5E9'},
            {'name': 'Gold', 'percentage': 10, 'color': '#EAB308'},
            {'name': 'Cash', 'percentage': 5, 'color': '#84CC16'}
        ]
    },
    'goals': [
        {
            'id': 'goal-1',
            'name': 'Retirement',
            'type': 'retirement',
            'targetAmount': 12500000,
            'currentAmount': 3750000,
            'targetDate': '2050-01-01',
            'progress': 30,
            'probability': 65
        },
        {
            'id': 'goal-2',
            'name': 'Home Purchase',
            'type': 'home',
            'targetAmount': 7500000,
            'currentAmount': 5625000,
            'targetDate': '2027-06-30',
            'progress': 75,
            'probability': 88
        },
        {
            'id': 'goal-3',
            'name': 'Children\'s Education',
            'type': 'education',
            'targetAmount': 4000000,
            'currentAmount': 1000000,
            'targetDate': '2035-04-15',
            'progress': 25,
            'probability': 42
        },
        {
            'id': 'goal-4',
            'name': 'Emergency Fund',
            'type': 'emergency',
            'targetAmount': 625000,
            'currentAmount': 156250,
            'targetDate': None,
            'progress': 25,
            'probability': 35
        }
    ],
    'recommendations': [
        {
            'id': 'rec-1',
            'type': 'contribution',
            'title': 'Increase Retirement Contribution',
            'description': 'Increasing your monthly retirement contribution by ₹15,000 will significantly improve your retirement goal success probability.',
            'impact': 'Improves retirement probability by 25%',
            'actionType': 'adjust_contribution',
            'actionText': 'Apply'
        },
        {
            'id': 'rec-2',
            'type': 'allocation',
            'title': 'Optimize Asset Allocation',
            'description': 'Reallocating 10% from debt to equity could improve your long-term returns.',
            'impact': 'Potential 3% increase in annual returns',
            'actionType': 'adjust_allocation',
            'actionText': 'Apply'
        },
        {
            'id': 'rec-3',
            'type': 'expense',
            'title': 'Reduce Discretionary Expenses',
            'description': 'Reducing monthly discretionary expenses by ₹10,000 would allow higher savings rate.',
            'impact': 'Improves all goal probabilities by ~5-10%',
            'actionType': 'adjust_expense',
            'actionText': 'Learn More'
        }
    ]
}


@mock_api.route('/profiles/<profile_id>/overview', methods=['GET'])
def get_profile_overview(profile_id):
    """Get financial overview for a profile"""
    # Simulate delay
    time.sleep(0.5)
    
    # Simulate occasional errors for testing
    if random.random() < 0.1:  # 10% chance of error
        abort(500, description="Simulated server error")
    
    if profile_id not in MOCK_PROFILES:
        abort(404, description=f"Profile {profile_id} not found")
    
    # Return mock overview data
    return jsonify(MOCK_OVERVIEW)


@mock_api.route('/profiles/<profile_id>/recommendations/<action_type>', methods=['POST'])
def apply_recommendation(profile_id, action_type):
    """Apply a recommendation action"""
    # Simulate delay
    time.sleep(0.8)
    
    # Validate profile
    if profile_id not in MOCK_PROFILES:
        abort(404, description=f"Profile {profile_id} not found")
    
    # Get recommendation ID from request
    data = request.get_json()
    recommendation_id = data.get('recommendationId')
    
    if not recommendation_id:
        abort(400, description="Recommendation ID is required")
    
    # Validate action type
    valid_actions = ['adjust_contribution', 'adjust_allocation', 'adjust_timeline', 'apply']
    if action_type not in valid_actions:
        abort(400, description=f"Invalid action type: {action_type}")
    
    # Simulate success response
    return jsonify({
        'success': True,
        'message': f"Recommendation {recommendation_id} applied successfully",
        'actionType': action_type,
        'appliedAt': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })


@mock_api.route('/profiles/<profile_id>/recommendations/apply', methods=['POST'])
def apply_general_recommendation(profile_id):
    """Apply a general recommendation"""
    return apply_recommendation(profile_id, 'apply')


# Question Flow API mock endpoints
@mock_api.route('/questions/flow', methods=['GET'])
def get_next_question():
    """Get the next question for a profile"""
    # Simulate delay
    time.sleep(0.6)
    
    # Get profile ID from query param
    profile_id = request.args.get('profile_id')
    
    if not profile_id:
        abort(400, description="profile_id is required")
    
    # Validate profile
    if profile_id not in MOCK_PROFILES and not profile_id.startswith('test-'):
        abort(404, description=f"Profile {profile_id} not found")
    
    # Generate a mock question
    question_types = ['core', 'next_level', 'behavioral', 'goal']
    question_categories = ['demographics', 'financial_basics', 'assets_and_debts', 'goals']
    input_types = ['text', 'number', 'select', 'radio', 'multiselect']
    
    question_type = random.choice(question_types)
    category = random.choice(question_categories)
    input_type = random.choice(input_types)
    
    # Create question ID based on type and category
    question_id = f"{question_type}_{category}_{int(time.time())}"
    
    # Create question text based on category
    question_texts = {
        'demographics': [
            'What is your age?',
            'What is your marital status?',
            'How many dependents do you have?'
        ],
        'financial_basics': [
            'What is your annual income?',
            'What are your monthly expenses?',
            'What is your current savings rate?'
        ],
        'assets_and_debts': [
            'What is the total value of your investments?',
            'Do you have any outstanding loans?',
            'What is your current emergency fund amount?'
        ],
        'goals': [
            'When do you plan to retire?',
            'Are you saving for a home purchase?',
            'What are your education funding goals?'
        ]
    }
    
    question_text = random.choice(question_texts.get(category, ['Default question']))
    
    # Create options for select/radio/multiselect
    options = None
    if input_type in ['select', 'radio', 'multiselect']:
        if category == 'demographics':
            options = ['Single', 'Married', 'Divorced', 'Widowed']
        elif category == 'financial_basics':
            options = ['Less than ₹5 lakhs', '₹5-10 lakhs', '₹10-20 lakhs', 'More than ₹20 lakhs']
        elif category == 'assets_and_debts':
            options = ['Yes', 'No', 'Not Sure']
        elif category == 'goals':
            options = ['High Priority', 'Medium Priority', 'Low Priority', 'Not Applicable']
    
    # Create completion metrics
    completion = {
        'overall': random.randint(10, 90),
        'core': {
            'overall': random.randint(30, 100),
            'count': random.randint(3, 10),
            'total': 10
        },
        'next_level': {
            'completion': random.randint(10, 80),
            'questions_answered': random.randint(1, 8),
            'questions_count': 10
        },
        'behavioral': {
            'completion': random.randint(0, 70),
            'questions_answered': random.randint(0, 5),
            'questions_count': 7
        }
    }
    
    # Create question object
    question = {
        'id': question_id,
        'text': question_text,
        'type': question_type,
        'category': category,
        'input_type': input_type,
        'help_text': f'This is a help text for the {category} question.'
    }
    
    # Add options if applicable
    if options:
        question['options'] = options
    
    # Add min/max for number input
    if input_type == 'number':
        question['min'] = 0
        question['max'] = 10000000
    
    # Return the response
    return jsonify({
        'next_question': question,
        'completion': completion,
        'no_questions': False
    })


@mock_api.route('/questions/submit', methods=['POST'])
def submit_question_answer():
    """Submit an answer to a question"""
    # Simulate delay
    time.sleep(0.5)
    
    # Get request data
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['profile_id', 'question_id', 'answer']
    for field in required_fields:
        if field not in data:
            abort(400, description=f"{field} is required")
    
    # Simulate occasional errors for testing
    if data.get('answer') == 'trigger_error':
        abort(500, description="Simulated error in answer submission")
        
    # Return success response
    return jsonify({
        'success': True,
        'message': 'Answer submitted successfully',
        'next_url': '/questions',
        'question_id': data.get('question_id'),
        'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })


# Add error handlers
@mock_api.errorhandler(400)
def handle_bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': str(error.description)
    }), 400


@mock_api.errorhandler(404)
def handle_not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': str(error.description)
    }), 404


@mock_api.errorhandler(500)
def handle_server_error(error):
    return jsonify({
        'error': 'Server Error',
        'message': str(error.description) if error.description else 'An unexpected error occurred'
    }), 500
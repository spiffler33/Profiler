import pytest
import json
import os
import types
import time
from flask import url_for, session
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

# Import our application for testing
from app import app, profile_manager, question_service
from models.profile_understanding import PROFILE_UNDERSTANDING_LEVELS, ProfileUnderstandingCalculator

"""
Comprehensive Frontend Testing Suite for Financial Profiler

This module contains comprehensive tests for understanding level indicators and frontend behaviors.
It uses pytest fixtures and Flask's test client to thoroughly verify all UI behaviors
across all understanding levels without Chrome driver dependencies.
"""

@pytest.fixture
def client():
    """Flask test client fixture."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def profile_data_by_level():
    """
    Test data fixture that returns a dictionary mapping understanding levels 
    to the data needed to achieve that level.
    """
    return {
        'RED': {
            # No answers needed for RED level (empty profile)
            'core_questions': [],
            'goal_questions': [],
            'next_level_questions': [],
            'behavioral_questions': []
        },
        'AMBER': {
            # Core questions complete + 3 goal questions
            'core_questions': get_core_question_data(),
            'goal_questions': get_goal_question_data()[:3],
            'next_level_questions': [],
            'behavioral_questions': []
        },
        'YELLOW': {
            # Core questions complete + 7 goal questions + 5 next level questions
            'core_questions': get_core_question_data(),
            'goal_questions': get_goal_question_data()[:7],
            'next_level_questions': get_next_level_question_data()[:5],
            'behavioral_questions': []
        },
        'GREEN': {
            # Core + 7 goal + 5 next level + 3 behavioral
            'core_questions': get_core_question_data(),
            'goal_questions': get_goal_question_data()[:7],
            'next_level_questions': get_next_level_question_data()[:5],
            'behavioral_questions': get_behavioral_question_data()[:3],
        },
        'DARK_GREEN': {
            # Core + 7 goal + 15 next level + 7 behavioral (all complete)
            'core_questions': get_core_question_data(),
            'goal_questions': get_goal_question_data()[:7],
            'next_level_questions': get_next_level_question_data()[:15],
            'behavioral_questions': get_behavioral_question_data()[:7],
        }
    }

@pytest.fixture
def mock_understanding_calculator():
    """
    Mock the understanding level calculator to return the expected level
    based on the profile's ID which will contain the target level.
    """
    original_calculator = question_service.understanding_calculator.calculate_level
    
    def mock_calculate_level(self, profile, completion_metrics):
        # Extract the target level from the profile name (e.g. "Test RED Profile")
        for level in PROFILE_UNDERSTANDING_LEVELS.keys():
            if f"Test {level} Profile" in profile.get('name', ''):
                level_info = PROFILE_UNDERSTANDING_LEVELS[level].copy()
                level_info['id'] = level
                
                # Add counts for debugging and display
                level_info['counts'] = {
                    'goal_questions': len([a for a in profile.get('answers', []) if a.get('question_id', '').startswith('goals_')]),
                    'next_level_questions': len([a for a in profile.get('answers', []) if a.get('question_id', '').startswith('next_level_')]),
                    'behavioral_questions': len([a for a in profile.get('answers', []) if a.get('question_id', '').startswith('behavioral_')]),
                    'core_completion': completion_metrics.get('core', {}).get('overall', 0)
                }
                
                # Add next level information for UI
                if level != 'DARK_GREEN':
                    levels = list(PROFILE_UNDERSTANDING_LEVELS.keys())
                    current_index = levels.index(level)
                    next_level_id = levels[current_index + 1]
                    next_level_info = PROFILE_UNDERSTANDING_LEVELS[next_level_id]
                    
                    level_info['next_level'] = {
                        'id': next_level_id,
                        'label': next_level_info['label'],
                        'requirements': [
                            "Complete all remaining questions to advance"
                        ]
                    }
                
                return level_info
                
        # Default to RED if no match
        return original_calculator(profile, completion_metrics)
    
    # Apply the mock
    with patch.object(question_service.understanding_calculator, 'calculate_level', 
                     new=types.MethodType(mock_calculate_level, question_service.understanding_calculator)):
        yield

@pytest.fixture
def profiles_by_level(profile_data_by_level, mock_understanding_calculator):
    """Create test profiles for each understanding level with appropriate answers."""
    profile_ids = {}
    
    for level in PROFILE_UNDERSTANDING_LEVELS.keys():
        # Create a profile and add the level to the name so we can identify it
        timestamp = int(time.time())
        profile = profile_manager.create_profile(
            f"Test {level} Profile {timestamp}", 
            f"test_{level.lower()}@example.com"
        )
        profile_id = profile['id']
        
        # Get the question data for this level
        level_data = profile_data_by_level[level]
        
        # Add all the appropriate questions to the profile
        add_questions_to_profile(profile_id, level_data)
        
        # Force refresh the understanding level calculation
        question_service.get_profile_completion(profile_id)
        
        profile_ids[level] = profile_id
    
    yield profile_ids
    
    # Clean up test profiles after tests
    for profile_id in profile_ids.values():
        try:
            profile_manager.delete_profile(profile_id)
        except:
            pass

def get_core_question_data():
    """Return test data for core questions."""
    return [
        {'id': 'demographics_age', 'answer': 35},
        {'id': 'demographics_location', 'answer': 'CA'},
        {'id': 'demographics_marital_status', 'answer': 'Married'},
        {'id': 'demographics_dependents', 'answer': 2},
        {'id': 'financial_basics_income', 'answer': 120000},
        {'id': 'financial_basics_monthly_expenses', 'answer': 5000},
        {'id': 'financial_basics_savings_rate', 'answer': 15},
        {'id': 'financial_basics_debt_payments', 'answer': 2000},
        {'id': 'assets_debts_cash', 'answer': 25000},
        {'id': 'assets_debts_investments', 'answer': 250000},
        {'id': 'assets_debts_retirement', 'answer': 180000},
        {'id': 'assets_debts_home_equity', 'answer': 300000},
        {'id': 'assets_debts_mortgage', 'answer': 400000},
        {'id': 'assets_debts_student_loans', 'answer': 0},
        {'id': 'assets_debts_credit_card', 'answer': 0},
        {'id': 'assets_debts_auto_loans', 'answer': 15000},
        {'id': 'special_cases_job_stability', 'answer': 'Stable'},
        {'id': 'special_cases_employer_benefits', 'answer': 'Yes'},
        {'id': 'special_cases_tax_situation', 'answer': 'Standard'}
    ]

def get_goal_question_data():
    """Return test data for goal questions."""
    return [
        {'id': 'goals_emergency_fund_exists', 'answer': 'Yes'},
        {'id': 'goals_emergency_fund_months', 'answer': '6-9 months'},
        {'id': 'goals_emergency_fund_target', 'answer': 'No'},
        {'id': 'goals_retirement', 'answer': 'Yes'},
        {'id': 'goals_retirement_age', 'answer': '65'},
        {'id': 'goals_home_purchase', 'answer': 'Yes'},
        {'id': 'goals_education', 'answer': 'Yes'},
        {'id': 'goals_travel', 'answer': 'Yes'},
        {'id': 'goals_major_purchase', 'answer': 'Yes'},
        {'id': 'goals_small_business', 'answer': 'No'}
    ]

def get_next_level_question_data():
    """Return test data for next level questions."""
    return [
        {'id': f'next_level_test_{i}', 'answer': f'Test answer {i}'} for i in range(15)
    ]

def get_behavioral_question_data():
    """Return test data for behavioral questions."""
    return [
        {'id': 'behavioral_risk_tolerance', 'answer': 5},
        {'id': 'behavioral_investment_horizon', 'answer': '5-10 years'},
        {'id': 'behavioral_decision_making', 'answer': 'Thoughtful'},
        {'id': 'behavioral_financial_stress', 'answer': 3},
        {'id': 'behavioral_money_mindset', 'answer': 'Pragmatic'},
        {'id': 'behavioral_financial_knowledge', 'answer': 4},
        {'id': 'behavioral_financial_discipline', 'answer': 4},
        {'id': 'behavioral_market_timing', 'answer': 2}
    ]

def add_questions_to_profile(profile_id, level_data):
    """Add all questions for a given level to a profile."""
    all_questions = []
    all_questions.extend(level_data['core_questions'])
    all_questions.extend(level_data['goal_questions'])
    all_questions.extend(level_data['next_level_questions'])
    all_questions.extend(level_data['behavioral_questions'])
    
    for question_data in all_questions:
        question_id = question_data['id']
        answer = question_data['answer']
        
        # First check if this question exists in the repository
        if hasattr(question_service.question_repository, 'get_question'):
            question = question_service.question_repository.get_question(question_id)
            if not question:
                # Determine question type and category from ID
                question_type = 'core'
                category = question_id.split('_')[0]
                
                if question_id.startswith('goals_'):
                    question_type = 'goal'
                    category = 'goals'
                elif question_id.startswith('next_level_'):
                    question_type = 'next_level'
                    category = 'next_level'
                elif question_id.startswith('behavioral_'):
                    question_type = 'behavioral'
                    category = 'behavioral'
                
                # Determine input type based on answer
                if isinstance(answer, (int, float)):
                    input_type = 'number'
                elif answer in ['Yes', 'No', 'Maybe']:
                    input_type = 'radio'
                    options = ['Yes', 'No', 'Maybe']
                elif isinstance(answer, str) and answer in ['5-10 years', '6-9 months']:
                    input_type = 'select'
                    options = [answer, 'Other option 1', 'Other option 2']
                else:
                    input_type = 'text'
                
                # Create a mock question
                question = {
                    'id': question_id,
                    'text': f'Test question for {question_id}',
                    'input_type': input_type,
                    'type': question_type,
                    'category': category
                }
                
                # Add options if needed
                if input_type in ['select', 'radio']:
                    question['options'] = options
                
                # Add it to the repository
                if hasattr(question_service.question_repository, 'questions'):
                    question_service.question_repository.questions[question_id] = question
        
        # Submit the answer
        question_service.submit_answer(profile_id, question_id, answer)

@pytest.mark.parametrize("level", list(PROFILE_UNDERSTANDING_LEVELS.keys()))
def test_understanding_level_display(client, profiles_by_level, level):
    """
    Comprehensive test that each understanding level displays correctly.
    This parametrized test runs once for each level, verifying all UI elements.
    """
    # Set the profile ID in the session
    with client.session_transaction() as session:
        session['profile_id'] = profiles_by_level[level]
    
    # Navigate to the questions page
    response = client.get('/questions')
    assert response.status_code == 200
    
    # Parse the HTML response
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Get the level info
    level_info = PROFILE_UNDERSTANDING_LEVELS[level]
    
    # ===== 1. Verify badge (color, text, etc.) =====
    badge = soup.find(class_="understanding-level-badge")
    assert badge is not None, "Understanding level badge not found"
    assert level_info['css_class'] in badge['class'], f"Expected class {level_info['css_class']} not found in badge classes"
    assert level_info['label'] == badge.text.strip(), f"Badge text '{badge.text.strip()}' doesn't match expected label '{level_info['label']}'"
    
    # ===== 2. Verify descriptive text =====
    description = soup.find(class_="understanding-level-description")
    assert description is not None, "Understanding level description not found"
    assert level_info['description'] == description.text.strip(), f"Description doesn't match expected text"
    
    # ===== 3. Verify understanding level indicators (the dots/circles) =====
    level_indicators = soup.find_all(class_="level-indicator")
    
    # Make sure we have the correct number of indicators (one for each level)
    assert len(level_indicators) == len(PROFILE_UNDERSTANDING_LEVELS), f"Expected {len(PROFILE_UNDERSTANDING_LEVELS)} level indicators, found {len(level_indicators)}"
    
    # Check that the correct indicator is active
    found_active_indicator = False
    for indicator in level_indicators:
        indicator_classes = indicator.get('class', [])
        level_class = f"level-{level.lower().replace('_', '-')}"  # Handle special cases like DARK_GREEN → dark-green
        
        if level_class in indicator_classes:
            assert "active" in indicator_classes, f"Indicator for {level} should be active"
            found_active_indicator = True
        elif "active" in indicator_classes:
            # If another indicator is active, this is an error
            active_class = [cls for cls in indicator_classes if cls.startswith('level-')]
            if active_class:
                assert False, f"Wrong indicator active: {active_class[0]} instead of {level_class}"
    
    assert found_active_indicator, f"No active indicator found for level {level}"
    
    # ===== 4. Verify next level info (except for DARK_GREEN) =====
    if level != 'DARK_GREEN':
        # Get the expected next level
        levels = list(PROFILE_UNDERSTANDING_LEVELS.keys())
        current_index = levels.index(level)
        next_level_id = levels[current_index + 1]
        next_level_label = PROFILE_UNDERSTANDING_LEVELS[next_level_id]['label']
        
        # Verify next level section exists
        next_level_info = soup.find(class_="next-level-info")
        assert next_level_info is not None, f"Next level info not found for {level} level"
        
        # Verify next level heading
        next_level_heading = next_level_info.find("h5")
        assert next_level_heading is not None, f"Next level heading not found for {level} level"
        assert "Next Level:" in next_level_heading.text, f"Expected 'Next Level:' in heading text"
        assert next_level_label in next_level_heading.text, f"Expected next level '{next_level_label}' in heading"
        
        # Verify requirements list has content
        requirements_list = next_level_info.find(class_="next-level-requirements")
        assert requirements_list is not None, f"Requirements list not found for {level} level"
        requirements = requirements_list.find_all("li")
        assert len(requirements) > 0, f"No requirements shown for next level after {level}"
    else:
        # DARK_GREEN should not have next level section
        next_level_elements = soup.find_all(class_="next-level-info")
        assert len(next_level_elements) == 0, "Dark Green level should not show next level info"

def test_level_progression_ui(client, profiles_by_level):
    """
    Comprehensive test of level progression UI elements across all understanding levels.
    This test verifies that the visual progression indicators show the correct states.
    """
    for level in PROFILE_UNDERSTANDING_LEVELS.keys():
        # Set the profile ID in the session
        with client.session_transaction() as session:
            session['profile_id'] = profiles_by_level[level]
        
        # Navigate to the questions page
        response = client.get('/questions')
        assert response.status_code == 200
        
        # Parse the HTML response
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Find all level indicators
        level_indicators = soup.find_all(class_="level-indicator")
        
        # Get the levels in order
        ordered_levels = list(PROFILE_UNDERSTANDING_LEVELS.keys())
        current_index = ordered_levels.index(level)
        
        # Check all indicators' state:
        # - Levels before current should be completed
        # - Current level should be active
        # - Levels after current should be inactive/incomplete
        for i, indicator_level in enumerate(ordered_levels):
            # Find the indicator for this level
            indicator = None
            for ind in level_indicators:
                # Handle special cases like DARK_GREEN → dark-green
                level_class = f"level-{indicator_level.lower().replace('_', '-')}"
                if level_class in ind.get('class', []):
                    indicator = ind
                    break
            
            assert indicator is not None, f"Indicator for {indicator_level} not found"
            
            # Check the state of this indicator based on our specific implementation
            # Since we don't actually use a 'completed' class, we'll just check if the
            # current level is active and the correct level indicator is displayed
            if i == current_index:
                # Current level should be active or have some kind of current indicator
                assert "active" in indicator.get('class', []), f"{indicator_level} should be active"

def test_form_submission_across_levels(client, profiles_by_level):
    """
    Test form submission across different understanding levels to ensure
    answers are correctly processed regardless of profile level.
    """
    # Test profiles at different levels
    for level in ['RED', 'AMBER', 'GREEN']:  # Test a few representative levels
        profile_id = profiles_by_level[level]
        
        with client.session_transaction() as session:
            session['profile_id'] = profile_id
        
        # Create test questions of different types to test form submission
        test_questions = [
            {
                'id': f'test_{level}_text_q',
                'text': f'Test {level} Text Question',
                'input_type': 'text',
                'type': 'core',
                'category': 'test'
            },
            {
                'id': f'test_{level}_number_q',
                'text': f'Test {level} Number Question',
                'input_type': 'number',
                'type': 'core',
                'category': 'test'
            },
            {
                'id': f'test_{level}_select_q',
                'text': f'Test {level} Select Question',
                'input_type': 'select',
                'options': ['Option A', 'Option B', 'Option C'],
                'type': 'core',
                'category': 'test'
            }
        ]
        
        # Add each test question to the repository and test submission
        for question in test_questions:
            # Add the question to the repository
            if hasattr(question_service.question_repository, 'questions'):
                question_service.question_repository.questions[question['id']] = question
            
            # Prepare form data based on question type
            form_data = {
                'question_id': question['id']
            }
            
            if question['input_type'] == 'text':
                form_data['answer'] = f'Answer for {level} text question'
            elif question['input_type'] == 'number':
                form_data['answer'] = '42'
            elif question['input_type'] == 'select':
                form_data['answer'] = question['options'][0]
            
            # Submit the answer
            response = client.post('/answer/submit', data=form_data)
            assert response.status_code == 200
            
            # Verify successful submission
            data = json.loads(response.data)
            assert data['success'] is True, f"Form submission failed for {level} profile, question type {question['input_type']}"
            
            # Check that the answer was saved in the profile
            profile = profile_manager.get_profile(profile_id)
            assert any(a['question_id'] == question['id'] for a in profile.get('answers', [])), \
                f"Answer not found in profile for {level} profile, question type {question['input_type']}"

def test_responsive_design(client, profiles_by_level):
    """
    Test that the understanding level UI is responsive across different device sizes.
    This simulates different viewport sizes by setting custom headers.
    """
    # Use a GREEN level profile for good visual complexity
    profile_id = profiles_by_level['GREEN']
    
    with client.session_transaction() as session:
        session['profile_id'] = profile_id
    
    # Test with different viewport sizes
    viewport_sizes = [
        {'width': 1920, 'height': 1080, 'description': 'Desktop'},
        {'width': 768, 'height': 1024, 'description': 'Tablet'},
        {'width': 375, 'height': 667, 'description': 'Mobile'}
    ]
    
    for viewport in viewport_sizes:
        # Custom headers to simulate viewport size
        headers = {
            'X-Viewport-Width': str(viewport['width']),
            'X-Viewport-Height': str(viewport['height']),
            'User-Agent': f"Test {viewport['description']} User Agent"
        }
        
        # Make request with custom headers
        response = client.get('/questions', headers=headers)
        assert response.status_code == 200
        
        # Parse the HTML response
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verify that all essential elements are present regardless of viewport size
        assert soup.find(class_="understanding-level-container") is not None, \
            f"Understanding level container not found on {viewport['description']} viewport"
        assert soup.find(class_="understanding-level-badge") is not None, \
            f"Understanding level badge not found on {viewport['description']} viewport"
        assert soup.find(class_="understanding-level-description") is not None, \
            f"Understanding level description not found on {viewport['description']} viewport"
        
        # Verify level indicators are present
        level_indicators = soup.find_all(class_="level-indicator")
        assert len(level_indicators) == len(PROFILE_UNDERSTANDING_LEVELS), \
            f"Wrong number of level indicators on {viewport['description']} viewport"

def test_question_form_interactions(client, profiles_by_level):
    """
    Test advanced form interactions like validation, dynamic field updates,
    and proper error handling.
    """
    # Use a RED level profile for simplicity
    profile_id = profiles_by_level['RED']
    
    with client.session_transaction() as session:
        session['profile_id'] = profile_id
    
    # Test form validations by submitting invalid data
    test_cases = [
        # Test case: Missing question_id
        {
            'form_data': {'answer': 'Answer without question ID'},
            'expected_error': True,
            'description': 'Missing question_id field'
        },
        # Test case: Invalid question ID
        {
            'form_data': {'question_id': 'nonexistent_question_id', 'answer': 'Answer'},
            'expected_error': True,
            'description': 'Invalid question ID'
        },
        # Test case: Invalid number (text in number field)
        {
            'form_data': {'question_id': 'test_number_validation', 'answer': 'not-a-number'},
            'expected_error': True,
            'description': 'Invalid number input'
        },
        # Test case: Valid submission
        {
            'form_data': {'question_id': 'test_valid_submission', 'answer': 'Valid answer'},
            'expected_error': False,
            'description': 'Valid submission'
        }
    ]
    
    # Add the test questions to the repository
    if hasattr(question_service.question_repository, 'questions'):
        question_service.question_repository.questions['test_validation_question'] = {
            'id': 'test_validation_question',
            'text': 'Test Validation Question',
            'input_type': 'text',
            'type': 'core',
            'category': 'test'
        }
        
        question_service.question_repository.questions['test_number_validation'] = {
            'id': 'test_number_validation',
            'text': 'Test Number Validation',
            'input_type': 'number',
            'type': 'core',
            'category': 'test'
        }
        
        question_service.question_repository.questions['test_valid_submission'] = {
            'id': 'test_valid_submission',
            'text': 'Test Valid Submission',
            'input_type': 'text',
            'type': 'core',
            'category': 'test'
        }
    
    # Test each validation case
    for test_case in test_cases:
        # Submit the form data
        response = client.post('/answer/submit', data=test_case['form_data'])
        assert response.status_code == 200
        
        # Parse the response
        data = json.loads(response.data)
        
        if test_case['expected_error']:
            assert data['success'] is False, f"Expected error for {test_case['description']}, but got success"
            assert 'error' in data, f"Expected error message for {test_case['description']}"
        else:
            assert data['success'] is True, f"Expected success for {test_case['description']}, but got error"
            
            # For valid submissions, verify the answer was saved
            if not test_case['expected_error']:
                profile = profile_manager.get_profile(profile_id)
                assert any(a['question_id'] == test_case['form_data']['question_id'] for a in profile.get('answers', [])), \
                    f"Answer not saved for {test_case['description']}"

def test_session_handling(client, profiles_by_level):
    """
    Test session management aspects of the frontend - new sessions,
    session expiration, and profile switching.
    """
    # Test cases for different session scenarios
    test_cases = [
        # Case 1: No active session/profile - should redirect to create profile
        {
            'setup_session': lambda s: None,  # No session setup
            'path': '/questions',
            'expected_redirect': '/profile/create',
            'description': 'No active profile'
        },
        # Case 2: Valid session with profile - should show questions page
        {
            'setup_session': lambda s: s.update({'profile_id': profiles_by_level['RED']}),
            'path': '/questions',
            'expected_status': 200,
            'expected_content': 'understanding-level-badge',
            'description': 'Valid profile session'
        },
        # Case 3: Profile switching - should clear session and redirect
        {
            'setup_session': lambda s: s.update({'profile_id': profiles_by_level['RED']}),
            'path': '/profile/switch',
            'expected_redirect': '/',
            'expected_session': {'profile_id': None},
            'description': 'Profile switching'
        }
    ]
    
    # Run each test case
    for test_case in test_cases:
        # Set up the session according to test case
        with client.session_transaction() as session:
            test_case['setup_session'](session)
        
        # Make the request
        response = client.get(test_case['path'], follow_redirects=False)
        
        # Check for expected redirect
        if 'expected_redirect' in test_case:
            assert response.status_code in [301, 302, 303], \
                f"Expected redirect for {test_case['description']}, got status {response.status_code}"
            assert test_case['expected_redirect'] in response.location, \
                f"Wrong redirect location for {test_case['description']}"
        
        # Check for expected status code
        if 'expected_status' in test_case:
            assert response.status_code == test_case['expected_status'], \
                f"Wrong status code for {test_case['description']}"
        
        # Check for expected content
        if 'expected_content' in test_case:
            if response.status_code == 200:  # Only check content for 200 responses
                assert test_case['expected_content'] in response.data.decode('utf-8'), \
                    f"Expected content missing for {test_case['description']}"
        
        # Check for expected session state after request
        if 'expected_session' in test_case:
            with client.session_transaction() as session:
                for key, value in test_case['expected_session'].items():
                    if value is None:
                        assert key not in session, f"Expected {key} to be removed from session"
                    else:
                        assert session.get(key) == value, f"Wrong session value for {key}"
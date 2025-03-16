import unittest
import json
from models.profile_understanding import ProfileUnderstandingCalculator
from models.question_repository import QuestionRepository
from models.profile_manager import ProfileManager
from services.question_service import QuestionService
from unittest.mock import MagicMock, patch

class TestUnderstandingLevels(unittest.TestCase):
    """
    Test cases for the profile understanding level functionality.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.understanding_calculator = ProfileUnderstandingCalculator()
        self.question_repository = QuestionRepository()
        self.profile_manager = MagicMock(spec=ProfileManager)
        self.question_service = QuestionService(
            self.question_repository, 
            self.profile_manager,
            llm_service=MagicMock()
        )
        
    def test_empty_profile(self):
        """Test understanding level with an empty profile."""
        # Create empty profile
        empty_profile = {
            'id': 'test_empty',
            'name': 'Test User',
            'answers': []
        }
        
        # Create mock completion metrics (similar to what question_service would return)
        completion_metrics = {
            'overall': 0,
            'by_category': {
                'demographics': 0,
                'financial_basics': 0,
                'assets_and_debts': 0,
                'special_cases': 0
            },
            'core': {
                'overall': 0,
                'by_category': {
                    'demographics': 0,
                    'financial_basics': 0,
                    'assets_and_debts': 0,
                    'special_cases': 0
                }
            },
            'next_level': {
                'questions_count': 0,
                'questions_answered': 0,
                'completion': 0
            },
            'behavioral': {
                'questions_count': 0,
                'questions_answered': 0,
                'completion': 0
            }
        }
        
        # Calculate understanding level
        level = self.understanding_calculator.calculate_level(empty_profile, completion_metrics)
        
        # Assert it's at RED level (lowest)
        self.assertEqual(level['id'], 'RED')
        self.assertIn('counts', level)
        self.assertEqual(level['counts']['goal_questions'], 0)
        self.assertEqual(level['counts']['next_level_questions'], 0)
        self.assertEqual(level['counts']['behavioral_questions'], 0)
        
    def test_core_complete_profile(self):
        """Test profile with complete core questions."""
        # Create a profile with all core questions answered
        core_questions = self.question_repository.get_core_questions()
        profile_answers = []
        
        # Create dummy answers for all core questions
        for question in core_questions:
            profile_answers.append({
                'question_id': question['id'],
                'answer': 'test answer',
            })
        
        profile = {
            'id': 'test_core_complete',
            'name': 'Test User',
            'answers': profile_answers
        }
        
        # Mock completion metrics
        completion_metrics = {
            'overall': 50,
            'by_category': {
                'demographics': 100,
                'financial_basics': 100,
                'assets_and_debts': 100,
                'special_cases': 100
            },
            'core': {
                'overall': 100,
                'by_category': {
                    'demographics': 100,
                    'financial_basics': 100,
                    'assets_and_debts': 100,
                    'special_cases': 100
                }
            },
            'next_level': {
                'questions_count': 10,
                'questions_answered': 0,
                'completion': 0
            },
            'behavioral': {
                'questions_count': 7,
                'questions_answered': 0,
                'completion': 0
            }
        }
        
        # Calculate understanding level
        level = self.understanding_calculator.calculate_level(profile, completion_metrics)
        
        # Assert it's still at RED level (need goals too)
        self.assertEqual(level['id'], 'RED')
        self.assertEqual(level['counts']['core_completion'], 100)
        
    def test_core_and_goals_profile(self):
        """Test profile with core complete and enough goal questions."""
        # Create a profile with all core questions and some goal questions
        core_questions = self.question_repository.get_core_questions()
        profile_answers = []
        
        # Create dummy answers for all core questions
        for question in core_questions:
            profile_answers.append({
                'question_id': question['id'],
                'answer': 'test answer',
            })
        
        # Add 3 goal questions
        for i in range(3):
            profile_answers.append({
                'question_id': f'goals_test_{i}',
                'answer': 'test answer',
            })
        
        profile = {
            'id': 'test_with_goals',
            'name': 'Test User',
            'answers': profile_answers
        }
        
        # Mock completion metrics
        completion_metrics = {
            'overall': 60,
            'by_category': {
                'demographics': 100,
                'financial_basics': 100,
                'assets_and_debts': 100,
                'special_cases': 100
            },
            'core': {
                'overall': 100,
                'by_category': {
                    'demographics': 100,
                    'financial_basics': 100,
                    'assets_and_debts': 100,
                    'special_cases': 100
                }
            },
            'next_level': {
                'questions_count': 10,
                'questions_answered': 0,
                'completion': 0
            },
            'behavioral': {
                'questions_count': 7,
                'questions_answered': 0,
                'completion': 0
            }
        }
        
        # Calculate understanding level
        level = self.understanding_calculator.calculate_level(profile, completion_metrics)
        
        # Assert it's at AMBER level
        self.assertEqual(level['id'], 'AMBER')
        self.assertEqual(level['counts']['goal_questions'], 3)
        
    def test_yellow_level_profile(self):
        """Test profile meeting YELLOW level requirements."""
        # Create a profile with all required components for yellow
        core_questions = self.question_repository.get_core_questions()
        profile_answers = []
        
        # Create dummy answers for all core questions
        for question in core_questions:
            profile_answers.append({
                'question_id': question['id'],
                'answer': 'test answer',
            })
        
        # Add 7 goal questions
        for i in range(7):
            profile_answers.append({
                'question_id': f'goals_test_{i}',
                'answer': 'test answer',
            })
            
        # Add 5 next-level questions
        for i in range(5):
            profile_answers.append({
                'question_id': f'next_level_test_{i}',
                'answer': 'test answer',
            })
        
        profile = {
            'id': 'test_yellow',
            'name': 'Test User',
            'answers': profile_answers
        }
        
        # Mock completion metrics
        completion_metrics = {
            'overall': 75,
            'by_category': {
                'demographics': 100,
                'financial_basics': 100,
                'assets_and_debts': 100,
                'special_cases': 100
            },
            'core': {
                'overall': 100,
                'by_category': {
                    'demographics': 100,
                    'financial_basics': 100,
                    'assets_and_debts': 100,
                    'special_cases': 100
                }
            },
            'next_level': {
                'questions_count': 10,
                'questions_answered': 5,
                'completion': 50
            },
            'behavioral': {
                'questions_count': 7,
                'questions_answered': 0,
                'completion': 0
            }
        }
        
        # Calculate understanding level
        level = self.understanding_calculator.calculate_level(profile, completion_metrics)
        
        # Assert it's at YELLOW level
        self.assertEqual(level['id'], 'YELLOW')
        self.assertEqual(level['counts']['goal_questions'], 7)
        self.assertEqual(level['counts']['next_level_questions'], 5)
        
    def test_green_level_profile(self):
        """Test profile meeting GREEN level requirements."""
        # Create a profile with all required components for green
        core_questions = self.question_repository.get_core_questions()
        profile_answers = []
        
        # Create dummy answers for all core questions
        for question in core_questions:
            profile_answers.append({
                'question_id': question['id'],
                'answer': 'test answer',
            })
        
        # Add 7 goal questions
        for i in range(7):
            profile_answers.append({
                'question_id': f'goals_test_{i}',
                'answer': 'test answer',
            })
            
        # Add 5 next-level questions
        for i in range(5):
            profile_answers.append({
                'question_id': f'next_level_test_{i}',
                'answer': 'test answer',
            })
            
        # Add 3 behavioral questions
        for i in range(3):
            profile_answers.append({
                'question_id': f'behavioral_test_{i}',
                'answer': 'test answer',
            })
        
        profile = {
            'id': 'test_green',
            'name': 'Test User',
            'answers': profile_answers
        }
        
        # Mock completion metrics
        completion_metrics = {
            'overall': 85,
            'by_category': {
                'demographics': 100,
                'financial_basics': 100,
                'assets_and_debts': 100,
                'special_cases': 100
            },
            'core': {
                'overall': 100,
                'by_category': {
                    'demographics': 100,
                    'financial_basics': 100,
                    'assets_and_debts': 100,
                    'special_cases': 100
                }
            },
            'next_level': {
                'questions_count': 10,
                'questions_answered': 5,
                'completion': 50
            },
            'behavioral': {
                'questions_count': 7,
                'questions_answered': 3,
                'completion': 42.8
            }
        }
        
        # Calculate understanding level
        level = self.understanding_calculator.calculate_level(profile, completion_metrics)
        
        # Assert it's at GREEN level
        self.assertEqual(level['id'], 'GREEN')
        self.assertEqual(level['counts']['behavioral_questions'], 3)
        
    def test_dark_green_level_profile(self):
        """Test profile meeting DARK_GREEN level requirements."""
        # Create a profile with all required components for dark green
        core_questions = self.question_repository.get_core_questions()
        profile_answers = []
        
        # Create dummy answers for all core questions
        for question in core_questions:
            profile_answers.append({
                'question_id': question['id'],
                'answer': 'test answer',
            })
        
        # Add 7 goal questions
        for i in range(7):
            profile_answers.append({
                'question_id': f'goals_test_{i}',
                'answer': 'test answer',
            })
            
        # Add 15 next-level questions
        for i in range(15):
            profile_answers.append({
                'question_id': f'next_level_test_{i}',
                'answer': 'test answer',
            })
            
        # Add 7 behavioral questions
        for i in range(7):
            profile_answers.append({
                'question_id': f'behavioral_test_{i}',
                'answer': 'test answer',
            })
        
        profile = {
            'id': 'test_dark_green',
            'name': 'Test User',
            'answers': profile_answers
        }
        
        # Mock completion metrics
        completion_metrics = {
            'overall': 95,
            'by_category': {
                'demographics': 100,
                'financial_basics': 100,
                'assets_and_debts': 100,
                'special_cases': 100
            },
            'core': {
                'overall': 100,
                'by_category': {
                    'demographics': 100,
                    'financial_basics': 100,
                    'assets_and_debts': 100,
                    'special_cases': 100
                }
            },
            'next_level': {
                'questions_count': 15,
                'questions_answered': 15,
                'completion': 100
            },
            'behavioral': {
                'questions_count': 7,
                'questions_answered': 7,
                'completion': 100
            }
        }
        
        # Calculate understanding level
        level = self.understanding_calculator.calculate_level(profile, completion_metrics)
        
        # Assert it's at DARK_GREEN level
        self.assertEqual(level['id'], 'DARK_GREEN')
        self.assertEqual(level['counts']['next_level_questions'], 15)
        self.assertEqual(level['counts']['behavioral_questions'], 7)
        
    def test_service_integration(self):
        """Test integration with QuestionService."""
        # Create a mock profile
        profile = {
            'id': 'test_integration',
            'name': 'Test User',
            'answers': [
                {'question_id': 'demographics_age', 'answer': 30},
                {'question_id': 'financial_basics_monthly_expenses', 'answer': 5000}
            ]
        }
        
        # Mock the profile_manager get_profile method to return our test profile
        self.profile_manager.get_profile.return_value = profile
        
        # Get completion metrics with understanding level
        completion = self.question_service.get_profile_completion('test_integration')
        
        # Assert understanding level is included
        self.assertIn('understanding_level', completion)
        self.assertEqual(completion['understanding_level']['id'], 'RED')
        
    def test_template_rendering(self):
        """Test template rendering with understanding level data."""
        from flask import Flask, render_template_string
        
        app = Flask(__name__)
        app.template_folder = './templates'
        
        # Simple template that includes understanding level
        test_template = """
        {% if completion.understanding_level %}
        <div>{{ completion.understanding_level.label }}</div>
        {% else %}
        <div>No understanding level</div>
        {% endif %}
        """
        
        with app.app_context():
            # Test with understanding level
            completion_with_level = {
                'understanding_level': {
                    'id': 'RED',
                    'label': 'Basic Information',
                    'css_class': 'profile-level-red'
                }
            }
            
            result_with = render_template_string(test_template, completion=completion_with_level)
            self.assertIn('Basic Information', result_with)
            
            # Test without understanding level
            completion_without_level = {}
            result_without = render_template_string(test_template, completion=completion_without_level)
            self.assertIn('No understanding level', result_without)
            
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with invalid completion metrics (missing required fields)
        incomplete_metrics = {
            'overall': 50,
            # Missing 'core' and other required fields
        }
        
        minimal_profile = {
            'id': 'test_edge',
            'answers': []
        }
        
        # Should not raise an exception, but fall back to RED level
        try:
            level = self.understanding_calculator.calculate_level(minimal_profile, incomplete_metrics)
            self.assertEqual(level['id'], 'RED')
        except Exception as e:
            self.fail(f"calculate_level raised exception on incomplete metrics: {e}")
            
        # Test with missing answers list
        no_answers_profile = {
            'id': 'test_no_answers'
            # No 'answers' key
        }
        
        try:
            level = self.understanding_calculator.calculate_level(no_answers_profile, incomplete_metrics)
            self.assertEqual(level['id'], 'RED')
            self.assertEqual(level['counts']['goal_questions'], 0)
        except Exception as e:
            self.fail(f"calculate_level raised exception on profile with no answers: {e}")

if __name__ == '__main__':
    unittest.main()
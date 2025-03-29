import unittest
from models.question_repository import QuestionRepository
from services.question_service import QuestionService
from unittest.mock import MagicMock

class TestQuestionFlow(unittest.TestCase):
    """
    Test the question flow logic to ensure it handles transitions properly.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.question_repository = QuestionRepository()
        self.profile_manager = MagicMock()
        self.llm_service = MagicMock()
        self.question_service = QuestionService(
            self.question_repository, 
            self.profile_manager,
            llm_service=self.llm_service
        )
    
    def test_empty_profile_flow(self):
        """Test question flow with an empty profile."""
        # Create an empty profile
        empty_profile = {
            'id': 'test_empty_flow',
            'answers': []
        }
        
        # Setup mock to return this profile
        self.profile_manager.get_profile.return_value = empty_profile
        
        # Get next question
        next_question, profile = self.question_service.get_next_question('test_empty_flow')
        
        # Assert it's a core question
        self.assertIsNotNone(next_question)
        self.assertEqual(next_question['type'], 'core')
    
    def test_core_to_goals_transition(self):
        """Test transition from core to goal questions."""
        # Create a profile with core questions completed (80%)
        core_questions = self.question_repository.get_core_questions()
        required_core = [q for q in core_questions if q.get('required', True)]
        
        # Calculate 80% of core questions
        required_count = len(required_core)
        to_answer_count = int(required_count * 0.8)
        
        # Create profile with 80% core questions answered
        profile_answers = []
        for i in range(to_answer_count):
            profile_answers.append({
                'question_id': required_core[i]['id'],
                'answer': 'test answer'
            })
        
        profile = {
            'id': 'test_core_to_goals',
            'answers': profile_answers
        }
        
        # Setup mock
        self.profile_manager.get_profile.return_value = profile
        
        # Stub the goal question repository function
        original_get_questions_by_type = self.question_repository.get_questions_by_type
        self.question_repository.get_questions_by_type = MagicMock()
        
        def mock_get_questions_by_type(question_type):
            if question_type == 'goal':
                return [{'id': 'goals_test', 'type': 'goal', 'text': 'Test goal question', 'order': 1}]
            return original_get_questions_by_type(question_type)
            
        self.question_repository.get_questions_by_type.side_effect = mock_get_questions_by_type
        
        # Get next question - should be a core question still (missing 20%)
        next_question, profile = self.question_service.get_next_question('test_core_to_goals')
        
        # Should return a core question since we haven't reached 100% yet
        self.assertEqual(next_question['type'], 'core')
        
        # Now add the rest of core questions to reach 100%
        for i in range(to_answer_count, required_count):
            profile_answers.append({
                'question_id': required_core[i]['id'],
                'answer': 'test answer'
            })
            
        # Mock is_ready_for_goals to return True
        original_is_ready = self.question_service._is_ready_for_goals
        self.question_service._is_ready_for_goals = MagicMock(return_value=True)
        
        # Get next question - should be a goal question now
        next_question, profile = self.question_service.get_next_question('test_core_to_goals')
        
        # Reset mocks
        self.question_service._is_ready_for_goals = original_is_ready
        self.question_repository.get_questions_by_type = original_get_questions_by_type
        
        # Verify we're getting a goal question
        self.assertEqual(next_question['type'], 'goal')
    
    def test_goals_to_next_level_transition(self):
        """Test transition from goals to next-level questions."""
        # Create a profile with all core and minimum goal questions
        profile_answers = []
        
        # Add all core questions as answered
        core_questions = self.question_repository.get_core_questions()
        for question in core_questions:
            profile_answers.append({
                'question_id': question['id'],
                'answer': 'test answer'
            })
        
        # Add minimum required goal questions (3) - including emergency fund questions
        profile_answers.append({
            'question_id': 'goals_emergency_fund_exists',
            'answer': 'Yes'
        })
        profile_answers.append({
            'question_id': 'goals_emergency_fund_months',
            'answer': '6-9 months'
        })
        profile_answers.append({
            'question_id': 'goals_emergency_fund_target',
            'answer': 'No'
        })
        
        profile = {
            'id': 'test_goals_to_next_level',
            'answers': profile_answers
        }
        
        # Setup mocks
        self.profile_manager.get_profile.return_value = profile
        
        # Mock the necessary methods to ensure we bypass goal questions
        self.question_service._is_ready_for_goals = MagicMock(return_value=False)
        self.question_service._has_pending_goal_questions = MagicMock(return_value=False)
        self.question_service._is_ready_for_next_level = MagicMock(return_value=True)
        self.question_service._get_next_level_question = MagicMock(return_value={
            'id': 'next_level_test',
            'type': 'next_level',
            'text': 'Test next-level question'
        })
        
        # Get next question
        next_question, profile = self.question_service.get_next_question('test_goals_to_next_level')
        
        # Verify we get a next-level question
        self.assertEqual(next_question['type'], 'next_level')
    
    def test_get_behavioral_question(self):
        """Test that _get_behavioral_question works correctly."""
        # Create a test profile
        profile = {
            'id': 'test_behavioral_flow',
            'answers': [
                # Include some already answered behavioral questions
                {'question_id': 'behavioral_test_1', 'answer': 'test'}
            ]
        }
        
        # Create a mock behavioral question list
        mock_behavioral_questions = [
            {
                'id': 'behavioral_test_1',
                'type': 'behavioral',
                'order': 1
            },
            {
                'id': 'behavioral_test_2',
                'type': 'behavioral',
                'order': 2
            }
        ]
        
        # Mock the question repository
        original_get_questions_by_type = self.question_repository.get_questions_by_type
        self.question_repository.get_questions_by_type = MagicMock(return_value=mock_behavioral_questions)
        
        # Call the get_behavioral_question method directly
        result = self.question_service._get_behavioral_question(profile)
        
        # Restore the original method
        self.question_repository.get_questions_by_type = original_get_questions_by_type
        
        # Verify we get the second question (first unanswered one)
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 'behavioral_test_2')
    
    def test_behavioral_question_limit(self):
        """Test that we respect the maximum limit of behavioral questions."""
        # Create a profile with all requirements and maximum behavioral questions
        profile_answers = []
        
        # Add all core questions
        core_questions = self.question_repository.get_core_questions()
        for question in core_questions:
            profile_answers.append({
                'question_id': question['id'],
                'answer': 'test answer'
            })
        
        # Add goal questions
        for i in range(7):
            profile_answers.append({
                'question_id': f'goals_test_{i}',
                'answer': 'test answer'
            })
        
        # Add next-level questions
        for i in range(5):
            profile_answers.append({
                'question_id': f'next_level_test_{i}',
                'answer': 'test answer'
            })
        
        # Add maximum behavioral questions (7)
        for i in range(7):
            profile_answers.append({
                'question_id': f'behavioral_test_{i}',
                'answer': 'test answer'
            })
        
        profile = {
            'id': 'test_behavioral_limit',
            'answers': profile_answers
        }
        
        # Setup mocks
        self.profile_manager.get_profile.return_value = profile
        
        # Get available behavioral questions
        behavioral_questions = self.question_repository.get_questions_by_type('behavioral')
        
        # Create a profile with non-existing behavioral questions
        self.question_service._is_ready_for_behavioral = MagicMock(return_value=True)
        
        # Call get_behavioral_question directly to test the limit check
        result = self.question_service._get_behavioral_question(profile)
        
        # Should return None as we've reached the limit of 7
        self.assertIsNone(result)
    
    def test_edge_case_handling(self):
        """Test that the question flow handles edge cases gracefully."""
        # 1. Test with a profile with no answers
        empty_profile = {
            'id': 'test_empty_edge',
            'answers': []
        }
        
        self.profile_manager.get_profile.return_value = empty_profile
        
        # Should return a core question without crashing
        next_question, _ = self.question_service.get_next_question('test_empty_edge')
        self.assertIsNotNone(next_question)
        self.assertEqual(next_question['type'], 'core')
        
        # 2. Test with a non-existent profile
        self.profile_manager.get_profile.return_value = None
        
        # Should handle gracefully without crashing
        next_question, profile = self.question_service.get_next_question('non_existent')
        self.assertIsNone(next_question)
        self.assertIsNone(profile)
        
        # 3. Test with a profile that's partway through each section
        partial_profile = {
            'id': 'test_partial',
            'answers': [
                # Some core questions
                {'question_id': 'demographics_age', 'answer': 30},
                # Some goal questions
                {'question_id': 'goals_test_1', 'answer': 'test'},
                # Some next-level questions
                {'question_id': 'next_level_test_1', 'answer': 'test'},
                # Some behavioral questions
                {'question_id': 'behavioral_test_1', 'answer': 'test'}
            ]
        }
        
        self.profile_manager.get_profile.return_value = partial_profile
        
        # Mock core questions check to represent incomplete core
        incomplete_core_questions = [q for q in self.question_repository.get_core_questions() 
                                   if q['id'] != 'demographics_age']
        self.question_repository.get_next_question = MagicMock(return_value=incomplete_core_questions[0])
        
        # Should prioritize core questions
        next_question, _ = self.question_service.get_next_question('test_partial')
        self.assertEqual(next_question['type'], 'core')

if __name__ == '__main__':
    unittest.main()
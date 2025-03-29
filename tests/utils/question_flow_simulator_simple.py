import json
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import the simplified question service
import services.question_service_simplified

# Monkey patch the import in the module
services.question_service_simplified.__name__ = 'services.question_service'
sys.modules['services.question_service'] = services.question_service_simplified

from models.question_repository import QuestionRepository
from services.question_service_simplified import QuestionService, QuestionLogger
from models.profile_understanding import ProfileUnderstandingCalculator
from models.database_profile_manager import DatabaseProfileManager
from services.llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('question_flow_simulator')

class QuestionFlowSimulator:
    """
    Simulates the question flow system without requiring the frontend.
    """
    
    def __init__(self, profile_id=None):
        """Initialize the simulator with optional profile ID."""
        self.question_repository = QuestionRepository()
        self.profile_manager = DatabaseProfileManager()
        self.llm_service = LLMService()
        self.question_service = QuestionService(
            self.question_repository,
            self.profile_manager,
            self.llm_service
        )
        self.understanding_calculator = ProfileUnderstandingCalculator()
        
        # Create a new profile if none provided
        if profile_id:
            self.profile_id = profile_id
        else:
            self.profile_id = self._create_test_profile()
        
        logger.info(f"Initialized simulator with profile ID: {self.profile_id}")
    
    def _create_test_profile(self):
        """Create a test profile for simulation."""
        name = 'Test Simulation Profile'
        email = 'test_simulation@example.com'
        
        # Create profile with required arguments
        profile_obj = self.profile_manager.create_profile(name, email)
        
        # Extract just the ID string from the returned profile
        if isinstance(profile_obj, dict) and 'id' in profile_obj:
            return profile_obj['id']
        else:
            return profile_obj
    
    def simulate_question_flow(self, num_questions=10, answer_strategy='basic'):
        """
        Simulate answering a series of questions and observe the flow.
        
        Args:
            num_questions: Number of questions to simulate (default: 10)
            answer_strategy: How to answer questions (basic, random, or custom)
        """
        logger.info(f"Starting question flow simulation for {num_questions} questions")
        print(f"\n{'='*80}\nQUESTION FLOW SIMULATION\n{'='*80}")
        print(f"Profile ID: {self.profile_id}")
        print(f"Number of questions: {num_questions}")
        print(f"Answer strategy: {answer_strategy}\n")
        
        # Track questions asked in this simulation
        questions_asked = []
        
        # Step through the questions
        for i in range(num_questions):
            print(f"\n{'='*60}\nQUESTION {i+1}\n{'='*60}")
            
            # Get the next question
            next_question, profile = self.question_service.get_next_question(self.profile_id)
            
            if not next_question:
                print("No more questions available!")
                break
            
            # Display question information
            self._display_question_info(next_question)
            questions_asked.append(next_question)
            
            # Generate an answer based on the strategy
            answer = self._generate_answer(next_question, answer_strategy)
            
            # Submit the answer
            self._submit_answer(next_question, answer)
            
            # Show current understanding level
            understanding_level = self.understanding_calculator.calculate_understanding_level(profile)
            print(f"\nCurrent understanding level: {understanding_level}")
            
            # If this is a dynamically generated question, note that
            if next_question.get('type') == 'next_level' and next_question.get('id', '').startswith('gen_'):
                print("(This was a dynamically generated question)")
        
        # Final summary
        print(f"\n{'='*80}\nSIMULATION SUMMARY\n{'='*80}")
        profile = self.profile_manager.get_profile(self.profile_id)
        final_understanding = self.understanding_calculator.calculate_understanding_level(profile)
        
        # Summarize questions by type
        question_types = {}
        for q in questions_asked:
            q_type = q.get('type', 'unknown')
            if q_type not in question_types:
                question_types[q_type] = 0
            question_types[q_type] += 1
        
        print(f"Total questions answered: {len(questions_asked)}")
        print(f"Final understanding level: {final_understanding}")
        print("\nQuestions by type:")
        for q_type, count in question_types.items():
            print(f"  - {q_type}: {count}")
        
        # Check for dynamically generated questions
        dynamic_count = sum(1 for q in questions_asked if q.get('id', '').startswith('gen_'))
        print(f"\nDynamically generated questions: {dynamic_count}")
        
        return questions_asked
    
    def _display_question_info(self, question):
        """Display information about a question."""
        print(f"ID: {question.get('id')}")
        print(f"Type: {question.get('type')}")
        print(f"Category: {question.get('category', 'N/A')}")
        print(f"Input type: {question.get('input_type', 'text')}")
        if question.get('relevance_score'):
            print(f"Relevance score: {question.get('relevance_score')}")
        print(f"\nQuestion: {question.get('text')}\n")
        
        # If it has options, display them
        if question.get('options'):
            print("Options:")
            for i, option in enumerate(question['options']):
                if isinstance(option, dict):
                    print(f"  {i+1}. {option.get('label', option.get('value', 'Unknown'))}")
                else:
                    print(f"  {i+1}. {option}")
            print()
    
    def _generate_answer(self, question, strategy):
        """Generate an answer for a question based on the strategy."""
        input_type = question.get('input_type', 'text')
        
        if strategy == 'basic':
            # Basic strategy uses simple defaults for each question type
            if input_type == 'text':
                return "This is a test answer"
            elif input_type == 'number':
                return 50000
            elif input_type == 'select':
                # Return the first option
                options = question.get('options', [])
                if options:
                    if isinstance(options[0], dict):
                        return options[0].get('value')
                    else:
                        return options[0]
                return "first_option"
            elif input_type == 'multiselect':
                # Return the first two options if available
                options = question.get('options', [])
                if len(options) >= 2:
                    if isinstance(options[0], dict):
                        return [options[0].get('value'), options[1].get('value')]
                    else:
                        return [options[0], options[1]]
                return ["option1", "option2"]
        elif strategy == 'random':
            # Implement random strategy here if needed
            return "Random answer not implemented"
        else:
            # Custom strategy - ask for input
            print("Please provide an answer for this question:")
            user_answer = input("> ")
            return user_answer
        
    def _submit_answer(self, question, answer):
        """Submit an answer to a question."""
        question_id = question.get('id')
        print(f"Submitting answer: {answer}")
        
        # Create the answer object
        answer_obj = {
            'question_id': question_id,
            'answer': answer,
            'text': question.get('text'),  # Include question text for context
            'timestamp': None  # Let the service fill this
        }
        
        # Submit the answer
        success = self.question_service.save_question_answer(self.profile_id, answer_obj)
        
        if success:
            print("Answer submitted successfully")
        else:
            print("Failed to submit answer")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulate the question flow system')
    parser.add_argument('--profile_id', help='Use an existing profile ID')
    parser.add_argument('--questions', type=int, default=10, help='Number of questions to simulate')
    parser.add_argument('--strategy', choices=['basic', 'random', 'custom'], default='basic',
                        help='Strategy for answering questions')
    
    args = parser.parse_args()
    
    simulator = QuestionFlowSimulator(profile_id=args.profile_id)
    simulator.simulate_question_flow(num_questions=args.questions, answer_strategy=args.strategy)
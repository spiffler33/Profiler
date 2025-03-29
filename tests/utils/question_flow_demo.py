import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('question_flow_demo')

class QuestionFlowDemo:
    """
    A simplified demonstration of the question flow system, using
    hardcoded questions without external dependencies.
    """
    
    def __init__(self):
        """Initialize with demo data."""
        # Create a simple in-memory profile
        self.profile = {
            'id': 'demo_profile',
            'name': 'Demo User',
            'answers': []
        }
        
        # Define some sample questions
        self.core_questions = [
            {
                'id': 'demographics_age',
                'type': 'core',
                'category': 'demographics',
                'text': 'What is your age?',
                'input_type': 'number'
            },
            {
                'id': 'demographics_income',
                'type': 'core',
                'category': 'demographics',
                'text': 'What is your annual income?',
                'input_type': 'number'
            },
            {
                'id': 'demographics_occupation',
                'type': 'core',
                'category': 'demographics', 
                'text': 'What is your occupation?',
                'input_type': 'text'
            },
            {
                'id': 'financial_basics_emergency_fund',
                'type': 'core',
                'category': 'financial_basics',
                'text': 'Do you have an emergency fund?',
                'input_type': 'select',
                'options': ['Yes', 'No']
            }
        ]
        
        self.goal_questions = [
            {
                'id': 'goals_emergency_fund',
                'type': 'goal',
                'category': 'emergency_fund',
                'text': 'How much would you like to save for an emergency fund?',
                'input_type': 'number'
            },
            {
                'id': 'goals_retirement',
                'type': 'goal',
                'category': 'retirement',
                'text': 'At what age would you like to retire?',
                'input_type': 'number'
            },
            {
                'id': 'goals_home_purchase',
                'type': 'goal',
                'category': 'home_purchase',
                'text': 'Are you planning to purchase a home in the future?',
                'input_type': 'select',
                'options': ['Yes', 'No', 'Already own a home']
            }
        ]
        
        self.next_level_questions = [
            {
                'id': 'next_level_investment_risk',
                'type': 'next_level',
                'category': 'investment_planning',
                'text': 'On a scale of 1-10, how comfortable are you with investment risk?',
                'input_type': 'number'
            },
            {
                'id': 'next_level_tax_planning',
                'type': 'next_level',
                'category': 'tax_planning',
                'text': 'Do you currently use any tax-advantaged investment accounts?',
                'input_type': 'select',
                'options': ['Yes', 'No', 'Not sure']
            }
        ]
        
        # Dynamic questions that would normally be generated by LLM
        self.dynamic_questions = [
            {
                'id': 'gen_question_tax_planning_1',
                'type': 'next_level',
                'category': 'tax_planning',
                'text': 'Based on your income of ₹800,000, which Section 80C investments would be most suitable for your tax bracket?',
                'input_type': 'select',
                'options': ['ELSS Mutual Funds', 'PPF', 'NSC', 'Tax-saving FDs'],
                'relevance_score': 85
            },
            {
                'id': 'gen_question_investment_planning_1',
                'type': 'next_level',
                'category': 'investment_planning',
                'text': 'How regularly are you investing through SIPs (Systematic Investment Plans), and what is your monthly SIP amount?',
                'input_type': 'text',
                'relevance_score': 78
            },
            {
                'id': 'gen_question_retirement_planning_1',
                'type': 'next_level',
                'category': 'retirement_planning',
                'text': 'How are you balancing your PPF contributions versus other debt instruments in your portfolio?',
                'input_type': 'text',
                'relevance_score': 82
            }
        ]
        
        logger.info("Demo initialized with sample questions")
    
    def run_demo(self, num_questions=8):
        """
        Run the question flow demonstration.
        
        Args:
            num_questions: Number of questions to demonstrate
        """
        print(f"\n{'='*80}\nQUESTION FLOW DEMONSTRATION\n{'='*80}")
        print("This demo shows the new question flow system's behavior, including:")
        print("1. Starting with core questions")
        print("2. Transitioning to goal questions after core questions")
        print("3. Moving to next-level questions")
        print("4. Introducing dynamically generated questions with relevance scores")
        print("5. Adapting the question flow based on profile understanding\n")
        
        # Process questions
        understanding_level = "RED"  # Start at RED level
        questions_asked = []
        
        for i in range(num_questions):
            print(f"\n{'='*60}\nQUESTION {i+1}\n{'='*60}")
            
            # Get the next question based on the current flow state
            if i < 4:
                # First 4 questions are core
                question = self.core_questions[i]
                print(f"Current understanding level: {understanding_level}")
                print("✓ Prioritizing core financial information")
            elif i < 6:
                # Next 2 are goal questions
                question = self.goal_questions[i-4]
                understanding_level = "YELLOW"  # Progress to YELLOW after core questions
                print(f"Current understanding level: {understanding_level}")
                print("✓ Basic profile complete, now exploring financial goals")
            else:
                # Last 2 are dynamic next-level questions
                idx = i - 6
                if idx < len(self.dynamic_questions):
                    question = self.dynamic_questions[idx]
                    understanding_level = "GREEN"  # Progress to GREEN after goals
                    print(f"Current understanding level: {understanding_level}")
                    print(f"✓ Dynamically generated question with relevance score: {question.get('relevance_score')}")
                    print("✓ Personalized to Indian financial context")
                else:
                    print("No more questions available!")
                    break
            
            # Display question
            self._display_question(question)
            questions_asked.append(question)
            
            # Simulate answering
            answer = self._simulate_answer(question)
            self._save_answer(question, answer)
            
        # Summary
        print(f"\n{'='*80}\nDEMONSTRATION SUMMARY\n{'='*80}")
        print(f"Final understanding level: {understanding_level}")
        
        # Count questions by type
        core_count = sum(1 for q in questions_asked if q.get('type') == 'core')
        goal_count = sum(1 for q in questions_asked if q.get('type') == 'goal')
        dynamic_count = sum(1 for q in questions_asked if q.get('id', '').startswith('gen_'))
        
        print(f"\nQuestion breakdown:")
        print(f"- Core questions: {core_count}")
        print(f"- Goal questions: {goal_count}")
        print(f"- Dynamic personalized questions: {dynamic_count}")
        
        if dynamic_count > 0:
            print("\nDynamic questions are generated using:")
            print("- LLM integration for personalized question creation")
            print("- Profile understanding analysis")
            print("- Knowledge gap detection")
            print("- Financial security foundation prioritization")
            print("- Goal probability integration")
        
        print("\nKey differences from legacy approach:")
        print("1. Dynamic question generation based on profile context")
        print("2. Adaptive questioning based on understanding level")
        print("3. Smart prioritization of financial security foundations")
        print("4. Integration of financial knowledge gap analysis")
        print("5. Enhanced educational content with calculations")
        print("6. Goal probability visualization integration")
        print("7. Indian financial context specialization")
    
    def _display_question(self, question):
        """Display a question with its metadata."""
        print(f"ID: {question.get('id')}")
        print(f"Type: {question.get('type')}")
        print(f"Category: {question.get('category')}")
        print(f"Input type: {question.get('input_type')}")
        
        if question.get('relevance_score'):
            print(f"Relevance score: {question.get('relevance_score')}")
            
        print(f"\nQuestion: {question.get('text')}")
        
        if question.get('options'):
            print("\nOptions:")
            for i, option in enumerate(question['options']):
                print(f"  {i+1}. {option}")
        
        print()
    
    def _simulate_answer(self, question):
        """Simulate answering a question."""
        input_type = question.get('input_type')
        
        if input_type == 'number':
            if 'age' in question.get('id'):
                return 35
            elif 'income' in question.get('id'):
                return 800000
            elif 'emergency' in question.get('id'):
                return 300000
            elif 'retire' in question.get('id'):
                return 60
            elif 'risk' in question.get('id'):
                return 7
            else:
                return 50000
        elif input_type == 'select':
            options = question.get('options', [])
            if options:
                return options[0]
            return "Yes"
        else:
            if 'occupation' in question.get('id'):
                return "Software Engineer"
            elif 'SIP' in question.get('text'):
                return "Monthly SIPs of ₹15,000"
            elif 'PPF' in question.get('text'):
                return "60% PPF, 40% other debt instruments"
            else:
                return "Sample text answer"
    
    def _save_answer(self, question, answer):
        """Save an answer to the profile."""
        self.profile['answers'].append({
            'question_id': question.get('id'),
            'answer': answer,
            'text': question.get('text'),
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"Answer: {answer}")
        print(f"✓ Answer saved to profile")

if __name__ == "__main__":
    # Run the demonstration
    demo = QuestionFlowDemo()
    demo.run_demo()
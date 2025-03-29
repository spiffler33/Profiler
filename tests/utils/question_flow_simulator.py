import json
import os
import sys
import logging
import random
import datetime
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from models.question_repository import QuestionRepository
from services.question_service import QuestionService, QuestionLogger
from models.profile_understanding import ProfileUnderstandingCalculator
from models.database_profile_manager import DatabaseProfileManager
from services.llm_service import LLMService
from models.financial_parameters import FinancialParameters
from services.financial_parameter_service import FinancialParameterService
# Removed ProfileAnswer import as it's not needed

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('question_flow_simulator')

class RealisticAnswerGenerator:
    """
    Generates realistic financial answers based on Indian context and question types.
    """
    
    def __init__(self):
        """Initialize the answer generator with reasonable financial ranges."""
        # Age ranges for demographics
        self.age_ranges = {
            'young_adult': (22, 35),
            'mid_career': (36, 50),
            'pre_retirement': (51, 65),
            'retirement': (66, 80)
        }
        
        # Income ranges (annual, in INR)
        self.income_ranges = {
            'entry_level': (300000, 800000),       # 3-8 lakhs
            'mid_level': (800001, 2000000),        # 8-20 lakhs
            'senior_level': (2000001, 5000000),    # 20-50 lakhs
            'executive': (5000001, 10000000)       # 50 lakhs - 1 crore
        }
        
        # Expense ranges (monthly, as percentage of income)
        self.expense_percentages = {
            'essential': (0.3, 0.5),      # 30-50% of income
            'discretionary': (0.1, 0.3),  # 10-30% of income
            'savings': (0.2, 0.4)         # 20-40% of income
        }
        
        # Asset values
        self.asset_ranges = {
            'cash': (50000, 500000),             # 50k - 5 lakhs
            'equity': (100000, 3000000),         # 1 lakh - 30 lakhs
            'fixed_income': (200000, 2000000),   # 2 lakhs - 20 lakhs
            'real_estate': (2000000, 10000000),  # 20 lakhs - 1 crore
            'gold': (50000, 1000000),            # 50k - 10 lakhs
            'epf': (100000, 1500000),            # 1 lakh - 15 lakhs
            'ppf': (100000, 1000000)             # 1 lakh - 10 lakhs
        }
        
        # Debt ranges
        self.debt_ranges = {
            'home_loan': (1000000, 8000000),       # 10 lakhs - 80 lakhs
            'car_loan': (300000, 1000000),         # 3 lakhs - 10 lakhs
            'personal_loan': (100000, 500000),     # 1 lakh - 5 lakhs
            'education_loan': (500000, 2000000),   # 5 lakhs - 20 lakhs
            'credit_card': (10000, 100000)         # 10k - 1 lakh
        }
        
        # Emergency fund ranges (in months)
        self.emergency_fund_months = [3, 6, 9, 12]
        
        # Goal timeframes (in years)
        self.goal_timeframes = {
            'short_term': (1, 3),
            'medium_term': (4, 7),
            'long_term': (8, 20)
        }
        
        # Risk tolerance options
        self.risk_profiles = ['Conservative', 'Moderate', 'Aggressive']
        
        # Education levels
        self.education_levels = ['High School', 'Bachelor\'s', 'Master\'s', 'PhD']
        
        # Marital status
        self.marital_statuses = ['Single', 'Married', 'Divorced', 'Widowed']
        
        # Children options
        self.children_options = [0, 1, 2, 3]
        
        # Yes/No probabilities
        self.yes_no_probabilities = {
            'has_emergency_fund': 0.7,
            'has_life_insurance': 0.6,
            'has_health_insurance': 0.8,
            'has_home_loan': 0.5,
            'has_car_loan': 0.3,
            'has_education_loan': 0.2,
            'has_personal_loan': 0.15,
            'has_credit_card_debt': 0.4,
            'interested_in_retirement': 0.9,
            'interested_in_education': 0.6,
            'interested_in_home_purchase': 0.7
        }
        
        # Current profile context (will be built during simulation)
        self.profile_context = {}
        
    def set_profile_context(self, profile):
        """
        Build up context from previously answered questions to maintain consistency.
        """
        self.profile_context = {}
        
        if not profile or 'answers' not in profile:
            return
            
        for answer_obj in profile['answers']:
            question_id = answer_obj.get('question_id')
            answer = answer_obj.get('answer')
            
            if question_id and answer is not None:
                self.profile_context[question_id] = answer
        
        # Derive implied context
        if 'demographics_age' in self.profile_context:
            age = self.profile_context['demographics_age']
            if isinstance(age, str):
                try:
                    age = int(age)
                except ValueError:
                    age = 35  # Default
            
            if age < 36:
                self.profile_context['age_group'] = 'young_adult'
            elif age < 51:
                self.profile_context['age_group'] = 'mid_career'
            elif age < 66:
                self.profile_context['age_group'] = 'pre_retirement'
            else:
                self.profile_context['age_group'] = 'retirement'
    
    def generate_answer(self, question: Dict[str, Any]) -> Any:
        """
        Generate a realistic answer based on the question type and current profile context.
        """
        question_id = question.get('id', '')
        question_type = question.get('type', '')
        input_type = question.get('input_type', 'text')
        category = question.get('category', '')
        
        # Check if we need consistent answers based on previous responses
        if self._should_use_consistent_answer(question_id):
            return self._generate_consistent_answer(question_id, question)
        
        # Handle different question categories
        if category == 'demographics':
            return self._generate_demographic_answer(question_id, input_type, question)
        elif category == 'financial_basics':
            return self._generate_financial_basic_answer(question_id, input_type, question)
        elif category == 'assets_and_debts':
            return self._generate_assets_debts_answer(question_id, input_type, question)
        elif question_type == 'goal':
            return self._generate_goal_answer(question_id, input_type, question)
        elif category == 'behavioral':
            return self._generate_behavioral_answer(question_id, input_type, question)
        
        # Default handling based on input type
        return self._generate_by_input_type(input_type, question)
    
    def _should_use_consistent_answer(self, question_id: str) -> bool:
        """
        Determine if we need to generate an answer consistent with previous answers.
        """
        # Questions that need consistency with previous answers
        consistency_checks = {
            'financial_basics_monthly_expenses': 'financial_basics_monthly_income',
            'emergency_fund_target_amount': 'financial_basics_monthly_expenses',
            'goals_emergency_fund_target': 'financial_basics_monthly_expenses',
            'debt_repayment_goal_amount': 'assets_and_debts_total_debt',
            'home_loan_emi': 'assets_and_debts_home_loan_amount',
            'goals_retirement_target': 'financial_basics_monthly_expenses'
        }
        
        return question_id in consistency_checks and consistency_checks[question_id] in self.profile_context
    
    def _generate_consistent_answer(self, question_id: str, question: Dict[str, Any]) -> Any:
        """
        Generate an answer that's consistent with previous answers.
        """
        input_type = question.get('input_type', 'text')
        
        if question_id == 'financial_basics_monthly_expenses':
            # Expenses should be less than income
            monthly_income = float(self.profile_context.get('financial_basics_monthly_income', 100000))
            return int(monthly_income * random.uniform(0.6, 0.9))
            
        elif question_id == 'emergency_fund_target_amount' or question_id == 'goals_emergency_fund_target':
            # Emergency fund target based on monthly expenses
            monthly_expenses = float(self.profile_context.get('financial_basics_monthly_expenses', 50000))
            months = random.choice([3, 6, 9, 12])
            return int(monthly_expenses * months)
            
        elif question_id == 'debt_repayment_goal_amount':
            # Should be related to total debt
            total_debt = float(self.profile_context.get('assets_and_debts_total_debt', 1000000))
            return int(total_debt * random.uniform(0.9, 1.1))
            
        elif question_id == 'home_loan_emi':
            # EMI calculation based on loan amount
            loan_amount = float(self.profile_context.get('assets_and_debts_home_loan_amount', 5000000))
            # Approximate EMI for a 20-year loan at 8.5%
            return int(loan_amount * 0.0086)
            
        elif question_id == 'goals_retirement_target':
            # Retirement target based on current expenses
            monthly_expenses = float(self.profile_context.get('financial_basics_monthly_expenses', 50000))
            annual_expenses = monthly_expenses * 12
            return int(annual_expenses * 25)  # 25x annual expenses is a common rule of thumb
            
        # Default to input-type based generation if no specific logic
        return self._generate_by_input_type(input_type, question)
    
    def _generate_demographic_answer(self, question_id: str, input_type: str, question: Dict[str, Any]) -> Any:
        """Generate realistic demographic answers."""
        if question_id == 'demographics_age':
            age_group = self.profile_context.get('age_group', random.choice(list(self.age_ranges.keys())))
            min_age, max_age = self.age_ranges[age_group]
            return random.randint(min_age, max_age)
            
        elif question_id == 'demographics_education':
            return random.choice(self.education_levels)
            
        elif question_id == 'demographics_marital_status':
            return random.choice(self.marital_statuses)
            
        elif question_id == 'demographics_children':
            return random.choice(self.children_options)
            
        elif question_id == 'demographics_city':
            cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune', 'Kolkata']
            return random.choice(cities)
            
        return self._generate_by_input_type(input_type, question)
    
    def _generate_financial_basic_answer(self, question_id: str, input_type: str, question: Dict[str, Any]) -> Any:
        """Generate realistic financial basic answers."""
        if question_id == 'financial_basics_monthly_income':
            age_group = self.profile_context.get('age_group', 'mid_career')
            
            # Map age groups to income levels
            income_level = 'entry_level'
            if age_group == 'young_adult':
                income_level = 'entry_level'
            elif age_group == 'mid_career':
                income_level = random.choice(['mid_level', 'senior_level'])
            elif age_group == 'pre_retirement':
                income_level = random.choice(['senior_level', 'executive'])
            else:
                income_level = random.choice(['mid_level', 'senior_level'])
                
            min_income, max_income = self.income_ranges[income_level]
            annual_income = random.randint(min_income, max_income)
            return int(annual_income / 12)  # Convert to monthly
            
        elif question_id == 'financial_basics_monthly_expenses':
            if 'financial_basics_monthly_income' in self.profile_context:
                income = float(self.profile_context['financial_basics_monthly_income'])
                min_pct, max_pct = self.expense_percentages['essential']
                return int(income * random.uniform(min_pct, max_pct))
            else:
                return random.randint(30000, 80000)  # Default range
                
        elif question_id == 'financial_basics_tax_bracket':
            tax_brackets = ['0-5%', '5-10%', '10-20%', '20-30%', '30% and above']
            
            if 'financial_basics_monthly_income' in self.profile_context:
                income = float(self.profile_context['financial_basics_monthly_income']) * 12
                if income < 500000:
                    return tax_brackets[0]
                elif income < 750000:
                    return tax_brackets[1]
                elif income < 1000000:
                    return tax_brackets[2]
                elif income < 1500000:
                    return tax_brackets[3]
                else:
                    return tax_brackets[4]
            else:
                return random.choice(tax_brackets)
                
        elif question_id == 'financial_basics_saving_rate':
            saving_rates = ['Less than 10%', '10-20%', '20-30%', '30-40%', 'More than 40%']
            if 'financial_basics_monthly_income' in self.profile_context and 'financial_basics_monthly_expenses' in self.profile_context:
                income = float(self.profile_context['financial_basics_monthly_income'])
                expenses = float(self.profile_context['financial_basics_monthly_expenses'])
                saving_rate = (income - expenses) / income * 100
                
                if saving_rate < 10:
                    return saving_rates[0]
                elif saving_rate < 20:
                    return saving_rates[1]
                elif saving_rate < 30:
                    return saving_rates[2]
                elif saving_rate < 40:
                    return saving_rates[3]
                else:
                    return saving_rates[4]
            else:
                return random.choice(saving_rates)
        
        return self._generate_by_input_type(input_type, question)
    
    def _generate_assets_debts_answer(self, question_id: str, input_type: str, question: Dict[str, Any]) -> Any:
        """Generate realistic asset and debt answers."""
        if 'has_' in question_id:
            # Binary questions about having assets/debts
            key = question_id.replace('has_', '')
            probability = self.yes_no_probabilities.get(key, 0.5)
            return 'Yes' if random.random() < probability else 'No'
            
        elif 'amount' in question_id:
            # Amount-based questions
            asset_type = None
            for asset in self.asset_ranges:
                if asset in question_id:
                    asset_type = asset
                    break
                    
            debt_type = None
            for debt in self.debt_ranges:
                if debt in question_id:
                    debt_type = debt
                    break
            
            if asset_type:
                min_val, max_val = self.asset_ranges[asset_type]
                return random.randint(min_val, max_val)
            elif debt_type:
                min_val, max_val = self.debt_ranges[debt_type]
                return random.randint(min_val, max_val)
                
        elif 'emergency_fund' in question_id:
            if 'months' in question_id:
                return random.choice(self.emergency_fund_months)
            elif 'target' in question_id:
                if 'financial_basics_monthly_expenses' in self.profile_context:
                    expenses = float(self.profile_context['financial_basics_monthly_expenses'])
                    months = random.choice(self.emergency_fund_months)
                    return int(expenses * months)
                else:
                    return random.randint(200000, 600000)
        
        return self._generate_by_input_type(input_type, question)
    
    def _generate_goal_answer(self, question_id: str, input_type: str, question: Dict[str, Any]) -> Any:
        """Generate realistic goal-related answers."""
        if 'priority' in question_id:
            priorities = ['High', 'Medium', 'Low']
            return random.choice(priorities)
            
        elif 'timeframe' in question_id:
            timeframes = ['1-3 years', '3-5 years', '5-10 years', '10+ years']
            return random.choice(timeframes)
            
        elif 'retirement' in question_id:
            if 'age' in question_id:
                current_age = int(self.profile_context.get('demographics_age', 35))
                return random.randint(current_age + 10, 70)
            elif 'target' in question_id:
                if 'financial_basics_monthly_expenses' in self.profile_context:
                    monthly_expenses = float(self.profile_context['financial_basics_monthly_expenses'])
                    annual_expenses = monthly_expenses * 12
                    return int(annual_expenses * random.randint(20, 30))
                else:
                    return random.randint(10000000, 30000000)
                    
        elif 'education' in question_id:
            if 'target' in question_id:
                return random.randint(1000000, 5000000)
                
        elif 'home' in question_id:
            if 'target' in question_id:
                return random.randint(3000000, 10000000)
                
        elif 'emergency_fund' in question_id:
            if 'exists' in question_id:
                return 'Yes' if random.random() < 0.7 else 'No'
            elif 'months' in question_id:
                return random.choice(['3-6 months', '6-9 months', '9-12 months'])
                
        elif 'interested' in question_id:
            goal_type = question_id.replace('goals_interested_', '')
            probability = self.yes_no_probabilities.get(f'interested_in_{goal_type}', 0.5)
            return 'Yes' if random.random() < probability else 'No'
        
        return self._generate_by_input_type(input_type, question)
    
    def _generate_behavioral_answer(self, question_id: str, input_type: str, question: Dict[str, Any]) -> Any:
        """Generate realistic behavioral finance answers."""
        if 'risk_tolerance' in question_id:
            return random.choice(self.risk_profiles)
            
        elif 'loss_aversion' in question_id:
            # Loss aversion scenario with amounts
            options = question.get('options', [])
            return random.choice(options) if options else 'Moderate'
            
        elif 'decision_making' in question_id:
            decision_styles = ['Analytical', 'Intuitive', 'Consultative', 'Spontaneous']
            return random.choice(decision_styles)
            
        elif 'financial_stress' in question_id:
            stress_levels = ['Very Low', 'Low', 'Moderate', 'High', 'Very High']
            return random.choice(stress_levels)
        
        return self._generate_by_input_type(input_type, question)
    
    def _generate_by_input_type(self, input_type: str, question: Dict[str, Any]) -> Any:
        """Generate answer based on the input type."""
        if input_type == 'text':
            return "Response for " + question.get('id', 'unknown')
            
        elif input_type == 'number':
            min_val = question.get('min', 0)
            max_val = question.get('max', 1000000)
            
            # If not specified, make reasonable assumptions
            if min_val == 0 and max_val == 1000000:
                # Is this likely a large amount (asset/debt/goal)?
                if any(kw in question.get('id', '') for kw in ['amount', 'target', 'value', 'loan']):
                    min_val = 100000
                    max_val = 5000000
                # Is this likely a monthly value?
                elif any(kw in question.get('id', '') for kw in ['monthly', 'income', 'expense', 'emi']):
                    min_val = 10000
                    max_val = 200000
            
            return random.randint(min_val, max_val)
            
        elif input_type == 'select' or input_type == 'radio':
            options = question.get('options', [])
            if not options:
                return "No options available"
                
            if isinstance(options[0], dict):
                selected = random.choice(options)
                return selected.get('value')
            else:
                return random.choice(options)
                
        elif input_type == 'multiselect':
            options = question.get('options', [])
            if not options:
                return []
                
            # Select 1-3 options
            num_selections = random.randint(1, min(3, len(options)))
            selected_indices = random.sample(range(len(options)), num_selections)
            
            if isinstance(options[0], dict):
                return [options[i].get('value') for i in selected_indices]
            else:
                return [options[i] for i in selected_indices]
                
        elif input_type == 'slider':
            min_val = question.get('min', 0)
            max_val = question.get('max', 100)
            step = question.get('step', 1)
            
            # Generate a value that's a multiple of step
            range_steps = int((max_val - min_val) / step)
            steps = random.randint(0, range_steps)
            return min_val + (steps * step)
            
        elif input_type == 'date':
            # Generate a date in the appropriate range
            if 'birth' in question.get('id', ''):
                # Birth date - based on age
                age = self.profile_context.get('demographics_age', 35)
                year = datetime.datetime.now().year - age
                month = random.randint(1, 12)
                day = random.randint(1, 28)  # Safe for all months
                return f"{year}-{month:02d}-{day:02d}"
            else:
                # Future date
                years_ahead = random.randint(1, 10)
                year = datetime.datetime.now().year + years_ahead
                month = random.randint(1, 12)
                day = random.randint(1, 28)
                return f"{year}-{month:02d}-{day:02d}"
        
        # Default for unhandled types
        return "Generated answer for " + question.get('id', 'unknown')


class QuestionFlowSimulator:
    """
    Simulates the question flow system without requiring the frontend.
    Enhanced to provide more realistic financial answers and handle all question types.
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
        self.financial_parameter_service = FinancialParameterService()
        self.answer_generator = RealisticAnswerGenerator()
        
        # Create a new profile if none provided
        if profile_id:
            self.profile_id = profile_id
        else:
            self.profile_id = self._create_test_profile()
        
        logger.info(f"Initialized simulator with profile ID: {self.profile_id}")
    
    def _create_test_profile(self):
        """Create a test profile for simulation."""
        name = f"Test Simulation {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        email = f"test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        profile = self.profile_manager.create_profile(name, email)
        return profile['id']
    
    def simulate_question_flow(self, num_questions=30, answer_strategy='realistic'):
        """
        Simulate answering a series of questions and observe the flow.
        
        Args:
            num_questions: Number of questions to simulate (default: 30)
            answer_strategy: How to answer questions (realistic, random, or custom)
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
            
            # Update the profile context for consistent answers
            self.answer_generator.set_profile_context(profile)
            
            # Display question information
            self._display_question_info(next_question)
            questions_asked.append(next_question)
            
            # Generate an answer based on the strategy
            answer = self._generate_answer(next_question, answer_strategy)
            
            # Submit the answer
            self._submit_answer(next_question, answer)
            
            # Show current understanding level
            completion_metrics = self.question_service.get_profile_completion(profile)
            understanding_level = self.understanding_calculator.calculate_level(profile, completion_metrics)
            print(f"\nCurrent understanding level: {understanding_level}")
            
            # If this is a dynamically generated question, note that
            if next_question.get('type') == 'next_level' and next_question.get('id', '').startswith('gen_'):
                print("(This was a dynamically generated question)")
        
        # Final summary
        print(f"\n{'='*80}\nSIMULATION SUMMARY\n{'='*80}")
        profile = self.profile_manager.get_profile(self.profile_id)
        completion_metrics = self.question_service.get_profile_completion(profile)
        final_understanding = self.understanding_calculator.calculate_level(profile, completion_metrics)
        
        # Summarize questions by type
        question_types = {}
        for q in questions_asked:
            q_type = q.get('type', 'unknown')
            if q_type not in question_types:
                question_types[q_type] = 0
            question_types[q_type] += 1
        
        # Summarize questions by category
        question_categories = {}
        for q in questions_asked:
            q_cat = q.get('category', 'uncategorized')
            if q_cat not in question_categories:
                question_categories[q_cat] = 0
            question_categories[q_cat] += 1
        
        print(f"Total questions answered: {len(questions_asked)}")
        print(f"Final understanding level: {final_understanding}")
        
        print("\nQuestions by type:")
        for q_type, count in question_types.items():
            print(f"  - {q_type}: {count}")
            
        print("\nQuestions by category:")
        for q_cat, count in question_categories.items():
            print(f"  - {q_cat}: {count}")
        
        # Check for dynamically generated questions
        dynamic_count = sum(1 for q in questions_asked if q.get('id', '').startswith('gen_'))
        print(f"\nDynamically generated questions: {dynamic_count}")
        
        # Save report to question logs directory if it doesn't exist
        self._save_simulation_report(profile, questions_asked, understanding_level=final_understanding)
        
        return questions_asked
    
    def _display_question_info(self, question):
        """Display information about a question."""
        print(f"ID: {question.get('id')}")
        print(f"Type: {question.get('type')}")
        print(f"Category: {question.get('category', 'N/A')}")
        print(f"Input type: {question.get('input_type', 'text')}")
        
        if question.get('required'):
            print("Required: Yes")
        
        if question.get('dependencies'):
            print(f"Has dependencies: Yes ({len(question['dependencies'])})")
            
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
        if strategy == 'realistic':
            # Use the realistic answer generator
            return self.answer_generator.generate_answer(question)
        elif strategy == 'random':
            # Simple random approach for testing
            input_type = question.get('input_type', 'text')
            if input_type == 'text':
                return "Random test answer"
            elif input_type == 'number':
                return random.randint(1000, 500000)
            elif input_type in ('select', 'radio'):
                options = question.get('options', [])
                if options:
                    if isinstance(options[0], dict):
                        return random.choice(options).get('value')
                    else:
                        return random.choice(options)
                return "option1"
            elif input_type == 'multiselect':
                options = question.get('options', [])
                if options:
                    # Pick 1-3 random options
                    num_selections = random.randint(1, min(3, len(options)))
                    selected = random.sample(options, num_selections)
                    if isinstance(selected[0], dict):
                        return [item.get('value') for item in selected]
                    else:
                        return selected
                return ["option1"]
            else:
                return "Random answer for " + input_type
        else:
            # Custom strategy - ask for input
            print("Please provide an answer for this question:")
            user_answer = input("> ")
            
            # Parse the input based on question type
            input_type = question.get('input_type', 'text')
            if input_type == 'number':
                try:
                    return int(user_answer)
                except ValueError:
                    print("Invalid number format. Using default value 0.")
                    return 0
            elif input_type == 'multiselect':
                # Expect comma-separated values
                return [item.strip() for item in user_answer.split(',')]
            else:
                return user_answer
        
    def _submit_answer(self, question, answer):
        """Submit an answer to a question."""
        question_id = question.get('id')
        
        # Format the answer for display
        if isinstance(answer, list):
            display_answer = ", ".join(str(item) for item in answer)
        else:
            display_answer = str(answer)
            
        print(f"Submitting answer: {display_answer}")
        
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
    
    def _save_simulation_report(self, profile, questions_asked, understanding_level=None):
        """Save a report of the simulation to the question logs directory."""
        if not profile or not questions_asked:
            return
            
        try:
            # Create directory for this simulation
            logs_dir = Path(project_root) / 'data' / 'question_logs' / self.profile_id
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Save all questions and answers
            all_questions_path = logs_dir / 'all_questions.json'
            
            # Format questions for saving
            questions_with_answers = []
            profile_answers = {a.get('question_id'): a.get('answer') for a in profile.get('answers', [])}
            
            for q in questions_asked:
                q_data = q.copy()
                q_data['submitted_answer'] = profile_answers.get(q.get('id'))
                questions_with_answers.append(q_data)
                
            with open(all_questions_path, 'w') as f:
                json.dump(questions_with_answers, f, indent=2, default=str)
                
            # Create a summary report
            summary = {
                'profile_id': self.profile_id,
                'simulation_date': datetime.datetime.now().isoformat(),
                'total_questions': len(questions_asked),
                'understanding_level': understanding_level,
                'question_types': {},
                'question_categories': {}
            }
            
            # Summarize question types and categories
            for q in questions_asked:
                q_type = q.get('type', 'unknown')
                if q_type not in summary['question_types']:
                    summary['question_types'][q_type] = 0
                summary['question_types'][q_type] += 1
                
                q_cat = q.get('category', 'uncategorized')
                if q_cat not in summary['question_categories']:
                    summary['question_categories'][q_cat] = 0
                summary['question_categories'][q_cat] += 1
            
            # Save the summary
            summary_path = logs_dir / 'question_summary.json'
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
                
            # Generate a simple HTML report
            self._generate_html_report(logs_dir, summary, questions_with_answers)
            
            logger.info(f"Saved simulation reports to {logs_dir}")
        except Exception as e:
            logger.error(f"Error saving simulation report: {e}")
    
    def _generate_html_report(self, logs_dir, summary, questions):
        """Generate a simple HTML report for the simulation."""
        report_path = logs_dir / 'question_report.html'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Question Flow Simulation Report - {self.profile_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .summary {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .question {{ margin-bottom: 30px; border-left: 4px solid #ccc; padding-left: 15px; }}
                .question.core {{ border-left-color: #4CAF50; }}
                .question.goal {{ border-left-color: #2196F3; }}
                .question.next_level {{ border-left-color: #FF9800; }}
                .question.behavioral {{ border-left-color: #9C27B0; }}
                .meta {{ color: #666; font-size: 0.9em; }}
                .answer {{ margin-top: 10px; background-color: #f0f0f0; padding: 10px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1>Question Flow Simulation Report</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Profile ID: {self.profile_id}</p>
                <p>Simulation Date: {summary.get('simulation_date')}</p>
                <p>Total Questions: {summary.get('total_questions')}</p>
                <p>Understanding Level: {summary.get('understanding_level')}</p>
                
                <h3>Questions by Type</h3>
                <table>
                    <tr>
                        <th>Type</th>
                        <th>Count</th>
                    </tr>
        """
        
        # Add question type rows
        for q_type, count in summary.get('question_types', {}).items():
            html_content += f"""
                    <tr>
                        <td>{q_type}</td>
                        <td>{count}</td>
                    </tr>
            """
            
        html_content += """
                </table>
                
                <h3>Questions by Category</h3>
                <table>
                    <tr>
                        <th>Category</th>
                        <th>Count</th>
                    </tr>
        """
        
        # Add category rows
        for category, count in summary.get('question_categories', {}).items():
            html_content += f"""
                    <tr>
                        <td>{category}</td>
                        <td>{count}</td>
                    </tr>
            """
            
        html_content += """
                </table>
            </div>
            
            <h2>Questions and Answers</h2>
        """
        
        # Add each question and answer
        for i, question in enumerate(questions):
            q_type = question.get('type', 'unknown')
            q_id = question.get('id', 'unknown')
            q_category = question.get('category', 'N/A')
            q_text = question.get('text', 'No question text')
            q_answer = question.get('submitted_answer', 'No answer')
            
            # Format the answer for display
            if isinstance(q_answer, list):
                display_answer = ", ".join(str(item) for item in q_answer)
            else:
                display_answer = str(q_answer)
                
            html_content += f"""
            <div class="question {q_type}">
                <h3>Question {i+1}: {q_id}</h3>
                <div class="meta">
                    <p>Type: {q_type} | Category: {q_category} | Input Type: {question.get('input_type', 'text')}</p>
                    {f"<p>Relevance Score: {question.get('relevance_score')}</p>" if question.get('relevance_score') else ""}
                </div>
                <p>{q_text}</p>
                <div class="answer">
                    <strong>Answer:</strong> {display_answer}
                </div>
            </div>
            """
            
        html_content += """
        </body>
        </html>
        """
        
        with open(report_path, 'w') as f:
            f.write(html_content)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulate the question flow system')
    parser.add_argument('--profile_id', help='Use an existing profile ID')
    parser.add_argument('--questions', type=int, default=30, help='Number of questions to simulate')
    parser.add_argument('--strategy', choices=['realistic', 'random', 'custom'], default='realistic',
                        help='Strategy for answering questions')
    
    args = parser.parse_args()
    
    simulator = QuestionFlowSimulator(profile_id=args.profile_id)
    simulator.simulate_question_flow(num_questions=args.questions, answer_strategy=args.strategy)
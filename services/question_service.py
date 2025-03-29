import logging
from datetime import datetime
import json
import time
import os
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from services.llm_service import LLMService
from models.profile_understanding import ProfileUnderstandingCalculator
from models.question_generator import QuestionGenerator
from models.goal_probability import GoalProbabilityAnalyzer
from models.goal_adjustment import GoalAdjustmentRecommender, AdjustmentType
from services.goal_service import GoalService
from services.financial_parameter_service import get_financial_parameter_service
from services.goal_adjustment_service import GoalAdjustmentService
from models.goal_models import Goal, GoalCategory, GoalManager
from models.gap_analysis.analyzer import GapAnalysis

class QuestionLogger:
    """
    Dedicated logger for tracking question lifecycle events.
    Creates and maintains logs of all question events for each profile.
    """
    
    def __init__(self, log_dir="/Users/coddiwomplers/Desktop/Python/Profiler4/data/question_logs"):
        """Initialize the question logger with the specified log directory"""
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.question_data = {}
        
    def _get_profile_log_dir(self, profile_id):
        """Get the log directory for a specific profile"""
        profile_dir = os.path.join(self.log_dir, profile_id)
        os.makedirs(profile_dir, exist_ok=True)
        return profile_dir
    
    def log_question_generation(self, profile_id, question):
        """Log when a question is generated"""
        timestamp = datetime.now().isoformat()
        question_id = question.get('id', 'unknown')
        question_data = self._get_question_data(profile_id)
        
        if question_id not in question_data:
            question_data[question_id] = {
                'question_id': question_id,
                'question_text': question.get('text', ''),
                'question_type': question.get('type', ''),
                'generated_at': timestamp,
                'displayed_at': None,
                'answered_at': None,
                'answer': None
            }
        else:
            # Update generation timestamp if already exists
            question_data[question_id]['generated_at'] = timestamp
        
        self._save_question_data(profile_id, question_data)
    
    def log_question_display(self, profile_id, question_id):
        """Log when a question is displayed to the user"""
        timestamp = datetime.now().isoformat()
        question_data = self._get_question_data(profile_id)
        
        if question_id in question_data:
            question_data[question_id]['displayed_at'] = timestamp
        else:
            # Create a minimal entry if question wasn't previously tracked
            question_data[question_id] = {
                'question_id': question_id,
                'generated_at': None,
                'displayed_at': timestamp,
                'answered_at': None,
                'answer': None
            }
        
        self._save_question_data(profile_id, question_data)
        
    def log_question_displayed(self, profile_id, question_id, question_data=None):
        """Log when a question is displayed to the user (alias for log_question_display)"""
        # If question_data is provided, log more details
        if question_data and isinstance(question_data, dict):
            # Make sure we have the question ID
            if 'id' in question_data and question_id is None:
                question_id = question_data['id']
                
            # Log the full question for tracking
            self.log_question_generation(profile_id, question_data)
            
        # Log the display event
        self.log_question_display(profile_id, question_id)
    
    def log_answer_submission(self, profile_id, answer_data):
        """Log when an answer is submitted"""
        timestamp = datetime.now().isoformat()
        question_id = answer_data.get('question_id', 'unknown')
        question_data = self._get_question_data(profile_id)
        
        if question_id in question_data:
            question_data[question_id]['answered_at'] = timestamp
            question_data[question_id]['answer'] = answer_data.get('answer')
        else:
            # Create an entry if question wasn't previously tracked
            question_data[question_id] = {
                'question_id': question_id,
                'question_text': answer_data.get('text', ''),
                'generated_at': None,
                'displayed_at': None,
                'answered_at': timestamp,
                'answer': answer_data.get('answer')
            }
        
        self._save_question_data(profile_id, question_data)
    
    def _get_question_data(self, profile_id):
        """Get current question data for a profile"""
        # Check if already loaded in memory
        if profile_id in self.question_data:
            return self.question_data[profile_id]
        
        # Otherwise load from disk
        profile_dir = self._get_profile_log_dir(profile_id)
        data_file = os.path.join(profile_dir, 'all_questions.json')
        
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                self.question_data[profile_id] = data
                return data
            except Exception as e:
                logging.error(f"Error loading question data for {profile_id}: {str(e)}")
                return {}
        else:
            # No existing data
            return {}
    
    def _save_question_data(self, profile_id, question_data):
        """Save question data to disk"""
        self.question_data[profile_id] = question_data
        profile_dir = self._get_profile_log_dir(profile_id)
        data_file = os.path.join(profile_dir, 'all_questions.json')
        
        try:
            with open(data_file, 'w') as f:
                json.dump(question_data, f, indent=2)
            self._generate_summary_report(profile_id, question_data)
        except Exception as e:
            logging.error(f"Error saving question data for {profile_id}: {str(e)}")
    
    def _generate_summary_report(self, profile_id, question_data):
        """Generate a summary report of questions and answers"""
        profile_dir = self._get_profile_log_dir(profile_id)
        summary_file = os.path.join(profile_dir, 'question_summary.json')
        report_file = os.path.join(profile_dir, 'question_report.html')
        
        # Generate summary stats
        total_questions = len(question_data)
        answered_questions = sum(1 for q in question_data.values() if q.get('answered_at'))
        
        # Group by question type
        question_types = {}
        for q in question_data.values():
            q_type = q.get('question_type', 'unknown')
            if q_type not in question_types:
                question_types[q_type] = 0
            question_types[q_type] += 1
        
        # Calculate average response time for answered questions
        response_times = []
        for q in question_data.values():
            if q.get('displayed_at') and q.get('answered_at'):
                try:
                    display_time = datetime.fromisoformat(q['displayed_at'])
                    answer_time = datetime.fromisoformat(q['answered_at'])
                    response_time = (answer_time - display_time).total_seconds()
                    response_times.append(response_time)
                except:
                    pass
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Create summary data
        summary = {
            'profile_id': profile_id,
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'completion_percentage': round(answered_questions / total_questions * 100, 1) if total_questions else 0,
            'question_types': question_types,
            'avg_response_time_seconds': round(avg_response_time, 2),
            'generated_at': datetime.now().isoformat()
        }
        
        # Save summary
        try:
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving question summary for {profile_id}: {str(e)}")
        
        # Generate HTML report
        try:
            html = self._generate_html_report(profile_id, question_data, summary)
            with open(report_file, 'w') as f:
                f.write(html)
        except Exception as e:
            logging.error(f"Error generating HTML report for {profile_id}: {str(e)}")
    
    def _generate_html_report(self, profile_id, question_data, summary):
        """Generate an HTML report for visualization"""
        questions_html = ""
        for q_id, q in sorted(question_data.items(), 
                             key=lambda x: (x[1].get('generated_at') or 
                                           x[1].get('displayed_at') or 
                                           x[1].get('answered_at') or '')):
            # Format timestamps
            generated = q.get('generated_at', 'N/A')
            displayed = q.get('displayed_at', 'N/A')
            answered = q.get('answered_at', 'N/A')
            
            # Format answer based on type
            answer = q.get('answer')
            answer_text = "N/A"
            if answer is not None:
                if isinstance(answer, list):
                    answer_text = ", ".join(str(a) for a in answer)
                else:
                    answer_text = str(answer)
            
            # Create question entry
            questions_html += f"""
            <div class="question-entry">
                <h3>Question: {q.get('question_text', q_id)}</h3>
                <div class="question-details">
                    <div><strong>ID:</strong> {q_id}</div>
                    <div><strong>Type:</strong> {q.get('question_type', 'Unknown')}</div>
                    <div><strong>Generated:</strong> {generated}</div>
                    <div><strong>Displayed:</strong> {displayed}</div>
                    <div><strong>Answered:</strong> {answered}</div>
                    <div><strong>Answer:</strong> {answer_text}</div>
                </div>
            </div>
            """
        
        # Create summary section
        summary_html = f"""
        <div class="summary-section">
            <h2>Question Flow Summary</h2>
            <div class="summary-stats">
                <div><strong>Total Questions:</strong> {summary['total_questions']}</div>
                <div><strong>Answered Questions:</strong> {summary['answered_questions']}</div>
                <div><strong>Completion:</strong> {summary['completion_percentage']}%</div>
                <div><strong>Avg Response Time:</strong> {summary['avg_response_time_seconds']} seconds</div>
            </div>
            
            <h3>Question Types</h3>
            <ul class="question-types">
        """
        
        for q_type, count in summary['question_types'].items():
            summary_html += f"<li><strong>{q_type}:</strong> {count}</li>"
        
        summary_html += """
            </ul>
        </div>
        """
        
        # Complete HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Question Flow Report - {profile_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .summary-section {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .summary-stats {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 10px 0; }}
                .question-entry {{ border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; border-radius: 5px; }}
                .question-details {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; }}
                @media (max-width: 768px) {{
                    .summary-stats, .question-details {{ grid-template-columns: 1fr; }}
                }}
            </style>
        </head>
        <body>
            <h1>Question Flow Report</h1>
            <div><strong>Profile ID:</strong> {profile_id}</div>
            <div><strong>Generated:</strong> {summary['generated_at']}</div>
            
            {summary_html}
            
            <h2>Question Details</h2>
            {questions_html}
        </body>
        </html>
        """
        
        return html

class QuestionService:
    """
    Enhanced service for managing questions and answers with sophisticated prioritization,
    dynamic question generation, and adaptive flows based on profile understanding.
    """
    
    def __init__(self, question_repository, profile_manager, llm_service=None):
        """
        Initialize the question service.
        
        Args:
            question_repository: Repository of questions
            profile_manager: Manager for user profiles
            llm_service: Optional LLM service for dynamic question generation
        """
        self.question_repository = question_repository
        self.profile_manager = profile_manager
        self.llm_service = llm_service or LLMService()
        
        # Initialize understanding calculator
        self.understanding_calculator = ProfileUnderstandingCalculator()
        
        # Initialize dynamic question generator if LLM is available
        self.question_generator = QuestionGenerator(self.llm_service)
        
        # Initialize the goal probability analyzer for enhanced question integration
        self.goal_probability_analyzer = GoalProbabilityAnalyzer()
        
        # Initialize services for goals and adjustments
        self.goal_adjustment_recommender = GoalAdjustmentRecommender()
        self.goal_service = GoalService()
        self.parameter_service = get_financial_parameter_service()
        self.goal_adjustment_service = GoalAdjustmentService()
        
        # Initialize gap analysis
        self.gap_analysis = GapAnalysis()
        
        # Initialize question logger
        self.question_logger = QuestionLogger()
        
        # Track how many questions have been answered for each profile
        self.profile_question_counts = {}
        
        # Initialize dynamic questions cache
        self.dynamic_questions_cache = {}
    
    def get_next_question(self, profile_id) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Get the next question to ask for a profile.
        
        The question flow follows this logic:
        1. Core questions first, until requirements are met
        2. Goal questions next, until minimum goals are established
        3. Next-level questions as appropriate for deeper understanding
        4. Behavioral questions to round out understanding
        
        Args:
            profile_id: ID of the user profile
            
        Returns:
            Tuple of (question, profile) or (None, profile) if no more questions
        """
        # Get the profile
        profile = self.profile_manager.get_profile(profile_id)
        if not profile:
            logging.error(f"Profile not found for ID: {profile_id}")
            return None, None
        
        # Get completion metrics
        completion_metrics = self.get_profile_completion(profile)
        
        # Calculate understanding level
        understanding_level = self.understanding_calculator.calculate_level(profile, completion_metrics)
        level = understanding_level.get('id', 'RED')
        
        logging.info(f"Profile {profile_id} understanding level: {level}")
        
        # Check if there are any core questions to ask first
        if completion_metrics['core']['overall'] < 100:
            # Prioritize core questions with financial security foundation
            next_question = self._get_next_core_question(profile, completion_metrics)
            if next_question:
                logging.info(f"Returning core question for profile {profile_id}")
                # Log question generation
                self._log_question_generation(profile_id, next_question)
                return next_question, profile
        
        # Check if profile has enough goals defined - only move to next-level if ready
        if self._is_ready_for_goals(profile, completion_metrics):
            if self._has_pending_goal_questions(profile):
                # Return the next relevant goal question
                goal_question = self._get_next_goal_question(profile)
                if goal_question:
                    logging.info(f"Returning goal question for profile {profile_id}")
                    # Log question generation
                    self._log_question_generation(profile_id, goal_question)
                    return goal_question, profile
        
        # If we've answered all core and goal questions, move to next-level questions
        if self._is_ready_for_next_level(profile, completion_metrics):
            # Get next level question
            next_level_question = self._get_next_level_question(profile)
            if next_level_question:
                logging.info(f"Returning next-level question for profile {profile_id}")
                # Log the question generation
                self._log_question_generation(profile_id, next_level_question)
                return next_level_question, profile
            
            # If no next-level questions, try a behavioral question
            if self._is_ready_for_behavioral(profile, completion_metrics):
                behavioral_question = self._get_behavioral_question(profile)
                if behavioral_question:
                    logging.info(f"Returning behavioral question for profile {profile_id}")
                    # Log the question generation
                    self._log_question_generation(profile_id, behavioral_question)
                    return behavioral_question, profile
        
        # If we still have no questions, try to generate a dynamic question
        # based on the profile's current state
        next_level_question = self._generate_next_level_question(profile)
        if next_level_question:
            question_id = next_level_question.get('id')
            logging.info(f"Generated next-level question ({question_id}) for profile {profile_id}")
            # Log the question generation
            self._log_question_generation(profile_id, next_level_question)
            return next_level_question, profile
            
        # If we still have no questions, return None to indicate completion
        logging.info(f"No more questions available for profile {profile_id}")
        return None, profile
    
    def _add_emergency_fund_calculations(self, goal_question, emergency_fund_data, is_default=False):
        """
        Add emergency fund calculations to a goal question.
        
        Args:
            goal_question: The question to add calculations to
            emergency_fund_data: Data for the emergency fund calculation
            is_default: Whether this is using default values
        """
        # Format the numbers with commas for better readability
        monthly_expenses = f"₹{emergency_fund_data['monthly_expenses']:,.0f}"
        minimum_fund = f"₹{emergency_fund_data['minimum_fund']:,.0f}"
        recommended_fund = f"₹{emergency_fund_data['recommended_fund']:,.0f}"
        
        # Check if we're using default values
        is_default = emergency_fund_data.get('is_default', False)
        data_source = emergency_fund_data.get('data_source', "Your Data" if not is_default else "Example")
        
        # Create enhanced educational content with the actual calculations
        if is_default:
            educational_content = f"""
                <h3>Example Emergency Fund Calculation</h3>
                
                <p>Since you haven't provided your monthly expenses yet, here's an example calculation 
                based on a monthly expense of {monthly_expenses}. This demonstrates how emergency funds 
                are calculated in India:</p>
            """
        else:
            educational_content = f"""
                <h3>Your Personalized Emergency Fund Calculation</h3>
                
                <p>Based on the financial guidelines for India and your reported monthly expenses, 
                we've calculated recommended emergency fund targets for your specific situation:</p>
            """
        
        # Create calculation_details for the calculation box - using properly formatted HTML with data source
        calculation_details = f"""
            <div class="calculation-item">
                <div class="calculation-label">Your Monthly Expenses:</div>
                <div class="calculation-value">{monthly_expenses}</div>
            </div>
            <div class="calculation-item">
                <div class="calculation-label">Minimum Recommended (6 months):</div>
                <div class="calculation-value">{minimum_fund}</div>
            </div>
            <div class="calculation-item">
                <div class="calculation-label">Ideal Recommended (9 months):</div>
                <div class="calculation-value">{recommended_fund}</div>
            </div>
        """
        
        # Log the calculation details to help with debugging
        logging.info(f"CALCULATION DETAILS ADDED: Monthly Expenses={monthly_expenses}, " +
                    f"Minimum={minimum_fund}, Recommended={recommended_fund}, " +
                    f"Is Default={is_default}")
        
        # Explicitly add these properties to the question
        goal_question['educational_content'] = educational_content
        goal_question['calculation_details'] = calculation_details
        
        # Debug: Log that we've successfully added calculation_details
        logging.info(f"DEBUG: Successfully added calculation_details to question {goal_question.get('id')}")
        logging.info(f"DEBUG: Question now has keys: {goal_question.keys()}")
        
        # Add help text as fallback
        help_text = (
            f"Current Monthly Expenses: {monthly_expenses}\n"
            f"Minimum Recommended (6 months): {minimum_fund}\n"
            f"Ideal Recommended (9 months): {recommended_fund}"
        )
        goal_question.setdefault('help_text', help_text)
        
        return goal_question
    
    def _calculate_emergency_fund_recommendations(self, profile):
        """
        Calculate emergency fund recommendations based on profile data.
        
        Args:
            profile: User profile
            
        Returns:
            Dict with monthly_expenses, minimum_fund, and recommended_fund
        """
        # Get monthly expenses from profile if available
        monthly_expenses = None
        for answer in profile.get('answers', []):
            if answer.get('question_id') == 'financial_basics_monthly_expenses':
                try:
                    monthly_expenses = float(answer.get('answer', 0))
                    break
                except (ValueError, TypeError):
                    pass
        
        # Use default if not available
        if not monthly_expenses:
            # Example figures for a middle-class Indian household
            monthly_expenses = 50000  # ₹50,000 per month
            return {
                'monthly_expenses': monthly_expenses,
                'minimum_fund': monthly_expenses * 6,  # 6 months
                'recommended_fund': monthly_expenses * 9,  # 9 months
                'is_default': True,
                'data_source': 'Example'
            }
        
        # Calculate based on actual expenses
        return {
            'monthly_expenses': monthly_expenses,
            'minimum_fund': monthly_expenses * 6,  # 6 months
            'recommended_fund': monthly_expenses * 9,  # 9 months
            'is_default': False,
            'data_source': 'Your Data'
        }
    
    def _get_next_core_question(self, profile: Dict[str, Any], completion_metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the next core question to ask based on priority and completion.
        
        Core questions follow this priority:
        1. Financial Security Foundation questions first
        2. Income and expense questions
        3. Asset and debt questions
        4. Family and demographic questions
        
        Args:
            profile: User profile
            completion_metrics: Metrics on profile completion
            
        Returns:
            The next question to ask, or None if all core questions are answered
        """
        # Get all core questions
        all_core_questions = self.question_repository.get_core_questions()
        
        # Get the IDs of already answered questions
        answered_question_ids = [a['question_id'] for a in profile.get('answers', [])]
        
        # Filter out answered questions
        unanswered_questions = [q for q in all_core_questions if q['id'] not in answered_question_ids]
        
        if not unanswered_questions:
            return None
        
        # Define priority weights for different categories of core questions
        priority_categories = {
            'financial_security': 100,  # Highest priority - emergency fund, insurance
            'income_expenses': 80,      # Income, spending, savings rate
            'assets_debts': 60,         # Assets, debts, net worth
            'demographics': 40,         # Age, family, location
            'goals': 20                 # Basic goal information
        }
        
        # Map question IDs to their categories
        category_patterns = {
            'financial_security': ['emergency_fund', 'insurance', 'health'],
            'income_expenses': ['income', 'expense', 'saving', 'spending'],
            'assets_debts': ['asset', 'debt', 'loan', 'investment'],
            'demographics': ['age', 'family', 'location', 'dependents'],
            'goals': ['goals', 'plans', 'retirement']
        }
        
        # Score each question by its priority category and order within category
        for question in unanswered_questions:
            q_id = question['id'].lower()
            q_order = question.get('order', 50)  # Default order if not specified
            
            # Calculate base priority score
            priority = 0
            for category, weight in priority_categories.items():
                for pattern in category_patterns[category]:
                    if pattern in q_id:
                        priority = weight
                        break
                if priority > 0:
                    break
            
            # Final score is priority + inverse order (so lower order = higher score)
            question['_priority_score'] = priority + (100 - q_order) / 100
        
        # Sort by priority score (highest first)
        sorted_questions = sorted(unanswered_questions, 
                                 key=lambda q: q.get('_priority_score', 0), 
                                 reverse=True)
        
        if sorted_questions:
            # Remove the temporary score field
            if '_priority_score' in sorted_questions[0]:
                del sorted_questions[0]['_priority_score']
            return sorted_questions[0]
        
        return None
    
    def _get_next_goal_question(self, profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the next goal-related question to ask.
        
        Goal questions prioritize:
        1. Emergency fund questions first
        2. Basic retirement questions
        3. Other prioritized financial goals
        
        Args:
            profile: User profile
            
        Returns:
            The next goal question to ask, or None if all goal questions are answered
        """
        # Get all goal questions
        all_goal_questions = self.question_repository.get_questions_by_type('goal')
        
        # Get the IDs of already answered questions
        answered_question_ids = [a['question_id'] for a in profile.get('answers', [])]
        
        # Filter out answered questions
        unanswered_questions = [q for q in all_goal_questions if q['id'] not in answered_question_ids]
        
        if not unanswered_questions:
            return None
        
        # Define priority categories
        priority_categories = {
            'emergency_fund': 100,  # Highest priority
            'retirement': 80,
            'debt_repayment': 70,
            'education': 60,
            'home_purchase': 50,
            'other_goals': 40
        }
        
        # Score each question by category and order
        for question in unanswered_questions:
            q_id = question['id'].lower()
            q_order = question.get('order', 50)
            
            # Calculate priority score
            priority = 0
            for category, weight in priority_categories.items():
                if category in q_id:
                    priority = weight
                    break
            
            # If no specific category matched, use default
            if priority == 0:
                priority = priority_categories['other_goals']
            
            # Final score combines priority with inverse order
            question['_priority_score'] = priority + (100 - q_order) / 100
            
            # Special case for emergency fund - check if they already have one
            if 'emergency_fund' in q_id:
                has_emergency_fund = False
                for answer in profile.get('answers', []):
                    if answer.get('question_id') == 'goals_emergency_fund_exists':
                        if answer.get('answer', '').lower() == 'yes':
                            has_emergency_fund = True
                            break
                
                # If they already have an emergency fund, reduce priority of follow-up questions
                if has_emergency_fund and 'amount' in q_id:
                    question['_priority_score'] -= 20
        
        # Sort by priority score (highest first)
        sorted_questions = sorted(unanswered_questions, 
                                 key=lambda q: q.get('_priority_score', 0), 
                                 reverse=True)
        
        if not sorted_questions:
            return None
        
        # Select the highest priority question
        next_goal_question = sorted_questions[0]
        
        # Remove the temporary score field
        if '_priority_score' in next_goal_question:
            del next_goal_question['_priority_score']
        
        # Add enhanced goal content to certain question types
        if "emergency_fund" in next_goal_question.get('id', ''):
            profile_id = profile.get('id', 'unknown')
            
            # If this is the emergency fund target question
            if next_goal_question.get('id') == 'goals_emergency_fund_target':
                # Calculate emergency fund recommendations
                try:
                    emergency_fund_data = self._calculate_emergency_fund_recommendations(profile)
                    if emergency_fund_data:
                        next_goal_question = self._add_emergency_fund_calculations(
                            next_goal_question, 
                            emergency_fund_data
                        )
                except Exception as e:
                    # Log error if calculation failed
                    logging.error(f"ERROR: Failed to calculate emergency fund values: {str(e)}")
                    # Provide default value since calculation failed
                    next_goal_question['calculation_details'] = """
                        <div class="calculation-item">
                            <div class="calculation-label">Your Monthly Expenses (Example):</div>
                            <div class="calculation-value">₹50,000</div>
                        </div>
                        <div class="calculation-item">
                            <div class="calculation-label">Minimum Recommended (6 months):</div>
                            <div class="calculation-value">₹300,000</div>
                        </div>
                        <div class="calculation-item">
                            <div class="calculation-label">Ideal Recommended (9 months):</div>
                            <div class="calculation-value">₹450,000</div>
                        </div>
                    """
            
            # If this is the emergency fund amount question, set a default value based on calculations
            elif next_goal_question.get('id') == 'goals_emergency_fund_amount':
                # Calculate emergency fund recommendations
                emergency_fund_data = self._calculate_emergency_fund_recommendations(profile)
                if emergency_fund_data:
                    # Set default amount as recommended fund
                    next_goal_question['default'] = emergency_fund_data['recommended_fund']
        
        return next_goal_question
    
    def _get_next_level_question(self, profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the next higher-level question to ask.
        
        Args:
            profile: User profile
            
        Returns:
            The next question to ask, or None if all next-level questions are answered
        """
        # Get all next-level questions
        all_next_level_questions = self.question_repository.get_questions_by_type('next_level')
        
        # Get the IDs of already answered questions
        answered_question_ids = [a['question_id'] for a in profile.get('answers', [])]
        
        # Filter out answered questions
        unanswered_questions = [q for q in all_next_level_questions if q['id'] not in answered_question_ids]
        
        if not unanswered_questions:
            return None
        
        # Calculate relevance scores for each question based on profile
        for question in unanswered_questions:
            # Base score starts at 50
            relevance_score = 50
            
            # Check if category matches a goal
            question_category = question.get('category', '').lower()
            
            # Extract goals from profile
            has_matching_goal = False
            for answer in profile.get('answers', []):
                if answer.get('question_id', '').startswith('goals_'):
                    answer_value = answer.get('answer', '')
                    
                    # Check if answer contains this category
                    if isinstance(answer_value, str) and question_category in answer_value.lower():
                        has_matching_goal = True
                        relevance_score += 20
                        break
                    elif isinstance(answer_value, list) and any(question_category in str(v).lower() for v in answer_value):
                        has_matching_goal = True
                        relevance_score += 20
                        break
            
            # Boost score if matches priorities
            priorities = {
                'investment': 15,
                'tax': 15,
                'retirement': 10,
                'debt': 10,
                'emergency': 15
            }
            
            for keyword, boost in priorities.items():
                if keyword in question.get('id', '').lower() or keyword in question_category:
                    relevance_score += boost
            
            # Store the relevance score
            question['_relevance_score'] = relevance_score
        
        # Sort by relevance score (highest first)
        sorted_questions = sorted(unanswered_questions, 
                                 key=lambda q: q.get('_relevance_score', 0), 
                                 reverse=True)
        
        if not sorted_questions:
            return None
        
        # Select the highest relevance question
        next_level_question = sorted_questions[0]
        
        # Remove the temporary score field
        if '_relevance_score' in next_level_question:
            del next_level_question['_relevance_score']
        
        return next_level_question
    
    def _get_behavioral_question(self, profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the next behavioral question to ask.
        
        Args:
            profile: User profile
            
        Returns:
            The next behavioral question to ask, or None if all are answered
        """
        # Get all behavioral questions
        all_behavioral_questions = self.question_repository.get_questions_by_type('behavioral')
        
        # Get the IDs of already answered behavioral questions
        answered_behavioral_ids = [a['question_id'] for a in profile.get('answers', []) 
                                 if a['question_id'].startswith('behavioral_')]
        
        # Limit to 7 behavioral questions total
        if len(answered_behavioral_ids) >= 7:
            return None
        
        # Filter out answered questions
        unanswered_questions = [q for q in all_behavioral_questions if q['id'] not in answered_behavioral_ids]
        
        if not unanswered_questions:
            return None
        
        # Sort by order field if present
        sorted_questions = sorted(unanswered_questions, key=lambda q: q.get('order', 999))
        
        if sorted_questions:
            return sorted_questions[0]
        
        return None
    
    def _generate_next_level_question(self, profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate a dynamic next-level question based on profile data.
        
        Args:
            profile: User profile
            
        Returns:
            A dynamically generated question or None
        """
        # Skip if LLM service is not enabled
        if not self.llm_service.enabled:
            return None
            
        profile_id = profile.get('id', 'unknown')
        
        try:
            # Check if we've already asked multiple dynamic questions
            dynamic_questions_asked = sum(1 for a in profile.get('answers', []) 
                                        if a.get('question_id', '').startswith('gen_question_'))
            
            # Limit to a reasonable number of dynamically generated questions
            if dynamic_questions_asked >= 10:
                logging.info(f"Already asked {dynamic_questions_asked} dynamic questions - skipping generation")
                return None
            
            # Use the question generator to create personalized questions
            excluded_categories = []
            
            # Check which categories to exclude based on existing answers
            category_answer_counts = {}
            for answer in profile.get('answers', []):
                q_id = answer.get('question_id', '')
                if q_id.startswith('gen_question_'):
                    # Extract category from question ID (format: gen_question_category_timestamp)
                    parts = q_id.split('_')
                    if len(parts) > 2:
                        category = parts[2]
                        if category not in category_answer_counts:
                            category_answer_counts[category] = 0
                        category_answer_counts[category] += 1
            
            # Exclude categories with too many questions already
            for category, count in category_answer_counts.items():
                if count >= 3:  # Limit each category to 3 dynamic questions
                    excluded_categories.append(category)
            
            # Generate one personalized question
            generated_questions = self.question_generator.generate_personalized_questions(
                profile, 
                count=1,
                excluded_categories=excluded_categories
            )
            
            if generated_questions:
                return generated_questions[0]
                
        except Exception as e:
            logging.error(f"Error generating dynamic question for profile {profile_id}: {str(e)}")
            return None
        
        return None
    
    def _is_ready_for_goals(self, profile: Dict[str, Any], completion_metrics: Dict[str, Any]) -> bool:
        """
        Check if the profile is ready for goal questions.
        
        Args:
            profile: User profile
            completion_metrics: Metrics on profile completion
            
        Returns:
            True if ready for goal questions, False otherwise
        """
        # Require at least 60% of core questions to be completed
        if completion_metrics['core']['overall'] < 60:
            return False
            
        # Check if we have the essential financial data
        essential_questions = [
            'demographics_age',
            'financial_basics_annual_income',
            'financial_basics_monthly_expenses'
        ]
        
        # Count how many essential questions are answered
        answered_essential = 0
        for answer in profile.get('answers', []):
            if answer.get('question_id') in essential_questions:
                answered_essential += 1
        
        # Require at least 2 out of 3 essential questions
        return answered_essential >= 2
    
    def _has_pending_goal_questions(self, profile: Dict[str, Any]) -> bool:
        """
        Check if there are any unanswered goal questions.
        
        Args:
            profile: User profile
            
        Returns:
            True if there are unanswered goal questions, False otherwise
        """
        # Get all goal questions
        all_goal_questions = self.question_repository.get_questions_by_type('goal')
        
        # Get the IDs of already answered questions
        answered_question_ids = [a['question_id'] for a in profile.get('answers', [])]
        
        # Check if there are any unanswered goal questions
        for question in all_goal_questions:
            if question['id'] not in answered_question_ids:
                return True
        
        return False
    
    def _is_ready_for_next_level(self, profile: Dict[str, Any], completion_metrics: Dict[str, Any]) -> bool:
        """
        Check if the profile is ready for next-level questions.
        
        Args:
            profile: User profile
            completion_metrics: Metrics on profile completion
            
        Returns:
            True if ready for next-level questions, False otherwise
        """
        # Require at least 80% of core questions to be completed
        if completion_metrics['core']['overall'] < 80:
            return False
            
        # Count how many goal questions have been answered
        goal_questions_answered = 0
        for answer in profile.get('answers', []):
            if answer.get('question_id', '').startswith('goals_'):
                goal_questions_answered += 1
        
        # Require at least 3 goal questions to be answered
        return goal_questions_answered >= 3
    
    def _is_ready_for_behavioral(self, profile: Dict[str, Any], completion_metrics: Dict[str, Any]) -> bool:
        """
        Check if the profile is ready for behavioral questions.
        
        Args:
            profile: User profile
            completion_metrics: Metrics on profile completion
            
        Returns:
            True if ready for behavioral questions, False otherwise
        """
        # Require at least 80% of core questions to be completed
        if completion_metrics['core']['overall'] < 80:
            return False
            
        # Count how many next-level questions have been answered
        next_level_questions_answered = 0
        for answer in profile.get('answers', []):
            q_id = answer.get('question_id', '')
            if q_id.startswith('next_level_') or q_id.startswith('gen_question_'):
                next_level_questions_answered += 1
        
        # Require at least 3 next-level questions to be answered
        return next_level_questions_answered >= 3
    
    def get_profile_completion(self, profile_or_id: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        Calculate completion metrics for a profile.
        
        Args:
            profile_or_id: User profile object or profile ID
            
        Returns:
            Dict with completion metrics
        """
        # Handle both profile object and profile ID
        if isinstance(profile_or_id, str):
            # If profile_id is provided, get the profile
            profile = self.profile_manager.get_profile(profile_or_id)
        else:
            # If profile object is provided, use it directly
            profile = profile_or_id
            
        if not profile:
            return {
                'overall': 0,
                'core': {'overall': 0, 'count': 0, 'total': 0},
                'goals': {'overall': 0, 'count': 0, 'total': 0},
                'next_level': {'overall': 0, 'count': 0, 'total': 0},
                'behavioral': {'overall': 0, 'count': 0, 'total': 0}
            }
        
        # Get all question counts by type
        total_core = len(self.question_repository.get_core_questions())
        total_goals = len(self.question_repository.get_questions_by_type('goal'))
        total_next_level = len(self.question_repository.get_questions_by_type('next_level'))
        total_behavioral = len(self.question_repository.get_questions_by_type('behavioral'))
        
        # Count answered questions by type
        answered_questions = profile.get('answers', [])
        
        answered_core = sum(1 for a in answered_questions if a['question_id'].startswith(('demographics_', 'financial_basics_', 'assets_debts_')))
        answered_goals = sum(1 for a in answered_questions if a['question_id'].startswith('goals_'))
        
        # Count both standard and generated next-level questions
        answered_next_level = sum(1 for a in answered_questions 
                                if a['question_id'].startswith('next_level_') or 
                                a['question_id'].startswith('gen_question_'))
                                
        answered_behavioral = sum(1 for a in answered_questions if a['question_id'].startswith('behavioral_'))
        
        # Calculate percentages
        core_pct = min(100, int(answered_core / total_core * 100)) if total_core > 0 else 0
        goals_pct = min(100, int(answered_goals / total_goals * 100)) if total_goals > 0 else 0
        
        # For next-level and behavioral, use a min target count since we generate questions dynamically
        next_level_target = max(total_next_level, 10)  # At least 10 next-level questions
        next_level_pct = min(100, int(answered_next_level / next_level_target * 100))
        
        behavioral_target = min(total_behavioral, 7)  # Cap at 7 behavioral questions
        behavioral_pct = min(100, int(answered_behavioral / behavioral_target * 100))
        
        # Calculate overall percentage with weightings
        weights = {'core': 0.4, 'goals': 0.3, 'next_level': 0.2, 'behavioral': 0.1}
        overall_pct = int(
            core_pct * weights['core'] +
            goals_pct * weights['goals'] +
            next_level_pct * weights['next_level'] +
            behavioral_pct * weights['behavioral']
        )
        
        # Return detailed metrics
        return {
            'overall': overall_pct,
            'core': {
                'overall': core_pct,
                'count': answered_core,
                'total': total_core
            },
            'goals': {
                'overall': goals_pct,
                'count': answered_goals,
                'total': total_goals
            },
            'next_level': {
                'overall': next_level_pct,
                'count': answered_next_level,
                'total': next_level_target
            },
            'behavioral': {
                'overall': behavioral_pct,
                'count': answered_behavioral,
                'total': behavioral_target
            }
        }
    
    def save_question_answer(self, profile_id, answer_data):
        """Save a question answer."""
        # Set up detailed logging
        request_id = f"save_{uuid.uuid4().hex[:8]}"
        logging.info(f"[{request_id}] Starting save_question_answer for profile: {profile_id}")
        
        if not profile_id or not answer_data:
            logging.error(f"[{request_id}] Invalid save request - missing profile_id or answer_data: {profile_id}, {answer_data}")
            return False
            
        # Add timestamp if missing
        if 'timestamp' not in answer_data or not answer_data['timestamp']:
            answer_data['timestamp'] = datetime.now().isoformat()
        
        # Get the profile first
        try:
            logging.info(f"[{request_id}] Fetching profile with ID: {profile_id}")
            profile = self.profile_manager.get_profile(profile_id)
            if not profile:
                logging.error(f"[{request_id}] Profile not found for ID: {profile_id}")
                return False
            logging.info(f"[{request_id}] Successfully retrieved profile, answer count: {len(profile.get('answers', []))}")
        except Exception as e:
            logging.error(f"[{request_id}] Exception retrieving profile: {str(e)}")
            return False
            
        # Add the answer to the profile
        question_id = answer_data.get('question_id')
        answer_value = answer_data.get('answer')
        
        logging.info(f"[{request_id}] Processing answer for question ID: {question_id}, value type: {type(answer_value)}, value: {answer_value}")
        
        # Check only if question_id is missing
        if not question_id:
            logging.error(f"[{request_id}] Missing question ID in answer data")
            return False
            
        # For multiselect, empty list is acceptable. For other types, None is not acceptable
        if answer_value is None:
            logging.error(f"[{request_id}] Answer value is None for question {question_id}")
            return False
            
        try:
            # Check if the profile already has an answer for this question and remove it if exists
            existing_answers = profile.get('answers', [])
            previous_answer_count = len(existing_answers)
            profile['answers'] = [a for a in existing_answers if a.get('question_id') != question_id]
            current_answer_count = len(profile.get('answers', []))
            
            logging.info(f"[{request_id}] Filtered existing answers: {previous_answer_count} -> {current_answer_count}")
            
            # Add the answer to the profile
            logging.info(f"[{request_id}] Calling profile_manager.add_answer")
            saved = self.profile_manager.add_answer(profile, question_id, answer_value)
            
            # Log the result and verify answer count after save
            if saved:
                try:
                    # Double-check the profile was updated correctly
                    updated_profile = self.profile_manager.get_profile(profile_id)
                    if updated_profile:
                        updated_answer_count = len(updated_profile.get('answers', []))
                        logging.info(f"[{request_id}] Profile after save has {updated_answer_count} answers")
                except Exception as check_e:
                    logging.error(f"[{request_id}] Error checking updated profile: {str(check_e)}")
                
                # Log the answer
                try:
                    logger = QuestionLogger()
                    logger.log_answer_submission(profile_id, answer_data)
                except Exception as log_e:
                    logging.error(f"[{request_id}] Error logging answer: {str(log_e)}")
                
                logging.info(f"[{request_id}] Successfully saved answer for question {question_id} in profile {profile_id}")
            else:
                logging.error(f"[{request_id}] Failed to save answer for question {question_id} in profile {profile_id}")
        except Exception as e:
            logging.error(f"[{request_id}] Exception in save_question_answer processing: {str(e)}")
            return False
            
        return saved
    
    def _log_question_generation(self, profile_id, question):
        """Log the generation of a question."""
        logger = QuestionLogger()
        logger.log_question_generation(profile_id, question)
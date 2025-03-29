import logging
from datetime import datetime
import json
import time
import os
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
        
        # Create the log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Dictionary to store in-memory logs before writing to file
        self.question_logs = {}
    
    def _ensure_profile_log(self, profile_id):
        """Ensure the profile's log file exists and is properly initialized"""
        profile_log_dir = os.path.join(self.log_dir, profile_id)
        
        if not os.path.exists(profile_log_dir):
            os.makedirs(profile_log_dir)
            
        return profile_log_dir
    
    def log_question_generated(self, profile_id, question_id, question_data):
        """Log when a question is generated (by system or LLM)"""
        log_entry = {
            "event": "question_generated",
            "timestamp": datetime.now().isoformat(),
            "question_id": question_id,
            "question_type": question_data.get('type', 'unknown'),
            "question_category": question_data.get('category', 'unknown'),
            "question_text": question_data.get('text', ''),
            "input_type": question_data.get('input_type', 'unknown'),
            "is_llm_generated": bool('llm_next_level' in question_id or 'gen_question' in question_id),
            "is_fallback": bool('fallback' in question_id),
            "is_required": question_data.get('required', False),
            "order": question_data.get('order', None),
        }
        
        self._append_to_question_log(profile_id, question_id, log_entry)
    
    def log_question_displayed(self, profile_id, question_id, question_data):
        """Log when a question is displayed to the user"""
        log_entry = {
            "event": "question_displayed",
            "timestamp": datetime.now().isoformat(),
            "question_id": question_id,
            "question_text": question_data.get('text', ''),
        }
        
        self._append_to_question_log(profile_id, question_id, log_entry)
    
    def log_question_answered(self, profile_id, question_id, answer_value, question_data=None):
        """Log when a question is answered by the user"""
        log_entry = {
            "event": "question_answered",
            "timestamp": datetime.now().isoformat(),
            "question_id": question_id,
            "answer_value": self._format_answer_for_log(answer_value),
        }
        
        if question_data:
            log_entry["question_text"] = question_data.get('text', '')
            log_entry["question_type"] = question_data.get('type', 'unknown')
            log_entry["question_category"] = question_data.get('category', 'unknown')
        
        self._append_to_question_log(profile_id, question_id, log_entry)
    
    def _format_answer_for_log(self, answer_value):
        """Format the answer value to ensure it can be properly serialized"""
        # If the answer is an iterable but not a string or dict, convert to list
        if hasattr(answer_value, '__iter__') and not isinstance(answer_value, (str, dict)):
            return list(answer_value)
        return answer_value
    
    def _append_to_question_log(self, profile_id, question_id, log_entry):
        """Append a log entry to the appropriate question log"""
        # Initialize profile logs if not exist
        if profile_id not in self.question_logs:
            self.question_logs[profile_id] = {}
            
        # Initialize question log if not exist
        if question_id not in self.question_logs[profile_id]:
            self.question_logs[profile_id][question_id] = []
            
        # Add the log entry
        self.question_logs[profile_id][question_id].append(log_entry)
        
        # Write the updated logs to disk
        self._write_logs_to_disk(profile_id)
    
    def _write_logs_to_disk(self, profile_id):
        """Write the question logs for a profile to disk"""
        profile_log_dir = self._ensure_profile_log(profile_id)
        
        # Write a comprehensive log file with all questions
        all_questions_log_path = os.path.join(profile_log_dir, "all_questions.json")
        
        try:
            with open(all_questions_log_path, 'w') as f:
                json.dump(self.question_logs[profile_id], f, indent=2)
        except Exception as e:
            logging.error(f"Error writing question logs for profile {profile_id}: {str(e)}")
            
        # Write a summary file for easier analysis
        summary_log_path = os.path.join(profile_log_dir, "question_summary.json")
        
        try:
            summary = {}
            for question_id, events in self.question_logs[profile_id].items():
                # Get the most recent version of each event type
                latest_events = {}
                for event in events:
                    event_type = event["event"]
                    latest_events[event_type] = event
                
                # Create the summary entry
                summary[question_id] = {
                    "question_id": question_id,
                    "question_text": (latest_events.get("question_generated", {}).get("question_text") or
                                     latest_events.get("question_displayed", {}).get("question_text") or
                                     latest_events.get("question_answered", {}).get("question_text") or ""),
                    "question_type": latest_events.get("question_generated", {}).get("question_type", "unknown"),
                    "category": latest_events.get("question_generated", {}).get("question_category", "unknown"),
                    "is_llm_generated": latest_events.get("question_generated", {}).get("is_llm_generated", False),
                    "is_fallback": latest_events.get("question_generated", {}).get("is_fallback", False),
                    "generated_at": latest_events.get("question_generated", {}).get("timestamp", None),
                    "displayed_at": latest_events.get("question_displayed", {}).get("timestamp", None),
                    "answered_at": latest_events.get("question_answered", {}).get("timestamp", None),
                    "answer_value": latest_events.get("question_answered", {}).get("answer_value", None),
                    "lifecycle_complete": all(e in latest_events for e in ["question_generated", "question_displayed", "question_answered"]),
                }
            
            with open(summary_log_path, 'w') as f:
                json.dump(summary, f, indent=2)
                
            # Generate an HTML summary for easier viewing
            self._generate_html_summary(profile_id, summary)
                
        except Exception as e:
            logging.error(f"Error writing question summary log for profile {profile_id}: {str(e)}")
            
    def _generate_html_summary(self, profile_id, summary):
        """Generate an HTML summary of questions for easier analysis"""
        profile_log_dir = self._ensure_profile_log(profile_id)
        html_path = os.path.join(profile_log_dir, "question_report.html")
        
        try:
            # Sort questions by types and the time they were first displayed
            core_questions = []
            goal_questions = []
            next_level_questions = []
            behavioral_questions = []
            other_questions = []
            
            for qid, q_data in summary.items():
                if q_data["question_type"] == "core":
                    core_questions.append(q_data)
                elif q_data["question_type"] == "goal":
                    goal_questions.append(q_data)
                elif q_data["question_type"] == "next_level":
                    next_level_questions.append(q_data)
                elif q_data["question_type"] == "behavioral":
                    behavioral_questions.append(q_data)
                else:
                    other_questions.append(q_data)
            
            # Sort each group by displayed_at timestamp
            for q_list in [core_questions, goal_questions, next_level_questions, behavioral_questions, other_questions]:
                q_list.sort(key=lambda q: q.get("displayed_at", "9999-99-99") or "9999-99-99")
            
            # Generate HTML
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Question Report for Profile {profile_id}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                    h1, h2, h3 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .timestamp {{ font-size: 0.8em; color: #666; }}
                    .duplicated {{ background-color: #ffe6e6; }}
                    .section {{ margin-bottom: 40px; }}
                    .question-text {{ font-weight: bold; }}
                    .llm-generated {{ background-color: #e6f7ff; }}
                    .fallback {{ background-color: #fff2e6; }}
                    .lifecycle-incomplete {{ background-color: #fffde6; }}
                    .durations {{ font-size: 0.85em; color: #444; }}
                </style>
            </head>
            <body>
                <h1>Question Report for Profile {profile_id}</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="section">
                    <h2>Summary Statistics</h2>
                    <table>
                        <tr>
                            <th>Metric</th>
                            <th>Count</th>
                        </tr>
                        <tr>
                            <td>Total Questions</td>
                            <td>{len(summary)}</td>
                        </tr>
                        <tr>
                            <td>Core Questions</td>
                            <td>{len(core_questions)}</td>
                        </tr>
                        <tr>
                            <td>Goal Questions</td>
                            <td>{len(goal_questions)}</td>
                        </tr>
                        <tr>
                            <td>Next-Level Questions</td>
                            <td>{len(next_level_questions)}</td>
                        </tr>
                        <tr>
                            <td>Behavioral Questions</td>
                            <td>{len(behavioral_questions)}</td>
                        </tr>
                        <tr>
                            <td>LLM-Generated Questions</td>
                            <td>{len([q for q in summary.values() if q.get("is_llm_generated", False)])}</td>
                        </tr>
                        <tr>
                            <td>Fallback Questions</td>
                            <td>{len([q for q in summary.values() if q.get("is_fallback", False)])}</td>
                        </tr>
                    </table>
                </div>
            """
            
            # Function to generate a table for a question set
            def generate_question_table(title, questions):
                if not questions:
                    return f"<div class='section'><h2>{title}</h2><p>No questions in this category.</p></div>"
                
                # Find duplicate questions (by text)
                text_count = {}
                for q in questions:
                    text = q.get("question_text", "")
                    text_count[text] = text_count.get(text, 0) + 1
                
                html = f"""
                <div class="section">
                    <h2>{title} ({len(questions)})</h2>
                    <table>
                        <tr>
                            <th>ID</th>
                            <th>Question</th>
                            <th>Answer</th>
                            <th>Timestamps</th>
                            <th>Details</th>
                        </tr>
                """
                
                for q in questions:
                    # Calculate time between events
                    generated_time = None
                    displayed_time = None
                    answered_time = None
                    
                    if q.get("generated_at"):
                        generated_time = datetime.fromisoformat(q["generated_at"])
                    if q.get("displayed_at"):
                        displayed_time = datetime.fromisoformat(q["displayed_at"])
                    if q.get("answered_at"):
                        answered_time = datetime.fromisoformat(q["answered_at"])
                    
                    durations = []
                    if generated_time and displayed_time:
                        gen_to_display = (displayed_time - generated_time).total_seconds()
                        durations.append(f"Gen→Display: {gen_to_display:.1f}s")
                    
                    if displayed_time and answered_time:
                        display_to_answer = (answered_time - displayed_time).total_seconds()
                        durations.append(f"Display→Answer: {display_to_answer:.1f}s")
                    
                    # Check if this question text is duplicated
                    is_duplicated = text_count.get(q.get("question_text", ""), 0) > 1
                    is_llm = q.get("is_llm_generated", False)
                    is_fallback = q.get("is_fallback", False)
                    is_complete = q.get("lifecycle_complete", False)
                    
                    # Determine row CSS classes
                    row_classes = []
                    if is_duplicated:
                        row_classes.append("duplicated")
                    if is_llm:
                        row_classes.append("llm-generated")
                    if is_fallback:
                        row_classes.append("fallback")
                    if not is_complete:
                        row_classes.append("lifecycle-incomplete")
                    
                    row_class = f"class='{' '.join(row_classes)}'" if row_classes else ""
                    
                    # Format the answer value for display
                    answer_value = q.get("answer_value")
                    if isinstance(answer_value, list):
                        answer_display = ", ".join(str(item) for item in answer_value)
                    elif answer_value is None:
                        answer_display = "<em>Not answered</em>"
                    else:
                        answer_display = str(answer_value)
                    
                    html += f"""
                        <tr {row_class}>
                            <td>{q["question_id"]}</td>
                            <td class="question-text">{q["question_text"]}</td>
                            <td>{answer_display}</td>
                            <td>
                                <div class="timestamp">Generated: {q.get("generated_at", "N/A")}</div>
                                <div class="timestamp">Displayed: {q.get("displayed_at", "N/A")}</div>
                                <div class="timestamp">Answered: {q.get("answered_at", "N/A")}</div>
                                <div class="durations">{" | ".join(durations)}</div>
                            </td>
                            <td>
                                <div>Type: {q["question_type"]}</div>
                                <div>Category: {q["category"]}</div>
                                <div>LLM Generated: {str(is_llm)}</div>
                                <div>Fallback: {str(is_fallback)}</div>
                                <div>Lifecycle Complete: {str(is_complete)}</div>
                            </td>
                        </tr>
                    """
                
                html += """
                    </table>
                </div>
                """
                return html
            
            # Generate tables for each question type
            html_content += generate_question_table("Core Questions", core_questions)
            html_content += generate_question_table("Goal Questions", goal_questions)
            html_content += generate_question_table("Next-Level Questions", next_level_questions)
            html_content += generate_question_table("Behavioral Questions", behavioral_questions)
            html_content += generate_question_table("Other Questions", other_questions)
            
            # Finish the HTML document
            html_content += """
            </body>
            </html>
            """
            
            # Write to file
            with open(html_path, 'w') as f:
                f.write(html_content)
                
            logging.info(f"Generated HTML question report for profile {profile_id}: {html_path}")
            
        except Exception as e:
            logging.error(f"Error generating HTML question report for profile {profile_id}: {str(e)}")

class QuestionService:
    """
    Service for handling question flow logic and answer management.
    Determines next questions and processes answer submissions.
    """
    
    def __init__(self, question_repository, profile_manager, llm_service=None):
        """
        Initialize the question service with required dependencies.
        
        Args:
            question_repository: Repository for question definitions
            profile_manager: Manager for profile operations
            llm_service: Optional LLMService for generating dynamic questions
        """
        self.question_repository = question_repository
        self.profile_manager = profile_manager
        self.llm_service = llm_service or LLMService()
        
        # Cache for dynamically generated questions
        self.dynamic_questions_cache = {}
        
        # Understanding level calculator
        self.understanding_calculator = ProfileUnderstandingCalculator()
        
        # Initialize the question logger
        self.question_logger = QuestionLogger()
        
        # New enhanced components
        self.question_generator = QuestionGenerator(self.llm_service)
        self.goal_service = GoalService()
        self.goal_adjustment_service = GoalAdjustmentService()
        self.goal_probability_analyzer = GoalProbabilityAnalyzer()
        self.goal_manager = GoalManager()
        self.parameter_service = get_financial_parameter_service()
        
        # Cache for probability analysis
        self.probability_analysis_cache = {}
        
        # Indian context specific configuration
        self.india_specific_configs = {
            "tax_benefits": {
                "section_80c_limit": 150000,  # ₹1.5 lakh
                "section_80d_limit": 25000,   # ₹25,000 for self (50,000 for seniors)
                "nps_additional_limit": 50000 # ₹50,000 additional under 80CCD(1B)
            },
            "investment_priorities": [
                "emergency_fund",       # First priority
                "health_insurance",     # Second priority
                "life_insurance",       # Third priority  
                "debt_repayment",       # Fourth priority
                "retirement_planning",  # Fifth priority
                "education_planning",   # Sixth priority (higher in Indian context)
                "home_purchase",        # Seventh priority
                "other_goals"           # Eighth priority
            ],
            "financial_context_relevance": {
                "family_support": 0.8,  # High relevance for family financial support
                "education": 0.9,       # Very high relevance for education funding
                "real_estate": 0.7,     # High relevance for home ownership
                "gold": 0.6,            # Medium-high relevance for gold as investment
                "epf_ppf": 0.8          # High relevance for EPF/PPF retirement vehicles
            }
        }
        
        logging.basicConfig(level=logging.INFO)
        
    def get_next_question(self, profile_id):
        """
        Get the next appropriate question for a profile.
        
        Enhanced implementation that:
        - Integrates with QuestionGenerator for personalized follow-up questions
        - Prioritizes questions that would improve goal calculation accuracy
        - Adapts sequencing based on detected financial knowledge gaps
        - Adds educational content specific to Indian financial context
        - Displays calculated probability data alongside relevant questions
        - Implements financial security hierarchy prioritization
        
        Args:
            profile_id (str): ID of the profile
            
        Returns:
            dict: Question definition or None if all required questions are complete
            dict: Profile object for context
        """
        # Load profile
        profile = self.profile_manager.get_profile(profile_id)
        if not profile:
            logging.error(f"Profile {profile_id} not found")
            return None, None
            
        # Calculate understanding level once to use throughout the method
        understanding_level = self.understanding_calculator.calculate_understanding_level(profile)
        logging.info(f"Profile {profile_id} understanding level: {understanding_level}")
        
        # 0. Check if we should recalculate goal probabilities
        self._update_goal_probabilities(profile)
        
        # 1. ENHANCEMENT: Check for financial security foundation gaps
        foundation_question = self._check_financial_security_foundation(profile)
        if foundation_question:
            question_id = foundation_question.get('id')
            logging.info(f"Prioritizing foundation security question ({question_id}) in profile {profile_id}")
            # Add educational context for Indian financial landscape if needed
            if self._should_add_indian_educational_context(foundation_question, profile):
                foundation_question = self._add_indian_educational_context(foundation_question, profile)
            # Add probability visualization if goal-related
            if self._is_goal_related_question(foundation_question):
                foundation_question = self._add_goal_probability_visualization(foundation_question, profile)
            # Log the question generation
            self._log_question_generation(profile_id, foundation_question)
            return foundation_question, profile
        
        # 2. Continue with regular hierarchy - Check for special cases
        special_case_question = self._check_special_case_questions(profile)
        if special_case_question:
            question_id = special_case_question.get('id')
            logging.info(f"Prioritizing special case question ({question_id}) in profile {profile_id}")
            # Add Indian context if appropriate
            if self._should_add_indian_educational_context(special_case_question, profile):
                special_case_question = self._add_indian_educational_context(special_case_question, profile)
            # Log the question generation
            self._log_question_generation(profile_id, special_case_question)
            return special_case_question, profile
            
        # 3. ENHANCEMENT: Check for Indian-specific financial paths
        indian_context_question = self._get_indian_context_question(profile, understanding_level)
        if indian_context_question:
            question_id = indian_context_question.get('id')
            logging.info(f"Serving Indian financial context question ({question_id}) for profile {profile_id}")
            # Add goal probability visualization if relevant
            if self._is_goal_related_question(indian_context_question):
                indian_context_question = self._add_goal_probability_visualization(indian_context_question, profile)
            # Log the question generation
            self._log_question_generation(profile_id, indian_context_question)
            return indian_context_question, profile
            
        # 4. Check for unanswered core questions from repository
        core_question = self._get_next_core_question(profile)
        if core_question:
            question_id = core_question.get('id')
            logging.info(f"Found unanswered core question ({question_id}) for profile {profile_id}")
            # Add educational context if needed
            if self._should_add_indian_educational_context(core_question, profile):
                core_question = self._add_indian_educational_context(core_question, profile)
            # Log the question generation
            self._log_question_generation(profile_id, core_question)
            return core_question, profile
            
        # 5. Check for unanswered goal-setting questions with enhanced prioritization
        goal_question = self._get_next_goal_question(profile)
        if goal_question:
            question_id = goal_question.get('id')
            logging.info(f"Found unanswered goal question ({question_id}) for profile {profile_id}")
            # Add goal probability visualization
            goal_question = self._add_goal_probability_visualization(goal_question, profile)
            # Log the question generation
            self._log_question_generation(profile_id, goal_question)
            return goal_question, profile
        
        # 6. ENHANCEMENT: Generate personalized follow-up questions based on knowledge gaps
        if understanding_level == "RED":
            # Try to get a specific educational question with Indian context
            educational_question = self._get_next_educational_question(profile, add_indian_context=True)
            if educational_question:
                question_id = educational_question.get('id')
                logging.info(f"Serving educational question ({question_id}) due to RED understanding level")
                # Log the question generation
                self._log_question_generation(profile_id, educational_question)
                return educational_question, profile
        
        # 7. Check for behavioral questions if the profile has a good financial foundation
        if understanding_level in ["YELLOW", "GREEN"]:
            behavioral_question = self._get_next_behavioral_question(profile)
            if behavioral_question:
                question_id = behavioral_question.get('id')
                logging.info(f"Found behavioral question ({question_id}) for profile with {understanding_level} understanding")
                # Log the question generation
                self._log_question_generation(profile_id, behavioral_question)
                return behavioral_question, profile
        
        # 8. ENHANCEMENT: Use QuestionGenerator for personalized questions
        # For profiles with existing answers and goals, generate more personalized questions
        if len(profile.get('answers', [])) > 5:  # Only if we have some context
            try:
                personalized_questions = self.question_generator.generate_personalized_questions(
                    profile=profile,
                    count=1,  # Just get the highest priority question
                    excluded_categories=[]
                )
                
                if personalized_questions:
                    question = personalized_questions[0]
                    question_id = question.get('id')
                    logging.info(f"Generated personalized question ({question_id}) for profile {profile_id}")
                    
                    # Add goal probability visualization if goal-related
                    if self._is_goal_related_question(question):
                        question = self._add_goal_probability_visualization(question, profile)
                        
                    # Log the question generation
                    self._log_question_generation(profile_id, question)
                    return question, profile
            except Exception as e:
                logging.error(f"Error generating personalized questions: {str(e)}")
                # Continue to fallback options
        
        # 9. As a fallback, try to get LLM-generated next-level questions
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

    def _log_question_generation(self, profile_id, question):
        """Log the generation of a question."""
        logger = QuestionLogger()
        logger.log_question_generation(profile_id, question)

    def save_question_answer(self, profile_id, answer_data):
        """Save a question answer."""
        if not profile_id or not answer_data:
            return False
            
        # Add timestamp if missing
        if 'timestamp' not in answer_data or not answer_data['timestamp']:
            answer_data['timestamp'] = datetime.now().isoformat()
            
        # Add the answer to the profile
        saved = self.profile_manager.add_answer(profile_id, answer_data)
        
        # Log the answer
        if saved:
            logger = QuestionLogger()
            logger.log_answer_submission(profile_id, answer_data)
            
        return saved

import logging
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
import re

from services.llm_service import LLMService
from models.profile_understanding import ProfileUnderstandingCalculator

class QuestionGenerator:
    """
    Enhanced question generator that leverages LLM capabilities to create
    personalized follow-up questions based on a user's profile data and
    previous responses.
    
    This class focuses on generating high-quality, contextually relevant questions
    with specific emphasis on Indian financial context elements like tax benefits,
    SIPs, and other India-specific financial instruments.
    """
    
    # Question categories for Indian financial context
    INDIAN_FINANCIAL_CATEGORIES = [
        "tax_planning", 
        "investment_planning", 
        "retirement_planning", 
        "real_estate", 
        "insurance", 
        "family_financial_planning"
    ]
    
    # Map of financial context to specific question subtypes
    INDIAN_CONTEXT_QUESTION_TYPES = {
        "tax_planning": [
            "section_80c", 
            "section_80d", 
            "nps_benefits", 
            "tax_saving_instruments"
        ],
        "investment_planning": [
            "sip_strategy", 
            "mutual_funds", 
            "equity_strategy", 
            "gold_investment"
        ],
        "retirement_planning": [
            "ppf_epf_strategy", 
            "nps_strategy", 
            "pension_plans", 
            "early_retirement"
        ],
        "real_estate": [
            "property_tax", 
            "housing_loan_tax_benefits", 
            "reit_investment", 
            "rental_income"
        ],
        "insurance": [
            "health_insurance_adequacy", 
            "term_life_planning", 
            "critical_illness", 
            "family_floater"
        ],
        "family_financial_planning": [
            "education_planning", 
            "wedding_planning", 
            "intergenerational_wealth", 
            "joint_family_finances"
        ]
    }
    
    # Knowledge gap weights for scoring
    KNOWLEDGE_GAP_WEIGHTS = {
        "tax_planning": 0.85,
        "investment_planning": 0.80,
        "retirement_planning": 0.75,
        "real_estate": 0.65,
        "insurance": 0.70,
        "family_financial_planning": 0.60,
        "debt_management": 0.75,
        "emergency_planning": 0.80,
        "goal_planning": 0.70
    }
    
    # Question templates for Indian context
    INDIA_SPECIFIC_TEMPLATES = {
        "section_80c": [
            "Based on your income of ₹{income}, which Section 80C investments would be most suitable for your tax bracket?",
            "How are you currently utilizing the ₹1.5 lakh deduction available under Section 80C?",
            "Would you prefer to maximize your Section 80C benefits through ELSS funds, PPF, or other tax-saving instruments?"
        ],
        "sip_strategy": [
            "How regularly are you investing through SIPs (Systematic Investment Plans), and what is your monthly SIP amount?",
            "Would you prefer to increase your SIP contributions during market corrections to take advantage of rupee cost averaging?",
            "Have you considered step-up SIPs that increase your investment amount annually to match your income growth?"
        ],
        "ppf_epf_strategy": [
            "How are you balancing your PPF contributions versus other debt instruments in your portfolio?",
            "Are you aware of the tax benefits and sovereign guarantee advantages of your EPF/PPF investments?",
            "Would you consider maximizing your VPF (Voluntary Provident Fund) contributions for tax-free returns?"
        ],
        "health_insurance_adequacy": [
            "Considering the rising healthcare costs in India, do you think your current health insurance coverage of ₹{health_coverage} is adequate?",
            "Have you evaluated whether a super top-up health policy would be more cost-effective than increasing your base coverage?",
            "Does your health insurance plan cover the specific healthcare needs of metropolitan cities in India?"
        ],
        "real_estate_taxation": [
            "How are you planning to optimize the tax benefits on your home loan's principal (Section 80C) and interest (Section 24) components?",
            "Are you aware of the capital gains tax implications if you sell your property before 3 years versus after 3 years?",
            "Have you considered the tax benefits of joint home ownership with your spouse?"
        ]
    }
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the question generator with an LLM service.
        
        Args:
            llm_service: Optional LLM service for generating questions. If not provided,
                         a new service will be created.
        """
        self.llm_service = llm_service or LLMService()
        self.understanding_calculator = ProfileUnderstandingCalculator()
        self.question_cache = {}  # Cache previously generated questions by profile ID
        
        logging.info("QuestionGenerator initialized")
    
    def generate_personalized_questions(
        self, 
        profile: Dict[str, Any], 
        count: int = 5, 
        excluded_categories: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized follow-up questions based on the user's profile data.
        
        Args:
            profile: User profile data including previous answers and goals
            count: Number of questions to generate (default: 5)
            excluded_categories: Optional list of categories to exclude
            
        Returns:
            List of question objects with fields:
            - id: Unique question ID
            - question_id: Same as id (for compatibility)
            - text: Question text
            - category: Question category
            - type: Question type
            - input_type: Input type (text, select, number, etc.)
            - relevance_score: Score from 0-100 indicating question relevance
        """
        if not profile:
            logging.warning("Cannot generate questions for empty profile")
            return []
        
        # Initialize excluded categories if None
        excluded_categories = excluded_categories or []
        
        # Extract relevant data from profile
        profile_id = profile.get('id', 'unknown')
        answers = profile.get('answers', [])
        goals = self._extract_goals(profile)
        
        # Determine knowledge gaps by analyzing existing answers
        knowledge_gaps = self._identify_knowledge_gaps(profile)
        
        # Get existing questions to avoid duplicates
        existing_question_ids = [a.get('question_id', '') for a in answers]
        
        # Generate a batch of candidate questions
        timestamp = int(time.time())
        candidate_questions = []
        
        # Check if we have questions in the cache for this profile
        if profile_id in self.question_cache:
            # Get cached questions not already asked
            cached_questions = [q for q in self.question_cache[profile_id] 
                              if q.get('question_id') not in existing_question_ids]
            
            # If we have enough cached questions, use those
            if len(cached_questions) >= count:
                logging.info(f"Using {count} cached questions for profile {profile_id}")
                # Return the top N by relevance score
                sorted_questions = sorted(cached_questions, 
                                       key=lambda q: q.get('relevance_score', 0), 
                                       reverse=True)
                return sorted_questions[:count]
            
            # Otherwise, add cached questions to candidates and generate more
            candidate_questions.extend(cached_questions)
            logging.info(f"Using {len(cached_questions)} cached questions and generating more")
        
        # Determine how many new questions we need
        questions_needed = count - len(candidate_questions)
        
        # If we need more questions, generate them
        if questions_needed > 0:
            # Generate at least twice as many as needed so we can select the best ones
            new_questions = self._generate_questions_batch(
                profile, 
                knowledge_gaps, 
                goals, 
                count=questions_needed * 2, 
                existing_question_ids=existing_question_ids,
                excluded_categories=excluded_categories
            )
            
            # Score and filter the new questions
            scored_questions = self._score_and_prioritize_questions(
                new_questions, 
                knowledge_gaps, 
                profile
            )
            
            # Add the new questions to candidates
            candidate_questions.extend(scored_questions)
            
            # Update the cache with the new questions
            self._update_question_cache(profile_id, scored_questions)
        
        # Sort the candidates by relevance score and select the top N
        sorted_questions = sorted(candidate_questions, 
                               key=lambda q: q.get('relevance_score', 0), 
                               reverse=True)
        
        selected_questions = sorted_questions[:count]
        
        # Log summary of generated questions
        logging.info(f"Generated {len(selected_questions)} personalized questions for profile {profile_id}")
        
        # Ensure all questions have the right formats and fields
        formatted_questions = []
        for i, q in enumerate(selected_questions):
            formatted_question = self._format_question(q, i, timestamp)
            formatted_questions.append(formatted_question)
        
        return formatted_questions
    
    def _format_question(self, question: Dict[str, Any], index: int, timestamp: int) -> Dict[str, Any]:
        """Format a question with consistent fields and IDs."""
        # Generate a unique ID if not present
        if not question.get('id') or not question.get('question_id'):
            category = question.get('category', 'general')
            question_id = f"gen_question_{category}_{timestamp}_{index}"
            question['id'] = question_id
            question['question_id'] = question_id
        
        # Ensure all required fields are present
        question['input_type'] = question.get('input_type', 'text')
        question['required'] = question.get('required', False)
        question['type'] = question.get('type', 'next_level')
        
        # Ensure the text doesn't have odd formatting
        question['text'] = question.get('text', '').strip()
        
        return question
    
    def _generate_questions_batch(
        self, 
        profile: Dict[str, Any], 
        knowledge_gaps: Dict[str, float], 
        goals: List[Dict[str, Any]], 
        count: int, 
        existing_question_ids: List[str],
        excluded_categories: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate a batch of questions using LLM and templates.
        
        Args:
            profile: User profile
            knowledge_gaps: Dictionary of knowledge gaps by category
            goals: List of user's financial goals
            count: Number of questions to generate
            existing_question_ids: List of existing question IDs
            excluded_categories: Categories to exclude
            
        Returns:
            List of generated question dictionaries
        """
        generated_questions = []
        
        # Determine how many questions to generate for each source
        llm_question_count = int(count * 0.7)  # 70% from LLM
        template_question_count = count - llm_question_count  # Rest from templates
        
        # 1. Generate questions using the LLM service
        llm_questions = self._generate_llm_questions(
            profile, 
            knowledge_gaps, 
            llm_question_count, 
            existing_question_ids,
            excluded_categories
        )
        generated_questions.extend(llm_questions)
        
        # 2. Generate questions from templates
        template_questions = self._generate_template_questions(
            profile, 
            knowledge_gaps, 
            goals, 
            template_question_count,
            existing_question_ids,
            excluded_categories
        )
        generated_questions.extend(template_questions)
        
        # Return the combined list
        return generated_questions
    
    def _generate_llm_questions(
        self, 
        profile: Dict[str, Any], 
        knowledge_gaps: Dict[str, float], 
        count: int, 
        existing_question_ids: List[str],
        excluded_categories: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate questions using the LLM service.
        
        Args:
            profile: User profile
            knowledge_gaps: Dictionary of knowledge gaps by category
            count: Number of questions to generate
            existing_question_ids: List of existing question IDs
            excluded_categories: Categories to exclude
            
        Returns:
            List of generated question dictionaries from LLM
        """
        if not self.llm_service.enabled:
            logging.warning("LLM service is disabled, skipping LLM question generation")
            return []
        
        generated_questions = []
        
        # Sort knowledge gaps by value (largest first)
        sorted_gaps = sorted(knowledge_gaps.items(), key=lambda x: x[1], reverse=True)
        
        # Filter out excluded categories
        filtered_gaps = [(category, weight) for category, weight in sorted_gaps 
                        if category not in excluded_categories]
        
        # Determine how many categories to target based on count
        # Try to get at least 2 questions per category for the top N categories
        max_categories = max(1, min(len(filtered_gaps), count // 2))
        
        # For each priority category, generate questions
        for i, (category, gap_weight) in enumerate(filtered_gaps[:max_categories]):
            # Skip if we already have enough questions
            if len(generated_questions) >= count:
                break
                
            # Number of questions to generate for this category - more for higher-weighted gaps
            category_question_count = max(1, int(count * (gap_weight / sum(w for _, w in filtered_gaps[:max_categories]))))
            
            # Limit to remaining count needed
            category_question_count = min(category_question_count, count - len(generated_questions))
            
            # Create the context for the LLM
            profile_context = self._create_profile_context_for_llm(profile, category)
            
            # Construct the specific prompt for Indian financial context for this category
            india_specific_prompt = self._create_india_specific_prompt(category, profile)
            
            # Full LLM prompt combining profile context and India-specific elements
            prompt = f"""
            You are an expert financial advisor specializing in Indian personal finance. 
            Generate {category_question_count} personalized follow-up questions for a client based on their financial profile.
            
            Client profile summary:
            {profile_context}
            
            Focus on the '{category}' category, where I've identified a knowledge gap.
            
            India-specific context to consider:
            {india_specific_prompt}
            
            Requirements for generated questions:
            1. Questions should be specific, actionable, and directly relevant to Indian financial context
            2. Focus on revealing information that would help provide better financial advice
            3. Each question should address a distinct aspect of the '{category}' category
            4. Questions should feel conversational but professional
            5. Format the response as a JSON array of question objects with these fields:
               - text: The question text
               - category: '{category}'
               - input_type: The appropriate input type (text, select, number, etc.)
               - options: For 'select' input types, provide an array of choice objects with value and label fields
            
            Examples of good questions:
            - For tax_planning: "Given your income bracket, how much of your ₹1.5 lakh Section 80C limit are you currently utilizing?"
            - For investment_planning: "How comfortable are you with increasing your SIP contributions during market corrections?"
            - For retirement_planning: "What allocation do you maintain between EPF/PPF and market-linked retirement options like NPS?"
            
            Do NOT generate questions that:
            - Have already been asked ({', '.join(existing_question_ids[-5:]) if existing_question_ids else 'None'})
            - Are too generic (e.g., "What are your financial goals?")
            - Request basic information already in the profile
            
            Return ONLY a valid JSON array without any additional text.
            """
            
            # Call the LLM service
            try:
                response = self.llm_service._call_llm_api(prompt)
                
                # Parse the response
                try:
                    questions_data = json.loads(response)
                    
                    # Ensure it's a list
                    if isinstance(questions_data, dict) and "questions" in questions_data:
                        questions_data = questions_data["questions"]
                    elif not isinstance(questions_data, list):
                        questions_data = [questions_data]
                    
                    # Process each question
                    for q in questions_data:
                        # Skip if this doesn't look like a question
                        if not isinstance(q, dict) or "text" not in q:
                            continue
                            
                        # Add category if missing
                        if "category" not in q:
                            q["category"] = category
                            
                        # Add type
                        q["type"] = "next_level"
                        
                        # Add temporary relevance score based on gap weight (will be refined later)
                        q["relevance_score"] = int(gap_weight * 70)  # Base score from gap weight
                        
                        generated_questions.append(q)
                        
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse LLM response as JSON: {str(e)}")
                    # Try to extract a JSON array using regex as fallback
                    json_array_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
                    if json_array_match:
                        try:
                            # Add the brackets back
                            json_str = "[" + json_array_match.group(1) + "]"
                            questions_data = json.loads(json_str)
                            
                            # Process questions as above
                            for q in questions_data:
                                if not isinstance(q, dict) or "text" not in q:
                                    continue
                                q["category"] = q.get("category", category)
                                q["type"] = "next_level"
                                q["relevance_score"] = int(gap_weight * 70)
                                generated_questions.append(q)
                                
                        except json.JSONDecodeError:
                            logging.error(f"Failed to extract JSON array from LLM response via regex")
                
            except Exception as e:
                logging.error(f"Error generating LLM questions for category {category}: {str(e)}")
        
        # Return the generated questions, up to the requested count
        return generated_questions[:count]
    
    def _create_profile_context_for_llm(self, profile: Dict[str, Any], category: str) -> str:
        """Create a summary of the profile for the LLM prompt."""
        # Extract basic demographic and financial information
        age = self._extract_answer(profile, "demographics_age", "Not specified")
        income = self._extract_answer(profile, "financial_basics_annual_income", "Not specified")
        risk_tolerance = self._extract_answer(profile, "behavioral_risk_tolerance", "Moderate")
        savings = self._extract_answer(profile, "financial_basics_current_savings", "Not specified")
        expenses = self._extract_answer(profile, "financial_basics_monthly_expenses", "Not specified")
        dependents = self._extract_answer(profile, "demographics_dependents", "None")
        debt = self._extract_answer(profile, "assets_debts_total_debt", "Not specified")
        
        # Extract goals relevant to the category
        goals = self._extract_goals(profile)
        relevant_goals = []
        
        # Map categories to relevant goal types
        category_goal_mapping = {
            "tax_planning": ["retirement", "tax_saving", "wealth_accumulation"],
            "investment_planning": ["investment", "wealth_accumulation", "education", "retirement"],
            "retirement_planning": ["retirement", "early_retirement"],
            "real_estate": ["home_purchase", "property_investment", "real_estate"],
            "insurance": ["health", "protection", "family_security"],
            "family_financial_planning": ["education", "marriage", "legacy", "family_security"],
            "debt_management": ["debt_repayment", "loan", "mortgage"],
            "emergency_planning": ["emergency_fund", "contingency"],
            "goal_planning": ["all"]  # All goals are relevant
        }
        
        # Filter goals by relevance to the category
        relevant_goal_types = category_goal_mapping.get(category, [])
        if "all" in relevant_goal_types:
            relevant_goals = goals
        else:
            relevant_goals = [g for g in goals 
                            if any(goal_type in g.get("type", "").lower() 
                                  or goal_type in g.get("category", "").lower() 
                                  for goal_type in relevant_goal_types)]
        
        # Create the profile context
        context = f"""
        Age: {age}
        Annual Income: {income}
        Risk Tolerance: {risk_tolerance}
        Current Savings: {savings}
        Monthly Expenses: {expenses}
        Dependents: {dependents}
        Outstanding Debt: {debt}
        """
        
        # Add relevant goals
        if relevant_goals:
            context += "\nRelevant financial goals:\n"
            for i, goal in enumerate(relevant_goals[:3]):  # Limit to top 3 for brevity
                goal_text = f"- {goal.get('title', 'Unnamed goal')}: "
                goal_text += f"₹{goal.get('target_amount', 'Not specified')} "
                goal_text += f"by {goal.get('timeframe', 'Not specified')}"
                context += goal_text + "\n"
        
        # Add recent answers related to the category if available
        category_answers = self._get_category_related_answers(profile, category, max_answers=3)
        if category_answers:
            context += "\nRecent relevant responses:\n"
            for q_text, answer in category_answers:
                context += f"- Question: {q_text}\n  Response: {answer}\n"
        
        return context
    
    def _create_india_specific_prompt(self, category: str, profile: Dict[str, Any]) -> str:
        """Create India-specific prompt guidance for the category."""
        # Get the specific question types for this category
        question_types = self.INDIAN_CONTEXT_QUESTION_TYPES.get(category, [])
        
        india_specific_context = {
            "tax_planning": """
            - Section 80C offers tax deductions up to ₹1.5 lakh for investments in PPF, ELSS, etc.
            - Section 80D offers deductions for health insurance premiums
            - NPS offers additional tax benefits up to ₹50,000 under Section 80CCD(1B)
            - Tax saving should be considered in the context of overall financial plan, not in isolation
            """,
            
            "investment_planning": """
            - SIPs (Systematic Investment Plans) are the most popular investment vehicle in India
            - Market-linked investments like equity mutual funds typically offer better long-term returns
            - Gold remains an important cultural and investment asset in many Indian portfolios
            - Consider index funds and ETFs as low-cost alternatives to actively managed funds
            """,
            
            "retirement_planning": """
            - EPF (Employee Provident Fund) forms the core retirement savings for many Indian employees
            - NPS (National Pension System) offers market-linked returns with tax benefits
            - PPF (Public Provident Fund) provides tax-free returns with government backing
            - Most Indians lack adequate retirement planning beyond mandatory EPF contributions
            """,
            
            "real_estate": """
            - Real estate remains a preferred asset class in India, often overweighted in portfolios
            - Housing loans offer significant tax benefits under Section 24 and Section 80C
            - REIT investments are a newer alternative for real estate exposure without direct ownership
            - Property tax and maintenance costs are often underestimated in homeownership decisions
            """,
            
            "insurance": """
            - Health insurance coverage is often inadequate given rising medical costs in India
            - Term insurance is underutilized despite being the most cost-effective protection
            - Critical illness coverage is increasingly important given lifestyle disease trends
            - Family floater policies may be more cost-effective than individual policies
            """,
            
            "family_financial_planning": """
            - Education expenses are rising rapidly, especially for professional degrees
            - Marriage expenses remain significant in Indian culture and require planning
            - Joint family dynamics often impact financial decision-making
            - Intergenerational financial support is common in Indian families
            """
        }
        
        # Get the basic context for this category
        context = india_specific_context.get(category, "Focus on Indian financial context for this category.")
        
        # Add specific guidance based on profile attributes
        age = self._extract_answer(profile, "demographics_age", None)
        if age:
            if category == "retirement_planning" and int(age) > 45:
                context += "\n- For clients over 45, catch-up retirement strategies are especially important."
            elif category == "tax_planning" and int(age) < 30:
                context += "\n- For young professionals, tax planning should balance immediate savings with long-term growth potential."
        
        # Add guidance based on income
        income = self._extract_answer(profile, "financial_basics_annual_income", None)
        if income:
            try:
                income_value = float(income.replace('₹', '').replace(',', ''))
                if category == "tax_planning" and income_value > 1000000:  # 10 lakhs+
                    context += "\n- High-income individuals may benefit from sophisticated tax planning beyond standard deductions."
                elif category == "investment_planning" and income_value < 500000:  # Under 5 lakhs
                    context += "\n- For modest incomes, focus on establishing emergency funds and basic SIPs before complex investments."
            except (ValueError, AttributeError):
                pass  # Unable to parse income, skip this customization
        
        # Return the combined context
        return context.strip()
    
    def _generate_template_questions(
        self, 
        profile: Dict[str, Any], 
        knowledge_gaps: Dict[str, float], 
        goals: List[Dict[str, Any]], 
        count: int,
        existing_question_ids: List[str],
        excluded_categories: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate questions using pre-defined templates.
        
        Args:
            profile: User profile
            knowledge_gaps: Dictionary of knowledge gaps by category
            goals: List of user's financial goals
            count: Number of questions to generate
            existing_question_ids: List of existing question IDs
            excluded_categories: Categories to exclude
            
        Returns:
            List of generated question dictionaries from templates
        """
        generated_questions = []
        
        # Sort knowledge gaps by value (largest first)
        sorted_gaps = sorted(knowledge_gaps.items(), key=lambda x: x[1], reverse=True)
        
        # Filter out excluded categories
        filtered_gaps = [(category, weight) for category, weight in sorted_gaps 
                        if category not in excluded_categories]
        
        # For each gap, try to generate a template question
        for category, gap_weight in filtered_gaps:
            # Skip if we already have enough questions
            if len(generated_questions) >= count:
                break
            
            # Get the question types for this category
            question_types = self.INDIAN_CONTEXT_QUESTION_TYPES.get(category, [])
            
            if not question_types:
                continue
                
            # Try each question type
            for q_type in question_types:
                # Skip if we already have enough questions
                if len(generated_questions) >= count:
                    break
                    
                # Get templates for this question type
                templates = self.INDIA_SPECIFIC_TEMPLATES.get(q_type, [])
                
                if not templates:
                    continue
                    
                # Select a template
                template = templates[hash(str(profile.get('id', ''))) % len(templates)]
                
                # Personalize the template
                question_text = self._personalize_template(template, profile)
                
                # Create question object
                question = {
                    "text": question_text,
                    "category": category,
                    "type": "next_level",
                    "input_type": "text",  # Default to text input
                    "relevance_score": int(gap_weight * 60)  # Base score from gap weight
                }
                
                # For some specific question types, use different input types
                if "choose" in question_text.lower() or "prefer" in question_text.lower():
                    question["input_type"] = "select"
                    # Add options based on the question type
                    if q_type == "section_80c":
                        question["options"] = [
                            {"value": "ppf", "label": "Public Provident Fund (PPF)"},
                            {"value": "elss", "label": "Equity Linked Savings Scheme (ELSS)"},
                            {"value": "insurance", "label": "Life Insurance Premium"},
                            {"value": "home_loan", "label": "Home Loan Principal Repayment"},
                            {"value": "nsc", "label": "National Savings Certificate (NSC)"}
                        ]
                    elif q_type == "sip_strategy":
                        question["options"] = [
                            {"value": "monthly", "label": "Monthly SIPs"},
                            {"value": "quarterly", "label": "Quarterly SIPs"},
                            {"value": "lumpsum", "label": "Lumpsum with occasional top-ups"},
                            {"value": "step_up", "label": "Step-up SIPs (increasing annually)"}
                        ]
                
                # Add the question to the list
                generated_questions.append(question)
        
        return generated_questions[:count]
    
    def _personalize_template(self, template: str, profile: Dict[str, Any]) -> str:
        """Personalize a question template with profile data."""
        # Extract values for common placeholders
        placeholders = {
            "income": self._extract_answer(profile, "financial_basics_annual_income", "your current income"),
            "age": self._extract_answer(profile, "demographics_age", "your age"),
            "health_coverage": self._extract_answer(profile, "insurance_health_coverage", "your current health coverage"),
            "retirement_age": self._extract_answer(profile, "retirement_target_age", "your target retirement age"),
            "risk_tolerance": self._extract_answer(profile, "behavioral_risk_tolerance", "your risk tolerance"),
            "monthly_investment": self._extract_answer(profile, "investment_monthly_amount", "your monthly investment amount")
        }
        
        # Format the template with extracted values
        personalized_text = template
        for key, value in placeholders.items():
            placeholder = "{" + key + "}"
            if placeholder in personalized_text:
                personalized_text = personalized_text.replace(placeholder, str(value))
        
        return personalized_text
    
    def _score_and_prioritize_questions(
        self, 
        questions: List[Dict[str, Any]], 
        knowledge_gaps: Dict[str, float], 
        profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Score and prioritize questions based on relevance to the user's situation.
        
        Args:
            questions: List of candidate questions
            knowledge_gaps: Dictionary of knowledge gaps by category
            profile: User profile
            
        Returns:
            List of scored questions with relevance_score field
        """
        scored_questions = []
        
        # Get understanding level to determine what knowledge is most helpful
        understanding_level = self.understanding_calculator.calculate_understanding_level(profile)
        
        # Get goals and their priorities
        goals = self._extract_goals(profile)
        goal_types = [g.get("type", "").lower() for g in goals]
        high_priority_goals = [g for g in goals if g.get("priority", "").lower() == "high"]
        
        # For each question, calculate a relevance score (0-100)
        for question in questions:
            # Start with the base score (0-70) from knowledge gaps
            base_score = question.get("relevance_score", 0)
            
            # Get the category weight multiplier
            category = question.get("category", "")
            category_weight = knowledge_gaps.get(category, 0.5)  # Default to 0.5 if no gap info
            
            # Adjust score based on goal relevance (0-15)
            goal_relevance = 0
            question_text = question.get("text", "").lower()
            
            # Map categories to related goal keywords
            category_goal_keywords = {
                "tax_planning": ["tax", "section 80", "deduction", "saving"],
                "investment_planning": ["invest", "return", "sip", "mutual fund", "equity"],
                "retirement_planning": ["retire", "pension", "old age", "corpus", "ppf", "epf"],
                "real_estate": ["home", "house", "property", "rent", "mortgage"],
                "insurance": ["insurance", "cover", "premium", "health", "life"],
                "family_financial_planning": ["family", "child", "education", "marriage"]
            }
            
            # Check if question relates to high-priority goals
            keywords = category_goal_keywords.get(category, [])
            for keyword in keywords:
                if keyword in question_text:
                    # Boost if this keyword relates to high-priority goals
                    for goal in high_priority_goals:
                        goal_text = (goal.get("title", "") + " " + goal.get("description", "")).lower()
                        if keyword in goal_text:
                            goal_relevance += 5  # Significant boost for high-priority goal match
                        else:
                            goal_relevance += 2  # Smaller boost for general keyword match
            
            # Cap goal relevance boost at 15
            goal_relevance = min(15, goal_relevance)
            
            # Adjust score based on timing within flow (0-15)
            timing_score = 0
            if understanding_level == "RED" and category in ["emergency_planning", "financial_basics"]:
                timing_score += 15  # For beginners, prioritize basic financial understanding
            elif understanding_level == "AMBER" and category in ["tax_planning", "investment_planning"]:
                timing_score += 15  # At amber level, tax and investment planning becomes relevant
            elif understanding_level in ["YELLOW", "GREEN"] and category in ["retirement_planning", "family_financial_planning"]:
                timing_score += 15  # At higher levels, longer-term planning becomes more relevant
            
            # Final score is weighted combination
            final_score = base_score + goal_relevance + timing_score
            
            # Normalize to 0-100 range and ensure it's an integer
            normalized_score = min(100, max(0, int(final_score)))
            
            # Add score to question
            question["relevance_score"] = normalized_score
            scored_questions.append(question)
        
        # Sort by relevance score (highest first)
        return sorted(scored_questions, key=lambda q: q.get("relevance_score", 0), reverse=True)
    
    def _identify_knowledge_gaps(self, profile: Dict[str, Any]) -> Dict[str, float]:
        """
        Identify knowledge gaps in the user's profile.
        
        Args:
            profile: User profile
            
        Returns:
            Dictionary mapping categories to gap weights (0.0-1.0)
        """
        answers = profile.get('answers', [])
        
        # Define category-to-question mapping
        category_questions = {
            "tax_planning": ["tax_planning", "tax_saving", "tax_strategy", "section_80c"],
            "investment_planning": ["investment_strategy", "investment_types", "asset_allocation"],
            "retirement_planning": ["retirement_planning", "retirement_savings", "pension_plans"],
            "real_estate": ["real_estate", "property", "home_loan", "housing"],
            "insurance": ["insurance_health", "insurance_life", "protection_planning"],
            "family_financial_planning": ["education_planning", "marriage_planning", "estate_planning"],
            "debt_management": ["debt_strategy", "loan_management", "mortgage"],
            "emergency_planning": ["emergency_fund", "contingency_planning"],
            "goal_planning": ["financial_goals", "goal_strategy", "goal_timeframe"]
        }
        
        # Count answered questions by category
        category_counts = {category: 0 for category in category_questions}
        total_possible = {category: len(question_keywords) for category, question_keywords in category_questions.items()}
        
        # Count answered questions
        for answer in answers:
            question_id = answer.get('question_id', '').lower()
            
            for category, question_keywords in category_questions.items():
                if any(keyword in question_id for keyword in question_keywords):
                    category_counts[category] += 1
        
        # Calculate gaps as 1 - (answered/total)
        gaps = {}
        for category, count in category_counts.items():
            possible = total_possible[category]
            if possible > 0:
                gap = 1.0 - (min(count, possible) / possible)
                # Apply weight from knowledge gap weights
                weighted_gap = gap * self.KNOWLEDGE_GAP_WEIGHTS.get(category, 0.7)
                gaps[category] = weighted_gap
        
        # Ensure all categories have a gap value
        for category in category_questions:
            if category not in gaps:
                gaps[category] = self.KNOWLEDGE_GAP_WEIGHTS.get(category, 0.7)
                
        return gaps
    
    def _extract_goals(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract financial goals from profile."""
        # Check if goals are directly in the profile
        if 'goals' in profile and isinstance(profile['goals'], list):
            return profile['goals']
            
        # Otherwise try to extract from answers
        goals = []
        answers = profile.get('answers', [])
        
        for answer in answers:
            q_id = answer.get('question_id', '')
            if q_id.startswith('goals_') and 'answer' in answer:
                if isinstance(answer['answer'], list):
                    # This might be a list of goal names/types
                    goals.extend([{'type': goal_type, 'title': goal_type.replace('_', ' ').title()} 
                                 for goal_type in answer['answer']])
                elif isinstance(answer['answer'], dict):
                    # This might be a structured goal
                    goals.append(answer['answer'])
        
        return goals
    
    def _extract_answer(self, profile: Dict[str, Any], question_id: str, default: Any = None) -> Any:
        """Extract an answer for a specific question from the profile."""
        answers = profile.get('answers', [])
        
        for answer in answers:
            if answer.get('question_id') == question_id and 'answer' in answer:
                return answer['answer']
                
        return default
    
    def _get_category_related_answers(
        self, 
        profile: Dict[str, Any], 
        category: str, 
        max_answers: int = 3
    ) -> List[Tuple[str, Any]]:
        """Get recent answers related to a specific category."""
        answers = profile.get('answers', [])
        category_related = []
        
        # Map each category to related keywords
        category_keywords = {
            "tax_planning": ["tax", "deduction", "saving"],
            "investment_planning": ["invest", "portfolio", "return", "sip"],
            "retirement_planning": ["retire", "pension", "old age"],
            "real_estate": ["home", "house", "property", "rent"],
            "insurance": ["insurance", "cover", "premium", "health"],
            "family_financial_planning": ["family", "child", "education", "marriage"]
        }
        
        keywords = category_keywords.get(category, [])
        if not keywords:
            return []
            
        # Find answers with questions containing these keywords
        for answer in answers:
            q_text = answer.get('text', '')  # Question text
            a_value = answer.get('answer', '')  # Answer value
            
            # Skip empty answers
            if not a_value:
                continue
                
            # Check if question text contains any of the keywords
            if any(keyword in q_text.lower() for keyword in keywords):
                category_related.append((q_text, a_value))
                
            # If we have enough answers, stop
            if len(category_related) >= max_answers:
                break
                
        return category_related
    
    def _update_question_cache(self, profile_id: str, questions: List[Dict[str, Any]]) -> None:
        """Update the question cache with new questions."""
        # Initialize the cache for this profile if it doesn't exist
        if profile_id not in self.question_cache:
            self.question_cache[profile_id] = []
            
        # Add questions to the cache
        self.question_cache[profile_id].extend(questions)
        
        # Trim the cache if it gets too large (keep top 20 by relevance score)
        if len(self.question_cache[profile_id]) > 20:
            self.question_cache[profile_id] = sorted(
                self.question_cache[profile_id],
                key=lambda q: q.get('relevance_score', 0),
                reverse=True
            )[:20]
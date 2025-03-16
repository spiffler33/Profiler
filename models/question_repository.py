import os
import json
import logging

class QuestionRepository:
    """
    Repository for all question definitions, organized by type and category.
    Provides lookup methods and manages question metadata.
    """
    
    def __init__(self):
        """Initialize the question repository with core, next-level, behavioral, and goal questions"""
        self.questions = {}
        logging.basicConfig(level=logging.INFO)
        
        # Initialize question tiers
        self.init_core_questions()
        self.init_next_level_questions()
        self.init_behavioral_questions()
        self.init_goal_questions()
    
    def init_core_questions(self):
        """Initialize the core questions based on the specification"""
        
        # DEMOGRAPHICS CATEGORY
        self.add_question({
            "id": "demographics_age",
            "text": "What is your age?",
            "type": "core",
            "category": "demographics",
            "input_type": "number",
            "min": 18,
            "max": 100,
            "required": True,
            "order": 1,
            "help_text": "Your age helps determine investment horizon and risk capacity"
        })
        
        self.add_question({
            "id": "demographics_employment_type",
            "text": "What is your employment type?",
            "type": "core",
            "category": "demographics",
            "input_type": "select",
            "options": ["Full-time employee", "Part-time employee", "Self-employed", "Business owner", "Retired", "Unemployed", "Student"],
            "required": True,
            "order": 2,
            "help_text": "Your employment type affects income stability and emergency fund requirements"
        })
        
        self.add_question({
            "id": "demographics_dependents",
            "text": "How many dependents do you have?",
            "type": "core",
            "category": "demographics",
            "input_type": "number",
            "min": 0,
            "max": 20,
            "required": True,
            "order": 3,
            "help_text": "Dependents influence your insurance needs and protection planning"
        })
        
        self.add_question({
            "id": "demographics_health_status",
            "text": "How would you rate your overall health?",
            "type": "core",
            "category": "demographics",
            "input_type": "select",
            "options": ["Excellent", "Good", "Fair", "Poor"],
            "required": True,
            "order": 4,
            "help_text": "Your health status affects emergency fund sizing and insurance requirements"
        })
        
        self.add_question({
            "id": "demographics_risk_appetite",
            "text": "How would you describe your risk tolerance?",
            "type": "core",
            "category": "demographics",
            "input_type": "select",
            "options": ["Conservative (-1)", "Moderate (0)", "Aggressive (1)"],
            "required": True,
            "order": 5,
            "help_text": "Your personal risk tolerance on a scale from conservative to aggressive"
        })
        
        self.add_question({
            "id": "demographics_financial_maturity",
            "text": "How would you rate your financial knowledge?",
            "type": "core",
            "category": "demographics",
            "input_type": "select",
            "options": ["Beginner", "Intermediate", "Advanced", "Expert"],
            "required": True,
            "order": 6,
            "help_text": "Your financial knowledge level helps determine appropriate recommendations"
        })
        
        self.add_question({
            "id": "demographics_market_outlook",
            "text": "What is your outlook on the market for the next 12 months?",
            "type": "core",
            "category": "demographics",
            "input_type": "select",
            "options": ["Bearish (Negative)", "Neutral", "Bullish (Positive)"],
            "required": True,
            "order": 7,
            "help_text": "Your personal view on market conditions"
        })
        
        self.add_question({
            "id": "demographics_location",
            "text": "Where are you located?",
            "type": "core",
            "category": "demographics",
            "input_type": "text",
            "required": True,
            "order": 8,
            "help_text": "Your location provides geographic context for recommendations"
        })
        
        # FINANCIAL BASICS CATEGORY
        self.add_question({
            "id": "financial_basics_monthly_expenses",
            "text": "What are your average monthly expenses?",
            "type": "core",
            "category": "financial_basics",
            "input_type": "number",
            "min": 0,
            "required": True,
            "order": 1,
            "help_text": "Your monthly expenses are the foundation for emergency fund calculation"
        })
        
        self.add_question({
            "id": "financial_basics_savings_percentage",
            "text": "What percentage of your income do you save monthly?",
            "type": "core",
            "category": "financial_basics",
            "input_type": "number",
            "min": 0,
            "max": 100,
            "required": True,
            "order": 2,
            "help_text": "Your savings rate is a key indicator of financial health"
        })
        
        self.add_question({
            "id": "financial_basics_current_savings",
            "text": "What is the total value of your current savings and investments?",
            "type": "core",
            "category": "financial_basics",
            "input_type": "number",
            "min": 0,
            "required": True,
            "order": 3,
            "help_text": "Your current savings are the starting point for financial planning"
        })
        
        # ASSETS AND DEBTS CATEGORY
        self.add_question({
            "id": "assets_debts_total_debt",
            "text": "What is your total outstanding debt?",
            "type": "core",
            "category": "assets_and_debts",
            "input_type": "number",
            "min": 0,
            "required": True,
            "order": 1,
            "help_text": "Your total debt helps assess your financial obligations"
        })
        
        self.add_question({
            "id": "assets_debts_housing_loan",
            "text": "Do you have a housing loan?",
            "type": "core",
            "category": "assets_and_debts",
            "input_type": "radio",
            "options": ["Yes", "No"],
            "required": True,
            "order": 2,
            "help_text": "Housing loans are treated differently from other debts"
        })
        
        # SPECIAL CASES CATEGORY
        self.add_question({
            "id": "special_cases_business_value",
            "text": "If you own a business, what is its approximate value?",
            "type": "core",
            "category": "special_cases",
            "input_type": "number",
            "min": 0,
            "required": False,
            "order": 1,
            "help_text": "Business value is important for business owners",
            "depends_on": {
                "question_id": "demographics_employment_type",
                "value": "Business owner"
            }
        })
        
        self.add_question({
            "id": "special_cases_real_estate_value",
            "text": "What is the total value of real estate you own?",
            "type": "core",
            "category": "special_cases",
            "input_type": "number",
            "min": 0,
            "required": False,
            "order": 2,
            "help_text": "Real estate value helps assess your total assets",
            "depends_on": {
                "question_id": "assets_debts_housing_loan",
                "value": "Yes"
            }
        })
        
        self.add_question({
            "id": "special_cases_real_estate_type",
            "text": "What type of real estate do you own?",
            "type": "core",
            "category": "special_cases",
            "input_type": "select",
            "options": ["None", "Primary residence", "Investment property", "Vacation home", "Multiple properties"],
            "required": False,
            "order": 3,
            "help_text": "The type of real estate affects how it's considered in your financial plan",
            "depends_on": {
                "question_id": "special_cases_real_estate_value",
                "value_condition": "greater_than_zero"
            }
        })
        
        logging.info(f"Initialized core questions: {len(self.questions)}")
        
    def init_next_level_questions(self):
        """Initialize next-level questions that build upon core answers"""
        
        # DEMOGRAPHICS NEXT-LEVEL QUESTIONS
        self.add_question({
            "id": "next_level_demographics_dependents",
            "text": "You mentioned having dependents. Could you clarify their relationship to you and how financially dependent they are on your income?",
            "type": "next_level",
            "category": "demographics",
            "input_type": "text",
            "required": False,
            "order": 101,
            "help_text": "Understanding the nature of your dependencies helps tailor protection planning",
            "related_to": "demographics_dependents",
            "depends_on": {
                "question_id": "demographics_dependents",
                "value_condition": "greater_than_zero"
            }
        })
        
        self.add_question({
            "id": "next_level_demographics_health",
            "text": "You indicated your health status is not optimal. Does this affect your ability to work, or require ongoing medical expenses?",
            "type": "next_level",
            "category": "demographics",
            "input_type": "select",
            "options": ["No impact", "Minor impact", "Moderate impact", "Significant impact"],
            "required": False,
            "order": 102,
            "help_text": "Health impacts on work and expenses are important financial considerations",
            "related_to": "demographics_health_status",
            "depends_on": {
                "question_id": "demographics_health_status",
                "values": ["Fair", "Poor"]
            }
        })
        
        self.add_question({
            "id": "next_level_demographics_employment",
            "text": "As someone with variable employment, how stable would you say your income has been over the past 2 years?",
            "type": "next_level",
            "category": "demographics",
            "input_type": "select",
            "options": ["Very stable", "Mostly stable", "Somewhat variable", "Highly variable"],
            "required": False,
            "order": 103,
            "help_text": "Income stability affects emergency fund requirements and financial planning",
            "related_to": "demographics_employment_type",
            "depends_on": {
                "question_id": "demographics_employment_type",
                "values": ["Self-employed", "Business owner", "Part-time employee"]
            }
        })
        
        # FINANCIAL BASICS NEXT-LEVEL QUESTIONS
        self.add_question({
            "id": "next_level_financial_savings_distribution",
            "text": "Could you share roughly how your current savings are distributed? What percentage is in fixed deposits, equity, or other investments?",
            "type": "next_level",
            "category": "financial_basics",
            "input_type": "text",
            "required": False,
            "order": 101,
            "help_text": "Understanding your current asset allocation helps assess portfolio diversification",
            "related_to": "financial_basics_current_savings",
            "depends_on": {
                "question_id": "financial_basics_current_savings",
                "value_condition": "greater_than_zero"
            }
        })
        
        self.add_question({
            "id": "next_level_financial_expenses_essential",
            "text": "Of your monthly expenses, approximately what percentage would you consider essential (housing, food, utilities)?",
            "type": "next_level",
            "category": "financial_basics",
            "input_type": "number",
            "min": 0,
            "max": 100,
            "required": False,
            "order": 102,
            "help_text": "Understanding essential vs. discretionary expenses helps with budgeting and emergency planning",
            "related_to": "financial_basics_monthly_expenses"
        })
        
        self.add_question({
            "id": "next_level_financial_savings_goal",
            "text": "Do you have a specific savings goal or target amount you're working towards?",
            "type": "next_level",
            "category": "financial_basics",
            "input_type": "text",
            "required": False,
            "order": 103,
            "help_text": "Having clear savings goals helps with financial planning and motivation",
            "related_to": "financial_basics_savings_percentage"
        })
        
        # ASSETS AND DEBTS NEXT-LEVEL QUESTIONS
        self.add_question({
            "id": "next_level_assets_debts_housing_loan",
            "text": "Regarding your home loan, how would you rate the sellability of your property if needed? Is it in a high-demand location?",
            "type": "next_level",
            "category": "assets_and_debts",
            "input_type": "select",
            "options": ["Highly sellable", "Moderately sellable", "Difficult to sell", "Very difficult to sell"],
            "required": False,
            "order": 101,
            "help_text": "Property liquidity is an important consideration in financial resilience",
            "related_to": "assets_debts_housing_loan",
            "depends_on": {
                "question_id": "assets_debts_housing_loan",
                "value": "Yes"
            }
        })
        
        self.add_question({
            "id": "next_level_assets_debts_types",
            "text": "What types of debts do you currently have, and what are their approximate interest rates?",
            "type": "next_level",
            "category": "assets_and_debts",
            "input_type": "text",
            "required": False,
            "order": 102,
            "help_text": "Understanding debt types and interest rates helps prioritize debt repayment strategies",
            "related_to": "assets_debts_total_debt",
            "depends_on": {
                "question_id": "assets_debts_total_debt",
                "value_condition": "greater_than_zero"
            }
        })
        
        # SPECIAL CASES NEXT-LEVEL QUESTIONS
        self.add_question({
            "id": "next_level_special_cases_business",
            "text": "What percentage of your net worth is tied to your business assets?",
            "type": "next_level",
            "category": "special_cases",
            "input_type": "number",
            "min": 0,
            "max": 100,
            "required": False,
            "order": 101,
            "help_text": "Understanding business concentration in your net worth helps assess diversification",
            "related_to": "special_cases_business_value",
            "depends_on": {
                "question_id": "special_cases_business_value",
                "value_condition": "greater_than_zero"
            }
        })
        
        self.add_question({
            "id": "next_level_special_cases_real_estate",
            "text": "Do you plan to hold this property long-term or sell it within the next 5 years?",
            "type": "next_level",
            "category": "special_cases",
            "input_type": "select",
            "options": ["Hold long-term", "Likely sell within 5 years", "Undecided"],
            "required": False,
            "order": 102,
            "help_text": "Your real estate holding intentions affect overall investment strategy",
            "related_to": "special_cases_real_estate_value",
            "depends_on": {
                "question_id": "special_cases_real_estate_value",
                "value_condition": "greater_than_zero"
            }
        })
        
        logging.info(f"Initialized next-level questions: {len(self.questions) - len(self.get_core_questions())}")
    
    def init_behavioral_questions(self):
        """Initialize behavioral questions to assess financial psychology and biases"""
        
        # LOSS AVERSION QUESTIONS
        self.add_question({
            "id": "behavioral_loss_aversion_1",
            "text": "How much do you agree with this statement: 'I feel the pain of financial losses more strongly than the pleasure of equivalent gains.'",
            "type": "behavioral",
            "category": "financial_psychology",
            "input_type": "slider",
            "min": 1,
            "max": 10,
            "step": 1,
            "required": False,
            "order": 1,
            "help_text": "This helps assess your loss aversion, which can impact investment decisions",
            "behavioral_trait": "loss_aversion"
        })
        
        # FOMO (FEAR OF MISSING OUT) QUESTIONS
        self.add_question({
            "id": "behavioral_fomo_1",
            "text": "When you hear about others making significant gains in an investment that you don't own, how likely are you to feel you should invest in it too?",
            "type": "behavioral",
            "category": "financial_psychology",
            "input_type": "slider",
            "min": 1,
            "max": 10,
            "step": 1,
            "required": False,
            "order": 2,
            "help_text": "This helps assess your susceptibility to FOMO (fear of missing out) in investing",
            "behavioral_trait": "fomo"
        })
        
        # OVERCONFIDENCE QUESTIONS
        self.add_question({
            "id": "behavioral_overconfidence_1",
            "text": "When making investment decisions, how confident are you in your ability to outperform the market?",
            "type": "behavioral",
            "category": "financial_psychology",
            "input_type": "slider",
            "min": 1,
            "max": 10,
            "step": 1,
            "required": False, 
            "order": 3,
            "help_text": "This helps assess your level of confidence in investment decision-making",
            "behavioral_trait": "overconfidence"
        })
        
        # RISK TOLERANCE IN PRACTICE
        self.add_question({
            "id": "behavioral_risk_practice_1",
            "text": "If your investment portfolio suddenly dropped 20% in value, what would you most likely do?",
            "type": "behavioral",
            "category": "financial_psychology",
            "input_type": "select",
            "options": ["Sell everything to prevent further losses", "Sell some investments to reduce risk", "Do nothing and wait for recovery", "Buy more while prices are low"],
            "required": False,
            "order": 4,
            "help_text": "This helps assess how you actually respond to market downturns, beyond theoretical risk tolerance",
            "behavioral_trait": "practical_risk_tolerance"
        })
        
        # EMOTIONAL INVESTING
        self.add_question({
            "id": "behavioral_emotional_investing_1",
            "text": "How much do your emotions (fear, excitement, anxiety, etc.) typically influence your financial decisions?",
            "type": "behavioral",
            "category": "financial_psychology",
            "input_type": "slider",
            "min": 1,
            "max": 10,
            "step": 1,
            "required": False,
            "order": 5,
            "help_text": "This helps assess the impact of emotions on your financial decision-making",
            "behavioral_trait": "emotional_investing"
        })
        
        # DISCIPLINE AND CONSISTENCY
        self.add_question({
            "id": "behavioral_discipline_1",
            "text": "How consistently do you stick to your financial plan during market volatility?",
            "type": "behavioral",
            "category": "financial_psychology",
            "input_type": "slider",
            "min": 1,
            "max": 10,
            "step": 1,
            "required": False,
            "order": 6,
            "help_text": "This helps assess your financial discipline and consistency",
            "behavioral_trait": "discipline"
        })
        
        # INFORMATION PROCESSING
        self.add_question({
            "id": "behavioral_information_1",
            "text": "When making financial decisions, how much research do you typically conduct before acting?",
            "type": "behavioral",
            "category": "financial_psychology",
            "input_type": "select",
            "options": ["Minimal - I often make quick decisions", "Basic - I review some information", "Moderate - I gather various perspectives", "Extensive - I thoroughly research all options"],
            "required": False,
            "order": 7,
            "help_text": "This helps assess your information processing approach to financial decisions",
            "behavioral_trait": "information_processing"
        })
        
        logging.info(f"Initialized behavioral questions: {len(self.get_questions_by_type('behavioral'))}")
    
    def init_goal_questions(self):
        """Initialize goal-related questions to establish financial goals"""
        
        # EMERGENCY FUND QUESTIONS
        self.add_question({
            "id": "goals_emergency_fund_exists",
            "text": "Do you have an emergency fund set aside for unexpected expenses?",
            "type": "goal",
            "category": "goals",
            "input_type": "radio",
            "options": ["Yes", "No", "Partially"],
            "required": False,
            "order": 1,
            "help_text": "In India, financial experts recommend an emergency fund covering 6-9 months of expenses, compared to the global standard of 3-6 months. This is due to factors like healthcare costs and employment market conditions."
        })
        
        self.add_question({
            "id": "goals_emergency_fund_months",
            "text": "How many months of expenses does your emergency fund cover?",
            "type": "goal",
            "category": "goals",
            "input_type": "select",
            "options": ["Less than 1 month", "1-2 months", "3-4 months", "5-6 months", "6-9 months", "More than 9 months"],
            "required": False,
            "order": 2,
            "help_text": "In India, a minimum of 6 months is typically recommended, with 9 months being ideal for most situations. This helps assess the adequacy of your emergency fund.",
            "depends_on": {
                "question_id": "goals_emergency_fund_exists",
                "values": ["Yes", "Partially"]
            }
        })
        
        self.add_question({
            "id": "goals_emergency_fund_education",
            "text": "Emergency Fund Guidelines for India",
            "type": "goal",
            "category": "goals",
            "input_type": "educational",
            "required": False,
            "order": 3,
            "educational_content": """
                <h3>Emergency Fund Guidelines for India</h3>
                
                <p>In India, financial experts recommend maintaining an emergency fund that covers <strong>6-9 months</strong> 
                of your regular monthly expenses. This differs from the global standard of 3-6 months due to several factors 
                specific to the Indian context:</p>
                
                <ul>
                    <li><strong>Healthcare costs:</strong> Lower insurance penetration and higher out-of-pocket 
                    medical expenses necessitate larger emergency reserves</li>
                    <li><strong>Employment conditions:</strong> Job transitions can take longer, and notice periods 
                    and severance packages may vary significantly</li>
                    <li><strong>Family support systems:</strong> Many Indians have financial responsibilities for 
                    extended family members</li>
                    <li><strong>Economic volatility:</strong> Inflationary pressures and economic cycles can impact 
                    expenses unpredictably</li>
                </ul>
                
                <p>Having an adequate emergency fund is typically considered the foundation of financial security, 
                as it provides protection against unexpected expenses without derailing your long-term financial plans.</p>
            """,
            "help_text": "DISCLAIMER: We are only a profiler, not providing recommendations. The following information is for educational purposes only, based on financial literature, not personalized advice. We are not RBI/SEBI regulated financial advisors. Your specific situation may require different amounts.",
            "depends_on": {
                "question_id": "financial_basics_monthly_expenses",
                "value_condition": "greater_than_zero"
            }
        })
        
        self.add_question({
            "id": "goals_emergency_fund_calculation",
            "text": "Your Emergency Fund Calculation",
            "type": "goal",
            "category": "goals",
            "input_type": "educational",
            "required": False,
            "order": 3.5,
            "educational_content": """
                <h3>Your Personalized Emergency Fund Calculation</h3>
                
                <p>Based on the financial guidelines for India and your reported monthly expenses, 
                we've calculated recommended emergency fund targets below. These are general 
                guidelines that serve as a starting point - your specific needs may vary based on 
                your individual circumstances.</p>
            """,
            "help_text": "Based on your monthly expenses, we've calculated recommended emergency fund amounts. This is not personalized financial advice but a general rule of thumb used in financial planning.",
            "depends_on": {
                "question_id": "financial_basics_monthly_expenses",
                "value_condition": "greater_than_zero"
            }
        })
        
        self.add_question({
            "id": "goals_emergency_fund_target",
            "text": "Would you like to set a goal to build or enhance your emergency fund?",
            "type": "goal",
            "category": "goals",
            "input_type": "radio",
            "options": ["Yes", "No"],
            "required": False,
            "order": 4,
            "help_text": "Creating an emergency fund is typically the first financial priority"
        })
        
        self.add_question({
            "id": "goals_emergency_fund_amount",
            "text": "What is your target amount for your emergency fund?",
            "type": "goal",
            "category": "goals",
            "input_type": "number",
            "min": 0,
            "required": False,
            "order": 5,
            "help_text": "In India, 6-9 months of expenses is recommended. You can override this with your own target amount that suits your specific situation.",
            "depends_on": {
                "question_id": "goals_emergency_fund_target",
                "value": "Yes"
            }
        })
        
        self.add_question({
            "id": "goals_emergency_fund_timeframe",
            "text": "By when would you like to complete your emergency fund goal?",
            "type": "goal",
            "category": "goals",
            "input_type": "select",
            "options": ["Within 6 months", "Within 1 year", "Within 2 years", "More than 2 years"],
            "required": False,
            "order": 6,
            "help_text": "Your target timeframe helps prioritize this goal",
            "depends_on": {
                "question_id": "goals_emergency_fund_target",
                "value": "Yes"
            }
        })
        
        # INSURANCE QUESTIONS
        # Insurance education for Indian context
        self.add_question({
            "id": "goals_insurance_education",
            "text": "Insurance Guidelines for India",
            "type": "goal",
            "category": "goals",
            "input_type": "educational",
            "required": False,
            "order": 5.5,
            "educational_content": """
                <h3>Insurance Planning in the Indian Context</h3>
                
                <p>Insurance planning in India requires special considerations due to the unique healthcare 
                system, family structures, and economic environment:</p>
                
                <ul>
                    <li><strong>Health Insurance:</strong> A family floater policy of at least ₹10-15 lakh 
                    is recommended for a family of four, with regular increases to match medical inflation 
                    (15-20% annually). Individual policies may be better for senior family members.</li>
                    
                    <li><strong>Term Life Insurance:</strong> Coverage should be 10-15 times your annual income 
                    to provide adequate financial security for dependents. Term insurance offers the highest 
                    coverage at the lowest cost.</li>
                    
                    <li><strong>Critical Illness Cover:</strong> A separate critical illness rider or 
                    standalone policy (₹25-50 lakh) is valuable in India where specific treatments like 
                    cancer care can be extremely costly.</li>
                    
                    <li><strong>Personal Accident:</strong> Coverage equal to at least 5 times annual 
                    income is recommended, especially for primary earning members.</li>
                    
                    <li><strong>Home Insurance:</strong> Despite low penetration in India, home insurance 
                    is crucial protection against natural disasters and unforeseen events.</li>
                </ul>
                
                <p>Insurance policies should be reviewed annually and updated with major life events 
                (marriage, children, property purchase). Before purchasing, compare premiums, coverage, 
                claim settlement ratios, and exclusions across providers.</p>
            """,
            "help_text": "DISCLAIMER: We are only a profiler, not providing recommendations. The following information is for educational purposes only, based on financial literature, not personalized advice. We are not RBI/SEBI regulated financial advisors."
        })
        
        self.add_question({
            "id": "goals_insurance_adequacy",
            "text": "Do you feel your current insurance coverage (health, life, etc.) is adequate?",
            "type": "goal",
            "category": "goals",
            "input_type": "radio",
            "options": ["Yes, fully adequate", "Somewhat adequate", "Not adequate", "I don't have insurance"],
            "required": False,
            "order": 6,
            "help_text": "Insurance is an important part of financial security"
        })
        
        self.add_question({
            "id": "goals_insurance_types",
            "text": "What types of insurance do you currently have? (Select all that apply)",
            "type": "goal",
            "category": "goals",
            "input_type": "multiselect",
            "options": ["Health Insurance", "Life Insurance", "Term Insurance", "Critical Illness", "Disability Insurance", "Home Insurance", "Vehicle Insurance", "None of these"],
            "required": False,
            "order": 7,
            "help_text": "Understanding your current insurance helps identify gaps in coverage"
        })
        
        self.add_question({
            "id": "goals_insurance_target",
            "text": "Would you like to set a goal to improve your insurance coverage?",
            "type": "goal",
            "category": "goals",
            "input_type": "radio",
            "options": ["Yes", "No"],
            "required": False,
            "order": 8,
            "help_text": "Appropriate insurance coverage is a fundamental financial protection"
        })
        
        self.add_question({
            "id": "goals_insurance_type_target",
            "text": "Which type of insurance would you like to prioritize?",
            "type": "goal",
            "category": "goals",
            "input_type": "select",
            "options": ["Health Insurance", "Life Insurance", "Term Insurance", "Critical Illness", "Disability Insurance", "Home Insurance", "Vehicle Insurance"],
            "required": False,
            "order": 9,
            "help_text": "Select the insurance type you'd like to prioritize as a goal",
            "depends_on": {
                "question_id": "goals_insurance_target",
                "value": "Yes"
            }
        })
        
        self.add_question({
            "id": "goals_insurance_timeframe",
            "text": "By when would you like to achieve this insurance goal?",
            "type": "goal",
            "category": "goals",
            "input_type": "select",
            "options": ["Within 3 months", "Within 6 months", "Within 1 year", "More than 1 year"],
            "required": False,
            "order": 10,
            "help_text": "Your target timeframe helps prioritize this goal",
            "depends_on": {
                "question_id": "goals_insurance_target",
                "value": "Yes"
            }
        })
        
        # OTHER FINANCIAL GOALS QUESTIONS
        self.add_question({
            "id": "goals_other_categories",
            "text": "What other financial goals are important to you? (Select all that apply)",
            "type": "goal",
            "category": "goals",
            "input_type": "multiselect",
            "options": [
                "Home purchase or down payment", 
                "Education funding", 
                "Debt elimination", 
                "Early retirement", 
                "Traditional retirement", 
                "Travel", 
                "Vehicle purchase", 
                "Home improvement", 
                "Estate planning", 
                "Charitable giving", 
                "Custom goal"
            ],
            "required": False,
            "order": 11,
            "help_text": "Select the financial goals you'd like to track and work towards"
        })
        
        # HOME PURCHASE GOAL QUESTIONS
        self.add_question({
            "id": "goals_home_purchase_amount",
            "text": "What is your target amount for home purchase or down payment?",
            "type": "goal",
            "category": "goals",
            "input_type": "number",
            "min": 0,
            "required": False,
            "order": 12,
            "help_text": "Your target amount for home purchase or down payment",
            "depends_on": {
                "question_id": "goals_other_categories",
                "has_value": "Home purchase or down payment"
            }
        })
        
        self.add_question({
            "id": "goals_home_purchase_timeframe",
            "text": "By when would you like to achieve your home purchase goal?",
            "type": "goal",
            "category": "goals",
            "input_type": "select",
            "options": ["Within 1 year", "1-3 years", "3-5 years", "5-10 years", "More than 10 years"],
            "required": False,
            "order": 13,
            "help_text": "Your target timeframe for home purchase goal",
            "depends_on": {
                "question_id": "goals_other_categories",
                "has_value": "Home purchase or down payment"
            }
        })
        
        # EDUCATION FUNDING GOAL QUESTIONS
        self.add_question({
            "id": "goals_education_amount",
            "text": "What is your target amount for education funding?",
            "type": "goal",
            "category": "goals",
            "input_type": "number",
            "min": 0,
            "required": False,
            "order": 14,
            "help_text": "Your target amount for education funding",
            "depends_on": {
                "question_id": "goals_other_categories",
                "has_value": "Education funding"
            }
        })
        
        self.add_question({
            "id": "goals_education_timeframe",
            "text": "By when would you like to achieve your education funding goal?",
            "type": "goal",
            "category": "goals",
            "input_type": "select",
            "options": ["Within 1 year", "1-3 years", "3-5 years", "5-10 years", "More than 10 years"],
            "required": False,
            "order": 15,
            "help_text": "Your target timeframe for education funding goal",
            "depends_on": {
                "question_id": "goals_other_categories",
                "has_value": "Education funding"
            }
        })
        
        # DEBT ELIMINATION GOAL QUESTIONS
        self.add_question({
            "id": "goals_debt_amount",
            "text": "What is your target amount for debt elimination?",
            "type": "goal",
            "category": "goals",
            "input_type": "number",
            "min": 0,
            "required": False,
            "order": 16,
            "help_text": "Your target amount for debt elimination",
            "depends_on": {
                "question_id": "goals_other_categories",
                "has_value": "Debt elimination"
            }
        })
        
        self.add_question({
            "id": "goals_debt_timeframe",
            "text": "By when would you like to achieve your debt elimination goal?",
            "type": "goal",
            "category": "goals",
            "input_type": "select",
            "options": ["Within 1 year", "1-3 years", "3-5 years", "5-10 years", "More than 10 years"],
            "required": False,
            "order": 17,
            "help_text": "Your target timeframe for debt elimination goal",
            "depends_on": {
                "question_id": "goals_other_categories",
                "has_value": "Debt elimination"
            }
        })
        
        # RETIREMENT GOAL QUESTIONS
        self.add_question({
            "id": "goals_retirement_amount",
            "text": "What is your target amount for retirement savings?",
            "type": "goal",
            "category": "goals",
            "input_type": "number",
            "min": 0,
            "required": False,
            "order": 18,
            "help_text": "Your target amount for retirement savings",
            "depends_on": {
                "question_id": "goals_other_categories",
                "has_values_any": ["Early retirement", "Traditional retirement"]
            }
        })
        
        self.add_question({
            "id": "goals_retirement_timeframe",
            "text": "By what age would you like to retire?",
            "type": "goal",
            "category": "goals",
            "input_type": "number",
            "min": 35,
            "max": 80,
            "required": False,
            "order": 19,
            "help_text": "Your target retirement age",
            "depends_on": {
                "question_id": "goals_other_categories",
                "has_values_any": ["Early retirement", "Traditional retirement"]
            }
        })
        
        # CUSTOM GOAL QUESTIONS
        self.add_question({
            "id": "goals_custom_title",
            "text": "What is the title of your custom financial goal?",
            "type": "goal",
            "category": "goals",
            "input_type": "text",
            "required": False,
            "order": 20,
            "help_text": "Give your custom goal a specific title",
            "depends_on": {
                "question_id": "goals_other_categories",
                "has_value": "Custom goal"
            }
        })
        
        self.add_question({
            "id": "goals_custom_amount",
            "text": "What is your target amount for this custom goal?",
            "type": "goal",
            "category": "goals",
            "input_type": "number",
            "min": 0,
            "required": False,
            "order": 21,
            "help_text": "Your target amount for this custom goal",
            "depends_on": {
                "question_id": "goals_other_categories",
                "has_value": "Custom goal"
            }
        })
        
        self.add_question({
            "id": "goals_custom_timeframe",
            "text": "By when would you like to achieve this custom goal?",
            "type": "goal",
            "category": "goals",
            "input_type": "select",
            "options": ["Within 1 year", "1-3 years", "3-5 years", "5-10 years", "More than 10 years"],
            "required": False,
            "order": 22,
            "help_text": "Your target timeframe for this custom goal",
            "depends_on": {
                "question_id": "goals_other_categories",
                "has_value": "Custom goal"
            }
        })
        
        # GOAL IMPORTANCE AND FLEXIBILITY
        self.add_question({
            "id": "goals_importance_flexibility",
            "text": "For your financial goals, please indicate the most important factors:",
            "type": "goal",
            "category": "goals",
            "input_type": "radio",
            "options": [
                "Achieving the exact target amount is most important, timing is flexible",
                "Achieving the goal by the target date is most important, amount is flexible",
                "Both target amount and timing are equally important",
                "Both target amount and timing are somewhat flexible"
            ],
            "required": False,
            "order": 23,
            "help_text": "This helps prioritize your goals based on importance and flexibility"
        })
        
        # Goal completion confirmation
        self.add_question({
            "id": "goals_confirmation",
            "text": "You've successfully set up your initial financial goals. Would you like to continue with deeper financial profiling questions?",
            "type": "goal",
            "category": "goals",
            "input_type": "radio",
            "options": ["Yes, continue with more questions", "No, I'm done for now"],
            "required": False,
            "order": 24,
            "help_text": "Next-level questions will further refine your financial profile"
        })
        
        logging.info(f"Initialized goal questions: {len(self.get_questions_by_type('goal'))}")
    
    def add_question(self, question):
        """
        Add a question to the repository.
        
        Args:
            question (dict): Question definition
        """
        if 'id' not in question:
            raise ValueError("Question must have an id")
        
        self.questions[question['id']] = question
    
    def get_question(self, question_id):
        """
        Get a question by ID.
        
        Args:
            question_id (str): ID of the question
            
        Returns:
            dict: Question definition or None if not found
        """
        return self.questions.get(question_id)
    
    def get_questions_by_category(self, category):
        """
        Get all questions in a specific category.
        
        Args:
            category (str): Category name
            
        Returns:
            list: Questions in the category, sorted by order
        """
        category_questions = [q for q in self.questions.values() if q.get('category') == category]
        return sorted(category_questions, key=lambda x: x.get('order', 9999))
    
    def get_questions_by_type(self, question_type):
        """
        Get all questions of a specific type.
        
        Args:
            question_type (str): Question type (core, next_level, behavioral)
            
        Returns:
            list: Questions of the type
        """
        return [q for q in self.questions.values() if q.get('type') == question_type]
    
    def get_core_questions(self):
        """
        Get all core questions.
        
        Returns:
            list: Core questions
        """
        return self.get_questions_by_type('core')
    
    def get_category_completion(self, profile, category):
        """
        Calculate completion percentage for a category.
        
        Args:
            profile (dict): User profile
            category (str): Category name
            
        Returns:
            float: Completion percentage (0-100)
        """
        category_questions = self.get_questions_by_category(category)
        required_questions = [q for q in category_questions if q.get('required', False)]
        
        if not required_questions:
            return 100.0
        
        # Get answered question IDs
        answered_ids = [a.get('question_id') for a in profile.get('answers', [])]
        
        # Count required questions that have been answered
        answered_required = [q for q in required_questions if q.get('id') in answered_ids]
        
        completion = (len(answered_required) / len(required_questions)) * 100
        return round(completion, 1)
    
    def get_dependent_questions(self, profile):
        """
        Get questions that depend on existing answers.
        
        Args:
            profile (dict): User profile
            
        Returns:
            list: Questions that should be shown based on dependencies
        """
        result = []
        answers = {a.get('question_id'): a.get('answer') for a in profile.get('answers', [])}
        
        for question in self.questions.values():
            if 'depends_on' not in question:
                continue
                
            dependency = question.get('depends_on', {})
            dependent_question_id = dependency.get('question_id')
            
            if dependent_question_id not in answers:
                continue
                
            dependent_answer = answers[dependent_question_id]
            expected_value = dependency.get('value', None)
            value_condition = dependency.get('value_condition', None)
            
            # Handle different types of conditions
            if value_condition == 'greater_than_zero' and isinstance(dependent_answer, (int, float)) and dependent_answer > 0:
                result.append(question)
            elif expected_value and dependent_answer == expected_value:
                result.append(question)
            elif 'values' in dependency and dependent_answer in dependency['values']:
                # For multiple allowed values (select from a list)
                result.append(question)
            elif 'has_value' in dependency and isinstance(dependent_answer, list) and dependency['has_value'] in dependent_answer:
                # For multiselect where a specific value is required
                result.append(question)
            elif 'has_values_any' in dependency and isinstance(dependent_answer, list):
                # For multiselect where any of several values is required
                required_values = dependency['has_values_any']
                if any(val in dependent_answer for val in required_values):
                    result.append(question)
                
        return result
        
    def get_all_questions(self):
        """
        Get all questions in the repository.
        
        Returns:
            list: All questions in the repository
        """
        return list(self.questions.values())
    
    def get_next_question(self, profile):
        """
        Determine the next question to ask based on profile state.
        
        Args:
            profile (dict): User profile
            
        Returns:
            dict: Next question to ask or None if all required are complete
        """
        # Get answered question IDs
        answered_ids = [a.get('question_id') for a in profile.get('answers', [])]
        
        # Check core questions first, by category order
        categories = ['demographics', 'financial_basics', 'assets_and_debts', 'special_cases']
        
        for category in categories:
            category_questions = self.get_questions_by_category(category)
            
            # Filter for required questions that haven't been answered
            unanswered = [q for q in category_questions 
                         if q.get('required', False) 
                         and q.get('id') not in answered_ids
                         and 'depends_on' not in q]
            
            if unanswered:
                # Return the first unanswered required question in this category
                return unanswered[0]
        
        # Check dependent questions - special priority for business and real estate value questions
        dependent_questions = self.get_dependent_questions(profile)
        
        # First check for business value or real estate value questions that need to be answered
        special_value_questions = [q for q in dependent_questions 
                                 if q.get('id') in ['special_cases_business_value', 'special_cases_real_estate_value'] 
                                 and q.get('id') not in answered_ids]
        
        if special_value_questions:
            # Sort by order to maintain consistent flow
            sorted_special = sorted(special_value_questions, key=lambda q: q.get('order', 0))
            logging.info(f"Found dependent special value question: {sorted_special[0].get('id')}")
            return sorted_special[0]
            
        # Then check other dependent questions
        unanswered_dependent = [q for q in dependent_questions if q.get('id') not in answered_ids]
        
        if unanswered_dependent:
            return unanswered_dependent[0]
        
        # All required questions answered
        return None
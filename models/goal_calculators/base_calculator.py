import json
import time
import logging
import calendar
import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from enum import Enum

logger = logging.getLogger(__name__)

def get_financial_parameter_service():
    """
    Get the financial parameter service instance.
    
    This is separated out to avoid circular imports and to make testing easier.
    """
    try:
        from services.financial_parameter_service import FinancialParameterService
        return FinancialParameterService()
    except ImportError:
        logger.warning("Financial Parameter Service not available, using default parameters")
        return None


class GoalCalculator:
    """
    Base class for goal calculations that provides core calculation methods
    and utility functions for all goal types.
    """
    
    @classmethod
    def get_calculator_for_category(cls, category):
        """
        Factory method to get the appropriate calculator for a goal category.
        
        Args:
            category (str): The goal category name
            
        Returns:
            GoalCalculator: An instance of the appropriate calculator subclass
        """
        # Import locally to avoid circular imports
        from models.goal_calculators.emergency_fund_calculator import EmergencyFundCalculator
        from models.goal_calculators.retirement_calculator import RetirementCalculator, EarlyRetirementCalculator
        from models.goal_calculators.education_calculator import EducationCalculator
        from models.goal_calculators.home_calculator import HomeDownPaymentCalculator
        from models.goal_calculators.debt_repayment_calculator import DebtRepaymentCalculator
        from models.goal_calculators.discretionary_calculator import DiscretionaryGoalCalculator
        from models.goal_calculators.wedding_calculator import WeddingCalculator
        from models.goal_calculators.legacy_planning_calculator import LegacyPlanningCalculator, CharitableGivingCalculator
        from models.goal_calculators.custom_goal_calculator import CustomGoalCalculator
        
        # Map category names to calculator classes
        calculators = {
            'emergency_fund': EmergencyFundCalculator,
            'retirement': RetirementCalculator,
            'early_retirement': EarlyRetirementCalculator,
            'education': EducationCalculator,
            'home_purchase': HomeDownPaymentCalculator,
            'debt_repayment': DebtRepaymentCalculator,
            'debt_elimination': DebtRepaymentCalculator,  # Alias for backward compatibility
            'travel': DiscretionaryGoalCalculator,
            'lifestyle': DiscretionaryGoalCalculator,  # Alias for backward compatibility
            'discretionary': DiscretionaryGoalCalculator,
            'wedding': WeddingCalculator,
            'legacy_planning': LegacyPlanningCalculator,
            'estate_planning': LegacyPlanningCalculator,  # Alias for backward compatibility
            'charitable_giving': CharitableGivingCalculator,
            'vehicle': DiscretionaryGoalCalculator,  # Use DiscretionaryGoalCalculator for vehicle goals
            'home_improvement': DiscretionaryGoalCalculator,  # Use DiscretionaryGoalCalculator for home improvement
            'insurance': DiscretionaryGoalCalculator,  # Use DiscretionaryGoalCalculator for insurance
            'custom': CustomGoalCalculator
        }
        
        # Normalize category name
        if isinstance(category, str):
            category = category.lower().replace(' ', '_')
        
        # Return the appropriate calculator instance
        if category in calculators:
            return calculators[category]()
        else:
            # Default to CustomGoalCalculator for unknown categories
            return CustomGoalCalculator()
    
    @classmethod
    def get_calculator_for_goal(cls, goal):
        """
        Factory method to get the appropriate calculator for a goal.
        
        Args:
            goal: The goal object (dict or object with a category attribute)
            
        Returns:
            GoalCalculator: An instance of the appropriate calculator subclass
        """
        # Extract category from goal
        if isinstance(goal, dict):
            category = goal.get('category', 'custom')
        else:
            category = getattr(goal, 'category', 'custom')
            
        # Get calculator for this category
        return cls.get_calculator_for_category(category)
    
    def __init__(self):
        """Initialize the calculator with parameters from FinancialParameterService"""
        # Get financial parameter service
        self.param_service = get_financial_parameter_service()
        
        # Initialize params dictionary with default values
        self.params = {
            "inflation_rate": 0.06,  # Default: 6% annual inflation
            "emergency_fund_months": 6,  # Default: 6 months of expenses
            "high_interest_debt_threshold": 0.10,  # 10% interest rate threshold
            "gold_allocation_percent": 0.15,  # Default gold allocation
            "savings_rate_base": 0.20,  # Default savings rate: 20% of income
            "equity_returns": {
                "conservative": 0.09,  # 9% for conservative equity returns
                "moderate": 0.12,      # 12% for moderate equity returns
                "aggressive": 0.15     # 15% for aggressive equity returns
            },
            "debt_returns": {
                "conservative": 0.06,  # 6% for conservative debt returns
                "moderate": 0.07,      # 7% for moderate debt returns
                "aggressive": 0.08     # 8% for aggressive debt returns
            },
            "gold_returns": 0.08,      # 8% gold returns
            "real_estate_appreciation": 0.09,  # 9% real estate appreciation
            "retirement_corpus_multiplier": 25,  # 25x annual expenses for retirement
            "life_expectancy": 85,     # Life expectancy of 85 years
            "home_down_payment_percent": 0.20  # 20% down payment for home purchase
        }
        
        # Load parameters from service if available
        if self.param_service:
            try:
                service_params = self.param_service.get_all_parameters()
                # Update default params with those from the service
                for key, value in service_params.items():
                    if key in self.params and key != "equity_returns" and key != "debt_returns":
                        # Handle simple values
                        if isinstance(value, (int, float, str, bool)):
                            self.params[key] = value
                    elif key == "equity_returns" or key == "debt_returns":
                        # Handle nested dictionaries
                        if isinstance(value, dict):
                            for risk_level, return_value in value.items():
                                if risk_level in self.params[key]:
                                    self.params[key][risk_level] = return_value
            except Exception as e:
                logger.error(f"Error loading parameters from service: {str(e)}")
                
    def get_parameter(self, param_path, default=None, profile_id=None):
        """
        Get a parameter value from the service with fallback to local params dictionary.
        
        This method provides standardized parameter access across all calculators.
        
        Args:
            param_path (str): Parameter path in dot notation
            default: Default value if parameter not found
            profile_id (str, optional): User profile ID for personalized parameters
            
        Returns:
            Parameter value or default if not found
        """
        value = None
        
        # Parameter path alias mappings for backward compatibility
        aliases = {
            "inflation.general": ["inflation_rate"],
            "emergency_fund.months_of_expenses": ["emergency_fund_months"],
            "retirement.corpus_multiplier": ["retirement_corpus_multiplier"],
            "retirement.life_expectancy": ["life_expectancy"],
            "housing.down_payment_percent": ["home_down_payment_percent"],
            "debt.high_interest_threshold": ["high_interest_debt_threshold"],
            "asset_returns.equity.value": ["equity_returns.moderate"],
            "asset_returns.bond.value": ["debt_returns.moderate"],
            "asset_returns.gold.value": ["gold_returns"]
        }
        
        # Try to get from parameter service first (live value)
        if self.param_service:
            try:
                # Try user-specific parameter if profile_id provided
                if profile_id:
                    # Try to extract profile_id from profile dict if provided
                    if isinstance(profile_id, dict) and 'user_id' in profile_id:
                        profile_id = profile_id['user_id']
                    
                    value = self.param_service.get(param_path, None, profile_id)
                    if value is not None:
                        return value
                
                # Try standard parameter from service
                value = self.param_service.get(param_path)
                if value is not None:
                    return value
                
                # Try aliases if primary path not found
                if param_path in aliases:
                    for alias in aliases[param_path]:
                        value = self.param_service.get(alias)
                        if value is not None:
                            return value
            except Exception as e:
                logger.debug(f"Error accessing parameter '{param_path}' from service: {str(e)}")
        
        # If not found in service, try local params dictionary
        try:
            # Handle nested parameters with dot notation
            if "." in param_path:
                parts = param_path.split(".")
                current = self.params
                for part in parts:
                    if part in current:
                        current = current[part]
                    else:
                        # Not found in nested structure
                        current = None
                        break
                
                if current is not None:
                    return current
            elif param_path in self.params:
                return self.params[param_path]
            
            # Try aliases with local params if main path not found
            if param_path in aliases:
                for alias in aliases[param_path]:
                    if "." in alias:
                        parts = alias.split(".")
                        current = self.params
                        for part in parts:
                            if part in current:
                                current = current[part]
                            else:
                                current = None
                                break
                        
                        if current is not None:
                            return current
                    elif alias in self.params:
                        return self.params[alias]
        except Exception as e:
            logger.debug(f"Error accessing parameter '{param_path}' from local params: {str(e)}")
        
        # Return default value if parameter not found anywhere
        return default
    
    def _get_age(self, profile: Dict[str, Any]) -> int:
        """
        Extract age from profile data.
        
        Args:
            profile: User profile with age information
            
        Returns:
            int: User's age
        """
        # Default age if we can't extract it
        default_age = 35
        
        try:
            # Check if age is directly available
            if 'age' in profile:
                age = profile['age']
                if isinstance(age, (int, float)):
                    return int(age)
                elif isinstance(age, str) and age.isdigit():
                    return int(age)
            
            # Check if DOB is available
            if 'dob' in profile or 'date_of_birth' in profile:
                dob_str = profile.get('dob', profile.get('date_of_birth'))
                # Convert string to date
                if isinstance(dob_str, str):
                    try:
                        # Try different date formats
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
                            try:
                                dob = datetime.strptime(dob_str, fmt)
                                # Calculate age
                                today = datetime.now()
                                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                                return age
                            except ValueError:
                                continue
                    except Exception as e:
                        logger.error(f"Error parsing date of birth: {str(e)}")
            
            # Try to find age in answers
            if 'answers' in profile:
                answers = profile['answers']
                for answer in answers:
                    if 'question_id' in answer and 'age' in answer['question_id'].lower():
                        value = answer.get('answer')
                        if isinstance(value, (int, float)):
                            return int(value)
                        elif isinstance(value, str) and value.isdigit():
                            return int(value)
                        
        except Exception as e:
            logger.error(f"Error extracting age from profile: {str(e)}")
        
        logger.warning(f"Could not determine age from profile, using default: {default_age}")
        return default_age
    
    def _get_monthly_income(self, profile: Dict[str, Any]) -> float:
        """
        Extract monthly income from profile data.
        
        Args:
            profile: User profile with income information
            
        Returns:
            float: Monthly income
        """
        # Default income if we can't extract it
        default_income = 5000.0
        
        try:
            # Check if income is directly available
            if 'income' in profile:
                income_value = profile['income']
                # Check if annual or monthly
                is_annual = False
                
                if isinstance(income_value, dict):
                    amount = income_value.get('amount', 0)
                    is_annual = income_value.get('frequency', '').lower() in ['annual', 'yearly']
                else:
                    amount = income_value
                
                # Convert to float
                if isinstance(amount, (int, float)):
                    income = float(amount)
                elif isinstance(amount, str) and amount.replace('.', '', 1).isdigit():
                    income = float(amount)
                else:
                    return default_income
                
                # Convert to monthly if annual
                if is_annual:
                    return income / 12
                return income
            
            # Try to find income in answers
            if 'answers' in profile:
                answers = profile['answers']
                
                # Find the most relevant income question
                best_answer = None
                best_score = 0
                
                for answer in answers:
                    if 'question_id' in answer:
                        question_id = answer['question_id'].lower()
                        score = 0
                        
                        # Score based on relevance
                        if 'income' in question_id:
                            score += 5
                        if 'monthly' in question_id:
                            score += 3
                        if 'salary' in question_id:
                            score += 2
                        if 'annual' in question_id:
                            score += 1
                        
                        if score > best_score:
                            best_score = score
                            best_answer = answer
                
                if best_answer:
                    value = best_answer.get('answer')
                    question_id = best_answer.get('question_id', '').lower()
                    
                    # Handle different formats
                    if isinstance(value, (int, float)):
                        income_value = float(value)
                    elif isinstance(value, str) and value.replace('.', '', 1).isdigit():
                        income_value = float(value)
                    elif isinstance(value, dict) and 'amount' in value:
                        income_value = float(value['amount'])
                    else:
                        return default_income
                    
                    # Check if annual or monthly
                    is_annual = 'annual' in question_id or 'yearly' in question_id
                    if isinstance(value, dict) and 'frequency' in value:
                        is_annual = value['frequency'].lower() in ['annual', 'yearly']
                    
                    # Convert to monthly if annual
                    if is_annual:
                        return income_value / 12
                    return income_value
                    
        except Exception as e:
            logger.error(f"Error extracting income from profile: {str(e)}")
        
        logger.warning(f"Could not determine income from profile, using default: {default_income}")
        return default_income
    
    def _get_risk_profile(self, profile: Dict[str, Any]) -> str:
        """
        Extract risk profile from user data.
        
        Args:
            profile: User profile with risk information
            
        Returns:
            str: Risk profile (conservative, moderate, aggressive)
        """
        # Default risk profile
        default_profile = "moderate"
        
        try:
            # Check if risk profile is directly available
            if 'risk_profile' in profile:
                risk = profile['risk_profile'].lower()
                if risk in ['conservative', 'moderate', 'aggressive']:
                    return risk
            
            # Try to find risk score in answers
            if 'answers' in profile:
                answers = profile['answers']
                for answer in answers:
                    if 'question_id' in answer and 'risk' in answer['question_id'].lower():
                        value = answer.get('answer')
                        
                        # Handle different formats
                        if isinstance(value, str):
                            value_lower = value.lower()
                            if 'conservative' in value_lower or 'low' in value_lower:
                                return 'conservative'
                            elif 'aggressive' in value_lower or 'high' in value_lower:
                                return 'aggressive'
                            elif 'moderate' in value_lower or 'medium' in value_lower:
                                return 'moderate'
                        elif isinstance(value, (int, float)):
                            # Assume 1-10 scale
                            if value <= 3:
                                return 'conservative'
                            elif value <= 7:
                                return 'moderate'
                            else:
                                return 'aggressive'
                        
        except Exception as e:
            logger.error(f"Error extracting risk profile from profile: {str(e)}")
        
        logger.warning(f"Could not determine risk profile from profile, using default: {default_profile}")
        return default_profile
    
    def _get_monthly_expenses(self, profile: Dict[str, Any]) -> float:
        """
        Extract monthly expenses from profile data.
        
        Args:
            profile: User profile with expense information
            
        Returns:
            float: Monthly expenses
        """
        # Try to find expense information in profile answers
        monthly_expenses = 0.0
        
        try:
            # Check if expenses are directly available
            if 'expenses' in profile:
                expenses_value = profile['expenses']
                # Check if annual or monthly
                is_annual = False
                
                if isinstance(expenses_value, dict):
                    amount = expenses_value.get('amount', 0)
                    is_annual = expenses_value.get('frequency', '').lower() in ['annual', 'yearly']
                else:
                    amount = expenses_value
                
                # Convert to float
                if isinstance(amount, (int, float)):
                    expenses = float(amount)
                elif isinstance(amount, str) and amount.replace('.', '', 1).isdigit():
                    expenses = float(amount)
                else:
                    expenses = 0.0
                
                # Convert to monthly if annual
                if is_annual:
                    return expenses / 12
                return expenses
            
            # Look for expense-related answers in profile
            if 'answers' in profile:
                answers = profile['answers']
                
                for answer in answers:
                    if 'question_id' in answer and ('expense' in answer['question_id'].lower() or 'spending' in answer['question_id'].lower()):
                        value = answer.get('answer', 0)
                        
                        # Handle different formats
                        if isinstance(value, (int, float)):
                            expense_value = float(value)
                        elif isinstance(value, str) and value.replace('.', '', 1).isdigit():
                            expense_value = float(value)
                        elif isinstance(value, dict) and 'amount' in value:
                            expense_value = float(value['amount'])
                        else:
                            continue
                        
                        # Check if annual or monthly
                        is_annual = False
                        question_id = answer.get('question_id', '').lower()
                        if isinstance(value, dict) and 'frequency' in value:
                            is_annual = value['frequency'].lower() in ['annual', 'yearly', 'per year']
                        elif 'annual' in question_id or 'yearly' in question_id:
                            is_annual = True
                        
                        # Convert to monthly if annual
                        if is_annual:
                            expense_value /= 12
                        
                        # Update monthly expenses if higher
                        if expense_value > monthly_expenses:
                            monthly_expenses = expense_value
        except Exception as e:
            logger.error(f"Error extracting expenses from profile: {str(e)}")
        
        if monthly_expenses <= 0:
            # Fallback to income-based estimation
            monthly_income = self._get_monthly_income(profile)
            # Estimate expenses as 70% of income
            monthly_expenses = monthly_income * 0.7
            logger.warning(f"Could not determine expenses from profile, estimating as: {monthly_expenses}")
        
        return monthly_expenses
    
    def calculate_amount_needed(self, goal, profile: Dict[str, Any]) -> float:
        """
        Calculate the amount needed for a goal.
        
        This is a base implementation that should be overridden by subclasses.
        
        Args:
            goal: The goal to calculate
            profile: User profile
            
        Returns:
            float: Calculated amount needed
        """
        raise NotImplementedError("Subclasses must implement calculate_amount_needed")
    
    # Alias for backward compatibility with older code
    def calculate_required_saving_rate(self, goal, profile: Dict[str, Any]) -> Union[float, Tuple[float, float]]:
        """
        Calculate required saving rate (monthly and annual) for a goal.
        Alias for backward compatibility with older code.
        
        Args:
            goal: The goal to calculate for
            profile: User profile
            
        Returns:
            Union[float, Tuple[float, float]]: Monthly savings rate or (monthly_savings, annual_savings)
            For backward compatibility, returns just the monthly value
        """
        monthly = self.calculate_monthly_contribution(goal, profile)
        annual = monthly * 12
        
        # For backward compatibility with older code, just return the monthly amount
        # This way tests expecting a single value will continue to work
        return monthly  # Changed to return just monthly for compatibility
    
    def calculate_goal_success_probability(self, goal, profile: Dict[str, Any]) -> float:
        """
        Calculate probability of achieving the goal.
        Added for backward compatibility with older code.
        
        Args:
            goal: The goal to calculate for
            profile: User profile
            
        Returns:
            float: Success probability percentage (0-100)
        """
        # Get current and target amounts
        if isinstance(goal, dict):
            current_amount = goal.get('current_amount', 0)
            target_amount = goal.get('target_amount', 0)
        else:
            current_amount = getattr(goal, 'current_amount', 0)
            target_amount = getattr(goal, 'target_amount', 0)
            
        # If target amount is not set, calculate it
        if target_amount <= 0:
            target_amount = self.calculate_amount_needed(goal, profile)
            
        # Calculate time available in months
        months_available = self.calculate_time_available(goal, profile)
        
        if months_available <= 0:
            return 0.0  # No time left to achieve goal
            
        # Calculate required monthly contribution
        required_monthly = self.calculate_monthly_contribution(goal, profile)
        
        # Get user's monthly income and expenses
        monthly_income = self._get_monthly_income(profile)
        monthly_expenses = self._get_monthly_expenses(profile)
        
        # Calculate disposable income (income minus expenses)
        disposable_income = max(0, monthly_income - monthly_expenses)
        
        # Calculate current progress as a percentage
        if target_amount > 0:
            current_progress = min(100.0, (current_amount / target_amount) * 100.0)
        else:
            current_progress = 0.0
            
        # If already achieved
        if current_progress >= 100.0:
            return 100.0
            
        # If required contribution is zero, but not complete
        if required_monthly <= 0 and current_progress < 100.0:
            return 95.0  # High but not guaranteed
            
        # Calculate affordability ratio (disposable / required)
        if required_monthly > 0:
            affordability_ratio = disposable_income / required_monthly
        else:
            affordability_ratio = 10.0  # High ratio means easily affordable
            
        # Base probability on multiple factors
        if affordability_ratio >= 2.0:
            # Very affordable - high probability
            base_probability = 90.0
        elif affordability_ratio >= 1.0:
            # Affordable - good probability
            base_probability = 75.0
        elif affordability_ratio >= 0.5:
            # Challenging but possible - moderate probability
            base_probability = 50.0
        elif affordability_ratio > 0.0:
            # Very challenging - low probability
            base_probability = 30.0
        else:
            # Not affordable - very low probability
            base_probability = 10.0
            
        # Adjust for current progress
        progress_factor = 1.0 + (current_progress / 100.0)
        
        # Adjust for time - longer timeframes allow for more variability
        if months_available <= 12:
            time_factor = 0.9  # Short timeframe - less chance for adjustment
        elif months_available <= 36:
            time_factor = 1.0  # Medium timeframe - neutral
        elif months_available <= 60:
            time_factor = 1.1  # Medium-long timeframe - more flexibility
        else:
            time_factor = 1.2  # Long timeframe - highest flexibility
            
        # Calculate final probability
        probability = base_probability * progress_factor * time_factor
        
        # Cap at 100%
        return min(100.0, probability)
        
    def calculate_monthly_contribution(self, goal, profile: Dict[str, Any]) -> float:
        """
        Calculate recommended monthly contribution for a goal.
        
        Args:
            goal: The goal to calculate for
            profile: User profile
            
        Returns:
            float: Calculated monthly contribution
        """
        # Get current amount and target amount
        if isinstance(goal, dict):
            current_amount = goal.get('current_amount', 0)
            target_amount = goal.get('target_amount', 0)
            target_date = goal.get('target_date')
        else:
            current_amount = getattr(goal, 'current_amount', 0)
            target_amount = getattr(goal, 'target_amount', 0)
            target_date = getattr(goal, 'target_date', None)
            
        # If target amount is not set, calculate it
        if target_amount <= 0:
            target_amount = self.calculate_amount_needed(goal, profile)
        
        # Calculate time available in months
        months = self.calculate_time_available(goal, profile)
        
        # If no time constraint or already achieved, return 0
        if months <= 0 or current_amount >= target_amount:
            return 0.0
        
        # Calculate simple monthly contribution (no growth)
        amount_needed = target_amount - current_amount
        simple_monthly = amount_needed / months
        
        # Get risk profile
        risk_profile = self._get_risk_profile(profile)
        
        # Get expected return based on risk profile
        if risk_profile == "conservative":
            expected_return = 0.06  # 6% annual return
        elif risk_profile == "aggressive":
            expected_return = 0.10  # 10% annual return
        else:
            expected_return = 0.08  # 8% annual return
            
        # Calculate monthly contribution with compound growth
        # Formula: PMT = (FV - PV * (1 + r)^n) / (((1 + r)^n - 1) / r)
        # Where r is monthly rate, n is number of months
        monthly_rate = expected_return / 12
        
        if monthly_rate > 0:
            contribution = (target_amount - current_amount * ((1 + monthly_rate) ** months)) / (((1 + monthly_rate) ** months - 1) / monthly_rate)
        else:
            contribution = simple_monthly
        
        # Make sure contribution is positive and a float
        return float(max(0.0, contribution))
        
    def get_recommended_allocation(self, goal, profile: Dict[str, Any]) -> Dict[str, float]:
        """
        Get recommended asset allocation for a goal.
        Added for backward compatibility with older code.
        
        Args:
            goal: The goal to get allocation for
            profile: User profile
            
        Returns:
            dict: Recommended allocation percentages by asset class
        """
        # Extract goal parameters
        if isinstance(goal, dict):
            time_horizon = goal.get('time_horizon', 0)
            if time_horizon == 0:
                # Try to calculate time horizon from target date
                months = self.calculate_time_available(goal, profile)
                time_horizon = months / 12  # Convert to years
        else:
            time_horizon = getattr(goal, 'time_horizon', 0)
            if time_horizon == 0:
                # Try to calculate time horizon from target date
                months = self.calculate_time_available(goal, profile)
                time_horizon = months / 12  # Convert to years
                
        # Get risk profile
        risk_profile = self._get_risk_profile(profile)
        
        # Determine allocation based on time horizon and risk profile
        if time_horizon < 1:
            # Short-term goals - safety first
            allocations = {
                'equity': 0.0,
                'debt': 0.8,
                'gold': 0.1,
                'cash': 0.1
            }
        elif time_horizon < 3:
            # Short-medium term goals
            if risk_profile == 'conservative':
                allocations = {
                    'equity': 0.2,
                    'debt': 0.6,
                    'gold': 0.1,
                    'cash': 0.1
                }
            elif risk_profile == 'aggressive':
                allocations = {
                    'equity': 0.4,
                    'debt': 0.4,
                    'gold': 0.1,
                    'cash': 0.1
                }
            else:  # moderate
                allocations = {
                    'equity': 0.3,
                    'debt': 0.5,
                    'gold': 0.1,
                    'cash': 0.1
                }
        elif time_horizon < 7:
            # Medium term goals
            if risk_profile == 'conservative':
                allocations = {
                    'equity': 0.4,
                    'debt': 0.4,
                    'gold': 0.15,
                    'cash': 0.05
                }
            elif risk_profile == 'aggressive':
                allocations = {
                    'equity': 0.6,
                    'debt': 0.25,
                    'gold': 0.1,
                    'cash': 0.05
                }
            else:  # moderate
                allocations = {
                    'equity': 0.5,
                    'debt': 0.35,
                    'gold': 0.1,
                    'cash': 0.05
                }
        else:
            # Long term goals
            if risk_profile == 'conservative':
                allocations = {
                    'equity': 0.5,
                    'debt': 0.3,
                    'gold': 0.15,
                    'cash': 0.05
                }
            elif risk_profile == 'aggressive':
                allocations = {
                    'equity': 0.8,
                    'debt': 0.1,
                    'gold': 0.05,
                    'cash': 0.05
                }
            else:  # moderate
                allocations = {
                    'equity': 0.7,
                    'debt': 0.2,
                    'gold': 0.05,
                    'cash': 0.05
                }
                
        return allocations
        
    def calculate_time_available(self, goal, profile: Dict[str, Any]) -> int:
        """
        Calculate time available for reaching a goal in months.
        
        Args:
            goal: The goal to calculate for
            profile: User profile
            
        Returns:
            int: Time available in months
        """
        # Get today's date
        today = datetime.now().date()
        
        # Extract target date
        target_date = None
        if isinstance(goal, dict):
            # First check for target_date as the preferred field
            target_date_str = goal.get('target_date')
            
            # If not found, try timeframe as a fallback
            if not target_date_str:
                target_date_str = goal.get('timeframe')
                
            # If still not found, try time_horizon for backward compatibility
            if not target_date_str and 'time_horizon' in goal:
                # Convert time_horizon (years) to target date
                try:
                    years = float(goal['time_horizon'])
                    if years > 0:
                        target_date = today.replace(year=today.year + int(years))
                        return int(years * 12)  # Convert years to months
                except (ValueError, TypeError):
                    pass
        else:
            # For object-based goals
            target_date_str = getattr(goal, 'target_date', None)
            
            # If not found, try timeframe as a fallback
            if not target_date_str:
                target_date_str = getattr(goal, 'timeframe', None)
                
            # If still not found, try time_horizon for backward compatibility
            if not target_date_str and hasattr(goal, 'time_horizon'):
                try:
                    years = float(goal.time_horizon)
                    if years > 0:
                        target_date = today.replace(year=today.year + int(years))
                        return int(years * 12)  # Convert years to months
                except (ValueError, TypeError):
                    pass
        
        # Convert string to date if needed
        if target_date_str:
            if isinstance(target_date_str, str):
                try:
                    # Try ISO format first (most common)
                    try:
                        target_date = datetime.fromisoformat(target_date_str.split('T')[0]).date()
                    except (ValueError, AttributeError):
                        # Try different date formats
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                            try:
                                target_date = datetime.strptime(target_date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                except Exception as e:
                    logger.error(f"Error parsing target date: {str(e)}")
            elif hasattr(target_date_str, 'date'):
                target_date = target_date_str.date()
            
        # If no target date, try to extract from notes or use default
        if not target_date:
            # Try to find target year in notes
            target_year = None
            if isinstance(goal, dict):
                notes = goal.get('notes', '')
            else:
                notes = getattr(goal, 'notes', '')
                
            if notes:
                import re
                # Look for years in the future
                year_matches = re.findall(r'\b(20[2-9]\d)\b', notes)
                if year_matches:
                    future_years = [int(y) for y in year_matches if int(y) > today.year]
                    if future_years:
                        target_year = min(future_years)  # Use closest future year
                        
            if target_year:
                # Assume middle of the year if only year is given
                target_date = datetime(target_year, 6, 30).date()
            else:
                # Default to 5 years from now if no target date found
                target_date = today.replace(year=today.year + 5)
        
        # Calculate months between today and target date
        if target_date <= today:
            return 0  # Goal is overdue
            
        # Calculate months difference
        months = (target_date.year - today.year) * 12 + target_date.month - today.month
        # Adjust for day of month
        if target_date.day < today.day:
            months -= 1
            
        return max(0, months)
        
    def calculate_priority_score(self, goal, profile: Dict[str, Any]) -> float:
        """
        Calculate a priority score for the goal based on various factors.
        
        Args:
            goal: The goal to calculate for
            profile: User profile
            
        Returns:
            float: Priority score (higher means higher priority)
        """
        # Extract goal attributes
        if isinstance(goal, dict):
            importance = goal.get('importance', 'medium')
            flexibility = goal.get('flexibility', 'somewhat_flexible')
            category = goal.get('category', '').lower()
        else:
            importance = getattr(goal, 'importance', 'medium')
            flexibility = getattr(goal, 'flexibility', 'somewhat_flexible')
            category = getattr(goal, 'category', '').lower()
            
        # Normalize importance string values
        if isinstance(importance, str):
            importance = importance.lower()
            if 'high' in importance:
                importance = 'high'
            elif 'medium' in importance or 'moderate' in importance:
                importance = 'medium'
            else:
                importance = 'low'
        
        # Base score from importance (0-40 points)
        importance_scores = {
            'high': 40,
            'medium': 25,
            'low': 10
        }
        score = importance_scores.get(importance, 25)
        
        # Add points for urgency based on time available (0-30 points)
        months = self.calculate_time_available(goal, profile)
        if months <= 1:
            urgency_score = 30  # Immediate goal
        elif months <= 12:
            urgency_score = 25  # Within a year
        elif months <= 36:
            urgency_score = 20  # 1-3 years
        elif months <= 60:
            urgency_score = 15  # 3-5 years
        elif months <= 120:
            urgency_score = 10  # 5-10 years
        else:
            urgency_score = 5   # 10+ years
            
        score += urgency_score
        
        # Add points for flexibility (0-15 points)
        flexibility_scores = {
            'fixed': 15,
            'somewhat_flexible': 10,
            'very_flexible': 5
        }
        score += flexibility_scores.get(flexibility, 10)
        
        # Add points for category (0-15 points)
        # Categories based on financial security hierarchy
        category_scores = {
            'emergency_fund': 15,  # Security level
            'insurance': 15,
            'home_purchase': 12,   # Essential level
            'education': 12,
            'debt_repayment': 12,
            'retirement': 10,      # Retirement level
            'early_retirement': 10,
            'travel': 8,           # Lifestyle level
            'vehicle': 8,
            'home_improvement': 8,
            'wedding': 8,
            'charitable_giving': 5, # Legacy level
            'estate_planning': 5,
            'inheritance': 5
        }
        score += category_scores.get(category, 8)  # Default to lifestyle level
        
        # Normalize score to 0-100 range
        normalized_score = min(100, max(0, score))
        
        return normalized_score
    
    @staticmethod
    def get_calculator_for_goal(goal) -> 'GoalCalculator':
        """
        Factory method to get the appropriate calculator for a goal type.
        
        Args:
            goal: Goal to get calculator for
            
        Returns:
            GoalCalculator: Instance of appropriate calculator class
        """
        # Extract goal category
        category = ''
        if isinstance(goal, dict):
            category = goal.get('category', '').lower()
        else:
            category = getattr(goal, 'category', '').lower()
        
        # Import implementation classes to avoid circular imports
        from models.goal_calculators.emergency_fund_calculator import EmergencyFundCalculator
        from models.goal_calculators.retirement_calculator import RetirementCalculator, EarlyRetirementCalculator
        from models.goal_calculators.debt_repayment_calculator import DebtRepaymentCalculator
        from models.goal_calculators.home_calculator import HomeDownPaymentCalculator
        from models.goal_calculators.education_calculator import EducationCalculator
        from models.goal_calculators.wedding_calculator import WeddingCalculator
        from models.goal_calculators.legacy_planning_calculator import LegacyPlanningCalculator, CharitableGivingCalculator
        from models.goal_calculators.discretionary_calculator import DiscretionaryGoalCalculator
        from models.goal_calculators.custom_goal_calculator import CustomGoalCalculator
        
        # Return appropriate calculator based on category
        if category in ['emergency_fund', 'emergency']:
            return EmergencyFundCalculator()
        elif category in ['retirement', 'traditional_retirement']:
            return RetirementCalculator()
        elif category in ['early_retirement', 'fire']:
            return EarlyRetirementCalculator()
        elif category in ['debt_repayment', 'debt', 'debt_consolidation', 'debt_elimination']:
            return DebtRepaymentCalculator()
        elif category in ['home_purchase', 'home', 'down_payment']:
            return HomeDownPaymentCalculator()
        elif category in ['education', 'higher_education']:
            return EducationCalculator()
        elif category in ['wedding', 'marriage']:
            return WeddingCalculator()
        elif category in ['estate_planning', 'legacy_planning', 'legacy']:
            return LegacyPlanningCalculator()
        elif category in ['charitable_giving', 'charity']:
            return CharitableGivingCalculator()
        elif category in ['travel', 'vehicle', 'vacation', 'home_improvement', 'discretionary']:
            return DiscretionaryGoalCalculator()
        elif category in ['custom', 'other']:
            return CustomGoalCalculator()
        else:
            # Default to base calculator for unknown categories
            logger.warning(f"No specialized calculator for category: {category}")
            return GoalCalculator()
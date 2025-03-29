"""
Expense Projection Module

This module provides tools for projecting expenses over time with support for
different expense categories, category-specific inflation rates, and life stage
adjustments.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Union, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import math

from models.projections.base_projection import BaseProjection, FrequencyType

logger = logging.getLogger(__name__)

class ExpenseCategory(Enum):
    """Enum representing different expense categories"""
    # Essential expenses
    HOUSING = "housing"
    FOOD = "food"
    TRANSPORTATION = "transportation"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    DEBT_PAYMENTS = "debt_payments"
    
    # Discretionary expenses
    ENTERTAINMENT = "entertainment"
    CLOTHING = "clothing"
    PERSONAL_CARE = "personal_care"
    DINING_OUT = "dining_out"
    TRAVEL = "travel"
    HOBBIES = "hobbies"
    SUBSCRIPTIONS = "subscriptions"
    DISCRETIONARY = "discretionary"
    
    # Financial categories
    SAVINGS = "savings"
    INVESTMENTS = "investments"
    TAXES = "taxes"
    
    # Family and social
    CHILDCARE = "childcare"
    ELDERCARE = "eldercare"
    CHARITY = "charity"
    GIFTS = "gifts"
    
    # Indian-specific categories
    WEDDING = "wedding"
    FESTIVALS = "festivals"
    RELIGIOUS = "religious"
    DOMESTIC_HELP = "domestic_help"
    
    # Other
    OTHER = "other"

class LifeStage(Enum):
    """Enum representing different life stages affecting expenses"""
    SINGLE = "single"
    COUPLE = "couple"
    FAMILY_YOUNG_CHILDREN = "family_young_children"
    FAMILY_TEENAGE_CHILDREN = "family_teenage_children"
    EMPTY_NEST = "empty_nest"
    RETIREMENT = "retirement"
    LATE_RETIREMENT = "late_retirement"
    
    # Indian-specific life stages
    JOINT_FAMILY = "joint_family"               # Living in extended family
    JOINT_FAMILY_EARNING_MEMBER = "joint_family_earning_member"  # Primary earner in joint family
    JOINT_FAMILY_DEPENDENT = "joint_family_dependent"  # Dependent in joint family
    NRI = "nri"                                 # Non-resident Indian
    RETURNING_NRI = "returning_nri"             # NRI returned to India

class CityTier(Enum):
    """Enum representing different city tiers in India affecting cost of living"""
    TIER_1 = "tier_1"       # Metro cities (Mumbai, Delhi, Bangalore, etc.)
    TIER_2 = "tier_2"       # Smaller cities (Pune, Jaipur, Kochi, etc.)
    TIER_3 = "tier_3"       # Small towns
    RURAL = "rural"         # Villages and rural areas

@dataclass
class EducationPlan:
    """Data class for education expense planning"""
    child_age: int
    current_year: int = 2023
    school_type: str = "private"        # private, public, international
    college_type: str = "private"       # government, private, foreign
    college_stream: str = "engineering" # engineering, medicine, arts, commerce
    target_graduation_year: Optional[int] = None
    coaching_required: bool = False
    education_loan: bool = False
    scholarship_expected: bool = False

@dataclass
class FestivalExpense:
    """Data class for festival-related expenses in Indian context"""
    name: str                              # Festival name (Diwali, Eid, Christmas, etc.)
    month: int                             # Month of occurrence (1-12)
    recurring: bool = True                 # Whether it recurs annually
    clothing_budget: float = 0.0           # Budget for new clothes
    gifts_budget: float = 0.0              # Budget for gifts
    food_budget: float = 0.0               # Budget for special food
    decoration_budget: float = 0.0         # Budget for decorations
    travel_budget: float = 0.0             # Budget for travel
    religious_budget: float = 0.0          # Budget for religious activities
    entertainment_budget: float = 0.0      # Budget for entertainment
    
    def total_budget(self) -> float:
        """Calculate total festival budget"""
        return (self.clothing_budget + self.gifts_budget + self.food_budget +
                self.decoration_budget + self.travel_budget + self.religious_budget +
                self.entertainment_budget)
    
    def to_expense_dict(self) -> Dict[ExpenseCategory, float]:
        """Convert to expense category dictionary"""
        return {
            ExpenseCategory.CLOTHING: self.clothing_budget,
            ExpenseCategory.GIFTS: self.gifts_budget,
            ExpenseCategory.FOOD: self.food_budget,
            ExpenseCategory.ENTERTAINMENT: self.entertainment_budget,
            ExpenseCategory.TRAVEL: self.travel_budget,
            ExpenseCategory.RELIGIOUS: self.religious_budget,
            ExpenseCategory.FESTIVALS: self.decoration_budget
        }

@dataclass
class OneTimeExpense:
    """Data class for major one-time expenses"""
    name: str
    year: int
    month: Optional[int] = None
    amount: float = 0.0
    category: ExpenseCategory = ExpenseCategory.OTHER
    spread_years: int = 1               # Number of years to spread expense (like loan duration)
    probability: float = 1.0            # Probability of expense occurring (0.0-1.0)
    inflation_adjusted: bool = True     # Whether to apply inflation
    recurring_interval: Optional[int] = None  # If it repeats (e.g., every 5 years)

@dataclass
class LifeEvent:
    """Data class representing a life event that affects expenses"""
    year: int
    event_type: str
    description: str
    expense_multipliers: Dict[ExpenseCategory, float] = field(default_factory=dict)
    expense_additions: Dict[ExpenseCategory, float] = field(default_factory=dict)
    one_time_expenses: List[OneTimeExpense] = field(default_factory=list)
    city_tier_change: Optional[CityTier] = None
    life_stage_change: Optional[LifeStage] = None
    
    def apply_to_expenses(self, 
                         current_expenses: Dict[ExpenseCategory, float]) -> Dict[ExpenseCategory, float]:
        """Apply the life event effect to current expenses"""
        updated_expenses = current_expenses.copy()
        
        # Apply multipliers
        for category, multiplier in self.expense_multipliers.items():
            if category in updated_expenses:
                updated_expenses[category] *= multiplier
        
        # Apply additions
        for category, addition in self.expense_additions.items():
            if category in updated_expenses:
                updated_expenses[category] += addition
            else:
                updated_expenses[category] = addition
        
        return updated_expenses

@dataclass
class ExpenseProjectionResult:
    """Data class for storing and visualizing expense projection results"""
    years: List[int]
    expense_values: Dict[ExpenseCategory, List[float]]
    total_expenses: List[float]
    real_expenses: Optional[List[float]] = None
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert expense result to pandas DataFrame for analysis/visualization"""
        data = {
            'Year': self.years,
            'Total_Expenses': self.total_expenses
        }
        
        if self.real_expenses:
            data['Real_Expenses'] = self.real_expenses
        
        # Add individual expense categories
        for category, values in self.expense_values.items():
            data[f'Expense_{category.value.capitalize()}'] = values
        
        return pd.DataFrame(data)

class ExpenseProjection(BaseProjection):
    """
    Class for projecting expenses over time with support for different expense
    categories, category-specific inflation rates, and life stage adjustments.
    
    This class includes specialized support for Indian expense patterns including
    festival expenses, education planning, and city tier-specific costs.
    """
    
    # Default inflation rates by expense category (Indian context)
    DEFAULT_INFLATION_RATES = {
        # Essential expenses
        ExpenseCategory.HOUSING: 0.070,         # 7.0% annual inflation (high in Indian metros)
        ExpenseCategory.FOOD: 0.065,            # 6.5% annual inflation (food inflation in India)
        ExpenseCategory.TRANSPORTATION: 0.050,  # 5.0% annual inflation (fuel price volatility)
        ExpenseCategory.HEALTHCARE: 0.080,      # 8.0% annual inflation (medical inflation in India)
        ExpenseCategory.EDUCATION: 0.100,       # 10.0% annual inflation (very high in India)
        ExpenseCategory.UTILITIES: 0.060,       # 6.0% annual inflation
        ExpenseCategory.INSURANCE: 0.070,       # 7.0% annual inflation
        ExpenseCategory.DEBT_PAYMENTS: 0.000,   # 0.0% annual inflation (fixed payments)
        
        # Discretionary expenses
        ExpenseCategory.ENTERTAINMENT: 0.050,   # 5.0% annual inflation
        ExpenseCategory.CLOTHING: 0.045,        # 4.5% annual inflation
        ExpenseCategory.PERSONAL_CARE: 0.055,   # 5.5% annual inflation
        ExpenseCategory.DINING_OUT: 0.075,      # 7.5% annual inflation
        ExpenseCategory.TRAVEL: 0.060,          # 6.0% annual inflation
        ExpenseCategory.HOBBIES: 0.040,         # 4.0% annual inflation
        ExpenseCategory.SUBSCRIPTIONS: 0.030,   # 3.0% annual inflation
        ExpenseCategory.DISCRETIONARY: 0.050,   # 5.0% annual inflation
        
        # Financial categories
        ExpenseCategory.SAVINGS: 0.000,         # 0.0% annual inflation (not inflation-adjusted)
        ExpenseCategory.INVESTMENTS: 0.000,     # 0.0% annual inflation (not inflation-adjusted)
        ExpenseCategory.TAXES: 0.040,           # 4.0% annual inflation
        
        # Family and social
        ExpenseCategory.CHILDCARE: 0.090,       # 9.0% annual inflation (high in urban India)
        ExpenseCategory.ELDERCARE: 0.085,       # 8.5% annual inflation
        ExpenseCategory.CHARITY: 0.045,         # 4.5% annual inflation
        ExpenseCategory.GIFTS: 0.050,           # 5.0% annual inflation
        
        # Indian-specific categories
        ExpenseCategory.WEDDING: 0.120,         # 12.0% annual inflation (very high in India)
        ExpenseCategory.FESTIVALS: 0.070,       # 7.0% annual inflation
        ExpenseCategory.RELIGIOUS: 0.060,       # 6.0% annual inflation
        ExpenseCategory.DOMESTIC_HELP: 0.080,   # 8.0% annual inflation (rising wages)
        
        # Other
        ExpenseCategory.OTHER: 0.055,           # 5.5% annual inflation
    }
    
    # Expense multipliers by city tier in India
    CITY_TIER_MULTIPLIERS = {
        CityTier.TIER_1: {
            ExpenseCategory.HOUSING: 2.5,       # 150% more expensive than average
            ExpenseCategory.FOOD: 1.4,          # 40% more expensive
            ExpenseCategory.TRANSPORTATION: 1.3, # 30% more expensive
            ExpenseCategory.EDUCATION: 1.8,     # 80% more expensive
            ExpenseCategory.HEALTHCARE: 1.5,    # 50% more expensive
            ExpenseCategory.DOMESTIC_HELP: 1.6,  # 60% more expensive
        },
        CityTier.TIER_2: {
            ExpenseCategory.HOUSING: 1.3,       # 30% more expensive than average
            ExpenseCategory.FOOD: 1.1,          # 10% more expensive
            ExpenseCategory.EDUCATION: 1.3,     # 30% more expensive
        },
        CityTier.TIER_3: {
            # Reference level (1.0)
        },
        CityTier.RURAL: {
            ExpenseCategory.HOUSING: 0.6,       # 40% cheaper than average
            ExpenseCategory.FOOD: 0.8,          # 20% cheaper
            ExpenseCategory.TRANSPORTATION: 1.2, # 20% more expensive (due to distance)
            ExpenseCategory.EDUCATION: 0.7,     # 30% cheaper
            ExpenseCategory.HEALTHCARE: 0.7,    # 30% cheaper
            ExpenseCategory.DOMESTIC_HELP: 0.7,  # 30% cheaper
        }
    }
    
    # Indian education costs by type (annual in INR)
    EDUCATION_COSTS = {
        "school": {
            "public": 15000,                 # Government school
            "private": 120000,               # Average private school
            "international": 500000,         # International school
        },
        "college": {
            "government": {
                "arts": 20000,               # Government college - Arts/Commerce
                "science": 35000,            # Government college - Science
                "engineering": 80000,        # Government engineering college
                "medicine": 100000,          # Government medical college
                "management": 50000,         # Government management program
            },
            "private": {
                "arts": 100000,              # Private college - Arts/Commerce
                "science": 150000,           # Private college - Science
                "engineering": 400000,       # Private engineering college
                "medicine": 1200000,         # Private medical college
                "management": 600000,        # Private management program
            },
            "foreign": {
                "us": 5000000,               # US university (approx.)
                "uk": 4000000,               # UK university (approx.)
                "australia": 3500000,        # Australian university (approx.)
                "canada": 3000000,           # Canadian university (approx.)
                "europe": 2500000,           # European university (approx.)
                "singapore": 3000000,        # Singapore university (approx.)
            }
        },
        "coaching": {
            "iit_jee": 300000,               # IIT-JEE coaching
            "neet": 250000,                  # NEET (medical) coaching
            "upsc": 200000,                  # Civil services coaching
            "cat": 150000,                   # CAT (MBA) coaching
            "general": 80000,                # General coaching
        }
    }
    
    # Typical festival expenses as percentage of monthly income
    FESTIVAL_EXPENSE_RATIOS = {
        "diwali": 0.80,                     # 80% of monthly income
        "eid": 0.75,                        # 75% of monthly income
        "christmas": 0.70,                  # 70% of monthly income
        "navratri": 0.40,                   # 40% of monthly income
        "durga_puja": 0.60,                 # 60% of monthly income
        "holi": 0.25,                       # 25% of monthly income
        "raksha_bandhan": 0.15,             # 15% of monthly income
        "onam": 0.40,                       # 40% of monthly income
        "pongal": 0.35,                     # 35% of monthly income
        "ganesh_chaturthi": 0.30,           # 30% of monthly income
        "other": 0.10,                      # 10% of monthly income
    }
    
    # Life stage expense multipliers (relative to SINGLE)
    LIFE_STAGE_MULTIPLIERS = {
        LifeStage.SINGLE: {
            # Baseline
        },
        LifeStage.COUPLE: {
            ExpenseCategory.HOUSING: 1.3,       # 30% increase
            ExpenseCategory.FOOD: 1.7,          # 70% increase
            ExpenseCategory.TRANSPORTATION: 1.5, # 50% increase
            ExpenseCategory.HEALTHCARE: 2.0,    # 100% increase (two people)
            ExpenseCategory.UTILITIES: 1.2,     # 20% increase
            ExpenseCategory.ENTERTAINMENT: 1.8,  # 80% increase
        },
        LifeStage.FAMILY_YOUNG_CHILDREN: {
            ExpenseCategory.HOUSING: 1.5,       # 50% increase
            ExpenseCategory.FOOD: 2.2,          # 120% increase
            ExpenseCategory.TRANSPORTATION: 1.8, # 80% increase
            ExpenseCategory.HEALTHCARE: 2.5,    # 150% increase
            ExpenseCategory.EDUCATION: 3.0,     # 200% increase
            ExpenseCategory.UTILITIES: 1.5,     # 50% increase
            ExpenseCategory.CHILDCARE: 10.0,    # Added expense (multiplier from zero)
        },
        LifeStage.FAMILY_TEENAGE_CHILDREN: {
            ExpenseCategory.HOUSING: 1.6,       # 60% increase
            ExpenseCategory.FOOD: 2.5,          # 150% increase
            ExpenseCategory.TRANSPORTATION: 2.0, # 100% increase
            ExpenseCategory.HEALTHCARE: 2.5,    # 150% increase
            ExpenseCategory.EDUCATION: 5.0,     # 400% increase (college prep, activities)
            ExpenseCategory.UTILITIES: 1.8,     # 80% increase
        },
        LifeStage.EMPTY_NEST: {
            ExpenseCategory.HOUSING: 1.2,       # 20% increase
            ExpenseCategory.FOOD: 1.5,          # 50% increase
            ExpenseCategory.TRANSPORTATION: 1.3, # 30% increase
            ExpenseCategory.HEALTHCARE: 2.2,    # 120% increase (aging)
            ExpenseCategory.UTILITIES: 1.3,     # 30% increase
            ExpenseCategory.TRAVEL: 2.0,        # 100% increase
        },
        LifeStage.RETIREMENT: {
            ExpenseCategory.HOUSING: 1.0,       # No change
            ExpenseCategory.FOOD: 1.3,          # 30% increase
            ExpenseCategory.TRANSPORTATION: 0.7, # 30% decrease
            ExpenseCategory.HEALTHCARE: 2.5,    # 150% increase
            ExpenseCategory.UTILITIES: 1.2,     # 20% increase
            ExpenseCategory.TRAVEL: 1.8,        # 80% increase
            ExpenseCategory.ENTERTAINMENT: 1.5,  # 50% increase
        },
        LifeStage.LATE_RETIREMENT: {
            ExpenseCategory.HOUSING: 1.0,       # No change
            ExpenseCategory.FOOD: 1.2,          # 20% increase
            ExpenseCategory.TRANSPORTATION: 0.5, # 50% decrease
            ExpenseCategory.HEALTHCARE: 3.0,    # 200% increase
            ExpenseCategory.UTILITIES: 1.2,     # 20% increase
            ExpenseCategory.TRAVEL: 0.8,        # 20% decrease
            ExpenseCategory.ELDERCARE: 5.0,     # Added expense (multiplier from zero)
        },
    }
    
    def __init__(self, 
                parameters=None, 
                general_inflation_rate: float = 0.03,
                use_category_inflation: bool = True,
                current_life_stage: Union[str, LifeStage] = LifeStage.SINGLE,
                seed: Optional[int] = None):
        """
        Initialize the expense projection model.
        
        Parameters:
        -----------
        parameters : object, optional
            Financial parameters object for accessing system settings
        general_inflation_rate : float, default 0.03
            General inflation rate to use when category-specific rates are not available
        use_category_inflation : bool, default True
            Whether to use category-specific inflation rates
        current_life_stage : str or LifeStage, default LifeStage.SINGLE
            Current life stage for expense modeling
        seed : int, optional
            Random seed for Monte Carlo simulations
        """
        super().__init__(parameters)
        
        self.general_inflation_rate = general_inflation_rate
        self.use_category_inflation = use_category_inflation
        
        # Convert life_stage to enum if it's a string
        if isinstance(current_life_stage, str):
            try:
                self.current_life_stage = LifeStage(current_life_stage)
            except ValueError:
                logger.warning(f"Invalid life stage: {current_life_stage}. Using SINGLE instead.")
                self.current_life_stage = LifeStage.SINGLE
        else:
            self.current_life_stage = current_life_stage
        
        # Set random seed if provided
        if seed is not None:
            np.random.seed(seed)
    
    def extract_expense_data(self, profile: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract expense data from a user profile.
        
        Parameters:
        -----------
        profile : Dict[str, Any]
            User profile data
            
        Returns:
        --------
        Dict[str, float]
            Dictionary mapping expense categories to monthly amounts
        """
        expense_data = {}
        
        # Extract total monthly expenses if available
        total_expenses = self._extract_value_from_profile(
            profile, 
            ['monthly_expenses', 'total_expenses', 'expenses.total']
        )
        
        # Extract individual expense categories
        housing = self._extract_value_from_profile(
            profile, 
            ['housing_expense', 'rent', 'mortgage', 'expenses.housing']
        )
        if housing is not None:
            expense_data['housing'] = housing
        
        food = self._extract_value_from_profile(
            profile, 
            ['food_expense', 'groceries', 'dining_out', 'expenses.food']
        )
        if food is not None:
            expense_data['food'] = food
        
        transportation = self._extract_value_from_profile(
            profile, 
            ['transportation_expense', 'car_payment', 'fuel', 'public_transport', 'expenses.transportation']
        )
        if transportation is not None:
            expense_data['transportation'] = transportation
        
        healthcare = self._extract_value_from_profile(
            profile, 
            ['healthcare_expense', 'medical', 'expenses.healthcare']
        )
        if healthcare is not None:
            expense_data['healthcare'] = healthcare
        
        utilities = self._extract_value_from_profile(
            profile, 
            ['utilities_expense', 'electricity', 'water', 'gas', 'internet', 'expenses.utilities']
        )
        if utilities is not None:
            expense_data['utilities'] = utilities
        
        education = self._extract_value_from_profile(
            profile, 
            ['education_expense', 'tuition', 'expenses.education']
        )
        if education is not None:
            expense_data['education'] = education
        
        entertainment = self._extract_value_from_profile(
            profile, 
            ['entertainment_expense', 'recreation', 'expenses.entertainment']
        )
        if entertainment is not None:
            expense_data['entertainment'] = entertainment
        
        debt_payments = self._extract_value_from_profile(
            profile, 
            ['debt_payments', 'loan_payments', 'credit_card_payments', 'expenses.debt_payments']
        )
        if debt_payments is not None:
            expense_data['debt_payments'] = debt_payments
        
        childcare = self._extract_value_from_profile(
            profile, 
            ['childcare_expense', 'daycare', 'expenses.childcare']
        )
        if childcare is not None:
            expense_data['childcare'] = childcare
        
        # If we have total expenses but missing individual categories,
        # allocate the remaining amount to "other"
        if total_expenses is not None:
            extracted_total = sum(expense_data.values())
            if extracted_total < total_expenses:
                expense_data['other'] = total_expenses - extracted_total
        
        return expense_data
    
    def categorize_expenses(self, expense_data: Dict[str, float]) -> Dict[ExpenseCategory, float]:
        """
        Categorize expense data into standard expense categories.
        
        Parameters:
        -----------
        expense_data : Dict[str, float]
            Dictionary of expense data with string keys
            
        Returns:
        --------
        Dict[ExpenseCategory, float]
            Dictionary with categorized expenses
        """
        categorized_expenses = {}
        
        # Map of common expense names to ExpenseCategory enum values
        category_mapping = {
            'housing': ExpenseCategory.HOUSING,
            'rent': ExpenseCategory.HOUSING,
            'mortgage': ExpenseCategory.HOUSING,
            
            'food': ExpenseCategory.FOOD,
            'groceries': ExpenseCategory.FOOD,
            'dining_out': ExpenseCategory.FOOD,
            
            'transportation': ExpenseCategory.TRANSPORTATION,
            'car_payment': ExpenseCategory.TRANSPORTATION,
            'fuel': ExpenseCategory.TRANSPORTATION,
            'public_transport': ExpenseCategory.TRANSPORTATION,
            
            'healthcare': ExpenseCategory.HEALTHCARE,
            'medical': ExpenseCategory.HEALTHCARE,
            'health_insurance': ExpenseCategory.HEALTHCARE,
            
            'education': ExpenseCategory.EDUCATION,
            'tuition': ExpenseCategory.EDUCATION,
            'school': ExpenseCategory.EDUCATION,
            
            'entertainment': ExpenseCategory.ENTERTAINMENT,
            'recreation': ExpenseCategory.ENTERTAINMENT,
            'hobbies': ExpenseCategory.ENTERTAINMENT,
            
            'clothing': ExpenseCategory.CLOTHING,
            'apparel': ExpenseCategory.CLOTHING,
            
            'personal_care': ExpenseCategory.PERSONAL_CARE,
            'grooming': ExpenseCategory.PERSONAL_CARE,
            
            'utilities': ExpenseCategory.UTILITIES,
            'electricity': ExpenseCategory.UTILITIES,
            'water': ExpenseCategory.UTILITIES,
            'gas': ExpenseCategory.UTILITIES,
            'internet': ExpenseCategory.UTILITIES,
            'phone': ExpenseCategory.UTILITIES,
            
            'insurance': ExpenseCategory.INSURANCE,
            'life_insurance': ExpenseCategory.INSURANCE,
            'home_insurance': ExpenseCategory.INSURANCE,
            'car_insurance': ExpenseCategory.INSURANCE,
            
            'debt_payments': ExpenseCategory.DEBT_PAYMENTS,
            'loan_payments': ExpenseCategory.DEBT_PAYMENTS,
            'credit_card_payments': ExpenseCategory.DEBT_PAYMENTS,
            
            'discretionary': ExpenseCategory.DISCRETIONARY,
            'misc': ExpenseCategory.DISCRETIONARY,
            
            'savings': ExpenseCategory.SAVINGS,
            'emergency_fund': ExpenseCategory.SAVINGS,
            
            'investments': ExpenseCategory.INVESTMENTS,
            'stocks': ExpenseCategory.INVESTMENTS,
            'mutual_funds': ExpenseCategory.INVESTMENTS,
            
            'taxes': ExpenseCategory.TAXES,
            'property_tax': ExpenseCategory.TAXES,
            
            'childcare': ExpenseCategory.CHILDCARE,
            'daycare': ExpenseCategory.CHILDCARE,
            'babysitting': ExpenseCategory.CHILDCARE,
            
            'eldercare': ExpenseCategory.ELDERCARE,
            'senior_care': ExpenseCategory.ELDERCARE,
            
            'charity': ExpenseCategory.CHARITY,
            'donations': ExpenseCategory.CHARITY,
            'giving': ExpenseCategory.CHARITY,
            
            'travel': ExpenseCategory.TRAVEL,
            'vacation': ExpenseCategory.TRAVEL,
            
            'other': ExpenseCategory.OTHER
        }
        
        # Process each expense category
        for key, amount in expense_data.items():
            # Normalize key to lowercase and remove spaces
            normalized_key = key.lower().replace(' ', '_')
            
            # Check if key matches any known categories
            if normalized_key in category_mapping:
                expense_category = category_mapping[normalized_key]
            else:
                # Try to find a partial match
                found = False
                for mapping_key, category_value in category_mapping.items():
                    if mapping_key in normalized_key:
                        expense_category = category_value
                        found = True
                        break
                
                # Default to OTHER if no match found
                if not found:
                    expense_category = ExpenseCategory.OTHER
            
            # Add to categorized expenses (summing if multiple sources map to same enum)
            if expense_category in categorized_expenses:
                categorized_expenses[expense_category] += amount
            else:
                categorized_expenses[expense_category] = amount
        
        return categorized_expenses
    
    def project_expenses(self,
                        monthly_expenses: Union[float, Dict[Union[str, ExpenseCategory], float]],
                        years: int,
                        frequency: Union[str, FrequencyType] = FrequencyType.MONTHLY,
                        include_inflation: bool = True,
                        real_values: bool = False) -> ExpenseProjectionResult:
        """
        Project expenses over time with optional inflation adjustment.
        
        Parameters:
        -----------
        monthly_expenses : float or Dict
            Monthly expenses amount (total or by category)
        years : int
            Number of years to project
        frequency : str or FrequencyType, default FrequencyType.MONTHLY
            Frequency of expense values provided
        include_inflation : bool, default True
            Whether to apply inflation to expenses
        real_values : bool, default False
            Whether to include inflation-adjusted (real) values in addition to nominal
            
        Returns:
        --------
        ExpenseProjectionResult
            Object containing expense projection results
        """
        # Convert frequency to enum if it's a string
        if isinstance(frequency, str):
            try:
                frequency = FrequencyType(frequency)
            except ValueError:
                logger.warning(f"Invalid frequency: {frequency}. Using MONTHLY instead.")
                frequency = FrequencyType.MONTHLY
        
        # Process input expenses
        if isinstance(monthly_expenses, (int, float)):
            # Single total expense value
            annualized_expenses = monthly_expenses * (12 / self._get_periods_per_year(frequency))
            expense_categories = {ExpenseCategory.OTHER: annualized_expenses}
        else:
            # Expenses by category
            expense_categories = {}
            
            # Convert string keys to ExpenseCategory enum if needed
            for key, value in monthly_expenses.items():
                if isinstance(key, str):
                    try:
                        key = ExpenseCategory(key)
                    except ValueError:
                        # Try to find a matching category
                        categorized = self.categorize_expenses({key: value})
                        if categorized:
                            # Use the first categorized key
                            key = next(iter(categorized))
                        else:
                            # Default to OTHER if no match found
                            key = ExpenseCategory.OTHER
                
                # Convert to annual amount based on frequency
                annualized_value = value * (12 / self._get_periods_per_year(frequency))
                expense_categories[key] = annualized_value
        
        # Initialize result containers
        years_list = list(range(years + 1))
        expense_values = {category: [amount] for category, amount in expense_categories.items()}
        total_expenses = [sum(expense_categories.values())]
        
        # Current values for tracking
        current_expenses = expense_categories.copy()
        
        # Project expenses year by year
        for year in range(1, years + 1):
            year_total = 0
            
            # Project each expense category
            for category, current_amount in list(current_expenses.items()):
                # Apply inflation if enabled
                if include_inflation:
                    inflation_rate = self._get_inflation_rate(category)
                    new_amount = current_amount * (1 + inflation_rate)
                else:
                    new_amount = current_amount
                
                # Update current amount
                current_expenses[category] = new_amount
                expense_values[category].append(new_amount)
                year_total += new_amount
            
            # Add to total expenses
            total_expenses.append(year_total)
        
        # Create result object
        result = ExpenseProjectionResult(
            years=years_list,
            expense_values=expense_values,
            total_expenses=total_expenses
        )
        
        # Calculate real values if requested
        if real_values and include_inflation:
            real_expenses = self.apply_inflation_adjustment(
                total_expenses,
                years_list,
                self.general_inflation_rate
            )
            result.real_expenses = real_expenses
        
        return result
    
    def apply_category_inflation(self,
                               projection: ExpenseProjectionResult,
                               category_rates: Optional[Dict[ExpenseCategory, float]] = None) -> ExpenseProjectionResult:
        """
        Apply category-specific inflation rates to an expense projection.
        
        Parameters:
        -----------
        projection : ExpenseProjectionResult
            Original expense projection
        category_rates : Dict[ExpenseCategory, float], optional
            Dictionary mapping expense categories to inflation rates
            
        Returns:
        --------
        ExpenseProjectionResult
            Expense projection with category-specific inflation applied
        """
        # Use default rates if not provided
        if category_rates is None:
            if self.use_category_inflation:
                category_rates = {cat: self._get_inflation_rate(cat) for cat in projection.expense_values.keys()}
            else:
                # Use general inflation for all categories
                category_rates = {cat: self.general_inflation_rate for cat in projection.expense_values.keys()}
        
        # Create copy of original projection data
        updated_values = {}
        for category, values in projection.expense_values.items():
            updated_values[category] = values.copy()
        
        # Apply inflation rates to each category
        for category, values in updated_values.items():
            # Get inflation rate for this category
            inflation_rate = category_rates.get(category, self.general_inflation_rate)
            
            # Apply cumulative inflation starting from year 1
            for year_idx in range(1, len(values)):
                cumulative_factor = (1 + inflation_rate) ** year_idx
                updated_values[category][year_idx] = values[0] * cumulative_factor
        
        # Recalculate total expenses
        updated_total = []
        for year_idx in range(len(projection.years)):
            year_total = sum(values[year_idx] for values in updated_values.values() if year_idx < len(values))
            updated_total.append(year_total)
        
        # Create updated result
        return ExpenseProjectionResult(
            years=projection.years,
            expense_values=updated_values,
            total_expenses=updated_total
        )
    
    def adjust_for_life_stage(self,
                            projection: ExpenseProjectionResult,
                            life_events: List[LifeEvent]) -> ExpenseProjectionResult:
        """
        Adjust expense projection based on life events and life stages.
        
        Parameters:
        -----------
        projection : ExpenseProjectionResult
            Original expense projection
        life_events : List[LifeEvent]
            List of life events that affect expenses
            
        Returns:
        --------
        ExpenseProjectionResult
            Adjusted expense projection
        """
        # Sort life events by year
        sorted_events = sorted(life_events, key=lambda e: e.year)
        
        # Create copy of original projection data
        updated_values = {}
        for category, values in projection.expense_values.items():
            updated_values[category] = values.copy()
        
        # Track current expense levels
        current_expenses = {
            category: values[0] 
            for category, values in projection.expense_values.items()
        }
        
        # Apply life events to expenses
        for event in sorted_events:
            # Skip events beyond projection range
            if event.year >= len(projection.years):
                continue
            
            # Apply event effect to current expenses
            updated_current = event.apply_to_expenses(current_expenses)
            
            # Calculate difference from current expenses
            for category, new_amount in updated_current.items():
                # Ensure category exists in updated values
                if category not in updated_values:
                    # Initialize with zeros
                    updated_values[category] = [0] * len(projection.years)
                    # Set initial value based on first year's expenses
                    if len(updated_values[category]) > 0:
                        updated_values[category][0] = current_expenses.get(category, 0)
                
                # Calculate relative change
                old_amount = current_expenses.get(category, 0)
                if old_amount != 0:
                    relative_change = new_amount / old_amount
                else:
                    relative_change = 1.0
                
                # Apply change to all future years
                for year_idx in range(event.year, len(projection.years)):
                    if year_idx < len(updated_values[category]):
                        # Maintain inflation trajectory by scaling rather than replacing
                        updated_values[category][year_idx] *= relative_change
                    else:
                        # Extend list if needed
                        updated_values[category].append(new_amount)
            
            # Update current expenses
            current_expenses = updated_current
        
        # Recalculate total expenses
        updated_total = []
        for year_idx in range(len(projection.years)):
            year_total = sum(
                values[year_idx] 
                for values in updated_values.values() 
                if year_idx < len(values)
            )
            updated_total.append(year_total)
        
        # Create updated result
        return ExpenseProjectionResult(
            years=projection.years,
            expense_values=updated_values,
            total_expenses=updated_total
        )
    
    def project_retirement_expenses(self,
                                  pre_retirement_expenses: Union[float, Dict[Union[str, ExpenseCategory], float]],
                                  years_to_retirement: int,
                                  retirement_years: int,
                                  retirement_expense_ratio: float = 0.8,
                                  category_adjustments: Optional[Dict[ExpenseCategory, float]] = None) -> ExpenseProjectionResult:
        """
        Project expenses through retirement with appropriate adjustments.
        
        Parameters:
        -----------
        pre_retirement_expenses : float or Dict
            Current monthly expenses (total or by category)
        years_to_retirement : int
            Number of years until retirement
        retirement_years : int
            Number of years in retirement to project
        retirement_expense_ratio : float, default 0.8
            Ratio of retirement expenses to pre-retirement expenses (if not by category)
        category_adjustments : Dict[ExpenseCategory, float], optional
            Dictionary mapping expense categories to retirement adjustment factors
            
        Returns:
        --------
        ExpenseProjectionResult
            Projection of expenses through retirement
        """
        # Set default category adjustments if not provided
        if category_adjustments is None:
            category_adjustments = {
                ExpenseCategory.HOUSING: 0.9,        # 10% decrease
                ExpenseCategory.FOOD: 1.0,           # No change
                ExpenseCategory.TRANSPORTATION: 0.7,  # 30% decrease
                ExpenseCategory.HEALTHCARE: 1.5,     # 50% increase
                ExpenseCategory.ENTERTAINMENT: 1.2,  # 20% increase
                ExpenseCategory.TRAVEL: 1.3,         # 30% increase
                ExpenseCategory.DEBT_PAYMENTS: 0.5,  # 50% decrease (assuming most debts paid off)
            }
        
        # Total projection years
        total_years = years_to_retirement + retirement_years
        
        # First, project pre-retirement expenses
        pre_retirement_projection = self.project_expenses(
            monthly_expenses=pre_retirement_expenses,
            years=years_to_retirement,
            include_inflation=True
        )
        
        # Get expenses at retirement
        retirement_expenses = {}
        for category, values in pre_retirement_projection.expense_values.items():
            if years_to_retirement < len(values):
                # Get expense at retirement and apply category-specific adjustment
                adjustment = category_adjustments.get(category, retirement_expense_ratio)
                retirement_expenses[category] = values[years_to_retirement] * adjustment
        
        # If no category-specific data, use the total with adjustment
        if not retirement_expenses and years_to_retirement < len(pre_retirement_projection.total_expenses):
            retirement_expenses[ExpenseCategory.OTHER] = (
                pre_retirement_projection.total_expenses[years_to_retirement] * 
                retirement_expense_ratio
            )
        
        # Project retirement expenses
        retirement_projection = self.project_expenses(
            monthly_expenses=retirement_expenses,
            years=retirement_years,
            frequency=FrequencyType.ANNUAL,  # Already annualized
            include_inflation=True
        )
        
        # Combine pre-retirement and retirement projections
        combined_years = list(range(total_years + 1))
        combined_expense_values = {}
        
        # Process each expense category
        all_categories = set(list(pre_retirement_projection.expense_values.keys()) + 
                           list(retirement_projection.expense_values.keys()))
        
        for category in all_categories:
            combined_values = []
            
            # Add pre-retirement values
            if category in pre_retirement_projection.expense_values:
                combined_values.extend(pre_retirement_projection.expense_values[category])
            else:
                combined_values.extend([0] * (years_to_retirement + 1))
            
            # Add retirement values (skipping first value which overlaps)
            if category in retirement_projection.expense_values:
                combined_values.extend(retirement_projection.expense_values[category][1:])
            else:
                combined_values.extend([0] * retirement_years)
            
            combined_expense_values[category] = combined_values
        
        # Combine total expenses
        combined_total = (
            pre_retirement_projection.total_expenses + 
            retirement_projection.total_expenses[1:]
        )
        
        # Create combined result
        return ExpenseProjectionResult(
            years=combined_years,
            expense_values=combined_expense_values,
            total_expenses=combined_total
        )
    
    def generate_typical_expenses(self,
                                household_income: float,
                                household_size: int = 1,
                                location_factor: float = 1.0,
                                life_stage: Optional[Union[str, LifeStage]] = None) -> Dict[ExpenseCategory, float]:
        """
        Generate typical expense distribution based on income and household characteristics.
        
        Parameters:
        -----------
        household_income : float
            Annual household income
        household_size : int, default 1
            Number of people in household
        location_factor : float, default 1.0
            Cost of living factor (1.0 is average, higher means more expensive)
        life_stage : str or LifeStage, optional
            Life stage (defaults to instance's current_life_stage)
            
        Returns:
        --------
        Dict[ExpenseCategory, float]
            Dictionary mapping expense categories to typical monthly amounts
        """
        # Use instance life stage if not provided
        if life_stage is None:
            life_stage = self.current_life_stage
        
        # Convert life_stage to enum if it's a string
        if isinstance(life_stage, str):
            try:
                life_stage = LifeStage(life_stage)
            except ValueError:
                logger.warning(f"Invalid life stage: {life_stage}. Using {self.current_life_stage.value} instead.")
                life_stage = self.current_life_stage
        
        # Calculate monthly income
        monthly_income = household_income / 12
        
        # Base expense ratios as percentages of income
        base_expense_ratios = {
            ExpenseCategory.HOUSING: 0.30,        # 30% of income
            ExpenseCategory.FOOD: 0.12,           # 12% of income
            ExpenseCategory.TRANSPORTATION: 0.10,  # 10% of income
            ExpenseCategory.HEALTHCARE: 0.07,     # 7% of income
            ExpenseCategory.UTILITIES: 0.05,      # 5% of income
            ExpenseCategory.DEBT_PAYMENTS: 0.10,  # 10% of income
            ExpenseCategory.ENTERTAINMENT: 0.05,  # 5% of income
            ExpenseCategory.PERSONAL_CARE: 0.03,  # 3% of income
            ExpenseCategory.CLOTHING: 0.03,       # 3% of income
            ExpenseCategory.INSURANCE: 0.05,      # 5% of income
            ExpenseCategory.SAVINGS: 0.10,        # 10% of income (recommended)
        }
        
        # Adjust ratios based on household size
        if household_size > 1:
            # These categories scale with household size (but not linearly)
            scaling_factor = 1 + (household_size - 1) * 0.5  # Add 50% for each additional person
            base_expense_ratios[ExpenseCategory.FOOD] *= scaling_factor
            base_expense_ratios[ExpenseCategory.HEALTHCARE] *= scaling_factor
            base_expense_ratios[ExpenseCategory.PERSONAL_CARE] *= scaling_factor
            base_expense_ratios[ExpenseCategory.CLOTHING] *= scaling_factor
        
        # Apply location factor to housing, food, transportation
        base_expense_ratios[ExpenseCategory.HOUSING] *= location_factor
        base_expense_ratios[ExpenseCategory.FOOD] *= location_factor
        base_expense_ratios[ExpenseCategory.TRANSPORTATION] *= location_factor
        
        # Add life stage specific expenses
        if life_stage == LifeStage.FAMILY_YOUNG_CHILDREN:
            base_expense_ratios[ExpenseCategory.CHILDCARE] = 0.12  # 12% of income
            base_expense_ratios[ExpenseCategory.EDUCATION] = 0.05  # 5% of income
        elif life_stage == LifeStage.FAMILY_TEENAGE_CHILDREN:
            base_expense_ratios[ExpenseCategory.EDUCATION] = 0.12  # 12% of income
        elif life_stage == LifeStage.RETIREMENT:
            # Remove childcare and redistribute
            base_expense_ratios.pop(ExpenseCategory.CHILDCARE, None)
            base_expense_ratios[ExpenseCategory.HEALTHCARE] = 0.12  # 12% of income
            base_expense_ratios[ExpenseCategory.TRAVEL] = 0.07      # 7% of income
        elif life_stage == LifeStage.LATE_RETIREMENT:
            base_expense_ratios.pop(ExpenseCategory.CHILDCARE, None)
            base_expense_ratios[ExpenseCategory.HEALTHCARE] = 0.18  # 18% of income
            base_expense_ratios[ExpenseCategory.ELDERCARE] = 0.10   # 10% of income
        
        # Calculate monetary values
        monthly_expenses = {}
        for category, ratio in base_expense_ratios.items():
            monthly_expenses[category] = monthly_income * ratio
        
        return monthly_expenses
    
    def _get_inflation_rate(self, category: ExpenseCategory) -> float:
        """
        Get the inflation rate for a specific expense category.
        
        Parameters:
        -----------
        category : ExpenseCategory
            Expense category
            
        Returns:
        --------
        float
            Inflation rate for the category
        """
        # Try to get from parameters first
        param_path = f"inflation.{category.value}"
        rate = self.get_parameter(param_path)
        
        if rate is not None:
            return rate
        
        # If category-specific inflation is enabled, use default rates
        if self.use_category_inflation:
            return self.DEFAULT_INFLATION_RATES.get(category, self.general_inflation_rate)
        else:
            return self.general_inflation_rate
    
    def project_essential_expenses(self,
                              monthly_expenses: Dict[ExpenseCategory, float],
                              years: int,
                              city_tier: Union[str, CityTier] = None,
                              life_stage: Union[str, LifeStage] = None) -> Dict[ExpenseCategory, List[float]]:
        """
        Project essential expenses over time with category-specific adjustments.
        
        Parameters:
        -----------
        monthly_expenses : Dict[ExpenseCategory, float]
            Monthly essential expenses by category
        years : int
            Number of years to project
        city_tier : str or CityTier, optional
            City tier for location-based adjustments
        life_stage : str or LifeStage, optional
            Life stage for demographics-based adjustments
            
        Returns:
        --------
        Dict[ExpenseCategory, List[float]]
            Projection of essential expenses by category
        """
        # Determine which categories are essential
        essential_categories = [
            ExpenseCategory.HOUSING,
            ExpenseCategory.FOOD,
            ExpenseCategory.TRANSPORTATION,
            ExpenseCategory.HEALTHCARE,
            ExpenseCategory.UTILITIES,
            ExpenseCategory.INSURANCE,
            ExpenseCategory.EDUCATION,
            ExpenseCategory.DEBT_PAYMENTS,
            ExpenseCategory.CHILDCARE,
            ExpenseCategory.ELDERCARE
        ]
        
        # Filter for essential expenses only
        essential_expenses = {
            category: amount 
            for category, amount in monthly_expenses.items()
            if category in essential_categories
        }
        
        # Convert city tier to enum if needed
        if isinstance(city_tier, str):
            try:
                city_tier = CityTier(city_tier)
            except (ValueError, TypeError):
                city_tier = None
        
        # Apply city tier multipliers if available
        if city_tier is not None and city_tier in self.CITY_TIER_MULTIPLIERS:
            multipliers = self.CITY_TIER_MULTIPLIERS[city_tier]
            for category, multiplier in multipliers.items():
                if category in essential_expenses:
                    essential_expenses[category] *= multiplier
        
        # Project expenses with inflation
        result = {}
        for category, amount in essential_expenses.items():
            inflation_rate = self._get_inflation_rate(category)
            category_result = [amount]  # Initial value
            
            for year in range(1, years + 1):
                next_value = category_result[-1] * (1 + inflation_rate)
                category_result.append(next_value)
            
            result[category] = category_result
            
        return result

    def project_discretionary_expenses(self,
                                    monthly_expenses: Dict[ExpenseCategory, float],
                                    years: int,
                                    income_growth_rate: float = 0.03,
                                    lifestyle_inflation: bool = True) -> Dict[ExpenseCategory, List[float]]:
        """
        Project discretionary expenses over time with lifestyle inflation option.
        
        Parameters:
        -----------
        monthly_expenses : Dict[ExpenseCategory, float]
            Monthly discretionary expenses by category
        years : int
            Number of years to project
        income_growth_rate : float, default 0.03
            Annual income growth rate for lifestyle inflation
        lifestyle_inflation : bool, default True
            Whether to model lifestyle inflation tied to income
            
        Returns:
        --------
        Dict[ExpenseCategory, List[float]]
            Projection of discretionary expenses by category
        """
        # Determine which categories are discretionary
        discretionary_categories = [
            ExpenseCategory.ENTERTAINMENT,
            ExpenseCategory.CLOTHING,
            ExpenseCategory.PERSONAL_CARE,
            ExpenseCategory.DINING_OUT,
            ExpenseCategory.TRAVEL,
            ExpenseCategory.HOBBIES,
            ExpenseCategory.SUBSCRIPTIONS,
            ExpenseCategory.DISCRETIONARY,
            ExpenseCategory.GIFTS,
            ExpenseCategory.CHARITY,
            ExpenseCategory.FESTIVALS,
            ExpenseCategory.RELIGIOUS
        ]
        
        # Filter for discretionary expenses only
        discretionary_expenses = {
            category: amount 
            for category, amount in monthly_expenses.items()
            if category in discretionary_categories
        }
        
        # Project expenses
        result = {}
        for category, amount in discretionary_expenses.items():
            # Get category-specific inflation rate
            inflation_rate = self._get_inflation_rate(category)
            
            # Add lifestyle inflation if enabled
            if lifestyle_inflation:
                # Model lifestyle inflation as a portion of income growth
                # (discretionary spending tends to grow with income)
                lifestyle_factor = 0.5  # Discretionary spending grows at 50% of income growth rate
                effective_rate = inflation_rate + (income_growth_rate * lifestyle_factor)
            else:
                effective_rate = inflation_rate
            
            # Project values
            category_result = [amount]  # Initial value
            for year in range(1, years + 1):
                next_value = category_result[-1] * (1 + effective_rate)
                category_result.append(next_value)
            
            result[category] = category_result
            
        return result
    
    def project_healthcare_expenses(self,
                                 base_expense: float,
                                 years: int,
                                 age: int = 30,
                                 health_conditions: List[str] = None) -> List[float]:
        """
        Project healthcare expenses with age-based adjustments.
        
        Parameters:
        -----------
        base_expense : float
            Current monthly healthcare expense
        years : int
            Number of years to project
        age : int, default 30
            Current age for age-based adjustments
        health_conditions : List[str], optional
            List of health conditions affecting projections
            
        Returns:
        --------
        List[float]
            Projected healthcare expenses
        """
        # Base healthcare inflation rate
        healthcare_inflation = self._get_inflation_rate(ExpenseCategory.HEALTHCARE)
        
        # Age-based adjustments (healthcare costs increase more with age)
        age_adjustment_factors = {
            (0, 30): 0.0,      # No extra adjustment for young adults
            (31, 40): 0.005,   # +0.5% annual growth for 31-40
            (41, 50): 0.01,    # +1.0% annual growth for 41-50
            (51, 60): 0.015,   # +1.5% annual growth for 51-60
            (61, 70): 0.025,   # +2.5% annual growth for 61-70
            (71, 80): 0.035,   # +3.5% annual growth for 71-80
            (81, 120): 0.045,  # +4.5% annual growth for 81+
        }
        
        # Additional adjustments for health conditions
        condition_factor = 0.0
        if health_conditions:
            # Add 0.5% per condition up to a cap
            condition_factor = min(len(health_conditions) * 0.005, 0.025)
        
        # Project year by year with dynamic age adjustment
        result = [base_expense]  # Start with current expense
        current_age = age
        
        for year in range(1, years + 1):
            current_age = age + year
            
            # Find age bracket and corresponding adjustment
            age_factor = 0.0
            for (min_age, max_age), factor in age_adjustment_factors.items():
                if min_age <= current_age <= max_age:
                    age_factor = factor
                    break
            
            # Calculate effective inflation rate for this year
            effective_rate = healthcare_inflation + age_factor + condition_factor
            
            # Apply to get next year's value
            next_value = result[-1] * (1 + effective_rate)
            result.append(next_value)
        
        return result
    
    def project_education_expenses(self,
                                education_plans: List[EducationPlan],
                                years: int,
                                currency: str = "INR") -> Dict[str, List[float]]:
        """
        Project education expenses based on provided education plans.
        
        Parameters:
        -----------
        education_plans : List[EducationPlan]
            List of education plans for projection
        years : int
            Number of years to project
        currency : str, default "INR"
            Currency for cost calculations
            
        Returns:
        --------
        Dict[str, List[float]]
            Projected education expenses by child/plan
        """
        # Education inflation rate
        education_inflation = self._get_inflation_rate(ExpenseCategory.EDUCATION)
        
        # Initialize results
        result_by_plan = {}
        
        # Process each education plan
        for i, plan in enumerate(education_plans):
            plan_name = f"Child_{i+1}" if not hasattr(plan, "name") else plan.name
            
            # Initialize with zeros
            expenses = [0.0] * (years + 1)
            current_year = plan.current_year
            child_age = plan.child_age
            
            # Calculate school expenses (ages 6-18)
            school_cost = self.EDUCATION_COSTS["school"].get(plan.school_type, 
                                                          self.EDUCATION_COSTS["school"]["private"])
            
            # Calculate college expenses
            if plan.college_type == "foreign":
                # For foreign education, get specific country costs
                if hasattr(plan, "foreign_country") and plan.foreign_country in self.EDUCATION_COSTS["college"]["foreign"]:
                    college_cost = self.EDUCATION_COSTS["college"]["foreign"][plan.foreign_country]
                else:
                    # Default to US if country not specified
                    college_cost = self.EDUCATION_COSTS["college"]["foreign"]["us"]
            else:
                # For Indian education
                college_stream = plan.college_stream
                college_type = plan.college_type
                if college_type in self.EDUCATION_COSTS["college"] and college_stream in self.EDUCATION_COSTS["college"][college_type]:
                    college_cost = self.EDUCATION_COSTS["college"][college_type][college_stream]
                else:
                    # Default to private engineering if combination not found
                    college_cost = self.EDUCATION_COSTS["college"]["private"]["engineering"]
            
            # Calculate coaching costs if applicable
            coaching_cost = 0
            if plan.coaching_required:
                if hasattr(plan, "coaching_type") and plan.coaching_type in self.EDUCATION_COSTS["coaching"]:
                    coaching_cost = self.EDUCATION_COSTS["coaching"][plan.coaching_type]
                else:
                    coaching_cost = self.EDUCATION_COSTS["coaching"]["general"]
            
            # Project year by year
            for year_idx in range(years + 1):
                projection_year = current_year + year_idx
                projected_age = child_age + year_idx
                
                # School expenses (ages 6-18)
                if 6 <= projected_age <= 18:
                    # Apply cumulative inflation
                    inflation_factor = (1 + education_inflation) ** year_idx
                    year_expense = school_cost * inflation_factor
                    expenses[year_idx] += year_expense
                
                # College expenses (typically ages 18-22)
                elif 18 < projected_age <= 22:
                    # Apply cumulative inflation
                    inflation_factor = (1 + education_inflation) ** year_idx
                    year_expense = college_cost * inflation_factor
                    expenses[year_idx] += year_expense
                
                # Coaching expenses (typically for ages 16-18, before college)
                if plan.coaching_required and 16 <= projected_age <= 18:
                    # Apply cumulative inflation
                    inflation_factor = (1 + education_inflation) ** year_idx
                    year_expense = coaching_cost * inflation_factor
                    expenses[year_idx] += year_expense
                    
                # Adjust for scholarship if expected
                if plan.scholarship_expected and projected_age > 18:
                    # Apply scholarship discount (assume 30% reduction)
                    scholarship_discount = 0.3
                    expenses[year_idx] *= (1 - scholarship_discount)
            
            # Save results for this plan
            result_by_plan[plan_name] = expenses
        
        return result_by_plan
    
    def model_lifestyle_inflation(self,
                               base_expenses: Dict[ExpenseCategory, float],
                               income_projection: List[float],
                               years: int,
                               elasticity: float = 0.7) -> Dict[ExpenseCategory, List[float]]:
        """
        Model lifestyle inflation based on income growth.
        
        Parameters:
        -----------
        base_expenses : Dict[ExpenseCategory, float]
            Current expenses by category
        income_projection : List[float]
            Projected income over time
        years : int
            Number of years to project
        elasticity : float, default 0.7
            Elasticity of expenses with respect to income changes
            
        Returns:
        --------
        Dict[ExpenseCategory, List[float]]
            Expenses projected with lifestyle inflation
        """
        # Categories most affected by lifestyle inflation
        lifestyle_categories = [
            ExpenseCategory.HOUSING,
            ExpenseCategory.DINING_OUT,
            ExpenseCategory.ENTERTAINMENT,
            ExpenseCategory.TRAVEL,
            ExpenseCategory.CLOTHING,
            ExpenseCategory.PERSONAL_CARE,
            ExpenseCategory.SUBSCRIPTIONS,
            ExpenseCategory.HOBBIES
        ]
        
        # Categories least affected by lifestyle inflation
        essential_categories = [
            ExpenseCategory.FOOD,
            ExpenseCategory.TRANSPORTATION,
            ExpenseCategory.HEALTHCARE,
            ExpenseCategory.UTILITIES,
            ExpenseCategory.INSURANCE,
            ExpenseCategory.DEBT_PAYMENTS
        ]
        
        # Set elasticity factors by category type
        category_elasticity = {}
        for category in base_expenses.keys():
            if category in lifestyle_categories:
                # Higher elasticity for lifestyle categories
                category_elasticity[category] = elasticity
            elif category in essential_categories:
                # Lower elasticity for essential categories
                category_elasticity[category] = elasticity * 0.3
            else:
                # Medium elasticity for others
                category_elasticity[category] = elasticity * 0.6
        
        # Ensure we have enough income projections
        if len(income_projection) < years + 1:
            # Extend income projection if needed
            extended_income = income_projection.copy()
            last_income = income_projection[-1]
            for _ in range(years + 1 - len(income_projection)):
                extended_income.append(last_income)
            income_projection = extended_income
        
        # Calculate income growth rates
        income_growth_rates = []
        for i in range(1, years + 1):
            if income_projection[i-1] > 0:
                growth_rate = income_projection[i] / income_projection[i-1] - 1
            else:
                growth_rate = 0
            income_growth_rates.append(growth_rate)
            
        # Project expenses with lifestyle inflation
        result = {}
        for category, amount in base_expenses.items():
            # Get base inflation rate for this category
            inflation_rate = self._get_inflation_rate(category)
            
            # Initialize with starting amount
            category_result = [amount]
            
            # Project year by year
            for year in range(years):
                # Get income growth for this year
                income_growth = income_growth_rates[year]
                
                # Calculate lifestyle component (income growth * elasticity)
                lifestyle_component = income_growth * category_elasticity.get(category, 0)
                
                # Combine with regular inflation (compounding)
                effective_rate = (1 + inflation_rate) * (1 + lifestyle_component) - 1
                
                # Ensure we don't get negative growth in normal scenarios
                effective_rate = max(effective_rate, 0)
                
                # Calculate next year's expense
                next_value = category_result[-1] * (1 + effective_rate)
                category_result.append(next_value)
            
            result[category] = category_result
            
        return result
    
    def project_festival_expenses(self,
                               monthly_income: float,
                               years: int,
                               festivals: List[FestivalExpense] = None,
                               region: str = "north") -> Dict[str, List[float]]:
        """
        Project festival-related expenses common in Indian households.
        
        Parameters:
        -----------
        monthly_income : float
            Current monthly income
        years : int
            Number of years to project
        festivals : List[FestivalExpense], optional
            List of festival expenses to include
        region : str, default "north"
            Region in India for region-specific festivals
            
        Returns:
        --------
        Dict[str, List[float]]
            Projected festival expenses by festival
        """
        # Festival inflation rate
        festival_inflation = self._get_inflation_rate(ExpenseCategory.FESTIVALS)
        
        # Default festivals based on region if none provided
        if festivals is None:
            festivals = []
            
            # Common festivals across regions
            festivals.append(FestivalExpense(
                name="Diwali",
                month=10,  # Typically in October/November
                clothing_budget=monthly_income * 0.20,
                gifts_budget=monthly_income * 0.25,
                food_budget=monthly_income * 0.15,
                decoration_budget=monthly_income * 0.10,
                religious_budget=monthly_income * 0.10
            ))
            
            # Add region-specific festivals
            if region.lower() in ["north", "central"]:
                festivals.append(FestivalExpense(
                    name="Holi",
                    month=3,  # Typically in March
                    clothing_budget=monthly_income * 0.05,
                    food_budget=monthly_income * 0.10,
                    gifts_budget=monthly_income * 0.05,
                    entertainment_budget=monthly_income * 0.05
                ))
            
            if region.lower() in ["east", "northeast"]:
                festivals.append(FestivalExpense(
                    name="Durga Puja",
                    month=10,  # Typically in September/October
                    clothing_budget=monthly_income * 0.20,
                    food_budget=monthly_income * 0.15,
                    religious_budget=monthly_income * 0.15,
                    entertainment_budget=monthly_income * 0.10
                ))
            
            if region.lower() == "south":
                festivals.append(FestivalExpense(
                    name="Pongal",
                    month=1,  # January
                    food_budget=monthly_income * 0.15,
                    religious_budget=monthly_income * 0.10,
                    gifts_budget=monthly_income * 0.10
                ))
            
            if region.lower() == "west":
                festivals.append(FestivalExpense(
                    name="Ganesh Chaturthi",
                    month=9,  # Typically in August/September
                    decoration_budget=monthly_income * 0.15,
                    food_budget=monthly_income * 0.10,
                    religious_budget=monthly_income * 0.10
                ))
        
        # Initialize results
        result = {}
        
        # Project expenses for each festival
        for festival in festivals:
            # Start with initial budget
            total_budget = festival.total_budget()
            festival_result = [total_budget]
            
            # Project for future years
            for year in range(1, years + 1):
                # Calculate with festival-specific inflation
                next_value = festival_result[-1] * (1 + festival_inflation)
                
                # Increase festival budget with income growth (assumes 5% annual income growth)
                income_growth_factor = 0.05
                next_value *= (1 + income_growth_factor * 0.5)  # Festival spending grows at 50% of income growth
                
                festival_result.append(next_value)
            
            result[festival.name] = festival_result
        
        return result
    
    def incorporate_one_time_expenses(self,
                                   base_projection: ExpenseProjectionResult,
                                   one_time_expenses: List[OneTimeExpense]) -> ExpenseProjectionResult:
        """
        Incorporate one-time expenses into an existing expense projection.
        
        Parameters:
        -----------
        base_projection : ExpenseProjectionResult
            Base expense projection
        one_time_expenses : List[OneTimeExpense]
            List of one-time expenses to incorporate
            
        Returns:
        --------
        ExpenseProjectionResult
            Updated expense projection with one-time expenses
        """
        # Copy the original projection data
        updated_values = {}
        for category, values in base_projection.expense_values.items():
            updated_values[category] = values.copy()
        
        # Get years list
        years = base_projection.years
        first_year = years[0]
        
        # Process each one-time expense
        for expense in one_time_expenses:
            # Skip if expense year is outside projection range
            if expense.year < first_year or expense.year > years[-1]:
                continue
            
            # Get year index in our projection
            year_idx = expense.year - first_year
            
            # Get expense category
            category = expense.category
            
            # Ensure category exists in our projection
            if category not in updated_values:
                updated_values[category] = [0.0] * len(years)
            
            # Apply inflation adjustment if needed
            amount = expense.amount
            if expense.inflation_adjusted:
                inflation_rate = self._get_inflation_rate(category)
                years_from_now = expense.year - first_year
                amount *= (1 + inflation_rate) ** years_from_now
            
            # Add to the appropriate year
            if expense.spread_years <= 1:
                # Single year expense
                updated_values[category][year_idx] += amount
            else:
                # Multi-year expense (like a loan payment)
                annual_amount = amount / expense.spread_years
                for i in range(expense.spread_years):
                    if year_idx + i < len(years):
                        updated_values[category][year_idx + i] += annual_amount
            
            # Handle recurring expenses
            if expense.recurring_interval is not None and expense.recurring_interval > 0:
                next_year = expense.year + expense.recurring_interval
                while next_year <= years[-1]:
                    next_idx = next_year - first_year
                    
                    # Apply inflation for the recurring instance
                    recurring_amount = expense.amount
                    if expense.inflation_adjusted:
                        years_from_original = next_year - expense.year
                        recurring_amount *= (1 + inflation_rate) ** years_from_original
                    
                    # Add to the appropriate years
                    if expense.spread_years <= 1:
                        # Single year expense
                        updated_values[category][next_idx] += recurring_amount
                    else:
                        # Multi-year expense
                        annual_amount = recurring_amount / expense.spread_years
                        for i in range(expense.spread_years):
                            if next_idx + i < len(years):
                                updated_values[category][next_idx + i] += annual_amount
                    
                    # Move to next occurrence
                    next_year += expense.recurring_interval
        
        # Recalculate total expenses
        updated_total = []
        for year_idx in range(len(years)):
            year_total = sum(values[year_idx] for values in updated_values.values())
            updated_total.append(year_total)
        
        # Create updated result
        return ExpenseProjectionResult(
            years=years,
            expense_values=updated_values,
            total_expenses=updated_total
        )
    
    def identify_expense_optimization_opportunities(self,
                                                monthly_expenses: Dict[ExpenseCategory, float],
                                                income: float,
                                                baseline_ratios: Dict[ExpenseCategory, float] = None) -> Dict[str, Dict]:
        """
        Identify potential opportunities to optimize expenses.
        
        Parameters:
        -----------
        monthly_expenses : Dict[ExpenseCategory, float]
            Current expenses by category
        income : float
            Monthly income
        baseline_ratios : Dict[ExpenseCategory, float], optional
            Baseline expense-to-income ratios for comparison
            
        Returns:
        --------
        Dict[str, Dict]
            Dictionary of optimization opportunities with details
        """
        # Default baseline ratios if not provided
        if baseline_ratios is None:
            baseline_ratios = {
                ExpenseCategory.HOUSING: 0.30,        # Should be under 30% of income
                ExpenseCategory.FOOD: 0.12,           # Should be under 12% of income
                ExpenseCategory.TRANSPORTATION: 0.10,  # Should be under 10% of income
                ExpenseCategory.DEBT_PAYMENTS: 0.15,  # Should be under 15% of income
                ExpenseCategory.SAVINGS: 0.20,        # Should be at least 20% of income
                ExpenseCategory.ENTERTAINMENT: 0.05,  # Should be under 5% of income
                ExpenseCategory.DISCRETIONARY: 0.10,  # Should be under 10% of income
            }
        
        # Initialize results
        opportunities = {}
        
        # Calculate actual ratios
        actual_ratios = {}
        for category, amount in monthly_expenses.items():
            actual_ratios[category] = amount / income if income > 0 else 0
        
        # Check housing expenses
        if ExpenseCategory.HOUSING in actual_ratios:
            housing_ratio = actual_ratios[ExpenseCategory.HOUSING]
            housing_baseline = baseline_ratios.get(ExpenseCategory.HOUSING, 0.30)
            
            if housing_ratio > housing_baseline:
                opportunities["housing"] = {
                    "category": ExpenseCategory.HOUSING.value,
                    "current_ratio": housing_ratio,
                    "target_ratio": housing_baseline,
                    "current_amount": monthly_expenses[ExpenseCategory.HOUSING],
                    "target_amount": income * housing_baseline,
                    "potential_savings": monthly_expenses[ExpenseCategory.HOUSING] - (income * housing_baseline),
                    "suggestions": [
                        "Consider downsizing to a smaller home",
                        "Look for a more affordable location",
                        "Explore house sharing or renting out a room",
                        "Refinance mortgage to lower interest rate"
                    ]
                }
        
        # Check food expenses
        if ExpenseCategory.FOOD in actual_ratios:
            food_ratio = actual_ratios[ExpenseCategory.FOOD]
            food_baseline = baseline_ratios.get(ExpenseCategory.FOOD, 0.12)
            
            if food_ratio > food_baseline:
                opportunities["food"] = {
                    "category": ExpenseCategory.FOOD.value,
                    "current_ratio": food_ratio,
                    "target_ratio": food_baseline,
                    "current_amount": monthly_expenses[ExpenseCategory.FOOD],
                    "target_amount": income * food_baseline,
                    "potential_savings": monthly_expenses[ExpenseCategory.FOOD] - (income * food_baseline),
                    "suggestions": [
                        "Meal planning and bulk cooking",
                        "Reduce dining out frequency",
                        "Use grocery store loyalty programs",
                        "Buy seasonal produce"
                    ]
                }
        
        # Check transportation expenses
        if ExpenseCategory.TRANSPORTATION in actual_ratios:
            transport_ratio = actual_ratios[ExpenseCategory.TRANSPORTATION]
            transport_baseline = baseline_ratios.get(ExpenseCategory.TRANSPORTATION, 0.10)
            
            if transport_ratio > transport_baseline:
                opportunities["transportation"] = {
                    "category": ExpenseCategory.TRANSPORTATION.value,
                    "current_ratio": transport_ratio,
                    "target_ratio": transport_baseline,
                    "current_amount": monthly_expenses[ExpenseCategory.TRANSPORTATION],
                    "target_amount": income * transport_baseline,
                    "potential_savings": monthly_expenses[ExpenseCategory.TRANSPORTATION] - (income * transport_baseline),
                    "suggestions": [
                        "Use public transportation when possible",
                        "Carpool or rideshare",
                        "Consider a more fuel-efficient vehicle",
                        "Combine errands to reduce fuel usage"
                    ]
                }
        
        # Check entertainment and discretionary spending
        discretionary_categories = [
            ExpenseCategory.ENTERTAINMENT,
            ExpenseCategory.DINING_OUT,
            ExpenseCategory.SHOPPING,
            ExpenseCategory.TRAVEL,
            ExpenseCategory.HOBBIES,
            ExpenseCategory.SUBSCRIPTIONS,
            ExpenseCategory.DISCRETIONARY
        ]
        
        total_discretionary = sum(monthly_expenses.get(cat, 0) for cat in discretionary_categories)
        discretionary_ratio = total_discretionary / income if income > 0 else 0
        discretionary_baseline = 0.10  # 10% of income
        
        if discretionary_ratio > discretionary_baseline:
            opportunities["discretionary"] = {
                "category": "discretionary",
                "current_ratio": discretionary_ratio,
                "target_ratio": discretionary_baseline,
                "current_amount": total_discretionary,
                "target_amount": income * discretionary_baseline,
                "potential_savings": total_discretionary - (income * discretionary_baseline),
                "suggestions": [
                    "Review and cancel unused subscriptions",
                    "Find free or low-cost entertainment alternatives",
                    "Set a specific budget for discretionary spending",
                    "Implement a 24-hour rule for purchases"
                ]
            }
        
        # Check debt payments
        if ExpenseCategory.DEBT_PAYMENTS in actual_ratios:
            debt_ratio = actual_ratios[ExpenseCategory.DEBT_PAYMENTS]
            debt_baseline = baseline_ratios.get(ExpenseCategory.DEBT_PAYMENTS, 0.15)
            
            if debt_ratio > debt_baseline:
                opportunities["debt"] = {
                    "category": ExpenseCategory.DEBT_PAYMENTS.value,
                    "current_ratio": debt_ratio,
                    "target_ratio": debt_baseline,
                    "current_amount": monthly_expenses[ExpenseCategory.DEBT_PAYMENTS],
                    "target_amount": income * debt_baseline,
                    "potential_savings": monthly_expenses[ExpenseCategory.DEBT_PAYMENTS] - (income * debt_baseline),
                    "suggestions": [
                        "Consolidate high-interest debt",
                        "Negotiate lower interest rates",
                        "Create a debt payoff strategy (snowball or avalanche)",
                        "Avoid taking on new debt"
                    ]
                }
        
        # Check savings rate
        savings_categories = [
            ExpenseCategory.SAVINGS,
            ExpenseCategory.INVESTMENTS
        ]
        
        total_savings = sum(monthly_expenses.get(cat, 0) for cat in savings_categories)
        savings_ratio = total_savings / income if income > 0 else 0
        savings_baseline = baseline_ratios.get(ExpenseCategory.SAVINGS, 0.20)
        
        if savings_ratio < savings_baseline:
            opportunities["savings"] = {
                "category": "savings",
                "current_ratio": savings_ratio,
                "target_ratio": savings_baseline,
                "current_amount": total_savings,
                "target_amount": income * savings_baseline,
                "improvement_needed": (income * savings_baseline) - total_savings,
                "suggestions": [
                    "Set up automated transfers to savings",
                    "Save increases in income",
                    "Redirect savings from reduced expenses",
                    "Build emergency fund first, then other savings goals"
                ]
            }
        
        return opportunities
    
    def calculate_expense_elasticity(self,
                                  expenses_time_series: Dict[ExpenseCategory, List[float]],
                                  income_time_series: List[float]) -> Dict[ExpenseCategory, float]:
        """
        Calculate expense elasticity with respect to income.
        
        Parameters:
        -----------
        expenses_time_series : Dict[ExpenseCategory, List[float]]
            Historical expense data by category
        income_time_series : List[float]
            Historical income data
            
        Returns:
        --------
        Dict[ExpenseCategory, float]
            Calculated elasticity values by category
        """
        # Ensure we have enough data points
        if len(income_time_series) < 2:
            return {}
        
        # Calculate income growth rates
        income_growth_rates = []
        for i in range(1, len(income_time_series)):
            if income_time_series[i-1] > 0:
                growth_rate = income_time_series[i] / income_time_series[i-1] - 1
            else:
                growth_rate = 0
            income_growth_rates.append(growth_rate)
        
        # Calculate elasticity for each expense category
        elasticities = {}
        
        for category, expenses in expenses_time_series.items():
            # Skip if we don't have enough data points
            if len(expenses) < len(income_growth_rates) + 1:
                continue
            
            # Calculate expense growth rates
            expense_growth_rates = []
            for i in range(1, len(expenses)):
                if expenses[i-1] > 0:
                    growth_rate = expenses[i] / expenses[i-1] - 1
                else:
                    growth_rate = 0
                expense_growth_rates.append(growth_rate)
            
            # Calculate elasticity (average of expense growth / income growth)
            category_elasticities = []
            for i in range(len(income_growth_rates)):
                if income_growth_rates[i] != 0:
                    elasticity = expense_growth_rates[i] / income_growth_rates[i]
                    category_elasticities.append(elasticity)
            
            # Calculate average elasticity, excluding outliers
            if category_elasticities:
                # Sort elasticities
                sorted_elasticities = sorted(category_elasticities)
                
                # Remove extreme outliers (keep middle 90%)
                if len(sorted_elasticities) >= 10:
                    start_idx = len(sorted_elasticities) // 20  # 5th percentile
                    end_idx = len(sorted_elasticities) - start_idx  # 95th percentile
                    trimmed_elasticities = sorted_elasticities[start_idx:end_idx]
                else:
                    trimmed_elasticities = sorted_elasticities
                
                # Calculate average
                elasticities[category] = sum(trimmed_elasticities) / len(trimmed_elasticities)
            
        return elasticities
    
    def simulate_expense_reduction_impact(self,
                                       current_expenses: Dict[ExpenseCategory, float],
                                       reduction_targets: Dict[ExpenseCategory, float],
                                       years: int = 10,
                                       investment_rate: float = 0.08) -> Dict[str, Union[float, List[float]]]:
        """
        Simulate the long-term impact of expense reductions on financial growth.
        
        Parameters:
        -----------
        current_expenses : Dict[ExpenseCategory, float]
            Current monthly expenses by category
        reduction_targets : Dict[ExpenseCategory, float]
            Target reduction percentage by category (0.0-1.0)
        years : int, default 10
            Years to simulate
        investment_rate : float, default 0.08
            Annual investment return rate for redirected savings
            
        Returns:
        --------
        Dict[str, Union[float, List[float]]]
            Simulation results including total savings and growth
        """
        # Calculate monthly savings
        monthly_savings = 0.0
        savings_by_category = {}
        
        for category, amount in current_expenses.items():
            if category in reduction_targets:
                reduction_pct = reduction_targets[category]
                savings = amount * reduction_pct
                monthly_savings += savings
                savings_by_category[category] = savings
        
        # Convert to annual
        annual_savings = monthly_savings * 12
        
        # Project future value with compound growth
        future_values = [0.0]  # Starting value
        cumulative_contributions = [0.0]  # Starting value
        
        for year in range(1, years + 1):
            # New amount saved this year
            new_contribution = annual_savings
            
            # Last year's total with growth
            last_value_with_growth = future_values[-1] * (1 + investment_rate)
            
            # New total
            new_total = last_value_with_growth + new_contribution
            
            # Track values
            future_values.append(new_total)
            cumulative_contributions.append(cumulative_contributions[-1] + new_contribution)
        
        # Calculate growth component (investment returns)
        growth_component = future_values[-1] - cumulative_contributions[-1]
        
        # Calculate monthly expense reductions
        expense_reductions = {}
        for category, amount in current_expenses.items():
            if category in reduction_targets:
                reduced_amount = amount * (1 - reduction_targets[category])
                expense_reductions[category] = reduced_amount
        
        # Calculate impact metrics
        results = {
            "monthly_savings": monthly_savings,
            "annual_savings": annual_savings,
            "total_contributions": cumulative_contributions[-1],
            "future_value": future_values[-1],
            "investment_growth": growth_component,
            "reduced_expenses": expense_reductions,
            "savings_by_category": savings_by_category,
            "future_value_timeline": future_values,
            "contribution_timeline": cumulative_contributions
        }
        
        return results
    
    def _extract_value_from_profile(self, 
                                  profile: Dict[str, Any], 
                                  possible_keys: List[str]) -> Optional[float]:
        """
        Extract a value from a user profile using multiple possible keys.
        
        Parameters:
        -----------
        profile : Dict[str, Any]
            User profile data
        possible_keys : List[str]
            List of possible keys to try
            
        Returns:
        --------
        float or None
            Extracted value, or None if not found
        """
        if not profile:
            return None
        
        # Try each key in order
        for key in possible_keys:
            # Handle nested keys with dot notation
            if '.' in key:
                parts = key.split('.')
                value = profile
                try:
                    for part in parts:
                        value = value[part]
                    return float(value) if value is not None else None
                except (KeyError, TypeError, ValueError):
                    continue
            
            # Handle direct key
            if key in profile and profile[key] is not None:
                try:
                    return float(profile[key])
                except (TypeError, ValueError):
                    continue
        
        return None
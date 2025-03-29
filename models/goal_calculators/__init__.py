# Goal Calculators Module

from .base_calculator import GoalCalculator
from .emergency_fund_calculator import EmergencyFundCalculator
from .retirement_calculator import RetirementCalculator, EarlyRetirementCalculator
from .education_calculator import EducationCalculator
from .home_calculator import HomeDownPaymentCalculator  # Correct class name
from .debt_repayment_calculator import DebtRepaymentCalculator
from .discretionary_calculator import DiscretionaryGoalCalculator
from .wedding_calculator import WeddingCalculator
from .legacy_planning_calculator import LegacyPlanningCalculator, CharitableGivingCalculator
from .custom_goal_calculator import CustomGoalCalculator
from .tax_optimization_calculator import TaxOptimizationCalculator

__all__ = [
    'GoalCalculator',
    'EmergencyFundCalculator',
    'RetirementCalculator',
    'EarlyRetirementCalculator',
    'EducationCalculator',
    'HomeDownPaymentCalculator',
    'DebtRepaymentCalculator',
    'DiscretionaryGoalCalculator',
    'WeddingCalculator',
    'LegacyPlanningCalculator',
    'CharitableGivingCalculator',
    'CustomGoalCalculator',
    'TaxOptimizationCalculator'
]
"""
Goal Calculator - Adapter Module

This file acts as a backward-compatibility layer to import and re-export
all calculator implementations from the goal_calculators package.

For new code, import directly from the models.goal_calculators package instead.
"""

# Re-export all calculator implementations
from models.goal_calculators import (
    GoalCalculator,
    EmergencyFundCalculator,
    RetirementCalculator,
    EarlyRetirementCalculator,
    EducationCalculator,
    HomeDownPaymentCalculator,
    DebtRepaymentCalculator,
    DiscretionaryGoalCalculator,
    WeddingCalculator,
    LegacyPlanningCalculator,
    CharitableGivingCalculator,
    CustomGoalCalculator
)

# Get the factory methods directly
get_calculator_for_goal = GoalCalculator.get_calculator_for_goal
get_calculator_for_category = GoalCalculator.get_calculator_for_category

# For backward compatibility with older code:

# Alias for DebtRepaymentCalculator
DebtEliminationCalculator = DebtRepaymentCalculator

# Alias for DiscretionaryGoalCalculator
LifestyleGoalCalculator = DiscretionaryGoalCalculator
VehicleCalculator = DiscretionaryGoalCalculator
HomeImprovementCalculator = DiscretionaryGoalCalculator
InsuranceCalculator = DiscretionaryGoalCalculator

# Expose parameters from FinancialParameters module
try:
    from models.financial_parameters import get_parameters
except ImportError:
    # Define a dummy function if the module isn't available
    def get_parameters(*args, **kwargs):
        return None

# Additional backward compatibility exports or aliases can be added here
# as needed to maintain compatibility with existing code
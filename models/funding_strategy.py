"""
Funding Strategy module for financial goals.

This module has been updated to import the classes from the funding_strategies package.

This file is maintained for backward compatibility.
"""

from models.funding_strategies import (
    FundingStrategyGenerator,
    RetirementFundingStrategy,
    EducationFundingStrategy,
    EmergencyFundStrategy,
    HomeDownPaymentStrategy,
    DiscretionaryGoalStrategy,
    WeddingFundingStrategy,
    DebtRepaymentStrategy,
    LegacyPlanningStrategy,
    CharitableGivingStrategy,
    CustomGoalStrategy
)

__all__ = [
    'FundingStrategyGenerator',
    'RetirementFundingStrategy',
    'EducationFundingStrategy',
    'EmergencyFundStrategy',
    'HomeDownPaymentStrategy',
    'DiscretionaryGoalStrategy',
    'WeddingFundingStrategy',
    'DebtRepaymentStrategy',
    'LegacyPlanningStrategy',
    'CharitableGivingStrategy',
    'CustomGoalStrategy'
]
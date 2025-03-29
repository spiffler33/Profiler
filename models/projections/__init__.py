"""
Projections Module

This module provides a collection of classes for projecting financial values 
over time, including assets, income, expenses, and other financial metrics.
"""

from models.projections.base_projection import BaseProjection, FrequencyType
from models.projections.asset_projection import (
    AssetProjection, AssetClass, RiskProfile, AssetAllocation, ProjectionResult
)
from models.projections.income_projection import (
    IncomeProjection, IncomeSource, CareerStage, TaxRegime, 
    IncomeMilestone, IncomeProjectionResult
)
from models.projections.expense_projection import (
    ExpenseProjection, ExpenseCategory, LifeStage, LifeEvent,
    ExpenseProjectionResult
)

__all__ = [
    'BaseProjection',
    'FrequencyType',
    
    'AssetProjection',
    'AssetClass',
    'RiskProfile',
    'AssetAllocation',
    'ProjectionResult',
    
    'IncomeProjection',
    'IncomeSource',
    'CareerStage',
    'TaxRegime',
    'IncomeMilestone',
    'IncomeProjectionResult',
    
    'ExpenseProjection',
    'ExpenseCategory',
    'LifeStage',
    'LifeEvent',
    'ExpenseProjectionResult',
]
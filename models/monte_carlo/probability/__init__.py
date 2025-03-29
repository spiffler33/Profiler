"""
Probability analysis module for Monte Carlo simulations.

This package provides components for analyzing goal achievement probability
using Monte Carlo simulations, with a focus on financial goals.
"""

from models.monte_carlo.probability.result import ProbabilityResult
from models.monte_carlo.probability.distribution import GoalOutcomeDistribution
from models.monte_carlo.probability.analyzer import GoalProbabilityAnalyzer

__all__ = [
    'ProbabilityResult',
    'GoalOutcomeDistribution',
    'GoalProbabilityAnalyzer',
]
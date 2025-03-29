"""
Core gap analysis components

This module provides the fundamental data structures and utility functions
used throughout the gap analysis system.
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any, Tuple, Callable

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


class GapSeverity(Enum):
    """Enum representing the severity levels of financial gaps"""
    CRITICAL = "critical"       # Severe gap requiring immediate attention
    SIGNIFICANT = "significant" # Large gap requiring substantial adjustment
    MODERATE = "moderate"       # Moderate gap requiring some adjustment
    MINOR = "minor"             # Small gap that can be addressed with minor changes


@dataclass
class GapResult:
    """Data class for storing gap analysis results"""
    goal_id: str
    goal_title: str
    goal_category: str
    target_amount: float
    current_amount: float
    gap_amount: float
    gap_percentage: float
    timeframe_gap: int = 0  # Additional months needed at current pace
    capacity_gap: float = 0.0  # Gap between required and available savings capacity
    capacity_gap_percentage: float = 0.0  # Capacity gap as percentage of income
    severity: GapSeverity = GapSeverity.MODERATE
    recommended_adjustments: Dict[str, Any] = field(default_factory=dict)
    resource_conflicts: List[str] = field(default_factory=list)
    description: str = ""
    projected_values: Dict[str, List[float]] = field(default_factory=dict)  # Projected values over time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the gap result to a dictionary for serialization"""
        return {
            "goal_id": self.goal_id,
            "goal_title": self.goal_title,
            "goal_category": self.goal_category,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "gap_amount": self.gap_amount,
            "gap_percentage": self.gap_percentage,
            "timeframe_gap": self.timeframe_gap,
            "capacity_gap": self.capacity_gap,
            "capacity_gap_percentage": self.capacity_gap_percentage,
            "severity": self.severity.value,
            "recommended_adjustments": self.recommended_adjustments,
            "resource_conflicts": self.resource_conflicts,
            "description": self.description,
            "projected_values": self.projected_values
        }


@dataclass
class RemediationOption:
    """Data class for storing a remediation option"""
    description: str
    impact_metrics: Dict[str, Any]
    feasibility_score: float = 0.0
    implementation_steps: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the remediation option to a dictionary for serialization"""
        return {
            "description": self.description,
            "impact_metrics": self.impact_metrics,
            "feasibility_score": self.feasibility_score,
            "implementation_steps": self.implementation_steps
        }


@dataclass
class Scenario:
    """Data class for storing financial scenario information"""
    name: str
    description: str
    goals: List[Dict[str, Any]]
    profile: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to a dictionary for serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "goals": self.goals,
            "profile": self.profile,
            "metadata": self.metadata
        }


@dataclass
class ScenarioResult:
    """Data class for storing scenario analysis outcomes"""
    scenario: Scenario
    gap_results: List[GapResult]
    success_probability: float = 0.0
    effort_required: float = 0.0
    financial_impact: Dict[str, Any] = field(default_factory=dict)
    timeline_impact: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario result to a dictionary for serialization"""
        return {
            "scenario": self.scenario.to_dict(),
            "gap_results": [result.to_dict() for result in self.gap_results],
            "success_probability": self.success_probability,
            "effort_required": self.effort_required,
            "financial_impact": self.financial_impact,
            "timeline_impact": self.timeline_impact
        }


@dataclass
class ScenarioComparison:
    """Data class for comparing multiple scenarios"""
    scenarios: List[ScenarioResult]
    optimal_scenario_id: str = ""
    comparison_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario comparison to a dictionary for serialization"""
        return {
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
            "optimal_scenario_id": self.optimal_scenario_id,
            "comparison_metrics": self.comparison_metrics
        }
"""
Gap Analysis Module

This module provides tools for analyzing mismatches between financial goals and resources.
It helps identify funding gaps, timeframe issues, and prioritization conflicts to enable
better financial planning decisions.
"""

# Import all classes and functions to maintain backward compatibility
from models.gap_analysis.core import (
    GapSeverity,
    GapResult,
    RemediationOption,
    Scenario,
    ScenarioResult,
    ScenarioComparison,
    get_financial_parameter_service
)

from models.gap_analysis.analyzer import GapAnalysis
from models.gap_analysis.remediation_strategies import (
    GapRemediationStrategy,
    RemediationImpactAnalysis
)
from models.gap_analysis.timeframe_adjustments import TimeframeAdjustment
from models.gap_analysis.target_adjustments import TargetAdjustment
from models.gap_analysis.allocation_adjustments import AllocationAdjustment
from models.gap_analysis.contribution_adjustments import ContributionAdjustment
from models.gap_analysis.priority_adjustments import PriorityAdjustment
from models.gap_analysis.scenarios import GoalScenarioComparison
from models.gap_analysis.scenario_generators import ScenarioGenerator
from models.gap_analysis.scenario_analysis import (
    ScenarioAnalyzer,
    ScenarioVisualizer,
    ScenarioImpactAnalyzer
)

# Convenience functions for scenario generation
def generate_baseline_scenario(goals, profile):
    """Generate a baseline scenario with current trajectory"""
    generator = ScenarioGenerator()
    return generator.generate_baseline_scenario(goals, profile)

def generate_alternative_scenarios(goals, profile):
    """Generate a set of alternative scenarios for comparison"""
    generator = ScenarioGenerator()
    scenarios = [
        generator.generate_baseline_scenario(goals, profile),
        generator.generate_conservative_scenario(goals, profile),
        generator.generate_aggressive_scenario(goals, profile),
        generator.generate_balanced_scenario(goals, profile)
    ]
    return scenarios

# Convenience functions for scenario analysis
def analyze_scenario(scenario, gap_analyzer=None):
    """Analyze a scenario using the ScenarioAnalyzer"""
    analyzer = ScenarioAnalyzer()
    return analyzer.analyze_scenario(scenario, gap_analyzer)

def compare_scenarios(baseline, alternative):
    """Compare two scenarios to identify improvements and differences"""
    analyzer = ScenarioAnalyzer()
    return analyzer.compare_scenario_gaps(baseline, alternative)

def prepare_visualization(scenarios):
    """Prepare visualization data for a list of scenarios"""
    visualizer = ScenarioVisualizer()
    return visualizer.prepare_visualization_data(scenarios)

# For backward compatibility, expose all classes at module level
__all__ = [
    'GapSeverity',
    'GapResult',
    'GapAnalysis',
    'RemediationOption',
    'Scenario',
    'ScenarioResult',
    'ScenarioComparison',
    'GoalScenarioComparison',
    'ScenarioGenerator',
    'ScenarioAnalyzer',
    'ScenarioVisualizer',
    'ScenarioImpactAnalyzer',
    'GapRemediationStrategy',
    'TimeframeAdjustment',
    'AllocationAdjustment',
    'ContributionAdjustment',
    'TargetAdjustment',
    'PriorityAdjustment',
    'RemediationImpactAnalysis',
    'generate_baseline_scenario',
    'generate_alternative_scenarios',
    'analyze_scenario',
    'compare_scenarios',
    'prepare_visualization',
    'get_financial_parameter_service'
]
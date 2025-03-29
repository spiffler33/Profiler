"""
Scenario comparison framework for gap analysis

This module provides utilities for creating and comparing alternative financial scenarios.
It enables "what if" analysis for different goal configurations and adjustments.
"""

import logging
import json
import copy
from datetime import datetime, date
from typing import Dict, List, Optional, Union, Any, Tuple, Callable, Set

from models.gap_analysis.core import (
    GapSeverity,
    GapResult,
    Scenario,
    ScenarioResult,
    ScenarioComparison,
    get_financial_parameter_service
)
from models.gap_analysis.analyzer import GapAnalysis

logger = logging.getLogger(__name__)

class GoalScenarioComparison:
    """
    Class for comparing different goal-based financial scenarios.
    
    This class allows creating and evaluating alternative scenarios for
    financial planning by modifying goals, timeline, allocation, or other
    parameters and comparing the outcomes.
    """
    
    def __init__(self, param_service=None):
        """
        Initialize the scenario comparison with financial parameters.
        
        Args:
            param_service: Optional financial parameter service instance.
                           If not provided, will attempt to get one.
        """
        # Get parameter service if not provided
        self.param_service = param_service
        
        # Only try to get service if explicitly None (for test patching)
        if self.param_service is None:
            self.param_service = get_financial_parameter_service()
            
        # Create a gap analysis instance for evaluating scenarios
        self.gap_analyzer = GapAnalysis(param_service=self.param_service)
        
        # Default parameters for scenario evaluation
        self.params = {
            "min_success_probability": 0.7,  # 70% success probability is minimum acceptable
            "max_effort_threshold": 0.8,     # 80% effort is maximum reasonable threshold
            "financial_impact_weight": 0.5,  # Weight for financial impact in scoring
            "timeline_impact_weight": 0.3,   # Weight for timeline impact in scoring
            "effort_weight": 0.2,            # Weight for effort required in scoring
        }
        
        # Override defaults with values from parameter service if available
        if self.param_service:
            try:
                # Try to use get_parameters_by_prefix if available
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    param_values = self.param_service.get_parameters_by_prefix("scenario_comparison.")
                    if param_values:
                        self.params.update(param_values)
                # Fall back to getting individual parameters
                else:
                    for key in self.params.keys():
                        param_path = f"scenario_comparison.{key}"
                        value = self.param_service.get(param_path)
                        if value is not None:
                            self.params[key] = value
            except Exception as e:
                logger.warning(f"Error getting parameters: {e}")
                # Continue with defaults
    
    def create_scenario(self, 
                       name: str, 
                       goals: List[Dict[str, Any]], 
                       profile: Dict[str, Any], 
                       adjustments: Optional[Dict[str, Any]] = None,
                       description: str = "") -> Scenario:
        """
        Create a scenario by applying adjustments to goals and profile data.
        
        Args:
            name: Name for the scenario
            goals: Original list of financial goals
            profile: User profile with financial information
            adjustments: Dictionary of adjustments to apply (can include goal
                         modifications, timeline changes, etc.)
            description: Optional description of the scenario
            
        Returns:
            Scenario object with the adjusted goals and profile
        """
        # Make deep copies to avoid modifying originals
        scenario_goals = copy.deepcopy(goals)
        scenario_profile = copy.deepcopy(profile)
        
        # Generate a default description if none provided
        if not description:
            description = f"Scenario '{name}' created on {datetime.now().strftime('%Y-%m-%d')}"
        
        # Track metadata about the scenario
        metadata = {
            "created_at": datetime.now().isoformat(),
            "adjustments_applied": {},
        }
        
        # Apply adjustments if provided
        if adjustments:
            # Apply goal adjustments
            if "goal_adjustments" in adjustments:
                goal_adj = adjustments["goal_adjustments"]
                scenario_goals = self._apply_goal_adjustments(scenario_goals, goal_adj)
                metadata["adjustments_applied"]["goals"] = list(goal_adj.keys())
            
            # Apply profile adjustments
            if "profile_adjustments" in adjustments:
                profile_adj = adjustments["profile_adjustments"]
                scenario_profile = self._apply_profile_adjustments(scenario_profile, profile_adj)
                metadata["adjustments_applied"]["profile"] = list(profile_adj.keys())
                
            # Apply timeline adjustments
            if "timeline_adjustments" in adjustments:
                timeline_adj = adjustments["timeline_adjustments"]
                scenario_goals = self._apply_timeline_adjustments(scenario_goals, timeline_adj)
                metadata["adjustments_applied"]["timeline"] = timeline_adj
                
            # Apply allocation adjustments
            if "allocation_adjustments" in adjustments:
                alloc_adj = adjustments["allocation_adjustments"]
                scenario_goals = self._apply_allocation_adjustments(scenario_goals, alloc_adj)
                metadata["adjustments_applied"]["allocation"] = alloc_adj
        
        # Create and return the scenario object
        return Scenario(
            name=name,
            description=description,
            goals=scenario_goals,
            profile=scenario_profile,
            metadata=metadata
        )
    
    def compare_scenarios(self, scenarios: List[Scenario]) -> ScenarioComparison:
        """
        Compare multiple scenarios to evaluate their relative outcomes.
        
        Args:
            scenarios: List of scenarios to compare
            
        Returns:
            ScenarioComparison object with analysis results
        """
        # Analyze each scenario
        scenario_results = []
        for scenario in scenarios:
            # Analyze the scenario
            gap_results = []
            for goal in scenario.goals:
                gap_result = self.gap_analyzer.analyze_goal_gap(goal, scenario.profile)
                gap_results.append(gap_result)
            
            # Calculate additional metrics
            success_probability = self.calculate_scenario_success_probability(scenario, gap_results)
            effort_required = self.calculate_scenario_effort_required(scenario, gap_results)
            financial_impact = self.calculate_scenario_financial_impact(scenario, gap_results)
            timeline_impact = self.calculate_scenario_timeline_impact(scenario, gap_results)
            
            # Create the scenario result
            result = ScenarioResult(
                scenario=scenario,
                gap_results=gap_results,
                success_probability=success_probability,
                effort_required=effort_required,
                financial_impact=financial_impact,
                timeline_impact=timeline_impact
            )
            
            scenario_results.append(result)
        
        # Calculate comparison metrics between scenarios
        comparison_metrics = self._calculate_comparison_metrics(scenario_results)
        
        # Determine the optimal scenario
        optimal_scenario_id = self._identify_optimal_scenario(scenario_results)
        
        # Create the comparison object
        return ScenarioComparison(
            scenarios=scenario_results,
            optimal_scenario_id=optimal_scenario_id,
            comparison_metrics=comparison_metrics
        )
    
    def identify_optimal_scenario(self, scenarios: List[ScenarioResult], 
                                priorities: Optional[Dict[str, float]] = None) -> str:
        """
        Identify the optimal scenario based on user priorities.
        
        Args:
            scenarios: List of scenario results to compare
            priorities: Dictionary mapping priority factors to their weights
                        (e.g., "financial_impact": 0.6, "effort": 0.2, etc.)
            
        Returns:
            ID of the optimal scenario
        """
        # If no priorities provided, use default weights
        if not priorities:
            priorities = {
                "financial_impact": self.params["financial_impact_weight"],
                "timeline_impact": self.params["timeline_impact_weight"],
                "effort": self.params["effort_weight"]
            }
        
        # Normalize weights to sum to 1.0
        total_weight = sum(priorities.values())
        normalized_priorities = {k: v / total_weight for k, v in priorities.items()}
        
        # Calculate weighted scores for each scenario
        scores = {}
        for scenario in scenarios:
            # Get financial impact score (higher is better)
            financial_score = scenario.financial_impact.get("overall_improvement", 0) / 100.0
            
            # Get timeline impact score (higher is better)
            timeline_score = scenario.timeline_impact.get("timeline_improvement", 0) / 100.0
            
            # Get effort score (lower effort is better)
            effort_score = 1.0 - scenario.effort_required
            
            # Calculate weighted score
            weighted_score = (
                financial_score * normalized_priorities.get("financial_impact", 0.5) +
                timeline_score * normalized_priorities.get("timeline_impact", 0.3) +
                effort_score * normalized_priorities.get("effort", 0.2)
            )
            
            scores[scenario.scenario.name] = weighted_score
        
        # Return the scenario with the highest score
        if scores:
            optimal_scenario = max(scores.items(), key=lambda x: x[1])[0]
            return optimal_scenario
        
        # Default to the first scenario if no scores calculated
        return scenarios[0].scenario.name if scenarios else ""
    
    def clone_and_adjust_goals(self, goals: List[Dict[str, Any]], 
                             adjustments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Clone and adjust a set of goals based on specified adjustments.
        
        Args:
            goals: Original list of financial goals
            adjustments: Dictionary of adjustments to apply to the goals
            
        Returns:
            New list of adjusted goals
        """
        # Make a deep copy of the goals
        adjusted_goals = copy.deepcopy(goals)
        
        # Apply the adjustments
        if "goal_adjustments" in adjustments:
            adjusted_goals = self._apply_goal_adjustments(adjusted_goals, adjustments["goal_adjustments"])
        
        if "timeline_adjustments" in adjustments:
            adjusted_goals = self._apply_timeline_adjustments(adjusted_goals, adjustments["timeline_adjustments"])
            
        if "allocation_adjustments" in adjustments:
            adjusted_goals = self._apply_allocation_adjustments(adjusted_goals, adjustments["allocation_adjustments"])
        
        return adjusted_goals
    
    def calculate_scenario_success_probability(self, scenario: Scenario, 
                                             gap_results: Optional[List[GapResult]] = None) -> float:
        """
        Calculate the probability of success for a given scenario.
        
        Args:
            scenario: The scenario to evaluate
            gap_results: Optional pre-calculated gap results
            
        Returns:
            Success probability (0.0 to 1.0)
        """
        # Calculate gap results if not provided
        if gap_results is None:
            gap_results = []
            for goal in scenario.goals:
                gap_result = self.gap_analyzer.analyze_goal_gap(goal, scenario.profile)
                gap_results.append(gap_result)
        
        # Calculate a success probability based on gap severity and goal importance
        if not gap_results:
            return 0.5  # Default to 50% if no goals
        
        # Map severity to success factor (higher severity = lower success probability)
        severity_factors = {
            GapSeverity.CRITICAL: 0.3,      # Critical gaps significantly reduce success probability
            GapSeverity.SIGNIFICANT: 0.5,   # Significant gaps moderately reduce success probability
            GapSeverity.MODERATE: 0.7,      # Moderate gaps slightly reduce success probability
            GapSeverity.MINOR: 0.9          # Minor gaps have minimal impact on success probability
        }
        
        # Calculate weighted probability based on goal importance
        total_weight = 0
        weighted_probability = 0
        
        for goal, result in zip(scenario.goals, gap_results):
            # Get importance weight
            importance = goal.get("importance", "medium")
            importance_weight = {
                "high": 3.0,
                "medium": 2.0,
                "low": 1.0
            }.get(importance, 2.0)
            
            # Get success factor based on gap severity
            success_factor = severity_factors.get(result.severity, 0.5)
            
            # Calculate weighted probability
            weighted_probability += success_factor * importance_weight
            total_weight += importance_weight
        
        # Calculate overall probability
        if total_weight > 0:
            overall_probability = weighted_probability / total_weight
        else:
            overall_probability = 0.5
        
        return overall_probability
    
    def calculate_scenario_effort_required(self, scenario: Scenario, 
                                        gap_results: Optional[List[GapResult]] = None) -> float:
        """
        Calculate the effort required to implement a given scenario.
        
        Args:
            scenario: The scenario to evaluate
            gap_results: Optional pre-calculated gap results
            
        Returns:
            Effort required (0.0 to 1.0, where 1.0 is maximum effort)
        """
        # Get adjustments from scenario metadata
        adjustments = scenario.metadata.get("adjustments_applied", {})
        
        # Baseline effort
        effort = 0.2  # Baseline effort for any scenario
        
        # Additional effort based on number of adjustments
        num_goal_adjustments = len(adjustments.get("goals", []))
        num_profile_adjustments = len(adjustments.get("profile", []))
        
        # Add effort for goal adjustments
        effort += num_goal_adjustments * 0.05  # 5% effort per goal adjustment
        
        # Add effort for profile adjustments
        effort += num_profile_adjustments * 0.08  # 8% effort per profile adjustment
        
        # Additional effort for timeline adjustments
        if "timeline" in adjustments:
            effort += 0.15  # Timeline adjustments require moderate effort
        
        # Additional effort for allocation adjustments
        if "allocation" in adjustments:
            effort += 0.25  # Allocation adjustments require significant effort
        
        # Calculate additional effort based on gap results if provided
        if gap_results:
            # Additional effort for goals with significant or critical gaps
            critical_gaps = sum(1 for result in gap_results if result.severity == GapSeverity.CRITICAL)
            significant_gaps = sum(1 for result in gap_results if result.severity == GapSeverity.SIGNIFICANT)
            
            effort += critical_gaps * 0.1  # 10% additional effort per critical gap
            effort += significant_gaps * 0.05  # 5% additional effort per significant gap
        
        # Cap effort at 1.0
        return min(effort, 1.0)
    
    def calculate_scenario_financial_impact(self, scenario: Scenario, 
                                         gap_results: Optional[List[GapResult]] = None) -> Dict[str, Any]:
        """
        Calculate the financial impact of a given scenario.
        
        Args:
            scenario: The scenario to evaluate
            gap_results: Optional pre-calculated gap results
            
        Returns:
            Dictionary with financial impact metrics
        """
        # Calculate gap results if not provided
        if gap_results is None:
            gap_results = []
            for goal in scenario.goals:
                gap_result = self.gap_analyzer.analyze_goal_gap(goal, scenario.profile)
                gap_results.append(gap_result)
        
        # Calculate total current amount and target amount
        total_current = sum(goal.get("current_amount", 0) for goal in scenario.goals)
        total_target = sum(goal.get("target_amount", 0) for goal in scenario.goals)
        
        # Calculate total gap amount
        total_gap = sum(result.gap_amount for result in gap_results)
        
        # Calculate total investment needed
        monthly_income = self._extract_monthly_income(scenario.profile)
        total_monthly_needed = sum(result.capacity_gap for result in gap_results)
        annual_investment = total_monthly_needed * 12
        
        # Calculate gap as percentage of income
        income_percentage = (total_monthly_needed / monthly_income) * 100 if monthly_income > 0 else 0
        
        # Calculate potential improvement
        gap_percentage = (total_gap / total_target) * 100 if total_target > 0 else 0
        
        # Evaluate overall improvement using a financial health score
        if total_gap == 0:
            overall_improvement = 100
        elif total_gap < total_target * 0.1:
            overall_improvement = 90
        elif total_gap < total_target * 0.2:
            overall_improvement = 80
        elif total_gap < total_target * 0.3:
            overall_improvement = 70
        elif total_gap < total_target * 0.4:
            overall_improvement = 60
        else:
            overall_improvement = 50 - min(50, int(gap_percentage / 2))
        
        # Return financial impact metrics
        return {
            "total_gap_amount": total_gap,
            "gap_percentage": gap_percentage,
            "monthly_investment_needed": total_monthly_needed,
            "annual_investment_needed": annual_investment,
            "income_percentage": income_percentage,
            "overall_improvement": overall_improvement
        }
    
    def calculate_scenario_timeline_impact(self, scenario: Scenario, 
                                        gap_results: Optional[List[GapResult]] = None) -> Dict[str, Any]:
        """
        Calculate the timeline impact of a given scenario.
        
        Args:
            scenario: The scenario to evaluate
            gap_results: Optional pre-calculated gap results
            
        Returns:
            Dictionary with timeline impact metrics
        """
        # Calculate gap results if not provided
        if gap_results is None:
            gap_results = []
            for goal in scenario.goals:
                gap_result = self.gap_analyzer.analyze_goal_gap(goal, scenario.profile)
                gap_results.append(gap_result)
        
        # Calculate average timeline gap
        total_timeframe_gap = sum(result.timeframe_gap for result in gap_results)
        avg_timeframe_gap = total_timeframe_gap / len(gap_results) if gap_results else 0
        
        # Calculate number of delayed goals
        delayed_goals = sum(1 for result in gap_results if result.timeframe_gap > 0)
        
        # Calculate timeline impact on high-priority goals
        high_priority_gaps = []
        for goal, result in zip(scenario.goals, gap_results):
            if goal.get("importance", "medium") == "high":
                high_priority_gaps.append(result.timeframe_gap)
        
        high_priority_avg_gap = sum(high_priority_gaps) / len(high_priority_gaps) if high_priority_gaps else 0
        
        # Calculate timeline feasibility score
        if avg_timeframe_gap <= 0:
            timeline_feasibility = 100  # On time or ahead of schedule
        elif avg_timeframe_gap < 6:
            timeline_feasibility = 90 - (avg_timeframe_gap * 2)  # Minor delays
        elif avg_timeframe_gap < 12:
            timeline_feasibility = 80 - (avg_timeframe_gap * 1.5)  # Moderate delays
        elif avg_timeframe_gap < 24:
            timeline_feasibility = 60 - avg_timeframe_gap  # Significant delays
        else:
            timeline_feasibility = 30  # Severe delays
        
        # Cap feasibility between 0 and 100
        timeline_feasibility = max(0, min(100, timeline_feasibility))
        
        # Calculate overall timeline improvement
        timeline_improvement = 100 - abs(min(0, int(timeline_feasibility - 70) * 1.5))
        
        # Return timeline impact metrics
        return {
            "average_timeframe_gap": avg_timeframe_gap,
            "delayed_goals": delayed_goals,
            "high_priority_avg_gap": high_priority_avg_gap,
            "timeline_feasibility": timeline_feasibility,
            "timeline_improvement": timeline_improvement
        }
    
    # Private helper methods
    
    def _apply_goal_adjustments(self, goals: List[Dict[str, Any]], 
                             adjustments: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply adjustments to specific goals"""
        # Create a mapping of goal ID to goal
        goal_dict = {goal["id"]: goal for goal in goals}
        
        # Apply adjustments to each goal
        for goal_id, goal_adj in adjustments.items():
            if goal_id in goal_dict:
                # Update the goal with the adjustments
                for key, value in goal_adj.items():
                    goal_dict[goal_id][key] = value
        
        # Return the updated goals list
        return list(goal_dict.values())
    
    def _apply_profile_adjustments(self, profile: Dict[str, Any], 
                                adjustments: Dict[str, Any]) -> Dict[str, Any]:
        """Apply adjustments to the user profile"""
        # Make a copy of the profile
        updated_profile = copy.deepcopy(profile)
        
        # Apply direct adjustments to the profile
        for key, value in adjustments.items():
            if isinstance(value, dict) and key in updated_profile and isinstance(updated_profile[key], dict):
                # Update nested dictionary
                updated_profile[key].update(value)
            else:
                # Update or add top-level key
                updated_profile[key] = value
        
        # Return the updated profile
        return updated_profile
    
    def _apply_timeline_adjustments(self, goals: List[Dict[str, Any]], 
                                 adjustments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply timeline adjustments to goals"""
        # Create a mapping of goal ID to goal
        goal_dict = {goal["id"]: goal for goal in goals}
        
        # Apply general timeline adjustment if specified
        if "general_extension_months" in adjustments:
            extension_months = adjustments["general_extension_months"]
            for goal in goal_dict.values():
                if "target_date" in goal:
                    try:
                        target_date = datetime.strptime(goal["target_date"], "%Y-%m-%d").date()
                        # Add months to the target date
                        new_month = target_date.month + extension_months
                        years_to_add = (new_month - 1) // 12
                        new_month = ((new_month - 1) % 12) + 1
                        new_date = date(
                            year=target_date.year + years_to_add,
                            month=new_month,
                            day=min(target_date.day, [31, 29 if years_to_add % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][new_month - 1])
                        )
                        goal["target_date"] = new_date.strftime("%Y-%m-%d")
                    except (ValueError, KeyError):
                        logger.warning(f"Could not adjust target date for goal {goal.get('id')}")
        
        # Apply specific goal timeline adjustments
        if "goal_extensions" in adjustments:
            for goal_id, extension_months in adjustments["goal_extensions"].items():
                if goal_id in goal_dict and "target_date" in goal_dict[goal_id]:
                    try:
                        target_date = datetime.strptime(goal_dict[goal_id]["target_date"], "%Y-%m-%d").date()
                        # Add months to the target date
                        new_month = target_date.month + extension_months
                        years_to_add = (new_month - 1) // 12
                        new_month = ((new_month - 1) % 12) + 1
                        new_date = date(
                            year=target_date.year + years_to_add,
                            month=new_month,
                            day=min(target_date.day, [31, 29 if years_to_add % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][new_month - 1])
                        )
                        goal_dict[goal_id]["target_date"] = new_date.strftime("%Y-%m-%d")
                    except (ValueError, KeyError):
                        logger.warning(f"Could not adjust target date for goal {goal_id}")
        
        # Return the updated goals
        return list(goal_dict.values())
    
    def _apply_allocation_adjustments(self, goals: List[Dict[str, Any]], 
                                   adjustments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply asset allocation adjustments to goals"""
        # Create a mapping of goal ID to goal
        goal_dict = {goal["id"]: goal for goal in goals}
        
        # Apply specific goal allocation adjustments
        for goal_id, allocation in adjustments.items():
            if goal_id in goal_dict:
                # Update or add allocation
                goal_dict[goal_id]["asset_allocation"] = allocation
        
        # Return the updated goals
        return list(goal_dict.values())
    
    def _calculate_comparison_metrics(self, scenarios: List[ScenarioResult]) -> Dict[str, Dict[str, Any]]:
        """Calculate comparative metrics between scenarios"""
        comparison = {}
        
        # Calculate relative success probability
        if scenarios:
            base_success = scenarios[0].success_probability
            comparison["relative_success"] = {
                scenario.scenario.name: ((scenario.success_probability / base_success) - 1) * 100 
                for scenario in scenarios
            }
        
        # Calculate relative financial impact
        if scenarios:
            base_financials = scenarios[0].financial_impact.get("overall_improvement", 50)
            comparison["relative_financial_impact"] = {
                scenario.scenario.name: ((scenario.financial_impact.get("overall_improvement", 50) / base_financials) - 1) * 100 
                for scenario in scenarios
            }
        
        # Calculate relative timeline impact
        if scenarios:
            base_timeline = scenarios[0].timeline_impact.get("timeline_improvement", 50)
            comparison["relative_timeline_impact"] = {
                scenario.scenario.name: ((scenario.timeline_impact.get("timeline_improvement", 50) / base_timeline) - 1) * 100 
                for scenario in scenarios
            }
        
        # Calculate composite score
        comparison["composite_score"] = {}
        for scenario in scenarios:
            financial_score = scenario.financial_impact.get("overall_improvement", 0) / 100.0
            timeline_score = scenario.timeline_impact.get("timeline_improvement", 0) / 100.0
            effort_score = 1.0 - scenario.effort_required
            
            composite = (
                financial_score * self.params["financial_impact_weight"] +
                timeline_score * self.params["timeline_impact_weight"] +
                effort_score * self.params["effort_weight"]
            ) * 100
            
            comparison["composite_score"][scenario.scenario.name] = composite
        
        return comparison
    
    def _identify_optimal_scenario(self, scenarios: List[ScenarioResult]) -> str:
        """Identify the optimal scenario based on composite score"""
        if not scenarios:
            return ""
        
        # Calculate composite scores
        scores = {}
        for scenario in scenarios:
            financial_score = scenario.financial_impact.get("overall_improvement", 0) / 100.0
            timeline_score = scenario.timeline_impact.get("timeline_improvement", 0) / 100.0
            effort_score = 1.0 - scenario.effort_required
            
            composite = (
                financial_score * self.params["financial_impact_weight"] +
                timeline_score * self.params["timeline_impact_weight"] +
                effort_score * self.params["effort_weight"]
            )
            
            scores[scenario.scenario.name] = composite
        
        # Return the scenario with the highest score
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        # Default to the first scenario
        return scenarios[0].scenario.name
    
    def _extract_monthly_income(self, profile: Dict[str, Any]) -> float:
        """Extract monthly income from profile data"""
        # Look for direct income field
        if "income" in profile:
            return float(profile["income"])
        
        # Look in answers
        if "answers" in profile:
            for answer in profile["answers"]:
                if answer.get("question_id") == "monthly_income":
                    return float(answer.get("answer", 0))
        
        # Default value
        return 50000  # Default assumption
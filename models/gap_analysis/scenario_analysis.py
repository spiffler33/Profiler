"""
Scenario Analysis Module

This module provides tools for analyzing scenarios, comparing gap differences,
and preparing visualization data for gap analysis results.
"""

import logging
import json
import copy
import math
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Union, Any, Tuple, Set

from models.gap_analysis.core import (
    GapSeverity,
    GapResult,
    Scenario,
    ScenarioResult,
    ScenarioComparison
)
from models.gap_analysis.analyzer import GapAnalysis
from models.gap_analysis.scenarios import GoalScenarioComparison
from models.gap_analysis.scenario_generators import ScenarioGenerator

logger = logging.getLogger(__name__)

class ScenarioAnalyzer:
    """
    Class for analyzing scenarios and comparing gaps between different scenarios.
    
    This class provides methods to analyze scenarios, compare gaps between different 
    scenarios, and identify improvements or deteriorations in financial outcomes.
    """
    
    def __init__(self, param_service=None):
        """
        Initialize the scenario analyzer with financial parameters.
        
        Args:
            param_service: Optional financial parameter service instance.
                           If not provided, will attempt to get one.
        """
        # Get parameter service if not provided
        self.param_service = param_service
        
        # Only try to get service if explicitly None (for test patching)
        if self.param_service is None:
            from models.gap_analysis.core import get_financial_parameter_service
            self.param_service = get_financial_parameter_service()
            
        # Create a gap analysis instance for evaluating scenarios
        self.gap_analyzer = GapAnalysis(param_service=self.param_service)
        
    def analyze_scenario(self, scenario: Scenario, gap_analyzer: Optional[GapAnalysis] = None) -> Dict[str, Any]:
        """
        Run a full gap analysis on a scenario.
        
        Args:
            scenario: The scenario to analyze
            gap_analyzer: Optional gap analyzer instance to use
                         (if not provided, uses the instance from initialization)
                         
        Returns:
            Dictionary with detailed gap analysis results
        """
        # Use provided gap analyzer or default
        analyzer = gap_analyzer or self.gap_analyzer
        
        # Analyze each goal in the scenario
        goal_gaps = []
        for goal in scenario.goals:
            gap_result = analyzer.analyze_goal_gap(goal, scenario.profile)
            goal_gaps.append(gap_result)
        
        # Calculate aggregate metrics
        total_gap_amount = sum(result.gap_amount for result in goal_gaps)
        average_gap_percentage = sum(result.gap_percentage for result in goal_gaps) / len(goal_gaps) if goal_gaps else 0
        total_monthly_required = sum(result.capacity_gap for result in goal_gaps)
        
        # Identify resource conflicts
        resource_conflicts = analyzer._identify_resource_conflicts(goal_gaps, scenario.profile)
        
        # Generate overall assessment
        overall_assessment = analyzer._generate_overall_assessment(goal_gaps, scenario.profile)
        
        # Prepare result
        result = {
            "scenario_name": scenario.name,
            "overall_assessment": overall_assessment,
            "goal_gaps": [gap.to_dict() for gap in goal_gaps],
            "resource_conflicts": resource_conflicts,
            "total_gap_amount": total_gap_amount,
            "average_gap_percentage": average_gap_percentage,
            "total_monthly_required": total_monthly_required,
            "saving_potential": analyzer._calculate_saving_potential(scenario.profile)
        }
        
        return result
    
    def compare_scenario_gaps(self, scenario1: Scenario, scenario2: Scenario) -> Dict[str, Any]:
        """
        Compare gap differences between two scenarios.
        
        Args:
            scenario1: First scenario (often baseline)
            scenario2: Second scenario to compare against
            
        Returns:
            Dictionary with comparison results
        """
        # Analyze both scenarios
        scenario1_analysis = self.analyze_scenario(scenario1)
        scenario2_analysis = self.analyze_scenario(scenario2)
        
        # Calculate delta metrics
        delta_total_gap = scenario2_analysis["total_gap_amount"] - scenario1_analysis["total_gap_amount"]
        delta_percentage = scenario2_analysis["average_gap_percentage"] - scenario1_analysis["average_gap_percentage"]
        delta_monthly = scenario2_analysis["total_monthly_required"] - scenario1_analysis["total_monthly_required"]
        
        # Map goals by ID for comparison
        goals1_by_id = {goal["id"]: goal for goal in scenario1.goals}
        goals2_by_id = {goal["id"]: goal for goal in scenario2.goals}
        
        # Create sets of goal IDs
        goal_ids1 = set(goals1_by_id.keys())
        goal_ids2 = set(goals2_by_id.keys())
        
        # Map gap results by goal ID
        gaps1_by_id = {gap["goal_id"]: gap for gap in scenario1_analysis["goal_gaps"]}
        gaps2_by_id = {gap["goal_id"]: gap for gap in scenario2_analysis["goal_gaps"]}
        
        # Compare individual goals present in both scenarios
        common_goal_ids = goal_ids1.intersection(goal_ids2)
        goal_comparisons = []
        
        for goal_id in common_goal_ids:
            if goal_id in gaps1_by_id and goal_id in gaps2_by_id:
                gap1 = gaps1_by_id[goal_id]
                gap2 = gaps2_by_id[goal_id]
                
                # Calculate deltas
                gap_amount_delta = gap2["gap_amount"] - gap1["gap_amount"]
                gap_percentage_delta = gap2["gap_percentage"] - gap1["gap_percentage"]
                timeframe_delta = gap2["timeframe_gap"] - gap1["timeframe_gap"]
                capacity_delta = gap2["capacity_gap"] - gap1["capacity_gap"]
                
                # Determine improvement/deterioration
                has_improved = (gap_amount_delta < 0 or gap_percentage_delta < 0 or 
                               (timeframe_delta < 0 and gap1["timeframe_gap"] > 0) or 
                               (capacity_delta < 0 and gap1["capacity_gap"] > 0))
                
                goal_comparison = {
                    "goal_id": goal_id,
                    "goal_title": gap2["goal_title"],
                    "gap_amount_delta": gap_amount_delta,
                    "gap_percentage_delta": gap_percentage_delta,
                    "timeframe_delta": timeframe_delta,
                    "capacity_delta": capacity_delta,
                    "has_improved": has_improved
                }
                
                goal_comparisons.append(goal_comparison)
        
        # Goals only in scenario 1
        only_in_scenario1 = []
        for goal_id in goal_ids1.difference(goal_ids2):
            only_in_scenario1.append({
                "goal_id": goal_id,
                "goal_title": goals1_by_id[goal_id].get("title", "Unknown Goal")
            })
        
        # Goals only in scenario 2
        only_in_scenario2 = []
        for goal_id in goal_ids2.difference(goal_ids1):
            only_in_scenario2.append({
                "goal_id": goal_id,
                "goal_title": goals2_by_id[goal_id].get("title", "Unknown Goal")
            })
        
        # Calculate overall improvement percentage
        if scenario1_analysis["total_gap_amount"] > 0:
            overall_improvement = -delta_total_gap / scenario1_analysis["total_gap_amount"] * 100
        else:
            overall_improvement = 0 if delta_total_gap >= 0 else 100
        
        # Return comparison results
        return {
            "scenario1_name": scenario1.name,
            "scenario2_name": scenario2.name,
            "delta_total_gap": delta_total_gap,
            "delta_percentage": delta_percentage,
            "delta_monthly_required": delta_monthly,
            "overall_improvement_percentage": overall_improvement,
            "goal_comparisons": goal_comparisons,
            "only_in_scenario1": only_in_scenario1,
            "only_in_scenario2": only_in_scenario2,
            "is_overall_improvement": delta_total_gap < 0
        }
    
    def identify_most_improved_goals(self, baseline: Scenario, alternative: Scenario) -> List[Dict[str, Any]]:
        """
        Identify goals with the biggest improvements between scenarios.
        
        Args:
            baseline: Baseline scenario
            alternative: Alternative scenario to compare against
            
        Returns:
            List of goals with improvement metrics, sorted by improvement magnitude
        """
        # Get comparison data
        comparison = self.compare_scenario_gaps(baseline, alternative)
        
        # Filter for improved goals
        improved_goals = [goal for goal in comparison["goal_comparisons"] if goal["has_improved"]]
        
        # Add improvement percentage
        for goal in improved_goals:
            # Find baseline gap for this goal
            baseline_analysis = self.analyze_scenario(baseline)
            baseline_gaps = {gap["goal_id"]: gap for gap in baseline_analysis["goal_gaps"]}
            
            if goal["goal_id"] in baseline_gaps:
                baseline_gap = baseline_gaps[goal["goal_id"]]
                
                # Calculate improvement percentage
                if baseline_gap["gap_amount"] > 0:
                    goal["improvement_percentage"] = abs(goal["gap_amount_delta"]) / baseline_gap["gap_amount"] * 100
                else:
                    goal["improvement_percentage"] = 100 if goal["gap_amount_delta"] < 0 else 0
            else:
                goal["improvement_percentage"] = 0
        
        # Sort by improvement percentage
        improved_goals.sort(key=lambda x: x.get("improvement_percentage", 0), reverse=True)
        
        return improved_goals
    
    def identify_worsened_goals(self, baseline: Scenario, alternative: Scenario) -> List[Dict[str, Any]]:
        """
        Identify goals that worsened between scenarios.
        
        Args:
            baseline: Baseline scenario
            alternative: Alternative scenario to compare against
            
        Returns:
            List of goals with deterioration metrics, sorted by deterioration magnitude
        """
        # Get comparison data
        comparison = self.compare_scenario_gaps(baseline, alternative)
        
        # Filter for worsened goals
        worsened_goals = [goal for goal in comparison["goal_comparisons"] if not goal["has_improved"]]
        
        # Add deterioration percentage
        for goal in worsened_goals:
            # Find baseline gap for this goal
            baseline_analysis = self.analyze_scenario(baseline)
            baseline_gaps = {gap["goal_id"]: gap for gap in baseline_analysis["goal_gaps"]}
            
            if goal["goal_id"] in baseline_gaps:
                baseline_gap = baseline_gaps[goal["goal_id"]]
                
                # Calculate deterioration percentage
                if baseline_gap["gap_amount"] > 0:
                    goal["deterioration_percentage"] = abs(goal["gap_amount_delta"]) / baseline_gap["gap_amount"] * 100
                else:
                    goal["deterioration_percentage"] = 100 if goal["gap_amount_delta"] > 0 else 0
            else:
                goal["deterioration_percentage"] = 0
        
        # Sort by deterioration percentage
        worsened_goals.sort(key=lambda x: x.get("deterioration_percentage", 0), reverse=True)
        
        return worsened_goals
    
    def calculate_total_gap_reduction(self, baseline: Scenario, alternative: Scenario) -> Dict[str, Any]:
        """
        Calculate total gap reduction between scenarios.
        
        Args:
            baseline: Baseline scenario
            alternative: Alternative scenario to compare against
            
        Returns:
            Dictionary with gap reduction metrics
        """
        # Analyze both scenarios
        baseline_analysis = self.analyze_scenario(baseline)
        alternative_analysis = self.analyze_scenario(alternative)
        
        # Calculate absolute gap reduction
        gap_reduction = baseline_analysis["total_gap_amount"] - alternative_analysis["total_gap_amount"]
        
        # Calculate percentage reduction
        if baseline_analysis["total_gap_amount"] > 0:
            percentage_reduction = (gap_reduction / baseline_analysis["total_gap_amount"]) * 100
        else:
            percentage_reduction = 100 if gap_reduction > 0 else 0
        
        # Calculate monthly contribution reduction
        monthly_reduction = baseline_analysis["total_monthly_required"] - alternative_analysis["total_monthly_required"]
        
        # Return reduction metrics
        return {
            "absolute_gap_reduction": gap_reduction,
            "percentage_reduction": percentage_reduction,
            "monthly_contribution_reduction": monthly_reduction,
            "is_improvement": gap_reduction > 0
        }


class ScenarioVisualizer:
    """
    Class for preparing visualization data from scenario analyses.
    
    This class provides methods to format and structure scenario data
    for various visualization types including charts, timelines, and
    comparative views.
    """
    
    def __init__(self):
        """Initialize the scenario visualizer."""
        pass
    
    def prepare_visualization_data(self, scenarios: List[Scenario]) -> Dict[str, Any]:
        """
        Prepare data for visualization across multiple scenarios.
        
        Args:
            scenarios: List of scenarios to visualize
            
        Returns:
            Dictionary with formatted data for visualization
        """
        # Create an analyzer to get scenario data
        analyzer = ScenarioAnalyzer()
        
        # Analyze each scenario
        scenario_analyses = [analyzer.analyze_scenario(scenario) for scenario in scenarios]
        
        # Extract key metrics for visualization
        scenario_names = [scenario.name for scenario in scenarios]
        total_gaps = [analysis["total_gap_amount"] for analysis in scenario_analyses]
        avg_percentages = [analysis["average_gap_percentage"] for analysis in scenario_analyses]
        monthly_required = [analysis["total_monthly_required"] for analysis in scenario_analyses]
        
        # Prepare data for bar charts
        bar_chart_data = {
            "labels": scenario_names,
            "datasets": [
                {
                    "label": "Total Gap Amount",
                    "data": total_gaps
                },
                {
                    "label": "Monthly Required",
                    "data": monthly_required
                }
            ]
        }
        
        # Prepare data for radar chart
        radar_chart_data = {
            "labels": scenario_names,
            "datasets": [
                {
                    "label": "Gap Percentage",
                    "data": avg_percentages
                },
                {
                    "label": "Monthly Contribution (scaled)",
                    "data": [monthly / max(monthly_required) * 100 if max(monthly_required) > 0 else 0 
                             for monthly in monthly_required]
                }
            ]
        }
        
        # Get goal categories across all scenarios
        all_goals = [goal for scenario in scenarios for goal in scenario.goals]
        unique_categories = set(goal.get("category", "other") for goal in all_goals)
        
        # Prepare category comparison data
        category_data = {}
        for category in unique_categories:
            category_data[category] = []
            
            for analysis in scenario_analyses:
                # Find gaps for this category
                category_gaps = [gap for gap in analysis["goal_gaps"] 
                                if gap["goal_category"] == category]
                
                # Calculate average gap percentage for this category
                if category_gaps:
                    avg_gap = sum(gap["gap_percentage"] for gap in category_gaps) / len(category_gaps)
                else:
                    avg_gap = 0
                    
                category_data[category].append(avg_gap)
        
        # Return visualization data
        return {
            "scenario_names": scenario_names,
            "bar_chart_data": bar_chart_data,
            "radar_chart_data": radar_chart_data,
            "category_data": category_data
        }
    
    def prepare_timeline_comparison(self, scenarios: List[Scenario]) -> Dict[str, Any]:
        """
        Prepare data for timeline visualization across scenarios.
        
        Args:
            scenarios: List of scenarios to visualize
            
        Returns:
            Dictionary with formatted data for timeline visualization
        """
        # Create an analyzer to get scenario data
        analyzer = ScenarioAnalyzer()
        
        # Analyze each scenario
        scenario_analyses = [analyzer.analyze_scenario(scenario) for scenario in scenarios]
        
        # Extract timeline data from goals across all scenarios
        timeline_data = {}
        
        for i, scenario in enumerate(scenarios):
            analysis = scenario_analyses[i]
            scenario_name = scenario.name
            timeline_data[scenario_name] = []
            
            # Extract timing for each goal
            for goal in scenario.goals:
                goal_id = goal.get("id")
                goal_title = goal.get("title", "Unknown Goal")
                
                # Find corresponding gap analysis
                goal_gap = next((gap for gap in analysis["goal_gaps"] if gap["goal_id"] == goal_id), None)
                
                if goal_gap:
                    # Extract target date
                    target_date_str = goal.get("target_date")
                    if target_date_str:
                        try:
                            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
                            
                            # Calculate actual completion date based on timeframe gap
                            timeframe_gap = goal_gap["timeframe_gap"]
                            if timeframe_gap > 0:
                                # Add months to target date if there's a gap
                                completion_date = date(
                                    year=target_date.year + ((target_date.month + timeframe_gap - 1) // 12),
                                    month=((target_date.month + timeframe_gap - 1) % 12) + 1,
                                    day=min(target_date.day, 28)  # Simplify day handling
                                )
                            else:
                                # Use target date if no gap or ahead of schedule
                                completion_date = target_date
                                
                            # Add to timeline data
                            timeline_data[scenario_name].append({
                                "goal_id": goal_id,
                                "goal_title": goal_title,
                                "target_date": target_date.isoformat(),
                                "completion_date": completion_date.isoformat(),
                                "timeframe_gap": timeframe_gap,
                                "on_track": timeframe_gap <= 0
                            })
                        except ValueError:
                            # Skip if date parsing fails
                            pass
        
        # Prepare timeline visualization data
        start_date = date.today().isoformat()
        end_date = date.today().replace(year=date.today().year + 10).isoformat()  # 10 years out
        
        # Return timeline data
        return {
            "scenario_names": [scenario.name for scenario in scenarios],
            "timeline_data": timeline_data,
            "start_date": start_date,
            "end_date": end_date
        }
    
    def prepare_funding_comparison(self, scenarios: List[Scenario]) -> Dict[str, Any]:
        """
        Prepare data for funding comparison visualization.
        
        Args:
            scenarios: List of scenarios to visualize
            
        Returns:
            Dictionary with formatted data for funding comparison
        """
        # Create an analyzer to get scenario data
        analyzer = ScenarioAnalyzer()
        
        # Analyze each scenario
        scenario_analyses = [analyzer.analyze_scenario(scenario) for scenario in scenarios]
        
        # Extract funding data
        funding_data = {}
        
        for i, scenario in enumerate(scenarios):
            analysis = scenario_analyses[i]
            scenario_name = scenario.name
            
            # Get total monthly funding required
            monthly_required = analysis["total_monthly_required"]
            
            # Approximate monthly income (could come from scenario profile)
            monthly_income = analyzer.gap_analyzer._extract_monthly_income(scenario.profile)
            
            # Calculate percentage of income
            income_percentage = (monthly_required / monthly_income * 100) if monthly_income > 0 else 0
            
            # Get goal-specific funding requirements
            goal_funding = []
            for gap in analysis["goal_gaps"]:
                if gap["capacity_gap"] > 0:
                    goal_funding.append({
                        "goal_id": gap["goal_id"],
                        "goal_title": gap["goal_title"],
                        "monthly_required": gap["capacity_gap"],
                        "percentage_of_total": (gap["capacity_gap"] / monthly_required * 100) if monthly_required > 0 else 0
                    })
            
            # Sort by monthly required
            goal_funding.sort(key=lambda x: x["monthly_required"], reverse=True)
            
            # Add to funding data
            funding_data[scenario_name] = {
                "total_monthly_required": monthly_required,
                "monthly_income": monthly_income,
                "income_percentage": income_percentage,
                "goal_funding": goal_funding
            }
        
        # Return funding comparison data
        return {
            "scenario_names": [scenario.name for scenario in scenarios],
            "funding_data": funding_data
        }
    
    def prepare_success_probability_comparison(self, scenarios: List[Scenario]) -> Dict[str, Any]:
        """
        Prepare data for success probability comparison.
        
        Args:
            scenarios: List of scenarios to visualize
            
        Returns:
            Dictionary with formatted data for success probability visualization
        """
        # Create scenario comparison to calculate success probabilities
        scenario_comparison = GoalScenarioComparison()
        
        # Calculate success probability for each scenario
        probabilities = {}
        for scenario in scenarios:
            probability = scenario_comparison.calculate_scenario_success_probability(scenario)
            probabilities[scenario.name] = probability * 100  # Convert to percentage
        
        # Prepare success ranges (simplified)
        success_ranges = {
            "high": [80, 100],
            "medium": [60, 80],
            "low": [40, 60],
            "very_low": [0, 40]
        }
        
        # Classify each scenario
        classifications = {}
        for name, probability in probabilities.items():
            if probability >= success_ranges["high"][0]:
                classifications[name] = "high"
            elif probability >= success_ranges["medium"][0]:
                classifications[name] = "medium"
            elif probability >= success_ranges["low"][0]:
                classifications[name] = "low"
            else:
                classifications[name] = "very_low"
        
        # Return success probability data
        return {
            "scenario_names": [scenario.name for scenario in scenarios],
            "probabilities": probabilities,
            "classifications": classifications,
            "success_ranges": success_ranges
        }
    
    def format_data_for_radar_chart(self, scenarios: List[Scenario], metrics: List[str]) -> Dict[str, Any]:
        """
        Format data specifically for multi-dimensional radar chart visualization.
        
        Args:
            scenarios: List of scenarios to visualize
            metrics: List of metric names to include in the radar chart
            
        Returns:
            Dictionary with radar chart formatted data
        """
        # Create an analyzer and comparison object
        analyzer = ScenarioAnalyzer()
        comparison = GoalScenarioComparison()
        
        # Initialize results
        radar_data = {
            "labels": metrics,
            "datasets": []
        }
        
        # Define metric extractors (functions to get metric values)
        metric_extractors = {
            "success_probability": lambda s: comparison.calculate_scenario_success_probability(s) * 100,
            "total_gap": lambda s: analyzer.analyze_scenario(s)["total_gap_amount"],
            "monthly_required": lambda s: analyzer.analyze_scenario(s)["total_monthly_required"],
            "gap_percentage": lambda s: analyzer.analyze_scenario(s)["average_gap_percentage"],
            "effort_required": lambda s: comparison.calculate_scenario_effort_required(s) * 100,
        }
        
        # Extract metric values for each scenario
        raw_values = {}
        for metric in metrics:
            if metric in metric_extractors:
                raw_values[metric] = [metric_extractors[metric](scenario) for scenario in scenarios]
            else:
                # Default to zeros if metric not recognized
                raw_values[metric] = [0] * len(scenarios)
        
        # Normalize values to 0-100 range for radar chart
        normalized_values = {}
        for metric, values in raw_values.items():
            if not values or all(v == 0 for v in values):
                normalized_values[metric] = [0] * len(scenarios)
                continue
                
            # For gap metrics, lower is better, so invert
            if metric in ["total_gap", "monthly_required", "gap_percentage", "effort_required"]:
                max_val = max(values)
                if max_val > 0:
                    # Invert so lower values get higher scores
                    normalized_values[metric] = [100 - (v / max_val * 100) for v in values]
                else:
                    normalized_values[metric] = [100] * len(scenarios)
            else:
                # For success probability, higher is better
                max_val = max(values)
                if max_val > 0:
                    normalized_values[metric] = [(v / max_val * 100) for v in values]
                else:
                    normalized_values[metric] = [0] * len(scenarios)
        
        # Create radar chart datasets
        for i, scenario in enumerate(scenarios):
            dataset = {
                "label": scenario.name,
                "data": [normalized_values[metric][i] for metric in metrics]
            }
            radar_data["datasets"].append(dataset)
        
        # Return radar chart data
        return radar_data


class ScenarioImpactAnalyzer:
    """
    Class for analyzing the broader financial impact of different scenarios.
    
    This class provides methods to evaluate scenarios across multiple financial
    health dimensions including liquidity, stability, debt management, and 
    tax efficiency.
    """
    
    def __init__(self, param_service=None):
        """
        Initialize the impact analyzer with financial parameters.
        
        Args:
            param_service: Optional financial parameter service instance.
                           If not provided, will attempt to get one.
        """
        # Get parameter service if not provided
        self.param_service = param_service
        
        # Only try to get service if explicitly None (for test patching)
        if self.param_service is None:
            from models.gap_analysis.core import get_financial_parameter_service
            self.param_service = get_financial_parameter_service()
        
        # Default impact assessment parameters
        self.params = {
            "emergency_fund_weight": 0.25,
            "retirement_weight": 0.25,
            "debt_management_weight": 0.20,
            "goal_achievement_weight": 0.20,
            "tax_efficiency_weight": 0.10,
            
            # Indian context parameters
            "ideal_emergency_fund_months": 6,
            "min_retirement_contribution": 0.15,  # 15% of income
            "max_debt_service_ratio": 0.40,  # 40% of income
            "ideal_debt_payoff_years": 7,
            "min_tax_optimized_percentage": 0.80  # 80% of eligible deductions
        }
        
        # Override defaults with values from parameter service if available
        if self.param_service:
            try:
                # Try to use get_parameters_by_prefix if available
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    param_values = self.param_service.get_parameters_by_prefix("impact_analysis.")
                    if param_values:
                        self.params.update(param_values)
            except Exception as e:
                logger.warning(f"Error getting parameters: {e}")
                # Continue with defaults
    
    def analyze_financial_health_impact(self, scenario: Scenario) -> Dict[str, Any]:
        """
        Evaluate overall financial wellbeing impact of a scenario.
        
        Args:
            scenario: The scenario to evaluate
            
        Returns:
            Dictionary with financial health impact metrics
        """
        # Calculate individual health metrics
        liquidity_impact = self.calculate_liquidity_impact(scenario)
        stability_impact = self.calculate_long_term_stability_impact(scenario)
        debt_impact = self.calculate_debt_management_impact(scenario)
        tax_impact = self.calculate_tax_efficiency_impact(scenario)
        
        # Calculate goal achievement impact
        # Create scenario analyzer to get gap analysis
        analyzer = ScenarioAnalyzer()
        analysis = analyzer.analyze_scenario(scenario)
        
        # Calculate achievement score (inverse of average gap percentage)
        achievement_score = max(0, 100 - analysis["average_gap_percentage"])
        
        # Calculate overall health score (weighted average)
        overall_score = (
            liquidity_impact["emergency_fund_score"] * self.params["emergency_fund_weight"] +
            stability_impact["retirement_readiness_score"] * self.params["retirement_weight"] +
            debt_impact["overall_debt_score"] * self.params["debt_management_weight"] +
            achievement_score * self.params["goal_achievement_weight"] +
            tax_impact["tax_efficiency_score"] * self.params["tax_efficiency_weight"]
        )
        
        # Classify health impact
        health_classification = self._classify_financial_health(overall_score)
        
        # Generate recommendations
        recommendations = self._generate_health_recommendations(
            liquidity_impact, stability_impact, debt_impact, tax_impact, achievement_score
        )
        
        # Return overall health impact
        return {
            "overall_health_score": overall_score,
            "health_classification": health_classification,
            "component_scores": {
                "emergency_fund": liquidity_impact["emergency_fund_score"],
                "retirement_readiness": stability_impact["retirement_readiness_score"],
                "debt_management": debt_impact["overall_debt_score"],
                "goal_achievement": achievement_score,
                "tax_efficiency": tax_impact["tax_efficiency_score"]
            },
            "recommendations": recommendations
        }
    
    def calculate_liquidity_impact(self, scenario: Scenario) -> Dict[str, Any]:
        """
        Assess effect on emergency preparedness and liquidity.
        
        Args:
            scenario: The scenario to evaluate
            
        Returns:
            Dictionary with liquidity impact metrics
        """
        # Extract profile data
        profile = scenario.profile
        monthly_expenses = self._extract_monthly_expenses(profile)
        
        # Look for emergency fund goal
        emergency_fund_goal = next(
            (goal for goal in scenario.goals if goal.get("category") == "emergency_fund"),
            None
        )
        
        # Calculate emergency fund coverage
        if emergency_fund_goal:
            target_amount = float(emergency_fund_goal.get("target_amount", 0))
            current_amount = float(emergency_fund_goal.get("current_amount", 0))
            
            if monthly_expenses > 0:
                current_months_coverage = current_amount / monthly_expenses
                target_months_coverage = target_amount / monthly_expenses
            else:
                current_months_coverage = 0
                target_months_coverage = 0
        else:
            # If no emergency fund goal, look for cash assets
            cash_assets = 0
            if "assets" in profile and "cash" in profile["assets"]:
                cash_assets = float(profile["assets"]["cash"])
            
            current_months_coverage = cash_assets / monthly_expenses if monthly_expenses > 0 else 0
            target_months_coverage = self.params["ideal_emergency_fund_months"]
            current_amount = cash_assets
            target_amount = monthly_expenses * target_months_coverage
        
        # Calculate shortfall
        shortfall = max(0, target_amount - current_amount)
        shortfall_percentage = (shortfall / target_amount * 100) if target_amount > 0 else 0
        
        # Calculate emergency fund score
        ideal_months = self.params["ideal_emergency_fund_months"]
        if current_months_coverage >= ideal_months:
            emergency_fund_score = 100
        elif current_months_coverage <= 0:
            emergency_fund_score = 0
        else:
            emergency_fund_score = (current_months_coverage / ideal_months) * 100
        
        # Return liquidity impact metrics
        return {
            "current_months_coverage": current_months_coverage,
            "target_months_coverage": target_months_coverage,
            "shortfall": shortfall,
            "shortfall_percentage": shortfall_percentage,
            "emergency_fund_score": emergency_fund_score,
            "current_amount": current_amount,
            "target_amount": target_amount
        }
    
    def calculate_long_term_stability_impact(self, scenario: Scenario) -> Dict[str, Any]:
        """
        Assess impact on retirement security and long-term stability.
        
        Args:
            scenario: The scenario to evaluate
            
        Returns:
            Dictionary with long-term stability impact metrics
        """
        # Extract profile data
        profile = scenario.profile
        monthly_income = self._extract_monthly_income(profile)
        annual_income = monthly_income * 12
        age = profile.get("age", 35)  # Default to 35 if not specified
        
        # Look for retirement goal
        retirement_goal = next(
            (goal for goal in scenario.goals if goal.get("category") == "retirement"),
            None
        )
        
        # Calculate retirement metrics
        if retirement_goal:
            target_amount = float(retirement_goal.get("target_amount", 0))
            current_amount = float(retirement_goal.get("current_amount", 0))
            
            # Extract or estimate retirement age
            retirement_age = 60  # Default
            if "target_date" in retirement_goal:
                try:
                    target_date = datetime.strptime(retirement_goal["target_date"], "%Y-%m-%d").date()
                    retirement_age = target_date.year - date.today().year + age
                except ValueError:
                    pass
            
            # Calculate years to retirement
            years_to_retirement = max(0, retirement_age - age)
            
            # Get or estimate monthly contribution
            if "monthly_contribution" in retirement_goal:
                monthly_contribution = float(retirement_goal["monthly_contribution"])
            else:
                monthly_contribution = annual_income * 0.15 / 12  # Default to 15% of income
            
            # Calculate contribution as percentage of income
            contribution_percentage = (monthly_contribution * 12 / annual_income * 100) if annual_income > 0 else 0
            
            # Calculate progress percentage
            progress_percentage = (current_amount / target_amount * 100) if target_amount > 0 else 0
            
            # Calculate if on track (simplified)
            # In a real system, this would use proper financial projections
            on_track_amount = target_amount * (years_to_retirement / 30)  # Simplified linear progress
            on_track = current_amount >= on_track_amount
        else:
            # Default values if no retirement goal
            target_amount = annual_income * 25  # 25x annual income as a rule of thumb
            current_amount = 0
            if "assets" in profile and "retirement" in profile["assets"]:
                current_amount = float(profile["assets"]["retirement"])
            
            retirement_age = 60
            years_to_retirement = max(0, retirement_age - age)
            monthly_contribution = 0
            contribution_percentage = 0
            progress_percentage = 0
            on_track = False
        
        # Calculate retirement readiness score
        min_contribution = self.params["min_retirement_contribution"]
        
        if contribution_percentage >= min_contribution * 100 and on_track:
            retirement_score = 100
        elif contribution_percentage <= 0:
            retirement_score = 0
        else:
            # Score based on contribution percentage and progress
            contribution_factor = min(1, contribution_percentage / (min_contribution * 100))
            progress_factor = progress_percentage / 100
            retirement_score = (contribution_factor * 0.6 + progress_factor * 0.4) * 100
        
        # Return stability impact metrics
        return {
            "current_amount": current_amount,
            "target_amount": target_amount,
            "monthly_contribution": monthly_contribution,
            "contribution_percentage": contribution_percentage,
            "progress_percentage": progress_percentage,
            "years_to_retirement": years_to_retirement,
            "retirement_age": retirement_age,
            "on_track": on_track,
            "retirement_readiness_score": retirement_score
        }
    
    def calculate_debt_management_impact(self, scenario: Scenario) -> Dict[str, Any]:
        """
        Assess effect on debt strategies and overall debt burden.
        
        Args:
            scenario: The scenario to evaluate
            
        Returns:
            Dictionary with debt management impact metrics
        """
        # Extract profile data
        profile = scenario.profile
        monthly_income = self._extract_monthly_income(profile)
        
        # Extract debt information
        total_debt = 0
        debt_payments = 0
        
        if "debts" in profile:
            # Sum up all debts
            for debt_type, debt_info in profile["debts"].items():
                if isinstance(debt_info, dict):
                    # If detailed debt info
                    total_debt += float(debt_info.get("balance", 0))
                    debt_payments += float(debt_info.get("monthly_payment", 0))
                else:
                    # If just amount
                    total_debt += float(debt_info)
                    
                    # Estimate payment (simplified)
                    if debt_type == "mortgage":
                        # Rough estimate: 30-year mortgage at 6%
                        debt_payments += float(debt_info) * 0.006  # 0.6% monthly payment
                    elif debt_type == "car_loan":
                        # Rough estimate: 5-year car loan at 7%
                        debt_payments += float(debt_info) * 0.02  # 2% monthly payment
                    else:
                        # General debt (credit cards, etc.)
                        debt_payments += float(debt_info) * 0.03  # 3% monthly payment
        
        # Look for debt repayment goals
        debt_goals = [goal for goal in scenario.goals if goal.get("category") == "debt_repayment"]
        
        # If there are specific debt goals, use their data
        if debt_goals:
            # Sum target and current amounts
            debt_target_total = sum(float(goal.get("target_amount", 0)) for goal in debt_goals)
            debt_current_total = sum(float(goal.get("current_amount", 0)) for goal in debt_goals)
            
            # Target amount is how much to pay off
            total_debt = debt_target_total - debt_current_total
        
        # Calculate debt metrics
        debt_to_income = (total_debt / (monthly_income * 12)) if monthly_income > 0 else 0
        debt_service_ratio = (debt_payments / monthly_income) if monthly_income > 0 else 0
        
        # Calculate debt payoff time (in years) based on current payments
        if debt_payments > 0:
            average_interest_rate = 0.06  # Simplified assumption
            
            # Simple formula for approximating payoff time with interest
            # Handle domain error when debt payments are too small relative to total debt
            try:
                payoff_years = -math.log(1 - (total_debt * average_interest_rate / debt_payments)) / math.log(1 + average_interest_rate) / 12
            except (ValueError, ZeroDivisionError):
                # If there's a math domain error, debt can't be paid off with current payments
                payoff_years = float('inf')
            
            # Cap at a reasonable value
            payoff_years = min(50, payoff_years)
        else:
            payoff_years = float('inf') if total_debt > 0 else 0
        
        # Calculate debt management score
        max_dsr = self.params["max_debt_service_ratio"]
        ideal_payoff = self.params["ideal_debt_payoff_years"]
        
        if total_debt <= 0:
            debt_score = 100  # No debt is perfect
        else:
            # Score based on debt service ratio and payoff time
            dsr_factor = max(0, 1 - debt_service_ratio / max_dsr)
            
            if payoff_years == float('inf'):
                payoff_factor = 0
            else:
                payoff_factor = max(0, 1 - payoff_years / (ideal_payoff * 2))
                
            debt_score = (dsr_factor * 0.6 + payoff_factor * 0.4) * 100
        
        # Return debt impact metrics
        return {
            "total_debt": total_debt,
            "monthly_debt_payments": debt_payments,
            "debt_to_income_ratio": debt_to_income,
            "debt_service_ratio": debt_service_ratio,
            "estimated_payoff_years": payoff_years if payoff_years != float('inf') else None,
            "overall_debt_score": debt_score
        }
    
    def calculate_tax_efficiency_impact(self, scenario: Scenario) -> Dict[str, Any]:
        """
        Assess impact on tax optimization strategies.
        
        Args:
            scenario: The scenario to evaluate
            
        Returns:
            Dictionary with tax efficiency impact metrics
        """
        # Extract profile data
        profile = scenario.profile
        tax_bracket = self._extract_tax_bracket(profile)
        
        # Simplistic analysis for Indian context
        is_indian_context = profile.get("country", "").lower() == "india"
        
        # Tax-advantaged contributions
        sec_80c_limit = 150000 if is_indian_context else 0  # Section 80C limit in India
        sec_80c_used = 0
        
        if "tax_details" in profile:
            sec_80c_used = float(profile["tax_details"].get("sec_80c_used", 0))
        
        # Calculate potential tax deductions from goals
        potential_deductions = 0
        
        for goal in scenario.goals:
            category = goal.get("category", "")
            
            # Tax-advantaged categories in Indian context
            if is_indian_context:
                if category == "retirement":
                    potential_deductions += min(
                        float(goal.get("monthly_contribution", 0)) * 12,
                        150000 - sec_80c_used  # Limit to remaining 80C
                    )
                elif category == "education":
                    # Section 80E (education loan interest)
                    if "loan_details" in goal and "interest" in goal["loan_details"]:
                        potential_deductions += float(goal["loan_details"]["interest"])
                elif category == "home":
                    # Section 24 (home loan interest) and 80C (principal)
                    if "loan_details" in goal:
                        if "interest" in goal["loan_details"]:
                            potential_deductions += min(float(goal["loan_details"]["interest"]), 200000)
                        if "principal" in goal["loan_details"]:
                            potential_deductions += min(
                                float(goal["loan_details"]["principal"]),
                                150000 - sec_80c_used  # Limit to remaining 80C
                            )
        
        # Calculate tax efficiency
        total_available = sec_80c_limit + 200000  # Simplified: 80C + 24 (home loan) + health insurance
        total_utilized = sec_80c_used + potential_deductions
        
        efficiency_percentage = (total_utilized / total_available * 100) if total_available > 0 else 0
        optimization_level = self._classify_tax_optimization(efficiency_percentage)
        
        # Calculate potential tax savings
        tax_rate = self._get_tax_rate_for_bracket(tax_bracket)
        potential_savings = potential_deductions * tax_rate
        
        # Calculate tax efficiency score
        min_optimized = self.params["min_tax_optimized_percentage"]
        
        if efficiency_percentage >= min_optimized * 100:
            tax_score = 100
        else:
            tax_score = (efficiency_percentage / (min_optimized * 100)) * 100
        
        # Return tax impact metrics
        return {
            "tax_bracket": tax_bracket,
            "total_available_deductions": total_available,
            "utilized_deductions": total_utilized,
            "efficiency_percentage": efficiency_percentage,
            "optimization_level": optimization_level,
            "potential_tax_savings": potential_savings,
            "tax_efficiency_score": tax_score,
            "is_indian_context": is_indian_context
        }
    
    # Helper methods
    
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
    
    def _extract_monthly_expenses(self, profile: Dict[str, Any]) -> float:
        """Extract monthly expenses from profile data"""
        # Look for direct expenses field
        if "expenses" in profile:
            return float(profile["expenses"])
        
        # Look in answers
        if "answers" in profile:
            for answer in profile["answers"]:
                if answer.get("question_id") == "monthly_expenses":
                    return float(answer.get("answer", 0))
        
        # Default value - assume 60% of income if we know income
        income = self._extract_monthly_income(profile)
        return income * 0.6
    
    def _extract_tax_bracket(self, profile: Dict[str, Any]) -> str:
        """Extract tax bracket from profile data"""
        # Look for direct tax bracket field
        if "tax_details" in profile and "tax_bracket" in profile["tax_details"]:
            return profile["tax_details"]["tax_bracket"]
        
        # Estimate based on income
        annual_income = self._extract_monthly_income(profile) * 12
        
        # Indian tax brackets (simplified)
        if profile.get("country", "").lower() == "india":
            if annual_income <= 500000:
                return "0%"
            elif annual_income <= 750000:
                return "10%"
            elif annual_income <= 1000000:
                return "15%"
            elif annual_income <= 1250000:
                return "20%"
            elif annual_income <= 1500000:
                return "25%"
            else:
                return "30%"
        else:
            # Generic brackets
            if annual_income <= 250000:
                return "0%"
            elif annual_income <= 500000:
                return "5%"
            elif annual_income <= 1000000:
                return "10%"
            elif annual_income <= 2000000:
                return "20%"
            else:
                return "30%"
    
    def _get_tax_rate_for_bracket(self, bracket: str) -> float:
        """Convert tax bracket string to rate"""
        try:
            return float(bracket.strip('%')) / 100
        except (ValueError, AttributeError):
            return 0.2  # Default to 20%
    
    def _classify_financial_health(self, score: float) -> str:
        """Classify financial health based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Satisfactory"
        elif score >= 40:
            return "Needs Improvement"
        else:
            return "Critical Attention Required"
    
    def _classify_tax_optimization(self, efficiency_percentage: float) -> str:
        """Classify tax optimization level"""
        if efficiency_percentage >= 90:
            return "Highly Optimized"
        elif efficiency_percentage >= 70:
            return "Well Optimized"
        elif efficiency_percentage >= 50:
            return "Partially Optimized"
        elif efficiency_percentage >= 30:
            return "Under-Optimized"
        else:
            return "Poorly Optimized"
    
    def _generate_health_recommendations(self, liquidity_impact, stability_impact, 
                                        debt_impact, tax_impact, achievement_score) -> List[str]:
        """Generate financial health recommendations"""
        recommendations = []
        
        # Emergency fund recommendations
        if liquidity_impact["emergency_fund_score"] < 70:
            months = liquidity_impact["current_months_coverage"]
            target = self.params["ideal_emergency_fund_months"]
            recommendations.append(
                f"Build your emergency fund from {months:.1f} months to {target} months of expenses."
            )
        
        # Retirement recommendations
        if stability_impact["retirement_readiness_score"] < 70:
            if stability_impact["contribution_percentage"] < self.params["min_retirement_contribution"] * 100:
                current = stability_impact["contribution_percentage"]
                target = self.params["min_retirement_contribution"] * 100
                recommendations.append(
                    f"Increase retirement contributions from {current:.1f}% to at least {target:.1f}% of income."
                )
            elif not stability_impact["on_track"]:
                recommendations.append(
                    "Consider increasing retirement contributions to get on track with your retirement goal."
                )
        
        # Debt recommendations
        if debt_impact["overall_debt_score"] < 70:
            if debt_impact["debt_service_ratio"] > self.params["max_debt_service_ratio"]:
                recommendations.append(
                    "Reduce your debt service ratio which is currently high relative to your income."
                )
            if debt_impact["estimated_payoff_years"] and debt_impact["estimated_payoff_years"] > self.params["ideal_debt_payoff_years"]:
                current = debt_impact["estimated_payoff_years"]
                target = self.params["ideal_debt_payoff_years"]
                recommendations.append(
                    f"Accelerate debt repayment to reduce payoff time from {current:.1f} years to {target} years."
                )
        
        # Tax recommendations
        if tax_impact["tax_efficiency_score"] < 70:
            if tax_impact["is_indian_context"]:
                recommendations.append(
                    "Maximize Section 80C investments and explore other tax deductions available in India."
                )
            else:
                recommendations.append(
                    "Utilize available tax-advantaged accounts and deductions to optimize your tax situation."
                )
        
        # Goal achievement recommendations
        if achievement_score < 70:
            recommendations.append(
                "Review your financial goals and consider adjusting timelines, targets, or contributions."
            )
        
        return recommendations
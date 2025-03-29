"""
Scenario Generator Module

This module provides predefined scenario generation for gap analysis.
It helps create consistent, well-structured scenarios for comparing
different financial planning approaches.
"""

import logging
import copy
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple, Callable

from models.gap_analysis.core import (
    GapSeverity,
    GapResult,
    Scenario,
    ScenarioResult,
    get_financial_parameter_service
)
from models.gap_analysis.scenarios import GoalScenarioComparison
from models.gap_analysis.timeframe_adjustments import TimeframeAdjustment
from models.gap_analysis.target_adjustments import TargetAdjustment
from models.gap_analysis.allocation_adjustments import AllocationAdjustment
from models.gap_analysis.contribution_adjustments import ContributionAdjustment
from models.gap_analysis.priority_adjustments import PriorityAdjustment

logger = logging.getLogger(__name__)

class ScenarioGenerator:
    """
    Class for generating predefined financial planning scenarios.
    
    This class provides methods to create common financial planning scenarios
    based on different approaches (conservative, aggressive, balanced, etc.)
    that can be compared to help users make informed decisions.
    """
    
    def __init__(self, param_service=None):
        """
        Initialize the scenario generator with financial parameters.
        
        Args:
            param_service: Optional financial parameter service instance.
                           If not provided, will attempt to get one.
        """
        # Get parameter service if not provided
        self.param_service = param_service
        
        # Only try to get service if explicitly None (for test patching)
        if self.param_service is None:
            self.param_service = get_financial_parameter_service()
            
        # Create a scenario comparison instance for creating and evaluating scenarios
        self.scenario_comparison = GoalScenarioComparison(param_service=self.param_service)
        
        # Initialize adjustment strategy classes
        self.timeframe_adjustment = TimeframeAdjustment()
        self.target_adjustment = TargetAdjustment()
        self.allocation_adjustment = AllocationAdjustment()
        self.contribution_adjustment = ContributionAdjustment()
        self.priority_adjustment = PriorityAdjustment()
        
        # Default parameters for scenario generation
        self.params = {
            "conservative_timeline_extension": 24,  # 24 months extension for conservative approach
            "aggressive_contribution_increase": 0.25,  # 25% increase in contributions for aggressive approach
            "aggressive_equity_allocation_increase": 0.15,  # 15% increase in equity allocation
            "conservative_target_reduction": 0.15,  # 15% reduction in target amounts
            "balanced_timeline_extension": 12,  # 12 months extension for balanced approach
            "balanced_contribution_increase": 0.15,  # 15% increase in contributions for balanced approach
            "india_inflation_adjustment": 0.02,  # Additional 2% inflation adjustment for Indian context
            "family_support_factor": 0.1,  # 10% reduction in expenses due to family support
        }
        
        # Override defaults with values from parameter service if available
        if self.param_service:
            try:
                # Try to use get_parameters_by_prefix if available
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    param_values = self.param_service.get_parameters_by_prefix("scenario_generator.")
                    if param_values:
                        self.params.update(param_values)
                # Fall back to getting individual parameters
                else:
                    for key in self.params.keys():
                        param_path = f"scenario_generator.{key}"
                        value = self.param_service.get(param_path)
                        if value is not None:
                            self.params[key] = value
            except Exception as e:
                logger.warning(f"Error getting parameters: {e}")
                # Continue with defaults
    
    def generate_baseline_scenario(self, goals: List[Dict[str, Any]], 
                                  profile: Dict[str, Any]) -> Scenario:
        """
        Generate a baseline scenario using current trajectory without adjustments.
        
        Args:
            goals: List of financial goals
            profile: User profile with financial information
            
        Returns:
            Baseline scenario
        """
        # Create a baseline scenario with no adjustments
        scenario = self.scenario_comparison.create_scenario(
            name="Baseline",
            goals=goals,
            profile=profile,
            description="Baseline scenario with current financial trajectory and no adjustments."
        )
        
        # Add scenario documentation
        scenario.metadata["documentation"] = {
            "description": self.generate_scenario_description(scenario),
            "rationale": "This scenario provides a baseline for comparison, representing the current financial trajectory without any adjustments.",
            "assumptions": [
                "Current saving and spending patterns continue",
                "No changes to goal timelines or target amounts",
                "Current asset allocations are maintained",
                "No significant life changes that would affect finances"
            ]
        }
        
        return scenario
    
    def generate_aggressive_scenario(self, goals: List[Dict[str, Any]], 
                                   profile: Dict[str, Any]) -> Scenario:
        """
        Generate an aggressive scenario with increased contributions and risk.
        
        Args:
            goals: List of financial goals
            profile: User profile with financial information
            
        Returns:
            Aggressive scenario
        """
        # Determine aggressive parameters
        aggressive_params = self.determine_aggressive_parameters(profile)
        
        # Prepare adjustments
        adjustments = {
            "goal_adjustments": {},
            "profile_adjustments": {
                "risk_tolerance": "high",
                "monthly_savings": profile.get("monthly_savings", 0) * (1 + aggressive_params["contribution_increase"])
            },
            "allocation_adjustments": {}
        }
        
        # Apply increased equity allocations to each goal
        for goal in goals:
            goal_id = goal.get("id")
            current_allocation = goal.get("asset_allocation", {})
            
            # Adjust asset allocation to be more aggressive
            new_allocation = self._generate_aggressive_allocation(current_allocation)
            adjustments["allocation_adjustments"][goal_id] = new_allocation
        
        # Create aggressive scenario
        scenario = self.scenario_comparison.create_scenario(
            name="Aggressive",
            goals=goals,
            profile=profile,
            adjustments=adjustments,
            description="Aggressive scenario with increased contributions and higher risk tolerance."
        )
        
        # Add scenario documentation
        scenario.metadata["documentation"] = {
            "description": self.generate_scenario_description(scenario),
            "adjustments": self.document_scenario_adjustments(scenario),
            "rationale": self.explain_scenario_rationale(scenario),
            "assumptions": self.document_scenario_assumptions(scenario)
        }
        
        return scenario
    
    def generate_conservative_scenario(self, goals: List[Dict[str, Any]], 
                                     profile: Dict[str, Any]) -> Scenario:
        """
        Generate a conservative scenario with reduced targets and extended timeframes.
        
        Args:
            goals: List of financial goals
            profile: User profile with financial information
            
        Returns:
            Conservative scenario
        """
        # Determine conservative parameters
        conservative_params = self.determine_conservative_parameters(profile)
        
        # Prepare adjustments
        adjustments = {
            "goal_adjustments": {},
            "profile_adjustments": {
                "risk_tolerance": "low"
            },
            "timeline_adjustments": {
                "general_extension_months": conservative_params["timeline_extension"]
            },
            "allocation_adjustments": {}
        }
        
        # Apply target reductions and conservative allocations to each goal
        for goal in goals:
            goal_id = goal.get("id")
            target_amount = goal.get("target_amount", 0)
            
            # Reduce target amount by the specified percentage
            new_target = target_amount * (1 - conservative_params["target_reduction"])
            adjustments["goal_adjustments"][goal_id] = {"target_amount": new_target}
            
            # Adjust asset allocation to be more conservative
            current_allocation = goal.get("asset_allocation", {})
            new_allocation = self._generate_conservative_allocation(current_allocation)
            adjustments["allocation_adjustments"][goal_id] = new_allocation
        
        # Create conservative scenario
        scenario = self.scenario_comparison.create_scenario(
            name="Conservative",
            goals=goals,
            profile=profile,
            adjustments=adjustments,
            description="Conservative scenario with reduced targets, extended timeframes, and lower risk."
        )
        
        # Add scenario documentation
        scenario.metadata["documentation"] = {
            "description": self.generate_scenario_description(scenario),
            "adjustments": self.document_scenario_adjustments(scenario),
            "rationale": self.explain_scenario_rationale(scenario),
            "assumptions": self.document_scenario_assumptions(scenario)
        }
        
        return scenario
    
    def generate_prioritized_scenario(self, goals: List[Dict[str, Any]], 
                                    profile: Dict[str, Any],
                                    priorities: Optional[Dict[str, str]] = None) -> Scenario:
        """
        Generate a prioritized scenario focusing on high-priority goals.
        
        Args:
            goals: List of financial goals
            profile: User profile with financial information
            priorities: Optional dictionary mapping goal IDs to priority levels
                       (e.g., {"goal-id-1": "high", "goal-id-2": "medium"})
            
        Returns:
            Prioritized scenario
        """
        # Make a copy of goals
        prioritized_goals = copy.deepcopy(goals)
        
        # If priorities not provided, use existing importance or default all to medium
        if not priorities:
            priorities = {goal.get("id"): goal.get("importance", "medium") for goal in goals}
        
        # Update goals with priorities
        for goal in prioritized_goals:
            goal_id = goal.get("id")
            if goal_id in priorities:
                goal["importance"] = priorities[goal_id]
        
        # Categorize goals by priority
        high_priority_goals = [goal for goal in prioritized_goals if goal.get("importance") == "high"]
        medium_priority_goals = [goal for goal in prioritized_goals if goal.get("importance") == "medium"]
        low_priority_goals = [goal for goal in prioritized_goals if goal.get("importance") == "low"]
        
        # Prepare adjustments
        adjustments = {
            "goal_adjustments": {},
            "timeline_adjustments": {
                "goal_extensions": {}
            }
        }
        
        # Extend timeframes for medium and low priority goals
        for goal in medium_priority_goals:
            goal_id = goal.get("id")
            adjustments["timeline_adjustments"]["goal_extensions"][goal_id] = 12  # Extend by 12 months
        
        for goal in low_priority_goals:
            goal_id = goal.get("id")
            adjustments["timeline_adjustments"]["goal_extensions"][goal_id] = 24  # Extend by 24 months
            
            # Reduce target amount for low priority goals
            target_amount = goal.get("target_amount", 0)
            new_target = target_amount * 0.9  # Reduce by 10%
            adjustments["goal_adjustments"][goal_id] = {"target_amount": new_target}
        
        # Create prioritized scenario
        scenario = self.scenario_comparison.create_scenario(
            name="Prioritized",
            goals=prioritized_goals,
            profile=profile,
            adjustments=adjustments,
            description="Prioritized scenario focusing on high-priority goals with adjustments to other goals."
        )
        
        # Add scenario documentation
        scenario.metadata["documentation"] = {
            "description": self.generate_scenario_description(scenario),
            "adjustments": self.document_scenario_adjustments(scenario),
            "rationale": self.explain_scenario_rationale(scenario),
            "assumptions": self.document_scenario_assumptions(scenario)
        }
        
        return scenario
    
    def generate_balanced_scenario(self, goals: List[Dict[str, Any]], 
                                 profile: Dict[str, Any]) -> Scenario:
        """
        Generate a balanced scenario that optimizes across multiple factors.
        
        Args:
            goals: List of financial goals
            profile: User profile with financial information
            
        Returns:
            Balanced scenario
        """
        # Determine balanced parameters
        balanced_params = self.determine_balanced_parameters(profile)
        
        # Prepare adjustments
        adjustments = {
            "goal_adjustments": {},
            "profile_adjustments": {
                "risk_tolerance": "moderate",
                "monthly_savings": profile.get("monthly_savings", 0) * (1 + balanced_params["contribution_increase"])
            },
            "timeline_adjustments": {
                "general_extension_months": balanced_params["timeline_extension"]
            },
            "allocation_adjustments": {}
        }
        
        # Identify high-priority vs. other goals
        high_priority_goals = [goal for goal in goals if goal.get("importance") == "high"]
        other_goals = [goal for goal in goals if goal.get("importance") != "high"]
        
        # Apply different adjustments based on goal priority
        for goal in goals:
            goal_id = goal.get("id")
            importance = goal.get("importance", "medium")
            
            if importance == "high":
                # No target reduction for high priority goals
                # Slightly more aggressive allocation for high priority goals
                current_allocation = goal.get("asset_allocation", {})
                new_allocation = self._generate_moderately_aggressive_allocation(current_allocation)
                adjustments["allocation_adjustments"][goal_id] = new_allocation
            else:
                # Slight target reduction for medium/low priority goals
                target_amount = goal.get("target_amount", 0)
                reduction_factor = 0.05 if importance == "medium" else 0.1  # 5% or 10% reduction
                new_target = target_amount * (1 - reduction_factor)
                adjustments["goal_adjustments"][goal_id] = {"target_amount": new_target}
                
                # Balanced allocation for medium/low priority goals
                current_allocation = goal.get("asset_allocation", {})
                new_allocation = self._generate_balanced_allocation(current_allocation)
                adjustments["allocation_adjustments"][goal_id] = new_allocation
        
        # Create balanced scenario
        scenario = self.scenario_comparison.create_scenario(
            name="Balanced",
            goals=goals,
            profile=profile,
            adjustments=adjustments,
            description="Balanced scenario with moderate adjustments across contributions, timeframes, and allocations."
        )
        
        # Add scenario documentation
        scenario.metadata["documentation"] = {
            "description": self.generate_scenario_description(scenario),
            "adjustments": self.document_scenario_adjustments(scenario),
            "rationale": self.explain_scenario_rationale(scenario),
            "assumptions": self.document_scenario_assumptions(scenario)
        }
        
        return scenario
    
    def determine_conservative_parameters(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine parameters for a conservative financial approach.
        
        Args:
            profile: User profile with financial information
            
        Returns:
            Dictionary with conservative parameters
        """
        # Base parameters
        params = {
            "timeline_extension": self.params["conservative_timeline_extension"],
            "target_reduction": self.params["conservative_target_reduction"],
            "equity_allocation": 0.3,  # 30% equity allocation
            "debt_allocation": 0.5,    # 50% debt allocation
            "cash_allocation": 0.2     # 20% cash allocation
        }
        
        # Adjust based on age
        age = profile.get("age", 35)
        if age > 50:
            # More conservative for older individuals
            params["equity_allocation"] -= 0.05
            params["debt_allocation"] += 0.05
        elif age < 30:
            # Less conservative for younger individuals
            params["equity_allocation"] += 0.05
            params["debt_allocation"] -= 0.05
        
        # Adjust based on stated risk tolerance
        risk_tolerance = profile.get("risk_tolerance", "moderate")
        if risk_tolerance == "low":
            # Even more conservative
            params["equity_allocation"] -= 0.05
            params["cash_allocation"] += 0.05
        elif risk_tolerance == "high":
            # Less conservative
            params["equity_allocation"] += 0.05
            params["cash_allocation"] -= 0.05
        
        # Apply Indian context adjustments if applicable
        if profile.get("country", "").lower() == "india":
            params = self.adjust_parameters_for_indian_context(params)
        
        return params
    
    def determine_aggressive_parameters(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine parameters for an aggressive financial approach.
        
        Args:
            profile: User profile with financial information
            
        Returns:
            Dictionary with aggressive parameters
        """
        # Base parameters
        params = {
            "contribution_increase": self.params["aggressive_contribution_increase"],
            "equity_allocation": 0.7,   # 70% equity allocation
            "debt_allocation": 0.25,    # 25% debt allocation
            "cash_allocation": 0.05     # 5% cash allocation
        }
        
        # Adjust based on age
        age = profile.get("age", 35)
        if age > 50:
            # Less aggressive for older individuals
            params["equity_allocation"] -= 0.1
            params["debt_allocation"] += 0.1
        elif age < 30:
            # More aggressive for younger individuals
            params["equity_allocation"] += 0.1
            params["debt_allocation"] -= 0.1
            params["contribution_increase"] += 0.05
        
        # Adjust based on stated risk tolerance
        risk_tolerance = profile.get("risk_tolerance", "moderate")
        if risk_tolerance == "low":
            # Less aggressive
            params["equity_allocation"] -= 0.1
            params["debt_allocation"] += 0.05
            params["cash_allocation"] += 0.05
        elif risk_tolerance == "high":
            # More aggressive
            params["equity_allocation"] += 0.1
            params["debt_allocation"] -= 0.05
            params["cash_allocation"] -= 0.05
            params["contribution_increase"] += 0.05
        
        # Adjust based on income stability
        income_stability = profile.get("income_stability", "stable")
        if income_stability == "unstable":
            # Less aggressive with unstable income
            params["equity_allocation"] -= 0.05
            params["cash_allocation"] += 0.05
            params["contribution_increase"] -= 0.05
        
        # Apply Indian context adjustments if applicable
        if profile.get("country", "").lower() == "india":
            params = self.adjust_parameters_for_indian_context(params)
        
        return params
    
    def determine_balanced_parameters(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine parameters for a balanced financial approach.
        
        Args:
            profile: User profile with financial information
            
        Returns:
            Dictionary with balanced parameters
        """
        # Base parameters
        params = {
            "timeline_extension": self.params["balanced_timeline_extension"],
            "contribution_increase": self.params["balanced_contribution_increase"],
            "target_reduction": self.params["conservative_target_reduction"] / 2,  # Half of conservative reduction
            "equity_allocation": 0.5,   # 50% equity allocation
            "debt_allocation": 0.35,    # 35% debt allocation
            "cash_allocation": 0.1,     # 10% cash allocation
            "gold_allocation": 0.05     # 5% gold allocation
        }
        
        # Adjust based on age
        age = profile.get("age", 35)
        if age > 50:
            # More conservative allocation for older individuals
            params["equity_allocation"] -= 0.1
            params["debt_allocation"] += 0.1
        elif age < 30:
            # More aggressive allocation for younger individuals
            params["equity_allocation"] += 0.1
            params["debt_allocation"] -= 0.1
        
        # Adjust based on stated risk tolerance
        risk_tolerance = profile.get("risk_tolerance", "moderate")
        if risk_tolerance == "low":
            # More conservative
            params["equity_allocation"] -= 0.1
            params["debt_allocation"] += 0.05
            params["cash_allocation"] += 0.05
        elif risk_tolerance == "high":
            # More aggressive
            params["equity_allocation"] += 0.1
            params["debt_allocation"] -= 0.05
            params["cash_allocation"] -= 0.05
        
        # Apply Indian context adjustments if applicable
        if profile.get("country", "").lower() == "india":
            params = self.adjust_parameters_for_indian_context(params)
        
        return params
    
    def adjust_parameters_for_indian_context(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust financial parameters for Indian financial environment.
        
        Args:
            parameters: Original parameters
            
        Returns:
            Adjusted parameters for Indian context
        """
        # Make a copy of parameters to avoid modifying the original
        adjusted_params = copy.deepcopy(parameters)
        
        # Adjust for higher inflation in India
        if "timeline_extension" in adjusted_params:
            # Shorter timeline extensions due to higher inflation
            adjusted_params["timeline_extension"] = max(6, int(adjusted_params["timeline_extension"] * 0.8))
        
        # Adjust asset allocation to include gold (traditional safe haven in India)
        if "gold_allocation" not in adjusted_params:
            # Reduce other allocations proportionally to add gold
            gold_allocation = 0.05  # Start with 5% gold allocation
            reduction_factor = 1 - gold_allocation
            
            adjusted_params["gold_allocation"] = gold_allocation
            for key in ["equity_allocation", "debt_allocation", "cash_allocation"]:
                if key in adjusted_params:
                    adjusted_params[key] *= reduction_factor
        else:
            # Increase existing gold allocation slightly
            adjusted_params["gold_allocation"] += 0.02
            
            # Reduce other allocations proportionally
            reduction_factor = 1 - 0.02
            for key in ["equity_allocation", "debt_allocation", "cash_allocation"]:
                if key in adjusted_params:
                    adjusted_params[key] *= reduction_factor
        
        # Consider family financial dynamics in Indian context
        if "family_support_factor" in self.params:
            # Add parameter to represent family financial support
            adjusted_params["family_support_factor"] = self.params["family_support_factor"]
        
        # Consider tax-advantaged investments more heavily in Indian context
        adjusted_params["tax_advantaged_allocation"] = 0.2  # Allocation to tax-advantaged investments
        
        return adjusted_params
    
    def generate_scenario_description(self, scenario: Scenario) -> str:
        """
        Generate a human-readable description of a scenario.
        
        Args:
            scenario: The scenario to describe
            
        Returns:
            Human-readable description
        """
        scenario_name = scenario.name
        adjustments = scenario.metadata.get("adjustments_applied", {})
        
        # Start with a base description based on scenario name
        if scenario_name == "Baseline":
            description = "This scenario represents your current financial trajectory without any adjustments. "
            description += "It serves as a reference point to compare other scenarios against."
        elif scenario_name == "Conservative":
            description = "This conservative approach prioritizes security and reliability over growth. "
            description += "It includes reduced target amounts, extended timeframes, and lower-risk investments."
        elif scenario_name == "Aggressive":
            description = "This aggressive approach aims to maximize growth through increased contributions and higher-risk investments. "
            description += "It may require more discipline but offers potential for greater returns."
        elif scenario_name == "Balanced":
            description = "This balanced approach seeks a middle ground between growth and security. "
            description += "It includes moderate adjustments to contributions, timeframes, and investment allocations."
        elif scenario_name == "Prioritized":
            description = "This approach focuses resources on your highest-priority goals while making adjustments to lower-priority goals. "
            description += "It helps ensure your most important goals are achieved even if others are delayed."
        else:
            description = f"The {scenario_name} scenario provides an alternative financial approach. "
        
        # Add details about specific adjustments
        if "timeline" in adjustments:
            timeline_adj = adjustments.get("timeline", {})
            if "general_extension_months" in timeline_adj:
                months = timeline_adj["general_extension_months"]
                description += f"Timeframes for goals are extended by {months} months. "
        
        if "goals" in adjustments:
            num_goals = len(adjustments.get("goals", []))
            description += f"Adjustments are made to {num_goals} goals. "
        
        if "allocation" in adjustments:
            description += "Investment allocations are modified to align with the scenario's risk profile. "
        
        if "profile" in adjustments:
            if "risk_tolerance" in scenario.profile:
                risk = scenario.profile["risk_tolerance"]
                description += f"This scenario assumes a {risk} risk tolerance. "
            
            if "monthly_savings" in scenario.profile:
                description += "Monthly savings amounts are adjusted. "
        
        return description
    
    def document_scenario_adjustments(self, scenario: Scenario) -> Dict[str, Any]:
        """
        Document all modifications made in a scenario.
        
        Args:
            scenario: The scenario to document
            
        Returns:
            Dictionary with detailed adjustment documentation
        """
        adjustments = scenario.metadata.get("adjustments_applied", {})
        documentation = {}
        
        # Document timeline adjustments
        if "timeline" in adjustments:
            timeline_doc = {}
            timeline_adj = adjustments.get("timeline", {})
            
            if "general_extension_months" in timeline_adj:
                months = timeline_adj["general_extension_months"]
                timeline_doc["general_extension"] = f"{months} months added to all goal timelines"
            
            if "goal_extensions" in timeline_adj:
                goal_ext = {}
                for goal_id, months in timeline_adj["goal_extensions"].items():
                    # Find goal name for better documentation
                    goal_name = next((g.get("title", "Unknown Goal") for g in scenario.goals if g.get("id") == goal_id), "Unknown Goal")
                    goal_ext[goal_name] = f"{months} months extension"
                
                timeline_doc["specific_goal_extensions"] = goal_ext
            
            documentation["timeline_adjustments"] = timeline_doc
        
        # Document goal adjustments
        if "goals" in adjustments:
            goal_doc = {}
            goal_adj = {}
            
            # Get goal adjustments from metadata
            if isinstance(adjustments.get("goals"), list):
                # If it's a list of goal IDs
                goal_ids = adjustments.get("goals", [])
                # Find corresponding adjustments (we have to infer these)
                for goal_id in goal_ids:
                    original_goal = next((g for g in scenario.goals if g.get("id") == goal_id), None)
                    modified_goal = next((g for g in scenario.goals if g.get("id") == goal_id), None)
                    
                    if original_goal and modified_goal:
                        # Compare to find differences
                        changes = {}
                        for key in modified_goal:
                            if key in original_goal and modified_goal[key] != original_goal[key]:
                                changes[key] = f"Changed from {original_goal[key]} to {modified_goal[key]}"
                        
                        if changes:
                            goal_name = original_goal.get("title", "Unknown Goal")
                            goal_adj[goal_name] = changes
            
            documentation["goal_adjustments"] = goal_adj
        
        # Document allocation adjustments
        if "allocation" in adjustments:
            alloc_doc = {}
            alloc_adj = adjustments.get("allocation", {})
            
            for goal_id, allocation in alloc_adj.items():
                # Find goal name for better documentation
                goal_name = next((g.get("title", "Unknown Goal") for g in scenario.goals if g.get("id") == goal_id), "Unknown Goal")
                alloc_doc[goal_name] = allocation
            
            documentation["allocation_adjustments"] = alloc_doc
        
        # Document profile adjustments
        if "profile" in adjustments:
            profile_doc = {}
            profile_adj = adjustments.get("profile", [])
            
            for key in profile_adj:
                profile_doc[key] = f"Adjusted to {scenario.profile.get(key, 'unknown')}"
            
            documentation["profile_adjustments"] = profile_doc
        
        return documentation
    
    def explain_scenario_rationale(self, scenario: Scenario) -> str:
        """
        Generate an explanation of the reasoning behind a scenario's strategy.
        
        Args:
            scenario: The scenario to explain
            
        Returns:
            Explanation of strategy reasoning
        """
        scenario_name = scenario.name
        
        # Base rationale based on scenario name
        if scenario_name == "Baseline":
            rationale = "The baseline scenario provides a reference point that shows what would happen if you continue with your current financial trajectory. "
            rationale += "This scenario is useful for understanding the gaps between your current approach and your financial goals."
        elif scenario_name == "Conservative":
            rationale = "The conservative scenario is designed for individuals who prioritize certainty and stability over maximizing returns. "
            rationale += "By extending timeframes and reducing target amounts, this approach reduces the stress on your finances while "
            rationale += "maintaining a more conservative investment allocation to minimize volatility. "
            rationale += "This approach is often suitable for those closer to retirement, with lower risk tolerance, or in unstable financial situations."
        elif scenario_name == "Aggressive":
            rationale = "The aggressive scenario is designed for individuals who are willing to accept higher risk and make larger financial commitments to achieve their goals faster. "
            rationale += "By increasing contributions and adopting a growth-oriented investment strategy, this approach aims to accelerate progress toward financial goals. "
            rationale += "This strategy typically works best for younger individuals with stable incomes, higher risk tolerance, and longer time horizons."
        elif scenario_name == "Balanced":
            rationale = "The balanced scenario seeks to find a middle ground that balances risk and return, effort and outcome. "
            rationale += "It makes moderate adjustments across multiple factors rather than extreme changes in any single area. "
            rationale += "This approach is suitable for most individuals as it provides a reasonable balance between financial security and growth potential."
        elif scenario_name == "Prioritized":
            rationale = "The prioritized scenario focuses resources on your most important goals while making compromises on lower-priority objectives. "
            rationale += "This approach acknowledges that not all goals are equally important and ensures that limited resources are allocated efficiently. "
            rationale += "It's particularly useful when facing resource constraints that make achieving all goals simultaneously challenging."
        else:
            rationale = f"The {scenario_name} scenario presents an alternative financial strategy tailored to specific circumstances and preferences."
        
        # Add context about Indian financial environment if applicable
        if any(g.get("country", "").lower() == "india" for g in scenario.goals) or scenario.profile.get("country", "").lower() == "india":
            rationale += "\n\nThis scenario takes into account aspects of the Indian financial environment, including higher inflation rates, "
            rationale += "the cultural significance of gold as an asset class, and family financial interdependence."
        
        return rationale
    
    def document_scenario_assumptions(self, scenario: Scenario) -> List[str]:
        """
        List the underlying assumptions of a scenario.
        
        Args:
            scenario: The scenario to document
            
        Returns:
            List of assumptions
        """
        scenario_name = scenario.name
        assumptions = []
        
        # Common assumptions for all scenarios
        assumptions.append("Inflation remains relatively stable")
        assumptions.append("No major financial emergencies occur")
        assumptions.append("Employment and income generally follow expected patterns")
        
        # Scenario-specific assumptions
        if scenario_name == "Baseline":
            assumptions.append("Current saving and spending patterns continue")
            assumptions.append("Current asset allocations are maintained")
            assumptions.append("No significant adjustments to financial goals")
        elif scenario_name == "Conservative":
            assumptions.append("Lower-risk investments will provide more stable, albeit lower, returns")
            assumptions.append("Extended timeframes are acceptable for goal achievement")
            assumptions.append("Reduced target amounts still meet essential needs")
            assumptions.append("Security and stability are valued over maximizing returns")
        elif scenario_name == "Aggressive":
            assumptions.append("Higher monthly savings rate is sustainable long-term")
            assumptions.append("Higher-risk investments will provide better returns over time despite volatility")
            assumptions.append("Income stability allows for continued higher contributions")
            assumptions.append("Market conditions support the higher expected returns")
        elif scenario_name == "Balanced":
            assumptions.append("Moderate adjustments across multiple factors provide a suitable compromise")
            assumptions.append("Achieving balance between risk and reward is prioritized")
            assumptions.append("Some flexibility exists in both timeframes and target amounts")
            assumptions.append("Investment returns are in line with historical moderate-risk portfolios")
        elif scenario_name == "Prioritized":
            assumptions.append("High-priority goals can be achieved without significant compromise")
            assumptions.append("Lower-priority goals can be delayed or modified")
            assumptions.append("Priorities remain relatively stable over time")
            assumptions.append("Resource allocation follows priority ranking")
        
        # Add Indian context-specific assumptions if applicable
        if any(g.get("country", "").lower() == "india" for g in scenario.goals) or scenario.profile.get("country", "").lower() == "india":
            assumptions.append("Inflation in India may be higher than global averages")
            assumptions.append("Gold continues to play a culturally important role in asset allocation")
            assumptions.append("Family financial support structures remain relatively stable")
            assumptions.append("Tax-advantaged investments like PPF, ELSS, and NPS continue to offer benefits")
        
        return assumptions
    
    # Private helper methods
    
    def _generate_conservative_allocation(self, current_allocation: Dict[str, float]) -> Dict[str, float]:
        """Generate a conservative asset allocation"""
        # Default conservative allocation
        conservative = {
            "equity": 0.3,
            "debt": 0.5,
            "gold": 0.05,
            "cash": 0.15
        }
        
        # If current allocation exists, adjust gradually
        if current_allocation:
            conservative = {}
            for asset, target in {"equity": 0.3, "debt": 0.5, "gold": 0.05, "cash": 0.15}.items():
                current = current_allocation.get(asset, target)
                # Move 70% of the way toward the target
                conservative[asset] = current + 0.7 * (target - current)
        
        # Normalize to ensure it sums to 1.0
        total = sum(conservative.values())
        return {k: v / total for k, v in conservative.items()}
    
    def _generate_aggressive_allocation(self, current_allocation: Dict[str, float]) -> Dict[str, float]:
        """Generate an aggressive asset allocation"""
        # Default aggressive allocation
        aggressive = {
            "equity": 0.7,
            "debt": 0.25,
            "gold": 0.0,
            "cash": 0.05
        }
        
        # If current allocation exists, adjust gradually
        if current_allocation:
            aggressive = {}
            for asset, target in {"equity": 0.7, "debt": 0.25, "gold": 0.0, "cash": 0.05}.items():
                current = current_allocation.get(asset, target)
                # Move 70% of the way toward the target
                aggressive[asset] = current + 0.7 * (target - current)
        
        # Normalize to ensure it sums to 1.0
        total = sum(aggressive.values())
        return {k: v / total for k, v in aggressive.items()}
    
    def _generate_balanced_allocation(self, current_allocation: Dict[str, float]) -> Dict[str, float]:
        """Generate a balanced asset allocation"""
        # Default balanced allocation
        balanced = {
            "equity": 0.5,
            "debt": 0.35,
            "gold": 0.05,
            "cash": 0.1
        }
        
        # If current allocation exists, adjust gradually
        if current_allocation:
            balanced = {}
            for asset, target in {"equity": 0.5, "debt": 0.35, "gold": 0.05, "cash": 0.1}.items():
                current = current_allocation.get(asset, target)
                # Move 70% of the way toward the target
                balanced[asset] = current + 0.7 * (target - current)
        
        # Normalize to ensure it sums to 1.0
        total = sum(balanced.values())
        return {k: v / total for k, v in balanced.items()}
    
    def _generate_moderately_aggressive_allocation(self, current_allocation: Dict[str, float]) -> Dict[str, float]:
        """Generate a moderately aggressive asset allocation"""
        # Default moderately aggressive allocation
        mod_aggressive = {
            "equity": 0.6,
            "debt": 0.3,
            "gold": 0.05,
            "cash": 0.05
        }
        
        # If current allocation exists, adjust gradually
        if current_allocation:
            mod_aggressive = {}
            for asset, target in {"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05}.items():
                current = current_allocation.get(asset, target)
                # Move 70% of the way toward the target
                mod_aggressive[asset] = current + 0.7 * (target - current)
        
        # Normalize to ensure it sums to 1.0
        total = sum(mod_aggressive.values())
        return {k: v / total for k, v in mod_aggressive.items()}
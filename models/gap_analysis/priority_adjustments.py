"""
Priority Adjustment Module

This module provides specialized strategies for reprioritizing financial goals
to address resource conflicts. It calculates optimal prioritization schemes and
evaluates their impact on overall financial health.
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple

from models.gap_analysis.core import (
    GapResult, 
    GapSeverity,
    RemediationOption,
    get_financial_parameter_service
)
from models.gap_analysis.remediation_strategies import GapRemediationStrategy

logger = logging.getLogger(__name__)

class PriorityAdjustment(GapRemediationStrategy):
    """
    Class for reprioritizing financial goals based on analysis results.
    
    This class provides tools to reprioritize financial goals based on analysis results,
    resource availability, and other factors. It helps optimize resource allocation
    across competing financial goals.
    """
    
    def __init__(self):
        """
        Initialize the priority adjustment strategy.
        """
        super().__init__()
        
        # Additional parameters specific to priority adjustments
        self.priority_params = {
            "critical_goal_weight": 1.5,  # Weight for critical goals
            "significant_goal_weight": 1.2,  # Weight for significant goals
            "moderate_goal_weight": 1.0,  # Weight for moderate goals
            "minor_goal_weight": 0.8,  # Weight for minor goals
            "resource_conflict_threshold": 0.8,  # Threshold for resource conflicts
            "max_high_priority_goals": 3,  # Maximum number of high priority goals
        }
        
        # Override defaults with values from parameter service if available
        if self.param_service:
            try:
                # Try to use get_parameters_by_prefix if available
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    param_values = self.param_service.get_parameters_by_prefix("priority_adjustment.")
                    if param_values:
                        self.priority_params.update(param_values)
                # Fall back to getting individual parameters
                else:
                    for key in self.priority_params.keys():
                        if not isinstance(self.priority_params[key], dict):  # Skip nested dict
                            param_path = f"priority_adjustment.{key}"
                            value = self.param_service.get(param_path)
                            if value is not None:
                                self.priority_params[key] = value
            except Exception as e:
                logger.warning(f"Error getting parameters: {e}")
                # Continue with defaults
    
    def analyze_priority_impact(self, current_priorities: List[str], new_priorities: List[str], 
                               profile: dict) -> Dict[str, Any]:
        """
        Analyze the impact of changing goal priorities.
        
        Args:
            current_priorities: Current goal priority order
            new_priorities: New goal priority order
            profile: The user profile with financial information
            
        Returns:
            Dictionary with priority impact analysis
        """
        # Get goals from profile
        goals = self._extract_goals(profile)
        goal_dict = {goal["id"]: goal for goal in goals}
        
        # Validate that priorities contain valid goal IDs
        valid_current = [p for p in current_priorities if p in goal_dict]
        valid_new = [p for p in new_priorities if p in goal_dict]
        
        # Extract changes
        promoted = [p for p in valid_new if p in valid_current and valid_new.index(p) < valid_current.index(p)]
        demoted = [p for p in valid_current if p in valid_new and valid_new.index(p) > valid_current.index(p)]
        unchanged = [p for p in valid_current if p in valid_new and valid_new.index(p) == valid_current.index(p)]
        
        # Calculate resource reallocation
        resource_impact = self._calculate_resource_reallocation(valid_current, valid_new, profile)
        
        # Analyze specific impacts on goals
        goal_impacts = {}
        for goal_id in set(valid_current + valid_new):
            if goal_id in goal_dict:
                goal = goal_dict[goal_id]
                
                old_priority = valid_current.index(goal_id) if goal_id in valid_current else len(valid_current)
                new_priority = valid_new.index(goal_id) if goal_id in valid_new else len(valid_new)
                
                # Determine change type
                if goal_id in promoted:
                    change_type = "promoted"
                elif goal_id in demoted:
                    change_type = "demoted"
                else:
                    change_type = "unchanged"
                
                # Calculate funding impact
                funding_change = resource_impact.get("reallocations", {}).get(goal_id, 0)
                funding_change_pct = (funding_change / float(goal.get("target_amount", 1))) * 100
                
                # Estimate timeline impact
                timeline_impact = self._estimate_timeline_impact(goal, funding_change)
                
                goal_impacts[goal_id] = {
                    "title": goal.get("title", "Unnamed Goal"),
                    "old_priority": old_priority + 1,  # 1-indexed for user-friendly display
                    "new_priority": new_priority + 1,  # 1-indexed for user-friendly display
                    "change_type": change_type,
                    "funding_change": funding_change,
                    "funding_change_percentage": funding_change_pct,
                    "timeline_impact": timeline_impact
                }
        
        # Calculate overall impact on financial health
        overall_impact = self._calculate_overall_impact(valid_current, valid_new, goal_dict)
        
        return {
            "goal_impacts": goal_impacts,
            "resource_impact": resource_impact,
            "overall_impact": overall_impact,
            "changes": {
                "promoted": [goal_dict[p]["title"] for p in promoted if p in goal_dict],
                "demoted": [goal_dict[p]["title"] for p in demoted if p in goal_dict],
                "unchanged": [goal_dict[p]["title"] for p in unchanged if p in goal_dict]
            }
        }
    
    def calculate_optimal_priorities(self, gap_results: List[GapResult], goals: List[Dict[str, Any]], 
                                   profile: dict) -> List[str]:
        """
        Calculate the optimal priority order for goals based on gap analysis.
        
        Args:
            gap_results: List of gap analysis results
            goals: List of financial goals
            profile: User profile with financial information
            
        Returns:
            List of goal IDs in optimal priority order
        """
        # Calculate priority scores for each goal
        scores = {}
        goal_dict = {goal["id"]: goal for goal in goals}
        
        for result in gap_results:
            goal_id = result.goal_id
            
            # Skip goals not in the goal dictionary
            if goal_id not in goal_dict:
                continue
                
            goal = goal_dict[goal_id]
            
            # Base score from gap severity
            severity_weights = {
                GapSeverity.CRITICAL: self.priority_params["critical_goal_weight"],
                GapSeverity.SIGNIFICANT: self.priority_params["significant_goal_weight"],
                GapSeverity.MODERATE: self.priority_params["moderate_goal_weight"],
                GapSeverity.MINOR: self.priority_params["minor_goal_weight"]
            }
            
            base_score = severity_weights.get(result.severity, 1.0) * 100
            
            # Adjust by goal importance
            importance_factor = {
                "high": 1.5,
                "medium": 1.0,
                "low": 0.7
            }.get(goal.get("importance", "medium"), 1.0)
            
            # Adjust by time pressure
            months_to_goal = self._calculate_months_to_goal(goal)
            time_factor = 1.0
            if months_to_goal < 12:
                time_factor = 1.5  # Short-term goals get higher priority
            elif months_to_goal > 60:
                time_factor = 0.7  # Long-term goals get lower priority
            
            # Calculate final score
            final_score = base_score * importance_factor * time_factor
            scores[goal_id] = final_score
        
        # Sort goals by score (descending)
        sorted_goals = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        optimal_order = [goal_id for goal_id, score in sorted_goals]
        
        return optimal_order
    
    def generate_priority_options(self, gap_results: List[GapResult], goals: List[Dict[str, Any]], 
                                 profile: dict) -> List[Dict[str, Any]]:
        """
        Generate multiple priority ordering options with varying impacts.
        
        Args:
            gap_results: List of gap analysis results
            goals: List of financial goals
            profile: User profile with financial information
            
        Returns:
            List of priority ordering options with impact analysis
        """
        options = []
        
        # Get current priorities
        current_priorities = self._extract_current_priorities(goals)
        
        # Calculate optimal priorities
        optimal_priorities = self.calculate_optimal_priorities(gap_results, goals, profile)
        
        # Generate options
        # 1. Optimal prioritization
        optimal_option = {
            "name": "Optimal Prioritization",
            "description": "Recommended priority order based on gap analysis",
            "priorities": optimal_priorities,
            "goal_names": self._get_goal_names(optimal_priorities, goals),
            "impact": self.analyze_priority_impact(current_priorities, optimal_priorities, profile)
        }
        options.append(optimal_option)
        
        # 2. Emergency First prioritization
        emergency_priorities = self._prioritize_emergency_first(optimal_priorities, goals)
        if emergency_priorities != optimal_priorities:
            emergency_option = {
                "name": "Emergency First",
                "description": "Prioritize emergency fund and critical short-term needs",
                "priorities": emergency_priorities,
                "goal_names": self._get_goal_names(emergency_priorities, goals),
                "impact": self.analyze_priority_impact(current_priorities, emergency_priorities, profile)
            }
            options.append(emergency_option)
        
        # 3. Balanced approach
        balanced_priorities = self._create_balanced_priorities(optimal_priorities, current_priorities, goals)
        if balanced_priorities != optimal_priorities and balanced_priorities != current_priorities:
            balanced_option = {
                "name": "Balanced Approach",
                "description": "Balance current priorities with recommended changes",
                "priorities": balanced_priorities,
                "goal_names": self._get_goal_names(balanced_priorities, goals),
                "impact": self.analyze_priority_impact(current_priorities, balanced_priorities, profile)
            }
            options.append(balanced_option)
        
        return options
    
    def create_priority_option(self, new_priorities: List[str], goals: List[Dict[str, Any]], 
                              profile: dict) -> RemediationOption:
        """
        Create a remediation option for priority adjustment.
        
        Args:
            new_priorities: New goal priority order
            goals: List of financial goals
            profile: User profile with financial information
            
        Returns:
            Remediation option for priority adjustment
        """
        # Get current priorities
        current_priorities = self._extract_current_priorities(goals)
        
        # Get goal names
        goal_dict = {goal["id"]: goal for goal in goals}
        
        # Analyze impact
        impact = self.analyze_priority_impact(current_priorities, new_priorities, profile)
        
        # Create description
        promoted = impact["changes"]["promoted"]
        demoted = impact["changes"]["demoted"]
        
        description_parts = []
        if promoted:
            description_parts.append(f"prioritize {', '.join(promoted[:2])}")
            if len(promoted) > 2:
                description_parts[-1] += ", and others"
        if demoted:
            description_parts.append(f"deprioritize {', '.join(demoted[:2])}")
            if len(demoted) > 2:
                description_parts[-1] += ", and others"
        
        description = "Adjust goal priorities: " + ", ".join(description_parts)
        
        # Create impact metrics
        impact_metrics = {
            "current_priorities": [goal_dict.get(goal_id, {}).get("title", f"Goal {goal_id}") for goal_id in current_priorities],
            "new_priorities": [goal_dict.get(goal_id, {}).get("title", f"Goal {goal_id}") for goal_id in new_priorities],
            "resource_reallocations": impact["resource_impact"]["reallocations"],
            "overall_improvement": impact["overall_impact"]["improvement_score"]
        }
        
        # Create implementation steps
        implementation_steps = [
            "Review and update your goal priorities in your financial plan",
            "Adjust your monthly contributions according to the new priorities",
            "Monitor progress of high-priority goals more frequently",
            "Revisit prioritization in 6 months or when circumstances change"
        ]
        
        return RemediationOption(
            description=description,
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps
        )
    
    def _extract_goals(self, profile: dict) -> List[Dict[str, Any]]:
        """Extract goals from profile data"""
        # Look for direct goals field
        if "goals" in profile:
            return profile["goals"]
        
        # Empty list if not found
        return []
    
    def _extract_current_priorities(self, goals: List[Dict[str, Any]]) -> List[str]:
        """Extract current priorities from goals"""
        # Sort goals by priority if available
        if all("priority" in goal for goal in goals):
            sorted_goals = sorted(goals, key=lambda g: g.get("priority", 999))
            return [goal["id"] for goal in sorted_goals]
        
        # Otherwise, sort by importance
        importance_map = {"high": 0, "medium": 1, "low": 2}
        sorted_goals = sorted(goals, key=lambda g: importance_map.get(g.get("importance", "medium"), 1))
        return [goal["id"] for goal in sorted_goals]
    
    def _calculate_resource_reallocation(self, current_priorities: List[str], new_priorities: List[str], 
                                        profile: dict) -> Dict[str, Any]:
        """Calculate resource reallocation based on priority changes"""
        # Extract available resources
        monthly_resources = self._extract_monthly_resources(profile)
        
        # Simple model: assume resources allocated based on priority position
        # Higher priority gets more resources
        current_allocations = self._calculate_allocations(current_priorities, monthly_resources)
        new_allocations = self._calculate_allocations(new_priorities, monthly_resources)
        
        # Calculate changes
        reallocations = {}
        for goal_id in set(current_priorities + new_priorities):
            current_amount = current_allocations.get(goal_id, 0)
            new_amount = new_allocations.get(goal_id, 0)
            change = new_amount - current_amount
            if abs(change) > 100:  # Only include significant changes
                reallocations[goal_id] = change
        
        return {
            "monthly_resources": monthly_resources,
            "current_allocations": current_allocations,
            "new_allocations": new_allocations,
            "reallocations": reallocations,
            "total_reallocation": sum(abs(v) for v in reallocations.values()) / 2  # Divide by 2 to avoid double counting
        }
    
    def _calculate_allocations(self, priorities: List[str], total_resources: float) -> Dict[str, float]:
        """Calculate resource allocations based on priority order"""
        if not priorities:
            return {}
            
        # Exponential decay model: higher priorities get exponentially more resources
        decay_factor = 0.8
        weights = [decay_factor ** i for i in range(len(priorities))]
        total_weight = sum(weights)
        
        # Calculate allocations
        allocations = {}
        for i, goal_id in enumerate(priorities):
            allocation = (weights[i] / total_weight) * total_resources
            allocations[goal_id] = allocation
        
        return allocations
    
    def _estimate_timeline_impact(self, goal: Dict[str, Any], funding_change: float) -> Dict[str, Any]:
        """Estimate the impact of funding change on goal timeline"""
        # Extract goal details
        target_amount = float(goal.get("target_amount", 0))
        current_amount = float(goal.get("current_amount", 0))
        gap_amount = max(0, target_amount - current_amount)
        
        # Get current and new monthly contribution
        current_monthly = self._extract_current_monthly(goal)
        new_monthly = current_monthly + funding_change
        
        # Calculate time to goal with current monthly
        current_months = 999 if current_monthly <= 0 else gap_amount / current_monthly
        
        # Calculate time to goal with new monthly
        new_months = 999 if new_monthly <= 0 else gap_amount / new_monthly
        
        # Calculate difference
        difference_months = current_months - new_months
        
        # Determine impact level
        if difference_months > 12:
            impact_level = "significant"
        elif difference_months > 6:
            impact_level = "moderate"
        elif difference_months > 0:
            impact_level = "minor"
        elif difference_months < -12:
            impact_level = "significant_negative"
        elif difference_months < -6:
            impact_level = "moderate_negative"
        elif difference_months < 0:
            impact_level = "minor_negative"
        else:
            impact_level = "neutral"
        
        return {
            "current_months": int(current_months),
            "new_months": int(new_months),
            "difference_months": int(difference_months),
            "impact_level": impact_level
        }
    
    def _calculate_overall_impact(self, current_priorities: List[str], new_priorities: List[str], 
                                goal_dict: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall impact on financial health"""
        # Analyze impact on critical goals
        critical_ids = [goal_id for goal_id, goal in goal_dict.items() 
                      if goal.get("importance", "medium") == "high"]
        
        # Check if high-importance goals are given higher priority
        current_critical_avg = self._calculate_average_position(critical_ids, current_priorities)
        new_critical_avg = self._calculate_average_position(critical_ids, new_priorities)
        critical_improvement = current_critical_avg - new_critical_avg  # Lower is better
        
        # Analyze impact on short-term goals
        short_term_ids = [goal_id for goal_id, goal in goal_dict.items() 
                        if self._calculate_months_to_goal(goal) < 12]
        
        current_short_term_avg = self._calculate_average_position(short_term_ids, current_priorities)
        new_short_term_avg = self._calculate_average_position(short_term_ids, new_priorities)
        short_term_improvement = current_short_term_avg - new_short_term_avg  # Lower is better
        
        # Calculate overall improvement score
        improvement_score = (critical_improvement * 0.6) + (short_term_improvement * 0.4)
        
        # Determine impact level
        if improvement_score > 2:
            impact_level = "significant_positive"
        elif improvement_score > 0.5:
            impact_level = "moderate_positive"
        elif improvement_score > -0.5:
            impact_level = "neutral"
        elif improvement_score > -2:
            impact_level = "moderate_negative"
        else:
            impact_level = "significant_negative"
        
        return {
            "critical_goal_improvement": critical_improvement,
            "short_term_goal_improvement": short_term_improvement,
            "improvement_score": improvement_score,
            "impact_level": impact_level
        }
    
    def _calculate_average_position(self, goal_ids: List[str], priorities: List[str]) -> float:
        """Calculate average position of goals in priority list"""
        positions = []
        for goal_id in goal_ids:
            if goal_id in priorities:
                positions.append(priorities.index(goal_id))
            else:
                positions.append(len(priorities))  # Place at the end if not in list
        
        return sum(positions) / len(positions) if positions else 0
    
    def _prioritize_emergency_first(self, priorities: List[str], goals: List[Dict[str, Any]]) -> List[str]:
        """Create a priority list that puts emergency fund first"""
        goal_dict = {goal["id"]: goal for goal in goals}
        
        # Find emergency fund goals
        emergency_ids = [goal["id"] for goal in goals if goal.get("category") == "emergency_fund"]
        
        # If no emergency fund goals, return original priorities
        if not emergency_ids:
            return priorities.copy()
        
        # Create new priority list with emergency fund first
        new_priorities = emergency_ids.copy()
        for goal_id in priorities:
            if goal_id not in emergency_ids:
                new_priorities.append(goal_id)
        
        return new_priorities
    
    def _create_balanced_priorities(self, optimal_priorities: List[str], current_priorities: List[str], 
                                   goals: List[Dict[str, Any]]) -> List[str]:
        """Create a balanced priority list by blending optimal and current priorities"""
        goal_dict = {goal["id"]: goal for goal in goals}
        
        # Find high importance goals
        high_importance_ids = [goal["id"] for goal in goals if goal.get("importance") == "high"]
        
        # Find emergency and short-term goals
        critical_ids = high_importance_ids + [
            goal["id"] for goal in goals 
            if goal.get("category") == "emergency_fund" or self._calculate_months_to_goal(goal) < 12
        ]
        critical_ids = list(set(critical_ids))  # Remove duplicates
        
        # Calculate a score for each goal based on optimal and current position
        scores = {}
        for goal_id in set(optimal_priorities + current_priorities):
            # Position in optimal priorities (lower is better)
            opt_pos = optimal_priorities.index(goal_id) if goal_id in optimal_priorities else len(optimal_priorities)
            
            # Position in current priorities (lower is better)
            curr_pos = current_priorities.index(goal_id) if goal_id in current_priorities else len(current_priorities)
            
            # Critical goals get a bonus
            critical_bonus = 5 if goal_id in critical_ids else 0
            
            # Calculate score (lower is better)
            scores[goal_id] = (opt_pos * 0.6) + (curr_pos * 0.4) - critical_bonus
        
        # Sort by score
        balanced_priorities = sorted(scores.keys(), key=lambda x: scores[x])
        
        return balanced_priorities
    
    def _extract_monthly_resources(self, profile: dict) -> float:
        """Extract available monthly resources for goal funding"""
        # Extract income and expenses
        monthly_income = self._extract_monthly_income(profile)
        monthly_expenses = self._extract_monthly_expenses(profile)
        
        # Calculate disposable income
        disposable_income = monthly_income - monthly_expenses
        
        # Assume a portion is available for goal funding
        return max(0, disposable_income * 0.8)  # 80% of disposable income
    
    def _extract_monthly_income(self, profile: dict) -> float:
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
    
    def _extract_monthly_expenses(self, profile: dict) -> float:
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
    
    def _extract_current_monthly(self, goal: Dict[str, Any]) -> float:
        """Extract current monthly contribution for a goal"""
        if "monthly_contribution" in goal:
            return float(goal["monthly_contribution"])
        
        # Default value
        return 5000  # Default assumption
    
    def _calculate_months_to_goal(self, goal: Dict[str, Any]) -> int:
        """Calculate months to goal target date"""
        # Try to calculate from target date
        if "target_date" in goal:
            try:
                from datetime import datetime, date
                target_date = datetime.strptime(goal["target_date"], "%Y-%m-%d").date()
                today = date.today()
                months = (target_date.year - today.year) * 12 + (target_date.month - today.month)
                return max(0, months)
            except (ValueError, TypeError):
                pass
        
        # Default based on goal category
        category = goal.get("category", "")
        return {
            "retirement": 240,
            "education": 120,
            "home": 84,
            "emergency_fund": 12,
            "discretionary": 36,
            "wedding": 24,
            "healthcare": 60,
            "legacy_planning": 180,
            "charitable_giving": 120,
            "debt_repayment": 36
        }.get(category, 60)  # Default 5 years
    
    def _get_goal_names(self, goal_ids: List[str], goals: List[Dict[str, Any]]) -> List[str]:
        """Get goal names from goal IDs"""
        goal_dict = {goal["id"]: goal for goal in goals}
        return [goal_dict.get(goal_id, {}).get("title", f"Goal {goal_id}") for goal_id in goal_ids]
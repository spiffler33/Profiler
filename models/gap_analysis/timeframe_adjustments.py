"""
Timeframe Adjustment Module

This module provides specialized strategies for adjusting goal timeframes
to address funding gaps. It calculates optimal timeline extensions and
evaluates their impact on goal feasibility.
"""

import logging
import math
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple

from models.gap_analysis.core import (
    GapResult, 
    RemediationOption,
    get_financial_parameter_service
)
from models.gap_analysis.remediation_strategies import GapRemediationStrategy

logger = logging.getLogger(__name__)

class TimeframeAdjustment(GapRemediationStrategy):
    """
    Class for calculating and evaluating timeframe extensions for goals.
    
    This class provides methods to calculate and evaluate timeframe extensions
    for financial goals with funding gaps. It helps determine optimal extensions
    that balance goal achievement with realistic timelines.
    """
    
    def __init__(self):
        """
        Initialize the timeframe adjustment strategy.
        """
        super().__init__()
        
        # Additional parameters specific to timeframe adjustments
        self.timeframe_params = {
            "min_extension_months": 3,
            "optimal_extension_factor": 1.5,  # Optimal extension relative to gap
            "critical_extension_threshold": 60,  # Extensions beyond 5 years are critical
            "high_impact_threshold": 0.7,  # High impact on feasibility
        }
        
        # Override defaults with values from parameter service if available
        if self.param_service:
            try:
                # Try to use get_parameters_by_prefix if available
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    param_values = self.param_service.get_parameters_by_prefix("timeframe_adjustment.")
                    if param_values:
                        self.timeframe_params.update(param_values)
                # Fall back to getting individual parameters
                else:
                    for key in self.timeframe_params.keys():
                        param_path = f"timeframe_adjustment.{key}"
                        value = self.param_service.get(param_path)
                        if value is not None:
                            self.timeframe_params[key] = value
            except Exception as e:
                logger.warning(f"Error getting parameters: {e}")
                # Continue with defaults
    
    def analyze_timeframe_impact(self, goal, extension_months: int, profile: dict) -> Dict[str, Any]:
        """
        Analyze the impact of extending a goal's timeframe.
        
        Args:
            goal: The goal to analyze
            extension_months: Number of months to extend the timeline
            profile: The user profile with financial information
            
        Returns:
            Dictionary with impact analysis
        """
        # Get current timeline information
        current_timeline = self._extract_goal_timeline(goal)
        
        # Calculate new timeline
        new_end_date = self._extend_date(current_timeline["end_date"], extension_months)
        new_timeline = {
            "start_date": current_timeline["start_date"],
            "end_date": new_end_date,
            "original_months": current_timeline["total_months"],
            "new_months": current_timeline["elapsed_months"] + extension_months,
            "extension_months": extension_months,
            "extension_percentage": (extension_months / current_timeline["total_months"]) * 100 if current_timeline["total_months"] > 0 else 0
        }
        
        # Calculate financial impact
        target_amount = float(goal.get("target_amount", 0))
        current_amount = float(goal.get("current_amount", 0))
        gap_amount = max(0, target_amount - current_amount)
        
        # Calculate new required monthly contribution
        old_monthly = self._calculate_monthly_contribution(gap_amount, current_timeline["remaining_months"])
        new_monthly = self._calculate_monthly_contribution(gap_amount, current_timeline["remaining_months"] + extension_months)
        monthly_reduction = old_monthly - new_monthly
        
        financial_impact = {
            "old_monthly_contribution": old_monthly,
            "new_monthly_contribution": new_monthly,
            "monthly_reduction": monthly_reduction,
            "monthly_reduction_percentage": (monthly_reduction / old_monthly) * 100 if old_monthly > 0 else 0,
            "annual_contribution_savings": monthly_reduction * 12
        }
        
        # Assess feasibility improvement
        feasibility_improvement = self._calculate_feasibility_improvement(
            new_monthly / old_monthly if old_monthly > 0 else 0,
            extension_months
        )
        
        # Consider life stage implications
        life_stage_impact = self._assess_life_stage_impact(goal, extension_months, profile)
        
        # Overall assessment
        if extension_months > self.timeframe_params["critical_extension_threshold"]:
            impact_level = "significant"
            confidence = 0.7
        elif extension_months > self.timeframe_params["critical_extension_threshold"] / 2:
            impact_level = "moderate"
            confidence = 0.8
        else:
            impact_level = "minor"
            confidence = 0.9
        
        return {
            "timeline": new_timeline,
            "financial_impact": financial_impact,
            "feasibility_improvement": feasibility_improvement,
            "life_stage_impact": life_stage_impact,
            "impact_level": impact_level,
            "confidence": confidence
        }
    
    def calculate_optimal_extension(self, gap_result: GapResult, profile: dict) -> int:
        """
        Calculate the optimal timeframe extension for a goal with a funding gap.
        
        Args:
            gap_result: Gap analysis result for the goal
            profile: User profile with financial information
            
        Returns:
            Optimal extension in months
        """
        # Start with the timeframe gap if available
        if gap_result.timeframe_gap > 0:
            base_extension = gap_result.timeframe_gap
        else:
            # Calculate a reasonable extension based on gap percentage
            base_extension = int(gap_result.gap_percentage / 2)  # 50% gap = 25 months
        
        # Apply optimal extension factor
        optimal_extension = int(base_extension * self.timeframe_params["optimal_extension_factor"])
        
        # Ensure minimum extension
        optimal_extension = max(self.timeframe_params["min_extension_months"], optimal_extension)
        
        # Cap maximum extension
        optimal_extension = min(self.params["max_timeline_extension"], optimal_extension)
        
        # Adjust based on goal category and importance
        goal_category = gap_result.goal_category
        
        # Certain goals need special handling
        if goal_category == "education":
            # Education goals often have hard deadlines
            optimal_extension = min(optimal_extension, 12)  # Max 1 year for education
        elif goal_category == "retirement":
            # Retirement goals can have longer extensions
            age = self._extract_age(profile)
            if age and age < 50:
                optimal_extension = min(optimal_extension, 60)  # Up to 5 years if under 50
            else:
                optimal_extension = min(optimal_extension, 24)  # Max 2 years if 50+
        
        return optimal_extension
    
    def generate_extension_scenarios(self, gap_result: GapResult, profile: dict) -> List[Dict[str, Any]]:
        """
        Generate multiple timeframe extension scenarios with varying impacts.
        
        Args:
            gap_result: Gap analysis result for the goal
            profile: User profile with financial information
            
        Returns:
            List of extension scenarios with impact analysis
        """
        scenarios = []
        
        # Calculate optimal extension
        optimal_extension = self.calculate_optimal_extension(gap_result, profile)
        
        # Generate scenarios around the optimal point
        extensions = [
            max(3, int(optimal_extension * 0.5)),  # Conservative option
            optimal_extension,  # Optimal option
            min(self.params["max_timeline_extension"], int(optimal_extension * 1.5))  # Aggressive option
        ]
        
        # Ensure extensions are unique
        extensions = list(set(extensions))
        extensions.sort()
        
        # Create a mock goal for analysis
        mock_goal = {
            "id": gap_result.goal_id,
            "title": gap_result.goal_title,
            "category": gap_result.goal_category,
            "target_amount": gap_result.target_amount,
            "current_amount": gap_result.current_amount,
            "importance": "medium"  # Default
        }
        
        # Analyze each extension scenario
        for extension in extensions:
            impact = self.analyze_timeframe_impact(mock_goal, extension, profile)
            
            # Categorize the scenario
            if extension == optimal_extension:
                category = "optimal"
            elif extension < optimal_extension:
                category = "conservative"
            else:
                category = "aggressive"
            
            scenario = {
                "extension_months": extension,
                "impact": impact,
                "category": category,
                "feasibility_score": impact["feasibility_improvement"] / 100,
                "monthly_contribution": impact["financial_impact"]["new_monthly_contribution"]
            }
            
            scenarios.append(scenario)
        
        return scenarios
    
    def create_timeline_option(self, extension_months: int, gap_result: GapResult) -> RemediationOption:
        """
        Create a remediation option for timeline extension.
        
        Args:
            extension_months: Number of months to extend the timeline
            gap_result: Gap analysis result for the goal
            
        Returns:
            Remediation option for timeline extension
        """
        # Calculate current monthly contribution (simplified)
        current_monthly = gap_result.gap_amount / 36  # Assume 3 years by default
        
        # Calculate new monthly contribution
        new_monthly = gap_result.gap_amount / (36 + extension_months)
        
        # Calculate monthly savings
        monthly_savings = current_monthly - new_monthly
        
        # Calculate impact metrics
        impact_metrics = {
            "extension_months": extension_months,
            "current_monthly": current_monthly,
            "new_monthly": new_monthly,
            "monthly_savings": monthly_savings,
            "annual_savings": monthly_savings * 12,
            "feasibility_improvement": self._calculate_feasibility_improvement(
                new_monthly / current_monthly if current_monthly > 0 else 0,
                extension_months
            )
        }
        
        # Create description
        years_str = f"{extension_months // 12} years" if extension_months >= 12 else ""
        months_str = f"{extension_months % 12} months" if extension_months % 12 > 0 else ""
        
        if years_str and months_str:
            time_str = f"{years_str} and {months_str}"
        else:
            time_str = years_str or months_str
        
        description = f"Extend the timeline by {time_str}, reducing monthly contribution by ₹{monthly_savings:,.0f}"
        
        # Create implementation steps
        implementation_steps = [
            f"Extend the timeline for {gap_result.goal_title} by {extension_months} months",
            f"Reduce monthly contribution from ₹{current_monthly:,.0f} to ₹{new_monthly:,.0f}",
            "Update your financial plan to reflect the new timeline",
            "Set up automatic contributions at the new amount"
        ]
        
        return RemediationOption(
            description=description,
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps
        )
    
    def _extract_goal_timeline(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """Extract timeline information from a goal"""
        # Set defaults
        start_date = date.today()
        end_date = start_date + timedelta(days=365 * 3)  # Default 3 years
        
        # Try to parse dates
        if "start_date" in goal:
            try:
                start_date = datetime.strptime(goal["start_date"], "%Y-%m-%d").date()
            except ValueError:
                pass
        
        if "target_date" in goal:
            try:
                end_date = datetime.strptime(goal["target_date"], "%Y-%m-%d").date()
            except ValueError:
                pass
        
        # Calculate months
        today = date.today()
        total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        elapsed_months = (today.year - start_date.year) * 12 + (today.month - start_date.month)
        remaining_months = (end_date.year - today.year) * 12 + (end_date.month - today.month)
        
        # Ensure non-negative values
        elapsed_months = max(0, elapsed_months)
        remaining_months = max(0, remaining_months)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_months": total_months,
            "elapsed_months": elapsed_months,
            "remaining_months": remaining_months,
            "percent_complete": (elapsed_months / total_months * 100) if total_months > 0 else 0
        }
    
    def _extend_date(self, base_date: date, months: int) -> date:
        """Extend a date by a number of months"""
        new_month = base_date.month + months
        years_to_add = new_month // 12
        new_month = new_month % 12
        
        if new_month == 0:
            new_month = 12
            years_to_add -= 1
        
        try:
            return date(base_date.year + years_to_add, new_month, base_date.day)
        except ValueError:
            # Handle month end dates (e.g., Jan 31 + 1 month is not Feb 31)
            if new_month in [4, 6, 9, 11]:  # 30-day months
                return date(base_date.year + years_to_add, new_month, min(base_date.day, 30))
            elif new_month == 2:  # February
                leap_year = ((base_date.year + years_to_add) % 4 == 0 and 
                             (base_date.year + years_to_add) % 100 != 0 or 
                             (base_date.year + years_to_add) % 400 == 0)
                return date(base_date.year + years_to_add, new_month, 
                            min(base_date.day, 29 if leap_year else 28))
            else:
                return date(base_date.year + years_to_add, new_month, base_date.day)
    
    def _calculate_monthly_contribution(self, amount: float, months: int) -> float:
        """Calculate monthly contribution required to reach an amount over time"""
        if months <= 0:
            return amount  # Full amount needed immediately
        
        # Simple calculation without interest
        return amount / months
    
    def _calculate_feasibility_improvement(self, contribution_ratio: float, extension_months: int) -> float:
        """
        Calculate feasibility improvement from timeline extension.
        
        Args:
            contribution_ratio: Ratio of new to old contribution (lower is better)
            extension_months: Months of extension
            
        Returns:
            Feasibility improvement score (0-100)
        """
        # Contribution reduction impact (0-70 points)
        contribution_impact = min(70, (1 - contribution_ratio) * 100)
        
        # Extension reasonableness (0-30 points)
        extension_factor = min(1.0, extension_months / self.params["max_timeline_extension"])
        extension_reasonableness = 30 * (1 - extension_factor)
        
        return contribution_impact + extension_reasonableness
    
    def _assess_life_stage_impact(self, goal: Dict[str, Any], extension_months: int, profile: dict) -> Dict[str, Any]:
        """
        Assess the impact of a timeline extension on life stages.
        
        Args:
            goal: The goal being extended
            extension_months: Number of months being added
            profile: User profile with demographic information
            
        Returns:
            Assessment of life stage impacts
        """
        goal_category = goal.get("category", "")
        age = self._extract_age(profile)
        
        # Default impact assessment
        impact = {
            "concerns": [],
            "severity": "low",
            "recommendations": []
        }
        
        # Analyze based on goal type and age
        if goal_category == "retirement" and age:
            if age > 50 and extension_months > 24:
                impact["concerns"].append("Extending retirement timeline significantly after age 50")
                impact["severity"] = "high"
                impact["recommendations"].append("Consider increasing contributions instead of extending timeline")
            elif age > 40 and extension_months > 48:
                impact["concerns"].append("Long retirement extension in mid-career")
                impact["severity"] = "medium"
                impact["recommendations"].append("Balance timeline extension with increased contributions")
        
        elif goal_category == "education" and extension_months > 12:
            impact["concerns"].append("Education goals typically have fixed deadlines")
            impact["severity"] = "high"
            impact["recommendations"].append("Consider other strategies as timeline is likely fixed")
        
        elif goal_category == "home" and extension_months > 36:
            impact["concerns"].append("Significant delay in home purchase")
            impact["severity"] = "medium"
            impact["recommendations"].append("Consider interim housing arrangements during extended timeline")
        
        return impact
    
    def _extract_age(self, profile: dict) -> Optional[int]:
        """Extract age from profile data"""
        # Look for direct age field
        if "age" in profile:
            return int(profile["age"])
        
        # Look in demographics
        if "demographics" in profile and "age" in profile["demographics"]:
            return int(profile["demographics"]["age"])
        
        # Look for birth date
        if "birth_date" in profile:
            try:
                birth_date = datetime.strptime(profile["birth_date"], "%Y-%m-%d").date()
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                return age
            except ValueError:
                pass
        
        # Look in answers
        if "answers" in profile:
            for answer in profile["answers"]:
                if answer.get("question_id") == "age":
                    return int(answer.get("answer", 0))
        
        # Age not found
        return None
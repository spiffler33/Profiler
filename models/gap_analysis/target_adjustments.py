"""
Target Adjustment Module

This module provides specialized strategies for adjusting goal targets
to address funding gaps. It calculates optimal target reductions and
evaluates their impact on goal feasibility.
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple

from models.gap_analysis.core import (
    GapResult, 
    RemediationOption,
    get_financial_parameter_service
)
from models.gap_analysis.remediation_strategies import GapRemediationStrategy

logger = logging.getLogger(__name__)

class TargetAdjustment(GapRemediationStrategy):
    """
    Class for calculating and evaluating target amount reductions.
    
    This class provides methods to calculate and evaluate target amount reductions
    for financial goals with funding gaps. It helps determine reasonable reductions
    that balance goal achievement with financial feasibility.
    """
    
    def __init__(self):
        """
        Initialize the target adjustment strategy.
        """
        super().__init__()
        
        # Additional parameters specific to target adjustments
        self.target_params = {
            "min_reduction_percentage": 0.05,  # Minimum 5% reduction
            "max_reduction_percentage": 0.30,  # Maximum 30% reduction
            "optimal_reduction_factor": 0.7,  # Optimal reduction relative to gap
            "gap_severity_factor": 1.0,  # Default gap severity factor
            "importance_weight": {
                "high": 0.6,  # Less reduction for high importance
                "medium": 1.0,  # Normal reduction for medium importance
                "low": 1.4,  # More reduction for low importance
            }
        }
        
        # Override defaults with values from parameter service if available
        if self.param_service:
            try:
                # Try to use get_parameters_by_prefix if available
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    param_values = self.param_service.get_parameters_by_prefix("target_adjustment.")
                    if param_values:
                        self.target_params.update(param_values)
                # Fall back to getting individual parameters
                else:
                    for key in self.target_params.keys():
                        if key != "importance_weight":  # Skip nested dict
                            param_path = f"target_adjustment.{key}"
                            value = self.param_service.get(param_path)
                            if value is not None:
                                self.target_params[key] = value
            except Exception as e:
                logger.warning(f"Error getting parameters: {e}")
                # Continue with defaults
    
    def analyze_target_impact(self, goal, reduction_percentage: float) -> Dict[str, Any]:
        """
        Analyze the impact of reducing a goal's target amount.
        
        Args:
            goal: The goal to analyze
            reduction_percentage: Percentage to reduce the target (0-100)
            
        Returns:
            Dictionary with impact analysis
        """
        # Extract goal details
        target_amount = float(goal.get("target_amount", 0))
        current_amount = float(goal.get("current_amount", 0))
        gap_amount = max(0, target_amount - current_amount)
        goal_category = goal.get("category", "")
        goal_importance = goal.get("importance", "medium")
        
        # Calculate reduction amount
        reduction_decimal = reduction_percentage / 100
        reduction_amount = target_amount * reduction_decimal
        new_target = target_amount - reduction_amount
        
        # Calculate new gap
        new_gap = max(0, new_target - current_amount)
        gap_reduction = gap_amount - new_gap
        gap_reduction_percentage = (gap_reduction / gap_amount * 100) if gap_amount > 0 else 0
        
        # Calculate financial impact
        monthly_savings = gap_reduction / 36  # Assume 3 years by default
        
        financial_impact = {
            "reduction_amount": reduction_amount,
            "reduction_percentage": reduction_percentage,
            "new_target": new_target,
            "old_gap": gap_amount,
            "new_gap": new_gap,
            "gap_reduction": gap_reduction,
            "gap_reduction_percentage": gap_reduction_percentage,
            "monthly_savings": monthly_savings,
            "annual_savings": monthly_savings * 12
        }
        
        # Assess feasibility improvement
        feasibility_score = min(100, gap_reduction_percentage * 1.2)
        
        # Assess quality impact
        quality_impact = self._assess_quality_impact(
            goal_category, reduction_percentage, goal_importance
        )
        
        # Overall assessment
        if reduction_percentage > 25:
            impact_level = "significant"
            confidence = 0.7
        elif reduction_percentage > 15:
            impact_level = "moderate"
            confidence = 0.8
        else:
            impact_level = "minor"
            confidence = 0.9
        
        return {
            "financial_impact": financial_impact,
            "feasibility_improvement": feasibility_score,
            "quality_impact": quality_impact,
            "impact_level": impact_level,
            "confidence": confidence,
            "alternatives": self._suggest_alternatives(goal_category, reduction_percentage)
        }
    
    def calculate_optimal_reduction(self, gap_result: GapResult) -> float:
        """
        Calculate the optimal target reduction percentage for a goal with a funding gap.
        
        Args:
            gap_result: Gap analysis result for the goal
            
        Returns:
            Optimal reduction percentage (0-100)
        """
        # Start with gap percentage
        gap_percentage = gap_result.gap_percentage
        
        # Apply optimal reduction factor
        optimal_reduction = gap_percentage * self.target_params["optimal_reduction_factor"]
        
        # Adjust based on goal importance
        goal_importance = self._extract_goal_importance(gap_result.goal_id, "medium")
        importance_factor = self.target_params["importance_weight"].get(goal_importance, 1.0)
        
        adjusted_reduction = optimal_reduction * importance_factor
        
        # Ensure within range
        reduction = max(
            self.target_params["min_reduction_percentage"] * 100,
            min(self.target_params["max_reduction_percentage"] * 100, adjusted_reduction)
        )
        
        return reduction
    
    def generate_reduction_scenarios(self, gap_result: GapResult) -> List[Dict[str, Any]]:
        """
        Generate multiple target reduction scenarios with varying impacts.
        
        Args:
            gap_result: Gap analysis result for the goal
            
        Returns:
            List of reduction scenarios with impact analysis
        """
        scenarios = []
        
        # Calculate optimal reduction
        optimal_reduction = self.calculate_optimal_reduction(gap_result)
        
        # Generate scenarios around the optimal point
        reductions = [
            max(5, round(optimal_reduction * 0.5)),  # Conservative option
            round(optimal_reduction),  # Optimal option
            min(30, round(optimal_reduction * 1.5))  # Aggressive option
        ]
        
        # Ensure reductions are unique
        reductions = list(set(reductions))
        reductions.sort()
        
        # Create a mock goal for analysis
        mock_goal = {
            "id": gap_result.goal_id,
            "title": gap_result.goal_title,
            "category": gap_result.goal_category,
            "target_amount": gap_result.target_amount,
            "current_amount": gap_result.current_amount,
            "importance": self._extract_goal_importance(gap_result.goal_id, "medium")
        }
        
        # Analyze each reduction scenario
        for reduction in reductions:
            impact = self.analyze_target_impact(mock_goal, reduction)
            
            # Categorize the scenario
            if reduction == round(optimal_reduction):
                category = "optimal"
            elif reduction < round(optimal_reduction):
                category = "conservative"
            else:
                category = "aggressive"
            
            scenario = {
                "reduction_percentage": reduction,
                "impact": impact,
                "category": category,
                "feasibility_score": impact["feasibility_improvement"] / 100,
                "new_target": impact["financial_impact"]["new_target"]
            }
            
            scenarios.append(scenario)
        
        return scenarios
    
    def create_target_option(self, reduction_percentage: float, gap_result: GapResult) -> RemediationOption:
        """
        Create a remediation option for target reduction.
        
        Args:
            reduction_percentage: Percentage to reduce the target
            gap_result: Gap analysis result for the goal
            
        Returns:
            Remediation option for target reduction
        """
        # Calculate reduction amount
        target_amount = gap_result.target_amount
        reduction_amount = target_amount * (reduction_percentage / 100)
        new_target = target_amount - reduction_amount
        
        # Calculate gap impact
        gap_amount = gap_result.gap_amount
        new_gap = max(0, new_target - gap_result.current_amount)
        gap_reduction = gap_amount - new_gap
        gap_reduction_percentage = (gap_reduction / gap_amount * 100) if gap_amount > 0 else 0
        
        # Create impact metrics
        impact_metrics = {
            "reduction_percentage": reduction_percentage,
            "reduction_amount": reduction_amount,
            "new_target": new_target,
            "gap_reduction": gap_reduction,
            "gap_reduction_percentage": gap_reduction_percentage,
            "monthly_savings": gap_reduction / 36  # Assume 3 years
        }
        
        # Create description
        description = f"Reduce target amount by {reduction_percentage:.0f}% (₹{reduction_amount:,.0f}), saving ₹{gap_reduction:,.0f}"
        
        # Create implementation steps
        implementation_steps = [
            f"Adjust the target amount for {gap_result.goal_title} from ₹{target_amount:,.0f} to ₹{new_target:,.0f}",
            "Research alternatives that could meet your needs at the lower budget",
            "Consider phasing your goal into multiple stages",
            "Recalculate your monthly contribution based on the new target"
        ]
        
        return RemediationOption(
            description=description,
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps
        )
    
    def _assess_quality_impact(self, goal_category: str, reduction_percentage: float, 
                             goal_importance: str) -> Dict[str, Any]:
        """
        Assess the impact of target reduction on goal quality.
        
        Args:
            goal_category: Category of the goal
            reduction_percentage: Percentage reduction in target
            goal_importance: Importance of the goal
            
        Returns:
            Assessment of quality impact
        """
        # Define category-specific impact factors
        category_impact = {
            "retirement": 1.5,      # High impact for retirement
            "education": 1.3,       # High impact for education
            "home": 1.2,            # High impact for home
            "healthcare": 1.4,      # High impact for healthcare
            "wedding": 0.9,         # Lower impact for wedding
            "discretionary": 0.7,   # Lower impact for discretionary
            "emergency_fund": 1.5,  # High impact for emergency fund
            "travel": 0.6           # Low impact for travel
        }.get(goal_category, 1.0)
        
        # Importance multiplier
        importance_multiplier = {
            "high": 1.3,
            "medium": 1.0,
            "low": 0.7
        }.get(goal_importance, 1.0)
        
        # Calculate quality impact score (0-100)
        raw_impact = reduction_percentage * category_impact * importance_multiplier
        quality_impact_score = min(100, raw_impact)
        
        # Determine impact level
        if quality_impact_score > 50:
            impact_level = "significant"
            considerations = self._get_significant_considerations(goal_category)
        elif quality_impact_score > 25:
            impact_level = "moderate"
            considerations = self._get_moderate_considerations(goal_category)
        else:
            impact_level = "minor"
            considerations = ["This reduction should have minimal impact on your goal quality"]
        
        return {
            "impact_score": quality_impact_score,
            "impact_level": impact_level,
            "considerations": considerations
        }
    
    def _get_significant_considerations(self, goal_category: str) -> List[str]:
        """Get considerations for significant quality impact"""
        considerations = [
            "This reduction may significantly impact the quality or feasibility of your goal"
        ]
        
        # Add category-specific considerations
        if goal_category == "retirement":
            considerations.extend([
                "Could significantly reduce your retirement standard of living",
                "May require working longer or part-time during retirement"
            ])
        elif goal_category == "education":
            considerations.extend([
                "May limit institution options or require significant financial aid",
                "Consider public universities or scholarship opportunities"
            ])
        elif goal_category == "home":
            considerations.extend([
                "May require compromising on location, size, or amenities",
                "Consider a smaller starter home or different neighborhood"
            ])
        elif goal_category == "healthcare":
            considerations.extend([
                "Could impact quality of care or treatment options",
                "Research alternative insurance options or government programs"
            ])
        
        return considerations
    
    def _get_moderate_considerations(self, goal_category: str) -> List[str]:
        """Get considerations for moderate quality impact"""
        considerations = [
            "This reduction will require some compromises but should still allow for goal achievement"
        ]
        
        # Add category-specific considerations
        if goal_category == "retirement":
            considerations.append("May require some lifestyle adjustments during retirement")
        elif goal_category == "education":
            considerations.append("Consider community college for initial years or part-time work")
        elif goal_category == "home":
            considerations.append("Consider properties that need some renovation or are farther from city center")
        elif goal_category == "wedding":
            considerations.append("Consider reducing guest count or choosing off-peak wedding dates")
        
        return considerations
    
    def _suggest_alternatives(self, goal_category: str, reduction_percentage: float) -> List[str]:
        """Suggest alternatives to help achieve the goal with reduced target"""
        alternatives = []
        
        # General alternatives
        alternatives.append("Look for cost-saving alternatives that deliver similar benefits")
        
        # Category-specific alternatives
        if goal_category == "education":
            alternatives.extend([
                "Consider starting at a community college and transferring",
                "Research scholarship and financial aid opportunities",
                "Explore online education options for part of the degree"
            ])
        elif goal_category == "home":
            alternatives.extend([
                "Consider properties in emerging neighborhoods",
                "Look for homes needing minor renovations",
                "Explore foreclosure or auction opportunities"
            ])
        elif goal_category == "retirement":
            alternatives.extend([
                "Consider a phased retirement approach",
                "Explore part-time work options during early retirement",
                "Research lower cost of living areas for retirement"
            ])
        elif goal_category == "wedding":
            alternatives.extend([
                "Consider an off-season or weekday wedding date",
                "Explore all-inclusive packages or non-traditional venues",
                "Prioritize key elements and reduce spending on others"
            ])
        elif goal_category == "discretionary":
            alternatives.extend([
                "Look for off-peak travel dates or package deals",
                "Consider pre-owned options for luxury purchases",
                "Explore rental or sharing options for infrequent use items"
            ])
        
        return alternatives
    
    def _extract_goal_importance(self, goal_id: str, default: str = "medium") -> str:
        """Extract goal importance (may need to be implemented)"""
        # In a real implementation, this would look up the goal importance
        # For now, return the default
        return default
"""
Gap Remediation Strategies Module

This module provides the framework and implementations for strategies to address
financial gaps. These strategies generate and evaluate remediation options for
financial goals that are not on track.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

from models.gap_analysis.core import (
    GapResult, 
    RemediationOption,
    get_financial_parameter_service
)

logger = logging.getLogger(__name__)

class GapRemediationStrategy:
    """
    Base class for remediation strategies to address financial gaps.
    
    This class provides the framework for generating and evaluating
    remediation options to address gaps identified in the financial plan.
    Strategies consider the Indian financial context for recommendations.
    """
    
    def __init__(self):
        """
        Initialize the remediation strategy with access to financial parameters.
        """
        self.param_service = get_financial_parameter_service()
        
        # Initialize default parameters
        self.params = {
            "feasibility_threshold": 0.5,  # Min feasibility score to recommend
            "max_expense_reduction": 0.3,  # Max 30% expense reduction
            "max_contribution_increase": 0.2,  # Max 20% income as additional contribution
            "max_timeline_extension": 60,  # Max 60 months timeline extension
            "max_target_reduction": 0.3,  # Max 30% target reduction
        }
        
        # Override defaults with values from parameter service if available
        if self.param_service:
            try:
                # Try to use get_parameters_by_prefix if available
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    param_values = self.param_service.get_parameters_by_prefix("remediation.")
                    if param_values:
                        self.params.update(param_values)
                # Fall back to getting individual parameters
                else:
                    for key in self.params.keys():
                        param_path = f"remediation.{key}"
                        value = self.param_service.get(param_path)
                        if value is not None:
                            self.params[key] = value
            except Exception as e:
                logger.warning(f"Error getting parameters: {e}")
                # Continue with defaults
    
    def generate_options(self, gap_result: GapResult, profile: Dict[str, Any]) -> List[RemediationOption]:
        """
        Generate remediation options for a given gap.
        
        Args:
            gap_result: The gap analysis result
            profile: The user profile with financial information
            
        Returns:
            List of remediation options
        """
        # This is a base implementation that can be overridden by subclasses
        options = []
        
        # Default options that apply to most gaps
        options.append(self._create_contribution_option(gap_result, profile))
        options.append(self._create_timeline_option(gap_result))
        options.append(self._create_target_option(gap_result))
        
        # Filter out None values (if any options couldn't be created)
        return [option for option in options if option is not None]
    
    def evaluate_options(self, options: List[RemediationOption], profile: Dict[str, Any]) -> List[RemediationOption]:
        """
        Evaluate the feasibility and impact of remediation options.
        
        Args:
            options: List of remediation options to evaluate
            profile: The user profile with financial information
            
        Returns:
            Evaluated remediation options with feasibility scores
        """
        evaluated_options = []
        
        for option in options:
            # Calculate feasibility score
            feasibility = self._calculate_feasibility(option, profile)
            option.feasibility_score = feasibility
            
            # Only include options with sufficient feasibility
            if feasibility >= self.params["feasibility_threshold"]:
                evaluated_options.append(option)
        
        # Sort by feasibility
        evaluated_options.sort(key=lambda x: x.feasibility_score, reverse=True)
        
        return evaluated_options
    
    def recommend_best_option(self, options: List[RemediationOption], profile: Dict[str, Any]) -> Optional[RemediationOption]:
        """
        Recommend the best remediation option based on evaluation.
        
        Args:
            options: List of evaluated remediation options
            profile: The user profile with financial information
            
        Returns:
            The best remediation option or None if no viable options
        """
        if not options:
            return None
        
        # Evaluate if not already evaluated
        if any(option.feasibility_score == 0 for option in options):
            options = self.evaluate_options(options, profile)
        
        # Return the highest feasibility option
        return options[0] if options else None
    
    def generate_implementation_steps(self, option: RemediationOption, profile: Dict[str, Any]) -> List[str]:
        """
        Generate implementation steps for a remediation option.
        
        Args:
            option: The remediation option
            profile: The user profile with financial information
            
        Returns:
            List of implementation steps
        """
        # This is a base implementation that should be overridden by subclasses
        description = option.description.lower()
        
        if "contribution" in description:
            return self._generate_contribution_steps(option, profile)
        elif "timeline" in description or "extend" in description:
            return self._generate_timeline_steps(option)
        elif "target" in description or "reduce" in description:
            return self._generate_target_steps(option)
        else:
            return ["Review your financial plan", "Implement the suggested changes", "Monitor progress regularly"]
    
    def _calculate_feasibility(self, option: RemediationOption, profile: Dict[str, Any]) -> float:
        """Calculate the feasibility score for a remediation option"""
        # Default implementation - should be overridden by subclasses
        # Basic feasibility assessment
        description = option.description.lower()
        
        # Default moderate feasibility
        feasibility = 0.5
        
        # Adjust based on option type
        if "contribution" in description:
            # Check if the contribution increase is manageable
            increase = option.impact_metrics.get("monthly_increase", 0)
            income = self._extract_monthly_income(profile)
            
            # Lower feasibility if increase is too large relative to income
            if income > 0:
                increase_pct = increase / income
                if increase_pct > self.params["max_contribution_increase"]:
                    feasibility *= 0.5
                elif increase_pct < 0.05:  # Small increase is very feasible
                    feasibility *= 1.5
        
        elif "timeline" in description or "extend" in description:
            # Check if timeline extension is reasonable
            extension = option.impact_metrics.get("recommended_months", 0)
            
            # Lower feasibility if extension is too long
            if extension > self.params["max_timeline_extension"]:
                feasibility *= 0.6
            elif extension < 12:  # Small extension is very feasible
                feasibility *= 1.4
        
        elif "target" in description or "reduce" in description:
            # Check if target reduction is reasonable
            reduction_pct = option.impact_metrics.get("recommended_reduction_percent", 0)
            
            # Lower feasibility if reduction is too large
            if reduction_pct > self.params["max_target_reduction"] * 100:
                feasibility *= 0.7
            elif reduction_pct < 10:  # Small reduction is very feasible
                feasibility *= 1.3
        
        # Cap feasibility between 0 and 1
        return max(0.1, min(1.0, feasibility))
    
    def _create_contribution_option(self, gap_result: GapResult, profile: Dict[str, Any]) -> Optional[RemediationOption]:
        """Create a contribution increase option"""
        # Extract income data
        monthly_income = self._extract_monthly_income(profile)
        
        # Calculate a reasonable increase amount
        if gap_result.capacity_gap > 0:
            increase_amount = gap_result.capacity_gap
        else:
            # If no specific capacity gap, suggest percentage of income
            increase_amount = monthly_income * 0.05  # 5% of income
        
        # Cap at maximum percentage of income
        max_increase = monthly_income * self.params["max_contribution_increase"]
        final_increase = min(increase_amount, max_increase)
        
        # If increase is too small, don't create an option
        if final_increase < 1000:  # Minimum meaningful increase
            return None
        
        # Calculate impact metrics
        gap_closure_months = (gap_result.gap_amount / final_increase) if final_increase > 0 else 0
        
        impact_metrics = {
            "monthly_increase": final_increase,
            "percentage_of_income": (final_increase / monthly_income) * 100 if monthly_income > 0 else 0,
            "yearly_impact": final_increase * 12,
            "gap_closure_months": int(gap_closure_months)
        }
        
        # Create option
        description = f"Increase monthly contribution by ₹{final_increase:,.0f}"
        implementation_steps = [
            "Review your monthly budget",
            f"Allocate an additional ₹{final_increase:,.0f} per month",
            "Set up an automatic transfer to your goal account"
        ]
        
        return RemediationOption(
            description=description,
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps
        )
    
    def _create_timeline_option(self, gap_result: GapResult) -> Optional[RemediationOption]:
        """Create a timeline extension option"""
        # Calculate a reasonable extension period
        if gap_result.timeframe_gap > 0:
            extension_months = min(gap_result.timeframe_gap * 1.5, self.params["max_timeline_extension"])
        else:
            # If no specific timeframe gap, suggest based on gap amount
            extension_months = int(gap_result.gap_percentage / 5)  # 5% gap = 1 month
        
        # Ensure minimum meaningful extension
        extension_months = max(3, min(int(extension_months), self.params["max_timeline_extension"]))
        
        # Calculate impact metrics
        feasibility_improvement = min(extension_months / 12 * 10, 100)  # 1 year = 10% improvement
        required_monthly = gap_result.gap_amount / extension_months if extension_months > 0 else 0
        
        impact_metrics = {
            "recommended_months": extension_months,
            "goal_feasibility_improvement": feasibility_improvement,
            "required_monthly_contribution": required_monthly
        }
        
        # Create option
        description = f"Extend goal timeline by {extension_months} months"
        implementation_steps = [
            "Review your goal's current timeline",
            f"Adjust your target date to extend by {extension_months} months",
            "Recalculate your required monthly savings"
        ]
        
        return RemediationOption(
            description=description,
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps
        )
    
    def _create_target_option(self, gap_result: GapResult) -> Optional[RemediationOption]:
        """Create a target reduction option"""
        # Calculate a reasonable reduction percentage based on gap percentage
        reduction_percentage = min(gap_result.gap_percentage / 2, self.params["max_target_reduction"] * 100)
        
        # Ensure minimum meaningful reduction
        reduction_percentage = max(5.0, min(reduction_percentage, self.params["max_target_reduction"] * 100))
        
        # Calculate reduction amount
        reduction_amount = gap_result.target_amount * (reduction_percentage / 100)
        new_target = gap_result.target_amount - reduction_amount
        
        # Calculate impact metrics
        feasibility_improvement = reduction_percentage * 2  # Reducing by 10% improves feasibility by 20%
        
        impact_metrics = {
            "recommended_reduction_percent": reduction_percentage,
            "recommended_reduction_amount": reduction_amount,
            "new_target": new_target,
            "feasibility_improvement": feasibility_improvement
        }
        
        # Create option
        description = f"Reduce target amount by {reduction_percentage:.1f}% (₹{reduction_amount:,.0f})"
        implementation_steps = [
            "Review your goal's requirements",
            f"Adjust your target amount to ₹{new_target:,.0f}",
            "Consider alternatives to reduce the goal cost"
        ]
        
        return RemediationOption(
            description=description,
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps
        )
    
    def _generate_contribution_steps(self, option: RemediationOption, profile: Dict[str, Any]) -> List[str]:
        """Generate implementation steps for a contribution increase option"""
        increase = option.impact_metrics.get("monthly_increase", 0)
        
        steps = [
            "Review your monthly budget to identify areas for saving",
            f"Set aside an additional ₹{increase:,.0f} per month for this goal",
            "Set up an automatic transfer or SIP to ensure regular contributions",
            "Review and adjust your budget to accommodate the increased savings"
        ]
        
        # Add India-specific steps
        steps.append("Consider tax-efficient investment vehicles like ELSS, PPF, or NPS")
        
        return steps
    
    def _generate_timeline_steps(self, option: RemediationOption) -> List[str]:
        """Generate implementation steps for a timeline extension option"""
        extension = option.impact_metrics.get("recommended_months", 0)
        
        steps = [
            f"Extend your goal timeline by {extension} months",
            "Recalculate your monthly contribution requirements",
            "Update your financial plan to reflect the new timeline",
            "Set realistic milestones for tracking progress on the extended timeline"
        ]
        
        return steps
    
    def _generate_target_steps(self, option: RemediationOption) -> List[str]:
        """Generate implementation steps for a target reduction option"""
        new_target = option.impact_metrics.get("new_target", 0)
        reduction_percent = option.impact_metrics.get("recommended_reduction_percent", 0)
        
        steps = [
            f"Adjust your goal target to ₹{new_target:,.0f} (a {reduction_percent:.1f}% reduction)",
            "Research cost-saving alternatives for achieving your goal",
            "Consider phasing the goal into multiple stages",
            "Recalculate your monthly contribution based on the new target"
        ]
        
        return steps
    
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


class RemediationImpactAnalysis:
    """
    Class for analyzing the impact of remediation options and strategies.
    
    This class provides tools to evaluate the feasibility, emotional impact,
    and side effects of various remediation options to help users make
    informed decisions about addressing financial gaps.
    """
    
    def __init__(self):
        """
        Initialize the remediation impact analysis.
        """
        self.param_service = get_financial_parameter_service()
        
        # Default parameters
        self.params = {
            "emotional_weight_timeline": 0.5,  # Weight for timeline changes
            "emotional_weight_target": 0.7,    # Weight for target changes
            "emotional_weight_contribution": 0.3,  # Weight for contribution changes
            "min_income_buffer": 0.1,  # Minimum 10% income buffer
        }
        
        # Override defaults with values from parameter service if available
        if self.param_service:
            try:
                # Try to use get_parameters_by_prefix if available
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    param_values = self.param_service.get_parameters_by_prefix("remediation_impact.")
                    if param_values:
                        self.params.update(param_values)
                # Fall back to getting individual parameters
                else:
                    for key in self.params.keys():
                        param_path = f"remediation_impact.{key}"
                        value = self.param_service.get(param_path)
                        if value is not None:
                            self.params[key] = value
            except Exception as e:
                logger.warning(f"Error getting parameters: {e}")
                # Continue with defaults
    
    def analyze_emotional_impact(self, remediation_options: List[RemediationOption], profile: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze the emotional impact of remediation options.
        
        Args:
            remediation_options: List of remediation options to analyze
            profile: The user profile with financial information
            
        Returns:
            Dictionary mapping option descriptions to emotional impact assessments
        """
        results = {}
        
        for option in remediation_options:
            # Determine option type
            option_type = self._determine_option_type(option)
            
            # Calculate emotional impact based on type
            if option_type == "contribution":
                impact = self._analyze_contribution_impact(option, profile)
            elif option_type == "timeline":
                impact = self._analyze_timeline_impact(option)
            elif option_type == "target":
                impact = self._analyze_target_impact(option)
            else:
                impact = {"emotional_impact": "neutral", "confidence": 0.5}
            
            results[option.description] = impact
        
        return results
    
    def _determine_option_type(self, option: RemediationOption) -> str:
        """Determine the type of remediation option"""
        description = option.description.lower()
        
        if "contribution" in description or "increase" in description:
            return "contribution"
        elif "timeline" in description or "extend" in description:
            return "timeline"
        elif "target" in description or "reduce" in description:
            return "target"
        else:
            return "unknown"
    
    def _analyze_contribution_impact(self, option: RemediationOption, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the emotional impact of a contribution change"""
        # Extract details
        increase = option.impact_metrics.get("monthly_increase", 0)
        income = self._extract_monthly_income(profile)
        
        # Calculate impact metrics
        increase_pct = (increase / income) * 100 if income > 0 else 0
        
        # Determine emotional impact
        if increase_pct > 15:
            emotional_impact = "significant_stress"
            confidence = 0.8
        elif increase_pct > 10:
            emotional_impact = "moderate_stress"
            confidence = 0.7
        elif increase_pct > 5:
            emotional_impact = "mild_stress"
            confidence = 0.6
        else:
            emotional_impact = "minimal"
            confidence = 0.9
        
        # Check if income buffer is sufficient
        disposable_income = income * 0.3  # Assume 30% disposable
        if increase > disposable_income * (1 - self.params["min_income_buffer"]):
            risk_factors = ["Leaves insufficient discretionary income buffer"]
        else:
            risk_factors = []
        
        return {
            "emotional_impact": emotional_impact,
            "confidence": confidence,
            "impact_percentage": increase_pct,
            "risk_factors": risk_factors
        }
    
    def _analyze_timeline_impact(self, option: RemediationOption) -> Dict[str, Any]:
        """Analyze the emotional impact of a timeline change"""
        # Extract details
        extension = option.impact_metrics.get("recommended_months", 0)
        
        # Determine emotional impact based on extension length
        if extension > 36:  # 3 years
            emotional_impact = "significant_disappointment"
            confidence = 0.8
            risk_factors = ["Substantially delays goal achievement", "May affect related goals"]
        elif extension > 24:  # 2 years
            emotional_impact = "moderate_disappointment"
            confidence = 0.7
            risk_factors = ["Significantly delays goal achievement"]
        elif extension > 12:  # 1 year
            emotional_impact = "mild_disappointment"
            confidence = 0.6
            risk_factors = []
        else:
            emotional_impact = "minimal"
            confidence = 0.9
            risk_factors = []
        
        return {
            "emotional_impact": emotional_impact,
            "confidence": confidence,
            "extension_impact": extension / 12,  # Impact in years
            "risk_factors": risk_factors
        }
    
    def _analyze_target_impact(self, option: RemediationOption) -> Dict[str, Any]:
        """Analyze the emotional impact of a target change"""
        # Extract details
        reduction_pct = option.impact_metrics.get("recommended_reduction_percent", 0)
        
        # Determine emotional impact based on reduction percentage
        if reduction_pct > 25:
            emotional_impact = "significant_compromise"
            confidence = 0.8
            risk_factors = ["Substantially changes goal quality", "May not meet actual needs"]
        elif reduction_pct > 15:
            emotional_impact = "moderate_compromise"
            confidence = 0.7
            risk_factors = ["Significantly changes goal quality"]
        elif reduction_pct > 10:
            emotional_impact = "mild_compromise"
            confidence = 0.6
            risk_factors = []
        else:
            emotional_impact = "minimal"
            confidence = 0.9
            risk_factors = []
        
        return {
            "emotional_impact": emotional_impact,
            "confidence": confidence,
            "reduction_impact": reduction_pct / 100,  # Impact as decimal
            "risk_factors": risk_factors
        }
    
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
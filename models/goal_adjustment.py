"""
Goal Adjustment Recommender Module

This module provides tools for recommending adjustments to financial goals based on
gap analysis results. It offers concrete, actionable recommendations tailored to the
Indian financial context, considering tax implications, cultural preferences, and
investment patterns common in India.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Type
from dataclasses import dataclass, field
from enum import Enum
import math
from datetime import datetime, timedelta

# Import related modules
from models.gap_analysis.core import (
    GapResult,
    GapSeverity,
    RemediationOption,
    get_financial_parameter_service
)

logger = logging.getLogger(__name__)


class AdjustmentType(Enum):
    """Enum for different types of goal adjustments"""
    TARGET_AMOUNT = "target_amount"  # Adjust the target amount
    TIMEFRAME = "timeframe"  # Adjust the timeframe (extend/shorten)
    CONTRIBUTION = "contribution"  # Adjust contributions (increase/decrease)
    ALLOCATION = "allocation"  # Adjust asset allocation


@dataclass
class GoalAdjustment:
    """
    Data class representing a recommended adjustment to a goal.
    
    This class provides a structured way to represent adjustments to financial
    goals, including the type of adjustment, its value, impact metrics, and
    steps for implementation.
    """
    goal_id: str
    adjustment_type: AdjustmentType
    adjustment_value: Union[float, int, Dict[str, float]]
    original_value: Union[float, int, Dict[str, float]]
    description: str
    impact_metrics: Dict[str, Any] = field(default_factory=dict)
    implementation_steps: List[str] = field(default_factory=list)
    tax_implications: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    suitability_score: float = 0.0
    india_specific_notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert adjustment to dictionary for serialization"""
        return {
            "goal_id": self.goal_id,
            "adjustment_type": self.adjustment_type.value,
            "adjustment_value": self.adjustment_value,
            "original_value": self.original_value,
            "description": self.description,
            "impact_metrics": self.impact_metrics,
            "implementation_steps": self.implementation_steps,
            "tax_implications": self.tax_implications,
            "confidence_score": self.confidence_score,
            "suitability_score": self.suitability_score,
            "india_specific_notes": self.india_specific_notes
        }


class GoalAdjustmentRecommender:
    """
    Recommends adjustments to financial goals based on gap analysis results.
    
    This class provides methods to recommend concrete, actionable adjustments to
    financial goals to improve their probability of success. The recommendations
    are tailored to the Indian financial context, considering tax implications,
    cultural preferences, and investment patterns common in India.
    """
    
    def __init__(self, param_service=None):
        """
        Initialize the goal adjustment recommender with financial parameters.
        
        Args:
            param_service: Optional financial parameter service instance.
                          If not provided, will attempt to get one.
        """
        # Get parameter service if not provided
        self.param_service = param_service
        
        # Only try to get service if explicitly None (for test patching)
        if self.param_service is None:
            self.param_service = get_financial_parameter_service()
        
        # Default parameters for adjustment recommendations
        self.params = {
            "max_target_reduction": 0.30,  # Max 30% target reduction
            "max_timeframe_extension": 60,  # Max 60 months extension
            "max_contribution_increase": 0.20,  # Max 20% of income as additional contribution
            "max_allocation_shift": 0.20,  # Max 20% shift in asset allocation
            "min_equity_allocation": 0.20,  # Min 20% equity for long-term goals
            "max_equity_allocation": 0.80,  # Max 80% equity for any goal
            "emergency_fund_months": 6,  # 6 months expenses for emergency fund
            "min_adjustment_impact": 0.10,  # Min 10% improvement to recommend
            "section_80c_limit": 150000,  # Section 80C tax benefit limit (₹)
            "ppf_annual_limit": 150000,  # PPF annual contribution limit (₹)
            "nps_tax_benefit_limit": 50000,  # Additional NPS tax benefit (₹)
            "elss_lock_in_years": 3,  # ELSS lock-in period in years
            "ppf_lock_in_years": 15,  # PPF lock-in period in years
            "gold_allocation_cap": 0.15,  # Maximum recommended gold allocation
        }
        
        # Override defaults with values from parameter service if available
        if self.param_service:
            try:
                # Try to use get_parameters_by_prefix if available
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    param_values = self.param_service.get_parameters_by_prefix("goal_adjustment.")
                    if param_values:
                        self.params.update(param_values)
                # Fall back to getting individual parameters
                else:
                    for key in self.params.keys():
                        param_path = f"goal_adjustment.{key}"
                        value = self.param_service.get(param_path)
                        if value is not None:
                            self.params[key] = value
            except Exception as e:
                logger.warning(f"Error getting parameters: {e}")
                # Continue with defaults
    
    def recommend_adjustments(
        self,
        gap_result: GapResult,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        adjustment_types: Optional[List[AdjustmentType]] = None
    ) -> List[GoalAdjustment]:
        """
        Recommend adjustments to a goal based on gap analysis results.
        
        Args:
            gap_result: Gap analysis result for the goal
            goal_data: Complete goal data including current parameters
            profile: User profile with financial information
            adjustment_types: Optional list of adjustment types to consider
                            If None, all adjustment types will be considered
                            
        Returns:
            List of recommended goal adjustments, sorted by suitability
        """
        adjustments = []
        
        # If adjustment types not specified, consider all types
        if adjustment_types is None:
            adjustment_types = list(AdjustmentType)
        
        # Generate recommendations based on specified adjustment types
        for adj_type in adjustment_types:
            if adj_type == AdjustmentType.TARGET_AMOUNT:
                adjustment = self.adjust_target_amount(gap_result, goal_data, profile)
                if adjustment:
                    adjustments.append(adjustment)
            
            elif adj_type == AdjustmentType.TIMEFRAME:
                adjustment = self.adjust_timeframe(gap_result, goal_data, profile)
                if adjustment:
                    adjustments.append(adjustment)
            
            elif adj_type == AdjustmentType.CONTRIBUTION:
                adjustment = self.adjust_contribution(gap_result, goal_data, profile)
                if adjustment:
                    adjustments.append(adjustment)
            
            elif adj_type == AdjustmentType.ALLOCATION:
                adjustment = self.adjust_allocation(gap_result, goal_data, profile)
                if adjustment:
                    adjustments.append(adjustment)
        
        # Sort adjustments by suitability score (highest first)
        adjustments.sort(key=lambda x: x.suitability_score, reverse=True)
        
        return adjustments
    
    def adjust_target_amount(
        self,
        gap_result: GapResult,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> Optional[GoalAdjustment]:
        """
        Recommend target amount adjustment based on gap analysis.
        
        Args:
            gap_result: Gap analysis result for the goal
            goal_data: Complete goal data including current parameters
            profile: User profile with financial information
            
        Returns:
            Goal adjustment with target amount recommendation or None
        """
        # Only reduce target if gap is significant
        if gap_result.gap_percentage < self.params["min_adjustment_impact"]:
            return None
        
        # Calculate a reasonable reduction percentage based on gap
        reduction_percentage = min(
            gap_result.gap_percentage / 2,  # Half the gap percentage
            self.params["max_target_reduction"]  # Maximum allowed reduction
        )
        
        # Ensure minimum meaningful reduction (at least 5%)
        reduction_percentage = max(0.05, reduction_percentage)
        
        # Calculate reduction amount and new target
        target_amount = gap_result.target_amount
        reduction_amount = target_amount * reduction_percentage
        new_target = target_amount - reduction_amount
        
        # Calculate impact metrics
        feasibility_improvement = reduction_percentage * 2  # Reducing by 10% improves feasibility by ~20%
        
        impact_metrics = {
            "reduction_percentage": reduction_percentage * 100,  # Convert to percentage
            "reduction_amount": reduction_amount,
            "new_target_amount": new_target,
            "feasibility_improvement": feasibility_improvement * 100,  # Convert to percentage
            "monthly_saving_reduction": self._calculate_monthly_impact(reduction_amount, goal_data)
        }
        
        # Generate implementation steps
        implementation_steps = [
            f"Reduce your target amount from ₹{target_amount:,.0f} to ₹{new_target:,.0f}",
            "Review your goal requirements to identify areas for cost reduction",
            "Consider alternatives or phased approach to achieve your goal",
            "Adjust your financial plan to reflect the new target amount"
        ]
        
        # Add goal-specific implementation steps
        goal_category = goal_data.get("category", "").lower()
        if "education" in goal_category:
            implementation_steps.extend([
                "Research education loan options as a supplement to savings",
                "Consider educational institutions with lower fees or scholarship opportunities",
                "Look into distance learning or part-time programs to reduce costs"
            ])
        elif "home" in goal_category or "house" in goal_category:
            implementation_steps.extend([
                "Consider a smaller property or different location",
                "Explore properties requiring less renovation",
                "Research home loan options with better interest rates"
            ])
        elif "wedding" in goal_category or "marriage" in goal_category:
            implementation_steps.extend([
                "Consider a more intimate ceremony with fewer guests",
                "Look for off-season wedding dates for better venue rates",
                "Prioritize essential elements and reduce spending on less important aspects"
            ])
        
        # Calculate tax implications (minimal for target reduction)
        tax_implications = {
            "direct_tax_impact": "None",
            "indirect_tax_impact": "Reduced tax-saving investment needs"
        }
        
        # India-specific notes
        india_specific_notes = [
            "Consider the cultural importance of your goal when reducing targets",
            "Evaluate joint family contribution possibilities for important goals"
        ]
        
        # Goal-specific India notes
        if "education" in goal_category:
            india_specific_notes.append(
                "Consider education loans with interest subsidies from the government"
            )
        elif "wedding" in goal_category:
            india_specific_notes.append(
                "Consider gold monetization schemes for wedding jewelry requirements"
            )
        
        # Calculate suitability score based on goal type and cultural context
        suitability_score = self._calculate_target_reduction_suitability(
            goal_category, reduction_percentage, profile
        )
        
        # Create the adjustment
        return GoalAdjustment(
            goal_id=goal_data.get("id", ""),
            adjustment_type=AdjustmentType.TARGET_AMOUNT,
            adjustment_value=new_target,
            original_value=target_amount,
            description=f"Reduce target amount by {reduction_percentage*100:.1f}% (₹{reduction_amount:,.0f})",
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps,
            tax_implications=tax_implications,
            confidence_score=0.7,  # Target reductions have moderate confidence
            suitability_score=suitability_score,
            india_specific_notes=india_specific_notes
        )
    
    def adjust_timeframe(
        self,
        gap_result: GapResult,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> Optional[GoalAdjustment]:
        """
        Recommend timeframe adjustment based on gap analysis.
        
        Args:
            gap_result: Gap analysis result for the goal
            goal_data: Complete goal data including current parameters
            profile: User profile with financial information
            
        Returns:
            Goal adjustment with timeframe recommendation or None
        """
        # Skip if the goal has a hard deadline that cannot be extended
        if goal_data.get("has_fixed_deadline", False):
            return None
        
        # Calculate reasonable extension period
        if gap_result.timeframe_gap > 0:
            # Use the calculated timeframe gap with a small buffer
            extension_months = min(
                int(gap_result.timeframe_gap * 1.2),  # 20% buffer on timeframe gap
                self.params["max_timeframe_extension"]  # Maximum allowed extension
            )
        else:
            # If no specific timeframe gap, suggest based on gap percentage
            extension_months = int(gap_result.gap_percentage * 24)  # 1% gap ≈ 0.24 months
        
        # Ensure minimum meaningful extension (at least 3 months)
        extension_months = max(3, extension_months)
        
        # Get current timeline information
        target_date_str = goal_data.get("target_date", "")
        try:
            current_target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
            new_target_date = current_target_date + timedelta(days=extension_months * 30)
            current_timeline_months = self._calculate_months_to_goal(current_target_date)
        except (ValueError, TypeError):
            # If target date is invalid, use estimated timeline
            current_timeline_months = goal_data.get("timeline_months", 60)
            new_target_date = datetime.now() + timedelta(days=(current_timeline_months + extension_months) * 30)
        
        new_timeline_months = current_timeline_months + extension_months
        
        # Calculate impact metrics
        monthly_contribution = goal_data.get("monthly_contribution", 0)
        reduced_monthly = self._calculate_adjusted_contribution(
            gap_result.target_amount,
            gap_result.current_amount,
            new_timeline_months,
            goal_data.get("expected_return", 0.08)
        )
        
        monthly_saving = monthly_contribution - reduced_monthly
        
        impact_metrics = {
            "extension_months": extension_months,
            "new_timeline_months": new_timeline_months,
            "original_timeline_months": current_timeline_months,
            "new_target_date": new_target_date.strftime("%Y-%m-%d"),
            "monthly_contribution_reduction": monthly_saving,
            "monthly_contribution_reduction_percent": 
                (monthly_saving / monthly_contribution * 100) if monthly_contribution > 0 else 0
        }
        
        # Generate implementation steps
        implementation_steps = [
            f"Extend your goal timeline by {extension_months} months",
            f"Update your target date to {new_target_date.strftime('%d %b %Y')}",
            f"Reduce your monthly contribution from ₹{monthly_contribution:,.0f} to ₹{reduced_monthly:,.0f}",
            "Adjust your SIP (Systematic Investment Plan) instructions accordingly"
        ]
        
        # Add goal-specific implementation steps
        goal_category = goal_data.get("category", "").lower()
        if "education" in goal_category:
            implementation_steps.append(
                "Consider if the extended timeline aligns with academic year schedules"
            )
        elif "retirement" in goal_category:
            implementation_steps.append(
                "Adjust your retirement age in your planning documents"
            )
        elif "wedding" in goal_category:
            implementation_steps.append(
                "Consider auspicious dates when selecting your new timeline"
            )
        
        # Calculate tax implications
        tax_implications = {
            "direct_tax_impact": "Reduced tax-saving investments may impact Section 80C benefits",
            "potential_benefit": f"Spread tax benefits over a longer period for better utilization"
        }
        
        # India-specific notes
        india_specific_notes = [
            "Align your SIP dates with your salary credit date for better cash flow management",
            "Consider step-up SIPs to complement timeline extensions as your income grows"
        ]
        
        # Goal-specific India notes
        if "education" in goal_category:
            india_specific_notes.append(
                "Align education timelines with academic years starting in June/July"
            )
        elif "retirement" in goal_category:
            india_specific_notes.append(
                "NPS (National Pension System) allows continued contributions until age 70"
            )
        
        # Calculate suitability score
        suitability_score = self._calculate_timeframe_extension_suitability(
            goal_category, extension_months, profile
        )
        
        # Create the adjustment
        return GoalAdjustment(
            goal_id=goal_data.get("id", ""),
            adjustment_type=AdjustmentType.TIMEFRAME,
            adjustment_value=extension_months,
            original_value=current_timeline_months,
            description=f"Extend goal timeline by {extension_months} months",
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps,
            tax_implications=tax_implications,
            confidence_score=0.8,  # Timeframe extensions have high confidence
            suitability_score=suitability_score,
            india_specific_notes=india_specific_notes
        )
    
    def adjust_contribution(
        self,
        gap_result: GapResult,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> Optional[GoalAdjustment]:
        """
        Recommend contribution adjustment based on gap analysis.
        
        Args:
            gap_result: Gap analysis result for the goal
            goal_data: Complete goal data including current parameters
            profile: User profile with financial information
            
        Returns:
            Goal adjustment with contribution recommendation or None
        """
        # Extract income data
        monthly_income = self._extract_monthly_income(profile)
        
        # Current contribution
        current_contribution = goal_data.get("monthly_contribution", 0)
        
        # Calculate required contribution increase
        if gap_result.capacity_gap > 0:
            increase_amount = gap_result.capacity_gap
        else:
            # If no specific capacity gap, calculate based on funding gap
            timeline_months = self._get_remaining_timeline(goal_data)
            if timeline_months <= 0:
                timeline_months = 60  # Default to 5 years if timeline is invalid
                
            # Simple approximation - divide gap by remaining months
            # For a more accurate calculation, we'd need to account for investment returns
            increase_amount = gap_result.gap_amount / timeline_months
        
        # Cap increase at maximum percentage of income
        max_increase = monthly_income * self.params["max_contribution_increase"]
        final_increase = min(increase_amount, max_increase)
        
        # Ensure minimum meaningful increase (at least 1000 INR or 5% of current)
        min_increase = max(1000, current_contribution * 0.05)
        if final_increase < min_increase:
            return None
        
        new_contribution = current_contribution + final_increase
        
        # Calculate impact metrics
        impact_metrics = {
            "monthly_increase": final_increase,
            "percentage_of_income": (final_increase / monthly_income) * 100 if monthly_income > 0 else 0,
            "yearly_impact": final_increase * 12,
            "new_monthly_contribution": new_contribution,
            "contribution_increase_percent": (final_increase / current_contribution) * 100
                if current_contribution > 0 else 100
        }
        
        # Calculate tax impact
        tax_savings = self._calculate_tax_savings(final_increase * 12, goal_data, profile)
        if tax_savings > 0:
            impact_metrics["annual_tax_savings"] = tax_savings
        
        # Generate implementation steps
        implementation_steps = [
            f"Increase your monthly contribution from ₹{current_contribution:,.0f} to ₹{new_contribution:,.0f}",
            "Review your monthly budget to identify areas for saving",
            "Set up or update your Systematic Investment Plan (SIP) with the new amount",
            "Consider setting up automatic transfers on your salary date"
        ]
        
        # Add goal-specific implementation steps
        goal_category = goal_data.get("category", "").lower()
        if "retirement" in goal_category:
            implementation_steps.extend([
                "Consider using NPS for additional tax benefits under Section 80CCD(1B)",
                "Explore employer matching contributions to retirement accounts if available"
            ])
        elif "education" in goal_category:
            implementation_steps.append(
                "Consider Sukanya Samriddhi Yojana for girl child education with tax benefits"
            )
        
        # Calculate tax implications
        tax_implications = self._calculate_contribution_tax_implications(
            final_increase, goal_data, profile
        )
        
        # India-specific notes
        india_specific_notes = [
            "Consider SIPs in tax-saving ELSS funds for dual benefits of tax saving and goal funding",
            "Link contribution increases to annual salary increments for better sustainability"
        ]
        
        # Goal-specific India notes
        if "retirement" in goal_category:
            india_specific_notes.append(
                "NPS offers additional tax deduction of ₹50,000 under Section 80CCD(1B)"
            )
        elif "home" in goal_category:
            india_specific_notes.append(
                "Home loan principal repayments qualify for Section 80C deduction up to ₹1.5 lakhs annually"
            )
        
        # Calculate suitability score
        suitability_score = self._calculate_contribution_increase_suitability(
            goal_category, final_increase, monthly_income, profile
        )
        
        # Create the adjustment
        return GoalAdjustment(
            goal_id=goal_data.get("id", ""),
            adjustment_type=AdjustmentType.CONTRIBUTION,
            adjustment_value=new_contribution,
            original_value=current_contribution,
            description=f"Increase monthly contribution by ₹{final_increase:,.0f}",
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps,
            tax_implications=tax_implications,
            confidence_score=0.85,  # Contribution increases have high confidence
            suitability_score=suitability_score,
            india_specific_notes=india_specific_notes
        )
    
    def adjust_allocation(
        self,
        gap_result: GapResult,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> Optional[GoalAdjustment]:
        """
        Recommend asset allocation adjustment based on gap analysis.
        
        Args:
            gap_result: Gap analysis result for the goal
            goal_data: Complete goal data including current parameters
            profile: User profile with financial information
            
        Returns:
            Goal adjustment with allocation recommendation or None
        """
        # Extract current allocation
        current_allocation = goal_data.get("asset_allocation", {})
        
        # Handle string JSON representation of allocation
        if isinstance(current_allocation, str):
            try:
                import json
                current_allocation = json.loads(current_allocation)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse asset allocation from string: {current_allocation}")
                current_allocation = {}
                
        if not current_allocation:
            # If no allocation data, use default allocation based on timeline
            timeline_years = self._get_remaining_timeline(goal_data) / 12
            current_allocation = self._get_default_allocation(timeline_years)
        
        # Calculate remaining time in years
        remaining_years = self._get_remaining_timeline(goal_data) / 12
        
        # Skip if very short term goal (less than 1 year)
        if remaining_years < 1:
            return None
        
        # Current equity allocation
        current_equity = current_allocation.get("equity", 0)
        
        # Calculate recommended equity based on timeline
        # Indian market context: Typically higher equity for longer term goals
        if remaining_years > 15:
            # Long-term goal (retirement, child's higher education)
            recommended_equity = min(0.75, current_equity + 0.2)
        elif remaining_years > 7:
            # Medium to long-term goal
            recommended_equity = min(0.65, current_equity + 0.15)
        elif remaining_years > 3:
            # Medium-term goal
            recommended_equity = min(0.5, current_equity + 0.1)
        else:
            # Short-term goal (1-3 years)
            recommended_equity = min(0.3, current_equity)
        
        # Cap equity shifts to maximum allowed
        equity_shift = min(
            abs(recommended_equity - current_equity),
            self.params["max_allocation_shift"]
        )
        
        # Apply shift direction
        if recommended_equity > current_equity:
            new_equity = current_equity + equity_shift
        else:
            new_equity = current_equity - equity_shift
        
        # Ensure minimum and maximum equity allocations
        new_equity = max(self.params["min_equity_allocation"], 
                         min(self.params["max_equity_allocation"], new_equity))
        
        # If no significant change, don't recommend adjustment
        if abs(new_equity - current_equity) < 0.05:  # 5% minimum change
            return None
        
        # Create new allocation
        new_allocation = current_allocation.copy()
        
        # Adjust equity
        new_allocation["equity"] = new_equity
        
        # Adjust debt to maintain balance
        current_debt = current_allocation.get("debt", 0)
        current_gold = current_allocation.get("gold", 0)
        current_cash = current_allocation.get("cash", 0)
        
        # Ensure allocations add up to 1
        equity_change = new_equity - current_equity
        
        # Prioritize adjusting debt first, then cash, then gold
        if equity_change > 0:
            # Increase equity by reducing others
            # First reduce debt
            new_debt = max(0, current_debt - equity_change)
            debt_change = new_debt - current_debt
            
            # If debt reduction wasn't enough, reduce cash
            remaining_change = equity_change + debt_change  # debt_change is negative
            if remaining_change > 0:
                new_cash = max(0, current_cash - remaining_change)
                cash_change = new_cash - current_cash
                
                # If cash reduction wasn't enough, reduce gold
                remaining_change = remaining_change + cash_change  # cash_change is negative
                if remaining_change > 0:
                    new_gold = max(0, current_gold - remaining_change)
                else:
                    new_gold = current_gold
            else:
                new_cash = current_cash
                new_gold = current_gold
        else:
            # Decrease equity by increasing others
            # First increase debt
            new_debt = current_debt - equity_change  # equity_change is negative
            
            # Ensure gold allocation doesn't exceed cap
            new_gold = min(current_gold, self.params["gold_allocation_cap"])
            
            # Adjust cash for any remaining allocation
            total_allocated = new_equity + new_debt + new_gold
            new_cash = max(0, 1 - total_allocated)
        
        # Final adjustments to ensure total is 1
        new_allocation["debt"] = new_debt
        new_allocation["gold"] = new_gold
        new_allocation["cash"] = new_cash
        
        # Normalize to ensure total is exactly 1
        total = sum(new_allocation.values())
        if total > 0:
            for key in new_allocation:
                new_allocation[key] /= total
        
        # Calculate impact metrics
        expected_return_change = self._calculate_expected_return_change(
            current_allocation, new_allocation
        )
        
        risk_change = self._calculate_risk_change(
            current_allocation, new_allocation
        )
        
        impact_metrics = {
            "equity_change_percentage": (new_equity - current_equity) * 100,
            "expected_return_change": expected_return_change * 100,
            "risk_change": risk_change * 100,
            "estimated_goal_probability_change": self._estimate_probability_change(
                goal_data, current_allocation, new_allocation
            ) * 100
        }
        
        # Generate implementation steps
        implementation_steps = [
            f"Adjust your asset allocation from {self._format_allocation(current_allocation)} to {self._format_allocation(new_allocation)}",
            "Rebalance your portfolio gradually to achieve the new allocation",
            "Consider tax implications when selling existing investments",
            "Use new contributions to shift allocation without selling existing investments"
        ]
        
        # Add India-specific implementation steps
        goal_category = goal_data.get("category", "").lower()
        if "retirement" in goal_category:
            implementation_steps.append(
                "Consider NPS Tier II accounts for flexibility in allocation changes"
            )
        
        # Calculate tax implications
        tax_implications = {
            "capital_gains_tax": "Short-term capital gains from equity (held < 1 year) taxed at 15%",
            "exit_load_consideration": "Mutual funds may have exit loads if sold within 1 year",
            "tax_efficiency_note": "Debt funds held > 3 years qualify for LTCG with indexation benefits"
        }
        
        # India-specific notes
        india_specific_notes = [
            "Consider Balanced Advantage Funds for automatic asset allocation adjustment",
            "Use SIP Top-up facility to gradually shift allocation"
        ]
        
        if equity_change > 0:
            india_specific_notes.append(
                "Consider tax-efficient ELSS funds for equity allocation increases"
            )
        else:
            india_specific_notes.append(
                "Consider liquid or short-term debt funds for shorter time horizons"
            )
        
        # Gold allocation specific notes
        if new_allocation.get("gold", 0) > 0.05:
            india_specific_notes.append(
                "Consider Gold ETFs or Sovereign Gold Bonds over physical gold for better returns and liquidity"
            )
        
        # Calculate suitability score
        suitability_score = self._calculate_allocation_change_suitability(
            goal_category, remaining_years, equity_change, profile
        )
        
        # Create the adjustment
        return GoalAdjustment(
            goal_id=goal_data.get("id", ""),
            adjustment_type=AdjustmentType.ALLOCATION,
            adjustment_value=new_allocation,
            original_value=current_allocation,
            description=f"Adjust asset allocation to {self._format_allocation(new_allocation)}",
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps,
            tax_implications=tax_implications,
            confidence_score=0.75,  # Allocation changes have moderate-high confidence
            suitability_score=suitability_score,
            india_specific_notes=india_specific_notes
        )
    
    # Helper methods
    
    def _calculate_months_to_goal(self, target_date: datetime) -> int:
        """Calculate months remaining to goal target date"""
        now = datetime.now()
        delta = target_date - now
        return max(0, int(delta.days / 30))
    
    def _get_remaining_timeline(self, goal_data: Dict[str, Any]) -> int:
        """Get remaining timeline in months for a goal"""
        target_date_str = goal_data.get("target_date", "")
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
            return self._calculate_months_to_goal(target_date)
        except (ValueError, TypeError):
            # If target date is invalid, use timeline_months if available
            return goal_data.get("timeline_months", 60)
    
    def _calculate_adjusted_contribution(
        self,
        target_amount: float,
        current_amount: float,
        timeline_months: int,
        expected_return: float
    ) -> float:
        """Calculate required monthly contribution for given parameters"""
        # Convert annual return to monthly
        monthly_return = (1 + expected_return) ** (1/12) - 1
        
        # Future value formula: FV = PV(1+r)^n + PMT*((1+r)^n - 1)/r
        # Solving for PMT: PMT = (FV - PV(1+r)^n) * r / ((1+r)^n - 1)
        
        if monthly_return > 0 and timeline_months > 0:
            future_factor = (1 + monthly_return) ** timeline_months
            pmt = (target_amount - current_amount * future_factor) * monthly_return / (future_factor - 1)
            return max(0, pmt)
        else:
            # Simple division if no returns or immediate goal
            return max(0, (target_amount - current_amount) / max(1, timeline_months))
    
    def _calculate_monthly_impact(self, amount_change: float, goal_data: Dict[str, Any]) -> float:
        """Calculate monthly contribution impact of a target amount change"""
        timeline_months = self._get_remaining_timeline(goal_data)
        expected_return = goal_data.get("expected_return", 0.08)
        
        # Simple approximation - divide by remaining months
        if timeline_months <= 0:
            return 0
            
        # For a more accurate calculation with returns
        # Monthly return rate
        monthly_return = (1 + expected_return) ** (1/12) - 1
        
        if monthly_return > 0:
            # Calculate using future value formula
            future_factor = (1 + monthly_return) ** timeline_months
            monthly_impact = amount_change * monthly_return / (future_factor - 1)
        else:
            # Simple division if no returns
            monthly_impact = amount_change / timeline_months
            
        return monthly_impact
    
    def _extract_monthly_income(self, profile: Dict[str, Any]) -> float:
        """Extract monthly income from profile data with support for Indian currency formats"""
        # Look for direct income field
        if "income" in profile:
            income_value = profile["income"]
            if isinstance(income_value, (int, float)):
                return float(income_value)
            elif isinstance(income_value, str):
                # Handle Indian currency format
                return self._parse_indian_currency(income_value)
            return 0.0
        
        # Check for monthly_income field
        if "monthly_income" in profile:
            income_value = profile["monthly_income"]
            if isinstance(income_value, (int, float)):
                return float(income_value)
            elif isinstance(income_value, str):
                # Handle Indian currency format
                return self._parse_indian_currency(income_value)
            return 0.0
        
        # Look in answers
        if "answers" in profile:
            for answer in profile["answers"]:
                if answer.get("question_id") == "monthly_income":
                    income_value = answer.get("answer", 0)
                    if isinstance(income_value, (int, float)):
                        return float(income_value)
                    elif isinstance(income_value, str):
                        # Handle Indian currency format
                        return self._parse_indian_currency(income_value)
        
        # Default value
        return 50000  # Default assumption
        
    def _parse_indian_currency(self, value_str: str) -> float:
        """
        Parse Indian currency format (₹1,00,000 or 1,00,000 or ₹1.5L or 1.5 Cr) to float
        
        Args:
            value_str: String representation of currency value
            
        Returns:
            float: The parsed value
        """
        try:
            # Handle empty strings or None
            if not value_str:
                return 0.0
                
            # Convert to string if it's not already
            if not isinstance(value_str, str):
                return float(value_str)
                
            # Remove rupee symbol
            clean_str = value_str.replace('₹', '')
            
            # Handle lakh (L) and crore (Cr) notations - need to check before removing commas
            if 'L' in clean_str.upper():
                # Convert lakhs to regular number (1L = 100,000)
                multiplier = 100000
                # Remove spaces and commas
                clean_str = clean_str.replace(' ', '').replace(',', '')
                # Remove the L and convert
                clean_str = clean_str.upper().replace('L', '')
                return float(clean_str) * multiplier
            elif any(x in clean_str.upper() for x in ['CR', 'CRORE']):
                # Convert crores to regular number (1Cr = 10,000,000)
                multiplier = 10000000
                # Remove spaces and commas
                clean_str = clean_str.replace(' ', '').replace(',', '')
                # Remove CR or CRORE and convert
                clean_str = clean_str.upper()
                clean_str = clean_str.replace('CRORE', '').replace('CR', '')
                return float(clean_str) * multiplier
            
            # For regular numbers, remove commas and spaces
            clean_str = clean_str.replace(',', '').replace(' ', '')
            
            # Regular number
            return float(clean_str)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse currency value '{value_str}': {str(e)}")
            return 0.0
    
    def _get_default_allocation(self, timeline_years: float) -> Dict[str, float]:
        """Get default asset allocation based on timeline"""
        if timeline_years > 15:
            # Long-term goals (retirement)
            return {"equity": 0.70, "debt": 0.20, "gold": 0.05, "cash": 0.05}
        elif timeline_years > 7:
            # Medium to long-term goals (child education)
            return {"equity": 0.60, "debt": 0.30, "gold": 0.05, "cash": 0.05}
        elif timeline_years > 3:
            # Medium-term goals (home down payment)
            return {"equity": 0.40, "debt": 0.45, "gold": 0.05, "cash": 0.10}
        elif timeline_years > 1:
            # Short-term goals (1-3 years)
            return {"equity": 0.20, "debt": 0.60, "gold": 0.05, "cash": 0.15}
        else:
            # Very short-term goals (< 1 year)
            return {"equity": 0.00, "debt": 0.40, "gold": 0.00, "cash": 0.60}
    
    def _format_allocation(self, allocation: Dict[str, float]) -> str:
        """Format allocation dictionary as readable string"""
        return ", ".join([f"{k}: {v*100:.0f}%" for k, v in allocation.items() if v > 0])
    
    def _calculate_expected_return_change(
        self,
        old_allocation: Dict[str, float],
        new_allocation: Dict[str, float]
    ) -> float:
        """Calculate expected return change from allocation shift"""
        # Expected returns by asset class (annual)
        expected_returns = {
            "equity": 0.12,  # 12% for equity
            "debt": 0.07,    # 7% for debt
            "gold": 0.08,    # 8% for gold
            "cash": 0.04     # 4% for cash/liquid funds
        }
        
        # Calculate weighted returns
        old_return = sum(alloc * expected_returns.get(asset, 0) 
                        for asset, alloc in old_allocation.items())
        
        new_return = sum(alloc * expected_returns.get(asset, 0) 
                        for asset, alloc in new_allocation.items())
        
        return new_return - old_return
    
    def _calculate_risk_change(
        self,
        old_allocation: Dict[str, float],
        new_allocation: Dict[str, float]
    ) -> float:
        """Calculate risk profile change from allocation shift"""
        # Volatility (risk) factors by asset class
        volatility = {
            "equity": 0.18,  # 18% volatility for equity
            "debt": 0.06,    # 6% for debt
            "gold": 0.15,    # 15% for gold
            "cash": 0.01     # 1% for cash/liquid funds
        }
        
        # Calculate weighted volatility (simplified)
        old_risk = sum(alloc * volatility.get(asset, 0) 
                       for asset, alloc in old_allocation.items())
        
        new_risk = sum(alloc * volatility.get(asset, 0) 
                       for asset, alloc in new_allocation.items())
        
        return new_risk - old_risk
    
    def _estimate_probability_change(
        self,
        goal_data: Dict[str, Any],
        old_allocation: Dict[str, float],
        new_allocation: Dict[str, float]
    ) -> float:
        """Estimate change in goal success probability from allocation change"""
        # Get timeline in years
        timeline_years = self._get_remaining_timeline(goal_data) / 12
        
        # Get current success probability if available
        current_probability = goal_data.get("success_probability", 0.5)
        
        # Calculate expected return change
        return_change = self._calculate_expected_return_change(old_allocation, new_allocation)
        
        # Simplified model: each 1% increase in return approximately 
        # improves probability by 2-5% depending on timeline
        if timeline_years > 10:
            # Long-term goals benefit more from return increases
            probability_change = return_change * 5
        elif timeline_years > 5:
            # Medium-term goals
            probability_change = return_change * 3
        else:
            # Short-term goals benefit less
            probability_change = return_change * 2
        
        # Cap the change to reasonable bounds
        probability_change = max(-0.2, min(0.2, probability_change))
        
        # Calculate new probability
        new_probability = current_probability + probability_change
        
        # Ensure probability is between 0 and 1
        new_probability = max(0, min(1, new_probability))
        
        return new_probability - current_probability
    
    def _calculate_tax_savings(
        self,
        annual_contribution: float,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> float:
        """Calculate potential tax savings from increased contributions"""
        goal_category = goal_data.get("category", "").lower()
        
        # Default tax rate - assume 30% tax bracket
        tax_rate = profile.get("tax_rate", 0.30)
        
        # Check if goal qualifies for tax benefits
        if "retirement" in goal_category:
            # Retirement savings - Section 80C and 80CCD benefits
            section_80c_limit = self.params["section_80c_limit"]
            nps_limit = self.params["nps_tax_benefit_limit"]
            
            # Estimate current tax-saving investments
            current_80c = profile.get("80c_investments", 0)
            
            # Calculate available Section 80C room
            available_80c = max(0, section_80c_limit - current_80c)
            
            # Calculate tax savings
            tax_savings = min(available_80c, annual_contribution) * tax_rate
            
            # Add NPS benefits if applicable
            if "nps" in goal_data.get("investment_vehicle", "").lower():
                tax_savings += min(nps_limit, max(0, annual_contribution - available_80c)) * tax_rate
            
            return tax_savings
            
        elif "education" in goal_category and "girl" in goal_data.get("description", "").lower():
            # Sukanya Samriddhi Yojana for girl child education - Section 80C
            section_80c_limit = self.params["section_80c_limit"]
            current_80c = profile.get("80c_investments", 0)
            available_80c = max(0, section_80c_limit - current_80c)
            
            return min(available_80c, annual_contribution) * tax_rate
            
        elif "home" in goal_category:
            # Home loan principal repayment - Section 80C
            section_80c_limit = self.params["section_80c_limit"]
            current_80c = profile.get("80c_investments", 0)
            available_80c = max(0, section_80c_limit - current_80c)
            
            return min(available_80c, annual_contribution) * tax_rate
        
        # No tax savings for other goal types
        return 0
    
    def _calculate_contribution_tax_implications(
        self,
        monthly_increase: float,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> Dict[str, str]:
        """Calculate detailed tax implications for contribution increases"""
        annual_increase = monthly_increase * 12
        goal_category = goal_data.get("category", "").lower()
        
        tax_implications = {
            "direct_tax_impact": "No direct tax benefits",
            "potential_strategies": []
        }
        
        # Retirement-related goals
        if "retirement" in goal_category:
            tax_implications["direct_tax_impact"] = (
                f"Potential Section 80C deduction for EPF/PPF/NPS contributions up to ₹{self.params['section_80c_limit']:,.0f}"
            )
            tax_implications["potential_strategies"] = [
                f"Additional NPS investment can give extra ₹{self.params['nps_tax_benefit_limit']:,.0f} deduction under 80CCD(1B)",
                "Employer NPS contributions (up to 10% of salary) eligible for deduction under 80CCD(2)"
            ]
        
        # Education-related goals
        elif "education" in goal_category:
            tax_implications["direct_tax_impact"] = (
                "Potential Section 80C deduction if investing in Sukanya Samriddhi Yojana for girl child"
            )
            tax_implications["potential_strategies"] = [
                "Education loan interest is deductible under Section 80E (no upper limit)",
                "Consider tax-free bonds for education corpus building"
            ]
        
        # Home-related goals
        elif "home" in goal_category:
            tax_implications["direct_tax_impact"] = (
                "Home loan principal repayment eligible for Section 80C deduction"
            )
            tax_implications["potential_strategies"] = [
                "Home loan interest deductible up to ₹2,00,000 under Section 24",
                "Additional ₹50,000 deduction for first-time home buyers under Section 80EE",
                "PMAY subsidy may be available for affordable housing"
            ]
        
        # Generic tax implications for investments
        else:
            tax_implications["potential_strategies"] = [
                "Consider ELSS mutual funds for tax-saving along with goal investing (3-year lock-in)",
                "Debt fund gains held >3 years taxed at 20% with indexation benefits",
                "Equity investments held >1 year enjoy LTCG taxation at 10% above ₹1 lakh"
            ]
        
        return tax_implications
    
    # Suitability scoring methods
    
    def _calculate_target_reduction_suitability(
        self,
        goal_category: str,
        reduction_percentage: float,
        profile: Dict[str, Any]
    ) -> float:
        """Calculate suitability score for target reduction adjustment"""
        # Base suitability score
        suitability = 0.5
        
        # Adjust based on goal category
        goal_category = goal_category.lower()
        
        # Some goals are culturally significant in India and less suitable for reduction
        if "wedding" in goal_category or "marriage" in goal_category:
            # Weddings are culturally significant in India
            suitability -= 0.15
        elif "higher_education" in goal_category or "education" in goal_category:
            # Education is highly valued in Indian culture
            suitability -= 0.1
        elif "pilgrimage" in goal_category or "religious" in goal_category:
            # Religious goals are culturally significant
            suitability -= 0.15
        elif "emergency" in goal_category:
            # Emergency funds shouldn't be reduced
            suitability -= 0.2
        elif "retirement" in goal_category:
            # Retirement funds need to be adequate
            suitability -= 0.05
        elif "luxury" in goal_category or "vacation" in goal_category:
            # Discretionary goals are more suitable for reduction
            suitability += 0.15
        
        # Adjust based on reduction percentage
        if reduction_percentage < 0.1:
            # Small reductions are more suitable
            suitability += 0.1
        elif reduction_percentage > 0.25:
            # Large reductions are less suitable
            suitability -= 0.15
        
        # Adjust based on profile risk tolerance
        risk_tolerance = profile.get("risk_tolerance", "moderate").lower()
        if "conservative" in risk_tolerance:
            # Conservative investors may prefer target reduction over other adjustments
            suitability += 0.05
        elif "aggressive" in risk_tolerance:
            # Aggressive investors may prefer other strategies
            suitability -= 0.05
        
        # Ensure suitability is between 0 and 1
        return max(0.1, min(0.9, suitability))
    
    def _calculate_timeframe_extension_suitability(
        self,
        goal_category: str,
        extension_months: int,
        profile: Dict[str, Any]
    ) -> float:
        """Calculate suitability score for timeframe extension adjustment"""
        # Base suitability score
        suitability = 0.6
        
        # Adjust based on goal category
        goal_category = goal_category.lower()
        
        # Some goals have natural deadlines and are less suitable for extension
        if "education" in goal_category:
            # Education has natural deadlines
            suitability -= 0.15
        elif "wedding" in goal_category and extension_months > 12:
            # Wedding dates can typically be extended, but not too much
            suitability -= 0.1
        elif "emergency" in goal_category:
            # Emergency funds shouldn't be delayed
            suitability -= 0.25
        elif "retirement" in goal_category:
            # Retirement can often be delayed (within limits)
            suitability += 0.1
        elif "home" in goal_category or "house" in goal_category:
            # Home purchase can often be delayed
            suitability += 0.05
        
        # Adjust based on extension length
        if extension_months < 6:
            # Small extensions are more suitable
            suitability += 0.1
        elif extension_months > 24:
            # Long extensions are less suitable
            suitability -= 0.15
        
        # Adjust based on age
        age = profile.get("age", 35)
        if age > 50 and "retirement" in goal_category:
            # Retirement extensions less suitable for older people
            suitability -= 0.2
        elif age < 30:
            # Younger people have more flexibility
            suitability += 0.05
        
        # Ensure suitability is between 0 and 1
        return max(0.1, min(0.9, suitability))
    
    def _calculate_contribution_increase_suitability(
        self,
        goal_category: str,
        increase_amount: float,
        monthly_income: float,
        profile: Dict[str, Any]
    ) -> float:
        """Calculate suitability score for contribution increase adjustment"""
        # Base suitability score
        suitability = 0.7
        
        # Calculate increase as percentage of income
        income_percentage = (increase_amount / monthly_income) if monthly_income > 0 else 0
        
        # Adjust based on percentage of income
        if income_percentage > 0.15:
            # Large increases are less suitable
            suitability -= 0.2
        elif income_percentage < 0.05:
            # Small increases are more suitable
            suitability += 0.1
        
        # Adjust based on goal category
        goal_category = goal_category.lower()
        
        if "retirement" in goal_category:
            # Retirement contributions have tax benefits
            suitability += 0.1
        elif "emergency" in goal_category:
            # Emergency funds are high priority
            suitability += 0.15
        
        # Adjust based on current expenses and savings rate
        expenses = profile.get("monthly_expenses", monthly_income * 0.7)  # Default to 70% of income
        current_savings = monthly_income - expenses
        savings_rate = current_savings / monthly_income if monthly_income > 0 else 0
        
        if savings_rate > 0.3:
            # Already saving a lot, may be difficult to save more
            suitability -= 0.1
        elif savings_rate < 0.1:
            # Low savings rate, may indicate limited ability to increase
            suitability -= 0.15
        
        # Adjust based on lifecycle stage
        lifecycle_stage = profile.get("lifecycle_stage", "").lower()
        
        if "peak_earning" in lifecycle_stage:
            # Peak earning years are good for increasing contributions
            suitability += 0.1
        elif "early_career" in lifecycle_stage:
            # Early career may have limited income but good growth potential
            suitability -= 0.05
        elif "pre_retirement" in lifecycle_stage:
            # Pre-retirement is a good time to boost retirement savings
            suitability += 0.15
        
        # Ensure suitability is between 0 and 1
        return max(0.1, min(0.9, suitability))
    
    def _calculate_allocation_change_suitability(
        self,
        goal_category: str,
        timeline_years: float,
        equity_change: float,
        profile: Dict[str, Any]
    ) -> float:
        """Calculate suitability score for allocation change adjustment"""
        # Base suitability score
        suitability = 0.6
        
        # Adjust based on timeline
        if timeline_years < 2 and equity_change > 0:
            # Increasing equity for short-term goals is less suitable
            suitability -= 0.2
        elif timeline_years > 10 and equity_change > 0:
            # Increasing equity for long-term goals is more suitable
            suitability += 0.15
        
        # Adjust based on risk tolerance
        risk_tolerance = profile.get("risk_tolerance", "moderate").lower()
        
        if "conservative" in risk_tolerance and equity_change > 0:
            # Increasing equity for conservative investors is less suitable
            suitability -= 0.15
        elif "aggressive" in risk_tolerance and equity_change > 0:
            # Increasing equity for aggressive investors is more suitable
            suitability += 0.1
        elif "aggressive" in risk_tolerance and equity_change < 0:
            # Decreasing equity for aggressive investors is less suitable
            suitability -= 0.1
        
        # Adjust based on goal category
        goal_category = goal_category.lower()
        
        if "retirement" in goal_category and timeline_years > 10:
            # Long-term retirement goals benefit from proper allocation
            suitability += 0.1
        elif "emergency" in goal_category and equity_change > 0:
            # Emergency funds should not have high equity
            suitability -= 0.25
        
        # Adjust based on market conditions (simplified)
        # In a real implementation, this would use market indicators
        market_condition = profile.get("market_condition", "normal").lower()
        
        if "bull" in market_condition and equity_change > 0:
            # Increasing equity in bull markets is less suitable (buying high)
            suitability -= 0.1
        elif "bear" in market_condition and equity_change > 0:
            # Increasing equity in bear markets can be suitable (buying low)
            suitability += 0.1
        
        # Ensure suitability is between 0 and 1
        return max(0.1, min(0.9, suitability))


# Flexible Goal-Type Adjustment Framework

from abc import ABC, abstractmethod
import importlib
import inspect
import json
import os
import sys


class BaseGoalTypeAdjuster(ABC):
    """
    Abstract base class for goal type-specific adjustment strategies.
    
    This class defines the standard interface that all goal type adjusters must
    implement and provides common utility methods for adjustment calculations.
    """
    
    def __init__(self, param_service=None):
        """
        Initialize the goal type adjuster with financial parameters.
        
        Args:
            param_service: Optional financial parameter service instance.
                          If not provided, will attempt to get one.
        """
        # Get parameter service if not provided
        self.param_service = param_service
        
        # Only try to get service if explicitly None (for test patching)
        if self.param_service is None:
            self.param_service = get_financial_parameter_service()
        
        # Default parameters - each adjuster can override with type-specific values
        self.params = {}
        
        # Load type-specific parameters
        self._load_type_specific_parameters()
    
    def _load_type_specific_parameters(self):
        """Load parameters specific to this goal type adjuster"""
        if self.param_service:
            try:
                # Get adjuster type name (lowercase)
                adjuster_type = self.__class__.__name__.lower()
                if adjuster_type.endswith('adjuster'):
                    adjuster_type = adjuster_type[:-8]  # Remove 'adjuster' suffix
                
                # Try to load parameters for this specific adjuster type
                prefix = f"goal_adjustment.{adjuster_type}."
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    params = self.param_service.get_parameters_by_prefix(prefix)
                    if params:
                        self.params.update(params)
            except Exception as e:
                logger.warning(f"Error loading type-specific parameters: {e}")
    
    @abstractmethod
    def get_adjustment_strategies(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available adjustment strategies for this goal type.
        
        Returns:
            Dictionary mapping strategy names to their configuration details
        """
        pass
    
    @abstractmethod
    def execute_strategy(
        self, 
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        strategy_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[GoalAdjustment]:
        """
        Execute a specific adjustment strategy for a goal.
        
        Args:
            goal_data: Complete goal data including current parameters
            profile: User profile with financial information
            strategy_name: Name of the strategy to execute
            parameters: Optional parameters to customize the strategy execution
            
        Returns:
            Goal adjustment result or None if strategy cannot be applied
        """
        pass
    
    @abstractmethod
    def evaluate_adjustment(
        self,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        adjustment: GoalAdjustment
    ) -> Dict[str, Any]:
        """
        Evaluate the impact and suitability of an adjustment.
        
        Args:
            goal_data: Complete goal data including current parameters
            profile: User profile with financial information
            adjustment: The adjustment to evaluate
            
        Returns:
            Evaluation metrics including suitability, impact scores, etc.
        """
        pass
    
    def estimate_strategy_impact(
        self,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        strategy_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimate the impact of applying a strategy without actually executing it.
        
        Args:
            goal_data: Complete goal data including current parameters
            profile: User profile with financial information
            strategy_name: Name of the strategy to estimate
            parameters: Optional parameters to customize the strategy
            
        Returns:
            Estimated impact metrics without creating an actual adjustment
        """
        # Execute the strategy to get the adjustment
        adjustment = self.execute_strategy(goal_data, profile, strategy_name, parameters)
        
        if adjustment:
            # Return the impact metrics from the adjustment
            return {
                "strategy_name": strategy_name,
                "impact_metrics": adjustment.impact_metrics,
                "suitability_score": adjustment.suitability_score,
                "confidence_score": adjustment.confidence_score
            }
        else:
            return {
                "strategy_name": strategy_name,
                "impact_metrics": {},
                "suitability_score": 0.0,
                "confidence_score": 0.0,
                "error": "Strategy could not be applied to this goal"
            }
    
    # Common utility methods that can be used by subclasses
    
    def calculate_monthly_impact(self, amount_change: float, goal_data: Dict[str, Any]) -> float:
        """Calculate monthly contribution impact of an amount change"""
        timeline_months = self._get_remaining_timeline(goal_data)
        expected_return = goal_data.get("expected_return", 0.08)
        
        # Simple approximation - divide by remaining months
        if timeline_months <= 0:
            return 0
            
        # For a more accurate calculation with returns
        # Monthly return rate
        monthly_return = (1 + expected_return) ** (1/12) - 1
        
        if monthly_return > 0:
            # Calculate using future value formula
            future_factor = (1 + monthly_return) ** timeline_months
            monthly_impact = amount_change * monthly_return / (future_factor - 1)
        else:
            # Simple division if no returns
            monthly_impact = amount_change / timeline_months
            
        return monthly_impact
    
    def calculate_adjusted_contribution(
        self,
        target_amount: float,
        current_amount: float,
        timeline_months: int,
        expected_return: float
    ) -> float:
        """Calculate required monthly contribution for given parameters"""
        # Convert annual return to monthly
        monthly_return = (1 + expected_return) ** (1/12) - 1
        
        # Future value formula: FV = PV(1+r)^n + PMT*((1+r)^n - 1)/r
        # Solving for PMT: PMT = (FV - PV(1+r)^n) * r / ((1+r)^n - 1)
        
        if monthly_return > 0 and timeline_months > 0:
            future_factor = (1 + monthly_return) ** timeline_months
            pmt = (target_amount - current_amount * future_factor) * monthly_return / (future_factor - 1)
            return max(0, pmt)
        else:
            # Simple division if no returns or immediate goal
            return max(0, (target_amount - current_amount) / max(1, timeline_months))
    
    def _get_remaining_timeline(self, goal_data: Dict[str, Any]) -> int:
        """Get remaining timeline in months for a goal"""
        target_date_str = goal_data.get("target_date", "")
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
            now = datetime.now()
            delta = target_date - now
            return max(0, int(delta.days / 30))
        except (ValueError, TypeError):
            # If target date is invalid, use timeline_months if available
            return goal_data.get("timeline_months", 60)
    
    @classmethod
    def get_adjuster_for_goal(cls, goal_data: Dict[str, Any]) -> 'BaseGoalTypeAdjuster':
        """
        Factory method to get the appropriate adjuster for a goal.
        
        Args:
            goal_data: Goal data containing category and other information
            
        Returns:
            An instance of the appropriate goal type adjuster
        """
        # This is a convenience method that delegates to the factory
        return GoalTypeAdjusterFactory.create_adjuster(goal_data)


class StrategyConfigurationManager:
    """
    Manages the loading, validation, and registration of adjustment strategies.
    
    This class provides a flexible system for loading strategy configurations
    from external sources and making them available to adjustment classes.
    """
    
    # Default configurations by strategy type
    DEFAULT_CONFIGURATIONS = {
        "target_amount": {
            "reduction": {
                "description": "Reduces the target amount to make the goal more achievable",
                "parameters": {
                    "max_reduction_percentage": 0.30,
                    "min_reduction_percentage": 0.05
                },
                "applicability": {
                    "excluded_categories": ["emergency_fund"],
                    "min_timeline_months": 0,
                    "max_timeline_months": None
                }
            }
        },
        "timeframe": {
            "extension": {
                "description": "Extends the goal timeline to allow more time for saving",
                "parameters": {
                    "max_extension_months": 60,
                    "min_extension_months": 3
                },
                "applicability": {
                    "excluded_categories": ["emergency_fund"],
                    "fixed_deadline_compatible": False
                }
            }
        },
        "contribution": {
            "increase": {
                "description": "Increases monthly contributions to meet the goal target",
                "parameters": {
                    "max_income_percentage": 0.20,
                    "min_meaningful_increase": 1000
                },
                "applicability": {
                    "excluded_categories": [],
                    "income_requirement": True
                }
            }
        },
        "allocation": {
            "equity_adjustment": {
                "description": "Adjusts equity allocation based on goal timeline and risk profile",
                "parameters": {
                    "max_shift_percentage": 0.20,
                    "min_equity_allocation": 0.20,
                    "max_equity_allocation": 0.80
                },
                "applicability": {
                    "excluded_categories": ["emergency_fund"],
                    "min_timeline_months": 12
                }
            }
        }
    }
    
    def __init__(self):
        """Initialize the strategy configuration manager."""
        # Strategy configurations by type and name
        self.configurations = {}
        # Load default configurations
        self.configurations = self.DEFAULT_CONFIGURATIONS.copy()
    
    def load_adjustment_strategies(self, source: Union[str, Dict[str, Any]]) -> bool:
        """
        Load strategies from an external source (file or dictionary).
        
        Args:
            source: Either a file path or a dictionary containing strategy configurations
            
        Returns:
            True if loading succeeded, False otherwise
        """
        try:
            # Load from file if source is a string
            if isinstance(source, str):
                if not os.path.exists(source):
                    logger.error(f"Strategy configuration file not found: {source}")
                    return False
                
                with open(source, 'r') as f:
                    config_data = json.load(f)
            else:
                config_data = source
            
            # Validate the configuration
            if not self.validate_strategy_configuration(config_data):
                logger.error("Invalid strategy configuration format")
                return False
            
            # Update configurations with loaded data
            for strategy_type, strategies in config_data.items():
                if strategy_type not in self.configurations:
                    self.configurations[strategy_type] = {}
                    
                for strategy_name, strategy_config in strategies.items():
                    self.configurations[strategy_type][strategy_name] = strategy_config
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading adjustment strategies: {e}")
            return False
    
    def register_custom_strategy(self, goal_type: str, strategy_info: Dict[str, Any]) -> bool:
        """
        Register a custom strategy at runtime.
        
        Args:
            goal_type: The goal type (e.g., "retirement", "education")
            strategy_info: Configuration for the strategy
            
        Returns:
            True if registration succeeded, False otherwise
        """
        try:
            # Validate the strategy info
            if not self._validate_strategy_info(strategy_info):
                logger.error("Invalid strategy information format")
                return False
            
            strategy_type = strategy_info.get("type")
            strategy_name = strategy_info.get("name")
            
            # Ensure strategy type exists in configurations
            if strategy_type not in self.configurations:
                self.configurations[strategy_type] = {}
            
            # Add or update the strategy
            self.configurations[strategy_type][strategy_name] = strategy_info.get("configuration", {})
            
            # Add goal type specific override if provided
            if "goal_type_configuration" in strategy_info:
                # Create goal type specific section if it doesn't exist
                if "goal_type_overrides" not in self.configurations[strategy_type][strategy_name]:
                    self.configurations[strategy_type][strategy_name]["goal_type_overrides"] = {}
                
                # Add the override
                self.configurations[strategy_type][strategy_name]["goal_type_overrides"][goal_type] = \
                    strategy_info["goal_type_configuration"]
            
            return True
            
        except Exception as e:
            logger.error(f"Error registering custom strategy: {e}")
            return False
    
    def validate_strategy_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Validate a strategy configuration for format and required fields.
        
        Args:
            config: The configuration to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        if not isinstance(config, dict):
            return False
        
        for strategy_type, strategies in config.items():
            # Strategy type should be a string
            if not isinstance(strategy_type, str):
                logger.error(f"Strategy type must be a string, got {type(strategy_type)}")
                return False
            
            # Strategies should be a dictionary
            if not isinstance(strategies, dict):
                logger.error(f"Strategies for {strategy_type} must be a dictionary")
                return False
            
            # Validate each strategy
            for strategy_name, strategy_config in strategies.items():
                if not isinstance(strategy_name, str):
                    logger.error(f"Strategy name must be a string, got {type(strategy_name)}")
                    return False
                
                if not isinstance(strategy_config, dict):
                    logger.error(f"Strategy config for {strategy_name} must be a dictionary")
                    return False
                
                # Check for required fields
                if "description" not in strategy_config:
                    logger.error(f"Missing description for strategy {strategy_name}")
                    return False
                
                if "parameters" not in strategy_config:
                    logger.error(f"Missing parameters for strategy {strategy_name}")
                    return False
                
                if "applicability" not in strategy_config:
                    logger.error(f"Missing applicability rules for strategy {strategy_name}")
                    return False
        
        return True
    
    def _validate_strategy_info(self, strategy_info: Dict[str, Any]) -> bool:
        """Validate a strategy registration info structure"""
        required_fields = ["type", "name", "configuration"]
        
        for field in required_fields:
            if field not in strategy_info:
                logger.error(f"Missing required field '{field}' in strategy info")
                return False
        
        # The configuration should have the same structure as in validate_strategy_configuration
        strategy_config = strategy_info.get("configuration", {})
        if not isinstance(strategy_config, dict):
            logger.error("Strategy configuration must be a dictionary")
            return False
        
        if "description" not in strategy_config:
            logger.error("Missing description in strategy configuration")
            return False
        
        if "parameters" not in strategy_config:
            logger.error("Missing parameters in strategy configuration")
            return False
        
        if "applicability" not in strategy_config:
            logger.error("Missing applicability rules in strategy configuration")
            return False
        
        return True
    
    def get_strategy_configuration(
        self,
        strategy_type: str,
        strategy_name: str,
        goal_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific strategy, with optional goal-type overrides.
        
        Args:
            strategy_type: The type of strategy (e.g., "target_amount", "timeframe")
            strategy_name: The name of the strategy (e.g., "reduction", "extension")
            goal_type: Optional goal type to check for overrides
            
        Returns:
            Strategy configuration or None if not found
        """
        if strategy_type not in self.configurations:
            return None
            
        if strategy_name not in self.configurations[strategy_type]:
            return None
        
        # Get the base configuration
        config = self.configurations[strategy_type][strategy_name].copy()
        
        # Apply goal type overrides if available
        if goal_type and "goal_type_overrides" in config and goal_type in config["goal_type_overrides"]:
            # Deep merge the override into the base config
            override = config["goal_type_overrides"][goal_type]
            
            for key, value in override.items():
                if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                    # Merge dictionaries
                    config[key].update(value)
                else:
                    # Override with new value
                    config[key] = value
        
        return config


class GoalTypeAdjusterFactory:
    """
    Factory class for creating goal type-specific adjusters.
    
    This class manages the registration and creation of adjusters for different
    goal types, allowing for runtime extension with custom adjusters.
    """
    
    # Registry of adjuster classes by goal type
    _adjuster_registry: Dict[str, Type[BaseGoalTypeAdjuster]] = {}
    
    # Strategy configuration manager instance
    _strategy_manager: Optional[StrategyConfigurationManager] = None
    
    @classmethod
    def register_adjuster(cls, goal_type: str, adjuster_class: Type[BaseGoalTypeAdjuster]) -> None:
        """
        Register an adjuster class for a specific goal type.
        
        Args:
            goal_type: The goal type to register the adjuster for
            adjuster_class: The adjuster class to register
        """
        cls._adjuster_registry[goal_type.lower()] = adjuster_class
    
    @classmethod
    def create_adjuster(cls, goal_data: Dict[str, Any], profile: Optional[Dict[str, Any]] = None) -> BaseGoalTypeAdjuster:
        """
        Create an appropriate adjuster instance for the given goal.
        
        Args:
            goal_data: Goal data including category and other information
            profile: Optional user profile data
            
        Returns:
            An instance of the appropriate goal type adjuster
        """
        goal_category = goal_data.get("category", "").lower()
        
        # Try to find a specific adjuster for this goal category
        adjuster_class = cls._adjuster_registry.get(goal_category)
        
        # If no specific adjuster, use the default adjuster
        if adjuster_class is None:
            # Look for a general adjuster
            adjuster_class = cls._adjuster_registry.get("default")
            
            # If still no adjuster, log an error and use a fallback
            if adjuster_class is None:
                logger.warning(f"No adjuster found for goal category: {goal_category}")
                # We'll define this class later in the module
                adjuster_class = DefaultGoalTypeAdjuster
        
        # Create and return the adjuster instance
        return adjuster_class()
    
    @classmethod
    def get_adjustment_strategies(cls, goal_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Get available adjustment strategies for a specific goal type.
        
        Args:
            goal_type: The goal type to get strategies for
            
        Returns:
            Dictionary of available strategies by type
        """
        # Get the strategy manager
        strategy_manager = cls._get_strategy_manager()
        
        # Collect strategies from all types that are applicable to this goal type
        strategies = {}
        
        for strategy_type, type_strategies in strategy_manager.configurations.items():
            strategies[strategy_type] = {}
            
            for strategy_name, strategy_config in type_strategies.items():
                # Check if strategy is applicable to this goal type
                applicability = strategy_config.get("applicability", {})
                excluded_categories = applicability.get("excluded_categories", [])
                
                if goal_type.lower() not in [cat.lower() for cat in excluded_categories]:
                    # Strategy is applicable, get configuration with potential overrides
                    config = strategy_manager.get_strategy_configuration(
                        strategy_type, strategy_name, goal_type
                    )
                    if config:
                        strategies[strategy_type][strategy_name] = config
        
        return strategies
    
    @classmethod
    def support_custom_adjusters(cls, extension_path: str) -> int:
        """
        Load and register custom adjuster classes from an extension path.
        
        Args:
            extension_path: Path to the directory containing adjuster extensions
            
        Returns:
            Number of adjusters successfully loaded
        """
        if not os.path.exists(extension_path) or not os.path.isdir(extension_path):
            logger.error(f"Extension path does not exist or is not a directory: {extension_path}")
            return 0
        
        # Add extension path to sys.path to allow importing
        if extension_path not in sys.path:
            sys.path.append(extension_path)
        
        # Track how many adjusters we loaded
        loaded_count = 0
        
        # Look for Python files in the extension path
        for filename in os.listdir(extension_path):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Import the module
                    module = importlib.import_module(module_name)
                    
                    # Find adjuster classes in the module
                    for item_name in dir(module):
                        item = getattr(module, item_name)
                        
                        # Check if it's a class that inherits from BaseGoalTypeAdjuster
                        if (inspect.isclass(item) 
                                and issubclass(item, BaseGoalTypeAdjuster) 
                                and item is not BaseGoalTypeAdjuster):
                            
                            # Look for goal type information
                            if hasattr(item, 'GOAL_TYPES'):
                                goal_types = item.GOAL_TYPES
                                if isinstance(goal_types, str):
                                    goal_types = [goal_types]
                                
                                # Register the adjuster for each goal type
                                for goal_type in goal_types:
                                    cls.register_adjuster(goal_type, item)
                                    loaded_count += 1
                                    logger.info(f"Registered adjuster {item.__name__} for goal type {goal_type}")
                
                except Exception as e:
                    logger.error(f"Error loading adjuster from {filename}: {e}")
        
        return loaded_count
    
    @classmethod
    def _get_strategy_manager(cls) -> StrategyConfigurationManager:
        """Get or create the strategy configuration manager"""
        if cls._strategy_manager is None:
            cls._strategy_manager = StrategyConfigurationManager()
        return cls._strategy_manager


class AdjustmentStrategyExecutor:
    """
    Executes adjustment strategies with parameter optimization and combination.
    
    This class provides methods to execute adjustment strategies, estimate their
    impact, combine multiple strategies, and optimize strategy parameters.
    """
    
    def __init__(self, factory: Optional[GoalTypeAdjusterFactory] = None):
        """
        Initialize the strategy executor.
        
        Args:
            factory: Optional factory to use for creating adjusters
        """
        self.factory = factory or GoalTypeAdjusterFactory
    
    def execute_adjustment_strategy(
        self,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        strategy_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[GoalAdjustment]:
        """
        Execute a named adjustment strategy for a goal.
        
        Args:
            goal_data: Goal data including category and other information
            profile: User profile data
            strategy_name: Name of the strategy to execute
            parameters: Optional parameters to customize the strategy
            
        Returns:
            Goal adjustment result or None if strategy cannot be applied
        """
        # Parse strategy name (format: type:name, e.g., "target_amount:reduction")
        if ":" in strategy_name:
            strategy_type, strategy_name = strategy_name.split(":", 1)
        else:
            # Default to contribution strategy if not specified
            strategy_type = "contribution"
        
        # Get the appropriate adjuster for this goal
        adjuster = self.factory.create_adjuster(goal_data, profile)
        
        # Get available strategies for this adjuster
        strategies = adjuster.get_adjustment_strategies()
        
        # Check if the requested strategy exists
        if strategy_type not in strategies or strategy_name not in strategies[strategy_type]:
            logger.error(f"Strategy {strategy_type}:{strategy_name} not found for goal type {goal_data.get('category')}")
            return None
        
        # Execute the strategy
        return adjuster.execute_strategy(goal_data, profile, strategy_name, parameters)
    
    def estimate_strategy_impact(
        self,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        strategy_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimate the impact of a strategy without executing it.
        
        Args:
            goal_data: Goal data including category and other information
            profile: User profile data
            strategy_name: Name of the strategy to estimate
            parameters: Optional parameters to customize the strategy
            
        Returns:
            Impact metrics dictionary
        """
        # Get the appropriate adjuster for this goal
        adjuster = self.factory.create_adjuster(goal_data, profile)
        
        # Parse strategy name
        if ":" in strategy_name:
            strategy_type, strategy_name = strategy_name.split(":", 1)
        else:
            strategy_type = "contribution"
        
        # Return the estimated impact
        return adjuster.estimate_strategy_impact(
            goal_data, profile, strategy_name, parameters
        )
    
    def combine_strategies(
        self,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        strategies: List[Tuple[str, Optional[Dict[str, Any]]]]
    ) -> Dict[str, Any]:
        """
        Apply multiple adjustment strategies and combine their results.
        
        Args:
            goal_data: Goal data including category and other information
            profile: User profile data
            strategies: List of (strategy_name, parameters) tuples to apply
            
        Returns:
            Combined results including all adjustments and their impact
        """
        results = []
        combined_impact = {}
        modified_goal = goal_data.copy()
        
        for strategy_name, parameters in strategies:
            # Execute the strategy on the progressively modified goal
            adjustment = self.execute_adjustment_strategy(
                modified_goal, profile, strategy_name, parameters
            )
            
            if adjustment:
                results.append(adjustment)
                
                # Apply the adjustment to the goal data for the next strategy
                self._apply_adjustment_to_goal(modified_goal, adjustment)
                
                # Combine impact metrics
                for key, value in adjustment.impact_metrics.items():
                    combined_impact[f"{strategy_name}.{key}"] = value
        
        return {
            "adjustments": [adj.to_dict() for adj in results],
            "combined_impact": combined_impact,
            "modified_goal": modified_goal
        }
    
    def optimize_strategy_parameters(
        self,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        strategy_name: str,
        constraints: Dict[str, Any],
        optimization_metric: str = "suitability_score",
        steps: int = 5
    ) -> Dict[str, Any]:
        """
        Find optimal parameters for a strategy based on constraints.
        
        Args:
            goal_data: Goal data including category and other information
            profile: User profile data
            strategy_name: Name of the strategy to optimize
            constraints: Constraints for parameter optimization
            optimization_metric: Metric to optimize (default: suitability_score)
            steps: Number of optimization steps to perform
            
        Returns:
            Optimized parameters and resulting adjustment
        """
        # Parse strategy name
        if ":" in strategy_name:
            strategy_type, strategy_name = strategy_name.split(":", 1)
        else:
            strategy_type = "contribution"
        
        # Get the appropriate adjuster
        adjuster = self.factory.create_adjuster(goal_data, profile)
        
        # Get the strategy configuration
        strategies = adjuster.get_adjustment_strategies()
        if strategy_type not in strategies or strategy_name not in strategies[strategy_type]:
            logger.error(f"Strategy {strategy_type}:{strategy_name} not found for optimization")
            return {"error": "Strategy not found"}
        
        strategy_config = strategies[strategy_type][strategy_name]
        
        # Get the parameters to optimize
        parameters = strategy_config.get("parameters", {})
        
        # Define the parameter search space based on constraints
        search_space = {}
        for param_name, param_value in parameters.items():
            if param_name in constraints:
                param_constraints = constraints[param_name]
                
                if isinstance(param_constraints, dict):
                    min_val = param_constraints.get("min", param_value * 0.5)
                    max_val = param_constraints.get("max", param_value * 1.5)
                    
                    # Create evenly spaced values for this parameter
                    search_space[param_name] = [
                        min_val + i * (max_val - min_val) / (steps - 1)
                        for i in range(steps)
                    ]
                else:
                    # Use the constraint value directly
                    search_space[param_name] = [param_constraints]
            else:
                # Use the default value
                search_space[param_name] = [param_value]
        
        # Generate parameter combinations
        def generate_combinations(params, current=None, idx=0):
            if current is None:
                current = {}
            
            if idx >= len(params.keys()):
                return [current.copy()]
            
            param_name = list(params.keys())[idx]
            param_values = params[param_name]
            
            combinations = []
            for value in param_values:
                current[param_name] = value
                combinations.extend(generate_combinations(params, current, idx + 1))
            
            return combinations
        
        parameter_combinations = generate_combinations(search_space)
        
        # Test each combination and find the optimal one
        best_score = -1
        best_params = None
        best_adjustment = None
        
        for params in parameter_combinations:
            # Execute the strategy with these parameters
            adjustment = self.execute_adjustment_strategy(
                goal_data, profile, f"{strategy_type}:{strategy_name}", params
            )
            
            if adjustment:
                # Get the optimization metric value
                if optimization_metric == "suitability_score":
                    score = adjustment.suitability_score
                elif optimization_metric == "confidence_score":
                    score = adjustment.confidence_score
                elif optimization_metric in adjustment.impact_metrics:
                    score = adjustment.impact_metrics[optimization_metric]
                else:
                    # Default to suitability if metric not found
                    score = adjustment.suitability_score
                
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_adjustment = adjustment
        
        if best_params is None:
            return {"error": "No valid parameter combination found"}
        
        return {
            "optimized_parameters": best_params,
            "optimization_score": best_score,
            "adjustment": best_adjustment.to_dict() if best_adjustment else None
        }
    
    def _apply_adjustment_to_goal(self, goal_data: Dict[str, Any], adjustment: GoalAdjustment) -> None:
        """
        Apply an adjustment to modify goal data for subsequent strategies.
        
        Args:
            goal_data: Goal data to modify
            adjustment: Adjustment to apply
        """
        # Apply based on adjustment type
        if adjustment.adjustment_type == AdjustmentType.TARGET_AMOUNT:
            goal_data["target_amount"] = adjustment.adjustment_value
        
        elif adjustment.adjustment_type == AdjustmentType.TIMEFRAME:
            # Update timeline months
            if "timeline_months" in goal_data:
                goal_data["timeline_months"] = adjustment.adjustment_value
            
            # Update target date if present
            if "target_date" in goal_data:
                try:
                    current_date = datetime.strptime(goal_data["target_date"], "%Y-%m-%d")
                    extension_months = adjustment.adjustment_value - adjustment.original_value
                    new_date = current_date + timedelta(days=extension_months * 30)
                    goal_data["target_date"] = new_date.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    # If date parsing fails, leave target_date unchanged
                    pass
        
        elif adjustment.adjustment_type == AdjustmentType.CONTRIBUTION:
            goal_data["monthly_contribution"] = adjustment.adjustment_value
        
        elif adjustment.adjustment_type == AdjustmentType.ALLOCATION:
            goal_data["asset_allocation"] = adjustment.adjustment_value


class StrategyEvaluationFramework:
    """
    Evaluates and compares different adjustment strategies.
    
    This class provides methods to evaluate the applicability and effectiveness
    of strategies, rank them by suitability, and provide explanations for
    recommendations.
    """
    
    def __init__(self, factory: Optional[GoalTypeAdjusterFactory] = None):
        """
        Initialize the evaluation framework.
        
        Args:
            factory: Optional factory to use for creating adjusters
        """
        self.factory = factory or GoalTypeAdjusterFactory
    
    def evaluate_strategy_applicability(
        self,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        strategy_name: str
    ) -> Dict[str, Any]:
        """
        Evaluate whether a strategy is applicable to a goal.
        
        Args:
            goal_data: Goal data including category and other information
            profile: User profile data
            strategy_name: Name of the strategy to evaluate
            
        Returns:
            Applicability evaluation results
        """
        # Parse strategy name
        if ":" in strategy_name:
            strategy_type, strategy_name = strategy_name.split(":", 1)
        else:
            strategy_type = "contribution"
        
        # Get strategy configuration
        strategy_manager = self.factory._get_strategy_manager()
        goal_category = goal_data.get("category", "").lower()
        
        config = strategy_manager.get_strategy_configuration(
            strategy_type, strategy_name, goal_category
        )
        
        if not config:
            return {
                "applicable": False,
                "reason": f"Strategy {strategy_type}:{strategy_name} not found"
            }
        
        # Check applicability rules
        applicability = config.get("applicability", {})
        
        # Check excluded categories
        excluded_categories = applicability.get("excluded_categories", [])
        if goal_category in [cat.lower() for cat in excluded_categories]:
            return {
                "applicable": False,
                "reason": f"Strategy not applicable to {goal_category} goals"
            }
        
        # Check timeline constraints
        min_timeline = applicability.get("min_timeline_months")
        max_timeline = applicability.get("max_timeline_months")
        
        timeline_months = self._get_remaining_timeline(goal_data)
        
        if min_timeline is not None and timeline_months < min_timeline:
            return {
                "applicable": False,
                "reason": f"Goal timeline ({timeline_months} months) is less than minimum ({min_timeline} months)"
            }
        
        if max_timeline is not None and timeline_months > max_timeline:
            return {
                "applicable": False,
                "reason": f"Goal timeline ({timeline_months} months) exceeds maximum ({max_timeline} months)"
            }
        
        # Check fixed deadline compatibility
        if applicability.get("fixed_deadline_compatible") is False and goal_data.get("has_fixed_deadline", False):
            return {
                "applicable": False,
                "reason": "Strategy not compatible with goals having fixed deadlines"
            }
        
        # Check income requirement
        if applicability.get("income_requirement", False):
            monthly_income = self._extract_monthly_income(profile)
            if monthly_income <= 0:
                return {
                    "applicable": False,
                    "reason": "Strategy requires income information which is missing"
                }
        
        # All checks passed, strategy is applicable
        return {
            "applicable": True,
            "configuration": config
        }
    
    def calculate_strategy_effectiveness(
        self,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        strategy_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate the potential effectiveness of a strategy.
        
        Args:
            goal_data: Goal data including category and other information
            profile: User profile data
            strategy_name: Name of the strategy to evaluate
            parameters: Optional parameters to customize the strategy
            
        Returns:
            Effectiveness metrics
        """
        # Check if strategy is applicable
        applicability = self.evaluate_strategy_applicability(goal_data, profile, strategy_name)
        if not applicability.get("applicable", False):
            return {
                "effectiveness_score": 0.0,
                "applicable": False,
                "reason": applicability.get("reason", "Strategy not applicable")
            }
        
        # Parse strategy name
        if ":" in strategy_name:
            strategy_type, strategy_name = strategy_name.split(":", 1)
        else:
            strategy_type = "contribution"
        
        # Create an executor to estimate impact
        executor = AdjustmentStrategyExecutor(self.factory)
        impact = executor.estimate_strategy_impact(
            goal_data, profile, f"{strategy_type}:{strategy_name}", parameters
        )
        
        # Calculate effectiveness score based on impact metrics
        effectiveness_score = impact.get("suitability_score", 0.0)
        
        # Cultural and personal factor adjustments
        goal_category = goal_data.get("category", "").lower()
        
        # Adjust effectiveness based on cultural priorities
        if strategy_type == "target_amount" and (
            "wedding" in goal_category or 
            "education" in goal_category or 
            "religious" in goal_category
        ):
            # These are culturally significant goals in India, reducing targets is less effective
            effectiveness_score *= 0.8
        
        # Adjust effectiveness based on life stage
        life_stage = profile.get("life_stage", "").lower()
        age = profile.get("age", 35)
        
        if strategy_type == "timeframe" and "retirement" in goal_category:
            if age > 50:
                # Time extension for retirement is less effective for older people
                effectiveness_score *= 0.7
        
        # Return effectiveness evaluation
        return {
            "effectiveness_score": effectiveness_score,
            "impact_metrics": impact.get("impact_metrics", {}),
            "confidence_score": impact.get("confidence_score", 0.0),
            "applicable": True
        }
    
    def rank_strategies_by_suitability(
        self,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        strategies: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank strategies by their suitability for a goal.
        
        Args:
            goal_data: Goal data including category and other information
            profile: User profile data
            strategies: Optional list of strategy names to evaluate
                       If None, all applicable strategies will be evaluated
            
        Returns:
            List of strategies ranked by suitability
        """
        goal_category = goal_data.get("category", "").lower()
        
        # If no strategies specified, get all strategies for this goal type
        if strategies is None:
            all_strategies = self.factory.get_adjustment_strategies(goal_category)
            strategies = []
            
            for strategy_type, type_strategies in all_strategies.items():
                for strategy_name in type_strategies:
                    strategies.append(f"{strategy_type}:{strategy_name}")
        
        # Evaluate each strategy
        results = []
        for strategy in strategies:
            # Check applicability
            applicability = self.evaluate_strategy_applicability(goal_data, profile, strategy)
            
            if applicability.get("applicable", False):
                # Calculate effectiveness
                effectiveness = self.calculate_strategy_effectiveness(goal_data, profile, strategy)
                
                # Add to results
                results.append({
                    "strategy": strategy,
                    "effectiveness_score": effectiveness.get("effectiveness_score", 0.0),
                    "confidence_score": effectiveness.get("confidence_score", 0.0),
                    "impact_metrics": effectiveness.get("impact_metrics", {}),
                    "description": applicability.get("configuration", {}).get("description", "")
                })
        
        # Sort by effectiveness score (highest first)
        results.sort(key=lambda x: x["effectiveness_score"], reverse=True)
        
        return results
    
    def _get_remaining_timeline(self, goal_data: Dict[str, Any]) -> int:
        """Get remaining timeline in months for a goal"""
        target_date_str = goal_data.get("target_date", "")
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
            now = datetime.now()
            delta = target_date - now
            return max(0, int(delta.days / 30))
        except (ValueError, TypeError):
            # If target date is invalid, use timeline_months if available
            return goal_data.get("timeline_months", 60)
    
    def _extract_monthly_income(self, profile: Dict[str, Any]) -> float:
        """Extract monthly income from profile data"""
        if "income" in profile:
            return float(profile["income"])
        
        if "answers" in profile:
            for answer in profile["answers"]:
                if answer.get("question_id") == "monthly_income":
                    return float(answer.get("answer", 0))
        
        return 0.0


class DefaultGoalTypeAdjuster(BaseGoalTypeAdjuster):
    """
    Default implementation of a goal type adjuster.
    
    This class provides a fallback implementation for goal types that don't have
    a specific adjuster registered. It implements the abstract methods with
    reasonable default behavior.
    """
    
    # This adjuster can handle any goal type
    GOAL_TYPES = ["default"]
    
    def get_adjustment_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Get available adjustment strategies for this goal type"""
        # Use the factory to get strategies for the default goal type
        return GoalTypeAdjusterFactory.get_adjustment_strategies("default")
    
    def execute_strategy(
        self, 
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        strategy_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[GoalAdjustment]:
        """Execute a specific adjustment strategy"""
        # Get strategy configuration
        strategies = self.get_adjustment_strategies()
        
        # Parse if strategy includes type
        if ":" in strategy_name:
            strategy_type, strategy_name = strategy_name.split(":", 1)
        else:
            # Try to find the strategy type
            for s_type, s_names in strategies.items():
                if strategy_name in s_names:
                    strategy_type = s_type
                    break
            else:
                # Default to contribution if not found
                strategy_type = "contribution"
        
        # Check if strategy exists
        if strategy_type not in strategies or strategy_name not in strategies[strategy_type]:
            logger.error(f"Strategy {strategy_type}:{strategy_name} not found")
            return None
        
        # Get the corresponding method from GoalAdjustmentRecommender
        strategy_methods = {
            "target_amount": "adjust_target_amount",
            "timeframe": "adjust_timeframe",
            "contribution": "adjust_contribution",
            "allocation": "adjust_allocation"
        }
        
        # If we have a corresponding method, delegate to GoalAdjustmentRecommender
        if strategy_type in strategy_methods:
            # Create a gap result from goal data (simplified)
            gap_result = self._create_gap_result_from_goal(goal_data)
            
            # Create a recommender instance
            recommender = GoalAdjustmentRecommender(self.param_service)
            
            # Call the appropriate method
            method_name = strategy_methods[strategy_type]
            method = getattr(recommender, method_name)
            
            return method(gap_result, goal_data, profile)
        
        return None
    
    def evaluate_adjustment(
        self,
        goal_data: Dict[str, Any],
        profile: Dict[str, Any],
        adjustment: GoalAdjustment
    ) -> Dict[str, Any]:
        """Evaluate the impact and suitability of an adjustment"""
        # Simple evaluation based on adjustment type
        evaluation = {
            "impact_score": 0.5,
            "feasibility_score": 0.5,
            "expected_improvement": 0.0
        }
        
        # Calculate expected improvement based on impact metrics
        if adjustment.adjustment_type == AdjustmentType.TARGET_AMOUNT:
            # Target reduction improves feasibility 
            reduction_pct = adjustment.impact_metrics.get("reduction_percentage", 0)
            evaluation["expected_improvement"] = reduction_pct / 100
            
        elif adjustment.adjustment_type == AdjustmentType.TIMEFRAME:
            # Timeline extension improves feasibility
            extension = adjustment.impact_metrics.get("extension_months", 0)
            timeline = self._get_remaining_timeline(goal_data)
            if timeline > 0:
                evaluation["expected_improvement"] = min(0.5, extension / timeline)
            
        elif adjustment.adjustment_type == AdjustmentType.CONTRIBUTION:
            # Contribution increase improves funding
            increase = adjustment.impact_metrics.get("monthly_increase", 0)
            current = goal_data.get("monthly_contribution", 0)
            if current > 0:
                evaluation["expected_improvement"] = min(0.7, increase / current)
            
        elif adjustment.adjustment_type == AdjustmentType.ALLOCATION:
            # Allocation changes may improve returns
            return_change = adjustment.impact_metrics.get("expected_return_change", 0)
            evaluation["expected_improvement"] = return_change / 5  # 5% return change → 1.0 improvement
        
        return evaluation
    
    def _create_gap_result_from_goal(self, goal_data: Dict[str, Any]) -> GapResult:
        """Create a simplified GapResult from goal data for use with recommender"""
        target_amount = goal_data.get("target_amount", 0)
        current_amount = goal_data.get("current_amount", 0)
        gap_amount = max(0, target_amount - current_amount)
        
        gap_percentage = gap_amount / target_amount if target_amount > 0 else 0
        
        return GapResult(
            goal_id=goal_data.get("id", ""),
            goal_title=goal_data.get("title", ""),
            goal_category=goal_data.get("category", ""),
            target_amount=target_amount,
            current_amount=current_amount,
            gap_amount=gap_amount,
            gap_percentage=gap_percentage,
            timeframe_gap=goal_data.get("timeframe_gap", 0),
            capacity_gap=goal_data.get("capacity_gap", 0),
            severity=GapSeverity.MODERATE
        )
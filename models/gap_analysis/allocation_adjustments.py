"""
Allocation Adjustment Module

This module provides specialized strategies for adjusting asset allocations
to address funding gaps. It calculates optimal allocation changes and
evaluates their impact on goal feasibility.
"""

import logging
import math
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

from models.gap_analysis.core import (
    GapResult, 
    RemediationOption,
    get_financial_parameter_service
)
from models.gap_analysis.remediation_strategies import GapRemediationStrategy

logger = logging.getLogger(__name__)

class AllocationAdjustment(GapRemediationStrategy):
    """
    Class for calculating and evaluating asset allocation changes.
    
    This class provides methods to calculate and evaluate asset allocation changes
    for financial goals with funding gaps. It helps determine optimal allocations
    that balance risk and return to improve goal feasibility.
    """
    
    def __init__(self):
        """
        Initialize the allocation adjustment strategy.
        """
        super().__init__()
        
        # Additional parameters specific to allocation adjustments
        self.allocation_params = {
            "min_equity_allocation": 0.1,  # Minimum 10% equity
            "max_equity_allocation": 0.8,  # Maximum 80% equity
            "risk_tolerance_factor": 1.0,  # Default risk tolerance
            "time_horizon_factor": 1.0,  # Default time horizon
        }
        
        # Define asset class expected returns, volatility, and correlations
        self.asset_classes = {
            "equity": {
                "expected_return": 0.12,  # 12% annual return
                "volatility": 0.18,  # 18% annual volatility
                "categories": ["large_cap", "mid_cap", "small_cap", "international"]
            },
            "debt": {
                "expected_return": 0.07,  # 7% annual return
                "volatility": 0.05,  # 5% annual volatility
                "categories": ["government", "corporate", "short_term", "long_term"]
            },
            "gold": {
                "expected_return": 0.08,  # 8% annual return
                "volatility": 0.15,  # 15% annual volatility
                "categories": ["physical", "sovereign", "etf"]
            },
            "cash": {
                "expected_return": 0.03,  # 3% annual return
                "volatility": 0.01,  # 1% annual volatility
                "categories": ["savings", "liquid_funds", "fd"]
            }
        }
        
        # Correlation matrix (simplified)
        self.correlation_matrix = {
            "equity": {"equity": 1.0, "debt": 0.2, "gold": -0.1, "cash": 0.0},
            "debt": {"equity": 0.2, "debt": 1.0, "gold": 0.0, "cash": 0.3},
            "gold": {"equity": -0.1, "debt": 0.0, "gold": 1.0, "cash": 0.0},
            "cash": {"equity": 0.0, "debt": 0.3, "gold": 0.0, "cash": 1.0}
        }
        
        # Override defaults with values from parameter service if available
        if self.param_service:
            try:
                # Try to use get_parameters_by_prefix if available
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    # Get allocation parameters
                    param_values = self.param_service.get_parameters_by_prefix("allocation_adjustment.")
                    if param_values:
                        self.allocation_params.update(param_values)
                    
                    # Get asset class parameters
                    for asset_class in self.asset_classes:
                        param_values = self.param_service.get_parameters_by_prefix(f"asset_class.{asset_class}.")
                        if param_values:
                            for key, value in param_values.items():
                                short_key = key.split(".")[-1]  # Get the part after the last dot
                                self.asset_classes[asset_class][short_key] = value
                # Fall back to getting individual parameters
                else:
                    # Get allocation parameters
                    for key in self.allocation_params.keys():
                        param_path = f"allocation_adjustment.{key}"
                        value = self.param_service.get(param_path)
                        if value is not None:
                            self.allocation_params[key] = value
                    
                    # Get asset class parameters (simplified approach)
                    for asset_class in self.asset_classes:
                        for key in ['expected_return', 'volatility']:
                            param_path = f"asset_class.{asset_class}.{key}"
                            value = self.param_service.get(param_path)
                            if value is not None:
                                self.asset_classes[asset_class][key] = value
            except Exception as e:
                logger.warning(f"Error getting parameters: {e}")
                # Continue with defaults
    
    def optimize_allocation_for_goal(self, goal: Dict[str, Any], risk_tolerance: str, 
                                     time_horizon_years: int) -> Dict[str, Any]:
        """
        Optimize asset allocation for a specific goal.
        
        Args:
            goal: The goal to optimize for
            risk_tolerance: Risk tolerance level (conservative, moderate, aggressive)
            time_horizon_years: Time horizon in years
            
        Returns:
            Optimized allocation and expected performance
        """
        # Determine appropriate allocation based on goal type, risk, and horizon
        goal_category = goal.get("category", "")
        
        # Convert risk tolerance to numerical factor
        risk_factor = self._risk_tolerance_to_factor(risk_tolerance)
        
        # Adjust for time horizon (longer = more risk capacity)
        time_factor = self._time_horizon_to_factor(time_horizon_years)
        
        # Calculate baseline allocation
        baseline_allocation = self._get_baseline_allocation(goal_category)
        
        # Adjust allocation based on risk and time factors
        adjusted_allocation = self._adjust_allocation(baseline_allocation, risk_factor, time_factor)
        
        # Calculate expected performance
        expected_return = self._calculate_expected_return(adjusted_allocation)
        volatility = self._calculate_portfolio_volatility(adjusted_allocation)
        
        # Calculate risk-adjusted metrics
        sharpe_ratio = (expected_return - 0.03) / volatility if volatility > 0 else 0
        
        # Calculate long-term projections
        projection = self._project_allocation_growth(
            adjusted_allocation, 
            float(goal.get("current_amount", 0)),
            float(goal.get("target_amount", 0)),
            time_horizon_years
        )
        
        return {
            "allocation": adjusted_allocation,
            "expected_annual_return": expected_return,
            "expected_volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "projected_outcome": projection
        }
    
    def calculate_expected_return_improvement(self, current_allocation: Dict[str, float], 
                                             optimal_allocation: Dict[str, float]) -> float:
        """
        Calculate the expected return improvement from changing allocation.
        
        Args:
            current_allocation: Current asset allocation
            optimal_allocation: Optimal asset allocation
            
        Returns:
            Expected annual return improvement (percentage points)
        """
        current_return = self._calculate_expected_return(current_allocation)
        optimal_return = self._calculate_expected_return(optimal_allocation)
        
        return optimal_return - current_return
    
    def generate_allocation_options(self, gap_result: GapResult, profile: Dict[str, Any], 
                                   current_allocation: Dict[str, float] = None) -> List[RemediationOption]:
        """
        Generate asset allocation options for addressing a funding gap.
        
        Args:
            gap_result: Gap analysis result
            profile: User profile with financial information
            current_allocation: Current asset allocation (optional)
            
        Returns:
            List of allocation change options
        """
        # If no current allocation provided, try to extract from profile
        if not current_allocation:
            current_allocation = self._extract_current_allocation(profile)
        
        # Normalize allocation to ensure it sums to 1
        current_allocation = self._normalize_allocation(current_allocation)
        
        # Create a mock goal for optimization
        mock_goal = {
            "id": gap_result.goal_id,
            "title": gap_result.goal_title,
            "category": gap_result.goal_category,
            "target_amount": gap_result.target_amount,
            "current_amount": gap_result.current_amount
        }
        
        # Extract risk tolerance and time horizon
        risk_tolerance = self._extract_risk_tolerance(profile)
        time_horizon_years = self._extract_time_horizon(mock_goal)
        
        # Generate options with different risk levels
        options = []
        
        # Conservative option
        conservative_result = self.optimize_allocation_for_goal(
            mock_goal, "conservative", time_horizon_years
        )
        conservative_option = self._create_allocation_option(
            current_allocation, conservative_result["allocation"], gap_result,
            "conservative", conservative_result
        )
        options.append(conservative_option)
        
        # Balanced option (if not the same as current risk tolerance)
        if risk_tolerance != "moderate":
            balanced_result = self.optimize_allocation_for_goal(
                mock_goal, "moderate", time_horizon_years
            )
            balanced_option = self._create_allocation_option(
                current_allocation, balanced_result["allocation"], gap_result,
                "balanced", balanced_result
            )
            options.append(balanced_option)
        
        # Aggressive option (if appropriate for time horizon)
        if time_horizon_years >= 5 and risk_tolerance != "aggressive":
            aggressive_result = self.optimize_allocation_for_goal(
                mock_goal, "aggressive", time_horizon_years
            )
            aggressive_option = self._create_allocation_option(
                current_allocation, aggressive_result["allocation"], gap_result,
                "aggressive", aggressive_result
            )
            options.append(aggressive_option)
        
        return options
    
    def _create_allocation_option(self, current_allocation: Dict[str, float], 
                                 new_allocation: Dict[str, float], gap_result: GapResult,
                                 risk_level: str, optimization_result: Dict[str, Any]) -> RemediationOption:
        """
        Create a remediation option for an allocation change.
        
        Args:
            current_allocation: Current asset allocation
            new_allocation: New asset allocation
            gap_result: Gap analysis result
            risk_level: Risk level of the new allocation
            optimization_result: Results from allocation optimization
            
        Returns:
            Remediation option for allocation change
        """
        # Calculate improvement in expected return
        return_improvement = self.calculate_expected_return_improvement(
            current_allocation, new_allocation
        )
        
        # Calculate impact on gap
        gap_impact = self._calculate_gap_impact(
            gap_result, return_improvement, optimization_result["projected_outcome"]["years"]
        )
        
        # Format allocation changes for description
        changes = []
        for asset_class, new_pct in new_allocation.items():
            current_pct = current_allocation.get(asset_class, 0)
            diff = new_pct - current_pct
            if abs(diff) >= 0.05:  # Only include significant changes
                direction = "increase" if diff > 0 else "decrease"
                changes.append(f"{asset_class} {direction} to {new_pct:.0%}")
        
        changes_text = ", ".join(changes[:3])  # Limit to top 3 changes for brevity
        if len(changes) > 3:
            changes_text += ", and other adjustments"
        
        # Create description
        description = f"Optimize to {risk_level} allocation ({changes_text}) for +{return_improvement:.1%} return"
        
        # Create impact metrics
        impact_metrics = {
            "current_allocation": current_allocation,
            "new_allocation": new_allocation,
            "return_improvement": return_improvement,
            "risk_level": risk_level,
            "expected_volatility": optimization_result["expected_volatility"],
            "gap_reduction": gap_impact["gap_reduction"],
            "time_to_goal": optimization_result["projected_outcome"]["years_to_goal"],
            "probability_of_success": gap_impact["probability_of_success"]
        }
        
        # Create implementation steps
        implementation_steps = [
            f"Rebalance portfolio to {risk_level} allocation: " + 
            ", ".join(f"{k}: {v:.0%}" for k, v in new_allocation.items()),
            "Consider tax implications before selling existing investments",
            "Implement changes gradually to minimize market timing risk",
            "Set up quarterly portfolio reviews to maintain target allocation"
        ]
        
        return RemediationOption(
            description=description,
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps
        )
    
    def _risk_tolerance_to_factor(self, risk_tolerance: str) -> float:
        """Convert risk tolerance level to a numerical factor"""
        return {
            "conservative": 0.7,
            "moderate": 1.0,
            "aggressive": 1.3,
            "very_conservative": 0.5,
            "very_aggressive": 1.5
        }.get(risk_tolerance.lower(), 1.0)
    
    def _time_horizon_to_factor(self, years: int) -> float:
        """Convert time horizon to a numerical factor"""
        if years < 2:
            return 0.6  # Short-term
        elif years < 5:
            return 0.8  # Medium-term
        elif years < 10:
            return 1.0  # Intermediate
        elif years < 20:
            return 1.2  # Long-term
        else:
            return 1.3  # Very long-term
    
    def _get_baseline_allocation(self, goal_category: str) -> Dict[str, float]:
        """Get baseline allocation based on goal category"""
        # Default allocations by goal type
        allocations = {
            "retirement": {"equity": 0.7, "debt": 0.2, "gold": 0.05, "cash": 0.05},
            "education": {"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05},
            "home": {"equity": 0.4, "debt": 0.5, "gold": 0.05, "cash": 0.05},
            "emergency_fund": {"equity": 0.0, "debt": 0.4, "gold": 0.0, "cash": 0.6},
            "discretionary": {"equity": 0.5, "debt": 0.3, "gold": 0.1, "cash": 0.1},
            "wedding": {"equity": 0.4, "debt": 0.4, "gold": 0.1, "cash": 0.1},
            "healthcare": {"equity": 0.5, "debt": 0.4, "gold": 0.05, "cash": 0.05},
            "legacy_planning": {"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05},
            "charitable_giving": {"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05},
            "debt_repayment": {"equity": 0.0, "debt": 0.0, "gold": 0.0, "cash": 1.0}
        }
        
        # Return the specific allocation or a balanced default
        return allocations.get(goal_category, {"equity": 0.5, "debt": 0.3, "gold": 0.1, "cash": 0.1})
    
    def _adjust_allocation(self, baseline: Dict[str, float], risk_factor: float, 
                          time_factor: float) -> Dict[str, float]:
        """
        Adjust allocation based on risk tolerance and time horizon.
        
        Args:
            baseline: Baseline allocation
            risk_factor: Risk tolerance factor
            time_factor: Time horizon factor
            
        Returns:
            Adjusted allocation
        """
        # Combined adjustment factor
        combined_factor = risk_factor * time_factor
        
        # Adjust equity allocation based on combined factor
        equity_adjustment = (combined_factor - 1.0) * 0.2  # 20% swing based on factors
        
        # Start with baseline
        adjusted = baseline.copy()
        
        # Apply equity adjustment (between min and max limits)
        baseline_equity = baseline.get("equity", 0)
        new_equity = max(
            self.allocation_params["min_equity_allocation"],
            min(self.allocation_params["max_equity_allocation"], baseline_equity + equity_adjustment)
        )
        
        # Calculate adjustment
        equity_diff = new_equity - baseline_equity
        
        # If equity changed, adjust other asset classes proportionally
        if equity_diff != 0:
            adjusted["equity"] = new_equity
            
            # Distribute the difference among other asset classes proportionally
            non_equity_total = sum(v for k, v in baseline.items() if k != "equity")
            if non_equity_total > 0:
                for asset_class in baseline:
                    if asset_class != "equity":
                        weight = baseline[asset_class] / non_equity_total
                        adjusted[asset_class] = max(0, baseline[asset_class] - (equity_diff * weight))
            
            # Normalize to ensure it sums to 1
            adjusted = self._normalize_allocation(adjusted)
        
        return adjusted
    
    def _normalize_allocation(self, allocation: Dict[str, float]) -> Dict[str, float]:
        """Normalize allocation to ensure it sums to 1"""
        total = sum(allocation.values())
        if total == 0:
            # If all zeros, return default allocation
            return {"equity": 0.5, "debt": 0.3, "gold": 0.1, "cash": 0.1}
        
        return {k: v / total for k, v in allocation.items()}
    
    def _calculate_expected_return(self, allocation: Dict[str, float]) -> float:
        """Calculate expected annual return for an allocation"""
        return sum(
            allocation.get(asset_class, 0) * self.asset_classes[asset_class]["expected_return"]
            for asset_class in self.asset_classes
            if asset_class in allocation
        )
    
    def _calculate_portfolio_volatility(self, allocation: Dict[str, float]) -> float:
        """Calculate portfolio volatility (standard deviation)"""
        # Create lists of weights and asset classes
        assets = [asset for asset in allocation if asset in self.asset_classes]
        weights = [allocation[asset] for asset in assets]
        
        # Calculate weighted variance
        variance = 0
        for i, asset_i in enumerate(assets):
            for j, asset_j in enumerate(assets):
                covariance = (
                    self.asset_classes[asset_i]["volatility"] * 
                    self.asset_classes[asset_j]["volatility"] * 
                    self.correlation_matrix[asset_i][asset_j]
                )
                variance += weights[i] * weights[j] * covariance
        
        return math.sqrt(variance)
    
    def _project_allocation_growth(self, allocation: Dict[str, float], initial_amount: float, 
                                  target_amount: float, years: int) -> Dict[str, Any]:
        """
        Project growth of an allocation over time.
        
        Args:
            allocation: Asset allocation
            initial_amount: Initial investment amount
            target_amount: Target amount to reach
            years: Time horizon in years
            
        Returns:
            Projection results
        """
        # Calculate expected return and volatility
        expected_return = self._calculate_expected_return(allocation)
        volatility = self._calculate_portfolio_volatility(allocation)
        
        # Simplified deterministic projection
        projected_amount = initial_amount * math.pow(1 + expected_return, years)
        
        # Calculate years to goal
        if initial_amount >= target_amount:
            years_to_goal = 0
        elif expected_return <= 0:
            years_to_goal = float('inf')
        else:
            years_to_goal = math.log(target_amount / initial_amount) / math.log(1 + expected_return)
        
        # Calculate probability of success using simplistic model
        if years_to_goal == 0:
            probability = 1.0
        elif years_to_goal == float('inf'):
            probability = 0.0
        else:
            # Simplified probability calculation using normal distribution
            shortfall_years = years_to_goal - years
            if shortfall_years <= 0:
                probability = 0.9 + 0.1 * (-shortfall_years / 5)  # Higher probability for excess years
                probability = min(0.99, probability)  # Cap at 99%
            else:
                probability = max(0.01, 0.9 * math.exp(-0.3 * shortfall_years))
        
        return {
            "initial_amount": initial_amount,
            "projected_amount": projected_amount,
            "target_amount": target_amount,
            "gap": max(0, target_amount - projected_amount),
            "years": years,
            "years_to_goal": years_to_goal,
            "expected_return": expected_return,
            "probability_of_success": probability
        }
    
    def _calculate_gap_impact(self, gap_result: GapResult, return_improvement: float, 
                            time_horizon_years: int) -> Dict[str, Any]:
        """
        Calculate the impact of return improvement on the funding gap.
        
        Args:
            gap_result: Gap analysis result
            return_improvement: Improvement in expected annual return
            time_horizon_years: Time horizon in years
            
        Returns:
            Impact assessment
        """
        current_amount = gap_result.current_amount
        target_amount = gap_result.target_amount
        gap_amount = gap_result.gap_amount
        
        # Calculate current projected amount (assuming 6% return)
        current_projected = current_amount * math.pow(1.06, time_horizon_years)
        
        # Calculate new projected amount
        new_projected = current_amount * math.pow(1.06 + return_improvement, time_horizon_years)
        
        # Calculate gap reduction
        original_gap = max(0, target_amount - current_projected)
        new_gap = max(0, target_amount - new_projected)
        gap_reduction = original_gap - new_gap
        gap_reduction_percentage = gap_reduction / original_gap * 100 if original_gap > 0 else 0
        
        # Calculate probability of success
        if target_amount <= new_projected:
            probability = 0.9 + 0.1 * ((new_projected - target_amount) / target_amount)
            probability = min(0.99, probability)
        else:
            shortfall = target_amount - new_projected
            probability = max(0.01, 0.9 * math.exp(-0.3 * shortfall / target_amount))
        
        return {
            "current_projected": current_projected,
            "new_projected": new_projected,
            "gap_reduction": gap_reduction,
            "gap_reduction_percentage": gap_reduction_percentage,
            "probability_of_success": probability
        }
    
    def _extract_current_allocation(self, profile: Dict[str, Any]) -> Dict[str, float]:
        """Extract current asset allocation from profile data"""
        # Look for direct allocation field
        if "asset_allocation" in profile:
            return profile["asset_allocation"]
        
        # Look for assets and calculate allocation
        if "assets" in profile:
            assets = profile["assets"]
            total = sum(float(v) for v in assets.values())
            if total > 0:
                return {k: float(v) / total for k, v in assets.items()}
        
        # Look in answers
        if "answers" in profile:
            allocation = {}
            for answer in profile["answers"]:
                if answer.get("question_id", "").startswith("allocation_"):
                    asset_class = answer.get("question_id").replace("allocation_", "")
                    allocation[asset_class] = float(answer.get("answer", 0)) / 100
            
            if allocation:
                return self._normalize_allocation(allocation)
        
        # Default allocation
        return {"equity": 0.5, "debt": 0.3, "gold": 0.1, "cash": 0.1}
    
    def _extract_risk_tolerance(self, profile: Dict[str, Any]) -> str:
        """Extract risk tolerance from profile data"""
        # Look for direct risk tolerance field
        if "risk_tolerance" in profile:
            return profile["risk_tolerance"]
        
        # Look in answers
        if "answers" in profile:
            for answer in profile["answers"]:
                if answer.get("question_id") == "risk_tolerance":
                    return answer.get("answer", "moderate")
        
        # Default value
        return "moderate"
    
    def _extract_time_horizon(self, goal: Dict[str, Any]) -> int:
        """Extract time horizon from goal data"""
        # Look for direct time horizon field
        if "time_horizon_years" in goal:
            return int(goal["time_horizon_years"])
        
        # Try to calculate from target date
        if "target_date" in goal:
            try:
                from datetime import datetime, date
                target_date = datetime.strptime(goal["target_date"], "%Y-%m-%d").date()
                today = date.today()
                years = (target_date.year - today.year) + (target_date.month - today.month) / 12
                return max(1, int(years))
            except (ValueError, TypeError):
                pass
        
        # Default based on goal category
        category = goal.get("category", "")
        return {
            "retirement": 20,
            "education": 10,
            "home": 7,
            "emergency_fund": 1,
            "discretionary": 3,
            "wedding": 2,
            "healthcare": 5,
            "legacy_planning": 15,
            "charitable_giving": 10,
            "debt_repayment": 3
        }.get(category, 5)  # Default 5 years
"""
Contribution Adjustment Module

This module provides specialized strategies for adjusting contribution amounts
to address funding gaps. It calculates optimal contribution increases and
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

class ContributionAdjustment(GapRemediationStrategy):
    """
    Class for calculating and evaluating contribution changes.
    
    This class provides methods to calculate and evaluate contribution changes
    for financial goals with funding gaps. It helps determine optimal increases
    that balance goal achievement with budget constraints.
    """
    
    def __init__(self):
        """
        Initialize the contribution adjustment strategy.
        """
        super().__init__()
        
        # Additional parameters specific to contribution adjustments
        self.contribution_params = {
            "min_increase_percentage": 0.05,  # Minimum 5% increase
            "max_income_percentage": 0.25,  # Maximum 25% of income
            "optimal_increase_factor": 1.2,  # Optimal increase relative to gap
            "income_buffer": 0.1,  # 10% buffer for income
            "expense_reduction_potential": 0.2,  # Potential to reduce expenses by 20%
        }
        
        # Override defaults with values from parameter service if available
        if self.param_service:
            try:
                # Try to use get_parameters_by_prefix if available
                if hasattr(self.param_service, 'get_parameters_by_prefix'):
                    param_values = self.param_service.get_parameters_by_prefix("contribution_adjustment.")
                    if param_values:
                        self.contribution_params.update(param_values)
                # Fall back to getting individual parameters
                else:
                    for key in self.contribution_params.keys():
                        param_path = f"contribution_adjustment.{key}"
                        value = self.param_service.get(param_path)
                        if value is not None:
                            self.contribution_params[key] = value
            except Exception as e:
                logger.warning(f"Error getting parameters: {e}")
                # Continue with defaults
    
    def analyze_affordability(self, additional_contribution: float, profile: dict) -> Dict[str, Any]:
        """
        Analyze the affordability of an additional monthly contribution.
        
        Args:
            additional_contribution: Additional monthly contribution amount
            profile: The user profile with financial information
            
        Returns:
            Dictionary with affordability analysis
        """
        # Extract income and expense information
        monthly_income = self._extract_monthly_income(profile)
        monthly_expenses = self._extract_monthly_expenses(profile)
        current_savings = monthly_income - monthly_expenses
        
        # Calculate key metrics
        disposable_income = current_savings
        current_savings_rate = (current_savings / monthly_income) if monthly_income > 0 else 0
        new_savings = current_savings + additional_contribution
        new_savings_rate = (new_savings / monthly_income) if monthly_income > 0 else 0
        
        # Calculate impact on budget
        income_impact_percentage = (additional_contribution / monthly_income) * 100 if monthly_income > 0 else 0
        
        # Determine if affordable
        buffer_amount = monthly_income * self.contribution_params["income_buffer"]
        affordable = (disposable_income - additional_contribution) >= buffer_amount
        
        # Calculate expense reduction potential
        expense_breakdown = self._extract_expense_breakdown(profile)
        reduction_potential = self._calculate_expense_reduction_potential(expense_breakdown, monthly_expenses)
        
        # Prepare affordability assessment
        affordability = {
            "affordable": affordable,
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "current_savings": current_savings,
            "current_savings_rate": current_savings_rate * 100,  # As percentage
            "new_savings": new_savings,
            "new_savings_rate": new_savings_rate * 100,  # As percentage
            "income_impact_percentage": income_impact_percentage,
            "buffer_required": buffer_amount,
            "buffer_remaining": disposable_income - additional_contribution - buffer_amount,
            "expense_reduction_potential": reduction_potential,
            "effective_impact": additional_contribution - reduction_potential  # Net impact after potential expense reductions
        }
        
        # Add recommendations based on affordability
        recommendations = []
        if not affordable:
            if reduction_potential >= additional_contribution:
                recommendations.append("Reduce discretionary expenses to accommodate increased savings")
            else:
                recommendations.append("Consider a smaller contribution increase or extend goal timeline")
                
            if income_impact_percentage > 15:
                recommendations.append("Look for additional income sources to support this goal")
        else:
            if income_impact_percentage < 5:
                recommendations.append("Consider increasing contribution further for faster goal achievement")
        
        affordability["recommendations"] = recommendations
        
        return affordability
    
    def calculate_optimal_contribution(self, gap_result: GapResult, profile: dict) -> float:
        """
        Calculate the optimal monthly contribution increase for a goal with a funding gap.
        
        Args:
            gap_result: Gap analysis result for the goal
            profile: User profile with financial information
            
        Returns:
            Optimal monthly contribution increase
        """
        # Extract goal timeline
        goal_id = gap_result.goal_id
        goal_timeline = 36  # Default 3 years
        
        # Calculate minimum required contribution
        min_contribution = gap_result.gap_amount / goal_timeline
        
        # Apply optimal increase factor
        optimal_contribution = min_contribution * self.contribution_params["optimal_increase_factor"]
        
        # Cap based on income
        monthly_income = self._extract_monthly_income(profile)
        max_contribution = monthly_income * self.contribution_params["max_income_percentage"]
        
        # Calculate affordable contribution
        monthly_expenses = self._extract_monthly_expenses(profile)
        disposable_income = monthly_income - monthly_expenses
        affordable_contribution = disposable_income * 0.5  # Use up to 50% of disposable income
        
        # Consider current contribution if available
        current_contribution = 0  # Default value
        
        # Choose the optimal contribution
        # Start with minimum required, adjust up to optimal if affordable, but cap at maximum
        contribution = min(max_contribution, max(min_contribution, min(optimal_contribution, affordable_contribution)))
        
        # Calculate the increase over current contribution
        increase = max(0, contribution - current_contribution)
        
        return increase
    
    def generate_contribution_scenarios(self, gap_result: GapResult, profile: dict) -> List[Dict[str, Any]]:
        """
        Generate multiple contribution increase scenarios with varying impacts.
        
        Args:
            gap_result: Gap analysis result for the goal
            profile: User profile with financial information
            
        Returns:
            List of contribution scenarios with impact analysis
        """
        scenarios = []
        
        # Calculate optimal contribution increase
        optimal_increase = self.calculate_optimal_contribution(gap_result, profile)
        
        # Generate scenarios around the optimal point
        increases = [
            max(1000, optimal_increase * 0.5),  # Conservative option
            optimal_increase,  # Optimal option
            min(optimal_increase * 1.5, optimal_increase + 5000)  # Aggressive option
        ]
        
        # Ensure increases are unique and reasonable
        increases = list(set([round(inc, -2) for inc in increases]))  # Round to nearest 100
        increases.sort()
        
        # Analyze each increase scenario
        for increase in increases:
            # First, check affordability
            affordability = self.analyze_affordability(increase, profile)
            
            # Then, calculate impact on goal
            years_to_goal = gap_result.gap_amount / (increase * 12)
            months_to_goal = int(years_to_goal * 12)
            
            # Calculate feasibility score
            feasibility = 0.8 if affordability["affordable"] else 0.4
            feasibility *= 0.5 + 0.5 * (1 - min(1, years_to_goal / 10))  # Higher for shorter time to goal
            
            # Categorize the scenario
            if increase == optimal_increase:
                category = "optimal"
            elif increase < optimal_increase:
                category = "conservative"
            else:
                category = "aggressive"
            
            scenario = {
                "increase_amount": increase,
                "affordability": affordability,
                "years_to_goal": years_to_goal,
                "months_to_goal": months_to_goal,
                "category": category,
                "feasibility_score": feasibility
            }
            
            scenarios.append(scenario)
        
        return scenarios
    
    def create_contribution_option(self, increase_amount: float, gap_result: GapResult, profile: dict) -> RemediationOption:
        """
        Create a remediation option for contribution increase.
        
        Args:
            increase_amount: Amount to increase monthly contribution
            gap_result: Gap analysis result for the goal
            profile: User profile with financial information
            
        Returns:
            Remediation option for contribution increase
        """
        # Analyze affordability
        affordability = self.analyze_affordability(increase_amount, profile)
        
        # Calculate time to goal
        gap_amount = gap_result.gap_amount
        months_to_goal = int(gap_amount / increase_amount) if increase_amount > 0 else 999
        years_to_goal = months_to_goal / 12
        
        # Format years and months
        if years_to_goal < 1:
            time_str = f"{months_to_goal} months"
        else:
            whole_years = int(years_to_goal)
            remaining_months = months_to_goal - (whole_years * 12)
            if remaining_months > 0:
                time_str = f"{whole_years} years and {remaining_months} months"
            else:
                time_str = f"{whole_years} years"
        
        # Create impact metrics
        impact_metrics = {
            "increase_amount": increase_amount,
            "affordable": affordability["affordable"],
            "income_percentage": affordability["income_impact_percentage"],
            "months_to_goal": months_to_goal,
            "years_to_goal": years_to_goal,
            "expense_reduction_needed": 0 if affordability["affordable"] else abs(affordability["buffer_remaining"])
        }
        
        # Create description
        description = f"Increase monthly contribution by ₹{increase_amount:,.0f}, reaching goal in {time_str}"
        
        # Create implementation steps
        implementation_steps = [
            f"Increase your monthly contribution for {gap_result.goal_title} by ₹{increase_amount:,.0f}",
            "Set up an automatic transfer on payday to ensure consistent contributions",
        ]
        
        # Add steps based on affordability
        if not affordability["affordable"]:
            implementation_steps.append(f"Reduce discretionary expenses by ₹{impact_metrics['expense_reduction_needed']:,.0f} per month")
            implementation_steps.append("Review your budget for cost-saving opportunities")
        else:
            implementation_steps.append("Maintain your current budget discipline")
            implementation_steps.append("Consider investing additional windfalls to accelerate progress")
        
        return RemediationOption(
            description=description,
            impact_metrics=impact_metrics,
            implementation_steps=implementation_steps
        )
    
    def _extract_expense_breakdown(self, profile: dict) -> Dict[str, float]:
        """Extract expense breakdown from profile data"""
        # Default breakdown if not found
        default_breakdown = {
            "housing": 0.3,
            "food": 0.15,
            "transportation": 0.1,
            "utilities": 0.1,
            "entertainment": 0.1,
            "dining_out": 0.05,
            "shopping": 0.05,
            "other": 0.15
        }
        
        # Look for direct expense breakdown field
        if "expense_breakdown" in profile:
            return profile["expense_breakdown"]
        
        # Look in answers
        if "answers" in profile:
            breakdown = {}
            for answer in profile["answers"]:
                if answer.get("question_id", "").startswith("expense_"):
                    category = answer.get("question_id").replace("expense_", "")
                    breakdown[category] = float(answer.get("answer", 0))
            
            if breakdown:
                # Convert absolute values to percentages
                total = sum(breakdown.values())
                if total > 0:
                    return {k: v / total for k, v in breakdown.items()}
        
        # Default value
        return default_breakdown
    
    def _calculate_expense_reduction_potential(self, expense_breakdown: Dict[str, float], total_expenses: float) -> float:
        """Calculate potential for expense reduction"""
        # Categories that have higher reduction potential
        reduction_factors = {
            "entertainment": 0.5,  # Can reduce entertainment by 50%
            "dining_out": 0.6,     # Can reduce dining out by 60%
            "shopping": 0.4,       # Can reduce shopping by 40%
            "discretionary": 0.5,  # Can reduce discretionary by 50%
            "subscriptions": 0.3,  # Can reduce subscriptions by 30%
            "other": 0.2           # Can reduce other by 20%
        }
        
        # Calculate potential reduction
        potential = 0
        for category, percentage in expense_breakdown.items():
            if category in reduction_factors:
                category_amount = total_expenses * percentage
                potential += category_amount * reduction_factors[category]
        
        return potential
    
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
"""
Gap Analysis Module

This module provides tools for analyzing mismatches between financial goals and resources.
It helps identify funding gaps, timeframe issues, and prioritization conflicts to enable
better financial planning decisions.
"""

import logging
import math
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any, Tuple, Callable
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

def get_financial_parameter_service():
    """
    Get the financial parameter service instance.
    
    This is separated out to avoid circular imports and to make testing easier.
    """
    try:
        from services.financial_parameter_service import FinancialParameterService
        return FinancialParameterService()
    except ImportError:
        logger.warning("Financial Parameter Service not available, using default parameters")
        return None


class GapSeverity(Enum):
    """Enum representing the severity levels of financial gaps"""
    CRITICAL = "critical"       # Severe gap requiring immediate attention
    SIGNIFICANT = "significant" # Large gap requiring substantial adjustment
    MODERATE = "moderate"       # Moderate gap requiring some adjustment
    MINOR = "minor"             # Small gap that can be addressed with minor changes


@dataclass
class GapResult:
    """Data class for storing gap analysis results"""
    goal_id: str
    goal_title: str
    goal_category: str
    target_amount: float
    current_amount: float
    gap_amount: float
    gap_percentage: float
    timeframe_gap: int = 0  # Additional months needed at current pace
    capacity_gap: float = 0.0  # Gap between required and available savings capacity
    capacity_gap_percentage: float = 0.0  # Capacity gap as percentage of income
    severity: GapSeverity = GapSeverity.MODERATE
    recommended_adjustments: Dict[str, Any] = field(default_factory=dict)
    resource_conflicts: List[str] = field(default_factory=list)
    description: str = ""
    projected_values: Dict[str, List[float]] = field(default_factory=dict)  # Projected values over time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the gap result to a dictionary for serialization"""
        return {
            "goal_id": self.goal_id,
            "goal_title": self.goal_title,
            "goal_category": self.goal_category,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "gap_amount": self.gap_amount,
            "gap_percentage": self.gap_percentage,
            "timeframe_gap": self.timeframe_gap,
            "capacity_gap": self.capacity_gap,
            "capacity_gap_percentage": self.capacity_gap_percentage,
            "severity": self.severity.value,
            "recommended_adjustments": self.recommended_adjustments,
            "resource_conflicts": self.resource_conflicts,
            "description": self.description,
            "projected_values": self.projected_values
        }


class GapAnalysis:
    """
    Class for analyzing mismatches between financial goals and available resources.
    
    This class provides methods to identify funding gaps, timeframe issues, and
    resource conflicts. It helps prioritize adjustments and offers insights for
    better financial planning decisions.
    
    Enhanced features include:
    - Gap metrics calculations (funding, time, capacity)
    - Integration with asset and income projections
    - India-specific context for financial analysis
    - Support for various goal types with specialized calculations
    - Holistic financial health analysis
    - Gap aggregation and categorization
    - Lifecycle-based goal analysis
    - Risk exposure evaluation
    - Indian tax efficiency and family structure analysis
    """


@dataclass
class RemediationOption:
    """
    Data structure for representing a gap remediation option.
    
    Each remediation option includes details about the proposed
    action, its impact on the goal, and implementation steps.
    """
    description: str
    impact_metrics: Dict[str, Any] = field(default_factory=dict)  # Quantitative effects on the goal
    feasibility_score: float = 0.0  # How practical the option is (0-100)
    implementation_steps: List[Dict[str, str]] = field(default_factory=list)  # Structured list of actions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the remediation option to a dictionary for serialization"""
        return {
            "description": self.description,
            "impact_metrics": self.impact_metrics,
            "feasibility_score": self.feasibility_score,
            "implementation_steps": self.implementation_steps
        }


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
            "inflation_rate": 0.06,  # Default: 6% annual inflation in India
            "equity_returns": {
                "conservative": 0.09,  # 9% for conservative equity returns
                "moderate": 0.12,      # 12% for moderate equity returns
                "aggressive": 0.15     # 15% for aggressive equity returns
            },
            "debt_returns": {
                "conservative": 0.06,  # 6% for conservative debt returns
                "moderate": 0.07,      # 7% for moderate debt returns
                "aggressive": 0.08     # 8% for aggressive debt returns
            },
            "savings_rate_adjustment_max": 0.10,  # Maximum advised adjustment to savings rate
            "timeframe_extension_max": 0.25,     # Maximum advised extension to timeframe (as fraction)
            "target_amount_reduction_max": 0.15  # Maximum advised reduction to target amount
        }
        
        # Load parameters from service if available
        if self.param_service:
            try:
                service_params = self.param_service.get_all_parameters()
                # Update default params with those from the service
                for key, value in service_params.items():
                    if key in self.params and not isinstance(self.params[key], dict):
                        self.params[key] = value
                    elif key in self.params and isinstance(self.params[key], dict):
                        if isinstance(value, dict):
                            for nested_key, nested_value in value.items():
                                if nested_key in self.params[key]:
                                    self.params[key][nested_key] = nested_value
            except Exception as e:
                logger.error(f"Error loading parameters from service: {str(e)}")
    
    def generate_remediation_options(self, gap_result: GapResult) -> List[RemediationOption]:
        """
        Generate a prioritized list of remediation options for a gap.
        
        Args:
            gap_result: The gap analysis result to remediate
            
        Returns:
            List of RemediationOption objects sorted by effectiveness
        """
        # Identify possible strategies based on gap characteristics
        strategies = self.identify_possible_strategies(gap_result)
        
        # Prioritize strategies based on effectiveness and feasibility
        prioritized_strategies = self.prioritize_strategies(strategies, gap_result)
        
        return prioritized_strategies
    
    def estimate_success_probability(self, remediation_option: RemediationOption) -> float:
        """
        Calculate the likelihood of a remediation option's success.
        
        Args:
            remediation_option: The remediation option to evaluate
            
        Returns:
            Probability of success as a percentage (0-100)
        """
        # Base probability starts with the feasibility score
        base_probability = remediation_option.feasibility_score
        
        # Adjust based on impact metrics
        impact_metrics = remediation_option.impact_metrics
        
        # Check if impact metrics include gap reduction percentage
        if "gap_reduction_percentage" in impact_metrics:
            gap_reduction = impact_metrics["gap_reduction_percentage"]
            
            # Higher gap reduction increases probability, but with diminishing returns
            if gap_reduction > 100:
                adjustment = 15  # Maximum bonus for exceeding gap
            elif gap_reduction > 75:
                adjustment = 10  # Strong bonus
            elif gap_reduction > 50:
                adjustment = 5   # Moderate bonus
            else:
                adjustment = 0   # No bonus
                
            base_probability += adjustment
        
        # Check if impact metrics include timeframe extension
        if "timeframe_extension" in impact_metrics:
            timeframe_extension = impact_metrics["timeframe_extension"]
            
            # Penalize excessive timeframe extensions
            if timeframe_extension > 0.5:  # More than 50% extension
                adjustment = -15  # Significant penalty
            elif timeframe_extension > 0.25:  # 25-50% extension
                adjustment = -10  # Moderate penalty
            elif timeframe_extension > 0.1:   # 10-25% extension
                adjustment = -5   # Small penalty
            else:
                adjustment = 0    # No penalty
                
            base_probability += adjustment
        
        # Ensure probability is within valid range
        return max(0, min(100, base_probability))
    
    def explain_remediation_strategy(self, remediation_option: RemediationOption) -> str:
        """
        Generate a human-readable explanation of a remediation strategy.
        
        Args:
            remediation_option: The remediation option to explain
            
        Returns:
            Detailed explanation of the strategy and its effects
        """
        explanation = [
            f"### {remediation_option.description}",
            "\n**Impact on your financial goals:**"
        ]
        
        # Add impact metrics in readable format
        if remediation_option.impact_metrics:
            for metric, value in remediation_option.impact_metrics.items():
                if metric == "gap_reduction_percentage":
                    explanation.append(f"- Reduces funding gap by approximately {value:.1f}%")
                elif metric == "timeframe_extension":
                    months = int(value * 12)
                    explanation.append(f"- Extends timeframe by approximately {months} months")
                elif metric == "target_adjustment":
                    explanation.append(f"- Adjusts target amount by ₹{value:,.2f}")
                elif metric == "monthly_savings_adjustment":
                    explanation.append(f"- Changes monthly savings by ₹{value:,.2f}")
                else:
                    explanation.append(f"- {metric.replace('_', ' ').title()}: {value}")
        
        # Add feasibility assessment
        feasibility = remediation_option.feasibility_score
        if feasibility >= 80:
            assessment = "This strategy is highly feasible and straightforward to implement."
        elif feasibility >= 60:
            assessment = "This strategy is moderately feasible with some effort required."
        elif feasibility >= 40:
            assessment = "This strategy may be challenging but is achievable with dedication."
        else:
            assessment = "This strategy will be difficult to implement and requires significant changes."
            
        explanation.append(f"\n**Feasibility: {feasibility:.0f}%**\n{assessment}")
        
        # Add implementation steps
        if remediation_option.implementation_steps:
            explanation.append("\n**Implementation Steps:**")
            for i, step in enumerate(remediation_option.implementation_steps, 1):
                if "action" in step and "note" in step:
                    explanation.append(f"{i}. {step['action']} - *{step['note']}*")
                elif "action" in step:
                    explanation.append(f"{i}. {step['action']}")
                    
        # Add Indian financial context if applicable
        if "indian_context" in remediation_option.impact_metrics:
            explanation.append(f"\n**Indian Financial Context:**\n{remediation_option.impact_metrics['indian_context']}")
            
        return "\n".join(explanation)
    
    def identify_possible_strategies(self, gap_result: GapResult) -> List[RemediationOption]:
        """
        Identify applicable remediation strategies for a specific gap.
        
        Args:
            gap_result: The gap analysis result to remediate
            
        Returns:
            List of potential RemediationOption objects
        """
        strategies = []
        
        # Get gap characteristics
        gap_amount = gap_result.gap_amount
        gap_percentage = gap_result.gap_percentage
        timeframe_gap = gap_result.timeframe_gap
        
        # Strategy 1: Increase savings rate
        if gap_amount > 0:
            # Calculate required increase in monthly contribution
            monthly_increase = gap_amount / (timeframe_gap if timeframe_gap > 0 else 36)
            
            strategies.append(RemediationOption(
                description="Increase monthly savings",
                impact_metrics={
                    "gap_reduction_percentage": 100.0,
                    "monthly_savings_adjustment": monthly_increase,
                    "timeframe_extension": 0.0
                },
                feasibility_score=max(20, 100 - (monthly_increase / 1000) * 5),
                implementation_steps=[
                    {"action": "Review current budget to identify potential savings", 
                     "note": "Look for discretionary expenses that can be reduced"},
                    {"action": f"Increase monthly contribution by ₹{monthly_increase:,.2f}",
                     "note": "Automate this additional contribution if possible"}
                ]
            ))
        
        # Strategy 2: Extend timeframe
        if timeframe_gap > 0:
            # Calculate a reasonable timeframe extension
            extension_factor = min(0.25, timeframe_gap / 36)  # Cap at 25% extension
            
            strategies.append(RemediationOption(
                description="Extend goal timeframe",
                impact_metrics={
                    "gap_reduction_percentage": 50.0,
                    "timeframe_extension": extension_factor,
                    "monthly_savings_adjustment": 0.0
                },
                feasibility_score=75.0,
                implementation_steps=[
                    {"action": "Adjust goal target date to allow more time for asset growth", 
                     "note": "This gives compounding returns more time to work"}
                ]
            ))
        
        # Strategy 3: Adjust asset allocation for higher returns
        strategies.append(RemediationOption(
            description="Optimize investment portfolio allocation",
            impact_metrics={
                "gap_reduction_percentage": 30.0,
                "expected_return_increase": 0.01,  # 1% higher returns
                "risk_increase": "moderate"
            },
            feasibility_score=85.0,
            implementation_steps=[
                {"action": "Review current investment allocation", 
                 "note": "Identify underperforming assets"},
                {"action": "Adjust allocation to optimize for your risk profile",
                 "note": "Consider Indian tax-advantaged investments like ELSS funds"}
            ]
        ))
        
        # Strategy 4: Explore additional income sources
        strategies.append(RemediationOption(
            description="Develop additional income streams",
            impact_metrics={
                "gap_reduction_percentage": 40.0,
                "monthly_income_increase": gap_amount / 36
            },
            feasibility_score=50.0,
            implementation_steps=[
                {"action": "Evaluate skills that could generate side income", 
                 "note": "Consider freelancing, consulting, or part-time work"},
                {"action": "Research passive income opportunities",
                 "note": "Dividend stocks, rental property, or digital products"}
            ]
        ))
        
        # Strategy 5: Reduce goal target amount (if appropriate)
        if gap_percentage > 25:
            # Only suggest reducing target for large gaps
            target_reduction = min(gap_result.target_amount * 0.15, gap_amount)
            
            strategies.append(RemediationOption(
                description="Adjust goal target amount",
                impact_metrics={
                    "gap_reduction_percentage": (target_reduction / gap_amount) * 100,
                    "target_adjustment": -target_reduction
                },
                feasibility_score=65.0,
                implementation_steps=[
                    {"action": "Re-evaluate goal requirements", 
                     "note": "Consider if the full target amount is necessary"},
                    {"action": f"Reduce target amount by ₹{target_reduction:,.2f}",
                     "note": "Focus on essential needs while trimming discretionary components"}
                ]
            ))
        
        return strategies
    
    def prioritize_strategies(self, strategies: List[RemediationOption], gap_result: GapResult) -> List[RemediationOption]:
        """
        Order remediation strategies by effectiveness and feasibility.
        
        Args:
            strategies: List of potential remediation options
            gap_result: The gap analysis result being remediated
            
        Returns:
            Sorted list of RemediationOption objects
        """
        # Calculate effectiveness score for each strategy
        scored_strategies = []
        for strategy in strategies:
            effectiveness = self.calculate_strategy_effectiveness(strategy, gap_result)
            # Combined score balances effectiveness and feasibility
            combined_score = (effectiveness * 0.7) + (strategy.feasibility_score * 0.3)
            scored_strategies.append((strategy, combined_score))
            
        # Sort by combined score (descending)
        scored_strategies.sort(key=lambda x: x[1], reverse=True)
        
        # Return sorted strategies without scores
        return [item[0] for item in scored_strategies]
    
    def calculate_strategy_effectiveness(self, strategy: RemediationOption, gap_result: GapResult) -> float:
        """
        Estimate the effectiveness of a remediation strategy for a specific gap.
        
        Args:
            strategy: The remediation strategy to evaluate
            gap_result: The gap analysis result being remediated
            
        Returns:
            Effectiveness score (0-100)
        """
        impact_metrics = strategy.impact_metrics
        
        # Base effectiveness on gap reduction percentage
        effectiveness = impact_metrics.get("gap_reduction_percentage", 0)
        
        # Penalize timeframe extensions
        if "timeframe_extension" in impact_metrics:
            extension = impact_metrics["timeframe_extension"]
            if extension > 0:
                # Penalty increases with extension size
                penalty = extension * 20  # 20% penalty per 100% extension
                effectiveness -= penalty
        
        # Penalize target reductions
        if "target_adjustment" in impact_metrics:
            adjustment = impact_metrics["target_adjustment"]
            if adjustment < 0:  # Negative adjustment = reduction
                # Convert to percentage of overall target
                reduction_pct = abs(adjustment) / gap_result.target_amount * 100
                penalty = reduction_pct * 0.5  # 0.5% penalty per 1% reduction
                effectiveness -= penalty
        
        # Bonus for strategies that increase income rather than cutting expenses
        if "monthly_income_increase" in impact_metrics:
            effectiveness += 10
            
        # Ensure score stays in valid range
        return max(0, min(100, effectiveness))


class TimeframeAdjustment:
    """
    Specialized remediation strategy focusing on goal timeframe adjustments.
    
    This class provides methods to calculate and evaluate timeframe extensions
    for goals with funding gaps, balancing feasibility with minimal delay.
    Considers Indian financial context including inflation impacts.
    """
    
    def __init__(self):
        """Initialize with financial parameter service access"""
        self.param_service = get_financial_parameter_service()
        
        # Initialize default parameters
        self.params = {
            "inflation_rate": 0.06,  # 6% annual inflation in India
            "min_extension_months": 3,  # Minimum practical extension
            "max_extension_ratio": 0.50,  # Maximum extension as percentage of original timeframe
            "optimal_extension_factor": 0.25,  # Target extension as percentage of original timeframe
            "culturally_sensitive_goals": ["wedding", "education", "religious_ceremony"]  # Goals with cultural timeframe sensitivity
        }
        
        # Load parameters from service if available
        if self.param_service:
            try:
                service_params = self.param_service.get_all_parameters()
                # Update default params with those from the service
                for key, value in service_params.items():
                    if key in self.params and not isinstance(self.params[key], dict):
                        self.params[key] = value
                    elif key in self.params and isinstance(self.params[key], dict):
                        if isinstance(value, dict):
                            for nested_key, nested_value in value.items():
                                if nested_key in self.params[key]:
                                    self.params[key][nested_key] = nested_value
            except Exception as e:
                logger.error(f"Error loading parameters for timeframe adjustment: {str(e)}")
    
    def extend_goal_deadline(self, goal, extension_months: int) -> datetime:
        """
        Calculate a new target date by extending the current deadline.
        
        Args:
            goal: The goal object to extend
            extension_months: Number of months to extend
            
        Returns:
            datetime: New target date
        """
        try:
            # Extract current timeframe as datetime
            if isinstance(goal, dict):
                timeframe_str = goal.get('timeframe', '')
            else:
                timeframe_str = getattr(goal, 'timeframe', '')
            
            # Parse the timeframe string to datetime
            if not timeframe_str:
                # If no timeframe, use current date + 1 year as base
                current_target = datetime.now()
            else:
                try:
                    # Try ISO format first
                    current_target = datetime.fromisoformat(timeframe_str.replace('Z', '+00:00'))
                except ValueError:
                    # Try other common formats
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            current_target = datetime.strptime(timeframe_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        # If no format matches, use current date
                        current_target = datetime.now()
            
            # Calculate new target date
            new_target = current_target
            # Add months properly
            month = new_target.month - 1 + extension_months
            year = new_target.year + month // 12
            month = month % 12 + 1
            
            # Handle day-of-month issues (e.g., adding months to Jan 31 could give Feb 31)
            day = min(new_target.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 
                                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
            
            new_target = new_target.replace(year=year, month=month, day=day)
            
            return new_target
            
        except Exception as e:
            logger.error(f"Error extending goal deadline: {str(e)}")
            # Return a safe fallback (current date + extension_months)
            return datetime.now() + timedelta(days=extension_months * 30)
    
    def estimate_required_extension(self, goal, gap_result: GapResult, profile: dict) -> int:
        """
        Determine the minimum timeframe extension needed to make the goal feasible.
        
        Args:
            goal: The goal object to analyze
            gap_result: Gap analysis result
            profile: User profile data
            
        Returns:
            int: Required extension in months
        """
        # Start with the timeframe gap from gap analysis
        base_extension = gap_result.timeframe_gap
        
        if base_extension <= 0:
            # If no timeframe gap in the analysis, calculate based on capacity gap
            monthly_capacity = self._calculate_monthly_capacity(profile)
            if monthly_capacity <= 0:
                return self.params["min_extension_months"]
            
            # Calculate months needed to close the gap at current capacity
            if gap_result.gap_amount > 0:
                base_extension = math.ceil(gap_result.gap_amount / monthly_capacity)
        
        # Apply minimum extension
        extension_months = max(base_extension, self.params["min_extension_months"])
        
        # Check if this is a culturally sensitive goal category
        is_sensitive = False
        if isinstance(goal, dict):
            category = goal.get('category', '').lower()
        else:
            category = getattr(goal, 'category', '').lower()
            
        if category in self.params["culturally_sensitive_goals"]:
            is_sensitive = True
            
        # For culturally sensitive goals, limit extension more strictly
        if is_sensitive:
            # Calculate original timeframe in months
            original_months = self._calculate_original_timeframe_months(goal)
            # Limit to 15% of original timeframe for sensitive goals
            max_extension = max(3, int(original_months * 0.15))
            extension_months = min(extension_months, max_extension)
            
        return extension_months
    
    def analyze_timeframe_impact(self, goal, extension_months: int, profile: dict) -> Dict[str, Any]:
        """
        Evaluate the effects of a timeframe extension on the goal.
        
        Args:
            goal: The goal object to analyze
            extension_months: Proposed extension in months
            profile: User profile data
            
        Returns:
            dict: Detailed impact analysis
        """
        # Initialize impact metrics
        impact = {
            "extension_months": extension_months,
            "original_target_date": None,
            "new_target_date": None,
            "monthly_contribution_reduction": 0.0,
            "inflation_impact": 0.0,
            "feasibility_improvement": 0.0,
            "cultural_impact": "None"
        }
        
        try:
            # Extract current target date
            if isinstance(goal, dict):
                timeframe_str = goal.get('timeframe', '')
                target_amount = goal.get('target_amount', 0.0)
                current_amount = goal.get('current_amount', 0.0)
                category = goal.get('category', '').lower()
            else:
                timeframe_str = getattr(goal, 'timeframe', '')
                target_amount = getattr(goal, 'target_amount', 0.0)
                current_amount = getattr(goal, 'current_amount', 0.0)
                category = getattr(goal, 'category', '').lower()
            
            # Parse the timeframe
            try:
                original_date = datetime.fromisoformat(timeframe_str.replace('Z', '+00:00'))
                impact["original_target_date"] = original_date.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                # Default to current date if parsing fails
                original_date = datetime.now()
                impact["original_target_date"] = "Not specified"
            
            # Calculate new target date
            new_date = self.extend_goal_deadline(goal, extension_months)
            impact["new_target_date"] = new_date.strftime('%Y-%m-%d')
            
            # Calculate monthly contribution reduction
            original_months = self._calculate_original_timeframe_months(goal)
            if original_months > 0:
                new_months = original_months + extension_months
                
                # Simple calculation for monthly contribution reduction
                amount_needed = target_amount - current_amount
                if amount_needed > 0:
                    original_monthly = amount_needed / original_months
                    new_monthly = amount_needed / new_months
                    impact["monthly_contribution_reduction"] = original_monthly - new_monthly
            
            # Calculate inflation impact
            inflation_rate = self.params["inflation_rate"]
            years_extended = extension_months / 12
            
            # Compound inflation effect on target amount
            inflation_impact = target_amount * ((1 + inflation_rate) ** years_extended - 1)
            impact["inflation_impact"] = inflation_impact
            
            # Estimate feasibility improvement (0-100 scale)
            if original_months > 0:
                # Base improvement on percentage reduction in monthly contribution
                improvement = (impact["monthly_contribution_reduction"] / (amount_needed / original_months)) * 100
                impact["feasibility_improvement"] = min(100, max(0, improvement))
            
            # Cultural impact assessment for certain goal types
            if category in self.params["culturally_sensitive_goals"]:
                if extension_months <= 3:
                    impact["cultural_impact"] = "Minimal"
                elif extension_months <= 6:
                    impact["cultural_impact"] = "Moderate"
                else:
                    impact["cultural_impact"] = "Significant"
            
            return impact
            
        except Exception as e:
            logger.error(f"Error analyzing timeframe impact: {str(e)}")
            return impact
    
    def get_optimal_extension(self, goal, gap_result: GapResult, profile: dict) -> Tuple[int, Dict[str, Any]]:
        """
        Calculate an optimal timeframe extension that balances feasibility with minimal delay.
        
        Args:
            goal: The goal object to analyze
            gap_result: Gap analysis result
            profile: User profile data
            
        Returns:
            tuple: (optimal_extension_months, impact_analysis)
        """
        # First get the minimum required extension
        required_extension = self.estimate_required_extension(goal, gap_result, profile)
        
        # Calculate original timeframe in months
        original_months = self._calculate_original_timeframe_months(goal)
        
        # Apply optimal extension factor (target percentage of original timeframe)
        optimal_factor = self.params["optimal_extension_factor"]
        target_extension = max(required_extension, int(original_months * optimal_factor))
        
        # Apply maximum extension constraint
        max_extension = max(6, int(original_months * self.params["max_extension_ratio"]))
        optimal_extension = min(target_extension, max_extension)
        
        # Analyze impact of the optimal extension
        impact = self.analyze_timeframe_impact(goal, optimal_extension, profile)
        
        return optimal_extension, impact
    
    def _calculate_monthly_capacity(self, profile: dict) -> float:
        """
        Calculate user's monthly savings capacity.
        
        Args:
            profile: User profile data
            
        Returns:
            float: Estimated monthly savings capacity
        """
        # Default capacity if we can't calculate from profile
        default_capacity = 1000.0
        
        try:
            # Extract income and expenses from profile
            if 'income' in profile:
                income = profile['income']
                if isinstance(income, dict) and 'amount' in income:
                    monthly_income = income['amount']
                    if income.get('frequency', '').lower() in ['annual', 'yearly']:
                        monthly_income /= 12
                else:
                    monthly_income = float(income)
            else:
                # Look in answers
                if 'answers' in profile:
                    for answer in profile['answers']:
                        if 'income' in answer.get('question_id', '').lower():
                            value = answer.get('answer')
                            if isinstance(value, (int, float)):
                                monthly_income = float(value)
                                break
                            elif isinstance(value, dict) and 'amount' in value:
                                monthly_income = float(value['amount'])
                                if value.get('frequency', '').lower() in ['annual', 'yearly']:
                                    monthly_income /= 12
                                break
                            elif isinstance(value, str) and value.replace('.', '', 1).isdigit():
                                monthly_income = float(value)
                                break
                    else:
                        # No income found in answers
                        monthly_income = 5000.0
                else:
                    monthly_income = 5000.0
            
            # Extract expenses similarly
            if 'expenses' in profile:
                expenses = profile['expenses']
                if isinstance(expenses, dict) and 'amount' in expenses:
                    monthly_expenses = expenses['amount']
                    if expenses.get('frequency', '').lower() in ['annual', 'yearly']:
                        monthly_expenses /= 12
                else:
                    monthly_expenses = float(expenses)
            else:
                # Estimate as percentage of income if not found
                monthly_expenses = monthly_income * 0.7
            
            # Calculate disposable income (capacity)
            capacity = max(0, monthly_income - monthly_expenses)
            
            # Apply a savings factor (not all disposable income goes to goals)
            savings_factor = 0.5  # 50% of disposable income available for goals
            return capacity * savings_factor
            
        except Exception as e:
            logger.error(f"Error calculating monthly capacity: {str(e)}")
            return default_capacity
    
    def _calculate_original_timeframe_months(self, goal) -> int:
        """
        Calculate the original timeframe of the goal in months.
        
        Args:
            goal: The goal object
            
        Returns:
            int: Original timeframe in months
        """
        try:
            # Extract timeframe
            if isinstance(goal, dict):
                timeframe_str = goal.get('timeframe', '')
            else:
                timeframe_str = getattr(goal, 'timeframe', '')
            
            # If no timeframe, return a default
            if not timeframe_str:
                return 36  # Default to 3 years
            
            # Try to parse timeframe
            try:
                target_date = datetime.fromisoformat(timeframe_str.replace('Z', '+00:00'))
                today = datetime.now()
                
                # Calculate months between today and target date
                months = (target_date.year - today.year) * 12 + target_date.month - today.month
                # Adjust for day of month
                if target_date.day < today.day:
                    months -= 1
                    
                return max(1, months)  # Ensure at least 1 month
                
            except ValueError:
                # Alternative: check if it's a time_horizon in years
                if isinstance(goal, dict) and 'time_horizon' in goal:
                    years = float(goal['time_horizon'])
                    return int(years * 12)
                elif hasattr(goal, 'time_horizon'):
                    years = float(goal.time_horizon)
                    return int(years * 12)
                
                # Default fallback
                return 36
                
        except Exception as e:
            logger.error(f"Error calculating original timeframe: {str(e)}")
            return 36  # Default to 3 years


class AllocationAdjustment:
    """
    Specialized remediation strategy focusing on asset allocation adjustments.
    
    This class provides methods to calculate and evaluate asset allocation changes
    for goals with funding gaps, balancing risk and return to improve goal feasibility.
    Includes support for Indian investment context with specialized handling for
    gold allocation and tax-efficient instruments like ELSS funds.
    """
    
    def __init__(self):
        """Initialize with financial parameter service access"""
        self.param_service = get_financial_parameter_service()
        
        # Initialize default parameters
        self.params = {
            "max_risk_increment": 0.15,    # Maximum risk level increment (percentage)
            "gold_allocation_range": {     # Valid gold allocation range (India-specific)
                "min": 0.05,
                "max": 0.25
            },
            "equity_returns": {            # Expected returns by risk level
                "conservative": 0.09,      # 9% for conservative equity portfolio
                "moderate": 0.12,          # 12% for moderate equity portfolio
                "aggressive": 0.15         # 15% for aggressive equity portfolio
            },
            "debt_returns": {
                "conservative": 0.06,      # 6% for conservative debt instruments
                "moderate": 0.07,          # 7% for moderate debt instruments
                "aggressive": 0.08         # 8% for aggressive debt instruments 
            },
            "gold_returns": 0.08,          # 8% for gold investments
            "sip_minimum": 500,            # Minimum SIP amount in rupees
            "elss_allocation_max": 0.30,   # Maximum allocation to ELSS funds
            "risk_transition_months": 6    # Months to transition to higher risk allocation
        }
        
        # Load parameters from service if available
        if self.param_service:
            try:
                service_params = self.param_service.get_all_parameters()
                # Update default params with those from the service
                for key, value in service_params.items():
                    if key in self.params and not isinstance(self.params[key], dict):
                        self.params[key] = value
                    elif key in self.params and isinstance(self.params[key], dict):
                        if isinstance(value, dict):
                            for nested_key, nested_value in value.items():
                                if nested_key in self.params[key]:
                                    self.params[key][nested_key] = nested_value
            except Exception as e:
                logger.error(f"Error loading parameters for allocation adjustment: {str(e)}")
    
    def increase_investment_risk(self, allocation: Dict[str, float], risk_increment: float) -> Dict[str, float]:
        """
        Adjust asset allocation to increase investment risk and potential returns.
        
        Args:
            allocation: Current asset allocation dictionary
            risk_increment: Percentage points to increase risk (0-1 scale)
            
        Returns:
            dict: Adjusted asset allocation
        """
        # Validate and limit risk increment
        risk_increment = min(self.params["max_risk_increment"], max(0, risk_increment))
        
        # Create a copy of the allocation
        adjusted = allocation.copy()
        
        # Get current equity and debt allocations
        equity_pct = adjusted.get('equity', 0)
        debt_pct = adjusted.get('debt', 0)
        gold_pct = adjusted.get('gold', 0)
        cash_pct = adjusted.get('cash', 0)
        
        # Calculate new equity allocation
        new_equity_pct = min(0.85, equity_pct + risk_increment)
        equity_increase = new_equity_pct - equity_pct
        
        # Reduce other asset classes proportionally
        total_other = debt_pct + gold_pct + cash_pct
        if total_other > 0:
            # Calculate reduction proportions
            debt_proportion = debt_pct / total_other
            gold_proportion = gold_pct / total_other
            cash_proportion = cash_pct / total_other
            
            # Apply reductions
            adjusted['debt'] = max(0.05, debt_pct - (equity_increase * debt_proportion))
            adjusted['gold'] = max(self.params["gold_allocation_range"]["min"], 
                                 gold_pct - (equity_increase * gold_proportion))
            adjusted['cash'] = max(0.02, cash_pct - (equity_increase * cash_proportion))
        else:
            # If no other assets, set minimal allocations
            adjusted['debt'] = 0.10
            adjusted['gold'] = 0.05
            adjusted['cash'] = 0.05
            
        # Set new equity allocation
        adjusted['equity'] = new_equity_pct
        
        # Normalize to ensure sum is 1.0
        total = sum(adjusted.values())
        if total != 1.0:
            for key in adjusted:
                adjusted[key] /= total
        
        return adjusted
    
    def optimize_allocation_for_goal(self, goal, gap_result: GapResult, profile: dict) -> Dict[str, Any]:
        """
        Determine optimal asset allocation based on goal characteristics and gap analysis.
        
        Args:
            goal: Goal object being analyzed
            gap_result: Gap analysis result
            profile: User profile data
            
        Returns:
            dict: Optimization results including new allocation and expected impact
        """
        try:
            # Extract current allocation if available
            current_allocation = None
            if isinstance(goal, dict) and 'asset_allocation' in goal:
                current_allocation = goal['asset_allocation']
            elif hasattr(goal, 'asset_allocation'):
                current_allocation = getattr(goal, 'asset_allocation')
            
            # If no current allocation, get from calculator
            if not current_allocation:
                # Import locally to avoid circular imports
                from models.goal_calculators.base_calculator import GoalCalculator
                calculator = GoalCalculator.get_calculator_for_goal(goal)
                current_allocation = calculator.get_recommended_allocation(goal, profile)
            
            # Extract gap severity and timeframe
            severity = gap_result.severity
            timeframe_months = 0
            
            if isinstance(goal, dict):
                timeframe_str = goal.get('timeframe', '')
            else:
                timeframe_str = getattr(goal, 'timeframe', '')
                
            # Calculate months to goal
            if timeframe_str:
                try:
                    target_date = datetime.fromisoformat(timeframe_str.replace('Z', '+00:00'))
                    today = datetime.now()
                    timeframe_months = ((target_date.year - today.year) * 12 + 
                                      target_date.month - today.month)
                except (ValueError, AttributeError):
                    # Use gap result timeframe as fallback
                    timeframe_months = gap_result.timeframe_gap
            
            # Determine appropriate risk increment based on gap severity and timeframe
            risk_increment = 0.0
            
            if severity == GapSeverity.CRITICAL:
                risk_increment = 0.15
            elif severity == GapSeverity.SIGNIFICANT:
                risk_increment = 0.10
            elif severity == GapSeverity.MODERATE:
                risk_increment = 0.05
            else:  # MINOR
                risk_increment = 0.02
                
            # Adjust risk increment based on timeframe
            # Less aggressive for shorter timeframes
            if timeframe_months < 12:
                risk_increment *= 0.5
            elif timeframe_months < 36:
                risk_increment *= 0.8
            elif timeframe_months > 120:  # 10+ years
                risk_increment *= 1.2
            
            # Increase investment risk
            optimized_allocation = self.increase_investment_risk(current_allocation, risk_increment)
            
            # Calculate expected return improvement
            return_improvement = self.calculate_expected_return_improvement(
                current_allocation, optimized_allocation)
            
            # Assess risk tolerance compatibility
            compatibility_score = self.estimate_risk_tolerance_compatibility(
                optimized_allocation, profile)
            
            # Create transition plan
            transition_plan = self.generate_allocation_transition_plan(
                current_allocation, optimized_allocation)
            
            # Calculate impact on gap
            gap_impact = self._calculate_gap_impact(
                gap_result, return_improvement, timeframe_months)
            
            # Generate India-specific recommendations
            india_recommendations = self._generate_india_specific_recommendations(
                optimized_allocation, goal)
            
            # Create result dictionary
            result = {
                "current_allocation": current_allocation,
                "optimized_allocation": optimized_allocation,
                "return_improvement": return_improvement,
                "risk_increment": risk_increment,
                "compatibility_score": compatibility_score,
                "transition_plan": transition_plan,
                "gap_impact": gap_impact,
                "india_recommendations": india_recommendations
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in optimize_allocation_for_goal: {str(e)}")
            # Return minimal result in case of error
            return {
                "current_allocation": current_allocation or {"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05},
                "optimized_allocation": {"equity": 0.7, "debt": 0.2, "gold": 0.05, "cash": 0.05},
                "return_improvement": 0.01,
                "risk_increment": 0.05,
                "compatibility_score": 0.7,
                "error": str(e)
            }
    
    def calculate_expected_return_improvement(self, current_allocation: Dict[str, float], 
                                           adjusted_allocation: Dict[str, float]) -> float:
        """
        Estimate the improvement in expected returns from an allocation adjustment.
        
        Args:
            current_allocation: Current asset allocation
            adjusted_allocation: Adjusted asset allocation
            
        Returns:
            float: Expected annual return improvement (percentage points)
        """
        # Get expected returns for each asset class
        equity_return = self.params["equity_returns"]["moderate"]
        debt_return = self.params["debt_returns"]["moderate"]
        gold_return = self.params["gold_returns"]
        cash_return = 0.04  # 4% for cash
        
        # Calculate expected return for current allocation
        current_return = (
            current_allocation.get('equity', 0) * equity_return +
            current_allocation.get('debt', 0) * debt_return +
            current_allocation.get('gold', 0) * gold_return +
            current_allocation.get('cash', 0) * cash_return
        )
        
        # Calculate expected return for adjusted allocation
        adjusted_return = (
            adjusted_allocation.get('equity', 0) * equity_return +
            adjusted_allocation.get('debt', 0) * debt_return +
            adjusted_allocation.get('gold', 0) * gold_return +
            adjusted_allocation.get('cash', 0) * cash_return
        )
        
        # Return the improvement in percentage points
        return adjusted_return - current_return
    
    def generate_allocation_transition_plan(self, current_allocation: Dict[str, float], 
                                        target_allocation: Dict[str, float]) -> Dict[str, Any]:
        """
        Create a gradual transition plan for shifting to a new asset allocation.
        Follows SIP approach popular in Indian investment context.
        
        Args:
            current_allocation: Current asset allocation
            target_allocation: Target asset allocation
            
        Returns:
            dict: Transition plan with steps and timeline
        """
        # Calculate allocation differences
        differences = {}
        for asset, target_pct in target_allocation.items():
            current_pct = current_allocation.get(asset, 0)
            differences[asset] = target_pct - current_pct
        
        # Determine transition period in months based on magnitude of change
        max_difference = max(abs(diff) for diff in differences.values())
        transition_months = min(12, max(3, int(max_difference * 100 / 5)))
        
        # Calculate monthly allocation changes
        monthly_changes = {asset: diff / transition_months for asset, diff in differences.items()}
        
        # Generate monthly allocations
        monthly_allocations = []
        current = current_allocation.copy()
        
        for month in range(1, transition_months + 1):
            # Update allocation for this month
            for asset, change in monthly_changes.items():
                if asset not in current:
                    current[asset] = 0
                current[asset] += change
            
            # Normalize to ensure sum is 1.0
            total = sum(current.values())
            normalized = {asset: pct / total for asset, pct in current.items()}
            
            # Add to monthly allocations
            monthly_allocations.append({
                "month": month,
                "allocation": normalized.copy()
            })
        
        # Calculate SIP adjustment recommendations (India-specific)
        sip_recommendations = self._calculate_sip_adjustments(
            current_allocation, target_allocation, transition_months)
        
        # Create transition plan
        plan = {
            "transition_months": transition_months,
            "monthly_allocations": monthly_allocations,
            "sip_recommendations": sip_recommendations,
            "elss_recommendation": self._calculate_elss_recommendation(target_allocation)
        }
        
        return plan
    
    def estimate_risk_tolerance_compatibility(self, adjusted_allocation: Dict[str, float], 
                                           profile: dict) -> float:
        """
        Assess how well the adjusted allocation matches the user's risk tolerance.
        
        Args:
            adjusted_allocation: Adjusted asset allocation
            profile: User profile data
            
        Returns:
            float: Compatibility score (0-1 scale, higher is better)
        """
        # Extract risk tolerance from profile
        risk_tolerance = "moderate"  # Default
        
        try:
            # Look for risk tolerance in profile
            if 'risk_tolerance' in profile:
                tolerance = profile['risk_tolerance'].lower()
                if 'conservative' in tolerance or 'low' in tolerance:
                    risk_tolerance = "conservative"
                elif 'aggressive' in tolerance or 'high' in tolerance:
                    risk_tolerance = "aggressive"
                else:
                    risk_tolerance = "moderate"
            
            # Look in answers if not found directly
            elif 'answers' in profile:
                for answer in profile['answers']:
                    if 'risk' in answer.get('question_id', '').lower():
                        value = answer.get('answer', '')
                        if isinstance(value, str):
                            if 'conservative' in value.lower() or 'low' in value.lower():
                                risk_tolerance = "conservative"
                            elif 'aggressive' in value.lower() or 'high' in value.lower():
                                risk_tolerance = "aggressive"
                            break
        except Exception as e:
            logger.error(f"Error extracting risk tolerance: {str(e)}")
        
        # Define ideal allocations by risk tolerance
        ideal_allocations = {
            "conservative": {"equity": 0.3, "debt": 0.5, "gold": 0.15, "cash": 0.05},
            "moderate": {"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05},
            "aggressive": {"equity": 0.8, "debt": 0.1, "gold": 0.05, "cash": 0.05}
        }
        
        # Calculate deviation from ideal allocation
        ideal = ideal_allocations[risk_tolerance]
        total_deviation = 0
        
        for asset in ideal:
            ideal_pct = ideal.get(asset, 0)
            adjusted_pct = adjusted_allocation.get(asset, 0)
            deviation = abs(ideal_pct - adjusted_pct)
            total_deviation += deviation
        
        # Convert to compatibility score (0-1 scale)
        # Max possible deviation is 2.0 (complete mismatch), so normalize to 0-1
        compatibility = 1.0 - (total_deviation / 2.0)
        
        return max(0, min(1, compatibility))
    
    def _calculate_gap_impact(self, gap_result: GapResult, return_improvement: float, 
                          timeframe_months: int) -> Dict[str, float]:
        """
        Calculate the impact of return improvement on the funding gap.
        
        Args:
            gap_result: Gap analysis result
            return_improvement: Expected return improvement
            timeframe_months: Months to goal
            
        Returns:
            dict: Gap impact metrics
        """
        # Convert return improvement to monthly
        monthly_improvement = (1 + return_improvement) ** (1/12) - 1
        
        # Calculate impact on gap amount
        current_amount = gap_result.current_amount
        gap_amount = gap_result.gap_amount
        
        # Calculate new final amount with improved returns
        improved_final_amount = current_amount * (1 + monthly_improvement) ** timeframe_months
        new_gap = gap_result.target_amount - improved_final_amount
        
        # Calculate gap reduction
        gap_reduction = gap_amount - new_gap
        gap_reduction_percentage = (gap_reduction / gap_amount) * 100 if gap_amount > 0 else 0
        
        return {
            "gap_reduction": gap_reduction,
            "gap_reduction_percentage": gap_reduction_percentage,
            "improved_final_amount": improved_final_amount,
            "new_gap": new_gap
        }
    
    def _calculate_sip_adjustments(self, current_allocation: Dict[str, float], 
                                target_allocation: Dict[str, float], 
                                transition_months: int) -> Dict[str, Any]:
        """
        Calculate SIP (Systematic Investment Plan) adjustments to reach target allocation.
        
        Args:
            current_allocation: Current asset allocation
            target_allocation: Target asset allocation
            transition_months: Number of months for transition
            
        Returns:
            dict: SIP adjustment recommendations
        """
        # Assume a base monthly SIP of 10,000 rupees
        base_sip = 10000
        
        # Calculate current SIP distribution
        current_sip = {asset: base_sip * pct for asset, pct in current_allocation.items()}
        
        # Calculate target SIP distribution
        target_sip = {asset: base_sip * pct for asset, pct in target_allocation.items()}
        
        # Calculate SIP changes
        sip_changes = {}
        for asset in set(target_allocation.keys()).union(current_allocation.keys()):
            current = current_sip.get(asset, 0)
            target = target_sip.get(asset, 0)
            sip_changes[asset] = target - current
        
        # Create SIP recommendations
        recommendations = []
        for asset, change in sip_changes.items():
            if abs(change) > self.params["sip_minimum"]:
                action = "increase" if change > 0 else "decrease"
                recommendations.append({
                    "asset_class": asset,
                    "action": action,
                    "amount": abs(change),
                    "percentage": abs(change) / base_sip * 100
                })
        
        return {
            "base_sip": base_sip,
            "current_sip": current_sip,
            "target_sip": target_sip,
            "recommendations": recommendations
        }
    
    def _calculate_elss_recommendation(self, allocation: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate ELSS (Equity Linked Savings Scheme) fund recommendations for tax efficiency.
        
        Args:
            allocation: Target asset allocation
            
        Returns:
            dict: ELSS recommendations
        """
        # Calculate recommended ELSS allocation (up to 30% of equity allocation)
        equity_allocation = allocation.get('equity', 0)
        elss_allocation = min(self.params["elss_allocation_max"], equity_allocation)
        elss_percentage = (elss_allocation / equity_allocation) * 100 if equity_allocation > 0 else 0
        
        return {
            "recommended_percentage": elss_percentage,
            "recommended_allocation": elss_allocation,
            "tax_benefit": elss_allocation > 0.05,
            "section_80c_eligible": True
        }
    
    def _generate_india_specific_recommendations(self, allocation: Dict[str, float], 
                                             goal) -> Dict[str, Any]:
        """
        Generate India-specific investment recommendations based on allocation.
        
        Args:
            allocation: Target asset allocation
            goal: Goal object
            
        Returns:
            dict: India-specific recommendations
        """
        # Extract goal category
        category = ""
        if isinstance(goal, dict):
            category = goal.get('category', '').lower()
        else:
            category = getattr(goal, 'category', '').lower()
        
        # Gold allocation recommendations (important in Indian portfolios)
        gold_recommendation = {
            "allocation": allocation.get('gold', 0),
            "digital_gold_percentage": 50,  # Recommend 50% in digital gold
            "physical_gold_percentage": 30,  # 30% in physical gold
            "gold_etf_percentage": 20       # 20% in Gold ETFs
        }
        
        # Mutual fund recommendations
        mutual_fund_types = {
            "large_cap_percentage": 40,
            "mid_cap_percentage": 30,
            "small_cap_percentage": 10,
            "multi_cap_percentage": 20
        }
        
        # Adjust based on goal category
        if category in ['retirement', 'early_retirement']:
            mutual_fund_types = {
                "large_cap_percentage": 50,
                "mid_cap_percentage": 20,
                "small_cap_percentage": 10,
                "multi_cap_percentage": 20
            }
        elif category in ['education', 'home_purchase']:
            mutual_fund_types = {
                "large_cap_percentage": 60,
                "mid_cap_percentage": 20,
                "small_cap_percentage": 0,
                "multi_cap_percentage": 20
            }
        
        # Tax efficiency recommendations
        tax_efficiency = {
            "equity": {
                "elss_funds": self._calculate_elss_recommendation(allocation),
                "long_term_holding": "Hold equity investments for >1 year for LTCG tax rate of 10%"
            },
            "debt": {
                "debt_funds": "Hold debt funds for >3 years for indexation benefits",
                "government_securities": "Consider tax-free government bonds if in high tax bracket"
            }
        }
        
        return {
            "gold_recommendation": gold_recommendation,
            "mutual_fund_types": mutual_fund_types,
            "tax_efficiency": tax_efficiency,
            "sip_approach": "Use SIP for disciplined investing and rupee cost averaging"
        }


class ContributionAdjustment:
    """
    Specialized remediation strategy focusing on contribution adjustments.
    
    This class provides methods to calculate and evaluate contribution changes
    for goals with funding gaps, identifying potential funding sources and
    creating stepped contribution plans. Includes special handling for SIP
    approaches popular in the Indian investment context.
    """
    
    def __init__(self):
        """Initialize with financial parameter service access"""
        self.param_service = get_financial_parameter_service()
        
        # Initialize default parameters
        self.params = {
            "max_contribution_increase_pct": 0.30,  # Maximum 30% increase in monthly savings
            "disposable_income_savings_cap": 0.50,  # Maximum 50% of disposable income for savings
            "expense_reduction_categories": {       # Categories for expense reduction
                "discretionary": 0.20,              # Can reduce discretionary expenses by 20%
                "lifestyle": 0.15,                  # Can reduce lifestyle expenses by 15%
                "essential": 0.05                   # Can reduce essential expenses by 5%
            },
            "typical_income_growth": {              # Typical income growth patterns in India
                "early_career": 0.12,               # 12% annual growth in early career
                "mid_career": 0.08,                 # 8% annual growth in mid-career
                "late_career": 0.05                 # 5% annual growth in late career
            },
            "stepped_contribution_months": 4,      # Default months between contribution steps
            "sip_minimum": 500,                    # Minimum SIP amount in rupees
            "goal_priority_levels": {              # Contribution priorities by goal type
                "emergency_fund": 10,              # Highest priority
                "debt_repayment": 9,
                "education": 8,
                "retirement": 7,
                "home_purchase": 6,
                "wedding": 5,
                "travel": 3,
                "luxury": 1                        # Lowest priority
            }
        }
        
        # Load parameters from service if available
        if self.param_service:
            try:
                service_params = self.param_service.get_all_parameters()
                # Update default params with those from the service
                for key, value in service_params.items():
                    if key in self.params and not isinstance(self.params[key], dict):
                        self.params[key] = value
                    elif key in self.params and isinstance(self.params[key], dict):
                        if isinstance(value, dict):
                            for nested_key, nested_value in value.items():
                                if nested_key in self.params[key]:
                                    self.params[key][nested_key] = nested_value
            except Exception as e:
                logger.error(f"Error loading parameters for contribution adjustment: {str(e)}")
    
    def increase_monthly_saving(self, goal, income_projection) -> Dict[str, Any]:
        """
        Determine the additional monthly savings needed to achieve a goal.
        
        Args:
            goal: Goal object to analyze
            income_projection: Income projection object or data
            
        Returns:
            dict: Monthly saving increase details
        """
        try:
            # Extract goal details
            if isinstance(goal, dict):
                target_amount = goal.get('target_amount', 0)
                current_amount = goal.get('current_amount', 0)
                timeframe_str = goal.get('timeframe', '')
            else:
                target_amount = getattr(goal, 'target_amount', 0)
                current_amount = getattr(goal, 'current_amount', 0)
                timeframe_str = getattr(goal, 'timeframe', '')
            
            # Calculate timeframe in months
            timeframe_months = 0
            try:
                if timeframe_str:
                    target_date = datetime.fromisoformat(timeframe_str.replace('Z', '+00:00'))
                    today = datetime.now()
                    timeframe_months = (target_date.year - today.year) * 12 + target_date.month - today.month
                    if target_date.day < today.day:
                        timeframe_months -= 1
            except Exception:
                # Default to 60 months (5 years) if timeframe can't be determined
                timeframe_months = 60
            
            if timeframe_months <= 0:
                return {
                    "error": "Goal timeframe is in the past or not specified",
                    "additional_monthly": 0,
                    "feasibility": 0
                }
                
            # Calculate the amount needed to meet the goal
            amount_needed = target_amount - current_amount
            
            if amount_needed <= 0:
                return {
                    "additional_monthly": 0,
                    "current_contribution": 0,
                    "new_contribution": 0,
                    "feasibility": 1.0,
                    "goal_already_achieved": True
                }
            
            # Calculate simple monthly savings required
            simple_monthly = amount_needed / timeframe_months
            
            # Adjust for investment returns (assuming moderate returns)
            monthly_return_rate = 0.08 / 12  # 8% annual return, converted to monthly
            
            # Use future value of annuity formula to calculate monthly savings with returns
            # FV = PMT * ((1 + r)^n - 1) / r
            # Solving for PMT: PMT = FV * r / ((1 + r)^n - 1)
            adjusted_monthly = amount_needed * monthly_return_rate / ((1 + monthly_return_rate) ** timeframe_months - 1)
            
            # Extract current monthly contribution if available
            current_contribution = 0
            if isinstance(goal, dict) and 'monthly_contribution' in goal:
                current_contribution = goal['monthly_contribution']
            elif hasattr(goal, 'monthly_contribution'):
                current_contribution = getattr(goal, 'monthly_contribution')
            
            # Calculate additional contribution needed
            additional_monthly = max(0, adjusted_monthly - current_contribution)
            
            # Calculate new total contribution
            new_contribution = current_contribution + additional_monthly
            
            # Calculate estimated income information from income projection
            income_estimate = self._extract_income_estimate(income_projection)
            feasibility = self.analyze_affordability(additional_monthly, income_estimate)
            
            # Create result with Indian context (SIP approach)
            result = {
                "additional_monthly": additional_monthly,
                "current_contribution": current_contribution,
                "new_contribution": new_contribution,
                "amount_needed": amount_needed,
                "timeframe_months": timeframe_months,
                "simple_monthly": simple_monthly,  # Without investment returns
                "adjusted_monthly": adjusted_monthly,  # With investment returns
                "feasibility": feasibility["feasibility_score"],
                "affordability_analysis": feasibility,
                "sip_recommendation": self._create_sip_recommendation(new_contribution)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in increase_monthly_saving: {str(e)}")
            return {
                "error": str(e),
                "additional_monthly": 0,
                "feasibility": 0
            }
    
    def analyze_affordability(self, additional_contribution: float, profile: dict) -> Dict[str, Any]:
        """
        Check the feasibility of an additional monthly contribution.
        
        Args:
            additional_contribution: Additional monthly contribution amount
            profile: User profile or income data
            
        Returns:
            dict: Affordability analysis results
        """
        # Extract monthly income and expenses
        monthly_income = self._extract_monthly_income(profile)
        monthly_expenses = self._extract_monthly_expenses(profile)
        
        # Calculate disposable income
        disposable_income = max(0, monthly_income - monthly_expenses)
        
        # Get current savings amount
        current_savings = self._extract_current_savings(profile)
        
        # Calculate available capacity for additional savings
        max_savings_capacity = disposable_income * self.params["disposable_income_savings_cap"]
        available_capacity = max(0, max_savings_capacity - current_savings)
        
        # Calculate affordability metrics
        if additional_contribution <= 0:
            affordability_ratio = 10.0  # Very affordable
        else:
            affordability_ratio = available_capacity / additional_contribution
            
        # Determine feasibility score (0-1)
        if affordability_ratio >= 2.0:
            feasibility_score = 1.0  # Easily affordable
        elif affordability_ratio >= 1.0:
            feasibility_score = 0.8  # Affordable
        elif affordability_ratio >= 0.5:
            feasibility_score = 0.5  # Challenging but possible
        elif affordability_ratio > 0:
            feasibility_score = 0.3  # Very challenging
        else:
            feasibility_score = 0.1  # Not affordable
        
        # Calculate percentage of disposable income
        pct_of_disposable = (additional_contribution / disposable_income * 100) if disposable_income > 0 else 100
        
        # Create result
        result = {
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "disposable_income": disposable_income,
            "current_savings": current_savings,
            "available_capacity": available_capacity,
            "affordability_ratio": affordability_ratio,
            "feasibility_score": feasibility_score,
            "percentage_of_disposable": pct_of_disposable,
            "expense_reduction_potential": self._calculate_expense_reduction_potential(monthly_expenses)
        }
        
        return result
    
    def suggest_expense_reductions(self, profile: dict, required_amount: float) -> Dict[str, Any]:
        """
        Suggest expense categories that could be reduced to fund savings.
        
        Args:
            profile: User profile data
            required_amount: Amount of additional savings needed
            
        Returns:
            dict: Expense reduction suggestions
        """
        # Get expense breakdown from profile or use defaults
        expense_breakdown = self._extract_expense_breakdown(profile)
        
        # Calculate reduction potential for each category
        reduction_potential = {}
        total_potential = 0
        
        for category, amount in expense_breakdown.items():
            # Determine reduction percentage based on category
            if category.lower() in ['entertainment', 'dining', 'shopping', 'vacation', 'travel']:
                category_type = 'discretionary'
            elif category.lower() in ['housing', 'food', 'healthcare', 'education', 'childcare']:
                category_type = 'essential'
            else:
                category_type = 'lifestyle'
                
            reduction_pct = self.params["expense_reduction_categories"].get(category_type, 0.05)
            potential = amount * reduction_pct
            
            reduction_potential[category] = {
                "current_amount": amount,
                "reduction_percentage": reduction_pct * 100,
                "reduction_amount": potential,
                "category_type": category_type
            }
            
            total_potential += potential
        
        # Sort categories by reduction potential (highest first)
        sorted_categories = sorted(
            reduction_potential.items(),
            key=lambda x: x[1]["reduction_amount"],
            reverse=True
        )
        
        # Create prioritized suggestions to meet required amount
        suggestions = []
        running_total = 0
        
        for category, details in sorted_categories:
            if running_total >= required_amount:
                # We have enough suggestions already
                break
                
            suggestions.append({
                "category": category,
                "amount": details["reduction_amount"],
                "percentage": details["reduction_percentage"],
                "priority": len(suggestions) + 1,
                "current_spending": details["current_amount"],
                "category_type": details["category_type"]
            })
            
            running_total += details["reduction_amount"]
        
        # Generate India-specific suggestions
        india_specific = self._generate_india_specific_expense_suggestions(profile)
        
        # Create result
        result = {
            "total_reduction_potential": total_potential,
            "required_amount": required_amount,
            "feasibility": total_potential >= required_amount,
            "coverage_percentage": (total_potential / required_amount * 100) if required_amount > 0 else 100,
            "suggestions": suggestions,
            "india_specific_suggestions": india_specific
        }
        
        return result
    
    def create_stepped_contribution_plan(self, current_amount: float, target_amount: float, 
                                      months: int) -> Dict[str, Any]:
        """
        Create a gradual monthly contribution increase plan.
        
        Args:
            current_amount: Current monthly contribution
            target_amount: Target monthly contribution
            months: Number of months for transition
            
        Returns:
            dict: Stepped contribution plan
        """
        # Ensure months is positive
        transition_months = max(1, months)
        
        # Calculate total increase needed
        total_increase = target_amount - current_amount
        
        if total_increase <= 0:
            return {
                "steps": [{"month": 1, "amount": current_amount}],
                "total_increase": 0,
                "average_increase": 0,
                "transition_months": 1
            }
        
        # Determine step interval (months between increases)
        step_interval = min(transition_months, self.params["stepped_contribution_months"])
        num_steps = max(1, math.ceil(transition_months / step_interval))
        
        # Calculate increase per step
        increase_per_step = total_increase / num_steps
        
        # Generate steps
        steps = []
        current = current_amount
        
        for step in range(num_steps + 1):
            if step == 0:
                # Starting amount
                amount = current_amount
                month = 0
            else:
                # Increment by calculated step amount
                current += increase_per_step
                amount = current
                month = step * step_interval
                
            steps.append({
                "month": month,
                "amount": amount,
                "increase_from_previous": increase_per_step if step > 0 else 0
            })
        
        # Create SIP recommendation (India-specific)
        sip_recommendation = self._create_sip_recommendation(target_amount)
        
        # Create result
        result = {
            "steps": steps,
            "total_increase": total_increase,
            "average_increase": total_increase / num_steps,
            "transition_months": transition_months,
            "step_interval": step_interval,
            "num_steps": num_steps,
            "sip_recommendation": sip_recommendation
        }
        
        return result
    
    def estimate_impact_on_other_goals(self, goals: List, additional_contribution: float, 
                                    profile: dict) -> Dict[str, Any]:
        """
        Identify potential trade-offs with other goals when increasing contribution.
        
        Args:
            goals: List of user goals
            additional_contribution: Additional monthly contribution amount
            profile: User profile data
            
        Returns:
            dict: Analysis of impact on other goals
        """
        # Extract relevant information from profile
        monthly_income = self._extract_monthly_income(profile)
        monthly_expenses = self._extract_monthly_expenses(profile)
        disposable_income = max(0, monthly_income - monthly_expenses)
        
        # Calculate total current goal contributions
        total_current_contributions = 0
        goal_contributions = []
        
        for goal in goals:
            # Extract monthly contribution
            if isinstance(goal, dict):
                contribution = goal.get('monthly_contribution', 0)
                goal_id = goal.get('id', 'unknown')
                goal_title = goal.get('title', 'Untitled Goal')
                goal_category = goal.get('category', 'other')
            else:
                contribution = getattr(goal, 'monthly_contribution', 0)
                goal_id = getattr(goal, 'id', 'unknown')
                goal_title = getattr(goal, 'title', 'Untitled Goal')
                goal_category = getattr(goal, 'category', 'other')
                
            total_current_contributions += contribution
            
            # Add to goal list
            goal_contributions.append({
                "goal_id": goal_id,
                "goal_title": goal_title,
                "goal_category": goal_category,
                "monthly_contribution": contribution
            })
        
        # Calculate affordability of all goals plus the additional contribution
        new_total_contributions = total_current_contributions + additional_contribution
        current_savings_ratio = total_current_contributions / disposable_income if disposable_income > 0 else 1
        new_savings_ratio = new_total_contributions / disposable_income if disposable_income > 0 else 1
        
        # Determine if rebalancing is needed
        rebalancing_needed = new_savings_ratio > self.params["disposable_income_savings_cap"]
        
        # If rebalancing needed, prioritize goals
        prioritized_goals = []
        if rebalancing_needed:
            # Copy goals and add priority score
            for g in goal_contributions:
                category = g["goal_category"].lower()
                priority = self.params["goal_priority_levels"].get(category, 5)
                
                prioritized_goals.append({
                    **g,
                    "priority_score": priority
                })
                
            # Sort by priority (highest first)
            prioritized_goals.sort(key=lambda x: x["priority_score"], reverse=True)
            
            # Calculate contribution adjustments
            available_for_goals = disposable_income * self.params["disposable_income_savings_cap"]
            excess_amount = new_total_contributions - available_for_goals
            
            # Adjust lower priority goals first
            remaining_excess = excess_amount
            
            for g in reversed(prioritized_goals):
                if remaining_excess <= 0:
                    break
                    
                reduction = min(g["monthly_contribution"], remaining_excess)
                g["recommended_reduction"] = reduction
                g["new_contribution"] = g["monthly_contribution"] - reduction
                
                remaining_excess -= reduction
        
        # Create result
        result = {
            "total_current_contributions": total_current_contributions,
            "new_total_contributions": new_total_contributions,
            "disposable_income": disposable_income,
            "current_savings_ratio": current_savings_ratio,
            "new_savings_ratio": new_savings_ratio,
            "rebalancing_needed": rebalancing_needed,
            "goals": goal_contributions,
            "prioritized_goals": prioritized_goals if rebalancing_needed else [],
            "max_recommended_ratio": self.params["disposable_income_savings_cap"]
        }
        
        return result
    
    def _extract_income_estimate(self, income_projection) -> Dict[str, float]:
        """
        Extract income estimate from income projection data.
        
        Args:
            income_projection: Income projection object or data
            
        Returns:
            dict: Extracted income estimate
        """
        # Initialize with default values
        income_data = {
            "monthly_income": 50000,  # Default assumption
            "monthly_growth": 0.005,  # 0.5% monthly growth
            "disposable_income_ratio": 0.3  # 30% of income is disposable
        }
        
        try:
            # Extract from IncomeProjection object
            if hasattr(income_projection, 'total_income') and income_projection.total_income:
                # Use first year income
                annual_income = income_projection.total_income[0]
                income_data["monthly_income"] = annual_income / 12
                
                # Calculate growth rate if we have multiple years
                if len(income_projection.total_income) > 1:
                    first_year = income_projection.total_income[0]
                    second_year = income_projection.total_income[1]
                    annual_growth = (second_year / first_year) - 1 if first_year > 0 else 0.06
                    income_data["monthly_growth"] = annual_growth / 12
            
            # Extract from dictionary format
            elif isinstance(income_projection, dict):
                if 'total_income' in income_projection and income_projection['total_income']:
                    annual_income = income_projection['total_income'][0]
                    income_data["monthly_income"] = annual_income / 12
                    
                    # Calculate growth rate if we have multiple years
                    if len(income_projection['total_income']) > 1:
                        first_year = income_projection['total_income'][0]
                        second_year = income_projection['total_income'][1]
                        annual_growth = (second_year / first_year) - 1 if first_year > 0 else 0.06
                        income_data["monthly_growth"] = annual_growth / 12
                
                # Try to extract disposable income ratio if available
                if 'after_tax_income' in income_projection and income_projection['after_tax_income']:
                    after_tax = income_projection['after_tax_income'][0]
                    expenses_estimate = after_tax * 0.7  # Assume 70% goes to expenses
                    disposable = after_tax - expenses_estimate
                    income_data["disposable_income_ratio"] = disposable / (annual_income / 12) if annual_income > 0 else 0.3
        
        except Exception as e:
            logger.debug(f"Error extracting income estimate: {str(e)}")
            
        return income_data
    
    def _extract_monthly_income(self, profile: dict) -> float:
        """
        Extract monthly income from profile data.
        
        Args:
            profile: User profile or income data
            
        Returns:
            float: Monthly income
        """
        # Default income
        default_income = 50000  # ₹50,000 default monthly income
        
        try:
            # Check if profile has income data directly
            if isinstance(profile, dict):
                if 'monthly_income' in profile:
                    return float(profile['monthly_income'])
                
                if 'income' in profile:
                    income_value = profile['income']
                    if isinstance(income_value, (int, float)):
                        return float(income_value)
                    elif isinstance(income_value, dict) and 'amount' in income_value:
                        amount = float(income_value['amount'])
                        if income_value.get('frequency', '').lower() in ['annual', 'yearly']:
                            return amount / 12
                        return amount
                
                # Check in answers
                if 'answers' in profile:
                    for answer in profile['answers']:
                        if 'income' in answer.get('question_id', '').lower():
                            value = answer.get('answer')
                            if isinstance(value, (int, float)):
                                return float(value)
                            elif isinstance(value, dict) and 'amount' in value:
                                amount = float(value['amount'])
                                if value.get('frequency', '').lower() in ['annual', 'yearly']:
                                    return amount / 12
                                return amount
            
            # If it's a number already, assume monthly
            if isinstance(profile, (int, float)):
                return float(profile)
            
        except Exception as e:
            logger.debug(f"Error extracting monthly income: {str(e)}")
            
        return default_income
    
    def _extract_monthly_expenses(self, profile: dict) -> float:
        """
        Extract monthly expenses from profile data.
        
        Args:
            profile: User profile or expense data
            
        Returns:
            float: Monthly expenses
        """
        try:
            # Check if profile has expense data directly
            if isinstance(profile, dict):
                if 'monthly_expenses' in profile:
                    return float(profile['monthly_expenses'])
                
                if 'expenses' in profile:
                    expense_value = profile['expenses']
                    if isinstance(expense_value, (int, float)):
                        return float(expense_value)
                    elif isinstance(expense_value, dict) and 'amount' in expense_value:
                        amount = float(expense_value['amount'])
                        if expense_value.get('frequency', '').lower() in ['annual', 'yearly']:
                            return amount / 12
                        return amount
                
                # Check in answers
                if 'answers' in profile:
                    for answer in profile['answers']:
                        if 'expense' in answer.get('question_id', '').lower():
                            value = answer.get('answer')
                            if isinstance(value, (int, float)):
                                return float(value)
                            elif isinstance(value, dict) and 'amount' in value:
                                amount = float(value['amount'])
                                if value.get('frequency', '').lower() in ['annual', 'yearly']:
                                    return amount / 12
                                return amount
            
            # If we have income, estimate expenses as 70% of income
            monthly_income = self._extract_monthly_income(profile)
            return monthly_income * 0.7
            
        except Exception as e:
            logger.debug(f"Error extracting monthly expenses: {str(e)}")
            
        # Default to 70% of income
        return self._extract_monthly_income(profile) * 0.7
    
    def _extract_current_savings(self, profile: dict) -> float:
        """
        Extract current monthly savings from profile data.
        
        Args:
            profile: User profile data
            
        Returns:
            float: Monthly savings
        """
        try:
            # Check if profile has savings data directly
            if isinstance(profile, dict):
                if 'monthly_savings' in profile:
                    return float(profile['monthly_savings'])
                
                if 'savings' in profile:
                    savings_value = profile['savings']
                    if isinstance(savings_value, (int, float)):
                        return float(savings_value)
                    elif isinstance(savings_value, dict) and 'amount' in savings_value:
                        amount = float(savings_value['amount'])
                        if savings_value.get('frequency', '').lower() in ['annual', 'yearly']:
                            return amount / 12
                        return amount
                
                # Check in answers
                if 'answers' in profile:
                    for answer in profile['answers']:
                        if 'saving' in answer.get('question_id', '').lower():
                            value = answer.get('answer')
                            if isinstance(value, (int, float)):
                                return float(value)
                            elif isinstance(value, dict) and 'amount' in value:
                                amount = float(value['amount'])
                                if value.get('frequency', '').lower() in ['annual', 'yearly']:
                                    return amount / 12
                                return amount
            
            # Estimate based on income and expenses
            monthly_income = self._extract_monthly_income(profile)
            monthly_expenses = self._extract_monthly_expenses(profile)
            estimated_savings = max(0, monthly_income - monthly_expenses)
            
            return estimated_savings
            
        except Exception as e:
            logger.debug(f"Error extracting current savings: {str(e)}")
            
        # Default to 20% of income
        return self._extract_monthly_income(profile) * 0.2
    
    def _extract_expense_breakdown(self, profile: dict) -> Dict[str, float]:
        """
        Extract expense breakdown by category from profile data.
        
        Args:
            profile: User profile data
            
        Returns:
            dict: Expense breakdown by category
        """
        # Default expense breakdown
        total_expenses = self._extract_monthly_expenses(profile)
        
        default_breakdown = {
            "Housing": total_expenses * 0.3,
            "Food": total_expenses * 0.15,
            "Transportation": total_expenses * 0.10,
            "Utilities": total_expenses * 0.08,
            "Entertainment": total_expenses * 0.08,
            "Shopping": total_expenses * 0.08,
            "Healthcare": total_expenses * 0.05,
            "Dining Out": total_expenses * 0.07,
            "Education": total_expenses * 0.05,
            "Miscellaneous": total_expenses * 0.04
        }
        
        try:
            # Check if profile has expense breakdown
            if isinstance(profile, dict) and 'expense_breakdown' in profile:
                return profile['expense_breakdown']
            
            # Check if there are categorized expenses in answers
            if isinstance(profile, dict) and 'answers' in profile:
                categories_found = {}
                
                for answer in profile['answers']:
                    question_id = answer.get('question_id', '').lower()
                    if 'expense' in question_id and 'category' in question_id:
                        category = None
                        amount = None
                        
                        # Try to extract category and amount
                        if isinstance(answer.get('answer'), dict):
                            category = answer['answer'].get('category')
                            amount = answer['answer'].get('amount')
                        
                        # If we found both, add to categories
                        if category and amount and isinstance(amount, (int, float)):
                            categories_found[category] = float(amount)
                
                # If we found categories, use them
                if categories_found:
                    # Adjust total to match expected total
                    total_found = sum(categories_found.values())
                    if total_found > 0:
                        scaling_factor = total_expenses / total_found
                        return {cat: amt * scaling_factor for cat, amt in categories_found.items()}
        
        except Exception as e:
            logger.debug(f"Error extracting expense breakdown: {str(e)}")
            
        return default_breakdown
    
    def _calculate_expense_reduction_potential(self, monthly_expenses: float) -> Dict[str, float]:
        """
        Calculate the potential for expense reduction across categories.
        
        Args:
            monthly_expenses: Total monthly expenses
            
        Returns:
            dict: Reduction potential by expense type
        """
        # Assume a breakdown of expenses by category type
        discretionary_pct = 0.25  # 25% discretionary
        lifestyle_pct = 0.35      # 35% lifestyle
        essential_pct = 0.40      # 40% essential
        
        # Calculate amounts
        discretionary = monthly_expenses * discretionary_pct
        lifestyle = monthly_expenses * lifestyle_pct
        essential = monthly_expenses * essential_pct
        
        # Calculate reduction potential
        discretionary_potential = discretionary * self.params["expense_reduction_categories"]["discretionary"]
        lifestyle_potential = lifestyle * self.params["expense_reduction_categories"]["lifestyle"]
        essential_potential = essential * self.params["expense_reduction_categories"]["essential"]
        
        total_potential = discretionary_potential + lifestyle_potential + essential_potential
        
        return {
            "discretionary": {
                "amount": discretionary,
                "reduction_potential": discretionary_potential,
                "percentage": self.params["expense_reduction_categories"]["discretionary"] * 100
            },
            "lifestyle": {
                "amount": lifestyle,
                "reduction_potential": lifestyle_potential,
                "percentage": self.params["expense_reduction_categories"]["lifestyle"] * 100
            },
            "essential": {
                "amount": essential,
                "reduction_potential": essential_potential,
                "percentage": self.params["expense_reduction_categories"]["essential"] * 100
            },
            "total_reduction_potential": total_potential,
            "total_reduction_percentage": (total_potential / monthly_expenses) * 100 if monthly_expenses > 0 else 0
        }
    
    def _create_sip_recommendation(self, monthly_amount: float) -> Dict[str, Any]:
        """
        Create SIP (Systematic Investment Plan) recommendations.
        
        Args:
            monthly_amount: Monthly contribution amount
            
        Returns:
            dict: SIP recommendations
        """
        # Minimum SIP amount
        min_sip = self.params["sip_minimum"]
        
        # Split into multiple SIPs if amount is large
        sips = []
        remaining = monthly_amount
        max_sip_size = 25000  # ₹25,000 max recommended SIP size
        
        while remaining > min_sip:
            sip_amount = min(remaining, max_sip_size)
            remaining -= sip_amount
            
            sips.append({
                "amount": sip_amount,
                "frequency": "Monthly"
            })
        
        # Add any remaining amount to the last SIP
        if sips and remaining > 0:
            sips[-1]["amount"] += remaining
        
        # Create recommendation
        recommendation = {
            "total_amount": monthly_amount,
            "number_of_sips": len(sips),
            "sips": sips,
            "debit_date": "1st of each month",  # Default recommendation
            "auto_debit": True,  # Recommend auto-debit for consistency
            "platforms": [
                "Bank direct debit",
                "AMC website",
                "Mutual fund apps"
            ]
        }
        
        return recommendation
    
    def _generate_india_specific_expense_suggestions(self, profile: dict) -> List[Dict[str, Any]]:
        """
        Generate India-specific expense reduction suggestions.
        
        Args:
            profile: User profile data
            
        Returns:
            list: India-specific expense suggestions
        """
        # Create India-specific suggestions
        suggestions = [
            {
                "category": "Utility Bills",
                "strategy": "Consider prepaid electricity for better monitoring",
                "potential_saving": "5-10%",
                "difficulty": "Low"
            },
            {
                "category": "Telecom",
                "strategy": "Switch to annual prepaid plans for better value",
                "potential_saving": "15-20%",
                "difficulty": "Low"
            },
            {
                "category": "Groceries",
                "strategy": "Use local kirana stores for better bulk pricing",
                "potential_saving": "10-15%",
                "difficulty": "Medium"
            },
            {
                "category": "Transportation",
                "strategy": "Consider metro pass or shared commute options",
                "potential_saving": "20-30%",
                "difficulty": "Medium"
            },
            {
                "category": "Entertainment",
                "strategy": "Share OTT subscriptions within family",
                "potential_saving": "40-50%",
                "difficulty": "Low"
            },
            {
                "category": "Shopping",
                "strategy": "Time purchases with festival sales (Diwali, etc.)",
                "potential_saving": "20-40%",
                "difficulty": "Medium"
            }
        ]
        
        return suggestions


class TargetAdjustment:
    """
    Specialized remediation strategy focusing on goal target amount adjustments.
    
    This class provides methods to calculate and evaluate target amount reductions
    for goals with funding gaps, preserving goal essence while ensuring feasibility.
    Considers Indian context in reductions, including cultural importance factors.
    """
    
    def __init__(self):
        """Initialize with financial parameter service access"""
        self.param_service = get_financial_parameter_service()
        
        # Initialize default parameters
        self.params = {
            "min_reduction_percentage": 0.05,  # Minimum practical reduction (5%)
            "max_reduction_percentage": 0.25,  # Maximum advised reduction (25%)
            "optimal_reduction_factor": 0.15,  # Target reduction factor (15%)
            "critical_goals": ["emergency_fund", "health_insurance", "education"],  # Goals with minimal flexibility
            "moderate_flexibility_goals": ["retirement", "debt_repayment", "home_purchase"],
            "high_flexibility_goals": ["travel", "lifestyle", "vehicle", "luxury"]
        }
        
        # Load parameters from service if available
        if self.param_service:
            try:
                service_params = self.param_service.get_all_parameters()
                # Update default params with those from the service
                for key, value in service_params.items():
                    if key in self.params and not isinstance(self.params[key], dict):
                        self.params[key] = value
                    elif key in self.params and isinstance(self.params[key], dict):
                        if isinstance(value, dict):
                            for nested_key, nested_value in value.items():
                                if nested_key in self.params[key]:
                                    self.params[key][nested_key] = nested_value
            except Exception as e:
                logger.error(f"Error loading parameters for target adjustment: {str(e)}")
    
    def reduce_goal_amount(self, goal, reduction_percentage: float) -> float:
        """
        Calculate a new target amount by reducing the current target.
        
        Args:
            goal: The goal object to adjust
            reduction_percentage: Percentage to reduce by (0-100)
            
        Returns:
            float: New target amount
        """
        try:
            # Extract current target amount
            if isinstance(goal, dict):
                current_target = goal.get('target_amount', 0.0)
            else:
                current_target = getattr(goal, 'target_amount', 0.0)
            
            # Convert percentage to decimal
            reduction_factor = min(1.0, max(0.0, reduction_percentage / 100))
            
            # Calculate new target amount
            reduction_amount = current_target * reduction_factor
            new_target = current_target - reduction_amount
            
            # Ensure target remains positive
            return max(0.01, new_target)
            
        except Exception as e:
            logger.error(f"Error reducing goal amount: {str(e)}")
            # Return original amount as fallback
            if isinstance(goal, dict):
                return goal.get('target_amount', 0.0)
            return getattr(goal, 'target_amount', 0.0)
    
    def estimate_required_reduction(self, goal, gap_result: GapResult, profile: dict) -> float:
        """
        Calculate the minimum target reduction needed to make the goal feasible.
        
        Args:
            goal: The goal object to analyze
            gap_result: Gap analysis result
            profile: User profile data
            
        Returns:
            float: Required reduction percentage (0-100)
        """
        # Extract key values
        if isinstance(goal, dict):
            target_amount = goal.get('target_amount', 0.0)
            current_amount = goal.get('current_amount', 0.0)
            category = goal.get('category', '').lower()
        else:
            target_amount = getattr(goal, 'target_amount', 0.0)
            current_amount = getattr(goal, 'current_amount', 0.0)
            category = getattr(goal, 'category', '').lower()
        
        # Check if the goal is critical with minimal flexibility
        if category in self.params["critical_goals"]:
            return self.params["min_reduction_percentage"] * 100  # Minimal reduction for critical goals
        
        # Calculate monthly savings capacity
        monthly_capacity = self._calculate_monthly_capacity(profile)
        
        # Calculate original timeframe in months
        timeframe_months = self._calculate_timeframe_months(goal)
        
        if timeframe_months <= 0:
            # Invalid timeframe, use minimum reduction
            return self.params["min_reduction_percentage"] * 100
        
        # Calculate total capacity over the timeframe
        total_capacity = monthly_capacity * timeframe_months
        
        # Calculate gap that can't be covered by capacity
        uncoverable_gap = max(0, gap_result.gap_amount - total_capacity)
        
        if uncoverable_gap <= 0:
            # Gap can be covered with current capacity
            return self.params["min_reduction_percentage"] * 100
        
        # Calculate required reduction percentage
        if target_amount > 0:
            required_percentage = (uncoverable_gap / target_amount) * 100
            
            # Apply minimum reduction
            min_reduction = self.params["min_reduction_percentage"] * 100
            required_percentage = max(min_reduction, required_percentage)
            
            # Limit maximum reduction based on goal category
            if category in self.params["critical_goals"]:
                max_reduction = 10.0  # 10% for critical goals
            elif category in self.params["moderate_flexibility_goals"]:
                max_reduction = 20.0  # 20% for moderate flexibility goals
            else:
                max_reduction = self.params["max_reduction_percentage"] * 100
                
            return min(required_percentage, max_reduction)
        else:
            return self.params["min_reduction_percentage"] * 100
    
    def analyze_target_impact(self, goal, reduction_percentage: float) -> Dict[str, Any]:
        """
        Evaluate the effects of a target amount reduction on the goal.
        
        Args:
            goal: The goal object to analyze
            reduction_percentage: Percentage to reduce by (0-100)
            
        Returns:
            dict: Detailed impact analysis
        """
        # Initialize impact metrics
        impact = {
            "reduction_percentage": reduction_percentage,
            "original_target": 0.0,
            "new_target": 0.0,
            "reduction_amount": 0.0,
            "progress_percentage_improvement": 0.0,
            "quality_impact": "Minimal",
            "scope_reduction_suggestions": [],
            "indian_context_note": ""
        }
        
        try:
            # Extract current values
            if isinstance(goal, dict):
                target_amount = goal.get('target_amount', 0.0)
                current_amount = goal.get('current_amount', 0.0) 
                category = goal.get('category', '').lower()
                title = goal.get('title', '')
            else:
                target_amount = getattr(goal, 'target_amount', 0.0)
                current_amount = getattr(goal, 'current_amount', 0.0)
                category = getattr(goal, 'category', '').lower()
                title = getattr(goal, 'title', '')
            
            # Calculate new target and reduction amount
            impact["original_target"] = target_amount
            impact["reduction_amount"] = target_amount * (reduction_percentage / 100)
            impact["new_target"] = target_amount - impact["reduction_amount"]
            
            # Calculate progress percentage improvement
            original_progress = 0.0
            if target_amount > 0:
                original_progress = (current_amount / target_amount) * 100
                
            new_progress = 0.0
            if impact["new_target"] > 0:
                new_progress = (current_amount / impact["new_target"]) * 100
                
            impact["progress_percentage_improvement"] = max(0, new_progress - original_progress)
            
            # Assess quality impact based on reduction percentage
            if reduction_percentage <= 10:
                impact["quality_impact"] = "Minimal"
            elif reduction_percentage <= 20:
                impact["quality_impact"] = "Moderate"
            else:
                impact["quality_impact"] = "Significant"
            
            # Generate scope reduction suggestions based on goal category
            if category == "education":
                impact["scope_reduction_suggestions"] = [
                    "Consider public institutions with lower fees",
                    "Explore scholarship and financial aid options",
                    "Focus on essential educational expenses only"
                ]
                impact["indian_context_note"] = "Education is highly valued in Indian culture. Consider institutions with lower fees while maintaining quality."
                
            elif category == "wedding":
                impact["scope_reduction_suggestions"] = [
                    "Reduce guest count while including close family",
                    "Simplify venue and catering arrangements",
                    "Focus on traditional elements while reducing decorative expenses"
                ]
                impact["indian_context_note"] = "Weddings hold cultural significance in India. Prioritize essential rituals while adapting the scale."
                
            elif category == "home_purchase":
                impact["scope_reduction_suggestions"] = [
                    "Consider slightly smaller property",
                    "Explore emerging areas with lower property rates",
                    "Focus on functionality over premium features"
                ]
                impact["indian_context_note"] = "Home ownership is important in Indian society. Consider slightly smaller properties or emerging neighborhoods."
                
            elif category == "travel":
                impact["scope_reduction_suggestions"] = [
                    "Consider off-peak travel times",
                    "Choose value accommodations over luxury stays",
                    "Focus on key experiences over premium options"
                ]
                impact["indian_context_note"] = "Consider domestic tourism opportunities with rich cultural experiences at lower costs."
                
            elif category == "retirement":
                impact["scope_reduction_suggestions"] = [
                    "Adjust lifestyle expectations slightly",
                    "Consider healthcare and essential needs as priorities",
                    "Explore lower cost of living areas for retirement"
                ]
                impact["indian_context_note"] = "Multi-generational living is common in India, which can reduce retirement costs while maintaining family connections."
                
            else:
                impact["scope_reduction_suggestions"] = [
                    "Focus on essential components of the goal",
                    "Consider value alternatives to premium options",
                    "Prioritize quality in key areas while reducing less critical aspects"
                ]
            
            return impact
            
        except Exception as e:
            logger.error(f"Error analyzing target impact: {str(e)}")
            return impact
    
    def find_optimal_reduction(self, goal, gap_result: GapResult, profile: dict) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate an optimal target reduction that preserves goal essence while ensuring feasibility.
        
        Args:
            goal: The goal object to analyze
            gap_result: Gap analysis result
            profile: User profile data
            
        Returns:
            tuple: (optimal_reduction_percentage, impact_analysis)
        """
        # First get the minimum required reduction
        required_reduction = self.estimate_required_reduction(goal, gap_result, profile)
        
        # Extract goal category
        if isinstance(goal, dict):
            category = goal.get('category', '').lower()
        else:
            category = getattr(goal, 'category', '').lower()
        
        # Determine optimal reduction based on goal category
        if category in self.params["critical_goals"]:
            # Critical goals - use minimum viable reduction
            optimal_reduction = required_reduction
        elif category in self.params["moderate_flexibility_goals"]:
            # Moderate flexibility - scale slightly above minimum
            optimal_reduction = required_reduction * 1.1
        else:
            # High flexibility - use optimal reduction factor
            optimal_factor = self.params["optimal_reduction_factor"]
            optimal_reduction = max(required_reduction, optimal_factor * 100)
        
        # Apply maximum constraints based on category
        if category in self.params["critical_goals"]:
            max_reduction = 10.0  # 10% for critical goals
        elif category in self.params["moderate_flexibility_goals"]:
            max_reduction = 20.0  # 20% for moderate flexibility goals
        else:
            max_reduction = self.params["max_reduction_percentage"] * 100
            
        optimal_reduction = min(optimal_reduction, max_reduction)
        
        # Analyze impact of the optimal reduction
        impact = self.analyze_target_impact(goal, optimal_reduction)
        
        return optimal_reduction, impact
    
    def _calculate_monthly_capacity(self, profile: dict) -> float:
        """
        Calculate user's monthly savings capacity.
        
        Args:
            profile: User profile data
            
        Returns:
            float: Estimated monthly savings capacity
        """
        # Default capacity if we can't calculate from profile
        default_capacity = 1000.0
        
        try:
            # Extract income and expenses from profile
            if 'income' in profile:
                income = profile['income']
                if isinstance(income, dict) and 'amount' in income:
                    monthly_income = income['amount']
                    if income.get('frequency', '').lower() in ['annual', 'yearly']:
                        monthly_income /= 12
                else:
                    monthly_income = float(income)
            else:
                # Look in answers
                if 'answers' in profile:
                    for answer in profile['answers']:
                        if 'income' in answer.get('question_id', '').lower():
                            value = answer.get('answer')
                            if isinstance(value, (int, float)):
                                monthly_income = float(value)
                                break
                            elif isinstance(value, dict) and 'amount' in value:
                                monthly_income = float(value['amount'])
                                if value.get('frequency', '').lower() in ['annual', 'yearly']:
                                    monthly_income /= 12
                                break
                            elif isinstance(value, str) and value.replace('.', '', 1).isdigit():
                                monthly_income = float(value)
                                break
                    else:
                        # No income found in answers
                        monthly_income = 5000.0
                else:
                    monthly_income = 5000.0
            
            # Extract expenses similarly
            if 'expenses' in profile:
                expenses = profile['expenses']
                if isinstance(expenses, dict) and 'amount' in expenses:
                    monthly_expenses = expenses['amount']
                    if expenses.get('frequency', '').lower() in ['annual', 'yearly']:
                        monthly_expenses /= 12
                else:
                    monthly_expenses = float(expenses)
            else:
                # Estimate as percentage of income if not found
                monthly_expenses = monthly_income * 0.7
            
            # Calculate disposable income (capacity)
            capacity = max(0, monthly_income - monthly_expenses)
            
            # Apply a savings factor (not all disposable income goes to goals)
            savings_factor = 0.5  # 50% of disposable income available for goals
            return capacity * savings_factor
            
        except Exception as e:
            logger.error(f"Error calculating monthly capacity: {str(e)}")
            return default_capacity
    
    def _calculate_original_timeframe_months(self, goal) -> int:
        """
        Calculate the original timeframe of the goal in months.
        
        Args:
            goal: The goal object
            
        Returns:
            int: Original timeframe in months
        """
        try:
            # Extract timeframe
            if isinstance(goal, dict):
                timeframe_str = goal.get('timeframe', '')
            else:
                timeframe_str = getattr(goal, 'timeframe', '')
            
            # If no timeframe, return a default
            if not timeframe_str:
                return 36  # Default to 3 years
            
            # Try to parse timeframe
            try:
                target_date = datetime.fromisoformat(timeframe_str.replace('Z', '+00:00'))
                today = datetime.now()
                
                # Calculate months between today and target date
                months = (target_date.year - today.year) * 12 + target_date.month - today.month
                # Adjust for day of month
                if target_date.day < today.day:
                    months -= 1
                    
                return max(1, months)  # Ensure at least 1 month
                
            except ValueError:
                # Alternative: check if it's a time_horizon in years
                if isinstance(goal, dict) and 'time_horizon' in goal:
                    years = float(goal['time_horizon'])
                    return int(years * 12)
                elif hasattr(goal, 'time_horizon'):
                    years = float(goal.time_horizon)
                    return int(years * 12)
                
                # Default fallback
                return 36
                
        except Exception as e:
            logger.error(f"Error calculating timeframe: {str(e)}")
            return 36  # Default to 3 years


class PriorityAdjustment:
    """
    Class for adjusting and optimizing goal priorities based on gap analysis results.
    
    This class provides tools to reprioritize financial goals based on analysis results,
    create staged priority plans, and evaluate the impact of priority changes on overall
    financial health. Includes Indian context-specific considerations.
    """
    
    def __init__(self):
        """Initialize with financial parameter service access"""
        self.param_service = get_financial_parameter_service()
        
        # Initialize default parameters
        self.params = {
            "max_priority_adjustment": 0.3,  # Maximum priority score adjustment (percentage)
            "critical_goals": ["emergency_fund", "health_insurance", "life_insurance"],
            "cultural_priority_factors": {
                "education": 1.2,        # Higher priority for education in Indian context
                "wedding": 1.1,          # Cultural importance for weddings
                "home_purchase": 1.15,   # Property ownership significance
                "parent_care": 1.25      # Family responsibility priority
            },
            "deferrable_threshold": 0.4  # Threshold for identifying deferrable goals (percentage)
        }
        
        # Load parameters from service if available
        if self.param_service:
            try:
                service_params = self.param_service.get_all_parameters()
                # Update default params with those from the service
                for key, value in service_params.items():
                    if key in self.params and not isinstance(self.params[key], dict):
                        self.params[key] = value
                    elif key in self.params and isinstance(self.params[key], dict):
                        if isinstance(value, dict):
                            for nested_key, nested_value in value.items():
                                if nested_key in self.params[key]:
                                    self.params[key][nested_key] = nested_value
            except Exception as e:
                logger.error(f"Error loading parameters for priority adjustment: {str(e)}")
    
    def reprioritize_goals(self, goals: List[Any], priority_ranking: List[str]) -> List[Any]:
        """
        Reorder goals based on a specified priority ranking.
        
        Args:
            goals: List of goal objects to reprioritize
            priority_ranking: List of goal IDs in desired priority order
            
        Returns:
            List of prioritized goal objects
        """
        # Create a dictionary mapping goal IDs to goals for quick lookup
        goal_map = {}
        for goal in goals:
            if isinstance(goal, dict):
                goal_id = goal.get('id', '')
            else:
                goal_id = getattr(goal, 'id', '')
            
            goal_map[goal_id] = goal
        
        # Create a new list of goals in the specified priority order
        prioritized_goals = []
        for goal_id in priority_ranking:
            if goal_id in goal_map:
                prioritized_goals.append(goal_map[goal_id])
        
        # Add any remaining goals (not in the priority_ranking) at the end
        remaining_goals = [g for g in goals if (isinstance(g, dict) and g.get('id', '') not in priority_ranking) or 
                          (not isinstance(g, dict) and getattr(g, 'id', '') not in priority_ranking)]
        
        return prioritized_goals + remaining_goals
    
    def suggest_priority_changes(self, goals: List[Any], gaps: List[GapResult], profile: dict) -> Dict[str, Any]:
        """
        Suggest changes to goal priorities based on gap analysis.
        
        Args:
            goals: List of goal objects
            gaps: List of gap analysis results
            profile: User profile data
            
        Returns:
            Dictionary with suggested priority changes and explanations
        """
        # Initialize suggestions
        suggestions = {
            "reprioritized_goal_ids": [],
            "explanations": {},
            "overall_impact": "",
            "indian_context_notes": "",
            "family_impact": ""
        }
        
        try:
            # Map gaps to goals for easy reference
            gap_map = {gap.goal_id: gap for gap in gaps}
            
            # Identify critical goals (security level or in critical list)
            critical_goals = []
            for goal in goals:
                if isinstance(goal, dict):
                    goal_id = goal.get('id', '')
                    category = goal.get('category', '').lower()
                else:
                    goal_id = getattr(goal, 'id', '')
                    category = getattr(goal, 'category', '').lower()
                
                if category in self.params["critical_goals"]:
                    critical_goals.append(goal_id)
            
            # Calculate priority scores for all goals if not already calculated
            calculated_scores = {}
            for goal in goals:
                if isinstance(goal, dict):
                    goal_id = goal.get('id', '')
                    if 'priority_score' in goal and goal['priority_score'] > 0:
                        calculated_scores[goal_id] = goal['priority_score']
                    else:
                        # Import as needed to avoid circular imports
                        from models.goal_models import Goal
                        temp_goal = Goal.from_dict(goal)
                        calculated_scores[goal_id] = temp_goal.calculate_priority_score()
                else:
                    goal_id = getattr(goal, 'id', '')
                    if hasattr(goal, 'priority_score') and goal.priority_score > 0:
                        calculated_scores[goal_id] = goal.priority_score
                    else:
                        calculated_scores[goal_id] = goal.calculate_priority_score()
            
            # Adjust scores based on gap severity
            adjusted_scores = calculated_scores.copy()
            for goal_id, gap in gap_map.items():
                # Skip adjustments for critical goals
                if goal_id in critical_goals:
                    continue
                
                # Adjust score based on gap severity
                if gap.severity == GapSeverity.CRITICAL:
                    adjustment = -0.3  # 30% reduction for critical gaps
                elif gap.severity == GapSeverity.SIGNIFICANT:
                    adjustment = -0.2  # 20% reduction for significant gaps
                elif gap.severity == GapSeverity.MODERATE:
                    adjustment = -0.1  # 10% reduction for moderate gaps
                else:
                    adjustment = 0  # No change for minor gaps
                
                # Apply the adjustment
                adjusted_scores[goal_id] = adjusted_scores[goal_id] * (1 + adjustment)
                
                # Add explanation if score was adjusted
                if adjustment != 0:
                    suggestions["explanations"][goal_id] = f"Priority adjusted due to {gap.severity.value} funding gap of ₹{gap.gap_amount:,.2f}"
            
            # Apply cultural adjustments for Indian context
            for goal in goals:
                if isinstance(goal, dict):
                    goal_id = goal.get('id', '')
                    title = goal.get('title', '').lower()
                    category = goal.get('category', '').lower()
                else:
                    goal_id = getattr(goal, 'id', '')
                    title = getattr(goal, 'title', '').lower()
                    category = getattr(goal, 'category', '').lower()
                
                # Check for cultural priority factors
                for cultural_key, factor in self.params["cultural_priority_factors"].items():
                    if cultural_key in category or cultural_key in title:
                        # Apply cultural adjustment factor
                        adjusted_scores[goal_id] = adjusted_scores[goal_id] * factor
                        
                        if goal_id not in suggestions["explanations"]:
                            suggestions["explanations"][goal_id] = ""
                        else:
                            suggestions["explanations"][goal_id] += ". "
                            
                        suggestions["explanations"][goal_id] += f"Priority increased due to cultural significance in Indian context"
            
            # Sort goal IDs by adjusted priority score (descending)
            prioritized_ids = sorted(adjusted_scores.keys(), key=lambda x: adjusted_scores[x], reverse=True)
            
            # Ensure critical goals remain at the top
            for goal_id in reversed(critical_goals):
                if goal_id in prioritized_ids:
                    prioritized_ids.remove(goal_id)
                    prioritized_ids.insert(0, goal_id)
            
            suggestions["reprioritized_goal_ids"] = prioritized_ids
            
            # Add Indian context-specific notes
            indian_context_notes = []
            if any("education" in getattr(goal, 'category', goal.get('category', '')).lower() for goal in goals):
                indian_context_notes.append("Education goals are prioritized higher reflecting their cultural importance in Indian society")
            
            if any("wedding" in getattr(goal, 'title', goal.get('title', '')).lower() for goal in goals):
                indian_context_notes.append("Wedding goals receive special consideration due to their cultural significance and family implications")
            
            if any("parent" in getattr(goal, 'title', goal.get('title', '')).lower() for goal in goals):
                indian_context_notes.append("Parent care goals reflect the joint family values and filial responsibilities in Indian culture")
            
            suggestions["indian_context_notes"] = ". ".join(indian_context_notes)
            
            # Evaluate family impact in Indian context
            family_impact = self._evaluate_family_impact(goals, prioritized_ids, profile)
            suggestions["family_impact"] = family_impact
            
            # Calculate overall impact
            adjusted_order = [goal_id for goal_id in prioritized_ids if goal_id in calculated_scores]
            original_order = sorted(calculated_scores.keys(), key=lambda x: calculated_scores[x], reverse=True)
            
            # Calculate position changes
            position_changes = 0
            for goal_id in adjusted_order:
                original_pos = original_order.index(goal_id)
                new_pos = adjusted_order.index(goal_id)
                position_changes += abs(original_pos - new_pos)
            
            # Generate impact description
            if position_changes == 0:
                suggestions["overall_impact"] = "No changes to goal priorities recommended."
            elif position_changes <= 2:
                suggestions["overall_impact"] = "Minor adjustments to goal priorities recommended to optimize resource allocation."
            elif position_changes <= 5:
                suggestions["overall_impact"] = "Moderate reprioritization recommended to address funding gaps and improve goal feasibility."
            else:
                suggestions["overall_impact"] = "Significant reprioritization recommended to realign goals with financial capacity and cultural priorities."
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting priority changes: {str(e)}")
            suggestions["overall_impact"] = "Unable to generate priority suggestions due to an error."
            return suggestions
    
    def analyze_priority_impact(self, current_priorities: List[str], new_priorities: List[str], profile: dict) -> Dict[str, Any]:
        """
        Evaluate the effects of changing goal priorities on overall financial health.
        
        Args:
            current_priorities: List of goal IDs in current priority order
            new_priorities: List of goal IDs in proposed priority order
            profile: User profile data
            
        Returns:
            Dictionary with impact analysis
        """
        impact = {
            "goal_position_changes": {},
            "resource_allocation_impact": {},
            "emotional_impact": {},
            "family_network_effects": {},
            "overall_assessment": ""
        }
        
        try:
            # Calculate position changes for each goal
            for i, goal_id in enumerate(new_priorities):
                if goal_id in current_priorities:
                    old_position = current_priorities.index(goal_id)
                    new_position = i
                    position_change = old_position - new_position  # Positive: moved up, Negative: moved down
                    
                    impact["goal_position_changes"][goal_id] = {
                        "old_position": old_position,
                        "new_position": new_position,
                        "change": position_change
                    }
            
            # Estimate resource allocation impact
            # For simplicity, assume higher priority gets more resources
            total_goals = len(new_priorities)
            for i, goal_id in enumerate(new_priorities):
                if goal_id in current_priorities:
                    old_position = current_priorities.index(goal_id)
                    
                    # Calculate resource allocation percentages (simplified model)
                    # Higher priority goals get more resources
                    old_allocation = (total_goals - old_position) / total_goals * 100
                    new_allocation = (total_goals - i) / total_goals * 100
                    
                    impact["resource_allocation_impact"][goal_id] = {
                        "allocation_change": new_allocation - old_allocation,
                        "description": self._get_allocation_impact_description(new_allocation - old_allocation)
                    }
            
            # Check for emotional impacts based on culturally significant goals
            for goal_id in new_priorities:
                if goal_id in current_priorities:
                    position_change = impact["goal_position_changes"][goal_id]["change"]
                    
                    # Determine if this is a culturally significant goal
                    cultural_significance = "standard"
                    for cultural_key in self.params["cultural_priority_factors"]:
                        # Check if the goal is related to this cultural factor
                        # This would require fetching the actual goal, but for simplicity, we'll use goal_id
                        if cultural_key in goal_id.lower():
                            cultural_significance = cultural_key
                            break
                    
                    # Assess emotional impact based on position change and cultural significance
                    impact["emotional_impact"][goal_id] = self._assess_emotional_impact(position_change, cultural_significance)
            
            # Assess family network effects (Indian context)
            impact["family_network_effects"] = self._assess_family_network_effects(new_priorities, profile)
            
            # Generate overall assessment
            position_changes = sum(abs(data["change"]) for data in impact["goal_position_changes"].values())
            allocation_changes = sum(abs(data["allocation_change"]) for data in impact["resource_allocation_impact"].values())
            
            if position_changes == 0:
                impact["overall_assessment"] = "No change in priorities. Current prioritization is maintained."
            elif position_changes <= 3 and allocation_changes < 20:
                impact["overall_assessment"] = "Minor adjustments with limited impact on resource allocation and family expectations."
            elif position_changes <= 6 and allocation_changes < 40:
                impact["overall_assessment"] = "Moderate reprioritization with noticeable shifts in resource allocation. Some family expectations may need to be managed."
            else:
                impact["overall_assessment"] = "Significant reprioritization with major resource allocation changes. Important to communicate these changes with family members affected by the priority shifts."
            
            return impact
            
        except Exception as e:
            logger.error(f"Error analyzing priority impact: {str(e)}")
            impact["overall_assessment"] = "Unable to analyze priority impact due to an error."
            return impact
    
    def identify_deferrable_goals(self, goals: List[Any], profile: dict) -> Dict[str, Any]:
        """
        Identify goals that can be temporarily deprioritized with minimal negative impact.
        
        Args:
            goals: List of goal objects
            profile: User profile data
            
        Returns:
            Dictionary with deferrable goals and rationale
        """
        result = {
            "deferrable_goals": [],
            "non_deferrable_goals": [],
            "deferral_rationale": {},
            "indian_context_considerations": {}
        }
        
        try:
            for goal in goals:
                # Extract goal information
                if isinstance(goal, dict):
                    goal_id = goal.get('id', '')
                    category = goal.get('category', '').lower()
                    title = goal.get('title', '').lower()
                    importance = goal.get('importance', '').lower()
                    flexibility = goal.get('flexibility', '').lower()
                    timeframe_str = goal.get('timeframe', '')
                else:
                    goal_id = getattr(goal, 'id', '')
                    category = getattr(goal, 'category', '').lower()
                    title = getattr(goal, 'title', '').lower()
                    importance = getattr(goal, 'importance', '').lower()
                    flexibility = getattr(goal, 'flexibility', '').lower()
                    timeframe_str = getattr(goal, 'timeframe', '')
                
                # Check if this is a critical goal (non-deferrable)
                if category in self.params["critical_goals"]:
                    result["non_deferrable_goals"].append(goal_id)
                    result["deferral_rationale"][goal_id] = "Critical financial security goal that cannot be deferred"
                    continue
                
                # Check cultural significance for Indian context
                cultural_significance = False
                cultural_factor = None
                for cultural_key, factor in self.params["cultural_priority_factors"].items():
                    if cultural_key in category or cultural_key in title:
                        cultural_significance = True
                        cultural_factor = cultural_key
                        break
                
                # Parse timeframe to check urgency
                urgent = False
                try:
                    target_date = datetime.fromisoformat(timeframe_str.replace('Z', '+00:00'))
                    today = datetime.now()
                    months_remaining = (target_date.year - today.year) * 12 + target_date.month - today.month
                    if months_remaining <= 12:  # Within a year
                        urgent = True
                except (ValueError, TypeError):
                    # Default to not urgent if we can't parse the date
                    pass
                
                # Determine deferrability
                if urgent:
                    result["non_deferrable_goals"].append(goal_id)
                    result["deferral_rationale"][goal_id] = "Goal timeframe is within 12 months and cannot be reasonably deferred"
                elif importance == "high" and flexibility == "fixed":
                    result["non_deferrable_goals"].append(goal_id)
                    result["deferral_rationale"][goal_id] = "High importance goal with fixed flexibility requires consistent funding"
                elif cultural_significance and self.params["cultural_priority_factors"].get(cultural_factor, 1.0) > 1.1:
                    result["non_deferrable_goals"].append(goal_id)
                    result["deferral_rationale"][goal_id] = f"Culturally significant goal ({cultural_factor}) with high priority in Indian context"
                    result["indian_context_considerations"][goal_id] = f"In Indian society, {cultural_factor} goals often carry family expectations and social considerations"
                else:
                    # This goal is potentially deferrable
                    result["deferrable_goals"].append(goal_id)
                    
                    rationale = []
                    if importance != "high":
                        rationale.append(f"{importance.capitalize()} importance")
                    if flexibility != "fixed":
                        rationale.append(f"{flexibility.replace('_', ' ')} timing")
                    if not urgent:
                        rationale.append("longer timeframe")
                    
                    result["deferral_rationale"][goal_id] = f"Can be temporarily deferred due to {', '.join(rationale)}"
                    
                    # Add Indian context if relevant
                    if cultural_significance:
                        result["indian_context_considerations"][goal_id] = f"While {cultural_factor} is culturally important, this specific goal has factors that allow temporary deferral"
            
            return result
            
        except Exception as e:
            logger.error(f"Error identifying deferrable goals: {str(e)}")
            return result
    
    def create_staged_priority_plan(self, goals: List[Any], gaps: List[GapResult], profile: dict) -> Dict[str, Any]:
        """
        Create a phased approach to goal prioritization over time.
        
        Args:
            goals: List of goal objects
            gaps: List of gap analysis results
            profile: User profile data
            
        Returns:
            Dictionary with staged priority plan
        """
        plan = {
            "immediate_priorities": [],
            "mid_term_priorities": [],
            "long_term_priorities": [],
            "stage_transitions": {},
            "resource_allocation_strategy": {},
            "indian_context_adaptations": {}
        }
        
        try:
            # Get deferrable goals information
            deferrable_info = self.identify_deferrable_goals(goals, profile)
            
            # Map gaps to goals for easy reference
            gap_map = {gap.goal_id: gap for gap in gaps}
            
            # Categorize goals by timeframe
            immediate_goals = []
            mid_term_goals = []
            long_term_goals = []
            
            for goal in goals:
                if isinstance(goal, dict):
                    goal_id = goal.get('id', '')
                    title = goal.get('title', '')
                    timeframe_str = goal.get('timeframe', '')
                    category = goal.get('category', '').lower()
                else:
                    goal_id = getattr(goal, 'id', '')
                    title = getattr(goal, 'title', '')
                    timeframe_str = getattr(goal, 'timeframe', '')
                    category = getattr(goal, 'category', '').lower()
                
                # Parse timeframe
                months_remaining = 36  # Default to 3 years
                try:
                    target_date = datetime.fromisoformat(timeframe_str.replace('Z', '+00:00'))
                    today = datetime.now()
                    months_remaining = (target_date.year - today.year) * 12 + target_date.month - today.month
                except (ValueError, TypeError):
                    # Use default if we can't parse the date
                    pass
                
                # Categorize based on timeframe and deferability
                if category in self.params["critical_goals"] or months_remaining <= 12:
                    immediate_goals.append((goal_id, title, months_remaining))
                elif months_remaining <= 36 or goal_id in deferrable_info["non_deferrable_goals"]:
                    mid_term_goals.append((goal_id, title, months_remaining))
                else:
                    long_term_goals.append((goal_id, title, months_remaining))
            
            # Sort each category by timeframe (ascending)
            immediate_goals.sort(key=lambda x: x[2])
            mid_term_goals.sort(key=lambda x: x[2])
            long_term_goals.sort(key=lambda x: x[2])
            
            # Add critical goals first in immediate priorities
            critical_ids = [goal_id for goal_id in deferrable_info["non_deferrable_goals"] 
                          if any(g[0] == goal_id for g in immediate_goals)]
            other_immediate = [g for g in immediate_goals if g[0] not in critical_ids]
            
            # Populate the staged plan
            plan["immediate_priorities"] = [(goal_id, title) for goal_id, title, _ in 
                                          [(gid, gtitle, 0) for gid, gtitle in [(g_id, g_title) for g_id, g_title, _ in immediate_goals if g_id in critical_ids]] + 
                                          other_immediate]
            
            plan["mid_term_priorities"] = [(goal_id, title) for goal_id, title, _ in mid_term_goals]
            plan["long_term_priorities"] = [(goal_id, title) for goal_id, title, _ in long_term_goals]
            
            # Define resource allocation strategy
            total_goals = len(plan["immediate_priorities"] + plan["mid_term_priorities"] + plan["long_term_priorities"])
            
            # Suggested allocation percentages
            if total_goals > 0:
                immediate_allocation = min(80, max(40, len(plan["immediate_priorities"]) / total_goals * 100))
                mid_term_allocation = min(50, max(15, len(plan["mid_term_priorities"]) / total_goals * 100))
                long_term_allocation = 100 - immediate_allocation - mid_term_allocation
                
                plan["resource_allocation_strategy"] = {
                    "immediate_allocation_percentage": immediate_allocation,
                    "mid_term_allocation_percentage": mid_term_allocation,
                    "long_term_allocation_percentage": long_term_allocation,
                    "description": f"Allocate approximately {immediate_allocation:.1f}% of available resources to immediate priorities, {mid_term_allocation:.1f}% to mid-term goals, and {long_term_allocation:.1f}% to long-term objectives."
                }
            
            # Define stage transitions
            for goal_id, title in plan["mid_term_priorities"]:
                # Check if this goal should transition to immediate priority soon
                for g_id, g_title, months in mid_term_goals:
                    if g_id == goal_id and months <= 18:
                        plan["stage_transitions"][goal_id] = {
                            "title": title,
                            "current_stage": "mid_term",
                            "next_stage": "immediate",
                            "transition_timeline": f"Transition to immediate priority in {max(1, months-12)} months",
                            "reason": "Approaching critical timeframe"
                        }
            
            # Add Indian context adaptations
            for goal in goals:
                if isinstance(goal, dict):
                    goal_id = goal.get('id', '')
                    category = goal.get('category', '').lower()
                    title = goal.get('title', '').lower()
                else:
                    goal_id = getattr(goal, 'id', '')
                    category = getattr(goal, 'category', '').lower()
                    title = getattr(goal, 'title', '').lower()
                
                # Check for culturally significant goals
                for cultural_key, factor in self.params["cultural_priority_factors"].items():
                    if cultural_key in category or cultural_key in title:
                        # Add cultural adaptation notes
                        plan["indian_context_adaptations"][goal_id] = {
                            "cultural_factor": cultural_key,
                            "significance": f"Higher prioritization reflecting {cultural_key}'s importance in Indian family context",
                            "seasonal_considerations": self._get_cultural_seasonal_considerations(cultural_key)
                        }
            
            return plan
            
        except Exception as e:
            logger.error(f"Error creating staged priority plan: {str(e)}")
            return plan
    
    def _evaluate_family_impact(self, goals: List[Any], prioritized_ids: List[str], profile: dict) -> str:
        """
        Evaluate the impact of prioritization on family financial security.
        
        Args:
            goals: List of goal objects
            prioritized_ids: List of goal IDs in priority order
            profile: User profile data
            
        Returns:
            String describing family impact
        """
        # Default response
        default_response = "Prioritization balances individual and family financial needs."
        
        try:
            # Check for joint family indicators in profile
            has_joint_family = False
            has_dependent_parents = False
            
            if 'family_type' in profile and 'joint' in profile['family_type'].lower():
                has_joint_family = True
            elif 'dependents' in profile:
                deps = profile['dependents']
                if isinstance(deps, list):
                    for dep in deps:
                        if isinstance(dep, dict) and dep.get('relationship', '').lower() in ['parent', 'father', 'mother']:
                            has_dependent_parents = True
                elif isinstance(deps, dict) and deps.get('parents', False):
                    has_dependent_parents = True
            
            # Check if family-oriented goals are properly prioritized
            family_oriented_goals = []
            for goal in goals:
                if isinstance(goal, dict):
                    goal_id = goal.get('id', '')
                    title = goal.get('title', '').lower()
                    category = goal.get('category', '').lower()
                else:
                    goal_id = getattr(goal, 'id', '')
                    title = getattr(goal, 'title', '').lower()
                    category = getattr(goal, 'category', '').lower()
                
                # Check if this is a family-oriented goal
                if any(term in title or term in category for term in 
                      ['education', 'wedding', 'parent', 'family', 'medical', 'health']):
                    family_oriented_goals.append(goal_id)
            
            # Assess if family goals are highly prioritized
            if not family_oriented_goals:
                return default_response
            
            family_goal_positions = [prioritized_ids.index(g_id) for g_id in family_oriented_goals if g_id in prioritized_ids]
            if not family_goal_positions:
                return default_response
            
            avg_position = sum(family_goal_positions) / len(family_goal_positions)
            total_goals = len(prioritized_ids)
            
            # Generate response based on family goal prioritization
            if avg_position < total_goals * 0.3:  # Top 30%
                if has_joint_family or has_dependent_parents:
                    return "Prioritization strongly supports joint family responsibilities, aligning well with traditional Indian family values."
                else:
                    return "Prioritization properly emphasizes family-oriented goals, supporting key family financial needs."
            elif avg_position < total_goals * 0.5:  # Top 50%
                return "Prioritization maintains a balance between individual financial goals and family responsibilities."
            else:
                if has_joint_family or has_dependent_parents:
                    return "Current prioritization may need adjustment to better reflect joint family responsibilities which are culturally significant in the Indian context."
                else:
                    return "Family-oriented goals might benefit from higher prioritization to ensure family financial security."
                
        except Exception as e:
            logger.error(f"Error evaluating family impact: {str(e)}")
            return default_response
    
    def _get_allocation_impact_description(self, allocation_change: float) -> str:
        """
        Generate a description of the resource allocation impact.
        
        Args:
            allocation_change: Change in resource allocation percentage
            
        Returns:
            Description string
        """
        if allocation_change > 15:
            return "Significant increase in resource allocation"
        elif allocation_change > 5:
            return "Moderate increase in resource allocation"
        elif allocation_change > 0:
            return "Slight increase in resource allocation"
        elif allocation_change > -5:
            return "Slight decrease in resource allocation"
        elif allocation_change > -15:
            return "Moderate decrease in resource allocation"
        else:
            return "Significant decrease in resource allocation"
    
    def _assess_emotional_impact(self, position_change: int, cultural_significance: str) -> Dict[str, str]:
        """
        Assess the emotional impact of goal priority changes.
        
        Args:
            position_change: Change in goal position (positive: moved up, negative: moved down)
            cultural_significance: Cultural significance factor
            
        Returns:
            Dictionary with emotional impact assessment
        """
        result = {
            "impact_level": "neutral",
            "description": "No significant emotional impact expected"
        }
        
        # Evaluate based on position change
        if position_change > 3:
            result["impact_level"] = "positive"
            result["description"] = "Positive emotional impact from increased goal priority"
        elif position_change > 0:
            result["impact_level"] = "slightly_positive"
            result["description"] = "Slightly positive emotional response to improved goal prioritization"
        elif position_change < -3:
            result["impact_level"] = "negative"
            result["description"] = "Potential disappointment from decreased goal priority"
        elif position_change < 0:
            result["impact_level"] = "slightly_negative"
            result["description"] = "Minor disappointment from slightly decreased goal priority"
        
        # Adjust based on cultural significance
        if cultural_significance != "standard":
            if cultural_significance == "education":
                if position_change > 0:
                    result["description"] += ". Aligns with cultural emphasis on education in Indian families"
                elif position_change < 0:
                    result["description"] += ". May conflict with cultural expectations regarding education priority"
            elif cultural_significance == "wedding":
                if position_change > 0:
                    result["description"] += ". Supports cultural importance of wedding preparations"
                elif position_change < 0:
                    result["description"] += ". May create tension with family expectations around wedding planning"
            elif cultural_significance == "parent_care":
                if position_change > 0:
                    result["description"] += ". Reinforces filial responsibility values important in Indian society"
                elif position_change < 0:
                    result["description"] += ". Could create concern about fulfilling family care responsibilities"
            elif cultural_significance == "home_purchase":
                if position_change > 0:
                    result["description"] += ". Supports cultural value of property ownership"
                elif position_change < 0:
                    result["description"] += ". May delay property ownership milestone valued in Indian society"
        
        return result
    
    def _assess_family_network_effects(self, priorities: List[str], profile: dict) -> Dict[str, str]:
        """
        Assess how priority changes affect the wider family network (Indian context).
        
        Args:
            priorities: List of goal IDs in priority order
            profile: User profile data
            
        Returns:
            Dictionary with family network effects assessment
        """
        effects = {
            "joint_family_implications": "No significant impact on joint family dynamics",
            "extended_family_expectations": "Maintains alignment with extended family expectations",
            "generational_responsibilities": "Balances responsibilities across generations"
        }
        
        # This is a simplified implementation that would need to be expanded
        # with actual data about family structure and cultural context
        
        # For now, return the default assessment
        return effects
    
    def _get_cultural_seasonal_considerations(self, cultural_factor: str) -> str:
        """
        Get seasonal considerations for culturally significant goals in Indian context.
        
        Args:
            cultural_factor: Cultural factor identifier
            
        Returns:
            String with seasonal considerations
        """
        if cultural_factor == "wedding":
            return "Consider traditional wedding seasons (Nov-Feb, Apr-Jun) for optimal planning and potentially lower costs outside peak seasons"
        elif cultural_factor == "education":
            return "Align funding with academic year timing (Jun-Apr) and entrance exam seasons (Jan-May)"
        elif cultural_factor == "home_purchase":
            return "Consider auspicious periods for property transactions and potential seasonal pricing variations"
        elif cultural_factor == "parent_care":
            return "Plan for seasonal healthcare needs and festival periods when family gatherings are common"
        else:
            return "No specific seasonal considerations identified"


class RemediationImpactAnalysis:
    """
    Class for analyzing the impact of gap remediation strategies.
    
    This class provides tools to evaluate the feasibility, emotional impact,
    and implementation difficulty of various remediation options. It also 
    supports sensitivity analysis and comparison of strategies with
    India-specific context factors.
    """
    
    def __init__(self):
        """Initialize with financial parameter service access"""
        self.param_service = get_financial_parameter_service()
        
        # Initialize default parameters
        self.params = {
            "income_sensitivity_factor": 0.8,  # Income sensitivity factor for feasibility calculations
            "inflation_impact_factor": 1.2,    # Inflation impact factor (higher in Indian context)
            "family_support_factor": 0.7,      # Family support impact on emotional factors
            "implementation_complexity_weights": {
                "time_required": 0.3,
                "knowledge_needed": 0.25,
                "effort_level": 0.25,
                "external_dependencies": 0.2
            },
            "cultural_consideration_factors": {
                "family_approval": 0.8,        # Importance of family approval in Indian context
                "social_status": 0.6,          # Impact on social status perception
                "traditional_values": 0.7      # Alignment with traditional values
            }
        }
        
        # Load parameters from service if available
        if self.param_service:
            try:
                service_params = self.param_service.get_all_parameters()
                # Update default params with those from the service
                for key, value in service_params.items():
                    if key in self.params and not isinstance(self.params[key], dict):
                        self.params[key] = value
                    elif key in self.params and isinstance(self.params[key], dict):
                        if isinstance(value, dict):
                            for nested_key, nested_value in value.items():
                                if nested_key in self.params[key]:
                                    self.params[key][nested_key] = nested_value
            except Exception as e:
                logger.error(f"Error loading parameters for remediation impact analysis: {str(e)}")
    
    def calculate_feasibility_scores(self, remediation_options: List[RemediationOption], profile: dict) -> Dict[str, float]:
        """
        Evaluate the practical feasibility of each remediation option.
        
        Args:
            remediation_options: List of remediation options to evaluate
            profile: User profile data
            
        Returns:
            Dictionary mapping option descriptions to feasibility scores (0-100)
        """
        scores = {}
        
        try:
            # Extract income data from profile for feasibility calculations
            monthly_income = self._extract_monthly_income(profile)
            
            for option in remediation_options:
                # Start with the base feasibility score from the option
                base_score = option.feasibility_score
                
                # Adjust based on income sensitivity
                income_factor = 1.0
                if "monthly_savings_adjustment" in option.impact_metrics:
                    savings_adjustment = option.impact_metrics["monthly_savings_adjustment"]
                    if monthly_income > 0:
                        # Calculate how much of monthly income this represents
                        adjustment_percentage = abs(savings_adjustment) / monthly_income
                        
                        # Apply income sensitivity factor
                        if adjustment_percentage > 0.3:  # More than 30% of income
                            income_factor = 0.5  # Major difficulty
                        elif adjustment_percentage > 0.2:  # 20-30% of income
                            income_factor = 0.7  # Significant difficulty
                        elif adjustment_percentage > 0.1:  # 10-20% of income
                            income_factor = 0.9  # Moderate difficulty
                
                # Adjust based on timeframe extension
                timeframe_factor = 1.0
                if "timeframe_extension" in option.impact_metrics:
                    extension = option.impact_metrics["timeframe_extension"]
                    if extension > 0.5:  # More than 50% extension
                        timeframe_factor = 0.8  # Significant extension
                    elif extension > 0.25:  # 25-50% extension
                        timeframe_factor = 0.9  # Moderate extension
                
                # Calculate final feasibility score
                adjusted_score = base_score * income_factor * timeframe_factor
                
                # Add Indian context adjustments
                indian_context_factor = self._calculate_indian_context_factor(option, profile)
                final_score = adjusted_score * indian_context_factor
                
                # Store the result
                scores[option.description] = max(0, min(100, final_score))
            
            return scores
            
        except Exception as e:
            logger.error(f"Error calculating feasibility scores: {str(e)}")
            return {option.description: option.feasibility_score for option in remediation_options}
    
    def analyze_emotional_impact(self, remediation_options: List[RemediationOption], profile: dict) -> Dict[str, Dict[str, Any]]:
        """
        Consider non-financial emotional factors of remediation options.
        
        Args:
            remediation_options: List of remediation options to evaluate
            profile: User profile data
            
        Returns:
            Dictionary mapping option descriptions to emotional impact assessments
        """
        results = {}
        
        try:
            # Check for family structure information
            has_joint_family = False
            family_orientation = "independent"
            
            if 'family_type' in profile:
                if 'joint' in profile['family_type'].lower():
                    has_joint_family = True
                    family_orientation = "joint"
                elif 'nuclear' in profile['family_type'].lower():
                    family_orientation = "nuclear"
            
            # Evaluate emotional impact for each option
            for option in remediation_options:
                impact = {
                    "stress_level": "medium",
                    "satisfaction_impact": "neutral",
                    "family_implications": "minimal",
                    "cultural_alignment": "moderate",
                    "description": "Balanced emotional impact with manageable stress levels"
                }
                
                # Analyze implementation steps for complexity
                step_count = len(option.implementation_steps)
                complex_steps = 0
                for step in option.implementation_steps:
                    if 'action' in step and any(term in step['action'].lower() for term in 
                                              ['difficult', 'complex', 'challenging', 'significant']):
                        complex_steps += 1
                
                complexity_ratio = complex_steps / max(1, step_count)
                
                # Assess stress level
                if complexity_ratio > 0.5:
                    impact["stress_level"] = "high"
                elif complexity_ratio > 0.25:
                    impact["stress_level"] = "medium"
                else:
                    impact["stress_level"] = "low"
                
                # Assess satisfaction impact based on gap reduction
                if "gap_reduction_percentage" in option.impact_metrics:
                    reduction = option.impact_metrics["gap_reduction_percentage"]
                    if reduction > 80:
                        impact["satisfaction_impact"] = "very_positive"
                    elif reduction > 50:
                        impact["satisfaction_impact"] = "positive"
                    elif reduction > 20:
                        impact["satisfaction_impact"] = "slightly_positive"
                    else:
                        impact["satisfaction_impact"] = "neutral"
                
                # Assess family implications (especially important in Indian context)
                if has_joint_family:
                    # In joint families, financial decisions often impact the wider family
                    if "monthly_savings_adjustment" in option.impact_metrics and abs(option.impact_metrics["monthly_savings_adjustment"]) > 5000:
                        impact["family_implications"] = "significant"
                    elif "target_adjustment" in option.impact_metrics and option.impact_metrics["target_adjustment"] < 0:
                        impact["family_implications"] = "moderate"
                    else:
                        impact["family_implications"] = "minor"
                
                # Assess cultural alignment
                cultural_alignment = self._assess_cultural_alignment(option, family_orientation)
                impact["cultural_alignment"] = cultural_alignment
                
                # Generate overall description
                stress = impact["stress_level"]
                satisfaction = impact["satisfaction_impact"]
                family = impact["family_implications"]
                culture = impact["cultural_alignment"]
                
                # Build description based on factors
                desc_parts = []
                
                if stress == "high":
                    desc_parts.append("potentially stressful implementation")
                
                if satisfaction in ["positive", "very_positive"]:
                    desc_parts.append("likely to provide satisfaction through significant progress")
                
                if family == "significant":
                    desc_parts.append("requires family discussion and agreement")
                
                if culture == "high":
                    desc_parts.append("well-aligned with cultural expectations")
                elif culture == "low":
                    desc_parts.append("may conflict with traditional expectations")
                
                if desc_parts:
                    impact["description"] = f"Strategy with {', '.join(desc_parts)}."
                
                # Add India-specific context if relevant
                india_specific = self._get_india_specific_emotional_factors(option, profile)
                if india_specific:
                    impact["india_specific_factors"] = india_specific
                
                results[option.description] = impact
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing emotional impact: {str(e)}")
            return {option.description: {"description": "Unable to analyze emotional impact"} for option in remediation_options}
    
    def estimate_implementation_difficulty(self, remediation_option: RemediationOption) -> Dict[str, Any]:
        """
        Assess the complexity and challenge level of implementing a remediation option.
        
        Args:
            remediation_option: Remediation option to evaluate
            
        Returns:
            Dictionary with implementation difficulty assessment
        """
        assessment = {
            "overall_difficulty": 0.0,
            "time_required": 0.0,
            "knowledge_needed": 0.0,
            "effort_level": 0.0,
            "external_dependencies": 0.0,
            "indian_market_complexity": 0.0,
            "difficulty_factors": [],
            "implementation_timeline": "",
            "description": ""
        }
        
        try:
            # Analyze implementation steps
            steps = remediation_option.implementation_steps
            
            # Assess time required
            time_required = len(steps) * 0.5  # Base estimate
            for step in steps:
                if 'action' in step and any(term in step['action'].lower() for term in 
                                          ['research', 'evaluate', 'analyze', 'review']):
                    time_required += 0.5  # Research steps take longer
            
            assessment["time_required"] = min(5.0, time_required)  # Scale from 0-5
            
            # Assess knowledge needed
            knowledge_terms = ['understand', 'learn', 'research', 'analyze', 'calculate', 'evaluate']
            knowledge_needed = 0.0
            for step in steps:
                if 'action' in step:
                    for term in knowledge_terms:
                        if term in step['action'].lower():
                            knowledge_needed += 0.5
                            break
            
            assessment["knowledge_needed"] = min(5.0, knowledge_needed)  # Scale from 0-5
            
            # Assess effort level
            effort_terms = ['increase', 'reduce', 'adjust', 'change', 'modify']
            effort_level = 0.0
            for step in steps:
                if 'action' in step:
                    for term in effort_terms:
                        if term in step['action'].lower():
                            effort_level += 0.5
                            break
            
            assessment["effort_level"] = min(5.0, effort_level)  # Scale from 0-5
            
            # Assess external dependencies
            dependency_terms = ['consult', 'advisor', 'professional', 'expert', 'agent', 'broker']
            external_dependencies = 0.0
            for step in steps:
                if 'action' in step:
                    for term in dependency_terms:
                        if term in step['action'].lower():
                            external_dependencies += 1.0
                            break
            
            assessment["external_dependencies"] = min(5.0, external_dependencies)  # Scale from 0-5
            
            # Assess Indian market complexity
            indian_terms = ['tax', 'elss', 'ppf', 'nps', 'mutual fund', 'insurance', 'ulip']
            market_complexity = 0.0
            for step in steps:
                if 'action' in step:
                    for term in indian_terms:
                        if term in step['action'].lower():
                            market_complexity += 0.7
                            break
            
            assessment["indian_market_complexity"] = min(5.0, market_complexity)  # Scale from 0-5
            
            # Calculate overall difficulty using weighted factors
            weights = self.params["implementation_complexity_weights"]
            overall = (
                weights["time_required"] * assessment["time_required"] +
                weights["knowledge_needed"] * assessment["knowledge_needed"] +
                weights["effort_level"] * assessment["effort_level"] +
                weights["external_dependencies"] * assessment["external_dependencies"]
            ) / sum(weights.values())
            
            # Add Indian market complexity to overall score
            overall = (overall * 0.8) + (assessment["indian_market_complexity"] * 0.2)
            
            assessment["overall_difficulty"] = min(5.0, overall)
            
            # Identify key difficulty factors
            factors = []
            if assessment["time_required"] >= 3.0:
                factors.append("Time-intensive implementation")
            if assessment["knowledge_needed"] >= 3.0:
                factors.append("Requires specialized financial knowledge")
            if assessment["effort_level"] >= 3.0:
                factors.append("Requires significant personal effort")
            if assessment["external_dependencies"] >= 3.0:
                factors.append("Dependent on external professionals")
            if assessment["indian_market_complexity"] >= 3.0:
                factors.append("Navigating complex Indian financial products")
            
            assessment["difficulty_factors"] = factors
            
            # Estimate implementation timeline
            timeline_months = 1 + math.ceil(assessment["overall_difficulty"])
            assessment["implementation_timeline"] = f"Approximately {timeline_months} months to fully implement"
            
            # Generate description
            if assessment["overall_difficulty"] < 1.5:
                difficulty = "Easy"
            elif assessment["overall_difficulty"] < 2.5:
                difficulty = "Moderate"
            elif assessment["overall_difficulty"] < 3.5:
                difficulty = "Challenging"
            elif assessment["overall_difficulty"] < 4.5:
                difficulty = "Difficult"
            else:
                difficulty = "Very Difficult"
                
            factor_text = ", ".join(factors) if factors else "No major difficulty factors"
            assessment["description"] = f"{difficulty} implementation. {factor_text}. {assessment['implementation_timeline']}."
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error estimating implementation difficulty: {str(e)}")
            assessment["description"] = "Unable to estimate implementation difficulty"
            return assessment
    
    def perform_sensitivity_analysis(self, gap: GapResult, variables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify critical factors that affect gap remediation strategy success.
        
        Args:
            gap: Gap analysis result
            variables: List of variables to test sensitivity for
                Each variable is a dict with keys: 'name', 'base_value', 'low_value', 'high_value'
            
        Returns:
            Dictionary with sensitivity analysis results
        """
        results = {
            "most_sensitive_variables": [],
            "sensitivity_scores": {},
            "critical_thresholds": {},
            "indian_context_factors": {},
            "inflation_sensitivity": {},
            "description": ""
        }
        
        try:
            if not variables:
                return results
            
            # Calculate base gap
            base_gap = gap.gap_amount
            
            # Analyze each variable
            sensitivities = {}
            for var in variables:
                name = var.get('name', 'Unknown')
                base = var.get('base_value', 0)
                low = var.get('low_value', base * 0.8)
                high = var.get('high_value', base * 1.2)
                
                if base == 0:
                    # Avoid division by zero
                    sensitivities[name] = 0
                    continue
                
                # Calculate gap with low value
                low_impact = self._calculate_modified_gap(gap, name, low)
                low_change_pct = (low_impact - base_gap) / abs(base_gap) if base_gap != 0 else 0
                
                # Calculate gap with high value
                high_impact = self._calculate_modified_gap(gap, name, high)
                high_change_pct = (high_impact - base_gap) / abs(base_gap) if base_gap != 0 else 0
                
                # Calculate sensitivity (average of absolute percentage changes)
                sensitivity = (abs(low_change_pct) + abs(high_change_pct)) / 2
                sensitivities[name] = sensitivity
                
                # Store detailed sensitivity results
                results["sensitivity_scores"][name] = {
                    "score": sensitivity,
                    "low_value_impact": low_change_pct,
                    "high_value_impact": high_change_pct
                }
                
                # Calculate critical threshold if possible
                if low_change_pct * high_change_pct < 0:  # Signs are different, indicating a threshold exists
                    # Simple linear interpolation to find threshold
                    threshold_pct = low + (high - low) * (abs(low_change_pct) / (abs(low_change_pct) + abs(high_change_pct)))
                    threshold_value = base * (threshold_pct / 100)
                    results["critical_thresholds"][name] = threshold_value
            
            # Sort variables by sensitivity
            sorted_vars = sorted(sensitivities.items(), key=lambda x: x[1], reverse=True)
            results["most_sensitive_variables"] = [v[0] for v in sorted_vars]
            
            # Analyze inflation sensitivity (especially important in Indian context)
            inflation_sensitivity = self._analyze_inflation_sensitivity(gap)
            results["inflation_sensitivity"] = inflation_sensitivity
            
            # Add Indian context factors
            indian_factors = {}
            for var in variables:
                name = var.get('name', '').lower()
                if name in ["inflation", "inflation_rate"]:
                    indian_factors["inflation"] = "Higher and more volatile inflation in India increases sensitivity"
                elif "return" in name:
                    indian_factors["returns"] = "Market returns in India can be more volatile than developed markets"
                elif "gold" in name:
                    indian_factors["gold"] = "Cultural significance of gold in India affects investment patterns"
                elif "property" in name or "real_estate" in name:
                    indian_factors["real_estate"] = "Property values in urban India have high growth potential but also high volatility"
            
            results["indian_context_factors"] = indian_factors
            
            # Generate description
            if results["most_sensitive_variables"]:
                top_var = results["most_sensitive_variables"][0]
                top_score = sensitivities[top_var]
                
                if top_score > 0.5:
                    sensitivity_level = "extremely sensitive"
                elif top_score > 0.3:
                    sensitivity_level = "highly sensitive"
                elif top_score > 0.1:
                    sensitivity_level = "moderately sensitive"
                else:
                    sensitivity_level = "relatively insensitive"
                
                results["description"] = f"Gap remediation is {sensitivity_level} to changes in {top_var}."
                
                if len(results["most_sensitive_variables"]) > 1:
                    second_var = results["most_sensitive_variables"][1]
                    results["description"] += f" Also significant sensitivity to {second_var}."
                
                # Add Indian context if relevant
                if "inflation" in indian_factors:
                    results["description"] += f" {indian_factors['inflation']}."
            else:
                results["description"] = "Unable to determine sensitivity factors with provided variables."
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing sensitivity analysis: {str(e)}")
            results["description"] = "Error in sensitivity analysis calculation"
            return results
    
    def compare_remediation_strategies(self, options: List[RemediationOption]) -> Dict[str, Any]:
        """
        Provide side-by-side comparison of different remediation strategies.
        
        Args:
            options: List of remediation options to compare
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            "ranked_options": [],
            "comparison_metrics": {},
            "tradeoff_analysis": {},
            "indian_context_ranking": [],
            "recommendation": "",
            "family_impact_comparison": {}
        }
        
        try:
            if not options:
                return comparison
            
            # Define comparison metrics
            metrics = [
                "gap_reduction_percentage",
                "monthly_savings_adjustment",
                "timeframe_extension",
                "feasibility_score"
            ]
            
            # Initialize comparison metrics
            comparison["comparison_metrics"] = {metric: {} for metric in metrics}
            
            # Collect metrics for each option
            for option in options:
                desc = option.description
                
                # Get values for each metric
                for metric in metrics:
                    if metric == "feasibility_score":
                        comparison["comparison_metrics"][metric][desc] = option.feasibility_score
                    elif metric in option.impact_metrics:
                        comparison["comparison_metrics"][metric][desc] = option.impact_metrics[metric]
                    else:
                        comparison["comparison_metrics"][metric][desc] = 0
            
            # Calculate scores for ranking
            scores = {}
            for option in options:
                desc = option.description
                
                # Gap reduction (higher is better) - weight: 0.4
                gap_reduction = comparison["comparison_metrics"]["gap_reduction_percentage"].get(desc, 0)
                gap_score = gap_reduction / 100 * 0.4
                
                # Feasibility (higher is better) - weight: 0.3
                feasibility = comparison["comparison_metrics"]["feasibility_score"].get(desc, 0)
                feasibility_score = feasibility / 100 * 0.3
                
                # Monthly savings adjustment (lower absolute value is better) - weight: 0.2
                savings_adj = abs(comparison["comparison_metrics"]["monthly_savings_adjustment"].get(desc, 0))
                max_adj = max(abs(comparison["comparison_metrics"]["monthly_savings_adjustment"].get(o.description, 0)) for o in options)
                savings_score = (1 - (savings_adj / max_adj if max_adj > 0 else 0)) * 0.2
                
                # Timeframe extension (lower is better) - weight: 0.1
                extension = comparison["comparison_metrics"]["timeframe_extension"].get(desc, 0)
                max_ext = max(comparison["comparison_metrics"]["timeframe_extension"].get(o.description, 0) for o in options)
                extension_score = (1 - (extension / max_ext if max_ext > 0 else 0)) * 0.1
                
                # Calculate total score
                total_score = gap_score + feasibility_score + savings_score + extension_score
                scores[desc] = total_score
            
            # Rank options by score
            comparison["ranked_options"] = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
            
            # Calculate Indian context ranking with cultural factors
            indian_scores = {}
            for option in options:
                desc = option.description
                
                # Start with base score
                indian_scores[desc] = scores[desc] * 0.7  # 70% of original score
                
                # Check for Indian context factors in implementation steps
                indian_factor_score = 0
                for step in option.implementation_steps:
                    if 'action' in step:
                        action = step['action'].lower()
                        # Check for culturally relevant terms
                        if any(term in action for term in ['family', 'parent', 'tradition', 'cultural', 'social']):
                            indian_factor_score += 0.05
                        # Check for India-specific investment terms
                        if any(term in action for term in ['ppf', 'elss', 'epf', 'nps', 'ulip']):
                            indian_factor_score += 0.05
                
                # Add Indian context bonus
                indian_scores[desc] += indian_factor_score
                
                # Adjust for family impact if relevant
                if "family" in desc.lower() or "parent" in desc.lower():
                    indian_scores[desc] *= 1.1  # 10% bonus for family-oriented strategies
            
            # Rank options by Indian context score
            comparison["indian_context_ranking"] = sorted(indian_scores.keys(), key=lambda x: indian_scores[x], reverse=True)
            
            # Generate tradeoff analysis
            tradeoffs = {}
            if len(options) >= 2:
                for i, option1_desc in enumerate(comparison["ranked_options"]):
                    for option2_desc in comparison["ranked_options"][i+1:]:
                        # Compare metrics between options
                        advantages = []
                        disadvantages = []
                        
                        for metric in metrics:
                            val1 = comparison["comparison_metrics"][metric].get(option1_desc, 0)
                            val2 = comparison["comparison_metrics"][metric].get(option2_desc, 0)
                            
                            if metric == "gap_reduction_percentage" or metric == "feasibility_score":
                                # Higher is better
                                if val1 > val2 * 1.1:  # At least 10% better
                                    advantages.append(f"Better {metric.replace('_', ' ')} ({val1:.1f} vs {val2:.1f})")
                                elif val2 > val1 * 1.1:
                                    disadvantages.append(f"Lower {metric.replace('_', ' ')} ({val1:.1f} vs {val2:.1f})")
                            else:
                                # Lower is better
                                if val1 * 1.1 < val2:  # At least 10% better
                                    advantages.append(f"Lower {metric.replace('_', ' ')} ({val1:.1f} vs {val2:.1f})")
                                elif val1 > val2 * 1.1:
                                    disadvantages.append(f"Higher {metric.replace('_', ' ')} ({val1:.1f} vs {val2:.1f})")
                        
                        # Store tradeoff analysis
                        tradeoffs[f"{option1_desc} vs {option2_desc}"] = {
                            "advantages": advantages,
                            "disadvantages": disadvantages
                        }
            
            comparison["tradeoff_analysis"] = tradeoffs
            
            # Compare family impact
            family_impacts = {}
            for option in options:
                desc = option.description
                
                # Check for family-related terms
                family_terms = ['family', 'parent', 'child', 'relative', 'dependent']
                family_mentions = sum(1 for step in option.implementation_steps if 'action' in step and 
                                     any(term in step['action'].lower() for term in family_terms))
                
                if family_mentions > 0:
                    family_impacts[desc] = "Direct family implications requiring discussion and agreement"
                elif any(term in desc.lower() for term in ['reduce', 'cut', 'lower', 'decrease']):
                    family_impacts[desc] = "May affect family resources and require explanation to family members"
                else:
                    family_impacts[desc] = "Minimal direct family impact"
            
            comparison["family_impact_comparison"] = family_impacts
            
            # Generate recommendation
            if comparison["ranked_options"]:
                top_option = comparison["ranked_options"][0]
                indian_top = comparison["indian_context_ranking"][0]
                
                if top_option == indian_top:
                    comparison["recommendation"] = f"Recommended strategy: {top_option}. This option provides the best balance of effectiveness, feasibility, and cultural alignment."
                else:
                    comparison["recommendation"] = f"Primary recommendation: {top_option} (optimal balance of effectiveness and feasibility). Alternative recommendation with stronger cultural alignment: {indian_top}."
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing remediation strategies: {str(e)}")
            comparison["recommendation"] = "Unable to compare strategies due to an error"
            return comparison
    
    def _extract_monthly_income(self, profile: dict) -> float:
        """
        Extract monthly income from profile data.
        
        Args:
            profile: User profile data
            
        Returns:
            Monthly income amount
        """
        monthly_income = 10000.0  # Default assumption
        
        try:
            if 'income' in profile:
                income = profile['income']
                if isinstance(income, dict) and 'amount' in income:
                    monthly_income = income['amount']
                    if income.get('frequency', '').lower() in ['annual', 'yearly']:
                        monthly_income /= 12
                else:
                    monthly_income = float(income)
            elif 'answers' in profile:
                for answer in profile['answers']:
                    if 'income' in answer.get('question_id', '').lower():
                        value = answer.get('answer')
                        if isinstance(value, (int, float)):
                            monthly_income = float(value)
                            break
                        elif isinstance(value, dict) and 'amount' in value:
                            monthly_income = float(value['amount'])
                            if value.get('frequency', '').lower() in ['annual', 'yearly']:
                                monthly_income /= 12
                            break
                        elif isinstance(value, str) and value.replace('.', '', 1).isdigit():
                            monthly_income = float(value)
                            break
            
            return monthly_income
            
        except Exception as e:
            logger.error(f"Error extracting monthly income: {str(e)}")
            return monthly_income
    
    def _calculate_indian_context_factor(self, option: RemediationOption, profile: dict) -> float:
        """
        Calculate Indian context adjustment factor for feasibility.
        
        Args:
            option: Remediation option
            profile: User profile data
            
        Returns:
            Adjustment factor (typically 0.7-1.2)
        """
        # Default factor (no adjustment)
        factor = 1.0
        
        try:
            # Check for family structure
            has_joint_family = False
            if 'family_type' in profile and 'joint' in profile['family_type'].lower():
                has_joint_family = True
                factor *= 0.9  # Joint families may have more complex decision processes
            
            # Check for implementation steps involving specific Indian financial products
            indian_products = ['ppf', 'epf', 'nps', 'elss', 'ulip', 'sukanya samriddhi']
            india_specific_steps = 0
            
            for step in option.implementation_steps:
                if 'action' in step:
                    if any(product in step['action'].lower() for product in indian_products):
                        india_specific_steps += 1
            
            if india_specific_steps > 0:
                # Adjust factor based on Indian-specific steps
                factor *= (1.0 - (india_specific_steps * 0.05))
            
            # Check for cultural factors
            if has_joint_family and "monthly_savings_adjustment" in option.impact_metrics:
                # In joint families, significant financial changes often require family consultation
                savings_change = option.impact_metrics["monthly_savings_adjustment"]
                if abs(savings_change) > 5000:
                    factor *= 0.9  # Additional adjustment for large changes in joint family context
            
            # Ensure factor stays in reasonable range
            return max(0.7, min(1.2, factor))
            
        except Exception as e:
            logger.error(f"Error calculating Indian context factor: {str(e)}")
            return factor
    
    def _assess_cultural_alignment(self, option: RemediationOption, family_orientation: str) -> str:
        """
        Assess how well the remediation option aligns with cultural expectations.
        
        Args:
            option: Remediation option
            family_orientation: Family structure type
            
        Returns:
            Cultural alignment level ("low", "moderate", "high")
        """
        # Default alignment
        alignment = "moderate"
        
        try:
            # Check for cultural alignment indicators
            alignment_score = 0
            
            # Check implementation steps
            for step in option.implementation_steps:
                if 'action' in step:
                    action = step['action'].lower()
                    
                    # Positive alignment factors
                    if any(term in action for term in ['family', 'together', 'discuss']):
                        alignment_score += 1
                    
                    # Neutral factors
                    if any(term in action for term in ['adjust', 'modify', 'review']):
                        alignment_score += 0
                    
                    # Negative alignment factors
                    if any(term in action for term in ['cut', 'reduce', 'eliminate', 'sacrifice']):
                        alignment_score -= 1
            
            # Check impact metrics
            if "target_adjustment" in option.impact_metrics and option.impact_metrics["target_adjustment"] < 0:
                # Reducing targets (especially for cultural goals) may have negative alignment
                alignment_score -= 1
            
            # Family orientation effect
            if family_orientation == "joint" and alignment_score < 0:
                alignment_score -= 1  # Additional penalty in joint family context
            
            # Determine final alignment
            if alignment_score >= 2:
                alignment = "high"
            elif alignment_score <= -2:
                alignment = "low"
            
            return alignment
            
        except Exception as e:
            logger.error(f"Error assessing cultural alignment: {str(e)}")
            return alignment
    
    def _get_india_specific_emotional_factors(self, option: RemediationOption, profile: dict) -> Dict[str, str]:
        """
        Get India-specific emotional impact factors.
        
        Args:
            option: Remediation option
            profile: User profile data
            
        Returns:
            Dictionary with India-specific emotional factors
        """
        factors = {}
        
        # Extract option characteristics
        desc = option.description.lower()
        
        # Check for education-related factors
        if "education" in desc:
            factors["education"] = "Educational goals have high emotional significance in Indian families and are often seen as non-negotiable"
        
        # Check for property-related factors
        if "property" in desc or "home" in desc:
            factors["property"] = "Property ownership carries significant social status implications in Indian society"
        
        # Check for wedding-related factors
        if "wedding" in desc or "marriage" in desc:
            factors["wedding"] = "Wedding expenses are often considered essential family obligations with social implications"
        
        # Check for retirement/parents-related factors
        if "parent" in desc or "retirement" in desc:
            factors["family_care"] = "Caring for parents and elders is a cultural expectation with strong emotional components"
        
        return factors
    
    def _calculate_modified_gap(self, gap: GapResult, variable_name: str, new_value: float) -> float:
        """
        Calculate modified gap amount when changing a variable.
        
        Args:
            gap: Gap analysis result
            variable_name: Name of variable being modified
            new_value: New value for the variable
            
        Returns:
            Modified gap amount
        """
        # This is a simplified simulation that would be expanded in a real implementation
        # with actual formulas for different variables
        
        base_gap = gap.gap_amount
        
        # Apply different calculations based on variable type
        if "return" in variable_name.lower():
            # Simplified calculation for return rate changes
            return base_gap * (1 - (new_value / 100))
        elif "contribution" in variable_name.lower() or "saving" in variable_name.lower():
            # For contribution changes
            return base_gap - (new_value * 12)  # Assuming monthly to annual conversion
        elif "inflation" in variable_name.lower():
            # For inflation changes
            inflation_sensitivity = 0.3  # Higher inflation increases gap
            return base_gap * (1 + ((new_value - 6) / 100 * inflation_sensitivity))
        elif "time" in variable_name.lower() or "duration" in variable_name.lower():
            # For timeframe changes
            return base_gap * (1 - (new_value / 60))  # Assuming time in months
        else:
            # Generic calculation for other variables
            return base_gap  # Default: no change
    
    def _analyze_inflation_sensitivity(self, gap: GapResult) -> Dict[str, Any]:
        """
        Analyze sensitivity to inflation, particularly important in Indian context.
        
        Args:
            gap: Gap analysis result
            
        Returns:
            Dictionary with inflation sensitivity analysis
        """
        result = {
            "base_inflation_rate": 6.0,  # Default Indian inflation
            "impact_per_percent": 0.0,
            "critical_inflation_rate": 0.0,
            "is_highly_sensitive": False,
            "indian_context_note": ""
        }
        
        # Calculate impact of different inflation rates
        base_gap = gap.gap_amount
        base_inflation = result["base_inflation_rate"]
        
        # Calculate gap at +1% inflation
        higher_gap = self._calculate_modified_gap(gap, "inflation_rate", base_inflation + 1)
        impact_per_percent = (higher_gap - base_gap) / base_gap * 100
        
        result["impact_per_percent"] = impact_per_percent
        
        # Determine if goal is highly sensitive to inflation
        if abs(impact_per_percent) > 10:
            result["is_highly_sensitive"] = True
        
        # Estimate critical inflation rate (where gap increases by 50%)
        if impact_per_percent > 0:
            critical_increase = 50 / impact_per_percent
            result["critical_inflation_rate"] = base_inflation + critical_increase
        
        # Add Indian context note
        if result["is_highly_sensitive"]:
            result["indian_context_note"] = "Goal shows high sensitivity to inflation, which is particularly concerning in the Indian context where inflation can be volatile. Consider inflation-hedged investments like TIPS, gold, or real estate."
        else:
            result["indian_context_note"] = "Goal shows manageable inflation sensitivity. Standard inflation protection strategies in Indian context should be sufficient."
        
        return result
"""
GoalDocumentGenerator Module

This module provides a comprehensive document generation system for financial goals.
It creates detailed, personalized goal documents with visualizations, recommendations,
and educational content tailored to Indian users' financial context.
"""

import os
import json
import logging
import uuid
import math
import locale
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
import io
import base64
from pathlib import Path

# Import models and services
from models.goal_models import Goal, GoalManager
from models.goal_probability import GoalOutcomeDistribution, ProbabilityResult
from models.goal_calculator import GoalCalculator
from models.financial_parameters import FinancialParameters
from models.financial_projection import AssetProjection

# Set locale for Indian Rupee formatting
try:
    locale.setlocale(locale.LC_MONETARY, 'en_IN')
except locale.Error:
    # Fallback if Indian locale not available
    logging.warning("Indian locale not available. Using default locale for monetary formatting.")
    locale.setlocale(locale.LC_MONETARY, '')

# Indian financial constants
INDIA_FINANCIAL_CONSTANTS = {
    "inflation": {
        "general": 0.06,  # 6% general inflation
        "education": 0.10,  # 10% education inflation
        "healthcare": 0.08,  # 8% healthcare inflation
        "housing": 0.07,  # 7% housing inflation
    },
    "tax_rates": {
        "old_regime": [
            {"limit": 250000, "rate": 0.0},
            {"limit": 500000, "rate": 0.05},
            {"limit": 1000000, "rate": 0.20},
            {"limit": float('inf'), "rate": 0.30}
        ],
        "new_regime": [
            {"limit": 300000, "rate": 0.0},
            {"limit": 600000, "rate": 0.05},
            {"limit": 900000, "rate": 0.10},
            {"limit": 1200000, "rate": 0.15},
            {"limit": 1500000, "rate": 0.20},
            {"limit": float('inf'), "rate": 0.30}
        ]
    },
    "tax_deductions": {
        "80c_limit": 150000,
        "80d_limit_self": 25000,
        "80d_limit_parents": 50000,
        "80d_limit_senior": 50000,
        "nps_additional": 50000,
        "standard_deduction": 50000,
        "hra_exemption_metro": 0.50,  # 50% of basic for metro cities
        "hra_exemption_non_metro": 0.40  # 40% of basic for non-metro cities
    },
    "retirement": {
        "epf_contribution_rate": 0.12,  # 12% of basic salary
        "epf_interest_rate": 0.0815,  # 8.15% current EPF interest rate
        "nps_annuity_requirement": 0.40  # 40% of corpus must be used for annuity
    },
    "investment": {
        "equity_expected_return": 0.12,  # 12% for equity
        "debt_expected_return": 0.07,  # 7% for debt
        "gold_expected_return": 0.08,  # 8% for gold
        "real_estate_expected_return": 0.09,  # 9% for real estate
        "fd_interest_rate": 0.065,  # 6.5% fixed deposit rate
        "ppf_interest_rate": 0.071,  # 7.1% PPF interest rate
        "sukanya_samriddhi_rate": 0.079  # 7.9% Sukanya Samriddhi Yojana rate
    },
    "life_stages": {
        "young_adult": {"age_min": 21, "age_max": 30},
        "early_career": {"age_min": 31, "age_max": 40},
        "mid_career": {"age_min": 41, "age_max": 50},
        "late_career": {"age_min": 51, "age_max": 60},
        "retirement": {"age_min": 61, "age_max": 120}
    },
    "asset_allocation": {
        "aggressive": {"equity": 0.75, "debt": 0.15, "gold": 0.05, "real_estate": 0.05},
        "moderately_aggressive": {"equity": 0.60, "debt": 0.25, "gold": 0.10, "real_estate": 0.05},
        "balanced": {"equity": 0.50, "debt": 0.30, "gold": 0.10, "real_estate": 0.10},
        "moderately_conservative": {"equity": 0.30, "debt": 0.50, "gold": 0.10, "real_estate": 0.10},
        "conservative": {"equity": 0.20, "debt": 0.60, "gold": 0.10, "real_estate": 0.10}
    }
}

# Optional PDF generation and visualization
try:
    import matplotlib.pyplot as plt
    import matplotlib.figure as figure
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.gridspec import GridSpec
    import matplotlib.colors as mcolors
    import matplotlib.patches as mpatches
    import numpy as np
    from matplotlib.ticker import FuncFormatter
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DocumentSection:
    """Base class for document sections to standardize structure."""
    
    def __init__(self, title: str, content: Dict[str, Any] = None):
        """
        Initialize a document section.
        
        Args:
            title (str): Section title
            content (Dict[str, Any], optional): Initial content dictionary
        """
        self.title = title
        self.content = content or {}
        self.visualizations = []
    
    def add_content(self, key: str, value: Any) -> None:
        """Add content to the section."""
        self.content[key] = value
    
    def add_visualization(self, viz_type: str, data: Dict[str, Any]) -> None:
        """Add visualization data."""
        self.visualizations.append({
            "type": viz_type,
            "data": data
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert section to dictionary format."""
        return {
            "title": self.title,
            "content": self.content,
            "visualizations": self.visualizations
        }


class GoalDocumentGenerator:
    """
    Generates detailed, personalized financial goal documents with visualizations,
    recommendations, and educational content tailored to Indian users.
    """
    
    def __init__(self, db_path: str = None, output_dir: str = None):
        """
        Initialize the document generator.
        
        Args:
            db_path (str, optional): Path to database for goal data
            output_dir (str, optional): Directory for saving generated documents
        """
        self.goal_manager = GoalManager(db_path) if db_path else GoalManager()
        self.output_dir = output_dir or os.path.join(os.getcwd(), "generated_documents")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
                logger.info(f"Created output directory: {self.output_dir}")
            except Exception as e:
                logger.error(f"Failed to create output directory: {str(e)}")
        
        # Initialize visualization capabilities
        self.visualization_enabled = HAS_MATPLOTLIB
        self.pdf_enabled = HAS_REPORTLAB
        
        if not self.visualization_enabled:
            logger.warning("Matplotlib not available. Visualizations will be limited.")
        
        if not self.pdf_enabled:
            logger.warning("ReportLab not available. PDF generation will be disabled.")
        
        # Initialize Indian financial context
        self.india_financial = INDIA_FINANCIAL_CONSTANTS
        
    def format_rupees(self, amount: float) -> str:
        """
        Format amount as Indian Rupees with appropriate symbols and commas.
        
        Args:
            amount (float): Amount to format
            
        Returns:
            str: Formatted amount string with ₹ symbol
        """
        try:
            # Try to use locale-based formatting
            formatted = locale.currency(amount, grouping=True, symbol=False)
            return f"₹{formatted}"
        except (ValueError, AttributeError):
            # Fallback to manual formatting
            if amount >= 10000000:  # 1 crore
                value = amount / 10000000
                return f"₹{value:.2f} Cr"
            elif amount >= 100000:  # 1 lakh
                value = amount / 100000
                return f"₹{value:.2f} L"
            elif amount >= 1000:
                # Custom format with commas for thousands
                s = f"{amount:.0f}"
                result = s[-3:]
                s = s[:-3]
                while s:
                    result = s[-2:] + "," + result if len(s) >= 2 else s + "," + result
                    s = s[:-2]
                return f"₹{result}"
            else:
                return f"₹{amount:.2f}"
    
    def calculate_tax_liability(self, income: float, deductions: Dict[str, float], regime: str = "new_regime") -> Dict[str, float]:
        """
        Calculate income tax liability using Indian tax slabs.
        
        Args:
            income (float): Total taxable income
            deductions (Dict[str, float]): Dictionary of applicable deductions
            regime (str): Tax regime to use ("old_regime" or "new_regime")
            
        Returns:
            Dict[str, float]: Tax calculation results
        """
        tax_slabs = self.india_financial["tax_rates"][regime]
        
        # Calculate total deductions
        total_deductions = sum(deductions.values())
        
        # Apply standard deduction if old regime
        if regime == "old_regime":
            total_deductions += self.india_financial["tax_deductions"]["standard_deduction"]
        
        # Calculate taxable income
        taxable_income = max(0, income - total_deductions)
        
        # Calculate tax based on slabs
        tax = 0.0
        remaining_income = taxable_income
        
        for i, slab in enumerate(tax_slabs):
            if i == 0:
                # First slab
                taxable_in_slab = min(remaining_income, slab["limit"])
                tax += taxable_in_slab * slab["rate"]
                remaining_income -= taxable_in_slab
            else:
                # Higher slabs
                prev_limit = tax_slabs[i-1]["limit"]
                limit_in_slab = slab["limit"] - prev_limit
                taxable_in_slab = min(remaining_income, limit_in_slab)
                tax += taxable_in_slab * slab["rate"]
                remaining_income -= taxable_in_slab
                
            if remaining_income <= 0:
                break
        
        # Calculate cess (4% health and education cess)
        cess = tax * 0.04
        
        # Calculate total tax liability
        total_tax = tax + cess
        
        # Calculate effective tax rate
        effective_tax_rate = (total_tax / income) * 100 if income > 0 else 0
        
        return {
            "gross_income": income,
            "total_deductions": total_deductions,
            "taxable_income": taxable_income,
            "tax_on_income": tax,
            "cess": cess,
            "total_tax_liability": total_tax,
            "effective_tax_rate": effective_tax_rate
        }
    
    def calculate_sip_amount(self, target_amount: float, years: float, expected_return: float = None) -> float:
        """
        Calculate required monthly SIP amount for a goal.
        
        Args:
            target_amount (float): Target amount to accumulate
            years (float): Time period in years
            expected_return (float, optional): Expected annual return rate
            
        Returns:
            float: Required monthly SIP amount
        """
        # Use default return rate based on asset allocation if not provided
        if expected_return is None:
            # Balanced portfolio return
            expected_return = (
                self.india_financial["investment"]["equity_expected_return"] * 0.5 +
                self.india_financial["investment"]["debt_expected_return"] * 0.3 +
                self.india_financial["investment"]["gold_expected_return"] * 0.1 +
                self.india_financial["investment"]["real_estate_expected_return"] * 0.1
            )
        
        # Convert annual rate to monthly rate
        monthly_rate = (1 + expected_return) ** (1/12) - 1
        
        # Calculate number of months
        months = years * 12
        
        # Calculate SIP amount using formula: A = P * [(1 + r)^n - 1] / [r * (1 + r)^n]
        # where A is target amount, P is monthly SIP, r is monthly rate, n is number of months
        # Rearranged for P: P = A * [r * (1 + r)^n] / [(1 + r)^n - 1]
        
        if monthly_rate <= 0 or months <= 0:
            return target_amount / months  # Simple division if no interest
        
        numerator = monthly_rate * ((1 + monthly_rate) ** months)
        denominator = ((1 + monthly_rate) ** months) - 1
        
        monthly_sip = target_amount * (numerator / denominator)
        
        return monthly_sip
    
    def project_inflation(self, amount: float, years: float, inflation_type: str = "general") -> float:
        """
        Project future value accounting for Indian inflation patterns.
        
        Args:
            amount (float): Present value amount
            years (float): Number of years
            inflation_type (str): Type of inflation to apply
            
        Returns:
            float: Inflation-adjusted future value
        """
        # Get appropriate inflation rate
        inflation_rate = self.india_financial["inflation"].get(
            inflation_type, 
            self.india_financial["inflation"]["general"]
        )
        
        # Calculate future value: FV = PV * (1 + r)^n
        future_value = amount * ((1 + inflation_rate) ** years)
        
        return future_value
    
    def get_life_stage_recommendations(self, age: int, income: float, goal_category: str) -> List[Dict[str, str]]:
        """
        Get life stage-appropriate recommendations for Indian demographics.
        
        Args:
            age (int): Age of the individual
            income (float): Monthly income
            goal_category (str): Category of the goal
            
        Returns:
            List[Dict[str, str]]: List of recommendations
        """
        # Determine life stage
        life_stage = "young_adult"  # Default
        for stage, age_range in self.india_financial["life_stages"].items():
            if age_range["age_min"] <= age <= age_range["age_max"]:
                life_stage = stage
                break
        
        # Base recommendations for all life stages
        recommendations = []
        
        # Add life stage specific recommendations
        if life_stage == "young_adult":
            recommendations.append({
                "title": "Start Early with SIPs",
                "description": f"At your age ({age}), starting SIPs even with small amounts can create significant wealth due to compounding.",
                "action": f"Start a monthly SIP of at least {self.format_rupees(income * 0.1)} (10% of income) in equity mutual funds."
            })
            
            recommendations.append({
                "title": "Emergency Fund Priority",
                "description": "In early career stages, establishing an emergency fund equivalent to 6 months of expenses should be your first financial goal.",
                "action": "Keep emergency funds in high-yield savings accounts or liquid funds for easy access."
            })
            
        elif life_stage == "early_career":
            recommendations.append({
                "title": "Increase SIP Amounts Progressively",
                "description": "As your income grows, increase your SIP amounts annually.",
                "action": f"Consider allocating 15-20% of your income ({self.format_rupees(income * 0.15)} to {self.format_rupees(income * 0.2)}) to long-term investments."
            })
            
            recommendations.append({
                "title": "Maximize Tax Benefits",
                "description": "Utilize Section 80C investments efficiently to reduce tax liability.",
                "action": "Consider ELSS funds for equity exposure with tax benefits under Section 80C."
            })
            
        elif life_stage == "mid_career":
            recommendations.append({
                "title": "Review Asset Allocation",
                "description": "At mid-career, balance between growth and stability becomes important.",
                "action": "Gradually shift toward a balanced portfolio with 50-60% in equity and the rest in debt."
            })
            
            recommendations.append({
                "title": "Accelerate Goal Funding",
                "description": "This is typically your peak earning phase; capitalize on it.",
                "action": f"Try to increase investments to 25-30% of income ({self.format_rupees(income * 0.25)} to {self.format_rupees(income * 0.3)}) to accelerate goal achievement."
            })
            
        elif life_stage == "late_career":
            recommendations.append({
                "title": "De-risk Portfolio Gradually",
                "description": "As you approach retirement, reduce volatility in your portfolio.",
                "action": "Consider shifting to a more conservative allocation with 30-40% equity and 60-70% in debt instruments."
            })
            
            recommendations.append({
                "title": "Focus on Debt Reduction",
                "description": "Aim to be debt-free before retirement.",
                "action": "Prioritize paying off high-interest loans and consider prepaying home loans if possible."
            })
            
        elif life_stage == "retirement":
            recommendations.append({
                "title": "Income Generation",
                "description": "Focus on creating regular income streams.",
                "action": "Consider Senior Citizen Savings Scheme, PMVVY, and systematic withdrawal plans from mutual funds."
            })
            
            recommendations.append({
                "title": "Healthcare Planning",
                "description": "Ensure adequate health coverage in retirement years.",
                "action": "Consider a comprehensive health insurance plan with senior citizen benefits."
            })
        
        # Add goal category specific recommendations
        if goal_category == "retirement":
            recommendations.append({
                "title": "NPS Contribution",
                "description": "National Pension System offers additional tax benefits under Section 80CCD(1B).",
                "action": f"Consider contributing up to {self.format_rupees(self.india_financial['tax_deductions']['nps_additional'])} annually to NPS for additional tax deduction."
            })
            
        elif goal_category in ["education", "higher_education"]:
            recommendations.append({
                "title": "Education-specific Investment Vehicles",
                "description": "For education goals, consider specialized investment options.",
                "action": "For girl child, consider Sukanya Samriddhi Yojana with {self.india_financial['investment']['sukanya_samriddhi_rate']*100:.1f}% interest rate."
            })
            
        elif goal_category == "home_purchase":
            recommendations.append({
                "title": "Home Loan Tax Benefits",
                "description": "Maximize tax benefits on home loans.",
                "action": "Claim principal repayment under Section 80C and interest under Section 24 for maximum tax efficiency."
            })
        
        return recommendations
    
    def generate_goal_document(self, goal: Union[Goal, str], profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete document for a specific financial goal.
        
        Args:
            goal (Union[Goal, str]): Goal object or goal ID
            profile (Dict[str, Any]): User profile data
            
        Returns:
            Dict[str, Any]: Complete document data structure
        """
        try:
            # Get Goal object if string ID was provided
            if isinstance(goal, str):
                goal = self.goal_manager.get_goal(goal)
                if not goal:
                    logger.error(f"Goal not found with ID {goal}")
                    return {"error": "Goal not found"}
            
            # Document metadata
            document = {
                "id": str(uuid.uuid4()),
                "type": "goal_document",
                "created_at": datetime.now().isoformat(),
                "goal_id": goal.id,
                "profile_id": goal.user_profile_id,
                "title": f"{goal.title} Financial Goal Plan",
                "sections": []
            }
            
            # Generate each document section
            executive_summary = self._generate_executive_summary(goal, profile)
            document["sections"].append(executive_summary.to_dict())
            
            progress_section = self._generate_progress_visualization(goal, profile)
            document["sections"].append(progress_section.to_dict())
            
            probability_section = self._generate_probability_analysis(goal, profile)
            document["sections"].append(probability_section.to_dict())
            
            recommendations = self._generate_recommendations(goal, profile)
            document["sections"].append(recommendations.to_dict())
            
            # Add Indian market specific information
            indian_context = self._generate_indian_market_context(goal.category)
            document["sections"].append(indian_context.to_dict())
            
            # Add monthly action plan
            monthly_action_plan = self._generate_monthly_action_plan(goal, profile)
            document["sections"].append(monthly_action_plan.to_dict())
            
            return document
            
        except Exception as e:
            logger.error(f"Error generating goal document: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    def generate_all_goals_summary(self, profile: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        Generate a consolidated summary of all goals for a profile.
        
        Args:
            profile (Union[Dict[str, Any], str]): Profile data or profile ID
            
        Returns:
            Dict[str, Any]: Consolidated goals summary document
        """
        try:
            # Get profile ID if full profile object was provided
            profile_id = profile if isinstance(profile, str) else profile.get("id")
            
            # Get all goals for the profile
            goals = self.goal_manager.get_profile_goals(profile_id)
            if not goals:
                logger.warning(f"No goals found for profile {profile_id}")
                return {"error": "No goals found for this profile"}
            
            # Document metadata
            document = {
                "id": str(uuid.uuid4()),
                "type": "goals_summary",
                "created_at": datetime.now().isoformat(),
                "profile_id": profile_id,
                "title": "Financial Goals Summary",
                "sections": []
            }
            
            # Overall summary section
            overall_summary = DocumentSection("Overall Goals Summary")
            
            # Goal priority analysis
            goals_by_priority = sorted(goals, key=lambda g: g.priority_score, reverse=True)
            priority_data = {
                "total_goals": len(goals),
                "total_target_amount": sum(g.target_amount for g in goals),
                "total_current_amount": sum(g.current_amount for g in goals),
                "overall_progress": self._calculate_overall_progress(goals),
                "goals_by_category": self._group_goals_by_category(goals),
                "priority_ranking": [{"id": g.id, "title": g.title, "score": g.priority_score} 
                                    for g in goals_by_priority]
            }
            overall_summary.add_content("priority_analysis", priority_data)
            
            # Add timeline visualization
            timeline_data = self._generate_goals_timeline(goals)
            overall_summary.add_visualization("timeline", timeline_data)
            
            # Add portfolio allocation recommendation
            allocation_data = self._generate_portfolio_allocation(goals)
            overall_summary.add_visualization("portfolio_allocation", allocation_data)
            
            document["sections"].append(overall_summary.to_dict())
            
            # Individual goal summaries section
            goals_section = DocumentSection("Individual Goals")
            goals_content = []
            
            for goal in goals_by_priority:
                goal_summary = {
                    "id": goal.id,
                    "title": goal.title,
                    "category": goal.category,
                    "target_amount": goal.target_amount,
                    "current_amount": goal.current_amount,
                    "progress": goal.current_progress,
                    "timeframe": goal.timeframe,
                    "priority_score": goal.priority_score,
                    "success_probability": goal.goal_success_probability
                }
                goals_content.append(goal_summary)
            
            goals_section.add_content("goals", goals_content)
            document["sections"].append(goals_section.to_dict())
            
            # Financial health indicators
            health_section = DocumentSection("Financial Health Indicators")
            health_metrics = self._calculate_financial_health_metrics(goals, profile)
            health_section.add_content("metrics", health_metrics)
            document["sections"].append(health_section.to_dict())
            
            return document
            
        except Exception as e:
            logger.error(f"Error generating goals summary: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    def generate_goal_comparison(self, goals: List[Union[Goal, str]]) -> Dict[str, Any]:
        """
        Generate a comparison report for multiple goals.
        
        Args:
            goals (List[Union[Goal, str]]): List of Goal objects or goal IDs
            
        Returns:
            Dict[str, Any]: Comparison document data
        """
        try:
            # Get Goal objects if IDs were provided
            goal_objects = []
            for goal in goals:
                if isinstance(goal, str):
                    goal_obj = self.goal_manager.get_goal(goal)
                    if goal_obj:
                        goal_objects.append(goal_obj)
                else:
                    goal_objects.append(goal)
            
            if not goal_objects:
                logger.error("No valid goals found for comparison")
                return {"error": "No valid goals found for comparison"}
            
            # Document metadata
            document = {
                "id": str(uuid.uuid4()),
                "type": "goal_comparison",
                "created_at": datetime.now().isoformat(),
                "title": "Financial Goals Comparison",
                "sections": []
            }
            
            # Comparison overview section
            comparison_section = DocumentSection("Goals Comparison Overview")
            
            # Basic comparison data
            comparison_data = []
            for goal in goal_objects:
                goal_data = {
                    "id": goal.id,
                    "title": goal.title,
                    "category": goal.category,
                    "target_amount": goal.target_amount,
                    "current_amount": goal.current_amount,
                    "progress": goal.current_progress,
                    "timeframe": goal.timeframe,
                    "priority_score": goal.priority_score,
                    "success_probability": goal.goal_success_probability,
                    "importance": goal.importance,
                    "flexibility": goal.flexibility
                }
                comparison_data.append(goal_data)
            
            comparison_section.add_content("compared_goals", comparison_data)
            
            # Add visualization for comparison
            comparison_viz = self._generate_goal_comparison_chart(goal_objects)
            comparison_section.add_visualization("comparison_chart", comparison_viz)
            
            document["sections"].append(comparison_section.to_dict())
            
            # Trade-off analysis section
            tradeoff_section = DocumentSection("Resource Trade-off Analysis")
            tradeoff_data = self._analyze_goal_tradeoffs(goal_objects)
            tradeoff_section.add_content("tradeoffs", tradeoff_data)
            document["sections"].append(tradeoff_section.to_dict())
            
            # Funding strategy comparison
            funding_section = DocumentSection("Funding Strategy Comparison")
            funding_comparison = self._compare_funding_strategies(goal_objects)
            funding_section.add_content("funding_comparison", funding_comparison)
            document["sections"].append(funding_section.to_dict())
            
            return document
            
        except Exception as e:
            logger.error(f"Error generating goals comparison: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    def generate_html(self, document_data: Dict[str, Any]) -> str:
        """
        Generate HTML for web display with interactive elements.
        
        Args:
            document_data (Dict[str, Any]): Document data structure
            
        Returns:
            str: HTML content
        """
        try:
            # Start with base HTML structure
            html = [
                '<!DOCTYPE html>',
                '<html lang="en">',
                '<head>',
                '    <meta charset="UTF-8">',
                '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
                f'    <title>{document_data.get("title", "Financial Goal Document")}</title>',
                '    <style>',
                '        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }',
                '        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }',
                '        h2 { color: #2980b9; margin-top: 30px; }',
                '        h3 { color: #3498db; }',
                '        .summary-box { background: #f8f9fa; border-left: 4px solid #2980b9; padding: 15px; margin: 20px 0; }',
                '        .recommendation { background: #e8f4f8; padding: 15px; margin: 10px 0; border-radius: 5px; }',
                '        .recommendation h4 { margin-top: 0; color: #2980b9; }',
                '        .progress-container { background: #ecf0f1; height: 25px; border-radius: 5px; margin: 20px 0; }',
                '        .progress-bar { background: #3498db; height: 100%; border-radius: 5px; text-align: center; color: white; line-height: 25px; }',
                '        .progress-bar.high { background: #27ae60; }',
                '        .progress-bar.medium { background: #f39c12; }',
                '        .progress-bar.low { background: #e74c3c; }',
                '        .metric { display: inline-block; text-align: center; background: #f8f9fa; padding: 15px; margin: 10px; border-radius: 5px; min-width: 150px; }',
                '        .metric .value { font-size: 24px; font-weight: bold; color: #2980b9; }',
                '        .metric .label { font-size: 14px; color: #7f8c8d; }',
                '        table { width: 100%; border-collapse: collapse; margin: 20px 0; }',
                '        th { background: #2980b9; color: white; text-align: left; padding: 10px; }',
                '        td { border: 1px solid #ddd; padding: 10px; }',
                '        tr:nth-child(even) { background: #f2f2f2; }',
                '        .timeline { position: relative; margin: 40px 0; padding-top: 20px; }',
                '        .timeline::before { content: ""; position: absolute; top: 0; bottom: 0; left: 50%; width: 4px; background: #3498db; }',
                '        .milestone { position: relative; margin-bottom: 30px; min-height: 70px; clear: both; }',
                '        .milestone-marker { position: absolute; top: 15px; left: 50%; width: 20px; height: 20px; background: #3498db; border-radius: 50%; transform: translateX(-50%); z-index: 1; }',
                '        .milestone-date { position: absolute; left: 0; width: 45%; text-align: right; padding-right: 30px; font-weight: bold; color: #2980b9; }',
                '        .milestone-details { position: absolute; right: 0; width: 45%; padding-left: 30px; background: #f8f9fa; border-radius: 5px; padding: 15px; }',
                '        .monthly-contribution-summary { background: #e1f0fa; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 30px; }',
                '        .contribution-amount { font-size: 32px; font-weight: bold; color: #2980b9; margin: 10px 0; }',
                '        .collapsed { display: none; }',
                '        .toggle-btn { background: #3498db; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; }',
                '        .toggle-btn:hover { background: #2980b9; }',
                '        .action-step { background: #e8f4f8; padding: 12px; margin: 10px 0; border-left: 4px solid #3498db; }',
                '        .education-section { background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }',
                '        .education-section h3 { color: #16a085; }',
                '        .tax-info { background: #ebf5eb; padding: 15px; margin: 15px 0; border-left: 4px solid #27ae60; }',
                '        .note { font-size: 0.9em; font-style: italic; color: #7f8c8d; }',
                '        @media print {',
                '            body { font-size: 12pt; }',
                '            .toggle-btn, .interactive-element { display: none; }',
                '            .collapsed { display: block; }',
                '            .timeline::before { left: 0; }',
                '            .milestone::after { left: 0; }',
                '            .milestone-content { width: 90%; margin-left: 20px !important; }',
                '            a { text-decoration: none; color: black; }',
                '            .page-break { page-break-after: always; }',
                '        }',
                '    </style>',
                '</head>',
                '<body>'
            ]
            
            # Add document header
            html.append(f'<h1>{document_data.get("title", "Financial Goal Document")}</h1>')
            html.append(f'<p>Generated on {datetime.now().strftime("%d %B %Y")}</p>')
            
            # Process each section
            for section in document_data.get("sections", []):
                section_title = section.get("title", "Section")
                html.append(f'<h2>{section_title}</h2>')
                
                # Process content based on section type
                content = section.get("content", {})
                
                # Special handling for Executive Summary section
                if section_title == "Executive Summary" and "summary" in content:
                    summary = content["summary"]
                    html.append('<div class="summary-box">')
                    
                    # Add key metrics at the top
                    html.append('<div style="display: flex; flex-wrap: wrap; justify-content: space-between;">')
                    
                    # Add progress meter
                    progress = summary.get("progress_percentage", 0)
                    progress_class = "high" if progress >= 75 else "medium" if progress >= 40 else "low"
                    html.append('<div class="metric">')
                    html.append(f'<div class="progress-container"><div class="progress-bar {progress_class}" style="width: {progress}%;">{progress:.1f}%</div></div>')
                    html.append('<div class="label">Progress</div>')
                    html.append('</div>')
                    
                    # Add status metric
                    status = summary.get("status", "")
                    html.append('<div class="metric">')
                    html.append(f'<div class="value">{status}</div>')
                    html.append('<div class="label">Status</div>')
                    html.append('</div>')
                    
                    # Add success probability
                    prob = summary.get("success_probability", 0)
                    html.append('<div class="metric">')
                    html.append(f'<div class="value">{prob:.1f}%</div>')
                    html.append('<div class="label">Success Probability</div>')
                    html.append('</div>')
                    
                    # Add amounts
                    html.append('<div class="metric">')
                    html.append(f'<div class="value">{self.format_rupees(summary.get("current_amount", 0))}</div>')
                    html.append('<div class="label">Current Amount</div>')
                    html.append('</div>')
                    
                    html.append('<div class="metric">')
                    html.append(f'<div class="value">{self.format_rupees(summary.get("target_amount", 0))}</div>')
                    html.append('<div class="label">Target Amount</div>')
                    html.append('</div>')
                    
                    # Time remaining
                    html.append('<div class="metric">')
                    html.append(f'<div class="value">{summary.get("time_remaining", "")}</div>')
                    html.append('<div class="label">Time Remaining</div>')
                    html.append('</div>')
                    
                    html.append('</div>') # Close metrics div
                    html.append('</div>') # Close summary box
                
                # Special handling for Recommendations section
                elif section_title == "Personalized Recommendations" and "recommendations" in content:
                    recommendations = content["recommendations"]
                    for rec in recommendations:
                        html.append('<div class="recommendation">')
                        html.append(f'<h4>{rec.get("title", "Recommendation")}</h4>')
                        html.append(f'<p>{rec.get("description", "")}</p>')
                        
                        # Add impact metrics if available
                        impact = rec.get("impact", {})
                        if impact:
                            improvement = impact.get("improvement", 0)
                            html.append('<div style="display: flex; flex-wrap: wrap;">')
                            html.append('<div class="metric">')
                            html.append(f'<div class="value">+{improvement:.1f}%</div>')
                            html.append('<div class="label">Success Probability Increase</div>')
                            html.append('</div>')
                            
                            # Add more impact metrics
                            html.append('<div class="metric">')
                            html.append(f'<div class="value">{impact.get("new_probability", 0):.1f}%</div>')
                            html.append('<div class="label">New Success Probability</div>')
                            html.append('</div>')
                            html.append('</div>') # Close metrics flex container
                        
                        html.append('</div>') # Close recommendation div
                
                # Special handling for Indian Market Context
                elif section_title == "Indian Market Context" and "indian_context" in content:
                    context = content["indian_context"]
                    html.append('<div class="education-section">')
                    html.append(f'<h3>{context.get("context", "Indian Market Context")}</h3>')
                    
                    # Key facts
                    key_facts = context.get("key_facts", [])
                    if key_facts:
                        html.append('<h4>Key Facts</h4>')
                        html.append('<ul>')
                        for fact in key_facts:
                            html.append(f'<li>{fact}</li>')
                        html.append('</ul>')
                    
                    # Tax benefits
                    tax_benefits = context.get("tax_benefits", "")
                    if tax_benefits:
                        html.append('<div class="tax-info">')
                        html.append('<h4>Tax Benefits</h4>')
                        html.append(f'<p>{tax_benefits}</p>')
                        html.append('</div>')
                    
                    # Market trends
                    market_trends = context.get("market_trends", "")
                    if market_trends:
                        html.append('<h4>Market Trends</h4>')
                        html.append(f'<p>{market_trends}</p>')
                    
                    html.append('</div>') # Close education section
                    
                    # Add tax recommendations if available
                    if "tax_recommendations" in content:
                        html.append('<h3>Tax Optimization Strategies</h3>')
                        tax_recs = content["tax_recommendations"]
                        for rec in tax_recs:
                            html.append('<div class="tax-info">')
                            html.append(f'<h4>{rec.get("title", "Tax Strategy")}</h4>')
                            html.append(f'<p>{rec.get("description", "")}</p>')
                            
                            # Add options if available
                            options = rec.get("options", [])
                            if options:
                                html.append('<ul>')
                                for option in options:
                                    html.append(f'<li>{option}</li>')
                                html.append('</ul>')
                            
                            html.append('</div>') # Close tax info div
                            
                    # Add investment vehicle recommendations
                    if "investment_vehicles" in content:
                        html.append('<h3>Recommended Investment Options</h3>')
                        vehicles = content["investment_vehicles"].get("recommended_vehicles", [])
                        
                        if vehicles:
                            html.append('<table>')
                            html.append('<tr><th>Investment Option</th><th>Suitability</th><th>Expected Returns</th><th>Lock-in Period</th><th>Tax Efficiency</th></tr>')
                            
                            for vehicle in vehicles:
                                html.append('<tr>')
                                html.append(f'<td><strong>{vehicle.get("name", "")}</strong><br><small>{vehicle.get("features", "")}</small></td>')
                                html.append(f'<td>{vehicle.get("suitability", "")}</td>')
                                html.append(f'<td>{vehicle.get("expected_returns", "")}</td>')
                                html.append(f'<td>{vehicle.get("lock_in", "")}</td>')
                                html.append(f'<td>{vehicle.get("tax_efficiency", "")}</td>')
                                html.append('</tr>')
                            
                            html.append('</table>')
                
                # Special handling for Monthly Action Plan
                elif section_title == "Monthly Action Plan" and "action_steps" in content:
                    # Display monthly contribution if available
                    if "monthly_contribution" in content:
                        monthly_contribution = content["monthly_contribution"]
                        html.append('<div class="monthly-contribution-summary">')
                        html.append('<h3>Required Monthly Contribution</h3>')
                        html.append(f'<p class="contribution-amount">{monthly_contribution.get("formatted", "")}</p>')
                        html.append('<p>This is the estimated monthly amount needed to reach your goal on time.</p>')
                        html.append('</div>')
                    
                    # Display action steps
                    steps = content["action_steps"]
                    html.append('<h3>Action Steps</h3>')
                    for i, step in enumerate(steps):
                        html.append('<div class="action-step">')
                        html.append(f'<h4>Step {i+1}: {step.get("title", "Action")}</h4>')
                        html.append(f'<p>{step.get("description", "")}</p>')
                        
                        # If there are specific tasks, add them as a list
                        tasks = step.get("tasks", [])
                        if tasks:
                            html.append('<ul>')
                            for task in tasks:
                                html.append(f'<li>{task}</li>')
                            html.append('</ul>')
                            
                        # Add target date if available
                        if "target_date" in step:
                            html.append(f'<p><strong>Target completion:</strong> {step["target_date"]}</p>')
                            
                        html.append('</div>')
                    
                    # Display milestone timeline if available
                    if "milestones" in content:
                        milestones = content["milestones"]
                        html.append('<div class="milestones-section">')
                        html.append('<h3>Goal Milestones</h3>')
                        html.append('<div class="timeline">')
                        
                        for milestone in milestones:
                            html.append('<div class="milestone">')
                            html.append(f'<div class="milestone-date">{milestone.get("date", "")}</div>')
                            html.append(f'<div class="milestone-marker"></div>')
                            html.append('<div class="milestone-details">')
                            html.append(f'<h4>{milestone.get("name", "Milestone")}</h4>')
                            if "formatted_amount" in milestone:
                                html.append(f'<p>Target: {milestone.get("formatted_amount", "")}</p>')
                            html.append('</div>')
                            html.append('</div>')
                        
                        html.append('</div>') # Close timeline
                        html.append('</div>') # Close milestones section
                
                # Special handling for Tax Implications
                elif section_title == "Tax Implications" and "tax_analysis" in content:
                    tax_analysis = content["tax_analysis"]
                    html.append('<div class="tax-info">')
                    
                    # Add tax savings summary
                    if "potential_tax_savings" in tax_analysis:
                        html.append('<h3>Potential Tax Savings</h3>')
                        html.append(f'<p>By optimizing your investments for this goal, you can save up to <strong>{self.format_rupees(tax_analysis["potential_tax_savings"])}</strong> in taxes.</p>')
                    
                    # Add tax regime comparison if available
                    if "regime_comparison" in tax_analysis:
                        comp = tax_analysis["regime_comparison"]
                        html.append('<h3>Tax Regime Comparison</h3>')
                        html.append('<table>')
                        html.append('<tr><th>Parameter</th><th>Old Regime</th><th>New Regime</th></tr>')
                        html.append(f'<tr><td>Taxable Income</td><td>{self.format_rupees(comp.get("old_taxable_income", 0))}</td><td>{self.format_rupees(comp.get("new_taxable_income", 0))}</td></tr>')
                        html.append(f'<tr><td>Tax Amount</td><td>{self.format_rupees(comp.get("old_tax", 0))}</td><td>{self.format_rupees(comp.get("new_tax", 0))}</td></tr>')
                        html.append(f'<tr><td>Effective Tax Rate</td><td>{comp.get("old_effective_rate", 0):.2f}%</td><td>{comp.get("new_effective_rate", 0):.2f}%</td></tr>')
                        html.append('</table>')
                        
                        # Add recommendation
                        better_regime = "old" if comp.get("old_tax", 0) < comp.get("new_tax", 0) else "new"
                        html.append(f'<p><strong>Recommendation:</strong> The <strong>{better_regime} tax regime</strong> appears more beneficial for your situation.</p>')
                    
                    html.append('</div>')
                    
                    # Add specific deduction opportunities
                    if "deduction_opportunities" in content:
                        deductions = content["deduction_opportunities"]
                        html.append('<h3>Available Tax Deduction Opportunities</h3>')
                        
                        html.append('<table>')
                        html.append('<tr><th>Section</th><th>Description</th><th>Maximum Deduction</th><th>Your Potential</th></tr>')
                        
                        for deduction in deductions:
                            html.append('<tr>')
                            html.append(f'<td>{deduction.get("section", "")}</td>')
                            html.append(f'<td>{deduction.get("description", "")}</td>')
                            html.append(f'<td>{self.format_rupees(deduction.get("max_amount", 0))}</td>')
                            html.append(f'<td>{self.format_rupees(deduction.get("your_potential", 0))}</td>')
                            html.append('</tr>')
                        
                        html.append('</table>')
                
                # General tables for any other structured content
                for key, value in content.items():
                    # Skip content that's been handled by special sections
                    if key in ["summary", "recommendations", "indian_context", "tax_recommendations", 
                              "investment_vehicles", "action_steps", "milestones", "monthly_contribution",
                              "tax_analysis", "deduction_opportunities"]:
                        continue
                        
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        # It's a list of objects, render as table
                        html.append(f'<h3>{key.replace("_", " ").title()}</h3>')
                        html.append('<table>')
                        
                        # Get all column names
                        columns = set()
                        for item in value:
                            columns.update(item.keys())
                        columns = sorted(columns)
                        
                        # Table header
                        html.append('<tr>')
                        for col in columns:
                            html.append(f'<th>{col.replace("_", " ").title()}</th>')
                        html.append('</tr>')
                        
                        # Table rows
                        for item in value:
                            html.append('<tr>')
                            for col in columns:
                                cell_value = item.get(col, "")
                                # Format monetary values
                                if isinstance(cell_value, (int, float)) and col.endswith(("amount", "value", "cost", "price")):
                                    cell_value = self.format_rupees(cell_value)
                                html.append(f'<td>{cell_value}</td>')
                            html.append('</tr>')
                        
                        html.append('</table>')
                    elif isinstance(value, dict):
                        # It's a single object, render as key-value pairs
                        html.append(f'<h3>{key.replace("_", " ").title()}</h3>')
                        html.append('<table>')
                        
                        for k, v in value.items():
                            # Format monetary values
                            if isinstance(v, (int, float)) and k.endswith(("amount", "value", "cost", "price")):
                                v = self.format_rupees(v)
                            html.append(f'<tr><th>{k.replace("_", " ").title()}</th><td>{v}</td></tr>')
                        
                        html.append('</table>')
                    elif isinstance(value, list):
                        # It's a simple list, render as a bullet list
                        html.append(f'<h3>{key.replace("_", " ").title()}</h3>')
                        html.append('<ul>')
                        
                        for item in value:
                            html.append(f'<li>{item}</li>')
                        
                        html.append('</ul>')
                    else:
                        # It's a simple value
                        html.append(f'<h3>{key.replace("_", " ").title()}</h3>')
                        html.append(f'<p>{value}</p>')
                
                # Process visualizations
                for viz in section.get("visualizations", []):
                    viz_type = viz.get("type", "")
                    viz_data = viz.get("data", {})
                    
                    # If there's image data, use it directly
                    if "image_data" in viz_data:
                        html.append(f'<div><img src="{viz_data["image_data"]}" alt="{viz_type}" style="max-width:100%;"></div>')
                    
                    # Add special interactive elements based on visualization type
                    if viz_type == "timeline":
                        milestones = viz_data.get("milestones", [])
                        if milestones:
                            html.append('<div class="timeline">')
                            
                            for milestone in milestones:
                                html.append('<div class="milestone">')
                                html.append('<div class="milestone-content">')
                                html.append(f'<div class="milestone-date">{milestone.get("name", "Milestone")}</div>')
                                if "date" in milestone:
                                    try:
                                        milestone_date = datetime.fromisoformat(milestone["date"].replace('Z', '+00:00'))
                                        html.append(f'<div>{milestone_date.strftime("%d %b %Y")}</div>')
                                    except (ValueError, AttributeError):
                                        html.append(f'<div>{milestone["date"]}</div>')
                                
                                if "expected_amount" in milestone:
                                    html.append(f'<div>Expected: {self.format_rupees(milestone["expected_amount"])}</div>')
                                
                                html.append('</div>') # Close milestone-content
                                html.append('</div>') # Close milestone
                            
                            html.append('</div>') # Close timeline
                    
                    elif viz_type == "asset_allocation" and not "image_data" in viz_data:
                        # Simplified HTML representation for asset allocation when image isn't available
                        html.append('<div style="margin: 20px 0;">')
                        html.append('<h4>Recommended Asset Allocation</h4>')
                        html.append('<div style="display: flex; flex-wrap: wrap;">')
                        
                        # Color mapping
                        colors = {
                            'equity': '#3498db',
                            'debt': '#2ecc71',
                            'liquid': '#f1c40f',
                            'gold': '#f39c12',
                            'real_estate': '#e74c3c',
                            'alternative': '#9b59b6'
                        }
                        
                        # Filter out image_data and metadata
                        allocation = {k: v for k, v in viz_data.items() 
                                     if isinstance(v, (int, float)) and k not in ["image_data"]}
                        
                        for asset, percentage in allocation.items():
                            color = colors.get(asset.lower(), '#95a5a6')
                            html.append(f'<div style="margin:10px; text-align:center; min-width:120px;">')
                            html.append(f'<div style="height:30px; background:{color}; border-radius:3px; padding:5px; color:white; font-weight:bold;">{percentage:.1f}%</div>')
                            html.append(f'<div style="margin-top:5px;">{asset.title()}</div>')
                            html.append('</div>')
                        
                        html.append('</div>') # Close flex container
                        html.append('</div>') # Close overall div
                
                # Add section divider
                html.append('<hr class="page-break">')
            
            # Add footer with disclaimer and closing tags
            html.append('<div class="note">')
            html.append('<p>DISCLAIMER: This document is for educational purposes only and does not constitute financial advice. ')
            html.append('Please consult with a certified financial advisor before making investment decisions.</p>')
            html.append('</div>')
            
            # Add simple JavaScript for interactive elements (collapsible sections, etc.)
            html.append('<script>')
            html.append('document.addEventListener("DOMContentLoaded", function() {')
            html.append('    var toggleButtons = document.querySelectorAll(".toggle-btn");')
            html.append('    for (var i = 0; i < toggleButtons.length; i++) {')
            html.append('        toggleButtons[i].addEventListener("click", function() {')
            html.append('            var targetId = this.getAttribute("data-target");')
            html.append('            var targetElement = document.getElementById(targetId);')
            html.append('            if (targetElement.classList.contains("collapsed")) {')
            html.append('                targetElement.classList.remove("collapsed");')
            html.append('                this.textContent = "Hide Details";')
            html.append('            } else {')
            html.append('                targetElement.classList.add("collapsed");')
            html.append('                this.textContent = "Show Details";')
            html.append('            }')
            html.append('        });')
            html.append('    }')
            html.append('});')
            html.append('</script>')
            
            html.append('</body>')
            html.append('</html>')
            
            # Join all lines
            return '\n'.join(html)
            
        except Exception as e:
            logger.error(f"Error generating HTML: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Return simple error HTML
            return f"""
            <!DOCTYPE html>
            <html>
            <body>
                <h1>Error Generating Document</h1>
                <p>An error occurred while generating the document: {str(e)}</p>
            </body>
            </html>
            """
    
    def generate_json(self, document_data: Dict[str, Any], simplified: bool = False) -> Dict[str, Any]:
        """
        Generate structured JSON for API responses.
        
        Args:
            document_data (Dict[str, Any]): Document data structure
            simplified (bool): Whether to return a simplified version without images
            
        Returns:
            Dict[str, Any]: JSON structure
        """
        try:
            if simplified:
                # Create a simplified copy without image data and large nested structures
                simplified_data = {
                    "id": document_data.get("id", ""),
                    "type": document_data.get("type", ""),
                    "title": document_data.get("title", ""),
                    "created_at": document_data.get("created_at", datetime.now().isoformat()),
                    "sections": []
                }
                
                for section in document_data.get("sections", []):
                    # Include content but remove large image data
                    section_copy = {
                        "title": section.get("title", ""),
                        "content": section.get("content", {}),
                        "visualizations": []
                    }
                    
                    # Include metadata about visualizations but not the actual images
                    for viz in section.get("visualizations", []):
                        viz_copy = {
                            "type": viz.get("type", ""),
                            "data": {k: v for k, v in viz.get("data", {}).items() 
                                   if k != "image_data"}
                        }
                        section_copy["visualizations"].append(viz_copy)
                    
                    simplified_data["sections"].append(section_copy)
                
                return simplified_data
            else:
                # Return full data structure
                return document_data
                
        except Exception as e:
            logger.error(f"Error generating JSON: {str(e)}")
            return {"error": str(e)}
    
    def generate_pdf(self, document_data: Dict[str, Any]) -> Optional[str]:
        """
        Export document as PDF.
        
        Args:
            document_data (Dict[str, Any]): Document data structure
            
        Returns:
            Optional[str]: Path to generated PDF or None if failed
        """
        if not self.pdf_enabled:
            logger.warning("PDF generation is disabled due to missing dependencies")
            return None
        
        try:
            # Generate unique filename
            doc_id = document_data.get("id", str(uuid.uuid4()))
            doc_type = document_data.get("type", "financial_document")
            filename = f"{doc_type}_{doc_id}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4,
                                   leftMargin=36, rightMargin=36,
                                   topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()
            
            # Customize styles for Indian context
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontName='Helvetica-Bold',
                fontSize=20,
                leading=24,
                alignment=1,  # Center
                textColor=colors.HexColor(0x2980b9)
            )
            
            heading1_style = ParagraphStyle(
                'CustomHeading1',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=16,
                leading=20,
                spaceAfter=12,
                textColor=colors.HexColor(0x2980b9)
            )
            
            heading2_style = ParagraphStyle(
                'CustomHeading2',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=14,
                leading=18,
                spaceBefore=12,
                spaceAfter=6,
                textColor=colors.HexColor(0x3498db)
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                leading=14,
                spaceBefore=6
            )
            
            note_style = ParagraphStyle(
                'Note',
                parent=normal_style,
                fontSize=9,
                leading=12,
                fontName='Helvetica-Oblique',
                textColor=colors.gray
            )
            
            elements = []
            
            # Add title
            elements.append(Paragraph(document_data.get("title", "Financial Document"), title_style))
            elements.append(Spacer(1, 12))
            
            # Add date and generated info
            date_string = datetime.now().strftime("%d %B %Y")
            elements.append(Paragraph(f"Generated on: {date_string}", normal_style))
            elements.append(Spacer(1, 24))
            
            # Process each section
            for section in document_data.get("sections", []):
                # Section title
                section_title = section.get("title", "Section")
                elements.append(Paragraph(section_title, heading1_style))
                elements.append(Spacer(1, 6))
                
                # Process based on section type
                content = section.get("content", {})
                
                # Special handling for Executive Summary
                if section_title == "Executive Summary" and "summary" in content:
                    summary = content["summary"]
                    
                    # Create a summary table
                    summary_data = [
                        ["Goal Name", summary.get("goal_name", "")],
                        ["Category", summary.get("category", "")],
                        ["Status", summary.get("status", "")],
                        ["Target Amount", self.format_rupees(summary.get("target_amount", 0))],
                        ["Current Amount", self.format_rupees(summary.get("current_amount", 0))],
                        ["Progress", f"{summary.get('progress_percentage', 0):.1f}%"],
                        ["Target Date", summary.get("target_date", "")],
                        ["Time Remaining", summary.get("time_remaining", "")],
                        ["Monthly Required", self.format_rupees(summary.get("monthly_savings_required", 0))],
                        ["Success Probability", f"{summary.get('success_probability', 0):.1f}%"]
                    ]
                    
                    # Create the table
                    summary_table = Table(summary_data, colWidths=[150, 300])
                    summary_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(0xf4f6f7)),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(0x2c3e50)),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (0, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(0xd5dbdb))
                    ]))
                    
                    elements.append(summary_table)
                    elements.append(Spacer(1, 12))
                
                # Special handling for recommendations section
                elif section_title == "Personalized Recommendations" and "recommendations" in content:
                    recommendations = content["recommendations"]
                    
                    elements.append(Paragraph("Based on our analysis, here are personalized recommendations to improve your goal success:", normal_style))
                    elements.append(Spacer(1, 12))
                    
                    for i, rec in enumerate(recommendations):
                        # Create boxed recommendation
                        elements.append(Paragraph(f"<strong>Recommendation {i+1}: {rec.get('title', '')}</strong>", heading2_style))
                        elements.append(Paragraph(rec.get("description", ""), normal_style))
                        
                        # Add impact data if available
                        impact = rec.get("impact", {})
                        if impact:
                            impact_data = [
                                ["Current Success Probability", f"{impact.get('old_probability', 0):.1f}%"],
                                ["New Success Probability", f"{impact.get('new_probability', 0):.1f}%"],
                                ["Improvement", f"+{impact.get('improvement', 0):.1f}%"]
                            ]
                            
                            impact_table = Table(impact_data, colWidths=[200, 150])
                            impact_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(0xebf5fb)),
                                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, -1), 9),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                ('TOPPADDING', (0, 0), (-1, -1), 6),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(0xd5dbdb))
                            ]))
                            
                            elements.append(Spacer(1, 6))
                            elements.append(impact_table)
                        
                        elements.append(Spacer(1, 12))
                
                # For monthly action plan
                elif section_title == "Monthly Action Plan" and "action_steps" in content:
                    steps = content["action_steps"]
                    
                    for i, step in enumerate(steps):
                        elements.append(Paragraph(f"<strong>Step {i+1}: {step.get('title', 'Action')}</strong>", heading2_style))
                        elements.append(Paragraph(step.get("description", ""), normal_style))
                        
                        # If there are specific tasks, add them as a list
                        tasks = step.get("tasks", [])
                        if tasks:
                            for task in tasks:
                                elements.append(Paragraph(f"• {task}", normal_style))
                        
                        # Add target date if available
                        if "target_date" in step:
                            elements.append(Paragraph(f"<strong>Target completion:</strong> {step['target_date']}", normal_style))
                            
                        elements.append(Spacer(1, 12))
                
                # For educational content
                elif section_title == "Indian Market Context" and "indian_context" in content:
                    context = content["indian_context"]
                    
                    # Add educational context
                    elements.append(Paragraph(f"<strong>{context.get('context', 'Indian Market Context')}</strong>", heading2_style))
                    
                    # Key facts
                    key_facts = context.get("key_facts", [])
                    if key_facts:
                        elements.append(Paragraph("<strong>Key Facts</strong>", heading2_style))
                        for fact in key_facts:
                            elements.append(Paragraph(f"• {fact}", normal_style))
                        elements.append(Spacer(1, 6))
                    
                    # Tax benefits
                    tax_benefits = context.get("tax_benefits", "")
                    if tax_benefits:
                        elements.append(Paragraph("<strong>Tax Benefits</strong>", heading2_style))
                        elements.append(Paragraph(tax_benefits, normal_style))
                        elements.append(Spacer(1, 6))
                    
                    # Market trends
                    market_trends = context.get("market_trends", "")
                    if market_trends:
                        elements.append(Paragraph("<strong>Market Trends</strong>", heading2_style))
                        elements.append(Paragraph(market_trends, normal_style))
                        elements.append(Spacer(1, 6))
                    
                    # Investment vehicles if available
                    if "investment_vehicles" in content:
                        elements.append(Paragraph("<strong>Recommended Investment Options</strong>", heading2_style))
                        vehicles = content["investment_vehicles"].get("recommended_vehicles", [])
                        
                        if vehicles:
                            # Create investment table
                            table_data = [["Investment Option", "Suitability", "Expected Returns", "Lock-in"]]
                            
                            for vehicle in vehicles:
                                table_data.append([
                                    vehicle.get("name", ""),
                                    vehicle.get("suitability", ""),
                                    vehicle.get("expected_returns", ""),
                                    vehicle.get("lock_in", "")
                                ])
                            
                            # Create the table with proper styling
                            investment_table = Table(table_data, colWidths=[150, 70, 100, 150])
                            investment_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(0x3498db)),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 10),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(0xd5dbdb)),
                                ('FONTSIZE', (0, 1), (-1, -1), 9),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                            ]))
                            
                            elements.append(investment_table)
                            elements.append(Spacer(1, 12))
                
                # For tax implications
                elif section_title == "Tax Implications" and "tax_analysis" in content:
                    tax_analysis = content["tax_analysis"]
                    
                    # Add tax savings summary
                    if "potential_tax_savings" in tax_analysis:
                        elements.append(Paragraph("<strong>Potential Tax Savings</strong>", heading2_style))
                        elements.append(Paragraph(f"By optimizing your investments for this goal, you can save up to <strong>{self.format_rupees(tax_analysis['potential_tax_savings'])}</strong> in taxes.", normal_style))
                        elements.append(Spacer(1, 6))
                    
                    # Add tax regime comparison if available
                    if "regime_comparison" in tax_analysis:
                        comp = tax_analysis["regime_comparison"]
                        elements.append(Paragraph("<strong>Tax Regime Comparison</strong>", heading2_style))
                        
                        # Create comparison table
                        comp_data = [
                            ["Parameter", "Old Regime", "New Regime"],
                            ["Taxable Income", self.format_rupees(comp.get("old_taxable_income", 0)), self.format_rupees(comp.get("new_taxable_income", 0))],
                            ["Tax Amount", self.format_rupees(comp.get("old_tax", 0)), self.format_rupees(comp.get("new_tax", 0))],
                            ["Effective Tax Rate", f"{comp.get('old_effective_rate', 0):.2f}%", f"{comp.get('new_effective_rate', 0):.2f}%"]
                        ]
                        
                        comp_table = Table(comp_data, colWidths=[150, 150, 150])
                        comp_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(0x27ae60)),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor(0xebf5eb)),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(0xd5dbdb)),
                            ('ALIGN', (1, 1), (-1, -1), 'RIGHT')
                        ]))
                        
                        elements.append(comp_table)
                        elements.append(Spacer(1, 6))
                        
                        # Add recommendation
                        better_regime = "old" if comp.get("old_tax", 0) < comp.get("new_tax", 0) else "new"
                        elements.append(Paragraph(f"<strong>Recommendation:</strong> The <strong>{better_regime} tax regime</strong> appears more beneficial for your situation.", normal_style))
                
                # Add visualizations
                for viz in section.get("visualizations", []):
                    # If there's image data, add it to the PDF
                    if "image_data" in viz.get("data", {}):
                        img_data = viz["data"]["image_data"]
                        
                        # Check if it's a base64 encoded image
                        if isinstance(img_data, str) and img_data.startswith("data:image"):
                            # Extract the base64 part and convert to bytes
                            img_data = img_data.split(",")[1]
                            img_data = base64.b64decode(img_data)
                            
                            # Create image from bytes
                            img_io = io.BytesIO(img_data)
                            img = Image(img_io, width=450, height=300)
                            
                            # Add the image
                            elements.append(Spacer(1, 12))
                            elements.append(img)
                            elements.append(Spacer(1, 6))
                
                # Add page break after each section
                elements.append(PageBreak())
            
            # Add disclaimer at the end
            elements.append(Paragraph("DISCLAIMER", heading2_style))
            elements.append(Paragraph(
                "This document is for educational purposes only and does not constitute financial advice. "
                "Please consult with a certified financial advisor before making investment decisions. "
                "Information provided is based on current tax laws and market conditions, which may change over time.",
                note_style
            ))
            
            # Build the PDF
            doc.build(elements)
            logger.info(f"PDF document generated: {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_printer_friendly_version(self, document_data: Dict[str, Any]) -> str:
        """
        Generate printer-friendly version with optimized layout.
        
        Args:
            document_data (Dict[str, Any]): Document data structure
            
        Returns:
            str: HTML content optimized for printing
        """
        try:
            # Generate HTML with print-specific CSS
            html = [
                '<!DOCTYPE html>',
                '<html lang="en">',
                '<head>',
                '    <meta charset="UTF-8">',
                '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
                f'    <title>{document_data.get("title", "Financial Goal Document")} (Print Version)</title>',
                '    <style>',
                '        @page { size: A4; margin: 2cm; }',
                '        body { font-family: Arial, sans-serif; line-height: 1.4; color: black; font-size: 11pt; }',
                '        h1 { font-size: 18pt; margin-top: 0; page-break-after: avoid; }',
                '        h2 { font-size: 14pt; page-break-after: avoid; border-bottom: 1pt solid black; }',
                '        h3 { font-size: 12pt; page-break-after: avoid; }',
                '        p, li { font-size: 11pt; }',
                '        table { width: 100%; border-collapse: collapse; margin: 10pt 0; page-break-inside: avoid; }',
                '        th { background: #eee; font-weight: bold; text-align: left; padding: 6pt; border: 1pt solid #ddd; }',
                '        td { padding: 6pt; border: 1pt solid #ddd; }',
                '        .box { border: 1pt solid #ddd; padding: 8pt; margin: 10pt 0; page-break-inside: avoid; }',
                '        .progress { height: 15pt; background: #eee; position: relative; margin: 10pt 0; }',
                '        .progress-value { position: absolute; height: 100%; background: #aaa; }',
                '        .progress-text { position: absolute; width: 100%; text-align: center; color: black; font-weight: bold; }',
                '        .recommendation { border-left: 4pt solid #ddd; padding-left: 8pt; margin: 10pt 0; page-break-inside: avoid; }',
                '        .metrics { display: flex; flex-wrap: wrap; justify-content: space-between; }',
                '        .metric { text-align: center; width: 30%; margin-bottom: 10pt; }',
                '        .metric-value { font-weight: bold; font-size: 14pt; }',
                '        .note { font-size: 9pt; font-style: italic; }',
                '        img { max-width: 100%; }',
                '        .section-break { page-break-after: always; }',
                '        a { text-decoration: none; color: black; }',
                '    </style>',
                '</head>',
                '<body>'
            ]
            
            # Add document header
            html.append(f'<h1>{document_data.get("title", "Financial Goal Document")}</h1>')
            html.append(f'<p>Generated on {datetime.now().strftime("%d %B %Y")}</p>')
            
            # Process each section
            for i, section in enumerate(document_data.get("sections", [])):
                section_title = section.get("title", "Section")
                html.append(f'<h2>{section_title}</h2>')
                
                # Process content
                content = section.get("content", {})
                
                # Special handling for Executive Summary with simplified layout
                if section_title == "Executive Summary" and "summary" in content:
                    summary = content["summary"]
                    html.append('<div class="box">')
                    
                    # Create a 2-column table for key metrics
                    html.append('<table>')
                    html.append('<tr><th>Goal Name</th><td>{}</td></tr>'.format(summary.get("goal_name", "")))
                    html.append('<tr><th>Category</th><td>{}</td></tr>'.format(summary.get("category", "")))
                    html.append('<tr><th>Target Amount</th><td>{}</td></tr>'.format(self.format_rupees(summary.get("target_amount", 0))))
                    html.append('<tr><th>Current Amount</th><td>{}</td></tr>'.format(self.format_rupees(summary.get("current_amount", 0))))
                    html.append('<tr><th>Progress</th><td>{:.1f}%</td></tr>'.format(summary.get("progress_percentage", 0)))
                    html.append('<tr><th>Target Date</th><td>{}</td></tr>'.format(summary.get("target_date", "")))
                    html.append('<tr><th>Monthly Required</th><td>{}</td></tr>'.format(self.format_rupees(summary.get("monthly_savings_required", 0))))
                    html.append('<tr><th>Success Probability</th><td>{:.1f}%</td></tr>'.format(summary.get("success_probability", 0)))
                    html.append('<tr><th>Status</th><td><strong>{}</strong></td></tr>'.format(summary.get("status", "")))
                    html.append('</table>')
                    
                    # Simple progress bar
                    progress = summary.get("progress_percentage", 0)
                    html.append('<div class="progress">')
                    html.append(f'<div class="progress-value" style="width: {progress}%;"></div>')
                    html.append(f'<div class="progress-text">{progress:.1f}%</div>')
                    html.append('</div>')
                    
                    html.append('</div>') # Close box
                
                # Special handling for Recommendations section with simplified layout
                elif section_title == "Personalized Recommendations" and "recommendations" in content:
                    recommendations = content["recommendations"]
                    for rec in recommendations:
                        html.append('<div class="recommendation">')
                        html.append(f'<h3>{rec.get("title", "Recommendation")}</h3>')
                        html.append(f'<p>{rec.get("description", "")}</p>')
                        
                        # Add impact metrics if available
                        impact = rec.get("impact", {})
                        if impact:
                            html.append('<p><strong>Impact:</strong> ')
                            html.append('Success probability would increase from ')
                            html.append(f'{impact.get("old_probability", 0):.1f}% to {impact.get("new_probability", 0):.1f}% ')
                            html.append(f'(+{impact.get("improvement", 0):.1f}% improvement)')
                            html.append('</p>')
                        
                        html.append('</div>') # Close recommendation div
                
                # Just output all other content in a simple format
                for key, value in content.items():
                    # Skip content that has been handled by special sections
                    if key in ["summary", "recommendations"]:
                        continue
                        
                    # Output any tables or lists in a printer-friendly format
                    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                        # Output as table
                        html.append(f'<h3>{key.replace("_", " ").title()}</h3>')
                        html.append('<table>')
                        
                        # Get all columns
                        columns = set()
                        for item in value:
                            columns.update(item.keys())
                        columns = sorted(columns)
                        
                        # Table header
                        html.append('<tr>')
                        for col in columns:
                            html.append(f'<th>{col.replace("_", " ").title()}</th>')
                        html.append('</tr>')
                        
                        # Table rows
                        for item in value:
                            html.append('<tr>')
                            for col in columns:
                                cell_value = item.get(col, "")
                                # Format monetary values
                                if isinstance(cell_value, (int, float)) and col.endswith(("amount", "value", "cost", "price")):
                                    cell_value = self.format_rupees(cell_value)
                                html.append(f'<td>{cell_value}</td>')
                            html.append('</tr>')
                        
                        html.append('</table>')
                    elif isinstance(value, list):
                        # Output as list
                        html.append(f'<h3>{key.replace("_", " ").title()}</h3>')
                        html.append('<ul>')
                        for item in value:
                            if isinstance(item, dict):
                                # Handle dictionaries in the list
                                html.append('<li><dl>')
                                for k, v in item.items():
                                    html.append(f'<dt><strong>{k.replace("_", " ").title()}:</strong></dt>')
                                    html.append(f'<dd>{v}</dd>')
                                html.append('</dl></li>')
                            else:
                                html.append(f'<li>{item}</li>')
                        html.append('</ul>')
                    elif isinstance(value, dict):
                        # Output as description list
                        html.append(f'<h3>{key.replace("_", " ").title()}</h3>')
                        html.append('<dl>')
                        for k, v in value.items():
                            if isinstance(v, (list, dict)):
                                # Skip complex nested structures in print version
                                continue
                            html.append(f'<dt><strong>{k.replace("_", " ").title()}:</strong></dt>')
                            
                            # Format monetary values
                            if isinstance(v, (int, float)) and k.endswith(("amount", "value", "cost", "price")):
                                v = self.format_rupees(v)
                            
                            html.append(f'<dd>{v}</dd>')
                        html.append('</dl>')
                    else:
                        # Output as simple paragraph
                        html.append(f'<h3>{key.replace("_", " ").title()}</h3>')
                        html.append(f'<p>{value}</p>')
                
                # Add visualizations as static images if available
                for viz in section.get("visualizations", []):
                    if "image_data" in viz.get("data", {}):
                        html.append(f'<div><img src="{viz["data"]["image_data"]}" alt="{viz.get("type", "Visualization")}" /></div>')
                
                # Add section break (page break) after each section except the last one
                if i < len(document_data.get("sections", [])) - 1:
                    html.append('<div class="section-break"></div>')
            
            # Add footer with disclaimer
            html.append('<div class="note">')
            html.append('<p>DISCLAIMER: This document is for educational purposes only and does not constitute financial advice. ')
            html.append('Please consult with a certified financial advisor before making investment decisions.</p>')
            html.append('<p>Document generated by GoalDocumentGenerator v1.0</p>')
            html.append('</div>')
            
            html.append('</body>')
            html.append('</html>')
            
            return '\n'.join(html)
            
        except Exception as e:
            logger.error(f"Error generating printer-friendly version: {str(e)}")
            return f"""
            <!DOCTYPE html>
            <html>
            <body>
                <h1>Error Generating Print Version</h1>
                <p>An error occurred: {str(e)}</p>
            </body>
            </html>
            """
    
    # Helper methods for document sections
    
    def _generate_executive_summary(self, goal: Goal, profile: Dict[str, Any]) -> DocumentSection:
        """Generate executive summary section with key metrics and goal status."""
        section = DocumentSection("Executive Summary")
        
        # Basic goal information
        summary = {
            "goal_name": goal.title,
            "category": goal.category,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "progress_percentage": goal.current_progress,
            "target_date": goal.timeframe,
            "importance": goal.importance,
            "flexibility": goal.flexibility
        }
        
        # Calculate time remaining
        time_remaining = ""
        try:
            target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
            today = datetime.now()
            days_remaining = (target_date - today).days
            
            if days_remaining < 0:
                time_remaining = "Goal date has passed"
            elif days_remaining < 30:
                time_remaining = f"{days_remaining} days remaining"
            elif days_remaining < 365:
                months = days_remaining // 30
                time_remaining = f"Approximately {months} months remaining"
            else:
                years = days_remaining // 365
                months = (days_remaining % 365) // 30
                time_remaining = f"Approximately {years} years and {months} months remaining"
        except (ValueError, AttributeError):
            time_remaining = "Date format not recognized"
        
        summary["time_remaining"] = time_remaining
        
        # Add funding gap analysis
        calculator = GoalCalculator.get_calculator_for_goal(goal)
        monthly_required = calculator.calculate_required_saving_rate(goal, profile)
        summary["monthly_savings_required"] = monthly_required
        
        # Success probability
        if goal.goal_success_probability > 0:
            summary["success_probability"] = goal.goal_success_probability
        else:
            # Calculate probability if not already set
            success_prob = calculator.calculate_goal_success_probability(goal, profile)
            summary["success_probability"] = success_prob
        
        # Determine status
        if summary["progress_percentage"] >= 100:
            status = "Achieved"
        elif summary["success_probability"] >= 80:
            status = "On Track"
        elif summary["success_probability"] >= 50:
            status = "Attention Needed"
        else:
            status = "At Risk"
        
        summary["status"] = status
        
        section.add_content("summary", summary)
        
        # Create executive dashboard visualization
        dashboard_data = {
            "progress": summary["progress_percentage"],
            "success_probability": summary["success_probability"],
            "monthly_required": monthly_required,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "status": status
        }
        section.add_visualization("executive_dashboard", dashboard_data)
        
        return section
    
    def _generate_progress_visualization(self, goal: Goal, profile: Dict[str, Any]) -> DocumentSection:
        """Generate current progress visualization with timeline."""
        section = DocumentSection("Goal Progress")
        
        # Basic progress metrics
        progress_data = {
            "current_amount": goal.current_amount,
            "target_amount": goal.target_amount,
            "percentage_complete": goal.current_progress,
            "target_date": goal.timeframe
        }
        
        # Calculate milestone markers
        milestones = []
        try:
            target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
            today = datetime.now()
            total_days = (target_date - datetime.fromisoformat(goal.created_at)).days
            elapsed_days = (today - datetime.fromisoformat(goal.created_at)).days
            
            if total_days > 0:
                progress_expected = (elapsed_days / total_days) * 100
                progress_data["expected_progress"] = min(100, progress_expected)
                
                # Create milestone markers
                quarter_milestone = total_days * 0.25
                half_milestone = total_days * 0.5
                three_quarters_milestone = total_days * 0.75
                
                milestone_date = datetime.fromisoformat(goal.created_at) + timedelta(days=int(quarter_milestone))
                milestones.append({
                    "name": "25% Time Elapsed",
                    "date": milestone_date.isoformat(),
                    "expected_amount": goal.target_amount * 0.25
                })
                
                milestone_date = datetime.fromisoformat(goal.created_at) + timedelta(days=int(half_milestone))
                milestones.append({
                    "name": "50% Time Elapsed",
                    "date": milestone_date.isoformat(),
                    "expected_amount": goal.target_amount * 0.5
                })
                
                milestone_date = datetime.fromisoformat(goal.created_at) + timedelta(days=int(three_quarters_milestone))
                milestones.append({
                    "name": "75% Time Elapsed",
                    "date": milestone_date.isoformat(),
                    "expected_amount": goal.target_amount * 0.75
                })
        except (ValueError, AttributeError):
            progress_data["expected_progress"] = 0
        
        progress_data["milestones"] = milestones
        section.add_content("progress_metrics", progress_data)
        
        # Progress chart data
        chart_data = {
            "current": goal.current_amount,
            "target": goal.target_amount,
            "percentage": goal.current_progress,
            "milestones": milestones,
            "start_date": goal.created_at,
            "end_date": goal.timeframe
        }
        section.add_visualization("progress_chart", chart_data)
        
        # Generate projection chart if visualization is enabled
        if self.visualization_enabled:
            # Project future progress based on current rate
            try:
                calculator = GoalCalculator.get_calculator_for_goal(goal)
                projection = calculator.simulate_goal_progress(goal, profile, years=5)
                projection_data = {
                    "dates": [p["date"] for p in projection],
                    "amounts": [p["amount"] for p in projection],
                    "current_trend_line": self._calculate_trend_line(projection)
                }
                section.add_visualization("progress_projection", projection_data)
            except Exception as e:
                logger.warning(f"Could not generate projection chart: {str(e)}")
        
        return section
    
    def _generate_probability_analysis(self, goal: Goal, profile: Dict[str, Any]) -> DocumentSection:
        """Generate probabilistic success analysis with fan chart."""
        section = DocumentSection("Success Probability Analysis")
        
        # Basic probability metrics
        probability_data = {}
        
        # Get goal calculator
        calculator = GoalCalculator.get_calculator_for_goal(goal)
        
        # Get or calculate success probability
        if goal.goal_success_probability > 0:
            base_probability = goal.goal_success_probability
        else:
            base_probability = calculator.calculate_goal_success_probability(goal, profile)
        
        probability_data["base_success_probability"] = base_probability
        
        # Run Monte Carlo simulation if possible
        monte_carlo_results = None
        try:
            # Attempt to generate detailed probability distribution
            from models.goal_probability import GoalProbabilityAnalyzer
            analyzer = GoalProbabilityAnalyzer(calculator)
            monte_carlo_results = analyzer.run_monte_carlo_simulation(goal, profile, num_simulations=1000)
            
            probability_data["monte_carlo"] = {
                "median_outcome": monte_carlo_results.distribution_data.get("median", 0),
                "percentile_10": monte_carlo_results.distribution_data.get("percentile_10", 0),
                "percentile_90": monte_carlo_results.distribution_data.get("percentile_90", 0),
                "upside_potential": monte_carlo_results.risk_metrics.get("upside_potential", 0),
                "downside_risk": monte_carlo_results.risk_metrics.get("downside_risk", 0)
            }
        except Exception as e:
            logger.warning(f"Could not run Monte Carlo simulation: {str(e)}")
            
        # Calculate sensitivity analysis
        sensitivity = self._calculate_sensitivity_analysis(goal, profile, calculator)
        probability_data["sensitivity_analysis"] = sensitivity
        
        section.add_content("probability_data", probability_data)
        
        # Fan chart visualization
        if monte_carlo_results and self.visualization_enabled:
            # Create fan chart data
            fan_chart_data = {
                "percentiles": monte_carlo_results.distribution_data.get("percentiles", {}),
                "time_series": monte_carlo_results.time_based_metrics.get("time_series", []),
                "median_path": monte_carlo_results.time_based_metrics.get("median_path", []),
                "goal_target": goal.target_amount
            }
            section.add_visualization("fan_chart", fan_chart_data)
        else:
            # Simplified probability visualization
            simplified_data = {
                "success_probability": base_probability,
                "target_amount": goal.target_amount,
                "sensitivity": sensitivity
            }
            section.add_visualization("probability_gauge", simplified_data)
        
        return section
    
    def _generate_recommendations(self, goal: Goal, profile: Dict[str, Any]) -> DocumentSection:
        """Generate personalized recommendations with impact metrics."""
        section = DocumentSection("Personalized Recommendations")
        
        # Basic recommendations setup
        recommendations = []
        
        # Get calculator for further analysis
        calculator = GoalCalculator.get_calculator_for_goal(goal)
        
        # Recommendation 1: Savings rate adjustment
        current_probability = goal.goal_success_probability
        if current_probability < 90:
            # Calculate how much more monthly savings would be needed for 90% probability
            current_monthly = calculator.calculate_required_saving_rate(goal, profile)
            
            # Try different increments to find what would push to 90%
            for increase_factor in [1.1, 1.25, 1.5, 2.0]:
                adjusted_monthly = current_monthly * increase_factor
                temp_goal = Goal.from_dict(goal.to_dict())  # Clone goal
                
                # Update probability with increased savings
                profile_with_adjustment = profile.copy()
                if "monthly_savings" in profile_with_adjustment:
                    profile_with_adjustment["monthly_savings"] = adjusted_monthly
                
                new_probability = calculator.calculate_goal_success_probability(temp_goal, profile_with_adjustment)
                
                if new_probability >= 90:
                    recommendations.append({
                        "type": "savings_rate_adjustment",
                        "title": "Increase Monthly Savings",
                        "description": f"Increasing your monthly savings from ₹{current_monthly:,.2f} to ₹{adjusted_monthly:,.2f} would boost your success probability to {new_probability:.1f}%.",
                        "current_value": current_monthly,
                        "recommended_value": adjusted_monthly,
                        "impact": {
                            "old_probability": current_probability,
                            "new_probability": new_probability,
                            "improvement": new_probability - current_probability
                        }
                    })
                    break
        
        # Recommendation 2: Asset allocation adjustment
        current_allocation = None
        if hasattr(calculator, "get_current_allocation"):
            current_allocation = calculator.get_current_allocation(goal, profile)
        
        recommended_allocation = None
        if hasattr(calculator, "get_recommended_allocation"):
            recommended_allocation = calculator.get_recommended_allocation(goal, profile)
        
        if current_allocation and recommended_allocation and current_allocation != recommended_allocation:
            # Calculate impact of allocation change
            temp_goal = Goal.from_dict(goal.to_dict())  # Clone goal
            profile_with_allocation = profile.copy()
            profile_with_allocation["allocation"] = recommended_allocation
            
            new_probability = calculator.calculate_goal_success_probability(temp_goal, profile_with_allocation)
            
            recommendations.append({
                "type": "asset_allocation_adjustment",
                "title": "Optimize Investment Allocation",
                "description": "Adjusting your investment allocation would better align with your goal timeframe and risk tolerance.",
                "current_value": current_allocation,
                "recommended_value": recommended_allocation,
                "impact": {
                    "old_probability": current_probability,
                    "new_probability": new_probability,
                    "improvement": new_probability - current_probability
                }
            })
        
        # Recommendation 3: Timeframe adjustment
        if current_probability < 80 and goal.flexibility != "fixed":
            # Try extending timeframe to see if it improves probability
            try:
                target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
                extended_date = target_date + timedelta(days=365)  # Add 1 year
                
                temp_goal = Goal.from_dict(goal.to_dict())  # Clone goal
                temp_goal.timeframe = extended_date.isoformat()
                
                new_probability = calculator.calculate_goal_success_probability(temp_goal, profile)
                
                if new_probability > current_probability + 15:  # Significant improvement
                    recommendations.append({
                        "type": "timeframe_adjustment",
                        "title": "Extend Goal Timeframe",
                        "description": f"Extending your goal timeframe by 1 year to {extended_date.strftime('%d %b %Y')} would significantly improve your chances of success.",
                        "current_value": goal.timeframe,
                        "recommended_value": extended_date.isoformat(),
                        "impact": {
                            "old_probability": current_probability,
                            "new_probability": new_probability,
                            "improvement": new_probability - current_probability
                        }
                    })
            except (ValueError, AttributeError):
                pass  # Skip if date parsing fails
        
        # Recommendation 4: Target amount adjustment (if flexible)
        if goal.flexibility == "very_flexible" and current_probability < 70:
            # Try a slightly reduced target to see if it improves probability
            reduced_target = goal.target_amount * 0.9  # 10% reduction
            
            temp_goal = Goal.from_dict(goal.to_dict())  # Clone goal
            temp_goal.target_amount = reduced_target
            
            new_probability = calculator.calculate_goal_success_probability(temp_goal, profile)
            
            if new_probability > current_probability + 20:  # Significant improvement
                recommendations.append({
                    "type": "target_adjustment",
                    "title": "Consider a Slightly Reduced Target",
                    "description": f"Adjusting your target amount from ₹{goal.target_amount:,.2f} to ₹{reduced_target:,.2f} would significantly improve your success probability.",
                    "current_value": goal.target_amount,
                    "recommended_value": reduced_target,
                    "impact": {
                        "old_probability": current_probability,
                        "new_probability": new_probability,
                        "improvement": new_probability - current_probability
                    }
                })
        
        # Add all recommendations to section
        section.add_content("recommendations", recommendations)
        
        # Add impact visualization
        if recommendations and self.visualization_enabled:
            # Get the most impactful recommendation
            most_impactful = max(recommendations, key=lambda r: r["impact"]["improvement"])
            
            impact_data = {
                "recommendations": [(r["title"], r["impact"]["improvement"]) for r in recommendations],
                "most_impactful": most_impactful["title"],
                "current_probability": current_probability,
                "best_improvement": most_impactful["impact"]["new_probability"]
            }
            section.add_visualization("impact_chart", impact_data)
        
        return section
    
    def _generate_indian_market_context(self, goal_category: str) -> DocumentSection:
        """Generate Indian market specific information for the goal category."""
        section = DocumentSection("Indian Market Context")
        
        # Define educational content based on goal category
        education_content = {}
        
        if goal_category in ["emergency_fund", "insurance", "life_insurance", "health_insurance"]:
            education_content = {
                "context": "Financial safety nets in India",
                "key_facts": [
                    "Health insurance penetration in India is around 36% as of 2023",
                    "The Insurance Regulatory and Development Authority of India (IRDAI) recommends health coverage of at least 5 lakhs per family",
                    "Emergency funds should typically cover 6-12 months of expenses in India, higher than the global recommendation of 3-6 months due to less comprehensive social security"
                ],
                "tax_benefits": f"Section 80D of Income Tax Act allows deduction for health insurance premiums up to {self.format_rupees(self.india_financial['tax_deductions']['80d_limit_self'])} ({self.format_rupees(self.india_financial['tax_deductions']['80d_limit_senior'])} for senior citizens)",
                "market_trends": "Rising healthcare costs in India (10-15% annually) make adequate insurance and emergency funds increasingly important"
            }
        
        elif goal_category in ["retirement", "early_retirement", "traditional_retirement"]:
            education_content = {
                "context": "Retirement planning in India",
                "key_facts": [
                    "India's pension system covers only about 12% of the working population",
                    "Average life expectancy in India is increasing (now around 70 years) requiring longer retirement funding",
                    f"National Pension System (NPS) offers market-linked returns with tax benefits and requires {self.india_financial['retirement']['nps_annuity_requirement']*100}% of corpus for annuity purchase at retirement"
                ],
                "tax_benefits": f"Contributions to EPF, PPF, and NPS offer tax deductions under Section 80C (up to {self.format_rupees(self.india_financial['tax_deductions']['80c_limit'])}) and additional NPS contribution up to {self.format_rupees(self.india_financial['tax_deductions']['nps_additional'])} under 80CCD(1B)",
                "market_trends": f"Mutual fund SIPs are increasingly popular retirement vehicles with average equity returns of {self.india_financial['investment']['equity_expected_return']*100:.0f}% over long periods"
            }
        
        elif goal_category in ["home_purchase"]:
            education_content = {
                "context": "Real estate market in India",
                "key_facts": [
                    f"Real estate prices in Tier 1 cities have appreciated at {self.india_financial['inflation']['housing']*100:.0f}-10% annually over the last decade",
                    "Typical home loan interest rates range from 6.5% to 9.5% in 2023",
                    "Most lenders require a minimum 20% down payment for home loans"
                ],
                "tax_benefits": f"Home loan principal repayment qualifies for deduction under Section 80C (up to {self.format_rupees(self.india_financial['tax_deductions']['80c_limit'])}), while interest is deductible under Section 24 (up to {self.format_rupees(200000)} for self-occupied property)",
                "market_trends": "Affordable housing segment is growing at 18-20% annually with government support under PMAY"
            }
        
        elif goal_category in ["education"]:
            education_content = {
                "context": "Education financing in India",
                "key_facts": [
                    f"Higher education costs in India are rising at {self.india_financial['inflation']['education']*100:.0f}% annually",
                    "Education abroad can cost ₹20-50 lakhs for undergraduate programs and ₹40-80 lakhs for graduate programs",
                    "Education loan interest rates typically range from 7% to 15% depending on the institution and loan amount"
                ],
                "tax_benefits": "Interest paid on education loans is deductible under Section 80E with no upper limit for up to 8 years",
                "market_trends": f"Specialized education-focused mutual funds are emerging, and Sukanya Samriddhi Yojana offers {self.india_financial['investment']['sukanya_samriddhi_rate']*100:.1f}% interest rate for girl child education"
            }
        
        else:
            # Default content for other goal types
            education_content = {
                "context": "Financial planning in India",
                "key_facts": [
                    "India's household savings rate is around 30% of GDP, one of the highest globally",
                    "Mutual funds have grown to manage over ₹40 lakh crore in assets",
                    "Digital payment systems like UPI have revolutionized financial transactions making tracking easier"
                ],
                "tax_benefits": f"Various investment options offer tax benefits under different sections of the Income Tax Act, with Section 80C offering deductions up to {self.format_rupees(self.india_financial['tax_deductions']['80c_limit'])} annually",
                "market_trends": "Goal-based financial planning is gaining popularity over product-focused approaches"
            }
        
        section.add_content("indian_context", education_content)
        
        # Add tax saving recommendations
        tax_recommendations = self._generate_tax_optimization_recommendations(goal_category)
        section.add_content("tax_recommendations", tax_recommendations)
        
        # Add investment vehicle recommendations specific to India
        investment_vehicles = self._generate_investment_vehicle_recommendations(goal_category)
        section.add_content("investment_vehicles", investment_vehicles)
        
        # Add relevant resources for further reading
        resources = self._get_resources_for_category(goal_category)
        section.add_content("resources", resources)
        
        return section
        
    def _generate_tax_optimization_recommendations(self, goal_category: str) -> List[Dict[str, str]]:
        """Generate tax optimization strategies based on Section 80C and other Indian tax provisions."""
        recommendations = []
        
        # Generic 80C recommendations for all goals
        recommendations.append({
            "title": "Maximize Section 80C Benefits",
            "description": f"Utilize the full {self.format_rupees(self.india_financial['tax_deductions']['80c_limit'])} deduction under Section 80C.",
            "options": [
                "ELSS Mutual Funds (3-year lock-in, equity exposure)",
                "Public Provident Fund (15-year lock-in, sovereign guarantee)",
                "National Savings Certificate (5-year lock-in)",
                "Tax Saving Fixed Deposits (5-year lock-in)",
                "ULIPs (5-year lock-in, insurance + investment)"
            ]
        })
        
        # Goal-specific recommendations
        if goal_category in ["retirement", "early_retirement", "traditional_retirement"]:
            recommendations.append({
                "title": "Additional NPS Tax Benefit",
                "description": f"Beyond 80C, contribute to NPS for additional {self.format_rupees(self.india_financial['tax_deductions']['nps_additional'])} deduction under Section 80CCD(1B).",
                "options": [
                    "Choose Active or Auto choice for asset allocation",
                    "Select from available pension fund managers",
                    "Consider corporate NPS if your employer offers it for additional tax benefits"
                ]
            })
            
        elif goal_category in ["home_purchase"]:
            recommendations.append({
                "title": "Home Loan Tax Benefits",
                "description": "Home loans offer dual tax benefits on principal and interest.",
                "options": [
                    f"Principal repayment qualifies under Section 80C (up to {self.format_rupees(self.india_financial['tax_deductions']['80c_limit'])})",
                    "Interest payment deductible under Section 24 (up to ₹2L for self-occupied)",
                    "Additional ₹1.5L deduction under 80EEA for first-time homebuyers (if applicable)",
                    "HRA exemption available until you purchase a home"
                ]
            })
            
        elif goal_category in ["education", "higher_education"]:
            recommendations.append({
                "title": "Education Loan Tax Benefits",
                "description": "Interest paid on education loans is fully deductible under Section 80E.",
                "options": [
                    "No upper limit on interest deduction",
                    "Available for 8 years from the year you start repayment",
                    "Covers education for self, spouse, children, or student for whom you are legal guardian"
                ]
            })
            
        elif goal_category in ["insurance", "life_insurance", "health_insurance"]:
            recommendations.append({
                "title": "Health Insurance Premium Deduction",
                "description": "Maximize tax benefits on health insurance premiums under Section 80D.",
                "options": [
                    f"Up to {self.format_rupees(self.india_financial['tax_deductions']['80d_limit_self'])} for self, spouse, and children",
                    f"Additional {self.format_rupees(self.india_financial['tax_deductions']['80d_limit_parents'])} for parents",
                    f"Higher limits of {self.format_rupees(self.india_financial['tax_deductions']['80d_limit_senior'])} if parents are senior citizens",
                    "Preventive health check-up costs also deductible up to ₹5,000 within these limits"
                ]
            })
        
        return recommendations
        
    def _generate_investment_vehicle_recommendations(self, goal_category: str) -> Dict[str, Any]:
        """Generate investment vehicle recommendations specific to Indian financial context."""
        vehicles = {
            "recommended_vehicles": [],
            "comparison": {}
        }
        
        # Goal-specific investment vehicles
        if goal_category in ["retirement", "early_retirement", "traditional_retirement"]:
            vehicles["recommended_vehicles"] = [
                {
                    "name": "National Pension System (NPS)",
                    "suitability": "High",
                    "features": "Government-backed pension scheme with tax benefits",
                    "expected_returns": "8-12% (based on asset allocation)",
                    "lock_in": "Until retirement age with partial withdrawal options for specific needs",
                    "tax_efficiency": "EEE for 60% corpus, EET for 40% annuity component"
                },
                {
                    "name": "Equity Mutual Fund SIPs",
                    "suitability": "High",
                    "features": "Disciplined investing in diversified equity portfolios",
                    "expected_returns": f"{self.india_financial['investment']['equity_expected_return']*100:.0f}% long-term",
                    "lock_in": "None (ELSS funds have 3 years)",
                    "tax_efficiency": "LTCG taxed at 10% above ₹1 lakh annually"
                },
                {
                    "name": "Public Provident Fund (PPF)",
                    "suitability": "Medium-High",
                    "features": "Government-backed savings scheme with sovereign guarantee",
                    "expected_returns": f"{self.india_financial['investment']['ppf_interest_rate']*100:.1f}% (subject to quarterly revisions)",
                    "lock_in": "15 years (partial withdrawals allowed after 7 years)",
                    "tax_efficiency": "EEE (Exempt-Exempt-Exempt)"
                }
            ]
            
            # Add comparison table for retirement vehicles
            vehicles["comparison"] = {
                "parameters": ["Expected Returns", "Risk Level", "Liquidity", "Tax Benefits", "Min Investment"],
                "vehicles": ["NPS", "ELSS", "PPF", "EPF"],
                "data": [
                    ["8-12%", "10-12%", f"{self.india_financial['investment']['ppf_interest_rate']*100:.1f}%", f"{self.india_financial['retirement']['epf_interest_rate']*100:.2f}%"],
                    ["Medium", "High", "Very Low", "Very Low"],
                    ["Low", "Medium", "Low", "Low"],
                    ["High", "Medium", "High", "High"],
                    ["₹500/month", "₹500", "₹500", "12% of Basic"]
                ]
            }
            
        elif goal_category in ["education", "higher_education"]:
            vehicles["recommended_vehicles"] = [
                {
                    "name": "Sukanya Samriddhi Yojana (for girl child)",
                    "suitability": "Very High (for daughters)",
                    "features": "Government-backed savings scheme for girl child education/marriage",
                    "expected_returns": f"{self.india_financial['investment']['sukanya_samriddhi_rate']*100:.1f}% (subject to quarterly revisions)",
                    "lock_in": "21 years or until marriage after 18 years",
                    "tax_efficiency": "EEE (Exempt-Exempt-Exempt)"
                },
                {
                    "name": "Balanced Mutual Funds",
                    "suitability": "High",
                    "features": "Mix of equity and debt providing growth with stability",
                    "expected_returns": "9-11% long-term",
                    "lock_in": "None",
                    "tax_efficiency": "As per equity/debt taxation rules"
                },
                {
                    "name": "Recurring Deposits",
                    "suitability": "Medium (short-term goals)",
                    "features": "Fixed monthly savings with guaranteed returns",
                    "expected_returns": "5.5-6.5%",
                    "lock_in": "As per selected tenure",
                    "tax_efficiency": "Interest taxable as per income slab"
                }
            ]
            
        elif goal_category in ["home_purchase"]:
            vehicles["recommended_vehicles"] = [
                {
                    "name": "Bank Recurring Deposits",
                    "suitability": "High (for down payment saving)",
                    "features": "Guaranteed returns with disciplined monthly contributions",
                    "expected_returns": "5.5-6.5%",
                    "lock_in": "Flexible based on goal timeline",
                    "tax_efficiency": "Interest taxable as per income slab"
                },
                {
                    "name": "Corporate Fixed Deposits",
                    "suitability": "Medium-High",
                    "features": "Higher returns than bank FDs with reasonable safety",
                    "expected_returns": "7-9%",
                    "lock_in": "1-5 years",
                    "tax_efficiency": "Interest taxable as per income slab"
                },
                {
                    "name": "Debt Mutual Funds",
                    "suitability": "Medium-High",
                    "features": "Professional management with diversification",
                    "expected_returns": f"{self.india_financial['investment']['debt_expected_return']*100:.0f}%",
                    "lock_in": "None (consider 3+ years for tax efficiency)",
                    "tax_efficiency": "Better tax efficiency for 3+ year investments"
                }
            ]
            
        elif goal_category in ["emergency_fund"]:
            vehicles["recommended_vehicles"] = [
                {
                    "name": "High-Yield Savings Account",
                    "suitability": "Very High",
                    "features": "Immediate accessibility with some interest",
                    "expected_returns": "3.5-4.5%",
                    "lock_in": "None",
                    "tax_efficiency": "Interest taxable as per income slab"
                },
                {
                    "name": "Liquid Funds",
                    "suitability": "High",
                    "features": "Low risk mutual funds with quick redemption (T+1)",
                    "expected_returns": "5-6%",
                    "lock_in": "None",
                    "tax_efficiency": "Better than savings account for 3+ years"
                },
                {
                    "name": "Sweep-in Fixed Deposits",
                    "suitability": "High",
                    "features": "Combines savings account liquidity with FD returns",
                    "expected_returns": "5.5-6.5% on swept amount",
                    "lock_in": "None",
                    "tax_efficiency": "Interest taxable as per income slab"
                }
            ]
            
        else:
            # Default investment vehicles for other goals
            vehicles["recommended_vehicles"] = [
                {
                    "name": "Hybrid Mutual Funds",
                    "suitability": "High",
                    "features": "Balanced mix of equity and debt based on goal timeline",
                    "expected_returns": "9-11% long-term",
                    "lock_in": "None",
                    "tax_efficiency": "As per equity/debt taxation rules"
                },
                {
                    "name": "Systematic Investment Plans (SIPs)",
                    "suitability": "High",
                    "features": "Disciplined investing with rupee cost averaging",
                    "expected_returns": "Based on chosen mutual fund category",
                    "lock_in": "None (ELSS funds have 3 years)",
                    "tax_efficiency": "Depends on fund type"
                },
                {
                    "name": "Corporate Bonds",
                    "suitability": "Medium",
                    "features": "Fixed income instruments with higher returns than FDs",
                    "expected_returns": "7-9%",
                    "lock_in": "Based on bond maturity",
                    "tax_efficiency": "Interest taxable as per income slab"
                }
            ]
        
        return vehicles
    
    def _generate_monthly_action_plan(self, goal: Goal, profile: Dict[str, Any]) -> DocumentSection:
        """
        Generate monthly action plan with specific tasks for reaching the goal.
        
        Args:
            goal (Goal): The financial goal to generate action plan for
            profile (Dict[str, Any]): User profile data
            
        Returns:
            DocumentSection: Monthly action plan section with tasks and timeline
        """
        section = DocumentSection("Monthly Action Plan")
        
        # Calculate goal metrics for action plan
        try:
            target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
            today = datetime.now()
            months_remaining = max(1, (target_date - today).days / 30)
            years_remaining = months_remaining / 12
            
            # Calculate monthly contribution needed
            current_amount = goal.current_amount or 0
            target_amount = goal.target_amount
            
            # Default expected return based on goal category and timeframe
            expected_return = 0.07  # 7% default
            if goal.category in ["retirement", "education"] and years_remaining > 5:
                expected_return = 0.09  # 9% for long-term goals
            elif goal.category in ["home_purchase", "vehicle"] and years_remaining > 3:
                expected_return = 0.08  # 8% for medium-term goals
            elif goal.category in ["emergency_fund", "short_term"]:
                expected_return = 0.05  # 5% for short-term goals
                
            # Calculate SIP amount needed
            monthly_contribution = self.calculate_sip_amount(
                target_amount - current_amount, 
                years_remaining, 
                expected_return
            )
            
            # Create action steps based on goal analysis
            action_steps = []
            
            # Step 1: Adjust monthly contributions
            action_steps.append({
                "title": "Adjust Monthly SIP Contribution",
                "description": f"Set up or adjust your monthly SIP to reach your goal target of {self.format_rupees(target_amount)}.",
                "tasks": [
                    f"Required monthly contribution: {self.format_rupees(monthly_contribution)}",
                    "Set up auto-debit from your bank account on a fixed date",
                    "Consider increasing SIP amount by 5-10% annually to account for inflation and income growth"
                ],
                "target_date": "Immediate"
            })
            
            # Step 2: Asset allocation review and adjustment
            action_steps.append({
                "title": "Review and Adjust Asset Allocation",
                "description": "Ensure your investments are aligned with appropriate asset allocation for this goal.",
                "tasks": [
                    f"For {goal.category} goals with {years_remaining:.1f} years remaining, consider:",
                    self._get_recommended_asset_allocation_task(goal.category, years_remaining),
                    "Review existing investments and realign if needed",
                    "Set calendar reminder to review allocation quarterly"
                ],
                "target_date": "Within 1 week"
            })
            
            # Step 3: Tax optimization
            if goal.category in ["retirement", "education", "home_purchase"]:
                action_steps.append({
                    "title": "Implement Tax Optimization Strategy",
                    "description": "Maximize tax benefits available for your goal.",
                    "tasks": [
                        "Review applicable tax deductions (Section 80C, 80D, etc.)",
                        "Select tax-efficient investment vehicles",
                        "Maintain documentation for tax filing"
                    ],
                    "target_date": "Within 2 weeks"
                })
            
            # Step 4: Set up tracking system
            action_steps.append({
                "title": "Establish Goal Tracking System",
                "description": "Set up a system to track progress towards your goal.",
                "tasks": [
                    "Create a spreadsheet or use an app to monitor contributions and growth",
                    "Schedule quarterly reviews of goal progress",
                    "Set alerts for major milestones (25%, 50%, 75% completion)"
                ],
                "target_date": "Within 2 weeks"
            })
            
            # Step 5: Contingency planning
            action_steps.append({
                "title": "Create Contingency Plan",
                "description": "Prepare backup plans for unexpected events or market downturns.",
                "tasks": [
                    "Identify flexible expenses that can be redirected to goal if needed",
                    "Consider goal insurance or protection if applicable",
                    "Define trigger points for plan revision (e.g., 10% market drop, income change)"
                ],
                "target_date": "Within 1 month"
            })
            
            # Calculate milestone dates
            milestones = []
            if months_remaining > 3:
                # Create quarterly milestones
                for i in range(1, min(5, int(months_remaining / 3) + 1)):
                    milestone_date = (today + timedelta(days=i * 3 * 30)).strftime("%Y-%m-%d")
                    milestone_target = current_amount + (i * 3 * monthly_contribution * 1.01)  # Slight growth added
                    milestones.append({
                        "date": milestone_date,
                        "name": f"Quarter {i} Review",
                        "target_amount": milestone_target,
                        "formatted_amount": self.format_rupees(milestone_target)
                    })
            
            # Add final milestone
            milestones.append({
                "date": target_date.strftime("%Y-%m-%d"),
                "name": "Goal Target Date",
                "target_amount": target_amount,
                "formatted_amount": self.format_rupees(target_amount)
            })
            
            # Add content to section
            section.add_content("action_steps", action_steps)
            section.add_content("milestones", milestones)
            section.add_content("monthly_contribution", {
                "amount": monthly_contribution,
                "formatted": self.format_rupees(monthly_contribution)
            })
            
            # Add visualization if available
            if self.visualization_enabled:
                try:
                    # Generate action plan timeline
                    timeline_data = {
                        "milestones": milestones,
                        "monthly_contribution": monthly_contribution
                    }
                    section.add_visualization("action_timeline", timeline_data)
                    
                    # Generate contribution impact visualization
                    # This shows how varying the contribution affects goal probability
                    contribution_impact = self.create_contribution_impact_chart(goal, monthly_contribution)
                    section.add_visualization("contribution_impact", contribution_impact)
                except Exception as e:
                    logger.error(f"Error generating action plan visualizations: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error generating monthly action plan: {str(e)}")
            # Add fallback content
            section.add_content("error", f"Could not generate detailed action plan: {str(e)}")
            section.add_content("action_steps", [{
                "title": "Review Your Goal Details",
                "description": "Please review your goal details to allow for proper action plan generation.",
                "tasks": [
                    "Ensure goal target amount is specified",
                    "Verify goal timeframe is valid",
                    "Update current progress information"
                ],
                "target_date": "Immediate"
            }])
        
        return section
    
    def _get_recommended_asset_allocation_task(self, category: str, years_remaining: float) -> str:
        """Get asset allocation recommendation based on goal category and time horizon."""
        if years_remaining < 1:
            return "Liquid funds (100%) for maximum safety with goal deadline approaching"
        elif years_remaining < 3:
            return "Liquid funds (50%), Short-term debt funds (40%), Equity funds (10%)"
        elif years_remaining < 5:
            return "Equity funds (30%), Debt funds (60%), Gold or alternative assets (10%)"
        elif years_remaining < 10:
            return "Equity funds (50%), Debt funds (40%), Gold or alternative assets (10%)"
        else:
            return "Equity funds (70%), Debt funds (20%), Gold or alternative assets (10%)"
    
    # Helper methods for calculations and visualizations
    
    def _calculate_overall_progress(self, goals: List[Goal]) -> float:
        """Calculate overall progress percentage across all goals."""
        total_target = sum(g.target_amount for g in goals)
        total_current = sum(g.current_amount for g in goals)
        
        if total_target > 0:
            return min(100.0, (total_current / total_target) * 100.0)
        return 0.0
    
    def _group_goals_by_category(self, goals: List[Goal]) -> Dict[str, Any]:
        """Group goals by category with summary metrics."""
        category_data = {}
        
        for goal in goals:
            if goal.category not in category_data:
                category_data[goal.category] = {
                    "count": 0,
                    "total_target": 0,
                    "total_current": 0,
                    "goals": []
                }
            
            category_data[goal.category]["count"] += 1
            category_data[goal.category]["total_target"] += goal.target_amount
            category_data[goal.category]["total_current"] += goal.current_amount
            category_data[goal.category]["goals"].append(goal.id)
        
        # Calculate progress for each category
        for category in category_data:
            if category_data[category]["total_target"] > 0:
                progress = (category_data[category]["total_current"] / 
                           category_data[category]["total_target"]) * 100.0
                category_data[category]["progress"] = min(100.0, progress)
            else:
                category_data[category]["progress"] = 0.0
        
        return category_data
    
    def _generate_goals_timeline(self, goals: List[Goal]) -> Dict[str, Any]:
        """Generate timeline data for goals visualization."""
        timeline_events = []
        
        for goal in goals:
            try:
                # Parse target date
                target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
                
                # Create timeline event
                timeline_events.append({
                    "goal_id": goal.id,
                    "title": goal.title,
                    "category": goal.category,
                    "date": target_date.isoformat(),
                    "target_amount": goal.target_amount,
                    "current_amount": goal.current_amount,
                    "progress": goal.current_progress
                })
            except (ValueError, AttributeError):
                # Skip goals with invalid dates
                continue
        
        # Sort events by date
        timeline_events.sort(key=lambda e: e["date"])
        
        return {
            "events": timeline_events,
            "categories": list(set(g.category for g in goals))
        }
    
    def _generate_portfolio_allocation(self, goals: List[Goal]) -> Dict[str, Any]:
        """Generate recommended portfolio allocation across all goals."""
        # Initialize allocation categories
        allocation = {
            "equity": 0,
            "debt": 0,
            "liquid": 0,
            "real_estate": 0,
            "gold": 0,
            "alternative": 0
        }
        
        # Get total target amount
        total_target = sum(g.target_amount for g in goals)
        
        if total_target <= 0:
            return allocation
        
        # Calculate weighted allocation based on goal timeframes and amounts
        for goal in goals:
            try:
                # Parse target date to determine time horizon
                target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
                today = datetime.now()
                years = max(0, (target_date - today).days / 365)
                
                # Weight of this goal in overall portfolio
                weight = goal.target_amount / total_target
                
                # Assign allocation based on time horizon
                if years < 1:
                    # Short-term: Mostly liquid and short-term debt
                    allocation["liquid"] += weight * 0.7
                    allocation["debt"] += weight * 0.3
                elif years < 3:
                    # Medium-short term: Conservative mix
                    allocation["liquid"] += weight * 0.3
                    allocation["debt"] += weight * 0.5
                    allocation["equity"] += weight * 0.15
                    allocation["gold"] += weight * 0.05
                elif years < 7:
                    # Medium term: Balanced mix
                    allocation["debt"] += weight * 0.4
                    allocation["equity"] += weight * 0.4
                    allocation["gold"] += weight * 0.1
                    allocation["real_estate"] += weight * 0.05
                    allocation["alternative"] += weight * 0.05
                else:
                    # Long term: Growth oriented
                    allocation["equity"] += weight * 0.6
                    allocation["debt"] += weight * 0.2
                    allocation["real_estate"] += weight * 0.1
                    allocation["gold"] += weight * 0.05
                    allocation["alternative"] += weight * 0.05
            except (ValueError, AttributeError, ZeroDivisionError):
                # Skip goals with invalid dates
                continue
        
        # Round to reasonable precision
        for key in allocation:
            allocation[key] = round(allocation[key] * 100, 1)  # Convert to percentage
        
        return allocation
    
    def _calculate_financial_health_metrics(self, goals: List[Goal], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate financial health indicators for the profile."""
        metrics = {}
        
        # Check if emergency fund exists
        has_emergency_fund = any(g.category == "emergency_fund" for g in goals)
        metrics["has_emergency_fund"] = has_emergency_fund
        
        # Check if insurance goals exist
        has_insurance = any(g.category in ["insurance", "life_insurance", "health_insurance"] for g in goals)
        metrics["has_insurance"] = has_insurance
        
        # Calculate savings rate if income info is available
        if "monthly_income" in profile and profile["monthly_income"] > 0:
            total_monthly_saving = profile.get("monthly_savings", 0)
            savings_rate = (total_monthly_saving / profile["monthly_income"]) * 100
            metrics["savings_rate"] = round(savings_rate, 1)
            
            # Benchmark against ideal rates
            if savings_rate >= 30:
                metrics["savings_status"] = "Excellent"
            elif savings_rate >= 20:
                metrics["savings_status"] = "Good"
            elif savings_rate >= 10:
                metrics["savings_status"] = "Moderate"
            else:
                metrics["savings_status"] = "Needs Improvement"
        
        # Calculate goal coverage
        essential_categories = ["emergency_fund", "insurance", "life_insurance", 
                              "health_insurance", "debt_repayment", "retirement"]
        has_essential_categories = [any(g.category == cat for g in goals) for cat in essential_categories]
        metrics["essential_coverage"] = sum(has_essential_categories) / len(essential_categories) * 100
        
        # Calculate debt-to-income ratio if available
        if "monthly_income" in profile and "monthly_debt_payments" in profile and profile["monthly_income"] > 0:
            debt_ratio = (profile["monthly_debt_payments"] / profile["monthly_income"]) * 100
            metrics["debt_to_income_ratio"] = round(debt_ratio, 1)
            
            # Benchmark against ideal ratios
            if debt_ratio <= 30:
                metrics["debt_status"] = "Healthy"
            elif debt_ratio <= 40:
                metrics["debt_status"] = "Manageable"
            elif debt_ratio <= 50:
                metrics["debt_status"] = "Concerning"
            else:
                metrics["debt_status"] = "Problematic"
        
        # Overall financial health score (simple calculation)
        health_score = 0
        components = 0
        
        if has_emergency_fund:
            health_score += 25
            components += 1
            
        if has_insurance:
            health_score += 25
            components += 1
            
        if "savings_rate" in metrics:
            rate_score = min(25, metrics["savings_rate"] * 25 / 30)  # Max score at 30% savings rate
            health_score += rate_score
            components += 1
            
        if "debt_to_income_ratio" in metrics:
            if metrics["debt_to_income_ratio"] <= 20:
                debt_score = 25
            else:
                debt_score = max(0, 25 - (metrics["debt_to_income_ratio"] - 20) * 25 / 30)
            health_score += debt_score
            components += 1
            
        if components > 0:
            metrics["financial_health_score"] = round(health_score / components, 0)
            
            # Health status
            if metrics["financial_health_score"] >= 80:
                metrics["health_status"] = "Excellent"
            elif metrics["financial_health_score"] >= 60:
                metrics["health_status"] = "Good"
            elif metrics["financial_health_score"] >= 40:
                metrics["health_status"] = "Fair"
            else:
                metrics["health_status"] = "Needs Attention"
        
        return metrics
    
    def _generate_goal_comparison_chart(self, goals: List[Goal]) -> Dict[str, Any]:
        """Generate comparison chart data for multiple goals."""
        chart_data = {
            "goal_ids": [g.id for g in goals],
            "titles": [g.title for g in goals],
            "target_amounts": [g.target_amount for g in goals],
            "current_amounts": [g.current_amount for g in goals],
            "progress": [g.current_progress for g in goals],
            "probabilities": [g.goal_success_probability for g in goals],
            "categories": [g.category for g in goals]
        }
        
        # Calculate time to target for each goal
        time_to_target = []
        for goal in goals:
            try:
                target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
                today = datetime.now()
                days = (target_date - today).days
                years = max(0, days / 365)
                time_to_target.append(years)
            except (ValueError, AttributeError):
                time_to_target.append(0)
        
        chart_data["time_to_target"] = time_to_target
        
        return chart_data
    
    def _analyze_goal_tradeoffs(self, goals: List[Goal]) -> Dict[str, Any]:
        """Analyze resource tradeoffs between multiple goals."""
        tradeoff_data = {
            "funding_competition": [],
            "timeline_conflicts": [],
            "priority_ranking": []
        }
        
        # Sort goals by priority score
        goals_by_priority = sorted(goals, key=lambda g: g.priority_score, reverse=True)
        
        # Add priority ranking
        for i, goal in enumerate(goals_by_priority):
            tradeoff_data["priority_ranking"].append({
                "goal_id": goal.id,
                "title": goal.title,
                "priority_score": goal.priority_score,
                "rank": i + 1
            })
        
        # Analyze timeframe overlaps
        timeline_goals = []
        for goal in goals:
            try:
                target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
                timeline_goals.append((goal, target_date))
            except (ValueError, AttributeError):
                continue
        
        # Sort by target date
        timeline_goals.sort(key=lambda g: g[1])
        
        # Find clusters of goals with nearby target dates
        clusters = []
        current_cluster = []
        
        for i, (goal, date) in enumerate(timeline_goals):
            if not current_cluster:
                current_cluster.append((goal, date))
            else:
                prev_date = current_cluster[-1][1]
                if (date - prev_date).days < 365:  # Goals within 1 year
                    current_cluster.append((goal, date))
                else:
                    if len(current_cluster) > 1:
                        clusters.append(current_cluster)
                    current_cluster = [(goal, date)]
        
        if len(current_cluster) > 1:
            clusters.append(current_cluster)
        
        # Add timeline conflicts
        for cluster in clusters:
            if len(cluster) > 1:
                conflict = {
                    "time_period": cluster[0][1].strftime("%b %Y") + " - " + cluster[-1][1].strftime("%b %Y"),
                    "goals": [{
                        "goal_id": g.id,
                        "title": g.title,
                        "target_amount": g.target_amount,
                        "target_date": d.isoformat()
                    } for g, d in cluster]
                }
                tradeoff_data["timeline_conflicts"].append(conflict)
        
        # Analyze funding competition for goals with overlapping timelines
        funding_competition = []
        for i, goal1 in enumerate(goals):
            for goal2 in goals[i+1:]:
                # Check if goals overlap in time
                try:
                    date1 = datetime.fromisoformat(goal1.timeframe.replace('Z', '+00:00'))
                    date2 = datetime.fromisoformat(goal2.timeframe.replace('Z', '+00:00'))
                    
                    # Both dates in future, and within 3 years of each other
                    today = datetime.now()
                    if date1 > today and date2 > today and abs((date1 - date2).days) < 1095:
                        competition = {
                            "goal1": {
                                "goal_id": goal1.id,
                                "title": goal1.title,
                                "target_amount": goal1.target_amount,
                                "target_date": goal1.timeframe,
                                "priority_score": goal1.priority_score
                            },
                            "goal2": {
                                "goal_id": goal2.id,
                                "title": goal2.title,
                                "target_amount": goal2.target_amount,
                                "target_date": goal2.timeframe,
                                "priority_score": goal2.priority_score
                            },
                            "competition_score": min(10, (goal1.target_amount + goal2.target_amount) / 100000)
                        }
                        funding_competition.append(competition)
                except (ValueError, AttributeError):
                    continue
        
        # Sort by competition score and add top competitions
        funding_competition.sort(key=lambda c: c["competition_score"], reverse=True)
        tradeoff_data["funding_competition"] = funding_competition[:3]  # Top 3 competitions
        
        return tradeoff_data
    
    def _compare_funding_strategies(self, goals: List[Goal]) -> Dict[str, Any]:
        """Compare funding strategies for multiple goals."""
        strategies_comparison = {
            "strategies": [],
            "recommended_sequence": []
        }
        
        for goal in goals:
            strategy = {}
            
            # Parse funding strategy from JSON if available
            if goal.funding_strategy:
                try:
                    strategy = json.loads(goal.funding_strategy)
                except (json.JSONDecodeError, TypeError):
                    strategy = {}
            
            # Add basic strategy information
            strategy_info = {
                "goal_id": goal.id,
                "title": goal.title,
                "category": goal.category,
                "priority_score": goal.priority_score,
                "importance": goal.importance,
                "recommended_priority": strategy.get("recommended_priority", 0)
            }
            
            # Add category-specific strategy elements
            if goal.category == "retirement":
                strategy_info["retirement_age"] = strategy.get("retirement_age", 60)
                strategy_info["withdrawal_rate"] = strategy.get("withdrawal_rate", 0.04)
            
            elif goal.category == "home_purchase":
                strategy_info["down_payment_percent"] = strategy.get("down_payment_percent", 0.20)
            
            elif goal.category in ["debt_repayment", "debt_elimination"]:
                strategy_info["debt_type"] = strategy.get("debt_type", "general")
                strategy_info["interest_rate"] = strategy.get("interest_rate", 0.10)
            
            strategies_comparison["strategies"].append(strategy_info)
        
        # Determine recommended funding sequence
        # Sort by recommended_priority first, then by priority_score
        sorted_goals = sorted(
            strategies_comparison["strategies"], 
            key=lambda g: (g.get("recommended_priority", 99), -g["priority_score"])
        )
        
        strategies_comparison["recommended_sequence"] = [
            {"goal_id": g["goal_id"], "title": g["title"], "sequence": i+1}
            for i, g in enumerate(sorted_goals)
        ]
        
        return strategies_comparison
    
    def _calculate_sensitivity_analysis(self, goal: Goal, profile: Dict[str, Any], 
                                     calculator: GoalCalculator) -> Dict[str, Any]:
        """Calculate sensitivity of goal success to different parameters."""
        sensitivity = {}
        
        # Get current success probability as baseline
        base_probability = calculator.calculate_goal_success_probability(goal, profile)
        
        # Test monthly savings sensitivity
        if "monthly_savings" in profile and profile["monthly_savings"] > 0:
            savings_increase = profile["monthly_savings"] * 0.2  # 20% increase
            
            # Create modified profile
            profile_mod = profile.copy()
            profile_mod["monthly_savings"] += savings_increase
            
            # Calculate new probability
            new_probability = calculator.calculate_goal_success_probability(goal, profile_mod)
            
            # Calculate sensitivity (change in probability per unit change in savings)
            sensitivity["monthly_savings"] = {
                "base_value": profile["monthly_savings"],
                "modified_value": profile_mod["monthly_savings"],
                "base_probability": base_probability,
                "modified_probability": new_probability,
                "change": new_probability - base_probability,
                "sensitivity": (new_probability - base_probability) / savings_increase
            }
        
        # Test return rate sensitivity
        if "expected_return" in profile:
            return_increase = 0.01  # 1% increase
            
            # Create modified profile
            profile_mod = profile.copy()
            profile_mod["expected_return"] = profile.get("expected_return", 0.08) + return_increase
            
            # Calculate new probability
            new_probability = calculator.calculate_goal_success_probability(goal, profile_mod)
            
            # Calculate sensitivity
            sensitivity["expected_return"] = {
                "base_value": profile.get("expected_return", 0.08),
                "modified_value": profile_mod["expected_return"],
                "base_probability": base_probability,
                "modified_probability": new_probability,
                "change": new_probability - base_probability,
                "sensitivity": (new_probability - base_probability) / return_increase
            }
        
        # Test timeframe sensitivity
        try:
            target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
            extended_date = target_date + timedelta(days=365)  # Add 1 year
            
            # Clone goal and modify timeframe
            temp_goal = Goal.from_dict(goal.to_dict())
            temp_goal.timeframe = extended_date.isoformat()
            
            # Calculate new probability
            new_probability = calculator.calculate_goal_success_probability(temp_goal, profile)
            
            # Calculate sensitivity
            sensitivity["timeframe"] = {
                "base_value": goal.timeframe,
                "modified_value": temp_goal.timeframe,
                "base_probability": base_probability,
                "modified_probability": new_probability,
                "change": new_probability - base_probability,
                "sensitivity": new_probability - base_probability  # Per year
            }
        except (ValueError, AttributeError):
            pass  # Skip if date parsing fails
        
        return sensitivity
    
    def _calculate_trend_line(self, projection: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trend line parameters from projection data."""
        if not projection or len(projection) < 2:
            return {"slope": 0, "intercept": 0}
        
        try:
            # Extract x (days from start) and y (amounts) values
            start_date = datetime.fromisoformat(projection[0]["date"].replace('Z', '+00:00'))
            x_values = []
            y_values = []
            
            for point in projection:
                date = datetime.fromisoformat(point["date"].replace('Z', '+00:00'))
                days = (date - start_date).days
                amount = point["amount"]
                
                x_values.append(days)
                y_values.append(amount)
            
            # Calculate mean of x and y
            n = len(x_values)
            mean_x = sum(x_values) / n
            mean_y = sum(y_values) / n
            
            # Calculate slope and intercept
            numerator = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
            denominator = sum((x_values[i] - mean_x) ** 2 for i in range(n))
            
            if denominator == 0:
                slope = 0
            else:
                slope = numerator / denominator
                
            intercept = mean_y - slope * mean_x
            
            return {
                "slope": slope,
                "intercept": intercept,
                "start_date": projection[0]["date"],
                "end_date": projection[-1]["date"]
            }
        except Exception as e:
            logger.warning(f"Error calculating trend line: {str(e)}")
            return {"slope": 0, "intercept": 0}
    
    def _format_data_as_table(self, data: Union[Dict[str, Any], List[Any]]) -> List[List[str]]:
        """Format dictionary or list data as a table for PDF report."""
        if not data:
            return None
        
        if isinstance(data, dict):
            # Format dictionary as 2-column table
            table_data = [["Key", "Value"]]  # Header row
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    # Skip complex nested structures
                    value = "Complex data (see detailed sections)"
                table_data.append([str(key), str(value)])
            return table_data
            
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            # Format list of dictionaries as table with keys as columns
            # Get all unique keys
            keys = set()
            for item in data:
                keys.update(item.keys())
            keys = sorted(keys)
            
            # Create header row
            table_data = [keys]
            
            # Add data rows
            for item in data:
                row = [str(item.get(key, "")) for key in keys]
                table_data.append(row)
                
            return table_data
            
        elif isinstance(data, list):
            # Format simple list as single column table
            table_data = [["Value"]]  # Header row
            for value in data:
                table_data.append([str(value)])
            return table_data
        
        return None
    
    def _get_resources_for_category(self, category: str) -> List[Dict[str, str]]:
        """Get relevant resources for a goal category targeted at Indian context."""
        # Define resources by category
        resources_by_category = {
            "emergency_fund": [
                {
                    "title": "Emergency Fund Planning in India",
                    "description": "Comprehensive guide to emergency fund planning for Indian families",
                    "source": "Moneycontrol",
                    "url": "https://www.moneycontrol.com/news/business/personal-finance/how-to-build-an-emergency-fund-8240171.html"
                },
                {
                    "title": "How much emergency fund do you need?",
                    "description": "Calculator and guidelines for determining adequate emergency savings",
                    "source": "Scripbox",
                    "url": "https://scripbox.com/pf/emergency-fund/"
                }
            ],
            "insurance": [
                {
                    "title": "Insurance Planning Guide",
                    "description": "Comprehensive insurance planning for Indian families",
                    "source": "IRDAI",
                    "url": "https://www.irdai.gov.in/consumer-education"
                },
                {
                    "title": "Health Insurance Needs Calculator",
                    "description": "Tool to determine optimal health insurance coverage",
                    "source": "PolicyBazaar",
                    "url": "https://www.policybazaar.com/health-insurance/"
                }
            ],
            "retirement": [
                {
                    "title": "Retirement Planning in India",
                    "description": "Comprehensive guide to retirement strategies for Indians",
                    "source": "Value Research",
                    "url": "https://www.valueresearchonline.com/stories/50986/retirement-planning-10-mistakes-that-indians-make/"
                },
                {
                    "title": "NPS vs Mutual Funds vs PPF",
                    "description": "Comparison of retirement vehicles in India",
                    "source": "Economic Times",
                    "url": "https://economictimes.indiatimes.com/wealth/invest/nps-vs-mutual-funds-vs-ppf-which-is-best-for-retirement-planning/articleshow/98636313.cms"
                }
            ],
            "home_purchase": [
                {
                    "title": "Home Buying Guide for India",
                    "description": "Step-by-step guide to purchasing property in India",
                    "source": "Housing.com",
                    "url": "https://housing.com/news/a-guide-to-buying-a-house-in-india/"
                },
                {
                    "title": "PMAY Subsidy Calculator",
                    "description": "Check eligibility for Pradhan Mantri Awas Yojana benefits",
                    "source": "NHB",
                    "url": "https://pmay-urban.gov.in/"
                }
            ],
            "education": [
                {
                    "title": "Education Planning in India",
                    "description": "Guide to funding education for children in India",
                    "source": "FundsIndia",
                    "url": "https://www.fundsindia.com/blog/education-planning-for-your-child/"
                },
                {
                    "title": "Education Loan Guide",
                    "description": "Comprehensive guide to education loans in India",
                    "source": "Vidya Lakshmi Portal",
                    "url": "https://www.vidyalakshmi.co.in/Students/"
                }
            ]
        }
        
        # Default resources for any category not specifically mapped
        default_resources = [
            {
                "title": "Financial Goal Planning",
                "description": "Guide to setting and achieving financial goals in India",
                "source": "Zerodha Varsity",
                "url": "https://zerodha.com/varsity/module/personalfinance/"
            },
            {
                "title": "Tax-Efficient Investment Guide",
                "description": "Maximizing returns through tax-efficient investment strategies",
                "source": "Cleartax",
                "url": "https://cleartax.in/s/investment-options"
            }
        ]
        
        # Return category-specific resources or defaults
        return resources_by_category.get(category, default_resources)
        
    # Visualization methods
    
    def create_progress_meter_visualization(self, progress_percentage: float, target_amount: float, 
                                        current_amount: float) -> Dict[str, Any]:
        """
        Create progress meter visualization showing percentage completion.
        
        Args:
            progress_percentage (float): Percentage completion (0-100)
            target_amount (float): Target amount
            current_amount (float): Current amount
            
        Returns:
            Dict[str, Any]: Visualization data
        """
        if not self.visualization_enabled:
            # Return data only if visualization not available
            return {
                "progress": progress_percentage,
                "target": target_amount,
                "current": current_amount,
                "formatted_target": self.format_rupees(target_amount),
                "formatted_current": self.format_rupees(current_amount)
            }
        
        try:
            # Create figure
            fig = plt.figure(figsize=(8, 3))
            ax = fig.add_subplot(111)
            
            # Progress bar colors
            if progress_percentage >= 80:
                color = '#27ae60'  # Green
            elif progress_percentage >= 40:
                color = '#f39c12'  # Amber
            else:
                color = '#e74c3c'  # Red
                
            # Create progress bar
            ax.barh(0, 100, height=0.5, color='#ecf0f1', alpha=0.3)
            ax.barh(0, progress_percentage, height=0.5, color=color)
            
            # Add percentage text
            ax.text(progress_percentage/2, 0, f"{progress_percentage:.1f}%", 
                   ha='center', va='center', color='white', fontweight='bold')
            
            # Add current and target amount texts
            ax.text(0, -0.5, self.format_rupees(current_amount), ha='left', va='top')
            ax.text(100, -0.5, self.format_rupees(target_amount), ha='right', va='top')
            
            # Clean up axes
            ax.set_xlim(0, 100)
            ax.set_ylim(-1, 1)
            ax.set_yticks([])
            ax.set_xticks([])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            plt.close(fig)
            
            # Encode image
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('ascii')
            image_data = f"data:image/png;base64,{image_base64}"
            
            return {
                "progress": progress_percentage,
                "target": target_amount,
                "current": current_amount,
                "formatted_target": self.format_rupees(target_amount),
                "formatted_current": self.format_rupees(current_amount),
                "image_data": image_data
            }
            
        except Exception as e:
            logger.error(f"Error creating progress meter visualization: {str(e)}")
            return {
                "progress": progress_percentage,
                "target": target_amount,
                "current": current_amount,
                "formatted_target": self.format_rupees(target_amount),
                "formatted_current": self.format_rupees(current_amount),
                "error": str(e)
            }
    
    def create_timeline_visualization(self, milestones: List[Dict[str, Any]], 
                                   start_date: str, end_date: str, 
                                   current_date: str = None) -> Dict[str, Any]:
        """
        Create timeline visualization with key milestones and target dates.
        
        Args:
            milestones (List[Dict[str, Any]]): List of milestone data
            start_date (str): Start date (ISO format)
            end_date (str): End date (ISO format)
            current_date (str, optional): Current date (ISO format)
            
        Returns:
            Dict[str, Any]: Visualization data
        """
        if not self.visualization_enabled:
            # Return data only if visualization not available
            return {
                "milestones": milestones,
                "start_date": start_date,
                "end_date": end_date,
                "current_date": current_date or datetime.now().isoformat()
            }
        
        try:
            # Parse dates
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            current = datetime.fromisoformat(current_date.replace('Z', '+00:00')) if current_date else datetime.now()
            
            # Create figure
            fig = plt.figure(figsize=(10, 4))
            ax = fig.add_subplot(111)
            
            # Timeline span in days
            total_days = (end - start).days
            if total_days <= 0:
                total_days = 1  # Prevent division by zero
                
            # Convert dates to positions
            current_pos = (current - start).days / total_days * 100
            
            # Draw timeline
            ax.plot([0, 100], [0, 0], 'k-', lw=2)
            
            # Add start and end markers
            ax.plot(0, 0, 'ko', ms=10)
            ax.plot(100, 0, 'ko', ms=10)
            
            # Add start and end labels
            ax.text(0, -0.2, start.strftime('%d %b %Y'), ha='center', va='top')
            ax.text(100, -0.2, end.strftime('%d %b %Y'), ha='center', va='top')
            
            # Add "today" marker if within timeline
            if 0 <= current_pos <= 100:
                ax.plot(current_pos, 0, 'ro', ms=10)
                ax.text(current_pos, 0.2, 'Today', ha='center', va='bottom', color='red')
            
            # Add milestones
            for i, milestone in enumerate(milestones):
                try:
                    milestone_date = datetime.fromisoformat(milestone["date"].replace('Z', '+00:00'))
                    pos = (milestone_date - start).days / total_days * 100
                    
                    if 0 <= pos <= 100:  # Only show milestones within timeline
                        marker_height = 0.3 if i % 2 == 0 else -0.3  # Alternate positions to avoid overlap
                        
                        ax.plot(pos, 0, 'go', ms=8)
                        ax.text(pos, marker_height, milestone.get("name", f"Milestone {i+1}"), 
                               ha='center', va='center', fontsize=8,
                               bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.3'))
                except (ValueError, KeyError):
                    continue
            
            # Clean up axes
            ax.set_xlim(-5, 105)
            ax.set_ylim(-1, 1)
            ax.set_yticks([])
            ax.set_xticks([])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            plt.close(fig)
            
            # Encode image
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('ascii')
            image_data = f"data:image/png;base64,{image_base64}"
            
            return {
                "milestones": milestones,
                "start_date": start_date,
                "end_date": end_date,
                "current_date": current_date or datetime.now().isoformat(),
                "image_data": image_data
            }
            
        except Exception as e:
            logger.error(f"Error creating timeline visualization: {str(e)}")
            return {
                "milestones": milestones,
                "start_date": start_date,
                "end_date": end_date,
                "current_date": current_date or datetime.now().isoformat(),
                "error": str(e)
            }
    
    def create_probability_fan_chart(self, percentiles: Dict[str, List[float]], 
                                  time_points: List[str], target_amount: float) -> Dict[str, Any]:
        """
        Create probability fan chart showing range of possible outcomes.
        
        Args:
            percentiles (Dict[str, List[float]]): Percentile data (10, 25, 50, 75, 90)
            time_points (List[str]): Time points (dates in ISO format) 
            target_amount (float): Target amount for goal
            
        Returns:
            Dict[str, Any]: Visualization data
        """
        if not self.visualization_enabled:
            # Return data only if visualization not available
            return {
                "percentiles": percentiles,
                "time_points": time_points,
                "target_amount": target_amount,
                "formatted_target": self.format_rupees(target_amount)
            }
        
        try:
            # Parse dates
            dates = [datetime.fromisoformat(tp.replace('Z', '+00:00')) for tp in time_points]
            
            # Create figure
            fig = plt.figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            
            # Colors for different bands
            colors = ['#f4d03f', '#e67e22', '#e74c3c']  # Yellow, Orange, Red
            alphas = [0.2, 0.3, 0.4]
            
            # Plot percentile ranges
            # 50% (median) as line
            if 'p50' in percentiles:
                ax.plot(dates, percentiles['p50'], 'k-', lw=2, label='Median')
            
            # 25-75 percentile band
            if 'p25' in percentiles and 'p75' in percentiles:
                ax.fill_between(dates, percentiles['p25'], percentiles['p75'], 
                               color=colors[0], alpha=alphas[0], label='25-75 percentile')
            
            # 10-90 percentile band
            if 'p10' in percentiles and 'p90' in percentiles:
                ax.fill_between(dates, percentiles['p10'], percentiles['p90'], 
                               color=colors[1], alpha=alphas[1], label='10-90 percentile')
                
            # Target line
            ax.axhline(y=target_amount, color='r', linestyle='--', label='Target amount')
            
            # Labels and formatting
            ax.set_xlabel('Date')
            ax.set_ylabel('Amount (₹)')
            ax.legend(loc='upper left')
            
            # Format y-axis as Rupees (simplified for chart)
            def rupee_formatter(x, pos):
                if x >= 10000000:  # 1 crore
                    return f'₹{x/10000000:.1f}Cr'
                elif x >= 100000:  # 1 lakh
                    return f'₹{x/100000:.1f}L'
                elif x >= 1000:
                    return f'₹{x/1000:.0f}K'
                else:
                    return f'₹{x:.0f}'
                    
            ax.yaxis.set_major_formatter(FuncFormatter(rupee_formatter))
            
            # Format dates on x-axis
            fig.autofmt_xdate()
            
            # Grid for readability
            ax.grid(True, linestyle='--', alpha=0.3)
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            plt.close(fig)
            
            # Encode image
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('ascii')
            image_data = f"data:image/png;base64,{image_base64}"
            
            return {
                "percentiles": percentiles,
                "time_points": time_points,
                "target_amount": target_amount,
                "formatted_target": self.format_rupees(target_amount),
                "image_data": image_data
            }
            
        except Exception as e:
            logger.error(f"Error creating probability fan chart: {str(e)}")
            return {
                "percentiles": percentiles,
                "time_points": time_points,
                "target_amount": target_amount,
                "formatted_target": self.format_rupees(target_amount),
                "error": str(e)
            }
    
    def create_contribution_impact_chart(self, contribution_levels: List[float], 
                                      success_probabilities: List[float],
                                      current_level: float = None) -> Dict[str, Any]:
        """
        Create contribution impact chart showing effects of different contribution levels.
        
        Args:
            contribution_levels (List[float]): Different monthly contribution amounts
            success_probabilities (List[float]): Corresponding success probabilities
            current_level (float, optional): Current contribution level
            
        Returns:
            Dict[str, Any]: Visualization data
        """
        if not self.visualization_enabled:
            # Return data only if visualization not available
            return {
                "contributions": contribution_levels,
                "probabilities": success_probabilities,
                "current_level": current_level,
                "formatted_contributions": [self.format_rupees(c) for c in contribution_levels]
            }
        
        try:
            # Create figure
            fig = plt.figure(figsize=(10, 5))
            ax = fig.add_subplot(111)
            
            # Plot impact curve
            ax.plot(contribution_levels, success_probabilities, 'o-', color='#3498db', lw=2)
            
            # Mark the current level if provided
            if current_level is not None:
                # Find the closest contribution level and its probability
                idx = min(range(len(contribution_levels)), 
                         key=lambda i: abs(contribution_levels[i] - current_level))
                current_probability = success_probabilities[idx]
                
                ax.plot([current_level], [current_probability], 'ro', ms=10)
                ax.axvline(x=current_level, color='r', linestyle='--', alpha=0.3)
                ax.axhline(y=current_probability, color='r', linestyle='--', alpha=0.3)
                
                # Add annotation
                ax.annotate(f"Current: {self.format_rupees(current_level)}\n({current_probability:.1f}%)",
                           xy=(current_level, current_probability),
                           xytext=(10, -30), textcoords='offset points',
                           arrowprops=dict(arrowstyle='->', color='red'))
            
            # Mark 90% success probability
            if min(success_probabilities) <= 90 <= max(success_probabilities):
                # Find the required contribution for 90% success
                for i in range(len(success_probabilities)-1):
                    if success_probabilities[i] <= 90 <= success_probabilities[i+1]:
                        # Linear interpolation
                        ratio = (90 - success_probabilities[i]) / (success_probabilities[i+1] - success_probabilities[i])
                        required_contrib = contribution_levels[i] + ratio * (contribution_levels[i+1] - contribution_levels[i])
                        
                        ax.axhline(y=90, color='g', linestyle='--', alpha=0.5)
                        ax.axvline(x=required_contrib, color='g', linestyle='--', alpha=0.5)
                        ax.plot([required_contrib], [90], 'go', ms=8)
                        
                        # Add annotation
                        ax.annotate(f"90% Success: {self.format_rupees(required_contrib)}",
                                   xy=(required_contrib, 90),
                                   xytext=(10, 30), textcoords='offset points',
                                   arrowprops=dict(arrowstyle='->', color='green'))
                        break
            
            # Labels and formatting
            ax.set_xlabel('Monthly Contribution (₹)')
            ax.set_ylabel('Success Probability (%)')
            ax.set_title('Impact of Monthly Contribution on Goal Success')
            
            # Format x-axis as Rupees
            def rupee_formatter(x, pos):
                return self.format_rupees(x)
                    
            ax.xaxis.set_major_formatter(FuncFormatter(rupee_formatter))
            
            # Set y-axis to percentage range
            ax.set_ylim(0, 100)
            
            # Grid for readability
            ax.grid(True, linestyle='--', alpha=0.3)
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            plt.close(fig)
            
            # Encode image
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('ascii')
            image_data = f"data:image/png;base64,{image_base64}"
            
            return {
                "contributions": contribution_levels,
                "probabilities": success_probabilities,
                "current_level": current_level,
                "formatted_contributions": [self.format_rupees(c) for c in contribution_levels],
                "image_data": image_data
            }
            
        except Exception as e:
            logger.error(f"Error creating contribution impact chart: {str(e)}")
            return {
                "contributions": contribution_levels,
                "probabilities": success_probabilities,
                "current_level": current_level,
                "formatted_contributions": [self.format_rupees(c) for c in contribution_levels],
                "error": str(e)
            }
    
    def create_asset_allocation_chart(self, allocation: Dict[str, float]) -> Dict[str, Any]:
        """
        Create asset allocation pie charts for recommended portfolio.
        
        Args:
            allocation (Dict[str, float]): Asset allocation percentages
            
        Returns:
            Dict[str, Any]: Visualization data
        """
        if not self.visualization_enabled:
            # Return data only if visualization not available
            return allocation
        
        try:
            # Extract data
            labels = list(allocation.keys())
            sizes = list(allocation.values())
            
            # Custom colors for each asset class
            colors = {
                'equity': '#3498db',     # Blue
                'debt': '#2ecc71',       # Green
                'liquid': '#f1c40f',     # Yellow
                'gold': '#f39c12',       # Orange
                'real_estate': '#e74c3c', # Red
                'alternative': '#9b59b6'  # Purple
            }
            
            # Map colors
            pie_colors = [colors.get(asset.lower(), '#95a5a6') for asset in labels]
            
            # Create figure
            fig = plt.figure(figsize=(8, 6))
            ax = fig.add_subplot(111)
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                sizes, 
                labels=None,
                autopct='%1.1f%%',
                startangle=90,
                colors=pie_colors,
                wedgeprops={'edgecolor': 'w', 'linewidth': 1}
            )
            
            # Customize text
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            # Add legend
            formatted_labels = [f"{label.title()} ({size:.1f}%)" for label, size in zip(labels, sizes)]
            ax.legend(wedges, formatted_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.set_aspect('equal')
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            plt.close(fig)
            
            # Encode image
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('ascii')
            image_data = f"data:image/png;base64,{image_base64}"
            
            return {
                **allocation,
                "image_data": image_data
            }
            
        except Exception as e:
            logger.error(f"Error creating asset allocation chart: {str(e)}")
            return {
                **allocation,
                "error": str(e)
            }
    
    def create_adjustment_comparison_chart(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create comparison charts for different adjustment scenarios.
        
        Args:
            scenarios (List[Dict[str, Any]]): List of scenarios with their impacts
            
        Returns:
            Dict[str, Any]: Visualization data
        """
        if not self.visualization_enabled or not scenarios:
            # Return data only if visualization not available
            return {"scenarios": scenarios}
        
        try:
            # Extract data
            names = [s.get("title", f"Scenario {i+1}") for i, s in enumerate(scenarios)]
            original_prob = scenarios[0].get("impact", {}).get("old_probability", 0)
            new_probs = [s.get("impact", {}).get("new_probability", 0) for s in scenarios]
            improvements = [s.get("impact", {}).get("improvement", 0) for s in scenarios]
            
            # Create figure
            fig = plt.figure(figsize=(12, 6))
            
            # Create comparison chart
            ax1 = fig.add_subplot(121)
            bars = ax1.bar(names, new_probs, color='#3498db')
            
            # Add baseline
            ax1.axhline(y=original_prob, color='r', linestyle='--', label=f"Current ({original_prob:.1f}%)")
            
            # Highlight the best option
            best_idx = new_probs.index(max(new_probs))
            bars[best_idx].set_color('#2ecc71')
            
            # Labels and formatting
            ax1.set_xlabel('Adjustment Options')
            ax1.set_ylabel('Success Probability (%)')
            ax1.set_title('Impact on Success Probability')
            ax1.legend()
            
            # Set y-axis to percentage range with padding
            max_prob = max(new_probs + [original_prob])
            ax1.set_ylim(0, min(100, max_prob * 1.1))
            
            # Rotate x labels for readability
            plt.setp(ax1.get_xticklabels(), rotation=30, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{height:.1f}%', ha='center', va='bottom')
            
            # Create improvement chart
            ax2 = fig.add_subplot(122)
            bars2 = ax2.bar(names, improvements, color='#9b59b6')
            
            # Highlight the best option
            best_idx = improvements.index(max(improvements))
            bars2[best_idx].set_color('#2ecc71')
            
            # Labels and formatting
            ax2.set_xlabel('Adjustment Options')
            ax2.set_ylabel('Improvement (%)')
            ax2.set_title('Improvement in Success Probability')
            
            # Rotate x labels for readability
            plt.setp(ax2.get_xticklabels(), rotation=30, ha='right')
            
            # Add value labels on bars
            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'+{height:.1f}%', ha='center', va='bottom')
            
            # Adjust layout
            plt.tight_layout()
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            plt.close(fig)
            
            # Encode image
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('ascii')
            image_data = f"data:image/png;base64,{image_base64}"
            
            return {
                "scenarios": scenarios,
                "best_option": names[best_idx],
                "max_improvement": improvements[best_idx],
                "image_data": image_data
            }
            
        except Exception as e:
            logger.error(f"Error creating adjustment comparison chart: {str(e)}")
            return {
                "scenarios": scenarios,
                "error": str(e)
            }
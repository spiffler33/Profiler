import logging
import math
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .base_strategy import FundingStrategyGenerator
from .rebalancing_strategy import RebalancingStrategy

logger = logging.getLogger(__name__)

class TaxOptimizationStrategy(FundingStrategyGenerator):
    """
    Specialized funding strategy for tax optimization goals with 
    India-specific tax benefits and structured tax-saving approaches.
    """
    
    def __init__(self):
        """Initialize with tax optimization specific parameters"""
        super().__init__()
        
        # Optimizer, constraints, and compound strategy objects will be lazy initialized
        self.optimizer = None
        self.constraints = None
        self.compound_strategy = None
        
        # Additional tax optimization specific parameters
        self.tax_params = {
            "tax_sections": {
                "80c": {
                    "max_deduction": 150000,
                    "instruments": ["PPF", "ELSS", "NSC", "tax-saving FD", "life insurance premium"]
                },
                "80ccd": {
                    "max_deduction": 50000,  # Additional NPS contribution deduction
                    "instruments": ["NPS Tier-1 account"]
                },
                "80d": {
                    "max_deduction": {
                        "self_family": 25000,  # Basic health insurance for self & family
                        "parents": 25000,      # Parents health insurance
                        "senior_citizen": 50000  # Increased limit for senior citizens
                    },
                    "instruments": ["health insurance premium", "preventive health checkup"]
                },
                "80g": {
                    "max_deduction": "100% or 50% depending on organization",
                    "instruments": ["donations to approved organizations"]
                },
                "80tta": {
                    "max_deduction": 10000,  # Interest from savings account
                    "instruments": ["savings account interest"]
                },
                "80e": {
                    "max_deduction": "No limit on interest payment",
                    "instruments": ["education loan interest"]
                }
            },
            "investment_options": {
                "low_risk": {
                    "instruments": ["PPF", "NSC", "tax-saving FD", "SCSS"],
                    "lock_in": "5-15 years",
                    "expected_return": "7-8%"
                },
                "medium_risk": {
                    "instruments": ["ELSS", "NPS", "ULIP"],
                    "lock_in": "3-5 years (except NPS)",
                    "expected_return": "10-12%"
                },
                "high_risk": {
                    "instruments": ["ELSS (equity focused)"],
                    "lock_in": "3 years",
                    "expected_return": "12-15%"
                }
            },
            "tax_slabs": {
                "old_regime": {
                    "0-2.5L": "0%",
                    "2.5L-5L": "5%",
                    "5L-10L": "20%",
                    "above_10L": "30%"
                },
                "new_regime": {
                    "0-3L": "0%",
                    "3L-6L": "5%",
                    "6L-9L": "10%",
                    "9L-12L": "15%",
                    "12L-15L": "20%",
                    "above_15L": "30%"
                }
            }
        }
        
        # Tax optimization parameters
        self.tax_optimization_params = {
            'tax_efficiency_weight': 0.60,      # Weight for tax efficiency optimization
            'liquidity_weight': 0.15,           # Weight for maintaining liquidity
            'return_weight': 0.25,              # Weight for returns maximization
            'diversification_threshold': 0.40,  # Maximum allocation to single instrument
            'minimum_investment_size': 5000,    # Minimum practical investment size
            'regime_comparison_factor': 0.90,   # Threshold for recommending new tax regime
            'section_priority': ["80C", "80CCD", "80D", "80G", "80TTA", "80E"]  # Priority order
        }
        
        # Load tax optimization specific parameters
        self._load_tax_optimization_parameters()
    
    def _initialize_optimizer(self):
        """Initialize the strategy optimizer with lazy loading pattern"""
        if not hasattr(self, 'optimizer') or self.optimizer is None:
            # Initialize the optimizer with tax-specific optimization parameters
            super()._initialize_optimizer()
            
            # Set tax-specific optimization parameters if needed
            if hasattr(self.optimizer, 'set_parameters'):
                self.optimizer.set_parameters({
                    'tax_efficiency_weight': self.tax_optimization_params['tax_efficiency_weight'],
                    'liquidity_weight': self.tax_optimization_params['liquidity_weight'],
                    'return_weight': self.tax_optimization_params['return_weight']
                })
    
    def _load_tax_optimization_parameters(self):
        """Load tax optimization specific parameters from parameter service"""
        if hasattr(self, 'parameter_service') and self.parameter_service:
            # Load parameters from parameter service with appropriate defaults
            self.tax_optimization_params['tax_efficiency_weight'] = self.get_parameter(
                'tax_optimization.weights.tax_efficiency', 0.60)
            self.tax_optimization_params['liquidity_weight'] = self.get_parameter(
                'tax_optimization.weights.liquidity', 0.15)
            self.tax_optimization_params['return_weight'] = self.get_parameter(
                'tax_optimization.weights.return', 0.25)
            self.tax_optimization_params['diversification_threshold'] = self.get_parameter(
                'tax_optimization.diversification_threshold', 0.40)
            self.tax_optimization_params['minimum_investment_size'] = self.get_parameter(
                'tax_optimization.minimum_investment', 5000)
            
            # Update tax section limits from parameters if available
            self.tax_params['tax_sections']['80c']['max_deduction'] = self.get_parameter(
                'tax.sections.80c.limit', 150000)
            self.tax_params['tax_sections']['80ccd']['max_deduction'] = self.get_parameter(
                'tax.sections.80ccd.limit', 50000)
            self.tax_params['tax_sections']['80d']['max_deduction']['self_family'] = self.get_parameter(
                'tax.sections.80d.self_family.limit', 25000)
            self.tax_params['tax_sections']['80d']['max_deduction']['parents'] = self.get_parameter(
                'tax.sections.80d.parents.limit', 25000)
            self.tax_params['tax_sections']['80d']['max_deduction']['senior_citizen'] = self.get_parameter(
                'tax.sections.80d.senior_citizen.limit', 50000)
            self.tax_params['tax_sections']['80tta']['max_deduction'] = self.get_parameter(
                'tax.sections.80tta.limit', 10000)
    
    def _extract_taxable_income(self, profile: Dict[str, Any]) -> float:
        """
        Extract taxable income from profile for tax optimization.
        
        Args:
            profile: User profile with income details
            
        Returns:
            float: Taxable income amount
        """
        # Default to monthly income * 12 if taxable income not explicitly provided
        if isinstance(profile, dict):
            # Check if taxable income is directly provided
            if 'taxable_income' in profile:
                return float(profile['taxable_income'])
                
            # Check for annual income
            if 'annual_income' in profile:
                return float(profile['annual_income'])
                
            # Get monthly income and convert to annual
            if 'monthly_income' in profile:
                return float(profile['monthly_income']) * 12
                
            # Check for income details structure
            if 'income' in profile and isinstance(profile['income'], dict):
                if 'taxable_amount' in profile['income']:
                    return float(profile['income']['taxable_amount'])
                if 'annual' in profile['income']:
                    return float(profile['income']['annual'])
                if 'monthly' in profile['income']:
                    return float(profile['income']['monthly']) * 12
        
        # Fallback to a default value if no income info found
        logger.warning(f"No income information found in profile {profile.get('id', 'unknown')}, using default")
        return 600000  # Default assumption: ₹6 lakhs taxable income
    
    def _get_tax_regime(self, profile: Dict[str, Any]) -> str:
        """
        Determine the applicable tax regime (old or new) for the user.
        
        Args:
            profile: User profile with tax preferences
            
        Returns:
            str: 'old_regime' or 'new_regime'
        """
        if isinstance(profile, dict):
            # Check if tax regime preference is explicitly provided
            if 'tax_regime' in profile:
                regime = profile['tax_regime']
                if regime in ['old_regime', 'new_regime']:
                    return regime
                    
            # Check in tax_preferences if available
            if 'tax_preferences' in profile and isinstance(profile['tax_preferences'], dict):
                if 'regime' in profile['tax_preferences']:
                    regime = profile['tax_preferences']['regime']
                    if regime in ['old_regime', 'new_regime']:
                        return regime
        
        # Default to old regime if not specified (since it allows deductions)
        return 'old_regime'
    
    def generate_strategy(self, goal, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a tax optimization funding strategy for the goal.
        
        Args:
            goal: The tax optimization goal
            profile: User profile
            
        Returns:
            dict: Tax optimization funding strategy
        """
        # Extract user_id for parameter access
        user_id = profile.get('user_id') if isinstance(profile, dict) else None
        
        # Extract tax-relevant information
        taxable_income = self._extract_taxable_income(profile)
        tax_regime = self._get_tax_regime(profile)
        
        # Extract goal details
        if isinstance(goal, dict):
            target_amount = goal.get('target_amount', 0)
            timeframe = goal.get('timeframe', '')
            current_amount = goal.get('current_amount', 0)
        else:
            target_amount = getattr(goal, 'target_amount', 0)
            timeframe = getattr(goal, 'timeframe', '')
            current_amount = getattr(goal, 'current_amount', 0)
        
        # Calculate remaining amount to invest
        remaining_amount = target_amount - current_amount
        
        # If already at or beyond target, just maintain current level
        if remaining_amount <= 0:
            return {
                "strategy_type": "tax_optimization",
                "tax_regime": tax_regime,
                "recommendation": "Target amount already achieved. Maintain current tax-saving investments.",
                "taxable_income": taxable_income,
                "investment_allocation": {},
                "expected_tax_savings": 0,
                "updated_at": datetime.now().isoformat()
            }
        
        # Create allocation plan based on tax regime
        if tax_regime == 'old_regime':
            # Under old regime, focus on maximizing deductions
            plan = self._generate_old_regime_plan(taxable_income, remaining_amount, profile, user_id)
        else:
            # Under new regime, focus on investments with good post-tax returns as deductions aren't available
            plan = self._generate_new_regime_plan(taxable_income, remaining_amount, profile, user_id)
        
        # Calculate expected tax savings
        expected_savings = self._calculate_tax_savings(taxable_income, plan['investment_allocation'], tax_regime)
        
        # Build the complete strategy
        strategy = {
            "strategy_type": "tax_optimization",
            "tax_regime": tax_regime,
            "recommendation": plan['recommendation'],
            "taxable_income": taxable_income,
            "investment_allocation": plan['investment_allocation'],
            "expected_tax_savings": expected_savings,
            "monthly_investment": plan.get('monthly_investment', 0),
            "regime_comparison": self._compare_tax_regimes(taxable_income, plan['investment_allocation']),
            "updated_at": datetime.now().isoformat()
        }
        
        return strategy
    
    def _generate_old_regime_plan(self, taxable_income: float, target_amount: float, 
                                profile: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate investment plan for old tax regime with deductions.
        
        Args:
            taxable_income: Annual taxable income
            target_amount: Target amount to invest for tax savings
            profile: User profile with preferences
            user_id: User ID for parameter access
            
        Returns:
            dict: Investment plan with allocations
        """
        # Get maximum deduction limits
        section_80c_limit = self.tax_params['tax_sections']['80c']['max_deduction']
        section_80ccd_limit = self.tax_params['tax_sections']['80ccd']['max_deduction']
        section_80d_limit_self = self.tax_params['tax_sections']['80d']['max_deduction']['self_family']
        
        # Check user age for senior citizen benefits
        is_senior = self._is_senior_citizen(profile)
        if is_senior:
            section_80d_limit_self = self.tax_params['tax_sections']['80d']['max_deduction']['senior_citizen']
        
        # Determine risk preference
        risk_profile = self._get_risk_profile(profile)
        
        # Initialize allocation
        allocation = {}
        remaining = target_amount
        monthly_investment = 0
        
        # Allocate to 80C section (maximum priority)
        if remaining > 0:
            allocation_80c = min(section_80c_limit, remaining)
            remaining -= allocation_80c
            
            # Allocate within 80C based on risk profile
            if risk_profile == 'high':
                allocation['ELSS'] = allocation_80c  # Equity-linked savings scheme
            elif risk_profile == 'medium':
                allocation['ELSS'] = allocation_80c * 0.6
                allocation['PPF'] = allocation_80c * 0.4  # Public Provident Fund
            else:  # low risk
                allocation['PPF'] = allocation_80c * 0.5
                allocation['NSC'] = allocation_80c * 0.3  # National Savings Certificate
                allocation['Tax-saving FD'] = allocation_80c * 0.2  # Tax-saving fixed deposits
        
        # Allocate to 80CCD section (NPS - additional deduction)
        if remaining > 0:
            allocation_80ccd = min(section_80ccd_limit, remaining)
            remaining -= allocation_80ccd
            
            allocation['NPS'] = allocation_80ccd  # National Pension System
        
        # Allocate to 80D section (health insurance)
        if remaining > 0:
            allocation_80d = min(section_80d_limit_self, remaining)
            remaining -= allocation_80d
            
            allocation['Health Insurance'] = allocation_80d
        
        # Calculate monthly investment amount (divide by 12 for annual amount)
        total_allocation = sum(allocation.values())
        monthly_investment = total_allocation / 12
        
        # Generate recommendation text
        if total_allocation >= (section_80c_limit + section_80ccd_limit):
            recommendation = (
                f"Comprehensive tax optimization plan utilizing full Section 80C (₹{section_80c_limit:,.0f}) "
                f"and 80CCD (₹{section_80ccd_limit:,.0f}) deductions. "
                f"Monthly investment: ₹{monthly_investment:,.0f}"
            )
        else:
            recommendation = (
                f"Tax optimization plan utilizing ₹{total_allocation:,.0f} in tax-saving instruments. "
                f"Monthly investment: ₹{monthly_investment:,.0f}"
            )
        
        return {
            "investment_allocation": allocation,
            "recommendation": recommendation,
            "monthly_investment": monthly_investment
        }
    
    def _generate_new_regime_plan(self, taxable_income: float, target_amount: float, 
                                profile: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate investment plan for new tax regime (focus on returns rather than deductions).
        
        Args:
            taxable_income: Annual taxable income
            target_amount: Target amount to invest for tax savings
            profile: User profile with preferences
            user_id: User ID for parameter access
            
        Returns:
            dict: Investment plan with allocations
        """
        # Determine risk preference
        risk_profile = self._get_risk_profile(profile)
        
        # Initialize allocation
        allocation = {}
        monthly_investment = 0
        
        # Under new regime, focus on returns rather than tax benefits
        # Since deductions aren't available, allocate based on expected returns
        if risk_profile == 'high':
            allocation['Equity Mutual Funds'] = target_amount * 0.7
            allocation['NPS'] = target_amount * 0.3  # Still good for retirement even without 80CCD benefit
        elif risk_profile == 'medium':
            allocation['Equity Mutual Funds'] = target_amount * 0.5
            allocation['NPS'] = target_amount * 0.3
            allocation['Debt Mutual Funds'] = target_amount * 0.2
        else:  # low risk
            allocation['NPS'] = target_amount * 0.4
            allocation['Debt Mutual Funds'] = target_amount * 0.4
            allocation['Fixed Deposits'] = target_amount * 0.2
        
        # Calculate monthly investment amount
        total_allocation = sum(allocation.values())
        monthly_investment = total_allocation / 12
        
        # Generate recommendation text
        recommendation = (
            f"Under new tax regime, focus on investment returns rather than tax deductions. "
            f"Monthly investment: ₹{monthly_investment:,.0f}. "
            f"Consider switching to old regime if deductions exceed ₹50,000."
        )
        
        return {
            "investment_allocation": allocation,
            "recommendation": recommendation,
            "monthly_investment": monthly_investment
        }
    
    def _calculate_tax_savings(self, taxable_income: float, allocation: Dict[str, float], 
                             tax_regime: str) -> float:
        """
        Calculate expected tax savings from investments.
        
        Args:
            taxable_income: Annual taxable income
            allocation: Investment allocation
            tax_regime: Tax regime ('old_regime' or 'new_regime')
            
        Returns:
            float: Expected tax savings amount
        """
        if tax_regime == 'new_regime':
            # No deductions available in new regime
            return 0
        
        # Calculate total deduction amount
        total_deduction = sum(allocation.values())
        
        # Determine applicable tax rate based on taxable income
        tax_rate = 0
        if taxable_income > 1000000:  # > 10 lakhs
            tax_rate = 0.30
        elif taxable_income > 500000:  # 5-10 lakhs
            tax_rate = 0.20
        elif taxable_income > 250000:  # 2.5-5 lakhs
            tax_rate = 0.05
            
        # Apply education cess (4%)
        effective_tax_rate = tax_rate * 1.04
        
        # Calculate tax savings
        tax_savings = min(total_deduction, taxable_income - 250000) * effective_tax_rate
        
        # Ensure non-negative
        return max(0, tax_savings)
    
    def _compare_tax_regimes(self, taxable_income: float, allocation: Dict[str, float]) -> Dict[str, Any]:
        """
        Compare tax liability under old and new regimes.
        
        Args:
            taxable_income: Annual taxable income
            allocation: Investment allocation
            
        Returns:
            dict: Comparison of tax regimes
        """
        # Calculate total deduction amount
        total_deduction = sum(allocation.values())
        
        # Calculate tax under old regime
        old_regime_taxable = max(0, taxable_income - total_deduction)
        old_regime_tax = self._calculate_tax(old_regime_taxable, 'old_regime')
        
        # Calculate tax under new regime
        new_regime_tax = self._calculate_tax(taxable_income, 'new_regime')
        
        # Determine difference and recommended regime
        difference = old_regime_tax - new_regime_tax
        recommended_regime = 'new_regime' if difference > 0 else 'old_regime'
        
        return {
            "old_regime_tax": old_regime_tax,
            "new_regime_tax": new_regime_tax,
            "difference": abs(difference),
            "recommended_regime": recommended_regime,
            "savings_with_recommended": abs(difference)
        }
    
    def _calculate_tax(self, taxable_income: float, regime: str) -> float:
        """
        Calculate tax liability for a given income and tax regime.
        
        Args:
            taxable_income: Annual taxable income
            regime: Tax regime ('old_regime' or 'new_regime')
            
        Returns:
            float: Tax amount
        """
        tax = 0
        
        if regime == 'old_regime':
            # Old regime slabs
            if taxable_income > 1000000:  # > 10 lakhs
                tax += (taxable_income - 1000000) * 0.30
                taxable_income = 1000000
                
            if taxable_income > 500000:  # 5-10 lakhs
                tax += (taxable_income - 500000) * 0.20
                taxable_income = 500000
                
            if taxable_income > 250000:  # 2.5-5 lakhs
                tax += (taxable_income - 250000) * 0.05
        else:
            # New regime slabs (simplified for calculation)
            if taxable_income > 1500000:  # > 15 lakhs
                tax += (taxable_income - 1500000) * 0.30
                taxable_income = 1500000
                
            if taxable_income > 1200000:  # 12-15 lakhs
                tax += (taxable_income - 1200000) * 0.20
                taxable_income = 1200000
                
            if taxable_income > 900000:  # 9-12 lakhs
                tax += (taxable_income - 900000) * 0.15
                taxable_income = 900000
                
            if taxable_income > 600000:  # 6-9 lakhs
                tax += (taxable_income - 600000) * 0.10
                taxable_income = 600000
                
            if taxable_income > 300000:  # 3-6 lakhs
                tax += (taxable_income - 300000) * 0.05
        
        # Add education cess (4%)
        tax = tax * 1.04
        
        return tax
    
    def _is_senior_citizen(self, profile: Dict[str, Any]) -> bool:
        """
        Determine if the user is a senior citizen (age ≥ 60).
        
        Args:
            profile: User profile with age information
            
        Returns:
            bool: True if senior citizen, False otherwise
        """
        if isinstance(profile, dict):
            # Check if age is directly provided
            if 'age' in profile:
                try:
                    return int(profile['age']) >= 60
                except (ValueError, TypeError):
                    pass
                    
            # Check for date of birth
            if 'date_of_birth' in profile:
                try:
                    dob = datetime.fromisoformat(str(profile['date_of_birth']).replace('Z', '+00:00'))
                    today = datetime.now()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    return age >= 60
                except (ValueError, TypeError):
                    pass
        
        # Default to not senior if no valid age info
        return False
    
    def _get_risk_profile(self, profile: Dict[str, Any]) -> str:
        """
        Determine user's risk profile (high, medium, low).
        
        Args:
            profile: User profile with risk preferences
            
        Returns:
            str: Risk profile ('high', 'medium', or 'low')
        """
        if isinstance(profile, dict):
            # Check if risk profile is directly provided
            if 'risk_profile' in profile:
                risk = profile['risk_profile']
                if risk in ['high', 'medium', 'low']:
                    return risk
                    
            # Check in investment_preferences if available
            if 'investment_preferences' in profile and isinstance(profile['investment_preferences'], dict):
                if 'risk_tolerance' in profile['investment_preferences']:
                    risk = profile['investment_preferences']['risk_tolerance']
                    if risk in ['high', 'medium', 'low']:
                        return risk
                    if risk in ['aggressive', 'very_aggressive']:
                        return 'high'
                    if risk in ['moderate', 'balanced']:
                        return 'medium'
                    if risk in ['conservative', 'very_conservative']:
                        return 'low'
        
        # Default to medium risk if not specified
        return 'medium'
    
    def calculate_monthly_investment(self, goal, profile: Dict[str, Any]) -> float:
        """
        Calculate the recommended monthly investment amount for tax optimization goal.
        
        Args:
            goal: The tax optimization goal
            profile: User profile
            
        Returns:
            float: Monthly investment amount
        """
        # Extract key information
        if isinstance(goal, dict):
            target_amount = goal.get('target_amount', 0)
            timeframe = goal.get('timeframe', '')
            current_amount = goal.get('current_amount', 0)
        else:
            target_amount = getattr(goal, 'target_amount', 0)
            timeframe = getattr(goal, 'timeframe', '')
            current_amount = getattr(goal, 'current_amount', 0)
        
        # Default to annual investment divided by 12 months
        annual_target = target_amount - current_amount
        if annual_target <= 0:
            return 0  # Already reached target
            
        # For tax optimization, usually align with financial year
        return annual_target / 12
    
    def get_recommended_instruments(self, goal, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get recommended investment instruments for tax optimization.
        
        Args:
            goal: The tax optimization goal
            profile: User profile
            
        Returns:
            list: List of recommended instruments with details
        """
        strategy = self.generate_strategy(goal, profile)
        allocation = strategy.get('investment_allocation', {})
        
        recommendations = []
        tax_regime = strategy.get('tax_regime', 'old_regime')
        
        for instrument, amount in allocation.items():
            instrument_details = {
                "name": instrument,
                "amount": amount,
                "percentage": (amount / sum(allocation.values()) * 100) if allocation else 0
            }
            
            # Add tax benefit information for old regime
            if tax_regime == 'old_regime':
                if instrument in ['ELSS', 'PPF', 'NSC', 'Tax-saving FD']:
                    instrument_details["tax_section"] = "80C"
                elif instrument == 'NPS':
                    instrument_details["tax_section"] = "80CCD"
                elif instrument == 'Health Insurance':
                    instrument_details["tax_section"] = "80D"
            
            recommendations.append(instrument_details)
        
        return recommendations
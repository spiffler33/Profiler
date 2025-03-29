import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_calculator import GoalCalculator

logger = logging.getLogger(__name__)

class TaxOptimizationCalculator(GoalCalculator):
    """Calculator for tax optimization goals focusing on Indian tax sections"""
    
    def calculate_amount_needed(self, goal, profile: Dict[str, Any]) -> float:
        """
        Calculate the amount needed for tax optimization goal.
        
        Args:
            goal: The tax optimization goal
            profile: User profile
            
        Returns:
            float: Calculated amount needed for tax optimization
        """
        # Extract user_id for parameter access
        user_id = profile.get('user_id') if isinstance(profile, dict) else None
        
        # If goal already has target amount, use that
        if isinstance(goal, dict):
            if goal.get('target_amount', 0) > 0:
                return goal['target_amount']
        elif hasattr(goal, 'target_amount') and goal.target_amount > 0:
            return goal.target_amount
        
        # Calculate based on taxable income and maximum possible deductions
        taxable_income = self._extract_taxable_income(profile)
        tax_regime = self._get_tax_regime(profile)
        
        # For new tax regime, optimization focus may be different
        # since deductions aren't available to reduce tax liability
        if tax_regime == 'new_regime':
            # Still recommend investing, but with focus on returns rather than tax savings
            recommended_amount = self._calculate_new_regime_investment(taxable_income, profile, user_id)
        else:
            # Calculate optimal investment amount for maximum tax benefits
            recommended_amount = self._calculate_old_regime_investment(taxable_income, profile, user_id)
        
        return recommended_amount
    
    def _extract_taxable_income(self, profile: Dict[str, Any]) -> float:
        """
        Extract taxable income from profile for tax optimization calculation.
        
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
    
    def _calculate_old_regime_investment(self, taxable_income: float, profile: Dict[str, Any], 
                                        user_id: Optional[str] = None) -> float:
        """
        Calculate optimal investment amount for old tax regime with deductions.
        
        Args:
            taxable_income: Annual taxable income
            profile: User profile with tax history
            user_id: User ID for parameter access
            
        Returns:
            float: Recommended investment amount
        """
        # Get deduction limits from parameters
        section_80c_limit = self.get_parameter('tax.sections.80c.limit', 150000, user_id)
        section_80ccd_limit = self.get_parameter('tax.sections.80ccd.limit', 50000, user_id)
        section_80d_limit_self = self.get_parameter('tax.sections.80d.self_family.limit', 25000, user_id)
        section_80d_limit_parents = self.get_parameter('tax.sections.80d.parents.limit', 25000, user_id)
        
        # Check for existing investments from profile
        existing_80c = self._get_existing_investment(profile, 'section_80c')
        existing_80ccd = self._get_existing_investment(profile, 'section_80ccd')
        existing_80d = self._get_existing_investment(profile, 'section_80d')
        
        # Calculate remaining deduction capacity
        remaining_80c = max(0, section_80c_limit - existing_80c)
        remaining_80ccd = max(0, section_80ccd_limit - existing_80ccd)
        remaining_80d = max(0, section_80d_limit_self - existing_80d)
        
        # For parents' health insurance if user has parents
        if self._has_dependent_parents(profile):
            # Adjust for senior citizen parents if applicable
            if self._has_senior_citizen_parents(profile):
                section_80d_limit_parents = self.get_parameter('tax.sections.80d.senior_citizen.limit', 50000, user_id)
                
            existing_80d_parents = self._get_existing_investment(profile, 'section_80d_parents')
            remaining_80d_parents = max(0, section_80d_limit_parents - existing_80d_parents)
            
            # Add to total 80D remaining
            remaining_80d += remaining_80d_parents
        
        # Calculate total available deductions
        total_available_deduction = remaining_80c + remaining_80ccd + remaining_80d
        
        # Determine recommended amount based on tax bracket
        if taxable_income <= 250000:
            # Below taxable income, minimal benefit
            recommended = self.get_parameter('tax.optimization.min_investment', 25000, user_id)
        elif taxable_income <= 500000:
            # 5% tax bracket
            recommended = min(total_available_deduction, 
                           taxable_income - 250000 + self.get_parameter('tax.optimization.buffer', 25000, user_id))
        elif taxable_income <= 1000000:
            # 20% tax bracket - higher incentive to optimize
            recommended = min(total_available_deduction, 
                           max(section_80c_limit + section_80ccd_limit, 
                              taxable_income * self.get_parameter('tax.optimization.high_bracket_rate', 0.15, user_id)))
        else:
            # 30% tax bracket - maximum incentive to optimize
            recommended = total_available_deduction  # Use all available deduction capacity
        
        # Ensure result is reasonable
        return max(self.get_parameter('tax.optimization.min_investment', 25000, user_id), 
                  min(total_available_deduction, recommended))
    
    def _calculate_new_regime_investment(self, taxable_income: float, profile: Dict[str, Any], 
                                       user_id: Optional[str] = None) -> float:
        """
        Calculate optimal investment amount for new tax regime (no deductions).
        
        Args:
            taxable_income: Annual taxable income
            profile: User profile
            user_id: User ID for parameter access
            
        Returns:
            float: Recommended investment amount
        """
        # Under new regime, investment is more about financial goals than tax optimization
        # Focus on creating a reasonable savings amount
        
        # Calculate as percentage of taxable income
        if taxable_income <= 500000:
            # Lower income - save modest amount
            rate = self.get_parameter('tax.new_regime.low_income_savings_rate', 0.05, user_id)
        elif taxable_income <= 1000000:
            # Middle income - save moderate amount
            rate = self.get_parameter('tax.new_regime.mid_income_savings_rate', 0.10, user_id)
        else:
            # Higher income - save significant amount
            rate = self.get_parameter('tax.new_regime.high_income_savings_rate', 0.15, user_id)
        
        recommended = taxable_income * rate
        
        # Ensure result is reasonable
        return max(self.get_parameter('tax.optimization.min_investment', 25000, user_id), 
                  min(taxable_income * 0.30, recommended))  # Cap at 30% of income
    
    def _get_existing_investment(self, profile: Dict[str, Any], section: str) -> float:
        """
        Get existing investment amount for a tax section from profile.
        
        Args:
            profile: User profile with tax history
            section: Tax section identifier
            
        Returns:
            float: Existing investment amount
        """
        if isinstance(profile, dict):
            # Check in tax_investments if available
            if 'tax_investments' in profile and isinstance(profile['tax_investments'], dict):
                if section in profile['tax_investments']:
                    try:
                        return float(profile['tax_investments'][section])
                    except (ValueError, TypeError):
                        pass
            
            # Check in financial history
            if 'financial_history' in profile and isinstance(profile['financial_history'], dict):
                if 'tax_investments' in profile['financial_history']:
                    investments = profile['financial_history']['tax_investments']
                    if isinstance(investments, dict) and section in investments:
                        try:
                            return float(investments[section])
                        except (ValueError, TypeError):
                            pass
        
        # Default to 0 if not found
        return 0
    
    def _has_dependent_parents(self, profile: Dict[str, Any]) -> bool:
        """
        Determine if user has dependent parents for health insurance calculation.
        
        Args:
            profile: User profile with family details
            
        Returns:
            bool: True if dependent parents exist, False otherwise
        """
        if isinstance(profile, dict):
            # Check direct flag
            if 'has_dependent_parents' in profile:
                return bool(profile['has_dependent_parents'])
            
            # Check in family details
            if 'family' in profile and isinstance(profile['family'], dict):
                if 'dependent_parents' in profile['family']:
                    return bool(profile['family']['dependent_parents'])
                    
                # Check for parents in dependents list
                if 'dependents' in profile['family'] and isinstance(profile['family']['dependents'], list):
                    for dependent in profile['family']['dependents']:
                        if isinstance(dependent, dict) and dependent.get('relationship') in ['father', 'mother', 'parent']:
                            return True
        
        # Default to False if not specified
        return False
    
    def _has_senior_citizen_parents(self, profile: Dict[str, Any]) -> bool:
        """
        Determine if user has senior citizen parents (age ≥ 60).
        
        Args:
            profile: User profile with family details
            
        Returns:
            bool: True if senior citizen parents exist, False otherwise
        """
        if isinstance(profile, dict) and self._has_dependent_parents(profile):
            # Check direct flag
            if 'has_senior_citizen_parents' in profile:
                return bool(profile['has_senior_citizen_parents'])
            
            # Check in family details
            if 'family' in profile and isinstance(profile['family'], dict):
                if 'senior_citizen_parents' in profile['family']:
                    return bool(profile['family']['senior_citizen_parents'])
                    
                # Check parents' age in dependents list
                if 'dependents' in profile['family'] and isinstance(profile['family']['dependents'], list):
                    for dependent in profile['family']['dependents']:
                        if isinstance(dependent, dict) and dependent.get('relationship') in ['father', 'mother', 'parent']:
                            if 'age' in dependent and dependent['age'] >= 60:
                                return True
                            
                            # Check DOB if age not directly provided
                            if 'date_of_birth' in dependent:
                                try:
                                    dob = datetime.fromisoformat(str(dependent['date_of_birth']).replace('Z', '+00:00'))
                                    today = datetime.now()
                                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                                    if age >= 60:
                                        return True
                                except (ValueError, TypeError):
                                    pass
        
        # Default to False if not specified or no parents
        return False
    
    def calculate_monthly_sip(self, goal, profile: Dict[str, Any]) -> float:
        """
        Calculate required monthly Systematic Investment Plan (SIP) amount for tax optimization.
        
        Args:
            goal: The tax optimization goal
            profile: User profile
            
        Returns:
            float: Monthly SIP amount
        """
        user_id = profile.get('user_id') if isinstance(profile, dict) else None
        
        # For tax optimization, usually divided evenly throughout the year
        # Default to total amount divided by 12 to spread across financial year
        if isinstance(goal, dict):
            target_amount = goal.get('target_amount', 0)
            current_amount = goal.get('current_amount', 0)
        else:
            target_amount = getattr(goal, 'target_amount', 0)
            current_amount = getattr(goal, 'current_amount', 0)
        
        remaining = target_amount - current_amount
        if remaining <= 0:
            return 0  # Already reached target
        
        # Calculate months remaining in current financial year
        current_date = datetime.now()
        fy_end = datetime(current_date.year, 3, 31)
        if current_date > fy_end:
            fy_end = datetime(current_date.year + 1, 3, 31)
        
        months_remaining = (fy_end.year - current_date.year) * 12 + fy_end.month - current_date.month
        months_remaining = max(1, months_remaining)  # At least 1 month
        
        # Adjust for preferred start month if specified
        preferred_start = None
        if isinstance(profile, dict) and 'tax_preferences' in profile:
            tax_prefs = profile['tax_preferences']
            if isinstance(tax_prefs, dict) and 'preferred_investment_month' in tax_prefs:
                try:
                    preferred_start = int(tax_prefs['preferred_investment_month'])
                except (ValueError, TypeError):
                    pass
        
        # Apply adjustment based on preferred start month
        if preferred_start and 1 <= preferred_start <= 12:
            current_month = current_date.month
            
            if preferred_start > current_month:
                # Preferred month is later this year
                months_remaining -= (preferred_start - current_month)
            elif preferred_start < current_month:
                # Preferred month already passed this year, adjust for next occurrence
                months_remaining = (months_remaining - (current_month - preferred_start)) % 12
            
            # Ensure at least 1 month
            months_remaining = max(1, months_remaining)
        
        # Calculate SIP amount based on months remaining
        monthly_sip = remaining / months_remaining
        
        # Apply minimum SIP amount parameter
        min_sip = self.get_parameter('tax.optimization.min_monthly_sip', 2000, user_id)
        return max(min_sip, monthly_sip)
    
    def get_tax_section_breakdown(self, goal, profile: Dict[str, Any]) -> Dict[str, float]:
        """
        Get breakdown of investment by tax section.
        
        Args:
            goal: The tax optimization goal
            profile: User profile
            
        Returns:
            dict: Breakdown of investment by tax section
        """
        user_id = profile.get('user_id') if isinstance(profile, dict) else None
        tax_regime = self._get_tax_regime(profile)
        
        # Extract goal details
        if isinstance(goal, dict):
            target_amount = goal.get('target_amount', 0)
        else:
            target_amount = getattr(goal, 'target_amount', 0)
        
        # If new tax regime, no section breakdown needed
        if tax_regime == 'new_regime':
            return {
                "non_deductible": target_amount,
                "note": "No tax deductions available under new tax regime"
            }
        
        # Get section limits
        section_80c_limit = self.get_parameter('tax.sections.80c.limit', 150000, user_id)
        section_80ccd_limit = self.get_parameter('tax.sections.80ccd.limit', 50000, user_id)
        section_80d_limit_self = self.get_parameter('tax.sections.80d.self_family.limit', 25000, user_id)
        
        # Existing investments
        existing_80c = self._get_existing_investment(profile, 'section_80c')
        existing_80ccd = self._get_existing_investment(profile, 'section_80ccd')
        existing_80d = self._get_existing_investment(profile, 'section_80d')
        
        # Calculate remaining deduction capacity
        remaining_80c = max(0, section_80c_limit - existing_80c)
        remaining_80ccd = max(0, section_80ccd_limit - existing_80ccd)
        remaining_80d = max(0, section_80d_limit_self - existing_80d)
        
        # Initialize breakdown
        breakdown = {
            "section_80c": 0,
            "section_80ccd": 0,
            "section_80d": 0,
            "other_investment": 0
        }
        
        remaining_amount = target_amount
        
        # Allocate to 80C first (highest priority)
        if remaining_amount > 0:
            breakdown["section_80c"] = min(remaining_80c, remaining_amount)
            remaining_amount -= breakdown["section_80c"]
        
        # Then allocate to 80CCD
        if remaining_amount > 0:
            breakdown["section_80ccd"] = min(remaining_80ccd, remaining_amount)
            remaining_amount -= breakdown["section_80ccd"]
        
        # Then allocate to 80D
        if remaining_amount > 0:
            breakdown["section_80d"] = min(remaining_80d, remaining_amount)
            remaining_amount -= breakdown["section_80d"]
        
        # Any remaining amount goes to non-deductible investments
        if remaining_amount > 0:
            breakdown["other_investment"] = remaining_amount
        
        return breakdown
    
    def get_expected_tax_savings(self, goal, profile: Dict[str, Any]) -> float:
        """
        Calculate expected tax savings from the tax optimization goal.
        
        Args:
            goal: The tax optimization goal
            profile: User profile
            
        Returns:
            float: Expected tax savings
        """
        tax_regime = self._get_tax_regime(profile)
        
        # No tax savings in new regime
        if tax_regime == 'new_regime':
            return 0
        
        # Get taxable income
        taxable_income = self._extract_taxable_income(profile)
        
        # Get section breakdown
        breakdown = self.get_tax_section_breakdown(goal, profile)
        
        # Calculate total deduction amount
        deductible_amount = breakdown.get("section_80c", 0) + breakdown.get("section_80ccd", 0) + breakdown.get("section_80d", 0)
        
        # Apply tax rate based on income bracket
        if taxable_income <= 250000:
            tax_rate = 0  # No tax
        elif taxable_income <= 500000:
            tax_rate = 0.05  # 5% bracket
        elif taxable_income <= 1000000:
            tax_rate = 0.20  # 20% bracket
        else:
            tax_rate = 0.30  # 30% bracket
        
        # Apply education cess (4%)
        effective_tax_rate = tax_rate * 1.04
        
        # Calculate tax savings (capped at taxable income - 250000)
        max_applicable_deduction = max(0, taxable_income - 250000)
        tax_savings = min(deductible_amount, max_applicable_deduction) * effective_tax_rate
        
        return tax_savings
    
    def get_recommended_allocation(self, goal, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get recommended investment allocation for tax optimization goal.
        
        Args:
            goal: The tax optimization goal
            profile: User profile
            
        Returns:
            dict: Recommended investment allocation
        """
        user_id = profile.get('user_id') if isinstance(profile, dict) else None
        tax_regime = self._get_tax_regime(profile)
        
        # Extract risk profile
        risk_profile = 'medium'  # Default
        if isinstance(profile, dict):
            if 'risk_profile' in profile:
                risk = profile['risk_profile']
                if risk in ['high', 'medium', 'low']:
                    risk_profile = risk
                    
            # Check in investment_preferences if available
            elif 'investment_preferences' in profile and isinstance(profile['investment_preferences'], dict):
                if 'risk_tolerance' in profile['investment_preferences']:
                    risk = profile['investment_preferences']['risk_tolerance']
                    if risk in ['high', 'medium', 'low']:
                        risk_profile = risk
                    elif risk in ['aggressive', 'very_aggressive']:
                        risk_profile = 'high'
                    elif risk in ['moderate', 'balanced']:
                        risk_profile = 'medium'
                    elif risk in ['conservative', 'very_conservative']:
                        risk_profile = 'low'
        
        # Get section breakdown
        breakdown = self.get_tax_section_breakdown(goal, profile)
        
        # Initialize allocation
        allocation = {}
        
        if tax_regime == 'old_regime':
            # 80C allocation based on risk profile
            if breakdown.get("section_80c", 0) > 0:
                if risk_profile == 'high':
                    allocation['ELSS (Equity Linked Savings Scheme)'] = breakdown["section_80c"]
                elif risk_profile == 'medium':
                    allocation['ELSS (Equity Linked Savings Scheme)'] = breakdown["section_80c"] * 0.6
                    allocation['PPF (Public Provident Fund)'] = breakdown["section_80c"] * 0.4
                else:  # low risk
                    allocation['PPF (Public Provident Fund)'] = breakdown["section_80c"] * 0.5
                    allocation['NSC (National Savings Certificate)'] = breakdown["section_80c"] * 0.3
                    allocation['Tax-Saving Fixed Deposits'] = breakdown["section_80c"] * 0.2
            
            # 80CCD allocation
            if breakdown.get("section_80ccd", 0) > 0:
                allocation['NPS (National Pension System)'] = breakdown["section_80ccd"]
            
            # 80D allocation
            if breakdown.get("section_80d", 0) > 0:
                allocation['Health Insurance Premium'] = breakdown["section_80d"]
            
            # Other investments
            if breakdown.get("other_investment", 0) > 0:
                if risk_profile == 'high':
                    allocation['Equity Mutual Funds'] = breakdown["other_investment"]
                elif risk_profile == 'medium':
                    allocation['Hybrid Mutual Funds'] = breakdown["other_investment"]
                else:  # low risk
                    allocation['Debt Mutual Funds'] = breakdown["other_investment"] * 0.6
                    allocation['Fixed Deposits'] = breakdown["other_investment"] * 0.4
        else:
            # New regime - focus on returns rather than tax savings
            amount = breakdown.get("non_deductible", 0)
            
            if amount > 0:
                if risk_profile == 'high':
                    allocation['Equity Mutual Funds'] = amount * 0.7
                    allocation['NPS (National Pension System)'] = amount * 0.3
                elif risk_profile == 'medium':
                    allocation['Equity Mutual Funds'] = amount * 0.5
                    allocation['NPS (National Pension System)'] = amount * 0.3
                    allocation['Debt Mutual Funds'] = amount * 0.2
                else:  # low risk
                    allocation['NPS (National Pension System)'] = amount * 0.4
                    allocation['Debt Mutual Funds'] = amount * 0.4
                    allocation['Fixed Deposits'] = amount * 0.2
        
        return {
            "recommended_allocation": allocation,
            "tax_regime": tax_regime,
            "risk_profile": risk_profile,
            "expected_tax_savings": self.get_expected_tax_savings(goal, profile)
        }
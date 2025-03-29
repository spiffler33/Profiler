"""
Income Projection Module

This module provides tools for projecting income over time with support for
multiple income sources, career milestones, retirement planning, and tax calculations.
Includes specialized support for Indian income patterns, tax regimes, and retirement options.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Union, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import math

from models.projections.base_projection import BaseProjection, FrequencyType

logger = logging.getLogger(__name__)

class IncomeSource(Enum):
    """Enum representing different income sources"""
    SALARY = "salary"
    BUSINESS = "business"
    RENTAL = "rental"
    DIVIDENDS = "dividends"
    INTEREST = "interest"
    PENSION = "pension"
    ANNUITY = "annuity"
    GOVT_BENEFITS = "government_benefits"
    EPF = "epf"                  # Employee Provident Fund
    PPF = "ppf"                  # Public Provident Fund
    NPS = "nps"                  # National Pension System
    GRATUITY = "gratuity"        # Retirement gratuity
    BONUS = "bonus"              # Annual/festival bonuses
    OTHER = "other"

class TaxRegime(Enum):
    """Enum representing different tax regimes in India"""
    OLD = "old_regime"           # Old tax regime with more deductions
    NEW = "new_regime"           # New tax regime with lower rates but fewer deductions

class CareerStage(Enum):
    """Enum representing different career stages"""
    EARLY = "early"          # Early career (0-5 years experience)
    GROWTH = "growth"        # Growth phase (5-15 years experience)
    PEAK = "peak"            # Peak earnings (15-30 years experience)
    LATE = "late"            # Late career (30+ years experience)
    RETIREMENT = "retirement"  # Retirement phase

@dataclass
class IncomeMilestone:
    """Data class representing a career milestone that affects income"""
    year: int
    description: str
    income_multiplier: float = 1.0     # Multiplier for base income (e.g., 1.2 for 20% increase)
    absolute_income_change: float = 0  # Absolute change amount (can be negative)
    
    def apply_to_income(self, current_income: float) -> float:
        """Apply the milestone effect to the current income"""
        return (current_income * self.income_multiplier) + self.absolute_income_change

@dataclass
class IncomeProjectionResult:
    """Data class for storing and visualizing income projection results"""
    years: List[int]
    income_values: Dict[IncomeSource, List[float]]
    total_income: List[float]
    after_tax_income: Optional[List[float]] = None
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert income result to pandas DataFrame for analysis/visualization"""
        data = {
            'Year': self.years,
            'Total_Income': self.total_income
        }
        
        if self.after_tax_income:
            data['After_Tax_Income'] = self.after_tax_income
        
        # Add individual income sources
        for source, values in self.income_values.items():
            data[f'Income_{source.value.capitalize()}'] = values
        
        return pd.DataFrame(data)

@dataclass
class PensionDetails:
    """Data class for pension and retirement benefits"""
    monthly_amount: float = 0.0         # Monthly pension amount
    annual_increment_rate: float = 0.0  # Annual increase rate for pension
    lump_sum_amount: float = 0.0        # One-time lump sum payment (like commutation)
    start_age: int = 60                 # Age when pension starts
    indexed_to_inflation: bool = False  # Whether pension is inflation-indexed

@dataclass
class FilingStatus:
    """Data class for tax filing status"""
    regime: TaxRegime = TaxRegime.OLD   # Tax regime (old or new)
    category: str = "individual"        # Filing category (individual, HUF, etc.)
    resident_status: str = "resident"   # Residency status for tax purposes
    senior_citizen: bool = False        # Whether the person is a senior citizen
    super_senior: bool = False          # Whether the person is a super senior citizen (80+)

@dataclass
class IndianRetirementBenefits:
    """Data class for Indian retirement benefits"""
    epf_balance: float = 0.0            # Employee Provident Fund balance
    epf_monthly_contribution: float = 0.0  # Monthly EPF contribution
    eps_eligible_years: int = 0         # Years of contribution to Employee Pension Scheme
    eps_eligible_salary: float = 0.0    # Average of last 60 months salary for EPS
    nps_balance: float = 0.0            # National Pension System balance
    nps_monthly_contribution: float = 0.0  # Monthly NPS contribution
    gratuity_eligible_years: int = 0    # Years of service for gratuity calculation
    gratuity_last_drawn_salary: float = 0.0  # Last drawn basic salary for gratuity

class IncomeProjection(BaseProjection):
    """
    Class for projecting income over time with support for multiple income sources,
    career milestones, retirement planning, and tax calculations.
    
    This class includes specialized support for Indian income patterns including
    festival bonuses, retirement gratuity, and various government pension schemes.
    """
    
    # Default growth rates by income source (Indian context)
    DEFAULT_GROWTH_RATES = {
        IncomeSource.SALARY: 0.08,      # 8% annual growth (Indian average)
        IncomeSource.BUSINESS: 0.10,    # 10% annual growth
        IncomeSource.RENTAL: 0.05,      # 5% annual growth
        IncomeSource.DIVIDENDS: 0.06,   # 6% annual growth
        IncomeSource.INTEREST: 0.04,    # 4% annual growth
        IncomeSource.PENSION: 0.03,     # 3% annual growth (partial inflation adjustment)
        IncomeSource.ANNUITY: 0.0,      # Fixed payments
        IncomeSource.GOVT_BENEFITS: 0.03,  # 3% annual growth
        IncomeSource.EPF: 0.085,        # 8.5% annual growth (EPF interest rate)
        IncomeSource.PPF: 0.071,        # 7.1% annual growth (PPF interest rate)
        IncomeSource.NPS: 0.10,         # 10% annual growth (NPS average returns)
        IncomeSource.BONUS: 0.07,       # 7% annual growth for bonuses
        IncomeSource.OTHER: 0.05,       # 5% annual growth
    }
    
    # Career stage growth modifiers
    CAREER_STAGE_MODIFIERS = {
        CareerStage.EARLY: 1.5,         # 50% higher growth in early career
        CareerStage.GROWTH: 1.2,        # 20% higher growth in growth phase
        CareerStage.PEAK: 0.8,          # 20% lower growth in peak years
        CareerStage.LATE: 0.5,          # 50% lower growth in late career
        CareerStage.RETIREMENT: 0.0,    # No growth in retirement
    }
    
    # Volatility factors by income source (higher values = more volatility)
    VOLATILITY_FACTORS = {
        IncomeSource.SALARY: 0.15,      # Relatively stable
        IncomeSource.BUSINESS: 0.40,    # Highly variable
        IncomeSource.RENTAL: 0.20,      # Moderately variable
        IncomeSource.DIVIDENDS: 0.25,   # Variable with market
        IncomeSource.INTEREST: 0.10,    # Fairly stable
        IncomeSource.PENSION: 0.05,     # Very stable
        IncomeSource.ANNUITY: 0.0,      # Fixed - no volatility
        IncomeSource.GOVT_BENEFITS: 0.05,  # Very stable
        IncomeSource.OTHER: 0.20,       # Moderately variable
    }
    
    # Indian income tax brackets (FY 2023-24)
    INDIA_TAX_BRACKETS_OLD = [
        (0, 250000, 0.0),           # Up to 2.5L: 0%
        (250001, 500000, 0.05),     # 2.5L to 5L: 5%
        (500001, 750000, 0.10),     # 5L to 7.5L: 10%
        (750001, 1000000, 0.15),    # 7.5L to 10L: 15%
        (1000001, 1250000, 0.20),   # 10L to 12.5L: 20%
        (1250001, 1500000, 0.25),   # 12.5L to 15L: 25%
        (1500001, float('inf'), 0.30)  # Above 15L: 30%
    ]
    
    # Indian income tax brackets - new regime (FY 2023-24)
    INDIA_TAX_BRACKETS_NEW = [
        (0, 300000, 0.0),           # Up to 3L: 0%
        (300001, 600000, 0.05),     # 3L to 6L: 5%
        (600001, 900000, 0.10),     # 6L to 9L: 10%
        (900001, 1200000, 0.15),    # 9L to 12L: 15%
        (1200001, 1500000, 0.20),   # 12L to 15L: 20%
        (1500001, float('inf'), 0.30)  # Above 15L: 30%
    ]
    
    # Common tax deductions in India (Section 80C, 80D, etc.)
    INDIA_TAX_DEDUCTIONS = {
        "80c": 150000,              # Section 80C limit (PF, ELSS, LIC, etc.)
        "80d_self": 25000,          # Health insurance for self (50k for senior citizens)
        "80d_parents": 25000,       # Health insurance for parents (50k if senior citizens)
        "standard_deduction": 50000,  # Standard deduction for salaried employees
        "hra_exemption_percent": 0.5,  # HRA exemption % of basic salary (metro cities)
        "nps_additional_deduction": 50000  # Additional NPS deduction under 80CCD(1B)
    }
    
    def __init__(self, 
                parameters=None, 
                inflation_rate: float = 0.06,  # Higher default for India
                tax_regime: TaxRegime = TaxRegime.OLD,
                include_bonus: bool = True,
                include_gratuity: bool = True,
                epf_contribution_rate: float = 0.12,  # 12% of basic salary
                seed: Optional[int] = None):
        """
        Initialize the income projection model.
        
        Parameters:
        -----------
        parameters : object, optional
            Financial parameters object for accessing system settings
        inflation_rate : float, default 0.06
            Annual inflation rate for real income calculations (higher default for India)
        tax_regime : TaxRegime, default TaxRegime.OLD
            Tax regime to use for tax calculations (old or new regime in India)
        include_bonus : bool, default True
            Whether to include festival/annual bonuses in projections
        include_gratuity : bool, default True
            Whether to include gratuity in retirement benefits
        epf_contribution_rate : float, default 0.12
            Employee Provident Fund contribution rate (% of basic salary)
        seed : int, optional
            Random seed for Monte Carlo simulations
        """
        super().__init__(parameters)
        
        self.inflation_rate = inflation_rate
        self.tax_regime = tax_regime
        self.include_bonus = include_bonus
        self.include_gratuity = include_gratuity
        self.epf_contribution_rate = epf_contribution_rate
        
        # Set random seed if provided
        if seed is not None:
            np.random.seed(seed)
    
    def project_income(self,
                      start_income: float,
                      years: int,
                      growth_rate: Optional[float] = None,
                      income_source: Union[str, IncomeSource] = IncomeSource.SALARY,
                      career_stage: Union[str, CareerStage] = CareerStage.GROWTH,
                      milestones: Optional[List[IncomeMilestone]] = None,
                      include_inflation_adjustment: bool = False,
                      calculate_taxes: bool = False,
                      start_year: int = 0) -> IncomeProjectionResult:
        """
        Project income growth over time for a single income source.
        
        Parameters:
        -----------
        start_income : float
            Starting annual income amount
        years : int
            Number of years to project
        growth_rate : float, optional
            Annual growth rate (if not provided, uses default for income source and career stage)
        income_source : str or IncomeSource, default IncomeSource.SALARY
            Type of income being projected
        career_stage : str or CareerStage, default CareerStage.GROWTH
            Career stage, which affects growth rate
        milestones : List[IncomeMilestone], optional
            List of career milestones that affect income over time
        include_inflation_adjustment : bool, default False
            Whether to adjust income for inflation (real vs. nominal income)
        calculate_taxes : bool, default False
            Whether to calculate after-tax income
        start_year : int, default 0
            Starting year for the projection
            
        Returns:
        --------
        IncomeProjectionResult
            Object containing income projection results
        """
        # Convert income_source to enum if it's a string
        if isinstance(income_source, str):
            try:
                income_source = IncomeSource(income_source)
            except ValueError:
                logger.warning(f"Invalid income source: {income_source}. Using SALARY instead.")
                income_source = IncomeSource.SALARY
        
        # Convert career_stage to enum if it's a string
        if isinstance(career_stage, str):
            try:
                career_stage = CareerStage(career_stage)
            except ValueError:
                logger.warning(f"Invalid career stage: {career_stage}. Using GROWTH instead.")
                career_stage = CareerStage.GROWTH
        
        # If growth rate is not provided, calculate it based on income source and career stage
        if growth_rate is None:
            growth_rate = self._get_growth_rate(income_source, career_stage)
        
        # Initialize tracking variables
        income_values = {income_source: [start_income]}
        total_income = [start_income]
        current_income = start_income
        
        # Sort milestones by year if provided
        milestone_dict = {}
        if milestones:
            for milestone in milestones:
                if milestone.year <= years:
                    milestone_dict[milestone.year] = milestone
        
        # Generate years list
        years_list = list(range(start_year, start_year + years + 1))
        
        # Calculate year-by-year projections
        for year_idx, year in enumerate(years_list[1:], 1):
            # Apply milestone if one exists for this year
            if year in milestone_dict:
                current_income = milestone_dict[year].apply_to_income(current_income)
            else:
                # Apply standard growth rate, adjusted for career progression
                year_growth = self._calculate_growth_for_year(growth_rate, year_idx, career_stage)
                current_income = current_income * (1 + year_growth)
            
            # Store results
            income_values[income_source].append(current_income)
            total_income.append(current_income)
        
        # Create result object
        result = IncomeProjectionResult(
            years=years_list,
            income_values=income_values,
            total_income=total_income
        )
        
        # Apply inflation adjustment if requested
        if include_inflation_adjustment:
            # Adjust total income
            adjusted_total = self.apply_inflation_adjustment(
                result.total_income, 
                result.years, 
                self.inflation_rate
            )
            
            # Adjust income values for each source
            adjusted_income_values = {}
            for source, values in result.income_values.items():
                adjusted_income_values[source] = self.apply_inflation_adjustment(
                    values, 
                    result.years, 
                    self.inflation_rate
                )
            
            # Update result with adjusted values
            result = IncomeProjectionResult(
                years=result.years,
                income_values=adjusted_income_values,
                total_income=adjusted_total
            )
        
        # Calculate after-tax income if requested
        if calculate_taxes:
            after_tax_income = self._calculate_after_tax_income(result.total_income)
            result.after_tax_income = after_tax_income
        
        return result
    
    def project_multiple_income_sources(self,
                                       income_sources: Dict[Union[str, IncomeSource], float],
                                       years: int,
                                       growth_rates: Optional[Dict[Union[str, IncomeSource], float]] = None,
                                       career_stages: Optional[Dict[Union[str, IncomeSource], Union[str, CareerStage]]] = None,
                                       milestones_by_source: Optional[Dict[Union[str, IncomeSource], List[IncomeMilestone]]] = None,
                                       include_inflation_adjustment: bool = False,
                                       calculate_taxes: bool = False,
                                       start_year: int = 0) -> IncomeProjectionResult:
        """
        Project income from multiple income sources over time.
        
        Parameters:
        -----------
        income_sources : Dict[str or IncomeSource, float]
            Dictionary mapping income sources to their starting amounts
        years : int
            Number of years to project
        growth_rates : Dict[str or IncomeSource, float], optional
            Dictionary mapping income sources to their growth rates
        career_stages : Dict[str or IncomeSource, str or CareerStage], optional
            Dictionary mapping income sources to their career stages
        milestones_by_source : Dict[str or IncomeSource, List[IncomeMilestone]], optional
            Dictionary mapping income sources to their milestone lists
        include_inflation_adjustment : bool, default False
            Whether to adjust income for inflation (real vs. nominal income)
        calculate_taxes : bool, default False
            Whether to calculate after-tax income
        start_year : int, default 0
            Starting year for the projection
            
        Returns:
        --------
        IncomeProjectionResult
            Object containing income projection results for all sources
        """
        # Normalize keys to IncomeSource enums
        normalized_income_sources = {}
        for source, amount in income_sources.items():
            if isinstance(source, str):
                try:
                    source = IncomeSource(source)
                except ValueError:
                    logger.warning(f"Invalid income source: {source}. Skipping.")
                    continue
            normalized_income_sources[source] = amount
        
        # Initialize tracking variables
        income_values = {source: [amount] for source, amount in normalized_income_sources.items()}
        current_values = {source: amount for source, amount in normalized_income_sources.items()}
        total_income = [sum(normalized_income_sources.values())]
        
        # Normalize growth rates if provided
        normalized_growth_rates = {}
        if growth_rates:
            for source, rate in growth_rates.items():
                if isinstance(source, str):
                    try:
                        source = IncomeSource(source)
                    except ValueError:
                        continue
                normalized_growth_rates[source] = rate
        
        # Normalize career stages if provided
        normalized_career_stages = {}
        if career_stages:
            for source, stage in career_stages.items():
                if isinstance(source, str):
                    try:
                        source = IncomeSource(source)
                    except ValueError:
                        continue
                
                if isinstance(stage, str):
                    try:
                        stage = CareerStage(stage)
                    except ValueError:
                        stage = CareerStage.GROWTH
                
                normalized_career_stages[source] = stage
        
        # Normalize milestones if provided
        normalized_milestones = {}
        if milestones_by_source:
            for source, milestones in milestones_by_source.items():
                if isinstance(source, str):
                    try:
                        source = IncomeSource(source)
                    except ValueError:
                        continue
                normalized_milestones[source] = milestones
        
        # Organize milestones by source and year
        milestone_dict = {}
        if normalized_milestones:
            for source, milestones in normalized_milestones.items():
                if source not in milestone_dict:
                    milestone_dict[source] = {}
                
                for milestone in milestones:
                    if milestone.year <= years:
                        milestone_dict[source][milestone.year] = milestone
        
        # Generate years list
        years_list = list(range(start_year, start_year + years + 1))
        
        # Project income year by year
        for year_idx, year in enumerate(years_list[1:], 1):
            year_total = 0
            
            # Process each income source
            for source in normalized_income_sources:
                current_value = current_values[source]
                
                # Apply milestone if one exists for this source and year
                if source in milestone_dict and year in milestone_dict[source]:
                    current_value = milestone_dict[source][year].apply_to_income(current_value)
                else:
                    # Get growth rate for this source
                    if source in normalized_growth_rates:
                        growth_rate = normalized_growth_rates[source]
                    else:
                        career_stage = normalized_career_stages.get(source, CareerStage.GROWTH)
                        growth_rate = self._get_growth_rate(source, career_stage)
                    
                    # Apply growth rate, adjusted for career progression
                    year_growth = self._calculate_growth_for_year(growth_rate, year_idx, 
                                                                normalized_career_stages.get(source, CareerStage.GROWTH))
                    current_value = current_value * (1 + year_growth)
                
                # Update current values
                current_values[source] = current_value
                income_values[source].append(current_value)
                year_total += current_value
            
            # Store total income for the year
            total_income.append(year_total)
        
        # Create result object
        result = IncomeProjectionResult(
            years=years_list,
            income_values=income_values,
            total_income=total_income
        )
        
        # Apply inflation adjustment if requested
        if include_inflation_adjustment:
            # Adjust total income
            adjusted_total = self.apply_inflation_adjustment(
                result.total_income, 
                result.years, 
                self.inflation_rate
            )
            
            # Adjust income values for each source
            adjusted_income_values = {}
            for source, values in result.income_values.items():
                adjusted_income_values[source] = self.apply_inflation_adjustment(
                    values, 
                    result.years, 
                    self.inflation_rate
                )
            
            # Update result with adjusted values
            result = IncomeProjectionResult(
                years=result.years,
                income_values=adjusted_income_values,
                total_income=adjusted_total
            )
        
        # Calculate after-tax income if requested
        if calculate_taxes:
            after_tax_income = self._calculate_after_tax_income(result.total_income)
            result.after_tax_income = after_tax_income
        
        return result
    
    def extract_income_data(self, profile: Dict[str, Any]) -> Dict[IncomeSource, float]:
        """
        Extract income data from a user profile.
        
        Parameters:
        -----------
        profile : Dict[str, Any]
            User profile data
            
        Returns:
        --------
        Dict[IncomeSource, float]
            Dictionary mapping income sources to amounts
        """
        income_data = {}
        
        # Extract income data from profile
        # This method will need customization based on the actual profile structure
        
        # Try to extract salary
        salary = self._extract_value_from_profile(profile, ['salary', 'annual_salary', 'income.salary'])
        if salary is not None:
            income_data[IncomeSource.SALARY] = salary
        
        # Try to extract business income
        business_income = self._extract_value_from_profile(profile, ['business_income', 'income.business'])
        if business_income is not None:
            income_data[IncomeSource.BUSINESS] = business_income
        
        # Try to extract rental income
        rental_income = self._extract_value_from_profile(profile, ['rental_income', 'income.rental'])
        if rental_income is not None:
            income_data[IncomeSource.RENTAL] = rental_income
        
        # Try to extract investment income (dividends and interest)
        dividend_income = self._extract_value_from_profile(profile, ['dividend_income', 'income.dividends'])
        if dividend_income is not None:
            income_data[IncomeSource.DIVIDENDS] = dividend_income
        
        interest_income = self._extract_value_from_profile(profile, ['interest_income', 'income.interest'])
        if interest_income is not None:
            income_data[IncomeSource.INTEREST] = interest_income
        
        # Try to extract pension income
        pension_income = self._extract_value_from_profile(profile, ['pension_income', 'income.pension'])
        if pension_income is not None:
            income_data[IncomeSource.PENSION] = pension_income
        
        # Try to extract government benefits
        govt_benefits = self._extract_value_from_profile(profile, ['govt_benefits', 'income.government_benefits'])
        if govt_benefits is not None:
            income_data[IncomeSource.GOVT_BENEFITS] = govt_benefits
        
        # Try to extract other income
        other_income = self._extract_value_from_profile(profile, ['other_income', 'income.other'])
        if other_income is not None:
            income_data[IncomeSource.OTHER] = other_income
        
        # If we have a general income field but no specific sources, use it as salary
        if not income_data:
            general_income = self._extract_value_from_profile(profile, ['income', 'annual_income'])
            if general_income is not None:
                income_data[IncomeSource.SALARY] = general_income
        
        return income_data
    
    def classify_income_sources(self, income_data: Dict[str, float]) -> Dict[IncomeSource, float]:
        """
        Classify income sources from generic data.
        
        Parameters:
        -----------
        income_data : Dict[str, float]
            Dictionary of income data with string keys
            
        Returns:
        --------
        Dict[IncomeSource, float]
            Dictionary with classified income sources
        """
        classified_income = {}
        
        # Map of common income source names to IncomeSource enum values
        source_mapping = {
            'salary': IncomeSource.SALARY,
            'wages': IncomeSource.SALARY,
            'compensation': IncomeSource.SALARY,
            'business': IncomeSource.BUSINESS,
            'self_employment': IncomeSource.BUSINESS,
            'freelance': IncomeSource.BUSINESS,
            'rental': IncomeSource.RENTAL,
            'rent': IncomeSource.RENTAL,
            'property': IncomeSource.RENTAL,
            'dividends': IncomeSource.DIVIDENDS,
            'dividend': IncomeSource.DIVIDENDS,
            'interest': IncomeSource.INTEREST,
            'fixed_deposit': IncomeSource.INTEREST,
            'savings': IncomeSource.INTEREST,
            'pension': IncomeSource.PENSION,
            'retirement': IncomeSource.PENSION,
            'annuity': IncomeSource.ANNUITY,
            'govt_benefits': IncomeSource.GOVT_BENEFITS,
            'government_benefits': IncomeSource.GOVT_BENEFITS,
            'social_security': IncomeSource.GOVT_BENEFITS,
            'welfare': IncomeSource.GOVT_BENEFITS,
            'other': IncomeSource.OTHER
        }
        
        # Process each income source
        for key, amount in income_data.items():
            # Normalize key to lowercase and remove spaces
            normalized_key = key.lower().replace(' ', '_')
            
            # Check if key matches any known sources
            if normalized_key in source_mapping:
                income_source = source_mapping[normalized_key]
            else:
                # Try to find a partial match
                found = False
                for mapping_key, income_source_value in source_mapping.items():
                    if mapping_key in normalized_key:
                        income_source = income_source_value
                        found = True
                        break
                
                # Default to OTHER if no match found
                if not found:
                    income_source = IncomeSource.OTHER
            
            # Add to classified income (summing if multiple sources map to same enum)
            if income_source in classified_income:
                classified_income[income_source] += amount
            else:
                classified_income[income_source] = amount
        
        return classified_income
    
    def adjust_for_career_milestones(self, 
                                   projection: IncomeProjectionResult, 
                                   milestones: List[IncomeMilestone]) -> IncomeProjectionResult:
        """
        Adjust an income projection to account for career milestones.
        
        Parameters:
        -----------
        projection : IncomeProjectionResult
            Original income projection
        milestones : List[IncomeMilestone]
            List of career milestones to apply
            
        Returns:
        --------
        IncomeProjectionResult
            Adjusted income projection
        """
        # Create a copy of the projection data
        adjusted_income_values = {source: list(values) for source, values in projection.income_values.items()}
        adjusted_total_income = list(projection.total_income)
        
        # Sort milestones by year
        sorted_milestones = sorted(milestones, key=lambda m: m.year)
        
        # Apply each milestone
        for milestone in sorted_milestones:
            year_index = milestone.year
            
            # Skip if milestone is outside projection range
            if year_index >= len(projection.years) or year_index < 0:
                continue
            
            # For each income source, apply the milestone effect
            for source in adjusted_income_values:
                # Get current value for this source
                current_value = adjusted_income_values[source][year_index]
                
                # Apply milestone effect
                new_value = milestone.apply_to_income(current_value)
                
                # Calculate the change in value
                value_change = new_value - current_value
                
                # Update the value for this year
                adjusted_income_values[source][year_index] = new_value
                
                # Also update all future years
                for future_year in range(year_index + 1, len(projection.years)):
                    # Update future values proportionally
                    growth_factor = adjusted_income_values[source][future_year] / current_value if current_value > 0 else 1
                    adjusted_income_values[source][future_year] = new_value * growth_factor
            
            # Recalculate total income
            for year in range(year_index, len(projection.years)):
                adjusted_total_income[year] = sum(source_values[year] for source_values in adjusted_income_values.values())
        
        # Create a new projection result with adjusted values
        result = IncomeProjectionResult(
            years=projection.years,
            income_values=adjusted_income_values,
            total_income=adjusted_total_income
        )
        
        # Add after-tax income if the original projection had it
        if projection.after_tax_income:
            result.after_tax_income = self._calculate_after_tax_income(result.total_income)
        
        return result
    
    def model_income_volatility(self, 
                              projection: IncomeProjectionResult, 
                              volatility: Optional[Dict[IncomeSource, float]] = None,
                              profile: Optional[Dict[str, Any]] = None) -> Dict[str, IncomeProjectionResult]:
        """
        Create different income projection scenarios based on volatility.
        
        Parameters:
        -----------
        projection : IncomeProjectionResult
            Base income projection
        volatility : Dict[IncomeSource, float], optional
            Dictionary mapping income sources to volatility factors
        profile : Dict[str, Any], optional
            User profile data (used to extract volatility preferences)
            
        Returns:
        --------
        Dict[str, IncomeProjectionResult]
            Dictionary mapping scenario names to income projections
        """
        # Use default volatility if not provided
        if volatility is None:
            volatility = self.VOLATILITY_FACTORS
        
        # Adjust volatility based on profile if provided
        if profile:
            # Try to extract volatility preferences from profile
            risk_tolerance = self._extract_value_from_profile(profile, ['risk_tolerance', 'income_volatility_tolerance'])
            if risk_tolerance is not None:
                # Scale volatility based on risk tolerance (0-10 scale, where 5 is normal)
                if isinstance(risk_tolerance, (int, float)):
                    scaling_factor = risk_tolerance / 5.0
                    volatility = {source: vol * scaling_factor for source, vol in volatility.items()}
        
        # Calculate different scenarios
        scenarios = {}
        
        # Optimistic scenario (higher growth)
        optimistic_income_values = {}
        optimistic_total = []
        
        # Pessimistic scenario (lower growth)
        pessimistic_income_values = {}
        pessimistic_total = []
        
        # Process each year
        for year_idx, year in enumerate(projection.years):
            optimistic_year_total = 0
            pessimistic_year_total = 0
            
            # Process each income source
            for source, values in projection.income_values.items():
                # Skip if no value for this year
                if year_idx >= len(values):
                    continue
                
                # Get base value for this year
                base_value = values[year_idx]
                
                # Get volatility factor for this source
                vol_factor = volatility.get(source, self.VOLATILITY_FACTORS.get(source, 0.15))
                
                # Calculate optimistic and pessimistic values
                # Volatility increases with time, but at a decreasing rate
                time_factor = math.sqrt(year_idx) if year_idx > 0 else 0
                year_volatility = vol_factor * time_factor
                
                optimistic_value = base_value * (1 + year_volatility)
                pessimistic_value = base_value * (1 - year_volatility)
                
                # Ensure pessimistic value doesn't go negative
                pessimistic_value = max(0, pessimistic_value)
                
                # Initialize source lists if needed
                if source not in optimistic_income_values:
                    optimistic_income_values[source] = []
                if source not in pessimistic_income_values:
                    pessimistic_income_values[source] = []
                
                # Add values to lists (padding if necessary)
                while len(optimistic_income_values[source]) < year_idx:
                    optimistic_income_values[source].append(0)
                while len(pessimistic_income_values[source]) < year_idx:
                    pessimistic_income_values[source].append(0)
                
                # Add values for this year
                optimistic_income_values[source].append(optimistic_value)
                pessimistic_income_values[source].append(pessimistic_value)
                
                # Add to year totals
                optimistic_year_total += optimistic_value
                pessimistic_year_total += pessimistic_value
            
            # Add to total lists
            optimistic_total.append(optimistic_year_total)
            pessimistic_total.append(pessimistic_year_total)
        
        # Create scenario results
        scenarios['optimistic'] = IncomeProjectionResult(
            years=projection.years,
            income_values=optimistic_income_values,
            total_income=optimistic_total
        )
        
        scenarios['pessimistic'] = IncomeProjectionResult(
            years=projection.years,
            income_values=pessimistic_income_values,
            total_income=pessimistic_total
        )
        
        # Add original projection as expected scenario
        scenarios['expected'] = projection
        
        # Calculate after-tax income for each scenario if needed
        if projection.after_tax_income:
            for scenario_name, scenario_result in scenarios.items():
                scenario_result.after_tax_income = self._calculate_after_tax_income(scenario_result.total_income)
        
        return scenarios
    
    def calculate_growth_trajectory(self, 
                                  base_income: float, 
                                  career_stage: Union[str, CareerStage], 
                                  years: int) -> List[float]:
        """
        Calculate a realistic income growth trajectory based on career stage.
        
        Parameters:
        -----------
        base_income : float
            Starting income amount
        career_stage : str or CareerStage
            Career stage, which affects growth curve
        years : int
            Number of years to project
            
        Returns:
        --------
        List[float]
            List of income values over time
        """
        # Convert career_stage to enum if it's a string
        if isinstance(career_stage, str):
            try:
                career_stage = CareerStage(career_stage)
            except ValueError:
                logger.warning(f"Invalid career stage: {career_stage}. Using GROWTH instead.")
                career_stage = CareerStage.GROWTH
        
        # Get base growth rate for salary
        base_growth_rate = self._get_growth_rate(IncomeSource.SALARY, career_stage)
        
        # Initialize result with starting income
        income_trajectory = [base_income]
        current_income = base_income
        
        # Calculate income for each year with a non-linear growth curve
        for year in range(1, years + 1):
            # Calculate year-specific growth rate based on career stage progression
            if career_stage == CareerStage.EARLY:
                # Early career: growth increases in early years, then stabilizes
                year_factor = 1.0 + 0.5 * min(1.0, year / 5)
            elif career_stage == CareerStage.GROWTH:
                # Growth phase: fairly stable growth
                year_factor = 1.0
            elif career_stage == CareerStage.PEAK:
                # Peak years: growth slows down gradually
                year_factor = 1.0 - 0.1 * min(1.0, year / 10)
            elif career_stage == CareerStage.LATE:
                # Late career: growth declines more rapidly
                year_factor = 0.8 - 0.3 * min(1.0, year / 10)
            else:  # RETIREMENT
                # Retirement: minimal or no growth
                year_factor = 0.2
            
            # Apply growth with year-specific factor
            year_growth = base_growth_rate * year_factor
            current_income *= (1 + year_growth)
            
            # Add to trajectory
            income_trajectory.append(current_income)
        
        return income_trajectory
    
    def _get_growth_rate(self, income_source: IncomeSource, career_stage: CareerStage) -> float:
        """
        Get the growth rate for an income source, adjusted for career stage.
        
        Parameters:
        -----------
        income_source : IncomeSource
            Income source type
        career_stage : CareerStage
            Career stage
            
        Returns:
        --------
        float
            Adjusted growth rate
        """
        # First try to get from parameters
        param_path = f"income_growth_rates.{income_source.value}.{career_stage.value}"
        growth_rate = self.get_parameter(param_path)
        
        if growth_rate is not None:
            return growth_rate
        
        # Fall back to default growth rate for the income source
        base_rate = self.DEFAULT_GROWTH_RATES.get(income_source, 0.03)
        
        # Apply career stage modifier
        modifier = self.CAREER_STAGE_MODIFIERS.get(career_stage, 1.0)
        
        return base_rate * modifier
    
    def _calculate_growth_for_year(self, 
                                  base_growth_rate: float, 
                                  year: int, 
                                  career_stage: CareerStage) -> float:
        """
        Calculate the growth rate for a specific year based on career stage dynamics.
        
        Parameters:
        -----------
        base_growth_rate : float
            Base annual growth rate
        year : int
            Year index (1-based)
        career_stage : CareerStage
            Career stage
            
        Returns:
        --------
        float
            Adjusted growth rate for the year
        """
        # Apply different growth patterns based on career stage
        if career_stage == CareerStage.EARLY:
            # Early career often has accelerating growth
            year_factor = min(1.5, 1.0 + 0.1 * year)
        elif career_stage == CareerStage.GROWTH:
            # Growth phase has relatively stable growth
            # Small random variation to model real-world fluctuations
            year_factor = 1.0 + 0.05 * (np.random.random() - 0.5)
        elif career_stage == CareerStage.PEAK:
            # Peak years have decelerating growth
            year_factor = max(0.5, 1.0 - 0.05 * year)
        elif career_stage == CareerStage.LATE:
            # Late career has minimal growth
            year_factor = max(0.2, 1.0 - 0.1 * year)
        else:  # RETIREMENT
            # Retirement has fixed income or minimal growth
            year_factor = 0.2
        
        return base_growth_rate * year_factor
    
    # Add method for projecting multiple income streams
    def project_multiple_streams(self,
                               income_sources: Dict[Union[str, IncomeSource], float],
                               years: int,
                               growth_rates: Optional[Dict[Union[str, IncomeSource], float]] = None,
                               include_inflation_adjustment: bool = False,
                               include_taxes: bool = True,
                               filing_status: Optional[FilingStatus] = None) -> IncomeProjectionResult:
        """
        Project income from multiple streams with specialized handling for each type.
        
        This is an enhanced version of project_multiple_income_sources that adds
        specialized handling for different income types, including Indian-specific
        income patterns like bonuses and retirement benefits.
        
        Parameters:
        -----------
        income_sources : Dict[str or IncomeSource, float]
            Dictionary mapping income sources to their starting amounts
        years : int
            Number of years to project
        growth_rates : Dict[str or IncomeSource, float], optional
            Dictionary mapping income sources to their growth rates
        include_inflation_adjustment : bool, default False
            Whether to adjust for inflation (real vs. nominal)
        include_taxes : bool, default True
            Whether to calculate after-tax income
        filing_status : FilingStatus, optional
            Tax filing status details
            
        Returns:
        --------
        IncomeProjectionResult
            Object containing projection results for all income streams
        """
        # Normalize keys to IncomeSource enums
        normalized_sources = {}
        for source, amount in income_sources.items():
            if isinstance(source, str):
                try:
                    source = IncomeSource(source)
                except ValueError:
                    logger.warning(f"Invalid income source: {source}. Skipping.")
                    continue
            normalized_sources[source] = amount
        
        # Normalize growth rates
        normalized_growth_rates = {}
        if growth_rates:
            for source, rate in growth_rates.items():
                if isinstance(source, str):
                    try:
                        source = IncomeSource(source)
                    except ValueError:
                        continue
                normalized_growth_rates[source] = rate
        
        # Separate active and passive income sources
        active_sources = {}
        passive_sources = {}
        for source, amount in normalized_sources.items():
            if source in [IncomeSource.SALARY, IncomeSource.BUSINESS, IncomeSource.BONUS]:
                active_sources[source] = amount
            else:
                passive_sources[source] = amount
        
        # Extract growth rates for active and passive sources
        active_growth_rates = {s: normalized_growth_rates.get(s) for s in active_sources if s in normalized_growth_rates}
        passive_growth_rates = {s: normalized_growth_rates.get(s) for s in passive_sources if s in normalized_growth_rates}
        
        # Project active income
        active_result = None
        if active_sources:
            active_result = self.project_multiple_income_sources(
                income_sources=active_sources,
                years=years,
                growth_rates=active_growth_rates,
                include_inflation_adjustment=False,  # Will adjust later if needed
                calculate_taxes=False  # Will calculate taxes after combining
            )
        
        # Project passive income
        passive_result = None
        if passive_sources:
            passive_result = self.project_passive_income_growth(
                passive_sources=passive_sources,
                years=years,
                growth_rates=passive_growth_rates,
                include_inflation_adjustment=False  # Will adjust later if needed
            )
        
        # Merge active and passive income
        if active_result and passive_result:
            result = self.merge_income_streams([active_result, passive_result])
        elif active_result:
            result = active_result
        elif passive_result:
            result = passive_result
        else:
            # Empty result if no income sources
            return IncomeProjectionResult(
                years=list(range(years + 1)),
                income_values={},
                total_income=[0] * (years + 1)
            )
        
        # Apply inflation adjustment if requested
        if include_inflation_adjustment:
            result = self._apply_inflation_adjustment_to_result(result)
        
        # Calculate after-tax income if requested
        if include_taxes:
            result.after_tax_income = self.calculate_post_tax_income(
                result.total_income,
                filing_status
            )
        
        return result
    
    def project_passive_income_growth(self,
                                    passive_sources: Dict[IncomeSource, float],
                                    years: int,
                                    growth_rates: Optional[Dict[IncomeSource, float]] = None,
                                    include_inflation_adjustment: bool = False) -> IncomeProjectionResult:
        """
        Project growth for passive income sources like rentals, dividends, interest.
        
        Parameters:
        -----------
        passive_sources : Dict[IncomeSource, float]
            Dictionary mapping passive income sources to their starting amounts
        years : int
            Number of years to project
        growth_rates : Dict[IncomeSource, float], optional
            Dictionary mapping income sources to their growth rates
        include_inflation_adjustment : bool, default False
            Whether to adjust for inflation (real vs. nominal)
            
        Returns:
        --------
        IncomeProjectionResult
            Object containing projection results for passive income
        """
        # Initialize tracking variables
        income_values = {source: [amount] for source, amount in passive_sources.items()}
        current_values = {source: amount for source, amount in passive_sources.items()}
        total_income = [sum(passive_sources.values())]
        
        # Generate years list
        years_list = list(range(years + 1))
        
        # Project year by year
        for year_idx in range(1, years + 1):
            year_total = 0
            
            # Process each income source
            for source, current_value in current_values.items():
                # Get growth rate for this source
                if growth_rates and source in growth_rates:
                    growth_rate = growth_rates[source]
                else:
                    growth_rate = self.DEFAULT_GROWTH_RATES.get(source, 0.04)
                
                # Apply specialized growth patterns based on source type
                if source == IncomeSource.RENTAL:
                    # Rental income typically grows with inflation plus a premium
                    growth_plus_premium = growth_rate + 0.01  # 1% premium above base growth
                    new_value = current_value * (1 + growth_plus_premium)
                    
                    # Apply periodic jumps (e.g., rent increases every 3 years)
                    if year_idx % 3 == 0:
                        new_value *= 1.1  # 10% jump every 3 years
                
                elif source in [IncomeSource.DIVIDENDS, IncomeSource.INTEREST]:
                    # Investment income can be more volatile
                    volatility = 0.3 if source == IncomeSource.DIVIDENDS else 0.1
                    random_factor = 1.0 + (np.random.random() - 0.5) * volatility
                    new_value = current_value * (1 + growth_rate * random_factor)
                
                elif source in [IncomeSource.EPF, IncomeSource.PPF, IncomeSource.NPS]:
                    # Retirement accounts with compound growth
                    new_value = current_value * (1 + growth_rate)
                    
                    # Add regular contributions if this is a retirement account
                    if hasattr(self, f"{source.value}_monthly_contribution"):
                        annual_contribution = getattr(self, f"{source.value}_monthly_contribution") * 12
                        new_value += annual_contribution
                
                else:
                    # Default growth pattern
                    new_value = current_value * (1 + growth_rate)
                
                # Update current value
                current_values[source] = new_value
                income_values[source].append(new_value)
                year_total += new_value
            
            # Add to total income
            total_income.append(year_total)
        
        # Create result
        result = IncomeProjectionResult(
            years=years_list,
            income_values=income_values,
            total_income=total_income
        )
        
        # Apply inflation adjustment if requested
        if include_inflation_adjustment:
            result = self._apply_inflation_adjustment_to_result(result)
        
        return result
    
    def merge_income_streams(self, projections: List[IncomeProjectionResult]) -> IncomeProjectionResult:
        """
        Merge multiple income projections into a single projection.
        
        Parameters:
        -----------
        projections : List[IncomeProjectionResult]
            List of income projections to merge
            
        Returns:
        --------
        IncomeProjectionResult
            Combined income projection
        """
        # Verify that we have projections to merge
        if not projections:
            return IncomeProjectionResult(
                years=[0],
                income_values={},
                total_income=[0]
            )
        
        # Use the first projection's years as the base
        base_years = projections[0].years
        max_years = len(base_years)
        
        # Initialize merged income values and total
        merged_income_values = {}
        merged_total_income = [0] * max_years
        
        # Merge each projection
        for projection in projections:
            # Ensure all projections have the same number of years
            if len(projection.years) != max_years:
                logger.warning("Projections have different year lengths. Using the shorter length.")
                max_years = min(max_years, len(projection.years))
            
            # Add income values for each source
            for source, values in projection.income_values.items():
                if source not in merged_income_values:
                    merged_income_values[source] = [0] * max_years
                
                # Add values up to max_years
                for i in range(min(max_years, len(values))):
                    merged_income_values[source][i] += values[i]
            
            # Add to total income
            for i in range(min(max_years, len(projection.total_income))):
                merged_total_income[i] += projection.total_income[i]
        
        # Create merged result
        return IncomeProjectionResult(
            years=base_years[:max_years],
            income_values=merged_income_values,
            total_income=merged_total_income
        )
    
    def calculate_tax_liability(self, 
                              income_projection: IncomeProjectionResult,
                              filing_status: Optional[FilingStatus] = None) -> Dict[str, List[float]]:
        """
        Calculate tax liability over time based on income projections.
        
        Parameters:
        -----------
        income_projection : IncomeProjectionResult
            Income projection result
        filing_status : FilingStatus, optional
            Tax filing status details
            
        Returns:
        --------
        Dict[str, List[float]]
            Dictionary containing tax liability and related metrics
        """
        # Use default filing status if not provided
        if filing_status is None:
            filing_status = FilingStatus(regime=self.tax_regime)
        
        # Initialize result containers
        tax_liability = []
        taxable_income = []
        effective_tax_rate = []
        
        # Get appropriate tax brackets based on regime
        tax_brackets = self._get_tax_brackets(filing_status.regime)
        
        # Calculate year by year
        for income in income_projection.total_income:
            # Calculate taxable income with deductions
            year_taxable = self._calculate_taxable_income(income, filing_status)
            taxable_income.append(year_taxable)
            
            # Calculate tax
            year_tax = self._calculate_tax(year_taxable, filing_status)
            tax_liability.append(year_tax)
            
            # Calculate effective tax rate
            if income > 0:
                rate = year_tax / income
            else:
                rate = 0
            effective_tax_rate.append(rate)
        
        return {
            "tax_liability": tax_liability,
            "taxable_income": taxable_income,
            "effective_tax_rate": effective_tax_rate
        }
    
    def calculate_post_tax_income(self, 
                                pre_tax_income: List[float],
                                filing_status: Optional[FilingStatus] = None) -> List[float]:
        """
        Calculate post-tax income from pre-tax income.
        
        Parameters:
        -----------
        pre_tax_income : List[float]
            List of pre-tax income values
        filing_status : FilingStatus, optional
            Tax filing status details
            
        Returns:
        --------
        List[float]
            List of post-tax income values
        """
        # Use default filing status if not provided
        if filing_status is None:
            filing_status = FilingStatus(regime=self.tax_regime)
        
        post_tax_income = []
        
        for income in pre_tax_income:
            # Calculate taxable income
            taxable = self._calculate_taxable_income(income, filing_status)
            
            # Calculate tax
            tax = self._calculate_tax(taxable, filing_status)
            
            # Calculate post-tax income
            post_tax = income - tax
            post_tax_income.append(post_tax)
        
        return post_tax_income
    
    def model_tax_regime_optimization(self,
                                    income_projection: IncomeProjectionResult,
                                    old_regime_deductions: Dict[str, float] = None,
                                    new_regime_deductions: Dict[str, float] = None) -> Dict[str, IncomeProjectionResult]:
        """
        Compare old vs. new tax regimes to identify the optimal choice for each year.
        
        Parameters:
        -----------
        income_projection : IncomeProjectionResult
            Income projection to analyze
        old_regime_deductions : Dict[str, float], optional
            Deductions applicable under the old regime
        new_regime_deductions : Dict[str, float], optional
            Deductions applicable under the new regime
            
        Returns:
        --------
        Dict[str, IncomeProjectionResult]
            Dictionary with results for old regime, new regime, and optimal regime
        """
        # Create filing status objects for both regimes
        old_filing_status = FilingStatus(regime=TaxRegime.OLD)
        new_filing_status = FilingStatus(regime=TaxRegime.NEW)
        
        # Store the original projection
        original_projection = income_projection
        
        # Calculate after-tax income for old regime
        old_regime_after_tax = self.calculate_post_tax_income(
            original_projection.total_income,
            old_filing_status
        )
        
        old_regime_result = IncomeProjectionResult(
            years=original_projection.years,
            income_values=original_projection.income_values,
            total_income=original_projection.total_income,
            after_tax_income=old_regime_after_tax
        )
        
        # Calculate after-tax income for new regime
        new_regime_after_tax = self.calculate_post_tax_income(
            original_projection.total_income,
            new_filing_status
        )
        
        new_regime_result = IncomeProjectionResult(
            years=original_projection.years,
            income_values=original_projection.income_values,
            total_income=original_projection.total_income,
            after_tax_income=new_regime_after_tax
        )
        
        # Find optimal regime for each year
        optimal_after_tax = []
        optimal_regime_by_year = []
        
        for old_tax, new_tax in zip(old_regime_after_tax, new_regime_after_tax):
            if old_tax >= new_tax:
                optimal_after_tax.append(old_tax)
                optimal_regime_by_year.append("old")
            else:
                optimal_after_tax.append(new_tax)
                optimal_regime_by_year.append("new")
        
        optimal_result = IncomeProjectionResult(
            years=original_projection.years,
            income_values=original_projection.income_values,
            total_income=original_projection.total_income,
            after_tax_income=optimal_after_tax
        )
        
        # Return all results
        return {
            "old_regime": old_regime_result,
            "new_regime": new_regime_result,
            "optimal": optimal_result,
            "optimal_regime_by_year": optimal_regime_by_year
        }
    
    def project_post_retirement_income(self,
                                     retirement_corpus: float,
                                     withdrawal_rate: float = 0.04,
                                     years: int = 30,
                                     inflation_rate: Optional[float] = None,
                                     include_pension: bool = True,
                                     pension_details: Optional[PensionDetails] = None) -> IncomeProjectionResult:
        """
        Project sustainable income during retirement years.
        
        Parameters:
        -----------
        retirement_corpus : float
            Total retirement corpus at the beginning of retirement
        withdrawal_rate : float, default 0.04
            Annual withdrawal rate (4% is common)
        years : int, default 30
            Number of years to project in retirement
        inflation_rate : float, optional
            Annual inflation rate (defaults to instance inflation_rate)
        include_pension : bool, default True
            Whether to include pension income
        pension_details : PensionDetails, optional
            Details of pension benefits
            
        Returns:
        --------
        IncomeProjectionResult
            Projection of retirement income
        """
        # Use instance inflation rate if not provided
        if inflation_rate is None:
            inflation_rate = self.inflation_rate
        
        # Calculate initial withdrawal amount
        initial_withdrawal = retirement_corpus * withdrawal_rate
        
        # Initialize tracking variables
        years_list = list(range(years + 1))
        corpus_values = [retirement_corpus]
        withdrawal_values = [0]  # No withdrawal at start
        income_values = {IncomeSource.INTEREST: [initial_withdrawal]}
        
        if include_pension and pension_details:
            income_values[IncomeSource.PENSION] = [0]  # No pension at start
        
        current_corpus = retirement_corpus
        current_withdrawal = initial_withdrawal
        
        # Project year by year
        for year in range(1, years + 1):
            # Calculate corpus after withdrawal
            corpus_after_withdrawal = current_corpus - current_withdrawal
            
            # Calculate returns on remaining corpus
            returns = corpus_after_withdrawal * 0.07  # Assuming 7% returns
            
            # Update corpus
            current_corpus = corpus_after_withdrawal + returns
            
            # Adjust withdrawal for inflation
            current_withdrawal = initial_withdrawal * (1 + inflation_rate) ** year
            
            # Add pension if included
            pension_amount = 0
            if include_pension and pension_details:
                if year >= pension_details.start_age:
                    if pension_details.indexed_to_inflation:
                        pension_amount = pension_details.monthly_amount * 12 * (1 + inflation_rate) ** year
                    else:
                        pension_amount = pension_details.monthly_amount * 12 * (1 + pension_details.annual_increment_rate) ** year
                
                income_values[IncomeSource.PENSION].append(pension_amount)
            
            # Store values
            corpus_values.append(current_corpus)
            withdrawal_values.append(current_withdrawal)
            income_values[IncomeSource.INTEREST].append(current_withdrawal)
        
        # Calculate total income
        total_income = []
        for year in range(years + 1):
            year_total = sum(values[year] for values in income_values.values() if year < len(values))
            total_income.append(year_total)
        
        # Create result
        return IncomeProjectionResult(
            years=years_list,
            income_values=income_values,
            total_income=total_income
        )
    
    def integrate_pension_income(self,
                               pension_details: PensionDetails,
                               retirement_age: int,
                               life_expectancy: int,
                               current_age: int = 30) -> IncomeProjectionResult:
        """
        Project pension income from retirement to end of life.
        
        Parameters:
        -----------
        pension_details : PensionDetails
            Details of pension benefits
        retirement_age : int
            Age at retirement
        life_expectancy : int
            Expected age at end of life
        current_age : int, default 30
            Current age
            
        Returns:
        --------
        IncomeProjectionResult
            Projection of pension income
        """
        # Calculate years until retirement and total projection years
        years_to_retirement = max(0, retirement_age - current_age)
        total_years = life_expectancy - current_age
        
        # Initialize tracking variables
        years_list = list(range(total_years + 1))
        pension_values = [0] * (years_to_retirement + 1)  # No pension before retirement
        
        # Calculate pension values after retirement
        monthly_pension = pension_details.monthly_amount
        annual_pension = monthly_pension * 12
        
        for year in range(years_to_retirement + 1, total_years + 1):
            years_in_retirement = year - years_to_retirement
            
            if pension_details.indexed_to_inflation:
                # Inflation-indexed pension
                pension_amount = annual_pension * (1 + self.inflation_rate) ** years_in_retirement
            else:
                # Fixed increments
                pension_amount = annual_pension * (1 + pension_details.annual_increment_rate) ** years_in_retirement
            
            pension_values.append(pension_amount)
        
        # Create income values dictionary
        income_values = {IncomeSource.PENSION: pension_values}
        
        # Create result
        return IncomeProjectionResult(
            years=years_list,
            income_values=income_values,
            total_income=pension_values
        )
    
    def calculate_eps_pension(self,
                           salary_history: List[float],
                           years_contributed: int,
                           retirement_age: int = 58) -> float:
        """
        Calculate pension amount under Employee Pension Scheme (EPS) in India.
        
        Parameters:
        -----------
        salary_history : List[float]
            History of monthly basic salaries (last 60 months used)
        years_contributed : int
            Number of years contributed to EPS
        retirement_age : int, default 58
            Age at retirement
            
        Returns:
        --------
        float
            Monthly EPS pension amount
        """
        # EPS formula: Pension = (Average Salary × Service Period) ÷ 70
        # where Average Salary is average of last 60 months' basic salary
        # Limited to max pensionable salary of ₹15,000
        
        # Calculate average salary (limited to pensionable ceiling)
        num_months = min(60, len(salary_history))
        last_salaries = salary_history[-num_months:]
        
        capped_salaries = [min(15000, salary) for salary in last_salaries]
        average_salary = sum(capped_salaries) / len(capped_salaries)
        
        # Calculate pension amount
        pension = (average_salary * years_contributed) / 70
        
        # Minimum pension is ₹1,000 per month
        pension = max(1000, pension)
        
        return pension
    
    def _apply_inflation_adjustment_to_result(self, result: IncomeProjectionResult) -> IncomeProjectionResult:
        """
        Apply inflation adjustment to an entire projection result.
        
        Parameters:
        -----------
        result : IncomeProjectionResult
            Income projection to adjust
            
        Returns:
        --------
        IncomeProjectionResult
            Inflation-adjusted income projection
        """
        # Adjust total income
        adjusted_total = self.apply_inflation_adjustment(
            result.total_income, 
            result.years, 
            self.inflation_rate
        )
        
        # Adjust income values for each source
        adjusted_income_values = {}
        for source, values in result.income_values.items():
            adjusted_income_values[source] = self.apply_inflation_adjustment(
                values, 
                result.years, 
                self.inflation_rate
            )
        
        # Adjust after-tax income if available
        adjusted_after_tax = None
        if result.after_tax_income:
            adjusted_after_tax = self.apply_inflation_adjustment(
                result.after_tax_income,
                result.years,
                self.inflation_rate
            )
        
        # Create result with adjusted values
        return IncomeProjectionResult(
            years=result.years,
            income_values=adjusted_income_values,
            total_income=adjusted_total,
            after_tax_income=adjusted_after_tax
        )
    
    def _calculate_taxable_income(self, income: float, filing_status: FilingStatus) -> float:
        """
        Calculate taxable income after deductions based on filing status.
        
        Parameters:
        -----------
        income : float
            Gross income amount
        filing_status : FilingStatus
            Tax filing status details
            
        Returns:
        --------
        float
            Taxable income after deductions
        """
        # Start with gross income
        taxable_income = income
        
        # Apply standard deduction for salaried employees
        standard_deduction = self.get_parameter(
            "tax_deductions.standard", 
            self.INDIA_TAX_DEDUCTIONS.get("standard_deduction", 50000)
        )
        taxable_income = max(0, taxable_income - standard_deduction)
        
        # Apply regime-specific deductions
        if filing_status.regime == TaxRegime.OLD:
            # Old regime has more deductions
            
            # Section 80C (PF, ELSS, etc.)
            section_80c_limit = self.get_parameter(
                "tax_deductions.80c", 
                self.INDIA_TAX_DEDUCTIONS.get("80c", 150000)
            )
            taxable_income = max(0, taxable_income - section_80c_limit)
            
            # Section 80D (Health Insurance)
            section_80d_self = self.get_parameter(
                "tax_deductions.80d_self",
                self.INDIA_TAX_DEDUCTIONS.get("80d_self", 25000)
            )
            taxable_income = max(0, taxable_income - section_80d_self)
            
            # NPS additional deduction
            nps_deduction = self.get_parameter(
                "tax_deductions.nps_additional",
                self.INDIA_TAX_DEDUCTIONS.get("nps_additional_deduction", 50000)
            )
            taxable_income = max(0, taxable_income - nps_deduction)
        
        # New regime has fewer deductions, most already handled above
        
        return taxable_income
    
    def _calculate_tax(self, taxable_income: float, filing_status: FilingStatus) -> float:
        """
        Calculate tax amount based on taxable income and filing status.
        
        Parameters:
        -----------
        taxable_income : float
            Taxable income after deductions
        filing_status : FilingStatus
            Tax filing status details
            
        Returns:
        --------
        float
            Tax amount
        """
        # Get appropriate tax brackets
        tax_brackets = self._get_tax_brackets(filing_status.regime)
        
        # Calculate tax using progressive brackets
        tax = 0
        for lower, upper, rate in tax_brackets:
            if taxable_income > lower:
                tax_in_bracket = min(taxable_income - lower, upper - lower) * rate
                tax += tax_in_bracket
        
        # Apply surcharge for high income individuals
        if taxable_income > 5000000:  # 50L
            surcharge_rate = 0.10
            if taxable_income > 10000000:  # 1Cr
                surcharge_rate = 0.15
            if taxable_income > 20000000:  # 2Cr
                surcharge_rate = 0.25
            if taxable_income > 50000000:  # 5Cr
                surcharge_rate = 0.37
                
            tax += tax * surcharge_rate
        
        # Add health and education cess (4%)
        tax += tax * 0.04
        
        return tax
    
    def _get_tax_brackets(self, regime: TaxRegime) -> List[Tuple[float, float, float]]:
        """
        Get tax brackets based on tax regime.
        
        Parameters:
        -----------
        regime : TaxRegime
            Tax regime (old or new)
            
        Returns:
        --------
        List[Tuple[float, float, float]]
            List of (lower_limit, upper_limit, rate) tuples
        """
        # Try to get from parameters first
        param_path = f"tax_brackets.{regime.value}"
        brackets = self.get_parameter(param_path)
        
        if brackets:
            return brackets
        
        # Fall back to default brackets
        if regime == TaxRegime.OLD:
            return self.INDIA_TAX_BRACKETS_OLD
        else:  # TaxRegime.NEW
            return self.INDIA_TAX_BRACKETS_NEW
    
    def _calculate_after_tax_income(self, income_values: List[float]) -> List[float]:
        """
        Calculate after-tax income based on income values and current tax regime.
        
        Parameters:
        -----------
        income_values : List[float]
            List of total income values
            
        Returns:
        --------
        List[float]
            List of after-tax income values
        """
        # Create default filing status based on instance tax regime
        filing_status = FilingStatus(regime=self.tax_regime)
        
        # Use the more comprehensive method
        return self.calculate_post_tax_income(income_values, filing_status)
    
    def _extract_value_from_profile(self, 
                                  profile: Dict[str, Any], 
                                  possible_keys: List[str]) -> Optional[float]:
        """
        Extract a value from a user profile using multiple possible keys.
        
        Parameters:
        -----------
        profile : Dict[str, Any]
            User profile data
        possible_keys : List[str]
            List of possible keys to try
            
        Returns:
        --------
        float or None
            Extracted value, or None if not found
        """
        if not profile:
            return None
        
        # Try each key in order
        for key in possible_keys:
            # Handle nested keys with dot notation
            if '.' in key:
                parts = key.split('.')
                value = profile
                try:
                    for part in parts:
                        value = value[part]
                    return float(value) if value is not None else None
                except (KeyError, TypeError, ValueError):
                    continue
            
            # Handle direct key
            if key in profile and profile[key] is not None:
                try:
                    return float(profile[key])
                except (TypeError, ValueError):
                    continue
        
        return None
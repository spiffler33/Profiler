"""
Base Projection Module

This module provides a base class for all financial projections, establishing common
methods and utilities for projecting values over time with different contribution
patterns, applying inflation adjustments, and calculating real returns.
"""

import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class FrequencyType(Enum):
    """Enum representing different contribution frequencies"""
    ANNUAL = "annual"
    SEMI_ANNUAL = "semi_annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    BI_WEEKLY = "bi_weekly"
    WEEKLY = "weekly"


class BaseProjection:
    """
    Base class for financial projections providing common utilities and methods.
    
    This class serves as a foundation for specialized projection classes such as
    AssetProjection, IncomeProjection, and ExpenseProjection. It implements common
    methods for parameter access, value projection, inflation adjustment, and
    contribution calculations.
    """
    
    def __init__(self, parameters=None):
        """
        Initialize the projection with financial parameters.
        
        Parameters:
        -----------
        parameters : object, optional
            Financial parameters object used for accessing projection settings.
            If None, will attempt to load parameters from the default source.
        """
        self.parameters = parameters
        
        # Try to load parameters if not provided
        if self.parameters is None:
            try:
                from models.financial_parameters import get_parameters
                self.parameters = get_parameters()
            except ImportError:
                logger.warning("Financial parameters module not found. Using default values.")
                self.parameters = {}
    
    def get_parameter(self, param_path: str, default_value: any = None, user_id: str = None) -> any:
        """
        Get a parameter value using standardized parameter access pattern.
        
        Parameters:
        -----------
        param_path : str
            The hierarchical path to the parameter (dot notation)
        default_value : any, optional
            Default value to return if parameter not found
        user_id : str, optional
            User ID for personalized parameters
            
        Returns:
        --------
        any
            The parameter value or default if not found
        """
        # If parameters is a dictionary, use simple dictionary access
        if isinstance(self.parameters, dict):
            return self.parameters.get(param_path, default_value)
        
        # Try to use the get_parameter method if available
        if hasattr(self.parameters, 'get_parameter'):
            return self.parameters.get_parameter(param_path, default_value, user_id)
        
        # Fall back to using get method if available
        if hasattr(self.parameters, 'get'):
            return self.parameters.get(param_path, default_value)
            
        # If all else fails, return the default value
        return default_value
    
    def project_values(self, 
                      initial_amount: float, 
                      annual_contributions: float, 
                      years: int, 
                      rate_func: Union[float, Callable[[int], float]],
                      contribution_frequency: Union[str, FrequencyType] = FrequencyType.ANNUAL,
                      start_year: int = 0) -> Tuple[List[int], List[float]]:
        """
        Project values over time using contributions and growth rate.
        
        This template method provides a foundation for various projection types.
        
        Parameters:
        -----------
        initial_amount : float
            Starting value
        annual_contributions : float
            Annual contribution amount
        years : int
            Number of years to project
        rate_func : float or callable
            Annual rate of return or a function that returns the rate for a given year
        contribution_frequency : str or FrequencyType, optional
            Frequency of contributions (default is annual)
        start_year : int, optional
            Starting year index (for projections that don't start at 0)
            
        Returns:
        --------
        Tuple[List[int], List[float]]
            Years and projected values
        """
        # Initialize tracking variables
        years_list = list(range(start_year, start_year + years + 1))
        values = [initial_amount]
        current_value = initial_amount
        
        # Convert contribution frequency to enum if it's a string
        if isinstance(contribution_frequency, str):
            try:
                contribution_frequency = FrequencyType(contribution_frequency)
            except ValueError:
                contribution_frequency = FrequencyType.ANNUAL
                logger.warning(f"Invalid contribution frequency: {contribution_frequency}. Using annual instead.")
        
        # Calculate periodic contribution based on frequency
        periodic_contribution = self.calculate_periodic_contributions(
            annual_contributions, 
            contribution_frequency
        )
        
        # Project values year by year
        for i, year in enumerate(years_list[1:], 1):
            # Get rate for this year
            if callable(rate_func):
                rate = rate_func(year)
            else:
                rate = rate_func
            
            # Calculate growth for this period before adding contributions
            growth = current_value * rate
            
            # Add growth and contributions to current value
            current_value = current_value + growth + periodic_contribution * self._get_periods_per_year(contribution_frequency)
            
            # Store the value for this year
            values.append(current_value)
        
        return years_list, values
    
    def apply_inflation_adjustment(self, 
                                  projected_values: List[float], 
                                  years: List[int], 
                                  inflation_rate: float) -> List[float]:
        """
        Adjust projected values to account for inflation.
        
        Parameters:
        -----------
        projected_values : List[float]
            Values to adjust for inflation
        years : List[int]
            Years corresponding to the projected values
        inflation_rate : float
            Annual inflation rate
            
        Returns:
        --------
        List[float]
            Inflation-adjusted values in real terms
        """
        # Create inflation discount factors for each year
        inflation_factors = [(1 / (1 + inflation_rate)) ** year for year in years]
        
        # Apply inflation adjustment to all values
        real_values = [value * factor for value, factor in zip(projected_values, inflation_factors)]
        
        return real_values
    
    def calculate_real_returns(self, 
                              nominal_returns: Union[float, Dict[str, float]], 
                              inflation_rate: float) -> Union[float, Dict[str, float]]:
        """
        Calculate real (inflation-adjusted) returns from nominal returns.
        
        Parameters:
        -----------
        nominal_returns : float or Dict[str, float]
            Nominal return rate(s)
        inflation_rate : float
            Annual inflation rate
            
        Returns:
        --------
        float or Dict[str, float]
            Real return rate(s)
        """
        # For a simple float value
        if isinstance(nominal_returns, (int, float)):
            real_return = (1 + nominal_returns) / (1 + inflation_rate) - 1
            return real_return
        
        # For a dictionary of values
        if isinstance(nominal_returns, dict):
            real_returns = {}
            for key, nominal_return in nominal_returns.items():
                real_returns[key] = (1 + nominal_return) / (1 + inflation_rate) - 1
            return real_returns
        
        # Return as-is for other types
        return nominal_returns
    
    def calculate_periodic_contributions(self, 
                                        annual_amount: float, 
                                        frequency: Union[str, FrequencyType]) -> float:
        """
        Calculate contribution amount per period based on frequency.
        
        Parameters:
        -----------
        annual_amount : float
            Total annual contribution amount
        frequency : str or FrequencyType
            Contribution frequency
            
        Returns:
        --------
        float
            Contribution amount per period
        """
        # Convert string to enum if needed
        if isinstance(frequency, str):
            try:
                frequency = FrequencyType(frequency)
            except ValueError:
                frequency = FrequencyType.ANNUAL
                logger.warning(f"Invalid frequency: {frequency}. Using annual instead.")
        
        # Get number of periods per year
        periods_per_year = self._get_periods_per_year(frequency)
        
        # Calculate contribution per period
        return annual_amount / periods_per_year
    
    def _get_periods_per_year(self, frequency: FrequencyType) -> int:
        """
        Get the number of periods per year for a given frequency.
        
        Parameters:
        -----------
        frequency : FrequencyType
            Contribution frequency
            
        Returns:
        --------
        int
            Number of periods per year
        """
        frequency_mapping = {
            FrequencyType.ANNUAL: 1,
            FrequencyType.SEMI_ANNUAL: 2,
            FrequencyType.QUARTERLY: 4,
            FrequencyType.MONTHLY: 12,
            FrequencyType.BI_WEEKLY: 26,
            FrequencyType.WEEKLY: 52
        }
        
        return frequency_mapping.get(frequency, 1)
    
    def compound_interest(self, 
                         principal: float, 
                         rate: float, 
                         time: int, 
                         periods_per_year: int = 1) -> float:
        """
        Calculate compound interest with optional compounding frequency.
        
        Parameters:
        -----------
        principal : float
            Initial amount
        rate : float
            Annual interest rate
        time : int
            Time in years
        periods_per_year : int, optional
            Number of compounding periods per year (default is 1 for annual)
            
        Returns:
        --------
        float
            Future value after compounding
        """
        return principal * (1 + rate / periods_per_year) ** (time * periods_per_year)
    
    def calculate_present_value(self, 
                              future_value: float, 
                              rate: float, 
                              time: int, 
                              periods_per_year: int = 1) -> float:
        """
        Calculate the present value of a future amount.
        
        Parameters:
        -----------
        future_value : float
            Future amount
        rate : float
            Annual discount rate
        time : int
            Time in years
        periods_per_year : int, optional
            Number of compounding periods per year (default is 1 for annual)
            
        Returns:
        --------
        float
            Present value
        """
        return future_value / (1 + rate / periods_per_year) ** (time * periods_per_year)
    
    def calculate_required_contribution(self, 
                                       target_amount: float, 
                                       years: int, 
                                       rate: float, 
                                       initial_amount: float = 0, 
                                       frequency: Union[str, FrequencyType] = FrequencyType.ANNUAL) -> float:
        """
        Calculate required periodic contribution to reach a target amount.
        
        Parameters:
        -----------
        target_amount : float
            Target future value
        years : int
            Time in years
        rate : float
            Annual growth rate
        initial_amount : float, optional
            Starting amount (default is 0)
        frequency : str or FrequencyType, optional
            Contribution frequency (default is annual)
            
        Returns:
        --------
        float
            Required contribution per period
        """
        # Convert frequency to enum if needed
        if isinstance(frequency, str):
            try:
                frequency = FrequencyType(frequency)
            except ValueError:
                frequency = FrequencyType.ANNUAL
        
        # Calculate periods and rate per period
        periods_per_year = self._get_periods_per_year(frequency)
        total_periods = years * periods_per_year
        rate_per_period = rate / periods_per_year
        
        # Calculate future value of initial amount
        future_value_of_initial = initial_amount * (1 + rate_per_period) ** total_periods
        
        # Calculate how much more we need from contributions
        remaining_amount = target_amount - future_value_of_initial
        
        if remaining_amount <= 0:
            return 0  # Initial amount will exceed target, no contributions needed
        
        # Formula for PMT (regular payment amount)
        # PMT = FV * rate / ((1 + rate)^n - 1)
        denominator = ((1 + rate_per_period) ** total_periods - 1) / rate_per_period
        
        # Calculate required payment per period
        payment_per_period = remaining_amount / denominator
        
        return payment_per_period
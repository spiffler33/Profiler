"""
Asset Projection Module

This module provides tools for projecting asset growth over time with various
configurations including different asset classes, allocation strategies, 
contribution patterns, and risk modeling capabilities.
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

class AssetClass(Enum):
    """Enum representing different asset classes for allocation"""
    EQUITY = "equity"
    DEBT = "debt" 
    GOLD = "gold"
    REAL_ESTATE = "real_estate"
    CASH = "cash"

class RiskProfile(Enum):
    """Enum representing different risk profiles for returns"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

@dataclass
class ProjectionResult:
    """Data class for storing and visualizing projection results"""
    years: List[int]
    projected_values: List[float]
    contributions: List[float]
    growth: List[float]
    
    # Optional risk metrics
    confidence_intervals: Optional[Dict[str, List[float]]] = None
    volatility: Optional[float] = None
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert projection result to pandas DataFrame for analysis/visualization"""
        df = pd.DataFrame({
            'Year': self.years,
            'Projected_Value': self.projected_values,
            'Contributions': self.contributions,
            'Growth': self.growth
        })
        
        # Add confidence intervals if available
        if self.confidence_intervals:
            for label, values in self.confidence_intervals.items():
                df[f'CI_{label}'] = values
                
        return df

@dataclass
class AssetAllocation:
    """Data class for defining asset allocation percentages"""
    equity: float = 0.0
    debt: float = 0.0
    gold: float = 0.0
    real_estate: float = 0.0
    cash: float = 0.0
    
    def __post_init__(self):
        """Validate allocation percentages after initialization"""
        total = self.equity + self.debt + self.gold + self.real_estate + self.cash
        if not 0.99 <= total <= 1.01:
            logger.warning(f"Asset allocation does not sum to 1.0 (actual: {total})")
    
    def to_dict(self) -> Dict[AssetClass, float]:
        """Convert allocation to dictionary with AssetClass keys"""
        return {
            AssetClass.EQUITY: self.equity,
            AssetClass.DEBT: self.debt,
            AssetClass.GOLD: self.gold,
            AssetClass.REAL_ESTATE: self.real_estate,
            AssetClass.CASH: self.cash
        }
    
    @classmethod
    def from_dict(cls, allocation_dict: Dict[Union[AssetClass, str], float]) -> 'AssetAllocation':
        """Create allocation from dictionary"""
        # Convert string keys to AssetClass enum if needed
        cleaned_dict = {}
        for key, value in allocation_dict.items():
            if isinstance(key, str):
                try:
                    asset_class = AssetClass(key)
                except ValueError:
                    logger.warning(f"Unknown asset class: {key}")
                    continue
                cleaned_dict[asset_class] = value
            else:
                cleaned_dict[key] = value
        
        # Create allocation with values from dictionary (defaulting to 0 if not present)
        return cls(
            equity=cleaned_dict.get(AssetClass.EQUITY, 0.0),
            debt=cleaned_dict.get(AssetClass.DEBT, 0.0),
            gold=cleaned_dict.get(AssetClass.GOLD, 0.0),
            real_estate=cleaned_dict.get(AssetClass.REAL_ESTATE, 0.0),
            cash=cleaned_dict.get(AssetClass.CASH, 0.0)
        )


class AssetProjection(BaseProjection):
    """
    Class for projecting asset growth across multiple asset classes,
    with support for different allocation strategies, contribution patterns,
    and risk modeling.
    
    This class is specifically tailored for Indian market conditions, with
    proper handling of gold as an important asset class and appropriate
    volatility parameters for the Indian market.
    """
    
    # Default annual returns (mean, volatility) by asset class and risk profile
    # Tailored for Indian market conditions
    DEFAULT_RETURNS = {
        RiskProfile.CONSERVATIVE: {
            AssetClass.EQUITY: (0.09, 0.16),       # 9% return, 16% volatility
            AssetClass.DEBT: (0.06, 0.05),         # 6% return, 5% volatility
            AssetClass.GOLD: (0.07, 0.15),         # 7% return, 15% volatility
            AssetClass.REAL_ESTATE: (0.07, 0.10),  # 7% return, 10% volatility
            AssetClass.CASH: (0.04, 0.01),         # 4% return, 1% volatility
        },
        RiskProfile.MODERATE: {
            AssetClass.EQUITY: (0.12, 0.18),       # 12% return, 18% volatility
            AssetClass.DEBT: (0.07, 0.06),         # 7% return, 6% volatility
            AssetClass.GOLD: (0.08, 0.15),         # 8% return, 15% volatility
            AssetClass.REAL_ESTATE: (0.09, 0.12),  # 9% return, 12% volatility
            AssetClass.CASH: (0.04, 0.01),         # 4% return, 1% volatility
        },
        RiskProfile.AGGRESSIVE: {
            AssetClass.EQUITY: (0.14, 0.22),       # 14% return, 22% volatility
            AssetClass.DEBT: (0.08, 0.07),         # 8% return, 7% volatility
            AssetClass.GOLD: (0.09, 0.16),         # 9% return, 16% volatility
            AssetClass.REAL_ESTATE: (0.10, 0.14),  # 10% return, 14% volatility
            AssetClass.CASH: (0.04, 0.01),         # 4% return, 1% volatility
        }
    }
    
    # Indian market correlation matrix between asset classes
    # Based on historical data and financial research
    DEFAULT_CORRELATIONS = {
        (AssetClass.EQUITY, AssetClass.DEBT): 0.2,
        (AssetClass.EQUITY, AssetClass.GOLD): -0.1,      # Negative correlation - gold as hedge
        (AssetClass.EQUITY, AssetClass.REAL_ESTATE): 0.5,
        (AssetClass.EQUITY, AssetClass.CASH): 0.0,
        (AssetClass.DEBT, AssetClass.GOLD): 0.3,
        (AssetClass.DEBT, AssetClass.REAL_ESTATE): 0.4,
        (AssetClass.DEBT, AssetClass.CASH): 0.5,
        (AssetClass.GOLD, AssetClass.REAL_ESTATE): 0.2,
        (AssetClass.GOLD, AssetClass.CASH): 0.1,
        (AssetClass.REAL_ESTATE, AssetClass.CASH): 0.0,
    }
    
    def __init__(self, 
                 parameters=None, 
                 risk_profile: Union[str, RiskProfile] = RiskProfile.MODERATE,
                 inflation_rate: float = 0.06,   # 6% is typical for India
                 rebalancing_frequency: Optional[str] = "annual",
                 seed: Optional[int] = None):
        """
        Initialize the asset projection model with parameters.
        
        Parameters:
        -----------
        parameters : object, optional
            Financial parameters object for accessing system settings
        risk_profile : str or RiskProfile, default RiskProfile.MODERATE
            Risk profile to use for default returns
        inflation_rate : float, default 0.06
            Annual inflation rate for real return calculations
        rebalancing_frequency : str, optional
            Frequency of portfolio rebalancing ('annual', 'quarterly', 'monthly', or None)
        seed : int, optional
            Random seed for Monte Carlo simulations
        """
        super().__init__(parameters)
        
        # Convert risk profile to enum if it's a string
        if isinstance(risk_profile, str):
            try:
                self.risk_profile = RiskProfile(risk_profile)
            except ValueError:
                logger.warning(f"Invalid risk profile: {risk_profile}. Using MODERATE instead.")
                self.risk_profile = RiskProfile.MODERATE
        else:
            self.risk_profile = risk_profile
            
        self.inflation_rate = inflation_rate
        self.rebalancing_frequency = rebalancing_frequency
        
        # Set random seed if provided
        if seed is not None:
            np.random.seed(seed)
    
    def get_asset_return(self, 
                        asset_class: Union[str, AssetClass], 
                        risk_profile: Union[str, RiskProfile] = None,
                        user_id: str = None) -> Tuple[float, float]:
        """
        Get expected return and volatility for an asset class.
        
        Parameters:
        -----------
        asset_class : str or AssetClass
            Asset class to get returns for
        risk_profile : str or RiskProfile, optional
            Risk profile to use (defaults to instance risk_profile)
        user_id : str, optional
            User ID for personalized parameters
            
        Returns:
        --------
        Tuple[float, float]
            (expected_return, volatility) for the asset class
        """
        # Convert asset_class to enum if it's a string
        if isinstance(asset_class, str):
            try:
                asset_class = AssetClass(asset_class)
            except ValueError:
                logger.error(f"Invalid asset class: {asset_class}")
                return (0.0, 0.0)
        
        # Use instance risk profile if not specified
        if risk_profile is None:
            risk_profile = self.risk_profile
        elif isinstance(risk_profile, str):
            try:
                risk_profile = RiskProfile(risk_profile)
            except ValueError:
                logger.warning(f"Invalid risk profile: {risk_profile}. Using {self.risk_profile.value} instead.")
                risk_profile = self.risk_profile
        
        # Try to get returns from parameter service first
        param_path = f"asset_returns.{asset_class.value}.{risk_profile.value}"
        return_value = self.get_parameter(param_path, None, user_id)
        
        if return_value is not None:
            # If parameter service returns a value with volatility, use it
            if isinstance(return_value, (tuple, list)) and len(return_value) >= 2:
                return return_value[0], return_value[1]
            
            # If parameter only has return but no volatility, get volatility from defaults
            volatility = self.DEFAULT_RETURNS[risk_profile][asset_class][1]
            return return_value, volatility
        
        # Fall back to defaults if parameter not found
        if asset_class in self.DEFAULT_RETURNS[risk_profile]:
            return self.DEFAULT_RETURNS[risk_profile][asset_class]
        
        # Last resort default
        logger.warning(f"No return data for {asset_class.value} with {risk_profile.value} profile")
        return (0.05, 0.05)
    
    def project_asset_growth(self, 
                            initial_amount: float,
                            annual_contributions: float,
                            years: int,
                            allocation: Union[Dict[Union[str, AssetClass], float], AssetAllocation],
                            contribution_frequency: Union[str, FrequencyType] = FrequencyType.MONTHLY,
                            include_inflation_adjustment: bool = False) -> ProjectionResult:
        """
        Project asset growth over time with the given allocation.
        
        Parameters:
        -----------
        initial_amount : float
            Starting value of the assets
        annual_contributions : float
            Annual contribution amount
        years : int
            Number of years to project
        allocation : Dict or AssetAllocation
            Asset allocation to use for projections
        contribution_frequency : str or FrequencyType, default FrequencyType.MONTHLY
            Frequency of contributions
        include_inflation_adjustment : bool, default False
            Whether to adjust values for inflation
            
        Returns:
        --------
        ProjectionResult
            Object containing projection results
        """
        # Convert allocation to AssetAllocation if it's a dictionary
        if isinstance(allocation, dict):
            allocation = AssetAllocation.from_dict(allocation)
        
        # Calculate expected portfolio return based on allocation
        expected_return = self._calculate_portfolio_return(allocation)
        
        # Apply rebalancing benefit if enabled
        if self.rebalancing_frequency:
            rebalancing_benefit = self._calculate_rebalancing_benefit(allocation)
            expected_return += rebalancing_benefit
        
        # Project values using base class method
        years_list, values = self.project_values(
            initial_amount=initial_amount,
            annual_contributions=annual_contributions,
            years=years,
            rate_func=expected_return,
            contribution_frequency=contribution_frequency
        )
        
        # Calculate contributions
        contributions = [0]  # No contribution at start
        periodic_contribution = self.calculate_periodic_contributions(
            annual_contributions, 
            contribution_frequency
        )
        periods_per_year = self._get_periods_per_year(
            contribution_frequency if isinstance(contribution_frequency, FrequencyType) 
            else FrequencyType(contribution_frequency)
        )
        annual_contribution = periodic_contribution * periods_per_year
        
        for _ in range(years):
            contributions.append(annual_contribution)
        
        # Calculate growth (value increase minus contribution)
        growth = [0]  # No growth at start
        for i in range(1, len(values)):
            growth_value = values[i] - values[i-1] - contributions[i]
            growth.append(growth_value)
        
        # Create result object
        result = ProjectionResult(
            years=years_list,
            projected_values=values,
            contributions=contributions,
            growth=growth
        )
        
        # Apply inflation adjustment if requested
        if include_inflation_adjustment:
            adjusted_values = self.apply_inflation_adjustment(
                result.projected_values, 
                result.years, 
                self.inflation_rate
            )
            adjusted_contributions = self.apply_inflation_adjustment(
                result.contributions, 
                result.years, 
                self.inflation_rate
            )
            adjusted_growth = self.apply_inflation_adjustment(
                result.growth, 
                result.years, 
                self.inflation_rate
            )
            
            result = ProjectionResult(
                years=result.years,
                projected_values=adjusted_values,
                contributions=adjusted_contributions,
                growth=adjusted_growth
            )
        
        return result
    
    def project_allocation_growth(self,
                                 allocation: Union[Dict[Union[str, AssetClass], float], AssetAllocation],
                                 initial_amount: float,
                                 annual_contributions: float,
                                 years: int,
                                 contribution_frequency: Union[str, FrequencyType] = FrequencyType.MONTHLY) -> Dict[AssetClass, ProjectionResult]:
        """
        Project growth for each asset class in an allocation.
        
        Parameters:
        -----------
        allocation : Dict or AssetAllocation
            Asset allocation to use for projections
        initial_amount : float
            Starting value of the assets
        annual_contributions : float
            Annual contribution amount
        years : int
            Number of years to project
        contribution_frequency : str or FrequencyType, default FrequencyType.MONTHLY
            Frequency of contributions
            
        Returns:
        --------
        Dict[AssetClass, ProjectionResult]
            Dictionary mapping asset classes to their projection results
        """
        # Convert allocation to AssetAllocation if it's a dictionary
        if isinstance(allocation, dict):
            allocation = AssetAllocation.from_dict(allocation)
        
        # Get allocation as dictionary
        allocation_dict = allocation.to_dict()
        
        # Project each asset class separately
        results = {}
        
        for asset_class, alloc_percent in allocation_dict.items():
            if alloc_percent > 0:
                # Calculate initial amount for this asset class
                asset_initial = initial_amount * alloc_percent
                
                # Calculate contributions for this asset class
                asset_contributions = annual_contributions * alloc_percent
                
                # Project based on asset class type
                if asset_class == AssetClass.EQUITY:
                    result = self.project_equity_growth(
                        amount=asset_initial,
                        allocation_percent=alloc_percent,
                        annual_contributions=asset_contributions,
                        years=years,
                        contribution_frequency=contribution_frequency
                    )
                elif asset_class == AssetClass.DEBT:
                    result = self.project_debt_growth(
                        amount=asset_initial,
                        allocation_percent=alloc_percent,
                        annual_contributions=asset_contributions,
                        years=years,
                        contribution_frequency=contribution_frequency
                    )
                elif asset_class == AssetClass.GOLD:
                    result = self.project_gold_growth(
                        amount=asset_initial,
                        allocation_percent=alloc_percent,
                        annual_contributions=asset_contributions,
                        years=years,
                        contribution_frequency=contribution_frequency
                    )
                elif asset_class == AssetClass.REAL_ESTATE:
                    result = self.project_real_estate_growth(
                        amount=asset_initial,
                        allocation_percent=alloc_percent,
                        annual_contributions=asset_contributions,
                        years=years,
                        contribution_frequency=contribution_frequency
                    )
                else:  # Cash or other
                    result = self.project_cash_growth(
                        amount=asset_initial,
                        allocation_percent=alloc_percent,
                        annual_contributions=asset_contributions,
                        years=years,
                        contribution_frequency=contribution_frequency
                    )
                
                results[asset_class] = result
        
        return results
    
    def project_equity_growth(self,
                             amount: float,
                             allocation_percent: float,
                             annual_contributions: float,
                             years: int,
                             contribution_frequency: Union[str, FrequencyType] = FrequencyType.MONTHLY) -> ProjectionResult:
        """
        Project growth for equity investments.
        
        Parameters:
        -----------
        amount : float
            Initial amount invested in equity
        allocation_percent : float
            Percentage of portfolio allocated to equity
        annual_contributions : float
            Annual contribution amount for equity
        years : int
            Number of years to project
        contribution_frequency : str or FrequencyType, default FrequencyType.MONTHLY
            Frequency of contributions
            
        Returns:
        --------
        ProjectionResult
            Projection result for equity investments
        """
        # Get equity returns
        equity_return, _ = self.get_asset_return(AssetClass.EQUITY, self.risk_profile)
        
        # Project using base method
        return self._project_asset_class_growth(
            amount=amount,
            annual_contributions=annual_contributions,
            years=years,
            return_rate=equity_return,
            contribution_frequency=contribution_frequency
        )
    
    def project_debt_growth(self,
                           amount: float,
                           allocation_percent: float,
                           annual_contributions: float,
                           years: int,
                           contribution_frequency: Union[str, FrequencyType] = FrequencyType.MONTHLY) -> ProjectionResult:
        """
        Project growth for debt instruments.
        
        Parameters:
        -----------
        amount : float
            Initial amount invested in debt
        allocation_percent : float
            Percentage of portfolio allocated to debt
        annual_contributions : float
            Annual contribution amount for debt
        years : int
            Number of years to project
        contribution_frequency : str or FrequencyType, default FrequencyType.MONTHLY
            Frequency of contributions
            
        Returns:
        --------
        ProjectionResult
            Projection result for debt investments
        """
        # Get debt returns
        debt_return, _ = self.get_asset_return(AssetClass.DEBT, self.risk_profile)
        
        # Project using base method
        return self._project_asset_class_growth(
            amount=amount,
            annual_contributions=annual_contributions,
            years=years,
            return_rate=debt_return,
            contribution_frequency=contribution_frequency
        )
    
    def project_gold_growth(self,
                           amount: float,
                           allocation_percent: float,
                           annual_contributions: float,
                           years: int,
                           contribution_frequency: Union[str, FrequencyType] = FrequencyType.MONTHLY) -> ProjectionResult:
        """
        Project growth for gold investments.
        
        Parameters:
        -----------
        amount : float
            Initial amount invested in gold
        allocation_percent : float
            Percentage of portfolio allocated to gold
        annual_contributions : float
            Annual contribution amount for gold
        years : int
            Number of years to project
        contribution_frequency : str or FrequencyType, default FrequencyType.MONTHLY
            Frequency of contributions
            
        Returns:
        --------
        ProjectionResult
            Projection result for gold investments
        """
        # Get gold returns
        gold_return, _ = self.get_asset_return(AssetClass.GOLD, self.risk_profile)
        
        # Project using base method
        return self._project_asset_class_growth(
            amount=amount,
            annual_contributions=annual_contributions,
            years=years,
            return_rate=gold_return,
            contribution_frequency=contribution_frequency
        )
    
    def project_real_estate_growth(self,
                                  amount: float,
                                  allocation_percent: float,
                                  annual_contributions: float,
                                  years: int,
                                  contribution_frequency: Union[str, FrequencyType] = FrequencyType.MONTHLY) -> ProjectionResult:
        """
        Project growth for real estate investments.
        
        Parameters:
        -----------
        amount : float
            Initial amount invested in real estate
        allocation_percent : float
            Percentage of portfolio allocated to real estate
        annual_contributions : float
            Annual contribution amount for real estate
        years : int
            Number of years to project
        contribution_frequency : str or FrequencyType, default FrequencyType.MONTHLY
            Frequency of contributions
            
        Returns:
        --------
        ProjectionResult
            Projection result for real estate investments
        """
        # Get real estate returns
        real_estate_return, _ = self.get_asset_return(AssetClass.REAL_ESTATE, self.risk_profile)
        
        # Project using base method
        return self._project_asset_class_growth(
            amount=amount,
            annual_contributions=annual_contributions,
            years=years,
            return_rate=real_estate_return,
            contribution_frequency=contribution_frequency
        )
    
    def project_cash_growth(self,
                           amount: float,
                           allocation_percent: float,
                           annual_contributions: float,
                           years: int,
                           contribution_frequency: Union[str, FrequencyType] = FrequencyType.MONTHLY) -> ProjectionResult:
        """
        Project growth for cash investments.
        
        Parameters:
        -----------
        amount : float
            Initial amount in cash
        allocation_percent : float
            Percentage of portfolio allocated to cash
        annual_contributions : float
            Annual contribution amount for cash
        years : int
            Number of years to project
        contribution_frequency : str or FrequencyType, default FrequencyType.MONTHLY
            Frequency of contributions
            
        Returns:
        --------
        ProjectionResult
            Projection result for cash investments
        """
        # Get cash returns
        cash_return, _ = self.get_asset_return(AssetClass.CASH, self.risk_profile)
        
        # Project using base method
        return self._project_asset_class_growth(
            amount=amount,
            annual_contributions=annual_contributions,
            years=years,
            return_rate=cash_return,
            contribution_frequency=contribution_frequency
        )
    
    def _project_asset_class_growth(self,
                                   amount: float,
                                   annual_contributions: float,
                                   years: int,
                                   return_rate: float,
                                   contribution_frequency: Union[str, FrequencyType] = FrequencyType.MONTHLY) -> ProjectionResult:
        """
        Helper method to project growth for a specific asset class.
        
        Parameters:
        -----------
        amount : float
            Initial amount invested
        annual_contributions : float
            Annual contribution amount
        years : int
            Number of years to project
        return_rate : float
            Annual return rate for the asset class
        contribution_frequency : str or FrequencyType, default FrequencyType.MONTHLY
            Frequency of contributions
            
        Returns:
        --------
        ProjectionResult
            Projection result for the asset class
        """
        # Project values using base class method
        years_list, values = self.project_values(
            initial_amount=amount,
            annual_contributions=annual_contributions,
            years=years,
            rate_func=return_rate,
            contribution_frequency=contribution_frequency
        )
        
        # Calculate contributions
        contributions = [0]  # No contribution at start
        periodic_contribution = self.calculate_periodic_contributions(
            annual_contributions, 
            contribution_frequency
        )
        periods_per_year = self._get_periods_per_year(
            contribution_frequency if isinstance(contribution_frequency, FrequencyType) 
            else FrequencyType(contribution_frequency)
        )
        annual_contribution = periodic_contribution * periods_per_year
        
        for _ in range(years):
            contributions.append(annual_contribution)
        
        # Calculate growth (value increase minus contribution)
        growth = [0]  # No growth at start
        for i in range(1, len(values)):
            growth_value = values[i] - values[i-1] - contributions[i]
            growth.append(growth_value)
        
        # Create result object
        return ProjectionResult(
            years=years_list,
            projected_values=values,
            contributions=contributions,
            growth=growth
        )
    
    def run_monte_carlo(self,
                       initial_amount: float,
                       annual_contributions: float,
                       years: int,
                       allocation: Union[Dict[Union[str, AssetClass], float], AssetAllocation],
                       runs: int = 1000,
                       confidence_levels: List[float] = [0.05, 0.25, 0.50, 0.75, 0.95],
                       contribution_frequency: Union[str, FrequencyType] = FrequencyType.MONTHLY) -> ProjectionResult:
        """
        Run Monte Carlo simulation to model market uncertainty.
        
        Parameters:
        -----------
        initial_amount : float
            Starting value of the assets
        annual_contributions : float
            Annual contribution amount
        years : int
            Number of years to project
        allocation : Dict or AssetAllocation
            Asset allocation to use for projections
        runs : int, default 1000
            Number of simulation runs
        confidence_levels : List[float], default [0.05, 0.25, 0.50, 0.75, 0.95]
            Percentiles to calculate for confidence intervals
        contribution_frequency : str or FrequencyType, default FrequencyType.MONTHLY
            Frequency of contributions
            
        Returns:
        --------
        ProjectionResult
            Projection result with confidence intervals
        """
        # Convert allocation to AssetAllocation if it's a dictionary
        if isinstance(allocation, dict):
            allocation = AssetAllocation.from_dict(allocation)
        
        # Convert contribution frequency to enum if it's a string
        if isinstance(contribution_frequency, str):
            try:
                contribution_frequency = FrequencyType(contribution_frequency)
            except ValueError:
                contribution_frequency = FrequencyType.MONTHLY
                logger.warning(f"Invalid contribution frequency: {contribution_frequency}. Using monthly instead.")
        
        # Calculate periodic contribution
        periodic_contribution = self.calculate_periodic_contributions(
            annual_contributions, 
            contribution_frequency
        )
        periods_per_year = self._get_periods_per_year(contribution_frequency)
        
        # Initialize results array for all simulations
        all_simulations = np.zeros((runs, years + 1))
        all_simulations[:, 0] = initial_amount  # Set initial amount for all simulations
        
        # Get returns and volatilities for each asset class
        returns_volatilities = {}
        for asset_class in allocation.to_dict():
            returns_volatilities[asset_class] = self.get_asset_return(asset_class, self.risk_profile)
        
        # Get correlation matrix
        correlation_matrix = self._get_correlation_matrix(allocation.to_dict().keys())
        
        # Run simulations
        for sim in range(runs):
            current_value = initial_amount
            
            for year in range(1, years + 1):
                # Simulate correlated returns for this year
                simulated_returns = self._simulate_correlated_returns(
                    allocation.to_dict(),
                    returns_volatilities,
                    correlation_matrix
                )
                
                # Calculate portfolio return for this year
                portfolio_return = 0
                for asset_class, alloc_percent in allocation.to_dict().items():
                    if alloc_percent > 0:
                        portfolio_return += alloc_percent * simulated_returns[asset_class]
                
                # Apply return to current value
                current_value = current_value * (1 + portfolio_return)
                
                # Add contributions
                current_value += periodic_contribution * periods_per_year
                
                # Store result for this year
                all_simulations[sim, year] = current_value
        
        # Calculate median projection (50th percentile)
        median_idx = runs // 2
        median_simulation = np.median(all_simulations, axis=0)
        
        # Calculate contributions (same for all simulations)
        contributions = [0]  # No contribution at start
        annual_contribution = periodic_contribution * periods_per_year
        for _ in range(years):
            contributions.append(annual_contribution)
        
        # Calculate growth based on median values
        growth = [0]  # No growth at start
        for year in range(1, years + 1):
            growth_value = median_simulation[year] - median_simulation[year-1] - contributions[year]
            growth.append(growth_value)
        
        # Calculate confidence intervals
        confidence_intervals = {}
        for level in confidence_levels:
            percentile = int(level * 100)
            confidence_intervals[f"P{percentile}"] = np.percentile(all_simulations, percentile, axis=0)
        
        # Calculate overall volatility
        final_values = all_simulations[:, -1]
        volatility = np.std(final_values) / np.mean(final_values)  # Coefficient of variation
        
        # Create result object
        return ProjectionResult(
            years=list(range(years + 1)),
            projected_values=list(median_simulation),
            contributions=contributions,
            growth=growth,
            confidence_intervals=confidence_intervals,
            volatility=volatility
        )
    
    def calculate_volatility_metrics(self, 
                                    projection_result: ProjectionResult) -> Dict[str, float]:
        """
        Calculate volatility metrics for a projection result.
        
        Parameters:
        -----------
        projection_result : ProjectionResult
            Projection result to analyze
            
        Returns:
        --------
        Dict[str, float]
            Dictionary of volatility metrics
        """
        metrics = {}
        
        # Use volatility if already calculated
        if projection_result.volatility is not None:
            metrics['coefficient_of_variation'] = projection_result.volatility
        
        # Calculate metrics from confidence intervals if available
        if projection_result.confidence_intervals:
            try:
                # Calculate annual volatility from confidence intervals
                # Using 90% confidence interval (P95 - P5) divided by 1.65 (90% in normal distribution)
                p95 = projection_result.confidence_intervals.get('P95', [])
                p5 = projection_result.confidence_intervals.get('P5', [])
                
                if p95 and p5 and len(p95) == len(p5):
                    final_p95 = p95[-1]
                    final_p5 = p5[-1]
                    range_90 = final_p95 - final_p5
                    
                    # Approximate annual volatility
                    metrics['annual_volatility_estimate'] = range_90 / (1.65 * 2 * projection_result.projected_values[-1])
                    
                    # Maximum drawdown estimate (based on worst-case scenario)
                    metrics['max_drawdown_estimate'] = (projection_result.projected_values[-1] - final_p5) / projection_result.projected_values[-1]
                    
                    # Downside risk (how far below median the P5 value is)
                    metrics['downside_risk'] = (projection_result.projected_values[-1] - final_p5) / projection_result.projected_values[-1]
                    
                    # Upside potential (how far above median the P95 value is)
                    metrics['upside_potential'] = (final_p95 - projection_result.projected_values[-1]) / projection_result.projected_values[-1]
            except Exception as e:
                logger.warning(f"Error calculating volatility metrics: {e}")
        
        return metrics
    
    def generate_confidence_intervals(self, 
                                    projection_result: ProjectionResult, 
                                    confidence_levels: List[float] = [0.95, 0.75, 0.5, 0.25, 0.05]) -> Dict[str, List[float]]:
        """
        Generate confidence intervals for risk visualization.
        
        Parameters:
        -----------
        projection_result : ProjectionResult
            Projection result to analyze
        confidence_levels : List[float], default [0.95, 0.75, 0.5, 0.25, 0.05]
            Confidence levels to generate
            
        Returns:
        --------
        Dict[str, List[float]]
            Dictionary mapping confidence level names to interval values
        """
        # If projection already has confidence intervals, use them
        if projection_result.confidence_intervals:
            return projection_result.confidence_intervals
        
        # Otherwise, we need to estimate confidence intervals
        intervals = {}
        
        # Get the projected values and time horizon
        values = projection_result.projected_values
        years = len(values) - 1
        
        # Estimate volatility (if not provided)
        volatility = projection_result.volatility
        if volatility is None:
            # Estimate volatility using a simplified approach based on risk profile
            if self.risk_profile == RiskProfile.CONSERVATIVE:
                volatility = 0.08
            elif self.risk_profile == RiskProfile.MODERATE:
                volatility = 0.12
            else:  # AGGRESSIVE
                volatility = 0.18
        
        # Generate confidence intervals for each confidence level
        for level in confidence_levels:
            # Convert to Z-score from normal distribution
            z_score = self._confidence_to_z_score(level)
            
            # Calculate interval values
            interval_values = []
            
            for year, value in enumerate(values):
                if year == 0:
                    # No uncertainty at starting point
                    interval_values.append(value)
                else:
                    # Uncertainty increases with square root of time
                    year_volatility = volatility * math.sqrt(year)
                    # Calculate interval value (using log-normal distribution)
                    interval_value = value * math.exp(z_score * year_volatility)
                    interval_values.append(interval_value)
            
            # Store interval
            intervals[f"P{int(level * 100)}"] = interval_values
        
        return intervals
    
    def _calculate_portfolio_return(self, allocation: AssetAllocation) -> float:
        """
        Calculate expected portfolio return based on asset allocation.
        
        Parameters:
        -----------
        allocation : AssetAllocation
            Asset allocation
            
        Returns:
        --------
        float
            Expected portfolio return
        """
        expected_return = 0
        
        # Calculate weighted return
        for asset_class, weight in allocation.to_dict().items():
            if weight > 0:
                # Get expected return for this asset class
                asset_return, _ = self.get_asset_return(asset_class, self.risk_profile)
                expected_return += weight * asset_return
        
        return expected_return
    
    def _calculate_rebalancing_benefit(self, allocation: AssetAllocation) -> float:
        """
        Calculate estimated rebalancing benefit (return boost).
        
        Parameters:
        -----------
        allocation : AssetAllocation
            Asset allocation
            
        Returns:
        --------
        float
            Estimated rebalancing benefit
        """
        # Calculate diversification benefit - more diverse portfolios get more rebalancing benefit
        asset_count = sum(1 for weight in allocation.to_dict().values() if weight > 0.05)
        
        # No benefit with only one asset class
        if asset_count <= 1:
            return 0.0
        
        # Calculate volatility spread
        volatility_spread = self._calculate_volatility_spread(allocation)
        
        # Rebalancing benefit increases with volatility spread and asset count
        base_benefit = 0.001  # 0.1% minimum benefit
        max_benefit = 0.004   # 0.4% maximum benefit
        
        # Linear scaling based on volatility spread and asset count
        benefit_factor = (volatility_spread / 0.2) * ((asset_count - 1) / 4)
        benefit_factor = max(0, min(1, benefit_factor))  # Cap between 0 and 1
        
        rebalancing_benefit = base_benefit + benefit_factor * (max_benefit - base_benefit)
        
        # Adjust based on rebalancing frequency
        if self.rebalancing_frequency == "quarterly":
            rebalancing_benefit *= 1.2  # 20% more benefit for quarterly rebalancing
        elif self.rebalancing_frequency == "monthly":
            rebalancing_benefit *= 1.3  # 30% more benefit for monthly rebalancing
            
        return rebalancing_benefit
    
    def _calculate_volatility_spread(self, allocation: AssetAllocation) -> float:
        """
        Calculate volatility spread among asset classes.
        
        Parameters:
        -----------
        allocation : AssetAllocation
            Asset allocation
            
        Returns:
        --------
        float
            Volatility spread
        """
        max_vol = 0
        min_vol = float('inf')
        
        for asset_class, weight in allocation.to_dict().items():
            if weight > 0.05:  # Only consider assets with significant allocation
                # Get volatility for this asset class
                _, volatility = self.get_asset_return(asset_class, self.risk_profile)
                max_vol = max(max_vol, volatility)
                min_vol = min(min_vol, volatility)
        
        if min_vol == float('inf'):
            return 0
            
        return max_vol - min_vol
    
    def _get_correlation_matrix(self, asset_classes) -> Dict[Tuple[AssetClass, AssetClass], float]:
        """
        Get correlation matrix for the given asset classes.
        
        Parameters:
        -----------
        asset_classes : Iterable[AssetClass]
            Asset classes to include in the matrix
            
        Returns:
        --------
        Dict[Tuple[AssetClass, AssetClass], float]
            Correlation matrix
        """
        correlations = {}
        
        # Use default correlations if no specific values from parameters
        for i, asset1 in enumerate(asset_classes):
            for j, asset2 in enumerate(asset_classes):
                if i == j:
                    # Perfect correlation with self
                    correlations[(asset1, asset2)] = 1.0
                else:
                    # Try to get correlation from parameters
                    param_path = f"asset_correlations.{asset1.value}.{asset2.value}"
                    correlation = self.get_parameter(param_path)
                    
                    if correlation is None:
                        # Check if correlation exists in the other direction
                        param_path = f"asset_correlations.{asset2.value}.{asset1.value}"
                        correlation = self.get_parameter(param_path)
                    
                    if correlation is None:
                        # Fall back to defaults
                        key = (asset1, asset2)
                        if key in self.DEFAULT_CORRELATIONS:
                            correlation = self.DEFAULT_CORRELATIONS[key]
                        else:
                            # Try reverse key
                            key = (asset2, asset1)
                            correlation = self.DEFAULT_CORRELATIONS.get(key, 0.0)
                    
                    correlations[(asset1, asset2)] = correlation
        
        return correlations
    
    def _simulate_correlated_returns(self, 
                                    allocation: Dict[AssetClass, float],
                                    returns_volatilities: Dict[AssetClass, Tuple[float, float]],
                                    correlation_matrix: Dict[Tuple[AssetClass, AssetClass], float]) -> Dict[AssetClass, float]:
        """
        Simulate correlated returns for asset classes.
        
        Parameters:
        -----------
        allocation : Dict[AssetClass, float]
            Asset allocation
        returns_volatilities : Dict[AssetClass, Tuple[float, float]]
            Returns and volatilities for each asset class
        correlation_matrix : Dict[Tuple[AssetClass, AssetClass], float]
            Correlation matrix
            
        Returns:
        --------
        Dict[AssetClass, float]
            Simulated returns for each asset class
        """
        # Get asset classes with allocation
        active_assets = [asset for asset, weight in allocation.items() if weight > 0]
        
        if not active_assets:
            return {}
        
        # Generate uncorrelated random numbers
        uncorrelated = np.random.normal(0, 1, len(active_assets))
        
        # Create correlation matrix as numpy array
        n = len(active_assets)
        corr_matrix = np.identity(n)
        for i in range(n):
            for j in range(i+1, n):
                corr = correlation_matrix.get((active_assets[i], active_assets[j]), 0.0)
                corr_matrix[i, j] = corr
                corr_matrix[j, i] = corr
        
        # Check if matrix is positive semi-definite
        # In a production system, we would use a proper method to ensure this
        # Here we'll just add a small value to the diagonal if needed
        while True:
            try:
                # Try to compute Cholesky decomposition
                chol = np.linalg.cholesky(corr_matrix)
                break
            except np.linalg.LinAlgError:
                # Add small value to diagonal and try again
                corr_matrix += np.identity(n) * 0.01
        
        # Generate correlated random numbers
        correlated = np.dot(chol, uncorrelated)
        
        # Calculate returns for each asset class
        simulated_returns = {}
        for i, asset in enumerate(active_assets):
            mean_return, volatility = returns_volatilities[asset]
            
            # Generate return using the correlated random number
            asset_return = mean_return + volatility * correlated[i]
            simulated_returns[asset] = asset_return
        
        return simulated_returns
    
    def _confidence_to_z_score(self, confidence_level: float) -> float:
        """
        Convert confidence level to Z-score.
        
        Parameters:
        -----------
        confidence_level : float
            Confidence level (0 to 1)
            
        Returns:
        --------
        float
            Z-score
        """
        # Simple approximation for common confidence levels
        if confidence_level >= 0.995:
            return 2.576
        elif confidence_level >= 0.99:
            return 2.326
        elif confidence_level >= 0.975:
            return 1.96
        elif confidence_level >= 0.95:
            return 1.645
        elif confidence_level >= 0.9:
            return 1.282
        elif confidence_level >= 0.8:
            return 0.842
        elif confidence_level >= 0.7:
            return 0.524
        elif confidence_level >= 0.6:
            return 0.253
        elif confidence_level >= 0.5:
            return 0.0
        elif confidence_level >= 0.4:
            return -0.253
        elif confidence_level >= 0.3:
            return -0.524
        elif confidence_level >= 0.2:
            return -0.842
        elif confidence_level >= 0.1:
            return -1.282
        elif confidence_level >= 0.05:
            return -1.645
        elif confidence_level >= 0.025:
            return -1.96
        elif confidence_level >= 0.01:
            return -2.326
        else:
            return -2.576
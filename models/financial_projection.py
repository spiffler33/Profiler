"""
Financial Projection Module

This module provides tools for projecting asset growth over time with various
configurations including different asset classes, contribution patterns,
allocation changes, and risk modeling capabilities.
"""

import numpy as np
import pandas as pd
import math
import time
from typing import Dict, List, Tuple, Union, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AssetClass(Enum):
    """Enum representing different asset classes for allocation"""
    EQUITY = "equity"
    DEBT = "debt" 
    GOLD = "gold"
    REAL_ESTATE = "real_estate"
    CASH = "cash"

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
    
    # Additional properties for internal use (not in __init__)
    # These will be set manually after initialization if needed
    all_projections: Optional[np.ndarray] = None    # Raw projection results for all simulations
    yearly_contributions: Optional[List[float]] = None  # Yearly contributions for caching
    creation_time: Optional[float] = None  # When this result was created
    
    def __post_init__(self):
        """Initialize additional properties after dataclass initialization"""
        self._ensure_consistent_lengths()
        self.creation_time = time.time() if 'time' in globals() else None
        
    def _ensure_consistent_lengths(self):
        """Ensure that all result arrays have consistent lengths"""
        # Check if projected_values and years exist and are not None
        has_projected_values = self.projected_values is not None and hasattr(self.projected_values, '__len__')
        has_years = self.years is not None and hasattr(self.years, '__len__')
        
        # Only check lengths if both arrays exist
        if has_projected_values and has_years:
            if len(self.projected_values) != len(self.years):
                logger.warning(f"Inconsistent lengths: projected_values={len(self.projected_values)}, years={len(self.years)}")
                # Truncate to shorter length
                min_len = min(len(self.projected_values), len(self.years))
                self.projected_values = self.projected_values[:min_len]
                self.years = self.years[:min_len]
            
        # Check contributions length
        has_contributions = self.contributions is not None and hasattr(self.contributions, '__len__')
        if has_contributions and has_years and len(self.contributions) != len(self.years):
            # Pad with zeros or truncate contributions
            if len(self.contributions) < len(self.years):
                self.contributions = self.contributions + [0] * (len(self.years) - len(self.contributions))
            else:
                self.contributions = self.contributions[:len(self.years)]
                
        # Check growth length
        has_growth = self.growth is not None and hasattr(self.growth, '__len__')
        if has_growth and has_years and len(self.growth) != len(self.years):
            # Pad with zeros or truncate growth
            if len(self.growth) < len(self.years):
                self.growth = self.growth + [0] * (len(self.years) - len(self.growth))
            else:
                self.growth = self.growth[:len(self.years)]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert projection result to pandas DataFrame for analysis/visualization"""
        df = pd.DataFrame({
            'Year': self.years,
            'Projected_Value': self.projected_values,
            'Contributions': self.contributions,
            'Growth': self.growth
        })
        
        # Add confidence intervals if available
        has_confidence_intervals = self.confidence_intervals is not None and isinstance(self.confidence_intervals, dict)
        if has_confidence_intervals:
            for label, values in self.confidence_intervals.items():
                if hasattr(values, '__len__') and len(values) == len(self.years):
                    df[f'CI_{label}'] = values
                else:
                    logger.warning(f"Skipping confidence interval {label} due to length mismatch")
                
        return df
        
    def get_success_probability(self, target_amount: float) -> float:
        """
        Calculate the probability of reaching a target amount by the end of the projection.
        
        This is useful when the ProjectionResult is a result of a Monte Carlo simulation
        and you want to know the probability of reaching a specific goal.
        
        Args:
            target_amount: The target amount to reach
            
        Returns:
            Probability (0-1) of reaching the target amount
        """
        if self.all_projections is None:
            # If we don't have raw simulation data, use the median projection
            return 1.0 if self.projected_values[-1] >= target_amount else 0.0
            
        # Calculate probability using raw simulation data
        final_values = self.all_projections[:, -1]
        success_count = np.sum(final_values >= target_amount)
        
        # Add partial credit for values close to target (within 10%)
        close_threshold = 0.9 * target_amount
        close_mask = (final_values >= close_threshold) & (final_values < target_amount)
        close_count = np.sum(close_mask)
        
        if close_count > 0:
            # Calculate closeness ratio for each close value
            close_values = final_values[close_mask]
            closeness_ratios = (close_values - close_threshold) / (target_amount - close_threshold)
            partial_credit = np.sum(closeness_ratios)
            
            # Adjusted success count with partial credit
            adjusted_success_count = success_count + partial_credit
        else:
            adjusted_success_count = success_count
            
        return adjusted_success_count / len(final_values)

@dataclass
class AllocationStrategy:
    """Data class for defining asset allocation strategies"""
    initial_allocation: Dict[AssetClass, float]
    target_allocation: Optional[Dict[AssetClass, float]] = None
    glide_path_years: Optional[int] = None
    
    def validate(self) -> bool:
        """Validate that allocations sum to approximately 1.0"""
        init_sum = sum(self.initial_allocation.values())
        if not 0.99 <= init_sum <= 1.01:
            logger.error(f"Initial allocation sums to {init_sum}, not 1.0")
            return False
            
        if self.target_allocation:
            target_sum = sum(self.target_allocation.values())
            if not 0.99 <= target_sum <= 1.01:
                logger.error(f"Target allocation sums to {target_sum}, not 1.0")
                return False
                
        return True

@dataclass
class ContributionPattern:
    """Data class for defining contribution patterns"""
    annual_amount: float
    growth_rate: float = 0.0  # For growing contributions (e.g., with income growth)
    frequency: str = "annual"  # Options: "annual", "monthly", "quarterly"
    irregular_schedule: Optional[Dict[int, float]] = None  # For irregular contributions
    
    def get_contribution_for_year(self, year: int) -> float:
        """Calculate contribution amount for a specific year"""
        # Check for irregular contribution first
        if self.irregular_schedule and year in self.irregular_schedule:
            return self.irregular_schedule[year]
            
        # Calculate regular contribution with growth
        contribution = self.annual_amount * (1 + self.growth_rate) ** (year - 1)
        
        return contribution


class AssetProjection:
    """
    Class for financial projections of assets across multiple asset classes,
    with support for different contribution patterns, allocation strategies,
    and risk modeling.
    """
    
    # Default annual returns (mean, volatility) by asset class
    DEFAULT_RETURNS = {
        AssetClass.EQUITY: (0.10, 0.18),       # 10% return, 18% volatility
        AssetClass.DEBT: (0.06, 0.05),         # 6% return, 5% volatility
        AssetClass.GOLD: (0.07, 0.15),         # 7% return, 15% volatility
        AssetClass.REAL_ESTATE: (0.08, 0.12),  # 8% return, 12% volatility
        AssetClass.CASH: (0.03, 0.01),         # 3% return, 1% volatility
    }
    
    def __init__(self, 
                 returns: Optional[Dict[AssetClass, Tuple[float, float]]] = None, 
                 inflation_rate: float = 0.03,
                 rebalancing_frequency: Optional[str] = "annual",
                 seed: Optional[int] = None,
                 cache_simulations: bool = True):
        """
        Initialize the projection model with asset return assumptions
        
        Parameters:
        -----------
        returns : Dict[AssetClass, Tuple[float, float]], optional
            Dictionary mapping asset classes to (mean_return, volatility) tuples
        inflation_rate : float, default 0.03
            Annual inflation rate for real return calculations
        rebalancing_frequency : str, optional
            Frequency of portfolio rebalancing ('annual', 'quarterly', 'monthly', or None)
        seed : int, optional
            Random seed for Monte Carlo simulations
        cache_simulations : bool, default True
            Whether to cache Monte Carlo simulation results for performance
        """
        self.returns = returns or self.DEFAULT_RETURNS
        self.inflation_rate = inflation_rate
        self.rebalancing_frequency = rebalancing_frequency
        self.cache_simulations = cache_simulations
        
        # Cache for Monte Carlo simulations to avoid expensive recalculations
        self._simulation_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Import time module if available (for performance tracking)
        try:
            import time
            self._time_module_available = True
        except ImportError:
            self._time_module_available = False
        
        # Set random seed if provided
        if seed is not None:
            np.random.seed(seed)
            
    def _get_cache_key(self, 
                       initial_amount: float, 
                       years: int,
                       simulations: int,
                       seed: int,
                       contribution_pattern_hash: str,
                       allocation_strategy_hash: str) -> str:
        """Generate a unique cache key for a simulation configuration"""
        return f"{initial_amount}_{years}_{simulations}_{seed}_{contribution_pattern_hash}_{allocation_strategy_hash}"
    
    def _get_contribution_pattern_hash(self, pattern: ContributionPattern) -> str:
        """Generate a hash for a contribution pattern"""
        if hasattr(pattern, 'annual_amount') and hasattr(pattern, 'growth_rate'):
            return f"{pattern.annual_amount}_{pattern.growth_rate}_{pattern.frequency}"
        return str(id(pattern))  # Fallback for complex patterns
    
    def _get_allocation_strategy_hash(self, strategy: AllocationStrategy) -> str:
        """Generate a hash for an allocation strategy"""
        initial_alloc = "_".join(f"{k.name}:{v:.2f}" for k, v in sorted(strategy.initial_allocation.items(), key=lambda x: x[0].name))
        
        if strategy.target_allocation:
            target_alloc = "_".join(f"{k.name}:{v:.2f}" for k, v in sorted(strategy.target_allocation.items(), key=lambda x: x[0].name))
            return f"{initial_alloc}_{target_alloc}_{strategy.glide_path_years}"
        
        return initial_alloc
    
    def project_asset_growth(self, 
                            initial_amount: float,
                            contribution_pattern: ContributionPattern,
                            years: int,
                            allocation_strategy: AllocationStrategy) -> ProjectionResult:
        """
        Project asset growth over time with the given parameters
        
        Parameters:
        -----------
        initial_amount : float
            Starting value of the assets
        contribution_pattern : ContributionPattern
            Pattern defining contribution schedule and growth
        years : int
            Number of years to project
        allocation_strategy : AllocationStrategy
            Asset allocation strategy to use
            
        Returns:
        --------
        ProjectionResult
            Object containing projection results and metadata
        """
        if not allocation_strategy.validate():
            raise ValueError("Invalid allocation strategy: allocations must sum to 1.0")
        
        # Initialize tracking variables
        projected_values = [initial_amount]
        contributions = [0]  # No contribution at start
        growth_values = [0]  # No growth at start
        current_value = initial_amount
        
        # Calculate year-by-year projections
        for year in range(1, years + 1):
            # Get contribution for this year
            contribution = contribution_pattern.get_contribution_for_year(year)
            
            # Calculate allocation for this year (accounting for glide path)
            current_allocation = self._calculate_allocation_for_year(
                allocation_strategy, year, years
            )
            
            # Calculate expected return based on allocation
            expected_return = self._calculate_expected_return(current_allocation)
            
            # Apply rebalancing benefit if enabled
            if self.rebalancing_frequency:
                rebalancing_benefit = self._calculate_rebalancing_benefit(current_allocation)
                expected_return += rebalancing_benefit
            
            # Calculate growth
            growth = current_value * expected_return
            
            # Update current value
            current_value = current_value + growth + contribution
            
            # Store results
            projected_values.append(current_value)
            contributions.append(contribution)
            growth_values.append(growth)
        
        # Return results
        return ProjectionResult(
            years=list(range(years + 1)),
            projected_values=projected_values,
            contributions=contributions,
            growth=growth_values
        )
    
    def project_with_monte_carlo(self,
                                initial_amount: float,
                                contribution_pattern: ContributionPattern,
                                years: int,
                                allocation_strategy: AllocationStrategy,
                                simulations: int = 1000,
                                confidence_levels: List[float] = [0.10, 0.25, 0.50, 0.75, 0.90],
                                seed: int = 42,
                                use_vectorized: bool = True,
                                use_cache: bool = None) -> ProjectionResult:
        """
        Project asset growth using Monte Carlo simulation
        
        Parameters:
        -----------
        initial_amount : float
            Starting value of the assets
        contribution_pattern : ContributionPattern
            Pattern defining contribution schedule and growth
        years : int
            Number of years to project
        allocation_strategy : AllocationStrategy
            Asset allocation strategy to use
        simulations : int, default 1000
            Number of Monte Carlo simulations to run (minimum 500 recommended for stability)
        confidence_levels : List[float], default [0.10, 0.25, 0.50, 0.75, 0.90]
            Percentiles to calculate for confidence intervals (expanded to include P25 and P75)
        seed : int, default 42
            Random seed for deterministic testing results
        use_vectorized : bool, default True
            Whether to use vectorized operations for improved performance
        use_cache : bool, optional
            Whether to use caching (defaults to self.cache_simulations)
            
        Returns:
        --------
        ProjectionResult
            Object containing projection results with confidence intervals
        """
        # Performance metrics for diagnostics
        start_time = time.time() if hasattr(self, '_time_module_available') and self._time_module_available else None
        
        if not allocation_strategy.validate():
            raise ValueError("Invalid allocation strategy: allocations must sum to 1.0")
            
        # Validate simulation count - minimum 500 for stability
        if simulations < 500:
            logger.warning(f"Simulation count {simulations} is too low for stable results, increasing to 500")
            simulations = 500
        
        # Determine whether to use cache
        if use_cache is None:
            use_cache = self.cache_simulations
            
        # If using cache, check if we have a cached result
        if use_cache:
            # Generate cache keys
            contribution_hash = self._get_contribution_pattern_hash(contribution_pattern)
            allocation_hash = self._get_allocation_strategy_hash(allocation_strategy)
            cache_key = self._get_cache_key(
                initial_amount=initial_amount,
                years=years,
                simulations=simulations,
                seed=seed,
                contribution_pattern_hash=contribution_hash,
                allocation_strategy_hash=allocation_hash
            )
            
            # Check cache
            if cache_key in self._simulation_cache:
                self._cache_hits += 1
                logger.debug(f"Monte Carlo simulation cache hit (key={cache_key})")
                cached_result = self._simulation_cache[cache_key]
                
                # If confidence levels match, return cached result directly
                cached_levels = set(level for level in cached_result.confidence_intervals.keys() 
                                if level.startswith('P'))
                requested_levels = set(f"P{int(level * 100)}" for level in confidence_levels)
                
                if cached_levels == requested_levels:
                    return cached_result
                    
                # If confidence levels don't match, we can reuse the projections data
                # but need to recalculate confidence intervals
                all_projections = cached_result.all_projections
                yearly_contributions = cached_result.yearly_contributions
                
                # Skip to confidence interval calculation
                logger.debug("Reusing cached projections with different confidence levels")
                median_projection = np.median(all_projections, axis=0)
        
                # Calculate growth values based on median projection
                growth_values = [0]
                for year in range(1, years + 1):
                    growth = median_projection[year] - median_projection[year-1] - yearly_contributions[year]
                    growth_values.append(growth)
                
                # Calculate confidence intervals with new levels
                confidence_intervals = {}
                for level in confidence_levels:
                    percentile = int(level * 100)
                    confidence_intervals[f"P{percentile}"] = np.percentile(all_projections, percentile, axis=0)
                    
                # Create result and store in cache
                result = ProjectionResult(
                    years=list(range(years + 1)),
                    projected_values=median_projection,
                    contributions=yearly_contributions,
                    growth=growth_values,
                    confidence_intervals=confidence_intervals,
                    volatility=np.std(all_projections[:, -1]) / np.mean(all_projections[:, -1])
                )
                
                # Add additional data for caching
                result.all_projections = all_projections
                result.yearly_contributions = yearly_contributions
                
                # Store in cache and return
                self._simulation_cache[cache_key] = result
                return result
            else:
                self._cache_misses += 1
                logger.debug(f"Monte Carlo simulation cache miss (key={cache_key})")
            
        # Set random seed for deterministic testing
        if seed is not None:
            logger.info(f"Setting random seed to {seed} for deterministic Monte Carlo simulation")
            np.random.seed(seed)
        
        # Store all simulation results
        all_projections = np.zeros((simulations, years + 1))
        all_projections[:, 0] = initial_amount  # All start with initial amount
        
        # Pre-calculate and cache contributions for each year for efficiency
        yearly_contributions = [0]  # No contribution at start
        for year in range(1, years + 1):
            yearly_contributions.append(contribution_pattern.get_contribution_for_year(year))
        
        # Pre-calculate allocations for each year for efficiency
        yearly_allocations = []
        for year in range(1, years + 1):
            yearly_allocations.append(self._calculate_allocation_for_year(
                allocation_strategy, year, years
            ))
            
        if use_vectorized:
            # Run simulations using vectorized operations (much faster)
            current_values = np.full(simulations, initial_amount)
            
            for year in range(1, years + 1):
                # Get contribution for this year (same for all simulations)
                contribution = yearly_contributions[year]
                
                # Calculate allocation for this year
                current_allocation = yearly_allocations[year-1]
                
                # Generate random returns for all simulations at once
                simulated_returns = self._simulate_portfolio_returns_vectorized(
                    current_allocation, simulations
                )
                
                # Update all values at once
                current_values = current_values * (1 + simulated_returns) + contribution
                all_projections[:, year] = current_values
        else:
            # Run simulations one by one (legacy approach)
            for sim in range(simulations):
                current_value = initial_amount
                
                for year in range(1, years + 1):
                    # Get contribution and allocation for this year
                    contribution = yearly_contributions[year]
                    current_allocation = yearly_allocations[year-1]
                    
                    # Generate random returns for each asset class
                    simulated_return = self._simulate_portfolio_return(current_allocation)
                    
                    # Update current value
                    current_value = current_value * (1 + simulated_return) + contribution
                    all_projections[sim, year] = current_value
        
        # Calculate statistics
        median_projection = np.median(all_projections, axis=0)
        
        # Calculate growth values based on median projection
        growth_values = [0]
        for year in range(1, years + 1):
            growth = median_projection[year] - median_projection[year-1] - yearly_contributions[year]
            growth_values.append(growth)
        
        # Calculate confidence intervals
        confidence_intervals = {}
        for level in confidence_levels:
            percentile = int(level * 100)
            confidence_intervals[f"P{percentile}"] = np.percentile(all_projections, percentile, axis=0)
            
        # Log performance metrics
        if start_time:
            duration = time.time() - start_time
            logger.debug(f"Monte Carlo simulation ({simulations} runs, {years} years) completed in {duration:.3f}s")
            if duration > 1.0 and not use_cache:
                logger.info(f"Performance note: Monte Carlo simulation took {duration:.3f}s. Consider enabling caching.")
            
        # Create result
        result = ProjectionResult(
            years=list(range(years + 1)),
            projected_values=median_projection,
            contributions=yearly_contributions,
            growth=growth_values,
            confidence_intervals=confidence_intervals,
            volatility=np.std(all_projections[:, -1]) / np.mean(all_projections[:, -1])
        )
        
        # Store additional data for caching
        if use_cache:
            # Add the raw projections data and contributions to the result for caching
            result.all_projections = all_projections
            result.yearly_contributions = yearly_contributions
            
            # Generate cache key and store in cache
            if not cache_key:
                contribution_hash = self._get_contribution_pattern_hash(contribution_pattern)
                allocation_hash = self._get_allocation_strategy_hash(allocation_strategy)
                cache_key = self._get_cache_key(
                    initial_amount=initial_amount,
                    years=years,
                    simulations=simulations,
                    seed=seed,
                    contribution_pattern_hash=contribution_hash,
                    allocation_strategy_hash=allocation_hash
                )
                
            self._simulation_cache[cache_key] = result
            logger.debug(f"Stored Monte Carlo simulation in cache (key={cache_key})")
            
            # Limit cache size to prevent memory issues
            if len(self._simulation_cache) > 100:
                logger.debug("Pruning simulation cache (keeping most recent 50 entries)")
                cache_keys = list(self._simulation_cache.keys())
                for old_key in cache_keys[:-50]:
                    del self._simulation_cache[old_key]
                    
        # Log cache statistics
        if use_cache and (self._cache_hits + self._cache_misses) % 10 == 0:
            hit_rate = self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0
            logger.debug(f"Monte Carlo cache statistics: hits={self._cache_hits}, misses={self._cache_misses}, hit_rate={hit_rate:.2f}")
        
        return result
        
        # Calculate overall volatility (standard deviation of final values)
        final_values = all_projections[:, -1]
        volatility = np.std(final_values) / np.mean(final_values)  # Coefficient of variation
        
        # Return results
        return ProjectionResult(
            years=list(range(years + 1)),
            projected_values=list(median_projection),
            contributions=contributions,
            growth=growth_values,
            confidence_intervals=confidence_intervals,
            volatility=volatility
        )
    
    def apply_inflation_adjustment(self, projection_result: ProjectionResult) -> ProjectionResult:
        """
        Adjust a projection result to account for inflation
        
        Parameters:
        -----------
        projection_result : ProjectionResult
            Original projection result in nominal terms
            
        Returns:
        --------
        ProjectionResult
            Inflation-adjusted projection result in real terms
        """
        # Create inflation discount factors for each year
        inflation_factors = [(1 / (1 + self.inflation_rate)) ** year for year in projection_result.years]
        
        # Adjust all monetary values
        real_values = [value * factor for value, factor in zip(projection_result.projected_values, inflation_factors)]
        real_contributions = [contrib * factor for contrib, factor in zip(projection_result.contributions, inflation_factors)]
        real_growth = [growth * factor for growth, factor in zip(projection_result.growth, inflation_factors)]
        
        # Adjust confidence intervals if present
        real_confidence_intervals = None
        if projection_result.confidence_intervals:
            real_confidence_intervals = {}
            for level, values in projection_result.confidence_intervals.items():
                real_confidence_intervals[level] = [value * factor for value, factor 
                                                  in zip(values, inflation_factors)]
        
        # Return adjusted projection
        return ProjectionResult(
            years=projection_result.years,
            projected_values=real_values,
            contributions=real_contributions,
            growth=real_growth,
            confidence_intervals=real_confidence_intervals,
            volatility=projection_result.volatility
        )
    
    def _calculate_allocation_for_year(self, 
                                      allocation_strategy: AllocationStrategy, 
                                      current_year: int,
                                      total_years: int) -> Dict[AssetClass, float]:
        """
        Calculate allocation for a specific year, accounting for glide path
        
        Parameters:
        -----------
        allocation_strategy : AllocationStrategy
            Allocation strategy with initial and target allocations
        current_year : int
            Current year in the projection
        total_years : int
            Total years in the projection
            
        Returns:
        --------
        Dict[AssetClass, float]
            Asset allocation for the current year
        """
        # If no glide path or target allocation, use initial allocation
        if (not allocation_strategy.target_allocation or 
            not allocation_strategy.glide_path_years):
            return allocation_strategy.initial_allocation
        
        # If beyond glide path years, use target allocation
        glide_years = min(allocation_strategy.glide_path_years, total_years)
        if current_year >= glide_years:
            return allocation_strategy.target_allocation
        
        # Calculate interpolated allocation along glide path
        interpolated_allocation = {}
        progress = current_year / glide_years
        
        for asset_class in allocation_strategy.initial_allocation:
            initial_weight = allocation_strategy.initial_allocation.get(asset_class, 0)
            target_weight = allocation_strategy.target_allocation.get(asset_class, 0)
            
            # Linear interpolation between initial and target weights
            interpolated_weight = initial_weight + progress * (target_weight - initial_weight)
            interpolated_allocation[asset_class] = interpolated_weight
            
        return interpolated_allocation
    
    def _calculate_expected_return(self, allocation: Dict[AssetClass, float]) -> float:
        """
        Calculate expected portfolio return based on asset allocation
        
        Parameters:
        -----------
        allocation : Dict[AssetClass, float]
            Current asset allocation
            
        Returns:
        --------
        float
            Expected portfolio return
        """
        expected_return = 0
        
        for asset_class, weight in allocation.items():
            if asset_class in self.returns:
                mean_return, _ = self.returns[asset_class]
                expected_return += weight * mean_return
        
        return expected_return
    
    def _calculate_rebalancing_benefit(self, allocation: Dict[AssetClass, float]) -> float:
        """
        Calculate estimated rebalancing benefit (return boost from rebalancing)
        Based on academic research showing modest return enhancement from disciplined rebalancing
        
        Parameters:
        -----------
        allocation : Dict[AssetClass, float]
            Current asset allocation
            
        Returns:
        --------
        float
            Estimated rebalancing benefit as additional return
        """
        # Calculate portfolio variance
        portfolio_variance = 0
        
        # First calculate correlations - simplified approach assuming fixed correlations
        # In a more sophisticated model, we would use a correlation matrix
        correlations = {
            (AssetClass.EQUITY, AssetClass.DEBT): 0.2,
            (AssetClass.EQUITY, AssetClass.GOLD): -0.1,
            (AssetClass.EQUITY, AssetClass.REAL_ESTATE): 0.5,
            (AssetClass.EQUITY, AssetClass.CASH): 0.0,
            (AssetClass.DEBT, AssetClass.GOLD): 0.3,
            (AssetClass.DEBT, AssetClass.REAL_ESTATE): 0.4,
            (AssetClass.DEBT, AssetClass.CASH): 0.5,
            (AssetClass.GOLD, AssetClass.REAL_ESTATE): 0.2,
            (AssetClass.GOLD, AssetClass.CASH): 0.1,
            (AssetClass.REAL_ESTATE, AssetClass.CASH): 0.0,
        }
        
        # Calculate diversification benefit - more diverse portfolios get more rebalancing benefit
        asset_count = sum(1 for weight in allocation.values() if weight > 0.05)
        
        # Simplified rebalancing benefit - more benefit with more asset classes and higher volatility spread
        if asset_count <= 1:
            return 0.0  # No benefit with only one asset class
        
        # Calculate rebalancing benefit based on research suggesting 0.1% to 0.4% annual benefit
        # More volatile and diverse portfolios get higher benefit
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
    
    def _calculate_volatility_spread(self, allocation: Dict[AssetClass, float]) -> float:
        """
        Calculate the spread between highest and lowest volatility assets in portfolio
        
        Parameters:
        -----------
        allocation : Dict[AssetClass, float]
            Current asset allocation
            
        Returns:
        --------
        float
            Volatility spread
        """
        max_vol = 0
        min_vol = float('inf')
        
        for asset_class, weight in allocation.items():
            if weight > 0.05 and asset_class in self.returns:  # Only consider assets with significant allocation
                _, volatility = self.returns[asset_class]
                max_vol = max(max_vol, volatility)
                min_vol = min(min_vol, volatility)
        
        if min_vol == float('inf'):
            return 0
            
        return max_vol - min_vol
    
    def _simulate_portfolio_return(self, allocation: Dict[AssetClass, float]) -> float:
        """
        Simulate a single year's portfolio return using random sampling
        
        Parameters:
        -----------
        allocation : Dict[AssetClass, float]
            Current asset allocation
            
        Returns:
        --------
        float
            Simulated portfolio return for one year
        """
        portfolio_return = 0
        
        # Using a more efficient implementation
        for asset_class, weight in allocation.items():
            if asset_class in self.returns and weight > 0.001:  # Skip negligible allocations
                mean_return, volatility = self.returns[asset_class]
                # Generate random return from normal distribution
                asset_return = np.random.normal(mean_return, volatility)
                portfolio_return += weight * asset_return
        
        return portfolio_return
        
    def _simulate_portfolio_returns_vectorized(self, allocation: Dict[AssetClass, float], simulations: int = 1) -> np.ndarray:
        """
        Simulate multiple portfolio returns at once using vectorized operations
        
        Parameters:
        -----------
        allocation : Dict[AssetClass, float]
            Current asset allocation
        simulations : int
            Number of simulations to generate
            
        Returns:
        --------
        np.ndarray
            Array of simulated returns (shape: simulations)
        """
        # Initialize with zeros
        portfolio_returns = np.zeros(simulations)
        
        # For each asset class, generate random returns for all simulations at once
        for asset_class, weight in allocation.items():
            if asset_class in self.returns and weight > 0.001:  # Skip negligible allocations
                mean_return, volatility = self.returns[asset_class]
                # Generate random returns for all simulations at once
                asset_returns = np.random.normal(mean_return, volatility, simulations)
                # Add weighted contribution to portfolio returns
                portfolio_returns += weight * asset_returns
        
        return portfolio_returns
    
    def calculate_volatility_metrics(self, 
                                    allocation: Dict[AssetClass, float], 
                                    time_horizon: int) -> Dict[str, float]:
        """
        Calculate volatility metrics for a given allocation and time horizon
        
        Parameters:
        -----------
        allocation : Dict[AssetClass, float]
            Asset allocation to analyze
        time_horizon : int
            Investment time horizon in years
            
        Returns:
        --------
        Dict[str, float]
            Dictionary of volatility metrics
        """
        # Calculate portfolio volatility (annual)
        annual_volatility = self._calculate_portfolio_volatility(allocation)
        
        # Calculate metrics
        metrics = {
            "annual_volatility": annual_volatility,
            "worst_case_annual": -annual_volatility * 1.96 + self._calculate_expected_return(allocation),
            "max_drawdown_estimate": annual_volatility * 2.5,  # Rough estimate based on empirical studies
        }
        
        # Long-term metrics (volatility declines with time - not as fast as sqrt(t) but close)
        if time_horizon > 1:
            # Long-term volatility declines but not as quickly as in perfectly efficient markets
            # Using a more conservative approach than square root of time
            horizon_factor = time_horizon ** 0.4  # Between 0.5 (efficient) and 0 (perfectly correlated)
            metrics["horizon_volatility"] = annual_volatility / horizon_factor
            
            # Probability of negative returns decreases with time
            metrics["probability_of_loss"] = self._calculate_loss_probability(allocation, time_horizon)
            
        return metrics
    
    def _calculate_portfolio_volatility(self, allocation: Dict[AssetClass, float]) -> float:
        """
        Calculate portfolio volatility based on asset allocation
        
        Parameters:
        -----------
        allocation : Dict[AssetClass, float]
            Asset allocation
            
        Returns:
        --------
        float
            Estimated portfolio volatility
        """
        # Simplified approach assuming fixed correlation matrix
        # In a production system, we would use a full correlation matrix and proper portfolio math
        
        # Asset volatilities
        volatilities = {}
        for asset_class, weight in allocation.items():
            if asset_class in self.returns:
                _, vol = self.returns[asset_class]
                volatilities[asset_class] = vol
        
        # Simplified correlation matrix - using average correlation of 0.3 between asset classes
        # This is a significant simplification; a real model would use asset-specific correlations
        avg_correlation = 0.3
        
        # Calculate weighted volatility
        weighted_vol_squared = 0
        
        # First, add the weighted individual volatilities squared
        for asset_class, weight in allocation.items():
            if asset_class in volatilities:
                weighted_vol_squared += (weight * volatilities[asset_class]) ** 2
        
        # Then add the correlation terms
        for asset1, weight1 in allocation.items():
            for asset2, weight2 in allocation.items():
                if asset1 != asset2 and asset1 in volatilities and asset2 in volatilities:
                    # Use the simplified correlation assumption
                    weighted_vol_squared += (
                        weight1 * weight2 * 
                        volatilities[asset1] * volatilities[asset2] * 
                        avg_correlation
                    )
        
        return weighted_vol_squared ** 0.5
    
    def _calculate_loss_probability(self, allocation: Dict[AssetClass, float], years: int) -> float:
        """
        Calculate the probability of negative returns over a given time horizon
        
        Parameters:
        -----------
        allocation : Dict[AssetClass, float]
            Asset allocation
        years : int
            Time horizon in years
            
        Returns:
        --------
        float
            Probability of negative returns over the time horizon
        """
        # Get expected return and volatility
        expected_return = self._calculate_expected_return(allocation)
        annual_volatility = self._calculate_portfolio_volatility(allocation)
        
        # For long time horizons, annual returns start to compound
        # and the distribution becomes more skewed, so we make adjustments
        
        # Calculate cumulative expected return over the time horizon
        cumulative_expected_return = (1 + expected_return) ** years - 1
        
        # Estimate cumulative volatility (this is more complex - using approximation)
        # Long-term volatility grows slower than sqrt(years) due to mean reversion
        cumulative_volatility = annual_volatility * (years ** 0.4)
        
        # Calculate probability of loss using normal approximation
        # z-score for loss = (0 - cumulative_expected_return) / cumulative_volatility
        z_score = -cumulative_expected_return / cumulative_volatility
        
        # Use normal CDF to get probability
        # Using simple approximation since we don't want to import scipy just for this
        probability = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))
        
        return probability


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
    OTHER = "other"


class TaxRegime(Enum):
    """Enum representing different tax regimes in India"""
    OLD = "old_regime"
    NEW = "new_regime"


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
class IncomeResult:
    """Data class for storing and visualizing income projection results"""
    years: List[int]
    income_values: Dict[IncomeSource, List[float]]
    total_income: List[float]
    after_tax_income: List[float]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert income result to pandas DataFrame for analysis/visualization"""
        df = pd.DataFrame({
            'Year': self.years,
            'Total_Income': self.total_income,
            'After_Tax_Income': self.after_tax_income
        })
        
        # Add individual income sources
        for source, values in self.income_values.items():
            df[f'Income_{source.value.capitalize()}'] = values
                
        return df


class IncomeProjection:
    """
    Class for projecting income over time with support for multiple income sources,
    career milestones, retirement planning, and tax calculations.
    
    This class implements Indian-specific defaults for income growth rates, tax
    calculations, and retirement benefits.
    """
    
    # Default growth rates by income source in Indian context
    DEFAULT_GROWTH_RATES = {
        IncomeSource.SALARY: 0.08,        # 8% annual growth
        IncomeSource.BUSINESS: 0.10,       # 10% annual growth
        IncomeSource.RENTAL: 0.05,         # 5% annual growth
        IncomeSource.DIVIDENDS: 0.06,      # 6% annual growth
        IncomeSource.INTEREST: 0.04,       # 4% annual growth
        IncomeSource.PENSION: 0.03,        # 3% annual growth (partial inflation adjustment)
        IncomeSource.ANNUITY: 0.0,         # Fixed payments
        IncomeSource.GOVT_BENEFITS: 0.03,  # 3% annual growth (partial inflation adjustment)
        IncomeSource.OTHER: 0.05,          # 5% annual growth
    }
    
    # Career volatility factors by income source
    # Higher values mean more volatility/variability in income growth
    VOLATILITY_FACTORS = {
        IncomeSource.SALARY: 0.15,         # Relatively stable
        IncomeSource.BUSINESS: 0.40,       # Highly variable
        IncomeSource.RENTAL: 0.20,         # Moderately variable
        IncomeSource.DIVIDENDS: 0.30,      # Variable with market
        IncomeSource.INTEREST: 0.10,       # Fairly stable
        IncomeSource.PENSION: 0.05,        # Very stable
        IncomeSource.ANNUITY: 0.0,         # Fixed - no volatility
        IncomeSource.GOVT_BENEFITS: 0.05,  # Very stable
        IncomeSource.OTHER: 0.25,          # Moderately variable
    }
    
    # Indian income tax brackets (simplified for illustration, FY 2023-24)
    # (These would be updated regularly in a production system)
    TAX_BRACKETS_OLD_REGIME = [
        (0, 250000, 0.0),           # Up to 2.5L: 0%
        (250001, 500000, 0.05),     # 2.5L to 5L: 5%
        (500001, 750000, 0.10),     # 5L to 7.5L: 10%
        (750001, 1000000, 0.15),    # 7.5L to 10L: 15%
        (1000001, 1250000, 0.20),   # 10L to 12.5L: 20%
        (1250001, 1500000, 0.25),   # 12.5L to 15L: 25%
        (1500001, float('inf'), 0.30)  # Above 15L: 30%
    ]
    
    TAX_BRACKETS_NEW_REGIME = [
        (0, 300000, 0.0),           # Up to 3L: 0%
        (300001, 600000, 0.05),     # 3L to 6L: 5%
        (600001, 900000, 0.10),     # 6L to 9L: 10%
        (900001, 1200000, 0.15),    # 9L to 12L: 15%
        (1200001, 1500000, 0.20),   # 12L to 15L: 20%
        (1500001, float('inf'), 0.30)  # Above 15L: 30%
    ]
    
    # Indian retirement benefits (simplified estimates)
    EPF_CONTRIBUTION_RATE = 0.12    # 12% of basic salary
    NPS_DEFAULT_RATE = 0.10         # 10% of income
    GRATUITY_FACTOR = 15/26         # 15 days salary per year of service (approx)
    
    def __init__(self, 
                inflation_rate: float = 0.06,  # 6% inflation - India average
                tax_regime: TaxRegime = TaxRegime.NEW,
                seed: Optional[int] = None):
        """
        Initialize the income projection model
        
        Parameters:
        -----------
        inflation_rate : float, default 0.06
            Annual inflation rate for real income calculations
        tax_regime : TaxRegime, default TaxRegime.NEW
            Tax regime to use for tax calculations (old or new)
        seed : int, optional
            Random seed for Monte Carlo simulations
        """
        self.inflation_rate = inflation_rate
        self.tax_regime = tax_regime
        
        # Set random seed if provided
        if seed is not None:
            np.random.seed(seed)
    
    def project_income(self,
                      start_income: float,
                      years: int,
                      growth_rate: Optional[float] = None,
                      income_source: IncomeSource = IncomeSource.SALARY,
                      milestones: Optional[List[IncomeMilestone]] = None) -> IncomeResult:
        """
        Project income growth over time with a single income source
        
        Parameters:
        -----------
        start_income : float
            Starting annual income amount
        years : int
            Number of years to project
        growth_rate : float, optional
            Annual growth rate (if not provided, uses default for income source)
        income_source : IncomeSource, default IncomeSource.SALARY
            Type of income being projected
        milestones : List[IncomeMilestone], optional
            List of career milestones that affect income over time
            
        Returns:
        --------
        IncomeResult
            Object containing income projection results
        """
        # Use default growth rate if not provided
        if growth_rate is None:
            growth_rate = self.DEFAULT_GROWTH_RATES[income_source]
        
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
        
        # Calculate year-by-year projections
        for year in range(1, years + 1):
            # Apply milestone if one exists for this year
            if year in milestone_dict:
                current_income = milestone_dict[year].apply_to_income(current_income)
            else:
                # Apply standard growth rate
                current_income = current_income * (1 + growth_rate)
                
            # Store results
            income_values[income_source].append(current_income)
            total_income.append(current_income)
        
        # Calculate after-tax income
        after_tax_income = self._calculate_after_tax_income(total_income)
        
        # Return results
        return IncomeResult(
            years=list(range(years + 1)),
            income_values=income_values,
            total_income=total_income,
            after_tax_income=after_tax_income
        )
    
    def project_multiple_income_streams(self,
                                       income_sources: Dict[IncomeSource, float],
                                       years: int,
                                       growth_rates: Optional[Dict[IncomeSource, float]] = None,
                                       milestones_by_source: Optional[Dict[IncomeSource, List[IncomeMilestone]]] = None) -> IncomeResult:
        """
        Project income from multiple income sources over time
        
        Parameters:
        -----------
        income_sources : Dict[IncomeSource, float]
            Dictionary mapping income sources to their starting amounts
        years : int
            Number of years to project
        growth_rates : Dict[IncomeSource, float], optional
            Dictionary mapping income sources to their growth rates
            (if not provided, uses defaults)
        milestones_by_source : Dict[IncomeSource, List[IncomeMilestone]], optional
            Dictionary mapping income sources to their milestone lists
            
        Returns:
        --------
        IncomeResult
            Object containing income projection results for all sources
        """
        # Initialize tracking variables
        income_values = {source: [amount] for source, amount in income_sources.items()}
        current_values = {source: amount for source, amount in income_sources.items()}
        total_income = [sum(income_sources.values())]
        
        # Use default growth rates if not provided
        if growth_rates is None:
            growth_rates = {source: self.DEFAULT_GROWTH_RATES[source] for source in income_sources}
        
        # Organize milestones by source and year if provided
        milestone_dict = {}
        if milestones_by_source:
            for source, milestones in milestones_by_source.items():
                if source not in milestone_dict:
                    milestone_dict[source] = {}
                
                for milestone in milestones:
                    if milestone.year <= years:
                        milestone_dict[source][milestone.year] = milestone
        
        # Calculate year-by-year projections
        for year in range(1, years + 1):
            year_total = 0
            
            # Process each income source
            for source in income_sources:
                current_value = current_values[source]
                
                # Apply milestone if one exists for this source and year
                if source in milestone_dict and year in milestone_dict[source]:
                    current_value = milestone_dict[source][year].apply_to_income(current_value)
                else:
                    # Apply standard growth rate
                    growth = growth_rates.get(source, self.DEFAULT_GROWTH_RATES[source])
                    current_value = current_value * (1 + growth)
                
                # Update current values
                current_values[source] = current_value
                income_values[source].append(current_value)
                year_total += current_value
            
            # Store total income for the year
            total_income.append(year_total)
        
        # Calculate after-tax income
        after_tax_income = self._calculate_after_tax_income(total_income)
        
        # Return results
        return IncomeResult(
            years=list(range(years + 1)),
            income_values=income_values,
            total_income=total_income,
            after_tax_income=after_tax_income
        )
    
    def apply_career_volatility(self, 
                               income_result: IncomeResult,
                               career_volatility: Optional[Dict[IncomeSource, float]] = None,
                               simulations: int = 1000,
                               confidence_levels: List[float] = [0.10, 0.50, 0.90]) -> Dict[str, IncomeResult]:
        """
        Apply career volatility to income projections to model income uncertainty
        
        Parameters:
        -----------
        income_result : IncomeResult
            Base income projection result
        career_volatility : Dict[IncomeSource, float], optional
            Dictionary mapping income sources to volatility factors
            (if not provided, uses default volatility factors)
        simulations : int, default 1000
            Number of Monte Carlo simulations to run
        confidence_levels : List[float], default [0.10, 0.50, 0.90]
            Percentiles to calculate for confidence intervals
            
        Returns:
        --------
        Dict[str, IncomeResult]
            Dictionary mapping scenario names to income projection results
        """
        # Use default volatility factors if not provided
        if career_volatility is None:
            career_volatility = self.VOLATILITY_FACTORS
        
        years = len(income_result.years) - 1  # Exclude initial year
        
        # Create simulations for each income source
        simulated_incomes = {}
        
        for source, values in income_result.income_values.items():
            volatility = career_volatility.get(source, self.VOLATILITY_FACTORS[source])
            
            # Store simulation results for this source
            simulated_incomes[source] = np.zeros((simulations, years + 1))
            simulated_incomes[source][:, 0] = values[0]  # All start with initial amount
            
            # Run simulations
            for sim in range(simulations):
                current_value = values[0]
                
                for year in range(1, years + 1):
                    # Calculate expected growth based on ratio of consecutive values in original projection
                    if values[year-1] > 0:
                        expected_growth_rate = (values[year] / values[year-1]) - 1
                    else:
                        expected_growth_rate = 0
                    
                    # Add random variation to growth rate
                    growth_variation = np.random.normal(0, volatility)
                    actual_growth_rate = expected_growth_rate + growth_variation
                    
                    # Ensure growth rate isn't excessively negative
                    actual_growth_rate = max(actual_growth_rate, -0.5)
                    
                    # Update current value
                    current_value = current_value * (1 + actual_growth_rate)
                    simulated_incomes[source][sim, year] = max(0, current_value)  # Ensure income isn't negative
        
        # Calculate aggregate results for different scenarios
        scenarios = {}
        
        # Build results for each confidence level
        for level in confidence_levels:
            percentile = int(level * 100)
            scenario_name = f"P{percentile}"
            
            # Initialize result structures
            scenario_income_values = {}
            scenario_total_income = [sum(source_values[0] for source_values in income_result.income_values.values())]
            
            # Calculate percentile values for each source and year
            for source, sim_values in simulated_incomes.items():
                source_percentiles = np.percentile(sim_values, percentile, axis=0)
                scenario_income_values[source] = list(source_percentiles)
            
            # Calculate total income for each year
            for year in range(1, years + 1):
                year_total = sum(values[year] for values in scenario_income_values.values())
                scenario_total_income.append(year_total)
            
            # Calculate after-tax income
            scenario_after_tax = self._calculate_after_tax_income(scenario_total_income)
            
            # Store scenario result
            scenarios[scenario_name] = IncomeResult(
                years=income_result.years,
                income_values=scenario_income_values,
                total_income=scenario_total_income,
                after_tax_income=scenario_after_tax
            )
        
        # Include the original projection as "expected" scenario
        scenarios["expected"] = income_result
        
        return scenarios
    
    def project_retirement_income(self,
                                 current_age: int,
                                 retirement_age: int,
                                 life_expectancy: int,
                                 current_income: Dict[IncomeSource, float],
                                 retirement_corpus: float,
                                 withdrawal_rate: float = 0.04,
                                 pension_monthly: float = 0,
                                 epf_balance: float = 0,
                                 nps_balance: float = 0,
                                 govt_benefits_monthly: float = 0) -> IncomeResult:
        """
        Project income during retirement years from various retirement income sources
        
        Parameters:
        -----------
        current_age : int
            Current age of the individual
        retirement_age : int
            Expected retirement age
        life_expectancy : int
            Expected life expectancy
        current_income : Dict[IncomeSource, float]
            Current income by source (used for pre-retirement projections)
        retirement_corpus : float
            Expected retirement corpus at retirement age (excluding EPF/NPS)
        withdrawal_rate : float, default 0.04
            Annual withdrawal rate from retirement corpus
        pension_monthly : float, default 0
            Expected monthly pension amount
        epf_balance : float, default 0
            Current EPF (Employee Provident Fund) balance
        nps_balance : float, default 0
            Current NPS (National Pension System) balance
        govt_benefits_monthly : float, default 0
            Expected monthly government benefits (e.g., social security)
            
        Returns:
        --------
        IncomeResult
            Object containing income projection results for pre and post-retirement
        """
        # Calculate years for pre-retirement and post-retirement phases
        pre_retirement_years = retirement_age - current_age
        post_retirement_years = life_expectancy - retirement_age
        total_years = life_expectancy - current_age
        
        # First, project pre-retirement income
        pre_retirement = self.project_multiple_income_streams(
            income_sources=current_income,
            years=pre_retirement_years
        )
        
        # Project EPF and NPS balances at retirement
        epf_at_retirement = self._project_epf_balance(
            current_balance=epf_balance,
            years=pre_retirement_years,
            monthly_salary=current_income.get(IncomeSource.SALARY, 0) / 12,
            salary_growth=self.DEFAULT_GROWTH_RATES[IncomeSource.SALARY]
        )
        
        nps_at_retirement = self._project_nps_balance(
            current_balance=nps_balance,
            years=pre_retirement_years,
            monthly_income=sum(current_income.values()) / 12,
            income_growth=self.DEFAULT_GROWTH_RATES[IncomeSource.SALARY]
        )
        
        # Initialize retirement income sources
        retirement_income = {
            IncomeSource.PENSION: pension_monthly * 12,
            IncomeSource.GOVT_BENEFITS: govt_benefits_monthly * 12,
            IncomeSource.INTEREST: retirement_corpus * withdrawal_rate,
            IncomeSource.OTHER: (epf_at_retirement + nps_at_retirement) * 0.05  # Annuitized portion
        }
        
        # Project post-retirement income
        post_retirement = self.project_multiple_income_streams(
            income_sources=retirement_income,
            years=post_retirement_years
        )
        
        # Combine pre and post-retirement results
        combined_years = list(range(total_years + 1))
        combined_income_values = {}
        
        # Initialize combined income values dictionary with all sources
        all_sources = set(list(pre_retirement.income_values.keys()) + list(post_retirement.income_values.keys()))
        for source in all_sources:
            combined_income_values[source] = [0] * (total_years + 1)
        
        # Fill pre-retirement income values
        for source, values in pre_retirement.income_values.items():
            for i, value in enumerate(values):
                combined_income_values[source][i] = value
        
        # Fill post-retirement income values
        for source, values in post_retirement.income_values.items():
            for i, value in enumerate(values):
                combined_income_values[source][i + pre_retirement_years] = value
        
        # Calculate combined total income
        combined_total_income = [0] * (total_years + 1)
        for i in range(pre_retirement_years + 1):
            combined_total_income[i] = pre_retirement.total_income[i]
        
        for i in range(post_retirement_years + 1):
            combined_total_income[i + pre_retirement_years] = post_retirement.total_income[i]
        
        # Calculate after-tax income
        combined_after_tax = self._calculate_after_tax_income(combined_total_income)
        
        # Return combined results
        return IncomeResult(
            years=combined_years,
            income_values=combined_income_values,
            total_income=combined_total_income,
            after_tax_income=combined_after_tax
        )
    
    def project_tax_liability(self, 
                             income_result: IncomeResult,
                             deductions: float = 150000,  # Standard Section 80C deduction
                             additional_deductions: Optional[Dict[int, float]] = None) -> Dict[str, List[float]]:
        """
        Project tax liability over time based on income projections
        
        Parameters:
        -----------
        income_result : IncomeResult
            Income projection result
        deductions : float, default 150000
            Standard annual tax deductions (e.g., 80C in India)
        additional_deductions : Dict[int, float], optional
            Dictionary mapping years to additional deductions for those years
            
        Returns:
        --------
        Dict[str, List[float]]
            Dictionary containing tax liability projections
        """
        tax_liability = []
        taxable_income = []
        tax_rate_effective = []
        
        for year, income in enumerate(income_result.total_income):
            # Calculate deductions for this year
            year_deductions = deductions
            if additional_deductions and year in additional_deductions:
                year_deductions += additional_deductions[year]
            
            # Calculate taxable income
            year_taxable = max(0, income - year_deductions)
            taxable_income.append(year_taxable)
            
            # Calculate tax based on tax regime
            if self.tax_regime == TaxRegime.OLD:
                year_tax = self._calculate_tax_old_regime(year_taxable)
            else:
                year_tax = self._calculate_tax_new_regime(year_taxable)
            
            tax_liability.append(year_tax)
            
            # Calculate effective tax rate
            if income > 0:
                effective_rate = year_tax / income
            else:
                effective_rate = 0
            
            tax_rate_effective.append(effective_rate)
        
        return {
            "tax_liability": tax_liability,
            "taxable_income": taxable_income,
            "effective_tax_rate": tax_rate_effective
        }
    
    def apply_inflation_adjustment(self, income_result: IncomeResult) -> IncomeResult:
        """
        Adjust income projections to account for inflation
        
        Parameters:
        -----------
        income_result : IncomeResult
            Original income projection result in nominal terms
            
        Returns:
        --------
        IncomeResult
            Inflation-adjusted income projection result in real terms
        """
        # Create inflation discount factors for each year
        inflation_factors = [(1 / (1 + self.inflation_rate)) ** year for year in income_result.years]
        
        # Adjust all income values
        real_income_values = {}
        for source, values in income_result.income_values.items():
            real_income_values[source] = [value * factor for value, factor in zip(values, inflation_factors)]
        
        real_total_income = [value * factor for value, factor in zip(income_result.total_income, inflation_factors)]
        real_after_tax = [value * factor for value, factor in zip(income_result.after_tax_income, inflation_factors)]
        
        # Return adjusted results
        return IncomeResult(
            years=income_result.years,
            income_values=real_income_values,
            total_income=real_total_income,
            after_tax_income=real_after_tax
        )
    
    def _calculate_after_tax_income(self, income_values: List[float]) -> List[float]:
        """
        Calculate after-tax income based on income values and current tax regime
        
        Parameters:
        -----------
        income_values : List[float]
            List of total income values
            
        Returns:
        --------
        List[float]
            List of after-tax income values
        """
        after_tax = []
        
        for income in income_values:
            # Apply standard deduction of 50,000 for simplicity
            # In a production system, this would use more detailed deduction logic
            taxable_income = max(0, income - 50000)
            
            # Calculate tax based on current regime
            if self.tax_regime == TaxRegime.OLD:
                tax = self._calculate_tax_old_regime(taxable_income)
            else:
                tax = self._calculate_tax_new_regime(taxable_income)
            
            # Calculate after-tax income
            after_tax_income = income - tax
            after_tax.append(after_tax_income)
        
        return after_tax
    
    def _calculate_tax_old_regime(self, taxable_income: float) -> float:
        """
        Calculate tax under the old tax regime in India
        
        Parameters:
        -----------
        taxable_income : float
            Taxable income after deductions
            
        Returns:
        --------
        float
            Tax liability
        """
        tax = 0
        
        for lower, upper, rate in self.TAX_BRACKETS_OLD_REGIME:
            if taxable_income > lower:
                tax_in_bracket = min(taxable_income - lower, upper - lower) * rate
                tax += tax_in_bracket
        
        # Add surcharge for high income individuals
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
    
    def _calculate_tax_new_regime(self, taxable_income: float) -> float:
        """
        Calculate tax under the new tax regime in India
        
        Parameters:
        -----------
        taxable_income : float
            Taxable income after deductions
            
        Returns:
        --------
        float
            Tax liability
        """
        tax = 0
        
        for lower, upper, rate in self.TAX_BRACKETS_NEW_REGIME:
            if taxable_income > lower:
                tax_in_bracket = min(taxable_income - lower, upper - lower) * rate
                tax += tax_in_bracket
        
        # Add surcharge for high income individuals
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
    
    def _project_epf_balance(self, 
                            current_balance: float,
                            years: int,
                            monthly_salary: float,
                            salary_growth: float) -> float:
        """
        Project EPF (Employee Provident Fund) balance at retirement
        
        Parameters:
        -----------
        current_balance : float
            Current EPF balance
        years : int
            Years until retirement
        monthly_salary : float
            Current monthly salary
        salary_growth : float
            Annual salary growth rate
            
        Returns:
        --------
        float
            Projected EPF balance at retirement
        """
        # Assume EPF contribution is on basic salary, which is typically 50% of CTC
        basic_salary = monthly_salary * 0.5
        
        # Initialize balance
        epf_balance = current_balance
        
        # EPF interest rate (current is ~8.15%, but we'll use a conservative estimate)
        epf_interest_rate = 0.08
        
        # Project year by year
        for year in range(1, years + 1):
            # Calculate basic salary for this year
            basic_salary = basic_salary * (1 + salary_growth)
            
            # Calculate annual contribution (employer + employee)
            annual_contribution = basic_salary * 12 * self.EPF_CONTRIBUTION_RATE * 2
            
            # Add contribution and interest
            epf_balance = (epf_balance + annual_contribution) * (1 + epf_interest_rate)
        
        return epf_balance
    
    def _project_nps_balance(self,
                            current_balance: float,
                            years: int,
                            monthly_income: float,
                            income_growth: float) -> float:
        """
        Project NPS (National Pension System) balance at retirement
        
        Parameters:
        -----------
        current_balance : float
            Current NPS balance
        years : int
            Years until retirement
        monthly_income : float
            Current monthly income
        income_growth : float
            Annual income growth rate
            
        Returns:
        --------
        float
            Projected NPS balance at retirement
        """
        # Initialize balance
        nps_balance = current_balance
        
        # Assume default NPS contribution rate
        contribution_rate = self.NPS_DEFAULT_RATE
        
        # NPS returns (assume a mix of equity, corporate bonds, and government securities)
        nps_return_rate = 0.09  # 9% annual return (conservative estimate)
        
        # Project year by year
        for year in range(1, years + 1):
            # Calculate income for this year
            monthly_income = monthly_income * (1 + income_growth)
            
            # Calculate annual contribution
            annual_contribution = monthly_income * 12 * contribution_rate
            
            # Add contribution and returns
            nps_balance = (nps_balance + annual_contribution) * (1 + nps_return_rate)
        
        return nps_balance
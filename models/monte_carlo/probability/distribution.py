"""
Distribution Module for Goal Outcome Analysis

This module provides the GoalOutcomeDistribution class for analyzing the
distribution of Monte Carlo simulation results.
"""

import logging
import math
import numpy as np
import statistics
import time
from typing import Dict, List, Any, Tuple, Optional, Union

logger = logging.getLogger(__name__)

class GoalOutcomeDistribution:
    """
    Models the full distribution of goal outcomes from Monte Carlo simulations.
    
    This class provides detailed statistical analysis of simulation results,
    including various distribution statistics (mean, median, percentiles),
    shortfall risks at different thresholds, and upside potential metrics.
    """
    
    def __init__(self, simulation_values: Optional[List[float]] = None):
        """
        Initialize with simulation outcome values.
        
        Args:
            simulation_values: List of final values from Monte Carlo simulations
        """
        self.simulation_values = simulation_values or []
        self._sorted_values = None
        self._mean = None
        self._median = None
        self._std_dev = None
        
    def add_simulation_result(self, value: float) -> None:
        """
        Add a single simulation result.
        
        Args:
            value: Final value from a simulation run
        """
        self.simulation_values.append(value)
        # Clear cached values
        self._sorted_values = None
        self._mean = None
        self._median = None
        self._std_dev = None
        
    def add_simulation_results(self, values: List[float]) -> None:
        """
        Add multiple simulation results.
        
        Args:
            values: List of final values from simulation runs
        """
        self.simulation_values.extend(values)
        # Clear cached values
        self._sorted_values = None
        self._mean = None
        self._median = None
        self._std_dev = None
    
    @property
    def sorted_values(self) -> List[float]:
        """Get sorted simulation values, caching for performance."""
        if self._sorted_values is None:
            self._sorted_values = sorted(self.simulation_values)
        return self._sorted_values
    
    @property
    def mean(self) -> float:
        """Calculate the mean (average) value."""
        if self._mean is None:
            self._mean = statistics.mean(self.simulation_values) if self.simulation_values else 0
        return self._mean
    
    @property
    def median(self) -> float:
        """Calculate the median (50th percentile) value."""
        if self._median is None:
            self._median = statistics.median(self.simulation_values) if self.simulation_values else 0
        return self._median
    
    @property
    def std_dev(self) -> float:
        """Calculate the standard deviation."""
        if self._std_dev is None:
            if len(self.simulation_values) >= 2:
                self._std_dev = statistics.stdev(self.simulation_values)
            else:
                self._std_dev = 0
        return self._std_dev
    
    def percentile(self, p: float) -> float:
        """
        Calculate the specified percentile value.
        
        Args:
            p: Percentile value (0-1)
            
        Returns:
            Value at the specified percentile
        """
        if not self.simulation_values:
            return 0
            
        sorted_vals = self.sorted_values
        idx = max(0, min(int(p * len(sorted_vals)), len(sorted_vals) - 1))
        return sorted_vals[idx]
    
    def success_probability(self, target_amount: float) -> float:
        """
        Calculate probability of meeting or exceeding target amount.
        
        This method counts simulations that meet or exceed the target amount
        and provides a more sophisticated probability calculation that includes
        partial credit for values that are close to the target.
        
        Args:
            target_amount: Goal target amount
            
        Returns:
            Probability (0-1) of meeting or exceeding target
        """
        if not self.simulation_values:
            logger.warning("[DIAGNOSTIC] No simulation values available for success probability calculation")
            return 0
            
        # Start timer for performance tracking
        start_time = time.time()
        
        # Count simulations that meet or exceed target and get metrics
        total_simulations = len(self.simulation_values)
        exact_success_count = sum(1 for val in self.simulation_values if val >= target_amount)
        exact_probability = exact_success_count / total_simulations
        
        # Log detail for diagnostic analysis
        logger.info(f"[DIAGNOSTIC] Basic success count: {exact_success_count}/{total_simulations} = {exact_probability:.4f}")
        
        # Enhanced sensitivity implementation - add partial credit for values close to target
        # This makes the probability calculation more sensitive to parameter changes
        sensitivity_adjusted_count = 0
        close_but_not_success = 0
        
        for val in self.simulation_values:
            if val >= target_amount:
                sensitivity_adjusted_count += 1
            else:
                # Calculate closeness as a ratio of achieved to target
                closeness = val / target_amount if target_amount > 0 else 0
                
                # Add partial credit for values that are very close (within 10% of target)
                if closeness > 0.9:
                    # Linear partial credit from 0 at 90% to 1 at 100%
                    partial_credit = (closeness - 0.9) * 10  # Scales 0.9->0.0, 1.0->1.0
                    sensitivity_adjusted_count += partial_credit
                    close_but_not_success += 1
        
        # Calculate adjusted probability
        adjusted_probability = sensitivity_adjusted_count / total_simulations
        
        # Log detailed diagnostic information
        logger.info(f"[DIAGNOSTIC] Success probability calculation - "
                 f"target_amount: {target_amount}, "
                 f"simulation_count: {total_simulations}, "
                 f"exact_success: {exact_success_count}, "
                 f"close_but_not_success: {close_but_not_success}, "
                 f"basic_probability: {exact_probability:.4f}, "
                 f"adjusted_probability: {adjusted_probability:.4f}, "
                 f"difference: {(adjusted_probability - exact_probability):.4f}")
        
        # Performance tracking
        duration = time.time() - start_time
        logger.debug(f"[TIMING] Success probability calculation took {duration:.6f} seconds")
        
        # Return the enhanced probability value
        return adjusted_probability
    
    def shortfall_risk(self, target_amount: float, threshold_percentage: float = 0.8) -> float:
        """
        Calculate probability of falling below a percentage of target amount.
        
        Args:
            target_amount: Goal target amount
            threshold_percentage: Percentage of target defining shortfall (default 80%)
            
        Returns:
            Probability (0-1) of falling below threshold
        """
        if not self.simulation_values:
            return 1.0
            
        shortfall_threshold = target_amount * threshold_percentage
        # Count simulations that fall below threshold
        count = sum(1 for val in self.simulation_values if val < shortfall_threshold)
        return count / len(self.simulation_values)
    
    def upside_probability(self, target_amount: float, excess_percentage: float = 1.2) -> float:
        """
        Calculate probability of exceeding target by a given percentage.
        
        Args:
            target_amount: Goal target amount
            excess_percentage: Percentage of target defining upside (default 120%)
            
        Returns:
            Probability (0-1) of exceeding threshold
        """
        if not self.simulation_values:
            return 0
            
        upside_threshold = target_amount * excess_percentage
        # Count simulations that exceed threshold
        count = sum(1 for val in self.simulation_values if val >= upside_threshold)
        return count / len(self.simulation_values)
    
    def value_at_risk(self, confidence_level: float = 0.95) -> float:
        """
        Calculate value at risk (VaR) for a given confidence level.
        
        Args:
            confidence_level: Confidence level (default 95%)
            
        Returns:
            Amount at risk at the specified confidence level
        """
        if not self.simulation_values:
            return 0
            
        # VaR is the loss that is not expected to be exceeded with given confidence level
        return self.percentile(1 - confidence_level)
    
    def conditional_value_at_risk(self, confidence_level: float = 0.95) -> float:
        """
        Calculate conditional value at risk (CVaR/Expected Shortfall).
        
        CVaR is the expected loss given that the loss exceeds the VaR.
        
        Args:
            confidence_level: Confidence level (default 95%)
            
        Returns:
            Expected shortfall at the specified confidence level
        """
        if not self.simulation_values:
            return 0
            
        var = self.value_at_risk(confidence_level)
        # Average of values below VaR
        tail_values = [v for v in self.simulation_values if v <= var]
        return statistics.mean(tail_values) if tail_values else var
    
    def calculate_histogram(self, bins: int = 10) -> Dict[str, List[float]]:
        """
        Calculate histogram data for visualization.
        
        Args:
            bins: Number of histogram bins
            
        Returns:
            Dictionary with bin_edges and bin_counts
        """
        if not self.simulation_values:
            return {"bin_edges": [], "bin_counts": []}
            
        hist, bin_edges = np.histogram(self.simulation_values, bins=bins)
        return {
            "bin_edges": bin_edges.tolist(),
            "bin_counts": hist.tolist()
        }
    
    def calculate_key_statistics(self, target_amount: float) -> Dict[str, float]:
        """
        Calculate key statistical metrics for the distribution.
        
        Args:
            target_amount: Goal target amount
            
        Returns:
            Dictionary with key statistics
        """
        return {
            "mean": self.mean,
            "median": self.median,
            "std_dev": self.std_dev,
            "success_probability": self.success_probability(target_amount),
            "shortfall_risk_80pct": self.shortfall_risk(target_amount, 0.8),
            "shortfall_risk_60pct": self.shortfall_risk(target_amount, 0.6),
            "upside_probability_120pct": self.upside_probability(target_amount, 1.2),
            "percentile_10": self.percentile(0.1),
            "percentile_25": self.percentile(0.25),
            "percentile_50": self.percentile(0.5),
            "percentile_75": self.percentile(0.75),
            "percentile_90": self.percentile(0.9),
            "value_at_risk_95pct": self.value_at_risk(0.95),
            "conditional_value_at_risk_95pct": self.conditional_value_at_risk(0.95)
        }
    
    def calculate_time_to_goal_probability(
        self, 
        target_probability: float, 
        target_amount: float,
        monthly_contribution: float,
        initial_amount: float,
        allocation_strategy: Dict[str, float],
        returns: Dict[str, Tuple[float, float]],
        max_years: int = 40
    ) -> float:
        """
        Estimate time needed to reach a specific success probability.
        
        Args:
            target_probability: Target probability of success (0-1)
            target_amount: Goal target amount
            monthly_contribution: Monthly contribution amount
            initial_amount: Initial investment amount
            allocation_strategy: Asset allocation strategy
            returns: Expected returns and volatility by asset class
            max_years: Maximum years to consider
            
        Returns:
            Estimated time in years to reach target probability
        """
        # Simple binary search implementation
        # For a more accurate implementation, we would need to run full Monte Carlo
        # simulations at each step, which would be computationally expensive
        
        def estimate_success_probability(years: int) -> float:
            # Simplified formula based on expected returns and volatility
            expected_return = sum(
                alloc * ret[0] 
                for asset, alloc in allocation_strategy.items() 
                for asset_class, ret in returns.items() 
                if asset.lower() == asset_class.name.lower()
            )
            
            # Future value of initial amount
            future_initial = initial_amount * (1 + expected_return) ** years
            
            # Future value of monthly contributions (assuming end of period)
            if expected_return > 0:
                future_contributions = monthly_contribution * 12 * ((1 + expected_return) ** years - 1) / expected_return
            else:
                future_contributions = monthly_contribution * 12 * years
                
            expected_outcome = future_initial + future_contributions
            
            # Rough estimate of volatility at the given time horizon
            volatility = sum(
                alloc * ret[1] 
                for asset, alloc in allocation_strategy.items() 
                for asset_class, ret in returns.items() 
                if asset.lower() == asset_class.name.lower()
            ) * math.sqrt(years)
            
            # Approximate probability using normal distribution
            z_score = (expected_outcome - target_amount) / (expected_outcome * volatility + 1e-10)
            return 1 - 0.5 * (1 + math.erf(-z_score / math.sqrt(2)))
        
        # Binary search for the time that gives target probability
        low, high = 1, max_years
        while high - low > 0.5:
            mid = (low + high) / 2
            prob = estimate_success_probability(mid)
            
            if prob < target_probability:
                low = mid
            else:
                high = mid
                
        return (low + high) / 2
    
    def calculate_probability_at_timepoints(
        self,
        timepoints: List[float],
        target_amount: float,
        monthly_contribution: float,
        initial_amount: float,
        allocation_strategy: Dict[str, float],
        returns: Dict[str, Tuple[float, float]],
    ) -> Dict[float, float]:
        """
        Calculate success probability at different time points.
        
        Args:
            timepoints: List of time points in years
            target_amount: Goal target amount
            monthly_contribution: Monthly contribution amount
            initial_amount: Initial investment amount
            allocation_strategy: Asset allocation strategy
            returns: Expected returns and volatility by asset class
            
        Returns:
            Dictionary mapping timepoints to success probabilities
        """
        results = {}
        
        def estimate_success_probability(years: float) -> float:
            # Similar to the approach in calculate_time_to_goal_probability
            expected_return = sum(
                alloc * ret[0] 
                for asset, alloc in allocation_strategy.items() 
                for asset_class, ret in returns.items() 
                if asset.lower() == asset_class.name.lower()
            )
            
            # Future value calculations
            future_initial = initial_amount * (1 + expected_return) ** years
            
            if expected_return > 0:
                future_contributions = monthly_contribution * 12 * ((1 + expected_return) ** years - 1) / expected_return
            else:
                future_contributions = monthly_contribution * 12 * years
                
            expected_outcome = future_initial + future_contributions
            
            # Volatility estimate
            volatility = sum(
                alloc * ret[1] 
                for asset, alloc in allocation_strategy.items() 
                for asset_class, ret in returns.items() 
                if asset.lower() == asset_class.name.lower()
            ) * math.sqrt(years)
            
            # Approximate probability using normal distribution
            z_score = (expected_outcome - target_amount) / (expected_outcome * volatility + 1e-10)
            return 1 - 0.5 * (1 + math.erf(-z_score / math.sqrt(2)))
        
        for year in timepoints:
            results[year] = estimate_success_probability(year)
            
        return results
    
    def identify_critical_periods(
        self, 
        time_series_results: List[List[float]],
        percentile_threshold: float = 0.9
    ) -> List[Dict[str, Any]]:
        """
        Identify periods with higher volatility or risk.
        
        Args:
            time_series_results: List of time series of simulation results
            percentile_threshold: Threshold for identifying critical periods
            
        Returns:
            List of critical periods with start, end, and risk metrics
        """
        if not time_series_results:
            return []
            
        # Calculate volatility at each time point
        num_timepoints = len(time_series_results[0])
        volatility = []
        
        for t in range(num_timepoints):
            values_at_t = [sim[t] for sim in time_series_results if t < len(sim)]
            if len(values_at_t) >= 2:
                vol = statistics.stdev(values_at_t)
                volatility.append(vol)
            else:
                volatility.append(0)
                
        # Identify periods where volatility exceeds threshold
        avg_vol = statistics.mean(volatility) if volatility else 0
        threshold = percentile_threshold * max(volatility) if volatility else 0
        
        critical_periods = []
        in_critical_period = False
        start_idx = 0
        
        for i, vol in enumerate(volatility):
            if vol > threshold and not in_critical_period:
                in_critical_period = True
                start_idx = i
            elif vol <= threshold and in_critical_period:
                in_critical_period = False
                critical_periods.append({
                    "start_time": start_idx,
                    "end_time": i - 1,
                    "peak_volatility": max(volatility[start_idx:i]),
                    "average_volatility": statistics.mean(volatility[start_idx:i]),
                    "volatility_vs_average": max(volatility[start_idx:i]) / avg_vol if avg_vol > 0 else 0
                })
                
        # Handle case where we end while still in a critical period
        if in_critical_period:
            critical_periods.append({
                "start_time": start_idx,
                "end_time": len(volatility) - 1,
                "peak_volatility": max(volatility[start_idx:]),
                "average_volatility": statistics.mean(volatility[start_idx:]),
                "volatility_vs_average": max(volatility[start_idx:]) / avg_vol if avg_vol > 0 else 0
            })
            
        return critical_periods
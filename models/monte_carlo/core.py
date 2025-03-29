"""
Core Monte Carlo simulation functionality for financial projections.

This module handles the core simulation logic for different types of financial goals,
providing a clean API for running simulations with different parameters.
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
import json
from datetime import date, datetime

from models.financial_projection import AllocationStrategy, ContributionPattern, ProjectionResult

logger = logging.getLogger(__name__)

class MonteCarloSimulation:
    """Monte Carlo simulation for financial goal projections."""
    
    def __init__(
        self, 
        goal: Any,
        return_assumptions: Dict[str, float],
        inflation_rate: float = 0.06,
        simulation_count: int = 1000,
        time_horizon_years: Optional[int] = None
    ):
        """
        Initialize the Monte Carlo simulation with given parameters.
        
        Args:
            goal: The financial goal to simulate
            return_assumptions: Asset class return assumptions
            inflation_rate: Annual inflation rate assumption
            simulation_count: Number of simulations to run
            time_horizon_years: Optional override for simulation timeframe
        """
        self.goal = goal
        self.return_assumptions = return_assumptions
        self.inflation_rate = inflation_rate
        self.simulation_count = simulation_count
        
        # Calculate time horizon from goal target date if not specified
        if time_horizon_years is None and hasattr(goal, 'target_date'):
            today = date.today()
            if isinstance(goal.target_date, str):
                goal_date = datetime.fromisoformat(goal.target_date).date()
            else:
                goal_date = goal.target_date
                
            self.time_horizon_years = max(1, (goal_date.year - today.year))
        else:
            self.time_horizon_years = time_horizon_years or 20
    
    def run_simulation(self) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for the goal.
        
        Returns:
            Dictionary with simulation results
        """
        # Get goal parameters
        goal_amount = getattr(self.goal, 'target_amount', 0)
        current_amount = getattr(self.goal, 'current_amount', 0)
        monthly_contribution = getattr(self.goal, 'monthly_contribution', 0)
        years = self.time_horizon_years
        
        # Create allocation strategy from goal's asset allocation
        if hasattr(self.goal, 'asset_allocation') and self.goal.asset_allocation:
            allocation = self.goal.asset_allocation
        else:
            # Default moderate allocation
            allocation = {"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05}
        
        allocation_strategy = self._create_allocation_strategy(allocation)
        
        # Create contribution pattern
        contribution_pattern = self._create_contribution_pattern(
            monthly_contribution=monthly_contribution,
            years=years
        )
        
        # Run the simulation based on goal type
        goal_type = getattr(self.goal, 'type', 'generic').lower()
        
        # Delegate to specific simulation method based on goal type
        if goal_type in ('retirement', 'early_retirement'):
            return self._simulate_retirement_goal(
                current_amount, goal_amount, years, allocation_strategy, contribution_pattern
            )
        elif goal_type == 'education':
            return self._simulate_education_goal(
                current_amount, goal_amount, years, allocation_strategy, contribution_pattern
            )
        elif goal_type == 'emergency_fund':
            return self._simulate_emergency_fund_goal(
                current_amount, goal_amount, years, allocation_strategy, contribution_pattern
            )
        elif goal_type in ('home', 'home_purchase'):
            return self._simulate_home_purchase_goal(
                current_amount, goal_amount, years, allocation_strategy, contribution_pattern
            )
        elif goal_type == 'debt_repayment':
            return self._simulate_debt_repayment_goal(
                current_amount, goal_amount, years, allocation_strategy, contribution_pattern
            )
        elif goal_type == 'wedding':
            return self._simulate_wedding_goal(
                current_amount, goal_amount, years, allocation_strategy, contribution_pattern
            )
        elif goal_type == 'charitable_giving':
            return self._simulate_charitable_giving_goal(
                current_amount, goal_amount, years, allocation_strategy, contribution_pattern
            )
        elif goal_type == 'legacy_planning':
            return self._simulate_legacy_planning_goal(
                current_amount, goal_amount, years, allocation_strategy, contribution_pattern
            )
        elif goal_type == 'discretionary':
            subcategory = getattr(self.goal, 'subcategory', 'general').lower()
            if subcategory == 'travel':
                return self._simulate_travel_goal(
                    current_amount, goal_amount, years, allocation_strategy, contribution_pattern
                )
            elif subcategory == 'vehicle':
                return self._simulate_vehicle_goal(
                    current_amount, goal_amount, years, allocation_strategy, contribution_pattern
                )
            else:
                return self._simulate_discretionary_goal(
                    current_amount, goal_amount, years, allocation_strategy, contribution_pattern
                )
        elif goal_type == 'custom':
            return self._simulate_custom_goal(
                current_amount, goal_amount, years, allocation_strategy, contribution_pattern
            )
        else:
            # Generic simulation for any other goal type
            return self._simulate_generic_goal(
                current_amount, goal_amount, years, allocation_strategy, contribution_pattern
            )
    
    def _create_allocation_strategy(self, allocation: Dict[str, float]) -> AllocationStrategy:
        """Create allocation strategy from asset allocation dictionary."""
        # This would create a proper AllocationStrategy in a real implementation
        # For now, we return a simple mock object for testing
        from unittest.mock import MagicMock
        
        allocation_strategy = MagicMock(spec=AllocationStrategy)
        
        # Calculate expected return and volatility based on allocation
        expected_return = sum(
            allocation.get(asset, 0) * self.return_assumptions.get(asset, 0)
            for asset in allocation
        )
        
        # Simple volatility estimate based on allocation
        # In reality this would use a covariance matrix
        equity_weight = allocation.get('equity', 0)
        debt_weight = allocation.get('debt', 0)
        
        # Higher equity = higher volatility
        volatility = 0.05 + equity_weight * 0.12 + debt_weight * 0.03
        
        allocation_strategy.get_expected_return.return_value = expected_return
        allocation_strategy.get_volatility.return_value = volatility
        
        return allocation_strategy
    
    def _create_contribution_pattern(self, monthly_contribution: float, years: int) -> ContributionPattern:
        """Create contribution pattern from monthly contribution amount."""
        # This would create a proper ContributionPattern in a real implementation
        # For now, we return a simple mock object for testing
        from unittest.mock import MagicMock
        
        contribution_pattern = MagicMock(spec=ContributionPattern)
        annual_contribution = monthly_contribution * 12
        
        # Set up the contribution pattern to return annual contributions
        contribution_pattern.get_contribution_for_year.side_effect = (
            lambda year: annual_contribution if year <= years else 0
        )
        
        return contribution_pattern
    
    def _simulate_generic_goal(
        self, 
        current_amount: float,
        goal_amount: float,
        years: int,
        allocation_strategy: AllocationStrategy,
        contribution_pattern: ContributionPattern
    ) -> Dict[str, Any]:
        """Run a generic simulation applicable to any goal type."""
        # Set up simulation
        np.random.seed(42)  # For reproducibility
        
        # Get parameters
        expected_return = allocation_strategy.get_expected_return()
        volatility = allocation_strategy.get_volatility()
        
        # Initialize results arrays
        simulation_results = np.zeros((self.simulation_count, years + 1))
        simulation_results[:, 0] = current_amount
        
        # Run simulations
        for sim in range(self.simulation_count):
            current_value = current_amount
            for year in range(1, years + 1):
                # Get contribution for this year
                contribution = contribution_pattern.get_contribution_for_year(year)
                
                # Generate random return for this year
                annual_return = np.random.normal(expected_return, volatility)
                
                # Update amount (apply return and add contribution)
                current_value = max(0, current_value * (1 + annual_return) + contribution)
                simulation_results[sim, year] = current_value
        
        # Calculate success probability
        final_values = simulation_results[:, -1]
        success_count = np.sum(final_values >= goal_amount)
        success_probability = success_count / self.simulation_count
        
        # Calculate percentiles
        percentiles = {
            "10": np.percentile(final_values, 10),
            "25": np.percentile(final_values, 25),
            "50": np.percentile(final_values, 50),
            "75": np.percentile(final_values, 75),
            "90": np.percentile(final_values, 90)
        }
        
        # Calculate achievement timeline
        goal_achievement_timeline = self._calculate_achievement_timeline(
            goal_amount, years, simulation_results
        )
        
        # Return results
        return {
            "goal_amount": goal_amount,
            "goal_timeline_years": years,
            "simulation_results": final_values,
            "success_probability": success_probability,
            "percentiles": percentiles,
            "goal_achievement_timeline": goal_achievement_timeline
        }
    
    def _simulate_retirement_goal(
        self, 
        current_amount: float,
        goal_amount: float,
        years: int,
        allocation_strategy: AllocationStrategy,
        contribution_pattern: ContributionPattern
    ) -> Dict[str, Any]:
        """Run simulation specific to retirement goals."""
        # For retirement, we might adjust volatility based on years to retirement
        adjusted_allocation = allocation_strategy
        
        # If less than 5 years to retirement, we might use a more conservative allocation
        if years < 5:
            # Get a more conservative expected return and volatility
            adjusted_expected_return = allocation_strategy.get_expected_return() * 0.8
            adjusted_volatility = allocation_strategy.get_volatility() * 0.7
            
            # Update the allocation strategy
            adjusted_allocation.get_expected_return.return_value = adjusted_expected_return
            adjusted_allocation.get_volatility.return_value = adjusted_volatility
        
        # Run the simulation using the adjusted allocation
        results = self._simulate_generic_goal(
            current_amount, goal_amount, years, adjusted_allocation, contribution_pattern
        )
        
        # Add retirement-specific metrics
        results["retirement_income_ratio"] = results["percentiles"]["50"] / goal_amount
        
        return results
    
    def _simulate_education_goal(
        self, 
        current_amount: float,
        goal_amount: float,
        years: int,
        allocation_strategy: AllocationStrategy,
        contribution_pattern: ContributionPattern
    ) -> Dict[str, Any]:
        """Run simulation specific to education goals."""
        # For education, we might use a different inflation rate
        education_inflation = self.inflation_rate * 1.5  # Education costs often rise faster
        
        # Adjust the goal amount for education-specific inflation
        inflation_adjusted_goal = goal_amount * (1 + education_inflation) ** years
        
        # Run the simulation with the adjusted goal
        results = self._simulate_generic_goal(
            current_amount, inflation_adjusted_goal, years, allocation_strategy, contribution_pattern
        )
        
        # Add education-specific metrics
        results["education_inflation_impact"] = inflation_adjusted_goal / goal_amount - 1
        
        return results
    
    def _simulate_emergency_fund_goal(
        self, 
        current_amount: float,
        goal_amount: float,
        years: int,
        allocation_strategy: AllocationStrategy,
        contribution_pattern: ContributionPattern
    ) -> Dict[str, Any]:
        """Run simulation specific to emergency fund goals."""
        # Emergency funds typically use very conservative allocations
        conservative_allocation = allocation_strategy
        
        # Override with very conservative returns
        conservative_allocation.get_expected_return.return_value = 0.04  # 4% expected return
        conservative_allocation.get_volatility.return_value = 0.02  # Low volatility
        
        # Run the simulation with the conservative allocation
        results = self._simulate_generic_goal(
            current_amount, goal_amount, years, conservative_allocation, contribution_pattern
        )
        
        # Add emergency fund specific metrics
        monthly_expenses = goal_amount / 6  # Typical emergency fund is 6 months of expenses
        results["months_of_expenses_covered"] = results["percentiles"]["50"] / monthly_expenses
        
        return results
    
    # Implement simulation methods for other goal types
    def _simulate_home_purchase_goal(self, current_amount, goal_amount, years, allocation_strategy, contribution_pattern):
        """Run simulation specific to home purchase goals."""
        # For home purchases, we might factor in real estate appreciation
        real_estate_appreciation = 0.05  # 5% annual appreciation
        
        # Adjust the goal amount based on real estate appreciation
        adjusted_goal = goal_amount * (1 + real_estate_appreciation) ** years
        
        # Get more conservative allocation for near-term home purchases
        if years <= 3:
            allocation_strategy.get_expected_return.return_value = 0.05
            allocation_strategy.get_volatility.return_value = 0.04
        
        # Run the simulation with the adjusted parameters
        results = self._simulate_generic_goal(
            current_amount, adjusted_goal, years, allocation_strategy, contribution_pattern
        )
        
        # Add home-specific metrics
        down_payment_percentage = min(1.0, results["percentiles"]["50"] / adjusted_goal)
        results["down_payment_percentage"] = down_payment_percentage
        results["loan_to_value_ratio"] = 1.0 - down_payment_percentage if down_payment_percentage < 1.0 else 0.0
        
        return results
    
    def _simulate_debt_repayment_goal(self, current_amount, goal_amount, years, allocation_strategy, contribution_pattern):
        """Run simulation specific to debt repayment goals."""
        # For debt repayment, we might consider interest rates
        debt_interest_rate = 0.08  # 8% interest rate on debt
        
        # Adjust the goal amount based on interest accrual
        adjusted_goal = goal_amount * (1 + debt_interest_rate) ** (years / 2)  # Assuming gradual paydown
        
        # Run the simulation with the adjusted goal
        results = self._simulate_generic_goal(
            current_amount, adjusted_goal, years, allocation_strategy, contribution_pattern
        )
        
        # Add debt-specific metrics
        results["interest_savings"] = adjusted_goal - goal_amount
        results["debt_free_percentage"] = min(1.0, results["percentiles"]["50"] / adjusted_goal)
        
        return results
    
    def _simulate_wedding_goal(self, current_amount, goal_amount, years, allocation_strategy, contribution_pattern):
        """Run simulation specific to wedding goals."""
        # Weddings have specific inflation rates
        wedding_inflation = 0.07  # 7% wedding cost inflation
        
        # Adjust the goal based on wedding inflation
        adjusted_goal = goal_amount * (1 + wedding_inflation) ** years
        
        # More conservative allocation for short-term wedding goals
        if years <= 2:
            allocation_strategy.get_expected_return.return_value = 0.04
            allocation_strategy.get_volatility.return_value = 0.03
        
        # Run the simulation with the adjusted parameters
        results = self._simulate_generic_goal(
            current_amount, adjusted_goal, years, allocation_strategy, contribution_pattern
        )
        
        # Add wedding-specific metrics
        results["wedding_budget_coverage"] = results["percentiles"]["50"] / adjusted_goal
        results["wedding_inflation_impact"] = adjusted_goal / goal_amount - 1
        
        return results
    
    def _simulate_charitable_giving_goal(self, current_amount, goal_amount, years, allocation_strategy, contribution_pattern):
        """Run simulation specific to charitable giving goals."""
        # Charitable giving might have tax benefits
        tax_benefit_rate = 0.30  # 30% tax benefit
        
        # Adjust goal to account for tax benefits
        effective_goal = goal_amount * (1 - tax_benefit_rate)
        
        # Run the simulation with the adjusted goal
        results = self._simulate_generic_goal(
            current_amount, effective_goal, years, allocation_strategy, contribution_pattern
        )
        
        # Add charitable giving specific metrics
        results["tax_benefit_amount"] = goal_amount * tax_benefit_rate
        results["giving_capacity"] = results["percentiles"]["50"] / (1 - tax_benefit_rate)
        
        return results
    
    def _simulate_legacy_planning_goal(self, current_amount, goal_amount, years, allocation_strategy, contribution_pattern):
        """Run simulation specific to legacy planning goals."""
        # Legacy planning might involve estate taxes
        estate_tax_rate = 0.40  # 40% estate tax
        
        # Adjust the goal to account for estate taxes
        adjusted_goal = goal_amount / (1 - estate_tax_rate)
        
        # Run the simulation with the adjusted goal
        results = self._simulate_generic_goal(
            current_amount, adjusted_goal, years, allocation_strategy, contribution_pattern
        )
        
        # Add legacy planning specific metrics
        results["estate_tax_impact"] = adjusted_goal - goal_amount
        results["legacy_funding_ratio"] = results["percentiles"]["50"] / adjusted_goal
        
        return results
    
    def _simulate_travel_goal(self, current_amount, goal_amount, years, allocation_strategy, contribution_pattern):
        """Run simulation specific to travel goals."""
        # Travel costs increase with inflation
        travel_inflation = self.inflation_rate * 1.2  # Travel costs often rise faster
        
        # Adjust the goal for travel inflation
        adjusted_goal = goal_amount * (1 + travel_inflation) ** years
        
        # More conservative allocation for short-term travel goals
        if years <= 2:
            allocation_strategy.get_expected_return.return_value = 0.04
            allocation_strategy.get_volatility.return_value = 0.03
        
        # Run the simulation with the adjusted parameters
        results = self._simulate_generic_goal(
            current_amount, adjusted_goal, years, allocation_strategy, contribution_pattern
        )
        
        # Add travel-specific metrics
        results["travel_budget_coverage"] = results["percentiles"]["50"] / adjusted_goal
        results["travel_inflation_impact"] = adjusted_goal / goal_amount - 1
        
        return results
    
    def _simulate_vehicle_goal(self, current_amount, goal_amount, years, allocation_strategy, contribution_pattern):
        """Run simulation specific to vehicle purchase goals."""
        # Vehicle costs change over time
        vehicle_inflation = 0.04  # 4% vehicle cost changes
        
        # Adjust the goal for vehicle inflation
        adjusted_goal = goal_amount * (1 + vehicle_inflation) ** years
        
        # More conservative allocation for short-term vehicle goals
        if years <= 3:
            allocation_strategy.get_expected_return.return_value = 0.04
            allocation_strategy.get_volatility.return_value = 0.03
        
        # Run the simulation with the adjusted parameters
        results = self._simulate_generic_goal(
            current_amount, adjusted_goal, years, allocation_strategy, contribution_pattern
        )
        
        # Add vehicle-specific metrics
        results["vehicle_budget_coverage"] = results["percentiles"]["50"] / adjusted_goal
        
        return results
    
    def _simulate_discretionary_goal(self, current_amount, goal_amount, years, allocation_strategy, contribution_pattern):
        """Run simulation for general discretionary goals."""
        # Discretionary goals typically have lower priority
        
        # More conservative allocation for short-term discretionary goals
        if years <= 2:
            allocation_strategy.get_expected_return.return_value = 0.04
            allocation_strategy.get_volatility.return_value = 0.03
        
        # Run the simulation
        results = self._simulate_generic_goal(
            current_amount, goal_amount, years, allocation_strategy, contribution_pattern
        )
        
        # Add discretionary-specific metrics
        results["discretionary_budget_coverage"] = results["percentiles"]["50"] / goal_amount
        
        return results
    
    def _simulate_custom_goal(self, current_amount, goal_amount, years, allocation_strategy, contribution_pattern):
        """Run simulation for custom goals with user-defined parameters."""
        # Custom goals might have specific parameters
        
        # Get custom parameters from the goal if available
        custom_inflation = getattr(self.goal, 'custom_inflation_rate', self.inflation_rate)
        custom_volatility_factor = getattr(self.goal, 'custom_volatility_factor', 1.0)
        
        # Adjust the goal for custom inflation
        adjusted_goal = goal_amount * (1 + custom_inflation) ** years
        
        # Adjust volatility based on custom factor
        custom_volatility = allocation_strategy.get_volatility() * custom_volatility_factor
        allocation_strategy.get_volatility.return_value = custom_volatility
        
        # Run the simulation with the adjusted parameters
        results = self._simulate_generic_goal(
            current_amount, adjusted_goal, years, allocation_strategy, contribution_pattern
        )
        
        # Add custom-specific metrics
        results["custom_funding_ratio"] = results["percentiles"]["50"] / adjusted_goal
        results["custom_inflation_impact"] = adjusted_goal / goal_amount - 1
        
        return results
    
    def _calculate_achievement_timeline(
        self, 
        goal_amount: float,
        years: int,
        simulation_results: np.ndarray
    ) -> Dict[str, Any]:
        """
        Calculate when the goal is likely to be achieved.
        
        Args:
            goal_amount: Target amount for the goal
            years: Total years in the simulation
            simulation_results: Array of simulation results (shape: simulations x years)
            
        Returns:
            Dictionary with timeline metrics
        """
        # Initialize variables
        achievement_years = []
        
        # For each simulation run
        for sim in range(simulation_results.shape[0]):
            # Find the first year where the goal is achieved
            for year in range(years + 1):
                if simulation_results[sim, year] >= goal_amount:
                    achievement_years.append(year)
                    break
            else:
                # Goal not achieved in this simulation
                achievement_years.append(years + 1)
        
        # Convert to numpy array for calculations
        achievement_years = np.array(achievement_years)
        
        # Calculate median achievement time
        median_year = np.median(achievement_years)
        
        # Calculate months component (fractional part of year)
        whole_years = int(median_year)
        months = int((median_year - whole_years) * 12)
        
        return {
            "years": whole_years,
            "months": months
        }
    
    def _calculate_percentiles(self, simulated_results: np.ndarray) -> Dict[str, float]:
        """
        Calculate percentiles from simulation results.
        
        Args:
            simulated_results: Array of final simulation values
            
        Returns:
            Dictionary of percentile values
        """
        return {
            "10": np.percentile(simulated_results, 10),
            "25": np.percentile(simulated_results, 25),
            "50": np.percentile(simulated_results, 50),
            "75": np.percentile(simulated_results, 75),
            "90": np.percentile(simulated_results, 90)
        }
    
    def _calculate_success_probability(self, simulated_results: np.ndarray, target_amount: float) -> float:
        """
        Calculate probability of success (reaching target amount).
        
        Args:
            simulated_results: Array of final simulation values
            target_amount: Goal target amount
            
        Returns:
            Success probability (0.0 to 1.0)
        """
        # Count simulations where final value exceeds target
        success_count = np.sum(simulated_results >= target_amount)
        
        # Calculate probability
        return success_count / len(simulated_results)


def run_simulation(
    goal: Any,
    return_assumptions: Dict[str, float],
    inflation_rate: float = 0.06,
    simulation_count: int = 1000,
    time_horizon_years: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a Monte Carlo simulation for a financial goal.
    
    Args:
        goal: The financial goal to simulate
        return_assumptions: Asset class return assumptions
        inflation_rate: Annual inflation rate assumption
        simulation_count: Number of simulations to run
        time_horizon_years: Optional override for simulation timeframe
        
    Returns:
        Dictionary with simulation results
    """
    # Create simulation instance
    simulation = MonteCarloSimulation(
        goal=goal,
        return_assumptions=return_assumptions,
        inflation_rate=inflation_rate,
        simulation_count=simulation_count,
        time_horizon_years=time_horizon_years
    )
    
    # Run the simulation
    return simulation.run_simulation()


def get_simulation_config(goal_type: str) -> Dict[str, Any]:
    """
    Get recommended simulation configuration for a specific goal type.
    
    Args:
        goal_type: Type of financial goal
        
    Returns:
        Dictionary with recommended configuration
    """
    # Base configuration
    base_config = {
        "simulation_count": 1000,
        "time_horizon_years": None,  # Use goal target date
        "inflation_rate": 0.06,
        "return_assumptions": {
            "equity": 0.10,
            "debt": 0.06,
            "gold": 0.07,
            "cash": 0.04
        }
    }
    
    # Adjust based on goal type
    if goal_type in ('retirement', 'early_retirement'):
        # Retirement goals need more simulations and higher equity allocation
        return {
            **base_config,
            "simulation_count": 2000,
            "return_assumptions": {
                "equity": 0.10,
                "debt": 0.06,
                "gold": 0.07,
                "cash": 0.04
            }
        }
    elif goal_type == 'education':
        # Education goals have higher inflation
        return {
            **base_config,
            "inflation_rate": 0.08,
            "return_assumptions": {
                "equity": 0.09,
                "debt": 0.06,
                "gold": 0.07,
                "cash": 0.04
            }
        }
    elif goal_type == 'emergency_fund':
        # Emergency funds need lower volatility
        return {
            **base_config,
            "simulation_count": 500,  # Less simulations needed for short-term goals
            "return_assumptions": {
                "equity": 0.05,
                "debt": 0.05,
                "gold": 0.06,
                "cash": 0.04
            }
        }
    elif goal_type in ('home', 'home_purchase'):
        # Home purchase goals need moderate risk
        return {
            **base_config,
            "inflation_rate": 0.07,  # Housing inflation
            "return_assumptions": {
                "equity": 0.08,
                "debt": 0.06,
                "gold": 0.07,
                "cash": 0.04
            }
        }
    else:
        # Default configuration for other goal types
        return base_config
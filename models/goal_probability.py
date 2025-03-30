# -*- coding: utf-8 -*-
"""
Module for calculating and analyzing goal achievement probability using Monte Carlo simulations.

This module provides classes and functions for:
- Generating Monte Carlo simulations for various financial goals
- Analyzing simulation results to calculate success probability and other metrics
- Providing detailed statistical analysis of goal outcomes
- Estimating time needed to reach a specific success probability
- Calculating probability at different time points

The module is designed to be flexible and extensible, allowing for customization of simulation parameters,
goal-specific calculations, and integration with other financial planning modules.
"""

import dataclasses
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.stats import norm

from models.financial_parameters import FinancialParameters
from models.goal_calculators.base_calculator import GoalCalculator
from models.monte_carlo.array_fix import to_scalar
from models.monte_carlo.cache import SimulationCache
from models.monte_carlo.parallel import run_parallel_monte_carlo
from models.monte_carlo.probability.analyzer import GoalProbabilityAnalyzer
from models.monte_carlo.probability.distribution import GoalOutcomeDistribution
from models.monte_carlo.probability.result import ProbabilityResult
from models.monte_carlo.simulation import cache_response
from models.parameter_extensions import get_financial_parameter_service

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ProbabilityResult:
    """
    Structured result class for probability analysis results.

    This class organizes probability analysis results in a structured format
    that's easy to consume by front-end displays and decision-making processes.
    It provides a consistent interface for accessing probability data across
    different goal types, with strong error handling and backwards compatibility.

    The class follows a nested dictionary structure to organize metrics by category:
    - success_metrics: Core probability and success/failure metrics
    - distribution_metrics: Detailed statistical analysis of goal outcomes
    - time_based_metrics: Probability estimates at different time points
    """

    success_metrics: Dict[str, Any]
    distribution_metrics: Dict[str, Any]
    time_based_metrics: Dict[str, Any]

    @property
    def success_probability(self) -> float:
        """
        Returns the overall success probability of the goal.
        """
        return self.success_metrics["success_probability"]

    def get_safe_success_probability(self) -> float:
        """
        Returns a more conservative estimate of success probability,
        taking into account potential risks and uncertainties.
        """
        return self.success_metrics.get("safe_success_probability", self.success_probability)


class GoalOutcomeDistribution:
    """
    Models the full distribution of goal outcomes from Monte Carlo simulations.

    This class provides detailed statistical analysis of simulation results,
    including various distribution statistics (mean, median, percentiles),
    shortfall risks at different thresholds, and upside potential metrics.
    """

    def __init__(self, simulation_results: np.ndarray):
        self.simulation_results = simulation_results
        self.analyzer = GoalProbabilityAnalyzer()

    def success_probability(self, target_amount: float) -> float:
        """
        Calculates the probability of achieving the goal with at least the target amount.

        Args:
            target_amount: The minimum amount considered a successful outcome.

        Returns:
            The probability of achieving the target amount or more.
        """
        return self.analyzer.analyze_goal_probability(
            goal={"target_amount": target_amount},
            simulation_results=self.simulation_results,
        ).success_probability

    def shortfall_risk(self, target_amount: float, threshold_percentage: float = 0.8) -> float:
        """
        Calculates the risk of falling short of the target amount by a specified percentage.

        Args:
            target_amount: The target amount for the goal.
            threshold_percentage: The percentage shortfall considered a risk.

        Returns:
            The probability of falling short of the target amount by at least the threshold percentage.
        """
        shortfall_threshold = target_amount * (1 - threshold_percentage)
        return 1 - self.success_probability(shortfall_threshold)

    def upside_probability(self, target_amount: float, excess_percentage: float = 1.2) -> float:
        """
        Calculates the probability of exceeding the target amount by a specified percentage.

        Args:
            target_amount: The target amount for the goal.
            excess_percentage: The percentage excess considered an upside potential.

        Returns:
            The probability of exceeding the target amount by at least the excess percentage.
        """
        excess_threshold = target_amount * excess_percentage
        return self.success_probability(excess_threshold)

    def value_at_risk(self, confidence_level: float = 0.95) -> float:
        """
        Calculates the Value at Risk (VaR) for the goal outcome distribution.

        Args:
            confidence_level: The confidence level for the VaR calculation (e.g., 0.95 for 95% confidence).

        Returns:
            The VaR value, representing the maximum potential loss with the specified confidence level.
        """
        return np.percentile(self.simulation_results, 100 * (1 - confidence_level))

    def conditional_value_at_risk(self, confidence_level: float = 0.95) -> float:
        """
        Calculates the Conditional Value at Risk (CVaR) for the goal outcome distribution.

        Args:
            confidence_level: The confidence level for the CVaR calculation (e.g., 0.95 for 95% confidence).

        Returns:
            The CVaR value, representing the average loss in the worst-case scenarios with the specified confidence level.
        """
        loss_threshold = self.value_at_risk(confidence_level)
        losses = self.simulation_results[self.simulation_results < loss_threshold]
        return np.mean(losses)

    def calculate_time_to_goal_probability(
        self,
        target_probability: float,
        target_amount: float,
        monthly_contribution: float,
        initial_amount: float,
        allocation_strategy: Dict[str, float],
        returns: Dict[str, Tuple[float, float]],
        max_years: int = 40,
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
            max_years: Maximum number of years to consider

        Returns:
            Estimated number of years to reach the target probability with the given parameters.
        """

        def estimate_success_probability(years: int) -> float:
            """
            Helper function to estimate success probability for a given number of years.
            """
            future_value = GoalCalculator.calculate_future_value(
                initial_amount,
                monthly_contribution,
                years,
                returns,
                allocation_strategy,
            )
            return self.success_probability(future_value)

        # Use binary search to find the year with the closest probability
        low = 0
        high = max_years
        while low <= high:
            mid = (low + high) // 2
            probability = estimate_success_probability(mid)
            if abs(probability - target_probability) < 0.01:
                return mid
            elif probability < target_probability:
                low = mid + 1
            else:
                high = mid - 1

        # If exact probability not found, return the closest year
        if abs(estimate_success_probability(low) - target_probability) < abs(
            estimate_success_probability(high) - target_probability
        ):
            return low
        else:
            return high

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
            Dictionary mapping time points to corresponding success probabilities.
        """

        def estimate_success_probability(years: float) -> float:
            """
            Helper function to estimate success probability for a given number of years.
            """
            future_value = GoalCalculator.calculate_future_value(
                initial_amount,
                monthly_contribution,
                years,
                returns,
                allocation_strategy,
            )
            return self.success_probability(future_value)

        return {timepoint: estimate_success_probability(timepoint) for timepoint in timepoints}


class GoalProbabilityAnalyzer:
    """
    Analyzes goal achievement probability using Monte Carlo simulations.

    This class leverages existing financial projection capabilities to calculate
    the probability of achieving various types of financial goals, with special
    consideration for Indian market conditions.

    The enhanced version provides more detailed statistical analysis of goal outcomes,
    time-based probability assessment, and goal-specific distribution analyses.
    """

    def __init__(self):
        self.financial_parameters = get_financial_parameter_service()
        self.cache = SimulationCache()

    def analyze_goal_probability(
        self,
        goal: Dict[str, Any],
        profile: Dict[str, Any] = None,
        simulations: int = 1000,
        use_parallel: bool = False,
        cache_results: bool = True,
    ) -> ProbabilityResult:
        """
        Analyzes the probability of achieving a financial goal using Monte Carlo simulations.

        Args:
            goal: A dictionary containing goal parameters and configuration.
            profile: A dictionary containing user profile information.
            simulations: The number of Monte Carlo simulations to run.
            use_parallel: Whether to use parallel processing for simulations.
            cache_results: Whether to cache simulation results for faster retrieval.

        Returns:
            A ProbabilityResult object containing success probability, distribution metrics,
            and time-based probability estimates.
        """

        # Get goal calculator based on goal type
        goal_calculator = GoalCalculator.get_calculator_for_category(goal["category"])

        # Get financial parameters
        parameters = self.financial_parameters.get_all_parameters(profile_id=profile.get("id"))

        # Generate simulation function based on goal type
        simulation_function = goal_calculator.generate_simulation_function(
            goal, parameters, profile
        )

        # Run Monte Carlo simulations
        simulation_results = self._run_monte_carlo_simulations(
            simulation_function, simulations, use_parallel, cache_results
        )

        # Analyze simulation results
        distribution = GoalOutcomeDistribution(simulation_results)
        success_metrics = {
            "success_probability": distribution.success_probability(goal["target_amount"]),
            "safe_success_probability": distribution.success_probability(
                goal["target_amount"] * 0.95
            ),
        }
        distribution_metrics = {
            "mean": np.mean(simulation_results),
            "median": np.median(simulation_results),
            "standard_deviation": np.std(simulation_results),
            "percentiles": {
                "25th": np.percentile(simulation_results, 25),
                "50th": np.percentile(simulation_results, 50),
                "75th": np.percentile(simulation_results, 75),
            },
            "shortfall_risk": distribution.shortfall_risk(goal["target_amount"]),
            "upside_potential": distribution.upside_probability(goal["target_amount"]),
            "value_at_risk": distribution.value_at_risk(),
            "conditional_value_at_risk": distribution.conditional_value_at_risk(),
        }
        time_based_metrics = {}

        # Calculate time-based probability estimates if requested
        if goal.get("time_based_analysis"):
            time_based_metrics = distribution.calculate_probability_at_timepoints(
                goal["time_based_analysis"]["timepoints"],
                goal["target_amount"],
                goal["monthly_contribution"],
                goal["initial_amount"],
                goal["allocation_strategy"],
                parameters["asset_returns"],
            )

        return ProbabilityResult(
            success_metrics=success_metrics,
            distribution_metrics=distribution_metrics,
            time_based_metrics=time_based_metrics,
        )

    def _run_monte_carlo_simulations(
        self,
        simulation_function: Callable,
        simulations: int,
        use_parallel: bool,
        cache_results: bool,
    ) -> np.ndarray:
        """
        Runs Monte Carlo simulations and returns the results.

        Args:
            simulation_function: The function to generate a single simulation.
            simulations: The number of simulations to run.
            use_parallel: Whether to use parallel processing.
            cache_results: Whether to cache simulation results.

        Returns:
            A NumPy array containing the simulation results.
        """

        # Check if results are cached
        cache_key = f"{simulation_function.__name__}_{simulations}_{use_parallel}"
        if cache_results and self.cache.has(cache_key):
            logger.info(f"Loading simulation results from cache: {cache_key}")
            return self.cache.get(cache_key)

        # Run simulations
        if use_parallel:
            simulation_results = run_parallel_monte_carlo(
                simulation_function, simulations, max_workers=None
            )
        else:
            simulation_results = np.array(
                [simulation_function() for _ in range(simulations)]
            )

        # Cache results if enabled
        if cache_results:
            logger.info(f"Caching simulation results: {cache_key}")
            self.cache.set(cache_key, simulation_results)

        return simulation_results


@cache_response
def calculate_goal_probability(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> ProbabilityResult:
    """
    Calculates the probability of achieving a financial goal using Monte Carlo simulations.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        A ProbabilityResult object containing success probability, distribution metrics,
        and time-based probability estimates.
    """

    analyzer = GoalProbabilityAnalyzer()
    return analyzer.analyze_goal_probability(
        goal, profile, simulations, use_parallel, cache_results
    )


def calculate_time_to_goal_probability(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    target_probability: float = 0.95,
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> float:
    """
    Calculates the estimated time needed to reach a specific success probability for a goal.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        target_probability: The target probability of success (0-1).
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        The estimated number of years needed to reach the target probability.
    """

    probability_result = calculate_goal_probability(
        goal,
        profile,
        simulations,
        use_parallel,
        cache_results,
    )
    distribution = GoalOutcomeDistribution(probability_result.success_metrics["success_probability"])
    return distribution.calculate_time_to_goal_probability(
        target_probability,
        goal["target_amount"],
        goal["monthly_contribution"],
        goal["initial_amount"],
        goal["allocation_strategy"],
        FinancialParameters().get_asset_returns(),
        max_years=40,
    )


def calculate_probability_at_timepoints(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    timepoints: List[float] = [5, 10, 15, 20, 25, 30],
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> Dict[float, float]:
    """
    Calculates the probability of achieving a goal at different time points.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        timepoints: A list of time points in years to calculate probabilities for.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        A dictionary mapping time points to corresponding success probabilities.
    """

    probability_result = calculate_goal_probability(
        goal,
        profile,
        simulations,
        use_parallel,
        cache_results,
    )
    distribution = GoalOutcomeDistribution(probability_result.success_metrics["success_probability"])
    return distribution.calculate_probability_at_timepoints(
        timepoints,
        goal["target_amount"],
        goal["monthly_contribution"],
        goal["initial_amount"],
        goal["allocation_strategy"],
        FinancialParameters().get_asset_returns(),
    )


def calculate_goal_probability_with_factors(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    factors: List[Dict[str, Any]] = [],
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> ProbabilityResult:
    """
    Calculates the probability of achieving a financial goal with additional factors influencing the outcome.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        factors: A list of dictionaries representing factors that influence the goal outcome.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        A ProbabilityResult object containing success probability, distribution metrics,
        and time-based probability estimates, taking into account the specified factors.
    """

    # Create a copy of the goal dictionary to avoid modifying the original
    goal_with_factors = goal.copy()

    # Apply factors to the goal parameters
    for factor in factors:
        if factor["type"] == "percentage_change":
            goal_with_factors[factor["parameter"]] *= 1 + factor["value"] / 100
        elif factor["type"] == "absolute_change":
            goal_with_factors[factor["parameter"]] += factor["value"]
        else:
            raise ValueError(f"Invalid factor type: {factor['type']}")

    # Calculate probability with modified goal parameters
    return calculate_goal_probability(
        goal_with_factors,
        profile,
        simulations,
        use_parallel,
        cache_results,
    )


def calculate_goal_probability_with_custom_parameters(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    custom_parameters: Dict[str, Any] = {},
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> ProbabilityResult:
    """
    Calculates the probability of achieving a financial goal using custom parameter values.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        custom_parameters: A dictionary of custom parameter values to override the default parameters.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        A ProbabilityResult object containing success probability, distribution metrics,
        and time-based probability estimates, using the provided custom parameter values.
    """

    # Create a copy of the goal dictionary to avoid modifying the original
    goal_with_custom_parameters = goal.copy()

    # Override goal parameters with custom values
    for parameter, value in custom_parameters.items():
        goal_with_custom_parameters[parameter] = value

    # Calculate probability with custom parameters
    return calculate_goal_probability(
        goal_with_custom_parameters,
        profile,
        simulations,
        use_parallel,
        cache_results,
    )


def calculate_goal_probability_with_override_parameters(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    override_parameters: Dict[str, Any] = {},
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> ProbabilityResult:
    """
    Calculates the probability of achieving a financial goal using parameter overrides.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        override_parameters: A dictionary of parameter overrides to apply to the user's profile.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        A ProbabilityResult object containing success probability, distribution metrics,
        and time-based probability estimates, using the provided parameter overrides.
    """

    # Create a copy of the profile to avoid modifying the original
    profile_with_overrides = profile.copy()

    # Apply parameter overrides to the profile
    for parameter, value in override_parameters.items():
        profile_with_overrides["parameters"][parameter] = value

    # Calculate probability with overridden parameters
    return calculate_goal_probability(
        goal,
        profile_with_overrides,
        simulations,
        use_parallel,
        cache_results,
    )


def calculate_goal_probability_with_custom_returns(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    custom_returns: Dict[str, Tuple[float, float]] = {},
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> ProbabilityResult:
    """
    Calculates the probability of achieving a financial goal using custom asset return values.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        custom_returns: A dictionary of custom asset return values to override the default values.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        A ProbabilityResult object containing success probability, distribution metrics,
        and time-based probability estimates, using the provided custom asset return values.
    """

    # Create a copy of the profile to avoid modifying the original
    profile_with_custom_returns = profile.copy()

    # Override asset return values in the profile
    for asset_class, (mean, std) in custom_returns.items():
        profile_with_custom_returns["parameters"]["asset_returns"][asset_class] = (mean, std)

    # Calculate probability with custom asset returns
    return calculate_goal_probability(
        goal,
        profile_with_custom_returns,
        simulations,
        use_parallel,
        cache_results,
    )


def calculate_goal_probability_with_custom_volatility(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    custom_volatility: Dict[str, float] = {},
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> ProbabilityResult:
    """
    Calculates the probability of achieving a financial goal using custom asset volatility values.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        custom_volatility: A dictionary of custom asset volatility values to override the default values.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        A ProbabilityResult object containing success probability, distribution metrics,
        and time-based probability estimates, using the provided custom asset volatility values.
    """

    # Create a copy of the profile to avoid modifying the original
    profile_with_custom_volatility = profile.copy()

    # Override asset volatility values in the profile
    for asset_class, std in custom_volatility.items():
        mean, _ = profile_with_custom_volatility["parameters"]["asset_returns"][asset_class]
        profile_with_custom_volatility["parameters"]["asset_returns"][asset_class] = (mean, std)

    # Calculate probability with custom asset volatility
    return calculate_goal_probability(
        goal,
        profile_with_custom_volatility,
        simulations,
        use_parallel,
        cache_results,
    )


def calculate_goal_probability_with_custom_correlation(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    custom_correlation: Dict[str, Dict[str, float]] = {},
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> ProbabilityResult:
    """
    Calculates the probability of achieving a financial goal using custom asset correlation values.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        custom_correlation: A dictionary of custom asset correlation values to override the default values.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        A ProbabilityResult object containing success probability, distribution metrics,
        and time-based probability estimates, using the provided custom asset correlation values.
    """

    # Create a copy of the profile to avoid modifying the original
    profile_with_custom_correlation = profile.copy()

    # Override asset correlation values in the profile
    for asset_class1, correlations in custom_correlation.items():
        for asset_class2, correlation in correlations.items():
            profile_with_custom_correlation["parameters"]["asset_correlation"][
                asset_class1
            ][asset_class2] = correlation

    # Calculate probability with custom asset correlation
    return calculate_goal_probability(
        goal,
        profile_with_custom_correlation,
        simulations,
        use_parallel,
        cache_results,
    )


def calculate_goal_probability_with_custom_inflation(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    custom_inflation: float = None,
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> ProbabilityResult:
    """
    Calculates the probability of achieving a financial goal using a custom inflation rate.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        custom_inflation: A custom inflation rate to override the default value.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        A ProbabilityResult object containing success probability, distribution metrics,
        and time-based probability estimates, using the provided custom inflation rate.
    """

    # Create a copy of the profile to avoid modifying the original
    profile_with_custom_inflation = profile.copy()

    # Override inflation rate in the profile
    if custom_inflation is not None:
        profile_with_custom_inflation["parameters"]["inflation"] = custom_inflation

    # Calculate probability with custom inflation rate
    return calculate_goal_probability(
        goal,
        profile_with_custom_inflation,
        simulations,
        use_parallel,
        cache_results,
    )


def calculate_goal_probability_with_custom_tax_rate(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    custom_tax_rate: float = None,
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> ProbabilityResult:
    """
    Calculates the probability of achieving a financial goal using a custom tax rate.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        custom_tax_rate: A custom tax rate to override the default value.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        A ProbabilityResult object containing success probability, distribution metrics,
        and time-based probability estimates, using the provided custom tax rate.
    """

    # Create a copy of the profile to avoid modifying the original
    profile_with_custom_tax_rate = profile.copy()

    # Override tax rate in the profile
    if custom_tax_rate is not None:
        profile_with_custom_tax_rate["parameters"]["tax_rate"] = custom_tax_rate

    # Calculate probability with custom tax rate
    return calculate_goal_probability(
        goal,
        profile_with_custom_tax_rate,
        simulations,
        use_parallel,
        cache_results,
    )


def calculate_goal_probability_with_custom_expenses(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    custom_expenses: Dict[str, float] = {},
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> ProbabilityResult:
    """
    Calculates the probability of achieving a financial goal using custom expense values.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        custom_expenses: A dictionary of custom expense values to override the default values.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel: Whether to use parallel processing for simulations.
        cache_results: Whether to cache simulation results for faster retrieval.

    Returns:
        A ProbabilityResult object containing success probability, distribution metrics,
        and time-based probability estimates, using the provided custom expense values.
    """

    # Create a copy of the profile to avoid modifying the original
    profile_with_custom_expenses = profile.copy()

    # Override expense values in the profile
    for expense_category, amount in custom_expenses.items():
        profile_with_custom_expenses["expenses"][expense_category] = amount

    # Calculate probability with custom expense values
    return calculate_goal_probability(
        goal,
        profile_with_custom_expenses,
        simulations,
        use_parallel,
        cache_results,
    )


def calculate_goal_probability_with_custom_income(
    goal: Dict[str, Any],
    profile: Dict[str, Any] = None,
    custom_income: Dict[str, float] = {},
    simulations: int = 1000,
    use_parallel: bool = False,
    cache_results: bool = True,
) -> ProbabilityResult:
    """
    Calculates the probability of achieving a financial goal using custom income values.

    Args:
        goal: A dictionary containing goal parameters and configuration.
        profile: A dictionary containing user profile information.
        custom_income: A dictionary of custom income values to override the default values.
        simulations: The number of Monte Carlo simulations to run.
        use_parallel
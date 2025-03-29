"""
Monte Carlo simulation components for financial projections.

This package contains modules for running efficient Monte Carlo simulations:
- core: Core simulation algorithms for different financial goals
- parallel: Parallel processing functionality for faster simulations
- cache: Caching system to avoid redundant calculations
- array_fix: Utilities for handling array truth value issues
- probability: Goal probability analysis components
"""

from models.monte_carlo.core import (
    MonteCarloSimulation,
    run_simulation,
    get_simulation_config
)

from models.monte_carlo.parallel import (
    run_parallel_monte_carlo,
    run_simulation_batch
)

from models.monte_carlo.cache import (
    cached_simulation,
    invalidate_cache,
    get_cache_stats
)

from models.monte_carlo.array_fix import (
    to_scalar,
    safe_array_compare,
    safe_median,
    safe_array_to_bool
)

from models.monte_carlo.probability import (
    ProbabilityResult,
    GoalOutcomeDistribution,
    GoalProbabilityAnalyzer
)
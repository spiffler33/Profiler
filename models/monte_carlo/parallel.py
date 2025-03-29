"""
Parallel processing functionality for Monte Carlo simulations.

This module provides parallel processing to accelerate Monte Carlo simulations
by distributing the workload across multiple CPU cores.
"""

import numpy as np
import multiprocessing
import logging
import time
from functools import partial
from typing import Dict, List, Tuple, Optional, Any, Callable

logger = logging.getLogger(__name__)

def run_parallel_monte_carlo(
    initial_amount: float,
    contribution_pattern: Any,  # ContributionPattern from financial_projection
    years: int,
    allocation_strategy: Any,  # AllocationStrategy from financial_projection
    simulation_function: Callable,  # Function that runs a single simulation
    simulations: int = 1000,
    confidence_levels: List[float] = [0.10, 0.25, 0.50, 0.75, 0.90],
    seed: int = 42,
    max_workers: Optional[int] = None,
    chunk_size: Optional[int] = None
) -> Any:  # ProjectionResult from financial_projection
    """
    Run Monte Carlo simulations in parallel using multiple processes.
    
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
    simulation_function : Callable
        Function that runs a single simulation with signature:
        f(seed_offset, initial_amount, contribution_pattern, years, allocation_strategy) -> np.ndarray
    simulations : int, default 1000
        Number of Monte Carlo simulations to run (minimum 500 recommended for stability)
    confidence_levels : List[float], default [0.10, 0.25, 0.50, 0.75, 0.90]
        Percentiles to calculate for confidence intervals
    seed : int, default 42
        Base random seed (will be offset for each worker)
    max_workers : int, optional
        Maximum number of worker processes (defaults to CPU count)
    chunk_size : int, optional
        Number of simulations per worker chunk (defaults to simulations // worker_count)
        
    Returns:
    --------
    ProjectionResult
        Object containing projection results with confidence intervals
    """
    start_time = time.time()
    
    # Validate simulation count - minimum 500 for stability
    if simulations < 500:
        logger.warning(f"Simulation count {simulations} is too low for stable results, increasing to 500")
        simulations = 500
    
    # Determine optimal number of worker processes (default to CPU count)
    cpu_count = multiprocessing.cpu_count()
    if max_workers is None:
        max_workers = cpu_count
    else:
        max_workers = min(max_workers, cpu_count)
    
    # Make sure we don't create more workers than simulations
    worker_count = min(max_workers, simulations)
    
    # Calculate simulations per worker
    if chunk_size is None:
        chunk_size = max(1, simulations // worker_count)
    
    # Calculate the actual number of simulations that will be run
    actual_simulations = chunk_size * worker_count
    if actual_simulations != simulations:
        logger.warning(f"Adjusted simulation count from {simulations} to {actual_simulations} for even distribution")
        simulations = actual_simulations
    
    logger.info(f"Running {simulations} Monte Carlo simulations with {worker_count} workers ({chunk_size} sims per worker)")
    
    try:
        # Create simulation batches with different seed offsets
        sim_batches = [(i, chunk_size, seed + i) for i in range(worker_count)]
        
        # Create worker function with fixed parameters
        worker_func = partial(
            run_simulation_batch,
            simulation_function=simulation_function,
            initial_amount=initial_amount,
            contribution_pattern=contribution_pattern,
            years=years,
            allocation_strategy=allocation_strategy
        )
        
        # Run simulations in parallel using process pool
        with multiprocessing.Pool(worker_count) as pool:
            batch_results = pool.map(worker_func, sim_batches)
        
        # Combine results from all batches
        all_projections = np.vstack([result for result in batch_results if result is not None])
        
        # If no valid results were returned, raise an exception
        if len(all_projections) == 0:
            raise ValueError("No valid simulation results were returned from workers")
            
        # Calculate median projection
        median_projection = np.median(all_projections, axis=0)
        
        # Pre-calculate and cache contributions for each year for efficiency
        yearly_contributions = [0]  # No contribution at start
        for year in range(1, years + 1):
            yearly_contributions.append(contribution_pattern.get_contribution_for_year(year))
        
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
        
        # Calculate volatility
        volatility = np.std(all_projections[:, -1]) / np.mean(all_projections[:, -1]) if np.mean(all_projections[:, -1]) > 0 else 0
        
        # Create result object (assumes ProjectionResult class has been imported)
        from models.financial_projection import ProjectionResult
        
        result = ProjectionResult(
            years=list(range(years + 1)),
            projected_values=median_projection,
            contributions=yearly_contributions,
            growth=growth_values,
            confidence_intervals=confidence_intervals,
            volatility=volatility
        )
        
        # Store additional data for caching if needed
        result.all_projections = all_projections
        result.yearly_contributions = yearly_contributions
        
        duration = time.time() - start_time
        logger.info(f"Parallel Monte Carlo simulation completed in {duration:.3f}s ({simulations} runs, {years} years)")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in parallel Monte Carlo simulation: {str(e)}", exc_info=True)
        raise RuntimeError(f"Parallel simulation failed: {str(e)}")

def run_simulation_batch(
    batch_info: Tuple[int, int, int],
    simulation_function: Callable,
    initial_amount: float,
    contribution_pattern: Any,
    years: int,
    allocation_strategy: Any
) -> np.ndarray:
    """
    Run a batch of simulations in a worker process.
    
    Parameters:
    -----------
    batch_info : Tuple[int, int, int]
        Tuple containing (batch_id, batch_size, seed)
    simulation_function : Callable
        Function to run a single simulation
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
    np.ndarray
        Array of simulation results (shape: batch_size x (years+1))
    """
    batch_id, batch_size, seed = batch_info
    
    try:
        # Set seed for this batch
        np.random.seed(seed)
        
        # Initialize array for storing this batch's results
        batch_results = np.zeros((batch_size, years + 1))
        
        # Run simulations in this batch
        for i in range(batch_size):
            # Use the provided simulation function to run a single simulation
            result = simulation_function(
                seed_offset=i,
                initial_amount=initial_amount,
                contribution_pattern=contribution_pattern,
                years=years,
                allocation_strategy=allocation_strategy
            )
            
            # Store the result
            batch_results[i] = result
            
        return batch_results
        
    except Exception as e:
        logger.error(f"Error in worker process (batch {batch_id}): {str(e)}", exc_info=True)
        return None
        
def single_simulation_example(
    seed_offset: int,
    initial_amount: float,
    contribution_pattern: Any,
    years: int,
    allocation_strategy: Any
) -> np.ndarray:
    """
    Example function showing the expected signature for a single simulation function.
    
    Parameters:
    -----------
    seed_offset : int
        Offset for the random seed for this simulation
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
    np.ndarray
        Array of values for each year (shape: years+1)
    """
    # This is just an example - replace with actual simulation logic
    np.random.seed(42 + seed_offset)
    
    # Initialize array for this simulation's results
    result = np.zeros(years + 1)
    result[0] = initial_amount
    
    current_value = initial_amount
    for year in range(1, years + 1):
        # Get contribution for this year
        contribution = contribution_pattern.get_contribution_for_year(year)
        
        # Simple random return simulation (replace with your actual simulation)
        simulated_return = np.random.normal(0.07, 0.15)  # Mean 7%, volatility 15%
        
        # Update current value
        current_value = current_value * (1 + simulated_return) + contribution
        result[year] = current_value
        
    return result
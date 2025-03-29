# Monte Carlo Simulation Framework

This module provides a comprehensive Monte Carlo simulation framework for financial goal projections, with a focus on performance, reliability, and scalability.

## Architecture Overview

The Monte Carlo simulation framework consists of several key components:

```
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│                     │      │                     │      │                     │
│  Goal Parameters    │─────▶│  Monte Carlo Core   │◀────▶│      Cache          │
│                     │      │                     │      │                     │
└─────────────────────┘      └──────────┬──────────┘      └─────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │                     │
                              │  Parallel Executor  │
                              │                     │
                              └──────────┬──────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │                           │
                            │  Probability Analysis     │
                            │                           │
                            └───────────────────────────┘
```

### Key Components

1. **Core Engine (`core.py`)**: Handles simulation logic for different goal types
2. **Caching System (`cache.py`)**: Optimizes performance by avoiding redundant calculations
3. **Parallel Execution (`parallel.py`)**: Distributes work across multiple CPU cores
4. **Array Utilities (`array_fix.py`)**: Handles NumPy array operations safely
5. **Probability Analysis (`probability/`)**:
   - Analyzer: Calculates success probability metrics
   - Distribution: Analyzes distribution of simulation outcomes
   - Result: Structures for storing probability results

## Component Interfaces

### Monte Carlo Core

```python
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
```

### Caching System

```python
@cached_simulation
def your_simulation_function(...):
    """
    Decorator for caching simulation results.
    
    Automatic caching of simulation results with proper key generation,
    TTL support, and cache invalidation mechanisms.
    """
    
def invalidate_cache(pattern: str = None) -> int:
    """
    Invalidate cache entries.
    
    Args:
        pattern: If provided, only invalidate keys containing this pattern
        
    Returns:
        Number of invalidated entries
    """
    
def get_cache_stats() -> Dict[str, Any]:
    """
    Get current cache statistics.
    
    Returns:
        Dictionary with stats like hits, misses, size, etc.
    """
```

### Parallel Execution

```python
def run_parallel_monte_carlo(
    initial_amount: float,
    contribution_pattern: Any,
    years: int,
    allocation_strategy: Any,
    simulation_function: Callable,
    simulations: int = 1000,
    confidence_levels: List[float] = [0.10, 0.25, 0.50, 0.75, 0.90],
    seed: int = 42,
    max_workers: Optional[int] = None,
    chunk_size: Optional[int] = None
) -> Any:
    """
    Run Monte Carlo simulations in parallel using multiple processes.
    
    Parameters:
        initial_amount: Starting value of the assets
        contribution_pattern: Pattern defining contribution schedule
        years: Number of years to project
        allocation_strategy: Asset allocation strategy to use
        simulation_function: Function that runs a single simulation
        simulations: Number of Monte Carlo simulations to run
        confidence_levels: Percentiles to calculate
        seed: Base random seed (will be offset for each worker)
        max_workers: Maximum number of worker processes
        chunk_size: Number of simulations per worker chunk
    """
```

## Expected Behavior

### Simulation Process

1. The `run_simulation` function accepts a goal and configuration parameters
2. It creates a `MonteCarloSimulation` instance with the provided parameters
3. The appropriate simulation method is chosen based on the goal type
4. The simulation is executed, potentially in parallel and with caching
5. Results are processed and returned with appropriate metrics

### Caching Behavior

- Cache keys are generated based on all input parameters
- First call with a unique parameter set -> Cache miss
- Subsequent calls with identical parameters -> Cache hit
- Cache entries have a time-to-live (TTL) and will expire
- Cache size is limited and uses a LRU (Least Recently Used) eviction policy
- Cache invalidation is supported for specific patterns

### Parallel Processing Behavior

- Simulations are divided into batches and distributed across worker processes
- Each worker gets a unique random seed offset to ensure independent simulations
- Results from all workers are combined for analysis
- The system adjusts to available CPU resources
- Failed simulations are handled gracefully

### Error Handling Approach

- NumPy array operations use safe comparison functions
- Function errors are caught and logged with appropriate context
- Random state is carefully managed to avoid reproducibility issues
- Cache key generation handles non-serializable objects
- Memory usage is monitored and controlled

## Performance Characteristics

| Operation | Expected Performance | Scaling Factor |
|-----------|----------------------|----------------|
| Single simulation (30 years) | ~10-20ms | Linear with years |
| Cached simulation retrieval | <1ms | Constant |
| 1000 simulations, parallel (4 cores) | ~0.5-1s | Linear with simulations/cores |
| Cache invalidation | <5ms | Constant |
| Memory usage (1000 simulations) | ~50-100MB | Linear with simulations*years |

## Testing and Validation

The Monte Carlo framework is thoroughly tested using:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Performance Tests**: Verify efficiency and scaling
4. **Edge Case Tests**: Test with extreme inputs (long timeframes, large portfolios)
5. **Regression Tests**: Compare against baseline performance metrics

See the `tests/models/` directory for comprehensive test suites.

## CI Integration

The Monte Carlo simulation system is integrated with our CI pipeline:

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: monte-carlo-tests
      name: Monte Carlo Tests
      entry: python -m unittest tests/models/test_monte_carlo_*.py
      language: system
      pass_filenames: false
      files: ^models/monte_carlo/.*\.py$
      
    - id: monte-carlo-performance
      name: Monte Carlo Performance
      entry: python -m unittest tests/models/test_monte_carlo_regression.py
      language: system
      pass_filenames: false
      files: ^models/monte_carlo/.*\.py$
```

### CI Checks for Performance

The system uses the regression detection framework to automatically identify performance issues:

```yaml
# .github/workflows/monte_carlo_performance.yml
name: Monte Carlo Performance

on:
  push:
    paths:
      - 'models/monte_carlo/**'
      - 'tests/models/test_monte_carlo_*.py'
  pull_request:
    paths:
      - 'models/monte_carlo/**'
      - 'tests/models/test_monte_carlo_*.py'

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run performance tests
        run: |
          python -m unittest tests/models/test_monte_carlo_regression.py
      - name: Check for regressions
        run: |
          if grep -q "PERFORMANCE REGRESSION" test_output.log; then
            echo "Performance regression detected!"
            exit 1
          fi
```

### Dependency Analysis

Automated dependency analysis is performed during CI to ensure API compatibility:

```python
# tools/dependency_analyzer.py

import ast
import sys
from typing import Dict, List, Set

class APIUsageAnalyzer(ast.NodeVisitor):
    """Analyze Python files for Monte Carlo API usage."""
    
    def __init__(self):
        self.api_calls = set()
        
    def visit_Call(self, node):
        # Track function calls
        if hasattr(node.func, 'id') and node.func.id in ['run_simulation', 'cached_simulation']:
            self.api_calls.add(node.func.id)
        # Track method calls on imported modules
        elif hasattr(node.func, 'attr') and node.func.attr in ['run_simulation', 'invalidate_cache']:
            self.api_calls.add(node.func.attr)
        self.generic_visit(node)

# Usage in CI
def analyze_dependencies(files):
    api_usage = {}
    for file in files:
        analyzer = APIUsageAnalyzer()
        with open(file) as f:
            tree = ast.parse(f.read())
            analyzer.visit(tree)
            api_usage[file] = analyzer.api_calls
    return api_usage
```

## Usage Examples

### Basic Simulation

```python
from models.monte_carlo.core import run_simulation

# Create a financial goal
goal = Goal(
    id="retirement",
    target_amount=1500000,
    current_amount=250000,
    monthly_contribution=2000,
    target_date="2050-01-01"
)

# Run simulation
result = run_simulation(
    goal=goal,
    return_assumptions={"equity": 0.07, "debt": 0.04, "gold": 0.03, "cash": 0.02},
    inflation_rate=0.02,
    simulation_count=1000
)

# Access results
print(f"Success probability: {result['success_probability']:.2%}")
print(f"Median outcome: ${result['percentiles']['50']:,.2f}")
```

### Cached Simulation

```python
from models.monte_carlo.cache import cached_simulation, invalidate_cache

@cached_simulation
def my_simulation_func(params):
    # Run expensive simulation here
    return results

# First run - will compute and cache
result1 = my_simulation_func(params)

# Second run - will use cache
result2 = my_simulation_func(params)

# Clear cache when needed
invalidate_cache()
```

### Parallel Simulation

```python
from models.monte_carlo.parallel import run_parallel_monte_carlo

def single_simulation(seed_offset, initial_amount, contribution_pattern, years, allocation_strategy):
    # Implement single simulation logic
    return result_array

# Run many simulations in parallel
result = run_parallel_monte_carlo(
    initial_amount=1000000,
    contribution_pattern=contribution_pattern,
    years=30,
    allocation_strategy=allocation_strategy,
    simulation_function=single_simulation,
    simulations=5000,
    max_workers=8
)
```
# Monte Carlo Implementation Guide

This guide documents the implementation details, architecture, and test approach for the Monte Carlo simulation framework.

## Component Architecture

The Monte Carlo simulation system is built with a modular architecture to ensure maintainability, testability, and performance:

### Core Components

1. **Monte Carlo Core (`core.py`)** 
   - Central engine that orchestrates simulations
   - Handles different goal types with specialized simulation logic
   - Provides clean public API through `run_simulation` function

2. **Caching System (`cache.py`)**
   - LRU-based cache for simulation results
   - Handles cache invalidation and statistics
   - Provides decorator-based caching interface

3. **Parallel Processing (`parallel.py`)**
   - Distributes simulations across multiple CPU cores
   - Manages worker processes and result aggregation
   - Optimizes workload distribution based on available resources

4. **Array Utilities (`array_fix.py`)**
   - Handles NumPy array truth value errors
   - Provides safe comparison and conversion functions
   - Decorator for automatic error handling

5. **Probability Analysis (`probability/`)**
   - Calculates probability metrics from simulation results
   - Analyzes distribution characteristics
   - Formats results for presentation

### Component Interactions

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│    API Layer    │◀────▶│   Cache Layer   │◀────▶│  Storage Layer  │
│                 │      │                 │      │                 │
└────────┬────────┘      └────────┬────────┘      └─────────────────┘
         │                        │
         │                        │
         ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Computation    │◀────▶│    Parallel     │◀────▶│  Result         │
│  Engine         │      │    Processing   │      │  Analysis       │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

## Testing Approach

Our testing approach for the Monte Carlo system is comprehensive, focusing on both functional correctness and performance characteristics:

### Test Categories

1. **Unit Tests**
   - Test each component in isolation
   - Mock dependencies to focus on specific functionality
   - Check edge cases and error handling

2. **Integration Tests**
   - Test interactions between components
   - Verify end-to-end simulation workflows
   - Ensure proper data flow between components

3. **Performance Tests**
   - Benchmark key operations
   - Track performance metrics over time
   - Detect performance regressions automatically

4. **Edge Case Tests**
   - Test with extreme inputs (very large values, long timeframes)
   - Test memory-intensive scenarios
   - Test complex allocation patterns

### Test Framework

The test framework provides:

1. **Benchmark Tracking**
   - Records performance metrics over time
   - Stores historical data for trend analysis
   - Detects performance regressions automatically

2. **Cache Testing**
   - Verifies cache hit/miss behavior
   - Tests cache key generation consistency
   - Checks thread safety and concurrent access

3. **Memory Tracking**
   - Monitors memory usage during operations
   - Checks for memory leaks
   - Tests behavior under memory pressure

## Implementation Patterns

### 1. Decorator-based Caching

```python
@cached_simulation
def simulate_retirement_goal(initial_amount, contribution_pattern, years, allocation_strategy):
    # Simulation logic here
    return result
```

This pattern makes it easy to add caching to any simulation function without modifying its implementation.

### 2. Strategy-based Goal Simulation

The core engine uses different simulation strategies based on goal type:

```python
def _simulate_goal(self, goal_type, params):
    if goal_type == 'retirement':
        return self._simulate_retirement_goal(params)
    elif goal_type == 'education':
        return self._simulate_education_goal(params)
    # ...etc.
```

This allows for specialized simulation logic for each goal type while maintaining a consistent API.

### 3. Safe Array Operations

Array truth value errors are handled with safe comparison functions:

```python
# Instead of: if array > value
if safe_array_compare(array, value, 'gt'):
    # Do something
```

### 4. Parallel Processing with Chunking

Simulations are distributed across workers in chunks:

```python
for worker_id in range(worker_count):
    chunk_size = simulations // worker_count
    pool.apply_async(run_simulation_batch, (worker_id, chunk_size, seed + worker_id))
```

This ensures even distribution of work and reproducible results.

## Optimization Techniques

### 1. Cache Key Generation

Cache keys are generated based on all input parameters:

```python
def _generate_key(self, args, kwargs):
    key_dict = {'args': args, 'kwargs': kwargs}
    try:
        # Try JSON serialization first (faster)
        key_str = json.dumps(key_dict, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    except (TypeError, ValueError):
        # Fall back to string representation if not serializable
        return hashlib.md5(str(key_dict).encode()).hexdigest()
```

### 2. Simulation Result Reuse

Common simulation patterns are cached to avoid redundant calculations:

```python
# First call - computes result
result1 = simulate_retirement_goal(initial_amount=1000000, ...)

# Second call with same parameters - returns cached result
result2 = simulate_retirement_goal(initial_amount=1000000, ...)
```

### 3. Vector Operations

NumPy vector operations are used for performance:

```python
# Instead of looping through each value
# for i in range(len(array)):
#     array[i] = array[i] * (1 + returns[i])

# Use vector operations
array *= (1 + returns)
```

### 4. Parallel Processing Optimizations

- Dynamic worker count based on CPU cores
- Optimal chunk size calculations
- Seed offsetting for reproducibility
- Error handling and recovery

## CI Integration

The Monte Carlo system is integrated with the CI pipeline to ensure ongoing quality:

### Pre-commit Hooks

Pre-commit hooks run tests and check for regressions:

```yaml
- id: monte-carlo-tests
  name: Monte Carlo Tests
  entry: python -m unittest tests/models/test_monte_carlo_*.py
  language: system
  files: ^models/monte_carlo/.*\.py$
```

### GitHub Actions

GitHub Actions workflow runs performance tests and trend analysis:

```yaml
name: Monte Carlo Performance
on:
  push:
    paths:
      - 'models/monte_carlo/**'
jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Performance Tests
        run: python -m unittest tests/models/test_monte_carlo_regression.py
```

### Dependency Analysis

Automatic API dependency analysis prevents breaking changes:

```python
# tools/check_monte_carlo_dependencies.py
def analyze_codebase():
    current_signatures = extract_current_api_signatures()
    previous_signatures = load_previous_api_signatures()
    changes = compare_signatures(previous_signatures, current_signatures)
    # Check for breaking changes
```

## Best Practices

1. **Maintain API Stability**
   - Use the dependency analyzer to catch breaking changes
   - Follow deprecation patterns when evolving APIs
   - Document any changes to public interfaces

2. **Performance Testing**
   - Always run performance tests before/after significant changes
   - Monitor trends to catch gradual performance degradation
   - Set appropriate thresholds for regression detection

3. **Caching Considerations**
   - Be careful with cache key generation for complex objects
   - Use appropriate TTLs based on data volatility
   - Monitor cache hit rates to ensure effectiveness

4. **Parallel Processing**
   - Ensure thread safety for shared resources
   - Use appropriate chunking strategies
   - Handle errors gracefully in worker processes

5. **Memory Management**
   - Track memory usage for large simulations
   - Use memory profiling for optimization
   - Implement cleanup for temporary large arrays

## Troubleshooting Guide

### Common Issues

1. **Cache Not Working Effectively**
   - Check cache key generation for non-deterministic components
   - Verify that objects in cache keys are hashable/serializable
   - Monitor cache hit/miss rates using `get_cache_stats()`

2. **Performance Degradation**
   - Run the regression tests to identify specific bottlenecks
   - Check memory usage and garbage collection patterns
   - Look for inefficient array operations or loops

3. **Parallel Processing Failures**
   - Check for proper error handling in worker processes
   - Ensure worker function is picklable (avoid class methods)
   - Verify that shared resources are thread-safe

4. **Array Truth Value Errors**
   - Use the `safe_array_compare` function for array comparisons
   - Apply the `with_numpy_error_handled` decorator to functions with complex array logic
   - Convert arrays to scalars with `to_scalar` when needed

### Debugging Tools

1. **Cache Analysis**
   - `get_cache_stats()` for hit/miss rates
   - `invalidate_cache()` to reset cache state
   - Add `key_prefix` to `@cached_simulation` for debugging

2. **Performance Profiling**
   - Use the `@benchmark` decorator to track function performance
   - Compare against baseline with `BenchmarkTracker`
   - Check memory usage with `@track_memory_usage`

3. **Test Helpers**
   - Use `create_cache_assertions` for cache-related tests
   - Check simulation consistency with `verify_simulation_consistency`
   - Set maximum execution time with `assert_execution_time`
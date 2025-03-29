# Monte Carlo Simulation Performance Benchmark Suite

This document outlines the benchmark tests used to validate and monitor the performance of the Monte Carlo simulation system, particularly focused on caching and optimization features.

## Benchmark Categories

The performance benchmark suite is divided into several categories:

### 1. Cache Performance

These tests measure the effectiveness of the caching system, including:

- Basic cache hit/miss performance
- Cache key generation consistency
- Performance under load (many parameters)
- Memory usage with large result sets
- Eviction policy effectiveness
- Time-to-live (TTL) functionality

### 2. Parallel Processing

Tests focused on parallel execution performance:

- Speedup achieved with multiple workers
- Scaling with number of simulations
- Thread safety and race condition detection
- Memory usage during parallel processing
- Cache interaction in parallel environments

### 3. Edge Case Performance

Tests designed to stress the system in extreme scenarios:

- Very large portfolios (high asset values)
- Long time horizons (50+ years)
- Complex allocation strategies (many asset classes)
- High volatility scenarios
- Memory-intensive simulations

### 4. Regression Detection

Tests specifically designed to catch performance regressions:

- Time series tracking for long-term trends
- Assertions based on previous performance metrics
- Comparison against baseline performance

## Running the Benchmark Suite

The benchmark suite can be run using the standard test framework:

```bash
python -m unittest tests/models/test_monte_carlo_cache_performance.py
```

For automated regression detection, run:

```bash
python -m unittest tests/models/test_monte_carlo_regression.py
```

## Benchmark Metrics

The primary metrics tracked by the benchmark suite include:

- Execution time: Raw and relative performance
- Cache hit rate: Percentage of simulation requests served from cache
- Memory usage: Peak memory consumption during simulation
- Parallelization efficiency: Speedup vs. number of workers
- Consistency: Variation in results between runs

## Baseline Performance

| Test Scenario | Single-Thread Time | Multi-Thread Time | Cache Hit Rate | Memory Usage |
|---------------|-------------------|-------------------|---------------|--------------|
| Standard retirement (30yr) | 1500ms | 380ms | 99.5% | 45MB |
| Long-term planning (50yr) | 2600ms | 520ms | 99.2% | 68MB |
| Education planning (10yr) | 550ms | 140ms | 99.8% | 32MB |
| Multi-goal portfolio | 4800ms | 750ms | 98.7% | 120MB |

## Integrating into CI Pipeline

To ensure ongoing performance monitoring, the benchmark suite is integrated into the CI pipeline with the following steps:

1. Run benchmark tests on each PR affecting Monte Carlo components
2. Compare results against baseline performance
3. Flag significant regressions (>10% slowdown)
4. Archive performance metrics for long-term trend analysis

## Reporting

The benchmark suite generates detailed reports in the following formats:

- Console output with key metrics
- JSON performance data for automated analysis
- Time series data for visualization 
- Detailed logs for debugging performance issues

## Future Enhancements

Planned enhancements to the benchmark suite include:

- Advanced visualization of performance trends
- Automated anomaly detection in performance metrics
- Expanded edge case testing
- Per-component performance profiling
- Resource utilization analysis
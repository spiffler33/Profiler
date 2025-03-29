# Monte Carlo System Documentation

## System Overview

The Monte Carlo system in Profiler4 is a comprehensive simulation framework that powers probability analysis, financial projections, and goal adjustment recommendations. This document provides a consolidated reference for all aspects of the system.

### Purpose

The Monte Carlo simulation system helps users understand their likelihood of achieving financial goals by simulating thousands of possible future scenarios based on random variations in market returns and other factors. It enables:

1. **Probability Analysis**: Calculating the likelihood of achieving specific financial goals
2. **Financial Projections**: Visualizing potential future scenarios across different confidence levels
3. **Recommendation Generation**: Providing actionable adjustments to improve goal success probability

### System Components

The system consists of four primary components:

1. **Core Simulation** (`models/monte_carlo/core.py`): Implements the core Monte Carlo simulation algorithm
2. **Parallel Processing** (`models/monte_carlo/parallel.py`): Provides parallel execution of simulations
3. **Caching** (`models/monte_carlo/cache.py`): Caches simulation results for performance
4. **Integration** (`models/monte_carlo/simulation.py` and `models/monte_carlo/api_integration.py`): Connects simulations to APIs

## Usage Examples

### Basic Usage

```python
from models.monte_carlo.core import run_monte_carlo_simulation

result = run_monte_carlo_simulation(
    initial_amount=10000,
    contribution_amount=500,
    years=10,
    return_rate=0.07,
    volatility=0.15,
    simulations=1000
)
```

### With Parallel Processing

```python
from models.monte_carlo.parallel import run_parallel_monte_carlo
from models.monte_carlo.core import simulate_single_run

result = run_parallel_monte_carlo(
    initial_amount=10000,
    contribution_pattern=contribution_pattern,
    years=10,
    allocation_strategy=allocation_strategy,
    simulation_function=simulate_single_run,
    simulations=1000
)
```

### With Caching

```python
from models.monte_carlo.cache import cached_simulation

@cached_simulation
def my_simulation_function(params):
    # Simulation logic here
    return result
```

### API Integration

```python
from models.monte_carlo.api_integration import create_simulation_endpoint

@app.route('/api/goals/<goal_id>/probability', methods=['GET'])
def goal_probability(goal_id):
    # Implementation using consolidated modules
    from models.monte_carlo.simulation import safely_get_simulation_data, cache_response
    
    # Get goal data
    goal = goal_service.get_goal(goal_id)
    
    # Use simulation functions
    simulation_data = safely_get_simulation_data(goal)
    
    # Prepare response
    response = {...}
    
    # Cache the response
    cache_response(f"goal_probability_{goal_id}", response)
    
    return jsonify(response), 200
```

## Key Functionality

### Probability Calculation

The system calculates the probability of reaching a financial goal by:

1. Running multiple simulations with random market returns
2. Counting how many simulations reach or exceed the target amount
3. Dividing the success count by the total number of simulations

```python
def calculate_success_probability(simulations, target_amount):
    success_count = sum(1 for sim in simulations if sim[-1] >= target_amount)
    return success_count / len(simulations)
```

### Confidence Intervals

The system provides multiple confidence levels to help understand the range of possible outcomes:

- P10 (Pessimistic): Only 10% of simulations perform worse than this
- P25 (Lower Quartile): 25% of simulations perform worse than this
- P50 (Median): The middle outcome
- P75 (Upper Quartile): 75% of simulations perform worse than this
- P90 (Optimistic): 90% of simulations perform worse than this

### Parallel Processing

To improve performance, the system can distribute simulation workloads across multiple CPU cores:

1. Divides simulations into batches based on CPU count
2. Runs batches in parallel using Python's multiprocessing
3. Combines results for final analysis

### Caching System

The caching system improves performance by storing and reusing simulation results:

- In-memory LRU cache with configurable size
- Time-based expiration (TTL)
- Thread-safe operations
- Persistence to disk
- Statistics tracking for cache hits/misses

## Implementation Details

### Core Simulation Algorithm

```python
def simulate_single_run(initial_amount, contributions, years, returns):
    result = np.zeros(years + 1)
    result[0] = initial_amount
    
    for year in range(1, years + 1):
        # Get annual return for this simulation (random based on allocation)
        annual_return = np.random.normal(returns.mean, returns.volatility)
        
        # Apply return to previous year's amount
        result[year] = result[year-1] * (1 + annual_return)
        
        # Add contribution for this year
        result[year] += contributions[year-1]
    
    return result
```

### Cache Key Generation

The cache system uses MD5 hashes of serialized parameters to create unique keys:

```python
def generate_key(args, kwargs):
    key_dict = {'args': args, 'kwargs': kwargs}
    key_str = json.dumps(key_dict, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()
```

### Error Handling

The system implements comprehensive error handling:

- Safe array operations to handle edge cases like NaN and infinity
- Type validation for all parameters
- Graceful fallbacks when simulations fail
- Cached error responses to prevent repeated expensive failures

## Performance Optimization

The Monte Carlo system includes several optimizations:

1. **Parallel Processing**: Distributes workloads across multiple CPU cores
2. **Vectorized Operations**: Uses NumPy for high-performance calculations
3. **Caching**: Reuses results for identical inputs
4. **Memory Optimization**: Minimizes memory usage in simulations
5. **Batch Processing**: Processes simulations in optimally sized batches

## Recent Improvements

### 1. System Consolidation

- Removed redundant parallel processing implementations
- Unified cache systems into a single implementation
- Created consolidated simulation and API integration modules

### 2. Enhanced Probability Sensitivity

- Improved sensitivity to parameter changes
- Ensures probability increases when parameters improve
- Provides more accurate assessment of recommendation impact

### 3. Caching Enhancements

- Added persistent cache with disk storage
- Implemented thread-safe operations
- Added statistics tracking
- Created tiered caching for different data types

### 4. API Integration Improvements

- Created factory functions for simulation endpoints
- Enhanced error handling and validation
- Improved consistency of API responses

## Known Limitations

1. **Long-term Projections**: Simulations beyond 20 years show higher variance

2. **Performance with Large Simulation Counts**: Large simulation counts (2000+) can be slow for complex goals

3. **Normal Distribution Assumptions**: Market returns use normal distributions which may underestimate extreme events

4. **Allocation Impact Precision**: Allocation recommendations may show smaller impact than expected for aggressive risk profiles

## Testing Strategy

The Monte Carlo system includes comprehensive testing:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Verify system works correctly as a whole
3. **Performance Tests**: Ensure system meets performance requirements
4. **Regression Tests**: Prevent reintroduction of fixed bugs

## Best Practices

1. **Appropriate Simulation Counts**:
   - Use 500+ simulations for stable results
   - Use 1000+ for critical analysis
   - Use 2000+ only when extreme precision is required

2. **Result Interpretation**:
   - Success probability of 75%+ is generally considered good
   - Focus on trends and relative changes rather than absolute values
   - Consider multiple confidence levels, not just success probability

3. **Parameter Sensitivity**:
   - Small changes in return assumptions can have large effects
   - Longer timeframes increase sensitivity to return assumptions
   - Higher initial amounts decrease sensitivity to contribution changes

4. **Resource Usage**:
   - Cache expensive simulation results
   - Use parallel processing for large simulation counts
   - Clear cache periodically to free memory

## Future Enhancements

1. **Advanced Distribution Models**:
   - Support for fat-tail distributions for more realistic market simulation
   - Custom return distributions for different asset classes

2. **Enhanced Parallelization**:
   - GPU-accelerated simulations for extremely large workloads
   - Adaptive parallelization based on system capabilities

3. **Smarter Caching**:
   - Predictive precaching of likely simulation parameters
   - Multi-level cache with in-memory and disk storage

4. **Visualization Enhancements**:
   - Interactive simulation visualizations
   - Sensitivity analysis tools
   - Parameter impact graphs

## API Reference

### Simulation Module

```python
# models/monte_carlo/simulation.py

def validate_simulation_parameters(parameters):
    """Validate simulation parameters."""
    
def prepare_simulation_data(goal, years=5):
    """Prepare simulation data for a goal."""
    
def safely_get_simulation_data(goal):
    """Safely extract simulation data from a goal."""
    
def cache_response(key, data, ttl=None):
    """Cache a response for future requests."""
```

### API Integration Module

```python
# models/monte_carlo/api_integration.py

def validate_api_parameters(params):
    """Validate parameters for simulation endpoints."""

def prepare_api_response(simulation_data, goal_data):
    """Prepare simulation data for API response."""

def create_simulation_endpoint(goal_service):
    """Factory function to create a simulation endpoint."""

def create_cache_clear_endpoint():
    """Factory function to create a cache clear endpoint."""
```

### Parallel Module

```python
# models/monte_carlo/parallel.py

def run_parallel_monte_carlo(
    initial_amount, contribution_pattern, years, 
    allocation_strategy, simulation_function,
    simulations=1000, confidence_levels=[0.10, 0.25, 0.50, 0.75, 0.90],
    seed=42, max_workers=None, chunk_size=None
):
    """Run Monte Carlo simulations in parallel using multiple processes."""

def single_simulation_example(
    seed_offset, initial_amount, contribution_pattern, 
    years, allocation_strategy
):
    """Example function showing the expected signature for a single simulation function."""
```

### Cache Module

```python
# models/monte_carlo/cache.py

def cached_simulation(func=None, ttl=None, key_prefix=''):
    """Decorator for caching simulation results."""

def invalidate_cache(pattern=None):
    """Invalidate cache entries."""

def get_cache_stats():
    """Get current cache statistics."""

def save_cache(file_path=None):
    """Save the cache to a file."""

def load_cache(file_path=None):
    """Load the cache from a file."""

def configure_cache(max_size=None, ttl=None, save_interval=None, 
                    cache_dir=None, cache_file=None):
    """Configure the global cache settings."""
```

## Related Documentation

- [Monte Carlo User Guide](MONTE_CARLO_USER_GUIDE.md): End-user focused guide
- [Monte Carlo Implementation Guide](MONTE_CARLO_IMPLEMENTATION_GUIDE.md): Developer-focused technical guide
- [Monte Carlo Testing Framework](MONTE_CARLO_TESTING_FRAMEWORK.md): Testing approach and methodologies
- [Monte Carlo Improvement Examples](MONTE_CARLO_IMPROVEMENT_EXAMPLES.md): Examples of system improvements
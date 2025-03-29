# Monte Carlo Simulation System Documentation

## Overview

The Monte Carlo simulation system is a key component of the financial projection and goal probability analysis in the Profiler4 application. It helps users understand their likelihood of achieving various financial goals by simulating multiple possible future scenarios based on random variations in market returns, inflation, and other economic factors.

This document explains the key components, working principles, and recent improvements to the Monte Carlo simulation system.

## Key Components

### 1. GoalProbabilityAnalyzer

The central component that orchestrates the probability analysis process. It:
- Takes a goal and user profile as input
- Runs Monte Carlo simulations with configurable parameters
- Calculates success probability and other metrics
- Returns structured data for visualization and decision-making

### 2. Financial Projection Module

Handles the actual projections of assets over time:
- Models different asset classes (equity, debt, gold, real estate, cash)
- Applies various return and volatility assumptions
- Simulates contribution patterns
- Accounts for allocation strategies and rebalancing

### 3. GoalAdjustmentService

Uses probability analysis to generate actionable recommendations:
- Analyzes current goal probability
- Identifies parameters that can be adjusted
- Calculates impact of potential adjustments
- Prioritizes recommendations based on feasibility and impact

## How It Works

1. **Input Processing**:
   - Goal details (target amount, timeframe, current savings, monthly contribution)
   - Asset allocation strategy
   - User profile information (age, income, risk profile)

2. **Simulation Setup**:
   - Configures simulation parameters (count, seed)
   - Sets up asset class return assumptions
   - Defines contribution pattern
   - Establishes allocation strategy

3. **Monte Carlo Simulation**:
   - Runs multiple simulations (default: 1000)
   - For each simulation:
     - Generates random returns for each asset class
     - Projects growth with contributions over time
     - Calculates final portfolio value

4. **Probability Calculation**:
   - Determines percentage of simulations that meet or exceed the target amount
   - Applies sensitivity calibration for values close to target
   - Calculates confidence intervals (P10, P25, P50, P75, P90)
   - Evaluates shortfall and upside risks

5. **Result Analysis and Recommendations**:
   - Analyzes simulation outcomes
   - Identifies parameters with highest impact on probability
   - Generates recommendations to improve probability
   - Calculates the impact of each recommendation

## Recent Improvements

### 1. Enhanced Probability Sensitivity

The system now uses an improved algorithm that shows appropriate sensitivity to parameter changes:

- **Partial Success Recognition**: Values very close to the target (within 10%) receive partial credit in probability calculations.
- **Graduated Impact Scaling**: Small parameter changes show proportional impact on probability.
- **Edge Case Handling**: Better handling of very high and very low probability scenarios.

### 2. Simulation Stability Enhancements

- **Increased Default Count**: Simulation count increased from 500 to 1000 for more stable results.
- **Minimum Count Validation**: Enforces a minimum simulation count of 500 to ensure statistical validity.
- **Consistent Random Seeds**: Uses fixed random seeds (default: 42) for deterministic testing and reproducible results.

### 3. Robust Integration with Goal Adjustment

- **Type-Safe Result Handling**: Improved handling of different result types and structures.
- **Enhanced Error Recovery**: Better error handling and fallback mechanisms throughout the system.
- **Consistent API**: Standardized interfaces between probability analysis and recommendation generation.

### 4. Performance Optimization System

- **Caching System**: Comprehensive caching to avoid redundant calculations.
- **Parallel Processing**: Multi-core execution for faster simulation runs.
- **Memory Optimization**: Efficient data structures to minimize memory usage.
- **Vectorized Operations**: NumPy-based operations for faster calculations.

### 5. Cache Persistence Framework

- **File-Based Persistence**: Saves cache to disk for persistence between application restarts.
- **Automatic Recovery**: Loads cache on application startup.
- **Scheduled Auto-Save**: Saves cache at configurable intervals.
- **Thread-Safe Operations**: Ensures data integrity with concurrent access.
- **Admin API Integration**: Provides API endpoints for cache management.

#### Cache Persistence Architecture

The cache persistence system provides robust storage of simulation results between application restarts, improving performance and reducing computational load. Key components include:

1. **Core Cache Class**: `SimulationCache` provides thread-safe operations with reentrant locks for all cache operations and separate locks for save operations.

2. **Storage Format**: Cache data is serialized using Python's pickle library with metadata including:
   - Timestamp of cache creation/modification
   - Version information
   - Cache statistics (hit/miss rates, entry counts)

3. **Atomic File Operations**: The save process uses atomic operations with temporary files to prevent corruption during system interruptions.

4. **Auto-Save Mechanism**: A configurable timer schedules regular cache saves at intervals defined in configuration.

5. **Lifecycle Management**:
   - Application startup: Cache is automatically loaded if available
   - Application shutdown: Unsaved cache data is persisted
   - Signal handling: SIGTERM and SIGINT trigger cache saving

6. **Error Handling**:
   - Graceful degradation when persistence fails
   - Fallback to in-memory operation
   - Comprehensive logging of errors

#### Cache API and Usage

The cache system provides both programmatic and HTTP API access:

```python
# Import cache functionality
from models.monte_carlo.cache import (
    cached_simulation,
    invalidate_cache,
    save_cache,
    load_cache,
    configure_cache,
    get_cache_stats
)

# Use the decorator to cache simulation results
@cached_simulation
def run_expensive_simulation(parameters):
    # Simulation code here
    return results

# Configure cache behavior
configure_cache(
    max_size=200,              # Maximum number of cache entries
    ttl=7200,                  # Time-to-live (seconds)
    save_interval=600,         # Auto-save interval (seconds)
    cache_dir='/path/to/cache' # Custom cache directory
)

# Manually save/load cache
save_cache('/custom/path/cache.pickle')
load_cache('/custom/path/cache.pickle')

# Get cache statistics
stats = get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

#### Configuration Options

The cache system can be configured through environment variables or application config:

| Option | Environment Variable | Default | Description |
|--------|---------------------|---------|-------------|
| Max Cache Size | MONTE_CARLO_CACHE_SIZE | 100 | Maximum number of cache entries |
| Cache TTL | MONTE_CARLO_CACHE_TTL | 3600 | Time-to-live in seconds |
| Save Interval | MONTE_CARLO_SAVE_INTERVAL | 300 | Auto-save interval in seconds |
| Cache Directory | MONTE_CARLO_CACHE_DIR | data/cache | Directory to store cache files |
| Cache Filename | MONTE_CARLO_CACHE_FILE | monte_carlo_cache.pickle | Name of cache file |
| Disable Cache | DISABLE_MONTE_CARLO_CACHE | false | Set to "true" to disable caching |

#### Admin Endpoints

The system provides API endpoints for cache management:

- `POST /api/v2/admin/cache/clear`: Clear the entire simulation cache
- `GET /api/v2/admin/cache/stats`: Get cache statistics
- `POST /api/v2/admin/cache/save`: Force a cache save operation
- `POST /api/v2/admin/cache/load`: Force a cache load operation
- `POST /api/v2/admin/cache/configure`: Update cache configuration

### 6. Comprehensive Testing Framework

- **Sensitivity Testing**: Validation of probability increases for parameter improvements.
- **Stability Testing**: Verification of result consistency with different simulation counts.
- **Edge Case Handling**: Specific tests for difficult goal scenarios (near-impossible, nearly-achieved).
- **Integration Testing**: End-to-end validation of the full recommendation pipeline.
- **Performance Benchmarking**: Measurement of simulation speed and optimization impact.

## Usage Examples

### Basic Probability Analysis

```python
# Initialize the analyzer
analyzer = GoalProbabilityAnalyzer()

# Define a goal
retirement_goal = {
    "id": "retirement-goal",
    "category": "retirement",
    "target_amount": 50000000,  # ₹5 crore
    "current_amount": 10000000,  # ₹1 crore
    "monthly_contribution": 50000,  # ₹50,000 per month
    "timeframe": "2042-01-01",  # Target retirement date
    "asset_allocation": {
        "equity": 0.60,
        "debt": 0.30,
        "gold": 0.05,
        "cash": 0.05
    }
}

# Define a user profile
user_profile = {
    "age": 40,
    "income": 2400000,  # ₹24 lakh annual
    "risk_profile": "moderate",
    "country": "India",
    "assets": {
        "equity": 1500000,
        "debt": 2000000,
        "gold": 500000,
        "cash": 800000
    }
}

# Analyze probability
result = analyzer.analyze_goal_probability(retirement_goal, user_profile, simulations=1000)

# Access results
print(f"Success probability: {result.success_probability:.2%}")
print(f"Expected outcome: ₹{result.success_metrics['expected_outcome']:,.2f}")
print(f"Percentiles:")
print(f"  P10: ₹{result.distribution_data['percentile_10']:,.2f}")
print(f"  P50: ₹{result.distribution_data['percentile_50']:,.2f}")
print(f"  P90: ₹{result.distribution_data['percentile_90']:,.2f}")
```

### Generating Adjustment Recommendations

```python
# Initialize the service
adjustment_service = GoalAdjustmentService()

# Generate recommendations
recommendations = adjustment_service.generate_adjustment_recommendations(retirement_goal, user_profile)

# Display recommendations
for i, rec in enumerate(recommendations["recommendations"], 1):
    print(f"Recommendation {i}: {rec['description']}")
    print(f"  Type: {rec['type']}")
    print(f"  Impact: {rec['impact']}")
    print(f"  Difficulty: {rec['implementation_difficulty']}")
    print()

# Apply a recommendation
modified_goal = adjustment_service.apply_recommendation(retirement_goal, recommendations["recommendations"][0])

# Calculate new probability
new_result = analyzer.analyze_goal_probability(modified_goal, user_profile)
print(f"New success probability: {new_result.success_probability:.2%}")
print(f"Probability improvement: {(new_result.success_probability - result.success_probability):.2%}")
```

### Working with Different Goal Types

The system supports various goal types with type-specific calculations:

- **Retirement**: Long-term goals with inflation and post-retirement income needs
- **Education**: Medium-term goals with education-specific inflation
- **Home Purchase**: Goals with down payment calculations and mortgage considerations
- **Emergency Fund**: Short-term goals with expense coverage analysis
- **Debt Repayment**: Goals with interest cost calculations and early payoff analytics
- **Custom**: General-purpose financial goals with flexible parameters

## Best Practices

1. **Use Sufficient Simulation Count**:
   - At least 1000 simulations for stable results
   - Consider using 2000+ for very long-term or complex goals

2. **Interpret Results Correctly**:
   - Success probability is not a guarantee
   - Consider the full range of outcomes (P10 to P90)
   - Pay attention to shortfall risks in addition to success probability

3. **Validate Parameter Sensitivity**:
   - Test different parameter adjustments to understand sensitivity
   - Focus on recommendations with highest impact-to-difficulty ratio

4. **Regular Recalculation**:
   - Recalculate probability as market conditions change
   - Update goals and parameters as personal circumstances evolve

## Performance Considerations

For optimal performance:

- Use the default simulation count (1000) for most analyses
- Increase simulation count only for critical decisions or long-term goals
- Consider vectorized implementation for high-volume calculations
- Use appropriate error handling for edge cases

## Known Limitations

1. **Very Long-Term Projections**: Goals with timeframes beyond 20 years show higher variance due to compounding uncertainty.
2. **Extreme Parameter Values**: Goals with extreme parameter values (near-zero contributions, very short timeframes) may produce less reliable results.
3. **Allocation Impact Precision**: Asset allocation impact on probability may be underestimated in certain scenarios, particularly for aggressive allocation strategies.

## Future Enhancements

Planned improvements to the Monte Carlo simulation system:

1. **Performance Optimizations**:
   - Vectorized operations for calculation-intensive parts
   - Parallel processing for independent simulations
   - Smart caching for common calculation patterns

2. **Enhanced Modeling**:
   - Time-varying return and volatility assumptions
   - Fat-tail distributions for more realistic market modeling
   - Scenario-based stress testing

3. **Improved Visualization**:
   - Interactive probability charts
   - Sensitivity analysis visualization
   - Recommendation impact comparison tools

## Appendix: Technical Specifications

### Return Assumptions (Default)

| Asset Class | Expected Return | Volatility |
|-------------|----------------|------------|
| Equity      | 10%            | 18%        |
| Debt        | 6%             | 5%         |
| Gold        | 7%             | 15%        |
| Real Estate | 8%             | 12%        |
| Cash        | 3%             | 1%         |

### Confidence Level Definitions

| Confidence Level | Description |
|------------------|-------------|
| P10              | Pessimistic case (exceeded by 90% of simulations) |
| P25              | Lower quartile (exceeded by 75% of simulations) |
| P50              | Median case (exceeded by 50% of simulations) |
| P75              | Upper quartile (exceeded by 25% of simulations) |
| P90              | Optimistic case (exceeded by 10% of simulations) |

### Simulation Parameters

| Parameter | Default Value | Minimum | Maximum |
|-----------|---------------|---------|---------|
| Simulation Count | 1000 | 500 | No limit |
| Random Seed | 42 | N/A | N/A |
| Inflation Rate | 6% | N/A | N/A |
| Rebalancing Frequency | Annual | N/A | N/A |
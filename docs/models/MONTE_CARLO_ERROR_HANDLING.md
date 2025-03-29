# Monte Carlo Error Handling & Resiliency Framework

This document outlines the comprehensive error handling and resiliency framework for the Monte Carlo simulation system, focusing on input validation, fault tolerance, recovery mechanisms, and logging capabilities.

## 1. Error Case Testing Framework

### 1.1 Invalid Parameter Validation

The `test_monte_carlo_error_handling.py` suite tests validation of invalid parameters including:

- **Simulation Parameters**: Tests for negative iterations, excessive iterations, invalid time steps
- **Goal Parameters**: Tests for invalid target amounts, past timeframes, extreme timeframes
- **Profile Data**: Tests for missing or malformed profile data
- **Database Constraints**: Tests for violations of database constraints and data validity checks
- **Goal Updates**: Tests for invalid updates like negative contributions or invalid allocations

Example test case:
```python
def test_invalid_simulation_parameters(self, test_retirement_goal, test_goal_service, profile_data):
    """Test handling of invalid simulation parameters."""
    # Test with negative iterations
    with pytest.raises(ValueError) as exc_info:
        test_goal_service.calculate_goal_probability(
            goal_id=test_retirement_goal,
            profile_data=profile_data,
            simulation_iterations=-100  # Invalid negative value
        )
    assert "iterations" in str(exc_info.value).lower(), "Error should mention invalid iterations"
```

### 1.2 Database Error Handling

Tests validate proper handling of database errors:

- **Connection Failures**: Tests for database connection failures
- **Constraint Violations**: Tests for integrity constraint violations
- **Transaction Management**: Tests for proper transaction rollback on errors
- **Database Locking**: Tests for database lock handling with concurrent access

Each test verifies that:
1. The appropriate error type is raised
2. Error messages are clear and useful
3. Transactions are properly rolled back
4. Resources are cleaned up

### 1.3 Input Edge Cases

Tests for boundary conditions and edge cases:

- **Zero Values**: Testing goals with zero contributions or zero starting balances
- **Very Large Values**: Testing extreme goal amounts and timeframes
- **Inconsistent Data**: Testing for data inconsistencies like current amount > target amount

Example edge case test:
```python
def test_inconsistent_database_state(self, mock_db_setup, profile_data):
    """Test handling of inconsistent database state."""
    # Corrupt the database by creating inconsistent state
    with sqlite3.connect(db_path) as conn:
        # Set inconsistent values in the goal
        conn.execute("""
            UPDATE goals SET 
            target_amount = 50000000,
            current_amount = 100000000  -- Current higher than target, inconsistent
            WHERE id = ?
        """, (goal_id,))
```

## 2. Resiliency Testing Framework

### 2.1 Mock Database Service

A specialized `MockDatabaseService` class simulates various failure modes:

- **Connection Failures**: Random or targeted connection failures
- **Query Timeouts**: Simulated timeouts during operations
- **Database Locks**: Simulated lock conflicts for concurrent operations
- **I/O Errors**: Simulated disk and network failures

Example mock DB configuration:
```python
# Set up mock database service with moderate failure rate
mock_db = MockDatabaseService(db_path, 
                             failure_rate=0.3,     # 30% operations fail
                             latency_ms=50,        # 50ms latency
                             timeout_probability=0.1)  # 10% timeouts
```

### 2.2 Recovery Testing

Tests verify the system's ability to recover from failures:

- **Cache Invalidation**: Tests cache invalidation after errors
- **Partial Calculation Recovery**: Tests recovery from failures mid-calculation
- **Resource Exhaustion**: Tests handling of memory limitations and CPU constraints
- **Database Timeouts**: Tests retry mechanisms for transient failures

Example recovery test:
```python
def test_cache_corruption_recovery(self, mock_db_setup, profile_data, tmp_path):
    """Test recovery from cache corruption."""
    # Create a corrupted cache file
    corrupt_cache_path = os.path.join(tmp_path, "corrupt_cache.pickle")
    with open(corrupt_cache_path, "wb") as f:
        f.write(b"This is not a valid pickle file")
    
    # Patch the cache file path
    with patch('models.monte_carlo.cache.CACHE_FILE', corrupt_cache_path):
        # Clear cache (should try to load corrupt file)
        invalidate_cache()
        
        # Try calculation
        result = goal_service.calculate_goal_probability(
            goal_id=goal_id,
            profile_data=profile_data
        )
```

### 2.3 Resource Cleanup

Tests verify that resources are properly cleaned up after errors:

- **File Handle Cleanup**: Tests for proper file handle cleanup
- **Database Connection Cleanup**: Tests for connection cleanup after errors
- **Memory Cleanup**: Tests for proper cleanup of large arrays and data structures

## 3. Logging and Monitoring Framework

### 3.1 Error Log Verification

The `test_monte_carlo_logging.py` suite verifies that errors are properly logged:

- **Log Content**: Tests that logs contain the error message, context, and stack trace
- **Log Levels**: Tests that appropriate log levels are used (ERROR for errors, DEBUG for traces)
- **Context Information**: Tests that logs include relevant context like goal IDs, parameters

Example log verification:
```python
def test_error_context_logging(self, test_setup, log_capture):
    """Test that errors include sufficient context for debugging."""
    # Create bad profile data with missing fields
    bad_profile_data = {
        "monthly_income": 150000
        # Missing many required fields
    }
    
    try:
        goal_service.calculate_goal_probability(
            goal_id=goal_id,
            profile_data=bad_profile_data
        )
    except Exception:
        pass  # Expected exception
    
    # Check error context in logs
    context_found = False
    for record in error_logs + warning_logs:
        message = record.getMessage().lower()
        
        # Look for specific context about the error
        if "profile" in message and "data" in message:
            # Check if the message includes specifics about missing fields
            if any(field in message for field in ["missing", "required", "invalid"]):
                context_found = True
                break
```

### 3.2 Performance Monitoring

Tests for performance monitoring logging:

- **Timing Information**: Tests that execution times are logged
- **Resource Usage**: Tests for memory usage logging
- **Iteration Counts**: Tests that simulation iterations are logged
- **Cache Statistics**: Tests that cache hit/miss rates are logged

### 3.3 Structured Logging

Tests verify that logs use structured formats for easier parsing:

- **Key-Value Pairs**: Tests for key=value or key: value format
- **JSON Formatting**: Tests for JSON-formatted log entries
- **Consistent Fields**: Tests for consistent field names across log entries

Example structured log verification:
```python
def test_structured_logging_format(self, test_setup, log_capture):
    """Test that logs use structured format for easier parsing."""
    # Check for structured logging patterns
    structured_patterns = [
        r'\w+=[\w.]+',  # key=value
        r'\w+: [\w.]+',  # key: value 
        r'"?\w+"?: [\w.]+',  # "key": value (JSON-like)
        r'[\w.]+=\{.*?\}',  # key={...}
        r'\{.*?\}'  # {...} (JSON object)
    ]
```

## 4. Implementation Recommendations

Based on the test suite, here are key implementation recommendations:

### 4.1 Input Validation

- Implement thorough validation of all parameters before simulation
- Use defensive programming with strict type and range checking
- Implement a validation layer with clear error messages
- Add sensible parameter limits to prevent resource exhaustion

### 4.2 Transaction Management

- Use a robust transaction management pattern for database operations
- Implement proper rollback on any error
- Use a context manager pattern for resource acquisition and cleanup
- Ensure proper cleanup even in error paths

### 4.3 Resilience Patterns

- Implement retry logic for transient failures
- Use circuit breakers for persistent failures
- Implement graceful degradation for resource constraints
- Add timeout handling for long-running operations

### 4.4 Monitoring and Alerting

- Log detailed error information with context
- Use structured logging for easier parsing
- Log performance metrics for monitoring
- Implement alerting thresholds for critical failures

## 5. Running the Test Suites

To run the comprehensive error handling test suite:

```bash
# Run error handling tests
pytest -xvs tests/integration/test_monte_carlo_error_handling.py

# Run resiliency tests
pytest -xvs tests/integration/test_monte_carlo_resiliency.py

# Run logging tests
pytest -xvs tests/integration/test_monte_carlo_logging.py
```

For specific test categories:
```bash
# Run invalid parameter tests
pytest -xvs tests/integration/test_monte_carlo_error_handling.py::TestMonteCarloErrorHandling::test_invalid_*

# Run database error tests
pytest -xvs tests/integration/test_monte_carlo_error_handling.py::TestMonteCarloErrorHandling::test_database_*
```

## 6. Conclusion

The comprehensive error handling and resiliency framework ensures the Monte Carlo simulation system is robust in the face of:

1. Invalid inputs and edge cases
2. Database failures and constraints
3. Resource limitations and concurrent access
4. Transient failures and timeouts

By running these tests regularly, we can ensure the Monte Carlo simulation system remains reliable even under adverse conditions.
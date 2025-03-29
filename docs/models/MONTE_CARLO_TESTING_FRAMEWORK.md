# Monte Carlo Testing Framework

This document describes the comprehensive testing framework for the Monte Carlo simulation system, including integration testing, error handling, resiliency testing, and monitoring capabilities.

## 1. Testing Philosophy

The Monte Carlo testing framework follows a comprehensive approach to ensure reliability, performance, and correctness of the simulation system:

- **Test-Driven Development**: Critical components are developed with test-first methodology
- **Comprehensive Coverage**: Tests cover normal, edge, and error cases
- **Realistic Scenarios**: Test fixtures mimic real-world data and usage patterns
- **Performance Focus**: Testing includes performance benchmarks and regression detection
- **Resilience Verification**: System is tested under various failure conditions

## 2. Database Integration Testing

### 2.1 Test Database Setup

The framework provides a robust test database setup:

```python
@pytest.fixture(scope="function")
def test_db_connection(test_db_path):
    """Create a connection to the test database with transaction support."""
    connection = sqlite3.connect(test_db_path, isolation_level=None)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    
    # Start a transaction
    connection.execute("BEGIN TRANSACTION")
    
    yield connection
    
    # Rollback the transaction to clean up after test
    connection.execute("ROLLBACK")
    connection.close()
```

Key features:
- Isolated test database using `tempfile` module
- Transaction-based test isolation for clean state between tests
- Automatic setup and teardown through pytest fixtures
- Support for both SQLite and in-memory databases

### 2.2 Real Data Fixtures

Test fixtures provide realistic data for comprehensive testing:

```python
@pytest.fixture(scope="function")
def test_goals_with_edge_cases(test_profile, test_goal_service):
    """Create a set of goals with edge cases for testing."""
    goals = []
    
    # 1. Goal with zero current amount
    zero_current_goal_data = {...}
    
    # 2. Goal with very high target
    high_target_goal_data = {...}
    
    # 3. Goal with short timeframe
    short_timeframe_goal_data = {...}
    
    yield goals
    
    # Clean up
    for goal_id in goals:
        test_goal_service.delete_goal(goal_id)
```

Edge cases tested include:
- Zero values (current amount, contributions)
- Very large target amounts
- Very short and very long timeframes
- Unusual asset allocations
- Goals with current amount > target

### 2.3 Complete End-to-End Test Flow

End-to-end tests verify the entire simulation flow:

```python
def test_api_probability_endpoint(self, client):
    """Test the API endpoint for calculating goal probability."""
    # Create a test profile and goal
    profile_response = client.post('/api/v2/profile', ...)
    goal_response = client.post(f'/api/v2/goals/{profile_id}', ...)
    
    # Call the probability API endpoint
    probability_response = client.post(
        f'/api/v2/goal/{goal_id}/probability',
        data=json.dumps({"force_recalculate": True})
    )
    
    # Verify database was updated
    goal_after = client.get(f'/api/v2/goal/{goal_id}')
    assert goal_after.json()['goal_success_probability'] == probability_result['success_probability']
```

Key aspects tested:
- Full HTTP request/response cycle
- Database persistence verification
- Response status and format validation
- Realistic API usage patterns

## 3. Error Handling Framework

### 3.1 Invalid Parameter Validation

Tests validate proper handling of invalid inputs:

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

Parameter validation tests include:
- Negative and zero values
- Extreme values (very large or small)
- Malformed inputs (wrong types, formats)
- Missing required parameters
- Invalid parameter combinations

### 3.2 Database Error Handling

Tests for database error handling include:

```python
def test_transaction_rollback_on_error(self, test_db_connection, test_retirement_goal,
                                      test_goal_service, profile_data):
    """Test that transactions are rolled back properly on errors."""
    # Get current probability
    goal_before = test_goal_service.get_goal(test_retirement_goal)
    orig_probability = goal_before.get('goal_success_probability', 0)
    
    # Patch a method to simulate an error mid-transaction
    with patch.object(test_goal_service, '_update_goal_probability') as mock_update:
        mock_update.side_effect = ValueError("Simulated error during update")
        
        # Attempt calculation, should fail
        with pytest.raises(ValueError):
            test_goal_service.calculate_goal_probability(...)
    
    # Verify goal probability wasn't changed (transaction rolled back)
    goal_after = test_goal_service.get_goal(test_retirement_goal)
    after_probability = goal_after.get('goal_success_probability', 0)
    
    assert abs(after_probability - orig_probability) < 0.0001, "Transaction rollback failed"
```

Database error tests verify:
- Transaction rollback on errors
- Proper error propagation
- Connection cleanup
- Error reporting with context
- Constraint violation handling

### 3.3 Edge Case Handling

Tests for edge cases ensure the system handles unusual situations:

```python
def test_edge_case_behavior(self, real_data_fixture, test_goal_service, profile_data):
    """Test Monte Carlo behavior with edge cases."""
    # Find edge case goals
    small_goal = next((g for g in all_goals if g['title'] == "New Smartphone"), None)
    zero_contribution_goal = next((g for g in all_goals if g['title'] == "Growth of Existing Investments"), None)
    
    # Test very small target with short timeframe
    if small_goal:
        result = test_goal_service.calculate_goal_probability(
            goal_id=small_goal['id'],
            profile_data=profile_data,
            force_recalculate=True
        )
        small_prob = to_scalar(result.get_safe_success_probability())
        
        # Should have very high probability due to small amount
        assert small_prob > 0.95, f"Small goal should have high probability"
```

Edge cases tested:
- Very small goals
- Zero contribution goals
- Very long timeframe goals
- Already-achieved goals
- Inconsistent goal data

## 4. Resiliency Testing Framework

### 4.1 Mock Database Service

A specialized mock database service simulates various failure modes:

```python
class MockDatabaseService:
    def __init__(self, db_path, failure_rate=0.0, latency_ms=0, timeout_probability=0.0):
        self.db_path = db_path
        self.failure_rate = failure_rate
        self.latency_ms = latency_ms
        self.timeout_probability = timeout_probability
        
    @contextmanager
    def connect(self):
        # Decide if this connection should fail
        if random.random() < self.failure_rate:
            raise sqlite3.OperationalError("Simulated connection failure")
        
        # Add simulated latency
        if self.latency_ms > 0:
            time.sleep(self.latency_ms / 1000.0)
            
        # Actual connection logic with mocking
        ...
```

The mock service can simulate:
- Connection failures
- Query timeouts
- Lock conflicts
- Slow responses
- Partial failures

### 4.2 Resiliency Tests

Tests verify the system's ability to handle failures:

```python
def test_database_connection_failures(self, mock_db_setup, profile_data):
    """Test handling of database connection failures."""
    db_path, profile_id, mock_db = mock_db_setup
    
    # Create a test goal
    goal_id = self._create_test_goal(db_path, profile_id)
    
    # Set up goal service with patch to use our mock DB
    goal_service = GoalService()
    goal_service.db_path = db_path
    
    # Increase failure rate for this test
    mock_db.set_failure_rate(0.5)
    
    # Patch sqlite3.connect to use our mock
    with patch('sqlite3.connect') as mock_connect:
        mock_connect.side_effect = lambda *args, **kwargs: mock_db.connect().__enter__()
        
        # Try calculation multiple times to encounter failures
        success_count = 0
        failure_count = 0
        
        for _ in range(5):
            try:
                # Clear any cached results
                invalidate_cache()
                
                # Attempt calculation
                result = goal_service.calculate_goal_probability(...)
                success_count += 1
            except Exception:
                failure_count += 1
                
        # We should have both successes and failures with 0.5 failure rate
        assert failure_count > 0, "Should have some failures with high failure rate"
```

Resiliency tests verify:
- Graceful handling of connection failures
- Proper timeout handling
- Recovery after transient errors
- Resource cleanup after failures
- Cache invalidation on errors

### 4.3 Cache Recovery Tests

Tests verify cache system recovery from corruption:

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
        
        # Try calculation - should recover by recalculating
        result = test_goal_service.calculate_goal_probability(...)
        
        # Verify we got a valid result
        assert result is not None
        
        # Verify probability is valid
        probability = result.get_safe_success_probability()
        assert 0 <= probability <= 1
```

Cache tests verify:
- Recovery from corrupt cache files
- Proper cache invalidation
- Cache consistency after errors
- Cache state after parameter changes

## 5. Logging and Monitoring Framework

### 5.1 Error Log Verification

Tests verify that errors are properly logged:

```python
def test_error_logging(self, test_retirement_goal, test_goal_service, profile_data, caplog):
    """Test that errors are properly logged with sufficient detail."""
    # Set caplog to capture DEBUG level
    caplog.set_level(logging.DEBUG)
    
    # Force an error with malformed profile data
    bad_profile_data = {
        "monthly_income": "not a number",  # Type error
        "risk_profile": None  # Missing required field
    }
    
    # Attempt calculation, should fail
    with pytest.raises(Exception):
        test_goal_service.calculate_goal_probability(...)
    
    # Check logs for error information
    assert any("error" in record.message.lower() for record in caplog.records)
    
    # Check for data details in logs
    detail_logged = False
    for record in caplog.records:
        if "profile" in record.message.lower() and "data" in record.message.lower():
            detail_logged = True
            break
    
    assert detail_logged, "Error logs should contain data details"
```

Error logging tests verify:
- Proper error level usage
- Inclusion of context information
- Error type identification
- Stack trace availability
- Data sanitization in logs

### 5.2 Performance Logging

Tests verify performance metric logging:

```python
def test_performance_logging(self, test_retirement_goal, test_goal_service, profile_data, caplog):
    """Test that performance metrics are logged appropriately."""
    # Set caplog to capture INFO level
    caplog.set_level(logging.INFO)
    
    # Calculate probability
    test_goal_service.calculate_goal_probability(...)
    
    # Check for performance logging
    performance_logged = False
    for record in caplog.records:
        message = record.getMessage().lower()
        if ("took" in message or "time" in message) and \
           any(unit in message for unit in ["ms", "sec", "s"]):
            performance_logged = True
            break
    
    assert performance_logged, "Performance metrics should be logged"
```

Performance logging tests verify:
- Execution time logging
- Resource usage logging
- Cache statistics logging
- Threshold violation alerts

### 5.3 Structured Logging Format

Tests verify log format quality:

```python
def test_structured_logging_format(self, test_retirement_goal, test_goal_service, profile_data, caplog):
    """Test that logs use structured format for easier parsing."""
    # Clear logs before test
    caplog.clear()
    
    # Calculate probability
    test_goal_service.calculate_goal_probability(...)
    
    # Check for structured logging patterns
    structured_patterns = [
        r'\w+=[\w.]+',  # key=value
        r'\w+: [\w.]+',  # key: value 
        r'"?\w+"?: [\w.]+',  # "key": value (JSON-like)
    ]
    
    structured_logs = []
    for record in caplog.records:
        message = record.getMessage()
        if any(re.search(pattern, message) for pattern in structured_patterns):
            structured_logs.append(message)
    
    # Should have some structured logs
    assert len(structured_logs) > 0, "No structured logging format detected"
```

Log format tests verify:
- Consistent field naming
- Machine-parseable format
- JSON-structured data where appropriate
- Context inclusion in log entries

## 6. Benchmark Testing

### 6.1 Performance Benchmarks

Performance tests track system performance:

```python
def test_monte_carlo_performance(self):
    """Benchmark Monte Carlo simulation performance."""
    # Standard test case
    goal_data = create_standard_goal()
    profile_data = create_standard_profile()
    
    # Warm up
    calculate_goal_probability(goal_data, profile_data)
    
    # Benchmark
    iterations = [100, 500, 1000, 2000]
    
    for iteration_count in iterations:
        start_time = time.time()
        result = calculate_goal_probability(
            goal_data, profile_data, 
            simulation_iterations=iteration_count
        )
        duration = time.time() - start_time
        
        print(f"Iterations: {iteration_count}, Time: {duration:.3f}s, " 
              f"Speed: {iteration_count/duration:.1f} iter/s")
```

Performance benchmarks include:
- Speed measurements for various iteration counts
- Memory usage tracking
- Scale testing with different goal complexities
- Cache efficiency measurement

### 6.2 Regression Detection

Tests detect performance regressions:

```python
def test_performance_regression(self, benchmark_fixture):
    """Test performance against baseline."""
    baseline = benchmark_fixture.get_baseline()
    
    # Run standard benchmark
    result, stats = run_benchmark(standard_benchmark_case)
    
    # Compare against baseline with tolerance
    assert stats.duration <= baseline.duration * 1.1, \
        f"Performance regression detected: {stats.duration:.3f}s vs baseline {baseline.duration:.3f}s"
```

Regression tests verify:
- Performance stays within acceptable limits
- No unexpected slowdowns
- Memory usage remains consistent
- Cache hit rates stay optimal

## 7. Running the Test Suites

### 7.1 Basic Test Commands

```bash
# Run database integration tests
pytest -xvs tests/integration/test_monte_carlo_database_integration.py

# Run error handling tests
pytest -xvs tests/integration/test_monte_carlo_error_handling.py

# Run resiliency tests
pytest -xvs tests/integration/test_monte_carlo_resiliency.py

# Run logging tests
pytest -xvs tests/integration/test_monte_carlo_logging.py
```

### 7.2 Running Specific Test Categories

```bash
# Run only transaction-related tests
pytest -xvs tests/integration/test_monte_carlo_database_integration.py::TestMonteCarloDbIntegration::test_transaction_*

# Run edge case tests
pytest -xvs tests/integration/test_monte_carlo_real_data.py::TestMonteCarloRealData::test_edge_case_*

# Run Flask integration tests
pytest -xvs tests/integration/test_monte_carlo_flask_integration.py
```

### 7.3 Performance Test Commands

```bash
# Run performance benchmarks and generate report
pytest tests/models/test_monte_carlo_benchmark_suite.py --benchmark-save

# Compare against previous benchmark
pytest tests/models/test_monte_carlo_benchmark_suite.py --benchmark-compare
```

## 8. Extending the Framework

### 8.1 Adding New Test Cases

To add new test cases to the framework:

1. **Choose the appropriate test file** based on what you're testing
2. **Create a test method** with a descriptive name
3. **Use fixtures** from `conftest.py` when possible
4. **Follow the test pattern** established in existing tests
5. **Add appropriate assertions**

```python
def test_new_feature(self, test_retirement_goal, test_goal_service, profile_data):
    """Test the behavior of a new feature."""
    # Setup
    # ...
    
    # Action
    result = test_goal_service.calculate_new_feature(...)
    
    # Assertions
    assert result is not None
    assert 0 <= result.probability <= 1
```

### 8.2 Creating Custom Test Fixtures

To create custom test fixtures:

1. **Add fixture to appropriate `conftest.py`**
2. **Give the fixture an appropriate scope** (function, class, module, session)
3. **Use existing fixtures** as dependencies when possible
4. **Include cleanup code** after the yield

```python
@pytest.fixture(scope="function")
def custom_test_fixture(test_profile):
    """Create a custom test fixture."""
    # Setup
    custom_data = create_test_data(test_profile)
    
    yield custom_data
    
    # Cleanup
    delete_test_data(custom_data)
```

### 8.3 Implementing Mock Services

To create new mock services:

1. **Create a new mock class** in the appropriate test module
2. **Implement core interfaces** from the real service
3. **Add failure simulation mechanisms**
4. **Add logging for diagnostic purposes**

```python
class MockCacheService:
    """Mock cache service for testing cache failures."""
    
    def __init__(self, failure_rate=0.0):
        self.failure_rate = failure_rate
        self.cache = {}
        self.hits = 0
        self.misses = 0
        
    def get(self, key):
        """Get an item from cache with simulated failures."""
        if random.random() < self.failure_rate:
            raise RuntimeError("Simulated cache failure")
            
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        else:
            self.misses += 1
            return None
```

## 9. Conclusion

The Monte Carlo testing framework provides a comprehensive approach to ensure the reliability, performance, and correctness of the Monte Carlo simulation system. By covering database integration, error handling, resiliency, and monitoring, the framework helps maintain a robust system that can handle real-world usage.

Future enhancements to the framework will include:

1. **Automated performance trend analysis**
2. **Integration with system monitoring tools**
3. **Enhanced fault injection mechanisms**
4. **Extended test coverage for new features**
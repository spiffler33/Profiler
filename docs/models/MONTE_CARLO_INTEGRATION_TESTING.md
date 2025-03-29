# Monte Carlo Integration Testing Framework

This document outlines the comprehensive integration testing framework for the Monte Carlo simulation system, focusing on database integration, real-world data fixtures, and end-to-end testing.

## Overview

The Monte Carlo integration testing framework provides:

1. **Isolated Test Database Environment**: Transaction-based testing with dedicated test databases
2. **Real-World Data Fixtures**: Predefined test profiles and goals with edge cases 
3. **End-to-End Testing**: Complete API route testing with Flask test client
4. **Concurrent Testing**: Testing for parallel Monte Carlo simulations and database access
5. **Database Backup/Restore**: Testing of database versioning capabilities

## Test Database Setup

### Key Components:

- **Pytest Fixtures**: Automatic database setup and teardown for each test
- **Transaction Isolation**: Each test runs in a transaction that's rolled back after completion
- **Temporary Database Files**: Using Python's tempfile module for isolated test databases
- **Pre-populated Test Data**: Common test fixtures are provided through pytest fixtures

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

## Real Data Fixtures

### Features:

- **Diverse Goal Types**: Retirement, education, home purchase, etc.
- **Edge Cases**: Zero starting balance, very large targets, very short timeframes
- **Foreign Currency Support**: Test fixtures with different currencies
- **Investment Allocations**: Various asset allocations for different risk profiles
- **Complex Funding Strategies**: Multiple funding sources, variable contributions, etc.

```python
@pytest.fixture(scope="function")
def test_goals_with_edge_cases(test_profile, test_goal_service):
    """Create a set of goals with edge cases for testing."""
    goals = []
    
    # 1. Goal with zero current amount
    zero_current_goal_data = {
        "category": "home_purchase",
        "title": "Zero Current Amount Goal",
        "target_amount": 10000000,
        "current_amount": 0,
        # ... additional fields
    }
    # ... additional edge cases
    
    yield goals
    
    # Clean up
    for goal_id in goals:
        test_goal_service.delete_goal(goal_id)
```

## End-to-End Test Flow

### Capabilities:

- **HTTP Route Testing**: Tests actual Flask API endpoints through the web interface
- **Database Persistence**: Verifies that API calls properly update the database
- **Concurrent Access**: Tests concurrent Monte Carlo calculations
- **Full UI Integration**: Tests that calculated probabilities appear in the web UI
- **API Error Handling**: Validates API behavior with invalid inputs

```python
def test_api_probability_endpoint(self, client):
    """Test the API endpoint for calculating goal probability."""
    # Create a test profile
    profile_response = client.post(
        '/api/v2/profile',
        data=json.dumps(profile_data),
        content_type='application/json'
    )
    
    # ... create a goal
    
    # Call the probability API endpoint
    probability_response = client.post(
        f'/api/v2/goal/{goal_id}/probability',
        data=json.dumps({
            "force_recalculate": True,
            "iterations": 1000
        }),
        content_type='application/json'
    )
    
    # ... verify response
```

## Database Integration Tests

### Test Cases:

1. **Probability Persistence**: Testing that probability values are correctly stored and retrieved
2. **Transaction Isolation**: Ensuring database transactions maintain ACID properties
3. **Batch Calculations**: Testing multiple goal calculations with a single database round-trip
4. **Parameter Impact**: Testing how parameter changes affect probability calculations
5. **Database Versioning**: Testing backup and restore capabilities

```python
def test_transaction_isolation(self, test_db_connection, test_retirement_goal, 
                              test_goal_service, profile_data):
    """Test transaction isolation for probability calculations."""
    # First get the current probability
    goal_before = test_goal_service.get_goal(test_retirement_goal)
    orig_probability = goal_before.get('goal_success_probability', 0)
    
    # Start a transaction in the test connection
    test_db_connection.execute("BEGIN TRANSACTION")
    
    # Update the goal probability directly in the DB
    test_probability = 0.987654  # Distinctive test value
    
    test_db_connection.execute(
        "UPDATE goals SET goal_success_probability = ? WHERE id = ?",
        (test_probability, test_retirement_goal)
    )
    
    # ... transaction testing logic
```

## Database Test Utilities

A dedicated `db_test_utils.py` module provides:

1. **Test Database Creation**: Create temporary databases for testing
2. **Schema Initialization**: Set up schema with all required tables
3. **Test Data Generation**: Create test profiles and goals
4. **Transaction Management**: Context manager for transaction isolation
5. **Backup/Restore**: Utilities for backing up and restoring databases

```python
def create_test_database():
    """Create a temporary test database file."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_monte_carlo_")
    os.close(fd)
    
    # Initialize database schema
    initialize_database_schema(path)
    
    return path
```

## Running the Tests

The test suite can be run with pytest:

```
pytest -xvs tests/integration/test_monte_carlo_database_integration.py
pytest -xvs tests/integration/test_monte_carlo_real_data.py
pytest -xvs tests/integration/test_monte_carlo_flask_integration.py
```

For running all Monte Carlo integration tests:

```
pytest -xvs tests/integration/test_monte_carlo_*.py
```

## Extending the Framework

To add new test cases:

1. **New Test Files**: Create new test files in the `tests/integration` directory
2. **Pytest Fixtures**: Use existing fixtures from `conftest.py`
3. **Database Utilities**: Use functions from `db_test_utils.py` for database operations
4. **Edge Cases**: Consider adding new edge cases to the `test_goals_with_edge_cases` fixture

## Conclusion

This comprehensive Monte Carlo integration testing framework provides robust testing of the simulation system from database interactions to web UI integration. It ensures that:

1. Probability calculations are correctly persisted
2. Database transactions maintain proper isolation
3. Edge cases are handled correctly
4. The API endpoints work as expected
5. The web UI correctly displays probability information

By running these tests regularly, we can ensure the Monte Carlo simulation system remains reliable even as we make changes to the codebase.
# API Integration Test Suite

This directory contains test scripts for validating the API endpoint integration between frontend components and backend services.

## Cache Management API Tests

### Overview

The Cache Management API endpoints are used by the CacheManagementTool frontend component to display, monitor, and maintain cache systems. The endpoints include:

- `GET /api/v2/admin/cache/stats` - Returns statistics for all cache systems
- `GET /api/v2/admin/cache/entries/{type}` - Lists cache entries for a specific type
- `POST /api/v2/admin/cache/invalidate` - Invalidates specific or all cache entries
- `POST /api/v2/admin/cache/refresh` - Refreshes all cache systems

### Automated Testing

The `cache_api_test.py` script provides automated tests for all cache management API endpoints.

To run the automated tests:

```bash
# Start the Flask application in one terminal
cd /Users/coddiwomplers/Desktop/Python/Profiler4
python app.py

# In another terminal, run the tests
python -m tests.api_fix.cache_api_test
```

The automated tests verify:
- Proper response structure and status codes
- Cache statistics retrieval
- Entry listing for different cache types
- Cache invalidation (specific entry, pattern-based, and full cache)
- Cache refresh functionality

### Manual Testing

The `api_test_manual.py` script provides a command-line interface for testing specific API endpoints individually, which is useful for debugging specific issues.

To use the manual testing script:

```bash
# Start the Flask application in one terminal
cd /Users/coddiwomplers/Desktop/Python/Profiler4
python app.py

# In another terminal, run specific test commands
python -m tests.api_fix.api_test_manual stats
python -m tests.api_fix.api_test_manual entries monte_carlo
python -m tests.api_fix.api_test_manual invalidate monte_carlo
python -m tests.api_fix.api_test_manual refresh

# Run all tests in sequence
python -m tests.api_fix.api_test_manual all

# Populate the cache with test data
python -m tests.api_fix.api_test_manual populate
```

Available commands:
- `stats` - Test the cache stats endpoint
- `entries <type>` - Test entry listing for a specific cache type (monte_carlo, parameter, all)
- `invalidate <type>` - Test invalidating all entries of a specific type
- `invalidate_key <type> <key>` - Test invalidating a specific cache entry
- `invalidate_pattern <type> <pattern>` - Test invalidating entries matching a pattern
- `refresh` - Test the cache refresh endpoint
- `populate` - Add test entries to the cache for testing
- `all` - Run all tests in sequence

## System Health Dashboard Tests

### API Testing

The `system_health_api_test.py` script provides comprehensive testing for the System Health API endpoints, which are used by the SystemHealthDashboard component:

- `GET /api/v2/admin/health` - Returns real-time system metrics
- `GET /api/v2/admin/health/history` - Returns historical metrics with time range and interval selection

To run the System Health API tests:

```bash
# Run all tests and generate a comprehensive report
python -m tests.api_fix.system_health_api_test all

# Run specific test groups
python -m tests.api_fix.system_health_api_test current
python -m tests.api_fix.system_health_api_test history
python -m tests.api_fix.system_health_api_test history_ranges
python -m tests.api_fix.system_health_api_test interval_validation
python -m tests.api_fix.system_health_api_test error_handling
python -m tests.api_fix.system_health_api_test alerts
python -m tests.api_fix.system_health_api_test browser_integration
```

The test script verifies:
- Real-time system metrics (CPU, memory, disk, API stats)
- Historical metrics with different time ranges
- Different aggregation intervals
- Alert generation and health status
- Error handling for invalid parameters
- Browser integration points for frontend components

### Browser Integration Testing

#### System Health Dashboard Test Page

The `system_health_dashboard_test.py` script provides a browser-based integration test for the SystemHealthDashboard component. It launches a test page that simulates the dashboard and verifies its interaction with the backend API.

To run the browser integration test:

```bash
python -m tests.api_fix.system_health_dashboard_test
```

This will open a browser window with a test dashboard that allows you to run individual tests for:
- Current metrics display
- Historical data visualization
- Time range selection
- Interval selection
- Alert visualization
- Auto-refresh functionality
- Error handling

#### Comprehensive Admin UI Testing

The `admin_browser_integration_test.py` script provides comprehensive browser-based testing for all admin interface components. It uses Selenium WebDriver to test real browser interactions with the UI components.

To run all admin component tests:
```bash
python -m tests.api_fix.admin_browser_integration_test all
```

Run tests for a specific component:
```bash
python -m tests.api_fix.admin_browser_integration_test health
python -m tests.api_fix.admin_browser_integration_test cache
python -m tests.api_fix.admin_browser_integration_test parameters
```

Additional options:
```bash
# Use Firefox instead of Chrome
python -m tests.api_fix.admin_browser_integration_test --browser firefox

# Run in headless mode
python -m tests.api_fix.admin_browser_integration_test --headless

# Use a different server URL
python -m tests.api_fix.admin_browser_integration_test --url http://localhost:5000
```

Test results are saved to the `reports/` directory, and screenshots are saved to `reports/screenshots/` for visual verification.

The admin browser integration tests cover the following test cases:

##### System Health Dashboard (SH)
- SH-01: Dashboard Loading
- SH-02: Service Status Indicators
- SH-03: System Metrics Display
- SH-04: Alerts Section
- SH-05: Historical Data Charts
- SH-06: Time Range Selection
- SH-07: Auto-Refresh Functionality

##### Cache Management (CM)
- CM-01: Cache Overview Loading
- CM-02: Cache Statistics Display
- CM-03: Cache Action Buttons
- CM-04: Cache Performance Chart
- CM-05: Cache Configuration Form

##### Parameter Admin (PA)
- PA-01: Parameter Panel Loading (basic test)

## Integration Testing Status

- ✅ Cache Management API endpoints have been implemented and tested
- ⚠️ Parameter API endpoints need validation
- ✅ Question Flow API endpoints have been implemented and tested
- ✅ System Health API endpoints have been fully implemented and tested (API + Browser)
- ✅ Browser-based integration tests have been implemented for:
  - ✅ Question Flow components
  - ✅ System Health Dashboard
  - ✅ Cache Management interface
  - ✅ Parameter Admin interface (comprehensive testing)
- ✅ Authentication UI components have been implemented
- ✅ Client-side token management has been implemented

## Next Steps

1. Complete validation of Parameter API endpoints (`/api/v2/admin/parameters/*`)
2. ✅ Enhance browser-based integration tests for the Parameter Admin interface
3. Implement additional error handling for authentication edge cases
4. Add redirect to previous page after successful login
5. Complete API documentation for all implemented endpoints
6. Add WebDriver setup documentation for developers
7. Integrate browser tests with CI/CD pipeline
8. Implement additional advanced Parameter Admin tests:
   - User parameter overrides
   - Parameter creation and deletion
   - Parameter validation
   - Edge case handling for large parameter sets
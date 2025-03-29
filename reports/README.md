# Test Reports

This directory contains test reports and related documentation for the Profiler4 project.

## System Health Dashboard Integration

- [System Health Dashboard Integration Report](system_health_dashboard_integration_report.md) - Comprehensive report on the System Health Dashboard API integration testing with details on test coverage, data structures, and browser UI integration.
- [System Health API Test Report](system_health_api_test_report_20250327_185344.txt) - Detailed results of running the system health API tests.

## API Integration Tests

- [API Consolidation Verification](api_consolidation_verification.md) - Verification report for the API consolidation efforts.
- [Parameter Usage Report](parameter_usage_report.html) - HTML report showing parameter usage across the application.

## Database Validation

- [Database Validation Report](database_validation_report_20250325_090512.html) - HTML report of database validation.
- [Goal Migration Report](goal_migration_report_20250325_085744.json) - JSON report of goal migration.

## Testing Browser-Based Components

### System Health Dashboard Test

The browser-based integration test for the System Health Dashboard can be run with:

```bash
python -m tests.api_fix.system_health_dashboard_test
```

This will:
1. Start a test Flask server on port 5556
2. Open a browser page with a test dashboard
3. Allow you to run automated tests for all dashboard features:
   - Current metrics display
   - Historical data visualization
   - Time range selection
   - Interval selection
   - Alert visualization
   - Auto-refresh functionality
   - Error handling

The tests validate the full integration between the frontend components and the backend API endpoints. They provide a comprehensive verification that all data needed by the UI components is properly provided by the API.

### Question Flow Test

The browser-based integration test for the Question Flow components can be run with:

```bash
python -m tests.api_fix.question_flow_integration_test
```

This launches a browser-based test environment for the Question Flow components, validating the interaction between the frontend components and the backend API.

## Running API Tests

To run the System Health API tests:

```bash
python -m tests.api_fix.system_health_api_test all
```

This will run the comprehensive test suite and generate a test report in this directory.

To run specific test cases:

```bash
python -m tests.api_fix.system_health_api_test [command]
```

Where command can be: current, history, history_ranges, interval_validation, error_handling, alerts, browser_integration, or all.

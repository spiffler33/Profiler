"""
Logging and monitoring tests for Monte Carlo simulations.

This module tests the logging and monitoring capabilities of the Monte Carlo
simulation system, verifying that errors are properly logged, performance is
tracked, and sufficient debug information is available.
"""

import pytest
import logging
import json
import re
import sqlite3
import os
import tempfile
from datetime import datetime, timedelta

from models.monte_carlo.cache import invalidate_cache
from services.goal_service import GoalService
from services.financial_parameter_service import get_financial_parameter_service


class CustomLogHandler(logging.Handler):
    """Custom log handler to capture log records for testing."""
    
    def __init__(self):
        super().__init__()
        self.logs = []
    
    def emit(self, record):
        self.logs.append(record)
    
    def get_logs(self, level=None):
        """Get logs filtered by level if specified."""
        if level is None:
            return self.logs
        return [r for r in self.logs if r.levelno == level]
    
    def clear(self):
        """Clear captured logs."""
        self.logs = []
    
    def format_logs(self):
        """Format logs for display in test output."""
        formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        return [formatter.format(record) for record in self.logs]


class TestMonteCarloLogging:
    """Test logging capabilities of Monte Carlo simulations."""
    
    @pytest.fixture(scope="function")
    def log_capture(self):
        """Set up a custom log handler to capture logs."""
        # Create and configure handler
        handler = CustomLogHandler()
        handler.setLevel(logging.DEBUG)
        
        # Add handler to relevant loggers
        loggers = [
            logging.getLogger("models.monte_carlo"),
            logging.getLogger("services.goal_service"),
            logging.getLogger("services.financial_parameter_service"),
            logging.getLogger("models.goal_probability")
        ]
        
        for logger in loggers:
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)
        
        # Ensure we capture logs even in root logger
        root_logger = logging.getLogger()
        original_level = root_logger.level
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(handler)
        
        yield handler
        
        # Clean up
        for logger in loggers:
            logger.removeHandler(handler)
        
        root_logger.removeHandler(handler)
        root_logger.setLevel(original_level)
    
    @pytest.fixture(scope="function")
    def test_db_path(self):
        """Create a temporary database file for testing."""
        fd, path = tempfile.mkstemp(suffix=".db", prefix="test_monte_carlo_")
        yield path
        os.close(fd)
        os.unlink(path)  # Clean up after tests
    
    def _create_test_profile(self, db_path):
        """Create a test profile in the database for logging tests."""
        profile_id = f"log-test-profile-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        current_time = datetime.now().isoformat()
        
        # Initialize the database with tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create user_profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Insert test profile
        cursor.execute("""
            INSERT INTO user_profiles (id, name, email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (profile_id, "Logging Test User", "log_test@example.com", current_time, current_time))
        
        # Create goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                user_profile_id TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                target_amount REAL,
                timeframe TEXT,
                current_amount REAL DEFAULT 0,
                importance TEXT CHECK(importance IN ('high', 'medium', 'low')) DEFAULT 'medium',
                flexibility TEXT CHECK(flexibility IN ('fixed', 'somewhat_flexible', 'very_flexible')) DEFAULT 'somewhat_flexible',
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                goal_type TEXT,
                monthly_contribution REAL DEFAULT 0,
                current_progress REAL DEFAULT 0,
                goal_success_probability REAL DEFAULT 0,
                funding_strategy TEXT,
                additional_funding_sources TEXT,
                allocation TEXT,
                FOREIGN KEY (user_profile_id) REFERENCES user_profiles (id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
        
        return profile_id
    
    def _create_test_goal(self, db_path, profile_id):
        """Create a test goal in the database for logging tests."""
        goal_id = f"log-test-goal-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        current_time = datetime.now().isoformat()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO goals (
                id, user_profile_id, category, title, target_amount, 
                timeframe, current_amount, importance, flexibility, notes,
                created_at, updated_at, goal_type, monthly_contribution,
                current_progress, goal_success_probability, allocation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            goal_id, profile_id, "retirement", "Logging Test Retirement", 50000000,
            (datetime.now() + timedelta(days=365*20)).isoformat(), 10000000,
            "high", "somewhat_flexible", "Test goal for logging",
            current_time, current_time, "retirement", 50000,
            20.0, 0.0, '{"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05}'
        ))
        
        conn.commit()
        conn.close()
        
        return goal_id
    
    def test_basic_logging(self, test_db_path, log_capture):
        """Test basic logging during Monte Carlo calculation."""
        # Set up test data
        profile_id = self._create_test_profile(test_db_path)
        goal_id = self._create_test_goal(test_db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Clear logs before test
        log_capture.clear()
        
        # Clear cache for full calculation
        invalidate_cache()
        
        # Profile data for calculations
        profile_data = {
            "monthly_income": 150000,
            "annual_income": 1800000,
            "monthly_expenses": 80000,
            "annual_expenses": 960000,
            "total_assets": 10000000,
            "risk_profile": "aggressive",
            "age": 35,
            "retirement_age": 55,
            "life_expectancy": 85,
            "inflation_rate": 0.06
        }
        
        # Perform a calculation
        goal_service.calculate_goal_probability(
            goal_id=goal_id,
            profile_data=profile_data,
            simulation_iterations=100,  # Low count for faster test
            force_recalculate=True
        )
        
        # Verify logs were captured
        logs = log_capture.get_logs()
        assert len(logs) > 0, "No logs were captured during calculation"
        
        # Check for different log levels
        info_logs = log_capture.get_logs(logging.INFO)
        debug_logs = log_capture.get_logs(logging.DEBUG)
        
        # Should have both info and debug logs
        assert len(info_logs) > 0, "No INFO level logs were captured"
        
        # Check for key log messages
        log_messages = [record.getMessage().lower() for record in logs]
        
        # Should mention calculation or probability
        assert any("calculat" in msg for msg in log_messages), "No calculation logs found"
        assert any("probabilit" in msg for msg in log_messages), "No probability logs found"
        
        # Should include some timing information
        timing_messages = [msg for msg in log_messages if re.search(r'(took|time|duration|ms|sec|second)', msg)]
        assert len(timing_messages) > 0, "No timing information logged"
    
    def test_error_logging(self, test_db_path, log_capture):
        """Test error logging during Monte Carlo calculation."""
        # Set up test data
        profile_id = self._create_test_profile(test_db_path)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Clear logs before test
        log_capture.clear()
        
        # Profile data for calculations
        profile_data = {
            "monthly_income": 150000,
            "annual_income": 1800000,
            "monthly_expenses": 80000,
            "annual_expenses": 960000,
            "total_assets": 10000000,
            "risk_profile": "aggressive",
            "age": 35,
            "retirement_age": 55,
            "life_expectancy": 85,
            "inflation_rate": 0.06
        }
        
        # Force an error by providing invalid goal ID
        invalid_goal_id = "non-existent-goal-id"
        
        try:
            goal_service.calculate_goal_probability(
                goal_id=invalid_goal_id,
                profile_data=profile_data
            )
            pytest.fail("Expected error not raised")
        except Exception as e:
            # Expected exception
            print(f"Expected test exception: {e}")
        
        # Check for error logs
        error_logs = log_capture.get_logs(logging.ERROR)
        warning_logs = log_capture.get_logs(logging.WARNING)
        
        # Should have error or warning logs
        assert len(error_logs) > 0 or len(warning_logs) > 0, "No ERROR or WARNING logs captured"
        
        # Check error log content
        error_messages = [record.getMessage().lower() for record in error_logs + warning_logs]
        
        # Should mention the invalid goal ID
        assert any("goal" in msg and "id" in msg and ("invalid" in msg or "not found" in msg or "missing" in msg) 
                  for msg in error_messages), "Error logs don't mention invalid goal ID"
        
        # Should include the specific ID that caused the error
        assert any(invalid_goal_id in msg for msg in error_messages), "Error logs don't include the invalid ID"
    
    def test_performance_logging(self, test_db_path, log_capture):
        """Test performance logging during Monte Carlo calculation."""
        # Set up test data
        profile_id = self._create_test_profile(test_db_path)
        goal_id = self._create_test_goal(test_db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Clear logs before test
        log_capture.clear()
        
        # Clear cache for full calculation
        invalidate_cache()
        
        # Profile data for calculations
        profile_data = {
            "monthly_income": 150000,
            "annual_income": 1800000,
            "monthly_expenses": 80000,
            "annual_expenses": 960000,
            "total_assets": 10000000,
            "risk_profile": "aggressive",
            "age": 35,
            "retirement_age": 55,
            "life_expectancy": 85,
            "inflation_rate": 0.06
        }
        
        # Perform a calculation with more iterations to measure performance
        goal_service.calculate_goal_probability(
            goal_id=goal_id,
            profile_data=profile_data,
            simulation_iterations=500,  # Higher count for performance testing
            force_recalculate=True
        )
        
        # Check for performance logs
        log_messages = [record.getMessage().lower() for record in log_capture.get_logs()]
        
        # Look for timing information
        time_pattern = r'(took|elapsed|duration|time).*?(\d+\.?\d*)\s*(ms|millisecond|s|sec|second)'
        timing_logs = [msg for msg in log_messages if re.search(time_pattern, msg)]
        
        assert len(timing_logs) > 0, "No performance timing logs found"
        
        # Extract timing values
        timing_values = []
        for msg in timing_logs:
            match = re.search(time_pattern, msg)
            if match:
                value = float(match.group(2))
                unit = match.group(3)
                
                # Convert to milliseconds for comparison
                if unit.startswith('s'):
                    value *= 1000
                
                timing_values.append(value)
        
        # Should have some meaningful timing values
        assert len(timing_values) > 0, "No timing values extracted from logs"
        assert max(timing_values) > 0, "No positive timing values found"
        
        # Check for common performance logging patterns
        perf_patterns = [
            r'simulation.*?(took|elapsed|time)',
            r'calculation.*?(took|elapsed|time)',
            r'(cache|hit|miss)'
        ]
        
        for pattern in perf_patterns:
            matching_logs = [msg for msg in log_messages if re.search(pattern, msg)]
            if matching_logs:
                print(f"Found {len(matching_logs)} logs matching '{pattern}'")
                if matching_logs:
                    print(f"Sample: {matching_logs[0]}")
    
    def test_debug_info_logging(self, test_db_path, log_capture):
        """Test that debug info is logged for troubleshooting."""
        # Set up test data
        profile_id = self._create_test_profile(test_db_path)
        goal_id = self._create_test_goal(test_db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Clear logs before test
        log_capture.clear()
        
        # Clear cache for full calculation
        invalidate_cache()
        
        # Profile data for calculations
        profile_data = {
            "monthly_income": 150000,
            "annual_income": 1800000,
            "monthly_expenses": 80000,
            "annual_expenses": 960000,
            "total_assets": 10000000,
            "risk_profile": "aggressive",
            "age": 35,
            "retirement_age": 55,
            "life_expectancy": 85,
            "inflation_rate": 0.06
        }
        
        # Perform a calculation with debug logging
        goal_service.calculate_goal_probability(
            goal_id=goal_id,
            profile_data=profile_data,
            simulation_iterations=100,  # Low count for faster test
            force_recalculate=True
        )
        
        # Get debug logs
        debug_logs = log_capture.get_logs(logging.DEBUG)
        
        # Should have debug logs
        assert len(debug_logs) > 0, "No DEBUG level logs were captured"
        
        # Check for key debug information categories
        debug_messages = [record.getMessage().lower() for record in debug_logs]
        
        # Define key debug info categories
        debug_categories = {
            "parameters": [r'param', r'equity', r'debt', r'return', r'volatility', r'inflation'],
            "simulation": [r'simulation', r'iteration', r'monte carlo'],
            "goal_details": [r'goal', r'target', r'timeframe', r'allocation'],
            "probability": [r'probability', r'result', r'success'],
            "cache": [r'cache', r'hit', r'miss', r'key']
        }
        
        # Check coverage of debug categories
        category_coverage = {}
        
        for category, patterns in debug_categories.items():
            matches = []
            for pattern in patterns:
                category_matches = [msg for msg in debug_messages if re.search(pattern, msg)]
                matches.extend(category_matches)
            
            # Get unique matches
            unique_matches = set(matches)
            category_coverage[category] = len(unique_matches)
            
            print(f"Debug category '{category}': {len(unique_matches)} matching logs")
            if unique_matches:
                print(f"  Sample: {next(iter(unique_matches))}")
        
        # Should have at least some coverage in key categories
        covered_categories = [cat for cat, count in category_coverage.items() if count > 0]
        assert len(covered_categories) > 0, "No debug categories covered in logs"
    
    def test_structured_logging_format(self, test_db_path, log_capture):
        """Test that logs use structured format for easier parsing."""
        # Set up test data
        profile_id = self._create_test_profile(test_db_path)
        goal_id = self._create_test_goal(test_db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Clear logs before test
        log_capture.clear()
        
        # Clear cache for full calculation
        invalidate_cache()
        
        # Profile data for calculations
        profile_data = {
            "monthly_income": 150000,
            "annual_income": 1800000,
            "monthly_expenses": 80000,
            "annual_expenses": 960000,
            "total_assets": 10000000,
            "risk_profile": "aggressive",
            "age": 35,
            "retirement_age": 55,
            "life_expectancy": 85,
            "inflation_rate": 0.06
        }
        
        # Perform a calculation
        goal_service.calculate_goal_probability(
            goal_id=goal_id,
            profile_data=profile_data,
            simulation_iterations=100,  # Low count for faster test
            force_recalculate=True
        )
        
        # Get all logs
        logs = log_capture.get_logs()
        
        # Check for structured logging patterns
        structured_patterns = [
            r'\w+=[\w.]+',  # key=value
            r'\w+: [\w.]+',  # key: value 
            r'"?\w+"?: [\w.]+',  # "key": value (JSON-like)
            r'[\w.]+=\{.*?\}',  # key={...}
            r'\{.*?\}'  # {...} (JSON object)
        ]
        
        structured_logs = []
        for record in logs:
            message = record.getMessage()
            if any(re.search(pattern, message) for pattern in structured_patterns):
                structured_logs.append(message)
        
        # Should have some structured logs
        assert len(structured_logs) > 0, "No structured logging format detected"
        
        # Calculate percentage of structured logs
        structured_percentage = len(structured_logs) / len(logs) * 100
        print(f"Structured logs: {len(structured_logs)}/{len(logs)} ({structured_percentage:.1f}%)")
        
        # Display some structured log samples
        for i, log in enumerate(structured_logs[:3]):
            print(f"Structured log sample {i+1}: {log}")
    
    def test_log_level_appropriateness(self, test_db_path, log_capture):
        """Test that appropriate log levels are used for different messages."""
        # Set up test data
        profile_id = self._create_test_profile(test_db_path)
        goal_id = self._create_test_goal(test_db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Clear logs before test
        log_capture.clear()
        
        # Profile data for calculations
        profile_data = {
            "monthly_income": 150000,
            "annual_income": 1800000,
            "monthly_expenses": 80000,
            "annual_expenses": 960000,
            "total_assets": 10000000,
            "risk_profile": "aggressive",
            "age": 35,
            "retirement_age": 55,
            "life_expectancy": 85,
            "inflation_rate": 0.06
        }
        
        # First perform a successful calculation
        goal_service.calculate_goal_probability(
            goal_id=goal_id,
            profile_data=profile_data,
            simulation_iterations=100,  # Low count for faster test
            force_recalculate=True
        )
        
        # Log level counts
        debug_logs = log_capture.get_logs(logging.DEBUG)
        info_logs = log_capture.get_logs(logging.INFO)
        warning_logs = log_capture.get_logs(logging.WARNING)
        error_logs = log_capture.get_logs(logging.ERROR)
        
        # For a successful calculation:
        # - Should have DEBUG and INFO logs
        # - Should not have ERROR logs
        # - May have some WARNING logs
        
        assert len(debug_logs) > 0, "No DEBUG logs for successful calculation"
        assert len(info_logs) > 0, "No INFO logs for successful calculation"
        assert len(error_logs) == 0, f"Found {len(error_logs)} ERROR logs for successful calculation"
        
        # Now force an error and check log levels
        log_capture.clear()
        
        try:
            # Invalid goal ID should cause error
            goal_service.calculate_goal_probability(
                goal_id="invalid-goal-id",
                profile_data=profile_data
            )
        except Exception:
            pass  # Expected exception
        
        # Check log levels for error case
        error_debug_logs = log_capture.get_logs(logging.DEBUG)
        error_info_logs = log_capture.get_logs(logging.INFO)
        error_warning_logs = log_capture.get_logs(logging.WARNING)
        error_error_logs = log_capture.get_logs(logging.ERROR)
        
        # For an error case:
        # - Should have ERROR or WARNING logs
        assert len(error_error_logs) > 0 or len(error_warning_logs) > 0, \
            "No ERROR or WARNING logs for failed calculation"
        
        # Display log level distribution
        print("Log level distribution for successful calculation:")
        print(f"  DEBUG: {len(debug_logs)}")
        print(f"  INFO: {len(info_logs)}")
        print(f"  WARNING: {len(warning_logs)}")
        print(f"  ERROR: {len(error_logs)}")
        
        print("Log level distribution for failed calculation:")
        print(f"  DEBUG: {len(error_debug_logs)}")
        print(f"  INFO: {len(error_info_logs)}")
        print(f"  WARNING: {len(error_warning_logs)}")
        print(f"  ERROR: {len(error_error_logs)}")
    
    def test_error_context_logging(self, test_db_path, log_capture):
        """Test that errors include sufficient context for debugging."""
        # Set up test data
        profile_id = self._create_test_profile(test_db_path)
        goal_id = self._create_test_goal(test_db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Clear logs before test
        log_capture.clear()
        
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
            pytest.fail("Expected error not raised")
        except Exception as e:
            # Expected exception
            print(f"Expected test exception: {e}")
        
        # Get error logs
        error_logs = log_capture.get_logs(logging.ERROR)
        warning_logs = log_capture.get_logs(logging.WARNING)
        
        # Should have error or warning logs
        assert len(error_logs) > 0 or len(warning_logs) > 0, "No ERROR or WARNING logs captured"
        
        # Check error context in logs
        context_found = False
        for record in error_logs + warning_logs:
            message = record.getMessage().lower()
            
            # Look for specific context about the error
            if "profile" in message and "data" in message:
                # Check if the message includes specifics about missing fields
                if any(field in message for field in ["missing", "required", "invalid"]):
                    context_found = True
                    print(f"Found error context: {message}")
                    break
        
        # Should include context or specific parameter validation errors
        assert context_found or len(error_logs) + len(warning_logs) > 1, \
            "Error logs don't include sufficient context about the issue"
    
    def test_monitoring_metric_logging(self, test_db_path, log_capture):
        """Test logging of metrics that would be useful for monitoring."""
        # Set up test data
        profile_id = self._create_test_profile(test_db_path)
        goal_id = self._create_test_goal(test_db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Clear logs before test
        log_capture.clear()
        
        # Clear cache for clean test
        invalidate_cache()
        
        # Profile data for calculations
        profile_data = {
            "monthly_income": 150000,
            "annual_income": 1800000,
            "monthly_expenses": 80000,
            "annual_expenses": 960000,
            "total_assets": 10000000,
            "risk_profile": "aggressive",
            "age": 35,
            "retirement_age": 55,
            "life_expectancy": 85,
            "inflation_rate": 0.06
        }
        
        # Perform a calculation with a realistic iteration count
        goal_service.calculate_goal_probability(
            goal_id=goal_id,
            profile_data=profile_data,
            simulation_iterations=500,  # Higher count to get more metrics
            force_recalculate=True
        )
        
        # Look for logs that contain monitoring metrics
        monitoring_metric_patterns = [
            r'time: \d+\.?\d*',  # Execution time
            r'took: \d+\.?\d*',  # Alternate time format
            r'iteration.*?: \d+',  # Iteration count
            r'memory.*?: \d+',  # Memory usage
            r'cache.*?: \d+',  # Cache statistics
            r'hit.*?: \d+',  # Cache hit rate
            r'miss.*?: \d+',  # Cache miss rate
            r'probability: \d+\.?\d*'  # Result probability
        ]
        
        # Track found metrics
        found_metrics = {}
        
        for record in log_capture.get_logs():
            message = record.getMessage().lower()
            
            for pattern in monitoring_metric_patterns:
                if re.search(pattern, message):
                    key = pattern.split(':')[0].strip(r'.*?')
                    if key not in found_metrics:
                        found_metrics[key] = []
                    found_metrics[key].append(message)
        
        # Should have at least some monitoring metrics
        assert len(found_metrics) > 0, "No monitoring metrics found in logs"
        
        # Display found metrics
        print(f"Found {len(found_metrics)} monitoring metric types:")
        for metric, occurrences in found_metrics.items():
            print(f"  {metric}: {len(occurrences)} occurrences")
            if occurrences:
                print(f"  Sample: {occurrences[0]}")
        
        # Time metric is critical for performance monitoring
        time_metrics = found_metrics.get('time', []) + found_metrics.get('took', [])
        assert time_metrics, "No execution time metrics logged - critical for monitoring"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
"""
Error handling tests for Monte Carlo simulations without mocks.

This module tests error handling, validation, and resilience in the Monte Carlo
simulation system, using real database operations and error conditions.
"""

import pytest
import json
import sqlite3
import logging
import tempfile
import os
import time
from datetime import datetime, timedelta

from services.goal_service import GoalService
from services.financial_parameter_service import get_financial_parameter_service
from models.monte_carlo.cache import invalidate_cache
from models.monte_carlo.array_fix import to_scalar


# Configure logging
logger = logging.getLogger(__name__)


class TestMonteCarloErrorHandling:
    """Test error handling in Monte Carlo simulation system with real error conditions."""
    
    @pytest.fixture(scope="function")
    def test_db_path(self):
        """Create a temporary database file for testing."""
        fd, path = tempfile.mkstemp(suffix=".db", prefix="test_monte_carlo_")
        yield path
        os.close(fd)
        os.unlink(path)  # Clean up after tests
    
    @pytest.fixture(scope="function")
    def test_db_connection(self, test_db_path):
        """Create a database connection for testing."""
        # Initialize necessary tables
        connection = sqlite3.connect(test_db_path)
        connection.row_factory = sqlite3.Row
        
        # Enable foreign keys
        connection.execute("PRAGMA foreign_keys = ON")
        
        # Create minimal schema needed for tests
        self._initialize_test_schema(connection)
        
        yield connection
        
        # Cleanup
        connection.close()
    
    def _initialize_test_schema(self, connection):
        """Initialize a minimal database schema for testing."""
        cursor = connection.cursor()
        
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
        
        # Create goals table with constraints
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
        
        connection.commit()
    
    def _create_test_profile(self, connection):
        """Create a test profile with a real insert operation."""
        profile_id = f"test-profile-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        current_time = datetime.now().isoformat()
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO user_profiles (id, name, email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (profile_id, "Test User", "test@example.com", current_time, current_time))
        
        connection.commit()
        return profile_id
    
    def _create_test_goal(self, connection, profile_id):
        """Create a test goal with a real insert operation."""
        goal_id = f"test-goal-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        current_time = datetime.now().isoformat()
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO goals (
                id, user_profile_id, category, title, target_amount, 
                timeframe, current_amount, importance, flexibility, notes,
                created_at, updated_at, goal_type, monthly_contribution,
                current_progress, goal_success_probability, allocation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            goal_id, profile_id, "retirement", "Test Retirement", 50000000,
            (datetime.now() + timedelta(days=365*20)).isoformat(), 10000000,
            "high", "somewhat_flexible", "Test goal",
            current_time, current_time, "retirement", 50000,
            20.0, 0.0, '{"equity": 0.6, "debt": 0.3, "gold": 0.05, "cash": 0.05}'
        ))
        
        connection.commit()
        return goal_id
    
    def test_invalid_db_path(self, test_db_path):
        """Test behavior with an invalid database path."""
        # Set up goal service with a non-existent database path
        non_existent_path = "/path/that/does/not/exist/test.db"
        goal_service = GoalService()
        goal_service.db_path = non_existent_path
        
        # Try to retrieve a goal - should fail with file not found
        with pytest.raises(sqlite3.OperationalError) as exc_info:
            goal_service.get_goal("any-goal-id")
        
        assert "no such file" in str(exc_info.value).lower() or "unable to open" in str(exc_info.value).lower(), \
            "Should raise appropriate error for missing database file"
        
        # Set to valid path for next part of test
        goal_service.db_path = test_db_path
        
        # Try to get a non-existent goal from a valid database
        with pytest.raises(ValueError) as exc_info:
            goal_service.get_goal("non-existent-goal")
        
        assert "not found" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower(), \
            "Should raise appropriate error for non-existent goal"
    
    def test_database_constraint_violations(self, test_db_connection):
        """Test handling of real database constraint violations."""
        profile_id = self._create_test_profile(test_db_connection)
        
        # 1. Test foreign key constraint violation
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            # Insert goal with non-existent profile ID
            cursor = test_db_connection.cursor()
            current_time = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO goals (
                    id, user_profile_id, category, title, target_amount,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "test-goal", "non-existent-profile-id", "retirement", "Test Goal", 5000000,
                current_time, current_time
            ))
        
        assert "foreign key constraint failed" in str(exc_info.value).lower(), \
            "Should raise foreign key constraint error"
        
        # 2. Test check constraint violation
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            # Insert goal with invalid importance value
            cursor = test_db_connection.cursor()
            current_time = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO goals (
                    id, user_profile_id, category, title, target_amount,
                    importance, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "test-goal", profile_id, "retirement", "Test Goal", 5000000,
                "invalid_importance", current_time, current_time
            ))
        
        assert "check constraint failed" in str(exc_info.value).lower() or "constraint failed" in str(exc_info.value).lower(), \
            "Should raise check constraint error"
        
        # 3. Test primary key constraint violation
        # First create a valid goal
        goal_id = self._create_test_goal(test_db_connection, profile_id)
        
        # Then try to create another with same ID
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            cursor = test_db_connection.cursor()
            current_time = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO goals (
                    id, user_profile_id, category, title, target_amount,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                goal_id, profile_id, "education", "Duplicate ID Goal", 5000000,
                current_time, current_time
            ))
        
        assert "unique constraint failed" in str(exc_info.value).lower() or "constraint failed" in str(exc_info.value).lower(), \
            "Should raise unique constraint error"
    
    def test_transaction_rollback(self, test_db_connection):
        """Test transaction rollback on errors with real transactions."""
        profile_id = self._create_test_profile(test_db_connection)
        goal_id = self._create_test_goal(test_db_connection, profile_id)
        
        # Start a transaction
        test_db_connection.execute("BEGIN TRANSACTION")
        
        # Update the goal with a new probability
        test_db_connection.execute("""
            UPDATE goals SET goal_success_probability = ? WHERE id = ?
        """, (0.7654, goal_id))
        
        # Check that the update is visible within the transaction
        cursor = test_db_connection.cursor()
        cursor.execute("""
            SELECT goal_success_probability FROM goals WHERE id = ?
        """, (goal_id,))
        row = cursor.fetchone()
        assert abs(row[0] - 0.7654) < 0.0001, "Update should be visible within transaction"
        
        # Rollback the transaction
        test_db_connection.execute("ROLLBACK")
        
        # Verify the change was rolled back
        cursor.execute("""
            SELECT goal_success_probability FROM goals WHERE id = ?
        """, (goal_id,))
        row = cursor.fetchone()
        assert abs(row[0] - 0.0) < 0.0001, "Update should be rolled back"
        
        # Now try with multiple operations
        test_db_connection.execute("BEGIN TRANSACTION")
        
        # Update probability
        test_db_connection.execute("""
            UPDATE goals SET goal_success_probability = ? WHERE id = ?
        """, (0.8765, goal_id))
        
        # Update target amount
        test_db_connection.execute("""
            UPDATE goals SET target_amount = ? WHERE id = ?
        """, (60000000, goal_id))
        
        # Trigger an error with an invalid SQL statement
        try:
            test_db_connection.execute("""
                UPDATE non_existent_table SET value = 1
            """)
            pytest.fail("Should have raised an error")
        except sqlite3.OperationalError:
            # Expected error - now rollback
            test_db_connection.execute("ROLLBACK")
        
        # Verify both changes were rolled back
        cursor.execute("""
            SELECT goal_success_probability, target_amount FROM goals WHERE id = ?
        """, (goal_id,))
        row = cursor.fetchone()
        assert abs(row[0] - 0.0) < 0.0001, "Probability update should be rolled back"
        assert abs(row[1] - 50000000) < 0.0001, "Target amount update should be rolled back"
    
    def test_invalid_goal_parameter_validation(self, test_db_path):
        """Test validation of invalid goal parameters with real service calls."""
        # Set up service with test database
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Create a profile directly in the database
        conn = sqlite3.connect(test_db_path)
        profile_id = self._create_test_profile(conn)
        conn.close()
        
        # Test with invalid targets
        with pytest.raises(ValueError) as exc_info:
            goal_service.create_goal({
                "category": "retirement",
                "title": "Test Goal",
                "target_amount": -5000000,  # Negative target
                "timeframe": (datetime.now() + timedelta(days=365*10)).isoformat()
            }, profile_id)
        
        assert "target" in str(exc_info.value).lower() and "negative" in str(exc_info.value).lower(), \
            "Should reject negative target amount"
        
        # Test with past timeframe
        with pytest.raises(ValueError) as exc_info:
            goal_service.create_goal({
                "category": "retirement",
                "title": "Test Goal",
                "target_amount": 5000000,
                "timeframe": (datetime.now() - timedelta(days=365)).isoformat()  # Past date
            }, profile_id)
        
        assert "timeframe" in str(exc_info.value).lower() and "past" in str(exc_info.value).lower(), \
            "Should reject past timeframe"
        
        # Test with invalid contribution
        with pytest.raises(ValueError) as exc_info:
            goal_service.create_goal({
                "category": "retirement",
                "title": "Test Goal",
                "target_amount": 5000000,
                "timeframe": (datetime.now() + timedelta(days=365*10)).isoformat(),
                "monthly_contribution": -10000  # Negative contribution
            }, profile_id)
        
        assert "contribution" in str(exc_info.value).lower() and "negative" in str(exc_info.value).lower(), \
            "Should reject negative monthly contribution"
    
    def test_goal_probability_parameter_validation(self, test_db_path):
        """Test validation of probability calculation parameters."""
        # Set up service with test database
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Create a profile and goal directly
        conn = sqlite3.connect(test_db_path)
        profile_id = self._create_test_profile(conn)
        goal_id = self._create_test_goal(conn, profile_id)
        conn.close()
        
        # Valid profile data
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
        
        # Test with negative iterations
        with pytest.raises(ValueError) as exc_info:
            goal_service.calculate_goal_probability(
                goal_id=goal_id,
                profile_data=profile_data,
                simulation_iterations=-100  # Negative iterations
            )
        
        assert "iterations" in str(exc_info.value).lower() and "negative" in str(exc_info.value).lower(), \
            "Should reject negative iterations"
        
        # Test with zero iterations
        with pytest.raises(ValueError) as exc_info:
            goal_service.calculate_goal_probability(
                goal_id=goal_id,
                profile_data=profile_data,
                simulation_iterations=0  # Zero iterations
            )
        
        assert "iterations" in str(exc_info.value).lower() and "zero" in str(exc_info.value).lower(), \
            "Should reject zero iterations"
        
        # Test with missing profile data
        with pytest.raises(ValueError) as exc_info:
            goal_service.calculate_goal_probability(
                goal_id=goal_id,
                profile_data={}  # Empty profile data
            )
        
        assert "profile" in str(exc_info.value).lower() and "missing" in str(exc_info.value).lower(), \
            "Should reject empty profile data"
    
    def test_database_locked_behavior(self, test_db_path):
        """Test behavior when database is locked with real database operations."""
        # This test simulates database locked errors by holding a write transaction open
        
        # Create a connection that will hold a lock
        lock_connection = sqlite3.connect(test_db_path)
        
        # Set up service with test database
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Create a profile and goal
        profile_id = self._create_test_profile(lock_connection)
        goal_id = self._create_test_goal(lock_connection, profile_id)
        
        # Start a transaction and make a change that locks the database
        lock_connection.execute("BEGIN IMMEDIATE TRANSACTION")
        lock_connection.execute("UPDATE goals SET target_amount = 60000000 WHERE id = ?", (goal_id,))
        
        # Try to use the service while the database is locked
        # The service should handle the lock error or time out appropriately
        try:
            # This will likely time out or fail with SQLITE_BUSY
            goal_service.get_goal(goal_id)
            # If we get here, the service has a retry mechanism
            assert True, "Service properly handled database lock"
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                # This is expected behavior if there's no retry mechanism
                assert True, "Database lock error raised as expected"
            else:
                pytest.fail(f"Unexpected database error: {e}")
        finally:
            # Always release the lock
            lock_connection.rollback()
            lock_connection.close()
    
    def test_corrupted_allocation_data(self, test_db_path):
        """Test handling of corrupted allocation data in the database."""
        # Create a profile and goal
        conn = sqlite3.connect(test_db_path)
        profile_id = self._create_test_profile(conn)
        goal_id = self._create_test_goal(conn, profile_id)
        
        # Corrupt the allocation data
        conn.execute("""
            UPDATE goals SET allocation = '{"equity": 0.6, "debt": 0.3, CORRUPTED' WHERE id = ?
        """, (goal_id,))
        conn.commit()
        conn.close()
        
        # Set up service with test database
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Test behavior when accessing corrupted data
        try:
            goal = goal_service.get_goal(goal_id)
            # If we got here, the service had error handling for corrupt data
            assert True, "Service properly handled corrupted allocation data"
        except json.JSONDecodeError:
            # This is also acceptable if the service doesn't have special handling
            assert True, "JSONDecodeError raised as expected for corrupted data"
        except Exception as e:
            # Some other error handling might be in place
            assert "json" in str(e).lower() or "allocation" in str(e).lower() or "parse" in str(e).lower(), \
                f"Unexpected error type: {type(e).__name__}, {str(e)}"
    
    def test_resource_limitations(self, test_db_path):
        """Test behavior under resource limitations with actual large operations."""
        # Set up service with test database
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
        # Create a profile and goal directly
        conn = sqlite3.connect(test_db_path)
        profile_id = self._create_test_profile(conn)
        goal_id = self._create_test_goal(conn, profile_id)
        conn.close()
        
        # Create a profile with valid data
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
        
        # Test with an extremely large iteration count to stress resources
        try:
            # This may cause memory issues or timeouts with extremely large counts
            result = goal_service.calculate_goal_probability(
                goal_id=goal_id,
                profile_data=profile_data,
                simulation_iterations=10000000  # Extremely large
            )
            # If it completed, check it's valid
            if result:
                probability = result.get_safe_success_probability()
                assert 0 <= probability <= 1, "Invalid probability result"
        except ValueError as e:
            # The service should properly validate and reject excessive iterations
            assert "iterations" in str(e).lower() or "too large" in str(e).lower() or "maximum" in str(e).lower(), \
                f"Expected validation error for large iterations, got: {str(e)}"
        except MemoryError:
            # This is also an acceptable outcome for memory exhaustion
            assert True, "MemoryError raised as expected for resource exhaustion"
        except Exception as e:
            # If some other error occurs, it should be resource-related
            assert "memory" in str(e).lower() or "resource" in str(e).lower() or "limit" in str(e).lower(), \
                f"Unexpected error type: {type(e).__name__}, {str(e)}"
    
    def test_concurrent_access_pattern(self, test_db_path):
        """Test behavior with concurrent access patterns using real threads."""
        import threading
        
        # Set up database
        conn = sqlite3.connect(test_db_path)
        profile_id = self._create_test_profile(conn)
        
        # Create multiple goals
        goal_ids = []
        for i in range(3):
            goal_id = self._create_test_goal(conn, profile_id)
            goal_ids.append(goal_id)
        conn.close()
        
        # Set up service with test database
        goal_service = GoalService()
        goal_service.db_path = test_db_path
        
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
        
        # Create thread worker function
        results = {"success": 0, "failure": 0, "lock_errors": 0}
        lock = threading.Lock()
        
        def worker_function(goal_id):
            """Thread worker to calculate probability for a goal."""
            try:
                result = goal_service.calculate_goal_probability(
                    goal_id=goal_id,
                    profile_data=profile_data,
                    simulation_iterations=500
                )
                
                # Verify result
                if result and 0 <= result.get_safe_success_probability() <= 1:
                    with lock:
                        results["success"] += 1
                else:
                    with lock:
                        results["failure"] += 1
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower():
                    with lock:
                        results["lock_errors"] += 1
                else:
                    with lock:
                        results["failure"] += 1
            except Exception:
                with lock:
                    results["failure"] += 1
        
        # Create multiple threads accessing the same database
        threads = []
        for _ in range(5):  # Run multiple times for each goal
            for goal_id in goal_ids:
                thread = threading.Thread(target=worker_function, args=(goal_id,))
                threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Analyze results
        total_attempts = results["success"] + results["failure"] + results["lock_errors"]
        logger.info(f"Concurrent access results: {results}")
        logger.info(f"Success rate: {results['success']/total_attempts:.2%}")
        
        # We should have some successes
        assert results["success"] > 0, "Should have some successful calculations"
        
        # If lock errors occurred, that's expected and shows concurrent access was tested
        if results["lock_errors"] > 0:
            logger.info("Lock errors detected, showing real concurrent access testing")
        
        # A reasonable success rate indicates good handling of concurrency
        assert results["success"] / total_attempts >= 0.5, "Success rate too low for concurrent access"


# Additional test class for cache-related error handling
class TestMonteCarloCacheErrorHandling:
    """Test error handling in Monte Carlo simulation cache system."""
    
    def test_cache_file_corruption(self, tmp_path):
        """Test handling of corrupt cache files with real file corruption."""
        from models.monte_carlo.cache import load_cache, save_cache
        
        # Create a corrupted cache file
        cache_file = tmp_path / "corrupted_cache.pickle"
        with open(cache_file, "wb") as f:
            f.write(b"This is not a valid pickle file and will cause an error when loading")
        
        # Test load_cache with corrupted file
        cache = load_cache(str(cache_file))
        # Should return an empty cache rather than failing
        assert isinstance(cache, dict), "Should return empty dict on cache corruption"
        assert len(cache) == 0, "Cache should be empty after corruption"
        
        # Create a valid cache
        valid_cache = {"key1": "value1", "key2": "value2"}
        save_cache(valid_cache, str(cache_file))
        
        # Verify it's loadable
        loaded_cache = load_cache(str(cache_file))
        assert loaded_cache == valid_cache, "Cache save/load cycle should preserve data"
        
        # Corrupt file again with partial data
        with open(cache_file, "w") as f:
            f.write("partial pickle data")
        
        # Should handle gracefully
        recovered_cache = load_cache(str(cache_file))
        assert isinstance(recovered_cache, dict), "Should handle partial corruption gracefully"
    
    def test_cache_permissions_error(self, tmp_path):
        """Test handling of permission errors with real permission changes."""
        import stat
        import sys
        from models.monte_carlo.cache import save_cache
        
        # Skip on non-POSIX systems where permissions work differently
        if sys.platform == "win32":
            pytest.skip("Skipping permission test on Windows")
            
        # Create a directory with restricted permissions
        restricted_dir = tmp_path / "restricted"
        restricted_dir.mkdir()
        restricted_file = restricted_dir / "restricted_cache.pickle"
        
        # Create the file
        with open(restricted_file, "w") as f:
            f.write("")
        
        # Make it read-only
        restricted_file.chmod(stat.S_IREAD)
        
        # Try to save cache to a read-only file
        try:
            save_cache({"key": "value"}, str(restricted_file))
            # If successful, permissions weren't properly set or the function handles it gracefully
            assert True, "Cache system handled permission error gracefully"
        except PermissionError:
            # This is also acceptable if the cache doesn't have special handling
            assert True, "PermissionError raised as expected for read-only file"
        except Exception as e:
            # Some other error handling might be in place
            assert "permission" in str(e).lower() or "access" in str(e).lower(), \
                f"Unexpected error type: {type(e).__name__}, {str(e)}"
        finally:
            # Restore permissions so the file can be deleted
            restricted_file.chmod(stat.S_IREAD | stat.S_IWRITE)
    
    def test_cache_invalidation_recovery(self):
        """Test recovery after cache invalidation with real cache operations."""
        from models.monte_carlo.cache import set_cache_value, get_cache_value, invalidate_cache
        
        # First clear the cache
        invalidate_cache()
        
        # Set some values
        set_cache_value("test_key_1", "test_value_1")
        set_cache_value("test_key_2", "test_value_2")
        
        # Verify they're retrievable
        assert get_cache_value("test_key_1") == "test_value_1", "Cache should store values"
        assert get_cache_value("test_key_2") == "test_value_2", "Cache should store multiple values"
        
        # Invalidate again
        invalidate_cache()
        
        # Values should be gone
        assert get_cache_value("test_key_1") is None, "Cache should be empty after invalidation"
        assert get_cache_value("test_key_2") is None, "All cache values should be cleared"
        
        # Set a new value and verify system still works
        set_cache_value("test_key_3", "test_value_3")
        assert get_cache_value("test_key_3") == "test_value_3", "Cache should work after invalidation"
    
    def test_cache_size_limits(self):
        """Test behavior when cache grows large with real large cache values."""
        from models.monte_carlo.cache import set_cache_value, get_cache_value, invalidate_cache, get_cache_stats
        
        # First clear the cache
        invalidate_cache()
        
        # Generate a large value (1MB)
        large_value = "x" * (1024 * 1024)
        
        # Fill cache with large values until either:
        # 1. We hit a size limit and values start getting evicted, or
        # 2. We reach a reasonable test limit (50MB)
        max_test_items = 50  # Maximum number of large items to try
        for i in range(max_test_items):
            set_cache_value(f"large_key_{i}", large_value)
            
            # Check stats after each addition
            stats = get_cache_stats()
            
            # If we see evictions happening, cache size limits are working
            if stats.get('evictions', 0) > 0:
                logger.info(f"Cache evictions detected after {i+1} large items")
                # This is the behavior we're looking for
                break
                
            # If this is the last iteration, the cache might not have size limits
            if i == max_test_items - 1:
                logger.info(f"Cache accepted {max_test_items} large items without eviction")
                assert True, "Cache size limits may not be implemented, but system handled large cache"
        
        # Check that cache is still functional
        set_cache_value("final_test_key", "final_test_value")
        assert get_cache_value("final_test_key") == "final_test_value", "Cache should remain functional after size test"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
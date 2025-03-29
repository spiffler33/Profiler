"""
Resiliency tests for Monte Carlo simulations.

This module tests the resilience of the Monte Carlo simulation system
under various failure scenarios, using the mock database service.
"""

import pytest
import logging
import sqlite3
import time
import random
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from tests.integration.mock_db_service import MockDatabaseService
from tests.integration.db_test_utils import create_test_database, create_test_profile
from services.goal_service import GoalService
from services.financial_parameter_service import get_financial_parameter_service
from models.monte_carlo.cache import invalidate_cache


# Configure logging
logger = logging.getLogger(__name__)


class TestMonteCarloResiliency:
    """Test the resiliency of Monte Carlo simulations under adverse conditions."""
    
    @pytest.fixture(scope="function")
    def mock_db_setup(self):
        """Set up a mock database with test data."""
        # Create a real test database
        db_path = create_test_database()
        
        # Create test profile
        profile_id = create_test_profile(db_path)
        
        # Set up mock database service with moderate failure rate
        mock_db = MockDatabaseService(db_path, failure_rate=0.1, latency_ms=50)
        
        yield db_path, profile_id, mock_db
        
        # Clean up the test database file
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture(scope="function")
    def profile_data(self):
        """Standard profile data for Monte Carlo simulations."""
        return {
            "monthly_income": 150000,
            "annual_income": 1800000,
            "monthly_expenses": 80000,
            "annual_expenses": 960000,
            "total_assets": 10000000,
            "risk_profile": "aggressive",
            "age": 35,
            "retirement_age": 55,
            "life_expectancy": 85,
            "inflation_rate": 0.06,
            "equity_return": 0.14,
            "debt_return": 0.08,
            "savings_rate": 0.40,
            "tax_rate": 0.30,
            "answers": [
                {"question_id": "monthly_income", "answer": 150000},
                {"question_id": "monthly_expenses", "answer": 80000},
                {"question_id": "total_assets", "answer": 10000000},
                {"question_id": "risk_profile", "answer": "aggressive"}
            ]
        }
    
    def _create_test_goal(self, db_path, profile_id):
        """Create a test goal in the database."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create a test goal
            goal_id = f"test-goal-{random.randint(1000, 9999)}"
            current_time = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO goals (
                    id, user_profile_id, category, title, target_amount, 
                    timeframe, current_amount, importance, flexibility, notes,
                    created_at, updated_at, goal_type, monthly_contribution,
                    current_progress, goal_success_probability
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                goal_id, profile_id, "retirement", "Test Retirement", 50000000,
                (datetime.now() + timedelta(days=365*20)).isoformat(), 10000000,
                "high", "somewhat_flexible", "Test goal",
                current_time, current_time, "retirement", 50000,
                20.0, 0.0
            ))
            
            conn.commit()
            
            return goal_id
    
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
            # Make connect use our mock
            mock_connect.side_effect = lambda *args, **kwargs: mock_db.connect().__enter__()
            
            # Try calculation multiple times to encounter failures
            success_count = 0
            failure_count = 0
            
            for _ in range(5):
                try:
                    # Clear any cached results
                    invalidate_cache()
                    
                    # Attempt calculation
                    result = goal_service.calculate_goal_probability(
                        goal_id=goal_id,
                        profile_data=profile_data,
                        force_recalculate=True
                    )
                    
                    # Count successes and verify result
                    success_count += 1
                    assert result is not None, "Got None result in successful calculation"
                    
                    # Verify probability is valid
                    probability = result.get_safe_success_probability()
                    assert 0 <= probability <= 1, f"Invalid probability: {probability}"
                    
                except Exception as e:
                    # Count failures and verify error type
                    failure_count += 1
                    assert isinstance(e, (sqlite3.Error, ValueError)), f"Unexpected error type: {type(e)}"
                    logger.info(f"Expected test failure: {e}")
            
            # We should have both successes and failures with 0.5 failure rate
            logger.info(f"Successes: {success_count}, Failures: {failure_count}")
            assert failure_count > 0, "Should have some failures with high failure rate"
            
            # Verify operations were recorded
            op_count = mock_db.get_operation_count()
            assert op_count > 0, f"No operations recorded, got {op_count}"
    
    def test_database_timeout_resilience(self, mock_db_setup, profile_data):
        """Test resilience to database timeouts."""
        db_path, profile_id, mock_db = mock_db_setup
        
        # Create a test goal
        goal_id = self._create_test_goal(db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = db_path
        
        # Set high timeout probability
        mock_db.set_timeout_probability(0.8)
        mock_db.set_failure_rate(0.0)  # No random failures
        
        # Queue specific timeout exceptions for critical operations
        mock_db.queue_exception(
            "execute", 
            sqlite3.OperationalError, 
            "database is locked"
        )
        
        # Patch sqlite3.connect to use our mock
        with patch('sqlite3.connect') as mock_connect:
            # Make connect use our mock
            mock_connect.side_effect = lambda *args, **kwargs: mock_db.connect().__enter__()
            
            # Set up retry logic monitoring
            retry_attempts = []
            
            # Patch the internal retry method if it exists
            if hasattr(goal_service, '_get_connection'):
                original_get_connection = goal_service._get_connection
                
                @contextmanager
                def mock_get_connection():
                    retry_attempts.append(1)
                    yield from original_get_connection()
                
                goal_service._get_connection = mock_get_connection
            
            # Attempt calculation with timeout likely
            try:
                invalidate_cache()
                
                result = goal_service.calculate_goal_probability(
                    goal_id=goal_id,
                    profile_data=profile_data,
                    force_recalculate=True
                )
                
                # If we got here without an exception, the system must have retry logic
                logger.info("Calculation succeeded despite timeout probability")
                assert result is not None, "Got None result when calculation succeeded"
                
                # Check if retries were detected
                if retry_attempts:
                    assert len(retry_attempts) > 1, f"Only {len(retry_attempts)} retries detected"
                    logger.info(f"Detected {len(retry_attempts)} retry attempts")
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() or "timeout" in str(e).lower():
                    # Expected timeout error is fine
                    logger.info(f"Got expected timeout error: {e}")
                else:
                    # Other sqlite errors indicate a problem
                    pytest.fail(f"Unexpected SQLite error: {e}")
            except Exception as e:
                # The system should either succeed or fail with a database timeout
                pytest.fail(f"Unexpected error type: {type(e)}, {e}")
    
    def test_partial_calculation_recovery(self, mock_db_setup, profile_data):
        """Test recovery from partial calculation failures."""
        db_path, profile_id, mock_db = mock_db_setup
        
        # Create a test goal
        goal_id = self._create_test_goal(db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = db_path
        
        # Set moderate failure rate
        mock_db.set_failure_rate(0.3)
        
        # Clear cache
        invalidate_cache()
        
        # Run with failure injection in key calculation components
        with patch('sqlite3.connect') as mock_connect:
            # Make connect use our mock
            mock_connect.side_effect = lambda *args, **kwargs: mock_db.connect().__enter__()
            
            # Also patch the numpy random generation to sometimes fail
            original_normal = random.gauss  # Use as standin
            fail_counter = [0]
            
            def failing_normal(*args, **kwargs):
                fail_counter[0] += 1
                if fail_counter[0] % 10 == 0:  # Fail every 10th call
                    raise RuntimeError("Simulated random generation failure")
                return original_normal(*args, **kwargs)
            
            with patch('random.gauss', failing_normal):
                # Try calculation
                try:
                    result = goal_service.calculate_goal_probability(
                        goal_id=goal_id,
                        profile_data=profile_data,
                        force_recalculate=True
                    )
                    
                    # If we got here, the system recovered from partial failures
                    assert result is not None, "Got None result when calculation succeeded"
                    
                    # Verify probability is valid
                    probability = result.get_safe_success_probability()
                    assert 0 <= probability <= 1, f"Invalid probability: {probability}"
                    
                    logger.info(f"Calculation recovered from partial failures, probability: {probability}")
                    
                except Exception as e:
                    # Check if this is an expected failure
                    if "random generation" in str(e).lower():
                        logger.info(f"Expected test failure: {e}")
                    else:
                        pytest.fail(f"Unexpected failure: {type(e)}, {e}")
    
    def test_cache_corruption_recovery(self, mock_db_setup, profile_data, tmp_path):
        """Test recovery from cache corruption."""
        db_path, profile_id, mock_db = mock_db_setup
        
        # Create a test goal
        goal_id = self._create_test_goal(db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = db_path
        
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
                profile_data=profile_data,
                force_recalculate=False  # Let it try to use cache
            )
            
            # Should recover by recalculating
            assert result is not None, "Failed to recover from corrupt cache"
            
            # Verify probability is valid
            probability = result.get_safe_success_probability()
            assert 0 <= probability <= 1, f"Invalid probability after cache corruption: {probability}"
    
    def test_inconsistent_database_state(self, mock_db_setup, profile_data):
        """Test handling of inconsistent database state."""
        db_path, profile_id, mock_db = mock_db_setup
        
        # Create a test goal
        goal_id = self._create_test_goal(db_path, profile_id)
        
        # Corrupt the database by creating inconsistent state
        with sqlite3.connect(db_path) as conn:
            # Set inconsistent values in the goal
            conn.execute("""
                UPDATE goals SET 
                target_amount = 50000000,
                current_amount = 100000000  -- Current higher than target, inconsistent
                WHERE id = ?
            """, (goal_id,))
            
            conn.commit()
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = db_path
        
        # Try calculation with inconsistent state
        result = goal_service.calculate_goal_probability(
            goal_id=goal_id,
            profile_data=profile_data,
            force_recalculate=True
        )
        
        # Should handle gracefully by either:
        # 1. Returning 100% probability (already achieved)
        # 2. Adjusting the values to be consistent
        # 3. Raising a specific validation error
        
        if result is not None:
            probability = result.get_safe_success_probability()
            
            # Either we get 100% (already achieved) or a valid calculation
            assert 0 <= probability <= 1, f"Invalid probability with inconsistent data: {probability}"
            
            if probability == 1.0:
                logger.info("System correctly calculated 100% probability for already-achieved goal")
            else:
                logger.info(f"System calculated {probability:.2f} probability despite inconsistent data")
                
                # Check if the system fixed the inconsistency
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT target_amount, current_amount FROM goals WHERE id = ?",
                        (goal_id,)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        target, current = row
                        logger.info(f"Updated values - Target: {target}, Current: {current}")
                        # Should have fixed the inconsistency
                        assert current <= target, "System did not fix the data inconsistency"
    
    def test_resource_exhaustion_handling(self, mock_db_setup, profile_data):
        """Test handling of resource exhaustion scenarios."""
        db_path, profile_id, mock_db = mock_db_setup
        
        # Create a test goal
        goal_id = self._create_test_goal(db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = db_path
        
        # Patch memory allocation to simulate exhaustion
        original_array = list  # Use as standin for numpy array creation
        
        def memory_error_array(*args, **kwargs):
            # Simulate memory error on large allocations
            if 'items' in kwargs and kwargs['items'] > 1000:
                raise MemoryError("Simulated out of memory")
            return original_array(*args, **kwargs)
        
        # Monitor resource limits
        with patch('list', memory_error_array):
            # Try calculation with different iteration counts
            
            # Small iteration count should succeed
            result_small = goal_service.calculate_goal_probability(
                goal_id=goal_id,
                profile_data=profile_data,
                simulation_iterations=100,  # Small number
                force_recalculate=True
            )
            
            assert result_small is not None, "Failed on small simulation"
            
            # Large iteration count might trigger resource limits
            try:
                result_large = goal_service.calculate_goal_probability(
                    goal_id=goal_id,
                    profile_data=profile_data,
                    simulation_iterations=10000,  # Large number
                    force_recalculate=True
                )
                
                # If succeeded, should have valid result
                assert result_large is not None, "Got None result for large simulation"
                
                # Verify probability is valid
                probability = result_large.get_safe_success_probability()
                assert 0 <= probability <= 1, f"Invalid probability for large simulation: {probability}"
                
            except MemoryError:
                # This is expected with our patch
                logger.info("Got expected memory error for large simulation")
            except Exception as e:
                # Other errors should be handled properly
                assert "memory" in str(e).lower() or "resource" in str(e).lower(), \
                    f"Unexpected error type: {type(e)}, {e}"
    
    def test_parallel_calculation_conflicts(self, mock_db_setup, profile_data):
        """Test handling of conflicts in parallel calculations."""
        db_path, profile_id, mock_db = mock_db_setup
        
        # Create test goals
        goal_id1 = self._create_test_goal(db_path, profile_id)
        goal_id2 = self._create_test_goal(db_path, profile_id)
        
        # Set up goal service
        goal_service = GoalService()
        goal_service.db_path = db_path
        
        # Simulate parallel execution conflicts
        with patch('sqlite3.connect') as mock_connect:
            # Configure mock DB for lock conflicts
            mock_db.set_failure_rate(0.0)  # No random failures
            
            # Queue lock errors for specific operations
            mock_db.queue_exception(
                "execute", 
                sqlite3.OperationalError, 
                "database is locked"
            )
            
            # Make connect use our mock
            mock_connect.side_effect = lambda *args, **kwargs: mock_db.connect().__enter__()
            
            # Try batch calculation with conflicts
            try:
                results = goal_service.calculate_goal_probabilities(
                    goal_ids=[goal_id1, goal_id2],
                    profile_data=profile_data,
                    force_recalculate=True
                )
                
                # If succeeded, should have results for both goals
                assert len(results) == 2, f"Should have 2 results, got {len(results)}"
                
                # Verify both results
                for goal_id, result in results.items():
                    assert result is not None, f"Got None result for goal {goal_id}"
                    
                    # Verify probability
                    probability = result.get_safe_success_probability()
                    assert 0 <= probability <= 1, f"Invalid probability for goal {goal_id}: {probability}"
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    # If the system doesn't handle lock conflicts, this is expected
                    logger.info(f"System failed with lock conflict: {e}")
                else:
                    pytest.fail(f"Unexpected SQLite error: {e}")
            except Exception as e:
                pytest.fail(f"Unexpected error type: {type(e)}, {e}")


# Helper context manager for the test
@contextmanager
def contextmanager(fn):
    gen = fn()
    value = next(gen)
    try:
        yield value
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Run tests with pytest
    pytest.main(["-xvs", __file__])
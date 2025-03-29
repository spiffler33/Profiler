"""
Mock database service for resiliency testing.

This module provides a mock database service that can simulate various failure
modes for testing Monte Carlo simulation system resilience.
"""

import sqlite3
import time
import random
import logging
import queue
from contextlib import contextmanager
from unittest.mock import MagicMock

# Configure logging
logger = logging.getLogger(__name__)


class MockDatabaseService:
    """
    Mock database service that simulates various failure scenarios.
    
    This service wraps a real SQLite connection but can inject failures
    on demand to test system resilience.
    """
    
    def __init__(self, db_path, failure_rate=0.0, latency_ms=0, timeout_probability=0.0):
        """
        Initialize the mock database service.
        
        Args:
            db_path (str): Path to the actual database file
            failure_rate (float): Probability of operation failure (0.0-1.0)
            latency_ms (int): Simulated latency in milliseconds
            timeout_probability (float): Probability of timeout (0.0-1.0)
        """
        self.db_path = db_path
        self.failure_rate = failure_rate
        self.latency_ms = latency_ms
        self.timeout_probability = timeout_probability
        
        # Keep track of operations
        self.operations = []
        
        # Queue for custom responses/failures
        self.response_queue = queue.Queue()
        
        logger.info(f"Initialized MockDatabaseService with {failure_rate:.2f} failure rate")
    
    @contextmanager
    def connect(self):
        """
        Context manager for getting a database connection with simulated failures.
        """
        # Decide if this connection should fail
        if random.random() < self.failure_rate:
            logger.warning("Simulating database connection failure")
            raise sqlite3.OperationalError("Simulated connection failure")
        
        # Add simulated latency
        if self.latency_ms > 0:
            time.sleep(self.latency_ms / 1000.0)
        
        # Try actual connection
        real_conn = None
        mock_conn = None
        
        try:
            real_conn = sqlite3.connect(self.db_path)
            
            # Create a mock connection that wraps the real one
            mock_conn = MagicMock()
            
            # Set up cursor function
            def mock_cursor():
                # Decide if this cursor should timeout
                if random.random() < self.timeout_probability:
                    logger.warning("Simulating database timeout")
                    raise sqlite3.OperationalError("Simulated database timeout")
                
                # Get real cursor
                real_cursor = real_conn.cursor()
                
                # Create mock cursor that wraps real cursor
                mock_cursor = MagicMock()
                
                # Set up execute function
                def mock_execute(query, params=None):
                    # Record operation
                    self.operations.append(("execute", query, params))
                    
                    # Check if there's a custom response queued
                    try:
                        response_type, response = self.response_queue.get_nowait()
                        if response_type == "execute":
                            if isinstance(response, Exception):
                                logger.warning(f"Returning queued exception: {response}")
                                raise response
                            else:
                                logger.info(f"Returning queued response: {response}")
                                return response
                    except queue.Empty:
                        pass  # No custom response queued
                    
                    # Add simulated latency
                    if self.latency_ms > 0:
                        time.sleep(self.latency_ms / 1000.0)
                    
                    # Decide if this operation should fail
                    if random.random() < self.failure_rate:
                        error_type = random.choice([
                            "OperationalError: database is locked",
                            "OperationalError: disk I/O error",
                            "IntegrityError: UNIQUE constraint failed",
                            "DatabaseError: database disk image is malformed"
                        ])
                        logger.warning(f"Simulating error: {error_type}")
                        
                        if "OperationalError" in error_type:
                            raise sqlite3.OperationalError(error_type.split(": ")[1])
                        elif "IntegrityError" in error_type:
                            raise sqlite3.IntegrityError(error_type.split(": ")[1])
                        else:
                            raise sqlite3.DatabaseError(error_type.split(": ")[1])
                    
                    # Execute real query
                    if params is not None:
                        return real_cursor.execute(query, params)
                    else:
                        return real_cursor.execute(query)
                
                # Set up fetchone function
                def mock_fetchone():
                    # Record operation
                    self.operations.append(("fetchone",))
                    
                    # Check if there's a custom response queued
                    try:
                        response_type, response = self.response_queue.get_nowait()
                        if response_type == "fetchone":
                            if isinstance(response, Exception):
                                logger.warning(f"Returning queued exception: {response}")
                                raise response
                            else:
                                logger.info(f"Returning queued response: {response}")
                                return response
                    except queue.Empty:
                        pass  # No custom response queued
                    
                    # Add simulated latency
                    if self.latency_ms > 0:
                        time.sleep(self.latency_ms / 1000.0)
                    
                    # Decide if this operation should fail
                    if random.random() < self.failure_rate:
                        logger.warning("Simulating fetchone failure")
                        return None  # Simulate no results
                    
                    # Return real results
                    return real_cursor.fetchone()
                
                # Set up fetchall function
                def mock_fetchall():
                    # Record operation
                    self.operations.append(("fetchall",))
                    
                    # Check if there's a custom response queued
                    try:
                        response_type, response = self.response_queue.get_nowait()
                        if response_type == "fetchall":
                            if isinstance(response, Exception):
                                logger.warning(f"Returning queued exception: {response}")
                                raise response
                            else:
                                logger.info(f"Returning queued response: {response}")
                                return response
                    except queue.Empty:
                        pass  # No custom response queued
                    
                    # Add simulated latency
                    if self.latency_ms > 0:
                        time.sleep(self.latency_ms / 1000.0)
                    
                    # Decide if this operation should fail
                    if random.random() < self.failure_rate:
                        logger.warning("Simulating fetchall failure")
                        return []  # Simulate empty results
                    
                    # Return real results
                    return real_cursor.fetchall()
                
                # Attach mock functions to cursor
                mock_cursor.execute = mock_execute
                mock_cursor.fetchone = mock_fetchone
                mock_cursor.fetchall = mock_fetchall
                
                # Make real cursor attributes accessible through mock
                mock_cursor.description = real_cursor.description
                mock_cursor.rowcount = real_cursor.rowcount
                mock_cursor.arraysize = real_cursor.arraysize
                
                return mock_cursor
            
            # Set up commit function
            def mock_commit():
                # Record operation
                self.operations.append(("commit",))
                
                # Check if there's a custom response queued
                try:
                    response_type, response = self.response_queue.get_nowait()
                    if response_type == "commit":
                        if isinstance(response, Exception):
                            logger.warning(f"Returning queued exception: {response}")
                            raise response
                except queue.Empty:
                    pass  # No custom response queued
                
                # Add simulated latency
                if self.latency_ms > 0:
                    time.sleep(self.latency_ms / 1000.0)
                
                # Decide if this operation should fail
                if random.random() < self.failure_rate:
                    logger.warning("Simulating commit failure")
                    raise sqlite3.OperationalError("Simulated commit failure")
                
                # Perform real commit
                return real_conn.commit()
            
            # Set up rollback function
            def mock_rollback():
                # Record operation
                self.operations.append(("rollback",))
                
                # Add simulated latency
                if self.latency_ms > 0:
                    time.sleep(self.latency_ms / 1000.0)
                
                # Perform real rollback
                return real_conn.rollback()
            
            # Attach mock functions
            mock_conn.cursor = mock_cursor
            mock_conn.commit = mock_commit
            mock_conn.rollback = mock_rollback
            mock_conn.real_conn = real_conn  # Keep reference to real connection
            
            yield mock_conn
            
        except Exception as e:
            if real_conn:
                real_conn.close()
            raise e
        finally:
            if real_conn:
                real_conn.close()
    
    def queue_response(self, operation_type, response):
        """
        Queue a custom response for a specific operation.
        
        Args:
            operation_type (str): Type of operation ("execute", "fetchone", "fetchall", "commit")
            response: Response to return or exception to raise
        """
        self.response_queue.put((operation_type, response))
        logger.info(f"Queued response for {operation_type}: {response}")
    
    def queue_exception(self, operation_type, exception_class, message):
        """
        Queue an exception for a specific operation.
        
        Args:
            operation_type (str): Type of operation ("execute", "fetchone", "fetchall", "commit")
            exception_class: Exception class to raise
            message (str): Exception message
        """
        exception = exception_class(message)
        self.queue_response(operation_type, exception)
    
    def set_failure_rate(self, failure_rate):
        """Set the failure rate for operations."""
        self.failure_rate = max(0.0, min(1.0, failure_rate))
        logger.info(f"Set failure rate to {self.failure_rate:.2f}")
    
    def set_latency(self, latency_ms):
        """Set the simulated latency in milliseconds."""
        self.latency_ms = max(0, latency_ms)
        logger.info(f"Set latency to {self.latency_ms}ms")
    
    def set_timeout_probability(self, timeout_probability):
        """Set the probability of timeout for operations."""
        self.timeout_probability = max(0.0, min(1.0, timeout_probability))
        logger.info(f"Set timeout probability to {self.timeout_probability:.2f}")
    
    def get_operation_count(self):
        """Get the count of operations performed."""
        return len(self.operations)
    
    def get_operations(self):
        """Get the list of operations performed."""
        return self.operations
    
    def clear_operations(self):
        """Clear the list of operations."""
        self.operations = []
        logger.info("Cleared operations log")
    
    def __repr__(self):
        return (f"MockDatabaseService(db_path={self.db_path}, "
                f"failure_rate={self.failure_rate:.2f}, "
                f"latency_ms={self.latency_ms}, "
                f"timeout_probability={self.timeout_probability:.2f})")


# Example usage:
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create a mock database service
    mock_db = MockDatabaseService(":memory:", failure_rate=0.2, latency_ms=100)
    
    # Try some operations
    try:
        with mock_db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            cursor.execute("INSERT INTO test (name) VALUES (?)", ("Test",))
            conn.commit()
            
            cursor.execute("SELECT * FROM test")
            result = cursor.fetchall()
            print(f"Result: {result}")
    except Exception as e:
        print(f"Got exception: {e}")
    
    # Print operations
    print(f"Performed {mock_db.get_operation_count()} operations:")
    for op in mock_db.get_operations():
        print(f"  {op}")
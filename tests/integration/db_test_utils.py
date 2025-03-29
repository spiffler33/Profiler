"""
Database test utilities for integration testing.

This module provides helper functions for setting up test databases,
creating fixtures, and managing database state for integration tests.
"""

import os
import sqlite3
import json
import uuid
import logging
import tempfile
import shutil
from datetime import datetime, timedelta
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_database():
    """Create a temporary test database file."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_monte_carlo_")
    os.close(fd)
    
    # Initialize database schema
    initialize_database_schema(path)
    
    logger.info(f"Created test database at {path}")
    return path


def initialize_database_schema(db_path):
    """Initialize the database schema for testing."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
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
        
        # Create profiles table for DatabaseProfileManager
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create profile_versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                data TEXT NOT NULL,
                version INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
            )
        """)
        
        # Create goal_categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goal_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                order_index INTEGER NOT NULL DEFAULT 0,
                is_foundation BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        
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
        
        # Initialize predefined goal categories
        initialize_goal_categories(cursor)
        
        conn.commit()
        
    logger.info(f"Initialized database schema at {db_path}")


def initialize_goal_categories(cursor):
    """Initialize predefined goal categories in the database."""
    # Check if categories already exist
    cursor.execute("SELECT COUNT(*) FROM goal_categories")
    count = cursor.fetchone()[0]
    
    if count > 0:
        return
        
    # Define predefined categories
    categories = [
        # Security goals (foundation)
        {"name": "emergency_fund", "description": "Emergency fund for unexpected expenses", "order_index": 1, "is_foundation": 1},
        {"name": "insurance", "description": "Insurance coverage for protection", "order_index": 2, "is_foundation": 1},
        
        # Essential goals
        {"name": "home_purchase", "description": "Saving for home purchase or down payment", "order_index": 3, "is_foundation": 0},
        {"name": "education", "description": "Education funding for self or family", "order_index": 4, "is_foundation": 0},
        {"name": "debt_elimination", "description": "Paying off existing debts", "order_index": 5, "is_foundation": 0},
        
        # Retirement goals
        {"name": "early_retirement", "description": "Saving for early retirement", "order_index": 6, "is_foundation": 0},
        {"name": "traditional_retirement", "description": "Saving for traditional retirement age", "order_index": 7, "is_foundation": 0},
        {"name": "retirement", "description": "General retirement goal", "order_index": 8, "is_foundation": 0},
        
        # Lifestyle goals
        {"name": "travel", "description": "Saving for travel experiences", "order_index": 9, "is_foundation": 0},
        {"name": "vehicle", "description": "Saving for vehicle purchase", "order_index": 10, "is_foundation": 0},
        {"name": "home_improvement", "description": "Saving for home improvements or renovations", "order_index": 11, "is_foundation": 0},
        
        # Legacy goals
        {"name": "estate_planning", "description": "Planning for wealth transfer and estate", "order_index": 12, "is_foundation": 0},
        {"name": "charitable_giving", "description": "Saving for charitable donations or giving", "order_index": 13, "is_foundation": 0},
        
        # Custom goals
        {"name": "custom", "description": "User-defined custom goal", "order_index": 14, "is_foundation": 0}
    ]
    
    # Insert categories
    for category in categories:
        cursor.execute(
            "INSERT INTO goal_categories (name, description, order_index, is_foundation) VALUES (?, ?, ?, ?)",
            (category["name"], category["description"], category["order_index"], category["is_foundation"])
        )
    
    logger.info(f"Initialized {len(categories)} goal categories")


def create_test_profile(db_path, name="Test User", email="test@example.com"):
    """Create a test user profile in the database."""
    try:
        # Generate a UUID for the profile
        profile_id = str(uuid.uuid4())
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert test profile
        current_time = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO user_profiles (id, name, email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (profile_id, name, email, current_time, current_time))
        
        # Also create entry in profiles table
        profile_data = {
            "id": profile_id,
            "name": name,
            "email": email,
            "answers": [
                {"question_id": "monthly_income", "answer": 150000},
                {"question_id": "monthly_expenses", "answer": 80000},
                {"question_id": "total_assets", "answer": 10000000},
                {"question_id": "risk_profile", "answer": "aggressive"}
            ],
            "created_at": current_time,
            "updated_at": current_time
        }
        
        cursor.execute("""
            INSERT INTO profiles (id, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (profile_id, json.dumps(profile_data), current_time, current_time))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created test profile with ID: {profile_id}")
        return profile_id
    
    except Exception as e:
        logger.error(f"Error creating test profile: {str(e)}")
        return None


def create_test_goal(db_path, profile_id, goal_data):
    """Create a test goal in the database."""
    try:
        # Generate a UUID for the goal
        goal_id = str(uuid.uuid4())
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Current time for created/updated timestamps
        current_time = datetime.now().isoformat()
        
        # Extract values from goal_data with defaults
        title = goal_data.get("title", "Test Goal")
        category = goal_data.get("category", "custom")
        target_amount = goal_data.get("target_amount", 1000000)
        current_amount = goal_data.get("current_amount", 0)
        
        # Default timeframe is 5 years from now
        timeframe = goal_data.get("timeframe", 
                                (datetime.now() + timedelta(days=365*5)).isoformat())
        
        importance = goal_data.get("importance", "medium")
        flexibility = goal_data.get("flexibility", "somewhat_flexible")
        notes = goal_data.get("notes", "")
        goal_type = goal_data.get("goal_type", category)
        monthly_contribution = goal_data.get("monthly_contribution", 0)
        
        # Calculate progress if not provided
        current_progress = goal_data.get("current_progress")
        if current_progress is None and target_amount > 0:
            current_progress = (current_amount / target_amount) * 100
            
        # Serialize complex fields if provided
        funding_strategy = goal_data.get("funding_strategy")
        if funding_strategy and not isinstance(funding_strategy, str):
            funding_strategy = json.dumps(funding_strategy)
            
        allocation = goal_data.get("allocation")
        if allocation and not isinstance(allocation, str):
            allocation = json.dumps(allocation)
            
        additional_funding_sources = goal_data.get("additional_funding_sources", "")
        
        # Insert into goals table
        cursor.execute("""
            INSERT INTO goals (
                id, user_profile_id, category, title, target_amount, 
                timeframe, current_amount, importance, flexibility, notes,
                created_at, updated_at, goal_type, monthly_contribution,
                current_progress, goal_success_probability, funding_strategy,
                additional_funding_sources, allocation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            goal_id, profile_id, category, title, target_amount,
            timeframe, current_amount, importance, flexibility, notes,
            current_time, current_time, goal_type, monthly_contribution,
            current_progress, 0.0, funding_strategy,
            additional_funding_sources, allocation
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created test goal with ID: {goal_id}")
        return goal_id
    
    except Exception as e:
        logger.error(f"Error creating test goal: {str(e)}")
        return None


def backup_database(db_path):
    """Create a backup copy of the database."""
    backup_path = f"{db_path}.backup"
    shutil.copy2(db_path, backup_path)
    logger.info(f"Created database backup at {backup_path}")
    return backup_path


def restore_database(backup_path, db_path):
    """Restore database from backup."""
    shutil.copy2(backup_path, db_path)
    logger.info(f"Restored database from {backup_path}")
    return True


@contextmanager
def transaction(db_path):
    """Context manager for database transactions."""
    connection = None
    try:
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN TRANSACTION")
        yield connection
        connection.commit()
    except Exception as e:
        logger.error(f"Transaction error: {str(e)}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()


def cleanup_database(db_path):
    """Clean up the test database."""
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"Removed test database {db_path}")
        
    # Also clean up any backup
    backup_path = f"{db_path}.backup"
    if os.path.exists(backup_path):
        os.remove(backup_path)
        logger.info(f"Removed backup database {backup_path}")


if __name__ == "__main__":
    # Simple test to create a database and add some test data
    test_db = create_test_database()
    
    try:
        profile_id = create_test_profile(test_db)
        
        if profile_id:
            # Create a couple test goals
            retirement_data = {
                "title": "Test Retirement",
                "category": "retirement",
                "target_amount": 50000000,
                "current_amount": 10000000,
                "monthly_contribution": 50000,
                "allocation": {
                    "equity": 0.6,
                    "debt": 0.3, 
                    "gold": 0.05,
                    "cash": 0.05
                }
            }
            
            education_data = {
                "title": "Test Education",
                "category": "education",
                "target_amount": 5000000,
                "current_amount": 1000000,
                "monthly_contribution": 20000
            }
            
            retirement_id = create_test_goal(test_db, profile_id, retirement_data)
            education_id = create_test_goal(test_db, profile_id, education_data)
            
            logger.info(f"Created test goals: {retirement_id}, {education_id}")
            
            # Test transactions
            with transaction(test_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE goals SET goal_success_probability = ? WHERE id = ?",
                    (0.75, retirement_id)
                )
                
            # Verify the update
            with sqlite3.connect(test_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT goal_success_probability FROM goals WHERE id = ?",
                    (retirement_id,)
                )
                prob = cursor.fetchone()[0]
                logger.info(f"Updated probability: {prob}")
                
    finally:
        cleanup_database(test_db)
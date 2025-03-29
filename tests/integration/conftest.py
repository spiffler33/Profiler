"""
Database fixtures and configuration for integration tests.

This module provides pytest fixtures for setting up test databases,
managing transactions, and creating test data fixtures for integration tests.
"""

import os
import pytest
import tempfile
import sqlite3
import uuid
import json
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager
from unittest.mock import patch, MagicMock

from models.goal_models import GoalManager, Goal, GoalCategory
from models.database_profile_manager import DatabaseProfileManager
from services.goal_service import GoalService
from services.financial_parameter_service import get_financial_parameter_service, FinancialParameterService
from models.monte_carlo.cache import invalidate_cache

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database Schema SQL (for test database setup)
SCHEMA_SQL = """
-- Create goal_categories table
CREATE TABLE IF NOT EXISTS goal_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,
    is_foundation INTEGER NOT NULL DEFAULT 0,
    hierarchy_level INTEGER,
    parent_category_id INTEGER,
    FOREIGN KEY (parent_category_id) REFERENCES goal_categories(id)
);

-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Create profile_versions table
CREATE TABLE IF NOT EXISTS profile_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    data TEXT NOT NULL,
    version INTEGER NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

-- Create goals table with all required fields
CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    user_profile_id TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    target_amount REAL NOT NULL,
    timeframe TEXT NOT NULL,
    current_amount REAL NOT NULL DEFAULT 0,
    importance TEXT NOT NULL DEFAULT 'medium',
    flexibility TEXT NOT NULL DEFAULT 'somewhat_flexible',
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    current_progress REAL DEFAULT 0,
    priority_score REAL DEFAULT 0,
    additional_funding_sources TEXT,
    goal_success_probability REAL DEFAULT 0,
    adjustments_required INTEGER DEFAULT 0,
    funding_strategy TEXT,
    simulation_data TEXT,
    scenarios TEXT,
    adjustments TEXT,
    last_simulation_time TEXT,
    simulation_parameters_json TEXT,
    probability_partial_success REAL DEFAULT 0,
    simulation_iterations INTEGER DEFAULT 1000,
    simulation_path_data TEXT,
    monthly_contribution REAL DEFAULT 0,
    monthly_sip_recommended REAL DEFAULT 0,
    probability_metrics TEXT,
    success_threshold REAL DEFAULT 0.8,
    FOREIGN KEY (user_profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

-- Create profile answers table
CREATE TABLE IF NOT EXISTS profile_answers (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    answer TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

-- Create parameters table
CREATE TABLE IF NOT EXISTS financial_parameters (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    value TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    validation_rules TEXT,
    default_value TEXT,
    user_editable INTEGER NOT NULL DEFAULT 1
);

-- Create parameter history table
CREATE TABLE IF NOT EXISTS parameter_history (
    id TEXT PRIMARY KEY,
    parameter_id TEXT NOT NULL,
    old_value TEXT NOT NULL,
    new_value TEXT NOT NULL,
    change_timestamp TEXT NOT NULL,
    change_reason TEXT,
    user_id TEXT,
    FOREIGN KEY (parameter_id) REFERENCES financial_parameters(id) ON DELETE CASCADE
);
"""

# Predefined categories for the test database
PREDEFINED_CATEGORIES = [
    {
        "name": "Security", 
        "description": "Foundation level for emergency fund and insurance goals",
        "order_index": 1,
        "is_foundation": 1,
        "hierarchy_level": 1,
        "parent_category_id": None
    },
    {
        "name": "Essential", 
        "description": "Basic needs like home, education, and debt goals",
        "order_index": 2,
        "is_foundation": 0, 
        "hierarchy_level": 2,
        "parent_category_id": None
    },
    {
        "name": "Retirement", 
        "description": "Long-term retirement planning goals",
        "order_index": 3,
        "is_foundation": 0,
        "hierarchy_level": 3,
        "parent_category_id": None
    },
    {
        "name": "Lifestyle", 
        "description": "Quality of life goals like travel, vehicles, etc.",
        "order_index": 4,
        "is_foundation": 0,
        "hierarchy_level": 4,
        "parent_category_id": None
    },
    {
        "name": "Legacy", 
        "description": "Estate planning, charitable giving, and impact goals",
        "order_index": 5,
        "is_foundation": 0,
        "hierarchy_level": 5,
        "parent_category_id": None
    },
    {
        "name": "Custom", 
        "description": "User-defined goals that don't fit other categories",
        "order_index": 6,
        "is_foundation": 0,
        "hierarchy_level": 6,
        "parent_category_id": None
    }
]

# Subcategory definitions
SUBCATEGORIES = [
    {"name": "emergency_fund", "description": "Emergency fund for unexpected expenses", "parent": "Security"},
    {"name": "insurance", "description": "Insurance coverage", "parent": "Security"},
    {"name": "health_insurance", "description": "Health insurance coverage", "parent": "Security"},
    {"name": "life_insurance", "description": "Life insurance coverage", "parent": "Security"},
    {"name": "home_purchase", "description": "Home or property purchase", "parent": "Essential"},
    {"name": "education", "description": "Education expenses", "parent": "Essential"},
    {"name": "debt_repayment", "description": "Debt repayment goals", "parent": "Essential"},
    {"name": "early_retirement", "description": "Early retirement planning", "parent": "Retirement"},
    {"name": "traditional_retirement", "description": "Traditional retirement", "parent": "Retirement"},
    {"name": "travel", "description": "Travel goals", "parent": "Lifestyle"},
    {"name": "vehicle", "description": "Vehicle purchase", "parent": "Lifestyle"},
    {"name": "home_improvement", "description": "Home improvement", "parent": "Lifestyle"},
    {"name": "charitable_giving", "description": "Charitable giving goals", "parent": "Legacy"}
]

# Default parameters for Monte Carlo simulations
DEFAULT_PARAMETERS = [
    {
        "id": str(uuid.uuid4()),
        "name": "simulation.iterations",
        "category": "monte_carlo",
        "value": "1000",
        "type": "integer",
        "description": "Number of iterations for Monte Carlo simulations",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "validation_rules": json.dumps({"min": 100, "max": 10000}),
        "default_value": "1000",
        "user_editable": 1
    },
    {
        "id": str(uuid.uuid4()),
        "name": "asset_returns.equity.value",
        "category": "returns",
        "value": "0.12",
        "type": "float",
        "description": "Expected return for equity investments",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "validation_rules": json.dumps({"min": 0.01, "max": 0.30}),
        "default_value": "0.12",
        "user_editable": 1
    },
    {
        "id": str(uuid.uuid4()),
        "name": "asset_returns.equity.volatility",
        "category": "volatility",
        "value": "0.18",
        "type": "float",
        "description": "Volatility for equity investments",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "validation_rules": json.dumps({"min": 0.05, "max": 0.40}),
        "default_value": "0.18",
        "user_editable": 1
    },
    {
        "id": str(uuid.uuid4()),
        "name": "asset_returns.debt.value",
        "category": "returns",
        "value": "0.07",
        "type": "float",
        "description": "Expected return for debt investments",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "validation_rules": json.dumps({"min": 0.02, "max": 0.15}),
        "default_value": "0.07",
        "user_editable": 1
    },
    {
        "id": str(uuid.uuid4()),
        "name": "asset_returns.debt.volatility",
        "category": "volatility",
        "value": "0.06",
        "type": "float",
        "description": "Volatility for debt investments",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "validation_rules": json.dumps({"min": 0.01, "max": 0.20}),
        "default_value": "0.06",
        "user_editable": 1
    },
    {
        "id": str(uuid.uuid4()),
        "name": "inflation.value",
        "category": "inflation",
        "value": "0.06",
        "type": "float",
        "description": "Expected inflation rate",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "validation_rules": json.dumps({"min": 0.01, "max": 0.15}),
        "default_value": "0.06",
        "user_editable": 1
    }
]


@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary database file for tests."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_monte_carlo_")
    
    # Initialize the database with schema
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)
    
    # Insert predefined categories
    parent_category_ids = {}
    
    # First, insert top-level categories
    for category in PREDEFINED_CATEGORIES:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO goal_categories (name, description, order_index, is_foundation, hierarchy_level, parent_category_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            category["name"],
            category["description"],
            category["order_index"],
            category["is_foundation"],
            category["hierarchy_level"],
            category["parent_category_id"]
        ))
        category_id = cursor.lastrowid
        parent_category_ids[category["name"]] = category_id
    
    # Then, insert subcategories with proper parent relationships
    for subcat in SUBCATEGORIES:
        parent_id = parent_category_ids.get(subcat["parent"])
        if parent_id:
            # Get parent's hierarchy level
            cursor = conn.cursor()
            cursor.execute("SELECT hierarchy_level FROM goal_categories WHERE id = ?", (parent_id,))
            parent_level = cursor.fetchone()[0]
            
            # Insert subcategory with parent reference
            cursor.execute("""
                INSERT INTO goal_categories (name, description, order_index, is_foundation, hierarchy_level, parent_category_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                subcat["name"],
                subcat["description"],
                0,  # Default order_index
                1 if subcat["parent"] == "Security" else 0,  # is_foundation
                parent_level,  # Inherit parent's hierarchy level
                parent_id
            ))
    
    # Insert default parameters
    for param in DEFAULT_PARAMETERS:
        conn.execute("""
            INSERT INTO financial_parameters 
            (id, name, category, value, type, description, created_at, updated_at, 
             validation_rules, default_value, user_editable)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            param["id"],
            param["name"],
            param["category"],
            param["value"],
            param["type"],
            param["description"],
            param["created_at"],
            param["updated_at"],
            param["validation_rules"],
            param["default_value"],
            param["user_editable"]
        ))
    
    conn.commit()
    conn.close()
    
    yield path
    
    # Clean up after all tests
    os.close(fd)
    os.unlink(path)


@pytest.fixture(scope="function")
def test_db_connection(test_db_path):
    """Create a connection to the test database with transaction support."""
    connection = sqlite3.connect(test_db_path, isolation_level=None)  # autocommit mode
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    
    # Start a transaction
    connection.execute("BEGIN TRANSACTION")
    
    yield connection
    
    # Rollback the transaction to clean up after test
    connection.execute("ROLLBACK")
    connection.close()


@pytest.fixture(scope="function")
def db_profile_manager(test_db_path):
    """Create a database profile manager with the test database."""
    profile_manager = DatabaseProfileManager(db_path=test_db_path)
    
    # Clear cache to start fresh
    profile_manager.cache = {}
    
    yield profile_manager


@pytest.fixture(scope="function")
def test_goal_manager(test_db_path):
    """Create a goal manager for the test database."""
    goal_manager = GoalManager(db_path=test_db_path)
    yield goal_manager


@pytest.fixture(scope="function")
def test_goal_service(test_db_path):
    """Create a goal service configured to use the test database."""
    # Create a goal service with the test database
    service = GoalService()
    service.db_path = test_db_path
    
    # Ensure the goal manager is initialized with the test database
    service.goal_manager = GoalManager(db_path=test_db_path)
    
    yield service


@pytest.fixture(scope="function")
def test_parameter_service(test_db_path):
    """Create a parameter service for testing with mock-free implementation."""
    # Create a clean parameter service with the test database
    parameter_service = FinancialParameterService(db_path=test_db_path)
    
    # Clear caches
    parameter_service.clear_all_caches()
    
    # Ensure default test parameters are available in the service
    for param in DEFAULT_PARAMETERS:
        # Check if parameter needs to be added/updated
        result = parameter_service.get(param["name"])
        if result is None:
            # Use set method instead of add_parameter
            parameter_service.set(
                param["name"],
                param["value"],
                source="test"
            )
    
    yield parameter_service
    
    # Clean up after test
    parameter_service.clear_all_caches()
    invalidate_cache()


@pytest.fixture(scope="function")
def test_profile(db_profile_manager):
    """Create a test user profile with standard test data."""
    profile = db_profile_manager.create_profile(
        name="Test User",
        email="test@example.com"
    )
    
    # Add basic answers
    profile = db_profile_manager.add_answer(profile, "monthly_income", 150000)
    profile = db_profile_manager.add_answer(profile, "monthly_expenses", 80000)
    profile = db_profile_manager.add_answer(profile, "total_assets", 10000000)
    profile = db_profile_manager.add_answer(profile, "risk_profile", "aggressive")
    
    yield profile


@pytest.fixture(scope="function")
def profile_data():
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


@pytest.fixture(scope="function")
def test_retirement_goal(test_profile, test_goal_service, test_db_connection):
    """Create a standard retirement goal for testing."""
    # Get the early_retirement category ID
    cursor = test_db_connection.cursor()
    cursor.execute("SELECT id FROM goal_categories WHERE name = 'early_retirement'")
    category_row = cursor.fetchone()
    
    # Create a unique ID for this test goal
    goal_id = str(uuid.uuid4())
    
    # Insert the goal directly to avoid issues with the service
    today = datetime.now()
    target_date = today + timedelta(days=365*20)
    
    funding_strategy = json.dumps({
        "retirement_age": 55,
        "withdrawal_rate": 0.035,
        "monthly_contribution": 50000
    })
    
    allocation = json.dumps({
        "equity": 0.6,
        "debt": 0.3,
        "gold": 0.05,
        "cash": 0.05
    })
    
    # Insert directly to the database
    test_db_connection.execute("""
        INSERT INTO goals (
            id, user_profile_id, category, title, 
            target_amount, timeframe, current_amount,
            importance, flexibility, notes, 
            created_at, updated_at,
            funding_strategy, monthly_contribution,
            current_progress, goal_success_probability
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        goal_id,
        test_profile["id"],
        "early_retirement",
        "Test Early Retirement",
        75000000,
        target_date.isoformat(),
        10000000,
        "high",
        "somewhat_flexible",
        "Early retirement goal for testing",
        today.isoformat(),
        today.isoformat(),
        funding_strategy,
        50000,
        13.33,
        0.0
    ))
    
    # Commit the changes
    test_db_connection.execute("COMMIT")
    test_db_connection.execute("BEGIN TRANSACTION")
    
    yield goal_id
    
    # Clean up (the transaction rollback will handle this automatically)


@pytest.fixture(scope="function")
def test_education_goal(test_profile, test_goal_service, test_db_connection):
    """Create a standard education goal for testing."""
    # Get the education category ID
    cursor = test_db_connection.cursor()
    cursor.execute("SELECT id FROM goal_categories WHERE name = 'education'")
    category_row = cursor.fetchone()
    
    # Create a unique ID for this test goal
    goal_id = str(uuid.uuid4())
    
    # Insert the goal directly to avoid issues with the service
    today = datetime.now()
    target_date = today + timedelta(days=365*10)
    
    funding_strategy = json.dumps({
        "education_level": "pg",
        "country": "india",
        "course_duration": 4,
        "annual_cost": 1250000  # 5M / 4 years
    })
    
    allocation = json.dumps({
        "equity": 0.4,
        "debt": 0.4,
        "gold": 0.1,
        "cash": 0.1
    })
    
    # Insert directly to the database
    test_db_connection.execute("""
        INSERT INTO goals (
            id, user_profile_id, category, title, 
            target_amount, timeframe, current_amount,
            importance, flexibility, notes, 
            created_at, updated_at,
            funding_strategy, monthly_contribution,
            current_progress, goal_success_probability
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        goal_id,
        test_profile["id"],
        "education",
        "Test Education Goal",
        5000000,
        target_date.isoformat(),
        500000,
        "high",
        "somewhat_flexible",
        "Education goal for testing",
        today.isoformat(),
        today.isoformat(),
        funding_strategy,
        20000,
        10.0,
        0.0
    ))
    
    # Commit the changes
    test_db_connection.execute("COMMIT")
    test_db_connection.execute("BEGIN TRANSACTION")
    
    yield goal_id
    
    # Clean up (the transaction rollback will handle this automatically)


@pytest.fixture(scope="function")
def test_goals_with_edge_cases(test_profile, test_goal_service, test_db_connection):
    """Create a set of goals with edge cases for testing."""
    goals = []
    today = datetime.now()
    
    # 1. Goal with zero current amount
    zero_current_goal_id = str(uuid.uuid4())
    test_db_connection.execute("""
        INSERT INTO goals (
            id, user_profile_id, category, title, 
            target_amount, timeframe, current_amount,
            importance, flexibility, notes, 
            created_at, updated_at,
            monthly_contribution, current_progress
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        zero_current_goal_id,
        test_profile["id"],
        "home_purchase",
        "Zero Current Amount Goal",
        10000000,
        (today + timedelta(days=365*5)).isoformat(),
        0,  # Zero current amount
        "medium",
        "somewhat_flexible",
        "Goal with zero current amount",
        today.isoformat(),
        today.isoformat(),
        40000,
        0.0
    ))
    goals.append(zero_current_goal_id)
    
    # 2. Goal with very high target
    high_target_goal_id = str(uuid.uuid4())
    test_db_connection.execute("""
        INSERT INTO goals (
            id, user_profile_id, category, title, 
            target_amount, timeframe, current_amount,
            importance, flexibility, notes, 
            created_at, updated_at,
            monthly_contribution, current_progress
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        high_target_goal_id,
        test_profile["id"],
        "custom",
        "Very High Target Goal",
        500000000,  # Very high target (50 Crore)
        (today + timedelta(days=365*30)).isoformat(),
        5000000,
        "medium",
        "somewhat_flexible",
        "Goal with very high target",
        today.isoformat(),
        today.isoformat(),
        100000,
        1.0  # Low progress percentage
    ))
    goals.append(high_target_goal_id)
    
    # 3. Goal with short timeframe
    short_timeframe_goal_id = str(uuid.uuid4())
    test_db_connection.execute("""
        INSERT INTO goals (
            id, user_profile_id, category, title, 
            target_amount, timeframe, current_amount,
            importance, flexibility, notes, 
            created_at, updated_at,
            monthly_contribution, current_progress
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        short_timeframe_goal_id,
        test_profile["id"],
        "travel",
        "Short Timeframe Goal",
        500000,
        (today + timedelta(days=180)).isoformat(),  # Only 6 months
        100000,
        "medium",
        "somewhat_flexible",
        "Goal with very short timeframe",
        today.isoformat(),
        today.isoformat(),
        60000,
        20.0
    ))
    goals.append(short_timeframe_goal_id)
    
    # Commit the changes
    test_db_connection.execute("COMMIT")
    test_db_connection.execute("BEGIN TRANSACTION")
    
    yield goals
    
    # Clean up will be handled by the transaction rollback


@pytest.fixture(scope="function", autouse=True)
def mock_goal_probability_analyzer():
    """Create a mock probability analyzer for testing."""
    mock_analyzer = MagicMock()
    
    # Configure the mock to return a ProbabilityResult
    probability_result = {
        "success_metrics": {
            "success_probability": 0.75,
            "partial_success_probability": 0.85,
            "failure_probability": 0.25
        },
        "time_based_metrics": {
            "years_to_goal": 15,
            "median_achievement_time": 12
        },
        "distribution_data": {
            "percentiles": {
                "10": 3500000,
                "25": 5000000,
                "50": 7500000,
                "75": 9000000,
                "90": 12000000
            }
        },
        "risk_metrics": {
            "volatility": 0.15,
            "shortfall_risk": 0.25
        }
    }
    
    # Mock the analyze_goal_probability method
    from models.monte_carlo.probability.result import ProbabilityResult
    mock_result = ProbabilityResult(
        success_metrics=probability_result["success_metrics"],
        time_based_metrics=probability_result["time_based_metrics"],
        distribution_data=probability_result["distribution_data"],
        risk_metrics=probability_result["risk_metrics"]
    )
    
    # The analyze_goal_probability method has parameters: goal, profile, use_parallel, use_cache
    mock_analyzer.analyze_goal_probability.return_value = mock_result
    
    # Make the method accept the iterations parameter for test compatibility, but ignore it
    def mock_analysis_func(goal, profile=None, use_parallel=False, use_cache=True, **kwargs):
        # Ignore any additional parameters like simulation_iterations
        return mock_result
        
    mock_analyzer.analyze_goal_probability = mock_analysis_func
    
    # Patch the analyzer so it's used in all tests
    with patch('models.goal_probability.GoalProbabilityAnalyzer', return_value=mock_analyzer):
        yield mock_analyzer
#!/usr/bin/env python3
"""
Enhance goal probability analysis, scenarios, and adjustment fields

This script performs a database migration to enhance the Goal table with additional
fields for probability analysis, Monte Carlo simulation data, and scenario tracking.

Steps:
1. Creates a backup of the goals table before migration
2. Adds new fields to the goals table:
   - simulation_data (TEXT) - JSON-serialized Monte Carlo simulation results
   - scenarios (TEXT) - JSON-serialized alternative scenarios for the goal
   - adjustments (TEXT) - JSON-serialized recommended adjustments to improve success probability
   - last_simulation_time (TIMESTAMP) - When simulation was last run
   - simulation_parameters_json (TEXT) - Parameters used for simulation 
3. Enhances the existing adjustments_required field by adding a related adjustments field
4. Updates goals with sensible defaults for the new fields
5. Creates appropriate database indexes for improved query performance
6. Provides validation to verify data integrity post-migration

Usage:
    python enhance_probability_fields.py [--backup-only] [--validate-only] [--rollback TIMESTAMP]

    --backup-only    Create a backup without performing migration
    --validate-only  Only run validation queries, don't migrate
    --rollback       Rollback to a specified backup timestamp (YYYYMMDD_HHMMSS)
"""

import os
import sys
import sqlite3
import argparse
import logging
import json
import shutil
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db"
BACKUP_DIR = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/backups/parameters"
MIGRATION_VERSION = "1.0.0"
MIGRATION_NAME = "enhance_probability_fields"

@contextmanager
def get_db_connection(db_path=DB_PATH):
    """
    Context manager for database connections.
    
    Args:
        db_path: Path to the SQLite database
        
    Yields:
        sqlite3.Connection: Database connection object
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def create_backup() -> str:
    """
    Create a backup of the database.
    
    Returns:
        str: Timestamp of the backup
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Ensure backup directory exists
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Backup file path
        backup_file = os.path.join(BACKUP_DIR, f"parameters_db_backup_{timestamp}.db")
        pre_rollback_file = os.path.join(BACKUP_DIR, f"pre_rollback_db_{timestamp}.db")
        
        # Copy the database file
        shutil.copy2(DB_PATH, backup_file)
        shutil.copy2(DB_PATH, pre_rollback_file)
        logger.info(f"Created database backup at {backup_file}")
        
        # Export goals table to JSON for easier rollback
        goals_backup_file = os.path.join(BACKUP_DIR, f"parameters_backup_{timestamp}.json")
        export_goals_to_json(goals_backup_file)
        logger.info(f"Exported goals to {goals_backup_file}")
        
        return timestamp
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise

def export_goals_to_json(output_file: str) -> None:
    """
    Export goals table to JSON.
    
    Args:
        output_file: Path to the output JSON file
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all goals
            cursor.execute("SELECT * FROM goals")
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            goals = []
            for row in rows:
                goal = {key: row[key] for key in row.keys()}
                goals.append(goal)
            
            # Write to JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(goals, f, indent=2, default=str)
                
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise

def check_new_columns_exist() -> Tuple[bool, List[str]]:
    """
    Check if the new columns already exist in the goals table.
    
    Returns:
        Tuple: (all_columns_exist, list_of_existing_new_columns)
    """
    new_columns = [
        "simulation_data", 
        "scenarios", 
        "adjustments",
        "last_simulation_time",
        "simulation_parameters_json",
        "probability_partial_success",
        "simulation_iterations",
        "simulation_path_data",
        "monthly_sip_recommended",
        "probability_metrics",
        "success_threshold"
    ]
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get current columns
            cursor.execute("PRAGMA table_info(goals)")
            existing_columns = [row['name'] for row in cursor.fetchall()]
            
            # Check which new columns already exist
            existing_new_columns = [col for col in new_columns if col in existing_columns]
            all_exist = len(existing_new_columns) == len(new_columns)
            
            # Also check if goal_success_probability and adjustments_required exist
            expected_existing = ["goal_success_probability", "adjustments_required"]
            for col in expected_existing:
                if col not in existing_columns:
                    logger.warning(f"Expected column {col} not found in goals table")
            
            return all_exist, existing_new_columns
            
    except Exception as e:
        logger.error(f"Column check failed: {e}")
        raise

def add_new_columns() -> None:
    """
    Add new columns to the goals table if they don't exist.
    """
    all_columns_exist, existing_columns = check_new_columns_exist()
    
    if all_columns_exist:
        logger.info("All new columns already exist in the goals table.")
        return
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Start a transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Define new columns and their SQL definitions
            new_columns = {
                "simulation_data": "TEXT DEFAULT NULL",
                "scenarios": "TEXT DEFAULT NULL",
                "adjustments": "TEXT DEFAULT NULL",
                "last_simulation_time": "TIMESTAMP DEFAULT NULL",
                "simulation_parameters_json": "TEXT DEFAULT NULL",
                "probability_partial_success": "FLOAT DEFAULT 0.0",
                "simulation_iterations": "INTEGER DEFAULT 1000",
                "simulation_path_data": "TEXT DEFAULT NULL",
                "monthly_sip_recommended": "FLOAT DEFAULT 0.0",
                "probability_metrics": "TEXT DEFAULT NULL",
                "success_threshold": "FLOAT DEFAULT 0.8"
            }
            
            # Add each column if it doesn't exist
            for column, definition in new_columns.items():
                if column not in existing_columns:
                    sql = f"ALTER TABLE goals ADD COLUMN {column} {definition}"
                    cursor.execute(sql)
                    logger.info(f"Added column {column} to goals table")
            
            # Create indexes for improved query performance
            try:
                # Index for goal_success_probability for faster sorting and filtering
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_goals_success_probability 
                    ON goals (goal_success_probability)
                """)
                logger.info("Created index on goal_success_probability")
                
                # Index for last_simulation_time for timestamp-based queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_goals_last_simulation_time 
                    ON goals (last_simulation_time)
                """)
                logger.info("Created index on last_simulation_time")
                
                # Composite index for category + success probability for category-based filtering
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_goals_category_probability 
                    ON goals (category, goal_success_probability)
                """)
                logger.info("Created composite index on category and goal_success_probability")
                
            except sqlite3.OperationalError as e:
                # Ignore index errors (they might already exist)
                logger.warning(f"Index creation warning (non-critical): {e}")
            
            # Commit transaction
            conn.commit()
            logger.info("Successfully added new columns and indexes to the goals table")
            
    except Exception as e:
        logger.error(f"Adding columns failed: {e}")
        raise

def generate_percentile_path(percentile: int, target_amount: float, timeframe: str, expected_return: float) -> List[float]:
    """
    Generate a simulated path for a specific percentile.
    
    Args:
        percentile: Percentile to generate (e.g., 10, 25, 50, 75, 90)
        target_amount: Goal target amount
        timeframe: Goal target date
        expected_return: Expected annual return rate
        
    Returns:
        list: List of values representing the growth path
    """
    try:
        # Parse timeframe as date
        target_date = datetime.fromisoformat(timeframe.replace('Z', '+00:00'))
        today = datetime.now()
        years = max(0.5, (target_date - today).days / 365.0)
        
        # Number of points to generate (monthly for first 2 years, then quarterly)
        num_points = min(48, int(years * 12))
        
        # Starting amount (typically 0-20% of target)
        starting_percentage = min(20.0, percentile / 5.0)
        current = target_amount * (starting_percentage / 100.0)
        
        # Calculate growth rate based on percentile and expected return
        # Higher percentiles get higher growth rates
        annual_growth = expected_return * (0.7 + (percentile / 100.0) * 0.6)
        
        # Generate path
        path = [current]
        
        for i in range(1, num_points):
            # Add some randomness based on percentile
            # Lower percentiles have more volatility/drawdowns
            volatility_factor = 1.0 - abs(50 - percentile) / 100.0
            
            # Monthly growth rate with randomness
            growth_rate = (1 + annual_growth) ** (1/12) - 1
            random_factor = 1.0 + random.uniform(-0.02, 0.02) * volatility_factor
            
            # Calculate next point
            current = current * (1 + growth_rate) * random_factor
            
            # For higher percentiles, ensure steady growth toward target
            if percentile >= 70:
                min_expected = path[0] * ((1 + annual_growth) ** (i/12))
                current = max(current, min_expected)
            
            # For 90th percentile, ensure we reach or exceed target
            if percentile >= 90 and i == num_points - 1:
                current = max(current, target_amount)
                
            path.append(current)
        
        return path
    
    except (ValueError, TypeError):
        # If we can't parse the timeframe, return a simple linear path
        return [target_amount * 0.1, target_amount * 0.3, target_amount * 0.6, target_amount]

def generate_time_points(timeframe: str) -> List[str]:
    """
    Generate time point labels for the path data.
    
    Args:
        timeframe: Goal target date
        
    Returns:
        list: List of time point labels
    """
    try:
        # Parse timeframe as date
        target_date = datetime.fromisoformat(timeframe.replace('Z', '+00:00'))
        today = datetime.now()
        years = max(0.5, (target_date - today).days / 365.0)
        
        # Number of points to generate (monthly for first 2 years, then quarterly)
        num_points = min(48, int(years * 12))
        
        # Generate time points
        time_points = []
        current_date = today
        
        for i in range(num_points):
            # Add months one at a time
            if i > 0:
                # Simple month addition (not perfect but works for this purpose)
                month = current_date.month + 1
                year = current_date.year
                if month > 12:
                    month = 1
                    year += 1
                current_date = current_date.replace(year=year, month=month)
            
            # Format as ISO date
            time_points.append(current_date.isoformat())
        
        return time_points
        
    except (ValueError, TypeError):
        # If we can't parse the timeframe, return generic labels
        return ["Start", "25%", "50%", "75%", "Target"]

def update_goals_with_defaults() -> int:
    """
    Update goals with sensible defaults for the new fields.
    
    Returns:
        int: Number of goals updated
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Start a transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Get all goals with existing data
            cursor.execute("""
                SELECT id, goal_success_probability, adjustments_required, target_amount, category, timeframe
                FROM goals
            """)
            goals = cursor.fetchall()
            
            update_count = 0
            current_time = datetime.now().isoformat()
            
            # Process each goal individually to populate sensible defaults
            for goal in goals:
                goal_id = goal['id']
                success_probability = goal['goal_success_probability'] or 0.0
                adjustments_req = goal['adjustments_required'] or 0
                target_amount = goal['target_amount'] or 0.0
                category = goal['category'] or ""
                timeframe = goal['timeframe'] or ""
                
                # Create default simulation_data with SIP considerations
                sip_amount = round(target_amount * 0.01, 2)  # Default SIP as 1% of target
                
                # Format for Indian financial context (use lakhs/crores for large values)
                if target_amount >= 10000000:  # 1 Crore
                    target_formatted = f"₹{target_amount/10000000:.2f} Cr"
                elif target_amount >= 100000:  # 1 Lakh
                    target_formatted = f"₹{target_amount/100000:.2f} L"
                else:
                    target_formatted = f"₹{target_amount:.2f}"
                
                # Create simulation data structure
                simulation_data = {
                    "monte_carlo": {
                        "trials": 1000,
                        "success_rate": success_probability,
                        "confidence_interval": [
                            max(0, success_probability - 15),
                            min(100, success_probability + 10)
                        ],
                        "market_conditions": [
                            {"scenario": "bearish", "probability": max(0, success_probability - 30)},
                            {"scenario": "normal", "probability": success_probability},
                            {"scenario": "bullish", "probability": min(100, success_probability + 20)}
                        ]
                    },
                    "investment_options": {
                        "sip": {
                            "monthly_amount": sip_amount,
                            "annual_increase": 10,  # 10% annual increase
                            "tax_benefits": {
                                "section_80c": True if "retirement" in category.lower() or "retirement" in goal_id.lower() else False,
                                "section_80d": True if "health" in category.lower() or "health" in goal_id.lower() else False
                            }
                        },
                        "lumpsum": {
                            "amount": target_amount * 0.2,  # 20% lumpsum
                            "timing": "immediate"
                        }
                    },
                    "target": {
                        "amount": target_amount,
                        "formatted": target_formatted
                    }
                }
                
                # Create default scenarios based on different market conditions
                scenarios = {
                    "conservative": {
                        "return_rate": 6.0,
                        "inflation": 5.0,
                        "success_probability": max(0, success_probability - 15),
                        "sip_amount": sip_amount * 1.25  # 25% higher SIP for conservative scenario
                    },
                    "moderate": {
                        "return_rate": 9.0,
                        "inflation": 4.0,
                        "success_probability": success_probability,
                        "sip_amount": sip_amount
                    },
                    "aggressive": {
                        "return_rate": 12.0,
                        "inflation": 4.0,
                        "success_probability": min(100, success_probability + 15),
                        "sip_amount": sip_amount * 0.85  # 15% lower SIP for aggressive scenario
                    }
                }
                
                # Create default adjustments if adjustments_required is True
                adjustments = None
                if adjustments_req:
                    adjustments = {
                        "recommended": [
                            {
                                "type": "increase_sip",
                                "amount": sip_amount * 0.2,  # 20% increase
                                "impact": 15.0,  # 15% increase in success probability
                                "description": "Increase monthly SIP by 20%"
                            },
                            {
                                "type": "extend_timeline",
                                "amount": 2,  # 2 years
                                "impact": 12.0,
                                "description": "Extend goal timeline by 2 years"
                            },
                            {
                                "type": "lumpsum_investment",
                                "amount": target_amount * 0.1,
                                "impact": 10.0,
                                "description": f"Add lumpsum of {target_formatted}"
                            }
                        ],
                        "applied": [],
                        "history": []
                    }
                
                # Create simulation parameters based on goal category
                expected_return = 9.0  # default return rate
                risk_level = "moderate"
                
                # Adjust parameters based on goal category
                if "retirement" in category.lower():
                    expected_return = 10.0  # higher for long-term retirement
                    risk_level = "aggressive" if timeframe and datetime.fromisoformat(timeframe.replace('Z', '+00:00')) > datetime.now() + timedelta(days=10*365) else "moderate"
                elif "emergency" in category.lower():
                    expected_return = 6.0  # lower for emergency funds
                    risk_level = "conservative"
                elif "education" in category.lower():
                    expected_return = 8.0  # moderate for education
                    risk_level = "moderate"
                
                simulation_parameters = {
                    "expected_return": expected_return,
                    "risk_level": risk_level,
                    "inflation_rate": 5.0,
                    "tax_rate": 30.0,
                    "rebalancing_frequency": "yearly",
                    "volatility": {
                        "equity": 18.0,
                        "debt": 6.0,
                        "gold": 15.0
                    },
                    "asset_allocation": {
                        "equity": 60.0,
                        "debt": 30.0,
                        "gold": 10.0
                    }
                }
                
                # Calculate partial success probability - typically slightly higher than full success
                partial_success_probability = min(99.0, success_probability + 10.0)
                
                # Generate path data for visualization (10th, 25th, 50th, 75th, 90th percentiles)
                path_data = {
                    "percentiles": {
                        "10": generate_percentile_path(10, target_amount, timeframe, expected_return * 0.7),
                        "25": generate_percentile_path(25, target_amount, timeframe, expected_return * 0.85),
                        "50": generate_percentile_path(50, target_amount, timeframe, expected_return),
                        "75": generate_percentile_path(75, target_amount, timeframe, expected_return * 1.15),
                        "90": generate_percentile_path(90, target_amount, timeframe, expected_return * 1.3)
                    },
                    "time_points": generate_time_points(timeframe)
                }
                
                # Calculate probability metrics
                probability_metrics = {
                    "volatility": 15.0 if "equity" in category.lower() else 8.0,
                    "max_drawdown": 25.0 if "equity" in category.lower() else 10.0,
                    "sharpe_ratio": 1.2 if expected_return > 9.0 else 0.9,
                    "success_factors": {
                        "timeframe_impact": 10.0 if timeframe and (datetime.fromisoformat(timeframe.replace('Z', '+00:00')) > datetime.now() + timedelta(days=5*365)) else 0.0,
                        "funding_impact": 15.0 if sip_amount > (target_amount * 0.01) else 5.0,
                        "market_impact": 10.0
                    }
                }
                
                # Update the goal with the new data
                cursor.execute("""
                    UPDATE goals
                    SET 
                        simulation_data = ?,
                        scenarios = ?,
                        adjustments = ?,
                        last_simulation_time = ?,
                        simulation_parameters_json = ?,
                        probability_partial_success = ?,
                        simulation_iterations = ?,
                        simulation_path_data = ?,
                        monthly_sip_recommended = ?,
                        probability_metrics = ?,
                        success_threshold = ?
                    WHERE id = ?
                """, (
                    json.dumps(simulation_data) if simulation_data else None,
                    json.dumps(scenarios) if scenarios else None,
                    json.dumps(adjustments) if adjustments else None,
                    current_time,
                    json.dumps(simulation_parameters) if simulation_parameters else None,
                    partial_success_probability,
                    1000, # Default to 1000 iterations
                    json.dumps(path_data) if path_data else None,
                    sip_amount * 1.2, # Recommended SIP is 20% higher than calculated for better probability
                    json.dumps(probability_metrics) if probability_metrics else None,
                    0.8, # Default success threshold
                    goal_id
                ))
                
                update_count += 1
            
            # Commit transaction
            conn.commit()
            logger.info(f"Successfully updated {update_count} goals with default values")
            
            return update_count
            
    except Exception as e:
        logger.error(f"Updating goals failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def validate_migration() -> Dict[str, Any]:
    """
    Run validation queries to verify data integrity post-migration.
    
    Returns:
        Dict: Validation results with statistics
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            validation_results = {
                "timestamp": datetime.now().isoformat(),
                "total_goals": 0,
                "null_values": {},
                "invalid_values": {},
                "statistics": {}
            }
            
            # Count total goals
            cursor.execute("SELECT COUNT(*) as count FROM goals")
            validation_results["total_goals"] = cursor.fetchone()['count']
            
            # Check for NULL values in new columns
            new_columns = [
                "simulation_data", 
                "scenarios", 
                "adjustments",
                "last_simulation_time",
                "simulation_parameters_json"
            ]
            
            for column in new_columns:
                cursor.execute(f"SELECT COUNT(*) as count FROM goals WHERE {column} IS NULL")
                null_count = cursor.fetchone()['count']
                validation_results["null_values"][column] = null_count
            
            # Validate JSON in new columns
            json_columns = [
                "simulation_data", 
                "scenarios", 
                "adjustments",
                "simulation_parameters_json"
            ]
            
            for column in json_columns:
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM goals 
                    WHERE {column} IS NOT NULL 
                    AND json_valid({column}) = 0
                """)
                invalid_json = cursor.fetchone()['count']
                validation_results["invalid_values"][f"{column}_invalid_json"] = invalid_json
            
            # Check goals with all new data populated
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM goals 
                WHERE simulation_data IS NOT NULL 
                AND scenarios IS NOT NULL 
                AND last_simulation_time IS NOT NULL
                AND simulation_parameters_json IS NOT NULL
                AND (adjustments IS NOT NULL OR adjustments_required = 0)
            """)
            validation_results["statistics"]["fully_populated_goals"] = cursor.fetchone()['count']
            
            # Check goals that need adjustments
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM goals 
                WHERE adjustments_required = 1
            """)
            validation_results["statistics"]["goals_needing_adjustment"] = cursor.fetchone()['count']
            
            # Check goals with non-empty adjustments
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM goals 
                WHERE adjustments IS NOT NULL 
                AND adjustments <> 'null' 
                AND adjustments <> '{}'
            """)
            validation_results["statistics"]["goals_with_adjustments"] = cursor.fetchone()['count']
            
            # Validate specific to India financial context
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM goals 
                WHERE simulation_data IS NOT NULL 
                AND json_extract(simulation_data, '$.investment_options.sip') IS NOT NULL
            """)
            validation_results["statistics"]["goals_with_sip_data"] = cursor.fetchone()['count']
            
            # Validate timestamp data
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM goals 
                WHERE last_simulation_time IS NOT NULL 
                AND last_simulation_time <> ''
            """)
            validation_results["statistics"]["goals_with_simulation_timestamp"] = cursor.fetchone()['count']
            
            # Check simulation parameters
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM goals 
                WHERE simulation_parameters_json IS NOT NULL 
                AND json_extract(simulation_parameters_json, '$.expected_return') IS NOT NULL
            """)
            validation_results["statistics"]["goals_with_complete_parameters"] = cursor.fetchone()['count']
            
            # Verify index creation
            cursor.execute("PRAGMA index_list(goals)")
            indexes = cursor.fetchall()
            index_names = [index['name'] for index in indexes]
            
            expected_indexes = [
                "idx_goals_success_probability",
                "idx_goals_last_simulation_time",
                "idx_goals_category_probability"
            ]
            
            validation_results["statistics"]["indexes_created"] = sum(1 for idx in expected_indexes if idx in index_names)
            validation_results["statistics"]["total_indexes"] = len(expected_indexes)
            
            return validation_results
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

def save_validation_results(results: Dict[str, Any], timestamp: str) -> None:
    """
    Save validation results to a file.
    
    Args:
        results: Validation results
        timestamp: Timestamp for the filename
    """
    try:
        # Ensure backup directory exists
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Save to JSON file
        output_file = os.path.join(BACKUP_DIR, f"validation_results_{timestamp}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
            
        logger.info(f"Saved validation results to {output_file}")
        
    except Exception as e:
        logger.error(f"Saving validation results failed: {e}")
        raise

def rollback_migration(timestamp: str) -> None:
    """
    Rollback to a previous backup.
    
    Args:
        timestamp: Backup timestamp to restore (YYYYMMDD_HHMMSS)
    """
    try:
        # Check if backup exists
        db_backup = os.path.join(BACKUP_DIR, f"parameters_db_backup_{timestamp}.db")
        goals_backup = os.path.join(BACKUP_DIR, f"parameters_backup_{timestamp}.json")
        
        if not os.path.exists(db_backup) or not os.path.exists(goals_backup):
            logger.error(f"Backup files for timestamp {timestamp} not found")
            raise FileNotFoundError(f"Backup files for timestamp {timestamp} not found")
        
        # Create a new backup of the current state first (already handled by create_backup)
        
        # Restore database from backup
        shutil.copy2(db_backup, DB_PATH)
        logger.info(f"Restored database from {db_backup}")
        
        logger.info(f"Successfully rolled back to {timestamp}")
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise

def main():
    """
    Main function to parse arguments and run the appropriate actions.
    """
    parser = argparse.ArgumentParser(description="Goal Probability Fields Enhancement Migration")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--backup-only", action="store_true", help="Create a backup without migration")
    group.add_argument("--validate-only", action="store_true", help="Run validation without migration")
    group.add_argument("--rollback", metavar="TIMESTAMP", help="Rollback to specified backup (YYYYMMDD_HHMMSS)")
    
    args = parser.parse_args()
    
    try:
        if args.backup_only:
            timestamp = create_backup()
            print(f"Backup created successfully with timestamp: {timestamp}")
            return
            
        if args.validate_only:
            results = validate_migration()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_validation_results(results, timestamp)
            
            # Print summary
            print("\nValidation Results:")
            print(f"Total goals: {results['total_goals']}")
            
            # Check for any NULL values
            null_count = sum(results["null_values"].values())
            if null_count > 0:
                print(f"WARNING: Found {null_count} NULL values across new columns")
                for column, count in results["null_values"].items():
                    if count > 0:
                        print(f"  - {column}: {count} NULL values")
            else:
                print("✓ No NULL values found in new columns")
            
            # Check for invalid values
            invalid_count = sum(results["invalid_values"].values())
            if invalid_count > 0:
                print(f"WARNING: Found {invalid_count} invalid values")
                for check, count in results["invalid_values"].items():
                    if count > 0:
                        print(f"  - {check}: {count} goals affected")
            else:
                print("✓ No invalid values found")
                
            print("\nStatistics:")
            print(f"Fully populated goals: {results['statistics']['fully_populated_goals']} of {results['total_goals']}")
            print(f"Goals needing adjustment: {results['statistics']['goals_needing_adjustment']}")
            print(f"Goals with adjustment data: {results['statistics']['goals_with_adjustments']}")
            print(f"Goals with SIP data: {results['statistics']['goals_with_sip_data']}")
            
            return
            
        if args.rollback:
            rollback_migration(args.rollback)
            print(f"Successfully rolled back to {args.rollback}")
            return
        
        # Default: run the migration
        print(f"Starting {MIGRATION_NAME} migration...")
        
        # Step 1: Create backup
        timestamp = create_backup()
        print(f"Created backup with timestamp: {timestamp}")
        
        # Step 2: Add new columns
        print("Adding new columns to goals table...")
        add_new_columns()
        
        # Step 3: Update with defaults
        print("Updating goals with default values...")
        count = update_goals_with_defaults()
        print(f"Updated {count} goals with default values")
        
        # Step 4: Validate migration
        print("Validating migration...")
        results = validate_migration()
        save_validation_results(results, timestamp)
        
        # Print validation summary
        null_count = sum(results["null_values"].values())
        invalid_count = sum(results["invalid_values"].values())
        
        if null_count > 0 or invalid_count > 0:
            print("\nWARNING: Validation found issues that should be addressed:")
            if null_count > 0:
                print(f"- {null_count} NULL values found in new columns")
            if invalid_count > 0:
                print(f"- {invalid_count} invalid values found")
            print(f"\nSee {BACKUP_DIR}/validation_results_{timestamp}.json for details")
            print("You may need to run additional clean-up steps or manually fix these issues.")
        else:
            print("\n✓ Migration completed successfully with no validation issues!")
        
        print(f"\nIf you need to rollback, run: python {MIGRATION_NAME}.py --rollback {timestamp}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Goals Table Migration Script

This script performs a database migration to add new fields to the goals table
with appropriate NULL constraints and sets sensible defaults.

Steps:
1. Creates a backup of the goals table before migration
2. Adds new fields to the goals table with NULL constraints initially
3. Updates goals with sensible defaults for the new fields
4. Provides validation to verify data integrity post-migration

Usage:
    python migrate_goals_table.py [--backup-only] [--validate-only] [--rollback TIMESTAMP]

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
BACKUP_DIR = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/backups"
MIGRATION_VERSION = "1.0.0"

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
        backup_file = os.path.join(BACKUP_DIR, f"profiles_backup_{timestamp}.db")
        
        # Copy the database file
        shutil.copy2(DB_PATH, backup_file)
        logger.info(f"Created database backup at {backup_file}")
        
        # Export goals table to JSON for easier rollback
        goals_backup_file = os.path.join(BACKUP_DIR, f"goals_backup_{timestamp}.json")
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
        "current_progress", 
        "priority_score", 
        "additional_funding_sources", 
        "goal_success_probability", 
        "adjustments_required", 
        "funding_strategy"
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
                "current_progress": "REAL DEFAULT 0.0",
                "priority_score": "REAL DEFAULT 0.0",
                "additional_funding_sources": "TEXT DEFAULT ''",
                "goal_success_probability": "REAL DEFAULT 0.0",
                "adjustments_required": "BOOLEAN DEFAULT 0",
                "funding_strategy": "TEXT DEFAULT ''"
            }
            
            # Add each column if it doesn't exist
            for column, definition in new_columns.items():
                if column not in existing_columns:
                    sql = f"ALTER TABLE goals ADD COLUMN {column} {definition}"
                    cursor.execute(sql)
                    logger.info(f"Added column {column} to goals table")
            
            # Commit transaction
            conn.commit()
            logger.info("Successfully added new columns to the goals table")
            
    except Exception as e:
        logger.error(f"Adding columns failed: {e}")
        raise

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
            
            # 1. Update current_progress based on current_amount and target_amount
            cursor.execute("""
                UPDATE goals
                SET current_progress = CASE
                    WHEN target_amount > 0 THEN MIN(100.0, (current_amount / target_amount) * 100.0)
                    ELSE 0.0
                END
                WHERE current_progress IS NULL OR current_progress = 0.0
            """)
            
            # 2. Calculate priority score based on importance and flexibility
            cursor.execute("""
                UPDATE goals
                SET priority_score = CASE
                    WHEN importance = 'high' THEN 70.0
                    WHEN importance = 'medium' THEN 50.0
                    ELSE 30.0
                END
                + CASE
                    WHEN flexibility = 'fixed' THEN 20.0
                    WHEN flexibility = 'somewhat_flexible' THEN 10.0
                    ELSE 5.0
                END
                WHERE priority_score IS NULL OR priority_score = 0.0
            """)
            
            # 3. Set sensible defaults for remaining fields
            cursor.execute("""
                UPDATE goals
                SET 
                    additional_funding_sources = COALESCE(additional_funding_sources, ''),
                    goal_success_probability = COALESCE(goal_success_probability, 
                        CASE
                            WHEN current_progress > 75.0 THEN 90.0
                            WHEN current_progress > 50.0 THEN 70.0
                            WHEN current_progress > 25.0 THEN 50.0
                            ELSE 30.0
                        END),
                    adjustments_required = COALESCE(adjustments_required, 0),
                    funding_strategy = COALESCE(funding_strategy, '')
            """)
            
            # Get count of updated goals
            cursor.execute("SELECT COUNT(*) as count FROM goals")
            count = cursor.fetchone()['count']
            
            # Commit transaction
            conn.commit()
            logger.info(f"Successfully updated {count} goals with default values")
            
            return count
            
    except Exception as e:
        logger.error(f"Updating goals failed: {e}")
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
                "current_progress", 
                "priority_score", 
                "additional_funding_sources", 
                "goal_success_probability", 
                "adjustments_required", 
                "funding_strategy"
            ]
            
            for column in new_columns:
                cursor.execute(f"SELECT COUNT(*) as count FROM goals WHERE {column} IS NULL")
                null_count = cursor.fetchone()['count']
                validation_results["null_values"][column] = null_count
            
            # Check for invalid values
            cursor.execute("SELECT COUNT(*) as count FROM goals WHERE current_progress < 0 OR current_progress > 100")
            validation_results["invalid_values"]["current_progress_out_of_range"] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM goals WHERE priority_score < 0")
            validation_results["invalid_values"]["negative_priority_score"] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM goals WHERE goal_success_probability < 0 OR goal_success_probability > 100")
            validation_results["invalid_values"]["probability_out_of_range"] = cursor.fetchone()['count']
            
            # Collect basic statistics
            cursor.execute("SELECT AVG(current_progress) as avg FROM goals")
            validation_results["statistics"]["avg_progress"] = cursor.fetchone()['avg']
            
            cursor.execute("SELECT AVG(priority_score) as avg FROM goals")
            validation_results["statistics"]["avg_priority_score"] = cursor.fetchone()['avg']
            
            cursor.execute("SELECT AVG(goal_success_probability) as avg FROM goals")
            validation_results["statistics"]["avg_success_probability"] = cursor.fetchone()['avg']
            
            cursor.execute("SELECT SUM(CASE WHEN adjustments_required = 1 THEN 1 ELSE 0 END) as count FROM goals")
            validation_results["statistics"]["goals_needing_adjustment"] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM goals WHERE additional_funding_sources != ''")
            validation_results["statistics"]["goals_with_additional_funding"] = cursor.fetchone()['count']
            
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
        db_backup = os.path.join(BACKUP_DIR, f"profiles_backup_{timestamp}.db")
        goals_backup = os.path.join(BACKUP_DIR, f"goals_backup_{timestamp}.json")
        
        if not os.path.exists(db_backup) or not os.path.exists(goals_backup):
            logger.error(f"Backup files for timestamp {timestamp} not found")
            raise FileNotFoundError(f"Backup files for timestamp {timestamp} not found")
        
        # Create a new backup of the current state first
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = os.path.join(BACKUP_DIR, f"profiles_pre_rollback_{current_timestamp}.db")
        shutil.copy2(DB_PATH, current_backup)
        logger.info(f"Created pre-rollback backup at {current_backup}")
        
        # Restore database from backup
        shutil.copy2(db_backup, DB_PATH)
        logger.info(f"Restored database from {db_backup}")
        
        # Alternatively, we could just restore the goals table from the JSON file
        # instead of replacing the entire database
        
        logger.info(f"Successfully rolled back to {timestamp}")
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise

def main():
    """
    Main function to parse arguments and run the appropriate actions.
    """
    parser = argparse.ArgumentParser(description="Goals Table Migration Script")
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
            print(f"Average progress: {results['statistics']['avg_progress']:.2f}%")
            print(f"Average priority score: {results['statistics']['avg_priority_score']:.2f}")
            print(f"Average success probability: {results['statistics']['avg_success_probability']:.2f}%")
            print(f"Goals needing adjustment: {results['statistics']['goals_needing_adjustment']}")
            print(f"Goals with additional funding sources: {results['statistics']['goals_with_additional_funding']}")
            
            return
            
        if args.rollback:
            rollback_migration(args.rollback)
            print(f"Successfully rolled back to {args.rollback}")
            return
        
        # Default: run the migration
        print("Starting goals table migration...")
        
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
        
        print(f"\nIf you need to rollback, run: python migrate_goals_table.py --rollback {timestamp}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
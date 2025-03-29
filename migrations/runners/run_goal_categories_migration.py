#!/usr/bin/env python3
"""
Migration runner script for goal categories with Indian financial context.

This script:
1. Runs the database migration to add Indian-specific fields:
   - category_priority (integer)
   - typical_timeframe_years (integer)
   - requires_sip (boolean)
   - applicable_tax_section (string - for Indian tax sections like 80C, 80D)
2. Initializes the database with common Indian financial goal categories:
   - Education (for children's higher education)
   - Marriage (for wedding expenses)
   - Home Purchase (for property acquisition)
   - Retirement (for post-retirement income)
   - Emergency Fund (for unexpected expenses)
   - Tax Optimization (for tax-efficient investments)
3. Provides feedback on the migration process and logs to /logs/goal_migration.log

Usage:
    python run_goal_categories_migration.py

Options:
    --force-update: Force update of existing categories to match predefined values
    --check-only: Only check if migration is needed, don't make changes
    --skip-categories: Skip adding Indian financial goal categories
"""

import os
import sys
import logging
import argparse
import sqlite3
import traceback
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def check_schema():
    """Check if the goal_categories table needs migration for Indian financial context"""
    db_path = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the goal_categories table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goal_categories'")
        if not cursor.fetchone():
            logger.error("goal_categories table not found in database")
            conn.close()
            return False, "Table does not exist"
        
        # Check for hierarchy columns and Indian-specific columns
        cursor.execute("PRAGMA table_info(goal_categories)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Keep track of all required columns
        required_columns = [
            # Hierarchical structure (for backward compatibility)
            'hierarchy_level',
            'parent_category_id',
            # Indian financial context
            'category_priority',
            'typical_timeframe_years',
            'requires_sip',
            'applicable_tax_section'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
            
        conn.close()
        
        if missing_columns:
            return False, f"Missing columns: {', '.join(missing_columns)}"
        return True, "Schema is up to date with Indian financial context"
        
    except Exception as e:
        logger.error(f"Error checking schema: {str(e)}")
        return False, str(e)

def run_migration(skip_categories=False):
    """Run the migration script for Indian financial context"""
    logger.info("Running database migration for goal categories with Indian financial context...")
    
    try:
        # Add the migrations/scripts directory to the Python path
        import sys
        from pathlib import Path
        
        # Get the absolute path to the migrations/scripts directory
        scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.append(str(scripts_dir))
        
        # Import and run the migration script with appropriate options
        import migrate_goal_categories
        
        # Prepare arguments for the migration script
        import sys
        sys_argv_backup = sys.argv
        
        try:
            # Set up command line arguments for the migration script
            sys.argv = ["migrate_goal_categories.py"]
            if skip_categories:
                sys.argv.append("--skip-categories")
                
            # Run the migration script
            migrate_goal_categories.main()
            logger.info("Migration script completed successfully")
            return True
        finally:
            # Restore original sys.argv
            sys.argv = sys_argv_backup
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    parser = argparse.ArgumentParser(description="Migrate and initialize goal categories with Indian financial context")
    parser.add_argument("--force-update", action="store_true", help="Force update existing categories")
    parser.add_argument("--check-only", action="store_true", help="Only check if migration is needed")
    parser.add_argument("--skip-categories", action="store_true", help="Skip adding Indian financial goal categories")
    
    args = parser.parse_args()
    
    # Set up file logging
    file_handler = logging.FileHandler("/Users/coddiwomplers/Desktop/Python/Profiler4/logs/goal_migration.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    logger.info("==== Starting Goal Categories Migration for Indian Financial Context ====")
    
    # Check if migration is needed
    schema_ok, message = check_schema()
    
    if args.check_only:
        if schema_ok:
            logger.info(f"Schema check: {message}")
        else:
            logger.warning(f"Schema needs migration: {message}")
        return
    
    # Run migration if needed
    if not schema_ok:
        logger.info(f"Schema needs migration: {message}")
        if not run_migration(skip_categories=args.skip_categories):
            logger.error("Migration failed, aborting")
            sys.exit(1)
    else:
        logger.info("Database schema is already up to date with Indian financial context")
        
        # Even if schema is up to date, we may still want to add the Indian categories
        if not args.skip_categories:
            logger.info("Running category initialization directly...")
            
            # Add the migrations/scripts directory to the Python path
            import sys
            from pathlib import Path
            
            # Get the absolute path to the migrations/scripts directory
            scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
            if str(scripts_dir) not in sys.path:
                sys.path.append(str(scripts_dir))
            
            # Import and initialize Indian goal categories
            try:
                import migrate_goal_categories
                migrate_goal_categories.initialize_indian_goal_categories()
                logger.info("Indian financial goal categories initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize categories: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
    
    logger.info("Goal categories migration for Indian financial context completed successfully")
    logger.info("==== Goal Categories Migration Completed ====")
    
    # Close file handler
    file_handler.close()
    logger.removeHandler(file_handler)

if __name__ == "__main__":
    main()
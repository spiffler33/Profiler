"""
Migration script to add missing columns to the goals table.
"""

import sqlite3
import logging
import os
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_existing_columns(cursor, table_name):
    """Get existing columns in the table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def alter_goals_table():
    """Add missing columns to goals table for API testing."""
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        # Check existing columns
        existing_columns = get_existing_columns(cursor, 'goals')
        logger.info(f"Current columns in goals table: {', '.join(existing_columns)}")
        
        # Add missing columns if they don't exist
        missing_columns = []
        
        # Column 1: last_simulation_time
        if 'last_simulation_time' not in existing_columns:
            missing_columns.append(('last_simulation_time', 'TEXT'))
            
        # Column 2: simulation_data
        if 'simulation_data' not in existing_columns:
            missing_columns.append(('simulation_data', 'TEXT'))
            
        # Column 3: scenarios
        if 'scenarios' not in existing_columns:
            missing_columns.append(('scenarios', 'TEXT'))
            
        # Column 4: adjustments
        if 'adjustments' not in existing_columns:
            missing_columns.append(('adjustments', 'TEXT'))
        
        # Column 5: simulation_parameters_json
        if 'simulation_parameters_json' not in existing_columns:
            missing_columns.append(('simulation_parameters_json', 'TEXT'))
        
        # Execute ALTER TABLE statements
        for column_name, column_type in missing_columns:
            try:
                cursor.execute(f"ALTER TABLE goals ADD COLUMN {column_name} {column_type}")
                logger.info(f"Added column {column_name} ({column_type}) to goals table")
            except sqlite3.OperationalError as e:
                logger.error(f"Error adding column {column_name}: {str(e)}")
        
        # Commit changes
        conn.commit()
        
        # Verify columns were added
        updated_columns = get_existing_columns(cursor, 'goals')
        logger.info(f"Updated columns in goals table: {', '.join(updated_columns)}")
        
        # Report status
        if missing_columns:
            logger.info(f"Added {len(missing_columns)} columns to goals table")
        else:
            logger.info("No columns needed to be added to goals table")
            
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    
if __name__ == "__main__":
    logger.info("Starting goals table migration")
    alter_goals_table()
    logger.info("Completed goals table migration")
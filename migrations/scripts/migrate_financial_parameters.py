#!/usr/bin/env python3
"""
Financial Parameters Migration Tool

This script provides functionality to migrate the financial parameters system:
1. Creates backups of current parameter values
2. Converts flat parameters to hierarchical structure
3. Adds versioning to parameter entries
4. Includes rollback capabilities

Usage:
    python migrate_financial_parameters.py [--backup-only] [--migrate] [--rollback BACKUP_FILE]
    
    --backup-only    Create a backup without performing migration
    --migrate        Perform the migration (this is the default action)
    --rollback       Rollback to a specified backup file
"""

import os
import sys
import json
import sqlite3
import argparse
import logging
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

# Import the financial parameters module
from models.financial_parameters import (
    get_parameters, FinancialParameters, ParameterMetadata, ParameterValue,
    ParameterSource, LEGACY_ACCESS_ENABLED, LOG_DEPRECATED_ACCESS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BACKUP_DIR = "data/backups/parameters/"
PARAMETERS_DB_PATH = "data/parameters.db"
VERSION = "1.0.0"  # Initial version for the migration

@contextmanager
def get_db_connection(db_path: str = PARAMETERS_DB_PATH):
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
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def initialize_database(db_path: str = PARAMETERS_DB_PATH) -> None:
    """
    Initialize the parameters database with necessary tables.
    
    Args:
        db_path: Path to the SQLite database
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Create parameters table with hierarchical structure support
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                value TEXT NOT NULL,
                data_type TEXT NOT NULL,
                source INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(path)
            )
            ''')
            
            # Create parameter_metadata table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS parameter_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                user_overridable BOOLEAN NOT NULL DEFAULT 0,
                regulatory BOOLEAN NOT NULL DEFAULT 0,
                volatility REAL NOT NULL DEFAULT 0.0,
                confidence REAL NOT NULL DEFAULT 1.0,
                last_updated TEXT NOT NULL,
                FOREIGN KEY (parameter_id) REFERENCES parameters (id) ON DELETE CASCADE
            )
            ''')
            
            # Create parameter_questions table for connecting parameters to input questions
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS parameter_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                FOREIGN KEY (parameter_id) REFERENCES parameters (id) ON DELETE CASCADE
            )
            ''')
            
            # Create parameter_versions table for versioning
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS parameter_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter_id INTEGER NOT NULL,
                value TEXT NOT NULL,
                source INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (parameter_id) REFERENCES parameters (id) ON DELETE CASCADE
            )
            ''')
            
            # Create migration_history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                description TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                backup_file TEXT
            )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def create_backup() -> str:
    """
    Create a backup of the current parameters.
    
    Returns:
        str: Path to the backup file
    """
    try:
        # Ensure backup directory exists
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"parameters_backup_{timestamp}.json")
        
        # Get current parameters
        params = get_parameters()
        
        # Convert parameters to dictionary
        if hasattr(params, "_parameters"):
            params_dict = params._parameters
        else:
            # For backwards compatibility with older versions
            params_dict = {}
            # Try to extract parameters using reflection
            for attr_name in dir(params):
                if attr_name.startswith("_") or callable(getattr(params, attr_name)):
                    continue
                params_dict[attr_name] = getattr(params, attr_name)
        
        # Create a backup file
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "version": VERSION,
                "parameters": params_dict
            }, f, indent=2, default=str)
        
        logger.info(f"Created parameters backup at {backup_path}")
        
        # If database exists, also backup the database
        if os.path.exists(PARAMETERS_DB_PATH):
            db_backup_path = os.path.join(BACKUP_DIR, f"parameters_db_backup_{timestamp}.db")
            shutil.copy2(PARAMETERS_DB_PATH, db_backup_path)
            logger.info(f"Created database backup at {db_backup_path}")
        
        return backup_path
    
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise

def flatten_parameters(params_dict: Dict[str, Any], parent_key: str = '', flattened: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Recursively flatten a nested parameter dictionary into dot-notation keys.
    
    Args:
        params_dict: Nested parameter dictionary
        parent_key: Parent key for recursion
        flattened: Output dictionary (created if None)
        
    Returns:
        Dict[str, Any]: Flattened parameter dictionary
    """
    if flattened is None:
        flattened = {}
        
    for key, value in params_dict.items():
        new_key = f"{parent_key}.{key}" if parent_key else key
        
        if isinstance(value, dict) and not any(k.startswith('_') for k in value.keys()):
            # It's a nested parameter section, recurse
            flatten_parameters(value, new_key, flattened)
        else:
            # It's a leaf parameter, add it to flattened dict
            flattened[new_key] = value
            
    return flattened

def get_data_type(value: Any) -> str:
    """
    Get the data type of a value as a string.
    
    Args:
        value: Value to check
        
    Returns:
        str: Data type as a string
    """
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, list):
        return "list"
    elif isinstance(value, dict):
        return "dict"
    else:
        return "unknown"

def migrate_parameters() -> None:
    """
    Migrate parameters from the in-memory system to the database with
    hierarchical structure and versioning.
    """
    try:
        # First create a backup
        backup_path = create_backup()
        
        # Initialize the database
        initialize_database()
        
        # Get current parameters
        params = get_parameters()
        
        # Extract the base parameters dictionary
        if hasattr(params, "_parameters"):
            params_dict = params._parameters
        else:
            # Access the BASE_PARAMETERS directly from the class
            params_dict = FinancialParameters.BASE_PARAMETERS
        
        # Flatten parameters for database storage
        flattened_params = flatten_parameters(params_dict)
        
        # Insert parameters into database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            
            try:
                # Insert each parameter
                for path, value in flattened_params.items():
                    # Get data type
                    data_type = get_data_type(value)
                    
                    # Convert value to JSON string
                    if data_type in ("list", "dict"):
                        value_str = json.dumps(value)
                    else:
                        value_str = str(value)
                    
                    # Check if parameter already exists before inserting
                    cursor.execute("SELECT id FROM parameters WHERE path = ?", (path,))
                    existing_param = cursor.fetchone()
                    
                    if existing_param:
                        # Update existing parameter
                        cursor.execute(
                            "UPDATE parameters SET value = ?, data_type = ?, updated_at = ? WHERE id = ?",
                            (value_str, data_type, current_time, existing_param['id'])
                        )
                        parameter_id = existing_param['id']
                    else:
                        # Insert new parameter
                        cursor.execute(
                            "INSERT INTO parameters (path, value, data_type, source, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (path, value_str, data_type, ParameterSource.DEFAULT, current_time, current_time)
                        )
                        parameter_id = cursor.lastrowid
                    
                    # parameter_id is already set in the if/else above
                    
                    # Create metadata entry
                    # Attempt to get metadata from existing parameters if available
                    description = "Migrated parameter"
                    user_overridable = False
                    regulatory = False
                    volatility = 0.0
                    confidence = 1.0
                    
                    # Try to extract path components for better descriptions
                    path_parts = path.split('.')
                    if len(path_parts) > 1:
                        if 'asset_returns' in path_parts:
                            description = f"Return rate for {path.replace('asset_returns.', '')}"
                            user_overridable = True
                            volatility = 0.1  # Default volatility for returns
                        elif 'inflation' in path_parts:
                            description = f"Inflation rate for {path.replace('inflation.', '')}"
                            user_overridable = True
                            volatility = 0.05  # Default volatility for inflation
                        elif 'tax' in path_parts:
                            description = f"Tax rate/threshold for {path.replace('tax.', '')}"
                            regulatory = True
                            user_overridable = False
                    
                    # Insert metadata
                    cursor.execute(
                        "INSERT INTO parameter_metadata (parameter_id, name, description, user_overridable, "
                        "regulatory, volatility, confidence, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (parameter_id, path_parts[-1], description, user_overridable, 
                        regulatory, volatility, confidence, current_time)
                    )
                    
                    # Create initial version
                    cursor.execute(
                        "INSERT INTO parameter_versions (parameter_id, value, source, reason, created_at) VALUES (?, ?, ?, ?, ?)",
                        (parameter_id, value_str, ParameterSource.DEFAULT, "Initial migration", current_time)
                    )
                
                # Record the migration
                cursor.execute(
                    "INSERT INTO migration_history (version, description, applied_at, backup_file) VALUES (?, ?, ?, ?)",
                    (VERSION, "Initial migration of financial parameters to hierarchical structure", current_time, backup_path)
                )
                
                # Commit transaction
                conn.commit()
                logger.info(f"Successfully migrated {len(flattened_params)} parameters to hierarchical structure")
                
            except Exception as e:
                # Rollback transaction on error
                conn.rollback()
                logger.error(f"Error during migration, rolled back: {e}")
                raise
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

def rollback_migration(backup_file: str) -> None:
    """
    Rollback to a previous backup.
    
    Args:
        backup_file: Path to the backup file
    """
    try:
        # Verify backup file exists
        if not os.path.exists(backup_file):
            logger.error(f"Backup file not found: {backup_file}")
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        # Load backup data
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Check if this is a valid backup file
        if "parameters" not in backup_data or "version" not in backup_data:
            logger.error(f"Invalid backup file format: {backup_file}")
            raise ValueError(f"Invalid backup file format: {backup_file}")
        
        logger.info(f"Rolling back to backup version {backup_data['version']} created at {backup_data['timestamp']}")
        
        # Extract database backup filename from the same timestamp if available
        timestamp = backup_data['timestamp']
        db_backup_path = os.path.join(BACKUP_DIR, f"parameters_db_backup_{timestamp}.db")
        
        # If database backup exists and database exists, restore it
        if os.path.exists(db_backup_path) and os.path.exists(PARAMETERS_DB_PATH):
            # Make sure no database connections are active
            try:
                # Force close any open connections
                conn = sqlite3.connect(PARAMETERS_DB_PATH)
                conn.close()
            except:
                pass
                
            # Backup current database before rollback
            current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_db_backup = os.path.join(BACKUP_DIR, f"pre_rollback_db_{current_timestamp}.db")
            shutil.copy2(PARAMETERS_DB_PATH, current_db_backup)
            logger.info(f"Backed up current database to {current_db_backup}")
            
            # Remove current database to avoid file locks
            os.remove(PARAMETERS_DB_PATH)
            
            # Restore database from backup
            shutil.copy2(db_backup_path, PARAMETERS_DB_PATH)
            logger.info(f"Restored database from {db_backup_path}")
            
            # Verify by opening and checking the database
            conn = sqlite3.connect(PARAMETERS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            if result and result[0] == 'ok':
                logger.info("Database integrity verified after restore")
            else:
                logger.warning(f"Database integrity check returned: {result}")
            conn.close()
        
        logger.info("Rollback completed successfully")
    
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise

def main():
    """
    Main function to parse arguments and run the appropriate action.
    """
    parser = argparse.ArgumentParser(description="Financial Parameters Migration Tool")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--backup-only", action="store_true", help="Create a backup without migration")
    group.add_argument("--migrate", action="store_true", help="Perform the migration (default)")
    group.add_argument("--rollback", metavar="BACKUP_FILE", help="Rollback to a specified backup file")
    
    args = parser.parse_args()
    
    try:
        if args.backup_only:
            backup_path = create_backup()
            print(f"Backup created successfully: {backup_path}")
        elif args.rollback:
            rollback_migration(args.rollback)
            print("Rollback completed successfully")
        else:  # Default is to migrate
            migrate_parameters()
            print("Migration completed successfully")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

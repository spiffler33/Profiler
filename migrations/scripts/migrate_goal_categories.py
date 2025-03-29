#!/usr/bin/env python3
"""
Migration script for updating the goal_categories table with Indian financial context fields.
Adds Indian-specific fields and common financial goal categories for Indian users.

This script:
1. Backs up the existing data
2. Alters the table to add new columns for Indian financial context:
   - category_priority (integer)
   - typical_timeframe_years (integer)
   - requires_sip (boolean)
   - applicable_tax_section (string - for Indian tax sections like 80C, 80D)
3. Updates existing data with appropriate values for new fields
4. Adds common Indian financial goal categories if they don't exist
5. Logs migration results to /logs/goal_migration.log

Usage:
    python migrate_goal_categories.py

To rollback (if needed):
    python migrate_goal_categories.py --rollback
"""

import os
import sys
import sqlite3
import argparse
import logging
from datetime import datetime
import json

# Configure logging
LOG_FILE = "/Users/coddiwomplers/Desktop/Python/Profiler4/logs/goal_migration.log"

# Ensure log directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE)
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db"
BACKUP_DIR = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/backups"

def backup_database():
    """Create a backup of the database before making changes"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"profiles_backup_{timestamp}.db")
    
    try:
        # Copy the database file
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        logger.info(f"Database backup created at: {backup_path}")
        
        # Also create a JSON backup of the goal_categories table
        backup_categories_to_json(timestamp)
        
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create database backup: {str(e)}")
        sys.exit(1)

def backup_categories_to_json(timestamp):
    """Backup the goal_categories table to JSON"""
    json_path = os.path.join(BACKUP_DIR, f"goal_categories_backup_{timestamp}.json")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM goal_categories")
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        categories = [dict(row) for row in rows]
        
        with open(json_path, 'w') as f:
            json.dump(categories, f, indent=4)
            
        logger.info(f"Goal categories backup created at: {json_path}")
        conn.close()
    except Exception as e:
        logger.error(f"Failed to backup goal categories to JSON: {str(e)}")

def migrate_table():
    """Migrate the goal_categories table to add Indian financial context fields"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Check if the columns already exist
        cursor.execute("PRAGMA table_info(goal_categories)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 2. Add new hierarchical columns if they don't exist (for backward compatibility)
        if 'hierarchy_level' not in columns:
            logger.info("Adding hierarchy_level column to goal_categories table")
            cursor.execute("ALTER TABLE goal_categories ADD COLUMN hierarchy_level INTEGER")
        else:
            logger.info("hierarchy_level column already exists")
            
        if 'parent_category_id' not in columns:
            logger.info("Adding parent_category_id column to goal_categories table")
            cursor.execute("ALTER TABLE goal_categories ADD COLUMN parent_category_id INTEGER REFERENCES goal_categories(id)")
        else:
            logger.info("parent_category_id column already exists")
        
        # 3. Add new Indian-specific columns if they don't exist
        if 'category_priority' not in columns:
            logger.info("Adding category_priority column to goal_categories table")
            cursor.execute("ALTER TABLE goal_categories ADD COLUMN category_priority INTEGER DEFAULT 5")
        else:
            logger.info("category_priority column already exists")
            
        if 'typical_timeframe_years' not in columns:
            logger.info("Adding typical_timeframe_years column to goal_categories table")
            cursor.execute("ALTER TABLE goal_categories ADD COLUMN typical_timeframe_years INTEGER")
        else:
            logger.info("typical_timeframe_years column already exists")
            
        if 'requires_sip' not in columns:
            logger.info("Adding requires_sip column to goal_categories table")
            cursor.execute("ALTER TABLE goal_categories ADD COLUMN requires_sip BOOLEAN DEFAULT 0")
        else:
            logger.info("requires_sip column already exists")
            
        if 'applicable_tax_section' not in columns:
            logger.info("Adding applicable_tax_section column to goal_categories table")
            cursor.execute("ALTER TABLE goal_categories ADD COLUMN applicable_tax_section TEXT")
        else:
            logger.info("applicable_tax_section column already exists")
        
        # 4. Update existing data - maintain backward compatibility with hierarchy levels
        logger.info("Updating existing records with hierarchy levels (for backward compatibility)")
        cursor.execute("""
            UPDATE goal_categories
            SET hierarchy_level = CASE
                WHEN is_foundation = 1 THEN 1  -- Security (level 1)
                ELSE 6  -- Custom (level 6) as default for existing categories
            END
            WHERE hierarchy_level IS NULL
        """)
        
        conn.commit()
        logger.info("Schema migration completed successfully")
        conn.close()
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)

def rollback_migration(backup_path):
    """Rollback the migration using the provided backup"""
    if not os.path.exists(backup_path):
        logger.error(f"Backup file not found: {backup_path}")
        sys.exit(1)
        
    try:
        import shutil
        shutil.copy2(backup_path, DB_PATH)
        logger.info(f"Rolled back to backup: {backup_path}")
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        sys.exit(1)

def list_backups():
    """List available backups"""
    if not os.path.exists(BACKUP_DIR):
        logger.info("No backups found (backup directory does not exist)")
        return
        
    backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith("profiles_backup_") and f.endswith(".db")]
    
    if not backups:
        logger.info("No backups found")
        return
        
    logger.info("Available backups:")
    for backup in sorted(backups):
        backup_path = os.path.join(BACKUP_DIR, backup)
        file_size = os.path.getsize(backup_path) / (1024 * 1024)  # Size in MB
        logger.info(f"  {backup} ({file_size:.2f} MB)")

def initialize_indian_goal_categories():
    """Initialize the table with common Indian financial goal categories"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Define the Indian financial goal categories with appropriate values
        # Ensuring consistency with existing goal types in the application
        categories = [
            {
                "name": "education",
                "description": "Saving for children's higher education (80C tax benefit)",
                "category_priority": 1,
                "typical_timeframe_years": 15,
                "requires_sip": 1,
                "applicable_tax_section": "80C",
                "hierarchy_level": 2
            },
            {
                "name": "wedding",
                "description": "Saving for wedding expenses",
                "category_priority": 2,
                "typical_timeframe_years": 8,
                "requires_sip": 1,
                "applicable_tax_section": None,
                "hierarchy_level": 3
            },
            {
                "name": "home_purchase",
                "description": "Saving for property acquisition (80C tax benefit)",
                "category_priority": 1,
                "typical_timeframe_years": 10,
                "requires_sip": 1,
                "applicable_tax_section": "80C",
                "hierarchy_level": 2
            },
            {
                "name": "retirement",
                "description": "Saving for post-retirement income (80C, 80CCD tax benefits)",
                "category_priority": 1,
                "typical_timeframe_years": 25,
                "requires_sip": 1,
                "applicable_tax_section": "80C,80CCD",
                "hierarchy_level": 1
            },
            {
                "name": "emergency_fund",
                "description": "Liquid funds for unexpected expenses",
                "category_priority": 1,
                "typical_timeframe_years": 1,
                "requires_sip": 0,
                "applicable_tax_section": None,
                "hierarchy_level": 1
            },
            {
                "name": "debt_repayment",
                "description": "Paying off outstanding debts",
                "category_priority": 1,
                "typical_timeframe_years": 5,
                "requires_sip": 1,
                "applicable_tax_section": None,
                "hierarchy_level": 2
            },
            {
                "name": "charitable_giving",
                "description": "Donations and philanthropy (80G tax benefit)",
                "category_priority": 3,
                "typical_timeframe_years": 1,
                "requires_sip": 0,
                "applicable_tax_section": "80G",
                "hierarchy_level": 5
            },
            {
                "name": "legacy_planning",
                "description": "Planning for wealth transfer",
                "category_priority": 3,
                "typical_timeframe_years": 20,
                "requires_sip": 1,
                "applicable_tax_section": None,
                "hierarchy_level": 5
            },
            {
                "name": "tax_optimization",
                "description": "Investments for tax efficiency (80C, 80D, 80G tax benefits)",
                "category_priority": 2,
                "typical_timeframe_years": 3,
                "requires_sip": 0,
                "applicable_tax_section": "80C,80D,80G",
                "hierarchy_level": 3
            }
        ]
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goal_categories'")
        if not cursor.fetchone():
            logger.error("goal_categories table doesn't exist, cannot initialize categories")
            conn.close()
            return False

        # For each category, insert if it doesn't already exist
        categories_added = 0
        categories_updated = 0
        
        for category in categories:
            # Check if category already exists
            cursor.execute("SELECT id FROM goal_categories WHERE name = ?", (category["name"],))
            existing = cursor.fetchone()
            
            if existing:
                # Category exists, update with new field values
                category_id = existing[0]
                cursor.execute("""
                    UPDATE goal_categories
                    SET description = ?,
                        category_priority = ?,
                        typical_timeframe_years = ?,
                        requires_sip = ?,
                        applicable_tax_section = ?,
                        hierarchy_level = ?
                    WHERE id = ?
                """, (
                    category["description"],
                    category["category_priority"],
                    category["typical_timeframe_years"],
                    category["requires_sip"],
                    category["applicable_tax_section"],
                    category["hierarchy_level"],
                    category_id
                ))
                categories_updated += 1
                logger.info(f"Updated existing category: {category['name']}")
            else:
                # Category doesn't exist, insert it
                cursor.execute("""
                    INSERT INTO goal_categories
                    (name, description, category_priority, typical_timeframe_years, requires_sip, 
                    applicable_tax_section, hierarchy_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    category["name"],
                    category["description"],
                    category["category_priority"],
                    category["typical_timeframe_years"],
                    category["requires_sip"],
                    category["applicable_tax_section"],
                    category["hierarchy_level"]
                ))
                categories_added += 1
                logger.info(f"Added new category: {category['name']}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Initialized goal categories: {categories_added} added, {categories_updated} updated")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Indian goal categories: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    parser = argparse.ArgumentParser(description="Migrate goal_categories table for Indian financial context")
    parser.add_argument("--rollback", help="Rollback to specified backup file", metavar="BACKUP_FILE")
    parser.add_argument("--list-backups", action="store_true", help="List available backups")
    parser.add_argument("--skip-categories", action="store_true", help="Skip adding Indian financial goal categories")
    
    args = parser.parse_args()
    
    if args.list_backups:
        list_backups()
        return
    
    if args.rollback:
        backup_path = args.rollback
        if not os.path.isabs(backup_path):
            # If not absolute path, assume it's in the backup directory
            backup_path = os.path.join(BACKUP_DIR, backup_path)
        rollback_migration(backup_path)
        return
    
    logger.info("Starting migration of goal_categories table for Indian financial context")
    backup_path = backup_database()
    migrate_table()
    
    if not args.skip_categories:
        logger.info("Initializing Indian financial goal categories")
        if initialize_indian_goal_categories():
            logger.info("Indian financial goal categories initialized successfully")
        else:
            logger.warning("Failed to initialize Indian financial goal categories")
    
    logger.info("Goal categories table migration completed successfully")

if __name__ == "__main__":
    main()
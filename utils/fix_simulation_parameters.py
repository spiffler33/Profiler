#!/usr/bin/env python3
"""
Script to fix NULL simulation_parameters_json values in migrated goals.

This script:
1. Connects to the profiles database
2. Identifies goals with NULL simulation_parameters_json
3. Creates sensible default parameters based on goal category
4. Updates the goals with the new parameters
5. Validates the results
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/goal_migration_fix.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "data/profiles.db"
BACKUP_DIR = "data/backups"

def create_backup():
    """Create a backup of the profiles database before making changes."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, f"profiles_backup_{timestamp}.db")
    
    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        logger.info(f"Created database backup at {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        sys.exit(1)

def get_default_parameters(category, title=""):
    """
    Get default simulation parameters based on goal category.
    
    Args:
        category: Goal category
        title: Goal title for additional context
        
    Returns:
        dict: Default simulation parameters
    """
    # Current timestamp
    current_time = datetime.now().isoformat()
    
    # Base parameters for all goals
    base_params = {
        "simulation_version": "1.0.0",
        "created_at": current_time,
        "simulation_count": 1000,
        "time_horizon_years": 10,
        "confidence_level": 0.95,
        "asset_allocations": {
            "equity": 0.6,
            "debt": 0.3,
            "gold": 0.1
        },
        "return_assumptions": {
            "equity": {
                "mean": 12.0,
                "std_dev": 18.0
            },
            "debt": {
                "mean": 7.0,
                "std_dev": 5.0
            },
            "gold": {
                "mean": 8.0,
                "std_dev": 15.0
            }
        },
        "inflation_assumption": 5.0,
        "tax_rate": 20.0,
        "is_india_specific": True
    }
    
    # Category-specific overrides
    category_specific = {}
    
    if "retirement" in category.lower() or "retirement" in title.lower():
        category_specific = {
            "time_horizon_years": 25,
            "asset_allocations": {
                "equity": 0.7,
                "debt": 0.25,
                "gold": 0.05
            },
            "withdrawal_rate": 4.0,
            "retirement_age": 60,
            "epf_included": True,
            "nps_included": True
        }
    elif "education" in category.lower() or "education" in title.lower():
        category_specific = {
            "time_horizon_years": 15,
            "education_inflation": 8.0,
            "asset_allocations": {
                "equity": 0.65,
                "debt": 0.3,
                "gold": 0.05
            }
        }
    elif "home" in category.lower() or "home" in title.lower():
        category_specific = {
            "time_horizon_years": 7,
            "asset_allocations": {
                "equity": 0.5,
                "debt": 0.4,
                "gold": 0.1
            },
            "property_inflation": 6.0,
            "down_payment_percentage": 20.0
        }
    elif "emergency" in category.lower() or "emergency" in title.lower():
        category_specific = {
            "time_horizon_years": 1,
            "asset_allocations": {
                "equity": 0.1,
                "debt": 0.8,
                "gold": 0.1
            },
            "months_of_expenses": 6
        }
    elif "car" in category.lower() or "vehicle" in category.lower() or "car" in title.lower():
        category_specific = {
            "time_horizon_years": 5,
            "asset_allocations": {
                "equity": 0.4,
                "debt": 0.5,
                "gold": 0.1
            }
        }
    
    # Merge base parameters with category-specific ones
    import copy
    merged_params = copy.deepcopy(base_params)
    
    for key, value in category_specific.items():
        if isinstance(value, dict) and key in merged_params and isinstance(merged_params[key], dict):
            merged_params[key].update(value)
        else:
            merged_params[key] = value
    
    return merged_params

def fix_simulation_parameters():
    """Fix NULL simulation_parameters_json values in goals table."""
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find goals with NULL simulation_parameters_json
        cursor.execute("SELECT id, category, title FROM goals WHERE simulation_parameters_json IS NULL OR simulation_parameters_json = ''")
        goals_to_fix = cursor.fetchall()
        
        if not goals_to_fix:
            logger.info("No goals found with NULL simulation_parameters_json. No fixes needed.")
            return 0
        
        logger.info(f"Found {len(goals_to_fix)} goals with NULL simulation_parameters_json")
        
        # Update each goal with appropriate parameters
        updated_count = 0
        for goal in goals_to_fix:
            goal_id = goal['id']
            category = goal['category']
            title = goal['title']
            
            # Get appropriate parameters for this goal
            params = get_default_parameters(category, title)
            params_json = json.dumps(params)
            
            # Update the goal
            cursor.execute(
                "UPDATE goals SET simulation_parameters_json = ?, updated_at = ? WHERE id = ?",
                (params_json, datetime.now().isoformat(), goal_id)
            )
            
            updated_count += 1
            logger.info(f"Updated goal {goal_id} ({title}) with simulation parameters")
        
        # Commit changes
        conn.commit()
        logger.info(f"Successfully updated {updated_count} goals with simulation parameters")
        
        # Validate results
        cursor.execute("SELECT COUNT(*) FROM goals WHERE simulation_parameters_json IS NULL OR simulation_parameters_json = ''")
        remaining_null = cursor.fetchone()[0]
        
        conn.close()
        
        if remaining_null > 0:
            logger.warning(f"There are still {remaining_null} goals with NULL simulation_parameters_json")
        else:
            logger.info("All goals now have valid simulation_parameters_json")
        
        return updated_count
    
    except Exception as e:
        logger.error(f"Error fixing simulation parameters: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return -1

def validate_json_fields():
    """Validate all JSON fields in goals table to ensure they contain valid JSON."""
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all goals
        cursor.execute("SELECT id, title, simulation_data, scenarios, adjustments, simulation_parameters_json FROM goals")
        goals = cursor.fetchall()
        
        logger.info(f"Validating JSON fields for {len(goals)} goals")
        
        validation_results = {
            "total_goals": len(goals),
            "invalid_fields": {
                "simulation_data": 0,
                "scenarios": 0,
                "adjustments": 0,
                "simulation_parameters_json": 0
            }
        }
        
        # Check each goal's JSON fields
        for goal in goals:
            goal_id = goal['id']
            title = goal['title']
            
            for field in ['simulation_data', 'scenarios', 'adjustments', 'simulation_parameters_json']:
                if goal[field]:
                    try:
                        json.loads(goal[field])
                    except json.JSONDecodeError:
                        logger.warning(f"Goal {goal_id} ({title}) has invalid JSON in {field}")
                        validation_results["invalid_fields"][field] += 1
        
        conn.close()
        
        # Print validation summary
        logger.info("JSON Field Validation Results:")
        for field, count in validation_results["invalid_fields"].items():
            status = "✓ Valid" if count == 0 else f"✗ Invalid ({count} goals)"
            logger.info(f"  {field}: {status}")
        
        return validation_results
    
    except Exception as e:
        logger.error(f"Error validating JSON fields: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def main():
    """Main function to fix simulation parameters and validate results."""
    print("Starting simulation parameters fix...")
    
    # First create a backup
    backup_path = create_backup()
    print(f"Created backup at: {backup_path}")
    
    # Fix simulation parameters
    updated_count = fix_simulation_parameters()
    
    if updated_count == -1:
        print("Error fixing simulation parameters. See log for details.")
        sys.exit(1)
    
    if updated_count == 0:
        print("No goals needed fixing. All simulation parameters are already populated.")
    else:
        print(f"Successfully updated {updated_count} goals with simulation parameters")
    
    # Validate JSON fields
    print("\nValidating JSON fields in all goals...")
    validation_results = validate_json_fields()
    
    if validation_results:
        invalid_count = sum(validation_results["invalid_fields"].values())
        if invalid_count == 0:
            print("✓ All JSON fields are valid")
        else:
            print(f"✗ Found {invalid_count} goals with invalid JSON fields")
            for field, count in validation_results["invalid_fields"].items():
                if count > 0:
                    print(f"  - {field}: {count} goals affected")
    
    print("\nCleanup complete! See logs/goal_migration_fix.log for details.")

if __name__ == "__main__":
    main()
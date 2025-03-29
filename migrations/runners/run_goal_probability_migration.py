#!/usr/bin/env python3
"""
Runner script for the goal probability fields migration.

This script provides a command-line interface to run the goal probability migration
that adds enhanced probability analysis fields to existing goals.

The migration adds the following fields to the goals table:
- simulation_data (TEXT) - JSON-serialized Monte Carlo simulation results
- scenarios (TEXT) - JSON-serialized alternative scenarios for the goal
- adjustments (TEXT) - JSON-serialized recommended adjustments to improve success probability
- last_simulation_time (TIMESTAMP) - When the simulation was last run
- simulation_parameters_json (TEXT) - Parameters used for simulation

Usage:
    python run_goal_probability_migration.py [--dry-run] [--categories CATEGORY1,CATEGORY2] [--backup-only] [--validate-only] [--rollback TIMESTAMP]

Options:
    --dry-run           Run the migration in simulation mode without saving changes
    --categories        Comma-separated list of goal categories to process (default: all)
    --backup-only       Create a backup without performing migration
    --validate-only     Only run validation queries, don't migrate
    --rollback          Rollback to a specified backup timestamp (YYYYMMDD_HHMMSS)
    --help              Show this help message and exit
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.goal_data_migrator import (
    migrate_goals, 
    print_report_summary, 
    save_report,
    GoalManager
)
from migrations.enhance_probability_fields import (
    create_backup,
    add_new_columns,
    validate_migration,
    save_validation_results,
    rollback_migration
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/goal_migration.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Goal Probability Fields Migration Runner"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in simulation mode without saving changes"
    )
    parser.add_argument(
        "--categories",
        type=str,
        help="Comma-separated list of goal categories to process (default: all)"
    )
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Create a backup without performing migration"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run validation without migration"
    )
    parser.add_argument(
        "--rollback",
        metavar="TIMESTAMP",
        help="Rollback to specified backup (YYYYMMDD_HHMMSS)"
    )
    
    return parser.parse_args()

def filter_goals_by_category(goal_manager, categories):
    """
    Filter goals by category.
    
    Args:
        goal_manager: GoalManager instance
        categories: Comma-separated list of categories
        
    Returns:
        list: Filtered goals
    """
    all_goals = goal_manager.get_all_goals()
    
    if not categories:
        return all_goals
    
    category_list = [cat.strip() for cat in categories.split(',')]
    return [goal for goal in all_goals if goal.category in category_list]

def main():
    """Main function to run the goal probability fields migration"""
    args = parse_args()
    
    try:
        # Create logs directory if not exists
        os.makedirs("logs", exist_ok=True)
        
        # Handle backup-only mode
        if args.backup_only:
            timestamp = create_backup()
            print(f"Backup created successfully with timestamp: {timestamp}")
            return
        
        # Handle validate-only mode
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
            for key, value in results['statistics'].items():
                print(f"{key.replace('_', ' ').title()}: {value}")
            
            return
        
        # Handle rollback mode
        if args.rollback:
            rollback_migration(args.rollback)
            print(f"Successfully rolled back to {args.rollback}")
            return
        
        # Start migration
        print("Starting goal probability fields migration...")
        
        # Step 1: Create backup
        timestamp = create_backup()
        print(f"Created backup with timestamp: {timestamp}")
        
        # Step 2: Add new columns to database schema
        print("Adding new columns to goals table...")
        add_new_columns()
        
        # Step 3: Migrate goal data
        goal_manager = GoalManager()
        if args.categories:
            print(f"Filtering goals by categories: {args.categories}")
            goals = filter_goals_by_category(goal_manager, args.categories)
            print(f"Found {len(goals)} goals in specified categories")
        else:
            goals = goal_manager.get_all_goals()
            print(f"Processing all {len(goals)} goals")
        
        if args.dry_run:
            print("Running in dry-run mode (no changes will be saved)")
        
        # Perform the goal data migration
        results = migrate_goals()
        
        # Save and print report
        report_file = save_report(results)
        print_report_summary(results)
        
        # Step 4: Validate migration
        print("Validating migration...")
        validation_results = validate_migration()
        save_validation_results(validation_results, timestamp)
        
        # Print validation summary
        null_count = sum(validation_results["null_values"].values())
        invalid_count = sum(validation_results["invalid_values"].values())
        
        if null_count > 0 or invalid_count > 0:
            print("\nWARNING: Validation found issues that should be addressed:")
            if null_count > 0:
                print(f"- {null_count} NULL values found in new columns")
            if invalid_count > 0:
                print(f"- {invalid_count} invalid values found")
            print(f"\nSee data/backups/parameters/validation_results_{timestamp}.json for details")
            print("You may need to run additional clean-up steps or manually fix these issues.")
        else:
            print("\n✓ Migration completed successfully with no validation issues!")
        
        print(f"\nIf you need to rollback, run: python run_goal_probability_migration.py --rollback {timestamp}")
        print(f"\nMigration completed. Full report saved to {report_file}")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        print(f"Error: Migration failed - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
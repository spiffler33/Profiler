# Goal Categories Hierarchical Structure Migration

This document provides instructions on how to migrate the goal categories in the Profiler4 application to the new hierarchical structure.

## Overview

The migration adds a hierarchical structure to goal categories with six predefined levels:

1. **Security** (Level 1) - For emergency fund, insurance goals, and tax optimization
2. **Essential** (Level 2) - For home purchase, education, and debt repayment goals
3. **Retirement** (Level 3) - For retirement and early retirement planning
4. **Lifestyle** (Level 4) - For wedding, travel, vehicles, etc.
5. **Legacy** (Level 5) - For legacy planning, charitable giving
6. **Custom** (Level 6) - For user-defined goals

The consistent goal types across the application are:
- retirement/early_retirement
- education
- emergency_fund
- home_purchase
- debt_repayment
- wedding
- charitable_giving
- legacy_planning
- tax_optimization

The migration process:
1. Adds new database columns to support the hierarchy
2. Populates the database with the predefined categories
3. Maps existing categories to the appropriate parent categories

## Migration Steps

### 1. Backup Your Database

Before running the migration, make sure to back up your database:

```bash
cp /Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db /Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles_backup.db
```

The migration scripts also create automatic backups, but it's good practice to make a manual backup as well.

### 2. Run the Migration

You can use the provided runner script which performs all necessary steps:

```bash
python run_goal_categories_migration.py
```

This script will:
- Check if the migration is needed
- Run the database schema migration if necessary
- Initialize the predefined categories
- Map existing categories to their parent categories

### Options

- `--check-only`: Just check if migration is needed without making changes
- `--force-update`: Force update of existing categories to match predefined values

```bash
# To check if migration is needed
python run_goal_categories_migration.py --check-only

# To force update existing categories
python run_goal_categories_migration.py --force-update
```

### 3. Verify the Migration

After running the migration, you can verify that it completed successfully by querying the database:

```bash
sqlite3 /Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db "SELECT id, name, hierarchy_level, parent_category_id FROM goal_categories ORDER BY hierarchy_level, order_index"
```

## Manual Migration (if needed)

If you prefer to run the migration steps manually:

### 1. Run the Database Schema Migration

```bash
python migrate_goal_categories.py
```

This adds the necessary columns to the database schema.

### 2. Initialize Predefined Categories

In Python code:

```python
from models.goal_models import GoalManager
manager = GoalManager()
manager.initialize_predefined_categories()
```

## Rollback (if needed)

The migration script creates backups before making changes. To list available backups:

```bash
python migrate_goal_categories.py --list-backups
```

To rollback to a specific backup:

```bash
python migrate_goal_categories.py --rollback profiles_backup_20250318_123456.db
```

## Technical Details

### New Database Columns

The migration adds two new columns to the `goal_categories` table:

- `hierarchy_level`: Integer representing priority level (1-6, lower = higher priority)
- `parent_category_id`: Foreign key reference to parent category (NULL for top-level categories)

### GoalCategory Class Changes

The `GoalCategory` class has been updated with:

- Constants for hierarchy levels (`SECURITY`, `ESSENTIAL`, etc.)
- New fields for hierarchy_level and parent_category_id
- Backward compatibility with existing code

### New GoalManager Methods

- `get_categories_by_hierarchy_level(level)`: Returns categories at the specified hierarchy level
- `initialize_predefined_categories(force_update=False)`: Populates the database with predefined categories
# Migrations

This directory contains all database migration scripts and runners for the application.

## Structure

- `scripts/`: Contains the core migration logic
  - `migrate_profiles.py`: Profile table migration
  - `migrate_goal_categories.py`: Goal categories migration
  - `migrate_financial_parameters.py`: Financial parameters migration
  - `migrate_goals_table.py`: Goals table migration

- `runners/`: Contains scripts that execute migrations
  - `run_goal_categories_migration.py`: Runner for goal categories migration
  - `run_financial_parameters_migration.py`: Runner for financial parameters migration

## Usage

The migration scripts should be run in the following order:

1. Financial parameters migration
2. Goal categories migration
3. Goals table migration
4. Profiles migration

Use the runner scripts to execute migrations with proper error handling and logging.
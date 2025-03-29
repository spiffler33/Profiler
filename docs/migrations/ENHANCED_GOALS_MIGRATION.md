# Enhanced Goals Migration Guide

This document describes the migration plan to upgrade the Goals functionality with new fields and capabilities.

## Migration Overview

1. **Backup**: Create a backup of the database before migration
2. **Schema Migration**: Add new fields to goals table with NULL constraints
3. **Data Migration**: Populate new fields with sensible defaults
4. **Validation**: Verify data integrity post-migration
5. **Rollback Plan**: Implement mechanism to revert changes if needed

## New Goal Fields

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `current_progress` | REAL | Percentage progress towards goal (0-100) | Calculated based on `current_amount`/`target_amount` |
| `priority_score` | REAL | Calculated priority score | Based on importance and flexibility |
| `additional_funding_sources` | TEXT | Other funding sources beyond regular savings | Empty string |
| `goal_success_probability` | REAL | Estimated probability of achieving goal (0-100) | Based on current progress |
| `adjustments_required` | BOOLEAN | Flag indicating goal needs adjustment | FALSE |
| `funding_strategy` | TEXT | JSON-encoded funding approach | Empty string |

## Migration Script Usage

The migration is handled by the `migrate_goals_table.py` script with the following options:

```bash
# Run full migration
python migrate_goals_table.py

# Create backup only without migration
python migrate_goals_table.py --backup-only

# Run validation without migration
python migrate_goals_table.py --validate-only

# Rollback to previous backup
python migrate_goals_table.py --rollback TIMESTAMP
```

## Migration Steps

### 1. Backup Creation

The script creates two backup files:
- Full database backup: `profiles_backup_TIMESTAMP.db`
- Goals table JSON export: `goals_backup_TIMESTAMP.json`

### 2. Schema Migration

The script adds new columns to the goals table with appropriate default values and NULL constraints.

SQL example:
```sql
ALTER TABLE goals ADD COLUMN current_progress REAL DEFAULT 0.0;
ALTER TABLE goals ADD COLUMN priority_score REAL DEFAULT 0.0;
ALTER TABLE goals ADD COLUMN additional_funding_sources TEXT DEFAULT '';
ALTER TABLE goals ADD COLUMN goal_success_probability REAL DEFAULT 0.0;
ALTER TABLE goals ADD COLUMN adjustments_required BOOLEAN DEFAULT 0;
ALTER TABLE goals ADD COLUMN funding_strategy TEXT DEFAULT '';
```

### 3. Data Migration

For existing goals, default values are applied:

1. **current_progress**: Calculated as `(current_amount / target_amount) * 100.0`
2. **priority_score**: Calculated based on:
   - Importance: high (70), medium (50), low (30)
   - Flexibility: fixed (20), somewhat_flexible (10), very_flexible (5)
3. **goal_success_probability**: Based on current progress:
   - > 75% progress: 90% probability
   - > 50% progress: 70% probability
   - > 25% progress: 50% probability
   - <= 25% progress: 30% probability
4. **adjustments_required**: Default to FALSE (0)
5. **additional_funding_sources**, **funding_strategy**: Default to empty string

### 4. Validation

The script runs validation queries to ensure data integrity:
- Check for NULL values in new columns
- Verify values are within appropriate ranges
- Generate statistics for review

A validation report is saved as `validation_results_TIMESTAMP.json`

## Rollback Procedure

If issues are encountered, the migration can be rolled back:

```bash
python migrate_goals_table.py --rollback TIMESTAMP
```

This restores the database from the backup created at the beginning of migration.

## Compatibility

The Goal class in `goal_models.py` already implements backward compatibility:
- Legacy getters map old field names to new ones
- `from_legacy_dict()` method for handling old formats
- `to_dict(legacy_mode=True)` for legacy output format

## Testing with Production Data

Before running on production:

1. Create a copy of the production database
2. Run migration against the copy
3. Run validation to check for issues
4. Test application functionality with migrated data
5. If successful, run on production

## Post-Migration Verification

After migration, verify:
1. All goals have appropriate values for new fields
2. No NULL values exist in required fields
3. Applications using goal data function properly
4. Goals API returns proper data
5. UI displays new goal attributes correctly

## Troubleshooting

Common issues and solutions:

1. **SQL Errors**: May indicate schema incompatibility. Check database version.
2. **NULL Values**: Run data migration step again with `--validate-only` to find affected rows.
3. **Rollback Errors**: Ensure backup files exist at specified path.
4. **Invalid Data**: Check for goals with unusual values (e.g., negative amounts).
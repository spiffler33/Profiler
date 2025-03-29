# Financial Parameters Migration Guide

This document describes the migration process for the financial parameters system from a flat structure to a hierarchical database-backed structure with versioning capabilities.

## Overview

The migration process includes:

1. **Backup Creation**: Automated backup of all current parameter values
2. **Database Setup**: Creation of a SQLite database with proper schema for hierarchical parameters
3. **Migration**: Conversion of flat parameters to hierarchical structure with metadata
4. **Versioning**: Implementation of versioning system for tracking parameter changes 
5. **Rollback Capability**: Ability to restore from backups if needed

## Database Schema

The new database schema includes the following tables:

- `parameters`: Stores parameter paths, values, and metadata
- `parameter_metadata`: Stores detailed metadata for each parameter
- `parameter_questions`: Maps parameters to input questions that can provide values
- `parameter_versions`: Tracks historical versions of parameter values
- `migration_history`: Tracks migration operations for auditing

## How to Run the Migration

### Quick Start

To run the migration with default settings:

```bash
python run_financial_parameters_migration.py
```

This script will:
- Create a backup of current parameters
- Set up the database schema
- Migrate parameters to the new structure
- Generate comprehensive logs of the process

### Advanced Usage

For more control over the migration process, use the main migration script directly:

```bash
# Create backup only without migration
python migrate_financial_parameters.py --backup-only

# Run migration (default action)
python migrate_financial_parameters.py --migrate

# Rollback to a previous backup
python migrate_financial_parameters.py --rollback data/backups/parameters/parameters_backup_20250319_120000.json
```

## Post-Migration Verification

After migration, you can verify the success of the migration by:

1. Checking the logs for any errors
2. Inspecting the `data/parameters.db` file with SQLite browser
3. Running test_financial_parameters.py to ensure parameters are accessible

## Adapting Your Code

### Accessing Parameters

The parameter access API remains backward compatible. You can continue to use:

```python
from models.financial_parameters import get_parameters

params = get_parameters()
inflation = params.get("inflation.general")
```

For new code, use the hierarchical paths:

```python
equity_large_cap = params.get("asset_returns.equity.large_cap.value") 
```

### Updating Parameters

To update parameters in the new system:

```python
from models.financial_parameters import get_parameters, ParameterSource

params = get_parameters()
params.update_parameter("inflation.general", 0.06, 
                       source=ParameterSource.USER_SPECIFIC,
                       reason="User override")
```

## Troubleshooting

If you encounter issues during or after migration:

1. Check the log files for detailed error messages
2. Verify database permissions and structure
3. Run the rollback command if necessary
4. Contact the development team if problems persist

## Technical Implementation Details

The migration uses these key components:

- `flatten_parameters()`: Converts nested dictionaries to dot-notation paths
- `initialize_database()`: Creates the database schema
- `create_backup()`: Creates backups of current parameters
- `migrate_parameters()`: Handles the migration transaction
- `rollback_migration()`: Restores from backup if needed

All operations are performed in transactions to ensure data integrity.

## Future Enhancements

Planned improvements after the initial migration:

1. Parameter validation rules
2. UI for parameter management
3. Audit logging for parameter changes
4. User-specific parameter overrides
5. Integration with Monte Carlo simulation engine
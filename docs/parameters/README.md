# Financial Parameters Documentation

This directory contains documentation for the Profiler4 financial parameters system.

## Overview

The financial parameters system manages all constants, market assumptions, tax rules, and other numerical values used throughout the application. This system provides:

1. A centralized repository for parameters
2. Version tracking of parameter changes
3. User-specific parameter overrides 
4. Programmatic and UI-based parameter management

## Parameter Management Tools

Profiler4 offers three ways to manage parameters:

### 1. Web Admin Interface

The web admin interface is accessible at `/admin/parameters` for authorized administrators. 
This interface provides:

- Visual parameter browsing and searching
- Parameter editing with validation
- Historical change tracking
- Parameter relationship visualization
- User-specific parameter override management

### 2. REST API

For programmatic access, a comprehensive RESTful API is available:

```
GET /api/v2/parameters?group=market.equity
GET /api/v2/parameters/{parameter_path}
PUT /api/v2/parameters/{parameter_path}
POST /api/v2/parameters
POST /api/v2/parameters/bulk
GET /api/v2/parameters/history/{parameter_path}
DELETE /api/v2/parameters/{parameter_path}
```

All API endpoints are protected with HTTP Basic Authentication.

### 3. Command-line Tools

For automation and script-based management, use the `manage_parameters.py` script:

```
# List parameters 
python manage_parameters.py list --group market.equity

# Get a specific parameter
python manage_parameters.py get market.equity.equity_large_cap

# Set a parameter
python manage_parameters.py set market.equity.equity_large_cap 13.0 --source "annual_review"

# Import parameters from a file
python manage_parameters.py import parameters.json

# Export parameters to a file
python manage_parameters.py export --output parameters.json --format json

# View parameter history
python manage_parameters.py history market.equity.equity_large_cap

# Manage user-specific overrides
python manage_parameters.py user list 123e4567-e89b-12d3-a456-426655440000
python manage_parameters.py user set 123e4567-e89b-12d3-a456-426655440000 market.equity.equity_large_cap 14.5
python manage_parameters.py user reset 123e4567-e89b-12d3-a456-426655440000 market.equity.equity_large_cap
```

## Parameter Structure

Parameters are organized in a hierarchical structure with dot notation:

- `market.equity.equity_large_cap`
- `inflation.general`
- `retirement.withdrawal_rate`
- `tax.income_tax_brackets`

This structure helps organize parameters by domain and allows for grouped operations.

## Parameter Metadata

Each parameter stores metadata including:

- **Description**: Purpose and usage of the parameter
- **Source**: Origin of the parameter value (e.g., research, assumption)
- **History**: Record of previous values with timestamps
- **Is Editable**: Whether users can modify the parameter
- **Is India Specific**: Whether the parameter is specific to Indian markets

## Best Practices

When working with parameters:

1. **Use Parameter Service**: Always access parameters through the `FinancialParameterService`
2. **Document Changes**: Include a source and reason when updating parameters
3. **Consider Impacts**: Assess the impact of parameter changes on calculations
4. **Use Bulk Operations**: When updating multiple related parameters, use bulk operations
5. **Test Changes**: Test the impact of parameter changes before applying in production

## Additional Documentation

- [Parameter Management Guide](PARAMETER_MANAGEMENT_GUIDE.md) - Implementation details
- [Parameter Service Updates](PARAMETER_SERVICE_UPDATES.md) - Service layer functionality
- [Parameter Access Patterns](Parameter_Access_Patterns.md) - Common usage patterns
- [Financial Parameters Optimization](FINANCIAL_PARAMETERS_OPTIMIZATION.md) - Performance considerations
- [Calculator Base Enhancements](CALCULATOR_BASE_ENHANCEMENTS.md) - Integration with calculators
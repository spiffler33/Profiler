# Financial Parameters Management Guide

## Overview

This document outlines how to manage the financial parameters in the Profiler4 system. After migrating from hardcoded parameters to a database-backed system, we need a way to update these parameters without modifying code.

## Implementation Plan for Parameter Management

### 1. Admin Web Interface

We'll create a web-based admin interface for managing financial parameters with these features:

- **Parameter Browser**: View all parameters with filtering by group and search functionality
- **Parameter Editor**: Edit individual parameters with validation and audit logging
- **Bulk Operations**: Import/export parameters via CSV/JSON
- **Versioning**: View parameter history and restore previous versions
- **User-specific Overrides**: Manage profile-specific parameter overrides

### 2. REST API Endpoints

We'll develop a comprehensive API for programmatic parameter management:

```
GET /api/v2/parameters?group=market.equity
GET /api/v2/parameters/{parameter_path}
PUT /api/v2/parameters/{parameter_path}
POST /api/v2/parameters/bulk
GET /api/v2/parameters/history/{parameter_path}
DELETE /api/v2/parameters/{parameter_path}
```

### 3. Command-line Tools

For DevOps and automation, we'll provide CLI tools:

```
python manage_parameters.py list --group market.equity
python manage_parameters.py set market.equity.equity_large_cap 13.0
python manage_parameters.py import parameters.json
python manage_parameters.py export --format json
```

## Implementation Steps

1. **Admin Panel UI Development**:
   - Create Flask routes for parameter admin pages
   - Design responsive UI with parameter grouping and search
   - Implement parameter editing with validation
   - Add user authentication and authorization

2. **API Development**:
   - Design RESTful API for parameter CRUD operations
   - Implement validation and error handling
   - Add authentication and rate limiting
   - Document with OpenAPI/Swagger

3. **Database Service Layer Enhancement**:
   - Extend FinancialParameterService for bulk operations
   - Add parameter validation and type conversion
   - Implement history tracking and rollback capabilities

4. **Command Line Tool**:
   - Develop scriptable CLI for parameter management
   - Support automation and CI/CD integration

5. **Testing**:
   - Unit and integration tests for all components
   - End-to-end testing for admin interface
   - Performance testing for bulk operations

## Detailed Design: Admin Interface

### UI Wireframes

The admin interface will include these main sections:

1. **Dashboard**:
   - Summary statistics of parameters by group
   - Recently changed parameters
   - Parameter health checks (missing or outdated)

2. **Parameter Browser**:
   - Hierarchical tree view by parameter group
   - Table view with sorting and filtering
   - Quick search with autocompletion

3. **Parameter Editor**:
   - Form-based editor with validation
   - JSON editor for complex parameters
   - Metadata editor (description, volatility, etc.)

4. **History View**:
   - Timeline of changes with diff view
   - Rollback capability
   - Audit log with filtering

### Authorization Model

We'll implement a granular permission system:

- **Viewer**: Can only view parameters
- **Editor**: Can edit parameters but not sensitive ones
- **Admin**: Full access, including sensitive parameters
- **Super Admin**: Can manage permissions and users

## API Documentation

### Core Endpoints

#### List Parameters

```
GET /api/v2/parameters
```

Query parameters:
- `group`: Filter by parameter group
- `search`: Search in parameter names and descriptions
- `is_india_specific`: Filter India-specific parameters

#### Get Parameter

```
GET /api/v2/parameters/{parameter_path}
```

Returns parameter value, metadata, and history.

#### Update Parameter

```
PUT /api/v2/parameters/{parameter_path}
```

Request body:
```json
{
  "value": 12.5,
  "source": "professional",
  "description": "Updated equity return based on latest market research",
  "reason": "Annual parameter review"
}
```

#### Bulk Update

```
POST /api/v2/parameters/bulk
```

Request body:
```json
{
  "parameters": [
    {
      "path": "market.equity.equity_large_cap",
      "value": 12.5
    },
    {
      "path": "market.equity.equity_mid_cap",
      "value": 14.5
    }
  ],
  "source": "professional",
  "reason": "Annual parameter review"
}
```

## Database Schema Extensions

We'll add these tables to enhance the parameter management:

1. **parameter_history**:
   - Records all parameter changes
   - Stores previous values, change metadata
   - Enables rollback functionality

2. **parameter_validation**:
   - Defines validation rules for parameters
   - Type constraints, range limits, regex patterns
   - Used to validate inputs before saving

3. **parameter_tags**:
   - Allows flexible tagging of parameters
   - Enables custom parameter grouping
   - Supports version tagging for sets of parameters

## Next Steps

1. Implement the admin routes in the Flask application
2. Create the parameter API endpoints
3. Develop the admin UI templates
4. Enhance the FinancialParameterService with new capabilities
5. Add unit and integration tests
6. Document the interface for users

This plan provides a comprehensive approach to parameter management, enabling non-technical users to update financial parameters while maintaining data integrity and change tracking.
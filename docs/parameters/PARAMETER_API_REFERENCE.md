# Parameter API Reference

This document provides detailed reference for the Financial Parameters API (v2).

## Authentication

All parameter API endpoints require HTTP Basic Authentication with admin credentials.

Example:
```bash
curl -X GET "https://example.com/api/v2/parameters" \
  -u "admin:password"
```

## Parameter Endpoints

### List Parameters

Retrieves a list of parameters, with optional filtering.

```
GET /api/v2/parameters
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| group | string | Filter parameters by group prefix (e.g., "market.equity") |
| search | string | Filter parameters by search term in path or description |
| is_india_specific | boolean | Filter India-specific parameters (true/false) |

#### Response

```json
{
  "parameters": [
    {
      "path": "market.equity.equity_large_cap",
      "value": 12.5,
      "description": "Expected annual return for large cap equities",
      "source": "research",
      "is_editable": true,
      "is_india_specific": false,
      "volatility": 18.0,
      "created": "2025-01-15T10:30:00",
      "last_updated": "2025-03-22T14:45:00",
      "has_overrides": false
    },
    // Additional parameters...
  ],
  "tree": {
    "market": {
      "equity": {
        "equity_large_cap": 12.5,
        // Other equity parameters...
      },
      // Other market categories...
    },
    // Other top-level categories...
  }
}
```

### Get Parameter

Retrieves a specific parameter by path.

```
GET /api/v2/parameters/{parameter_path}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| parameter_path | string | Dot-notation path to the parameter |

#### Response

```json
{
  "success": true,
  "parameter": {
    "path": "market.equity.equity_large_cap",
    "value": 12.5,
    "description": "Expected annual return for large cap equities",
    "source": "research",
    "is_editable": true,
    "is_india_specific": false,
    "volatility": 18.0,
    "created": "2025-01-15T10:30:00",
    "last_updated": "2025-03-22T14:45:00",
    "has_overrides": false
  },
  "history": [
    {
      "timestamp": "2025-03-22T14:45:00",
      "value": 12.5,
      "source": "research"
    },
    {
      "timestamp": "2025-01-15T10:30:00",
      "value": 12.0,
      "source": "initial"
    }
  ]
}
```

### Create Parameter

Creates a new parameter.

```
POST /api/v2/parameters
```

#### Request Body

```json
{
  "path": "market.equity.equity_large_cap",
  "value": 12.5,
  "description": "Expected annual return for large cap equities",
  "source": "research",
  "is_editable": true,
  "is_india_specific": false
}
```

#### Response

```json
{
  "success": true,
  "message": "Parameter 'market.equity.equity_large_cap' created successfully"
}
```

### Update Parameter

Updates an existing parameter.

```
PUT /api/v2/parameters/{parameter_path}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| parameter_path | string | Dot-notation path to the parameter |

#### Request Body

```json
{
  "value": 13.0,
  "description": "Updated expected annual return for large cap equities",
  "source": "annual_review",
  "reason": "Updated based on latest market research"
}
```

#### Response

```json
{
  "success": true,
  "message": "Parameter 'market.equity.equity_large_cap' updated successfully"
}
```

### Delete Parameter

Deletes a parameter.

```
DELETE /api/v2/parameters/{parameter_path}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| parameter_path | string | Dot-notation path to the parameter |

#### Response

```json
{
  "success": true,
  "message": "Parameter 'market.equity.equity_large_cap' deleted successfully"
}
```

### Bulk Update Parameters

Updates multiple parameters in a single request.

```
POST /api/v2/parameters/bulk
```

#### Request Body

```json
{
  "parameters": [
    {
      "path": "market.equity.equity_large_cap",
      "value": 13.0
    },
    {
      "path": "market.equity.equity_mid_cap",
      "value": 14.5
    },
    {
      "path": "market.equity.equity_small_cap",
      "value": 16.0
    }
  ],
  "source": "annual_review",
  "reason": "Updated based on latest market research"
}
```

#### Response

```json
{
  "success": true,
  "results": [
    {
      "path": "market.equity.equity_large_cap",
      "success": true,
      "error": null
    },
    {
      "path": "market.equity.equity_mid_cap",
      "success": true,
      "error": null
    },
    {
      "path": "market.equity.equity_small_cap",
      "success": true,
      "error": null
    }
  ],
  "summary": {
    "total": 3,
    "success": 3,
    "failure": 0
  }
}
```

### Get Parameter History

Retrieves the history of a parameter's values.

```
GET /api/v2/parameters/history/{parameter_path}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| parameter_path | string | Dot-notation path to the parameter |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| limit | integer | Maximum number of history entries to return (default: 10) |

#### Response

```json
{
  "success": true,
  "history": [
    {
      "timestamp": "2025-03-22T14:45:00",
      "value": 13.0,
      "source": "annual_review"
    },
    {
      "timestamp": "2025-01-15T10:30:00",
      "value": 12.5,
      "source": "research"
    },
    {
      "timestamp": "2024-12-01T09:00:00",
      "value": 12.0,
      "source": "initial"
    }
  ]
}
```

## Error Responses

All API endpoints return appropriate HTTP status codes and error messages:

### 400 Bad Request

```json
{
  "success": false,
  "error": "Required field 'path' is missing"
}
```

### 401 Unauthorized

```json
{
  "error": "Unauthorized: Authentication required"
}
```

### 404 Not Found

```json
{
  "success": false,
  "error": "Parameter 'nonexistent.parameter' not found"
}
```

### 409 Conflict

```json
{
  "success": false,
  "error": "Parameter 'market.equity.equity_large_cap' already exists"
}
```

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "An unexpected error occurred while processing your request"
}
```

## Common Parameter Groups

The API recognizes these common parameter groups:

| Group | Description |
|-------|-------------|
| market_assumptions | Asset returns, inflation rates |
| retirement | Withdrawal rates, life expectancy, replacement ratios |
| education | Cost increase rates, average college costs |
| housing | Mortgage rates, property taxes, maintenance costs |
| tax | Income tax brackets, capital gains rates, deductions |
| risk_profiles | Asset allocation models for different risk levels |

You can filter parameters by these groups using the `group` query parameter in the List Parameters endpoint.
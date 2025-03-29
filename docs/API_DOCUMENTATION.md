# Profiler4 API Documentation

## Overview

The Profiler4 API provides programmatic access to financial goal analysis, probability calculations, and visualization data. This document serves as a reference for all available endpoints, their parameters, and response formats.

## API Versions

- **v2**: Current API version with enhanced features, caching, and performance monitoring
- **v1**: Legacy API (deprecated)

## Authentication

The API uses two authentication mechanisms:

1. **Session-based authentication**: For regular users accessing their own data
2. **API key authentication**: For admin endpoints (`X-Admin-Key` header or `admin_key` query parameter)

## Goal Probability API

The Goal Probability API provides access to Monte Carlo simulations, probability analysis, and scenario management for financial goals.

### Endpoints

#### GET /api/v2/goals/{goal_id}/probability

Get the current probability analysis for a goal.

**Parameters**:
- `goal_id`: The UUID of the goal (path parameter)

**Response**:
```json
{
  "goal_id": "68dd4f2c-ebd1-4c72-aff9-a2887bd9a060",
  "success_probability": 0.75,
  "probability_metrics": {
    "base_probability": 0.7,
    "adjusted_probability": 0.75,
    "confidence_level": "medium",
    "probability_factors": [...],
    "last_calculated": "2025-03-24T10:30:45",
    "simulation_count": 1000,
    "convergence_rate": 0.98
  },
  "simulation_summary": {
    "target_amount": 2000000,
    "median_outcome": 2000000,
    "percentile_10": 1700000,
    "percentile_25": 1850000,
    "percentile_75": 2150000,
    "percentile_90": 2300000,
    "target_amount_formatted": "₹20.00 L",
    "median_outcome_formatted": "₹20.00 L"
  },
  "performance": {
    "duration_ms": 125.45,
    "endpoint": "/api/v2/goals/68dd4f2c-ebd1-4c72-aff9-a2887bd9a060/probability",
    "method": "GET",
    "cache_status": "HIT"
  }
}
```

#### POST /api/v2/goals/{goal_id}/probability/calculate

Calculate or recalculate the probability of a goal.

**Parameters**:
- `goal_id`: The UUID of the goal (path parameter)

**Request Body**:
```json
{
  "update_goal": true,
  "parameters": {
    "target_amount": 2500000,
    "current_amount": 500000,
    "monthly_contribution": 20000,
    "timeframe": "2028-03-24T00:00:00"
  }
}
```

**Response**:
```json
{
  "goal_id": "68dd4f2c-ebd1-4c72-aff9-a2887bd9a060",
  "success_probability": 0.82,
  "calculation_time": "2025-03-24T10:35:22",
  "probability_factors": [...],
  "simulation_summary": {...},
  "goal_updated": true,
  "simulation_metadata": {
    "simulation_count": 1000,
    "calculation_time_ms": 850.32,
    "confidence_interval": [0.79, 0.85],
    "convergence_rate": 0.98
  },
  "performance": {
    "duration_ms": 950.78,
    "endpoint": "/api/v2/goals/68dd4f2c-ebd1-4c72-aff9-a2887bd9a060/probability/calculate",
    "method": "POST",
    "cache_status": "MISS"
  }
}
```

#### GET /api/v2/goals/{goal_id}/adjustments

Get adjustment recommendations for a goal.

**Parameters**:
- `goal_id`: The UUID of the goal (path parameter)

**Response**:
```json
{
  "goal_id": "68dd4f2c-ebd1-4c72-aff9-a2887bd9a060",
  "current_probability": 0.75,
  "adjustments": [
    {
      "id": "adj-uuid-1",
      "type": "contribution_increase",
      "description": "Increase monthly SIP by ₹5,000",
      "impact": {
        "probability_increase": 0.15,
        "new_probability": 0.9
      },
      "implementation_steps": [
        "Set up additional SIP with your bank",
        "Consider tax-saving ELSS funds for 80C benefits"
      ],
      "tax_benefits": {
        "80C": 60000
      },
      "sip_details": {
        "monthly_amount": 5000,
        "annual_amount": 60000,
        "monthly_amount_formatted": "₹5,000.00",
        "annual_amount_formatted": "₹60,000.00"
      }
    },
    {
      "id": "adj-uuid-2",
      "type": "timeframe_extension",
      "description": "Extend goal timeframe by 12 months",
      "impact": {
        "probability_increase": 0.1,
        "new_probability": 0.85
      },
      "implementation_steps": [
        "Update your goal target date",
        "Continue current contributions"
      ]
    }
  ],
  "performance": {
    "duration_ms": 135.20,
    "endpoint": "/api/v2/goals/68dd4f2c-ebd1-4c72-aff9-a2887bd9a060/adjustments",
    "method": "GET",
    "cache_status": "MISS"
  }
}
```

#### GET /api/v2/goals/{goal_id}/scenarios

Get all scenarios for a goal.

**Parameters**:
- `goal_id`: The UUID of the goal (path parameter)

**Response**:
```json
{
  "goal_id": "68dd4f2c-ebd1-4c72-aff9-a2887bd9a060",
  "scenarios": [
    {
      "id": "baseline_scenario",
      "name": "Current Plan",
      "description": "Your current financial plan with no changes",
      "created_at": "2025-03-24T10:30:45",
      "probability": 0.75,
      "parameters": {
        "target_amount": 2000000,
        "current_amount": 500000,
        "monthly_contribution": 15000,
        "timeframe": "2028-01-01",
        "target_amount_formatted": "₹20.00 L",
        "current_amount_formatted": "₹5.00 L",
        "monthly_contribution_formatted": "₹15,000.00"
      },
      "is_baseline": true
    },
    {
      "id": "scenario-uuid-1",
      "name": "Aggressive Saving",
      "description": "Increase monthly contributions significantly",
      "created_at": "2025-03-24T10:35:22",
      "probability": 0.88,
      "parameters": {
        "target_amount": 2000000,
        "current_amount": 500000,
        "monthly_contribution": 25000,
        "timeframe": "2028-01-01",
        "target_amount_formatted": "₹20.00 L",
        "current_amount_formatted": "₹5.00 L",
        "monthly_contribution_formatted": "₹25,000.00"
      },
      "is_baseline": false
    }
  ],
  "performance": {
    "duration_ms": 98.65,
    "endpoint": "/api/v2/goals/68dd4f2c-ebd1-4c72-aff9-a2887bd9a060/scenarios",
    "method": "GET",
    "cache_status": "HIT"
  }
}
```

#### POST /api/v2/goals/{goal_id}/scenarios

Create a new scenario for a goal.

**Parameters**:
- `goal_id`: The UUID of the goal (path parameter)

**Request Body**:
```json
{
  "name": "Extended Timeline with Higher Equity",
  "description": "Extend timeline by 1 year and increase equity allocation",
  "parameters": {
    "target_amount": 3000000,
    "current_amount": 1000000,
    "monthly_contribution": 25000,
    "timeframe": "2026-03-24T00:00:00",
    "equity_allocation": 0.8
  }
}
```

**Response**:
```json
{
  "id": "scenario-uuid-new",
  "name": "Extended Timeline with Higher Equity",
  "description": "Extend timeline by 1 year and increase equity allocation",
  "created_at": "2025-03-24T10:40:15",
  "probability": 0.83,
  "parameters": {
    "target_amount": 3000000,
    "current_amount": 1000000,
    "monthly_contribution": 25000,
    "timeframe": "2026-03-24T00:00:00",
    "equity_allocation": 0.8
  },
  "is_baseline": false,
  "calculation_metadata": {
    "calculation_time_ms": 845.78,
    "simulation_count": 1000,
    "confidence_interval": [0.80, 0.86],
    "convergence_rate": 0.99
  },
  "performance": {
    "duration_ms": 890.35,
    "endpoint": "/api/v2/goals/68dd4f2c-ebd1-4c72-aff9-a2887bd9a060/scenarios",
    "method": "POST",
    "cache_status": "MISS"
  }
}
```

#### GET /api/v2/goals/{goal_id}/scenarios/{scenario_id}

Get a specific scenario for a goal.

**Parameters**:
- `goal_id`: The UUID of the goal (path parameter)
- `scenario_id`: The ID of the scenario (path parameter)

**Response**:
```json
{
  "id": "scenario-uuid-1",
  "name": "Aggressive Saving",
  "description": "Increase monthly contributions significantly",
  "created_at": "2025-03-24T10:35:22",
  "probability": 0.88,
  "parameters": {
    "target_amount": 2000000,
    "current_amount": 500000,
    "monthly_contribution": 25000,
    "timeframe": "2028-01-01",
    "target_amount_formatted": "₹20.00 L",
    "current_amount_formatted": "₹5.00 L",
    "monthly_contribution_formatted": "₹25,000.00"
  },
  "is_baseline": false,
  "performance": {
    "duration_ms": 45.25,
    "endpoint": "/api/v2/goals/68dd4f2c-ebd1-4c72-aff9-a2887bd9a060/scenarios/scenario-uuid-1",
    "method": "GET",
    "cache_status": "HIT"
  }
}
```

#### DELETE /api/v2/goals/{goal_id}/scenarios/{scenario_id}

Delete a scenario for a goal.

**Parameters**:
- `goal_id`: The UUID of the goal (path parameter)
- `scenario_id`: The ID of the scenario (path parameter)

**Response**:
```json
{
  "message": "Scenario deleted successfully",
  "goal_id": "68dd4f2c-ebd1-4c72-aff9-a2887bd9a060",
  "scenario_id": "scenario-uuid-1",
  "performance": {
    "duration_ms": 120.85,
    "endpoint": "/api/v2/goals/68dd4f2c-ebd1-4c72-aff9-a2887bd9a060/scenarios/scenario-uuid-1",
    "method": "DELETE",
    "cache_status": "BYPASS"
  }
}
```

## Visualization Data API

The Visualization Data API provides optimized data for frontend visualization components.

### Endpoints

#### GET /api/v2/goals/{goal_id}/visualization-data

Get all visualization data for a goal in a single API call.

**Parameters**:
- `goal_id`: The UUID of the goal (path parameter)

**Response**:
```json
{
  "goal_id": "68dd4f2c-ebd1-4c72-aff9-a2887bd9a060",
  "probabilisticGoalData": {
    "goalId": "68dd4f2c-ebd1-4c72-aff9-a2887bd9a060",
    "targetAmount": 2000000,
    "successProbability": 0.75,
    "simulationOutcomes": {
      "median": 2000000,
      "percentiles": {
        "10": 1700000,
        "25": 1850000,
        "50": 2000000,
        "75": 2150000,
        "90": 2300000
      }
    },
    "timeBasedMetrics": {
      "probabilityOverTime": {
        "labels": ["Start", "25%", "50%", "75%", "End"],
        "values": [0, 0.3, 0.45, 0.6, 0.75]
      }
    }
  },
  "adjustmentImpactData": {
    "goalId": "68dd4f2c-ebd1-4c72-aff9-a2887bd9a060",
    "currentProbability": 0.75,
    "adjustments": [...]
  },
  "scenarioComparisonData": {
    "goalId": "68dd4f2c-ebd1-4c72-aff9-a2887bd9a060",
    "scenarios": [...]
  },
  "dataSources": {
    "monte_carlo": "goal_data",
    "adjustments": "goal_data",
    "scenarios": "goal_data"
  },
  "performance": {
    "duration_ms": 180.32,
    "endpoint": "/api/v2/goals/68dd4f2c-ebd1-4c72-aff9-a2887bd9a060/visualization-data",
    "method": "GET",
    "cache_status": "MISS"
  }
}
```

#### GET /api/v2/goals/{goal_id}/projection-data

Get projection data for a specific goal type.

**Parameters**:
- `goal_id`: The UUID of the goal (path parameter)
- `type`: Projection type ('timeline', 'allocation', 'probability', 'all') (query parameter)
- `resolution`: Data resolution ('high', 'medium', 'low') (query parameter)

**Response**:
```json
{
  "goal_id": "68dd4f2c-ebd1-4c72-aff9-a2887bd9a060",
  "goal_type": "education",
  "projections": {
    "timeline": {
      "labels": ["2025", "2026", "2027", "2028"],
      "values": [500000, 900000, 1400000, 2000000],
      "resolution": "medium"
    },
    "allocation": {
      "labels": ["equity", "debt", "gold", "cash"],
      "values": [0.6, 0.25, 0.1, 0.05],
      "colors": ["#4285F4", "#34A853", "#FBBC05", "#EA4335"]
    },
    "probability": {
      "x": [1000000, 1250000, 1500000, 1750000, 2000000, 2250000, 2500000],
      "y": [0.02, 0.08, 0.15, 0.25, 0.3, 0.15, 0.05],
      "target": 2000000,
      "target_position": 4,
      "probability": 0.75,
      "resolution": "medium"
    }
  },
  "metadata": {
    "resolution": "medium",
    "currency": "INR",
    "use_indian_format": true
  },
  "performance": {
    "duration_ms": 150.25,
    "endpoint": "/api/v2/goals/68dd4f2c-ebd1-4c72-aff9-a2887bd9a060/projection-data",
    "method": "GET",
    "cache_status": "HIT"
  }
}
```

#### GET /api/v2/goals/portfolio-data

Get aggregate portfolio data across all goals.

**Parameters**:
- `user_id`: User profile ID (query parameter)
- `include_inactive`: Whether to include inactive goals (default: false) (query parameter)

**Response**:
```json
{
  "user_id": "b67a71e2-5f61-492a-9eeb-2037bf2e9993",
  "goal_count": 5,
  "categories": {
    "education": {
      "count": 1,
      "total_target": 2000000,
      "total_current": 500000,
      "avg_probability": 0.75,
      "goals": [...]
    },
    "retirement": {
      "count": 1,
      "total_target": 30000000,
      "total_current": 5000000,
      "avg_probability": 0.82,
      "goals": [...]
    },
    "emergency_fund": {
      "count": 1,
      "total_target": 300000,
      "total_current": 250000,
      "avg_probability": 0.95,
      "goals": [...]
    }
  },
  "timeline_projection": {
    "labels": ["2025", "2030", "2035", "2040", "2045", "2050"],
    "events": [...]
  },
  "portfolio_metrics": {
    "total_target_amount": 35300000,
    "total_current_amount": 6750000,
    "overall_progress_percent": 19.12,
    "monthly_contribution": 85000,
    "monthly_funding_gap": 15000,
    "goal_health": {
      "healthy": 2,
      "at_risk": 2,
      "critical": 1
    }
  },
  "performance": {
    "duration_ms": 380.45,
    "endpoint": "/api/v2/goals/portfolio-data",
    "method": "GET",
    "cache_status": "MISS"
  }
}
```

#### POST /api/v2/goals/calculate-probability

Calculate probability for goal parameters in real-time.

**Request Body**:
```json
{
  "category": "education",
  "target_amount": 2500000,
  "current_amount": 500000,
  "timeframe": "2028-03-24T00:00:00",
  "months_remaining": 36,
  "importance": "high",
  "flexibility": "somewhat_flexible",
  "emergency_fund_months": 6,
  "monthly_expenses": 50000
}
```

**Response**:
```json
{
  "success_probability": 78.5,
  "adjustments": [
    {
      "description": "Increase monthly contribution by ₹5,000",
      "impact_metrics": {
        "probability_increase": 0.15,
        "new_probability": 0.935
      }
    },
    {
      "description": "Extend goal timeframe by 6 months",
      "impact_metrics": {
        "probability_increase": 0.08,
        "new_probability": 0.865
      }
    }
  ],
  "simulation_data": {
    "successProbability": 0.785,
    "percentiles": {
      "10": 2000000,
      "25": 2200000,
      "50": 2500000,
      "75": 2800000,
      "90": 3000000
    },
    "resolution": "low"
  },
  "calculation_metadata": {
    "calculation_time_ms": 350.25,
    "simulation_count": 1000,
    "confidence_interval": [0.75, 0.82],
    "is_estimate": false
  },
  "performance": {
    "duration_ms": 380.15,
    "endpoint": "/api/v2/goals/calculate-probability",
    "method": "POST",
    "cache_status": "MISS"
  }
}
```

## Cache Control API (Admin)

The Cache Control API provides administrative endpoints for monitoring and managing the API cache.

### Endpoints

#### GET /api/v2/admin/cache_stats

Get statistics about the Monte Carlo simulation cache.

**Headers**:
- `X-Admin-Key`: Admin API key

**Response**:
```json
{
  "size": 128,
  "hit_count": 1024,
  "miss_count": 256,
  "hit_rate": 0.8,
  "hit_rate_percentage": 80,
  "cache_type": "in_memory",
  "uptime": 3600,
  "memory_usage_estimate": {
    "bytes": 1310720,
    "formatted": "1280 KB"
  },
  "enabled": true,
  "default_ttl": 3600,
  "api_version": "v2",
  "timestamp": "2025-03-24T10:45:30",
  "performance": {
    "duration_ms": 25.15,
    "endpoint": "/api/v2/admin/cache_stats",
    "method": "GET",
    "cache_status": "BYPASS"
  }
}
```

#### POST /api/v2/admin/cache/invalidate

Invalidate all or part of the Monte Carlo simulation cache.

**Headers**:
- `X-Admin-Key`: Admin API key

**Request Body**:
```json
{
  "pattern": "goal:*",
  "reason": "Updated market parameters"
}
```

**Response**:
```json
{
  "message": "Cache invalidated successfully",
  "invalidated_entries": 58,
  "pattern": "goal:*",
  "timestamp": "2025-03-24T10:50:15",
  "audit_id": "8c7d7ae6-e727-4006-8ba8-6a0c262d8114",
  "performance": {
    "duration_ms": 85.32,
    "endpoint": "/api/v2/admin/cache/invalidate",
    "method": "POST",
    "cache_status": "BYPASS"
  }
}
```

#### GET /api/v2/admin/performance

Get performance metrics for Monte Carlo simulations.

**Headers**:
- `X-Admin-Key`: Admin API key

**Query Parameters**:
- `period`: Time period for metrics ('hour', 'day', 'week', 'month', default: 'hour')
- `format`: Response format ('json', 'csv', default: 'json')

**Response**:
```json
{
  "cache": {
    "size": 128,
    "hit_count": 1024,
    "miss_count": 256,
    "hit_rate": 0.8
  },
  "simulation_times": {
    "average_ms": 850,
    "median_ms": 750,
    "p95_ms": 1500,
    "p99_ms": 2200
  },
  "resource_usage": {
    "cpu_utilization": {
      "average_percent": 25,
      "peak_percent": 70
    },
    "memory_usage": {
      "average_mb": 150,
      "peak_mb": 300
    }
  },
  "api_metrics": {
    "avg_response_time_ms": 120,
    "requests_per_minute": 15,
    "error_rate": 0.02,
    "cache_hit_rate": 0.85
  },
  "metadata": {
    "period": "hour",
    "timestamp": "2025-03-24T10:55:20",
    "api_version": "v2"
  },
  "rate_limits": {
    "enabled": true,
    "limit_per_minute": 100,
    "current_usage": {
      "127.0.0.1:default": {
        "count": 15,
        "window_start": 1616584520,
        "window_end": 1616584580,
        "remaining_seconds": 25
      }
    }
  },
  "performance": {
    "duration_ms": 65.45,
    "endpoint": "/api/v2/admin/performance",
    "method": "GET",
    "cache_status": "BYPASS"
  }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Rate limits are:

- Regular endpoints: 100 requests per minute per IP address
- Admin endpoints: 20 requests per minute per IP address

When a rate limit is exceeded, the API will respond with a 429 status code and information about when to retry:

```json
{
  "error": "Rate limit exceeded",
  "message": "Rate limit exceeded. Try again in 30 seconds",
  "retry_after": 30
}
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

- **400 Bad Request**: Invalid parameters or request body
- **401 Unauthorized**: Missing authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side error

Error response example:

```json
{
  "error": "Invalid parameters",
  "message": "target_amount must be a number",
  "validation_errors": [
    "target_amount must be a number"
  ]
}
```

## Feature Flags

The API uses feature flags to control the availability of certain features:

- `FEATURE_GOAL_PROBABILITY_API`: Controls Goal Probability API endpoints
- `FEATURE_VISUALIZATION_API`: Controls Visualization Data API endpoints
- `FEATURE_ADMIN_CACHE_API`: Controls Admin Cache Control API endpoints

## Caching

The API implements caching to improve performance and reduce computational load:

- Cache TTL (Time-To-Live): Default is 3600 seconds (1 hour)
- Cache entries can be invalidated through the admin API
- Cache status is included in all API responses (`HIT`, `MISS`, or `BYPASS`)

## Performance Monitoring

All API responses include performance information:

```json
"performance": {
  "duration_ms": 120.85,
  "endpoint": "/api/v2/goals/68dd4f2c-ebd1-4c72-aff9-a2887bd9a060/probability",
  "method": "GET",
  "cache_status": "HIT"
}
```

## Currency Formatting

For Indian users, the API supports Indian currency formatting (lakhs and crores):

- ₹100,000 → ₹1.00 L (1 lakh)
- ₹10,000,000 → ₹1.00 Cr (1 crore)

These formatted values are included alongside raw numeric values in appropriate responses.

## Versioning

The API follows semantic versioning principles:

- API path includes version: `/api/v2/...`
- Breaking changes trigger a version increment
- New features may be added within the same API version

## Security Recommendations

- Use HTTPS for all API requests
- Rotate admin API keys regularly
- Implement additional authentication for production use
- Monitor API usage for unusual patterns

## Integration Example

A simple example of integrating with the Goal Probability API:

```javascript
// Fetch probability data for a goal
async function getGoalProbability(goalId) {
  const response = await fetch(`/api/v2/goals/${goalId}/probability`);
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.message || 'Failed to fetch goal probability');
  }
  
  return data;
}

// Calculate probability with custom parameters
async function calculateProbability(goalId, parameters) {
  const response = await fetch(`/api/v2/goals/${goalId}/probability/calculate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      update_goal: false,
      parameters: parameters
    })
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.message || 'Failed to calculate probability');
  }
  
  return data;
}
```
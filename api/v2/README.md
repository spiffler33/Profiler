# API v2 Documentation

## Overview

The API v2 module provides a modern, maintainable API for accessing and manipulating goal data within the Profiler4 application. It includes:

- Goal management endpoints (CRUD operations)
- Probability analysis and Monte Carlo simulations
- Adjustment recommendations
- Scenario comparisons
- Visualization data

## Core Components

### 1. API Utilities (`utils.py`)

The `utils.py` module provides common functionality for all API endpoints:

- Rate limiting
- Caching
- Performance monitoring
- Error handling
- Admin access control

#### Usage Examples

**Rate Limiting**:
```python
# In a Blueprint's before_request handler
@blueprint.before_request
def check_rate_limit():
    """Check rate limits before processing requests."""
    return rate_limit_middleware()
```

**Caching**:
```python
# Check cache
cache_key = generate_cache_key(goal_id, "probability")
cached_response = check_cache(cache_key)
if cached_response:
    g.cache_status = "HIT"
    return cached_response

# Cache a response
cache_response(cache_key, response, ttl=3600)
```

**Performance Monitoring**:
```python
@monitor_performance
def my_api_endpoint():
    # Endpoint implementation
    # Performance metrics will be automatically added to the response
    return jsonify({"data": result})
```

**Error Handling**:
```python
# Create a standardized error response
response, status_code = create_error_response(
    "Invalid parameters",
    status_code=400,
    error_type="validation_error"
)
return response, status_code
```

**Admin Access**:
```python
if not check_admin_access():
    return jsonify({
        "error": "Unauthorized",
        "message": "Admin privileges required"
    }), 403
```

### 2. Goal Probability API (`goal_probability_api.py`)

Provides endpoints for:
- Retrieving goal probability data
- Calculating/recalculating probability
- Managing scenario comparisons
- Getting adjustment recommendations

### 3. Visualization Data API (`visualization_data.py`)

Provides endpoints for:
- Consolidated visualization data for UI components
- Real-time probability calculations for forms
- Goal projections
- Portfolio-level aggregations

## Common Patterns

1. **Cache Key Generation**: Each API module has its own method for generating cache keys with a consistent format.

2. **API Response Structure**: All API responses follow a common structure with:
   - Primary data
   - Metadata
   - Performance metrics
   - Error information (if applicable)

3. **Rate Limiting**: All endpoints enforce rate limits through middleware.

4. **Error Handling**: Errors are returned with consistent structure and appropriate HTTP status codes.

## Testing

The API can be tested using the following approaches:

1. Individual endpoint tests:
   ```
   python -m tests.api.test_goal_probability_api
   ```

2. Progressive test suite (increasingly complex tests):
   ```
   python -m tests.api_fix.progressive_api_test_suite
   ```

3. Utils module tests:
   ```
   python -m tests.api_fix.utils_consolidation_test
   ```

4. Running a specific test for debugging:
   ```
   python -m tests.api_fix.progressive_api_test_suite utils test_01_rate_limiting
   ```

## Future Improvements

1. Add API versioning mechanism for orderly deprecation of endpoints
2. Implement OpenAPI/Swagger documentation
3. Add pagination for list endpoints
4. Improve filtering and sorting options
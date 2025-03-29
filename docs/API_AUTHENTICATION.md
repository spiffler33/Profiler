# API Authentication Guide

## Overview

This document outlines the authentication mechanisms used in the Profiler4 API, including development and production modes, admin access, and best practices for API consumers.

## Authentication Modes

The API supports two authentication modes:

1. **Development Mode**: In development mode, authentication is bypassed for easier testing and development. This is controlled by the `DEV_MODE` configuration flag.

2. **Production Mode**: In production mode, all admin endpoints require proper authentication using HTTP Basic Auth.

## Admin API Access

Admin API endpoints are protected and require authentication. These endpoints are located under the `/api/v2/admin/` path.

### Authentication Methods

#### HTTP Basic Authentication

Admin endpoints use HTTP Basic Authentication:

```
Authorization: Basic <base64-encoded username:password>
```

Example:
```
Authorization: Basic YWRtaW46YWRtaW4=  # admin:admin
```

#### API Key Authentication

For programmatic access, you can use an API Key:

```
X-Admin-Key: <api-key>
```

The API key should be set in the configuration as `ADMIN_API_KEY`.

### Development Mode Bypass

When `DEV_MODE` is set to `True` in the configuration:

- All authentication checks are bypassed
- Admin endpoints can be accessed without credentials
- Rate limiting is disabled

To enable development mode, set the following environment variable:

```
export DEV_MODE=True
```

## Rate Limiting

The API implements rate limiting to protect against abuse. Rate limits differ based on the endpoint type:

- **Regular Endpoints**: 60 requests per minute by default
- **Admin Endpoints**: 30 requests per minute by default

Rate limit information is included in the response headers:

- `X-RateLimit-Limit`: Maximum requests allowed in the time window
- `X-RateLimit-Remaining`: Remaining requests in the current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit will reset

When a rate limit is exceeded, the API returns a `429 Too Many Requests` response with a `Retry-After` header indicating how many seconds to wait before retrying.

## Best Practices

1. **Use HTTPS**: Always use HTTPS to ensure credentials are encrypted in transit

2. **Store Credentials Securely**: Never hardcode credentials in your client applications

3. **Implement Rate Limit Handling**: Clients should respect rate limits and implement backoff strategies

4. **Handle Authentication Errors**: Properly handle 401 and 403 responses

## Testing Authentication

You can use the included test script to verify authentication:

```bash
python -m tests.api_fix.auth_test
```

This script tests authentication against various endpoints in both authenticated and unauthenticated modes.

## API Error Responses

Authentication errors return standard HTTP status codes:

- **401 Unauthorized**: Missing or invalid credentials
- **403 Forbidden**: Valid credentials but insufficient permissions
- **429 Too Many Requests**: Rate limit exceeded

Error response format:

```json
{
  "error": {
    "type": "authentication_error",
    "message": "Authentication required for this resource",
    "status": 401
  },
  "success": false
}
```

## Debugging Authentication Issues

For debugging authentication issues, the API provides a special endpoint:

```
GET /api/v2/test/auth_headers
```

This endpoint returns information about the current authentication configuration and request headers.

## Additional Notes

- All admin endpoints are consistently protected with the `@admin_required` decorator
- Authentication bypass in development mode does not compromise security in production
- The authentication system includes comprehensive logging for troubleshooting
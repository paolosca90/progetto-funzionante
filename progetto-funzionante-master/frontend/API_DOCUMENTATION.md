# AI Trading System API Documentation

## Overview

The AI Trading System API is a comprehensive FastAPI-based platform for generating, managing, and executing trading signals with OANDA integration and AI-powered analysis. This documentation provides complete information about all available endpoints, authentication methods, request/response schemas, and usage examples.

**Base URL**: `https://your-api-domain.com`
**Version**: 2.0.1
**Environment**: Production/Development/Staging/Testing

## Quick Links

- [Authentication](#authentication)
- [Endpoints](#api-endpoints)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [SDK Examples](#sdk-examples)
- [Troubleshooting](#troubleshooting)

## Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
   - [Authentication Endpoints](#authentication-endpoints)
   - [User Management](#user-management)
   - [Trading Signals](#trading-signals)
   - [OANDA Integration](#oanda-integration)
   - [Admin Operations](#admin-operations)
   - [Health & Monitoring](#health--monitoring)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Webhooks](#webhooks)
8. [SDK Examples](#sdk-examples)
9. [Troubleshooting](#troubleshooting)
10. [Changelog](#changelog)

## Quick Start Guide

### 1. Prerequisites

- Valid API credentials
- OANDA account for trading functionality
- Active subscription for full access

### 2. Authentication

All API requests require authentication using JWT tokens:

```bash
# Get access token
curl -X POST "https://your-api-domain.com/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"

# Use token in subsequent requests
curl -X GET "https://your-api-domain.com/api/signals/latest" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. First API Call

Get latest trading signals:

```bash
curl -X GET "https://your-api-domain.com/api/signals/latest?limit=5" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Authentication

### JWT Token Authentication

The API uses JWT (JSON Web Tokens) for authentication. Tokens are obtained by providing valid credentials to the `/token` endpoint.

#### Token Types

- **Access Token**: Short-lived token (30 minutes) for API requests
- **Refresh Token**: Long-lived token (7 days) for obtaining new access tokens

#### Required Headers

```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

### Authentication Flow

1. **Login**: Obtain access and refresh tokens
2. **API Calls**: Use access token in Authorization header
3. **Token Refresh**: Use refresh token to get new access token
4. **Logout**: Invalidate tokens (client-side)

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Default**: 100 requests per minute
- **Authentication endpoints**: 10 requests per 15 minutes
- **Signal generation**: Limited by subscription tier
- **Admin endpoints**: No rate limiting for admin users

Rate limit headers are included in API responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Error Handling

The API uses standard HTTP status codes and provides detailed error information:

### Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "error": "ErrorType",
  "message": "Detailed error message",
  "details": {
    "field": "Specific error details"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## API Endpoints

### Authentication Endpoints

#### POST /register
Register a new user account with automatic trial subscription.

**Request Body:**
```json
{
  "username": "string (3-50 chars)",
  "email": "valid@email.com",
  "password": "string (min 6 chars)",
  "full_name": "Optional full name"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "user123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "subscription_active": true
}
```

#### POST /token
Authenticate user and receive JWT tokens.

**Request Body:** (application/x-www-form-urlencoded)
```
username: string (username or email)
password: string
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

#### POST /logout
Logout current user (client-side token invalidation).

**Response:** `200 OK`
```json
{
  "message": "Logout effettuato con successo"
}
```

#### POST /forgot-password
Request password reset email.

**Request Body:** (application/x-www-form-urlencoded)
```
email: valid@email.com
```

**Response:** `200 OK`
```json
{
  "message": "Se l'email esiste nel nostro sistema, riceverai un link per il reset della password.",
  "email": "user@example.com"
}
```

#### POST /reset-password
Reset password using token.

**Request Body:** (application/x-www-form-urlencoded)
```
token: string (reset token)
new_password: string (min 8 chars)
```

**Response:** `200 OK`
```json
{
  "message": "Password aggiornata con successo"
}
```

#### POST /change-password
Change user password.

**Request Body:** (application/x-www-form-urlencoded)
```
current_password: string
new_password: string (min 8 chars)
```

**Response:** `200 OK`
```json
{
  "message": "Password cambiata con successo"
}
```

### User Management

#### GET /users/me
Get current user profile with statistics.

**Authentication Required:** Yes

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "user123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_admin": false,
  "subscription_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T12:00:00Z",
  "total_signals": 25,
  "active_signals": 3,
  "average_reliability": 78.5,
  "recent_signals_count": 5
}
```

#### GET /users/dashboard
Get comprehensive dashboard data for current user.

**Authentication Required:** Yes

**Response:** `200 OK`
```json
{
  "user_stats": {...},
  "recent_signals": [...],
  "signal_statistics": {...},
  "subscription_info": {...}
}
```

#### PATCH /users/profile
Update user profile.

**Authentication Required:** Yes

**Request Body:** (application/x-www-form-urlencoded)
```
full_name: "Updated Name" (optional)
email: "new@email.com" (optional)
```

**Response:** `200 OK`
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "user123",
    "email": "new@email.com",
    "full_name": "Updated Name"
  }
}
```

#### PATCH /users/subscription
Update subscription status (self-service).

**Authentication Required:** Yes

**Request Body:** (application/x-www-form-urlencoded)
```
is_active: boolean
```

**Response:** `200 OK`
```json
{
  "message": "Subscription status updated successfully",
  "subscription_active": true
}
```

#### DELETE /users/account
Delete user account.

**Authentication Required:** Yes

**Response:** `200 OK`
```json
{
  "message": "Account deleted successfully"
}
```

### Trading Signals

#### GET /signals/latest
Get latest active trading signals.

**Authentication Required:** Optional

**Query Parameters:**
- `limit`: Number of signals to return (1-100, default: 10)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "stop_loss": 1.0800,
    "take_profit": 1.0950,
    "reliability": 85.5,
    "status": "ACTIVE",
    "ai_analysis": "Strong bullish momentum with RSI oversold reversal...",
    "confidence_score": 87.2,
    "risk_level": "MEDIUM",
    "is_public": true,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "expires_at": "2024-01-01T06:00:00Z",
    "source": "OANDA_AI"
  }
]
```

#### GET /signals/top
Get top performing signals based on reliability.

**Authentication Required:** No

**Query Parameters:**
- `limit`: Number of signals to return (1-50, default: 10)

**Response:** `200 OK`
```json
{
  "signals": [...],
  "total_count": 150,
  "average_reliability": 82.3
}
```

#### GET /signals/
Get signals with filtering options.

**Authentication Required:** No

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records (1-1000, default: 100)
- `symbol`: Filter by trading symbol (optional)
- `signal_type`: Filter by signal type (BUY/SELL/HOLD)
- `risk_level`: Filter by risk level (LOW/MEDIUM/HIGH)
- `source`: Filter by source (optional)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "stop_loss": 1.0800,
    "take_profit": 1.0950,
    "reliability": 85.5,
    "status": "ACTIVE",
    "ai_analysis": "Technical analysis suggests upward momentum...",
    "confidence_score": 87.2,
    "risk_level": "MEDIUM",
    "is_public": true,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "expires_at": "2024-01-01T06:00:00Z",
    "source": "OANDA_AI"
  }
]
```

#### POST /signals/
Create a new trading signal.

**Authentication Required:** Yes

**Request Body:**
```json
{
  "symbol": "EURUSD",
  "signal_type": "BUY",
  "entry_price": 1.0850,
  "stop_loss": 1.0800,
  "take_profit": 1.0950,
  "reliability": 85.5,
  "ai_analysis": "Detailed AI analysis...",
  "confidence_score": 87.2,
  "risk_level": "MEDIUM",
  "expires_at": "2024-01-01T06:00:00Z"
}
```

**Response:** `201 Created`
```json
{
  "signal": {
    "id": 1,
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "stop_loss": 1.0800,
    "take_profit": 1.0950,
    "reliability": 85.5,
    "status": "ACTIVE",
    "ai_analysis": "Detailed AI analysis...",
    "confidence_score": 87.2,
    "risk_level": "MEDIUM",
    "is_public": true,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "expires_at": "2024-01-01T06:00:00Z",
    "source": "MANUAL"
  },
  "message": "Signal created successfully",
  "success": true
}
```

#### GET /signals/by-symbol/{symbol}
Get signals for a specific trading symbol.

**Authentication Required:** No

**Path Parameters:**
- `symbol`: Trading symbol (e.g., EURUSD)

**Query Parameters:**
- `limit`: Number of signals to return (1-100, default: 10)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "reliability": 85.5,
    "status": "ACTIVE",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /signals/search
Search signals by symbol or content.

**Authentication Required:** No

**Query Parameters:**
- `q`: Search query (min 2 characters)
- `limit`: Maximum number of results (1-1000, default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "reliability": 85.5,
    "status": "ACTIVE",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /signals/high-confidence
Get signals with high confidence scores.

**Authentication Required:** No

**Query Parameters:**
- `min_confidence`: Minimum confidence score (0.0-1.0, default: 0.8)
- `limit`: Maximum number of results (1-1000, default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "confidence_score": 0.87,
    "reliability": 85.5,
    "status": "ACTIVE",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /signals/my-signals
Get signals created by the current user.

**Authentication Required:** Yes

**Query Parameters:**
- `limit`: Maximum number of results (1-1000, default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "reliability": 85.5,
    "status": "ACTIVE",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /signals/statistics
Get overall signal statistics.

**Authentication Required:** No

**Response:** `200 OK`
```json
{
  "total_signals": 1500,
  "active_signals": 45,
  "average_reliability": 78.5,
  "success_rate": 76.2,
  "by_symbol": {
    "EURUSD": 350,
    "GBPUSD": 280,
    "USDJPY": 220
  },
  "by_type": {
    "BUY": 750,
    "SELL": 600,
    "HOLD": 150
  }
}
```

#### PATCH /signals/{signal_id}/close
Close a signal.

**Authentication Required:** Yes

**Path Parameters:**
- `signal_id`: ID of the signal to close

**Response:** `200 OK`
```json
{
  "message": "Signal closed successfully",
  "signal_id": 1
}
```

#### PATCH /signals/{signal_id}/cancel
Cancel a signal.

**Authentication Required:** Yes

**Path Parameters:**
- `signal_id`: ID of the signal to cancel

**Response:** `200 OK`
```json
{
  "message": "Signal cancelled successfully",
  "signal_id": 1
}
```

#### PATCH /signals/{signal_id}/reliability
Update signal reliability score.

**Authentication Required:** Yes

**Path Parameters:**
- `signal_id`: ID of the signal to update

**Query Parameters:**
- `reliability`: New reliability score (0.0-100.0)

**Response:** `200 OK`
```json
{
  "message": "Signal reliability updated successfully",
  "signal_id": 1,
  "new_reliability": 90.5
}
```

### OANDA Integration

#### GET /api/oanda/health
Check OANDA API health and connectivity.

**Authentication Required:** No

**Response:** `200 OK`
```json
{
  "available": true,
  "status": "Connected",
  "response_time_ms": 150,
  "last_check": "2024-01-01T00:00:00Z",
  "account_id": "123-456-789012-001",
  "environment": "demo"
}
```

#### POST /api/oanda/connect
Connect user's OANDA account.

**Authentication Required:** Yes

**Request Body:** (application/x-www-form-urlencoded)
```
account_id: string
environment: "demo" or "live"
```

**Response:** `200 OK`
```json
{
  "message": "OANDA account connected successfully",
  "account_id": "123-456-789012-001",
  "environment": "demo",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /api/oanda/connection
Get user's OANDA connection status.

**Authentication Required:** Yes

**Response:** `200 OK`
```json
{
  "connected": true,
  "account_id": "123-456-789012-001",
  "environment": "demo",
  "status": "CONNECTED",
  "balance": 10000.0,
  "currency": "USD",
  "last_connected": "2024-01-01T00:00:00Z",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /api/oanda/market-data/{symbol}
Get current market data for a symbol.

**Authentication Required:** No

**Path Parameters:**
- `symbol`: Trading symbol (e.g., EURUSD)

**Response:** `200 OK`
```json
{
  "symbol": "EURUSD",
  "bid": 1.0845,
  "ask": 1.0847,
  "spread": 0.0002,
  "timestamp": "2024-01-01T00:00:00Z",
  "daily_change": 0.0015,
  "daily_change_percent": 0.138,
  "volume": 1500,
  "high": 1.0860,
  "low": 1.0830
}
```

#### POST /api/signals/generate/{symbol}
Generate a signal for a specific symbol.

**Authentication Required:** Yes

**Path Parameters:**
- `symbol`: Trading symbol (e.g., EURUSD)

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Signal generated for EURUSD",
  "signal": {
    "id": 1,
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "reliability": 85.5,
    "status": "ACTIVE",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /api/generate-signals-if-needed
Auto-generate signals if needed based on time and availability.

**Authentication Required:** No

**Query Parameters:**
- `force`: Force generation (boolean, default: false)

**Response:** `200 OK`
```json
{
  "message": "Generated 3 new signals",
  "generated_signals": [
    {
      "symbol": "EURUSD",
      "signal_id": 1,
      "signal_type": "BUY",
      "reliability": 85.5
    }
  ],
  "errors": [],
  "generated": true,
  "oanda_status": {
    "available": true,
    "status": "Connected"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### POST /api/calculate-position-size
Calculate optimal position size based on risk management.

**Authentication Required:** No

**Request Body:** (application/x-www-form-urlencoded)
```
symbol: string
account_balance: float
risk_percentage: float (0.01-0.10)
stop_loss_pips: float
```

**Response:** `200 OK`
```json
{
  "symbol": "EURUSD",
  "account_balance": 10000.0,
  "risk_percentage": 0.02,
  "stop_loss_pips": 20,
  "position_size": 0.1,
  "risk_amount": 200.0,
  "pip_value": 10.0,
  "margin_required": 108.5,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Admin Operations

#### POST /admin/generate-signals
Generate signals manually using OANDA API (admin only).

**Authentication Required:** Admin

**Request Body:** (application/x-www-form-urlencoded)
```
symbols: string (comma-separated symbols, optional)
```

**Response:** `200 OK`
```json
{
  "message": "Signal generation completed. Generated 5 signals.",
  "generated_signals": [
    {
      "symbol": "EURUSD",
      "signal_id": 1,
      "signal_type": "BUY",
      "entry_price": 1.0850,
      "reliability": 85.5,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "errors": [],
  "total_requested": 5,
  "total_generated": 5,
  "oanda_status": {
    "available": true,
    "status": "Connected"
  }
}
```

#### GET /admin/signals-by-source
Show all signals grouped by source (admin only).

**Authentication Required:** Admin

**Response:** `200 OK`
```json
{
  "sources": {
    "OANDA_AI": {
      "count": 1200,
      "signals": [...]
    },
    "MANUAL": {
      "count": 300,
      "signals": [...]
    }
  },
  "overall_stats": {
    "total_signals": 1500,
    "average_reliability": 78.5
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /admin/dashboard
Get comprehensive admin dashboard data.

**Authentication Required:** Admin

**Response:** `200 OK`
```json
{
  "signal_statistics": {
    "total_signals": 1500,
    "active_signals": 45,
    "average_reliability": 78.5
  },
  "user_statistics": {
    "total_users": 250,
    "active_users": 180,
    "admin_users": 5,
    "subscribed_users": 120
  },
  "oanda_health": {
    "available": true,
    "status": "Connected"
  },
  "recent_activity": {
    "signals_24h": 25,
    "signals_week": 150,
    "latest_signals": [...]
  },
  "system_info": {
    "admin_user": "admin",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "2.0.1"
  }
}
```

#### GET /admin/system-health
Get overall system health status.

**Authentication Required:** Admin

**Response:** `200 OK`
```json
{
  "overall_status": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "message": "Database connection OK"
    },
    "oanda_api": {
      "available": true,
      "status": "Connected"
    }
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "checked_by": "admin"
}
```

#### POST /admin/cleanup-expired-signals
Close all expired signals (admin only).

**Authentication Required:** Admin

**Response:** `200 OK`
```json
{
  "message": "Successfully closed 5 expired signals",
  "count": 5,
  "admin_user": "admin",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### User Management (Admin)

#### GET /users/
Get all users (admin only).

**Authentication Required:** Admin

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records (1-1000, default: 100)
- `active_only`: Filter only active users (boolean, default: false)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "username": "user123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /users/statistics
Get user statistics (admin only).

**Authentication Required:** Admin

**Response:** `200 OK`
```json
{
  "total_users": 250,
  "active_users": 180,
  "inactive_users": 70,
  "subscribed_users": 120,
  "admin_users": 5,
  "activation_rate": 72.0
}
```

#### PATCH /users/{user_id}/activate
Activate a user account (admin only).

**Authentication Required:** Admin

**Path Parameters:**
- `user_id`: ID of the user to activate

**Response:** `200 OK`
```json
{
  "message": "User user123 activated successfully"
}
```

#### PATCH /users/{user_id}/deactivate
Deactivate a user account (admin only).

**Authentication Required:** Admin

**Path Parameters:**
- `user_id`: ID of the user to deactivate

**Response:** `200 OK`
```json
{
  "message": "User user123 deactivated successfully"
}
```

### Health & Monitoring

#### GET /health
Basic health check endpoint.

**Authentication Required:** No

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "2.0.1",
  "database": "connected",
  "environment": "production"
}
```

#### GET /health/detailed
Detailed health check for all components.

**Authentication Required:** No

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "response_time_ms": 150,
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 50,
      "details": {...}
    },
    "http_client": {
      "status": "healthy",
      "response_time_ms": 100,
      "details": {...}
    }
  },
  "summary": {
    "total_components": 8,
    "healthy_components": 8,
    "degraded_components": 0,
    "unhealthy_components": 0
  }
}
```

#### GET /cache/health
Cache health check endpoint.

**Authentication Required:** No

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "cache_health": {
    "connected": true,
    "ping_time_ms": 5
  },
  "cache_info": {
    "used_memory": "2.5MB",
    "total_keys": 1500,
    "hit_rate": 0.85
  },
  "version": "2.0.1"
}
```

#### GET /cache/metrics
Cache performance metrics endpoint.

**Authentication Required:** No

**Response:** `200 OK`
```json
{
  "status": "success",
  "timestamp": "2024-01-01T00:00:00Z",
  "metrics": {
    "hit_rate": 0.85,
    "error_rate": 0.01,
    "total_operations": 10000,
    "hits": 8500,
    "misses": 1500,
    "errors": 10,
    "average_response_time_ms": 2.5,
    "last_health_check": "2024-01-01T00:00:00Z"
  }
}
```

#### POST /cache/invalidate
Cache invalidation endpoint.

**Authentication Required:** No

**Query Parameters:**
- `pattern`: Cache key pattern to invalidate (optional)

**Response:** `200 OK`
```json
{
  "status": "success",
  "timestamp": "2024-01-01T00:00:00Z",
  "message": "Invalidated all cache entries",
  "deleted_count": 1500,
  "version": "2.0.1"
}
```

#### GET /performance/metrics
Get comprehensive performance metrics.

**Authentication Required:** No

**Query Parameters:**
- `period`: Time period (1h, 6h, 24h, 7d, default: 1h)

**Response:** `200 OK`
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "period": "1h",
  "start_time": "2023-12-31T23:00:00Z",
  "overall_status": "healthy",
  "metrics": {
    "application": {
      "uptime_seconds": 86400,
      "total_requests": 5000,
      "avg_response_time": 150,
      "error_rate": 0.02
    },
    "database": {
      "healthy": true,
      "pool_size": 20,
      "active_connections": 5
    },
    "system": {
      "cpu_percent": 45.5,
      "memory_percent": 65.2
    }
  }
}
```

## Data Models

### User Models

#### User
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "full_name": "string",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-01T00:00:00Z",
  "subscription_active": true,
  "last_login": "2024-01-01T12:00:00Z"
}
```

#### UserStats
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "full_name": "string",
  "is_active": true,
  "is_admin": false,
  "subscription_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T12:00:00Z",
  "total_signals": 25,
  "active_signals": 3,
  "average_reliability": 78.5,
  "recent_signals_count": 5
}
```

### Signal Models

#### Signal
```json
{
  "id": 1,
  "symbol": "EURUSD",
  "signal_type": "BUY",
  "entry_price": 1.0850,
  "stop_loss": 1.0800,
  "take_profit": 1.0950,
  "reliability": 85.5,
  "status": "ACTIVE",
  "ai_analysis": "string",
  "confidence_score": 87.2,
  "risk_level": "MEDIUM",
  "is_public": true,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-01T06:00:00Z",
  "source": "OANDA_AI"
}
```

#### SignalCreate
```json
{
  "symbol": "EURUSD",
  "signal_type": "BUY",
  "entry_price": 1.0850,
  "stop_loss": 1.0800,
  "take_profit": 1.0950,
  "reliability": 85.5,
  "ai_analysis": "string",
  "confidence_score": 87.2,
  "risk_level": "MEDIUM",
  "expires_at": "2024-01-01T06:00:00Z"
}
```

### OANDA Models

#### OANDAConnection
```json
{
  "id": 1,
  "user_id": 1,
  "account_id": "123-456-789012-001",
  "environment": "demo",
  "account_currency": "USD",
  "is_active": true,
  "last_connected": "2024-01-01T00:00:00Z",
  "connection_status": "CONNECTED",
  "balance": 10000.0,
  "equity": 10050.0,
  "margin_used": 100.0,
  "margin_available": 9900.0,
  "unrealized_pl": 50.0,
  "auto_trading_enabled": false,
  "risk_tolerance": "MEDIUM",
  "max_position_size": 1.0,
  "daily_loss_limit": 1000.0,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Common Models

#### APIResponse
```json
{
  "message": "string",
  "success": true,
  "data": {},
  "errors": []
}
```

#### ErrorResponse
```json
{
  "error": "ErrorType",
  "message": "string",
  "details": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Webhooks

The API supports webhooks for real-time notifications about signal updates and system events. Webhooks can be configured in the user dashboard or via the API.

### Webhook Events

- `signal.created`: New signal created
- `signal.updated`: Signal updated
- `signal.closed`: Signal closed
- `signal.cancelled`: Signal cancelled
- `user.registered`: New user registered
- `user.subscription_changed`: Subscription status changed

### Webhook Payload Format

```json
{
  "event": "signal.created",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "signal_id": 1,
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "reliability": 85.5
  }
}
```

## SDK Examples

### Python SDK

```python
import requests
import json

class TradingSignalsSDK:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.token = None

    def authenticate(self, username, password):
        """Authenticate and get access token"""
        response = requests.post(
            f"{self.base_url}/token",
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return self.token

    def get_headers(self):
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get_latest_signals(self, limit=10):
        """Get latest trading signals"""
        response = requests.get(
            f"{self.base_url}/signals/latest",
            headers=self.get_headers(),
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def create_signal(self, signal_data):
        """Create a new signal"""
        response = requests.post(
            f"{self.base_url}/signals/",
            headers=self.get_headers(),
            json=signal_data
        )
        response.raise_for_status()
        return response.json()

    def get_oanda_market_data(self, symbol):
        """Get OANDA market data"""
        response = requests.get(
            f"{self.base_url}/api/oanda/market-data/{symbol}",
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

# Usage example
sdk = TradingSignalsSDK("https://your-api-domain.com", "your-api-key")

# Authenticate
sdk.authenticate("your_username", "your_password")

# Get latest signals
signals = sdk.get_latest_signals(limit=5)
print(f"Latest signals: {signals}")

# Create a signal
signal_data = {
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "stop_loss": 1.0800,
    "take_profit": 1.0950,
    "reliability": 85.5
}
created_signal = sdk.create_signal(signal_data)
print(f"Created signal: {created_signal}")

# Get market data
market_data = sdk.get_oanda_market_data("EURUSD")
print(f"Market data: {market_data}")
```

### JavaScript SDK

```javascript
class TradingSignalsSDK {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.token = null;
    }

    async authenticate(username, password) {
        const response = await fetch(`${this.baseUrl}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `username=${username}&password=${password}`
        });

        if (!response.ok) {
            throw new Error('Authentication failed');
        }

        const data = await response.json();
        this.token = data.access_token;
        return this.token;
    }

    getHeaders() {
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }

    async getLatestSignals(limit = 10) {
        const response = await fetch(
            `${this.baseUrl}/signals/latest?limit=${limit}`,
            { headers: this.getHeaders() }
        );

        if (!response.ok) {
            throw new Error('Failed to get signals');
        }

        return await response.json();
    }

    async createSignal(signalData) {
        const response = await fetch(`${this.baseUrl}/signals/`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(signalData)
        });

        if (!response.ok) {
            throw new Error('Failed to create signal');
        }

        return await response.json();
    }

    async getOANDAMarketData(symbol) {
        const response = await fetch(
            `${this.baseUrl}/api/oanda/market-data/${symbol}`,
            { headers: this.getHeaders() }
        );

        if (!response.ok) {
            throw new Error('Failed to get market data');
        }

        return await response.json();
    }
}

// Usage example
const sdk = new TradingSignalsSDK('https://your-api-domain.com', 'your-api-key');

// Authenticate
await sdk.authenticate('your_username', 'your_password');

// Get latest signals
const signals = await sdk.getLatestSignals(5);
console.log('Latest signals:', signals);

// Create a signal
const signalData = {
    symbol: 'EURUSD',
    signal_type: 'BUY',
    entry_price: 1.0850,
    stop_loss: 1.0800,
    take_profit: 1.0950,
    reliability: 85.5
};
const createdSignal = await sdk.createSignal(signalData);
console.log('Created signal:', createdSignal);

// Get market data
const marketData = await sdk.getOANDAMarketData('EURUSD');
console.log('Market data:', marketData);
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Problem**: 401 Unauthorized error
**Solution**:
- Check that your JWT token is valid and not expired
- Ensure the Authorization header is correctly formatted
- Verify your credentials are correct

```bash
# Check token format
curl -X GET "https://your-api-domain.com/health" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 2. Rate Limiting

**Problem**: 429 Too Many Requests error
**Solution**:
- Implement exponential backoff
- Check rate limit headers
- Consider upgrading your subscription plan

```javascript
// Implement rate limiting in your code
async function makeRequestWithRetry(url, options, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetch(url, options);
            if (response.status === 429) {
                const resetTime = parseInt(response.headers.get('X-RateLimit-Reset'));
                const waitTime = resetTime - Math.floor(Date.now() / 1000);
                await new Promise(resolve => setTimeout(resolve, waitTime * 1000));
                continue;
            }
            return response;
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
        }
    }
}
```

#### 3. OANDA Connection Issues

**Problem**: OANDA API not available
**Solution**:
- Check OANDA service status
- Verify your API credentials
- Ensure your account is properly funded

```bash
# Check OANDA health
curl -X GET "https://your-api-domain.com/api/oanda/health"
```

#### 4. Database Connection Issues

**Problem**: Database connection failed
**Solution**:
- Check database health endpoint
- Verify your database URL configuration
- Ensure proper network connectivity

```bash
# Check database health
curl -X GET "https://your-api-domain.com/health/detailed"
```

#### 5. Signal Generation Failures

**Problem**: Signal generation fails or returns low reliability
**Solution**:
- Check market data availability
- Verify AI service status
- Ensure proper symbol formatting

```bash
# Check system health
curl -X GET "https://your-api-domain.com/admin/system-health" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Debug Mode

For development and debugging, you can enable debug mode to get detailed error information:

```bash
# Enable debug headers
curl -X GET "https://your-api-domain.com/api/signals/latest" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Debug: true"
```

### Logging

The API provides comprehensive logging. Check your application logs for detailed error information:

```javascript
// Check logs for specific errors
const checkLogs = async () => {
    const response = await fetch('https://your-api-domain.com/admin/logs', {
        headers: sdk.getHeaders()
    });
    const logs = await response.json();
    console.log('Recent logs:', logs);
};
```

## Changelog

### Version 2.0.1 (Current)
- Added comprehensive async health monitoring
- Enhanced OANDA integration with improved error handling
- Added performance monitoring dashboard
- Improved rate limiting and security
- Enhanced caching system with warming
- Added async task scheduling
- Improved error handling with circuit breakers

### Version 2.0.0
- Complete refactoring with async optimization
- Added AI-powered signal analysis
- Enhanced user management and subscription system
- Improved OANDA integration
- Added comprehensive monitoring and metrics
- Enhanced security and authentication

### Version 1.5.0
- Added OANDA API integration
- Enhanced signal generation algorithms
- Added user subscription management
- Improved database performance with indexing
- Added comprehensive logging

### Version 1.0.0
- Initial release
- Basic signal generation
- User authentication
- Simple dashboard

## Support

For technical support and questions:

- **Email**: support@trading-system.com
- **Documentation**: https://docs.trading-system.com
- **Status Page**: https://status.trading-system.com
- **Community**: https://community.trading-system.com

## Legal

### Terms of Service
By using this API, you agree to our terms of service available at https://trading-system.com/terms

### Privacy Policy
Your data is handled according to our privacy policy at https://trading-system.com/privacy

### License
This API is provided under the MIT License. See LICENSE file for details.

### Risk Disclaimer
Trading signals and market data are provided for informational purposes only. Past performance is not indicative of future results. Trading involves substantial risk and is not suitable for all investors.
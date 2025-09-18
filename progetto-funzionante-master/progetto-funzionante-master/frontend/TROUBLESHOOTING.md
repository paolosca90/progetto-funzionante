# Troubleshooting Guide for AI Trading System API

This guide provides comprehensive troubleshooting information for common issues encountered when using the AI Trading System API.

## Table of Contents

1. [Authentication Issues](#authentication-issues)
2. [API Connection Problems](#api-connection-problems)
3. [Rate Limiting Issues](#rate-limiting-issues)
4. [OANDA Integration Problems](#oanda-integration-problems)
5. [Database Connection Issues](#database-connection-issues)
6. [Signal Generation Problems](#signal-generation-problems)
7. [Performance Issues](#performance-issues)
8. [Environment Configuration](#environment-configuration)
9. [Debug Mode and Logging](#debug-mode-and-logging)
10. [Common Error Codes](#common-error-codes)
11. [Advanced Troubleshooting](#advanced-troubleshooting)

## Authentication Issues

### Problem: 401 Unauthorized Error

**Symptoms:**
- API calls return 401 status code
- Error message: "Not authenticated" or "Invalid token"

**Causes:**
- Invalid or expired JWT token
- Missing Authorization header
- Incorrect token format
- Credentials changed or revoked

**Solutions:**

#### 1. Check Token Validity

```python
import requests
import jwt
from datetime import datetime

def check_token_validity(token):
    try:
        # Decode token (without verification to check expiry)
        decoded = jwt.decode(token, options={"verify_signature": False})

        # Check expiration
        exp_time = datetime.fromtimestamp(decoded['exp'])
        now = datetime.now()

        if now > exp_time:
            print("Token has expired")
            return False

        print(f"Token is valid until {exp_time}")
        return True

    except Exception as e:
        print(f"Token error: {e}")
        return False

# Usage
token = "your_jwt_token"
check_token_validity(token)
```

#### 2. Refresh Token

```python
def refresh_access_token(refresh_token):
    response = requests.post(
        "https://your-api-domain.com/token/refresh",
        json={"refresh_token": refresh_token}
    )

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Token refresh failed: {response.status_code}")
        return None

# Usage
new_token = refresh_access_token("your_refresh_token")
```

#### 3. Re-authenticate

```python
def reauthenticate(username, password):
    response = requests.post(
        "https://your-api-domain.com/token",
        data={"username": username, "password": password}
    )

    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"Authentication failed: {response.status_code}")
        return None
```

#### 4. Check Authorization Header Format

```python
def test_auth_headers(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(
        "https://your-api-domain.com/users/me",
        headers=headers
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
```

### Problem: Invalid Credentials

**Symptoms:**
- Authentication fails with 401 error
- Error message: "Invalid username or password"

**Solutions:**

#### 1. Verify Credentials

```python
def verify_credentials(username, password):
    print(f"Username: {username}")
    print(f"Password length: {len(password)}")
    print(f"Password contains special chars: {any(not c.isalnum() for c in password)}")
```

#### 2. Check Account Status

```python
def check_account_status(token):
    headers = {"Authorization": f"Bearer {token}"}

    # Try to get user profile
    response = requests.get(
        "https://your-api-domain.com/users/me",
        headers=headers
    )

    if response.status_code == 200:
        user_data = response.json()
        print(f"Account active: {user_data.get('is_active', False)}")
        print(f"Subscription active: {user_data.get('subscription_active', False)}")
    else:
        print(f"Cannot check account status: {response.status_code}")
```

## API Connection Problems

### Problem: Connection Timeout

**Symptoms:**
- Requests timeout after 30 seconds
- Error message: "Connection timeout" or "Read timeout"

**Causes:**
- Network connectivity issues
- Server overload
- Firewall blocking requests
- DNS resolution problems

**Solutions:**

#### 1. Test Basic Connectivity

```python
import requests
import time

def test_connectivity():
    endpoints = [
        "https://your-api-domain.com/health",
        "https://your-api-domain.com/api/signals/latest",
        "https://your-api-domain.com/users/me"
    ]

    for endpoint in endpoints:
        try:
            start_time = time.time()
            response = requests.get(endpoint, timeout=10)
            response_time = time.time() - start_time

            print(f"{endpoint}: {response.status_code} ({response_time:.2f}s)")

        except requests.exceptions.Timeout:
            print(f"{endpoint}: Timeout")
        except requests.exceptions.ConnectionError:
            print(f"{endpoint}: Connection error")
        except Exception as e:
            print(f"{endpoint}: {e}")

# Usage
test_connectivity()
```

#### 2. Configure Timeouts

```python
def make_request_with_timeout(url, headers=None, timeout=30):
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        return response
    except requests.exceptions.Timeout:
        print(f"Request timed out after {timeout} seconds")
        return None
    except requests.exceptions.ConnectionError:
        print("Connection error occurred")
        return None
```

#### 3. Implement Retry Logic

```python
import time
from functools import wraps

def retry_request(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator

@retry_request(max_retries=3, delay=1)
def get_signals_with_retry(token):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(
        "https://your-api-domain.com/api/signals/latest",
        headers=headers,
        timeout=30
    )
```

### Problem: SSL Certificate Issues

**Symptoms:**
- SSL certificate verification errors
- Connection refused due to SSL

**Solutions:**

#### 1. Test SSL Connection

```python
import ssl
import socket

def test_ssl_connection(hostname, port=443):
    try:
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"SSL connection successful")
                print(f"Certificate subject: {ssock.getpeercert().get('subject')}")
                return True

    except Exception as e:
        print(f"SSL connection failed: {e}")
        return False

# Usage
test_ssl_connection("your-api-domain.com")
```

#### 2. Disable SSL Verification (Temporary)

```python
def make_request_without_ssl_verification(url):
    try:
        response = requests.get(url, verify=False)
        return response
    except Exception as e:
        print(f"Request failed: {e}")
        return None

# Warning: This is not secure for production use
```

## Rate Limiting Issues

### Problem: 429 Too Many Requests

**Symptoms:**
- API returns 429 status code
- Error message: "Rate limit exceeded"

**Causes:**
- Exceeding request limits
- Bot activity
- High-frequency requests

**Solutions:**

#### 1. Check Rate Limit Headers

```python
def check_rate_limits(response):
    if 'X-RateLimit-Limit' in response.headers:
        print(f"Rate limit: {response.headers['X-RateLimit-Limit']}")
        print(f"Remaining: {response.headers['X-RateLimit-Remaining']}")
        print(f"Reset time: {response.headers['X-RateLimit-Reset']}")
```

#### 2. Implement Rate Limiting

```python
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=100, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)

    def can_make_request(self, user_id):
        now = time.time()
        user_requests = self.requests[user_id]

        # Remove old requests
        user_requests = [req_time for req_time in user_requests if now - req_time < self.window]
        self.requests[user_id] = user_requests

        # Check if we can make a request
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            return True

        return False

    def wait_time(self, user_id):
        now = time.time()
        user_requests = self.requests[user_id]

        if len(user_requests) < self.max_requests:
            return 0

        # Calculate wait time until oldest request is outside window
        oldest_request = min(user_requests)
        wait_time = self.window - (now - oldest_request)

        return max(0, wait_time)

# Usage
limiter = RateLimiter(max_requests=100, window=60)

def make_rate_limited_request(url, user_id="default"):
    if not limiter.can_make_request(user_id):
        wait_time = limiter.wait_time(user_id)
        print(f"Rate limited. Wait {wait_time:.2f} seconds")
        time.sleep(wait_time)

    return requests.get(url)
```

#### 3. Exponential Backoff

```python
import time

def make_request_with_backoff(url, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)

            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2 ** attempt))
                print(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                continue

            return response

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff

    return None
```

## OANDA Integration Problems

### Problem: OANDA API Not Available

**Symptoms:**
- OANDA-related endpoints fail
- Error message: "OANDA API not available"

**Solutions:**

#### 1. Check OANDA Health

```python
def check_oanda_health(token):
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        "https://your-api-domain.com/api/oanda/health",
        headers=headers
    )

    if response.status_code == 200:
        health_data = response.json()
        print(f"OANDA available: {health_data.get('available', False)}")
        print(f"Status: {health_data.get('status', 'Unknown')}")
        print(f"Response time: {health_data.get('response_time_ms', 0)}ms")
        return health_data
    else:
        print(f"Failed to check OANDA health: {response.status_code}")
        return None
```

#### 2. Test Direct OANDA Connection

```python
def test_direct_oanda_connection(api_key, account_id, environment="demo"):
    base_url = "https://api-fxpractice.oanda.com/v3" if environment == "demo" else "https://api-fxtrade.oanda.com/v3"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Test account endpoint
    account_url = f"{base_url}/accounts/{account_id}"
    response = requests.get(account_url, headers=headers)

    print(f"Direct OANDA connection test: {response.status_code}")
    print(f"Response: {response.text}")

    return response.status_code == 200
```

#### 3. Verify OANDA Credentials

```python
def verify_oanda_credentials(api_key, account_id):
    print(f"API Key length: {len(api_key)}")
    print(f"API Key format: {api_key[:10]}...")
    print(f"Account ID: {account_id}")
    print(f"Account ID format: {'-' in account_id}")
```

### Problem: Invalid OANDA Account

**Symptoms:**
- Account connection fails
- Error message: "Invalid account ID" or "Account not found"

**Solutions:**

#### 1. Validate Account ID Format

```python
import re

def validate_oanda_account_id(account_id):
    """Validate OANDA account ID format"""
    pattern = r'^\d{3}-\d{3}-\d{6}-\d{3}$'

    if re.match(pattern, account_id):
        print("Account ID format is valid")
        return True
    else:
        print("Account ID format is invalid")
        print("Expected format: XXX-XXX-XXXXXX-XXX")
        return False
```

#### 2. Check Account Permissions

```python
def check_oanda_account_permissions(api_key, account_id):
    base_url = "https://api-fxpractice.oanda.com/v3"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Check account permissions
    permissions_url = f"{base_url}/accounts/{account_id}/permissions"
    response = requests.get(permissions_url, headers=headers)

    if response.status_code == 200:
        permissions = response.json()
        print("Account permissions:")
        for permission in permissions.get('permissions', []):
            print(f"  - {permission}")
    else:
        print(f"Failed to get permissions: {response.status_code}")
```

## Database Connection Issues

### Problem: Database Connection Failed

**Symptoms:**
- API endpoints return 500 errors
- Error message: "Database connection failed"

**Solutions:**

#### 1. Check Database Health

```python
def check_database_health(token):
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        "https://your-api-domain.com/health/detailed",
        headers=headers
    )

    if response.status_code == 200:
        health_data = response.json()
        db_status = health_data.get('components', {}).get('database', {})
        print(f"Database status: {db_status.get('status', 'Unknown')}")
        print(f"Response time: {db_status.get('response_time_ms', 0)}ms")
        return db_status.get('status') == 'healthy'
    else:
        print(f"Failed to check database health: {response.status_code}")
        return False
```

#### 2. Test Database Query Performance

```python
def test_database_performance(token):
    headers = {"Authorization": f"Bearer {token}"}

    # Test signal query
    start_time = time.time()
    response = requests.get(
        "https://your-api-domain.com/api/signals/latest?limit=50",
        headers=headers
    )
    query_time = time.time() - start_time

    if response.status_code == 200:
        signals = response.json()
        print(f"Retrieved {len(signals)} signals in {query_time:.2f}s")

        if query_time > 5:  # Slow query threshold
            print("Warning: Query performance is slow")
    else:
        print(f"Query failed: {response.status_code}")
```

## Signal Generation Problems

### Problem: Signal Generation Fails

**Symptoms:**
- Signal generation endpoints fail
- Error message: "Failed to generate signal"

**Solutions:**

#### 1. Check AI Service Status

```python
def check_ai_service_status(token):
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        "https://your-api-domain.com/health/detailed",
        headers=headers
    )

    if response.status_code == 200:
        health_data = response.json()
        components = health_data.get('components', {})

        # Check AI-related services
        ai_services = ['ai_service', 'gemini_api', 'signal_engine']
        for service in ai_services:
            if service in components:
                status = components[service].get('status', 'unknown')
                print(f"{service}: {status}")
```

#### 2. Test Signal Generation

```python
def test_signal_generation(token, symbol="EURUSD"):
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"https://your-api-domain.com/api/signals/generate/{symbol}",
        headers=headers
    )

    print(f"Signal generation status: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        signal_data = response.json()
        print(f"Generated signal: {signal_data.get('success', False)}")
        if signal_data.get('success'):
            signal = signal_data.get('signal', {})
            print(f"Symbol: {signal.get('symbol')}")
            print(f"Type: {signal.get('signal_type')}")
            print(f"Reliability: {signal.get('reliability')}")
```

#### 3. Check Market Data Availability

```python
def check_market_data_availability(token, symbol="EURUSD"):
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"https://your-api-domain.com/api/oanda/market-data/{symbol}",
        headers=headers
    )

    if response.status_code == 200:
        market_data = response.json()
        print(f"Market data available for {symbol}")
        print(f"  Bid: {market_data.get('bid')}")
        print(f"  Ask: {market_data.get('ask')}")
        print(f"  Spread: {market_data.get('spread')}")
        return True
    else:
        print(f"Market data not available: {response.status_code}")
        return False
```

## Performance Issues

### Problem: Slow API Response Times

**Symptoms:**
- API responses take longer than expected
- Timeouts on complex queries

**Solutions:**

#### 1. Benchmark API Performance

```python
import time
import statistics

def benchmark_api_performance(token, endpoint="/api/signals/latest", iterations=10):
    headers = {"Authorization": f"Bearer {token}"}
    response_times = []

    for i in range(iterations):
        start_time = time.time()
        response = requests.get(f"https://your-api-domain.com{endpoint}", headers=headers)
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        response_times.append(response_time)

        print(f"Iteration {i+1}: {response_time:.2f}ms")

    # Calculate statistics
    avg_time = statistics.mean(response_times)
    median_time = statistics.median(response_times)
    min_time = min(response_times)
    max_time = max(response_times)

    print(f"\nPerformance Summary:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Median: {median_time:.2f}ms")
    print(f"  Min: {min_time:.2f}ms")
    print(f"  Max: {max_time:.2f}ms")

    # Performance thresholds
    if avg_time > 1000:
        print("  Warning: Average response time is slow (> 1s)")
    if max_time > 5000:
        print("  Warning: Maximum response time is very slow (> 5s)")

    return response_times
```

#### 2. Monitor Memory Usage

```python
import psutil
import os

def monitor_memory_usage():
    process = psutil.Process(os.getpid())

    while True:
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()

        print(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB ({memory_percent:.1f}%)")

        if memory_percent > 80:
            print("Warning: High memory usage")

        time.sleep(5)
```

#### 3. Optimize Query Parameters

```python
def optimize_signal_queries(token):
    headers = {"Authorization": f"Bearer {token}"}

    # Test different query parameters
    queries = [
        "/api/signals/latest?limit=10",
        "/api/signals/latest?limit=50",
        "/api/signals/latest?limit=100",
        "/signals/?skip=0&limit=10",
        "/signals/?skip=0&limit=50",
        "/signals/?skip=0&limit=100"
    ]

    for query in queries:
        start_time = time.time()
        response = requests.get(f"https://your-api-domain.com{query}", headers=headers)
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        print(f"{query}: {response_time:.2f}ms ({response.status_code})")
```

## Environment Configuration

### Problem: Environment Variables Missing

**Symptoms:**
- Application fails to start
- Error message: "Missing required environment variables"

**Solutions:**

#### 1. Check Environment Variables

```python
import os

def check_environment_variables():
    required_vars = [
        'DATABASE_URL',
        'JWT_SECRET_KEY',
        'OANDA_API_KEY',
        'OANDA_ACCOUNT_ID',
        'GEMINI_API_KEY',
        'EMAIL_HOST',
        'EMAIL_USER',
        'EMAIL_PASSWORD'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"Missing environment variables: {missing_vars}")
        return False
    else:
        print("All required environment variables are set")
        return True
```

#### 2. Validate Environment Variables

```python
def validate_environment_variables():
    validations = []

    # Validate JWT secret key
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    if jwt_secret and len(jwt_secret) < 32:
        validations.append("JWT_SECRET_KEY must be at least 32 characters")

    # Validate database URL
    db_url = os.getenv('DATABASE_URL')
    if db_url and not db_url.startswith(('postgresql://', 'mysql://', 'sqlite:///')):
        validations.append("DATABASE_URL must be a valid database connection string")

    # Validate OANDA environment
    oanda_env = os.getenv('OANDA_ENVIRONMENT', 'demo')
    if oanda_env not in ['demo', 'live']:
        validations.append("OANDA_ENVIRONMENT must be 'demo' or 'live'")

    if validations:
        print("Environment variable validation issues:")
        for issue in validations:
            print(f"  - {issue}")
        return False
    else:
        print("All environment variables are valid")
        return True
```

## Debug Mode and Logging

### Enable Debug Mode

```python
def enable_debug_mode():
    """Enable debug mode for detailed error information"""
    import logging

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Enable debug headers
    debug_headers = {
        "X-Debug": "true",
        "X-Request-ID": "debug-request-123"
    }

    return debug_headers
```

### Advanced Logging

```python
import logging
import json
from datetime import datetime

class APILogger:
    def __init__(self, log_file="api_debug.log"):
        self.logger = logging.getLogger('api_debug')
        self.logger.setLevel(logging.DEBUG)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_request(self, method, url, headers=None, data=None):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'request',
            'method': method,
            'url': url,
            'headers': headers,
            'data': data
        }
        self.logger.debug(f"REQUEST: {json.dumps(log_entry, indent=2)}")

    def log_response(self, status_code, headers, response_data, response_time):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'response',
            'status_code': status_code,
            'headers': headers,
            'response_data': response_data,
            'response_time_ms': response_time
        }
        self.logger.debug(f"RESPONSE: {json.dumps(log_entry, indent=2)}")

    def log_error(self, error_message, exception=None):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'error',
            'message': error_message,
            'exception': str(exception) if exception else None
        }
        self.logger.error(f"ERROR: {json.dumps(log_entry, indent=2)}")

# Usage
logger = APILogger()

def make_logged_request(url, method='GET', headers=None, data=None):
    logger.log_request(method, url, headers, data)

    start_time = time.time()

    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response_time = (time.time() - start_time) * 1000

        logger.log_response(
            response.status_code,
            dict(response.headers),
            response.text if response.text else None,
            response_time
        )

        return response

    except Exception as e:
        logger.log_error(f"Request failed: {e}", e)
        raise
```

## Common Error Codes

### 400 Bad Request

**Cause:** Invalid request parameters
**Solution:** Check request body and parameters

```python
def handle_400_error(response):
    error_data = response.json()
    print(f"Bad Request: {error_data.get('message', 'Unknown error')}")

    # Check for validation errors
    if 'errors' in error_data:
        for field, errors in error_data['errors'].items():
            print(f"  {field}: {', '.join(errors)}")
```

### 401 Unauthorized

**Cause:** Authentication failed
**Solution:** Check token and credentials

```python
def handle_401_error(response):
    error_data = response.json()
    print(f"Unauthorized: {error_data.get('message', 'Authentication failed')}")

    # Try to re-authenticate
    print("Attempting to re-authenticate...")
    # Add re-authentication logic here
```

### 403 Forbidden

**Cause:** Insufficient permissions
**Solution:** Check user permissions and subscription

```python
def handle_403_error(response):
    error_data = response.json()
    print(f"Forbidden: {error_data.get('message', 'Insufficient permissions')}")

    # Check user permissions
    print("Checking user permissions...")
    # Add permission check logic here
```

### 404 Not Found

**Cause:** Resource not found
**Solution:** Check URL and resource existence

```python
def handle_404_error(response):
    error_data = response.json()
    print(f"Not Found: {error_data.get('message', 'Resource not found')}")

    # Check if URL is correct
    print("Please verify the URL and resource ID")
```

### 429 Too Many Requests

**Cause:** Rate limit exceeded
**Solution:** Implement rate limiting and backoff

```python
def handle_429_error(response):
    error_data = response.json()
    print(f"Rate Limited: {error_data.get('message', 'Rate limit exceeded')}")

    # Check rate limit headers
    retry_after = response.headers.get('Retry-After', 60)
    print(f"Retry after {retry_after} seconds")

    # Implement retry logic
    time.sleep(int(retry_after))
```

### 500 Internal Server Error

**Cause:** Server error
**Solution:** Check server logs and health

```python
def handle_500_error(response):
    error_data = response.json()
    print(f"Server Error: {error_data.get('message', 'Internal server error')}")

    # Check server health
    print("Checking server health...")
    # Add health check logic here
```

## Advanced Troubleshooting

### Network Diagnostics

```python
import socket
import subprocess
import platform

def run_network_diagnostics():
    print("=== Network Diagnostics ===")

    # Test DNS resolution
    try:
        ip = socket.gethostbyname("your-api-domain.com")
        print(f"DNS resolution: {ip}")
    except socket.gaierror:
        print("DNS resolution failed")

    # Test connectivity
    try:
        result = subprocess.run(["ping", "-c", "3", "your-api-domain.com"],
                              capture_output=True, text=True)
        print(f"Ping test: {result.returncode == 0}")
        if result.returncode == 0:
            print(f"  {result.stdout}")
    except FileNotFoundError:
        print("Ping command not available")

    # Test port connectivity
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(("your-api-domain.com", 443))
        sock.close()

        if result == 0:
            print("Port 443 (HTTPS): Open")
        else:
            print("Port 443 (HTTPS): Closed or blocked")
    except Exception as e:
        print(f"Port test failed: {e}")
```

### SSL/TLS Diagnostics

```python
import ssl
import socket

def test_ssl_configuration():
    print("=== SSL/TLS Diagnostics ===")

    try:
        context = ssl.create_default_context()

        # Test SSL version support
        print("Testing SSL versions...")
        for protocol in [ssl.PROTOCOL_TLSv1_2, ssl.PROTOCOL_TLSv1_3]:
            try:
                context.minimum_version = protocol
                with socket.create_connection(("your-api-domain.com", 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname="your-api-domain.com") as ssock:
                        print(f"  SSL version {protocol}: Supported")
            except Exception as e:
                print(f"  SSL version {protocol}: Not supported ({e})")

        # Test cipher suites
        print("Testing cipher suites...")
        context = ssl.create_default_context()
        with socket.create_connection(("your-api-domain.com", 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname="your-api-domain.com") as ssock:
                cipher = ssock.cipher()
                print(f"  Cipher: {cipher[0]}")
                print(f"  Protocol version: {ssock.version()}")
                print(f"  Certificate subject: {ssock.getpeercert().get('subject')}")

    except Exception as e:
        print(f"SSL test failed: {e}")
```

### Comprehensive Health Check

```python
def comprehensive_health_check(token):
    print("=== Comprehensive Health Check ===")

    headers = {"Authorization": f"Bearer {token}"}

    # Check main health
    print("1. Main health endpoint...")
    response = requests.get("https://your-api-domain.com/health", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        health_data = response.json()
        print(f"   Overall status: {health_data.get('status', 'Unknown')}")

    # Check detailed health
    print("\n2. Detailed health endpoint...")
    response = requests.get("https://your-api-domain.com/health/detailed", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        health_data = response.json()
        components = health_data.get('components', {})
        for component, status in components.items():
            print(f"   {component}: {status.get('status', 'Unknown')}")

    # Check OANDA health
    print("\n3. OANDA health...")
    response = requests.get("https://your-api-domain.com/api/oanda/health", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        oanda_health = response.json()
        print(f"   Available: {oanda_health.get('available', False)}")
        print(f"   Status: {oanda_health.get('status', 'Unknown')}")

    # Test signal retrieval
    print("\n4. Signal retrieval...")
    response = requests.get("https://your-api-domain.com/api/signals/latest?limit=1", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        signals = response.json()
        print(f"   Signals retrieved: {len(signals)}")

    # Test user profile
    print("\n5. User profile...")
    response = requests.get("https://your-api-domain.com/users/me", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        user_data = response.json()
        print(f"   User: {user_data.get('username', 'Unknown')}")
        print(f"   Subscription: {user_data.get('subscription_active', False)}")

    print("\n=== Health Check Complete ===")
```

This comprehensive troubleshooting guide provides solutions for common issues encountered when using the AI Trading System API. The guide includes practical code examples for diagnosing and resolving problems related to authentication, connectivity, rate limiting, OANDA integration, database issues, and performance optimization.
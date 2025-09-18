# TestSprite Configuration for AI Trading System

## Overview

This comprehensive TestSprite configuration provides production-ready testing capabilities for the AI Trading System, including API endpoint testing, authentication flows, OANDA integration, database operations, error handling, and performance benchmarking.

## 🚀 Quick Start

### 1. Setup Test Environment

```bash
# Run the test environment setup script
python setup_test_environment.py
```

This will:
- Create a virtual environment
- Install all dependencies
- Set up test directories
- Create configuration files
- Generate sample tests

### 2. Run Comprehensive Tests

```bash
# Run all tests
python run_tests.py

# Or using the comprehensive TestSprite runner
python testsprite_config.py
```

## 📁 Test Structure

```
progetto-funzionante-master/
├── testsprite_config.py          # Main TestSprite configuration
├── conftest.py                   # Pytest fixtures and configuration
├── pytest.ini                   # Pytest configuration
├── setup_test_environment.py     # Test environment setup script
├── run_tests.py                 # Test runner script
├── tests/
│   ├── unit/                    # Unit tests
│   │   ├── test_auth_service.py
│   │   ├── test_signal_service.py
│   │   └── ...
│   ├── integration/             # Integration tests
│   │   ├── test_database_integration.py
│   │   ├── test_oanda_integration.py
│   │   └── ...
│   ├── api/                     # API endpoint tests
│   │   ├── test_health_endpoints.py
│   │   ├── test_auth_endpoints.py
│   │   ├── test_signal_endpoints.py
│   │   └── ...
│   ├── performance/             # Performance tests
│   │   ├── test_load_testing.py
│   │   ├── test_response_times.py
│   │   └── ...
│   └── security/                # Security tests
│       ├── test_authentication.py
│       ├── test_authorization.py
│       └── ...
├── test_reports/                # Test reports directory
│   ├── html/                    # HTML coverage reports
│   ├── coverage/                # Coverage reports
│   └── performance/             # Performance reports
└── .github/workflows/           # CI/CD pipeline configuration
    └── test-automation.yml
```

## 🧪 Test Categories

### 1. Unit Tests
**Location:** `tests/unit/`

**Purpose:** Test individual components in isolation

**Examples:**
- Password hashing and verification
- JWT token generation and validation
- Signal calculation algorithms
- Database model operations

**Running:**
```bash
pytest tests/unit/ -v
```

### 2. Integration Tests
**Location:** `tests/integration/`

**Purpose:** Test component interactions

**Examples:**
- Database-Service integration
- Cache-Database synchronization
- Email service integration
- Configuration validation

**Running:**
```bash
pytest tests/integration/ -v
```

### 3. API Tests
**Location:** `tests/api/`

**Purpose:** Test HTTP API endpoints

**Examples:**
- Health check endpoints
- Authentication flows
- Signal management endpoints
- Admin functionality

**Running:**
```bash
pytest tests/api/ -v
```

### 4. Performance Tests
**Location:** `tests/performance/`

**Purpose:** Test system performance under load

**Examples:**
- Response time benchmarks
- Load testing
- Memory usage monitoring
- Database query optimization

**Running:**
```bash
pytest tests/performance/ -v
```

### 5. Security Tests
**Location:** `tests/security/`

**Purpose:** Test security vulnerabilities

**Examples:**
- Authentication bypass attempts
- SQL injection prevention
- XSS vulnerability testing
- Rate limiting effectiveness

**Running:**
```bash
pytest tests/security/ -v
```

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
minversion = 6.0
addopts = --cov=frontend --cov-report=term-missing --cov-report=html --junitxml=test-results.xml
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    performance: Performance tests
    security: Security tests
```

### Environment Variables

Create a `.env.test` file:

```bash
# Testing Configuration
TESTING=true
ENVIRONMENT=testing

# Database
DATABASE_URL=sqlite:///:memory:

# Security
JWT_SECRET_KEY=test-secret-key-for-testing-only

# OANDA Integration
OANDA_API_KEY=test-oanda-api-key
OANDA_ACCOUNT_ID=test-account-id
OANDA_ENVIRONMENT=practice

# AI Integration
GEMINI_API_KEY=test-gemini-api-key

# Email (Optional for testing)
EMAIL_HOST=
EMAIL_USER=
EMAIL_PASSWORD=
EMAIL_FROM=

# Cache
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300
```

## 📊 Test Data Management

### Test Data Factory

The `TestDataManager` class provides utilities for generating consistent test data:

```python
# Generate test user data
user_data = TestDataManager.generate_test_user()

# Generate test signal data
signal_data = TestDataManager.generate_test_signal_data("EURUSD")

# Generate OANDA mock data
oanda_data = TestDataManager.generate_oanda_mock_data("EURUSD")
```

### Available Test Symbols

```python
TEST_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
    "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "GOLD",
    "BTCUSD", "ETHUSD", "SPX500", "NAS100"
]
```

## 🔍 Test Suite Examples

### 1. Health Check Tests

```python
class TestHealthEndpoints:
    def test_basic_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]

    def test_cache_health_check(self, client):
        response = client.get("/cache/health")
        assert response.status_code == 200
        assert "cache_health" in response.json()
```

### 2. Authentication Tests

```python
class TestAuthentication:
    def test_user_registration(self, client):
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
        response = client.post("/register", json=user_data)
        assert response.status_code == 201

    def test_user_login(self, client, test_user):
        response = client.post("/token", data={
            "username": test_user.username,
            "password": "testpassword123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
```

### 3. Signal Tests

```python
class TestSignalEndpoints:
    def test_get_latest_signals(self, client, auth_headers):
        response = client.get("/signals/latest", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_signal(self, client, auth_headers):
        signal_data = TestDataManager.generate_test_signal_data("EURUSD")
        response = client.post("/signals/", json=signal_data, headers=auth_headers)
        assert response.status_code == 201
```

### 4. Performance Tests

```python
class TestPerformance:
    def test_signal_generation_performance(self, benchmark):
        def generate_signal():
            return TestDataManager.generate_test_signal_data("EURUSD")

        result = benchmark(generate_signal)
        assert result["avg_response_time_ms"] < 100
```

## 📈 Performance Benchmarking

The TestSprite configuration includes comprehensive performance benchmarking:

```python
# Run performance benchmarks
async def run_performance_benchmarks():
    runner = ComprehensiveTestRunner()

    # Benchmark key endpoints
    await runner.benchmark.benchmark_endpoint("GET", "/health", iterations=50)
    await runner.benchmark.benchmark_endpoint("GET", "/signals/latest", iterations=30)

    # Get performance summary
    summary = runner.benchmark.get_summary()
    print(f"Average response time: {summary['avg_response_time']}ms")
```

## 🔒 Security Testing

### Security Test Scenarios

```python
class TestSecurity:
    def test_sql_injection_prevention(self, client):
        malicious_payload = {"username": "admin' OR '1'='1", "password": "password"}
        response = client.post("/token", data=malicious_payload)
        assert response.status_code == 401

    def test_rate_limiting(self, client):
        # Make multiple rapid requests
        responses = []
        for i in range(15):
            response = client.post("/token", data={"username": "invalid", "password": "invalid"})
            responses.append(response.status_code)

        assert 429 in responses  # Should be rate limited
```

## 🚦 CI/CD Integration

### GitHub Actions

The configuration includes a comprehensive GitHub Actions workflow that:

1. **Runs on:** Push to main/master/develop branches and pull requests
2. **Executes:**
   - Unit tests
   - Integration tests
   - API tests
   - Performance tests
   - Security scans (Bandit, Safety, Semgrep)
   - Coverage reporting

### Manual Test Execution

```bash
# Run specific test category
pytest tests/unit/ -v

# Run with coverage
pytest --cov=frontend --cov-report=html

# Run performance tests
pytest tests/performance/ -v

# Run security tests
pytest tests/security/ -v
```

## 📊 Test Reports

### Generated Reports

1. **HTML Coverage Report:** `test_reports/html/index.html`
2. **JUnit XML:** `test-results.xml`
3. **Performance Report:** `test_results.json`
4. **Security Reports:** `security-reports/`

### Report Analysis

The comprehensive test runner generates detailed reports including:

- **Test Summary:** Total tests, pass/fail rates
- **Performance Metrics:** Response times, success rates
- **Security Findings:** Vulnerability reports
- **Coverage Analysis:** Code coverage metrics
- **Recommendations:** Actionable improvement suggestions

## 🔧 Customization

### Adding New Test Categories

1. Create directory: `tests/new_category/`
2. Add test files with `test_` prefix
3. Update `pytest.ini` markers if needed
4. Add to CI/CD workflow

### Custom Test Data

```python
# Add custom test data generators
class CustomTestDataGenerator:
    @staticmethod
    def generate_custom_signal():
        # Custom signal generation logic
        pass
```

### Custom Performance Thresholds

```python
# Update performance thresholds
PERFORMANCE_THRESHOLDS = {
    "max_response_time_ms": 1000,
    "min_success_rate": 0.95,
    "max_error_rate": 0.05
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors:** Ensure all dependencies are installed
2. **Database Connection:** Check DATABASE_URL configuration
3. **Authentication Failures:** Verify JWT_SECRET_KEY
4. **OANDA Integration:** Check OANDA API credentials

### Debug Commands

```bash
# Run tests with verbose output
pytest -v -s

# Run tests with coverage
pytest --cov=frontend --cov-report=term-missing

# Run specific test with debugging
pytest tests/api/test_health_endpoints.py::TestHealthEndpoints::test_basic_health_check -v -s
```

## 📝 Best Practices

### Test Writing Guidelines

1. **AAA Pattern:** Arrange, Act, Assert
2. **Descriptive Names:** Use clear, descriptive test names
3. **Isolation:** Tests should be independent
4. **Mocking:** Use mocks for external dependencies
5. **Edge Cases:** Test both happy and error paths

### Performance Testing

1. **Realistic Data:** Use realistic test data
2. **Baseline Metrics:** Establish performance baselines
3. **Thresholds:** Define acceptable performance thresholds
4. **Monitoring:** Continuously monitor performance trends

### Security Testing

1. **OWASP Guidelines:** Follow OWASP testing guidelines
2. **Common Vulnerabilities:** Test for common security issues
3. **Regular Scans:** Run regular security scans
4. **Dependency Updates:** Keep security dependencies updated

## 🎯 Next Steps

1. **Execute Setup:** Run `python setup_test_environment.py`
2. **Run Tests:** Execute `python testsprite_config.py`
3. **Review Results:** Analyze test reports and coverage
4. **Add Tests:** Implement additional tests as needed
5. **Integrate CI/CD:** Configure automated testing pipeline

This comprehensive TestSprite configuration provides a solid foundation for ensuring the reliability, security, and performance of your AI Trading System.
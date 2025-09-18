# Integration Tests Documentation

## Overview

This comprehensive integration test suite is designed to validate the FastAPI frontend application's functionality across multiple layers, ensuring that all components work together seamlessly. The tests complement the existing unit tests by focusing on interactions between services, database operations, external integrations, and end-to-end workflows.

## Test Structure

```
frontend/tests/integration/
├── conftest.py                 # Test configuration and fixtures
├── test_auth_integration.py    # Authentication and authorization
├── test_api_endpoints_integration.py  # API endpoint testing
├── test_database_operations_integration.py  # Database operations
├── test_external_services_integration.py    # External service integration
├── test_error_handling_integration.py       # Error handling and edge cases
├── test_performance_load_integration.py     # Performance and load testing
├── test_data_seeding.py                      # Test data generation
├── test_caching_async_integration.py         # Cache and async operations
├── test_end_to_end_workflows.py              # End-to-end workflows
└── README.md                                # This documentation
```

## Running the Tests

### Prerequisites

Ensure all dependencies are installed:

```bash
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

### Running All Integration Tests

```bash
cd progetto-funzionante-master/frontend
pytest tests/integration/ -v --cov=. --cov-report=html
```

### Running Specific Test Categories

```bash
# Run authentication tests
pytest tests/integration/test_auth_integration.py -v

# Run API endpoint tests
pytest tests/integration/test_api_endpoints_integration.py -v

# Run performance tests
pytest tests/integration/test_performance_load_integration.py -v

# Run end-to-end workflow tests
pytest tests/integration/test_end_to_end_workflows.py -v
```

### Running with Coverage Report

```bash
pytest tests/integration/ --cov=. --cov-report=html --cov-report=term-missing
```

## Key Fixtures and Utilities

### Database Fixtures

- `test_db_engine`: SQLite in-memory database engine
- `db_session`: Database session with automatic transaction rollback
- `test_database`: Creates test database tables and provides session

### Application Fixtures

- `test_app`: FastAPI application instance with test configuration
- `client`: TestClient for HTTP requests
- `auth_headers`: Authentication headers for authenticated requests

### Test Data Fixtures

- `test_user_data`: Sample user data for registration
- `test_user`: Created user instance
- `multiple_users_fixture`: Multiple user instances
- `test_signal_data`: Sample signal data
- `multiple_signals_fixture`: Multiple signal instances

### Mock Services

- `mock_cache_service`: Mocked cache service
- `mock_email_service`: Mocked email service
- `mock_oanda_service`: Mocked OANDA trading service

## Test Categories

### 1. Authentication and Authorization Tests

**File**: `test_auth_integration.py`

**Coverage**:
- User registration and email verification
- Login with JWT token generation
- Password hashing and validation
- Token refresh and validation
- Admin authorization
- Rate limiting
- Session management
- Account suspension and reactivation

**Key Tests**:
```python
def test_user_registration_flow(self, client: TestClient, db_session: Session):
    """Test complete user registration flow including email verification."""

def test_user_login_and_jwt_generation(self, client: TestClient, test_user: User):
    """Test user login with proper JWT token generation."""

def test_admin_authorization_checks(self, client: TestClient, admin_user: User):
    """Test admin access control for protected endpoints."""
```

### 2. API Endpoint Integration Tests

**File**: `test_api_endpoints_integration.py`

**Coverage**:
- Signals API (GET, POST, PUT, DELETE)
- Users API (CRUD operations)
- Admin endpoints
- Health check endpoints
- Pagination and filtering
- Data validation
- Error responses

**Key Tests**:
```python
def test_get_latest_signals(self, client: TestClient, multiple_signals_fixture: List[Signal]):
    """Test retrieving latest signals endpoint."""

def test_user_profile_management(self, client: TestClient, auth_headers: Dict[str, str]):
    """Test user profile CRUD operations."""

def test_admin_user_management(self, client: TestClient, admin_headers: Dict[str, str]):
    """Test admin user management endpoints."""
```

### 3. Database Operations Tests

**File**: `test_database_operations_integration.py`

**Coverage**:
- CRUD operations across multiple services
- Database relationships and constraints
- Concurrent database operations
- Cascade deletes
- Transaction rollback
- Database performance
- Backup and recovery simulation

**Key Tests**:
```python
def test_concurrent_database_operations(self, db_session: Session, test_user_data: Dict[str, Any]):
    """Test concurrent database operations."""

def test_database_relationships_and_constraints(self, db_session: Session):
    """Test database relationships and constraints enforcement."""

def test_transaction_rollback_handling(self, db_session: Session):
    """Test transaction rollback on errors."""
```

### 4. External Service Integration Tests

**File**: `test_external_services_integration.py`

**Coverage**:
- OANDA trading service
- Email service integration
- AI service integration
- HTTP client operations
- File service operations
- Service authentication
- Rate limiting
- Error handling and fallbacks

**Key Tests**:
```python
def test_oanda_service_initialization(self, db_session: Session):
    """Test OANDA service initialization and configuration."""

def test_email_service_integration(self, client: TestClient):
    """Test email service integration with SMTP."""

def test_external_service_error_handling(self, client: TestClient):
    """Test error handling for external service failures."""
```

### 5. Error Handling and Edge Cases

**File**: `test_error_handling_integration.py`

**Coverage**:
- Input validation errors
- HTTP error handling
- Database constraint violations
- Security vulnerabilities (SQL injection, XSS)
- Rate limiting
- Input sanitization
- Exception handling

**Key Tests**:
```python
def test_sql_injection_prevention(self, client: TestClient, auth_headers: Dict[str, str]):
    """Test prevention of SQL injection attacks."""

def test_input_validation_and_sanitization(self, client: TestClient):
    """Test input validation and sanitization."""

def test_rate_limiting_enforcement(self, client: TestClient):
    """Test rate limiting for API endpoints."""
```

### 6. Performance and Load Testing

**File**: `test_performance_load_integration.py`

**Coverage**:
- Concurrency testing
- Sustained load testing
- Burst load testing
- Memory usage analysis
- Database performance
- API response times
- Performance regression detection

**Key Tests**:
```python
def test_concurrent_api_requests(self, client: TestClient, performance_config: Dict[str, Any]):
    """Test concurrent API request handling."""

def test_sustained_load(self, client: TestClient, performance_config: Dict[str, Any]):
    """Test application performance under sustained load."""

def test_memory_usage_under_load(self, client: TestClient):
    """Test memory usage patterns under load."""
```

### 7. Test Data Seeding

**File**: `test_data_seeding.py`

**Coverage**:
- Factory pattern for test data
- Realistic user datasets
- Signal data generation
- Performance data creation
- Data relationship management
- Bulk data operations

**Key Features**:
```python
class TestDataSeeder:
    def create_realistic_user_dataset(self, count: int = 50) -> List[User]:
        """Create a realistic dataset of users with varying characteristics."""

    def create_signal_dataset(self, count: int = 100) -> List[Signal]:
        """Create a diverse set of trading signals."""

    def create_performance_data(self, user_count: int = 10, signal_count: int = 50):
        """Create performance metrics data."""
```

### 8. Caching and Async Operations

**File**: `test_caching_async_integration.py`

**Coverage**:
- Cache service operations
- Redis integration
- Async database queries
- Async HTTP clients
- Async file operations
- Concurrent async processing
- Performance benchmarks

**Key Tests**:
```python
def test_cache_basic_operations(self):
    """Test basic cache service operations."""

def test_async_database_operations(self, db_session: Session):
    """Test async database query performance."""

def test_concurrent_async_processing(self, client: TestClient):
    """Test concurrent async request processing."""
```

### 9. End-to-End Workflow Tests

**File**: `test_end_to_end_workflows.py`

**Coverage**:
- Complete user registration workflow
- Signal creation and management
- Trading signal execution
- Admin user management
- Signal analysis and decision making
- Account management
- Error recovery workflows
- Multi-user concurrent workflows

**Key Tests**:
```python
def test_complete_user_registration_workflow(self, client: TestClient):
    """Test complete user registration and onboarding workflow."""

def test_signal_creation_and_execution_workflow(self, client: TestClient, auth_headers: Dict[str, str]):
    """Test signal creation and execution workflow."""

def test_admin_management_workflow(self, client: TestClient, admin_headers: Dict[str, str]):
    """Test admin user management workflow."""
```

## Best Practices

### 1. Test Organization

- Use descriptive test names that explain the scenario
- Group related tests in logical classes
- Follow Arrange-Act-Assert pattern
- Use fixtures for reusable test setup

### 2. Data Management

- Use factory pattern for test data creation
- Clean up test data after each test
- Use realistic test data that mimics production scenarios
- Avoid hardcoding values in tests

### 3. Performance Testing

- Run performance tests in isolation
- Use appropriate load levels for your environment
- Monitor system resources during testing
- Establish performance baselines

### 4. Error Handling

- Test both happy paths and error scenarios
- Validate error messages and status codes
- Test recovery mechanisms
- Include edge cases and boundary conditions

### 5. Async Testing

- Use proper async test decorators
- Handle async fixture setup
- Test concurrent operations safely
- Consider race conditions

## Configuration

### Test Configuration

All test configuration is managed through `conftest.py`. Key configuration options:

```python
# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Performance test configuration
PERFORMANCE_CONFIG = {
    "concurrent_users": 10,
    "duration": 30,
    "requests_per_second": 5,
    "max_response_time": 2.0
}

# External service mocking
MOCK_EXTERNAL_SERVICES = True
```

### Environment Variables

Set these environment variables for external service testing:

```bash
# Database
TEST_DATABASE_URL=sqlite:///./test.db

# External Services
OANDA_API_KEY=your_test_key
OANDA_ACCOUNT_ID=your_test_account
SMTP_HOST=smtp.test.com
SMTP_PORT=587
SMTP_USERNAME=test@test.com
SMTP_PASSWORD=test_password

# Cache
REDIS_URL=redis://localhost:6379/0
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure test database URL is correct
   - Check database permissions
   - Verify database is not locked

2. **Authentication Failures**
   - Verify JWT secret configuration
   - Check user creation in test setup
   - Ensure proper token generation

3. **External Service Timeouts**
   - Increase timeout values in configuration
   - Check network connectivity
   - Verify service credentials

4. **Performance Test Failures**
   - Reduce load levels for testing environment
   - Check system resources
   - Verify test isolation

### Debug Mode

Run tests with debug output:

```bash
pytest tests/integration/ -v -s --tb=short
```

### Coverage Analysis

Generate detailed coverage reports:

```bash
pytest tests/integration/ --cov=. --cov-report=html --cov-report=term-missing
```

## Contributing

### Adding New Tests

1. Identify the appropriate test category
2. Follow the existing test structure
3. Use existing fixtures where possible
4. Add new fixtures if needed
5. Update documentation

### Test Maintenance

- Regularly update test data
- Review and update performance baselines
- Update documentation for new features
- Remove deprecated tests

## Performance Baselines

### API Response Times
- Simple endpoints: < 100ms
- Complex queries: < 500ms
- External service calls: < 2000ms

### Database Operations
- Single record operations: < 50ms
- Batch operations: < 1000ms
- Complex queries: < 2000ms

### Concurrency
- 10 concurrent users: < 2s response time
- 50 concurrent users: < 5s response time
- 100 concurrent users: < 10s response time

## Continuous Integration

The integration tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Integration Tests
  run: |
    cd frontend
    pytest tests/integration/ -v --cov=. --cov-report=xml
  env:
    TEST_DATABASE_URL: sqlite:///./test.db
    OANDA_API_KEY: ${{ secrets.OANDA_API_KEY }}
    OANDA_ACCOUNT_ID: ${{ secrets.OANDA_ACCOUNT_ID }}
```

## Reporting

### Test Reports
- HTML coverage reports: `htmlcov/index.html`
- XML coverage reports: `coverage.xml`
- Test results: `test-results.xml`

### Performance Reports
- Response time metrics
- Concurrency analysis
- Resource usage statistics
- Performance regression detection

## Test Data Management

Integration tests use:
- Factory Boy for test data generation
- Database transactions for isolation
- Cleanup procedures to maintain test database state
- Mock external services (OANDA, Email, AI services)

## Test Configuration Requirements

Integration tests require:
- Test database (SQLite for development, PostgreSQL for CI)
- Redis server (for caching tests)
- Mock external services (OANDA, Email, AI services)
- Proper environment configuration
- Network access for external service integration tests

## Conclusion

This comprehensive integration test suite ensures that the FastAPI frontend application is thoroughly tested across all layers of functionality. The tests provide confidence in the application's reliability, performance, and security while enabling rapid development and deployment cycles.

For questions or contributions, please refer to the main project documentation or contact the development team.
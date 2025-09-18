# Test Suite for FastAPI Frontend Application

This directory contains comprehensive tests for the FastAPI frontend trading signals application.

## Test Structure

```
tests/
├── conftest.py              # Shared pytest fixtures and configuration
├── unit/                    # Unit tests (isolated, fast)
│   ├── test_signal_service.py
│   ├── test_user_service.py
│   ├── test_signal_repository.py
│   ├── test_user_repository.py
│   └── test_pagination.py
├── integration/             # Integration tests (require services)
│   ├── test_api_endpoints.py
│   ├── test_auth_endpoints.py
│   └── README.md
├── factories/               # Test data factories
│   ├── user_factory.py
│   └── signal_factory.py
└── e2e/                     # End-to-end tests (future)
```

## Test Categories

### Unit Tests (tests/unit/)
- **Service Layer Tests**: Business logic testing
- **Repository Tests**: Data access layer testing
- **Utility Tests**: Helper function testing
- **Coverage**: ~80% minimum

### Integration Tests (tests/integration/)
- **API Endpoint Tests**: REST API functionality
- **Database Tests**: Real database operations
- **External Services**: Mocked external API integration

### Test Data Factories (tests/factories/)
- **UserFactory**: Realistic user test data
- **SignalFactory**: Trading signal test data
- **Configurable patterns**: Bulk data generation

## Running Tests

### Quick Start
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run unit tests only
pytest tests/unit/ -m unit

# Run with coverage
pytest --cov=app --cov-report=html
```

### Advanced Usage
```bash
# Run specific test file
pytest tests/unit/test_signal_service.py

# Run with verbose output
pytest -v

# Run with performance timing
pytest --durations=10

# Run parallel tests
pytest -n auto

# Run tests with markers
pytest -m "not slow"  # Skip slow tests
```

## Test Configuration

### pytest.ini
- Test discovery patterns
- Coverage configuration
- Custom markers
- Async test support
- Test timeout settings

### .coveragerc
- Coverage source paths
- Exclusion patterns
- Report configuration
- HTML output directory

## Test Data Management

### Fixtures (conftest.py)
- Database sessions
- Mock services
- Test users/signals
- Authentication headers

### Factories
- Realistic test data
- Configurable patterns
- Bulk generation
- Relationship handling

## Test Best Practices

### Unit Tests
- Fast execution (< 1 second per test)
- Isolated (no external dependencies)
- Deterministic (same results every run)
- Mock external services

### Integration Tests
- Test real interactions
- Use test databases
- Mock external APIs
- Clean up after each test

### Test Organization
- One test class per module
- Clear test names
- Arrange-Act-Assert pattern
- Proper test isolation

## Coverage Goals

- **Overall Coverage**: 80% minimum
- **Critical Paths**: 95%+ coverage
- **Services**: 90%+ coverage
- **Repositories**: 85%+ coverage
- **API Endpoints**: 80%+ coverage

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- Fast feedback (< 5 minutes)
- Parallel execution
- Coverage reporting
- Test result artifacts

## Test Reporting

### Coverage Reports
- HTML report: `htmlcov/index.html`
- XML report: `coverage.xml`
- Terminal summary

### Test Results
- JUnit XML format
- Performance metrics
- Failure diagnostics

## Adding New Tests

1. **Choose the right category** (unit/integration)
2. **Use existing fixtures** when possible
3. **Follow naming conventions**
4. **Add appropriate markers**
5. **Update coverage goals**

## Troubleshooting

### Common Issues
- **Import errors**: Check PYTHONPATH
- **Database issues**: Run migrations
- **Mock failures**: Verify mock setup
- **Timeout issues**: Increase timeout or optimize tests

### Debug Mode
```bash
# Run with debugger
pytest --pdb

# Stop on first failure
pytest -x

# Show local variables
pytest -l
```
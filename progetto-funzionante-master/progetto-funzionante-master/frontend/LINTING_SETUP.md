# Linting and Code Quality Setup

This document provides instructions for setting up and using the linting tools configured for this FastAPI project.

## 🛠️ Configured Tools

### 1. Black - Code Formatter
- **Purpose**: Opinionated code formatter for consistent code style
- **Configuration**: Line length 88 characters, Python 3.9+ support
- **Usage**:
  ```bash
  black .
  black --check --diff .  # Check without modifying
  ```

### 2. flake8 - Linter
- **Purpose**: Style guide enforcement, error detection, complexity analysis
- **Configuration**:
  - Max line length: 88 (matches Black)
  - Max complexity: 10
  - Ignores: E203, E501, W503 (handled by Black)
- **Usage**:
  ```bash
  flake8 .
  ```

### 3. isort - Import Sorter
- **Purpose**: Sorts and organizes Python imports
- **Configuration**: Black-compatible profile
- **Usage**:
  ```bash
  isort .
  isort --check-only --diff .  # Check without modifying
  ```

### 4. mypy - Type Checker
- **Purpose**: Static type checking for Python
- **Configuration**: Strict mode with selective ignore for external libraries
- **Usage**:
  ```bash
  mypy .
  ```

### 5. pytest - Test Framework
- **Purpose**: Running tests with coverage reporting
- **Configuration**: Async support, coverage reports, markers
- **Usage**:
  ```bash
  pytest
  pytest --cov=. --cov-report=html
  ```

## 📦 Installation

### Option 1: Using the Setup Script (Recommended)
```bash
# Run the automated setup script
python scripts/setup_linting.py
```

### Option 2: Manual Installation
```bash
# Install development dependencies
pip install -e ".[dev]"

# Or install individually
pip install black>=23.0.0
pip install flake8>=6.0.0
pip install isort>=5.12.0
pip install mypy>=1.0.0
pip install pytest>=7.0.0
pip install pytest-asyncio>=0.21.0
pip install pytest-cov>=4.0.0
pip install pre-commit>=3.0.0

# Setup pre-commit hooks
pre-commit install
```

## 🎯 Usage

### Using Make Commands (Easiest)
```bash
# Format code
make format

# Check for linting issues
make lint

# Fix auto-fixable issues
make lint-fix

# Run tests
make test

# Run tests with coverage
make test-cov

# Full setup
make setup

# Run all checks
make check-all
```

### Using Direct Commands
```bash
# Format code
black .
isort .

# Check formatting
black --check --diff .
isort --check-only --diff .

# Run linters
flake8 .
mypy .

# Run tests
pytest
pytest --cov=. --cov-report=html --cov-report=term-missing
```

## 🪝 Pre-commit Hooks

Pre-commit hooks are configured to run automatically before each commit:

```bash
# Setup pre-commit hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black
pre-commit run flake8
```

### Hooks Configuration (.pre-commit-config.yaml)
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Style and error checking
- **mypy**: Type checking
- **Standard hooks**: Trailing whitespace, end-of-file fixes, etc.

## ⚙️ Configuration Files

### pyproject.toml
Main configuration file with settings for:
- Black: `[tool.black]`
- isort: `[tool.isort]`
- flake8: `[tool.flake8]`
- mypy: `[tool.mypy]`
- pytest: `[tool.pytest.ini_options]`
- Coverage: `[tool.coverage.*]`

### .flake8
Additional flake8-specific configuration:
- Per-file ignore patterns
- Plugin configurations
- Complexity settings

### .gitignore
Comprehensive ignore patterns for Python projects including:
- Cache files (`__pycache__/`)
- Virtual environments (`venv/`, `.venv/`)
- Build artifacts (`build/`, `dist/`)
- IDE files (`.vscode/`, `.idea/`)
- Test and coverage reports (`.pytest_cache/`, `.coverage`)

## 🔄 Integration with Development Workflow

### 1. Before Committing
```bash
# Check and fix formatting
make format

# Run all checks
make check-all

# Commit changes (pre-commit hooks will run automatically)
git commit -m "Your commit message"
```

### 2. Continuous Integration
The linting configuration is designed to work well with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.9'

- name: Install dependencies
  run: |
    pip install -e ".[dev]"

- name: Run linting
  run: |
    make lint

- name: Run tests
  run: |
    make test-cov
```

### 3. IDE Integration

#### VS Code
Install these extensions:
- Python (Microsoft)
- Black Formatter
- isort
- flake8

Add to your `.vscode/settings.json`:
```json
{
    "python.formatting.provider": "black",
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### PyCharm
- Install Black and isort plugins
- Configure in Settings > Tools > External Tools

## 🐛 Troubleshooting

### Common Issues

1. **Import conflicts with isort**
   ```bash
   isort --profile black .
   ```

2. **Line length conflicts between Black and flake8**
   - Both are configured to 88 characters
   - Ensure your editor doesn't have different settings

3. **Type checking errors with mypy**
   ```bash
   # Install missing type stubs
   pip install types-requests
   pip install types-redis
   ```

4. **Pre-commit hooks failing**
   ```bash
   # Reinstall hooks
   pre-commit uninstall
   pre-commit install

   # Run manually to see errors
   pre-commit run --all-files
   ```

### Performance Tips

1. **Exclude directories** from linting when possible:
   - Virtual environments
   - `node_modules/`
   - Build directories

2. **Use incremental tools**:
   ```bash
   # Only check changed files
   git diff --name-only HEAD~1 | grep '\.py$' | xargs black --check
   ```

3. **Parallel processing**:
   ```bash
   # Use multiple cores for larger projects
   black --workers 4 .
   ```

## 📚 Best Practices

1. **Commit configuration files** along with your code
2. **Use consistent formatting** across the entire codebase
3. **Fix linting issues** before committing
4. **Write type hints** for better code documentation and catching errors
5. **Run tests locally** before pushing to ensure everything works

## 🔧 Customization

To modify the configuration:

1. **Edit pyproject.toml** for tool-specific settings
2. **Update .flake8** for flake8-specific rules
3. **Modify .pre-commit-config.yaml** for hook changes
4. **Update the Makefile** for custom commands

## 📝 Documentation Updates

When making changes to the linting configuration:
1. Update this document with any new tools or changed settings
2. Document any new ignore rules or exceptions
3. Update team members about significant changes

---

This setup ensures consistent code quality and style across the entire FastAPI project while maintaining good developer experience and integration with modern development tools.
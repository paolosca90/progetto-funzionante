# Pre-commit Hooks Configuration

This document describes the pre-commit hooks configuration for the AI Trading System project.

## Overview

Pre-commit hooks are automated checks that run before each commit to ensure code quality, consistency, and security. They help catch issues early and maintain a high standard of code quality across the project.

## Configuration Files

### Main Configuration
- **`.pre-commit-config.yaml`**: Main pre-commit configuration file defining all hooks
- **`.secrets.baseline`**: Baseline file for secret detection (created after setup)
- **`setup-pre-commit.sh`**: Unix/Linux/macOS setup script
- **`setup-pre-commit.bat`**: Windows setup script
- **`run-pre-commit.sh`**: Helper script for manual hook execution

### Existing Tool Configurations
- **`.flake8`**: Flake8 linting configuration
- **`pyproject.toml`**: Black, isort, mypy, and pytest configurations

## Installed Hooks

### Code Quality & Formatting
1. **Black** - Code formatting
   - Ensures consistent code style
   - Line length: 88 characters
   - Target Python: 3.13

2. **isort** - Import sorting
   - Organizes and standardizes imports
   - Compatible with Black formatting
   - Line length: 88 characters

3. **flake8** - Linting
   - Checks for code errors and style issues
   - Includes plugins for docstrings, imports, bug detection
   - Ignores formatting issues handled by Black

4. **mypy** - Type checking
   - Static type analysis
   - Helps catch type-related bugs
   - Configured for Python 3.13

### Security & Secrets
5. **detect-secrets** - Secret detection
   - Scans for potential secrets, API keys, passwords
   - Uses baseline file to ignore known safe strings

6. **bandit** - Security linting
   - Finds common security issues in Python code
   - Skips assert statements (B101) and shell warnings (B601)

7. **detect-private-key** - Private key detection
   - Detects private keys in committed files

### File Consistency
8. **trailing-whitespace** - Removes trailing whitespace
9. **end-of-file-fixer** - Ensures files end with newline
10. **mixed-line-ending** - Standardizes line endings
11. **check-yaml** - Validates YAML syntax
12. **check-json** - Validates JSON syntax
13. **check-toml** - Validates TOML syntax
14. **yamllint** - YAML linting with relaxed rules

### Code Quality Enhancement
15. **pyupgrade** - Python syntax upgrade
   - Upgrades Python syntax to modern versions
   - Target: Python 3.13+

16. **interrogate** - Documentation coverage
   - Checks for missing docstrings
   - Ignores magic methods, properties, private methods

### File Management
17. **check-added-large-files** - Prevents large file commits
   - Maximum file size: 1MB

18. **check-case-conflict** - Detects case sensitivity conflicts
19. **check-merge-conflict** - Detects merge conflict markers
20. **check-executables-have-shebangs** - Ensures executables have shebangs
21. **check-shebang-scripts-are-executable** - Ensures scripts with shebangs are executable

### Branch Protection
22. **no-commit-to-branch** - Prevents direct commits to main/master/develop

### Dependencies & Security
23. **python-safety-dependencies-check** - Checks for vulnerable dependencies
   - Scans requirements.txt and pyproject.toml

## Installation

### Automatic Installation (Recommended)

#### Windows
```bash
# Run the Windows setup script
setup-pre-commit.bat
```

#### Unix/Linux/macOS
```bash
# Make the script executable and run it
chmod +x setup-pre-commit.sh
./setup-pre-commit.sh
```

### Manual Installation

1. **Install pre-commit**
   ```bash
   pip install pre-commit
   ```

2. **Install hooks**
   ```bash
   pre-commit install
   ```

3. **Install additional hook types**
   ```bash
   pre-commit install --hook-type commit-msg
   pre-commit install --hook-type pre-push
   pre-commit install --hook-type pre-merge-commit
   pre-commit install --hook-type prepare-commit-msg
   ```

4. **Create secrets baseline**
   ```bash
   detect-secrets scan > .secrets.baseline
   ```

## Usage

### Automatic Execution
Hooks run automatically on:
- `git commit` - Most hooks run before commit
- `git push` - Some hooks run before push
- Manual execution with `pre-commit run`

### Manual Execution

#### Run all hooks
```bash
pre-commit run --all-files
```

#### Run specific hooks
```bash
pre-commit run black --all-files
pre-commit run flake8 --all-files
pre-commit run mypy --all-files
```

#### Using the helper script
```bash
chmod +x run-pre-commit.sh
./run-pre-commit.sh
```

### Skip Hooks (Not Recommended)
```bash
# Skip all hooks for a commit
git commit -n -m "Commit message"

# Skip specific hooks
SKIP=black,flake8 git commit -m "Commit message"
```

## Hook Stages

- **commit**: Runs before commit is created (most hooks)
- **push**: Runs before push to remote (security tests)
- **manual**: Only runs when manually executed
- **commit-message**: Validates commit messages

## Configuration Details

### File Exclusions
The following files and directories are excluded from all hooks:
- `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd` - Python cache files
- `.git/`, `.gitignore` - Git files
- `.mypy_cache/`, `.pytest_cache/` - Tool cache files
- `.venv/`, `venv/`, `env/` - Virtual environments
- `node_modules/`, `build/`, `dist/` - Build artifacts
- `*.egg-info/` - Python package info
- `.env*`, `*.key`, `*.pem`, `*.p12` - Sensitive files
- `backend/`, `*_vps.py`, `*_secret*` - Backend and secret files
- `*.db`, `*.sqlite3?` - Database files
- `.railway/`, `VPS_INSTALLAZIONE/` - Deployment files

### Hook Configuration
- **Default language**: Python 3.13
- **Line length**: 88 characters (Black standard)
- **Fail fast**: Disabled (runs all hooks even if one fails)
- **Minimum pre-commit version**: 3.0.0

## Troubleshooting

### Common Issues

1. **"No such file or directory" errors**
   - Ensure you're in the correct directory (frontend/)
   - Run setup scripts from the project root

2. **"Module not found" errors**
   - Install missing dependencies: `pip install -r requirements.txt`
   - Run `pre-commit clean` to clear cache

3. **"InvalidConfigError"**
   - Check YAML syntax in `.pre-commit-config.yaml`
   - Ensure all quotes and colons are properly escaped

4. **Python version issues**
   - Ensure Python 3.13 is available
   - Update `default_language_version` in config if needed

### Maintenance

#### Update hooks to latest versions
```bash
pre-commit autoupdate
```

#### Clean cache
```bash
pre-commit clean
```

#### Uninstall hooks
```bash
pre-commit uninstall
```

#### Reinstall hooks
```bash
pre-commit uninstall
pre-commit install
```

### Adding New Hooks

1. Add the hook to `.pre-commit-config.yaml`
2. Test with `pre-commit run <hook-id> --all-files`
3. Commit the configuration change

### Custom Hooks

For project-specific hooks, add them under the `local` repo section:

```yaml
- repo: local
  hooks:
    - id: custom-hook
      name: Custom Hook
      entry: python custom_script.py
      language: system
      files: \.py$
      stages: [commit, push]
```

## Best Practices

1. **Run hooks manually** before pushing to avoid surprises
2. **Fix issues automatically** when hooks modify files
3. **Stage changes** and commit again after hook modifications
4. **Keep hooks updated** with `pre-commit autoupdate`
5. **Use helper scripts** for consistent execution
6. **Review hook output** to understand code quality issues
7. **Configure CI/CD** to run the same hooks

## Integration with CI/CD

The same hooks can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run pre-commit
  uses: pre-commit/action@v3.0.0
```

## Performance Considerations

- Hooks run in parallel when possible
- Some hooks cache results for faster execution
- First run may be slow due to environment setup
- Subsequent runs are much faster
- Use `--files` parameter to run on specific files only

## Security Notes

- Secret detection baseline should be committed to the repository
- Review `.secrets.baseline` before committing
- Never commit actual secrets or API keys
- Security hooks run on push to prevent exposure

## Contributing

When contributing to this project:
1. Ensure all hooks pass before submitting pull requests
2. Keep hook configurations up to date
3. Test new hooks before adding them to the configuration
4. Document any changes to the pre-commit setup

## Support

For issues with pre-commit hooks:
1. Check the [pre-commit documentation](https://pre-commit.com/)
2. Review hook-specific documentation
3. Check the troubleshooting section above
4. Create an issue in the project repository
#!/usr/bin/env python3
"""
Setup script for linting tools configuration
This script helps set up and validate the linting configuration
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*50}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        return True, result
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}:")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        return False, e


def check_python_version():
    """Check if Python version is compatible"""
    print(f"\nPython version: {sys.version}")
    if sys.version_info < (3, 9):
        print("⚠️  Warning: Python 3.9+ recommended for best compatibility")
        return False
    return True


def install_dev_dependencies():
    """Install development dependencies"""
    print("\n📦 Installing development dependencies...")

    # Install pip if not available
    try:
        import pip
    except ImportError:
        print("Installing pip...")
        success, _ = run_command([sys.executable, "-m", "ensurepip", "--upgrade"], "Install pip")
        if not success:
            return False

    # Install development dependencies
    deps = [
        "black>=23.0.0",
        "flake8>=6.0.0",
        "isort>=5.12.0",
        "mypy>=1.0.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.0.0",
        "httpx>=0.24.0",
        "pre-commit>=3.0.0",
    ]

    for dep in deps:
        success, _ = run_command([sys.executable, "-m", "pip", "install", dep], f"Install {dep}")
        if not success:
            print(f"⚠️  Failed to install {dep}")

    return True


def validate_configuration():
    """Validate the linting configuration"""
    print("\n🔍 Validating configuration...")

    # Check if configuration files exist
    config_files = [
        "pyproject.toml",
        ".flake8",
        ".gitignore",
    ]

    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file} exists")
        else:
            print(f"❌ {config_file} missing")

    return True


def test_linting_tools():
    """Test that linting tools work with the configuration"""
    print("\n🧪 Testing linting tools...")

    # Test Black
    print("\nTesting Black...")
    success, result = run_command(
        [sys.executable, "-m", "black", "--check", "--diff", "main.py"],
        "Black check main.py"
    )
    if success:
        print("✅ Black configuration working")
    else:
        print("⚠️  Black found issues (this is expected if code isn't formatted)")

    # Test flake8
    print("\nTesting flake8...")
    success, result = run_command(
        [sys.executable, "-m", "flake8", "main.py"],
        "flake8 check main.py"
    )
    if success:
        print("✅ flake8 configuration working")
    else:
        print("⚠️  flake8 found issues (this is expected)")

    # Test isort
    print("\nTesting isort...")
    success, result = run_command(
        [sys.executable, "-m", "isort", "--check-only", "--diff", "main.py"],
        "isort check main.py"
    )
    if success:
        print("✅ isort configuration working")
    else:
        print("⚠️  isort found issues (this is expected)")

    return True


def setup_pre_commit():
    """Setup pre-commit hooks"""
    print("\n🪝 Setting up pre-commit hooks...")

    # Install pre-commit
    success, _ = run_command([sys.executable, "-m", "pip", "install", "pre-commit"], "Install pre-commit")
    if not success:
        return False

    # Create .pre-commit-config.yaml
    pre_commit_config = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-redis]
        args: [--ignore-missing-imports]
"""

    with open(".pre-commit-config.yaml", "w") as f:
        f.write(pre_commit_config)

    print("✅ .pre-commit-config.yaml created")

    # Install pre-commit hooks
    success, _ = run_command([sys.executable, "-m", "pre-commit", "install"], "Install pre-commit hooks")
    if success:
        print("✅ Pre-commit hooks installed")
    else:
        print("⚠️  Pre-commit hooks installation failed")

    return True


def create_makefile():
    """Create a Makefile for easy linting commands"""
    print("\n📝 Creating Makefile for linting commands...")

    makefile_content = """# Makefile for linting and formatting

.PHONY: help install-dev format lint lint-fix test test-cov pre-commit-setup clean

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\\033[36m%-20s\\033[0m %s\\n", $$1, $$2}'

install-dev:  ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

format:  ## Format code with black and isort
	black .
	isort .

lint:  ## Run linting tools (flake8, mypy, black check, isort check)
	flake8 .
	mypy .
	black --check --diff .
	isort --check-only --diff .

lint-fix:  ## Fix linting issues (format code)
	black .
	isort .

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=. --cov-report=html --cov-report=term-missing

pre-commit-setup:  ## Setup pre-commit hooks
	pre-commit install
	pre-commit run --all-files

clean:  ## Clean up cache and build files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

check-all: lint test  ## Run all checks (linting and tests)

setup: install-dev pre-commit-setup  ## Full setup of development environment
"""

    with open("Makefile", "w") as f:
        f.write(makefile_content)

    print("✅ Makefile created")


def main():
    """Main setup function"""
    print("🚀 Setting up linting tools for AI Trading System")
    print("=" * 60)

    # Change to the script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)  # Go to project root

    # Check Python version
    if not check_python_version():
        print("❌ Python version check failed")
        return 1

    # Install dependencies
    if not install_dev_dependencies():
        print("❌ Failed to install development dependencies")
        return 1

    # Validate configuration
    if not validate_configuration():
        print("❌ Configuration validation failed")
        return 1

    # Test linting tools
    if not test_linting_tools():
        print("❌ Linting tools test failed")
        return 1

    # Setup pre-commit
    if not setup_pre_commit():
        print("⚠️  Pre-commit setup failed (optional)")

    # Create Makefile
    create_makefile()

    print("\n" + "=" * 60)
    print("✅ Linting tools setup completed successfully!")
    print("\nNext steps:")
    print("1. Run 'make format' to format your code")
    print("2. Run 'make lint' to check for issues")
    print("3. Run 'make lint-fix' to fix auto-fixable issues")
    print("4. Run 'make test' to run tests")
    print("5. Commit your changes - pre-commit hooks will run automatically")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
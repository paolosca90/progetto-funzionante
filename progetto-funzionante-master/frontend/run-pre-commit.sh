#!/bin/bash

# Helper script to run pre-commit hooks manually

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    print_error "Pre-commit is not installed. Please run setup-pre-commit.sh first."
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f ".pre-commit-config.yaml" ]; then
    print_error ".pre-commit-config.yaml not found. Please run this script from the frontend directory."
    exit 1
fi

# Menu for hook selection
echo "Select pre-commit hook to run:"
echo "1) Run all hooks"
echo "2) Run formatting hooks (black, isort)"
echo "3) Run linting hooks (flake8, mypy)"
echo "4) Run security hooks (bandit, detect-secrets)"
echo "5) Run file consistency hooks (yaml, json, toml)"
echo "6) Run tests (pytest)"
echo "7) Update hooks to latest versions"
echo "8) Clean pre-commit cache"
echo "9) Exit"

read -p "Enter your choice (1-9): " choice

case $choice in
    1)
        print_status "Running all hooks..."
        pre-commit run --all-files
        ;;
    2)
        print_status "Running formatting hooks..."
        pre-commit run black isort --all-files
        ;;
    3)
        print_status "Running linting hooks..."
        pre-commit run flake8 mypy --all-files
        ;;
    4)
        print_status "Running security hooks..."
        pre-commit run bandit detect-secrets --all-files
        ;;
    5)
        print_status "Running file consistency hooks..."
        pre-commit run check-yaml check-json check-toml yamllint --all-files
        ;;
    6)
        print_status "Running tests..."
        if command -v pytest &> /dev/null; then
            pytest tests/ --tb=short
        else
            print_warning "pytest not found. Install with: pip install pytest"
        fi
        ;;
    7)
        print_status "Updating hooks to latest versions..."
        pre-commit autoupdate
        print_success "Hooks updated successfully."
        ;;
    8)
        print_status "Cleaning pre-commit cache..."
        pre-commit clean
        print_success "Cache cleaned successfully."
        ;;
    9)
        print_status "Exiting..."
        exit 0
        ;;
    *)
        print_error "Invalid choice. Please select a number between 1 and 9."
        exit 1
        ;;
esac

print_success "Pre-commit operation completed successfully."
#!/bin/bash

# Pre-commit Setup Script
# This script installs and configures pre-commit hooks for the project

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if we're in the correct directory
if [ ! -f ".pre-commit-config.yaml" ]; then
    print_error ".pre-commit-config.yaml not found. Please run this script from the frontend directory."
    exit 1
fi

print_status "Setting up pre-commit hooks..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is required but not installed."
    exit 1
fi

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    print_status "Installing pre-commit..."
    pip3 install pre-commit
    print_success "Pre-commit installed successfully."
else
    print_status "Pre-commit is already installed."
fi

# Install pre-commit hooks
print_status "Installing pre-commit hooks..."
pre-commit install
print_success "Pre-commit hooks installed."

# Optionally install pre-commit hooks for all git hooks
print_status "Installing pre-commit hooks for all git hooks..."
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push
pre-commit install --hook-type pre-merge-commit
pre-commit install --hook-type prepare-commit-msg
print_success "All pre-commit hooks installed."

# Create secrets baseline for detect-secrets
if [ ! -f ".secrets.baseline" ]; then
    print_status "Creating secrets baseline..."
    detect-secrets scan > .secrets.baseline
    print_success "Secrets baseline created."
else
    print_status "Secrets baseline already exists."
fi

# Update pre-commit hooks to latest versions
print_status "Updating pre-commit hooks to latest versions..."
pre-commit autoupdate
print_success "Pre-commit hooks updated."

# Run all hooks on existing files (optional)
read -p "Do you want to run all hooks on existing files? This may modify your code. (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Running all hooks on existing files..."
    pre-commit run --all-files
    print_success "All hooks executed on existing files."
fi

# Create a helper script for manual pre-commit runs
cat > run-pre-commit.sh << 'EOF'
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
        pre-commit run pytest-check --all-files
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
EOF

# Make the helper script executable
chmod +x run-pre-commit.sh

print_success "Helper script created: run-pre-commit.sh"

# Display usage instructions
print_success "Pre-commit setup completed successfully!"
echo ""
print_status "Usage:"
echo "  - Pre-commit hooks will run automatically on each commit"
echo "  - Run 'pre-commit run --all-files' to manually check all files"
echo "  - Run './run-pre-commit.sh' for a menu-driven hook runner"
echo "  - Run 'pre-commit autoupdate' to update hooks to latest versions"
echo "  - Run 'pre-commit clean' to clean the cache"
echo ""
print_warning "Important:"
echo "  - If hooks modify your files, you'll need to stage the changes and commit again"
echo "  - Some hooks may require additional dependencies to be installed"
echo "  - You can skip hooks temporarily with 'git commit -n' (not recommended)"
echo ""
print_status "Configuration files:"
echo "  - .pre-commit-config.yaml: Main pre-commit configuration"
echo "  - .secrets.baseline: Baseline for secret detection"
echo "  - .flake8: Flake8 linting configuration"
echo "  - pyproject.toml: Tool configurations (black, isort, mypy, etc.)"
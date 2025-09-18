@echo off
setlocal enabledelayedexpansion

REM Pre-commit Setup Script for Windows
REM This script installs and configures pre-commit hooks for the project

echo [INFO] Setting up pre-commit hooks...

REM Check if we're in the correct directory
if not exist ".pre-commit-config.yaml" (
    echo [ERROR] .pre-commit-config.yaml not found. Please run this script from the frontend directory.
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is required but not installed.
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is required but not installed.
    exit /b 1
)

REM Install pre-commit if not already installed
pre-commit --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing pre-commit...
    pip install pre-commit
    if errorlevel 1 (
        echo [ERROR] Failed to install pre-commit.
        exit /b 1
    )
    echo [SUCCESS] Pre-commit installed successfully.
) else (
    echo [INFO] Pre-commit is already installed.
)

REM Install pre-commit hooks
echo [INFO] Installing pre-commit hooks...
pre-commit install
if errorlevel 1 (
    echo [ERROR] Failed to install pre-commit hooks.
    exit /b 1
)
echo [SUCCESS] Pre-commit hooks installed.

REM Install pre-commit hooks for all git hooks
echo [INFO] Installing pre-commit hooks for all git hooks...
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push
pre-commit install --hook-type pre-merge-commit
pre-commit install --hook-type prepare-commit-msg
echo [SUCCESS] All pre-commit hooks installed.

REM Create secrets baseline for detect-secrets
if not exist ".secrets.baseline" (
    echo [INFO] Creating secrets baseline...
    detect-secrets scan > .secrets.baseline
    echo [SUCCESS] Secrets baseline created.
) else (
    echo [INFO] Secrets baseline already exists.
)

REM Update pre-commit hooks to latest versions
echo [INFO] Updating pre-commit hooks to latest versions...
pre-commit autoupdate
echo [SUCCESS] Pre-commit hooks updated.

REM Ask if user wants to run hooks on existing files
set /p "run_hooks=Do you want to run all hooks on existing files? This may modify your code. (y/N): "
if /i "!run_hooks!"=="y" (
    echo [INFO] Running all hooks on existing files...
    pre-commit run --all-files
    echo [SUCCESS] All hooks executed on existing files.
)

echo [SUCCESS] Pre-commit setup completed successfully!
echo.
echo [INFO] Usage:
echo   - Pre-commit hooks will run automatically on each commit
echo   - Run 'pre-commit run --all-files' to manually check all files
echo   - Run 'pre-commit autoupdate' to update hooks to latest versions
echo   - Run 'pre-commit clean' to clean the cache
echo.
echo [WARNING] Important:
echo   - If hooks modify your files, you'll need to stage the changes and commit again
echo   - Some hooks may require additional dependencies to be installed
echo   - You can skip hooks temporarily with 'git commit -n' (not recommended)
echo.
echo [INFO] Configuration files:
echo   - .pre-commit-config.yaml: Main pre-commit configuration
echo   - .secrets.baseline: Baseline for secret detection
echo   - .flake8: Flake8 linting configuration
echo   - pyproject.toml: Tool configurations (black, isort, mypy, etc.)

pause
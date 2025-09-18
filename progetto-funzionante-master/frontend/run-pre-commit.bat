@echo off
setlocal enabledelayedexpansion

REM Helper script to run pre-commit hooks manually

REM Check if pre-commit is installed
pre-commit --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Pre-commit is not installed. Please run setup-pre-commit.bat first.
    exit /b 1
)

REM Check if we're in the correct directory
if not exist ".pre-commit-config.yaml" (
    echo [ERROR] .pre-commit-config.yaml not found. Please run this script from the frontend directory.
    exit /b 1
)

:menu
echo Select pre-commit hook to run:
echo 1) Run all hooks
echo 2) Run formatting hooks (black, isort)
echo 3) Run linting hooks (flake8, mypy)
echo 4) Run security hooks (bandit, detect-secrets)
echo 5) Run file consistency hooks (yaml, json, toml)
echo 6) Update hooks to latest versions
echo 7) Clean pre-commit cache
echo 8) Exit

set /p "choice=Enter your choice (1-8): "

if "%choice%"=="1" (
    echo [INFO] Running all hooks...
    pre-commit run --all-files
) else if "%choice%"=="2" (
    echo [INFO] Running formatting hooks...
    pre-commit run black isort --all-files
) else if "%choice%"=="3" (
    echo [INFO] Running linting hooks...
    pre-commit run flake8 mypy --all-files
) else if "%choice%"=="4" (
    echo [INFO] Running security hooks...
    pre-commit run bandit detect-secrets --all-files
) else if "%choice%"=="5" (
    echo [INFO] Running file consistency hooks...
    pre-commit run check-yaml check-json check-toml yamllint --all-files
) else if "%choice%"=="6" (
    echo [INFO] Updating hooks to latest versions...
    pre-commit autoupdate
    echo [SUCCESS] Hooks updated successfully.
) else if "%choice%"=="7" (
    echo [INFO] Cleaning pre-commit cache...
    pre-commit clean
    echo [SUCCESS] Cache cleaned successfully.
) else if "%choice%"=="8" (
    echo [INFO] Exiting...
    exit /b 0
) else (
    echo [ERROR] Invalid choice. Please select a number between 1 and 8.
    goto menu
)

echo [SUCCESS] Pre-commit operation completed successfully.
pause
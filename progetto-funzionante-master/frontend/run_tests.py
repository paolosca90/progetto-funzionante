#!/usr/bin/env python3
"""
Test runner script for the FastAPI frontend application.
Provides convenient ways to run different types of tests.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and display results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        return False


def run_unit_tests():
    """Run unit tests only."""
    return run_command(
        ["pytest", "tests/unit/", "-m", "unit", "-v"],
        "Unit Tests"
    )


def run_integration_tests():
    """Run integration tests only."""
    return run_command(
        ["pytest", "tests/integration/", "-m", "integration", "-v"],
        "Integration Tests"
    )


def run_all_tests():
    """Run all tests."""
    return run_command(
        ["pytest", "-v", "--tb=short"],
        "All Tests"
    )


def run_tests_with_coverage():
    """Run tests with coverage report."""
    success = run_command(
        ["pytest", "--cov=app", "--cov-report=html", "--cov-report=term-missing", "--cov-report=xml"],
        "Tests with Coverage"
    )

    if success:
        print(f"\n📊 Coverage report generated:")
        print(f"   HTML: {Path('htmlcov/index.html').resolve()}")
        print(f"   XML: {Path('coverage.xml').resolve()}")

    return success


def run_parallel_tests():
    """Run tests in parallel for faster execution."""
    return run_command(
        ["pytest", "-n", "auto", "--dist=worksteal"],
        "Parallel Tests"
    )


def run_slow_tests():
    """Run only slow tests."""
    return run_command(
        ["pytest", "-m", "slow", "-v", "--durations=0"],
        "Slow Tests"
    )


def run_api_tests():
    """Run API endpoint tests."""
    return run_command(
        ["pytest", "-m", "api", "-v"],
        "API Tests"
    )


def run_database_tests():
    """Run database-related tests."""
    return run_command(
        ["pytest", "-m", "database", "-v"],
        "Database Tests"
    )


def run_linting():
    """Run code linting and formatting checks."""
    commands = [
        (["flake8", "app", "tests"], "Flake8 Linting"),
        (["black", "--check", "app", "tests"], "Black Formatting Check"),
        (["isort", "--check-only", "app", "tests"], "Import Sorting Check"),
    ]

    all_passed = True
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            all_passed = False

    return all_passed


def run_type_checking():
    """Run static type checking."""
    return run_command(
        ["mypy", "app"],
        "Type Checking (MyPy)"
    )


def setup_test_environment():
    """Set up the test environment."""
    print("🔧 Setting up test environment...")

    # Install test dependencies
    if not run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"],
        "Install test dependencies"
    ):
        return False

    # Create test database if needed
    print("📊 Test environment setup complete!")
    return True


def cleanup_test_artifacts():
    """Clean up test artifacts."""
    print("🧹 Cleaning up test artifacts...")

    artifacts = [
        "htmlcov",
        "coverage.xml",
        ".pytest_cache",
        ".coverage",
        "__pycache__",
        "*.pyc",
        "app/__pycache__",
        "tests/__pycache__"
    ]

    for artifact in artifacts:
        path = Path(artifact)
        if path.exists():
            if path.is_dir():
                subprocess.run(["rm", "-rf", str(path)], check=False)
            else:
                path.unlink()

    print("✅ Cleanup complete!")


def generate_test_report():
    """Generate a comprehensive test report."""
    print("📋 Generating test report...")

    report_file = Path("test_report.md")
    with open(report_file, "w") as f:
        f.write("# Test Report\n\n")
        f.write(f"Generated: {subprocess.run(['date'], capture_output=True, text=True).stdout}\n\n")

        # Add coverage summary if available
        if Path("coverage.xml").exists():
            f.write("## Coverage Summary\n\n")
            f.write("See `coverage.xml` for detailed coverage information.\n\n")

        # Add test results summary
        f.write("## Test Results\n\n")
        f.write("- Unit Tests: Run with `python run_tests.py unit`\n")
        f.write("- Integration Tests: Run with `python run_tests.py integration`\n")
        f.write("- Full Test Suite: Run with `python run_tests.py all`\n")
        f.write("- Coverage Report: Run with `python run_tests.py coverage`\n")

    print(f"📄 Test report generated: {report_file.resolve()}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test runner for FastAPI frontend application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py unit               # Run unit tests only
  python run_tests.py integration        # Run integration tests
  python run_tests.py coverage           # Run tests with coverage
  python run_tests.py parallel           # Run tests in parallel
  python run_tests.py setup              # Set up test environment
  python run_tests.py lint               # Run linting checks
  python run_tests.py clean              # Clean up artifacts
        """
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=[
            "all", "unit", "integration", "coverage", "parallel",
            "slow", "api", "database", "lint", "type-check",
            "setup", "clean", "report"
        ],
        help="Test command to run"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Change to the directory containing this script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Map commands to functions
    command_map = {
        "all": run_all_tests,
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "coverage": run_tests_with_coverage,
        "parallel": run_parallel_tests,
        "slow": run_slow_tests,
        "api": run_api_tests,
        "database": run_database_tests,
        "lint": run_linting,
        "type-check": run_type_checking,
        "setup": setup_test_environment,
        "clean": cleanup_test_artifacts,
        "report": generate_test_report,
    }

    # Execute the requested command
    success = command_map[args.command]()

    if success:
        print(f"\n🎉 {args.command.capitalize()} completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 {args.command.capitalize()} failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
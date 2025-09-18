#!/usr/bin/env python
"""
Test Environment Setup Script for AI Trading System
Sets up the testing environment with all necessary dependencies and configurations
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import logging
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestEnvironmentSetup:
    """Handles test environment setup and configuration"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "frontend" / "requirements.txt"
        self.test_requirements_file = self.project_root / "test-requirements.txt"
        self.python_version = sys.version_info
        self.os_info = platform.system().lower()

    def check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        logger.info("Checking Python version...")
        if self.python_version.major < 3 or (self.python_version.major == 3 and self.python_version.minor < 8):
            logger.error(f"Python 3.8+ required. Found {self.python_version.major}.{self.python_version.minor}")
            return False
        logger.info(f"Python version check passed: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        return True

    def create_virtual_environment(self) -> bool:
        """Create virtual environment for testing"""
        logger.info("Creating virtual environment...")
        venv_path = self.project_root / "test_venv"

        try:
            if venv_path.exists():
                logger.info("Virtual environment already exists, recreating...")
                shutil.rmtree(venv_path)

            # Create virtual environment
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("Virtual environment created successfully")
                return True
            else:
                logger.error(f"Failed to create virtual environment: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error creating virtual environment: {e}")
            return False

    def get_pip_executable(self) -> str:
        """Get pip executable from virtual environment"""
        if self.os_info == "windows":
            return str(self.project_root / "test_venv" / "Scripts" / "pip.exe")
        else:
            return str(self.project_root / "test_venv" / "bin" / "pip")

    def get_python_executable(self) -> str:
        """Get Python executable from virtual environment"""
        if self.os_info == "windows":
            return str(self.project_root / "test_venv" / "Scripts" / "python.exe")
        else:
            return str(self.project_root / "test_venv" / "bin" / "python")

    def install_dependencies(self) -> bool:
        """Install all required dependencies"""
        logger.info("Installing dependencies...")

        pip_executable = self.get_pip_executable()
        python_executable = self.get_python_executable()

        # Upgrade pip first
        logger.info("Upgrading pip...")
        result = subprocess.run(
            [pip_executable, "install", "--upgrade", "pip"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"Failed to upgrade pip: {result.stderr}")
            return False

        # Install main requirements
        if self.requirements_file.exists():
            logger.info("Installing main requirements...")
            result = subprocess.run(
                [pip_executable, "install", "-r", str(self.requirements_file)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Failed to install main requirements: {result.stderr}")
                return False
        else:
            logger.warning("Main requirements file not found")

        # Install test requirements
        test_requirements = self.create_test_requirements()
        if test_requirements:
            logger.info("Installing test requirements...")
            result = subprocess.run(
                [pip_executable, "install"] + test_requirements,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Failed to install test requirements: {result.stderr}")
                return False

        logger.info("All dependencies installed successfully")
        return True

    def create_test_requirements(self) -> List[str]:
        """Create list of test requirements"""
        return [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-xdist>=3.0.0",
            "pytest-html>=4.0.0",
            "pytest-benchmark>=4.0.0",
            "httpx>=0.24.0",
            "pytest-httpx>=0.22.0",
            "factory-boy>=3.3.0",
            "faker>=18.0.0",
            "responses>=0.23.0",
            "aioresponses>=0.7.0",
            "pytest-env>=1.0.0",
            "pytest-randomly>=3.12.0",
            "pytest-order>=1.0.0",
            "pytest-repeat>=0.9.0",
        ]

    def setup_environment_variables(self) -> bool:
        """Setup required environment variables for testing"""
        logger.info("Setting up environment variables...")

        test_env_vars = {
            "TESTING": "true",
            "DATABASE_URL": "sqlite:///:memory:",
            "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
            "OANDA_API_KEY": "test-oanda-api-key",
            "OANDA_ACCOUNT_ID": "test-account-id",
            "OANDA_ENVIRONMENT": "practice",
            "GEMINI_API_KEY": "test-gemini-api-key",
            "EMAIL_HOST": "",
            "EMAIL_USER": "",
            "EMAIL_PASSWORD": "",
            "EMAIL_FROM": "",
            "CACHE_TYPE": "simple",
            "CACHE_DEFAULT_TIMEOUT": "300",
            "ENVIRONMENT": "testing",
        }

        # Create .env.test file
        env_file = self.project_root / ".env.test"
        try:
            with open(env_file, 'w') as f:
                for key, value in test_env_vars.items():
                    f.write(f"{key}={value}\n")
            logger.info(f"Environment variables saved to {env_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to create .env.test file: {e}")
            return False

    def create_test_directories(self) -> bool:
        """Create necessary test directories"""
        logger.info("Creating test directories...")

        test_dirs = [
            self.project_root / "tests",
            self.project_root / "tests" / "unit",
            self.project_root / "tests" / "integration",
            self.project_root / "tests" / "api",
            self.project_root / "tests" / "performance",
            self.project_root / "test_reports",
            self.project_root / "test_reports" / "html",
            self.project_root / "test_reports" / "coverage",
            self.project_root / "test_data",
        ]

        for directory in test_dirs:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                return False

        return True

    def create_test_scripts(self) -> bool:
        """Create test runner scripts"""
        logger.info("Creating test runner scripts...")

        # Create run_tests.py
        test_script = self.project_root / "run_tests.py"
        try:
            with open(test_script, 'w') as f:
                f.write("""#!/usr/bin/env python
\"\"\"
Main test runner script for AI Trading System
\"\"\"

import subprocess
import sys
import os
from pathlib import Path

def main():
    # Add project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # Set test environment
    os.environ["TESTING"] = "true"
    os.environ["ENVIRONMENT"] = "testing"

    # Load test environment variables
    env_file = project_root / ".env.test"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    # Run tests
    python_executable = project_root / "test_venv"
    if os.name == "nt":  # Windows
        python_executable /= "Scripts" / "python.exe"
    else:
        python_executable /= "bin" / "python"

    cmd = [
        str(python_executable),
        "-m", "pytest",
        "-v",
        "--html=test_reports/html/report.html",
        "--cov=frontend",
        "--cov-report=html:test_reports/coverage",
        "--cov-report=term-missing",
        "--junitxml=test_results.xml",
        "tests/"
    ]

    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode

if __name__ == "__main__":
    exit(main())
""")
            logger.info("Created run_tests.py script")

            # Make script executable on Unix systems
            if self.os_info != "windows":
                os.chmod(test_script, 0o755)

        except Exception as e:
            logger.error(f"Failed to create test script: {e}")
            return False

        return True

    def create_sample_tests(self) -> bool:
        """Create sample test files"""
        logger.info("Creating sample test files...")

        # Create unit test sample
        unit_test_file = self.project_root / "tests" / "unit" / "test_sample.py"
        try:
            with open(unit_test_file, 'w') as f:
                f.write("""import pytest
from unittest.mock import Mock, patch
from app.services.auth_service import AuthService

class TestAuthService:
    \"\"\"Sample unit tests for AuthService\"\"\"

    def test_password_hashing(self):
        \"\"\"Test password hashing functionality\"\"\"
        password = "testpassword123"
        hashed = AuthService.get_password_hash(password)

        assert password != hashed
        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("wrongpassword", hashed)

    def test_create_access_token(self):
        \"\"\"Test JWT token creation\"\"\"
        data = {"sub": "testuser"}
        token = AuthService.create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    @patch('app.services.auth_service.AuthService.verify_password')
    def test_authenticate_user_success(self, mock_verify):
        \"\"\"Test successful user authentication\"\"\"
        mock_verify.return_value = True

        # Mock user
        mock_user = Mock()
        mock_user.hashed_password = "hashed_password"

        result = AuthService.authenticate_user("testuser", "password", mock_user)

        assert result == mock_user
        mock_verify.assert_called_once_with("password", "hashed_password")
""")
            logger.info("Created sample unit test")

        except Exception as e:
            logger.error(f"Failed to create sample unit test: {e}")
            return False

        # Create API test sample
        api_test_file = self.project_root / "tests" / "api" / "test_health_endpoints.py"
        try:
            with open(api_test_file, 'w') as f:
                f.write("""import pytest
from fastapi.testclient import TestClient
from main import app

class TestHealthEndpoints:
    \"\"\"API tests for health check endpoints\"\"\"

    def test_basic_health_check(self, client):
        \"\"\"Test basic health check endpoint\"\"\"
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] in ["healthy", "degraded"]

    def test_cache_health_check(self, client):
        \"\"\"Test cache health check endpoint\"\"\"
        response = client.get("/cache/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "cache_health" in data

    def test_ml_system_status(self, client):
        \"\"\"Test ML system status endpoint\"\"\"
        response = client.get("/ml-system/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
""")
            logger.info("Created sample API test")

        except Exception as e:
            logger.error(f"Failed to create sample API test: {e}")
            return False

        return True

    def validate_setup(self) -> bool:
        """Validate that the test environment is properly set up"""
        logger.info("Validating test environment setup...")

        validation_checks = [
            ("Virtual environment exists", (self.project_root / "test_venv").exists()),
            ("Test directories created", (self.project_root / "tests").exists()),
            ("Environment file created", (self.project_root / ".env.test").exists()),
            ("Test script created", (self.project_root / "run_tests.py").exists()),
            ("Pytest config exists", (self.project_root / "pytest.ini").exists()),
            ("Conftest exists", (self.project_root / "conftest.py").exists()),
        ]

        all_passed = True
        for check_name, check_result in validation_checks:
            if check_result:
                logger.info(f"✓ {check_name}")
            else:
                logger.error(f"✗ {check_name}")
                all_passed = False

        return all_passed

    def run_initial_tests(self) -> bool:
        """Run initial tests to validate the setup"""
        logger.info("Running initial tests to validate setup...")

        python_executable = self.get_python_executable()
        cmd = [
            python_executable,
            "-m", "pytest",
            "--collect-only",
            "-q"
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("Initial test collection successful")
                return True
            else:
                logger.error(f"Initial test collection failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error running initial tests: {e}")
            return False

    def setup_complete_message(self):
        """Display setup completion message"""
        message = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                   AI TRADING SYSTEM TEST ENVIRONMENT SETUP                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ✅ Test environment setup completed successfully!                            ║
║                                                                              ║
║  Quick Start Commands:                                                       ║
║  ─────────────────────                                                       ║
║  • Run all tests:              python run_tests.py                           ║
║  • Run specific test category:   python -m pytest tests/unit/ -v             ║
║  • Run with coverage:          python -m pytest --cov=frontend -v           ║
║  • Run performance tests:       python -m pytest tests/performance/ -v       ║
║                                                                              ║
║  Test Categories:                                                              ║
║  ──────────────────                                                              ║
║  • Unit Tests:                 tests/unit/                                   ║
║  • Integration Tests:          tests/integration/                            ║
║  • API Tests:                   tests/api/                                   ║
║  • Performance Tests:           tests/performance/                            ║
║                                                                              ║
║  Configuration Files:                                                          ║
║  ────────────────────                                                          ║
║  • pytest.ini                  Pytest configuration                          ║
║  • conftest.py                 Test fixtures and configuration               ║
║  • .env.test                   Test environment variables                   ║
║  • testsprite_config.py        Comprehensive test configuration             ║
║                                                                              ║
║  Test Reports:                                                                ║
║  ───────────────                                                                ║
║  • HTML Report:                test_reports/html/report.html                 ║
║  • Coverage Report:            test_reports/coverage/                        ║
║  • JUnit XML:                  test_results.xml                              ║
║                                                                              ║
║  Next Steps:                                                                   ║
║  ────────────                                                                   ║
║  1. Configure your environment variables in .env.test                           ║
║  2. Run the initial test suite: python run_tests.py                            ║
║  3. Review test results and coverage reports                                   ║
║  4. Add additional tests as needed                                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(message)

    def setup(self) -> bool:
        """Run complete test environment setup"""
        logger.info("Starting AI Trading System test environment setup...")

        setup_steps = [
            ("Python version check", self.check_python_version),
            ("Virtual environment creation", self.create_virtual_environment),
            ("Dependency installation", self.install_dependencies),
            ("Environment variables setup", self.setup_environment_variables),
            ("Test directories creation", self.create_test_directories),
            ("Test scripts creation", self.create_test_scripts),
            ("Sample tests creation", self.create_sample_tests),
            ("Setup validation", self.validate_setup),
            ("Initial test run", self.run_initial_tests),
        ]

        for step_name, step_function in setup_steps:
            logger.info(f"Executing: {step_name}")
            if not step_function():
                logger.error(f"Setup failed at step: {step_name}")
                return False
            logger.info(f"Completed: {step_name}")

        self.setup_complete_message()
        return True

def main():
    """Main function to run the setup"""
    print("AI Trading System - Test Environment Setup")
    print("=" * 60)

    setup = TestEnvironmentSetup()

    try:
        success = setup.setup()
        if success:
            print("\n🎉 Test environment setup completed successfully!")
            return 0
        else:
            print("\n❌ Test environment setup failed!")
            return 1

    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during setup: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
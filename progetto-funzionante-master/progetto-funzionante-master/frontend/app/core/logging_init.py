"""
Logging System Initialization
Provides initialization and setup functions for the comprehensive logging system.
"""

import logging
import asyncio
from typing import Optional

from .logging_config import LoggingConfig, get_logging_config
from .logging_integration import initialize_unified_logging, shutdown_unified_logging
from .logging_structured import get_logger, setup_logging
from .logging_filters import get_filter_manager
from .logging_rotation import initialize_rotation_system
from .logging_tracing import initialize_tracing
from .logging_performance import initialize_performance_monitoring


class LoggingInitializer:
    """Handles initialization of the complete logging system"""

    def __init__(self):
        self.initialized = False
        self.config: Optional[LoggingConfig] = None

    async def initialize(self, config: Optional[LoggingConfig] = None) -> bool:
        """Initialize the complete logging system"""
        if self.initialized:
            return True

        try:
            # Use provided config or get from environment
            self.config = config or get_logging_config()

            # Initialize basic logging first
            setup_logging(self.config)

            # Get logger for initialization
            logger = get_logger(__name__)
            logger.info("Starting comprehensive logging system initialization")

            # Initialize unified logging system
            success = await initialize_unified_logging(self.config)

            if success:
                self.initialized = True
                logger.info("Comprehensive logging system initialized successfully")
                return True
            else:
                logger.error("Failed to initialize unified logging system")
                return False

        except Exception as e:
            # Fallback to basic logging if initialization fails
            logging.basicConfig(level=logging.INFO)
            logging.error(f"Logging system initialization failed: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the logging system gracefully"""
        if not self.initialized:
            return

        try:
            await shutdown_unified_logging()
            self.initialized = False
        except Exception as e:
            if self.initialized:
                logger = get_logger(__name__)
                logger.error(f"Error during logging system shutdown: {e}")
            else:
                logging.error(f"Error during logging system shutdown: {e}")

    def is_initialized(self) -> bool:
        """Check if logging system is initialized"""
        return self.initialized

    def get_config(self) -> Optional[LoggingConfig]:
        """Get the current logging configuration"""
        return self.config


# Global initializer instance
_logging_initializer = LoggingInitializer()


async def initialize_comprehensive_logging(config: Optional[LoggingConfig] = None) -> bool:
    """Initialize the comprehensive logging system"""
    global _logging_initializer
    return await _logging_initializer.initialize(config)


async def shutdown_comprehensive_logging() -> None:
    """Shutdown the comprehensive logging system"""
    global _logging_initializer
    await _logging_initializer.shutdown()


def is_logging_initialized() -> bool:
    """Check if the logging system is initialized"""
    return _logging_initializer.is_initialized()


def get_logging_config_safe() -> Optional[LoggingConfig]:
    """Get logging configuration safely"""
    return _logging_initializer.get_config()


# Convenience function for FastAPI applications
def setup_fastapi_logging():
    """Setup logging for FastAPI application"""
    config = get_logging_config()

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.level.value),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Create log directory if it doesn't exist
    import os
    from pathlib import Path
    Path(config.log_directory).mkdir(parents=True, exist_ok=True)

    # Set up basic file logging
    if LogOutput.FILE in config.outputs:
        file_handler = logging.FileHandler(
            os.path.join(config.log_directory, config.main_log_file)
        )
        file_handler.setLevel(getattr(logging, config.level.value))
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)

    return config
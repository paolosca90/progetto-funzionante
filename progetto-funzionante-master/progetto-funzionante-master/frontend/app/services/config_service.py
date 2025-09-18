"""
Configuration Management Service

This service provides enhanced configuration management with dependency injection support,
environment-specific settings, validation, and hot-reload capabilities.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from abc import ABC, abstractmethod
import asyncio
from functools import lru_cache

from ..core.config import Settings as CoreSettings
from ..core.dependency_injection import ServiceLifetime, inject

logger = logging.getLogger(__name__)


class ConfigSource(Enum):
    """Configuration source enumeration"""
    ENVIRONMENT = "environment"
    FILE = "file"
    DATABASE = "database"
    REMOTE = "remote"


class ConfigFormat(Enum):
    """Configuration format enumeration"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    ENV = "env"


@dataclass
class ConfigValue:
    """Individual configuration value with metadata"""
    value: Any
    source: ConfigSource
    is_sensitive: bool = False
    validator: Optional[Callable[[Any], bool]] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ConfigSchema:
    """Configuration schema for validation"""
    required_fields: List[str] = field(default_factory=list)
    optional_fields: Dict[str, Any] = field(default_factory=dict)
    validators: Dict[str, Callable[[Any], bool]] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)


class ConfigProvider(ABC):
    """Abstract base class for configuration providers"""

    @abstractmethod
    async def load_config(self) -> Dict[str, Any]:
        """Load configuration from the source"""
        pass

    @abstractmethod
    async def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to the source"""
        pass

    @abstractmethod
    async def watch_changes(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Watch for configuration changes"""
        pass


class EnvironmentConfigProvider(ConfigProvider):
    """Environment variable configuration provider"""

    def __init__(self, prefix: str = "APP_"):
        self.prefix = prefix
        self._watchers: List[Callable[[Dict[str, Any]], None]] = []

    async def load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {}
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = key[len(self.prefix):].lower()
                config[config_key] = self._convert_value(value)
        return config

    async def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to environment variables (limited support)"""
        # Environment variables are typically read-only in production
        logger.warning("Cannot save configuration to environment variables")
        return False

    async def watch_changes(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Watch for environment variable changes (platform-specific)"""
        # Note: This is a simplified implementation
        # In production, you might use platform-specific solutions
        self._watchers.append(callback)

    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert string value to appropriate type"""
        try:
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            elif '.' in value:
                return float(value)
            elif value.isdigit():
                return int(value)
            else:
                return value
        except ValueError:
            return value


class FileConfigProvider(ConfigProvider):
    """File-based configuration provider"""

    def __init__(self, file_path: Union[str, Path], format: ConfigFormat = ConfigFormat.YAML):
        self.file_path = Path(file_path)
        self.format = format
        self._last_modified = 0
        self._watchers: List[Callable[[Dict[str, Any]], None]] = []

    async def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.file_path.exists():
            logger.warning(f"Config file not found: {self.file_path}")
            return {}

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if self.format == ConfigFormat.YAML:
                return yaml.safe_load(content) or {}
            elif self.format == ConfigFormat.JSON:
                return json.loads(content) if content else {}
            else:
                logger.error(f"Unsupported config format: {self.format}")
                return {}
        except Exception as e:
            logger.error(f"Error loading config from {self.file_path}: {e}")
            return {}

    async def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.file_path, 'w', encoding='utf-8') as f:
                if self.format == ConfigFormat.YAML:
                    yaml.dump(config, f, default_flow_style=False)
                elif self.format == ConfigFormat.JSON:
                    json.dump(config, f, indent=2)
                else:
                    logger.error(f"Unsupported config format: {self.format}")
                    return False

            self._last_modified = self.file_path.stat().st_mtime
            return True
        except Exception as e:
            logger.error(f"Error saving config to {self.file_path}: {e}")
            return False

    async def watch_changes(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Watch for file changes"""
        self._watchers.append(callback)
        # In a real implementation, you would use file system watchers
        # For now, we'll use a simple polling approach
        asyncio.create_task(self._poll_changes(callback))

    async def _poll_changes(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Poll for file changes"""
        while True:
            try:
                if self.file_path.exists():
                    current_mtime = self.file_path.stat().st_mtime
                    if current_mtime > self._last_modified:
                        self._last_modified = current_mtime
                        config = await self.load_config()
                        callback(config)
            except Exception as e:
                logger.error(f"Error polling config changes: {e}")

            await asyncio.sleep(5)  # Poll every 5 seconds


class ConfigService:
    """Enhanced configuration management service"""

    def __init__(self, settings: CoreSettings):
        self.settings = settings
        self._config: Dict[str, ConfigValue] = {}
        self._providers: List[ConfigProvider] = []
        self._validators: Dict[str, Callable[[Any], bool]] = {}
        self._change_callbacks: List[Callable[[str, Any, Any], None]] = []
        self._schemas: Dict[str, ConfigSchema] = {}
        self._lock = asyncio.Lock()

        # Initialize default providers
        self._initialize_providers()
        self._initialize_validators()
        self._initialize_schemas()

    def _initialize_providers(self) -> None:
        """Initialize default configuration providers"""
        # Environment provider
        env_provider = EnvironmentConfigProvider()
        self._providers.append(env_provider)

        # File providers
        config_dir = Path(__file__).parent.parent.parent / "config"
        config_files = [
            ("config.yaml", ConfigFormat.YAML),
            ("config.json", ConfigFormat.JSON),
            ("config.local.yaml", ConfigFormat.YAML),
        ]

        for filename, format_type in config_files:
            file_path = config_dir / filename
            if file_path.exists():
                file_provider = FileConfigProvider(file_path, format_type)
                self._providers.append(file_provider)

    def _initialize_validators(self) -> None:
        """Initialize configuration validators"""
        self._validators.update({
            'database_url': lambda x: x.startswith(('postgresql://', 'sqlite://')),
            'jwt_secret_key': lambda x: len(x) >= 32,
            'email_port': lambda x: 1 <= int(x) <= 65535,
            'redis_url': lambda x: x.startswith('redis://'),
            'oanda_api_key': lambda x: len(x) >= 32,
            'gemini_api_key': lambda x: len(x) >= 32,
        })

    def _initialize_schemas(self) -> None:
        """Initialize configuration schemas"""
        self._schemas.update({
            'database': ConfigSchema(
                required_fields=['database_url'],
                optional_fields={'pool_size': 10, 'max_overflow': 20},
                validators={'database_url': self._validators['database_url']}
            ),
            'auth': ConfigSchema(
                required_fields=['jwt_secret_key'],
                optional_fields={'access_token_expire_minutes': 1440},
                validators={'jwt_secret_key': self._validators['jwt_secret_key']}
            ),
            'email': ConfigSchema(
                required_fields=['email_host', 'email_user', 'email_password'],
                optional_fields={'email_port': 587, 'email_use_tls': True},
                validators={'email_port': self._validators['email_port']}
            ),
            'redis': ConfigSchema(
                required_fields=['redis_url'],
                optional_fields={'redis_db': 0, 'redis_timeout': 5},
                validators={'redis_url': self._validators['redis_url']}
            ),
            'oanda': ConfigSchema(
                required_fields=['oanda_api_key', 'oanda_account_id'],
                optional_fields={'oanda_environment': 'demo'},
                validators={
                    'oanda_api_key': self._validators['oanda_api_key']
                }
            ),
            'ai': ConfigSchema(
                required_fields=['gemini_api_key'],
                optional_fields={'ai_model': 'gemini-pro'},
                validators={'gemini_api_key': self._validators['gemini_api_key']}
            )
        })

    async def load_configuration(self) -> None:
        """Load configuration from all providers"""
        async with self._lock:
            self._config.clear()

            # Load settings from Settings class first
            for key, value in asdict(self.settings).items():
                self._config[key.lower()] = ConfigValue(
                    value=value,
                    source=ConfigSource.ENVIRONMENT,
                    description=f"Setting from Settings class"
                )

            # Load from providers
            for provider in self._providers:
                try:
                    provider_config = await provider.load_config()
                    for key, value in provider_config.items():
                        if isinstance(value, dict):
                            # Handle nested configuration
                            for sub_key, sub_value in value.items():
                                full_key = f"{key}_{sub_key}"
                                self._config[full_key] = ConfigValue(
                                    value=sub_value,
                                    source=ConfigSource.FILE if isinstance(provider, FileConfigProvider) else ConfigSource.ENVIRONMENT,
                                    description=f"Configuration from {provider.__class__.__name__}"
                                )
                        else:
                            self._config[key] = ConfigValue(
                                value=value,
                                source=ConfigSource.FILE if isinstance(provider, FileConfigProvider) else ConfigSource.ENVIRONMENT,
                                description=f"Configuration from {provider.__class__.__name__}"
                                )
                except Exception as e:
                    logger.error(f"Error loading config from {provider.__class__.__name__}: {e}")

            # Validate configuration
            self._validate_configuration()

            logger.info(f"Loaded {len(self._config)} configuration values")

    def _validate_configuration(self) -> None:
        """Validate all configuration values"""
        errors = []

        for schema_name, schema in self._schemas.items():
            # Check required fields
            for field in schema.required_fields:
                if field not in self._config:
                    errors.append(f"Required field '{field}' missing in schema '{schema_name}'")

            # Validate values
            for field, validator in schema.validators.items():
                if field in self._config:
                    try:
                        if not validator(self._config[field].value):
                            errors.append(f"Validation failed for field '{field}'")
                    except Exception as e:
                        errors.append(f"Validation error for field '{field}': {e}")

        if errors:
            logger.error(f"Configuration validation errors: {errors}")
            raise ValueError(f"Configuration validation failed: {errors}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        config_value = self._config.get(key.lower())
        if config_value is None:
            return default
        return config_value.value

    def set(self, key: str, value: Any, source: ConfigSource = ConfigSource.REMOTE) -> None:
        """Set configuration value"""
        old_value = self._config.get(key.lower())
        self._config[key.lower()] = ConfigValue(
            value=value,
            source=source,
            description="Manually set configuration"
        )

        # Notify change callbacks
        for callback in self._change_callbacks:
            try:
                callback(key.lower(), old_value.value if old_value else None, value)
            except Exception as e:
                logger.error(f"Error in config change callback: {e}")

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return {key: config_value.value for key, config_value in self._config.items()}

    def get_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """Get configuration values by prefix"""
        return {
            key: config_value.value
            for key, config_value in self._config.items()
            if key.startswith(prefix.lower())
        }

    def add_validator(self, key: str, validator: Callable[[Any], bool]) -> None:
        """Add a configuration validator"""
        self._validators[key] = validator

    def add_change_callback(self, callback: Callable[[str, Any, Any], None]) -> None:
        """Add a configuration change callback"""
        self._change_callbacks.append(callback)

    async def watch_changes(self) -> None:
        """Watch for configuration changes from all providers"""
        for provider in self._providers:
            try:
                await provider.watch_changes(self._on_config_change)
            except Exception as e:
                logger.error(f"Error setting up change watcher for {provider.__class__.__name__}: {e}")

    def _on_config_change(self, new_config: Dict[str, Any]) -> None:
        """Handle configuration changes"""
        for key, value in new_config.items():
            old_value = self._config.get(key.lower())
            if old_value is None or old_value.value != value:
                self.set(key, value, ConfigSource.FILE if isinstance(old_value, ConfigValue) and old_value.source == ConfigSource.FILE else ConfigSource.ENVIRONMENT)

    async def save_configuration(self) -> bool:
        """Save configuration to providers that support it"""
        success = True
        config_dict = self.get_all()

        for provider in self._providers:
            try:
                result = await provider.save_config(config_dict)
                if not result:
                    success = False
            except Exception as e:
                logger.error(f"Error saving config to {provider.__class__.__name__}: {e}")
                success = False

        return success

    def get_schema(self, schema_name: str) -> Optional[ConfigSchema]:
        """Get configuration schema"""
        return self._schemas.get(schema_name)

    def validate_schema(self, schema_name: str, config: Dict[str, Any]) -> List[str]:
        """Validate configuration against a schema"""
        schema = self._schemas.get(schema_name)
        if not schema:
            return [f"Schema '{schema_name}' not found"]

        errors = []

        # Check required fields
        for field in schema.required_fields:
            if field not in config:
                errors.append(f"Required field '{field}' missing")

        # Validate values
        for field, validator in schema.validators.items():
            if field in config:
                try:
                    if not validator(config[field]):
                        errors.append(f"Validation failed for field '{field}'")
                except Exception as e:
                    errors.append(f"Validation error for field '{field}': {e}")

        return errors

    def is_sensitive(self, key: str) -> bool:
        """Check if a configuration key contains sensitive information"""
        sensitive_keys = ['password', 'secret', 'key', 'token', 'api_key']
        return any(sensitive in key.lower() for sensitive in sensitive_keys)

    def mask_sensitive_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive values in configuration"""
        masked_config = {}
        for key, value in config.items():
            if self.is_sensitive(key):
                masked_config[key] = '***masked***'
            else:
                masked_config[key] = value
        return masked_config

    @lru_cache(maxsize=128)
    def get_cached(self, key: str, default: Any = None) -> Any:
        """Get cached configuration value"""
        return self.get(key, default)

    def clear_cache(self) -> None:
        """Clear the configuration cache"""
        self.get_cached.cache_clear()

    def __getitem__(self, key: str) -> Any:
        """Dictionary-like access"""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Dictionary-like setting"""
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """Dictionary-like contains check"""
        return key.lower() in self._config

    def get_database_config(self) -> Dict[str, Any]:
        """Get database-specific configuration"""
        return self.get_by_prefix('database')

    def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication-specific configuration"""
        return self.get_by_prefix('auth')

    def get_email_config(self) -> Dict[str, Any]:
        """Get email-specific configuration"""
        return self.get_by_prefix('email')

    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis-specific configuration"""
        return self.get_by_prefix('redis')

    def get_oanda_config(self) -> Dict[str, Any]:
        """Get OANDA-specific configuration"""
        return self.get_by_prefix('oanda')

    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI-specific configuration"""
        return self.get_by_prefix('ai')
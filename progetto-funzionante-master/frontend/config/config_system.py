"""
Comprehensive Configuration System for FastAPI Trading Application
Production-ready environment configuration with validation, hot-reloading, and security features
"""

import os
import json
import yaml
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime
from enum import Enum
import logging
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigType(str, Enum):
    """Configuration file types"""
    YAML = "yaml"
    JSON = "json"
    ENV = "env"
    TOML = "toml"

class ConfigSource(str, Enum):
    """Configuration sources"""
    FILE = "file"
    ENVIRONMENT = "environment"
    SECRETS_MANAGER = "secrets_manager"
    DATABASE = "database"
    REMOTE = "remote"

class SecurityLevel(str, Enum):
    """Security levels for configuration"""
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    SECRET = "secret"

@dataclass
class ConfigMetadata:
    """Metadata for configuration items"""
    key: str
    value_type: str
    security_level: SecurityLevel
    description: str
    required: bool = False
    validation_pattern: Optional[str] = None
    default_value: Any = None
    last_modified: Optional[datetime] = None
    modified_by: Optional[str] = None

@dataclass
class FeatureFlag:
    """Feature flag with metadata"""
    name: str
    enabled: bool
    description: str
    environment: str
    rollout_percentage: int = 100
    conditions: Dict[str, Any] = None
    created_at: datetime = None
    modified_at: datetime = None
    created_by: str = None
    tags: List[str] = None

    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.modified_at is None:
            self.modified_at = datetime.utcnow()

@dataclass
class ConfigVersion:
    """Configuration version information"""
    version: str
    environment: str
    created_at: datetime
    created_by: str
    checksum: str
    changes: List[str]
    rollback_available: bool = True
    feature_flags_snapshot: Dict[str, bool] = None

class ConfigValidator:
    """Validates configuration values"""

    @staticmethod
    def validate_string(value: str, min_length: int = 0, max_length: int = None, pattern: str = None) -> str:
        """Validate string configuration"""
        if not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value)}")

        if len(value) < min_length:
            raise ValueError(f"String must be at least {min_length} characters long")

        if max_length and len(value) > max_length:
            raise ValueError(f"String must be no more than {max_length} characters long")

        if pattern:
            import re
            if not re.match(pattern, value):
                raise ValueError(f"String does not match pattern: {pattern}")

        return value

    @staticmethod
    def validate_numeric(value: Union[int, float], min_value: float = None, max_value: float = None) -> Union[int, float]:
        """Validate numeric configuration"""
        if not isinstance(value, (int, float)):
            raise ValueError(f"Expected numeric, got {type(value)}")

        if min_value is not None and value < min_value:
            raise ValueError(f"Value must be at least {min_value}")

        if max_value is not None and value > max_value:
            raise ValueError(f"Value must be no more than {max_value}")

        return value

    @staticmethod
    def validate_url(value: str) -> str:
        """Validate URL configuration"""
        from urllib.parse import urlparse
        parsed = urlparse(value)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError(f"Invalid URL: {value}")
        return value

    @staticmethod
    def validate_email(value: str) -> str:
        """Validate email configuration"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValueError(f"Invalid email address: {value}")
        return value

class ConfigurationLoader:
    """Loads configuration from various sources"""

    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path.cwd()
        self.loaded_configs: Dict[str, Dict[str, Any]] = {}
        self.config_order: List[str] = []

    def load_config(self, source: str, config_type: ConfigType = ConfigType.YAML) -> Dict[str, Any]:
        """Load configuration from a source"""
        try:
            if config_type == ConfigType.YAML:
                return self._load_yaml(source)
            elif config_type == ConfigType.JSON:
                return self._load_json(source)
            elif config_type == ConfigType.ENV:
                return self._load_env(source)
            elif config_type == ConfigType.TOML:
                return self._load_toml(source)
            else:
                raise ValueError(f"Unsupported config type: {config_type}")
        except Exception as e:
            logger.error(f"Failed to load config from {source}: {e}")
            return {}

    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load YAML configuration"""
        path = self.base_path / file_path
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Load JSON configuration"""
        path = self.base_path / file_path
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_env(self, env_prefix: str = "") -> Dict[str, Any]:
        """Load environment variables"""
        config = {}
        prefix = env_prefix.upper() + "_" if env_prefix else ""

        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                config[config_key] = self._convert_env_value(value)

        return config

    def _load_toml(self, file_path: str) -> Dict[str, Any]:
        """Load TOML configuration"""
        try:
            import toml
            path = self.base_path / file_path
            with open(path, 'r', encoding='utf-8') as f:
                return toml.load(f)
        except ImportError:
            logger.warning("TOML support not available, install toml package")
            return {}

    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Try JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

        # Return as string
        return value

class SecretsManager:
    """Manages sensitive configuration and secrets"""

    def __init__(self):
        self.secrets_cache: Dict[str, Any] = {}
        self.secrets_metadata: Dict[str, ConfigMetadata] = {}
        self.encryption_key: Optional[str] = None

    def initialize(self, encryption_key: str = None):
        """Initialize secrets manager"""
        self.encryption_key = encryption_key or os.getenv('SECRETS_ENCRYPTION_KEY')
        if not self.encryption_key:
            logger.warning("No encryption key provided, secrets will be stored in plaintext")

    def store_secret(self, key: str, value: Any, security_level: SecurityLevel = SecurityLevel.SECRET) -> bool:
        """Store a secret"""
        try:
            # Create metadata
            metadata = ConfigMetadata(
                key=key,
                value_type=type(value).__name__,
                security_level=security_level,
                description=f"Secret: {key}",
                required=True,
                last_modified=datetime.utcnow(),
                modified_by="system"
            )

            # Encrypt if encryption key is available
            encrypted_value = self._encrypt_value(value) if self.encryption_key else value

            # Store secret
            self.secrets_cache[key] = encrypted_value
            self.secrets_metadata[key] = metadata

            logger.info(f"Secret '{key}' stored successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to store secret '{key}': {e}")
            return False

    def get_secret(self, key: str) -> Optional[Any]:
        """Retrieve a secret"""
        try:
            if key not in self.secrets_cache:
                logger.warning(f"Secret '{key}' not found")
                return None

            encrypted_value = self.secrets_cache[key]

            # Decrypt if encryption key is available
            if self.encryption_key:
                return self._decrypt_value(encrypted_value)

            return encrypted_value
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{key}': {e}")
            return None

    def _encrypt_value(self, value: Any) -> str:
        """Encrypt a value"""
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self.encryption_key.encode())
            json_value = json.dumps(value)
            return f.encrypt(json_value.encode()).decode()
        except ImportError:
            logger.warning("Cryptography not available, using base64 encoding")
            import base64
            return base64.b64encode(json.dumps(value).encode()).decode()

    def _decrypt_value(self, encrypted_value: str) -> Any:
        """Decrypt a value"""
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self.encryption_key.encode())
            decrypted = f.decrypt(encrypted_value.encode()).decode()
            return json.loads(decrypted)
        except ImportError:
            logger.warning("Cryptography not available, using base64 decoding")
            import base64
            decrypted = base64.b64decode(encrypted_value.encode()).decode()
            return json.loads(decrypted)

    def list_secrets(self, security_level: SecurityLevel = None) -> List[str]:
        """List available secrets"""
        if security_level:
            return [
                key for key, metadata in self.secrets_metadata.items()
                if metadata.security_level == security_level
            ]
        return list(self.secrets_metadata.keys())

    def rotate_secret(self, key: str, new_value: Any) -> bool:
        """Rotate a secret value"""
        try:
            if key not in self.secrets_cache:
                logger.error(f"Secret '{key}' not found for rotation")
                return False

            # Store old value for rollback
            old_value = self.secrets_cache[key]

            # Store new value
            success = self.store_secret(key, new_value)

            if success:
                logger.info(f"Secret '{key}' rotated successfully")
                return True
            else:
                # Restore old value if rotation failed
                self.secrets_cache[key] = old_value
                logger.error(f"Failed to rotate secret '{key}', restored old value")
                return False
        except Exception as e:
            logger.error(f"Failed to rotate secret '{key}': {e}")
            return False

class ConfigurationManager:
    """Main configuration management system"""

    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path("config")
        self.loader = ConfigurationLoader(self.config_dir)
        self.secrets_manager = SecretsManager()
        self.config_cache: Dict[str, Any] = {}
        self.config_history: List[ConfigVersion] = []
        self.validators: Dict[str, ConfigValidator] = {}
        self.feature_flags: Dict[str, FeatureFlag] = {}
        self.hot_reload_enabled = False
        self.watchers = []

        # Initialize configuration
        self._initialize()

    def _initialize(self):
        """Initialize configuration system"""
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)

        # Initialize secrets manager
        encryption_key = os.getenv('SECRETS_ENCRYPTION_KEY')
        self.secrets_manager.initialize(encryption_key)

        # Load default configurations
        self._load_default_configs()

        # Load environment-specific configurations
        self._load_environment_configs()

        # Load feature flags
        self._load_feature_flags()

    def _load_default_configs(self):
        """Load default configuration files"""
        config_files = [
            ("config.yaml", ConfigType.YAML),
            ("config.json", ConfigType.JSON),
            (".env", ConfigType.ENV)
        ]

        for filename, config_type in config_files:
            config_path = self.config_dir / filename
            if config_path.exists():
                config = self.loader.load_config(str(config_path), config_type)
                self.config_cache.update(config)
                logger.info(f"Loaded configuration from {filename}")

    def _load_environment_configs(self):
        """Load environment-specific configurations"""
        environment = os.getenv('ENVIRONMENT', 'development').lower()

        # Load environment-specific config
        env_config_file = f"config.{environment}.yaml"
        env_config_path = self.config_dir / env_config_file

        if env_config_path.exists():
            config = self.loader.load_config(str(env_config_path), ConfigType.YAML)
            self.config_cache.update(config)
            logger.info(f"Loaded environment-specific configuration from {env_config_file}")

        # Load environment variables
        env_config = self.loader.load_config("", ConfigType.ENV)
        self.config_cache.update(env_config)
        logger.info(f"Loaded {len(env_config)} environment variables")

    def _load_feature_flags(self):
        """Load feature flags"""
        feature_flags_file = self.config_dir / "feature_flags.yaml"
        if feature_flags_file.exists():
            feature_flags_data = self.loader.load_config(str(feature_flags_file), ConfigType.YAML)
            flags_data = feature_flags_data.get('flags', {})

            # Convert to FeatureFlag objects
            self.feature_flags = {}
            for flag_name, flag_data in flags_data.items():
                if isinstance(flag_data, dict):
                    self.feature_flags[flag_name] = FeatureFlag(
                        name=flag_name,
                        enabled=flag_data.get('enabled', False),
                        description=flag_data.get('description', ''),
                        environment=flag_data.get('environment', 'development'),
                        rollout_percentage=flag_data.get('rollout_percentage', 100),
                        conditions=flag_data.get('conditions', {}),
                        created_at=self._parse_datetime(flag_data.get('created_at')),
                        modified_at=self._parse_datetime(flag_data.get('modified_at')),
                        created_by=flag_data.get('created_by', 'system'),
                        tags=flag_data.get('tags', [])
                    )
                else:
                    # Simple boolean flag for backward compatibility
                    self.feature_flags[flag_name] = FeatureFlag(
                        name=flag_name,
                        enabled=bool(flag_data),
                        description=f'Legacy flag: {flag_name}',
                        environment='development'
                    )

            logger.info(f"Loaded {len(self.feature_flags)} feature flags")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config_cache.get(key, default)

    def set(self, key: str, value: Any, persist: bool = True) -> bool:
        """Set configuration value"""
        try:
            old_value = self.config_cache.get(key)
            self.config_cache[key] = value

            if persist:
                self._persist_config_change(key, old_value, value)

            logger.info(f"Configuration '{key}' updated")
            return True
        except Exception as e:
            logger.error(f"Failed to set configuration '{key}': {e}")
            return False

    def _persist_config_change(self, key: str, old_value: Any, new_value: Any):
        """Persist configuration change to storage"""
        # Create version entry
        version = ConfigVersion(
            version=f"v{len(self.config_history) + 1}",
            environment=os.getenv('ENVIRONMENT', 'development'),
            created_at=datetime.utcnow(),
            created_by="system",
            checksum=self._generate_checksum(str(new_value)),
            changes=[f"Updated {key}: {old_value} -> {new_value}"],
            feature_flags_snapshot={name: flag.enabled for name, flag in self.feature_flags.items()}
        )

        self.config_history.append(version)

        # Update configuration file
        self._update_config_file(key, new_value)

        # Prune history if too long
        self._prune_config_history()

    def _generate_checksum(self, value: str) -> str:
        """Generate checksum for configuration value"""
        import hashlib
        return hashlib.sha256(value.encode()).hexdigest()

    def _update_config_file(self, key: str, value: Any):
        """Update configuration file"""
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f) or {}

                config[key] = value

                with open(config_file, 'w') as f:
                    yaml.safe_dump(config, f, default_flow_style=False)

                logger.info(f"Configuration file updated for key '{key}'")
            except Exception as e:
                logger.error(f"Failed to update configuration file: {e}")

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate all configuration values"""
        errors = []
        warnings = []

        # Validate required configurations
        required_configs = [
            'database_url',
            'jwt_secret_key',
            'oanda_api_key',
            'gemini_api_key'
        ]

        for config_key in required_configs:
            if not self.get(config_key):
                errors.append(f"Required configuration '{config_key}' is missing")

        # Validate specific configurations
        self._validate_database_config(errors, warnings)
        self._validate_security_config(errors, warnings)
        self._validate_api_config(errors, warnings)

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_configs': len(self.config_cache)
        }

    def _validate_database_config(self, errors: List[str], warnings: List[str]):
        """Validate database configuration"""
        db_url = self.get('database_url')
        if db_url:
            if not db_url.startswith(('postgresql://', 'mysql://', 'sqlite:///')):
                errors.append("Database URL must be a valid database connection string")

    def _validate_security_config(self, errors: List[str], warnings: List[str]):
        """Validate security configuration"""
        jwt_secret = self.get('security.jwt_secret_key')
        if jwt_secret and len(jwt_secret) < 32:
            errors.append("JWT secret key must be at least 32 characters long")

    def _validate_api_config(self, errors: List[str], warnings: List[str]):
        """Validate API configuration"""
        rate_limit = self.get('rate_limit_requests')
        if rate_limit and rate_limit > 1000:
            warnings.append("High rate limit may impact system performance")

    def enable_hot_reload(self, watch_patterns: List[str] = None):
        """Enable hot-reloading of configuration"""
        self.hot_reload_enabled = True
        watch_patterns = watch_patterns or ["config/*.yaml", ".env"]

        # Setup file watchers
        self._setup_file_watchers(watch_patterns)

        logger.info("Hot-reloading enabled for configuration")

    def _setup_file_watchers(self, patterns: List[str]):
        """Setup file watchers for hot-reloading"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class ConfigFileHandler(FileSystemEventHandler):
                def __init__(self, config_manager):
                    self.config_manager = config_manager

                def on_modified(self, event):
                    if not event.is_directory:
                        self.config_manager._reload_configuration()

            observer = Observer()
            handler = ConfigFileHandler(self)

            for pattern in patterns:
                # This is a simplified version - in production, you'd want to properly handle glob patterns
                observer.schedule(handler, str(self.config_dir), recursive=False)

            observer.start()
            self.watchers.append(observer)

            logger.info(f"File watchers setup for patterns: {patterns}")
        except ImportError:
            logger.warning("Watchdog not available, hot-reloading disabled")

    def _reload_configuration(self):
        """Reload configuration when files change"""
        logger.info("Configuration files changed, reloading...")

        # Clear cache
        old_config = self.config_cache.copy()
        self.config_cache.clear()

        # Reload configurations
        self._load_default_configs()
        self._load_environment_configs()
        self._load_feature_flags()

        # Compare changes
        changes = self._find_config_changes(old_config, self.config_cache)
        if changes:
            logger.info(f"Configuration reloaded with {len(changes)} changes")
            for change in changes:
                logger.info(f"  {change}")

    def _find_config_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[str]:
        """Find changes between old and new configuration"""
        changes = []

        all_keys = set(old_config.keys()) | set(new_config.keys())

        for key in all_keys:
            old_value = old_config.get(key)
            new_value = new_config.get(key)

            if old_value != new_value:
                if key in old_config and key in new_config:
                    changes.append(f"{key}: {old_value} -> {new_value}")
                elif key in new_config:
                    changes.append(f"{key}: added = {new_value}")
                else:
                    changes.append(f"{key}: removed")

        return changes

    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse datetime string"""
        if datetime_str:
            try:
                return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            except:
                return datetime.utcnow()
        return None

    def get_feature_flag(self, flag_name: str, user_id: str = None, user_attributes: Dict[str, Any] = None) -> bool:
        """Get feature flag value with evaluation"""
        flag = self.feature_flags.get(flag_name)
        if not flag:
            return False

        # Check if flag is enabled for this environment
        if flag.environment != self.get('environment', 'development'):
            return False

        # Check rollout percentage
        if flag.rollout_percentage < 100:
            if user_id:
                # Use user_id for consistent rollout
                import hashlib
                hash_value = int(hashlib.md5(f"{flag_name}:{user_id}".encode()).hexdigest(), 16)
                if (hash_value % 100) >= flag.rollout_percentage:
                    return False
            else:
                # Random rollout for anonymous users
                import random
                if random.randint(1, 100) > flag.rollout_percentage:
                    return False

        # Check conditions
        if flag.conditions and user_attributes:
            for condition_key, condition_value in flag.conditions.items():
                if condition_key in user_attributes:
                    if user_attributes[condition_key] != condition_value:
                        return False

        return flag.enabled

    def set_feature_flag(self, flag_name: str, enabled: bool, description: str = None,
                        environment: str = None, rollout_percentage: int = 100,
                        conditions: Dict[str, Any] = None, tags: List[str] = None) -> bool:
        """Set feature flag value with metadata"""
        try:
            current_env = environment or self.get('environment', 'development')

            # Update existing flag or create new one
            if flag_name in self.feature_flags:
                flag = self.feature_flags[flag_name]
                flag.enabled = enabled
                flag.modified_at = datetime.utcnow()
                if description:
                    flag.description = description
                if environment:
                    flag.environment = environment
                if rollout_percentage is not None:
                    flag.rollout_percentage = rollout_percentage
                if conditions:
                    flag.conditions.update(conditions)
                if tags:
                    flag.tags = tags
            else:
                flag = FeatureFlag(
                    name=flag_name,
                    enabled=enabled,
                    description=description or f'Feature flag: {flag_name}',
                    environment=current_env,
                    rollout_percentage=rollout_percentage,
                    conditions=conditions or {},
                    tags=tags or []
                )
                self.feature_flags[flag_name] = flag

            self._persist_feature_flags()
            logger.info(f"Feature flag '{flag_name}' set to {enabled} (environment: {current_env}, rollout: {rollout_percentage}%)")
            return True
        except Exception as e:
            logger.error(f"Failed to set feature flag '{flag_name}': {e}")
            return False

    def list_feature_flags(self, environment: str = None, tag: str = None) -> List[FeatureFlag]:
        """List feature flags with filtering"""
        flags = list(self.feature_flags.values())

        if environment:
            flags = [f for f in flags if f.environment == environment]

        if tag:
            flags = [f for f in flags if tag in f.tags]

        return sorted(flags, key=lambda x: x.name)

    def delete_feature_flag(self, flag_name: str) -> bool:
        """Delete a feature flag"""
        try:
            if flag_name in self.feature_flags:
                del self.feature_flags[flag_name]
                self._persist_feature_flags()
                logger.info(f"Feature flag '{flag_name}' deleted")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete feature flag '{flag_name}': {e}")
            return False

    def _persist_feature_flags(self):
        """Persist feature flags to file"""
        feature_flags_file = self.config_dir / "feature_flags.yaml"
        try:
            # Convert FeatureFlag objects to dictionaries for serialization
            flags_data = {}
            for flag_name, flag in self.feature_flags.items():
                flags_data[flag_name] = {
                    'enabled': flag.enabled,
                    'description': flag.description,
                    'environment': flag.environment,
                    'rollout_percentage': flag.rollout_percentage,
                    'conditions': flag.conditions,
                    'created_at': flag.created_at.isoformat(),
                    'modified_at': flag.modified_at.isoformat(),
                    'created_by': flag.created_by,
                    'tags': flag.tags
                }

            feature_flags_data = {'flags': flags_data}
            with open(feature_flags_file, 'w') as f:
                yaml.safe_dump(feature_flags_data, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Failed to persist feature flags: {e}")

    def get_feature_flag_stats(self) -> Dict[str, Any]:
        """Get feature flag statistics"""
        total_flags = len(self.feature_flags)
        enabled_flags = sum(1 for f in self.feature_flags.values() if f.enabled)
        environments = set(f.environment for f in self.feature_flags.values())
        tags = set(tag for f in self.feature_flags.values() for tag in f.tags)

        return {
            'total_flags': total_flags,
            'enabled_flags': enabled_flags,
            'disabled_flags': total_flags - enabled_flags,
            'environments': list(environments),
            'tags': list(tags),
            'rollout_stats': {
                'full_rollout': sum(1 for f in self.feature_flags.values() if f.rollout_percentage == 100),
                'partial_rollout': sum(1 for f in self.feature_flags.values() if 0 < f.rollout_percentage < 100),
                'no_rollout': sum(1 for f in self.feature_flags.values() if f.rollout_percentage == 0)
            }
        }

    def _prune_config_history(self, max_versions: int = 50):
        """Prune configuration history to keep only recent versions"""
        if len(self.config_history) > max_versions:
            # Keep the most recent versions
            self.config_history = self.config_history[-max_versions:]
            logger.info(f"Configuration history pruned to {max_versions} versions")

    def get_config_version(self, version: str) -> Optional[ConfigVersion]:
        """Get a specific configuration version"""
        for config_version in self.config_history:
            if config_version.version == version:
                return config_version
        return None

    def rollback_to_version(self, version: str) -> bool:
        """Rollback configuration to a specific version"""
        try:
            target_version = self.get_config_version(version)
            if not target_version:
                logger.error(f"Configuration version '{version}' not found")
                return False

            if not target_version.rollback_available:
                logger.error(f"Rollback not available for version '{version}'")
                return False

            # Create backup before rollback
            self.backup_configuration()

            # Restore configuration from version data
            # Note: This is a simplified implementation. In production, you'd need to store
            # the actual configuration state for each version
            logger.info(f"Rolling back to configuration version '{version}'")

            # Restore feature flags if available
            if target_version.feature_flags_snapshot:
                for flag_name, flag_value in target_version.feature_flags_snapshot.items():
                    if flag_name in self.feature_flags:
                        self.feature_flags[flag_name].enabled = flag_value
                        self.feature_flags[flag_name].modified_at = datetime.utcnow()

                self._persist_feature_flags()

            # Create rollback version entry
            rollback_version = ConfigVersion(
                version=f"v{len(self.config_history) + 1}",
                environment=os.getenv('ENVIRONMENT', 'development'),
                created_at=datetime.utcnow(),
                created_by="system",
                checksum=self._generate_checksum(str(self.config_cache)),
                changes=[f"Rollback to version {version}"],
                feature_flags_snapshot={name: flag.enabled for name, flag in self.feature_flags.items()}
            )

            self.config_history.append(rollback_version)
            logger.info(f"Successfully rolled back to version '{version}'")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback to version '{version}': {e}")
            return False

    def create_config_version(self, description: str = None) -> str:
        """Create a manual configuration version"""
        version = f"v{len(self.config_history) + 1}"
        config_version = ConfigVersion(
            version=version,
            environment=os.getenv('ENVIRONMENT', 'development'),
            created_at=datetime.utcnow(),
            created_by="user",
            checksum=self._generate_checksum(str(self.config_cache)),
            changes=[description or "Manual version"],
            feature_flags_snapshot={name: flag.enabled for name, flag in self.feature_flags.items()}
        )

        self.config_history.append(config_version)
        logger.info(f"Created configuration version '{version}': {description}")
        return version

    def list_config_versions(self, limit: int = None) -> List[ConfigVersion]:
        """List configuration versions"""
        versions = self.config_history.copy()
        if limit:
            versions = versions[-limit:]
        return sorted(versions, key=lambda x: x.created_at, reverse=True)

    def backup_configuration(self, backup_path: Path = None) -> bool:
        """Backup current configuration"""
        try:
            if not backup_path:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_path = self.config_dir / f"backup_{timestamp}"

            backup_path.mkdir(exist_ok=True)

            # Backup configuration files
            config_files = ["config.yaml", "config.json", ".env", "feature_flags.yaml"]
            for filename in config_files:
                source = self.config_dir / filename
                if source.exists():
                    dest = backup_path / filename
                    dest.write_text(source.read_text())

            # Backup configuration cache
            cache_file = backup_path / "config_cache.json"
            with open(cache_file, 'w') as f:
                json.dump(self.config_cache, f, indent=2, default=str)

            # Backup version history
            history_file = backup_path / "config_history.json"
            history_data = [
                {
                    'version': v.version,
                    'environment': v.environment,
                    'created_at': v.created_at.isoformat(),
                    'created_by': v.created_by,
                    'checksum': v.checksum,
                    'changes': v.changes,
                    'rollback_available': v.rollback_available,
                    'feature_flags_snapshot': v.feature_flags_snapshot
                }
                for v in self.config_history
            ]
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2, default=str)

            logger.info(f"Configuration backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup configuration: {e}")
            return False

    def restore_configuration(self, backup_path: Path) -> bool:
        """Restore configuration from backup"""
        try:
            if not backup_path.exists():
                logger.error(f"Backup path does not exist: {backup_path}")
                return False

            # Restore configuration files
            config_files = ["config.yaml", "config.json", ".env", "feature_flags.yaml"]
            for filename in config_files:
                source = backup_path / filename
                if source.exists():
                    dest = self.config_dir / filename
                    dest.write_text(source.read_text())

            # Reload configuration
            self._initialize()

            logger.info(f"Configuration restored from {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore configuration: {e}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'total_configs': len(self.config_cache),
            'feature_flags': len(self.feature_flags),
            'config_history': len(self.config_history),
            'hot_reload_enabled': self.hot_reload_enabled,
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'secrets_count': len(self.secrets_manager.secrets_cache),
            'last_updated': max(
                (h.created_at for h in self.config_history),
                default=datetime.utcnow()
            )
        }

    def cleanup(self):
        """Cleanup resources"""
        # Stop file watchers
        for watcher in self.watchers:
            try:
                watcher.stop()
                watcher.join()
            except Exception as e:
                logger.error(f"Failed to stop file watcher: {e}")

        logger.info("Configuration manager cleaned up")

# Global configuration manager instance
config_manager = ConfigurationManager()
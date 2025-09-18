"""
Comprehensive Input Validation and Sanitization Framework
Production-ready input validation with security focus
"""

import re
import html
import json
import base64
import hashlib
import ipaddress
import urllib.parse
from typing import Union, Optional, List, Dict, Any, TypeVar, get_type_hints
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, validator, Field, constr
from fastapi import HTTPException, status
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ValidationErrorType(Enum):
    """Types of validation errors"""
    INVALID_FORMAT = "invalid_format"
    TOO_LONG = "too_long"
    TOO_SHORT = "too_short"
    INVALID_CHARACTERS = "invalid_characters"
    MALICIOUS_CONTENT = "malicious_content"
    REQUIRED_FIELD = "required_field"
    INVALID_RANGE = "invalid_range"
    INVALID_EMAIL = "invalid_email"
    INVALID_URL = "invalid_url"
    INVALID_IP = "invalid_ip"
    SQL_INJECTION = "sql_injection"
    XSS_INJECTION = "xss_injection"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"

@dataclass
class ValidationError:
    """Validation error details"""
    field: str
    error_type: ValidationErrorType
    message: str
    value: Any = None

class InputValidator(ABC):
    """Abstract base class for input validators"""

    @abstractmethod
    def validate(self, value: Any) -> Tuple[bool, List[ValidationError]]:
        """Validate input value"""
        pass

    @abstractmethod
    def sanitize(self, value: Any) -> Any:
        """Sanitize input value"""
        pass

class StringValidator(InputValidator):
    """Comprehensive string validator with security focus"""

    def __init__(
        self,
        min_length: int = 0,
        max_length: int = 1000,
        allowed_chars: Optional[str] = None,
        forbidden_chars: Optional[str] = None,
        forbidden_patterns: Optional[List[str]] = None,
        allow_html: bool = False,
        allow_sql: bool = False,
        trim_whitespace: bool = True,
        case_sensitive: bool = False
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.allowed_chars = set(allowed_chars) if allowed_chars else None
        self.forbidden_chars = set(forbidden_chars) if forbidden_chars else None
        self.forbidden_patterns = forbidden_patterns or []
        self.allow_html = allow_html
        self.allow_sql = allow_sql
        self.trim_whitespace = trim_whitespace
        self.case_sensitive = case_sensitive

        # Default forbidden patterns for security
        self.security_patterns = [
            # SQL injection patterns
            r"(?i)\b(union\s+select|select\s+.*\s+from|insert\s+into|update\s+.*\s+set|delete\s+from|drop\s+table|alter\s+table|create\s+table|exec\s*\(|execute\s*\(|sp_executesql|xp_cmdshell|;\s*--|/\*.*\*/)",
            # XSS patterns
            r"(?i)<script.*?>.*?</script>|javascript:|vbscript:|on\w+\s*=|eval\s*\(|document\.|window\.|alert\s*\(|prompt\s*\(|confirm\s*\(",
            # Command injection patterns
            r"(?i)\b(system|exec|shell_exec|passthru|proc_open|popen|curl|wget|nc|netcat|telnet|ssh|scp|ftp|sftp)\b|\|.*\||`.*`|\$\(|;|\&\&|\|\|",
            # Path traversal patterns
            r"\.\./|\.\.\\|%2e%2e%2f|%2e%2e\\|%2f%2e%2e|~%2f|%00",
            # LDAP injection patterns
            r"(?i)\*\)\(&\)|\*\)\(\|\(|\*\))",
            # NoSQL injection patterns
            r"(?i)\$where|\$ne|\$gt|\$lt|\$regex|\$exists"
        ]

    def validate(self, value: str) -> Tuple[bool, List[ValidationError]]:
        """Validate string input"""
        errors = []

        if not isinstance(value, str):
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message="Value must be a string"
            ))
            return False, errors

        # Trim whitespace if configured
        if self.trim_whitespace:
            value = value.strip()

        # Check length
        if len(value) < self.min_length:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.TOO_SHORT,
                message=f"String must be at least {self.min_length} characters long"
            ))

        if len(value) > self.max_length:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.TOO_LONG,
                message=f"String must be no more than {self.max_length} characters long"
            ))

        # Check allowed characters
        if self.allowed_chars:
            invalid_chars = set(value) - self.allowed_chars
            if invalid_chars:
                errors.append(ValidationError(
                    field="",
                    error_type=ValidationErrorType.INVALID_CHARACTERS,
                    message=f"String contains invalid characters: {', '.join(invalid_chars)}"
                ))

        # Check forbidden characters
        if self.forbidden_chars:
            forbidden_found = set(value) & self.forbidden_chars
            if forbidden_found:
                errors.append(ValidationError(
                    field="",
                    error_type=ValidationErrorType.INVALID_CHARACTERS,
                    message=f"String contains forbidden characters: {', '.join(forbidden_found)}"
                ))

        # Security checks
        security_patterns = self.security_patterns.copy()
        if not self.allow_sql:
            security_patterns.extend(self.forbidden_patterns)

        for pattern in security_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                errors.append(ValidationError(
                    field="",
                    error_type=ValidationErrorType.MALICIOUS_CONTENT,
                    message=f"String contains potentially malicious content: {pattern}"
                ))

        return len(errors) == 0, errors

    def sanitize(self, value: str) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return str(value)

        # HTML encoding if HTML not allowed
        if not self.allow_html:
            value = html.escape(value)

        # Remove potentially dangerous characters
        dangerous_chars = {'<', '>', '"', "'", '&', '\\', '/', ';', '|', '`', '$', '(', ')', '{', '}'}
        if not self.allow_html:
            value = ''.join(c if c not in dangerous_chars else '' for c in value)

        # Remove null bytes
        value = value.replace('\x00', '')

        # Trim whitespace
        if self.trim_whitespace:
            value = value.strip()

        return value

class EmailValidator(InputValidator):
    """Email address validator with security checks"""

    def __init__(self, max_length: int = 254):
        self.max_length = max_length
        # RFC 5322 compliant email regex
        self.email_regex = re.compile(
            r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        )

    def validate(self, value: str) -> Tuple[bool, List[ValidationError]]:
        """Validate email address"""
        errors = []

        if not isinstance(value, str):
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message="Email must be a string"
            ))
            return False, errors

        value = value.strip()

        if len(value) > self.max_length:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.TOO_LONG,
                message=f"Email must be no more than {self.max_length} characters long"
            ))

        if not self.email_regex.match(value):
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_EMAIL,
                message="Invalid email format"
            ))

        # Security checks for email
        if any(char in value for char in ['<', '>', '"', "'", '&', '\\', '/', ';', '|', '`', '$']):
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.MALICIOUS_CONTENT,
                message="Email contains potentially malicious characters"
            ))

        # Check for common malicious email patterns
        malicious_patterns = [
            r"@localhost\.localdomain$",
            r"@127\.0\.0\.1$",
            r"@192\.168\.",
            r"@10\.",
            r"@172\.(1[6-9]|2[0-9]|3[01])\.",
            r"^[^@]+$",  # No @ symbol
            r"@.*@",    # Multiple @ symbols
            r"\.\.",    # Double dots
            r"^\.|\.@",  # Starts or ends with dot
        ]

        for pattern in malicious_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                errors.append(ValidationError(
                    field="",
                    error_type=ValidationErrorType.MALICIOUS_CONTENT,
                    message="Email contains potentially malicious pattern"
                ))

        return len(errors) == 0, errors

    def sanitize(self, value: str) -> str:
        """Sanitize email address"""
        if not isinstance(value, str):
            return ""

        value = value.strip().lower()
        # Remove potentially dangerous characters
        value = re.sub(r'[<>"\'&\\|`$]', '', value)
        return value

class URLValidator(InputValidator):
    """URL validator with security checks"""

    def __init__(self, allowed_schemes: Optional[List[str]] = None, allowed_domains: Optional[List[str]] = None):
        self.allowed_schemes = allowed_schemes or ['http', 'https']
        self.allowed_domains = allowed_domains

    def validate(self, value: str) -> Tuple[bool, List[ValidationError]]:
        """Validate URL"""
        errors = []

        if not isinstance(value, str):
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message="URL must be a string"
            ))
            return False, errors

        value = value.strip()

        try:
            parsed = urllib.parse.urlparse(value)
        except Exception:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_URL,
                message="Invalid URL format"
            ))
            return False, errors

        # Check scheme
        if parsed.scheme not in self.allowed_schemes:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_URL,
                message=f"URL scheme '{parsed.scheme}' is not allowed"
            ))

        # Check domain restrictions
        if self.allowed_domains and parsed.netloc:
            if parsed.netloc not in self.allowed_domains:
                errors.append(ValidationError(
                    field="",
                    error_type=ValidationErrorType.INVALID_URL,
                    message=f"Domain '{parsed.netloc}' is not allowed"
                ))

        # Security checks
        if any(char in value for char in ['<', '>', '"', "'", '&', '\\', ';', '|', '`', '$']):
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.MALICIOUS_CONTENT,
                message="URL contains potentially malicious characters"
            ))

        # Check for common URL attacks
        malicious_patterns = [
            r"javascript:",
            r"vbscript:",
            r"data:",
            r"file:",
            r"ftp:",
            r"mailto:",
            r"tel:",
            r"sms:",
            r"about:",
            r"chrome:",
            r"edge:",
            r"safari:",
            r"moz-extension:",
            r"ms-browser-extension:",
        ]

        for pattern in malicious_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                errors.append(ValidationError(
                    field="",
                    error_type=ValidationErrorType.MALICIOUS_CONTENT,
                    message="URL contains potentially malicious protocol"
                ))

        return len(errors) == 0, errors

    def sanitize(self, value: str) -> str:
        """Sanitize URL"""
        if not isinstance(value, str):
            return ""

        value = value.strip()
        # Remove potentially dangerous characters
        value = re.sub(r'[<>"\'&\\|`$]', '', value)
        return value

class NumberValidator(InputValidator):
    """Number validator with range checking"""

    def __init__(self, min_value: Optional[Union[int, float]] = None, max_value: Optional[Union[int, float]] = None):
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Union[int, float, str]) -> Tuple[bool, List[ValidationError]]:
        """Validate number"""
        errors = []

        # Try to convert to number
        try:
            if isinstance(value, str):
                value = value.strip()
                if '.' in value:
                    num_value = float(value)
                else:
                    num_value = int(value)
            else:
                num_value = value
        except (ValueError, TypeError):
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message="Value must be a valid number"
            ))
            return False, errors

        # Check range
        if self.min_value is not None and num_value < self.min_value:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_RANGE,
                message=f"Value must be at least {self.min_value}"
            ))

        if self.max_value is not None and num_value > self.max_value:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_RANGE,
                message=f"Value must be no more than {self.max_value}"
            ))

        return len(errors) == 0, errors

    def sanitize(self, value: Union[int, float, str]) -> Union[int, float]:
        """Sanitize number"""
        try:
            if isinstance(value, str):
                value = value.strip()
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            return value
        except (ValueError, TypeError):
            return 0

class IPAddressValidator(InputValidator):
    """IP address validator"""

    def __init__(self, allow_private: bool = True, allow_reserved: bool = False):
        self.allow_private = allow_private
        self.allow_reserved = allow_reserved

    def validate(self, value: str) -> Tuple[bool, List[ValidationError]]:
        """Validate IP address"""
        errors = []

        if not isinstance(value, str):
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message="IP address must be a string"
            ))
            return False, errors

        value = value.strip()

        try:
            ip = ipaddress.ip_address(value)
        except ValueError:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_IP,
                message="Invalid IP address format"
            ))
            return False, errors

        # Check private addresses
        if not self.allow_private and ip.is_private:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_IP,
                message="Private IP addresses are not allowed"
            ))

        # Check reserved addresses
        if not self.allow_reserved and ip.is_reserved:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_IP,
                message="Reserved IP addresses are not allowed"
            ))

        return len(errors) == 0, errors

    def sanitize(self, value: str) -> str:
        """Sanitize IP address"""
        if not isinstance(value, str):
            return ""
        return value.strip()

class JSONValidator(InputValidator):
    """JSON validator with security checks"""

    def __init__(self, max_depth: int = 10, max_size: int = 1024 * 1024):  # 1MB
        self.max_depth = max_depth
        self.max_size = max_size

    def validate(self, value: str) -> Tuple[bool, List[ValidationError]]:
        """Validate JSON"""
        errors = []

        if not isinstance(value, str):
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message="JSON must be a string"
            ))
            return False, errors

        # Check size
        if len(value) > self.max_size:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.TOO_LONG,
                message=f"JSON must be no more than {self.max_size} bytes"
            ))

        # Try to parse JSON
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as e:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message=f"Invalid JSON format: {str(e)}"
            ))
            return False, errors

        # Check depth
        if self._check_depth(parsed) > self.max_depth:
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message=f"JSON depth exceeds maximum of {self.max_depth}"
            ))

        # Check for dangerous content
        dangerous_keys = ['__proto__', 'constructor', 'prototype', '__defineGetter__', '__defineSetter__']
        if self._check_dangerous_keys(parsed, dangerous_keys):
            errors.append(ValidationError(
                field="",
                error_type=ValidationErrorType.MALICIOUS_CONTENT,
                message="JSON contains potentially dangerous keys"
            ))

        return len(errors) == 0, errors

    def _check_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Recursively check JSON depth"""
        if current_depth > self.max_depth:
            return current_depth

        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._check_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._check_depth(v, current_depth + 1) for v in obj)

        return current_depth

    def _check_dangerous_keys(self, obj: Any, dangerous_keys: List[str]) -> bool:
        """Check for dangerous keys in JSON"""
        if isinstance(obj, dict):
            for key in obj.keys():
                if key in dangerous_keys:
                    return True
                if self._check_dangerous_keys(obj[key], dangerous_keys):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if self._check_dangerous_keys(item, dangerous_keys):
                    return True

        return False

    def sanitize(self, value: str) -> str:
        """Sanitize JSON"""
        if not isinstance(value, str):
            return ""

        try:
            # Parse and re-serialize to remove any malformed parts
            parsed = json.loads(value)
            return json.dumps(parsed)
        except json.JSONDecodeError:
            return ""

class InputValidationService:
    """Service for managing input validation"""

    def __init__(self):
        self.validators = {
            'username': StringValidator(min_length=3, max_length=50, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'),
            'email': EmailValidator(),
            'password': StringValidator(min_length=8, max_length=128, forbidden_chars='<>"\'&\\'),
            'url': URLValidator(),
            'ip_address': IPAddressValidator(),
            'json': JSONValidator(),
            'number': NumberValidator(),
            'symbol': StringValidator(min_length=6, max_length=20, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789'),
            'description': StringValidator(min_length=0, max_length=1000, allow_html=False),
            'api_key': StringValidator(min_length=16, max_length=128, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'),
        }

    def register_validator(self, name: str, validator: InputValidator):
        """Register a custom validator"""
        self.validators[name] = validator

    def validate_field(self, field_name: str, value: Any, validator_name: Optional[str] = None) -> Tuple[bool, List[ValidationError]]:
        """Validate a single field"""
        validator_name = validator_name or field_name
        validator = self.validators.get(validator_name)

        if not validator:
            # Default validation
            if isinstance(value, str):
                validator = StringValidator()
            elif isinstance(value, (int, float)):
                validator = NumberValidator()
            else:
                return True, []  # Allow unknown types by default

        return validator.validate(value)

    def validate_data(self, data: Dict[str, Any], validation_rules: Dict[str, str]) -> List[ValidationError]:
        """Validate multiple fields"""
        errors = []

        for field_name, value in data.items():
            validator_name = validation_rules.get(field_name, field_name)
            is_valid, field_errors = self.validate_field(field_name, value, validator_name)

            if not is_valid:
                errors.extend(field_errors)

        return errors

    def sanitize_field(self, field_name: str, value: Any, validator_name: Optional[str] = None) -> Any:
        """Sanitize a single field"""
        validator_name = validator_name or field_name
        validator = self.validators.get(validator_name)

        if validator:
            return validator.sanitize(value)

        return value

    def sanitize_data(self, data: Dict[str, Any], validation_rules: Dict[str, str]) -> Dict[str, Any]:
        """Sanitize multiple fields"""
        sanitized = {}

        for field_name, value in data.items():
            validator_name = validation_rules.get(field_name, field_name)
            sanitized[field_name] = self.sanitize_field(field_name, value, validator_name)

        return sanitized

def create_validation_decorator(validation_service: InputValidationService, validation_rules: Dict[str, str]):
    """Create a decorator for input validation"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Validate input data
            errors = validation_service.validate_data(kwargs, validation_rules)

            if errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Validation failed",
                        "validation_errors": [
                            {
                                "field": error.field,
                                "type": error.error_type.value,
                                "message": error.message
                            }
                            for error in errors
                        ]
                    }
                )

            # Sanitize input data
            sanitized_kwargs = validation_service.sanitize_data(kwargs, validation_rules)

            return func(*args, **sanitized_kwargs)
        return wrapper
    return decorator

# Global validation service instance
validation_service = InputValidationService()

# Common validation rules
COMMON_VALIDATION_RULES = {
    'username': 'username',
    'email': 'email',
    'password': 'password',
    'full_name': 'description',
    'symbol': 'symbol',
    'description': 'description',
}

# Create decorator for common use
validate_common_input = create_validation_decorator(validation_service, COMMON_VALIDATION_RULES)

# Security validation middleware
class SecurityValidationMiddleware:
    """Middleware for automatic input validation"""

    def __init__(self, validation_service: InputValidationService):
        self.validation_service = validation_service

    async def __call__(self, request, call_next):
        # Validate query parameters
        for key, value in request.query_params.items():
            is_valid, errors = self.validation_service.validate_field(key, value)
            if not is_valid:
                logger.warning(f"Invalid query parameter '{key}': {errors[0].message}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid query parameter '{key}': {errors[0].message}"
                )

        # For POST/PUT/PATCH requests, validate body
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                for key, value in body.items():
                    is_valid, errors = self.validation_service.validate_field(key, value)
                    if not is_valid:
                        logger.warning(f"Invalid body field '{key}': {errors[0].message}")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid field '{key}': {errors[0].message}"
                        )
            except Exception:
                # If JSON parsing fails, let the request continue - other middleware will handle it
                pass

        response = await call_next(request)
        return response

def validate_trading_symbol(symbol: str) -> bool:
    """Validate trading symbol format"""
    if not isinstance(symbol, str):
        return False

    symbol = symbol.upper().strip()

    # Common forex symbol patterns
    forex_pattern = r'^[A-Z]{6}$'  # 6 characters for major pairs
    metals_pattern = r'^[A-Z]{3}(XAU|XAG|XPD|XPT)$'  # Gold, Silver, etc.
    indices_pattern = r'^[A-Z]{2,4}_IND$'  # Stock indices

    return (re.match(forex_pattern, symbol) or
            re.match(metals_pattern, symbol) or
            re.match(indices_pattern, symbol))

def sanitize_trading_symbol(symbol: str) -> str:
    """Sanitize trading symbol"""
    if not isinstance(symbol, str):
        return ""

    symbol = symbol.upper().strip()
    # Remove any non-alphanumeric characters except underscore
    symbol = re.sub(r'[^A-Z0-9_]', '', symbol)

    return symbol

def validate_price(price: Union[str, float, int]) -> bool:
    """Validate price input"""
    try:
        price_float = float(price)
        return price_float > 0 and price_float <= 1000000  # Reasonable price range
    except (ValueError, TypeError):
        return False

def sanitize_price(price: Union[str, float, int]) -> float:
    """Sanitize price input"""
    try:
        price_float = float(price)
        return max(0.0, min(1000000.0, price_float))
    except (ValueError, TypeError):
        return 0.0
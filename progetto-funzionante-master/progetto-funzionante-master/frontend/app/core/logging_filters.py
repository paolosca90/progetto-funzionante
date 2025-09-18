"""
Advanced Log Filtering and Level Management
Provides sophisticated filtering capabilities for log entries with regex patterns,
conditional logic, and performance optimization.
"""

import re
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import fnmatch
import threading

from .logging_config import LogLevel, get_logging_config


class FilterOperator(Enum):
    """Filter operators for log filtering"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "ge"
    LESS_EQUAL = "le"
    IN = "in"
    NOT_IN = "not_in"


class FilterLogic(Enum):
    """Logic operators for combining filters"""
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class LogFilter:
    """Individual log filter"""
    field: str
    operator: FilterOperator
    value: Any
    case_sensitive: bool = False

    def matches(self, log_entry: Dict[str, Any]) -> bool:
        """Check if log entry matches this filter"""
        field_value = self._get_field_value(log_entry, self.field)

        if field_value is None:
            return False

        # Convert to string for text operations
        if isinstance(field_value, str) and not isinstance(self.value, (int, float, bool)):
            if not self.case_sensitive:
                field_value = field_value.lower()
                compare_value = str(self.value).lower()
            else:
                compare_value = str(self.value)
        else:
            compare_value = self.value

        # Apply operator
        if self.operator == FilterOperator.EQUALS:
            return field_value == compare_value
        elif self.operator == FilterOperator.NOT_EQUALS:
            return field_value != compare_value
        elif self.operator == FilterOperator.CONTAINS:
            return compare_value in str(field_value)
        elif self.operator == FilterOperator.NOT_CONTAINS:
            return compare_value not in str(field_value)
        elif self.operator == FilterOperator.STARTS_WITH:
            return str(field_value).startswith(str(compare_value))
        elif self.operator == FilterOperator.ENDS_WITH:
            return str(field_value).endswith(str(compare_value))
        elif self.operator == FilterOperator.REGEX:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            return bool(re.search(str(compare_value), str(field_value), flags))
        elif self.operator == FilterOperator.GREATER_THAN:
            return float(field_value) > float(compare_value)
        elif self.operator == FilterOperator.LESS_THAN:
            return float(field_value) < float(compare_value)
        elif self.operator == FilterOperator.GREATER_EQUAL:
            return float(field_value) >= float(compare_value)
        elif self.operator == FilterOperator.LESS_EQUAL:
            return float(field_value) <= float(compare_value)
        elif self.operator == FilterOperator.IN:
            return field_value in compare_value
        elif self.operator == FilterOperator.NOT_IN:
            return field_value not in compare_value

        return False

    def _get_field_value(self, log_entry: Dict[str, Any], field: str) -> Any:
        """Get field value from log entry using dot notation"""
        if '.' in field:
            # Nested field access
            parts = field.split('.')
            value = log_entry
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        else:
            return log_entry.get(field)


@dataclass
class FilterGroup:
    """Group of filters with logic"""
    logic: FilterLogic
    filters: List[Union['LogFilter', 'FilterGroup']]

    def matches(self, log_entry: Dict[str, Any]) -> bool:
        """Check if log entry matches this filter group"""
        if not self.filters:
            return True

        if self.logic == FilterLogic.AND:
            return all(f.matches(log_entry) for f in self.filters)
        elif self.logic == FilterLogic.OR:
            return any(f.matches(log_entry) for f in self.filters)
        elif self.logic == FilterLogic.NOT:
            return not any(f.matches(log_entry) for f in self.filters)

        return False


class LogLevelFilter(logging.Filter):
    """Custom log level filter"""

    def __init__(self, min_level: LogLevel, max_level: LogLevel = LogLevel.CRITICAL):
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level
        self.level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records by level"""
        record_level = LogLevel(record.levelname)
        min_order = self.level_order[self.min_level]
        max_order = self.level_order[self.max_level]
        record_order = self.level_order[record_level]

        return min_order <= record_order <= max_order


class ModuleFilter(logging.Filter):
    """Filter by module name"""

    def __init__(self, include_modules: List[str] = None, exclude_modules: List[str] = None):
        super().__init__()
        self.include_modules = include_modules or []
        self.exclude_modules = exclude_modules or []

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records by module"""
        if self.include_modules and not any(
            fnmatch.fnmatch(record.name, pattern) for pattern in self.include_modules
        ):
            return False

        if self.exclude_modules and any(
            fnmatch.fnmatch(record.name, pattern) for pattern in self.exclude_modules
        ):
            return False

        return True


class TimeRangeFilter(logging.Filter):
    """Filter by time range"""

    def __init__(self, start_time: datetime = None, end_time: datetime = None):
        super().__init__()
        self.start_time = start_time
        self.end_time = end_time

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records by time range"""
        record_time = datetime.fromtimestamp(record.created)

        if self.start_time and record_time < self.start_time:
            return False

        if self.end_time and record_time > self.end_time:
            return False

        return True


class PerformanceFilter(logging.Filter):
    """Filter by performance metrics"""

    def __init__(self, min_duration: float = None, max_duration: float = None,
                 slow_threshold: float = None):
        super().__init__()
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.slow_threshold = slow_threshold

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records by performance metrics"""
        duration = getattr(record, 'duration', None)

        if duration is None:
            return True

        if self.min_duration is not None and duration < self.min_duration:
            return False

        if self.max_duration is not None and duration > self.max_duration:
            return False

        if self.slow_threshold is not None and duration >= self.slow_threshold:
            return True

        return True


class ContextFilter(logging.Filter):
    """Filter by context fields"""

    def __init__(self, context_filters: Dict[str, Any] = None):
        super().__init__()
        self.context_filters = context_filters or {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records by context fields"""
        for field, expected_value in self.context_filters.items():
            actual_value = getattr(record, field, None)

            if actual_value != expected_value:
                return False

        return True


class RateLimitFilter(logging.Filter):
    """Rate limiting filter to prevent log spam"""

    def __init__(self, max_logs_per_minute: int = 100, reset_interval: int = 60):
        super().__init__()
        self.max_logs_per_minute = max_logs_per_minute
        self.reset_interval = reset_interval
        self.log_counts = {}
        self.last_reset = time.time()
        self._lock = threading.Lock()

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records by rate limit"""
        current_time = time.time()

        # Reset counters if interval has passed
        with self._lock:
            if current_time - self.last_reset > self.reset_interval:
                self.log_counts.clear()
                self.last_reset = current_time

            # Get logger name for rate limiting
            logger_key = record.name
            current_count = self.log_counts.get(logger_key, 0)

            if current_count >= self.max_logs_per_minute:
                return False

            self.log_counts[logger_key] = current_count + 1

        return True


class DuplicateFilter(logging.Filter):
    """Filter out duplicate log messages"""

    def __init__(self, time_window: int = 60, max_duplicates: int = 3):
        super().__init__()
        self.time_window = time_window
        self.max_duplicates = max_duplicates
        self.message_history = {}
        self._lock = threading.Lock()

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out duplicate log messages"""
        current_time = time.time()
        message_key = (record.name, record.levelname, record.getMessage())

        with self._lock:
            # Clean old entries
            cutoff_time = current_time - self.time_window
            self.message_history = {
                key: (timestamp, count) for key, (timestamp, count) in self.message_history.items()
                if timestamp > cutoff_time
            }

            # Check message history
            if message_key in self.message_history:
                timestamp, count = self.message_history[message_key]
                if count >= self.max_duplicates:
                    return False
                self.message_history[message_key] = (current_time, count + 1)
            else:
                self.message_history[message_key] = (current_time, 1)

        return True


class ErrorPatternFilter(logging.Filter):
    """Filter based on error patterns"""

    def __init__(self, error_patterns: List[str] = None, exclude_patterns: List[str] = None):
        super().__init__()
        self.error_patterns = [re.compile(pattern) for pattern in error_patterns or []]
        self.exclude_patterns = [re.compile(pattern) for pattern in exclude_patterns or []]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records by error patterns"""
        if record.levelno < logging.ERROR:
            return True

        message = record.getMessage()

        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if pattern.search(message):
                return False

        # Check error patterns
        if self.error_patterns:
            return any(pattern.search(message) for pattern in self.error_patterns)

        return True


class LogFilterManager:
    """Manages multiple log filters and provides filtering capabilities"""

    def __init__(self):
        self.filters: List[logging.Filter] = []
        self.filter_groups: List[FilterGroup] = []
        self._lock = threading.Lock()

    def add_filter(self, filter_instance: logging.Filter) -> None:
        """Add a filter to the manager"""
        with self._lock:
            self.filters.append(filter_instance)

    def remove_filter(self, filter_instance: logging.Filter) -> None:
        """Remove a filter from the manager"""
        with self._lock:
            if filter_instance in self.filters:
                self.filters.remove(filter_instance)

    def add_filter_group(self, filter_group: FilterGroup) -> None:
        """Add a filter group to the manager"""
        with self._lock:
            self.filter_groups.append(filter_group)

    def remove_filter_group(self, filter_group: FilterGroup) -> None:
        """Remove a filter group from the manager"""
        with self._lock:
            if filter_group in self.filter_groups:
                self.filter_groups.remove(filter_group)

    def apply_filters(self, logger: logging.Logger) -> None:
        """Apply all filters to a logger"""
        with self._lock:
            for filter_instance in self.filters:
                logger.addFilter(filter_instance)

    def remove_filters(self, logger: logging.Logger) -> None:
        """Remove all filters from a logger"""
        with self._lock:
            for filter_instance in self.filters:
                logger.removeFilter(filter_instance)

    def matches_all_filters(self, record: logging.LogRecord) -> bool:
        """Check if record matches all configured filters"""
        with self._lock:
            for filter_instance in self.filters:
                if not filter_instance.filter(record):
                    return False

            # Check filter groups
            for filter_group in self.filter_groups:
                # Convert record to dict for filter group matching
                log_dict = self._record_to_dict(record)
                if not filter_group.matches(log_dict):
                    return False

            return True

    def _record_to_dict(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Convert log record to dictionary"""
        return {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger_name': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread_id': record.thread,
            'process_id': record.process
        }

    def create_level_filter(self, min_level: LogLevel, max_level: LogLevel = None) -> LogLevelFilter:
        """Create a level filter"""
        return LogLevelFilter(min_level, max_level or LogLevel.CRITICAL)

    def create_module_filter(self, include_modules: List[str] = None, exclude_modules: List[str] = None) -> ModuleFilter:
        """Create a module filter"""
        return ModuleFilter(include_modules, exclude_modules)

    def create_time_range_filter(self, start_time: datetime = None, end_time: datetime = None) -> TimeRangeFilter:
        """Create a time range filter"""
        return TimeRangeFilter(start_time, end_time)

    def create_performance_filter(self, min_duration: float = None, max_duration: float = None,
                                 slow_threshold: float = None) -> PerformanceFilter:
        """Create a performance filter"""
        return PerformanceFilter(min_duration, max_duration, slow_threshold)

    def create_context_filter(self, context_filters: Dict[str, Any] = None) -> ContextFilter:
        """Create a context filter"""
        return ContextFilter(context_filters)

    def create_rate_limit_filter(self, max_logs_per_minute: int = 100) -> RateLimitFilter:
        """Create a rate limit filter"""
        return RateLimitFilter(max_logs_per_minute)

    def create_duplicate_filter(self, time_window: int = 60, max_duplicates: int = 3) -> DuplicateFilter:
        """Create a duplicate filter"""
        return DuplicateFilter(time_window, max_duplicates)

    def create_error_pattern_filter(self, error_patterns: List[str] = None, exclude_patterns: List[str] = None) -> ErrorPatternFilter:
        """Create an error pattern filter"""
        return ErrorPatternFilter(error_patterns, exclude_patterns)

    def create_filter_from_config(self) -> None:
        """Create filters from configuration"""
        config = get_logging_config()

        # Add level filter
        if config.filtering.enabled:
            level_filter = self.create_level_filter(config.filtering.min_level, config.filtering.max_level)
            self.add_filter(level_filter)

        # Add module filter
        if config.filtering.include_modules or config.filtering.exclude_modules:
            module_filter = self.create_module_filter(config.filtering.include_modules, config.filtering.exclude_modules)
            self.add_filter(module_filter)

        # Add performance filter
        if config.performance.enabled:
            perf_filter = self.create_performance_filter(
                slow_threshold=config.performance.slow_request_threshold
            )
            self.add_filter(perf_filter)

        # Add rate limit filter
        rate_limit_filter = self.create_rate_limit_filter(1000)  # 1000 logs per minute max
        self.add_filter(rate_limit_filter)

        # Add duplicate filter
        duplicate_filter = self.create_duplicate_filter(60, 5)  # 5 duplicates per minute
        self.add_filter(duplicate_filter)


# Global filter manager instance
filter_manager = LogFilterManager()


def get_filter_manager() -> LogFilterManager:
    """Get the global filter manager"""
    return filter_manager


def setup_logging_filters(logger: logging.Logger) -> None:
    """Setup logging filters for a logger"""
    filter_manager.apply_filters(logger)


def create_log_filter(field: str, operator: str, value: Any, case_sensitive: bool = False) -> LogFilter:
    """Create a single log filter"""
    return LogFilter(field, FilterOperator(operator), value, case_sensitive)


def create_filter_group(logic: str, filters: List[Union[LogFilter, 'FilterGroup']]) -> FilterGroup:
    """Create a filter group"""
    return FilterGroup(FilterLogic(logic), filters)


def filter_logs(log_entries: List[Dict[str, Any]], filter_group: FilterGroup) -> List[Dict[str, Any]]:
    """Filter a list of log entries"""
    return [entry for entry in log_entries if filter_group.matches(entry)]
"""
Async Task Scheduler and Concurrency Controller
Implements high-performance task scheduling with resource management,
priority queues, rate limiting, and comprehensive monitoring.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import heapq
from contextlib import asynccontextmanager
import uuid
from datetime import datetime, timedelta
import traceback

from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    TIMEOUT = "timeout"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5

class TaskType(Enum):
    """Task types for categorization"""
    DATABASE = "database"
    HTTP_REQUEST = "http_request"
    FILE_OPERATION = "file_operation"
    CACHE_OPERATION = "cache_operation"
    EXTERNAL_API = "external_api"
    BACKGROUND_JOB = "background_job"
    SCHEDULED_TASK = "scheduled_task"

@dataclass
class TaskResult:
    """Result of task execution"""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    retry_count: int = 0
    task_id: Optional[str] = None

@dataclass
class Task:
    """Task definition with metadata"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    task_type: TaskType = TaskType.BACKGROUND_JOB
    status: TaskStatus = TaskStatus.PENDING
    max_retries: int = 3
    timeout: Optional[float] = None
    retry_delay: float = 1.0
    created_at: float = field(default_factory=time.time)
    scheduled_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retry_count: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        """For priority queue comparison"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at

@dataclass
class ResourceLimit:
    """Resource limit configuration"""
    max_concurrent_tasks: int = 100
    max_tasks_per_type: Dict[TaskType, int] = field(default_factory=dict)
    max_tasks_per_priority: Dict[TaskPriority, int] = field(default_factory=dict)
    rate_limit_per_second: float = 100.0
    memory_limit_mb: Optional[int] = None

@dataclass
class SchedulerMetrics:
    """Scheduler performance metrics"""
    total_tasks_submitted: int = 0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    total_tasks_cancelled: int = 0
    total_retries: int = 0
    average_execution_time: float = 0.0
    current_running_tasks: int = 0
    current_pending_tasks: int = 0
    peak_concurrent_tasks: int = 0
    throughput_per_minute: float = 0.0
    last_minute_completions: deque = field(default_factory=lambda: deque(maxlen=60))

class AsyncTaskScheduler:
    """
    High-performance async task scheduler with features:
    - Priority-based task scheduling
    - Resource limiting and rate limiting
    - Task retry with exponential backoff
    - Task cancellation and timeout handling
    - Comprehensive metrics and monitoring
    - Scheduled task execution
    - Task dependencies
    """

    def __init__(self, resource_limits: Optional[ResourceLimit] = None):
        self.resource_limits = resource_limits or ResourceLimit()
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.scheduled_tasks: Dict[float, List[Task]] = defaultdict(list)
        self.task_dependencies: Dict[str, List[str]] = defaultdict(list)
        self.task_lock = asyncio.Lock()
        self.metrics = SchedulerMetrics()
        self._scheduler_task: Optional[asyncio.Task] = None
        self._scheduler_running = False
        self._rate_limiter = asyncio.Semaphore(int(self.resource_limits.rate_limit_per_second))
        self._resource_semaphores: Dict[TaskType, asyncio.Semaphore] = {}
        self._shutdown_event = asyncio.Event()

        # Initialize resource semaphores
        self._initialize_semaphores()

    def _initialize_semaphores(self):
        """Initialize resource limiting semaphores"""
        # Default limits per task type
        default_limits = {
            TaskType.DATABASE: 20,
            TaskType.HTTP_REQUEST: 50,
            TaskType.FILE_OPERATION: 10,
            TaskType.CACHE_OPERATION: 100,
            TaskType.EXTERNAL_API: 30,
            TaskType.BACKGROUND_JOB: 50,
            TaskType.SCHEDULED_TASK: 20
        }

        for task_type, limit in default_limits.items():
            actual_limit = self.resource_limits.max_tasks_per_type.get(task_type, limit)
            self._resource_semaphores[task_type] = asyncio.Semaphore(actual_limit)

    async def submit_task(
        self,
        func: Callable,
        *args,
        name: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_type: TaskType = TaskType.BACKGROUND_JOB,
        max_retries: int = 3,
        timeout: Optional[float] = None,
        retry_delay: float = 1.0,
        scheduled_at: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for execution

        Args:
            func: Async function to execute
            *args: Function arguments
            name: Task name (optional)
            priority: Task priority
            task_type: Task type for resource limiting
            max_retries: Maximum retry attempts
            timeout: Task timeout in seconds
            retry_delay: Delay between retries
            scheduled_at: Unix timestamp for scheduled execution
            tags: Task tags for grouping
            metadata: Additional task metadata
            dependencies: List of task IDs this task depends on
            **kwargs: Function keyword arguments

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            task_type=task_type,
            max_retries=max_retries,
            timeout=timeout,
            retry_delay=retry_delay,
            scheduled_at=scheduled_at,
            tags=tags or [],
            metadata=metadata or {}
        )

        async with self.task_lock:
            self.tasks[task_id] = task

            # Add dependencies
            if dependencies:
                self.task_dependencies[task_id] = dependencies

            # Schedule task for execution
            if scheduled_at and scheduled_at > time.time():
                self.scheduled_tasks[scheduled_at].append(task)
                logger.info(f"Scheduled task {task_id} for execution at {datetime.fromtimestamp(scheduled_at)}")
            else:
                heapq.heappush(self.task_queue, task)
                logger.debug(f"Task {task_id} queued for execution")

            self.metrics.total_tasks_submitted += 1
            self.metrics.current_pending_tasks += 1

        # Start scheduler if not running
        if not self._scheduler_running:
            asyncio.create_task(self.start_scheduler())

        return task_id

    async def start_scheduler(self):
        """Start the task scheduler"""
        if self._scheduler_running:
            return

        self._scheduler_running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Task scheduler started")

    async def stop_scheduler(self):
        """Stop the task scheduler gracefully"""
        if not self._scheduler_running:
            return

        self._shutdown_event.set()
        self._scheduler_running = False

        if self._scheduler_task:
            await self._scheduler_task

        logger.info("Task scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self._scheduler_running and not self._shutdown_event.is_set():
            try:
                # Check for scheduled tasks
                await self._check_scheduled_tasks()

                # Process queued tasks
                if self.task_queue and len(self.running_tasks) < self.resource_limits.max_concurrent_tasks:
                    await self._process_next_task()

                # Update metrics
                self._update_metrics()

                # Clean up completed tasks
                await self._cleanup_completed_tasks()

                # Sleep briefly to prevent CPU spinning
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(0.1)

    async def _check_scheduled_tasks(self):
        """Check and execute scheduled tasks"""
        current_time = time.time()

        # Get all tasks scheduled for now or earlier
        scheduled_times = [t for t in self.scheduled_tasks.keys() if t <= current_time]
        scheduled_times.sort()

        for scheduled_time in scheduled_times:
            tasks = self.scheduled_tasks.pop(scheduled_time, [])
            for task in tasks:
                heapq.heappush(self.task_queue, task)
                logger.debug(f"Scheduled task {task.id} moved to execution queue")

    async def _process_next_task(self):
        """Process the next task from the queue"""
        if not self.task_queue:
            return

        async with self.task_lock:
            if not self.task_queue:
                return

            task = heapq.heappop(self.task_queue)

            # Check dependencies
            if await self._check_dependencies(task):
                # Execute task
                execution_task = asyncio.create_task(self._execute_task(task))
                self.running_tasks[task.id] = execution_task
                self.metrics.current_pending_tasks -= 1
                self.metrics.current_running_tasks += 1
                self.metrics.peak_concurrent_tasks = max(
                    self.metrics.peak_concurrent_tasks,
                    self.metrics.current_running_tasks
                )
            else:
                # Re-queue task with lower priority
                task.priority = TaskPriority.LOW
                heapq.heappush(self.task_queue, task)

    async def _check_dependencies(self, task: Task) -> bool:
        """Check if task dependencies are satisfied"""
        dependencies = self.task_dependencies.get(task.id, [])
        if not dependencies:
            return True

        for dep_id in dependencies:
            if dep_id not in self.completed_tasks:
                return False

            dep_result = self.completed_tasks[dep_id]
            if not dep_result.success:
                logger.warning(f"Task {task.id} dependency {dep_id} failed")
                return False

        return True

    async def _execute_task(self, task: Task):
        """Execute a single task"""
        try:
            # Acquire rate limiter
            async with self._rate_limiter:
                # Acquire resource semaphore
                resource_semaphore = self._resource_semaphores.get(task.task_type)
                if resource_semaphore:
                    async with resource_semaphore:
                        await self._run_task(task)
                else:
                    await self._run_task(task)

        except Exception as e:
            logger.error(f"Task execution error for {task.id}: {e}")
            await self._handle_task_failure(task, e)

        finally:
            # Clean up running task
            self.running_tasks.pop(task.id, None)
            self.metrics.current_running_tasks -= 1

    async def _run_task(self, task: Task):
        """Run the actual task with timeout and error handling"""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()

        try:
            # Execute with timeout if specified
            if task.timeout:
                result = await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                result = await task.func(*task.args, **task.kwargs)

            # Task completed successfully
            task.completed_at = time.time()
            task.status = TaskStatus.COMPLETED

            execution_time = task.completed_at - task.started_at
            task_result = TaskResult(
                success=True,
                result=result,
                execution_time=execution_time,
                retry_count=task.retry_count,
                task_id=task.id
            )

            self.completed_tasks[task.id] = task_result
            self.metrics.total_tasks_completed += 1
            self.metrics.last_minute_completions.append(time.time())

            logger.debug(f"Task {task.id} completed successfully in {execution_time:.3f}s")

        except asyncio.TimeoutError:
            await self._handle_task_timeout(task)
        except Exception as e:
            await self._handle_task_failure(task, e)

    async def _handle_task_timeout(self, task: Task):
        """Handle task timeout"""
        task.status = TaskStatus.TIMEOUT
        task.completed_at = time.time()

        execution_time = task.completed_at - task.started_at
        task_result = TaskResult(
            success=False,
            error=TimeoutError(f"Task {task.id} timed out after {task.timeout}s"),
            execution_time=execution_time,
            retry_count=task.retry_count,
            task_id=task.id
        )

        self.completed_tasks[task.id] = task_result
        self.metrics.total_tasks_failed += 1

        logger.warning(f"Task {task.id} timed out after {task.timeout}s")

    async def _handle_task_failure(self, task: Task, error: Exception):
        """Handle task failure with retry logic"""
        if task.retry_count < task.max_retries:
            # Retry task
            task.retry_count += 1
            task.status = TaskStatus.RETRYING

            # Exponential backoff
            retry_delay = task.retry_delay * (2 ** (task.retry_count - 1))
            logger.info(f"Retrying task {task.id} (attempt {task.retry_count}/{task.max_retries}) in {retry_delay}s")

            # Schedule retry
            await asyncio.sleep(retry_delay)
            heapq.heappush(self.task_queue, task)
            self.metrics.total_retries += 1
        else:
            # Task failed permanently
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()

            execution_time = task.completed_at - (task.started_at or task.created_at)
            task_result = TaskResult(
                success=False,
                error=error,
                execution_time=execution_time,
                retry_count=task.retry_count,
                task_id=task.id
            )

            self.completed_tasks[task.id] = task_result
            self.metrics.total_tasks_failed += 1

            logger.error(f"Task {task.id} failed permanently: {error}")

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running or pending task"""
        async with self.task_lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            if task.status in [TaskStatus.PENDING, TaskStatus.RETRYING]:
                # Remove from queue
                if task in self.task_queue:
                    self.task_queue.remove(task)
                    heapq.heapify(self.task_queue)
                task.status = TaskStatus.CANCELLED
                task.completed_at = time.time()

                task_result = TaskResult(
                    success=False,
                    error=CancelledError(f"Task {task_id} was cancelled"),
                    execution_time=task.completed_at - task.created_at,
                    retry_count=task.retry_count,
                    task_id=task_id
                )

                self.completed_tasks[task_id] = task_result
                self.metrics.total_tasks_cancelled += 1
                self.metrics.current_pending_tasks -= 1

                return True

            elif task.status == TaskStatus.RUNNING:
                # Cancel running task
                running_task = self.running_tasks.get(task_id)
                if running_task:
                    running_task.cancel()
                    return True

        return False

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and information"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        task_result = self.completed_tasks.get(task_id)

        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "priority": task.priority.value,
            "task_type": task.task_type.value,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "tags": task.tags,
            "result": task_result.__dict__ if task_result else None,
            "dependencies": self.task_dependencies.get(task_id, [])
        }

    async def get_tasks_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get all tasks with a specific tag"""
        tasks = []
        for task in self.tasks.values():
            if tag in task.tags:
                task_info = await self.get_task_status(task.id)
                if task_info:
                    tasks.append(task_info)
        return tasks

    async def get_tasks_by_type(self, task_type: TaskType) -> List[Dict[str, Any]]:
        """Get all tasks of a specific type"""
        tasks = []
        for task in self.tasks.values():
            if task.task_type == task_type:
                task_info = await self.get_task_status(task.id)
                if task_info:
                    tasks.append(task_info)
        return tasks

    def _update_metrics(self):
        """Update scheduler metrics"""
        # Calculate average execution time
        completed_results = [r for r in self.completed_tasks.values() if r.success]
        if completed_results:
            self.metrics.average_execution_time = sum(r.execution_time for r in completed_results) / len(completed_results)

        # Calculate throughput per minute
        current_time = time.time()
        recent_completions = [
            t for t in self.metrics.last_minute_completions
            if current_time - t <= 60
        ]
        self.metrics.throughput_per_minute = len(recent_completions)

    async def _cleanup_completed_tasks(self):
        """Clean up old completed tasks"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # Keep tasks for 1 hour

        tasks_to_remove = []
        for task_id, result in self.completed_tasks.items():
            task = self.tasks.get(task_id)
            if task and task.completed_at and task.completed_at < cutoff_time:
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            self.completed_tasks.pop(task_id, None)
            self.tasks.pop(task_id, None)
            self.task_dependencies.pop(task_id, None)

    def get_metrics(self) -> Dict[str, Any]:
        """Get scheduler metrics"""
        return {
            "total_tasks_submitted": self.metrics.total_tasks_submitted,
            "total_tasks_completed": self.metrics.total_tasks_completed,
            "total_tasks_failed": self.metrics.total_tasks_failed,
            "total_tasks_cancelled": self.metrics.total_tasks_cancelled,
            "total_retries": self.metrics.total_retries,
            "success_rate": (
                (self.metrics.total_tasks_completed / max(1, self.metrics.total_tasks_submitted)) * 100
            ),
            "average_execution_time": self.metrics.average_execution_time,
            "current_running_tasks": self.metrics.current_running_tasks,
            "current_pending_tasks": self.metrics.current_pending_tasks,
            "peak_concurrent_tasks": self.metrics.peak_concurrent_tasks,
            "throughput_per_minute": self.metrics.throughput_per_minute,
            "resource_limits": {
                "max_concurrent_tasks": self.resource_limits.max_concurrent_tasks,
                "max_tasks_per_type": self.resource_limits.max_tasks_per_type,
                "rate_limit_per_second": self.resource_limits.rate_limit_per_second
            }
        }

    def reset_metrics(self):
        """Reset scheduler metrics"""
        self.metrics = SchedulerMetrics()

    @asynccontextmanager
    async def task_context(self, task_id: str):
        """Context manager for task execution"""
        try:
            yield
        except Exception as e:
            logger.error(f"Task context error for {task_id}: {e}")
            raise

    async def shutdown(self):
        """Graceful shutdown"""
        await self.stop_scheduler()

        # Cancel all running tasks
        for task_id, running_task in self.running_tasks.items():
            running_task.cancel()
            logger.info(f"Cancelled running task {task_id}")

        # Wait for tasks to complete
        if self.running_tasks:
            await asyncio.sleep(1)  # Give tasks time to cancel

        logger.info("Task scheduler shutdown complete")

# Global task scheduler instance
task_scheduler = AsyncTaskScheduler()

# Convenience functions
async def submit_task(
    func: Callable,
    *args,
    name: Optional[str] = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    task_type: TaskType = TaskType.BACKGROUND_JOB,
    **kwargs
) -> str:
    """Convenience function to submit a task"""
    return await task_scheduler.submit_task(
        func, *args,
        name=name,
        priority=priority,
        task_type=task_type,
        **kwargs
    )

async def schedule_task(
    func: Callable,
    delay_seconds: float,
    *args,
    name: Optional[str] = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    **kwargs
) -> str:
    """Convenience function to schedule a delayed task"""
    scheduled_at = time.time() + delay_seconds
    return await task_scheduler.submit_task(
        func, *args,
        name=name,
        priority=priority,
        scheduled_at=scheduled_at,
        **kwargs
    )

# Initialize function
async def init_task_scheduler():
    """Initialize task scheduler"""
    try:
        await task_scheduler.start_scheduler()
        logger.info("Task scheduler initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize task scheduler: {e}")
        return False

# Cleanup function
async def cleanup_task_scheduler():
    """Cleanup task scheduler"""
    try:
        await task_scheduler.shutdown()
        logger.info("Task scheduler cleaned up successfully")
    except Exception as e:
        logger.error(f"Failed to cleanup task scheduler: {e}")
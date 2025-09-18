"""
Release Tracking and Deployment Monitoring System
Track releases, deployments, and version changes with comprehensive metrics
"""

import os
import subprocess
import json
import hashlib
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
import threading
import time

from app.core.sentry_config import sentry_config, ErrorSeverity, ErrorCategory
from config.settings import settings


@dataclass
class ReleaseInfo:
    """Release information data structure"""
    version: str
    commit_hash: str
    branch: str
    timestamp: str
    author: str
    message: str
    files_changed: int
    insertions: int
    deletions: int
    environment: str
    deployment_status: str = "pending"
    deployment_id: Optional[str] = None
    rollback_available: bool = False
    previous_version: Optional[str] = None


@dataclass
class DeploymentMetrics:
    """Deployment metrics data structure"""
    deployment_id: str
    release_version: str
    environment: str
    start_time: str
    end_time: Optional[str] = None
    duration: Optional[float] = None
    status: str = "in_progress"
    success: bool = False
    error_message: Optional[str] = None
    health_checks_passed: int = 0
    health_checks_total: int = 0
    rollback_triggered: bool = False
    performance_impact: Dict[str, Any] = None


class ReleaseTracker:
    """
    Comprehensive release tracking and deployment monitoring system
    - Git integration for version tracking
    - Deployment health monitoring
    - Rollback capabilities
    - Release metrics and analytics
    """

    def __init__(self):
        self.releases: List[ReleaseInfo] = []
        self.deployments: List[DeploymentMetrics] = []
        self.current_release: Optional[ReleaseInfo] = None
        self.lock = threading.Lock()
        self.health_check_threshold = 300  # 5 minutes

    def initialize(self) -> None:
        """Initialize release tracker"""
        try:
            self._load_current_release()
            self._load_release_history()
            logging.info("Release tracker initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize release tracker: {e}")

    def _load_current_release(self) -> None:
        """Load current release information"""
        try:
            # Get git information
            commit_hash = self._get_git_commit_hash()
            branch = self._get_git_branch()
            author = self._get_git_author()
            message = self._get_git_commit_message()

            # Get file changes
            files_changed, insertions, deletions = self._get_git_diff_stats()

            # Create release info
            self.current_release = ReleaseInfo(
                version=settings.version,
                commit_hash=commit_hash,
                branch=branch,
                timestamp=datetime.now(UTC).isoformat(),
                author=author,
                message=message,
                files_changed=files_changed,
                insertions=insertions,
                deletions=deletions,
                environment=settings.environment.value
            )

            # Set release in Sentry
            if sentry_config.initialized:
                sentry_sdk.set_tag("release_version", self.current_release.version)
                sentry_sdk.set_tag("commit_hash", self.current_release.commit_hash)
                sentry_sdk.set_tag("branch", self.current_release.branch)

        except Exception as e:
            logging.error(f"Failed to load current release: {e}")

    def _get_git_commit_hash(self) -> str:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        return "unknown"

    def _get_git_branch(self) -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        return "unknown"

    def _get_git_author(self) -> str:
        """Get git commit author"""
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%an"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        return "unknown"

    def _get_git_commit_message(self) -> str:
        """Get git commit message"""
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%s"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        return "unknown"

    def _get_git_diff_stats(self) -> tuple[int, int, int]:
        """Get git diff statistics"""
        try:
            result = subprocess.run(
                ["git", "diff", "--shortstat"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                stats = result.stdout.strip()
                if stats:
                    parts = stats.split(", ")
                    files_changed = 0
                    insertions = 0
                    deletions = 0

                    for part in parts:
                        if "file" in part:
                            files_changed = int(part.split()[0])
                        elif "insertion" in part:
                            insertions = int(part.split()[0])
                        elif "deletion" in part:
                            deletions = int(part.split()[0])

                    return files_changed, insertions, deletions
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError, ValueError):
            pass
        return 0, 0, 0

    def _load_release_history(self) -> None:
        """Load release history from git"""
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "50"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # This is a simplified version - in production, you'd want more detailed parsing
                pass
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass

    def start_deployment(self, environment: str = None) -> DeploymentMetrics:
        """Start tracking a new deployment"""
        if not self.current_release:
            raise RuntimeError("No current release information available")

        env = environment or settings.environment.value
        deployment_id = f"deploy_{int(time.time() * 1000)}_{hashlib.md5(env.encode()).hexdigest()[:8]}"

        deployment = DeploymentMetrics(
            deployment_id=deployment_id,
            release_version=self.current_release.version,
            environment=env,
            start_time=datetime.now(UTC).isoformat(),
            status="in_progress"
        )

        with self.lock:
            self.deployments.append(deployment)

        # Notify Sentry
        if sentry_config.initialized:
            sentry_config.capture_message(
                f"Deployment started: {deployment.release_version} to {deployment.environment}",
                level=ErrorSeverity.INFO,
                category=ErrorCategory.SYSTEM,
                tags={
                    "deployment_id": deployment_id,
                    "release_version": deployment.release_version,
                    "environment": deployment.environment,
                    "deployment_status": "started"
                },
                extra_data=asdict(deployment)
            )

        logging.info(f"Deployment started: {deployment_id}")
        return deployment

    def complete_deployment(self, deployment_id: str, success: bool = True, error_message: str = None) -> bool:
        """Complete deployment tracking"""
        with self.lock:
            deployment = next((d for d in self.deployments if d.deployment_id == deployment_id), None)
            if not deployment:
                logging.error(f"Deployment not found: {deployment_id}")
                return False

            deployment.end_time = datetime.now(UTC).isoformat()
            deployment.duration = (
                datetime.fromisoformat(deployment.end_time) -
                datetime.fromisoformat(deployment.start_time)
            ).total_seconds()
            deployment.status = "completed" if success else "failed"
            deployment.success = success
            deployment.error_message = error_message

        # Update release status
        if self.current_release:
            self.current_release.deployment_status = "completed" if success else "failed"
            self.current_release.deployment_id = deployment_id

        # Notify Sentry
        if sentry_config.initialized:
            sentry_config.capture_message(
                f"Deployment {'completed successfully' if success else 'failed'}: {deployment.release_version} to {deployment.environment}",
                level=ErrorSeverity.INFO if success else ErrorSeverity.ERROR,
                category=ErrorCategory.SYSTEM,
                tags={
                    "deployment_id": deployment_id,
                    "release_version": deployment.release_version,
                    "environment": deployment.environment,
                    "deployment_status": "completed" if success else "failed",
                    "deployment_success": str(success).lower()
                },
                extra_data=asdict(deployment)
            )

        logging.info(f"Deployment completed: {deployment_id} - {'Success' if success else 'Failed'}")
        return True

    def update_deployment_health(self, deployment_id: str, checks_passed: int, checks_total: int) -> None:
        """Update deployment health check status"""
        with self.lock:
            deployment = next((d for d in self.deployments if d.deployment_id == deployment_id), None)
            if deployment:
                deployment.health_checks_passed = checks_passed
                deployment.health_checks_total = checks_total

    def trigger_rollback(self, deployment_id: str, reason: str) -> bool:
        """Trigger rollback for a deployment"""
        with self.lock:
            deployment = next((d for d in self.deployments if d.deployment_id == deployment_id), None)
            if not deployment:
                logging.error(f"Deployment not found for rollback: {deployment_id}")
                return False

            deployment.rollback_triggered = True
            deployment.status = "rolled_back"

        # Notify Sentry
        if sentry_config.initialized:
            sentry_config.capture_message(
                f"Rollback triggered for deployment: {deployment.release_version} to {deployment.environment}",
                level=ErrorSeverity.ERROR,
                category=ErrorCategory.SYSTEM,
                tags={
                    "deployment_id": deployment_id,
                    "release_version": deployment.release_version,
                    "environment": deployment.environment,
                    "rollback_reason": reason
                },
                extra_data={"deployment": asdict(deployment), "rollback_reason": reason}
            )

        logging.warning(f"Rollback triggered for deployment: {deployment_id} - {reason}")
        return True

    def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment status"""
        with self.lock:
            deployment = next((d for d in self.deployments if d.deployment_id == deployment_id), None)
            if deployment:
                return asdict(deployment)
            return None

    def get_release_summary(self) -> Dict[str, Any]:
        """Get release and deployment summary"""
        with self.lock:
            recent_deployments = sorted(
                self.deployments,
                key=lambda x: x.start_time,
                reverse=True
            )[:10]

            # Calculate deployment success rate
            total_deployments = len(self.deployments)
            successful_deployments = len([d for d in self.deployments if d.success])
            success_rate = (successful_deployments / total_deployments) if total_deployments > 0 else 0

            # Calculate average deployment time
            completed_deployments = [d for d in self.deployments if d.duration is not None]
            avg_deployment_time = (
                sum(d.duration for d in completed_deployments) / len(completed_deployments)
            ) if completed_deployments else 0

            return {
                "current_release": asdict(self.current_release) if self.current_release else None,
                "total_deployments": total_deployments,
                "successful_deployments": successful_deployments,
                "success_rate": success_rate,
                "average_deployment_time": avg_deployment_time,
                "recent_deployments": [asdict(d) for d in recent_deployments],
                "environment": settings.environment.value
            }

    def generate_release_notes(self, version: str) -> str:
        """Generate release notes for a version"""
        if not self.current_release or self.current_release.version != version:
            return "Release information not available"

        release = self.current_release

        notes = f"""
# Release Notes - {version}

## Release Information
- **Version**: {version}
- **Commit**: {release.commit_hash}
- **Branch**: {release.branch}
- **Environment**: {release.environment}
- **Released**: {release.timestamp}
- **Author**: {release.author}

## Changes
- **Files Changed**: {release.files_changed}
- **Insertions**: {release.insertions}
- **Deletions**: {release.deletions}

## Commit Message
{release.message}

## Deployment Status
- **Status**: {release.deployment_status}
- **Deployment ID**: {release.deployment_id or 'N/A'}

---

*Generated by Trading System Release Tracker*
"""
        return notes

    def check_deployment_health(self, deployment_id: str) -> Dict[str, Any]:
        """Check deployment health status"""
        with self.lock:
            deployment = next((d for d in self.deployments if d.deployment_id == deployment_id), None)
            if not deployment:
                return {"status": "not_found", "message": "Deployment not found"}

            # Check if deployment is recent
            deployment_time = datetime.fromisoformat(deployment.start_time)
            if datetime.now(UTC) - deployment_time > timedelta(hours=24):
                return {"status": "expired", "message": "Deployment is too old for health checks"}

            # Calculate health score
            health_score = 0
            checks = []

            if deployment.status == "completed":
                health_score += 40
                checks.append("Deployment completed successfully")

            if deployment.success:
                health_score += 30
                checks.append("Deployment successful")

            if deployment.health_checks_total > 0:
                health_check_ratio = deployment.health_checks_passed / deployment.health_checks_total
                health_score += int(health_check_ratio * 30)
                checks.append(f"Health checks: {deployment.health_checks_passed}/{deployment.health_checks_total}")

            if not deployment.rollback_triggered:
                health_score += 10
                checks.append("No rollback triggered")

            return {
                "status": "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical",
                "health_score": health_score,
                "checks": checks,
                "deployment": asdict(deployment)
            }


# Global release tracker instance
release_tracker = ReleaseTracker()
"""Thread-safe in-memory job store managing presentation generation lifecycle states."""

import asyncio
import threading
from datetime import datetime, timezone
from typing import Protocol

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.domain.enums import JobStatus
from backend.app.domain.jobs import JobError, JobProgress, JobState
from backend.app.jobs.models import ArtifactInfo, JobErrorResponse, JobStatusResponse


from backend.app.core.errors import JobNotFoundError, JobStateError

# Valid State Transitions Table
VALID_JOB_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.IDLE: {JobStatus.QUEUED, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.VALIDATING: {JobStatus.QUEUED, JobStatus.PLANNING, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.QUEUED: {
        JobStatus.PLANNING,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    },
    JobStatus.PLANNING: {
        JobStatus.PLANNING,
        JobStatus.DESIGNING,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    },
    JobStatus.DESIGNING: {
        JobStatus.DESIGNING,
        JobStatus.QA,
        JobStatus.RENDERING,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    },
    JobStatus.QA: {
        JobStatus.QA,
        JobStatus.FIXING,
        JobStatus.RENDERING,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    },
    JobStatus.FIXING: {
        JobStatus.FIXING,
        JobStatus.QA,
        JobStatus.RENDERING,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    },
    JobStatus.RENDERING: {
        JobStatus.RENDERING,
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    },
    JobStatus.COMPLETED: set(),  # Terminal state: strictly immutable
    JobStatus.FAILED: set(),     # Terminal state: strictly immutable
    JobStatus.CANCELLED: set(),  # Terminal state: strictly immutable
}

TERMINAL_JOB_STATES: set[JobStatus] = {
    JobStatus.COMPLETED,
    JobStatus.FAILED,
    JobStatus.CANCELLED,
}


class JobStore(Protocol):
    """Abstract protocol for generation job storage implementations."""

    def create_job(
        self,
        job_id: str,
        request: PresentationGenerationRequest,
        reference_bytes: bytes | None = None,
    ) -> JobState: ...

    def get_job(self, job_id: str) -> JobState | None: ...

    def get_request(self, job_id: str) -> PresentationGenerationRequest | None: ...

    def get_reference_bytes(self, job_id: str) -> bytes | None: ...

    def update_progress(
        self,
        job_id: str,
        stage: str,
        percent: int,
        message: str,
        status: JobStatus,
    ) -> JobState: ...

    def complete_job(
        self,
        job_id: str,
        artifact_path: str,
        filename: str,
        slide_count: int,
        size_bytes: int,
    ) -> JobState: ...

    def fail_job(
        self,
        job_id: str,
        code: str,
        message: str,
        retryable: bool = False,
    ) -> JobState: ...

    def check_and_fail_stuck_jobs(self, max_runtime_seconds: int = 300) -> list[str]: ...

    def cleanup_expired(self, ttl_seconds: int = 3600) -> int: ...


class MemoryJobStore:
    """Production in-memory job store with state transition integrity, monotonicity, and TTL."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: dict[str, JobState] = {}
        self._requests: dict[str, PresentationGenerationRequest] = {}
        self._reference_data: dict[str, bytes] = {}
        self._artifact_info: dict[str, ArtifactInfo] = {}

    def _validate_transition(self, current_status: JobStatus, target_status: JobStatus, job_id: str) -> None:
        """Validate lifecycle state transition integrity."""
        if current_status in TERMINAL_JOB_STATES:
            raise JobStateError(
                f"Cannot transition job '{job_id}' from terminal state '{current_status.value}' to '{target_status.value}'."
            )

        allowed = VALID_JOB_TRANSITIONS.get(current_status, set())
        if target_status not in allowed and target_status != current_status:
            raise JobStateError(
                f"Invalid state transition for job '{job_id}': '{current_status.value}' -> '{target_status.value}'."
            )

    def create_job(
        self,
        job_id: str,
        request: PresentationGenerationRequest,
        reference_bytes: bytes | None = None,
    ) -> JobState:
        """Register a new job in QUEUED status."""
        with self._lock:
            now = datetime.now(timezone.utc)
            job = JobState(
                job_id=job_id,
                status=JobStatus.QUEUED,
                progress=JobProgress(stage="queued", percent=0, message="Job queued for processing"),
                created_at=now,
                updated_at=now,
            )
            self._jobs[job_id] = job
            self._requests[job_id] = request
            if reference_bytes:
                self._reference_data[job_id] = reference_bytes
            return job.model_copy(deep=True)

    def get_job(self, job_id: str) -> JobState | None:
        """Retrieve job state by ID."""
        with self._lock:
            job = self._jobs.get(job_id)
            return job.model_copy(deep=True) if job else None

    def get_request(self, job_id: str) -> PresentationGenerationRequest | None:
        """Retrieve original request payload."""
        with self._lock:
            req = self._requests.get(job_id)
            return req.model_copy(deep=True) if req else None

    def get_reference_bytes(self, job_id: str) -> bytes | None:
        """Retrieve raw reference PPTX bytes if provided."""
        with self._lock:
            return self._reference_data.get(job_id)

    def update_progress(
        self,
        job_id: str,
        stage: str,
        percent: int,
        message: str,
        status: JobStatus = JobStatus.PLANNING,
    ) -> JobState:
        """Update job stage, monotonic percentage, and status with transition validation."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise JobNotFoundError(f"Job '{job_id}' not found")

            self._validate_transition(job.status, status, job_id)

            now = datetime.now(timezone.utc)
            job.status = status
            # Enforce monotonic progress (never decrease percent for a successful running job)
            monotonic_percent = max(job.progress.percent, max(0, min(100, percent)))
            job.progress = JobProgress(stage=stage, percent=monotonic_percent, message=message)
            job.updated_at = now
            return job.model_copy(deep=True)

    def complete_job(
        self,
        job_id: str,
        artifact_path: str,
        filename: str,
        slide_count: int,
        size_bytes: int = 0,
    ) -> JobState:
        """Mark job as COMPLETED and attach artifact metadata."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise JobNotFoundError(f"Job '{job_id}' not found")

            self._validate_transition(job.status, JobStatus.COMPLETED, job_id)

            now = datetime.now(timezone.utc)
            job.status = JobStatus.COMPLETED
            job.progress = JobProgress(stage="completed", percent=100, message="Presentation generated successfully")
            job.artifact_path = artifact_path
            job.updated_at = now

            self._artifact_info[job_id] = ArtifactInfo(
                filename=filename,
                download_url=f"/api/download/{job_id}",
                size_bytes=size_bytes,
                slide_count=slide_count,
            )

            # Free reference bytes from memory after successful generation
            self._reference_data.pop(job_id, None)
            return job.model_copy(deep=True)

    def fail_job(
        self,
        job_id: str,
        code: str,
        message: str,
        retryable: bool = False,
    ) -> JobState:
        """Mark job as FAILED and record structured error context."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise JobNotFoundError(f"Job '{job_id}' not found")

            if job.status == JobStatus.COMPLETED:
                raise JobStateError(f"Cannot fail already completed job '{job_id}'.")

            now = datetime.now(timezone.utc)
            job.status = JobStatus.FAILED
            job.error = JobError(code=code, message=message, retryable=retryable)
            job.updated_at = now

            # Clean temporary reference memory
            self._reference_data.pop(job_id, None)
            return job.model_copy(deep=True)

    def check_and_fail_stuck_jobs(self, max_runtime_seconds: int = 300) -> list[str]:
        """Find non-terminal jobs exceeding max runtime threshold and transition them to FAILED."""
        with self._lock:
            now = datetime.now(timezone.utc)
            failed_job_ids: list[str] = []

            for jid, job in self._jobs.items():
                if job.status not in TERMINAL_JOB_STATES:
                    elapsed = (now - job.created_at).total_seconds()
                    if elapsed > max_runtime_seconds:
                        job.status = JobStatus.FAILED
                        job.error = JobError(
                            code="JOB_TIMEOUT",
                            message="Presentation generation exceeded maximum runtime limit. Please try again.",
                            retryable=True,
                        )
                        job.updated_at = now
                        self._reference_data.pop(jid, None)
                        failed_job_ids.append(jid)

            return failed_job_ids

    def get_status_response(self, job_id: str) -> JobStatusResponse | None:
        """Build API-compatible JobStatusResponse."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            artifact = self._artifact_info.get(job_id)
            error = (
                JobErrorResponse(code=job.error.code, message=job.error.message, retryable=job.error.retryable)
                if job.error
                else None
            )

            return JobStatusResponse(
                job_id=job.job_id,
                state=job.status.value,
                progress=job.progress.percent,
                stage=job.progress.stage,
                message=job.progress.message,
                created_at=job.created_at.isoformat(),
                updated_at=job.updated_at.isoformat(),
                artifact=artifact,
                error=error,
            )

    def cleanup_expired(self, ttl_seconds: int = 3600) -> int:
        """Remove jobs older than configured TTL."""
        with self._lock:
            now = datetime.now(timezone.utc)
            expired_ids = [
                jid
                for jid, j in self._jobs.items()
                if (now - j.updated_at).total_seconds() > ttl_seconds
            ]
            for jid in expired_ids:
                self._jobs.pop(jid, None)
                self._requests.pop(jid, None)
                self._reference_data.pop(jid, None)
                self._artifact_info.pop(jid, None)
            return len(expired_ids)


# Global default in-memory job store singleton
default_job_store = MemoryJobStore()


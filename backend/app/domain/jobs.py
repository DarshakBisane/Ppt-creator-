"""Generation Job domain models."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.app.domain.enums import JobStatus


class JobProgress(BaseModel):
    """Job progress indicator with granular stage and percent."""

    stage: str = Field(default="idle", description="Current pipeline stage identifier")
    percent: int = Field(default=0, ge=0, le=100, description="Overall completion percent (0-100)")
    message: str = Field(default="Job initialized", description="Human-readable status description")


class JobError(BaseModel):
    """Structured job failure error context."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Sanitized human-readable error description")
    retryable: bool = Field(default=False, description="True if job failure can be safely retried")


class JobState(BaseModel):
    """Domain model tracking presentation generation job lifecycle."""

    job_id: str = Field(..., min_length=1, max_length=64)
    status: JobStatus = Field(default=JobStatus.IDLE)
    progress: JobProgress = Field(default_factory=JobProgress)
    error: JobError | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    presentation_id: str | None = None
    artifact_path: str | None = None

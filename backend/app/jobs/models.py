"""Pydantic API request and response models for generation jobs."""

from pydantic import BaseModel, Field


class ArtifactInfo(BaseModel):
    """Metadata regarding a generated PowerPoint artifact available for download."""

    filename: str = Field(..., description="Sanitized download filename")
    download_url: str = Field(..., description="Direct relative download endpoint URL")
    size_bytes: int = Field(default=0, ge=0, description="Binary file size in bytes")
    slide_count: int = Field(default=0, ge=0, description="Number of slides rendered")


class JobErrorResponse(BaseModel):
    """Structured error payload when a generation job fails."""

    code: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Sanitized human-readable error description")
    retryable: bool = Field(default=False, description="Whether resubmitting the job might succeed")


class JobStatusResponse(BaseModel):
    """Real-time job execution state and progress report."""

    job_id: str = Field(..., description="Unique job identifier")
    state: str = Field(..., description="Lifecycle status (queued, planning, designing, layout, visual_qa, rendering, completed, failed)")
    progress: int = Field(default=0, ge=0, le=100, description="Completion percentage (0-100)")
    stage: str = Field(default="idle", description="Current pipeline stage identifier")
    message: str = Field(default="", description="Human-readable progress description")
    created_at: str = Field(..., description="ISO 8601 job creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 last progress update timestamp")
    artifact: ArtifactInfo | None = Field(default=None, description="Download information if completed")
    error: JobErrorResponse | None = Field(default=None, description="Error details if failed")


class GenerationJobResponse(BaseModel):
    """Immediate response payload returned upon job creation."""

    job_id: str = Field(..., description="Allocated generation job identifier")
    state: str = Field(default="queued", description="Initial lifecycle state")
    status_url: str = Field(..., description="Polling endpoint URL for job progress")

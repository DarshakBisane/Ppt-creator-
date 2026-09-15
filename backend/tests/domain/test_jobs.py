"""Tests for JobState, JobProgress, and JobError models."""

import pytest
from pydantic import ValidationError

from backend.app.domain import (
    JobError,
    JobProgress,
    JobState,
    JobStatus,
)


def test_valid_job_lifecycle_state() -> None:
    """Verify clean instantiation of JobState."""
    job = JobState(
        job_id="job-uuid-12345",
        status=JobStatus.PLANNING,
        progress=JobProgress(
            stage="planning_slides",
            percent=35,
            message="Designing narrative structure and visual layout models",
        ),
    )
    assert job.job_id == "job-uuid-12345"
    assert job.status == JobStatus.PLANNING
    assert job.progress.percent == 35


def test_job_progress_percent_bounds() -> None:
    """Verify progress percent is bounded between 0 and 100."""
    with pytest.raises(ValidationError):
        JobProgress(stage="test", percent=-5)

    with pytest.raises(ValidationError):
        JobProgress(stage="test", percent=105)


def test_job_error_model() -> None:
    """Verify structured job failure details."""
    err = JobError(
        code="AI_TIMEOUT",
        message="Gemini API request timed out after 30 seconds",
        retryable=True,
    )
    assert err.code == "AI_TIMEOUT"
    assert err.retryable is True

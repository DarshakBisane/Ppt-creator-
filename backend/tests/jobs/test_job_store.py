"""Unit tests for the thread-safe MemoryJobStore."""

from datetime import datetime, timezone
import pytest

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.domain.enums import JobStatus
from backend.app.jobs.store import MemoryJobStore


def test_create_and_get_job() -> None:
    """Test creating and retrieving a generation job."""
    store = MemoryJobStore()
    req = PresentationGenerationRequest(topic="AI in Retail", slide_count=5)

    job = store.create_job("job_123", req)
    assert job.job_id == "job_123"
    assert job.status == JobStatus.QUEUED
    assert job.progress.percent == 0

    fetched = store.get_job("job_123")
    assert fetched is not None
    assert fetched.job_id == "job_123"
    assert fetched.status == JobStatus.QUEUED

    fetched_req = store.get_request("job_123")
    assert fetched_req is not None
    assert fetched_req.topic == "AI in Retail"


def test_update_progress() -> None:
    """Test updating stage, percentage, and message."""
    store = MemoryJobStore()
    req = PresentationGenerationRequest(topic="Quantum Computing", slide_count=6)
    store.create_job("job_456", req)

    updated = store.update_progress(
        job_id="job_456",
        stage="planning_slides",
        percent=15,
        message="Structuring presentation narrative",
        status=JobStatus.PLANNING,
    )
    assert updated.status == JobStatus.PLANNING
    assert updated.progress.stage == "planning_slides"
    assert updated.progress.percent == 15
    assert updated.progress.message == "Structuring presentation narrative"


def test_complete_job() -> None:
    """Test marking job complete and generating status response."""
    store = MemoryJobStore()
    req = PresentationGenerationRequest(topic="Cybersecurity", slide_count=4)
    store.create_job("job_789", req)
    store.update_progress("job_789", "planning", 15, "Planning", JobStatus.PLANNING)
    store.update_progress("job_789", "designing", 35, "Designing", JobStatus.DESIGNING)
    store.update_progress("job_789", "qa", 75, "QA", JobStatus.QA)
    store.update_progress("job_789", "rendering", 90, "Rendering", JobStatus.RENDERING)

    completed = store.complete_job(
        job_id="job_789",
        artifact_path="/path/to/Cybersecurity.pptx",
        filename="Cybersecurity.pptx",
        slide_count=4,
        size_bytes=15000,
    )
    assert completed.status == JobStatus.COMPLETED
    assert completed.progress.percent == 100

    resp = store.get_status_response("job_789")
    assert resp is not None
    assert resp.state == "completed"
    assert resp.progress == 100
    assert resp.artifact is not None
    assert resp.artifact.filename == "Cybersecurity.pptx"
    assert resp.artifact.download_url == "/api/download/job_789"
    assert resp.artifact.slide_count == 4


def test_fail_job() -> None:
    """Test marking job failed with structured error details."""
    store = MemoryJobStore()
    req = PresentationGenerationRequest(topic="Failed Topic", slide_count=3)
    store.create_job("job_fail", req)

    failed = store.fail_job(
        job_id="job_fail",
        code="AI_TIMEOUT",
        message="AI generation timed out",
        retryable=True,
    )
    assert failed.status == JobStatus.FAILED
    assert failed.error is not None
    assert failed.error.code == "AI_TIMEOUT"

    resp = store.get_status_response("job_fail")
    assert resp is not None
    assert resp.state == "failed"
    assert resp.error is not None
    assert resp.error.code == "AI_TIMEOUT"
    assert resp.error.retryable is True


def test_cleanup_expired_jobs() -> None:
    """Test TTL expiration of old jobs."""
    store = MemoryJobStore()
    req = PresentationGenerationRequest(topic="Old Topic", slide_count=3)
    store.create_job("job_old", req)

    # Simulate old timestamp
    old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
    store._jobs["job_old"].updated_at = old_time

    cleaned = store.cleanup_expired(ttl_seconds=60)
    assert cleaned == 1
    assert store.get_job("job_old") is None

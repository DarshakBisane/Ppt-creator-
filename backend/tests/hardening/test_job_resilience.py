"""Tests verifying job lifecycle resilience, state transition validation, and monotonicity."""

import pytest
from datetime import datetime, timedelta, timezone

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.core.errors import JobNotFoundError, JobStateError
from backend.app.domain.enums import JobStatus
from backend.app.jobs.store import MemoryJobStore


def test_valid_state_progression():
    """Job follows correct state progression: QUEUED -> PLANNING -> DESIGNING -> QA -> RENDERING -> COMPLETED."""
    store = MemoryJobStore()
    request = PresentationGenerationRequest(topic="State Machine Progression Test", slide_count=5)
    job = store.create_job("job-progression-1", request)
    assert job.status == JobStatus.QUEUED

    store.update_progress("job-progression-1", stage="planning", percent=15, message="Planning", status=JobStatus.PLANNING)
    assert store.get_job("job-progression-1").status == JobStatus.PLANNING

    store.update_progress("job-progression-1", stage="designing", percent=35, message="Designing", status=JobStatus.DESIGNING)
    assert store.get_job("job-progression-1").status == JobStatus.DESIGNING

    store.update_progress("job-progression-1", stage="qa", percent=75, message="QA", status=JobStatus.QA)
    assert store.get_job("job-progression-1").status == JobStatus.QA

    store.update_progress("job-progression-1", stage="rendering", percent=90, message="Rendering", status=JobStatus.RENDERING)
    assert store.get_job("job-progression-1").status == JobStatus.RENDERING

    store.complete_job("job-progression-1", artifact_path="/tmp/art.pptx", filename="Pres.pptx", slide_count=5)
    assert store.get_job("job-progression-1").status == JobStatus.COMPLETED


def test_invalid_state_transition_rejected():
    """Impossible state transitions raise JobStateError."""
    store = MemoryJobStore()
    request = PresentationGenerationRequest(topic="Invalid Transition Test", slide_count=5)
    store.create_job("job-invalid-1", request)

    # Cannot transition directly from QUEUED to RENDERING or COMPLETED
    with pytest.raises(JobStateError):
        store.complete_job("job-invalid-1", artifact_path="/tmp/art.pptx", filename="Pres.pptx", slide_count=5)


def test_terminal_state_immutability():
    """Terminal states (COMPLETED, FAILED) cannot be transitioned out of."""
    store = MemoryJobStore()
    request = PresentationGenerationRequest(topic="Terminal State Test", slide_count=5)
    store.create_job("job-terminal-1", request)
    store.update_progress("job-terminal-1", stage="planning", percent=15, message="Planning", status=JobStatus.PLANNING)
    store.update_progress("job-terminal-1", stage="designing", percent=35, message="Designing", status=JobStatus.DESIGNING)
    store.update_progress("job-terminal-1", stage="rendering", percent=90, message="Rendering", status=JobStatus.RENDERING)
    store.complete_job("job-terminal-1", artifact_path="/tmp/art.pptx", filename="Pres.pptx", slide_count=5)

    # Trying to update progress after completion raises JobStateError
    with pytest.raises(JobStateError):
        store.update_progress("job-terminal-1", stage="planning", percent=15, message="Planning", status=JobStatus.PLANNING)

    # Trying to fail an already completed job raises JobStateError
    with pytest.raises(JobStateError):
        store.fail_job("job-terminal-1", code="SOME_ERROR", message="Error after completion")


def test_progress_monotonicity():
    """Progress percent never decreases on updates."""
    store = MemoryJobStore()
    request = PresentationGenerationRequest(topic="Monotonicity Test", slide_count=5)
    store.create_job("job-mono-1", request)

    store.update_progress("job-mono-1", stage="planning", percent=50, message="Halfway", status=JobStatus.PLANNING)
    assert store.get_job("job-mono-1").progress.percent == 50

    # Attempt to set percent to 40
    store.update_progress("job-mono-1", stage="planning", percent=40, message="Backward attempt", status=JobStatus.PLANNING)
    assert store.get_job("job-mono-1").progress.percent == 50  # Must remain at maximum (50)


def test_check_and_fail_stuck_jobs():
    """Jobs that exceed max runtime in non-terminal states are failed with JOB_TIMEOUT."""
    store = MemoryJobStore()
    request = PresentationGenerationRequest(topic="Stuck Job Test", slide_count=5)
    store.create_job("job-stuck-1", request)

    # Simulate job started 400 seconds ago
    with store._lock:
        old_time = datetime.now(timezone.utc) - timedelta(seconds=400)
        store._jobs["job-stuck-1"].created_at = old_time
        store._jobs["job-stuck-1"].status = JobStatus.PLANNING

    failed_ids = store.check_and_fail_stuck_jobs(max_runtime_seconds=300)
    assert "job-stuck-1" in failed_ids

    job = store.get_job("job-stuck-1")
    assert job.status == JobStatus.FAILED
    assert job.error.code == "JOB_TIMEOUT"

"""Tests verifying partial artifact cleanup and failure-safe handling."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.domain.enums import JobStatus
from backend.app.jobs.orchestrator import GenerationOrchestrator
from backend.app.jobs.store import MemoryJobStore


@pytest.mark.asyncio
async def test_partial_artifacts_cleaned_on_pipeline_failure(isolated_job_store, isolated_artifact_storage):
    """Artifacts directory is cleaned up when pipeline stage fails."""
    job_id = "job-cleanup-test-01"
    request = PresentationGenerationRequest(topic="Testing Cleanup on Failure", slide_count=4)
    isolated_job_store.create_job(job_id, request)

    # Pre-create a dummy partial artifact in the job directory
    job_dir = isolated_artifact_storage.base_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    partial_file = job_dir / "partial.tmp"
    partial_file.write_bytes(b"partial temporary rendering artifacts")
    assert partial_file.exists()

    mock_ai = MagicMock()
    mock_ai.generate_presentation = AsyncMock(side_effect=RuntimeError("AI failure triggering cleanup"))

    orchestrator = GenerationOrchestrator(
        job_store=isolated_job_store,
        artifact_storage=isolated_artifact_storage,
        ai_provider=mock_ai,
    )

    await orchestrator.execute_generation_job(job_id)

    # The partial file and job directory should be cleaned
    assert not partial_file.exists()
    assert not job_dir.exists()

    job = isolated_job_store.get_job(job_id)
    assert job.status == JobStatus.FAILED


@pytest.mark.asyncio
async def test_cleanup_failure_does_not_mask_original_error(isolated_job_store, fake_ai):
    """If deleting the artifact raises an unexpected error, the original generation error is preserved."""
    job_id = "job-cleanup-mask-test"
    request = PresentationGenerationRequest(topic="Testing Cleanup Error Isolation", slide_count=4)
    isolated_job_store.create_job(job_id, request)

    mock_storage = MagicMock()
    mock_storage.delete_artifact.side_effect = PermissionError("OS locked file")

    mock_renderer = MagicMock()
    mock_renderer.render_to_bytes.side_effect = RuntimeError("Original rendering crash")

    orchestrator = GenerationOrchestrator(
        job_store=isolated_job_store,
        artifact_storage=mock_storage,
        ai_provider=fake_ai,
        pptx_renderer=mock_renderer,
    )

    await orchestrator.execute_generation_job(job_id)

    job = isolated_job_store.get_job(job_id)
    assert job.status == JobStatus.FAILED
    assert job.error.code == "RENDERING_ERROR"
    assert "PowerPoint rendering failed" in job.error.message

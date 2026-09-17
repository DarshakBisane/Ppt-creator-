"""Tests verifying concurrency limiter semaphore and execution runtime timeout handling."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.domain.enums import JobStatus
from backend.app.jobs.orchestrator import GenerationOrchestrator
from backend.app.jobs.store import MemoryJobStore


@pytest.mark.asyncio
async def test_job_execution_runtime_timeout(isolated_job_store, isolated_artifact_storage):
    """Job exceeding configured max runtime is cancelled and marked FAILED with JOB_TIMEOUT."""
    mock_ai = MagicMock()
    # Simulate an AI call that hangs for 5 seconds
    async def slow_generate(*args, **kwargs):
        await asyncio.sleep(5)

    mock_ai.generate_presentation = slow_generate

    orchestrator = GenerationOrchestrator(
        job_store=isolated_job_store,
        artifact_storage=isolated_artifact_storage,
        ai_provider=mock_ai,
        max_runtime_seconds=1,  # Strict 1-second timeout
    )

    job_id = "job-timeout-test"
    request = PresentationGenerationRequest(topic="Hanging AI Simulation", slide_count=5)
    isolated_job_store.create_job(job_id, request)

    await orchestrator.execute_generation_job(job_id)

    job = isolated_job_store.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.FAILED
    assert job.error is not None
    assert job.error.code == "JOB_TIMEOUT"


@pytest.mark.asyncio
async def test_concurrency_semaphore_limits_parallel_runs(isolated_job_store, isolated_artifact_storage, fake_ai):
    """GenerationOrchestrator bounded concurrency semaphore bounds active simultaneous runs."""
    active_count = 0
    max_active = 0
    lock = asyncio.Lock()

    mock_ai = MagicMock()
    async def track_concurrent(*args, **kwargs):
        nonlocal active_count, max_active
        async with lock:
            active_count += 1
            if active_count > max_active:
                max_active = active_count
        await asyncio.sleep(0.1)
        async with lock:
            active_count -= 1
        return await fake_ai.generate_presentation(args[0])

    mock_ai.generate_presentation = track_concurrent

    orchestrator = GenerationOrchestrator(
        job_store=isolated_job_store,
        artifact_storage=isolated_artifact_storage,
        ai_provider=mock_ai,
        max_concurrent_jobs=2,  # Maximum 2 concurrent jobs
    )

    # Launch 4 jobs concurrently
    job_ids = [f"job-conc-{i}" for i in range(4)]
    for jid in job_ids:
        isolated_job_store.create_job(jid, PresentationGenerationRequest(topic=f"Topic {jid}", slide_count=4))

    tasks = [orchestrator.execute_generation_job(jid) for jid in job_ids]
    await asyncio.gather(*tasks)

    # Max concurrent executions should not have exceeded 2
    assert max_active <= 2
    for jid in job_ids:
        job = isolated_job_store.get_job(jid)
        assert job.status == JobStatus.COMPLETED

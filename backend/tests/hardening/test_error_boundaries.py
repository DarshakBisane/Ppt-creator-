"""Tests verifying global exception boundaries and stage failure isolation."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.core.errors import (
    AIProviderError,
    LayoutError,
    RenderingError,
    SemanticSelectionError,
    VisualQAError,
)
from backend.app.domain.enums import JobStatus
from backend.app.jobs.orchestrator import GenerationOrchestrator
from backend.app.jobs.store import MemoryJobStore


@pytest.mark.asyncio
async def test_ai_planning_stage_failure_isolation(isolated_job_store, isolated_artifact_storage):
    """Failure in AI planning stage sets job to FAILED without crashing."""
    mock_ai = MagicMock()
    mock_ai.generate_presentation = AsyncMock(side_effect=RuntimeError("AI model crashed"))

    orchestrator = GenerationOrchestrator(
        job_store=isolated_job_store,
        artifact_storage=isolated_artifact_storage,
        ai_provider=mock_ai,
    )

    job_id = "job-ai-fail"
    request = PresentationGenerationRequest(topic="Testing AI Failure Isolation", slide_count=5)
    isolated_job_store.create_job(job_id=job_id, request=request)

    await orchestrator.execute_generation_job(job_id)

    job = isolated_job_store.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.FAILED
    assert job.error is not None
    assert job.error.code == "AI_PROVIDER_ERROR"
    assert "AI presentation planning failed" in job.error.message


@pytest.mark.asyncio
async def test_semantic_selection_failure_isolation(isolated_job_store, isolated_artifact_storage, fake_ai):
    """Failure in semantic selection stage is caught and mapped to SEMANTIC_SELECTION_ERROR."""
    mock_selector = MagicMock()
    mock_selector.refine_presentation.side_effect = ValueError("Corrupt archetype metadata")

    orchestrator = GenerationOrchestrator(
        job_store=isolated_job_store,
        artifact_storage=isolated_artifact_storage,
        ai_provider=fake_ai,
        visual_selector=mock_selector,
    )

    job_id = "job-selector-fail"
    request = PresentationGenerationRequest(topic="Testing Semantic Selector Failure", slide_count=5)
    isolated_job_store.create_job(job_id=job_id, request=request)

    await orchestrator.execute_generation_job(job_id)

    job = isolated_job_store.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.FAILED
    assert job.error is not None
    assert job.error.code == "SEMANTIC_SELECTION_ERROR"


@pytest.mark.asyncio
async def test_layout_stage_failure_isolation(isolated_job_store, isolated_artifact_storage, fake_ai):
    """Failure in layout calculation is caught and mapped to LAYOUT_ERROR."""
    mock_layout = MagicMock()
    mock_layout.layout_presentation.side_effect = RuntimeError("Coordinate calculation failure")

    orchestrator = GenerationOrchestrator(
        job_store=isolated_job_store,
        artifact_storage=isolated_artifact_storage,
        ai_provider=fake_ai,
        layout_engine=mock_layout,
    )

    job_id = "job-layout-fail"
    request = PresentationGenerationRequest(topic="Testing Layout Engine Failure", slide_count=5)
    isolated_job_store.create_job(job_id=job_id, request=request)

    await orchestrator.execute_generation_job(job_id)

    job = isolated_job_store.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.FAILED
    assert job.error is not None
    assert job.error.code == "LAYOUT_ERROR"


@pytest.mark.asyncio
async def test_visual_qa_failure_isolation(isolated_job_store, isolated_artifact_storage, fake_ai):
    """Failure in Visual QA stage is caught and mapped to VISUAL_QA_ERROR."""
    mock_qa = MagicMock()
    mock_qa.validate_and_correct_presentation.side_effect = RuntimeError("QA pass rule error")

    orchestrator = GenerationOrchestrator(
        job_store=isolated_job_store,
        artifact_storage=isolated_artifact_storage,
        ai_provider=fake_ai,
        qa_orchestrator=mock_qa,
    )

    job_id = "job-qa-fail"
    request = PresentationGenerationRequest(topic="Testing Visual QA Failure", slide_count=5)
    isolated_job_store.create_job(job_id=job_id, request=request)

    await orchestrator.execute_generation_job(job_id)

    job = isolated_job_store.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.FAILED
    assert job.error is not None
    assert job.error.code == "VISUAL_QA_ERROR"


@pytest.mark.asyncio
async def test_rendering_failure_isolation(isolated_job_store, isolated_artifact_storage, fake_ai):
    """Failure in OpenXML PPTX rendering is caught and mapped to RENDERING_ERROR."""
    mock_renderer = MagicMock()
    mock_renderer.render_to_bytes.side_effect = RuntimeError("OpenXML packing error")

    orchestrator = GenerationOrchestrator(
        job_store=isolated_job_store,
        artifact_storage=isolated_artifact_storage,
        ai_provider=fake_ai,
        pptx_renderer=mock_renderer,
    )

    job_id = "job-render-fail"
    request = PresentationGenerationRequest(topic="Testing Rendering Failure", slide_count=5)
    isolated_job_store.create_job(job_id=job_id, request=request)

    await orchestrator.execute_generation_job(job_id)

    job = isolated_job_store.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.FAILED
    assert job.error is not None
    assert job.error.code == "RENDERING_ERROR"

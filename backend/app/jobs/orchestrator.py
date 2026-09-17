"""Authoritative asynchronous presentation generation orchestrator service."""

import asyncio
import logging
import re
from typing import Any

import time

from backend.app.ai.context import DesignContext, PresentationGenerationRequest
from backend.app.ai.exceptions import AIProviderError
from backend.app.ai.fake_provider import FakeAIProvider
from backend.app.ai.gemini_provider import GeminiProvider
from backend.app.ai.provider import AIProvider
from backend.app.artifacts.storage import ArtifactStorage, default_artifact_storage
from backend.app.config import Settings, get_settings
from backend.app.core.errors import (
    AppException,
    ArtifactStorageError,
    JobTimeoutError,
    LayoutError,
    RenderingError,
    SemanticSelectionError,
    VisualQAError,
)
from backend.app.domain.enums import JobStatus
from backend.app.domain.presentation import Presentation
from backend.app.jobs.store import JobStore, default_job_store
from backend.app.layout.engine import LayoutEngine, default_layout_engine
from backend.app.reference.analyzer import ReferencePPTAnalyzer
from backend.app.rendering.engine import PPTXRenderer, default_pptx_renderer
from backend.app.visual_intelligence.selector import (
    SemanticVisualSelector,
    default_visual_selector,
)
from backend.app.visual_qa.orchestrator import (
    VisualQAOrchestrator,
    default_qa_orchestrator,
)

logger = logging.getLogger(__name__)


def get_ai_provider(settings: Settings | None = None) -> AIProvider:
    """Factory creating configured AI provider instance based on environment and credentials."""
    s = settings or get_settings()
    if s.is_test or not s.gemini_api_key or not s.gemini_api_key.strip():
        logger.info("Using FakeAIProvider for presentation generation")
        return FakeAIProvider()

    logger.info("Using production GeminiProvider for presentation generation")
    return GeminiProvider(
        api_key=s.gemini_api_key,
        model=s.gemini_model,
        timeout_seconds=float(s.ai_timeout_seconds),
        max_attempts=s.ai_max_attempts,
    )


def sanitize_presentation_filename(title: str) -> str:
    """Generate safe, clean filename for PowerPoint delivery."""
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "_", title.strip())
    clean = clean.strip("_")
    if not clean:
        clean = "Presentation"
    return f"{clean[:50]}.pptx"


class GenerationOrchestrator:
    """Orchestrates the complete Phase 1-9 generation pipeline with bounded concurrency and timeouts."""

    def __init__(
        self,
        job_store: JobStore | None = None,
        artifact_storage: ArtifactStorage | None = None,
        ai_provider: AIProvider | None = None,
        reference_analyzer: ReferencePPTAnalyzer | None = None,
        visual_selector: SemanticVisualSelector | None = None,
        layout_engine: LayoutEngine | None = None,
        qa_orchestrator: VisualQAOrchestrator | None = None,
        pptx_renderer: PPTXRenderer | None = None,
        max_concurrent_jobs: int | None = None,
        max_runtime_seconds: int | None = None,
    ) -> None:
        settings = get_settings()
        self.store = job_store or default_job_store
        self.artifacts = artifact_storage or default_artifact_storage
        self.ai_provider = ai_provider or get_ai_provider(settings)
        self.reference_analyzer = reference_analyzer or ReferencePPTAnalyzer()
        self.visual_selector = visual_selector or default_visual_selector
        self.layout_engine = layout_engine or default_layout_engine
        self.qa_orchestrator = qa_orchestrator or default_qa_orchestrator
        self.renderer = pptx_renderer or default_pptx_renderer

        max_concurrent = max_concurrent_jobs or settings.max_concurrent_jobs
        self.max_runtime_seconds = max_runtime_seconds or settings.max_job_runtime_seconds
        self._concurrency_semaphore = asyncio.Semaphore(max_concurrent)

    def _safe_cleanup_partial_artifacts(self, job_id: str) -> None:
        """Safely delete partial job artifact directory without raising exceptions."""
        try:
            self.artifacts.delete_artifact(job_id)
        except Exception as cleanup_err:
            logger.warning(
                "Partial artifact cleanup encountered an issue",
                extra={"job_id": job_id, "error": str(cleanup_err)},
            )

    async def execute_generation_job(self, job_id: str) -> None:
        """Execute the full generation lifecycle under bounded concurrency and runtime timeout."""
        job = self.store.get_job(job_id)
        if not job:
            logger.error("Generation job not found in store", extra={"job_id": job_id})
            return

        request = self.store.get_request(job_id)
        if not request:
            logger.error("Generation request payload missing", extra={"job_id": job_id})
            self.store.fail_job(job_id, "REQUEST_MISSING", "Generation request payload not found")
            return

        async with self._concurrency_semaphore:
            try:
                await asyncio.wait_for(
                    self._run_generation_pipeline(job_id, request),
                    timeout=float(self.max_runtime_seconds),
                )
            except (asyncio.TimeoutError, TimeoutError):
                logger.error(
                    "Job execution timed out",
                    extra={"job_id": job_id, "timeout_seconds": self.max_runtime_seconds},
                )
                self._safe_cleanup_partial_artifacts(job_id)
                self.store.fail_job(
                    job_id=job_id,
                    code="JOB_TIMEOUT",
                    message="Presentation generation exceeded maximum runtime limit. Please try again.",
                    retryable=True,
                )
            except AppException as app_err:
                logger.error(
                    "Presentation generation failed with domain exception",
                    extra={"job_id": job_id, "error_code": app_err.error_code, "err_msg": app_err.message},
                )
                self._safe_cleanup_partial_artifacts(job_id)
                self.store.fail_job(
                    job_id=job_id,
                    code=app_err.error_code,
                    message=app_err.message,
                    retryable=getattr(app_err, "retryable", False),
                )
            except Exception as unhandled_err:
                logger.exception(
                    "Unexpected error during presentation generation pipeline",
                    extra={"job_id": job_id},
                )
                self._safe_cleanup_partial_artifacts(job_id)
                self.store.fail_job(
                    job_id=job_id,
                    code="GENERATION_ERROR",
                    message="An error occurred while generating the presentation. Please check your topic and try again.",
                    retryable=True,
                )

    async def _run_generation_pipeline(
        self,
        job_id: str,
        request: PresentationGenerationRequest,
    ) -> None:
        """Internal execution sequence across all 7 pipeline stages with isolated boundaries and timing."""
        reference_bytes = self.store.get_reference_bytes(job_id)
        design_context: DesignContext | None = request.design_context
        extracted_ds = None
        pipeline_start_time = time.perf_counter()

        logger.info(
            "Starting background generation pipeline",
            extra={"job_id": job_id, "mode": request.mode, "topic": request.topic[:40]},
        )

        # -------------------------------------------------------------------
        # STAGE 1: PLANNING & REFERENCE ANALYSIS (15%)
        # -------------------------------------------------------------------
        stage1_start = time.perf_counter()
        self.store.update_progress(
            job_id=job_id,
            stage="planning_slides",
            percent=15,
            message="Analyzing requirements and planning presentation narrative",
            status=JobStatus.PLANNING,
        )

        if request.mode == "reference" and reference_bytes:
            try:
                design_context, extracted_ds, _ = self.reference_analyzer.analyze(reference_bytes)
                request.design_context = design_context
                logger.info("Reference PPTX design language extracted", extra={"job_id": job_id})
            except AppException:
                raise
            except Exception as ref_err:
                logger.warning(
                    "Reference analysis failed, falling back to default styling",
                    extra={"job_id": job_id, "error": str(ref_err)},
                )

        try:
            presentation: Presentation = await self.ai_provider.generate_presentation(request)
        except AppException:
            raise
        except Exception as ai_err:
            logger.error("AI Planning stage failed", extra={"job_id": job_id, "error": str(ai_err)})
            raise AIProviderError(f"AI presentation planning failed: {str(ai_err)}") from ai_err

        stage1_ms = (time.perf_counter() - stage1_start) * 1000

        # -------------------------------------------------------------------
        # STAGE 2: DESIGNING TOKENS (35%)
        # -------------------------------------------------------------------
        self.store.update_progress(
            job_id=job_id,
            stage="designing_layouts",
            percent=35,
            message="Constructing design system tokens and visual hierarchy",
            status=JobStatus.DESIGNING,
        )

        if extracted_ds is not None:
            presentation.design_system = extracted_ds

        # -------------------------------------------------------------------
        # STAGE 3: SEMANTIC SELECTION & LAYOUT (55%)
        # -------------------------------------------------------------------
        stage3_start = time.perf_counter()
        self.store.update_progress(
            job_id=job_id,
            stage="creating_visuals",
            percent=55,
            message="Selecting visual archetypes and computing 1920x1080 layout coordinates",
            status=JobStatus.DESIGNING,
        )

        try:
            refined_presentation = self.visual_selector.refine_presentation(
                presentation=presentation,
                design_context=design_context,
            )
        except AppException:
            raise
        except Exception as sel_err:
            logger.error("Semantic visual selection failed", extra={"job_id": job_id, "error": str(sel_err)})
            raise SemanticSelectionError(f"Visual archetype selection failed: {str(sel_err)}") from sel_err

        try:
            raw_layout = self.layout_engine.layout_presentation(refined_presentation)
        except AppException:
            raise
        except Exception as lay_err:
            logger.error("Layout geometry calculation failed", extra={"job_id": job_id, "error": str(lay_err)})
            raise LayoutError(f"Layout calculation failed: {str(lay_err)}") from lay_err

        stage3_ms = (time.perf_counter() - stage3_start) * 1000

        # -------------------------------------------------------------------
        # STAGE 4: VISUAL QA & 3-PASS CORRECTION (75%)
        # -------------------------------------------------------------------
        stage4_start = time.perf_counter()
        self.store.update_progress(
            job_id=job_id,
            stage="checking_slides",
            percent=75,
            message="Validating visual quality, text fitting, and boundary constraints",
            status=JobStatus.QA,
        )

        try:
            qa_result = self.qa_orchestrator.validate_and_correct_presentation(
                presentation=refined_presentation,
                layout_result=raw_layout,
            )
        except AppException:
            raise
        except Exception as qa_err:
            logger.error("Visual QA validation failed", extra={"job_id": job_id, "error": str(qa_err)})
            raise VisualQAError(f"Visual quality validation failed: {str(qa_err)}") from qa_err

        stage4_ms = (time.perf_counter() - stage4_start) * 1000

        # -------------------------------------------------------------------
        # STAGE 5: RENDERING (90%)
        # -------------------------------------------------------------------
        stage5_start = time.perf_counter()
        self.store.update_progress(
            job_id=job_id,
            stage="building_powerpoint",
            percent=90,
            message="Rendering editable PowerPoint OpenXML shapes, tables, and charts",
            status=JobStatus.RENDERING,
        )

        try:
            pptx_bytes = self.renderer.render_to_bytes(
                presentation=refined_presentation,
                layout_result=qa_result,
            )
        except AppException:
            raise
        except Exception as rend_err:
            logger.error("PPTX Rendering failed", extra={"job_id": job_id, "error": str(rend_err)})
            raise RenderingError(f"PowerPoint rendering failed: {str(rend_err)}") from rend_err

        stage5_ms = (time.perf_counter() - stage5_start) * 1000

        # -------------------------------------------------------------------
        # STAGE 6: ARTIFACT STORAGE & COMPLETION (100%)
        # -------------------------------------------------------------------
        filename = sanitize_presentation_filename(refined_presentation.metadata.title)
        try:
            artifact_path = self.artifacts.save_artifact(
                job_id=job_id,
                filename=filename,
                data=pptx_bytes,
            )
        except AppException:
            raise
        except Exception as stor_err:
            logger.error("Artifact saving failed", extra={"job_id": job_id, "error": str(stor_err)})
            raise ArtifactStorageError(f"Failed to persist presentation artifact: {str(stor_err)}") from stor_err

        slide_count = len(refined_presentation.slides)
        self.store.complete_job(
            job_id=job_id,
            artifact_path=str(artifact_path),
            filename=filename,
            slide_count=slide_count,
            size_bytes=len(pptx_bytes),
        )

        total_ms = (time.perf_counter() - pipeline_start_time) * 1000
        logger.info(
            "Presentation generation completed successfully",
            extra={
                "job_id": job_id,
                "slide_count": slide_count,
                "bytes": len(pptx_bytes),
                "qa_score": qa_result.final_quality_score,
                "duration_planning_ms": round(stage1_ms, 2),
                "duration_layout_ms": round(stage3_ms, 2),
                "duration_qa_ms": round(stage4_ms, 2),
                "duration_render_ms": round(stage5_ms, 2),
                "total_duration_ms": round(total_ms, 2),
            },
        )


# Global default generation orchestrator singleton
default_generation_orchestrator = GenerationOrchestrator()


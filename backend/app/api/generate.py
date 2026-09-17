"""Presentation generation and asynchronous job API endpoints."""

import json
import logging
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.artifacts.storage import ArtifactStorage, default_artifact_storage, is_safe_id
from backend.app.config import get_settings
from backend.app.jobs.models import GenerationJobResponse, JobStatusResponse
from backend.app.jobs.orchestrator import GenerationOrchestrator, default_generation_orchestrator
from backend.app.jobs.store import JobStore, default_job_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Presentation Generation"])


@router.post(
    "/generate",
    response_model=GenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create presentation generation job",
    description="Initiate an asynchronous presentation generation job from topic or reference PPTX.",
)
async def create_generation_job(
    request: Request,
    background_tasks: BackgroundTasks,
    topic: Annotated[str | None, Form()] = None,
    mode: Annotated[str | None, Form()] = None,
    audience: Annotated[str | None, Form()] = None,
    purpose: Annotated[str | None, Form()] = None,
    slide_count: Annotated[int | None, Form()] = None,
    style: Annotated[str | None, Form()] = None,
    reference_file: Annotated[UploadFile | None, File()] = None,
) -> GenerationJobResponse:
    """Create and queue a new presentation generation job."""
    settings = get_settings()
    content_type = request.headers.get("content-type", "")
    reference_bytes: bytes | None = None
    gen_request: PresentationGenerationRequest

    # Check if request is JSON body vs Multipart Form Data
    if "application/json" in content_type:
        try:
            body_json = await request.json()
            gen_request = PresentationGenerationRequest(**body_json)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "VALIDATION_ERROR", "message": f"Invalid request payload: {str(e)}"},
            )
    else:
        # Multipart / Form Data
        if not topic or not topic.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "VALIDATION_ERROR", "message": "Presentation topic is required."},
            )

        if reference_file:
            max_bytes = min(settings.max_upload_size_bytes, settings.max_reference_pptx_bytes)
            reference_bytes = await reference_file.read()
            if len(reference_bytes) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={
                        "code": "FILE_TOO_LARGE",
                        "message": f"Reference file exceeds maximum allowed size ({max_bytes} bytes).",
                    },
                )

        try:
            gen_request = PresentationGenerationRequest(
                mode="reference" if reference_file or mode == "reference" else "topic",
                topic=topic,
                audience=audience,
                purpose=purpose,
                slide_count=slide_count or 8,
                style=style or "professional",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "VALIDATION_ERROR", "message": str(e)},
            )

    job_id = str(uuid.uuid4())
    store: JobStore = default_job_store
    orchestrator: GenerationOrchestrator = default_generation_orchestrator

    # Register job in store
    store.create_job(
        job_id=job_id,
        request=gen_request,
        reference_bytes=reference_bytes,
    )

    # Dispatch background execution
    background_tasks.add_task(orchestrator.execute_generation_job, job_id)

    logger.info("Generation job queued", extra={"job_id": job_id, "mode": gen_request.mode})

    return GenerationJobResponse(
        job_id=job_id,
        state="queued",
        status_url=f"/api/jobs/{job_id}",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get generation job status",
    description="Poll current execution status, pipeline stage, and download link for a job.",
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Retrieve real-time progress and status for a generation job."""
    if not is_safe_id(job_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' was not found."},
        )

    store: JobStore = default_job_store
    status_resp = store.get_status_response(job_id)
    if not status_resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' was not found or has expired."},
        )

    return status_resp


@router.get(
    "/download/{job_id}",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Download generated PowerPoint presentation",
    description="Download the finalized native .pptx presentation file.",
)
async def download_presentation(job_id: str) -> FileResponse:
    """Serve the generated native PowerPoint presentation file."""
    if not is_safe_id(job_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' was not found."},
        )

    store: JobStore = default_job_store
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' was not found or has expired."},
        )

    if job.status.value != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "JOB_NOT_COMPLETED",
                "message": f"Job '{job_id}' is in '{job.status.value}' state and not yet ready for download.",
            },
        )

    artifacts: ArtifactStorage = default_artifact_storage
    artifact_data = artifacts.get_artifact(job_id)

    if not artifact_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ARTIFACT_NOT_FOUND", "message": f"Presentation file for job '{job_id}' was not found or has expired."},
        )

    _, filename, file_path = artifact_data

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


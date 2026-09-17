"""Tests verifying download endpoint security and integrity validation."""

import pytest
from fastapi.testclient import TestClient

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.artifacts.storage import default_artifact_storage
from backend.app.domain.enums import JobStatus
from backend.app.jobs.store import default_job_store
from backend.app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_download_nonexistent_job_returns_404(client):
    """Attempting to download a non-existent job ID returns structured 404."""
    response = client.get("/api/download/nonexistent-uuid-12345")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "JOB_NOT_FOUND"


def test_download_uncompleted_job_returns_400(client):
    """Attempting to download an in-progress or queued job returns 400 Bad Request."""
    job_id = "job-running-test"
    req = PresentationGenerationRequest(topic="Testing Incomplete Download", slide_count=5)
    default_job_store.create_job(job_id, req)
    default_job_store.update_progress(job_id, stage="planning", percent=15, message="Planning", status=JobStatus.PLANNING)

    response = client.get(f"/api/download/{job_id}")
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "JOB_NOT_COMPLETED"


def test_download_path_traversal_job_id_rejected(client):
    """Attempting to use path traversal in download endpoint returns 404."""
    response = client.get("/api/download/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code == 404


def test_download_completed_job_returns_pptx_with_safe_headers(client, valid_pptx_bytes):
    """Downloading a completed job delivers valid PPTX with safe Content-Disposition headers."""
    job_id = "job-download-success"
    req = PresentationGenerationRequest(topic="Quarterly Business Review", slide_count=5)
    default_job_store.create_job(job_id, req)
    default_job_store.update_progress(job_id, stage="planning", percent=15, message="Planning", status=JobStatus.PLANNING)
    default_job_store.update_progress(job_id, stage="designing", percent=35, message="Designing", status=JobStatus.DESIGNING)
    default_job_store.update_progress(job_id, stage="rendering", percent=90, message="Rendering", status=JobStatus.RENDERING)

    saved_path = default_artifact_storage.save_artifact(job_id, "Quarterly_Business_Review.pptx", valid_pptx_bytes)
    default_job_store.complete_job(job_id, str(saved_path), "Quarterly_Business_Review.pptx", slide_count=5, size_bytes=len(valid_pptx_bytes))

    response = client.get(f"/api/download/{job_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert 'attachment; filename="Quarterly_Business_Review.pptx"' in response.headers["content-disposition"]
    assert "no-cache" in response.headers["cache-control"]
    assert response.content == valid_pptx_bytes


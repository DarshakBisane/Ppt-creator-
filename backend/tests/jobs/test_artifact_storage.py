"""Unit tests for sandboxed ArtifactStorage and path traversal defense."""

import io
import os
import zipfile
from pathlib import Path
import pytest

from backend.app.artifacts.storage import ArtifactStorage, sanitize_filename


def create_sample_pptx_bytes() -> bytes:
    """Helper creating a minimal valid OpenXML PPTX zip byte payload."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("[Content_Types].xml", b"<Types></Types>")
        zf.writestr("ppt/presentation.xml", b"<p:presentation></p:presentation>")
    buffer.seek(0)
    return buffer.read()


def test_sanitize_filename() -> None:
    """Test filename sanitization preventing directory traversal."""
    assert sanitize_filename("My Presentation.pptx") == "My_Presentation.pptx"
    assert sanitize_filename("../../etc/passwd") == "passwd.pptx"
    assert sanitize_filename("cool presentation") == "cool_presentation.pptx"
    assert sanitize_filename("special!@#$characters.pptx") == "special____characters.pptx"


def test_save_and_get_artifact(tmp_path: Path) -> None:
    """Test saving and retrieving an artifact from sandboxed storage."""
    storage = ArtifactStorage(base_dir=tmp_path)
    pptx_bytes = create_sample_pptx_bytes()

    saved_path = storage.save_artifact("job_abc123", "Strategic_Plan.pptx", pptx_bytes)
    assert saved_path.exists()
    assert saved_path.name == "Strategic_Plan.pptx"

    result = storage.get_artifact("job_abc123")
    assert result is not None
    data, filename, path = result
    assert data == pptx_bytes
    assert filename == "Strategic_Plan.pptx"
    assert path == saved_path


def test_path_traversal_rejection(tmp_path: Path) -> None:
    """Test that path traversal attempts in job_id are strictly rejected."""
    storage = ArtifactStorage(base_dir=tmp_path)
    pptx_bytes = create_sample_pptx_bytes()

    with pytest.raises(ValueError, match="Invalid or unsafe job identifier"):
        storage.save_artifact("../evil_job", "file.pptx", pptx_bytes)

    with pytest.raises(ValueError, match="Invalid or unsafe job identifier"):
        storage.get_artifact("job/../../../etc")


def test_invalid_pptx_payload_rejected(tmp_path: Path) -> None:
    """Test that arbitrary non-PPTX binary payloads are rejected before saving."""
    storage = ArtifactStorage(base_dir=tmp_path)
    junk_data = b"This is plain text, not a PowerPoint zip package"

    with pytest.raises(ValueError, match="Corrupted or invalid OpenXML PowerPoint"):
        storage.save_artifact("job_junk", "presentation.pptx", junk_data)


def test_delete_and_cleanup_artifacts(tmp_path: Path) -> None:
    """Test deleting artifact and cleaning expired directories."""
    storage = ArtifactStorage(base_dir=tmp_path)
    pptx_bytes = create_sample_pptx_bytes()

    storage.save_artifact("job_to_delete", "test.pptx", pptx_bytes)
    assert storage.get_artifact("job_to_delete") is not None

    deleted = storage.delete_artifact("job_to_delete")
    assert deleted is True
    assert storage.get_artifact("job_to_delete") is None

    # Test TTL cleanup
    storage.save_artifact("job_expired", "test2.pptx", pptx_bytes)
    cleaned_count = storage.cleanup_expired_artifacts(ttl_seconds=-1)
    assert cleaned_count >= 1
    assert storage.get_artifact("job_expired") is None

"""Tests verifying artifact storage containment, traversal defenses, and package validation."""

import pytest
from pathlib import Path

from backend.app.artifacts.storage import ArtifactStorage, sanitize_filename, is_safe_id
from backend.app.core.errors import ArtifactSecurityError, ArtifactValidationError


def test_sanitize_filename():
    """sanitize_filename cleans unsafe characters, directory traversals, and enforces .pptx extension."""
    assert sanitize_filename("../evil.exe") == "evil.pptx"
    assert sanitize_filename("..\\evil.exe") == "evil.pptx"
    assert sanitize_filename("../../../evil.exe") == "evil.pptx"
    assert sanitize_filename("..\\..\\evil.pptx") == "evil.pptx"
    assert sanitize_filename("C:\\temp\\evil.pptx") == "evil.pptx"
    assert sanitize_filename("/tmp/evil.pptx") == "evil.pptx"
    assert sanitize_filename("normal presentation.pptx") == "normal_presentation.pptx"
    assert sanitize_filename("normal.pptx") == "normal.pptx"
    assert sanitize_filename("My Presentation / 2026") == "2026.pptx"
    assert sanitize_filename("") == "Presentation.pptx"


def test_is_safe_id():
    """is_safe_id strictly permits safe alphanumeric/hyphen/underscore identifiers."""
    assert is_safe_id("550e8400-e29b-41d4-a716-446655440000") is True
    assert is_safe_id("job_123-abc") is True

    # Rejections
    assert is_safe_id("../job") is False
    assert is_safe_id("/etc/passwd") is False
    assert is_safe_id("job/123") is False
    assert is_safe_id("job\\123") is False
    assert is_safe_id("job\x00123") is False
    assert is_safe_id("A" * 65) is False


def test_artifact_storage_path_traversal_rejection(tmp_path):
    """ArtifactStorage rejects path traversal job IDs."""
    storage = ArtifactStorage(base_dir=tmp_path / "artifacts")
    with pytest.raises(ArtifactSecurityError):
        storage._get_job_dir("../outside_dir")

    with pytest.raises(ArtifactSecurityError):
        storage._get_job_dir("job/subfolder")


def test_artifact_storage_save_and_retrieve_valid_pptx(tmp_path, valid_pptx_bytes):
    """Valid PPTX packages save and retrieve correctly within isolated directory."""
    storage = ArtifactStorage(base_dir=tmp_path / "artifacts")
    job_id = "test-job-save-01"

    saved_path = storage.save_artifact(
        job_id=job_id,
        filename="Financial_Report.pptx",
        data=valid_pptx_bytes,
    )
    assert saved_path.exists()
    assert saved_path.name == "Financial_Report.pptx"

    retrieved = storage.get_artifact(job_id)
    assert retrieved is not None
    data, name, path = retrieved
    assert data == valid_pptx_bytes
    assert name == "Financial_Report.pptx"


def test_artifact_storage_rejects_empty_or_corrupted_payload(tmp_path):
    """Corrupted non-PPTX data is rejected during save."""
    storage = ArtifactStorage(base_dir=tmp_path / "artifacts")
    with pytest.raises(ArtifactValidationError):
        storage.save_artifact("job-corrupt-1", "bad.pptx", b"")

    with pytest.raises(ArtifactValidationError):
        storage.save_artifact("job-corrupt-2", "bad.pptx", b"NOT_A_ZIP_FILE")

"""Sandboxed artifact storage manager with path traversal defense and OpenXML verification."""

import io
import logging
import os
import re
import shutil
import time
import zipfile
from pathlib import Path

from backend.app.config import Settings, get_settings
from backend.app.core.errors import (
    ArtifactNotFoundError,
    ArtifactSecurityError,
    ArtifactValidationError,
)

logger = logging.getLogger(__name__)

SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
SAFE_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{1,128}$")


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal and illegal filesystem characters."""
    if not filename:
        return "Presentation.pptx"
    
    # Strip Windows drive prefix if present (e.g. C:)
    clean = re.sub(r"^[a-zA-Z]:", "", filename.strip())
    # Extract the final component of any path
    clean = clean.replace("\\", "/").rstrip("/").split("/")[-1]
    # Replace any unsafe characters with underscore
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean)
    # Defang consecutive dots and trim leading/trailing dots/underscores
    clean = re.sub(r"\.\.+", "_", clean).strip("._")
    
    if not clean.lower().endswith(".pptx"):
        clean = f"{clean}.pptx" if clean else "Presentation.pptx"
    return clean[:100]




def is_safe_id(identifier: str) -> bool:
    """Validate that an ID contains only safe alphanumeric/hyphen/underscore characters."""
    if not identifier or not isinstance(identifier, str):
        return False
    if ".." in identifier or "/" in identifier or "\\" in identifier or "\x00" in identifier:
        return False
    return bool(SAFE_ID_PATTERN.match(identifier))


class ArtifactStorage:
    """Sandboxed storage for generated presentation artifacts."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        settings: Settings = get_settings()
        self.base_dir = Path(base_dir or settings.artifact_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_job_dir(self, job_id: str) -> Path:
        """Resolve and validate sandboxed job directory path."""
        if not is_safe_id(job_id):
            raise ArtifactSecurityError(f"Invalid or unsafe job identifier: '{job_id}'")

        job_dir = (self.base_dir / job_id).resolve()
        base_resolved = self.base_dir.resolve()

        # Ensure path stays strictly inside base_dir
        try:
            job_dir.relative_to(base_resolved)
        except ValueError:
            raise ArtifactSecurityError(f"Path traversal detected for job ID: '{job_id}'")

        return job_dir

    def save_artifact(self, job_id: str, filename: str, data: bytes) -> Path:
        """Save raw binary artifact into isolated job directory."""
        if not data or len(data) == 0:
            raise ArtifactValidationError("Cannot save empty artifact payload")

        # Validate PPTX package integrity before writing
        if not self.validate_pptx_package(data):
            raise ArtifactValidationError("Corrupted or invalid OpenXML PowerPoint package payload")

        job_dir = self._get_job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)

        clean_name = sanitize_filename(filename)
        artifact_path = (job_dir / clean_name).resolve()

        try:
            artifact_path.relative_to(job_dir)
        except ValueError:
            raise ArtifactSecurityError("Path traversal attempt in artifact filename")

        with open(artifact_path, "wb") as f:
            f.write(data)

        logger.info(
            "Artifact saved successfully",
            extra={"job_id": job_id, "size_bytes": len(data), "path": str(artifact_path)},
        )
        return artifact_path

    def get_artifact(self, job_id: str) -> tuple[bytes, str, Path] | None:
        """Retrieve binary payload, filename, and path for a completed job."""
        job_dir = self._get_job_dir(job_id)
        if not job_dir.exists() or not job_dir.is_dir():
            return None

        # Find first .pptx file in directory
        pptx_files = sorted(job_dir.glob("*.pptx"))
        if not pptx_files:
            return None

        target_file = pptx_files[0].resolve()
        try:
            target_file.relative_to(job_dir)
        except ValueError:
            raise ArtifactSecurityError("Artifact path escape detected")

        with open(target_file, "rb") as f:
            data = f.read()

        if not self.validate_pptx_package(data):
            logger.error("Artifact package corrupted on disk", extra={"job_id": job_id})
            return None

        return data, target_file.name, target_file

    def get_artifact_path(self, job_id: str) -> Path | None:
        """Get absolute path to job artifact if it exists."""
        try:
            job_dir = self._get_job_dir(job_id)
            if not job_dir.exists() or not job_dir.is_dir():
                return None

            pptx_files = sorted(job_dir.glob("*.pptx"))
            if not pptx_files:
                return None
            target_file = pptx_files[0].resolve()
            target_file.relative_to(job_dir)
            return target_file
        except (ValueError, ArtifactSecurityError):
            return None

    def delete_artifact(self, job_id: str) -> bool:
        """Delete isolated artifact directory for a job."""
        try:
            if not is_safe_id(job_id):
                return False
            job_dir = self._get_job_dir(job_id)
            if job_dir.exists() and job_dir.is_dir():
                shutil.rmtree(job_dir, ignore_errors=True)
                logger.info("Artifact directory cleaned", extra={"job_id": job_id})
                return True
            return False
        except Exception as e:
            logger.warning("Failed to delete artifact", extra={"job_id": job_id, "error": str(e)})
            return False

    def cleanup_expired_artifacts(self, ttl_seconds: int | None = None) -> int:
        """Delete artifact directories older than configured TTL."""
        settings = get_settings()
        ttl = ttl_seconds if ttl_seconds is not None else settings.artifact_ttl_seconds
        now = time.time()
        cleaned_count = 0

        if not self.base_dir.exists():
            return 0

        for item in self.base_dir.iterdir():
            if item.is_dir() and is_safe_id(item.name):
                try:
                    mtime = item.stat().st_mtime
                    if (now - mtime) > ttl:
                        shutil.rmtree(item, ignore_errors=True)
                        cleaned_count += 1
                except Exception as e:
                    logger.warning("Error during artifact TTL cleanup", extra={"item": item.name, "error": str(e)})

        if cleaned_count > 0:
            logger.info("Expired artifacts cleanup finished", extra={"cleaned_count": cleaned_count})
        return cleaned_count

    @staticmethod
    def validate_pptx_package(data_or_path: bytes | Path) -> bool:
        """Validate OpenXML presentation zip package headers and required parts."""
        try:
            stream = io.BytesIO(data_or_path) if isinstance(data_or_path, bytes) else data_or_path
            with zipfile.ZipFile(stream, "r") as zf:
                namelist = set(zf.namelist())
                return (
                    "[Content_Types].xml" in namelist
                    and "ppt/presentation.xml" in namelist
                )
        except Exception:
            return False


# Global default artifact storage singleton
default_artifact_storage = ArtifactStorage()


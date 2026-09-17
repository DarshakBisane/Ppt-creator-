"""Hardening test fixtures and realistic PPTX generators."""

import io
import zipfile
import pytest
from backend.app.ai.fake_provider import FakeAIProvider
from backend.app.artifacts.storage import ArtifactStorage
from backend.app.jobs.store import MemoryJobStore


def create_minimal_valid_pptx_bytes() -> bytes:
    """Construct an in-memory valid OpenXML PPTX binary payload."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="xml" ContentType="application/xml"/>'
            b'<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            b"</Types>",
        )
        zf.writestr(
            "ppt/presentation.xml",
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            b"<p:sldMasterIdLst/>"
            b"<p:sldIdLst/>"
            b"</p:presentation>",
        )
        zf.writestr(
            "ppt/slides/slide1.xml",
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            b"<p:cSld><p:spTree><p:nvGrpSpPr/><p:grpSpPr/></p:spTree></p:cSld>"
            b"</p:sld>",
        )
    return buf.getvalue()


def create_multi_slide_pptx_bytes(num_slides: int = 3) -> bytes:
    """Construct a multi-slide PPTX binary payload."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="xml" ContentType="application/xml"/>'
            b'<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            b"</Types>",
        )
        zf.writestr(
            "ppt/presentation.xml",
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>',
        )
        for i in range(1, num_slides + 1):
            zf.writestr(
                f"ppt/slides/slide{i}.xml",
                f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
                f"<p:cSld><p:spTree><p:nvGrpSpPr/><p:grpSpPr/></p:spTree></p:cSld>"
                f"</p:sld>".encode("utf-8"),
            )
    return buf.getvalue()


def create_xxe_pptx_bytes() -> bytes:
    """Construct a PPTX payload with an embedded external entity declaration."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b"<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>"
            b"<Types><Default Extension='xml' ContentType='application/xml'/></Types>",
        )
        zf.writestr("ppt/presentation.xml", b"<p:presentation/>")
    return buf.getvalue()


def create_traversal_pptx_bytes() -> bytes:
    """Construct a zip file containing path traversal entries."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("../../evil.txt", b"malicious content")
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr("ppt/presentation.xml", b"<p:presentation/>")
    return buf.getvalue()


@pytest.fixture
def valid_pptx_bytes() -> bytes:
    return create_minimal_valid_pptx_bytes()


@pytest.fixture
def multi_slide_pptx_bytes() -> bytes:
    return create_multi_slide_pptx_bytes(3)


@pytest.fixture
def xxe_pptx_bytes() -> bytes:
    return create_xxe_pptx_bytes()


@pytest.fixture
def traversal_pptx_bytes() -> bytes:
    return create_traversal_pptx_bytes()


@pytest.fixture
def isolated_job_store() -> MemoryJobStore:
    return MemoryJobStore()


@pytest.fixture
def isolated_artifact_storage(tmp_path) -> ArtifactStorage:
    return ArtifactStorage(base_dir=tmp_path / "artifacts")


@pytest.fixture
def fake_ai() -> FakeAIProvider:
    return FakeAIProvider()

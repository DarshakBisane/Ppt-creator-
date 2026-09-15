"""Tests for safe OpenXML package inspector and security boundaries."""

import io
import zipfile
import pytest

from backend.app.reference.exceptions import (
    InvalidReferencePPTXError,
    ReferencePackageTooLargeError,
    ReferenceXMLSecurityError,
)
from backend.app.reference.inspector import SafePPTXPackage, safe_parse_xml


def test_inspector_valid_pptx(dark_theme_pptx_bytes: bytes) -> None:
    """Verify inspection of valid in-memory PPTX package."""
    pkg = SafePPTXPackage(dark_theme_pptx_bytes)
    assert "[Content_Types].xml" in pkg.file_names
    assert "ppt/presentation.xml" in pkg.file_names
    assert len(pkg.get_slide_parts()) == 2
    pkg.close()


def test_inspector_rejects_corrupted_zip() -> None:
    """Verify rejection of non-zip or corrupted binary data."""
    corrupt_bytes = b"NOT_A_VALID_ZIP_HEADER_DATA"
    with pytest.raises(InvalidReferencePPTXError):
        SafePPTXPackage(corrupt_bytes)


def test_inspector_rejects_zip_missing_presentation_xml() -> None:
    """Verify rejection of arbitrary zip archives missing PowerPoint structure."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types></Types>")
        zf.writestr("random.txt", "hello")
    buf.seek(0)

    with pytest.raises(InvalidReferencePPTXError):
        SafePPTXPackage(buf.read())


def test_safe_parse_xml_rejects_entity_declarations() -> None:
    """Verify that safe XML parser forbids external entity expansion (XXE protection)."""
    malicious_xml = b"""<?xml version="1.0"?>
    <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
    <root>&xxe;</root>"""

    with pytest.raises(ReferenceXMLSecurityError):
        safe_parse_xml(malicious_xml, "test_part")


def test_inspector_rejects_excessive_file_count() -> None:
    """Verify protection against zip bombs with excessive files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("ppt/presentation.xml", "<p:presentation/>")
        for i in range(550):
            zf.writestr(f"file_{i}.xml", "<data/>")
    buf.seek(0)

    with pytest.raises(ReferencePackageTooLargeError):
        SafePPTXPackage(buf.read())

"""Tests verifying reference PPTX archive security, XML entity defenses, and ZIP bomb limits."""

import io
import zipfile
import pytest

from backend.app.reference.exceptions import (
    InvalidReferencePPTXError,
    ReferencePackageTooLargeError,
    ReferenceXMLSecurityError,
)
from backend.app.reference.inspector import SafePPTXPackage, safe_parse_xml


def test_safe_pptx_package_valid_presentation(valid_pptx_bytes, multi_slide_pptx_bytes):
    """Legitimate PPTX archives parse and list components without error."""
    pkg = SafePPTXPackage(valid_pptx_bytes)
    assert "[Content_Types].xml" in pkg.file_names
    assert len(pkg.get_slide_parts()) == 1
    pkg.close()

    multi_pkg = SafePPTXPackage(multi_slide_pptx_bytes)
    assert len(multi_pkg.get_slide_parts()) == 3
    multi_pkg.close()


def test_safe_pptx_package_rejects_path_traversal(traversal_pptx_bytes):
    """PPTX packages containing ../ traversal entries are rejected."""
    with pytest.raises(ReferenceXMLSecurityError) as exc_info:
        SafePPTXPackage(traversal_pptx_bytes)
    assert "Suspicious path" in str(exc_info.value)


def test_safe_pptx_package_rejects_absolute_path():
    """PPTX packages containing leading / or Windows drive paths are rejected."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("/root/evil.xml", b"<evil/>")
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr("ppt/presentation.xml", b"<p:presentation/>")

    with pytest.raises(ReferenceXMLSecurityError):
        SafePPTXPackage(buf.getvalue())

    buf2 = io.BytesIO()
    with zipfile.ZipFile(buf2, "w") as zf:
        zf.writestr("C:\\Windows\\system32\\evil.xml", b"<evil/>")
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr("ppt/presentation.xml", b"<p:presentation/>")

    with pytest.raises(ReferenceXMLSecurityError):
        SafePPTXPackage(buf2.getvalue())


def test_safe_pptx_package_rejects_control_characters():
    """PPTX packages with control characters in entry names are rejected."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("ppt/slides/slide\x07.xml", b"<p:sld/>")
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr("ppt/presentation.xml", b"<p:presentation/>")

    with pytest.raises(ReferenceXMLSecurityError):
        SafePPTXPackage(buf.getvalue())



def test_safe_parse_xml_rejects_xxe():
    """XML content containing <!ENTITY or external DTD references is rejected."""
    xxe_xml = b'<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>'
    with pytest.raises(ReferenceXMLSecurityError) as exc_info:
        safe_parse_xml(xxe_xml, part_name="test_xxe.xml")
    assert "Forbidden DTD or entity declaration" in str(exc_info.value)


def test_safe_parse_xml_rejects_system_and_public_entities():
    """XML content containing SYSTEM or PUBLIC entity indicators is rejected."""
    system_xml = b'<?xml version="1.0"?><!DOCTYPE test SYSTEM "http://evil.com/dtd"><test/>'
    with pytest.raises(ReferenceXMLSecurityError):
        safe_parse_xml(system_xml, part_name="system.xml")

    public_xml = b'<?xml version="1.0"?><!DOCTYPE test PUBLIC "-//EVIL//DTD" "http://evil.com"><test/>'
    with pytest.raises(ReferenceXMLSecurityError):
        safe_parse_xml(public_xml, part_name="public.xml")


def test_safe_parse_xml_rejects_malformed_xml():
    """Malformed XML triggers InvalidReferencePPTXError."""
    bad_xml = b'<?xml version="1.0"?><unclosed_tag><other></unclosed_tag>'
    with pytest.raises(InvalidReferencePPTXError):
        safe_parse_xml(bad_xml, part_name="bad.xml")


def test_safe_pptx_package_rejects_non_zip():
    """Non-zip files trigger InvalidReferencePPTXError."""
    with pytest.raises(InvalidReferencePPTXError):
        SafePPTXPackage(b"This is just plain text, not a zip file.")


def test_safe_pptx_package_rejects_missing_presentation_xml():
    """ZIP missing ppt/presentation.xml is rejected."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr("some_other_file.xml", b"<xml/>")

    with pytest.raises(InvalidReferencePPTXError) as exc_info:
        SafePPTXPackage(buf.getvalue())
    assert "Missing ppt/presentation.xml" in str(exc_info.value)

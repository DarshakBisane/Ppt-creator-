"""Safe OpenXML PowerPoint package inspector with security bounds and XML entity defenses."""

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import BinaryIO

from backend.app.reference.exceptions import (
    InvalidReferencePPTXError,
    ReferencePackageTooLargeError,
    ReferenceXMLSecurityError,
)

# Security Limits
MAX_ZIP_ENTRIES: int = 500
MAX_UNCOMPRESSED_TOTAL_BYTES: int = 50 * 1024 * 1024  # 50 MB
MAX_SINGLE_XML_BYTES: int = 10 * 1024 * 1024  # 10 MB

# XML Entity Defense Pattern
FORBIDDEN_XML_PATTERNS = [
    re.compile(rb"<!ENTITY", re.IGNORECASE),
    re.compile(rb"<!DOCTYPE[^>]*\[", re.IGNORECASE),
    re.compile(rb"SYSTEM\s+[\"']", re.IGNORECASE),
    re.compile(rb"PUBLIC\s+[\"']", re.IGNORECASE),
]

# Path Traversal Detection
PATH_TRAVERSAL_REGEX = re.compile(r"(^\.\./|\.\./|/|\\|\.\.\\)")


def safe_parse_xml(xml_bytes: bytes, part_name: str = "XML part") -> ET.Element:
    """Safely parse XML bytes enforcing entity and size restrictions."""
    if len(xml_bytes) > MAX_SINGLE_XML_BYTES:
        raise ReferencePackageTooLargeError(
            f"XML part '{part_name}' exceeds size limit ({len(xml_bytes)} > {MAX_SINGLE_XML_BYTES} bytes)."
        )

    for pattern in FORBIDDEN_XML_PATTERNS:
        if pattern.search(xml_bytes):
            raise ReferenceXMLSecurityError(
                f"Security violation: Forbidden DTD or entity declaration in '{part_name}'."
            )

    try:
        return ET.fromstring(xml_bytes)
    except ET.ParseError as parse_err:
        raise InvalidReferencePPTXError(f"Malformed XML in '{part_name}': {str(parse_err)}") from parse_err


class SafePPTXPackage:
    """Safe wrapper over a PowerPoint ZIP package with validation and safe XML access."""

    def __init__(self, source: bytes | str | BinaryIO) -> None:
        self._raw_zip: zipfile.ZipFile = self._open_zip(source)
        self._validate_archive_security()
        self._namelist: list[str] = sorted(self._raw_zip.namelist())
        self._validate_pptx_structure()

    def _open_zip(self, source: bytes | str | BinaryIO) -> zipfile.ZipFile:
        try:
            if isinstance(source, bytes):
                return zipfile.ZipFile(io.BytesIO(source), "r")
            elif isinstance(source, str):
                return zipfile.ZipFile(source, "r")
            else:
                return zipfile.ZipFile(source, "r")
        except zipfile.BadZipFile as bad_zip:
            raise InvalidReferencePPTXError("Uploaded file is not a valid ZIP/PPTX archive.") from bad_zip
        except Exception as exc:
            raise InvalidReferencePPTXError(f"Cannot open presentation package: {str(exc)}") from exc

    def _validate_archive_security(self) -> None:
        infolist = self._raw_zip.infolist()

        if len(infolist) > MAX_ZIP_ENTRIES:
            raise ReferencePackageTooLargeError(
                f"Presentation contains too many files ({len(infolist)} > {MAX_ZIP_ENTRIES})."
            )

        total_uncompressed = sum(info.file_size for info in infolist)
        if total_uncompressed > MAX_UNCOMPRESSED_TOTAL_BYTES:
            raise ReferencePackageTooLargeError(
                f"Uncompressed presentation size exceeds limit ({total_uncompressed} > {MAX_UNCOMPRESSED_TOTAL_BYTES} bytes)."
            )

        # Path traversal checks
        for info in infolist:
            name = info.filename
            if name.startswith("/") or name.startswith("\\") or ".." in name:
                raise ReferenceXMLSecurityError(f"Suspicious path in PPTX package: {name}")

    def _validate_pptx_structure(self) -> None:
        if "[Content_Types].xml" not in self._namelist:
            raise InvalidReferencePPTXError("Missing [Content_Types].xml in presentation package.")
        if "ppt/presentation.xml" not in self._namelist:
            raise InvalidReferencePPTXError("Missing ppt/presentation.xml in presentation package.")

    @property
    def file_names(self) -> list[str]:
        return self._namelist

    def read_bytes(self, filename: str) -> bytes:
        """Read raw bytes for an internal ZIP entry."""
        if filename not in self._namelist:
            raise InvalidReferencePPTXError(f"Entry '{filename}' not found in presentation package.")
        return self._raw_zip.read(filename)

    def read_xml(self, filename: str) -> ET.Element:
        """Safely parse and return the root Element for an internal XML entry."""
        raw_bytes = self.read_bytes(filename)
        return safe_parse_xml(raw_bytes, part_name=filename)

    def get_theme_parts(self) -> list[str]:
        """Return list of theme XML filenames in deterministic order."""
        return [f for f in self._namelist if f.startswith("ppt/theme/theme") and f.endswith(".xml")]

    def get_slide_parts(self) -> list[str]:
        """Return list of slide XML filenames in natural numeric order."""
        slide_files = [f for f in self._namelist if f.startswith("ppt/slides/slide") and f.endswith(".xml")]
        # Deterministic natural sort: slide1, slide2, slide10
        def _slide_num(s: str) -> int:
            m = re.search(r"slide(\d+)\.xml", s)
            return int(m.group(1)) if m else 0

        return sorted(slide_files, key=_slide_num)

    def get_slide_master_parts(self) -> list[str]:
        """Return list of slideMaster XML filenames."""
        return [f for f in self._namelist if f.startswith("ppt/slideMasters/slideMaster") and f.endswith(".xml")]

    def close(self) -> None:
        self._raw_zip.close()

"""Security and prompt-injection defense tests for the reference PPT analyzer."""

import pytest

from backend.app.reference.analyzer import ReferencePPTAnalyzer


def test_malicious_prompt_injection_text_does_not_leak(injection_payload_pptx_bytes: bytes) -> None:
    """Verify that malicious instructions inside reference slides/notes are strictly quarantined.
    
    Zero slide text or prompt injection phrases should ever leak into the extracted DesignContext
    or DesignSystem.
    """
    analyzer = ReferencePPTAnalyzer()
    design_context, design_system, summary = analyzer.analyze(injection_payload_pptx_bytes)

    # Convert entire extracted data to JSON string for full text inspection
    context_dump = design_context.model_dump_json().lower()
    system_dump = design_system.model_dump_json().lower()

    # Verify forbidden malicious instruction keywords do NOT exist anywhere in the extracted models
    forbidden_terms = [
        "system override",
        "api_secret_key",
        "prompt injection",
        "delete all database",
        "admin password",
        "previous instructions",
    ]

    for term in forbidden_terms:
        assert term not in context_dump, f"Security violation: Found '{term}' in extracted DesignContext"
        assert term not in system_dump, f"Security violation: Found '{term}' in extracted DesignSystem"

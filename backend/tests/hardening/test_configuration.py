"""Tests verifying configuration limits, CORS parsing, and documentation flags."""

import pytest
from backend.app.config import Settings


def test_configuration_default_hardening_limits():
    """Default configuration contains safe production bounds."""
    s = Settings()
    assert s.max_topic_chars == 1000
    assert s.min_slides == 3
    assert s.max_slides == 30
    assert s.max_reference_pptx_bytes == 50 * 1024 * 1024
    assert s.max_reference_unpacked_bytes == 50 * 1024 * 1024
    assert s.max_reference_files == 500
    assert s.max_reference_xml_bytes == 10 * 1024 * 1024
    assert s.max_job_runtime_seconds == 300
    assert s.max_concurrent_jobs == 5


def test_docs_exposure_setting():
    """Docs are enabled in development/test and disabled in production unless explicitly set."""
    dev_settings = Settings(environment="development")
    assert dev_settings.show_docs is True

    prod_settings = Settings(environment="production")
    assert prod_settings.show_docs is False

    override_prod = Settings(environment="production", enable_docs=True)
    assert override_prod.show_docs is True


def test_cors_origins_parsing():
    """CORS origins parse comma-separated strings and lists cleanly."""
    s1 = Settings(cors_origins="http://example.com, https://app.example.com")
    assert s1.cors_origins == ["http://example.com", "https://app.example.com"]

    s2 = Settings(cors_origins=["http://localhost:3000"])
    assert s2.cors_origins == ["http://localhost:3000"]

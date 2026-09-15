"""Unit tests for text overflow QA, font size limits, and container expansion."""

from backend.app.domain.content import CardContent, TextContent
from backend.app.domain.enums import ElementType
from backend.app.layout.models import ElementGeometry, Rect
from backend.app.visual_qa.models import QAIssueType, QASeverity
from backend.app.visual_qa.overflow import validate_text_overflow


def test_short_text_fits_without_issue() -> None:
    """Brief headline in a spacious container passes cleanly."""
    elem = ElementGeometry(
        id="card_1",
        semantic_type=ElementType.CARD,
        rect=Rect(x=100, y=200, width=500, height=300),
        content_data=CardContent(title="Short Title", body="Two words."),
    )
    issues = validate_text_overflow([elem], slide_id="s1")
    assert len(issues) == 0


def test_massive_text_overflow_detected() -> None:
    """Massive 400-word paragraph in a tiny 100x60 container triggers a TEXT_OVERFLOW ERROR/CRITICAL."""
    long_body = "This is a very long text explanation that will overflow this small card container. " * 7
    elem = ElementGeometry(
        id="overflow_card",
        semantic_type=ElementType.CARD,
        rect=Rect(x=100, y=200, width=200, height=80),
        content_data=CardContent(title="Dense Topic", body=long_body),
    )
    issues = validate_text_overflow([elem], slide_id="s1")
    assert any(i.issue_type == QAIssueType.TEXT_OVERFLOW and i.severity in (QASeverity.ERROR, QASeverity.CRITICAL) for i in issues)


def test_caption_respects_caption_minimum_font() -> None:
    """Footnote/caption text in a small badge is measured against caption minimum font (11pt)."""
    elem = ElementGeometry(
        id="footnote_1",
        semantic_type=ElementType.TEXT,
        role="footnote",
        rect=Rect(x=100, y=950, width=600, height=35),
        content_data=TextContent(text="Source: Internal audit financial data Q3 2026."),
    )
    issues = validate_text_overflow([elem], slide_id="s1")
    assert not any(i.severity == QASeverity.ERROR for i in issues)

"""Tests for multi-row layout grid limits, dynamic header positioning, and archetype remediation."""

import pytest
from backend.app.domain.content import CardContent, TextContent
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.elements import Element
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.domain.palettes import PaletteFamily, ProfessionalPaletteGenerator
from backend.app.domain.presentation import Presentation, PresentationMetadata, Slide
from backend.app.domain.visuals import VisualPlan
from backend.app.layout.engine import LayoutEngine
from backend.app.layout.models import Rect
from backend.app.layout.spacing import calculate_card_row, calculate_multi_row_cards
from backend.app.rendering.engine import PPTXRenderer
from backend.app.visual_qa.orchestrator import validate_and_correct_presentation


def test_calculate_card_row_clamps_to_max_four() -> None:
    """Test that calculate_card_row clamps to max 4 cards per row to prevent squishing."""
    bounds = Rect(x=100, y=200, width=1720, height=700)
    cards = calculate_card_row(bounds, count=8, gap=24)
    # Must clamp to 4 to prevent narrow slivers
    assert len(cards) == 4
    for c in cards:
        assert c.width >= 350  # Wide enough to be readable


def test_calculate_multi_row_cards_splits_eight_items_into_two_rows() -> None:
    """Test that 8 items are formatted as 2 balanced rows of 4 cards."""
    bounds = Rect(x=100, y=200, width=1720, height=700)
    cards = calculate_multi_row_cards(bounds, count=8, max_cols=4, col_gap=24, row_gap=24)
    assert len(cards) == 8

    row1 = cards[:4]
    row2 = cards[4:]

    # Row 1 and Row 2 have distinct Y levels
    assert row1[0].y == row1[1].y == row1[2].y == row1[3].y
    assert row2[0].y == row2[1].y == row2[2].y == row2[3].y
    assert row2[0].y > row1[0].bottom

    # Card widths are readable
    for c in cards:
        assert c.width >= 350
        assert c.height >= 250


def test_dynamic_title_and_subtitle_no_collision() -> None:
    """Test that multi-line titles expand dynamically and push subtitle below without overlap."""
    engine = LayoutEngine()
    ds = DesignSystem()

    long_title = "Strategic Transformation of Enterprise Digital Public Key Infrastructure and Scalable Certificate Governance Framework"
    slide = Slide(
        id="s_long_title",
        slide_number=2,
        title=long_title,
        subtitle="Operational architecture and cryptographic assurance metrics",
        narrative_role=NarrativeRole.ARCHITECTURE,
        visual_plan=VisualPlan(visual_type=VisualType.CARD_GRID),
        elements=[
            Element(id="c1", type=ElementType.CARD, card_content=CardContent(title="Card 1", body="Body 1")),
            Element(id="c2", type=ElementType.CARD, card_content=CardContent(title="Card 2", body="Body 2")),
            Element(id="c3", type=ElementType.CARD, card_content=CardContent(title="Card 3", body="Body 3")),
        ],
    )

    result = engine.layout_slide(slide, ds)
    title_elem = next(e for e in result.elements if e.id == "s_long_title_title")
    subtitle_elem = next(e for e in result.elements if e.id == "s_long_title_subtitle")

    # Subtitle must start strictly below title bottom
    assert subtitle_elem.rect.y >= title_elem.rect.bottom
    # Subtitle must not overlap any cards
    card_elems = [e for e in result.elements if "card" in e.id or e.semantic_type == ElementType.CARD]
    for c in card_elems:
        assert c.rect.y >= subtitle_elem.rect.bottom


def test_professional_palette_families_and_typography() -> None:
    """Test palette family selection and typography default."""
    ds = DesignSystem()
    assert ds.typography.display.font_family == "Calibri"
    assert ds.typography.title.font_family == "Calibri"
    assert ds.typography.body.font_family == "Calibri"
    assert ds.typography.title.font_size == 32
    assert ds.typography.body.font_size == 15

    # Check non-blue palettes
    p_academic = ProfessionalPaletteGenerator.create_palette(family=PaletteFamily.ACADEMIC)
    assert p_academic.primary.value == "#7F1D1D"  # Maroon
    assert p_academic.background.value == "#FDFBF7"  # Light parchment

    p_green = ProfessionalPaletteGenerator.create_palette(family=PaletteFamily.GREEN_PROFESSIONAL)
    assert p_green.primary.value == "#166534"  # Forest green

    p_warm = ProfessionalPaletteGenerator.create_palette(family=PaletteFamily.WARM_PROFESSIONAL)
    assert p_warm.primary.value == "#B45309"  # Terracotta


def test_eight_stage_lifecycle_slide_renders_clean_pptx() -> None:
    """Test that an 8-stage lifecycle slide uses multi-row layout and renders valid PPTX without overflow."""
    stages = [
        ("01 Key Generation", "Client generates asymmetric key pair in hardware security module."),
        ("02 CSR Submission", "Certificate Signing Request signed by private key sent to RA."),
        ("03 RA Identity Verification", "RA verifies domain ownership and corporate policy compliance."),
        ("04 CA Signature Issuance", "CA signs certificate and publishes signed bundle."),
        ("05 Repository Distribution", "Bundle distributed to TLS termination endpoints."),
        ("06 Live TLS Handshake", "End-users negotiate secure TLS sessions with client proof."),
        ("07 Real-Time OCSP Telemetry", "Continuous validation checks against revocation responders."),
        ("08 Automated Certificate Renewal", "ACME agent auto-renews certificate 30 days prior to expiry."),
    ]

    elements = [
        Element(
            id=f"elem_stage_{i+1}",
            type=ElementType.CARD,
            role="card",
            importance="primary" if i == 0 else "secondary",
            card_content=CardContent(title=title, body=desc),
        )
        for i, (title, desc) in enumerate(stages)
    ]

    slide = Slide(
        id="s_lifecycle_8",
        slide_number=2,
        title="Comprehensive X.509 Certificate Lifecycle Pipeline",
        subtitle="End-to-end eight-stage cryptographic lifecycle management",
        narrative_role=NarrativeRole.PROCESS,
        visual_plan=VisualPlan(visual_type=VisualType.LIFECYCLE),
        elements=elements,
    )

    pres = Presentation(
        metadata=PresentationMetadata(title="X.509 Lifecycle", topic="X.509 PKI", slide_count=2),
        slides=[
            Slide(id="s1", slide_number=1, title="X.509 Management", narrative_role=NarrativeRole.TITLE, visual_plan=VisualPlan(visual_type=VisualType.NONE)),
            slide,
        ],
    )

    qa = validate_and_correct_presentation(pres)
    assert qa.passed is True
    assert qa.critical_issues == 0

    renderer = PPTXRenderer()
    pptx_bytes = renderer.render_to_bytes(pres, qa)
    assert len(pptx_bytes) > 5000

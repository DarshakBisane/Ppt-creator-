"""Unit tests for visual density metrics and archetype-aware thresholds."""

from backend.app.domain.enums import ElementType, VisualType
from backend.app.layout.models import ElementGeometry, Rect
from backend.app.visual_qa.density import compute_slide_density
from backend.app.visual_qa.models import DensityLevel, QAIssueType


def test_sparse_hero_slide_density() -> None:
    """A minimal Hero slide with 1 prominent card has LOW or BALANCED density."""
    elem = ElementGeometry(
        id="hero_title",
        semantic_type=ElementType.HEADING,
        rect=Rect(x=200, y=300, width=1500, height=150),
        role="hero_title",
    )
    metrics, issues = compute_slide_density([elem], VisualType.HERO, slide_id="s1")
    assert metrics.density_level in (DensityLevel.LOW, DensityLevel.BALANCED)
    assert metrics.is_balanced is True
    assert len(issues) == 0


def test_dense_architecture_archetype_tolerance() -> None:
    """An architecture diagram with 12 node elements is tolerated as BALANCED or HIGH without critical alarms."""
    nodes: list[ElementGeometry] = []
    for i in range(12):
        nodes.append(
            ElementGeometry(
                id=f"arch_node_{i}",
                semantic_type=ElementType.CARD,
                rect=Rect(x=100 + (i % 4) * 400, y=200 + (i // 4) * 200, width=360, height=160),
                role="system_node",
            )
        )
    metrics, issues = compute_slide_density(nodes, VisualType.ARCHITECTURE, slide_id="s1")
    assert metrics.element_count == 12
    # Should not produce critical density warnings for Architecture archetype
    assert not any(i.issue_type == QAIssueType.DENSITY_HIGH and "CRITICAL" in i.message for i in issues)


def test_overcrowded_critical_density_flagged() -> None:
    """A slide packed with 35 overlapping cards and huge occupied area is rated CRITICAL."""
    cards: list[ElementGeometry] = []
    for i in range(35):
        cards.append(
            ElementGeometry(
                id=f"card_{i}",
                semantic_type=ElementType.CARD,
                rect=Rect(x=50, y=100 + (i * 25), width=1800, height=200),
                role="card",
            )
        )
    metrics, issues = compute_slide_density(cards, VisualType.CARD_GRID, slide_id="s1")
    assert metrics.density_level == DensityLevel.CRITICAL
    assert any(i.issue_type == QAIssueType.DENSITY_HIGH for i in issues)

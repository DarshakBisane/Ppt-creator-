"""Slide layout resolver coordinating header placement, content bounds, and archetype dispatch."""

from backend.app.domain.canvas import CanvasSpec
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.enums import Alignment, ElementType
from backend.app.domain.presentation import Slide
from backend.app.layout.constants import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    CONTENT_BOTTOM,
    CONTENT_TOP,
    HEADER_HEIGHT,
    HEADER_TOP,
    SAFE_MARGIN_X,
    SAFE_MARGIN_Y,
)
from backend.app.layout.constraints import validate_child_containment, validate_rect_bounds
from backend.app.layout.models import (
    ConnectorGeometry,
    ElementGeometry,
    LayoutWarning,
    Rect,
    SlideLayoutResult,
)
from backend.app.layout.registry import LayoutRegistry, default_layout_registry
from backend.app.layout.spacing import SpacingContext, generate_ports


class SlideLayoutResolver:
    """Resolves geometric positions for a single slide within the 1920x1080 canvas."""

    def __init__(self, registry: LayoutRegistry | None = None) -> None:
        self.registry = registry or default_layout_registry

    def resolve_slide(
        self,
        slide: Slide,
        design_system: DesignSystem | None = None,
    ) -> SlideLayoutResult:
        """Deterministically resolve a slide into full geometric coordinates."""
        ds = design_system or DesignSystem()
        ctx = SpacingContext(ds)
        all_warnings: list[LayoutWarning] = []
        all_elements: list[ElementGeometry] = []
        all_connectors: list[ConnectorGeometry] = []

        # 1. Slide Canvas Specification
        canvas = ds.canvas or CanvasSpec(width=CANVAS_WIDTH, height=CANVAS_HEIGHT)

        # 2. Slide 1 (Title Cover Slide) Dedicated Treatment
        if slide.narrative_role.value == "title" and slide.slide_number == 1:
            header_rect = None

            # Category / Presentation Badge
            badge_w = 260
            badge_rect = Rect(
                x=ctx.margin_x,
                y=100,
                width=badge_w,
                height=38,
            )
            badge_id = f"{slide.id}_cover_badge"
            all_elements.append(
                ElementGeometry(
                    id=badge_id,
                    semantic_type=ElementType.SHAPE,
                    rect=badge_rect,
                    alignment=Alignment.CENTER,
                    ports=generate_ports(badge_id, badge_rect),
                    role="narrative_badge",
                    importance="accent",
                    style_hints={"variant": "pill", "role": "title"},
                    content_data={"text": "EXECUTIVE BRIEFING"},
                )
            )

            # Master Title
            title_rect = Rect(
                x=ctx.margin_x,
                y=160,
                width=CANVAS_WIDTH - (ctx.margin_x * 2),
                height=240,
            )
            title_id = f"{slide.id}_title"
            all_elements.append(
                ElementGeometry(
                    id=title_id,
                    semantic_type=ElementType.HEADING,
                    rect=title_rect,
                    alignment=Alignment.LEFT,
                    ports=generate_ports(title_id, title_rect),
                    role="slide_title",
                    importance="primary",
                    style_hints={"variant": "cover_title"},
                    content_data={"text": slide.title},
                )
            )

            # Master Subtitle
            sub_text = slide.subtitle or slide.purpose or "A Strategic and Architectural Deep Dive"
            sub_rect = Rect(
                x=ctx.margin_x,
                y=420,
                width=CANVAS_WIDTH - (ctx.margin_x * 2),
                height=120,
            )
            sub_id = f"{slide.id}_subtitle"
            all_elements.append(
                ElementGeometry(
                    id=sub_id,
                    semantic_type=ElementType.TEXT,
                    rect=sub_rect,
                    alignment=Alignment.LEFT,
                    ports=generate_ports(sub_id, sub_rect),
                    role="slide_subtitle",
                    importance="secondary",
                    style_hints={"variant": "cover_subtitle"},
                    content_data={"text": sub_text},
                )
            )

            # Executive Takeaway / Mandate Card on Title Cover
            if slide.takeaway:
                takeaway_rect = Rect(
                    x=ctx.margin_x,
                    y=580,
                    width=CANVAS_WIDTH - (ctx.margin_x * 2),
                    height=90,
                )
                takeaway_id = f"{slide.id}_cover_takeaway"
                all_elements.append(
                    ElementGeometry(
                        id=takeaway_id,
                        semantic_type=ElementType.CARD,
                        rect=takeaway_rect,
                        alignment=Alignment.LEFT,
                        ports=generate_ports(takeaway_id, takeaway_rect),
                        role="takeaway",
                        importance="accent",
                        style_hints={"variant": "takeaway_banner"},
                        content_data={"title": "CORE THESIS", "body": slide.takeaway},
                    )
                )

            return SlideLayoutResult(
                slide_id=slide.id,
                slide_number=slide.slide_number,
                visual_type=slide.visual_plan.visual_type,
                narrative_role=slide.narrative_role,
                canvas=canvas,
                header_rect=header_rect,
                content_rect=Rect(x=ctx.margin_x, y=100, width=CANVAS_WIDTH - (ctx.margin_x * 2), height=CANVAS_HEIGHT - 200),
                elements=all_elements,
                connectors=all_connectors,
                warnings=all_warnings,
                metadata={"archetype": "TitleCoverResolver"},
            )

        # 3. Standard Body Slides (Header + Visual Core + Bottom Takeaway)
        header_h = HEADER_HEIGHT
        header_rect = Rect(
            x=ctx.margin_x,
            y=HEADER_TOP,
            width=CANVAS_WIDTH - (ctx.margin_x * 2),
            height=header_h,
        )

        # Slide Title Element
        title_w = header_rect.width - 220
        title_rect = Rect(
            x=header_rect.x,
            y=header_rect.y,
            width=title_w,
            height=50,
        )
        title_id = f"{slide.id}_title"
        all_elements.append(
            ElementGeometry(
                id=title_id,
                semantic_type=ElementType.HEADING,
                rect=title_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(title_id, title_rect),
                role="slide_title",
                importance="primary",
                content_data={"text": slide.title},
            )
        )

        # Slide Subtitle Element if present
        if slide.subtitle:
            sub_rect = Rect(
                x=header_rect.x,
                y=header_rect.y + 54,
                width=title_w,
                height=36,
            )
            sub_id = f"{slide.id}_subtitle"
            all_elements.append(
                ElementGeometry(
                    id=sub_id,
                    semantic_type=ElementType.TEXT,
                    rect=sub_rect,
                    alignment=Alignment.LEFT,
                    ports=generate_ports(sub_id, sub_rect),
                    role="slide_subtitle",
                    importance="secondary",
                    content_data={"text": slide.subtitle},
                )
            )

        # Narrative Role / Category Pill
        badge_w = 180
        badge_rect = Rect(
            x=header_rect.right - badge_w,
            y=header_rect.y + 6,
            width=badge_w,
            height=32,
        )
        badge_id = f"{slide.id}_narrative_badge"
        all_elements.append(
            ElementGeometry(
                id=badge_id,
                semantic_type=ElementType.SHAPE,
                rect=badge_rect,
                alignment=Alignment.CENTER,
                ports=generate_ports(badge_id, badge_rect),
                role="narrative_badge",
                importance="accent",
                style_hints={"variant": "pill", "role": slide.narrative_role.value},
                content_data={"text": slide.narrative_role.value.upper().replace("_", " ")},
            )
        )

        # Content Region calculation
        content_top_y = header_rect.bottom + ctx.section_gap
        has_takeaway = bool(slide.takeaway and len(slide.takeaway.strip()) >= 5)

        if has_takeaway:
            takeaway_h = 76
            takeaway_y = CONTENT_BOTTOM - takeaway_h
            content_h = max(200, (takeaway_y - ctx.row_gap) - content_top_y)
            content_rect = Rect(
                x=ctx.margin_x,
                y=content_top_y,
                width=CANVAS_WIDTH - (ctx.margin_x * 2),
                height=content_h,
            )

            # Dedicated Bottom Takeaway Banner
            takeaway_rect = Rect(
                x=ctx.margin_x,
                y=takeaway_y,
                width=CANVAS_WIDTH - (ctx.margin_x * 2),
                height=takeaway_h,
            )
            takeaway_id = f"{slide.id}_takeaway_banner"
            all_elements.append(
                ElementGeometry(
                    id=takeaway_id,
                    semantic_type=ElementType.CARD,
                    rect=takeaway_rect,
                    alignment=Alignment.LEFT,
                    ports=generate_ports(takeaway_id, takeaway_rect),
                    role="takeaway",
                    importance="accent",
                    style_hints={"variant": "takeaway_banner"},
                    content_data={"title": "KEY TAKEAWAY", "body": slide.takeaway},
                )
            )
        else:
            content_rect = Rect(
                x=ctx.margin_x,
                y=content_top_y,
                width=CANVAS_WIDTH - (ctx.margin_x * 2),
                height=CONTENT_BOTTOM - content_top_y,
            )

        # 4. Dispatch to Archetype Resolver
        archetype_resolver = self.registry.get_resolver(
            slide.visual_plan.visual_type,
            element_count=len(slide.elements),
        )

        body_elements, body_connectors, body_warnings = archetype_resolver.resolve(
            slide=slide,
            content_rect=content_rect,
            ctx=ctx,
        )

        all_elements.extend(body_elements)
        all_connectors.extend(body_connectors)
        all_warnings.extend(body_warnings)

        # 5. Geometric Constraints & Containment Validation
        for elem in all_elements:
            elem_warnings = validate_rect_bounds(elem.rect, element_id=elem.id)
            all_warnings.extend(elem_warnings)

        return SlideLayoutResult(
            slide_id=slide.id,
            slide_number=slide.slide_number,
            visual_type=slide.visual_plan.visual_type,
            narrative_role=slide.narrative_role,
            canvas=canvas,
            header_rect=header_rect,
            content_rect=content_rect,
            elements=all_elements,
            connectors=all_connectors,
            warnings=all_warnings,
            metadata={"archetype": archetype_resolver.__class__.__name__},
        )

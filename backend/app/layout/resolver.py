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
from backend.app.layout.text_measurer import estimate_text_dimensions


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

        # 2. Slide 1 (Title Cover Slide) Dedicated Dynamic Treatment
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

            # Master Title with dynamic measurement
            cover_title_w = CANVAS_WIDTH - (ctx.margin_x * 2)
            _, measured_c_title_h, _ = estimate_text_dimensions(
                text=slide.title,
                font_size=ds.typography.display.font_size,
                max_width=cover_title_w,
            )
            c_title_h = max(90, min(240, measured_c_title_h + 20))
            title_rect = Rect(
                x=ctx.margin_x,
                y=155,
                width=cover_title_w,
                height=c_title_h,
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

            # Master Subtitle positioned dynamically below Title
            sub_text = slide.subtitle or slide.purpose or "A Strategic and Architectural Deep Dive"
            _, measured_c_sub_h, _ = estimate_text_dimensions(
                text=sub_text,
                font_size=ds.typography.heading.font_size,
                max_width=cover_title_w,
            )
            c_sub_h = max(50, min(120, measured_c_sub_h + 16))
            sub_y = title_rect.bottom + 20
            sub_rect = Rect(
                x=ctx.margin_x,
                y=sub_y,
                width=cover_title_w,
                height=c_sub_h,
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

            # Executive Takeaway / Mandate Card on Title Cover positioned below Subtitle
            if slide.takeaway:
                takeaway_y = min(CANVAS_HEIGHT - 160, sub_rect.bottom + 30)
                takeaway_rect = Rect(
                    x=ctx.margin_x,
                    y=takeaway_y,
                    width=cover_title_w,
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

        # 3. Standard Body Slides (Dynamic Header + Visual Core + Bottom Takeaway)
        available_header_w = CANVAS_WIDTH - (ctx.margin_x * 2)
        badge_w = 180
        title_w = available_header_w - badge_w - ctx.column_gap

        # Measure title dimensions dynamically to handle wrapping cleanly
        title_font_size = ds.typography.title.font_size
        _, measured_title_h, title_lines = estimate_text_dimensions(
            text=slide.title,
            font_size=title_font_size,
            max_width=title_w,
        )
        title_h = max(44, min(100, measured_title_h + 6))

        title_rect = Rect(
            x=ctx.margin_x,
            y=HEADER_TOP,
            width=title_w,
            height=title_h,
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

        # Slide Subtitle Element positioned dynamically BELOW measured title
        if slide.subtitle:
            sub_font_size = ds.typography.body.font_size
            _, measured_sub_h, _ = estimate_text_dimensions(
                text=slide.subtitle,
                font_size=sub_font_size,
                max_width=title_w,
            )
            sub_h = max(26, min(56, measured_sub_h + 4))
            sub_y = title_rect.bottom + 4
            sub_rect = Rect(
                x=ctx.margin_x,
                y=sub_y,
                width=title_w,
                height=sub_h,
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
            header_bottom_y = sub_rect.bottom
        else:
            header_bottom_y = title_rect.bottom

        # Narrative Role / Category Pill at top right
        badge_rect = Rect(
            x=ctx.margin_x + available_header_w - badge_w,
            y=HEADER_TOP + 4,
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

        header_rect = Rect(
            x=ctx.margin_x,
            y=HEADER_TOP,
            width=available_header_w,
            height=header_bottom_y - HEADER_TOP,
        )

        # Content Region calculation
        content_top_y = header_bottom_y + ctx.section_gap
        has_takeaway = bool(slide.takeaway and len(slide.takeaway.strip()) >= 5)

        if has_takeaway:
            takeaway_h = 76
            takeaway_y = CONTENT_BOTTOM - takeaway_h
            content_h = max(180, (takeaway_y - ctx.row_gap) - content_top_y)
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

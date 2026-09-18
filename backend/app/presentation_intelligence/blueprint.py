"""Presentation Generation Blueprint models and deterministic mapper to canonical Presentation."""

import uuid
from pydantic import BaseModel, Field

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.domain.charts import ChartData, ChartSeries
from backend.app.domain.constants import CURRENT_SCHEMA_VERSION
from backend.app.domain.content import CardContent, KPIContent, TextContent
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.elements import Element
from backend.app.domain.enums import (
    ContentDepth,
    DataSource,
    ElementType,
    NarrativeRole,
    NarrativeStrategy,
    ProcessDirection,
    TimelineStatus,
    VisualType,
)
from backend.app.domain.palettes import ProfessionalPaletteGenerator
from backend.app.domain.presentation import (
    GenerationMetadata,
    Presentation,
    PresentationMetadata,
    Slide,
)
from backend.app.domain.tables import TableColumn, TableData, TableRow
from backend.app.domain.visuals import (
    ProcessFlowData,
    ProcessStep,
    TimelineData,
    TimelineMilestone,
    VisualPlan,
)
from backend.app.presentation_intelligence.topic_validator import SemanticTopicValidator
from backend.app.rendering.icons import get_semantic_icon


class ProcessStepBlueprint(BaseModel):
    order: int
    title: str
    description: str


class TimelineMilestoneBlueprint(BaseModel):
    label: str
    date: str
    description: str
    status: str = "planned"


class KPIBlueprint(BaseModel):
    label: str
    value: str
    context: str = ""
    trend: str = "up"


class ComparisonItemBlueprint(BaseModel):
    dimension: str
    option_a_value: str
    option_b_value: str
    notes: str = ""


class TableRowBlueprint(BaseModel):
    cells: list[str]


class SlideBlueprint(BaseModel):
    """Structured AI slide blueprint optimized for Gemini structured decoding."""

    slide_number: int
    title: str = Field(..., description="Action-oriented or insight-driven headline (e.g. 'Decentralized CA Architecture Eliminates Single Points of Failure')")
    subtitle: str = Field(..., description="Contextual subtitle explaining this slide's role in the presentation narrative")
    narrative_role: NarrativeRole = Field(default=NarrativeRole.CONTEXT)
    objective: str = Field(default="", description="Why this slide exists in the story")
    key_message: str = Field(default="", description="Core analytical thesis of the slide")
    takeaway: str = Field(..., description="Clear, actionable executive takeaway or strategic conclusion")
    visual_type: VisualType = Field(default=VisualType.CARD_GRID)
    visual_intent: str = Field(default="", description="Rationale for selecting this visual form")
    lead_summary: str = Field(default="", description="1-2 sentence executive overview for this slide")
    content_points: list[str] = Field(
        default_factory=list,
        description="3-4 detailed analytical points explaining domain mechanisms, trade-offs, and concrete examples (30-60 words each)",
    )
    process_steps: list[ProcessStepBlueprint] | None = None
    timeline_milestones: list[TimelineMilestoneBlueprint] | None = None
    kpis: list[KPIBlueprint] | None = None
    comparison_items: list[ComparisonItemBlueprint] | None = None
    table_columns: list[str] | None = None
    table_rows: list[TableRowBlueprint] | None = None
    speaker_notes: str | None = None


class PresentationBlueprint(BaseModel):
    """Clean, high-density AI generation schema free of design-token bloat."""

    title: str
    subtitle: str
    topic: str
    target_audience: str
    narrative_strategy: NarrativeStrategy = Field(default=NarrativeStrategy.BUSINESS_EXECUTIVE)
    content_depth: ContentDepth = Field(default=ContentDepth.PROFESSIONAL)
    executive_summary: str = Field(default="")
    slides: list[SlideBlueprint]


def blueprint_to_presentation(
    blueprint: PresentationBlueprint,
    request: PresentationGenerationRequest,
) -> Presentation:
    """Deterministically map an AI PresentationBlueprint to the canonical Presentation domain model."""
    slides: list[Slide] = []

    # Strictly respect target slide count if provided
    raw_slides = blueprint.slides
    if request.slide_count and len(raw_slides) > request.slide_count:
        raw_slides = raw_slides[:request.slide_count]

    for s_num, s_bp in enumerate(raw_slides, start=1):
        slide_id = f"slide_{s_num}"
        vtype = s_bp.visual_type
        elements: list[Element] = []

        # 1. Process Flow Data
        process_flow_data: ProcessFlowData | None = None
        if s_bp.process_steps:
            steps = [
                ProcessStep(
                    id=f"step_{s_num}_{ps.order}",
                    title=ps.title[:100],
                    description=ps.description[:300],
                    order=ps.order,
                )
                for ps in s_bp.process_steps
            ]
            process_flow_data = ProcessFlowData(
                direction=ProcessDirection.HORIZONTAL,
                steps=steps,
            )
            vtype = VisualType.PROCESS_FLOW

        # 2. Timeline Data
        timeline_data: TimelineData | None = None
        if s_bp.timeline_milestones:
            milestones = [
                TimelineMilestone(
                    label=tm.label[:100],
                    date=tm.date[:50],
                    description=tm.description[:300],
                    status=TimelineStatus.COMPLETED if i == 0 else TimelineStatus.PLANNED,
                )
                for i, tm in enumerate(s_bp.timeline_milestones)
            ]
            timeline_data = TimelineData(
                title=s_bp.title,
                milestones=milestones,
            )
            vtype = VisualType.TIMELINE

        # 3. Table Data / Comparison
        table_data: TableData | None = None
        if s_bp.table_columns and s_bp.table_rows:
            cols = [
                TableColumn(key=f"col_{i+1}", label=col_name[:50])
                for i, col_name in enumerate(s_bp.table_columns)
            ]
            rows = [
                TableRow(cells=[str(cell)[:100] for cell in r.cells])
                for r in s_bp.table_rows
            ]
            table_data = TableData(columns=cols, rows=rows, has_header=True)
            vtype = VisualType.TABLE
        elif s_bp.comparison_items:
            cols = [
                TableColumn(key="dim", label="Dimension"),
                TableColumn(key="opt_a", label="Primary Architecture"),
                TableColumn(key="opt_b", label="Legacy / Alternative"),
            ]
            rows = [
                TableRow(cells=[ci.dimension, ci.option_a_value, ci.option_b_value])
                for ci in s_bp.comparison_items
            ]
            table_data = TableData(columns=cols, rows=rows, has_header=True)
            vtype = VisualType.COMPARISON

        # 4. KPIs
        if s_bp.kpis and not (process_flow_data or timeline_data or table_data):
            for i, k in enumerate(s_bp.kpis):
                elements.append(
                    Element(
                        id=f"elem_s{s_num}_kpi{i+1}",
                        type=ElementType.KPI,
                        role="kpi",
                        importance="primary",
                        kpi_content=KPIContent(
                            label=k.label[:50],
                            value=k.value[:30],
                            context=k.context[:100],
                            trend="up" if k.trend.lower() == "up" else ("down" if k.trend.lower() == "down" else None),
                        ),
                    )
                )
            vtype = VisualType.KPI

        # 5. Content elements for Diagrams / Cards
        if not elements:
            if s_num == 1 or s_bp.narrative_role == NarrativeRole.TITLE:
                elements = [
                    Element(
                        id=f"elem_s{s_num}_title",
                        type=ElementType.TEXT,
                        role="title",
                        importance="primary",
                        text_content=TextContent(text=s_bp.title, emphasis=True),
                    ),
                    Element(
                        id=f"elem_s{s_num}_subtitle",
                        type=ElementType.TEXT,
                        role="subtitle",
                        importance="secondary",
                        text_content=TextContent(text=s_bp.subtitle),
                    ),
                ]
                vtype = VisualType.NONE
            else:
                raw_points = s_bp.content_points or [s_bp.key_message]
                for idx, point in enumerate(raw_points):
                    parts = point.split(":", 1)
                    if len(parts) == 2:
                        p_title = parts[0].strip().lstrip("*-# ")
                        p_body = parts[1].strip()
                    else:
                        p_title = f"Component {idx + 1}"
                        p_body = point.strip()

                    elements.append(
                        Element(
                            id=f"elem_s{s_num}_card{idx+1}",
                            type=ElementType.CARD,
                            role="card",
                            importance="primary" if idx == 0 else "secondary",
                            card_content=CardContent(
                                title=p_title[:80],
                                body=p_body[:400],
                            ),
                        )
                    )

        visual_plan = VisualPlan(
            visual_type=vtype,
            intent=s_bp.visual_intent or f"Visual layout for {vtype.value}",
            process_flow_data=process_flow_data,
            timeline_data=timeline_data,
            table_data=table_data,
        )

        slide = Slide(
            id=slide_id,
            slide_number=s_num,
            title=s_bp.title,
            subtitle=s_bp.subtitle,
            narrative_role=s_bp.narrative_role,
            purpose=s_bp.objective or s_bp.lead_summary,
            objective=s_bp.objective,
            key_message=s_bp.key_message,
            takeaway=s_bp.takeaway,
            visual_plan=visual_plan,
            elements=elements,
            speaker_notes=s_bp.speaker_notes,
        )
        slides.append(slide)

    if request.design_context and request.design_context.design_system:
        design_sys = request.design_context.design_system
    else:
        palette = ProfessionalPaletteGenerator.create_palette(
            topic=request.topic,
            audience=request.audience,
        )
        design_sys = DesignSystem(palette=palette)

    metadata = PresentationMetadata(
        title=blueprint.title,
        topic=request.topic,
        subtitle=blueprint.subtitle,
        audience=request.audience or blueprint.target_audience,
        purpose=request.purpose or blueprint.executive_summary[:100],
        narrative_strategy=blueprint.narrative_strategy,
        content_depth=blueprint.content_depth,
        slide_count=len(slides),
        language="en",
    )

    pres = Presentation(
        schema_version=CURRENT_SCHEMA_VERSION,
        metadata=metadata,
        design_system=design_sys,
        slides=slides,
        generation_metadata=GenerationMetadata(
            provider="gemini_provider",
            mode=request.mode,
            model="gemini-2.5-flash",
        ),
    )
    SemanticTopicValidator.disinfect_presentation(pres)
    return pres

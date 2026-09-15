"""Tests for VisualPlan, Timeline, and ProcessFlow domain models."""

import pytest
from pydantic import ValidationError

from backend.app.domain import (
    ProcessDirection,
    ProcessFlowData,
    ProcessStep,
    TimelineData,
    TimelineMilestone,
    TimelineStatus,
    VisualPlan,
    VisualType,
)


def test_valid_timeline_model() -> None:
    """Verify timeline with milestone sequence instantiates correctly."""
    timeline = TimelineData(
        title="Product Roadmap",
        milestones=[
            TimelineMilestone(
                label="Alpha Release",
                date="Q1 2026",
                description="Core AI pipeline and prompt compiler",
                status=TimelineStatus.COMPLETED,
            ),
            TimelineMilestone(
                label="Beta Launch",
                date="Q2 2026",
                description="PowerPoint OpenXML native rendering engine",
                status=TimelineStatus.CURRENT,
            ),
            TimelineMilestone(
                label="General Availability",
                date="Q3 2026",
                description="Full SaaS suite with reference adaptation",
                status=TimelineStatus.PLANNED,
            ),
        ],
    )

    assert len(timeline.milestones) == 3
    assert timeline.milestones[0].status == TimelineStatus.COMPLETED


def test_timeline_rejects_single_milestone() -> None:
    """Timeline requires at least 2 milestones."""
    with pytest.raises(ValidationError):
        TimelineData(
            milestones=[
                TimelineMilestone(
                    label="Only 1 Milestone",
                    date="2026",
                )
            ]
        )


def test_valid_process_flow_model() -> None:
    """Verify process flow with ordered steps."""
    flow = ProcessFlowData(
        direction=ProcessDirection.HORIZONTAL,
        steps=[
            ProcessStep(id="step-1", title="Ingest Topic", order=1),
            ProcessStep(id="step-2", title="Visual Plan", order=2),
            ProcessStep(id="step-3", title="Render PPTX", order=3),
        ],
    )
    assert len(flow.steps) == 3
    assert flow.direction == ProcessDirection.HORIZONTAL


def test_visual_plan_integration() -> None:
    """Verify VisualPlan with nested process flow."""
    plan = VisualPlan(
        visual_type=VisualType.PROCESS_FLOW,
        intent="Show 3-stage generation pipeline",
        priority="hero",
        process_flow_data=ProcessFlowData(
            steps=[
                ProcessStep(id="s1", title="Extract", order=1),
                ProcessStep(id="s2", title="Transform", order=2),
            ]
        ),
    )
    assert plan.visual_type == VisualType.PROCESS_FLOW
    assert plan.process_flow_data is not None
    assert len(plan.process_flow_data.steps) == 2

"""Semantic visual prompt guidance for Phase 4 AI planning layer."""

VISUAL_SELECTION_SYSTEM_INSTRUCTION = """
SEMANTIC VISUAL SELECTION GUIDELINES:
1. Match slide content to its natural semantic structure:
   - Chronological events, evolution, milestone dates -> visual_type="timeline"
   - Sequential workflows, onboarding, step-by-step procedures -> visual_type="process_flow"
   - System architectures, microservices, cloud stacks, layers -> visual_type="architecture"
   - Direct entity comparisons, pros/cons, option A vs B -> visual_type="comparison"
   - Numeric KPI scorecards, metrics, delta figures -> visual_type="kpi"
   - Continuous trends over time with quantitative data -> visual_type="line_chart"
   - Category breakdowns with discrete values -> visual_type="column_chart" or "bar_chart"
   - Multi-attribute feature matrices, technical specs -> visual_type="table"
   - Executive quotes, testimonials, guiding principles -> visual_type="quote"
   - Multi-category principles or feature pillars -> visual_type="card_grid"

2. AVOID TEXT-DOMINANT DECKS:
   - Do NOT produce consecutive generic title+bullet slides.
   - Actively construct the specific data models (process_flow_data, timeline_data, table_data, chart_data) whenever appropriate.
"""

"""Chart data models and strict validation."""

import math
from typing import Literal
from pydantic import BaseModel, Field, model_validator

from backend.app.domain.constants import (
    MAX_CHART_POINTS,
    MAX_CHART_SERIES,
    MAX_CHART_TITLE_LENGTH,
)
from backend.app.domain.enums import DataSource


class ChartSeries(BaseModel):
    """Single numerical data series for chart generation."""

    name: str = Field(..., min_length=1, max_length=100)
    values: list[float] = Field(..., min_length=1, max_length=MAX_CHART_POINTS)

    @model_validator(mode="after")
    def validate_finite_numbers(self) -> "ChartSeries":
        for val in self.values:
            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"Chart series '{self.name}' contains invalid non-finite value: {val}")
        return self


class ChartData(BaseModel):
    """Structured data for native PowerPoint charts with provenance tracking."""

    chart_type: Literal[
        "bar",
        "column",
        "line",
        "pie",
        "donut",
        "stacked_bar",
        "stacked_column",
        "area",
    ] = Field(default="column")
    title: str = Field(..., min_length=1, max_length=MAX_CHART_TITLE_LENGTH)
    categories: list[str] = Field(..., min_length=1, max_length=MAX_CHART_POINTS)
    series: list[ChartSeries] = Field(..., min_length=1, max_length=MAX_CHART_SERIES)
    data_source: DataSource = Field(
        default=DataSource.USER_PROVIDED,
        description="Data provenance to prevent unverified statistical claims",
    )
    is_illustrative: bool = Field(
        default=False,
        description="True if data is conceptual/illustrative rather than real empirical fact",
    )

    @model_validator(mode="after")
    def validate_series_lengths_match_categories(self) -> "ChartData":
        cat_count = len(self.categories)
        for s in self.series:
            if len(s.values) != cat_count:
                raise ValueError(
                    f"Chart series '{s.name}' has {len(s.values)} values, but categories has {cat_count} items. Lengths must match exactly."
                )
        return self

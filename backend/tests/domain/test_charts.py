"""Tests for ChartData and ChartSeries models."""

import pytest
from pydantic import ValidationError

from backend.app.domain import (
    ChartData,
    ChartSeries,
    DataSource,
)


def test_valid_chart_data_model() -> None:
    """Verify structured chart data with matching categories and series."""
    chart = ChartData(
        chart_type="column",
        title="Quarterly Enterprise Revenue Growth",
        categories=["Q1", "Q2", "Q3", "Q4"],
        series=[
            ChartSeries(name="2025 Actual", values=[12.5, 14.8, 16.2, 19.0]),
            ChartSeries(name="2026 Target", values=[15.0, 18.0, 21.5, 26.0]),
        ],
        data_source=DataSource.USER_PROVIDED,
        is_illustrative=False,
    )
    assert chart.title == "Quarterly Enterprise Revenue Growth"
    assert len(chart.categories) == 4
    assert len(chart.series) == 2
    assert chart.series[0].values[0] == 12.5


def test_chart_rejects_series_category_length_mismatch() -> None:
    """Verify chart validation rejects series with length differing from categories."""
    with pytest.raises(ValidationError) as exc:
        ChartData(
            chart_type="bar",
            title="Mismatched Chart",
            categories=["North", "South", "East", "West"],  # 4 categories
            series=[
                ChartSeries(name="Sales", values=[10.0, 20.0, 30.0]),  # Only 3 values!
            ],
        )
    assert "Length" in str(exc.value) or "categories" in str(exc.value)


def test_chart_rejects_nan_or_infinite_values() -> None:
    """Verify chart rejects non-finite floating point numbers."""
    with pytest.raises(ValidationError) as exc:
        ChartSeries(name="Corrupted Data", values=[10.0, float("nan"), 30.0])
    assert "non-finite" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ChartSeries(name="Infinite Data", values=[10.0, float("inf"), 30.0])
    assert "non-finite" in str(exc.value)


def test_chart_provenance_flagging() -> None:
    """Verify provenance tracking on illustrative data."""
    chart = ChartData(
        chart_type="line",
        title="Projected Market Penetration (Illustrative)",
        categories=["Year 1", "Year 2", "Year 3"],
        series=[ChartSeries(name="Projection", values=[5.0, 15.0, 35.0])],
        data_source=DataSource.ILLUSTRATIVE,
        is_illustrative=True,
    )
    assert chart.data_source == DataSource.ILLUSTRATIVE
    assert chart.is_illustrative is True

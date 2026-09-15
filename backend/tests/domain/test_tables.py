"""Tests for TableData, TableColumn, and TableRow models."""

import pytest
from pydantic import ValidationError

from backend.app.domain import (
    Alignment,
    TableColumn,
    TableData,
    TableRow,
)


def test_valid_table_data_model() -> None:
    """Verify structured table data with columns and rows."""
    table = TableData(
        columns=[
            TableColumn(key="feature", label="Feature", alignment=Alignment.LEFT),
            TableColumn(key="tier1", label="Standard", alignment=Alignment.CENTER),
            TableColumn(key="tier2", label="Enterprise", alignment=Alignment.CENTER),
        ],
        rows=[
            TableRow(cells=["Single Sign-On (SSO)", "No", "Yes (SAML / Okta)"]),
            TableRow(cells=["Custom AI Models", "No", "Yes"]),
            TableRow(cells=["Dedicated SLA", "99.9%", "99.999%"]),
        ],
        has_header=True,
    )
    assert len(table.columns) == 3
    assert len(table.rows) == 3
    assert table.rows[0].cells[0] == "Single Sign-On (SSO)"


def test_table_rejects_row_length_mismatch() -> None:
    """Verify table validation fails if row cell count != column count."""
    with pytest.raises(ValidationError) as exc:
        TableData(
            columns=[
                TableColumn(key="col1", label="Col 1"),
                TableColumn(key="col2", label="Col 2"),
            ],
            rows=[
                TableRow(cells=["Cell 1", "Cell 2", "Extra Cell 3"]),  # 3 cells vs 2 cols
            ],
        )
    assert "Row cell counts must match column count" in str(exc.value)


def test_table_rejects_empty_columns_or_rows() -> None:
    """Verify table requires at least 1 column and 1 row."""
    with pytest.raises(ValidationError):
        TableData(columns=[], rows=[])

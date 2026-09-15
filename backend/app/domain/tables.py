"""Table data models and schema validation."""

from pydantic import BaseModel, Field, model_validator

from backend.app.domain.constants import (
    MAX_TABLE_CELL_LENGTH,
    MAX_TABLE_COLUMNS,
    MAX_TABLE_ROWS,
)
from backend.app.domain.enums import Alignment


class TableColumn(BaseModel):
    """Specification of a table column."""

    key: str = Field(..., min_length=1, max_length=50)
    label: str = Field(..., min_length=1, max_length=100)
    alignment: Alignment = Field(default=Alignment.LEFT)


class TableRow(BaseModel):
    """Single row of table cells."""

    cells: list[str] = Field(..., min_length=1, max_length=MAX_TABLE_COLUMNS)

    @model_validator(mode="after")
    def validate_cell_lengths(self) -> "TableRow":
        for cell in self.cells:
            if len(cell) > MAX_TABLE_CELL_LENGTH:
                raise ValueError(
                    f"Table cell content exceeds maximum allowed length ({MAX_TABLE_CELL_LENGTH}): '{cell[:30]}...'"
                )
        return self


class TableData(BaseModel):
    """Structured table definition for native PowerPoint table rendering."""

    columns: list[TableColumn] = Field(..., min_length=1, max_length=MAX_TABLE_COLUMNS)
    rows: list[TableRow] = Field(..., min_length=1, max_length=MAX_TABLE_ROWS)
    has_header: bool = Field(default=True)

    @model_validator(mode="after")
    def validate_row_cell_counts(self) -> "TableData":
        col_count = len(self.columns)
        for i, row in enumerate(self.rows):
            if len(row.cells) != col_count:
                raise ValueError(
                    f"Table row #{i + 1} contains {len(row.cells)} cells, but column count is {col_count}. Row cell counts must match column count."
                )
        return self

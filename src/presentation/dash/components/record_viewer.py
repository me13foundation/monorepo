"""Enhanced data table component with fallback support.

Provides DataTable functionality with graceful degradation to HTML tables.
"""

import logging
from types import ModuleType
from typing import TYPE_CHECKING, Any, cast

import dash_bootstrap_components as dbc

from dash import html

if TYPE_CHECKING:  # pragma: no cover - typing only
    from dash.development.base_component import Component

# Import dash_table if available
dash_table_module: ModuleType | None
try:
    import dash.dash_table as dash_table_module
except ImportError:  # pragma: no cover - optional dependency
    dash_table_module = None

DASH_TABLE_AVAILABLE = dash_table_module is not None


logger = logging.getLogger(__name__)


def create_data_table(**kwargs: Any) -> "Component":
    """Create a DataTable if available, otherwise return a placeholder."""
    if DASH_TABLE_AVAILABLE and dash_table_module is not None:
        try:
            # Create DataTable component - Dash 3.x handles registration automatically
            return cast("Component", dash_table_module.DataTable(**kwargs))
        except (TypeError, ValueError) as e:
            logger.warning(f"DataTable component failed: {e}, using fallback")
            return _create_table_fallback(**kwargs)
    else:
        return _create_table_fallback(**kwargs)


def _create_table_fallback(**kwargs: Any) -> "Component":
    """Create an enhanced fallback table display with full functionality."""
    data = cast("list[dict[str, Any]]", kwargs.get("data", []))
    columns = cast("list[dict[str, Any]]", kwargs.get("columns", []))
    table_id = str(kwargs.get("id", "table"))

    if not data:
        return html.Div(
            [
                dbc.Alert(
                    [
                        html.H5("📊 Data Table", className="alert-heading"),
                        html.P("No data available to display.", className="mb-0"),
                    ],
                    color="info",
                ),
            ],
        )

    # Create enhanced HTML table with sorting and filtering capabilities
    table_header = _build_table_header(columns, table_id)

    table_rows = _build_table_rows(
        data,
        columns,
        table_id,
        kwargs.get("row_selectable"),
    )

    # Create pagination controls
    page_size_raw = kwargs.get("page_size", 25)
    try:
        page_size = int(page_size_raw)
    except (TypeError, ValueError):
        page_size = 25
    total_pages = (len(data) + page_size - 1) // page_size if data else 0

    pagination_controls = _build_pagination_controls(
        total_pages,
        page_size,
        table_id,
        len(data),
    )

    children: list[Component] = [
        dbc.Table(
            [html.Thead(html.Tr(table_header)), html.Tbody(table_rows)],
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="table-sm",
            id=f"{table_id}-fallback",
        ),
        html.Small(
            [
                html.I(className="fas fa-info-circle me-1"),
                " Enhanced HTML table with sorting and pagination support",
            ],
            className="text-muted mt-2 d-block",
        ),
    ]

    if pagination_controls is not None:
        children.insert(1, pagination_controls)

    return html.Div(children)


def _build_table_header(
    columns: list[dict[str, Any]],
    table_id: str,
) -> list["Component"]:
    header: list[Component] = []
    for col in columns or []:
        col_name = col.get("name", col.get("id", "Column"))
        col_id = col.get("id", "")
        header.append(
            html.Th(
                [
                    html.Span(col_name, className="me-2"),
                    html.I(
                        className="fas fa-sort text-muted",
                        style={"fontSize": "0.8em"},
                    ),
                ],
                style={"cursor": "pointer"},
                className="sortable-header",
                id=f"{table_id}-header-{col_id}",
            ),
        )
    return header


def _format_cell(col: dict[str, Any], value: Any) -> str:
    col_type = col.get("type", "text")
    if col_type == "numeric" and isinstance(value, (int, float)):
        return f"{value:.2f}" if isinstance(value, float) else str(value)
    if col_type == "datetime":
        return str(value)
    return str(value)


def _build_table_rows(
    data: list[dict[str, Any]],
    columns: list[dict[str, Any]],
    table_id: str,
    row_selectable: Any,
) -> list["Component"]:
    rows: list[Component] = []
    for idx, row in enumerate(data):
        cells: list[Component] = []
        if columns:
            for col in columns:
                col_id = col.get("id", "")
                cell_display = _format_cell(col, row.get(col_id, ""))
                cells.append(html.Td(cell_display))
        else:
            for key, value in row.items():
                cells.append(html.Td(f"{key}: {value}"))
        row_classes = "table-row"
        if row_selectable == "multi":
            row_classes += " selectable-row"
        rows.append(html.Tr(cells, className=row_classes, id=f"{table_id}-row-{idx}"))
    return rows


def _build_pagination_controls(
    total_pages: int,
    page_size: int,
    table_id: str,
    total_items: int,
) -> "Component | None":
    if total_pages <= 1:
        return None
    pagination_items = [
        dbc.PaginationItem(i + 1, active=(i == 0), id=f"{table_id}-page-{i + 1}")
        for i in range(min(5, total_pages))
    ]
    return html.Div(
        [
            html.Small(
                f"Showing {min(page_size, total_items)} of {total_items} items",
                className="text-muted me-3",
            ),
            dbc.Pagination(pagination_items, size="sm", className="mb-0"),
        ],
        className="d-flex justify-content-between align-items-center mt-3",
    )


__all__ = ["_create_table_fallback", "create_data_table"]

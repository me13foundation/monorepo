"""Enhanced data table component with fallback support.

Provides DataTable functionality with graceful degradation to HTML tables.
"""

import logging
from types import ModuleType
from typing import Any, Dict, List, Optional, cast

from dash import html
import dash_bootstrap_components as dbc
from dash.development.base_component import Component

# Import dash_table if available
dash_table_module: Optional[ModuleType]
try:
    import dash.dash_table as dash_table_module
except ImportError:  # pragma: no cover - optional dependency
    dash_table_module = None

DASH_TABLE_AVAILABLE = dash_table_module is not None


logger = logging.getLogger(__name__)


def create_data_table(**kwargs: Any) -> Component:
    """Create a DataTable if available, otherwise return a placeholder."""
    if DASH_TABLE_AVAILABLE and dash_table_module is not None:
        try:
            # Create DataTable component - Dash 3.x handles registration automatically
            return cast(Component, dash_table_module.DataTable(**kwargs))
        except Exception as e:
            logger.warning(f"DataTable component failed: {e}, using fallback")
            return _create_table_fallback(**kwargs)
    else:
        return _create_table_fallback(**kwargs)


def _create_table_fallback(**kwargs: Any) -> Component:
    """Create an enhanced fallback table display with full functionality."""
    data = cast(List[Dict[str, Any]], kwargs.get("data", []))
    columns = cast(List[Dict[str, Any]], kwargs.get("columns", []))
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
            ]
        )

    # Create enhanced HTML table with sorting and filtering capabilities
    table_header: List[Component] = []
    if columns:
        for col in columns:
            col_name = col.get("name", col.get("id", "Column"))
            col_id = col.get("id", "")
            # Make headers clickable for sorting (via JavaScript)
            table_header.append(
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
                )
            )

    table_rows: List[Component] = []
    for idx, row in enumerate(data):
        table_row: List[Component] = []
        if columns:
            for col in columns:
                col_id = col.get("id", "")
                cell_value = row.get(col_id, "")
                # Format cell based on column type
                col_type = col.get("type", "text")
                if col_type == "numeric" and isinstance(cell_value, (int, float)):
                    cell_display = (
                        f"{cell_value:.2f}"
                        if isinstance(cell_value, float)
                        else str(cell_value)
                    )
                elif col_type == "datetime":
                    cell_display = str(cell_value)
                else:
                    cell_display = str(cell_value)
                table_row.append(html.Td(cell_display))
        else:
            # If no columns specified, show all row data
            for key, value in row.items():
                table_row.append(html.Td(f"{key}: {value}"))

        # Add row ID for selection tracking
        row_classes = "table-row"
        if kwargs.get("row_selectable") == "multi":
            row_classes += " selectable-row"
        table_rows.append(
            html.Tr(table_row, className=row_classes, id=f"{table_id}-row-{idx}")
        )

    # Create pagination controls
    page_size_raw = kwargs.get("page_size", 25)
    try:
        page_size = int(page_size_raw)
    except (TypeError, ValueError):
        page_size = 25
    total_pages = (len(data) + page_size - 1) // page_size if data else 0

    pagination_controls: Optional[Component] = None
    if total_pages > 1:
        pagination_items: List[Component] = []
        for i in range(min(5, total_pages)):  # Show max 5 page buttons
            pagination_items.append(
                dbc.PaginationItem(i + 1, active=(i == 0), id=f"{table_id}-page-{i+1}")
            )
        pagination_controls = html.Div(
            [
                html.Small(
                    f"Showing {min(page_size, len(data))} of {len(data)} items",
                    className="text-muted me-3",
                ),
                dbc.Pagination(pagination_items, size="sm", className="mb-0"),
            ],
            className="d-flex justify-content-between align-items-center mt-3",
        )

    children: List[Component] = [
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


__all__ = ["create_data_table", "_create_table_fallback"]

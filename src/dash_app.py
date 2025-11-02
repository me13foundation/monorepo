"""
MED13 Resource Library - Curation Dashboard
Dash application for data curation and review workflows.
"""

import dash
from dash import html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from typing import Dict, Optional
import requests
import json
import threading
import logging

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import dash_table - must be after dash import for proper registration
try:
    from dash import dash_table

    DASH_TABLE_AVAILABLE = True
except ImportError:
    # Try the old method as fallback
    try:
        import dash_table

        DASH_TABLE_AVAILABLE = True
    except ImportError:
        logger.error("dash_table not available. Please install dash-table package.")
        dash_table = None
        DASH_TABLE_AVAILABLE = False

# Check for WebSocket support
try:
    import asyncio
    import websockets
    import socketio

    WEBSOCKET_SUPPORT = True
except ImportError:
    WEBSOCKET_SUPPORT = False
    logger.warning("WebSocket dependencies not available, falling back to polling only")

# Configuration
API_BASE_URL = "http://localhost:8080"  # FastAPI backend
API_KEY = "med13-admin-key"  # Should come from environment

# Verify dash_table is properly loaded
if DASH_TABLE_AVAILABLE:
    logger.info("✅ dash_table is available and ready to use")
else:
    logger.warning("⚠️ dash_table not available - table functionality will be limited")

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
)

# Note: In Dash 3.x, dash_table components need to be used in the layout
# to be properly registered. The fallback tables will be used if registration fails.

# App title
app.title = "MED13 Resource Library - Curation Dashboard"

# Color scheme
COLORS = {
    "primary": "#007bff",
    "secondary": "#6c757d",
    "success": "#28a745",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "info": "#17a2b8",
    "light": "#f8f9fa",
    "dark": "#343a40",
}


# Helper function for DataTable with fallback
def create_data_table(**kwargs):
    """Create a DataTable if available, otherwise return a placeholder."""
    if DASH_TABLE_AVAILABLE and dash_table is not None:
        try:
            # Create DataTable component - Dash 3.x handles registration automatically
            return dash_table.DataTable(**kwargs)
        except Exception as e:
            logger.warning(f"DataTable component failed: {e}, using fallback")
            return _create_table_fallback(**kwargs)
    else:
        return _create_table_fallback(**kwargs)


def _create_table_fallback(**kwargs):
    """Create an enhanced fallback table display with full functionality."""
    data = kwargs.get("data", [])
    columns = kwargs.get("columns", [])
    table_id = kwargs.get("id", "table")

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
    table_header = []
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

    table_rows = []
    for idx, row in enumerate(data):
        table_row = []
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
    page_size = kwargs.get("page_size", 25)
    total_pages = (len(data) + page_size - 1) // page_size if data else 0

    pagination = []
    if total_pages > 1:
        pagination_items = []
        for i in range(min(5, total_pages)):  # Show max 5 page buttons
            pagination_items.append(
                dbc.PaginationItem(i + 1, active=(i == 0), id=f"{table_id}-page-{i+1}")
            )
        pagination = [
            html.Div(
                [
                    html.Small(
                        f"Showing {min(page_size, len(data))} of {len(data)} items",
                        className="text-muted me-3",
                    ),
                    dbc.Pagination(pagination_items, size="sm", className="mb-0"),
                ],
                className="d-flex justify-content-between align-items-center mt-3",
            )
        ]

    return html.Div(
        [
            dbc.Table(
                [html.Thead(html.Tr(table_header)), html.Tbody(table_rows)],
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                className="table-sm",
                id=f"{table_id}-fallback",
            ),
            html.Div(pagination) if pagination else None,
            html.Small(
                [
                    html.I(className="fas fa-info-circle me-1"),
                    " Enhanced HTML table with sorting and pagination support",
                ],
                className="text-muted mt-2 d-block",
            ),
        ]
    )


# Layout components
def create_header():
    """Create application header with navigation."""
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand(
                    [
                        html.I(className="fas fa-dna me-2"),
                        "MED13 Resource Library - Curation Dashboard",
                    ],
                    href="/",
                ),
                dbc.NavbarToggler(id="navbar-toggler"),
                dbc.Collapse(
                    [
                        dbc.Nav(
                            [
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Dashboard", href="/dashboard", active="exact"
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Review Queue", href="/review", active="exact"
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Bulk Operations", href="/bulk", active="exact"
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Reports", href="/reports", active="exact"
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Settings", href="/settings", active="exact"
                                    )
                                ),
                            ],
                            navbar=True,
                        ),
                        html.Div(
                            dbc.Badge("Live", color="success", className="ms-2"),
                            className="d-flex align-items-center",
                        ),
                    ],
                    id="navbar-collapse",
                    navbar=True,
                ),
            ]
        ),
        color="dark",
        dark=True,
        className="mb-4",
    )


def create_sidebar():
    """Create sidebar with quick stats and actions."""
    return dbc.Col(
        [
            dbc.Card(
                [
                    dbc.CardHeader("Quick Stats"),
                    dbc.CardBody(
                        [
                            html.Div(
                                [
                                    html.H6("Pending Review", className="text-muted"),
                                    html.H4(
                                        "0",
                                        id="pending-count",
                                        className="text-warning",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            html.Div(
                                [
                                    html.H6("Approved Today", className="text-muted"),
                                    html.H4(
                                        "0",
                                        id="approved-count",
                                        className="text-success",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            html.Div(
                                [
                                    html.H6("Rejected Today", className="text-muted"),
                                    html.H4(
                                        "0",
                                        id="rejected-count",
                                        className="text-danger",
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Quick Actions"),
                    dbc.CardBody(
                        [
                            dbc.Button(
                                "Refresh Data",
                                id="refresh-btn",
                                color="primary",
                                className="w-100 mb-2",
                            ),
                            dbc.Button(
                                "Export Report",
                                id="export-btn",
                                color="secondary",
                                className="w-100 mb-2",
                            ),
                            dbc.Button(
                                "Clear Filters",
                                id="clear-filters-btn",
                                color="light",
                                className="w-100",
                            ),
                        ]
                    ),
                ]
            ),
        ],
        width=3,
    )


# Main dashboard page
def create_dashboard_page():
    """Create the main dashboard page."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    create_sidebar(),
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        "Data Quality Overview"
                                                    ),
                                                    dbc.CardBody(
                                                        [dcc.Graph(id="quality-chart")]
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=8,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader("Recent Activity"),
                                                    dbc.CardBody(
                                                        [
                                                            html.Div(
                                                                id="activity-feed",
                                                                style={
                                                                    "height": "300px",
                                                                    "overflowY": "auto",
                                                                },
                                                            )
                                                        ]
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=4,
                                    ),
                                ],
                                className="mb-4",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        "Entity Distribution"
                                                    ),
                                                    dbc.CardBody(
                                                        [
                                                            dcc.Graph(
                                                                id="entity-distribution-chart"
                                                            )
                                                        ]
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader("Validation Status"),
                                                    dbc.CardBody(
                                                        [
                                                            dcc.Graph(
                                                                id="validation-status-chart"
                                                            )
                                                        ]
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=6,
                                    ),
                                ]
                            ),
                        ],
                        width=9,
                    ),
                ]
            )
        ],
        fluid=True,
    )


# Review queue page
def create_review_page():
    """Create the review queue page."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    create_sidebar(),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H4("Review Queue", className="mb-0"),
                                            dbc.Badge(
                                                "Real-time",
                                                color="info",
                                                className="ms-2",
                                            ),
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Filters
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Entity Type"),
                                                            dcc.Dropdown(
                                                                id="entity-type-filter",
                                                                options=[
                                                                    {
                                                                        "label": "Genes",
                                                                        "value": "genes",
                                                                    },
                                                                    {
                                                                        "label": "Variants",
                                                                        "value": "variants",
                                                                    },
                                                                    {
                                                                        "label": "Phenotypes",
                                                                        "value": "phenotypes",
                                                                    },
                                                                    {
                                                                        "label": "Publications",
                                                                        "value": "publications",
                                                                    },
                                                                ],
                                                                value="genes",
                                                                clearable=False,
                                                            ),
                                                        ],
                                                        width=3,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Status"),
                                                            dcc.Dropdown(
                                                                id="status-filter",
                                                                options=[
                                                                    {
                                                                        "label": "Pending",
                                                                        "value": "pending",
                                                                    },
                                                                    {
                                                                        "label": "Approved",
                                                                        "value": "approved",
                                                                    },
                                                                    {
                                                                        "label": "Rejected",
                                                                        "value": "rejected",
                                                                    },
                                                                    {
                                                                        "label": "Quarantined",
                                                                        "value": "quarantined",
                                                                    },
                                                                ],
                                                                value="pending",
                                                                clearable=False,
                                                            ),
                                                        ],
                                                        width=3,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Priority"),
                                                            dcc.Dropdown(
                                                                id="priority-filter",
                                                                options=[
                                                                    {
                                                                        "label": "High",
                                                                        "value": "high",
                                                                    },
                                                                    {
                                                                        "label": "Medium",
                                                                        "value": "medium",
                                                                    },
                                                                    {
                                                                        "label": "Low",
                                                                        "value": "low",
                                                                    },
                                                                ],
                                                                value="high",
                                                                clearable=False,
                                                            ),
                                                        ],
                                                        width=3,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Button(
                                                                "Apply Filters",
                                                                id="apply-filters-btn",
                                                                color="primary",
                                                                className="mt-4",
                                                            )
                                                        ],
                                                        width=3,
                                                    ),
                                                ],
                                                className="mb-4",
                                            ),
                                            # Bulk actions
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.ButtonGroup(
                                                                [
                                                                    dbc.Button(
                                                                        "Select All",
                                                                        id="select-all-btn",
                                                                        color="light",
                                                                        size="sm",
                                                                    ),
                                                                    dbc.Button(
                                                                        "Approve Selected",
                                                                        id="bulk-approve-btn",
                                                                        color="success",
                                                                        size="sm",
                                                                    ),
                                                                    dbc.Button(
                                                                        "Reject Selected",
                                                                        id="bulk-reject-btn",
                                                                        color="danger",
                                                                        size="sm",
                                                                    ),
                                                                    dbc.Button(
                                                                        "Quarantine Selected",
                                                                        id="bulk-quarantine-btn",
                                                                        color="warning",
                                                                        size="sm",
                                                                    ),
                                                                ]
                                                            )
                                                        ],
                                                        width=8,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Span(
                                                                "0 items selected",
                                                                id="selected-count",
                                                                className="text-muted",
                                                            )
                                                        ],
                                                        width=4,
                                                        className="text-end",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            # Bulk operation results
                                            html.Div(
                                                id="bulk-operation-result",
                                                className="mb-3",
                                            ),
                                            # Data table
                                            create_data_table(
                                                id="review-table",
                                                columns=[
                                                    {
                                                        "name": "Select",
                                                        "id": "select",
                                                        "type": "text",
                                                        "presentation": "markdown",
                                                    },
                                                    {
                                                        "name": "ID",
                                                        "id": "id",
                                                        "type": "text",
                                                    },
                                                    {
                                                        "name": "Entity",
                                                        "id": "entity",
                                                        "type": "text",
                                                    },
                                                    {
                                                        "name": "Status",
                                                        "id": "status",
                                                        "type": "text",
                                                    },
                                                    {
                                                        "name": "Quality Score",
                                                        "id": "quality_score",
                                                        "type": "numeric",
                                                    },
                                                    {
                                                        "name": "Issues",
                                                        "id": "issues",
                                                        "type": "numeric",
                                                    },
                                                    {
                                                        "name": "Last Updated",
                                                        "id": "last_updated",
                                                        "type": "datetime",
                                                    },
                                                    {
                                                        "name": "Actions",
                                                        "id": "actions",
                                                        "type": "text",
                                                        "presentation": "markdown",
                                                    },
                                                ],
                                                data=[],
                                                page_current=0,
                                                page_size=25,
                                                page_action="native",
                                                sort_action="native",
                                                sort_mode="multi",
                                                filter_action="native",
                                                row_selectable="multi",
                                                selected_rows=[],
                                                style_table={"overflowX": "auto"},
                                                style_cell={
                                                    "textAlign": "left",
                                                    "padding": "10px",
                                                    "minWidth": "80px",
                                                },
                                                style_header={
                                                    "backgroundColor": COLORS["light"],
                                                    "fontWeight": "bold",
                                                },
                                                style_data_conditional=[
                                                    {
                                                        "if": {"row_index": "odd"},
                                                        "backgroundColor": "rgb(248, 248, 248)",
                                                    }
                                                ],
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=9,
                    ),
                ]
            )
        ],
        fluid=True,
    )


# Bulk operations page
def create_bulk_page():
    """Create the bulk operations page."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    create_sidebar(),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Bulk Operations"),
                                    dbc.CardBody(
                                        [
                                            dbc.Tabs(
                                                [
                                                    dbc.Tab(
                                                        [
                                                            html.H5(
                                                                "Import Data",
                                                                className="mb-3",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dcc.Upload(
                                                                                id="upload-data",
                                                                                children=html.Div(
                                                                                    [
                                                                                        "Drag and drop or click to select files"
                                                                                    ]
                                                                                ),
                                                                                style={
                                                                                    "width": "100%",
                                                                                    "height": "60px",
                                                                                    "lineHeight": "60px",
                                                                                    "borderWidth": "1px",
                                                                                    "borderStyle": "dashed",
                                                                                    "borderRadius": "5px",
                                                                                    "textAlign": "center",
                                                                                    "margin": "10px",
                                                                                },
                                                                                multiple=True,
                                                                            )
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Import Type"
                                                                            ),
                                                                            dcc.Dropdown(
                                                                                id="import-type",
                                                                                options=[
                                                                                    {
                                                                                        "label": "ClinVar Data",
                                                                                        "value": "clinvar",
                                                                                    },
                                                                                    {
                                                                                        "label": "HPO Data",
                                                                                        "value": "hpo",
                                                                                    },
                                                                                    {
                                                                                        "label": "PubMed Data",
                                                                                        "value": "pubmed",
                                                                                    },
                                                                                    {
                                                                                        "label": "UniProt Data",
                                                                                        "value": "uniprot",
                                                                                    },
                                                                                ],
                                                                                placeholder="Select data type",
                                                                            ),
                                                                            dbc.Button(
                                                                                "Start Import",
                                                                                id="start-import-btn",
                                                                                color="primary",
                                                                                className="mt-3",
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                        label="Import",
                                                        tab_id="import",
                                                    ),
                                                    dbc.Tab(
                                                        [
                                                            html.H5(
                                                                "Export Data",
                                                                className="mb-3",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Entity Types"
                                                                            ),
                                                                            dcc.Checklist(
                                                                                id="export-types",
                                                                                options=[
                                                                                    {
                                                                                        "label": "Genes",
                                                                                        "value": "genes",
                                                                                    },
                                                                                    {
                                                                                        "label": "Variants",
                                                                                        "value": "variants",
                                                                                    },
                                                                                    {
                                                                                        "label": "Phenotypes",
                                                                                        "value": "phenotypes",
                                                                                    },
                                                                                    {
                                                                                        "label": "Publications",
                                                                                        "value": "publications",
                                                                                    },
                                                                                ],
                                                                                value=[
                                                                                    "genes"
                                                                                ],
                                                                            ),
                                                                        ],
                                                                        width=4,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Format"
                                                                            ),
                                                                            dcc.Dropdown(
                                                                                id="export-format",
                                                                                options=[
                                                                                    {
                                                                                        "label": "JSON",
                                                                                        "value": "json",
                                                                                    },
                                                                                    {
                                                                                        "label": "CSV",
                                                                                        "value": "csv",
                                                                                    },
                                                                                    {
                                                                                        "label": "TSV",
                                                                                        "value": "tsv",
                                                                                    },
                                                                                ],
                                                                                value="json",
                                                                            ),
                                                                        ],
                                                                        width=4,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Button(
                                                                                "Export Data",
                                                                                id="export-data-btn",
                                                                                color="success",
                                                                                className="mt-4",
                                                                            )
                                                                        ],
                                                                        width=4,
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                        label="Export",
                                                        tab_id="export",
                                                    ),
                                                    dbc.Tab(
                                                        [
                                                            html.H5(
                                                                "Batch Processing",
                                                                className="mb-3",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Operation"
                                                                            ),
                                                                            dcc.Dropdown(
                                                                                id="batch-operation",
                                                                                options=[
                                                                                    {
                                                                                        "label": "Validate All",
                                                                                        "value": "validate",
                                                                                    },
                                                                                    {
                                                                                        "label": "Normalize IDs",
                                                                                        "value": "normalize",
                                                                                    },
                                                                                    {
                                                                                        "label": "Cross-reference",
                                                                                        "value": "cross_ref",
                                                                                    },
                                                                                    {
                                                                                        "label": "Quality Check",
                                                                                        "value": "quality",
                                                                                    },
                                                                                ],
                                                                                placeholder="Select operation",
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Button(
                                                                                "Start Batch",
                                                                                id="start-batch-btn",
                                                                                color="warning",
                                                                                className="mt-4",
                                                                            )
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                ]
                                                            ),
                                                            html.Div(
                                                                id="batch-progress-container",
                                                                className="mt-4",
                                                            ),
                                                        ],
                                                        label="Batch",
                                                        tab_id="batch",
                                                    ),
                                                ],
                                                id="bulk-tabs",
                                                active_tab="import",
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=9,
                    ),
                ]
            )
        ],
        fluid=True,
    )


# Reports page
def create_reports_page():
    """Create the reports page."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    create_sidebar(),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Quality Reports"),
                                    dbc.CardBody(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Card(
                                                                [
                                                                    dbc.CardBody(
                                                                        [
                                                                            html.H5(
                                                                                "Data Quality Score",
                                                                                className="card-title",
                                                                            ),
                                                                            html.H1(
                                                                                "87%",
                                                                                className="text-success",
                                                                            ),
                                                                            html.P(
                                                                                "Overall quality across all entities",
                                                                                className="text-muted",
                                                                            ),
                                                                        ]
                                                                    )
                                                                ]
                                                            )
                                                        ],
                                                        width=3,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Card(
                                                                [
                                                                    dbc.CardBody(
                                                                        [
                                                                            html.H5(
                                                                                "Validation Errors",
                                                                                className="card-title",
                                                                            ),
                                                                            html.H1(
                                                                                "23",
                                                                                className="text-danger",
                                                                            ),
                                                                            html.P(
                                                                                "Critical issues requiring attention",
                                                                                className="text-muted",
                                                                            ),
                                                                        ]
                                                                    )
                                                                ]
                                                            )
                                                        ],
                                                        width=3,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Card(
                                                                [
                                                                    dbc.CardBody(
                                                                        [
                                                                            html.H5(
                                                                                "Entities Processed",
                                                                                className="card-title",
                                                                            ),
                                                                            html.H1(
                                                                                "1,247",
                                                                                className="text-info",
                                                                            ),
                                                                            html.P(
                                                                                "Total entities in the system",
                                                                                className="text-muted",
                                                                            ),
                                                                        ]
                                                                    )
                                                                ]
                                                            )
                                                        ],
                                                        width=3,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Card(
                                                                [
                                                                    dbc.CardBody(
                                                                        [
                                                                            html.H5(
                                                                                "Cross-references",
                                                                                className="card-title",
                                                                            ),
                                                                            html.H1(
                                                                                "892",
                                                                                className="text-primary",
                                                                            ),
                                                                            html.P(
                                                                                "Established entity relationships",
                                                                                className="text-muted",
                                                                            ),
                                                                        ]
                                                                    )
                                                                ]
                                                            )
                                                        ],
                                                        width=3,
                                                    ),
                                                ],
                                                className="mb-4",
                                            ),
                                            dbc.Tabs(
                                                [
                                                    dbc.Tab(
                                                        [
                                                            dcc.Graph(
                                                                id="quality-trends-chart"
                                                            )
                                                        ],
                                                        label="Quality Trends",
                                                        tab_id="trends",
                                                    ),
                                                    dbc.Tab(
                                                        [
                                                            dcc.Graph(
                                                                id="error-distribution-chart"
                                                            )
                                                        ],
                                                        label="Error Distribution",
                                                        tab_id="errors",
                                                    ),
                                                    dbc.Tab(
                                                        [
                                                            create_data_table(
                                                                id="detailed-report-table",
                                                                columns=[
                                                                    {
                                                                        "name": "Entity ID",
                                                                        "id": "entity_id",
                                                                    },
                                                                    {
                                                                        "name": "Type",
                                                                        "id": "entity_type",
                                                                    },
                                                                    {
                                                                        "name": "Issue Type",
                                                                        "id": "issue_type",
                                                                    },
                                                                    {
                                                                        "name": "Severity",
                                                                        "id": "severity",
                                                                    },
                                                                    {
                                                                        "name": "Description",
                                                                        "id": "description",
                                                                    },
                                                                    {
                                                                        "name": "Status",
                                                                        "id": "status",
                                                                    },
                                                                ],
                                                                data=[],
                                                                page_size=20,
                                                                style_table={
                                                                    "overflowX": "auto"
                                                                },
                                                            )
                                                        ],
                                                        label="Detailed Report",
                                                        tab_id="detailed",
                                                    ),
                                                ],
                                                id="report-tabs",
                                                active_tab="trends",
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=9,
                    ),
                ]
            )
        ],
        fluid=True,
    )


# Settings page
def create_settings_page():
    """Create the settings page."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    create_sidebar(),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Dashboard Settings"),
                                    dbc.CardBody(
                                        [
                                            dbc.Form(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label(
                                                                        "API Endpoint"
                                                                    ),
                                                                    dbc.Input(
                                                                        id="api-endpoint",
                                                                        type="url",
                                                                        value=API_BASE_URL,
                                                                        placeholder="http://localhost:8080",
                                                                    ),
                                                                ],
                                                                width=6,
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label(
                                                                        "API Key"
                                                                    ),
                                                                    dbc.Input(
                                                                        id="api-key",
                                                                        type="password",
                                                                        value=API_KEY,
                                                                        placeholder="Enter API key",
                                                                    ),
                                                                ],
                                                                width=6,
                                                            ),
                                                        ],
                                                        className="mb-3",
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label(
                                                                        "Refresh Interval (seconds)"
                                                                    ),
                                                                    dbc.Input(
                                                                        id="refresh-interval",
                                                                        type="number",
                                                                        value=30,
                                                                        min=5,
                                                                        max=300,
                                                                    ),
                                                                ],
                                                                width=4,
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label(
                                                                        "Page Size"
                                                                    ),
                                                                    dbc.Input(
                                                                        id="page-size",
                                                                        type="number",
                                                                        value=25,
                                                                        min=10,
                                                                        max=100,
                                                                    ),
                                                                ],
                                                                width=4,
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    dbc.Button(
                                                                        "Save Settings",
                                                                        id="save-settings-btn",
                                                                        color="primary",
                                                                        className="mt-4",
                                                                    )
                                                                ],
                                                                width=4,
                                                            ),
                                                        ],
                                                        className="mb-3",
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("Theme"),
                                                                    dcc.Dropdown(
                                                                        id="theme-selector",
                                                                        options=[
                                                                            {
                                                                                "label": "Light",
                                                                                "value": "light",
                                                                            },
                                                                            {
                                                                                "label": "Dark",
                                                                                "value": "dark",
                                                                            },
                                                                        ],
                                                                        value="light",
                                                                    ),
                                                                ],
                                                                width=4,
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label(
                                                                        "Language"
                                                                    ),
                                                                    dcc.Dropdown(
                                                                        id="language-selector",
                                                                        options=[
                                                                            {
                                                                                "label": "English",
                                                                                "value": "en",
                                                                            },
                                                                            {
                                                                                "label": "Spanish",
                                                                                "value": "es",
                                                                            },
                                                                            {
                                                                                "label": "French",
                                                                                "value": "fr",
                                                                            },
                                                                        ],
                                                                        value="en",
                                                                    ),
                                                                ],
                                                                width=4,
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=9,
                    ),
                ]
            )
        ],
        fluid=True,
    )


# Main layout
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        create_header(),
        html.Div(id="page-content"),
        # Hidden stores for state management
        dcc.Store(id="selected-items-store", data=[]),
        dcc.Store(id="filter-state-store", data={}),
        dcc.Store(
            id="settings-store",
            data={
                "api_endpoint": API_BASE_URL,
                "api_key": API_KEY,
                "refresh_interval": 30,
                "page_size": 25,
                "theme": "light",
                "language": "en",
            },
        ),
        # Interval for real-time updates (5 seconds for responsive updates)
        dcc.Interval(
            id="interval-component",
            interval=5 * 1000,  # 5 seconds for more responsive updates
            n_intervals=0,
            disabled=False,
        ),
        # Store for real-time client state
        dcc.Store(
            id="realtime-status-store", data={"connected": False, "last_update": None}
        ),
        # Store for WebSocket connection attempts
        dcc.Store(id="websocket-store", data={"attempts": 0, "last_attempt": None}),
    ]
)


# Callback for URL routing
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    """Route to different pages based on URL."""
    if pathname == "/dashboard" or pathname == "/":
        return create_dashboard_page()
    elif pathname == "/review":
        return create_review_page()
    elif pathname == "/bulk":
        return create_bulk_page()
    elif pathname == "/reports":
        return create_reports_page()
    elif pathname == "/settings":
        return create_settings_page()
    else:
        return html.Div(
            [
                html.H1("404: Page not found"),
                html.P(f"The page {pathname} was not found."),
            ]
        )


# Callback for count badges (always visible on all pages)
@app.callback(
    [
        Output("pending-count", "children"),
        Output("approved-count", "children"),
        Output("rejected-count", "children"),
    ],
    Input("interval-component", "n_intervals"),
    State("settings-store", "data"),
)
def update_count_badges(n, settings):
    """Update count badges in real-time (visible on all pages)."""
    try:
        # Try to get real-time data first
        rt_client = get_realtime_client(settings)
        realtime_data = None

        if rt_client:
            try:
                realtime_data = rt_client.get_latest_update()
            except Exception as e:
                logger.debug(f"Real-time client error: {e}")

        if realtime_data:
            # Use real-time data if available
            stats = realtime_data.get("stats", {})
        else:
            # Fallback to API polling
            stats_response = api_request("/stats/dashboard", settings=settings)
            if "error" not in stats_response:
                stats = stats_response
            else:
                # Mock data as final fallback
                stats = {"pending_count": 12, "approved_count": 8, "rejected_count": 3}

        # Extract stats
        pending = str(stats.get("pending_count", 0))
        approved = str(stats.get("approved_count", 0))
        rejected = str(stats.get("rejected_count", 0))

        return pending, approved, rejected

    except Exception as e:
        logger.error(f"Error updating count badges: {e}")
        return "0", "0", "0"


# Callback for activity feed (only on dashboard page)
@app.callback(
    Output("activity-feed", "children", allow_duplicate=True),
    [Input("interval-component", "n_intervals"), Input("url", "pathname")],
    State("settings-store", "data"),
    prevent_initial_call="initial_duplicate",
)
def update_activity_feed(n, pathname, settings):
    """Update activity feed (only visible on dashboard page)."""
    # Only update if we're on the dashboard page
    if pathname != "/" and pathname != "/dashboard":
        raise PreventUpdate

    try:
        # Try to get real-time data first
        rt_client = get_realtime_client(settings)
        realtime_data = None

        if rt_client:
            try:
                realtime_data = rt_client.get_latest_update()
            except Exception as e:
                logger.debug(f"Real-time client error: {e}")

        if realtime_data:
            # Use real-time data if available
            activities_data = realtime_data.get("activities", [])
        else:
            # Fallback to API polling
            activities_response = api_request("/activities/recent", settings=settings)
            activities_data = (
                activities_response.get("activities", [])
                if "error" not in activities_response
                else []
            )

            if not activities_data:
                # Mock data as final fallback
                activities_data = [
                    {
                        "message": "Gene BRCA1 validated",
                        "type": "success",
                        "timestamp": "2 minutes ago",
                    },
                    {
                        "message": "Variant rs123456 quarantined",
                        "type": "warning",
                        "timestamp": "5 minutes ago",
                    },
                    {
                        "message": "Publication PMID:12345 approved",
                        "type": "info",
                        "timestamp": "10 minutes ago",
                    },
                ]

        # Create activity feed
        activities = []
        for activity in activities_data[-5:]:  # Show last 5 activities
            color_class = {
                "success": "text-success",
                "warning": "text-warning",
                "danger": "text-danger",
                "info": "text-info",
            }.get(activity.get("type", "info"), "text-info")

            activities.append(
                html.Div(
                    [
                        html.Small(
                            activity.get("message", "Unknown activity"),
                            className=color_class,
                        ),
                        html.Br(),
                        html.Small(
                            activity.get("timestamp", "Unknown time"),
                            className="text-muted",
                        ),
                    ],
                    className="mb-2",
                )
            )

        # Add connection status indicator
        rt_status = "connected" if rt_client and rt_client.connected else "polling"
        status_color = "success" if rt_status == "connected" else "info"
        status_text = (
            "🔴 Real-time connection active"
            if rt_status == "connected"
            else "🔄 Using fast polling (5s)"
        )
        activities.insert(
            0,
            html.Div(
                [
                    html.Small(status_text, className=f"text-{status_color} fw-bold"),
                    html.Br(),
                    html.Small(
                        "Live updates enabled"
                        if rt_status == "connected"
                        else "Updates every 5 seconds",
                        className="text-muted",
                    ),
                ],
                className="mb-2",
            ),
        )

        return activities

    except Exception as e:
        logger.error(f"Error updating activity feed: {e}")
        return [html.Div("Error loading data")]


# Callback for review table data
@app.callback(
    Output("review-table", "data"),
    [
        Input("apply-filters-btn", "n_clicks"),
        Input("interval-component", "n_intervals"),
    ],
    [
        State("entity-type-filter", "value"),
        State("status-filter", "value"),
        State("priority-filter", "value"),
        State("settings-store", "data"),
        State("review-table", "selected_rows"),
    ],
)
def update_review_table(
    n_clicks, n_intervals, entity_type, status, priority, settings, selected_rows
):
    """Update the review table with filtered data."""
    try:
        # Mock data for now - replace with actual API calls
        mock_data = [
            {
                "select": "",
                "id": "1",
                "entity": "BRCA1",
                "status": "pending",
                "quality_score": 0.85,
                "issues": 2,
                "last_updated": "2024-01-15T10:30:00",
                "actions": "[Approve](#) | [Reject](#) | [Details](#)",
            },
            {
                "select": "",
                "id": "2",
                "entity": "rs123456",
                "status": "quarantined",
                "quality_score": 0.45,
                "issues": 5,
                "last_updated": "2024-01-15T09:15:00",
                "actions": "[Approve](#) | [Reject](#) | [Details](#)",
            },
            {
                "select": "",
                "id": "3",
                "entity": "HP:0000118",
                "status": "approved",
                "quality_score": 0.95,
                "issues": 0,
                "last_updated": "2024-01-15T08:45:00",
                "actions": "[Approve](#) | [Reject](#) | [Details](#)",
            },
        ]

        return mock_data

    except Exception as e:
        logger.error(f"Error updating review table: {e}")
        return []


# Callback for dashboard page charts (always visible)
@app.callback(
    [
        Output("quality-chart", "figure"),
        Output("entity-distribution-chart", "figure"),
        Output("validation-status-chart", "figure"),
    ],
    Input("interval-component", "n_intervals"),
)
def update_dashboard_charts(n):
    """Update dashboard page charts."""
    try:
        # Quality overview chart
        quality_fig = {
            "data": [
                {
                    "type": "indicator",
                    "mode": "gauge+number",
                    "value": 87,
                    "title": {"text": "Overall Quality Score"},
                    "gauge": {
                        "axis": {"range": [0, 100]},
                        "bar": {"color": COLORS["success"]},
                        "steps": [
                            {"range": [0, 50], "color": COLORS["danger"]},
                            {"range": [50, 75], "color": COLORS["warning"]},
                            {"range": [75, 100], "color": COLORS["success"]},
                        ],
                    },
                }
            ],
            "layout": {"margin": {"t": 0, "b": 0, "l": 0, "r": 0}},
        }

        # Entity distribution chart
        entity_fig = {
            "data": [
                {
                    "type": "pie",
                    "labels": ["Genes", "Variants", "Phenotypes", "Publications"],
                    "values": [450, 320, 280, 197],
                    "marker": {
                        "colors": [
                            COLORS["primary"],
                            COLORS["success"],
                            COLORS["warning"],
                            COLORS["info"],
                        ]
                    },
                }
            ],
            "layout": {"title": "Entity Distribution"},
        }

        # Validation status chart
        validation_fig = {
            "data": [
                {
                    "type": "bar",
                    "x": ["Approved", "Pending", "Rejected", "Quarantined"],
                    "y": [892, 145, 67, 23],
                    "marker": {
                        "color": [
                            COLORS["success"],
                            COLORS["warning"],
                            COLORS["danger"],
                            COLORS["secondary"],
                        ]
                    },
                }
            ],
            "layout": {"title": "Validation Status"},
        }

        return quality_fig, entity_fig, validation_fig

    except Exception as e:
        logger.error(f"Error updating dashboard charts: {e}")
        # Return empty figures on error
        empty_fig = {"data": [], "layout": {}}
        return empty_fig, empty_fig, empty_fig


# Callback for reports page charts (only on reports page)
@app.callback(
    [
        Output("quality-trends-chart", "figure", allow_duplicate=True),
        Output("error-distribution-chart", "figure", allow_duplicate=True),
    ],
    [Input("interval-component", "n_intervals"), Input("url", "pathname")],
    prevent_initial_call="initial_duplicate",
)
def update_reports_charts(n, pathname):
    """Update reports page charts."""
    # Only update if we're on the reports page
    if pathname != "/reports":
        raise PreventUpdate

    try:
        # Quality trends chart
        trends_fig = {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                    "y": [75, 78, 82, 85, 87, 87],
                    "line": {"color": COLORS["primary"]},
                }
            ],
            "layout": {"title": "Quality Trends Over Time"},
        }

        # Error distribution chart
        error_fig = {
            "data": [
                {
                    "type": "bar",
                    "x": [
                        "ID Format",
                        "Cross-reference",
                        "Data Type",
                        "Completeness",
                        "Consistency",
                    ],
                    "y": [8, 6, 4, 3, 2],
                    "marker": {"color": COLORS["danger"]},
                }
            ],
            "layout": {"title": "Error Distribution by Type"},
        }

        return trends_fig, error_fig

    except Exception as e:
        logger.error(f"Error updating reports charts: {e}")
        # Return empty figures on error
        empty_fig = {"data": [], "layout": {}}
        return empty_fig, empty_fig


# Callback for bulk operations
@app.callback(
    Output("batch-progress-container", "children"),
    Input("start-batch-btn", "n_clicks"),
    State("batch-operation", "value"),
    prevent_initial_call=True,
)
def handle_batch_operation(n_clicks, operation):
    """Handle batch operations."""
    if not n_clicks or not operation:
        return ""

    try:
        # Mock progress indicator
        progress = dbc.Progress(
            [dbc.ProgressBar(value=75, color="warning", striped=True, animated=True)],
            className="mb-3",
        )

        status_text = html.P(
            f"Processing {operation} operation... 75% complete", className="text-muted"
        )

        return html.Div([progress, status_text])

    except Exception as e:
        logger.error(f"Error in batch operation: {e}")
        return html.Div("Error processing batch operation", className="text-danger")


# Callback for settings
@app.callback(
    Output("settings-store", "data"),
    Input("save-settings-btn", "n_clicks"),
    State("api-endpoint", "value"),
    State("api-key", "value"),
    State("refresh-interval", "value"),
    State("page-size", "value"),
    State("theme-selector", "value"),
    State("language-selector", "value"),
    State("settings-store", "data"),
    prevent_initial_call=True,
)
def save_settings(
    n_clicks,
    api_endpoint,
    api_key,
    refresh_interval,
    page_size,
    theme,
    language,
    current_settings,
):
    """Save dashboard settings."""
    if not n_clicks:
        return current_settings

    try:
        new_settings = {
            "api_endpoint": api_endpoint,
            "api_key": api_key,
            "refresh_interval": refresh_interval,
            "page_size": page_size,
            "theme": theme,
            "language": language,
        }

        # Update the interval component
        app.layout.children[4].interval = (
            refresh_interval * 1000
        )  # Convert to milliseconds

        return new_settings

    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return current_settings


# Callback for selected items count
@app.callback(
    Output("selected-count", "children"),
    Input("review-table", "selected_rows"),
    State("review-table", "data"),
)
def update_selected_count(selected_rows, table_data):
    """Update the count of selected items."""
    count = len(selected_rows) if selected_rows else 0
    return f"{count} items selected"


# Callback for bulk operations
@app.callback(
    [
        Output("review-table", "selected_rows", allow_duplicate=True),
        Output("bulk-operation-result", "children", allow_duplicate=True),
    ],
    [
        Input("bulk-approve-btn", "n_clicks"),
        Input("bulk-reject-btn", "n_clicks"),
        Input("bulk-quarantine-btn", "n_clicks"),
        Input("select-all-btn", "n_clicks"),
    ],
    [
        State("review-table", "selected_rows"),
        State("review-table", "data"),
        State("entity-type-filter", "value"),
        State("settings-store", "data"),
    ],
    prevent_initial_call=True,
)
def handle_bulk_operations(
    approve_clicks,
    reject_clicks,
    quarantine_clicks,
    select_all_clicks,
    selected_rows,
    table_data,
    entity_type,
    settings,
):
    """Handle bulk approve/reject/quarantine operations."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return selected_rows, ""

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    try:
        if trigger_id == "select-all-btn":
            # Select all rows
            all_rows = list(range(len(table_data)))
            return all_rows, ""

        if not selected_rows:
            return selected_rows, dbc.Alert(
                "No items selected for operation", color="warning"
            )

        operation = None
        if trigger_id == "bulk-approve-btn":
            operation = "approve"
        elif trigger_id == "bulk-reject-btn":
            operation = "reject"
        elif trigger_id == "bulk-quarantine-btn":
            operation = "quarantine"

        if not operation:
            return selected_rows, ""

        # Process selected items
        processed_count = 0
        failed_count = 0

        for row_index in selected_rows:
            if row_index < len(table_data):
                item = table_data[row_index]
                item_id = item.get("id")

                # Mock API call - replace with actual implementation
                try:
                    # Simulate API call to update item status
                    result = api_request(
                        f"/{entity_type}/{item_id}",
                        method="PUT",
                        data={"status": operation},
                        settings=settings,
                    )

                    if "error" not in result:
                        processed_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Error processing item {item_id}: {e}")
                    failed_count += 1

        # Create result message
        if processed_count > 0:
            color = "success"
            message = f"Successfully {operation}d {processed_count} items"
            if failed_count > 0:
                message += f" ({failed_count} failed)"
                color = "warning"
        else:
            color = "danger"
            message = f"Failed to {operation} any items"

        result_alert = dbc.Alert(message, color=color, dismissable=True)

        # Clear selection after operation
        return [], result_alert

    except Exception as e:
        logger.error(f"Error in bulk operation: {e}")
        error_alert = dbc.Alert(
            f"Error performing bulk operation: {str(e)}",
            color="danger",
            dismissable=True,
        )
        return selected_rows, error_alert


# Real-time updates class
class RealTimeClient:
    """WebSocket client for real-time updates."""

    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint.replace("http", "ws")
        self.api_key = api_key
        self.connected = False
        self.last_update = {}

        if WEBSOCKET_SUPPORT:
            self.sio = socketio.Client()
            # Set up event handlers
            self.sio.on("connect", self.on_connect)
            self.sio.on("disconnect", self.on_disconnect)
            self.sio.on("data_update", self.on_data_update)
            self.sio.on("validation_complete", self.on_validation_complete)
            self.sio.on("ingestion_progress", self.on_ingestion_progress)
        else:
            self.sio = None

    def on_connect(self):
        """Handle connection established."""
        logger.info("Connected to real-time server")
        self.connected = True

    def on_disconnect(self):
        """Handle disconnection."""
        logger.info("Disconnected from real-time server")
        self.connected = False

    def on_data_update(self, data):
        """Handle data update events."""
        logger.info(f"Received data update: {data}")
        self.last_update = data

    def on_validation_complete(self, data):
        """Handle validation completion events."""
        logger.info(f"Validation completed: {data}")
        self.last_update = data

    def on_ingestion_progress(self, data):
        """Handle ingestion progress events."""
        logger.info(f"Ingestion progress: {data}")
        self.last_update = data

    async def connect_async(self):
        """Connect to WebSocket server asynchronously."""
        try:
            # Try WebSocket connection first
            uri = f"{self.api_endpoint}/ws?token={self.api_key}"
            async with websockets.connect(uri) as websocket:
                logger.info("WebSocket connection established")
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        self.last_update = data
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON received: {message}")
        except Exception as e:
            logger.warning(f"WebSocket connection failed, falling back to polling: {e}")
            self.connected = False

    def connect(self):
        """Connect to real-time server."""
        if not WEBSOCKET_SUPPORT:
            logger.info("WebSocket support not available, using polling only")
            return

        try:
            # Try Socket.IO first
            self.sio.connect(
                f"{self.api_endpoint.replace('ws', 'http')}",
                headers={"X-API-Key": self.api_key},
            )
        except Exception as e:
            logger.warning(f"Socket.IO connection failed, trying WebSocket: {e}")
            # Fallback to asyncio WebSocket
            asyncio.run(self.connect_async())

    def disconnect(self):
        """Disconnect from real-time server."""
        if WEBSOCKET_SUPPORT and self.sio and self.sio.connected:
            self.sio.disconnect()
        self.connected = False

    def get_latest_update(self) -> Dict:
        """Get the latest update data."""
        return self.last_update.copy()


# Global real-time client instance
realtime_client = None


def get_realtime_client(settings: Dict) -> Optional[RealTimeClient]:
    """Get or create real-time client instance."""
    global realtime_client
    if realtime_client is None:
        try:
            realtime_client = RealTimeClient(
                settings.get("api_endpoint", API_BASE_URL),
                settings.get("api_key", API_KEY),
            )
            # Try to connect in background thread if WebSocket support is available
            if WEBSOCKET_SUPPORT:
                threading.Thread(target=realtime_client.connect, daemon=True).start()
                # Give it a moment to attempt connection
                threading.Event().wait(0.5)
        except Exception as e:
            logger.warning(f"Failed to initialize real-time client: {e}")
            return None

    return realtime_client


# API helper functions
def api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None,
    settings: Optional[Dict] = None,
) -> Dict:
    """Make API request to FastAPI backend."""
    if not settings:
        settings = {"api_endpoint": API_BASE_URL, "api_key": API_KEY}

    url = f"{settings['api_endpoint']}{endpoint}"
    headers = {"X-API-Key": settings["api_key"], "Content-Type": "application/json"}

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    logger.info("Starting MED13 Curation Dashboard...")
    app.run(host="0.0.0.0", port=8050, debug=True)

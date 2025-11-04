"""
Data Sources Management Page

Main dashboard for managing user-configured data sources, including:
- Source listing and status overview
- Quick actions (add, edit, delete sources)
- Template library access
- Monitoring widgets
"""

import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html

from src.presentation.dash.components.theme import COLORS


def create_data_sources_page() -> html.Div:
    """Create the main data sources management page."""
    return html.Div(
        [
            # Page header with title and actions
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1("Data Sources", className="mb-3"),
                            html.P(
                                "Manage and monitor your biomedical data sources. "
                                "Connect to APIs, upload files, and track data quality.",
                                className="text-muted",
                            ),
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        "Add Source",
                                        id="add-source-btn",
                                        color="primary",
                                        className="me-2",
                                    ),
                                    dbc.Button(
                                        "Browse Templates",
                                        id="browse-templates-btn",
                                        color="outline-secondary",
                                        className="me-2",
                                    ),
                                    dbc.Button(
                                        "Import/Export",
                                        id="import-export-btn",
                                        color="outline-secondary",
                                    ),
                                ],
                                className="float-end",
                            ),
                        ],
                        width=4,
                    ),
                ],
                className="mb-4",
            ),
            # Stats cards row
            dbc.Row(
                [
                    dbc.Col(
                        create_stat_card(
                            "Total Sources",
                            "0",
                            "sources-total",
                            "fas fa-database",
                            "primary",
                        ),
                        width=3,
                    ),
                    dbc.Col(
                        create_stat_card(
                            "Active Sources",
                            "0",
                            "sources-active",
                            "fas fa-play-circle",
                            "success",
                        ),
                        width=3,
                    ),
                    dbc.Col(
                        create_stat_card(
                            "Data Quality",
                            "0%",
                            "quality-score",
                            "fas fa-star",
                            "warning",
                        ),
                        width=3,
                    ),
                    dbc.Col(
                        create_stat_card(
                            "Last Updated",
                            "--",
                            "last-updated",
                            "fas fa-clock",
                            "info",
                        ),
                        width=3,
                    ),
                ],
                className="mb-4",
            ),
            # Main content row
            dbc.Row(
                [
                    # Sources table column
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                "My Data Sources", className="mb-0"
                                            ),
                                            dbc.Badge(
                                                "Auto-refresh",
                                                id="auto-refresh-badge",
                                                color="secondary",
                                                className="ms-2",
                                            ),
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Filters and search
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        dbc.InputGroup(
                                                            [
                                                                dbc.InputGroupText(
                                                                    html.I(
                                                                        className="fas fa-search"
                                                                    )
                                                                ),
                                                                dbc.Input(
                                                                    id="sources-search",
                                                                    placeholder="Search sources...",
                                                                    type="text",
                                                                ),
                                                            ]
                                                        ),
                                                        width=4,
                                                    ),
                                                    dbc.Col(
                                                        dbc.Select(
                                                            id="sources-status-filter",
                                                            options=[
                                                                {
                                                                    "label": "All Status",
                                                                    "value": "all",
                                                                },
                                                                {
                                                                    "label": "Active",
                                                                    "value": "active",
                                                                },
                                                                {
                                                                    "label": "Draft",
                                                                    "value": "draft",
                                                                },
                                                                {
                                                                    "label": "Error",
                                                                    "value": "error",
                                                                },
                                                                {
                                                                    "label": "Inactive",
                                                                    "value": "inactive",
                                                                },
                                                            ],
                                                            value="all",
                                                        ),
                                                        width=3,
                                                    ),
                                                    dbc.Col(
                                                        dbc.Select(
                                                            id="sources-type-filter",
                                                            options=[
                                                                {
                                                                    "label": "All Types",
                                                                    "value": "all",
                                                                },
                                                                {
                                                                    "label": "API",
                                                                    "value": "api",
                                                                },
                                                                {
                                                                    "label": "File",
                                                                    "value": "file",
                                                                },
                                                                {
                                                                    "label": "Database",
                                                                    "value": "database",
                                                                },
                                                            ],
                                                            value="all",
                                                        ),
                                                        width=3,
                                                    ),
                                                    dbc.Col(
                                                        dbc.Button(
                                                            "Refresh",
                                                            id="refresh-sources-btn",
                                                            color="outline-primary",
                                                            size="sm",
                                                        ),
                                                        width=2,
                                                        className="text-end",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            # Sources table
                                            dash_table.DataTable(  # type: ignore
                                                id="sources-table",
                                                columns=[
                                                    {
                                                        "name": "Name",
                                                        "id": "name",
                                                        "type": "text",
                                                        "presentation": "markdown",
                                                    },
                                                    {
                                                        "name": "Type",
                                                        "id": "source_type",
                                                        "type": "text",
                                                    },
                                                    {
                                                        "name": "Status",
                                                        "id": "status",
                                                        "type": "text",
                                                        "presentation": "markdown",
                                                    },
                                                    {
                                                        "name": "Quality",
                                                        "id": "quality_score",
                                                        "type": "numeric",
                                                        "format": {"specifier": ".1%"},
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
                                                page_size=10,
                                                page_current=0,
                                                page_action="native",
                                                sort_action="native",
                                                sort_mode="multi",
                                                filter_action="native",
                                                style_table={"overflowX": "auto"},
                                                style_cell={
                                                    "textAlign": "left",
                                                    "padding": "8px",
                                                    "minWidth": "100px",
                                                },
                                                style_header={
                                                    "backgroundColor": COLORS["light"],
                                                    "fontWeight": "bold",
                                                },
                                                style_data_conditional=[
                                                    {
                                                        "if": {"row_index": "odd"},
                                                        "backgroundColor": COLORS[
                                                            "light"
                                                        ],
                                                    }
                                                ],
                                                markdown_options={
                                                    "link_target": "_blank"
                                                },
                                            ),
                                            # Bulk actions
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        dbc.Checklist(
                                                            options=[
                                                                {
                                                                    "label": "Select All",
                                                                    "value": "select_all",
                                                                }
                                                            ],
                                                            value=[],
                                                            id="select-all-sources",
                                                            inline=True,
                                                            className="mt-3",
                                                        ),
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        dbc.ButtonGroup(
                                                            [
                                                                dbc.Button(
                                                                    "Bulk Edit",
                                                                    id="bulk-edit-btn",
                                                                    color="outline-primary",
                                                                    size="sm",
                                                                    disabled=True,
                                                                ),
                                                                dbc.Button(
                                                                    "Bulk Delete",
                                                                    id="bulk-delete-btn",
                                                                    color="outline-danger",
                                                                    size="sm",
                                                                    disabled=True,
                                                                ),
                                                            ],
                                                            className="float-end mt-2",
                                                        ),
                                                        width=6,
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=8,
                    ),
                    # Sidebar with monitoring and templates
                    dbc.Col(
                        [
                            # Recent Activity
                            dbc.Card(
                                [
                                    dbc.CardHeader("Recent Activity"),
                                    dbc.CardBody(
                                        html.Div(
                                            id="recent-activity",
                                            children=[
                                                html.P(
                                                    "No recent activity",
                                                    className="text-muted",
                                                )
                                            ],
                                        )
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Quick Templates
                            dbc.Card(
                                [
                                    dbc.CardHeader("Quick Templates"),
                                    dbc.CardBody(
                                        html.Div(
                                            id="quick-templates",
                                            children=[
                                                dbc.Button(
                                                    "ClinVar API",
                                                    id="template-clinvar",
                                                    color="outline-primary",
                                                    size="sm",
                                                    className="w-100 mb-2",
                                                ),
                                                dbc.Button(
                                                    "CSV Upload",
                                                    id="template-csv",
                                                    color="outline-primary",
                                                    size="sm",
                                                    className="w-100 mb-2",
                                                ),
                                                dbc.Button(
                                                    "PubMed API",
                                                    id="template-pubmed",
                                                    color="outline-primary",
                                                    size="sm",
                                                    className="w-100",
                                                ),
                                            ],
                                        )
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Quality Metrics
                            dbc.Card(
                                [
                                    dbc.CardHeader("Quality Overview"),
                                    dbc.CardBody(
                                        [
                                            dbc.Progress(
                                                id="quality-progress",
                                                value=75,
                                                max=100,
                                                color="success",
                                                striped=True,
                                                animated=True,
                                                className="mb-2",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "75%",
                                                        id="quality-percentage",
                                                        className="fw-bold text-success",
                                                    ),
                                                    html.Small(
                                                        " Overall data quality across all sources",
                                                        className="text-muted ms-2",
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=4,
                    ),
                ]
            ),
            # Hidden stores for state management
            dcc.Store(id="sources-data-store", data=[]),
            dcc.Store(id="selected-sources-store", data=[]),
            dcc.Store(id="templates-data-store", data=[]),
            # Modals
            create_add_source_modal(),
            create_template_browser_modal(),
            create_source_details_modal(),
        ],
        className="container-fluid p-4",
    )


def create_stat_card(
    title: str, value: str, value_id: str, icon: str, color: str
) -> dbc.Card:
    """Create a statistics card."""
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.I(className=f"{icon} fa-2x text-{color} mb-2"),
                        html.H4(value, id=value_id, className="card-title mb-0"),
                        html.P(title, className="card-text text-muted small"),
                    ],
                    className="text-center",
                )
            ]
        ),
        className="h-100",
    )


def create_add_source_modal() -> dbc.Modal:
    """Create the add source modal with wizard steps."""
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("Add Data Source"),
                id="add-source-modal-header",
            ),
            dbc.ModalBody(
                html.Div(
                    id="add-source-modal-body",
                    children=[
                        # Step 1: Choose source type
                        html.Div(
                            id="step-1-type",
                            children=[
                                html.H5("Choose Source Type"),
                                html.P(
                                    "Select the type of data source you want to add:"
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Card(
                                                [
                                                    dbc.CardBody(
                                                        [
                                                            html.I(
                                                                className="fas fa-globe fa-3x text-primary mb-3"
                                                            ),
                                                            html.H5("API Source"),
                                                            html.P(
                                                                "Connect to REST APIs, databases, or web services",
                                                                className="text-muted small",
                                                            ),
                                                            dbc.Button(
                                                                "Select API",
                                                                id="select-api-type",
                                                                color="primary",
                                                                className="mt-3",
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    )
                                                ],
                                                className="mb-3",
                                            ),
                                            width=6,
                                        ),
                                        dbc.Col(
                                            dbc.Card(
                                                [
                                                    dbc.CardBody(
                                                        [
                                                            html.I(
                                                                className="fas fa-file-upload fa-3x text-success mb-3"
                                                            ),
                                                            html.H5("File Upload"),
                                                            html.P(
                                                                "Upload CSV, JSON, XML, or other data files",
                                                                className="text-muted small",
                                                            ),
                                                            dbc.Button(
                                                                "Select File",
                                                                id="select-file-type",
                                                                color="success",
                                                                className="mt-3",
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    )
                                                ],
                                                className="mb-3",
                                            ),
                                            width=6,
                                        ),
                                    ]
                                ),
                            ],
                        ),
                        # Step 2: Configure source (hidden initially)
                        html.Div(
                            id="step-2-configure",
                            style={"display": "none"},
                            children=[
                                html.H5("Configure Source"),
                                # Configuration form will be populated by callbacks
                                html.Div(id="source-config-form"),
                            ],
                        ),
                        # Step 3: Review and save (hidden initially)
                        html.Div(
                            id="step-3-review",
                            style={"display": "none"},
                            children=[
                                html.H5("Review Configuration"),
                                html.Div(id="source-review-content"),
                            ],
                        ),
                    ],
                )
            ),
            dbc.ModalFooter(
                dbc.ButtonGroup(
                    [
                        dbc.Button(
                            "Previous",
                            id="wizard-prev-btn",
                            color="secondary",
                            disabled=True,
                        ),
                        dbc.Button(
                            "Next",
                            id="wizard-next-btn",
                            color="primary",
                        ),
                        dbc.Button(
                            "Cancel",
                            id="wizard-cancel-btn",
                            color="light",
                        ),
                    ]
                )
            ),
        ],
        id="add-source-modal",
        size="lg",
        is_open=False,
    )


def create_template_browser_modal() -> dbc.Modal:
    """Create the template browser modal."""
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Browse Templates")),
            dbc.ModalBody(
                [
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(html.I(className="fas fa-search")),
                            dbc.Input(
                                id="template-search",
                                placeholder="Search templates...",
                                type="text",
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Select(
                        id="template-category-filter",
                        options=[
                            {"label": "All Categories", "value": "all"},
                            {"label": "Clinical", "value": "clinical"},
                            {"label": "Research", "value": "research"},
                            {"label": "Genomic", "value": "genomic"},
                        ],
                        value="all",
                        className="mb-3",
                    ),
                    html.Div(id="templates-grid", children=[]),
                ]
            ),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-templates-btn", color="secondary")
            ),
        ],
        id="template-browser-modal",
        size="xl",
        is_open=False,
    )


def create_source_details_modal() -> dbc.Modal:
    """Create the source details/edit modal."""
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Source Details")),
            dbc.ModalBody(html.Div(id="source-details-content")),
            dbc.ModalFooter(
                dbc.ButtonGroup(
                    [
                        dbc.Button(
                            "Save Changes",
                            id="save-source-btn",
                            color="primary",
                        ),
                        dbc.Button(
                            "Delete Source",
                            id="delete-source-btn",
                            color="danger",
                        ),
                        dbc.Button(
                            "Close",
                            id="close-source-details-btn",
                            color="secondary",
                        ),
                    ]
                )
            ),
        ],
        id="source-details-modal",
        size="lg",
        is_open=False,
    )

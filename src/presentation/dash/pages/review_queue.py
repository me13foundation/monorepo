from typing import List

from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dcc import Dropdown

from src.presentation.dash.components.sidebar import create_sidebar
from src.presentation.dash.components.record_viewer import create_data_table
from src.presentation.dash.components.theme import COLORS
from src.presentation.dash.components.curation.clinical_card import (
    create_clinical_card_grid,
    create_enhanced_filters,
)
from src.presentation.dash.components.curation.clinical_viewer import (
    render_clinical_viewer,
)
from src.presentation.dash.components.curation.evidence_comparison import (
    render_evidence_matrix,
)
from src.presentation.dash.components.curation.conflict_panel import (
    render_conflict_panel,
)
from src.presentation.dash.components.curation.audit_summary import (
    render_audit_summary,
)

DropdownOption = Dropdown.Options

ENTITY_TYPE_OPTIONS: List[DropdownOption] = [
    {"label": "Genes", "value": "genes"},
    {"label": "Variants", "value": "variants"},
    {"label": "Phenotypes", "value": "phenotypes"},
    {"label": "Publications", "value": "publications"},
]

STATUS_OPTIONS: List[DropdownOption] = [
    {"label": "Pending", "value": "pending"},
    {"label": "Approved", "value": "approved"},
    {"label": "Rejected", "value": "rejected"},
    {"label": "Quarantined", "value": "quarantined"},
]

PRIORITY_OPTIONS: List[DropdownOption] = [
    {"label": "High", "value": "high"},
    {"label": "Medium", "value": "medium"},
    {"label": "Low", "value": "low"},
]


def create_review_page() -> dbc.Container:
    """Create the review queue page layout."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    create_sidebar("/review"),
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
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        html.I(className="fas fa-th"),
                                                        id="card-view-btn",
                                                        color="outline-primary",
                                                        size="sm",
                                                        title="Card View",
                                                        active=True,
                                                    ),
                                                    dbc.Button(
                                                        html.I(
                                                            className="fas fa-table"
                                                        ),
                                                        id="table-view-btn",
                                                        color="outline-primary",
                                                        size="sm",
                                                        title="Table View",
                                                    ),
                                                ],
                                                className="ms-auto",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center",
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Entity Type"),
                                                            dcc.Dropdown(
                                                                id="entity-type-filter",
                                                                options=ENTITY_TYPE_OPTIONS,
                                                                value="variants",  # Default to variants for clinical review
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
                                                                options=STATUS_OPTIONS,
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
                                                                options=PRIORITY_OPTIONS,
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
                                                            ),
                                                        ],
                                                        width=3,
                                                    ),
                                                ],
                                                className="mb-4",
                                            ),
                                            # Enhanced Clinical Filters
                                            create_enhanced_filters(),
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
                                                            ),
                                                        ],
                                                        width=4,
                                                        className="text-end",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            html.Div(
                                                id="bulk-operation-result",
                                                className="mb-3",
                                            ),
                                            # Clinical Review Cards Grid
                                            html.Div(
                                                id="clinical-card-container",
                                                children=create_clinical_card_grid(
                                                    []
                                                ),  # Will be populated by callbacks
                                            ),
                                            # Fallback to old table view (can be toggled)
                                            html.Div(
                                                id="table-view-container",
                                                style={
                                                    "display": "none"
                                                },  # Hidden by default
                                                children=create_data_table(
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
                                                        "backgroundColor": COLORS[
                                                            "light"
                                                        ],
                                                        "fontWeight": "bold",
                                                    },
                                                    style_data_conditional=[
                                                        {
                                                            "if": {"row_index": "odd"},
                                                            "backgroundColor": "rgb(248, 248, 248)",
                                                        }
                                                    ],
                                                ),
                                            ),
                                            dcc.Store(
                                                id="curation-detail-store",
                                                data=None,
                                            ),
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        html.Div(
                                                            [
                                                                html.H4(
                                                                    "Clinical Detail",
                                                                    className="mb-0",
                                                                ),
                                                                dbc.Badge(
                                                                    "Context",
                                                                    color="primary",
                                                                    className="ms-2",
                                                                ),
                                                            ],
                                                            className="d-flex align-items-center",
                                                        )
                                                    ),
                                                    dbc.CardBody(
                                                        dcc.Loading(
                                                            id="curation-detail-loading",
                                                            type="default",
                                                            children=[
                                                                html.Div(
                                                                    id="curation-summary-panel",
                                                                    children=render_clinical_viewer(
                                                                        None, ()
                                                                    ),
                                                                ),
                                                                html.Hr(),
                                                                html.Div(
                                                                    id="curation-evidence-panel",
                                                                    children=render_evidence_matrix(
                                                                        ()
                                                                    ),
                                                                ),
                                                                html.Hr(),
                                                                html.Div(
                                                                    id="curation-conflict-panel",
                                                                    children=render_conflict_panel(
                                                                        ()
                                                                    ),
                                                                ),
                                                                html.Hr(),
                                                                html.Div(
                                                                    id="curation-audit-panel",
                                                                    children=render_audit_summary(
                                                                        None
                                                                    ),
                                                                ),
                                                            ],
                                                        )
                                                    ),
                                                ],
                                                id="curation-detail-container",
                                                className="mt-4 shadow-sm",
                                                style={"display": "none"},
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


__all__ = ["create_review_page"]

from dash import html, dcc
import dash_bootstrap_components as dbc

from src.presentation.dash.components.sidebar import create_sidebar
from src.presentation.dash.components.record_viewer import create_data_table


def create_reports_page() -> dbc.Container:
    """Create the reports page."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    create_sidebar("/reports"),
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
                                                                id="quality-trends-chart",
                                                                config={
                                                                    "displayModeBar": False
                                                                },
                                                            )
                                                        ],
                                                        label="Quality Trends",
                                                        tab_id="trends",
                                                    ),
                                                    dbc.Tab(
                                                        [
                                                            dcc.Graph(
                                                                id="error-distribution-chart",
                                                                config={
                                                                    "displayModeBar": False
                                                                },
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


__all__ = ["create_reports_page"]

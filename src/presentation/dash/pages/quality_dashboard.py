from dash import html, dcc
import dash_bootstrap_components as dbc

from src.presentation.dash.components.sidebar import create_sidebar


def create_dashboard_page() -> dbc.Container:
    """Create the main dashboard page layout."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    create_sidebar("/"),
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
                                                        [
                                                            dcc.Graph(
                                                                id="quality-chart",
                                                                config={
                                                                    "displayModeBar": False
                                                                },
                                                            )
                                                        ]
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
                                                                id="entity-distribution-chart",
                                                                config={
                                                                    "displayModeBar": False
                                                                },
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
                                                                id="validation-status-chart",
                                                                config={
                                                                    "displayModeBar": False
                                                                },
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


__all__ = ["create_dashboard_page"]

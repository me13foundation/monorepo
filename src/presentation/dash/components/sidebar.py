from typing import List

from dash import html
import dash_bootstrap_components as dbc
from dash.development.base_component import Component


def create_sidebar(current_page: str = "/") -> dbc.Col:
    """Create sidebar with quick stats and actions."""
    quick_actions: List[Component] = [
        dbc.Button(
            "Refresh Data", id="refresh-btn", color="primary", className="w-100 mb-2"
        ),
    ]

    if current_page == "/review":
        quick_actions.extend(
            [
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
        )

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
                    dbc.CardBody(quick_actions),
                ]
            ),
        ],
        width=3,
    )


__all__ = ["create_sidebar"]

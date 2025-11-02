from typing import List

from dash import dcc
import dash_bootstrap_components as dbc
from dash.dcc import Dropdown

from src.presentation.dash.components.sidebar import create_sidebar

DropdownOption = Dropdown.Options

THEME_OPTIONS: List[DropdownOption] = [
    {"label": "Light", "value": "light"},
    {"label": "Dark", "value": "dark"},
]

LANGUAGE_OPTIONS: List[DropdownOption] = [
    {"label": "English", "value": "en"},
    {"label": "Spanish", "value": "es"},
    {"label": "French", "value": "fr"},
]


def create_settings_page() -> dbc.Container:
    """Create the settings page."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    create_sidebar("/settings"),
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
                                                                        value="http://localhost:8080",
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
                                                                        value="med13-admin-key",
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
                                                                        options=THEME_OPTIONS,
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
                                                                        options=LANGUAGE_OPTIONS,
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


__all__ = ["create_settings_page"]

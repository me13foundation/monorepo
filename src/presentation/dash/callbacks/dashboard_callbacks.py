"""Callbacks for app routing and the dashboard page.

This module wires URL routing to page layouts and will be extended with
dashboard-specific callbacks.
"""

from typing import cast

from dash import Dash, Input, Output, html
from dash.development.base_component import Component

from src.presentation.dash.pages.quality_dashboard import create_dashboard_page
from src.presentation.dash.pages.review_queue import create_review_page
from src.presentation.dash.pages.approval_history import create_bulk_page
from src.presentation.dash.pages.reports import create_reports_page
from src.presentation.dash.pages.settings import create_settings_page
from src.presentation.dash.pages.data_sources import create_data_sources_page


def register_callbacks(app: Dash) -> None:
    @app.callback(Output("page-content", "children"), Input("url", "pathname"))
    def display_page(pathname: str) -> Component:
        if pathname in {"/dashboard", "/"}:
            page = create_dashboard_page()
        elif pathname == "/review":
            page = create_review_page()
        elif pathname == "/bulk":
            page = create_bulk_page()
        elif pathname == "/reports":
            page = create_reports_page()
        elif pathname == "/settings":
            page = create_settings_page()
        elif pathname == "/data-sources":
            page = create_data_sources_page()
        else:
            page = html.Div(
                [
                    html.H1("404: Page not found"),
                    html.P(f"The page {pathname} was not found."),
                ]
            )

        return cast(Component, page)

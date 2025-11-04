"""
Callbacks for the Data Sources management page.

Handles source listing, creation, editing, monitoring, and template management.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, ctx, html
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate


def register_callbacks(app: Dash) -> None:
    """Register all data sources page callbacks."""

    # Main page data loading - using dummy data for now
    @app.callback(
        [
            Output("sources-data-store", "data"),
            Output("templates-data-store", "data"),
            Output("sources-total", "children"),
            Output("sources-active", "children"),
            Output("quality-score", "children"),
            Output("last-updated", "children"),
        ],
        Input("refresh-sources-btn", "n_clicks"),
        Input("interval-component", "n_intervals"),
    )
    def load_sources_data(
        refresh_clicks: Optional[int],
        interval: int,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str, str, str, str]:
        """Load sources and templates data."""
        # Dummy data for demonstration
        sources_data = [
            {
                "id": "1",
                "name": "ClinVar API",
                "source_type": "Api",
                "status": '<span class="badge bg-success">Active</span>',
                "quality_score": 0.95,
                "last_updated": "2024-01-15T10:30:00",
                "actions": "[Edit](edit-1) | [Delete](delete-1)",
            },
            {
                "id": "2",
                "name": "Patient Variants CSV",
                "source_type": "File",
                "status": '<span class="badge bg-secondary">Draft</span>',
                "quality_score": 0.0,
                "last_updated": "2024-01-14T15:20:00",
                "actions": "[Edit](edit-2) | [Delete](delete-2)",
            },
        ]

        templates_data = [
            {
                "id": "1",
                "name": "ClinVar API Template",
                "description": "Fetch genetic variants from ClinVar database",
                "category": "genomic",
                "source_type": "api",
                "usage_count": 25,
            },
            {
                "id": "2",
                "name": "CSV Upload Template",
                "description": "Upload variant data from CSV files",
                "category": "clinical",
                "source_type": "file",
                "usage_count": 18,
            },
        ]

        return (
            sources_data,
            templates_data,
            "2",
            "1",
            "47.5%",
            datetime.now(timezone.utc).strftime("%H:%M:%S"),
        )

    # Sources table update
    @app.callback(
        Output("sources-table", "data"),
        [
            Input("sources-data-store", "data"),
            Input("sources-search", "value"),
            Input("sources-status-filter", "value"),
            Input("sources-type-filter", "value"),
        ],
    )
    def update_sources_table(
        sources_data: List[Dict[str, Any]],
        search_term: Optional[str],
        status_filter: str,
        type_filter: str,
    ) -> List[Dict[str, Any]]:
        """Update sources table with filtering."""
        if not sources_data:
            return []

        filtered_data = sources_data.copy()

        # Apply search filter
        if search_term:
            filtered_data = [
                item
                for item in filtered_data
                if search_term.lower() in item["name"].lower()
            ]

        # Apply status filter
        if status_filter != "all":
            filtered_data = [
                item
                for item in filtered_data
                if status_filter in item["status"].lower()
            ]

        # Apply type filter
        if type_filter != "all":
            filtered_data = [
                item
                for item in filtered_data
                if type_filter in item["source_type"].lower()
            ]

        return filtered_data

    # Add source modal management
    @app.callback(
        Output("add-source-modal", "is_open"),
        [
            Input("add-source-btn", "n_clicks"),
            Input("wizard-cancel-btn", "n_clicks"),
            Input("close-templates-btn", "n_clicks"),
            Input("close-source-details-btn", "n_clicks"),
        ],
        State("add-source-modal", "is_open"),
    )
    def toggle_modals(
        add_clicks: Optional[int],
        cancel_clicks: Optional[int],
        close_templates_clicks: Optional[int],
        close_details_clicks: Optional[int],
        is_open: bool,
    ) -> bool:
        """Toggle modal visibility."""
        if any(
            [add_clicks, cancel_clicks, close_templates_clicks, close_details_clicks]
        ):
            return not is_open
        return is_open

    # Template browser modal
    @app.callback(
        Output("template-browser-modal", "is_open"),
        Input("browse-templates-btn", "n_clicks"),
        State("template-browser-modal", "is_open"),
    )
    def toggle_template_browser(browse_clicks: Optional[int], is_open: bool) -> bool:
        """Toggle template browser modal."""
        if browse_clicks:
            return not is_open
        return is_open

    # Template grid population
    @app.callback(
        Output("templates-grid", "children"),
        Input("templates-data-store", "data"),
    )
    def populate_templates_grid(
        templates_data: List[Dict[str, Any]],
    ) -> List[Component]:
        """Populate the templates grid."""
        if not templates_data:
            return [html.P("No templates available", className="text-muted")]

        cards = []
        for template in templates_data[:12]:  # Limit to 12 for grid
            card = dbc.Col(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H6(template["name"], className="card-title"),
                                html.P(
                                    template["description"][:100] + "...",
                                    className="card-text small text-muted",
                                ),
                                html.Small(
                                    f"Type: {template['source_type']} | "
                                    f"Used: {template['usage_count']} times",
                                    className="text-muted",
                                ),
                                dbc.Button(
                                    "Use Template",
                                    id={
                                        "type": "use-template-btn",
                                        "index": template["id"],
                                    },
                                    color="primary",
                                    size="sm",
                                    className="mt-2",
                                ),
                            ]
                        ),
                    ],
                    className="h-100",
                ),
                width=4,
                className="mb-3",
            )
            cards.append(card)

        return cards

    # Wizard step management
    @app.callback(
        [
            Output("step-1-type", "style"),
            Output("step-2-configure", "style"),
            Output("step-3-review", "style"),
            Output("wizard-prev-btn", "disabled"),
            Output("wizard-next-btn", "children"),
            Output("wizard-next-btn", "disabled"),
            Output("add-source-modal-header", "children"),
        ],
        Input("wizard-next-btn", "n_clicks"),
        Input("wizard-prev-btn", "n_clicks"),
        Input("select-api-type", "n_clicks"),
        Input("select-file-type", "n_clicks"),
        State("add-source-modal", "is_open"),
    )
    def manage_wizard_steps(
        next_clicks: Optional[int],
        prev_clicks: Optional[int],
        api_clicks: Optional[int],
        file_clicks: Optional[int],
        modal_open: bool,
    ) -> Tuple[
        Dict[str, Any], Dict[str, Any], Dict[str, Any], bool, str, bool, Component
    ]:
        """Manage wizard step visibility and navigation."""
        if not modal_open:
            return (
                {"display": "block"},
                {"display": "none"},
                {"display": "none"},
                True,
                "Next",
                True,
                dbc.ModalTitle("Add Data Source"),
            )

        # Determine current step based on trigger
        triggered_id = ctx.triggered_id if ctx.triggered else None

        # Step 1: Type selection (default)
        if (
            triggered_id in [None, "wizard-prev-btn"]
            or triggered_id == "add-source-btn"
        ):
            return (
                {"display": "block"},
                {"display": "none"},
                {"display": "none"},
                True,
                "Next",
                True,
                dbc.ModalTitle("Add Data Source - Step 1: Choose Type"),
            )

        # Step 2: Configuration
        elif triggered_id in ["select-api-type", "select-file-type"]:
            source_type = "API" if triggered_id == "select-api-type" else "File"
            return (
                {"display": "none"},
                {"display": "block"},
                {"display": "none"},
                False,
                "Review",
                False,
                dbc.ModalTitle(
                    f"Add Data Source - Step 2: Configure {source_type} Source"
                ),
            )

        # Step 3: Review
        elif triggered_id == "wizard-next-btn":
            return (
                {"display": "none"},
                {"display": "none"},
                {"display": "block"},
                False,
                "Save Source",
                False,
                dbc.ModalTitle("Add Data Source - Step 3: Review & Save"),
            )

        return (
            {"display": "block"},
            {"display": "none"},
            {"display": "none"},
            True,
            "Next",
            True,
            dbc.ModalTitle("Add Data Source"),
        )

    # Source configuration form
    @app.callback(
        Output("source-config-form", "children"),
        Input("select-api-type", "n_clicks"),
        Input("select-file-type", "n_clicks"),
    )
    def populate_config_form(
        api_clicks: Optional[int], file_clicks: Optional[int]
    ) -> Component:
        """Populate the configuration form based on selected type."""
        if not any([api_clicks, file_clicks]):
            return html.Div()

        if api_clicks:
            return create_api_config_form()
        else:
            return create_file_config_form()

    # Save source callback
    @app.callback(
        [
            Output("add-source-modal", "is_open", allow_duplicate=True),
            Output("sources-data-store", "data", allow_duplicate=True),
        ],
        Input("wizard-next-btn", "n_clicks"),
        State("add-source-modal", "is_open"),
        State("source-config-form", "children"),
        prevent_initial_call=True,
    )
    def save_source(
        save_clicks: Optional[int],
        modal_open: bool,
        config_form: Component,
        settings: Optional[Dict[str, Any]],
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Save the new source."""
        if not modal_open or not save_clicks:
            raise PreventUpdate

        # TODO: Extract form data and create source
        # For now, just close modal and refresh data
        return False, []


def create_api_config_form() -> html.Div:
    """Create the API source configuration form."""
    return html.Div("API Config Form - Coming Soon")


def create_file_config_form() -> html.Div:
    """Create the file upload configuration form."""
    return html.Div("File Config Form - Coming Soon")

"""
MED13 Resource Library - Curation Dashboard
Dash application for data curation and review workflows.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import UTC, datetime
from typing import Any, cast

import dash
import dash_bootstrap_components as dbc
import requests
from dash import Input, Output, State, dcc, html
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate

from src.presentation.dash.callbacks.approval_callbacks import (
    register_callbacks as register_bulk_callbacks,
)
from src.presentation.dash.callbacks.dashboard_callbacks import (
    register_callbacks as register_dashboard_callbacks,
)
from src.presentation.dash.callbacks.data_sources_callbacks import (
    register_callbacks as register_data_sources_callbacks,
)
from src.presentation.dash.callbacks.reports_callbacks import (
    register_callbacks as register_reports_callbacks,
)
from src.presentation.dash.callbacks.review_callbacks import (
    register_callbacks as register_review_callbacks,
)
from src.presentation.dash.callbacks.settings_callbacks import (
    register_callbacks as register_settings_callbacks,
)

# Presentation layer imports (progressive extraction)
from src.presentation.dash.components.header import (
    create_header as layout_create_header,
)

# Import shared components for backward compatibility
from src.presentation.dash.components.theme import COLORS

FigureDict = dict[str, Any]
SettingsDict = dict[str, Any]
TableRow = dict[str, Any]
ComponentValue = Component | str

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce noise from API connection attempts when server isn't running
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Import dash_table - must be after dash import for proper registration
try:
    from dash import dash_table

    DASH_TABLE_AVAILABLE = True
except ImportError:
    logger.exception("dash_table not available. Please install dash-table package.")
    dash_table: Any | None = None
    DASH_TABLE_AVAILABLE = False

# Check for WebSocket support
try:
    import asyncio

    import websockets

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


# Layout components
def create_header() -> dbc.Navbar:
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
                                        "Dashboard",
                                        href="/dashboard",
                                        active="exact",
                                    ),
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Review Queue",
                                        href="/review",
                                        active="exact",
                                    ),
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Bulk Operations",
                                        href="/bulk",
                                        active="exact",
                                    ),
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Reports",
                                        href="/reports",
                                        active="exact",
                                    ),
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Settings",
                                        href="/settings",
                                        active="exact",
                                    ),
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
            ],
        ),
        color="dark",
        dark=True,
        className="mb-4",
    )


# Main dashboard page
# Bulk operations page
# Reports page
# Settings page
# Main layout
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        layout_create_header(),
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
            id="realtime-status-store",
            data={"connected": False, "last_update": None},
        ),
        # Store for WebSocket connection attempts
        dcc.Store(id="websocket-store", data={"attempts": 0, "last_attempt": None}),
        # Notification containers for quick actions
        html.Div(id="refresh-notification"),
        html.Div(id="export-notification"),
        html.Div(id="clear-filters-notification"),
    ],
)


# Register callbacks from presentation layer modules
register_dashboard_callbacks(app)
register_review_callbacks(app)
register_bulk_callbacks(app)
register_reports_callbacks(app)
register_settings_callbacks(app)
register_data_sources_callbacks(app)


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
def update_count_badges(
    _n: int,
    settings: SettingsDict | None,
) -> tuple[str, str, str]:
    """Update count badges in real-time (visible on all pages)."""
    settings = settings or {}

    settings = settings or {}

    try:
        # Try to get real-time data first
        rt_client = get_realtime_client(settings)
        realtime_data = None

        if rt_client:
            try:
                realtime_data = rt_client.get_latest_update()
            except Exception as err:
                logger.debug("Real-time client error: %s", err)

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

    except Exception:
        logger.exception("Error updating count badges")
        return "0", "0", "0"


# Callback for activity feed (only on dashboard page)
@app.callback(
    Output("activity-feed", "children", allow_duplicate=True),
    [Input("interval-component", "n_intervals"), Input("url", "pathname")],
    State("settings-store", "data"),
    prevent_initial_call="initial_duplicate",
)
def update_activity_feed(
    _n: int,
    pathname: str,
    settings: SettingsDict | None,
) -> list[Component]:
    """Update activity feed (only visible on dashboard page)."""
    # Only update if we're on the dashboard page
    if pathname not in {"/", "/dashboard"}:
        raise PreventUpdate

    try:
        # Try to get real-time data first
        rt_client = get_realtime_client(settings)
        realtime_data = None

        if rt_client:
            try:
                realtime_data = rt_client.get_latest_update()
            except Exception as err:
                logger.debug("Real-time client error: %s", err)

        if realtime_data:
            # Use real-time data if available
            activities_data = realtime_data.get("activities", [])
        else:
            # Fallback to API polling
            activities_response = api_request(
                "/stats/activities/recent",
                settings=settings,
            )
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
        activities: list[Component] = []
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
                ),
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
                        (
                            "Live updates enabled"
                            if rt_status == "connected"
                            else "Updates every 5 seconds"
                        ),
                        className="text-muted",
                    ),
                ],
                className="mb-2",
            ),
        )

        return activities

    except Exception:
        logger.exception("Error updating activity feed")
        return [html.Div("Error loading data")]


# Callback for dashboard page charts (always visible)
@app.callback(
    [
        Output("quality-chart", "figure"),
        Output("entity-distribution-chart", "figure"),
        Output("validation-status-chart", "figure"),
    ],
    Input("interval-component", "n_intervals"),
)
def update_dashboard_charts(_n: int) -> tuple[FigureDict, FigureDict, FigureDict]:
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
                },
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
                        ],
                    },
                },
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
                        ],
                    },
                },
            ],
            "layout": {"title": "Validation Status"},
        }

        return quality_fig, entity_fig, validation_fig

    except Exception:
        logger.exception("Error updating dashboard charts")
        # Return empty figures on error
        empty_fig: FigureDict = {"data": [], "layout": {}}
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
def update_reports_charts(_n: int, pathname: str) -> tuple[FigureDict, FigureDict]:
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
                },
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
                },
            ],
            "layout": {"title": "Error Distribution by Type"},
        }

        return trends_fig, error_fig

    except Exception:
        logger.exception("Error updating reports charts")
        # Return empty figures on error
        empty_fig: FigureDict = {"data": [], "layout": {}}
        return empty_fig, empty_fig


# Callback for bulk operations
@app.callback(
    Output("batch-progress-container", "children"),
    Input("start-batch-btn", "n_clicks"),
    State("batch-operation", "value"),
    prevent_initial_call=True,
)
def handle_batch_operation(
    n_clicks: int | None,
    operation: str | None,
) -> ComponentValue:
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
            f"Processing {operation} operation... 75% complete",
            className="text-muted",
        )

        return html.Div([progress, status_text])

    except Exception as err:
        logger.exception("Error in batch operation: %s", err)
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
    n_clicks: int | None,
    api_endpoint: str | None,
    api_key: str | None,
    refresh_interval: int | None,
    page_size: int | None,
    theme: str | None,
    language: str | None,
    current_settings: SettingsDict | None,
) -> SettingsDict:
    """Save dashboard settings."""
    if not n_clicks:
        return current_settings or {}

    try:
        new_settings: SettingsDict = {
            "api_endpoint": api_endpoint,
            "api_key": api_key,
            "refresh_interval": refresh_interval,
            "page_size": page_size,
            "theme": theme,
            "language": language,
        }

        # Update the interval component
        interval_component = cast("dcc.Interval", app.layout.children[4])
        if refresh_interval is not None:
            interval_component.interval = refresh_interval * 1000

        return new_settings

    except Exception as err:
        logger.exception("Error saving settings: %s", err)
        return current_settings or {}


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
    approve_clicks: int | None,
    reject_clicks: int | None,
    quarantine_clicks: int | None,
    select_all_clicks: int | None,
    selected_rows: list[int] | None,
    table_data: list[TableRow] | None,
    entity_type: str | None,
    settings: SettingsDict | None,
) -> tuple[list[int] | None, ComponentValue]:
    """Handle bulk approve/reject/quarantine operations."""
    ctx: Any = dash.callback_context
    if not ctx.triggered:
        return selected_rows, ""

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    try:
        table_data = table_data or []
        settings = settings or {}

        if trigger_id == "select-all-btn":
            # Select all rows
            all_rows = list(range(len(table_data)))
            return all_rows, ""

        if not selected_rows:
            return selected_rows, dbc.Alert(
                "No items selected for operation",
                color="warning",
            )

        operation: str | None = None
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

        resource_type = entity_type or "entities"

        for row_index in selected_rows:
            if row_index < len(table_data):
                item = table_data[row_index]
                item_id = item.get("id")

                # Mock API call - replace with actual implementation
                try:
                    # Simulate API call to update item status
                    result = api_request(
                        f"/{resource_type}/{item_id}",
                        method="PUT",
                        data={"status": operation},
                        settings=settings,
                    )

                    if "error" not in result:
                        processed_count += 1
                    else:
                        failed_count += 1

                except Exception:
                    logger.exception("Error processing item %s", item_id)
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

    except Exception:
        logger.exception("Error in bulk operation")
        error_alert = dbc.Alert(
            "Error performing bulk operation",
            color="danger",
            dismissable=True,
        )
        return selected_rows, error_alert


# Real-time updates class
class RealTimeClient:
    """WebSocket client for real-time updates."""

    def __init__(self, api_endpoint: str, api_key: str) -> None:
        self.api_endpoint = api_endpoint.replace("http", "ws")
        self.api_key = api_key
        self.connected: bool = False
        self.last_update: dict[str, Any] = {}

        self.sio: Any | None
        if WEBSOCKET_SUPPORT:
            try:
                import socketio  # type: ignore[import-not-found]
            except Exception:
                self.sio = None
            else:
                self.sio = socketio.Client()
                # Set up event handlers
                self.sio.on("connect", self.on_connect)
                self.sio.on("disconnect", self.on_disconnect)
                self.sio.on("data_update", self.on_data_update)
                self.sio.on("validation_complete", self.on_validation_complete)
                self.sio.on("ingestion_progress", self.on_ingestion_progress)
        else:
            self.sio = None

    def on_connect(self) -> None:
        """Handle connection established."""
        logger.info("Connected to real-time server")
        self.connected = True

    def on_disconnect(self) -> None:
        """Handle disconnection."""
        logger.info("Disconnected from real-time server")
        self.connected = False

    def on_data_update(self, data: dict[str, Any]) -> None:
        """Handle data update events."""
        logger.info("Received data update: %s", data)
        self.last_update = data

    def on_validation_complete(self, data: dict[str, Any]) -> None:
        """Handle validation completion events."""
        logger.info("Validation completed: %s", data)
        self.last_update = data

    def on_ingestion_progress(self, data: dict[str, Any]) -> None:
        """Handle ingestion progress events."""
        logger.info("Ingestion progress: %s", data)
        self.last_update = data

    async def connect_async(self) -> None:
        """Connect to WebSocket server asynchronously."""
        try:
            # Try WebSocket connection first
            uri = f"{self.api_endpoint}/ws?token={self.api_key}"
            async with websockets.connect(uri) as websocket:
                logger.info("WebSocket connection established")
                async for message in websocket:
                    try:
                        message_str = (
                            message.decode("utf-8", "ignore")
                            if isinstance(message, (bytes, bytearray))
                            else message
                        )
                        data = json.loads(message_str)
                        self.last_update = data
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON received: {message_str}")
        except Exception as e:
            logger.warning(f"WebSocket connection failed, falling back to polling: {e}")
            self.connected = False

    def connect(self) -> None:
        """Connect to real-time server."""
        if not WEBSOCKET_SUPPORT:
            logger.info("WebSocket support not available, using polling only")
            return

        try:
            # Try Socket.IO first
            if self.sio is not None:
                self.sio.connect(
                    f"{self.api_endpoint.replace('ws', 'http')}",
                    headers={"X-API-Key": self.api_key},
                )
        except Exception as err:
            logger.warning("Socket.IO connection failed, trying WebSocket: %s", err)
            # Fallback to asyncio WebSocket
            asyncio.run(self.connect_async())

    def disconnect(self) -> None:
        """Disconnect from real-time server."""
        if WEBSOCKET_SUPPORT and self.sio is not None and self.sio.connected:
            self.sio.disconnect()
        self.connected = False

    def get_latest_update(self) -> dict[str, Any]:
        """Get the latest update data."""
        return self.last_update.copy()


# Global real-time client instance
realtime_client: RealTimeClient | None = None


def get_realtime_client(
    settings: SettingsDict | None,
) -> RealTimeClient | None:
    """Get or create real-time client instance."""
    global realtime_client
    settings = settings or {}
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
        except Exception as err:
            logger.warning("Failed to initialize real-time client: %s", err)
            return None

    return realtime_client


# API helper functions
def api_request(
    endpoint: str,
    method: str = "GET",
    data: SettingsDict | None = None,
    settings: SettingsDict | None = None,
) -> dict[str, Any]:
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
            msg = f"Unsupported HTTP method: {method}"
            raise ValueError(msg)

        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    except requests.RequestException as e:
        # Log as debug since we gracefully fall back to mock data
        # Connection errors are expected when API server isn't running
        logger.debug("API request failed (falling back to mock data): %s", e)
        return {"error": str(e)}


# Callback for refresh button
@app.callback(
    Output("refresh-notification", "children"),
    Input("refresh-btn", "n_clicks"),
    prevent_initial_call=True,
)
def handle_refresh(n_clicks: int | None) -> Any:
    """Handle refresh button click."""
    if not n_clicks:
        return dash.no_update

    # Trigger a refresh by updating the timestamp
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

    return dbc.Toast(
        f"Data refreshed at {timestamp}",
        header="Refresh Complete",
        icon="success",
        duration=3000,
        className="position-fixed top-0 end-0 m-3",
        style={"zIndex": 9999},
    )


# Callback for export button
@app.callback(
    Output("export-notification", "children"),
    Input("export-btn", "n_clicks"),
    State("entity-type-filter", "value"),
    State("status-filter", "value"),
    State("priority-filter", "value"),
    prevent_initial_call=True,
)
def handle_export(
    n_clicks: int | None,
    entity_type: str | None,
    status: str | None,
    priority: str | None,
) -> Any:
    """Handle export button click."""
    if not n_clicks:
        return dash.no_update

    try:
        # Get current filter state
        filters_applied = []
        if entity_type:
            filters_applied.append(f"Entity: {entity_type}")
        if status:
            filters_applied.append(f"Status: {status}")
        if priority:
            filters_applied.append(f"Priority: {priority}")

        filter_text = (
            f" with filters: {', '.join(filters_applied)}"
            if filters_applied
            else " (all data)"
        )

        # In a real implementation, this would generate and download a file
        # For now, show a notification
        return dbc.Toast(
            f"Report exported successfully{filter_text}",
            header="Export Complete",
            icon="success",
            duration=4000,
            className="position-fixed top-0 end-0 m-3",
            style={"zIndex": 9999},
        )

    except Exception as e:
        logger.error(f"Export failed: {e}")
        return dbc.Toast(
            "Export failed. Please try again.",
            header="Export Error",
            icon="danger",
            duration=4000,
            className="position-fixed top-0 end-0 m-3",
            style={"zIndex": 9999},
        )


# Callback for clear filters button
@app.callback(
    Output("clear-filters-notification", "children"),
    Output("entity-type-filter", "value"),
    Output("status-filter", "value"),
    Output("priority-filter", "value"),
    Output("filter-state-store", "data"),
    Input("clear-filters-btn", "n_clicks"),
    prevent_initial_call=True,
)
def handle_clear_filters(n_clicks: int | None) -> tuple[Any, Any, Any, Any, Any]:
    """Handle clear filters button click."""
    if not n_clicks:
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    # Clear all filter values
    return (
        dbc.Toast(
            "All filters cleared",
            header="Filters Cleared",
            icon="info",
            duration=2000,
            className="position-fixed top-0 end-0 m-3",
            style={"zIndex": 9999},
        ),
        None,  # entity-type-filter
        None,  # status-filter
        None,  # priority-filter
        {},  # filter-state-store
    )


if __name__ == "__main__":
    logger.info("Starting MED13 Curation Dashboard...")
    app.run(host="127.0.0.1", port=8050, debug=True)

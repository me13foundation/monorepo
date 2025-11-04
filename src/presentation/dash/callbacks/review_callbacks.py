"""Callbacks for the enhanced review queue."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, cast

import requests
from dash import ALL, Dash, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
from dash.development.base_component import Component

from src.presentation.dash.components.curation.clinical_card import (
    create_clinical_card_grid,
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
from src.presentation.dash.types import (
    CuratedRecordDetail,
    ReviewQueueItem,
    SettingsState,
    coerce_curated_detail,
    coerce_queue_items,
)

logger = logging.getLogger(__name__)


def register_callbacks(app: Dash) -> None:
    """Register curator queue callbacks."""

    @app.callback(
        Output("clinical-card-container", "children"),
        Output("review-table", "data"),
        Output("selected-count", "children"),
        Input("interval-component", "n_intervals"),
        Input("apply-filters-btn", "n_clicks"),
        State("entity-type-filter", "value"),
        State("status-filter", "value"),
        State("priority-filter", "value"),
        State("settings-store", "data"),
        State("url", "pathname"),
    )
    def refresh_queue(
        _interval: int,
        _apply_clicks: Optional[int],
        entity_type: Optional[str],
        status: Optional[str],
        priority: Optional[str],
        settings_data: Optional[Mapping[str, Any]],
        pathname: str,
    ) -> Tuple[Component, List[Dict[str, Any]], str]:
        if pathname != "/review":
            raise PreventUpdate

        settings = _coerce_settings(settings_data)
        query_params = _build_query_filters(entity_type, status, priority)
        queue_items = _fetch_queue_items(settings, query_params)

        card_children = create_clinical_card_grid(queue_items)
        table_rows = _queue_items_to_table(queue_items)
        counter_label = f"{len(queue_items)} items loaded"

        return card_children, table_rows, counter_label

    @app.callback(
        Output("clinical-card-container", "style"),
        Output("table-view-container", "style"),
        Output("card-view-btn", "active"),
        Output("table-view-btn", "active"),
        Input("card-view-btn", "n_clicks"),
        Input("table-view-btn", "n_clicks"),
    )
    def toggle_view(
        card_clicks: Optional[int], table_clicks: Optional[int]
    ) -> Tuple[Dict[str, str], Dict[str, str], bool, bool]:
        triggered = getattr(callback_context, "triggered_id", None)

        if triggered == "table-view-btn":
            return (
                {"display": "none"},
                {"display": "block"},
                False,
                True,
            )

        # Default to card view
        return (
            {"display": "block"},
            {"display": "none"},
            True,
            False,
        )

    @app.callback(
        Output("curation-detail-store", "data"),
        Input(
            {"type": "review-card-open", "entityId": ALL, "entityType": ALL}, "n_clicks"
        ),
        Input("review-table", "active_cell"),
        State({"type": "review-card-open", "entityId": ALL, "entityType": ALL}, "id"),
        State("review-table", "data"),
        State("settings-store", "data"),
        prevent_initial_call=True,
    )
    def load_curated_detail(
        card_clicks: Sequence[Optional[int]],
        active_cell: Optional[Mapping[str, Any]],
        card_ids: Sequence[Mapping[str, str]],
        table_data: Optional[Sequence[Mapping[str, Any]]],
        settings_data: Optional[Mapping[str, Any]],
    ) -> Optional[Mapping[str, Any]]:
        del card_clicks  # n_clicks values only signal which ID triggered

        triggered = getattr(callback_context, "triggered_id", None)
        if triggered is None:
            raise PreventUpdate

        settings = _coerce_settings(settings_data)

        if isinstance(triggered, dict):
            entity_type = triggered.get("entityType")
            entity_id = triggered.get("entityId")
        elif triggered == "review-table" and active_cell and table_data:
            row_index = active_cell.get("row")
            if row_index is None:
                raise PreventUpdate
            try:
                row = table_data[int(row_index)]
            except (IndexError, ValueError):
                raise PreventUpdate from None
            entity_type = cast(Optional[str], row.get("_entity_type"))
            entity_id = cast(Optional[str], row.get("_entity_id"))
        else:
            raise PreventUpdate

        if not entity_type or not entity_id:
            raise PreventUpdate

        detail = _fetch_curated_detail(settings, entity_type, entity_id)
        if detail is None:
            raise PreventUpdate

        return cast(Mapping[str, Any], detail)

    @app.callback(
        Output("curation-summary-panel", "children"),
        Output("curation-evidence-panel", "children"),
        Output("curation-conflict-panel", "children"),
        Output("curation-audit-panel", "children"),
        Output("curation-detail-container", "style"),
        Input("curation-detail-store", "data"),
    )
    def update_detail_panels(
        detail_data: Optional[Mapping[str, Any]],
    ) -> Tuple[Component, Component, Component, Component, Dict[str, str]]:
        if detail_data is None:
            placeholder = render_clinical_viewer(None, ())
            evidence_placeholder = render_evidence_matrix(())
            conflict_placeholder = render_conflict_panel(())
            audit_placeholder = render_audit_summary(None)
            return (
                placeholder,
                evidence_placeholder,
                conflict_placeholder,
                audit_placeholder,
                {"display": "none"},
            )

        try:
            typed_detail = coerce_curated_detail(detail_data)
        except ValueError as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to coerce curated detail: %s", exc)
            placeholder = render_clinical_viewer(None, ())
            return (
                placeholder,
                render_evidence_matrix(()),
                render_conflict_panel(()),
                render_audit_summary(None),
                {"display": "none"},
            )

        summary_component = render_clinical_viewer(
            typed_detail["variant"],
            typed_detail.get("phenotypes", ()),
        )
        evidence_component = render_evidence_matrix(
            typed_detail.get("evidence", ()),
        )
        conflict_component = render_conflict_panel(
            typed_detail.get("conflicts", ()),
        )
        audit_component = render_audit_summary(typed_detail.get("audit"))

        return (
            summary_component,
            evidence_component,
            conflict_component,
            audit_component,
            {"display": "block"},
        )


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #


def _coerce_settings(settings: Optional[Mapping[str, Any]]) -> SettingsState:
    if not settings:
        raise PreventUpdate
    return cast(SettingsState, settings)


def _build_query_filters(
    entity_type: Optional[str],
    status: Optional[str],
    priority: Optional[str],
) -> Dict[str, str]:
    filters: Dict[str, str] = {}
    if entity_type:
        filters["entity_type"] = entity_type
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    return filters


def _fetch_queue_items(
    settings: SettingsState, filters: Mapping[str, str]
) -> List[ReviewQueueItem]:
    url = f"{settings['api_endpoint'].rstrip('/')}/curation/queue"
    headers = _build_headers(settings)

    try:
        response = requests.get(url, headers=headers, params=filters, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.error("Failed to fetch review queue: %s", exc)
        return []

    if not isinstance(data, Sequence):
        logger.warning("Unexpected queue payload: %s", data)
        return []

    try:
        return coerce_queue_items(cast(Sequence[Mapping[str, object]], data))
    except ValueError as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to coerce queue items: %s", exc)
        return []


def _fetch_curated_detail(
    settings: SettingsState, entity_type: str, entity_id: str
) -> Optional[CuratedRecordDetail]:
    url = f"{settings['api_endpoint'].rstrip('/')}/curation/{entity_type}/{entity_id}"
    headers = _build_headers(settings)

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 404:
            logger.info("Curated detail not found for %s %s", entity_type, entity_id)
            return None
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logger.error("Failed to fetch curator detail: %s", exc)
        return None

    try:
        return coerce_curated_detail(cast(Mapping[str, object], payload))
    except ValueError as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to coerce curated detail payload: %s", exc)
        return None


def _queue_items_to_table(items: Sequence[ReviewQueueItem]) -> List[Dict[str, Any]]:
    table_rows: List[Dict[str, Any]] = []
    for item in items:
        table_rows.append(
            {
                "select": "",
                "id": item["id"],
                "entity": f"{item['entity_type'].title()} • {item['entity_id']}",
                "status": item.get("status", "pending").title(),
                "quality_score": item.get("quality_score"),
                "issues": item.get("issues", 0),
                "last_updated": item.get("last_updated", "—"),
                "actions": "View",
                "_entity_type": item["entity_type"],
                "_entity_id": item["entity_id"],
            }
        )
    return table_rows


def _build_headers(settings: SettingsState) -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    api_key = settings.get("api_key")
    if api_key:
        headers["X-API-Key"] = api_key
    return headers

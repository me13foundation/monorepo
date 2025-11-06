"""
Audit summary component for curator detail view.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import dash_bootstrap_components as dbc

from dash import html

if TYPE_CHECKING:  # pragma: no cover - typing only
    from dash.development.base_component import Component
    from src.presentation.dash.types import AuditInfo


def render_audit_summary(audit: AuditInfo | None) -> Component:
    """
    Render audit metadata for the selected entity.
    """
    if audit is None:
        return cast(
            "Component",
            dbc.Alert(
                [
                    html.I(className="fas fa-clipboard-list me-2"),
                    "No audit history recorded for this entity yet.",
                ],
                color="light",
                className="mb-0",
            ),
        )

    metadata_items = html.Div(
        [
            _meta_row("Last Updated", audit.get("last_updated_at") or "Unknown"),
            _meta_row("Updated By", audit.get("last_updated_by") or "Unassigned"),
            _meta_row(
                "Annotations Logged",
                str(audit.get("total_annotations", 0) or 0),
            ),
        ],
        className="mb-3",
    )

    pending_actions = audit.get("pending_actions", ())
    action_badges = (
        dbc.Stack(
            [
                dbc.Badge(action, color="info", className="me-2 mb-2")
                for action in pending_actions
            ],
            direction="horizontal",
            gap=2,
            className="flex-wrap",
        )
        if pending_actions
        else html.Small("No outstanding actions.", className="text-muted")
    )

    return cast(
        "Component",
        html.Div(
            [
                html.H5("Audit Timeline"),
                metadata_items,
                html.Div(
                    [
                        html.Small("Pending Actions", className="text-muted d-block"),
                        action_badges,
                    ],
                ),
            ],
        ),
    )


def _meta_row(label: str, value: str) -> Component:
    return cast(
        "Component",
        html.Div(
            [
                html.Span(label, className="text-muted d-block small"),
                html.Span(value, className="fw-semibold"),
            ],
            className="mb-2",
        ),
    )


__all__ = ["render_audit_summary"]

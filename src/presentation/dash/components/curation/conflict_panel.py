"""
Conflict panel component for curator detail view.
"""

from __future__ import annotations

from typing import Sequence, cast

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component

from src.presentation.dash.types import ConflictSummary


def render_conflict_panel(conflicts: Sequence[ConflictSummary]) -> Component:
    """
    Render a panel summarising detected conflicts.
    """
    if not conflicts:
        return cast(
            Component,
            dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    "No conflicts detected across linked evidence.",
                ],
                color="success",
                className="mb-0",
            ),
        )

    conflict_items = [
        dbc.ListGroupItem(
            [
                html.Div(
                    [
                        _severity_badge(conflict["severity"]),
                        html.Span(
                            conflict.get("kind", "conflict").replace("_", " ").title(),
                            className="ms-2 fw-semibold",
                        ),
                    ],
                    className="d-flex align-items-center mb-2",
                ),
                html.P(conflict["message"], className="mb-1"),
                html.Small(
                    f"Evidence IDs: {', '.join(str(eid) for eid in conflict.get('evidence_ids', ())) or 'N/A'}",
                    className="text-muted",
                ),
            ]
        )
        for conflict in conflicts
    ]

    return cast(
        Component,
        html.Div(
            [
                html.H5("Conflict Overview"),
                dbc.ListGroup(conflict_items, flush=True),
            ]
        ),
    )


def _severity_badge(severity: str) -> Component:
    normalized = severity.lower()
    color_map = {
        "high": "danger",
        "medium": "warning",
        "low": "secondary",
    }
    color = color_map.get(normalized, "info")
    label = normalized.title()
    return cast(Component, dbc.Badge(label, color=color))


__all__ = ["render_conflict_panel"]

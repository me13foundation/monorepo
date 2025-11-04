"""
Evidence comparison component for curator detail view.
"""

from __future__ import annotations

from typing import Sequence, cast

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component

from src.presentation.dash.types import EvidenceSnapshot


def render_evidence_matrix(evidence: Sequence[EvidenceSnapshot]) -> Component:
    """
    Render a comparison matrix style table summarising evidence records.
    """
    if not evidence:
        return cast(
            Component,
            dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "No evidence has been linked to this variant yet.",
                ],
                color="secondary",
                className="mb-0",
            ),
        )

    header = html.Thead(
        html.Tr(
            [
                html.Th("Evidence ID"),
                html.Th("Level"),
                html.Th("Type"),
                html.Th("Confidence"),
                html.Th("Clinical Significance"),
                html.Th("Summary"),
            ]
        )
    )

    rows = []
    for item in evidence:
        description = item.get("summary") or item.get("description", "")
        truncated = description if len(description) <= 160 else f"{description[:157]}…"

        rows.append(
            html.Tr(
                [
                    html.Td(item.get("id", "—")),
                    html.Td(_format_level(item["evidence_level"])),
                    html.Td(item["evidence_type"].replace("_", " ").title()),
                    html.Td(_format_confidence(item.get("confidence_score"))),
                    html.Td(item.get("clinical_significance", "—")),
                    html.Td(truncated or "—"),
                ]
            )
        )

    table = dbc.Table(
        [header, html.Tbody(rows)],
        bordered=True,
        hover=True,
        responsive=True,
        className="mb-0",
    )

    return cast(
        Component,
        html.Div([html.H5("Evidence Comparison"), table]),
    )


def _format_confidence(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.2f}"
    if isinstance(value, str):
        try:
            return f"{float(value):.2f}"
        except ValueError:
            return "—"
    return "—"


def _format_level(level: str) -> str:
    normalized = level.replace("_", " ").title()
    return normalized


__all__ = ["render_evidence_matrix"]

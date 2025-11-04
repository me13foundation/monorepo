"""
Curator queue card components.

These cards provide at-a-glance clinical context and action buttons for
queued review items.
"""

from __future__ import annotations

from typing import Optional, Sequence, cast

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component

from src.presentation.dash.types import ReviewQueueItem


def create_enhanced_filters() -> Component:
    """Return advanced filter controls for the review queue."""
    return cast(
        Component,
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Clinical Significance"),
                                        dbc.Checklist(
                                            options=[
                                                {
                                                    "label": "Pathogenic",
                                                    "value": "pathogenic",
                                                },
                                                {
                                                    "label": "Likely Pathogenic",
                                                    "value": "likely_pathogenic",
                                                },
                                                {
                                                    "label": "Uncertain",
                                                    "value": "uncertain_significance",
                                                },
                                                {
                                                    "label": "Likely Benign",
                                                    "value": "likely_benign",
                                                },
                                                {"label": "Benign", "value": "benign"},
                                            ],
                                            value=["pathogenic", "likely_pathogenic"],
                                            id="clinical-significance-filter",
                                            inline=True,
                                        ),
                                    ],
                                    width=12,
                                ),
                            ],
                            className="gy-2",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Minimum Confidence"),
                                        dbc.Input(
                                            id="confidence-threshold",
                                            type="number",
                                            min=0.0,
                                            max=1.0,
                                            step=0.1,
                                            value=0.5,
                                            placeholder="0.0 - 1.0",
                                        ),
                                    ],
                                    width=4,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Phenotype"),
                                        dbc.Input(
                                            id="phenotype-filter",
                                            type="text",
                                            placeholder="e.g. Intellectual disability",
                                        ),
                                    ],
                                    width=8,
                                ),
                            ],
                            className="gy-2",
                        ),
                    ],
                    title="Advanced Clinical Filters",
                )
            ],
            always_open=False,
            flush=True,
            className="mb-4",
        ),
    )


def create_clinical_card_grid(items: Sequence[ReviewQueueItem]) -> Component:
    """
    Render a responsive grid of review cards.

    Args:
        items: typed queue items returned from the API
    """
    if not items:
        return cast(
            Component,
            dbc.Alert(
                [
                    html.I(className="fas fa-search me-2"),
                    "No review items match the current filters.",
                ],
                color="secondary",
                className="mb-0",
            ),
        )

    columns: list[Component] = []
    for item in items:
        columns.append(
            cast(Component, dbc.Col(_create_single_card(item), width=12, xl=6))
        )

    return cast(Component, dbc.Row(columns, className="g-3", id="clinical-card-row"))


def _create_single_card(item: ReviewQueueItem) -> Component:
    """Create a single review card for a queue item."""
    priority_badge = _priority_badge(item["priority"])
    issues_badge: Component = cast(
        Component,
        dbc.Badge(
            f'{item["issues"]} issues',
            color="warning",
            className="ms-2",
        ),
    )
    quality_badge = _quality_badge(item.get("quality_score"))

    header = dbc.CardHeader(
        dbc.Row(
            [
                dbc.Col(
                    html.Span(
                        [
                            html.I(className="fas fa-dna me-2"),
                            item["entity_id"],
                        ],
                        className="fw-bold",
                    ),
                    width=7,
                ),
                dbc.Col(
                    html.Div(
                        [priority_badge, issues_badge, quality_badge],
                        className="d-flex justify-content-end flex-wrap gap-2",
                    ),
                    width=5,
                ),
            ],
            className="g-0 align-items-center",
        )
    )

    body = dbc.CardBody(
        [
            html.Div(
                [
                    html.Span(
                        [
                            html.I(className="fas fa-notes-medical me-2 text-muted"),
                            item.get("summary", "Clinical summary pending."),
                        ],
                        className="d-block mb-2",
                    ),
                    html.Small(
                        f"Status: {item.get('status', 'pending').title()}",
                        className="text-muted",
                    ),
                    html.Br(),
                    html.Small(
                        f"Updated: {item.get('last_updated', 'unknown')}",
                        className="text-muted",
                    ),
                ]
            )
        ]
    )

    footer = dbc.CardFooter(
        dbc.Button(
            "Open Clinical Detail",
            id={
                "type": "review-card-open",
                "entityId": item["entity_id"],
                "entityType": item["entity_type"],
            },
            color="primary",
            size="sm",
            n_clicks=0,
            className="w-100",
        )
    )

    return cast(
        Component, dbc.Card([header, body, footer], className="h-100 shadow-sm")
    )


def _priority_badge(priority: str) -> Component:
    normalized = priority.lower()
    color_map = {
        "high": "danger",
        "medium": "info",
        "low": "secondary",
    }
    color = color_map.get(normalized, "primary")
    return cast(Component, dbc.Badge(priority.title(), color=color))


def _quality_badge(quality_score: object) -> Component:
    if quality_score is None:
        return cast(
            Component, dbc.Badge("No Q/S", color="light", className="text-muted")
        )

    score: Optional[float]
    if isinstance(quality_score, (int, float)) and not isinstance(quality_score, bool):
        score = float(quality_score)
    elif isinstance(quality_score, str):
        try:
            score = float(quality_score)
        except ValueError:
            score = None
    else:
        score = None

    if score is None:
        return cast(
            Component, dbc.Badge("Q/S ?", color="light", className="text-muted")
        )

    if score >= 0.8:
        color = "success"
    elif score >= 0.6:
        color = "warning"
    else:
        color = "danger"
    return cast(Component, dbc.Badge(f"Q/S {score:.2f}", color=color, className="ms-2"))


def get_clinical_significance_color(significance: str) -> str:
    """Map clinical significance classifications to badge colors."""
    normalized = significance.lower()
    palette = {
        "pathogenic": "#c0392b",
        "likely_pathogenic": "#e74c3c",
        "uncertain_significance": "#f1c40f",
        "likely_benign": "#27ae60",
        "benign": "#1abc9c",
    }
    return palette.get(normalized, "#7f8c8d")


__all__ = [
    "create_clinical_card_grid",
    "create_enhanced_filters",
    "get_clinical_significance_color",
]

"""
Bulk Resolution Component for MED13 Curation Dashboard.

Provides tools for resolving multiple conflicts and curation tasks simultaneously.
"""

from typing import Any

import dash_bootstrap_components as dbc

from dash import dcc, html
from src.presentation.dash.components.curation.clinical_card import (
    get_clinical_significance_color,
)

# UI constants
PREVIEW_MAX_ITEMS: int = 5
PREVIEW_DESC_MAX_LEN: int = 60


def create_bulk_resolution_panel(
    conflicts: list[dict[str, Any]],
    variants: list[dict[str, Any]],
) -> dbc.Card:
    """
    Create a bulk resolution panel for handling multiple conflicts and variants.

    Args:
        conflicts: List of conflict dictionaries
        variants: List of variant dictionaries pending review

    Returns:
        Bootstrap Card with bulk resolution interface
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5("Bulk Resolution Tools", className="mb-0"),
                    dbc.Badge(
                        f"{len(conflicts)} Conflicts + {len(variants)} Variants",
                        color="info",
                        className="ms-2",
                    ),
                ],
            ),
            dbc.CardBody(
                [
                    # Quick actions section
                    dbc.Row(
                        [
                            dbc.Col(create_quick_actions(conflicts, variants), width=6),
                            dbc.Col(create_batch_processing(conflicts), width=6),
                        ],
                        className="mb-4",
                    ),
                    # Selection and preview
                    dbc.Row(
                        [dbc.Col(create_bulk_selection(conflicts, variants), width=12)],
                        className="mb-4",
                    ),
                    # Preview and confirmation
                    html.Div(
                        id="bulk-preview-container",
                        children=create_bulk_preview([]),
                    ),
                    # Action summary
                    dbc.Row([dbc.Col(create_action_summary(), width=12)]),
                ],
            ),
        ],
    )


def create_quick_actions(
    conflicts: list[dict[str, Any]],
    variants: list[dict[str, Any]],
) -> dbc.Card:
    """Create quick action buttons for common bulk operations."""
    conflict_count = len(conflicts)
    variant_count = len(variants)

    return dbc.Card(
        [
            dbc.CardHeader("Quick Actions"),
            dbc.CardBody(
                [
                    html.H6("Conflict Resolution", className="mb-3"),
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [
                                    html.I(className="fas fa-check-circle me-2"),
                                    f"Accept Highest Evidence ({conflict_count})",
                                ],
                                color="success",
                                size="sm",
                                id="bulk-accept-highest",
                                disabled=conflict_count == 0,
                                className="mb-1",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-balance-scale me-2"),
                                    f"Accept ClinVar Priority ({conflict_count})",
                                ],
                                color="primary",
                                size="sm",
                                id="bulk-accept-clinvar",
                                disabled=conflict_count == 0,
                                className="mb-1",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-flag me-2"),
                                    f"Flag All for Review ({conflict_count})",
                                ],
                                color="warning",
                                size="sm",
                                id="bulk-flag-all",
                                disabled=conflict_count == 0,
                                className="mb-1",
                            ),
                        ],
                        vertical=True,
                        className="w-100 mb-3",
                    ),
                    html.Hr(),
                    html.H6("Variant Triage", className="mb-3"),
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [
                                    html.I(className="fas fa-thumbs-up me-2"),
                                    f"Bulk Approve ({variant_count})",
                                ],
                                color="success",
                                size="sm",
                                id="bulk-approve-variants",
                                disabled=variant_count == 0,
                                className="mb-1",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-clock me-2"),
                                    f"Defer All ({variant_count})",
                                ],
                                color="secondary",
                                size="sm",
                                id="bulk-defer-variants",
                                disabled=variant_count == 0,
                                className="mb-1",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-user-md me-2"),
                                    f"Assign to Expert ({variant_count})",
                                ],
                                color="info",
                                size="sm",
                                id="bulk-assign-expert",
                                disabled=variant_count == 0,
                                className="mb-1",
                            ),
                        ],
                        vertical=True,
                        className="w-100",
                    ),
                ],
            ),
        ],
    )


def create_batch_processing(conflicts: list[dict[str, Any]]) -> dbc.Card:
    """Create batch processing interface with filters and rules."""
    return dbc.Card(
        [
            dbc.CardHeader("Batch Processing"),
            dbc.CardBody(
                [
                    html.H6("Processing Rules", className="mb-3"),
                    # Conflict severity filter
                    dbc.Label("Apply to conflicts with severity:"),
                    dcc.Checklist(
                        options=[  # type: ignore
                            {"label": " High priority conflicts", "value": "high"},
                            {"label": " Medium priority conflicts", "value": "medium"},
                            {"label": " Low priority conflicts", "value": "low"},
                        ],
                        value=["high", "medium"],
                        id="batch-severity-filter",
                        className="mb-3",
                    ),
                    # Evidence level filter
                    dbc.Label("Minimum evidence level:"),
                    dcc.Dropdown(
                        options=[  # type: ignore
                            {"label": "Any", "value": "any"},
                            {"label": "Limited or higher", "value": "limited"},
                            {"label": "Supporting or higher", "value": "supporting"},
                            {"label": "Strong or higher", "value": "strong"},
                            {"label": "Definitive only", "value": "definitive"},
                        ],
                        value="supporting",
                        id="batch-evidence-filter",
                        clearable=False,
                        className="mb-3",
                    ),
                    # Confidence threshold
                    dbc.Label("Minimum confidence score:"),
                    dcc.Slider(
                        id="batch-confidence-threshold",
                        min=0,
                        max=1,
                        step=0.1,
                        value=0.7,
                        marks={0: "0", 0.5: "0.5", 1: "1"},
                        className="mb-3",
                    ),
                    # Action selection
                    dbc.Label("Apply action:"),
                    dcc.Dropdown(
                        options=[  # type: ignore
                            {
                                "label": "Accept highest evidence level",
                                "value": "accept_highest",
                            },
                            {
                                "label": "Accept ClinVar classification",
                                "value": "accept_clinvar",
                            },
                            {"label": "Flag for expert review", "value": "flag_expert"},
                            {"label": "Defer decision", "value": "defer"},
                        ],
                        value="accept_highest",
                        id="batch-action",
                        clearable=False,
                        className="mb-3",
                    ),
                    # Batch size control
                    dbc.Label("Process in batches of:"),
                    dcc.Slider(
                        id="batch-size",
                        min=5,
                        max=50,
                        step=5,
                        value=25,
                        marks={5: "5", 25: "25", 50: "50"},
                        className="mb-3",
                    ),
                    # Execute button
                    dbc.Button(
                        [
                            html.I(className="fas fa-play me-2"),
                            "Execute Batch Processing",
                        ],
                        color="primary",
                        id="execute-batch",
                        className="w-100",
                    ),
                    # Progress indicator (hidden initially)
                    html.Div(
                        id="batch-progress-container",
                        style={"display": "none"},
                        children=[
                            dbc.Progress(
                                id="batch-progress",
                                value=0,
                                className="mb-2",
                            ),
                            html.Small(id="batch-status", className="text-muted"),
                        ],
                    ),
                ],
            ),
        ],
    )


def create_bulk_selection(
    conflicts: list[dict[str, Any]],
    variants: list[dict[str, Any]],
) -> html.Div:
    """Create bulk selection interface with checkboxes."""
    return html.Div(
        [
            html.H6("Selective Processing", className="mb-3"),
            dbc.Tabs(
                [
                    dbc.Tab(
                        [create_conflict_selection_table(conflicts)],
                        label=f"Conflicts ({len(conflicts)})",
                        tab_id="conflicts-tab",
                    ),
                    dbc.Tab(
                        [create_variant_selection_table(variants)],
                        label=f"Variants ({len(variants)})",
                        tab_id="variants-tab",
                    ),
                ],
                id="bulk-selection-tabs",
            ),
            html.Div(
                [
                    dbc.Button(
                        [
                            html.I(className="fas fa-eye me-2"),
                            "Preview Selected Actions",
                        ],
                        color="info",
                        id="preview-selected",
                        className="me-2",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-times me-2"), "Clear Selection"],
                        color="secondary",
                        id="clear-selection",
                    ),
                ],
                className="mt-3",
            ),
        ],
    )


def create_conflict_selection_table(conflicts: list[dict[str, Any]]) -> dbc.Table:
    """Create a table for selecting individual conflicts."""
    if not conflicts:
        return dbc.Table(
            html.Tbody(html.Tr(html.Td("No conflicts available", colSpan=4))),
        )

    headers = [
        html.Th("Select"),
        html.Th("Conflict Type"),
        html.Th("Severity"),
        html.Th("Description"),
        html.Th("Actions"),
    ]

    rows = []
    for i, conflict in enumerate(conflicts):
        severity_color = {"high": "danger", "medium": "warning", "low": "info"}.get(
            conflict["severity"],
            "secondary",
        )

        row = html.Tr(
            [
                html.Td(
                    html.Span(
                        "☐",
                        id=f"conflict-select-{i}",
                        className="text-primary fw-bold",
                    ),
                ),
                html.Td(conflict["type"].replace("_", " ").title()),
                html.Td(dbc.Badge(conflict["severity"].title(), color=severity_color)),
                html.Td(
                    html.Small(
                        (
                            conflict["description"][:PREVIEW_DESC_MAX_LEN] + "..."
                            if len(conflict["description"]) > PREVIEW_DESC_MAX_LEN
                            else conflict["description"]
                        ),
                    ),
                ),
                html.Td(
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                "Resolve",
                                size="sm",
                                color="outline-primary",
                                id=f"resolve-conflict-{i}",
                            ),
                            dbc.Button(
                                "Skip",
                                size="sm",
                                color="outline-secondary",
                                id=f"skip-conflict-{i}",
                            ),
                        ],
                        size="sm",
                    ),
                ),
            ],
        )
        rows.append(row)

    return dbc.Table(
        [html.Thead(html.Tr(headers)), html.Tbody(rows)],
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
    )


def create_variant_selection_table(variants: list[dict[str, Any]]) -> dbc.Table:
    """Create a table for selecting individual variants."""
    if not variants:
        return dbc.Table(
            html.Tbody(html.Tr(html.Td("No variants available", colSpan=5))),
        )

    headers = [
        html.Th("Select"),
        html.Th("Variant ID"),
        html.Th("Gene"),
        html.Th("Significance"),
        html.Th("Confidence"),
    ]

    rows = []
    for i, variant in enumerate(variants):
        significance_color = get_clinical_significance_color(
            variant.get("clinical_significance", "not_provided"),
        )

        row = html.Tr(
            [
                html.Td(
                    html.Span(
                        "☐",
                        id=f"variant-select-{i}",
                        className="text-primary fw-bold",
                    ),
                ),
                html.Td(variant.get("variant_id", "Unknown")),
                html.Td(variant.get("gene_symbol", "Unknown")),
                html.Td(
                    dbc.Badge(
                        variant.get("clinical_significance", "Unknown")
                        .replace("_", " ")
                        .title(),
                        style={"backgroundColor": significance_color, "color": "white"},
                    ),
                ),
                html.Td(f"{variant.get('confidence_score', 0):.1f}"),
            ],
        )
        rows.append(row)

    return dbc.Table(
        [html.Thead(html.Tr(headers)), html.Tbody(rows)],
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
    )


def create_bulk_preview(selected_items: list[dict[str, Any]]) -> dbc.Card:
    """Create a preview of bulk actions before execution."""
    if not selected_items:
        return dbc.Card(style={"display": "none"})

    # Group actions by type
    action_groups: dict[str, list[dict[str, Any]]] = {}
    for item in selected_items:
        action = item.get("action", "unknown")
        if action not in action_groups:
            action_groups[action] = []
        action_groups[action].append(item)

    preview_sections = []
    for action, items in action_groups.items():
        section = dbc.Card(
            [
                dbc.CardHeader(f"{action.title()} ({len(items)} items)"),
                dbc.CardBody(
                    [
                        html.Ul(
                            [
                                html.Li(
                                    f"{item.get('id', 'Unknown')} - {item.get('description', '')[:50]}...",
                                )
                                for item in items[
                                    :PREVIEW_MAX_ITEMS
                                ]  # Show max N items
                            ],
                        ),
                        html.Small(
                            (
                                f"And {len(items) - PREVIEW_MAX_ITEMS} more..."
                                if len(items) > PREVIEW_MAX_ITEMS
                                else ""
                            ),
                            className="text-muted",
                        ),
                    ],
                ),
            ],
            className="mb-2",
        )
        preview_sections.append(section)

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H6("Action Preview", className="mb-0"),
                    dbc.Badge(
                        f"{len(selected_items)} items selected",
                        color="info",
                        className="ms-2",
                    ),
                ],
            ),
            dbc.CardBody(
                [
                    html.Div(preview_sections),
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-check me-2"),
                                            "Confirm & Execute",
                                        ],
                                        color="success",
                                        id="confirm-bulk-action",
                                        className="w-100",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-edit me-2"),
                                            "Modify Actions",
                                        ],
                                        color="warning",
                                        id="modify-bulk-action",
                                        className="w-100",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def create_action_summary() -> dbc.Card:
    """Create a summary of bulk action results."""
    return dbc.Card(
        [
            dbc.CardHeader("Action Summary"),
            dbc.CardBody(
                [
                    html.Div(
                        id="bulk-action-results",
                        children=[
                            html.P(
                                "No bulk actions executed yet.",
                                className="text-muted mb-0",
                            ),
                        ],
                    ),
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H4(
                                                "0",
                                                id="actions-completed",
                                                className="text-success",
                                            ),
                                            html.Small(
                                                "Completed",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="text-center",
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H4(
                                                "0",
                                                id="actions-pending",
                                                className="text-warning",
                                            ),
                                            html.Small(
                                                "Pending",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="text-center",
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H4(
                                                "0",
                                                id="actions-failed",
                                                className="text-danger",
                                            ),
                                            html.Small(
                                                "Failed",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="text-center",
                                    ),
                                ],
                                width=4,
                            ),
                        ],
                        className="mt-3",
                    ),
                ],
            ),
        ],
    )


def create_bulk_workflow_templates() -> dbc.Card:
    """Create workflow templates for common bulk operations."""
    return dbc.Card(
        [
            dbc.CardHeader("Workflow Templates"),
            dbc.CardBody(
                [
                    html.H6("Quick Workflows", className="mb-3"),
                    # Template buttons
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-magic me-2"),
                                            "Daily Triage",
                                        ],
                                        color="outline-primary",
                                        size="sm",
                                        id="template-daily-triage",
                                        className="w-100 mb-2",
                                    ),
                                    html.Small(
                                        "Process routine variants with high confidence",
                                        className="text-muted d-block",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(
                                                className="fas fa-exclamation-triangle me-2",
                                            ),
                                            "Conflict Resolution",
                                        ],
                                        color="outline-warning",
                                        size="sm",
                                        id="template-conflict-resolution",
                                        className="w-100 mb-2",
                                    ),
                                    html.Small(
                                        "Focus on evidence conflicts",
                                        className="text-muted d-block",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-user-md me-2"),
                                            "Expert Review Prep",
                                        ],
                                        color="outline-info",
                                        size="sm",
                                        id="template-expert-review",
                                        className="w-100 mb-2",
                                    ),
                                    html.Small(
                                        "Prepare complex cases for experts",
                                        className="text-muted d-block",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-archive me-2"),
                                            "Batch Archival",
                                        ],
                                        color="outline-secondary",
                                        size="sm",
                                        id="template-archival",
                                        className="w-100 mb-2",
                                    ),
                                    html.Small(
                                        "Archive completed low-priority items",
                                        className="text-muted d-block",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                    ),
                    html.Hr(),
                    # Custom template creation
                    html.H6("Create Custom Template", className="mb-2"),
                    dbc.Input(
                        placeholder="Template name...",
                        id="custom-template-name",
                        className="mb-2",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Save Current Settings"],
                        color="outline-success",
                        size="sm",
                        id="save-custom-template",
                        className="w-100",
                    ),
                ],
            ),
        ],
    )


__all__ = [
    "create_action_summary",
    "create_batch_processing",
    "create_bulk_preview",
    "create_bulk_resolution_panel",
    "create_bulk_selection",
    "create_bulk_workflow_templates",
    "create_quick_actions",
]

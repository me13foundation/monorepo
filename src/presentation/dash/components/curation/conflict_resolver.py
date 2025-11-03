"""
Conflict Resolution Component for MED13 Curation Dashboard.

Provides interactive tools for resolving evidence conflicts and clinical disagreements.
"""

from typing import Any, Dict, List

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_conflict_resolution_panel(variant_data: Dict[str, Any]) -> dbc.Card:
    """
    Create a conflict resolution panel for handling evidence disagreements.

    Args:
        variant_data: Dictionary containing variant information with conflicts

    Returns:
        Bootstrap Card containing conflict resolution interface
    """
    evidence_records = variant_data.get("evidence_records", [])
    conflicts: List[Dict[str, Any]] = _detect_evidence_conflicts(evidence_records)

    if not conflicts:
        return dbc.Card(
            [
                dbc.CardHeader("Conflict Resolution"),
                dbc.CardBody(
                    [
                        dbc.Alert(
                            [
                                html.I(className="fas fa-check-circle me-2"),
                                "No evidence conflicts detected for this variant.",
                            ],
                            color="success",
                        )
                    ]
                ),
            ]
        )

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5("Conflict Resolution", className="mb-0"),
                    dbc.Badge(
                        f"{len(conflicts)} Conflicts", color="warning", className="ms-2"
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    # Conflict timeline
                    _create_conflict_timeline(conflicts),
                    # Individual conflict resolvers
                    _create_conflict_resolvers(conflicts),
                    # Resolution actions
                    _create_resolution_actions(),
                ]
            ),
        ]
    )


def _detect_evidence_conflicts(
    evidence_records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Detect conflicts in evidence records with detailed conflict information.

    Returns list of conflict objects with resolution options.
    """
    conflicts: List[Dict[str, Any]] = []

    if not evidence_records or len(evidence_records) < 2:
        return conflicts

    # Clinical significance conflict
    significances: Dict[str, List[int]] = {}
    for i, ev in enumerate(evidence_records):
        sig = ev.get("clinical_significance")
        if sig:
            if sig not in significances:
                significances[sig] = []
            significances[sig].append(i)

    if len(significances) > 1:
        conflict_options = []
        for sig, indices in significances.items():
            conflict_options.append(
                {
                    "value": f"sig_{sig}",
                    "label": f"Accept {sig.title()} (from {len(indices)} source{'s' if len(indices) > 1 else ''})",
                    "significance": sig,
                    "count": len(indices),
                    "indices": indices,
                }
            )

        conflicts.append(
            {
                "id": "clinical_significance",
                "type": "clinical_significance",
                "title": "Clinical Significance Conflict",
                "description": f'Multiple significance classifications detected: {", ".join(significances.keys())}',
                "severity": "high",
                "options": conflict_options,
                "recommended": _get_recommended_significance(
                    significances, evidence_records
                ),
            }
        )

    # Evidence level conflict
    levels: Dict[str, List[int]] = {}
    for i, ev in enumerate(evidence_records):
        level = ev.get("evidence_level")
        if level:
            if level not in levels:
                levels[level] = []
            levels[level].append(i)

    if len(levels) > 1:
        level_hierarchy = {"limited": 1, "supporting": 2, "strong": 3, "definitive": 4}
        sorted_levels = sorted(
            levels.keys(), key=lambda x: level_hierarchy.get(x, 0), reverse=True
        )

        conflict_options = []
        for level in sorted_levels:
            indices = levels[level]
            conflict_options.append(
                {
                    "value": f"level_{level}",
                    "label": f"Accept {level.title()} (from {len(indices)} source{'s' if len(indices) > 1 else ''})",
                    "level": level,
                    "count": len(indices),
                    "indices": indices,
                }
            )

        conflicts.append(
            {
                "id": "evidence_level",
                "type": "evidence_level",
                "title": "Evidence Level Conflict",
                "description": f'Conflicting evidence strength levels: {", ".join(sorted_levels)}',
                "severity": "medium",
                "options": conflict_options,
                "recommended": sorted_levels[0],  # Highest level
            }
        )

    return conflicts


def _get_recommended_significance(
    significances: Dict[str, List[int]], evidence_records: List[Dict[str, Any]]
) -> str:
    """Get recommended clinical significance based on evidence strength."""
    # Simple logic: prefer significance from highest evidence level
    level_hierarchy = {"limited": 1, "supporting": 2, "strong": 3, "definitive": 4}

    best_sig = None
    best_level = 0

    for sig, indices in significances.items():
        for idx in indices:
            level = evidence_records[idx].get("evidence_level", "limited")
            level_value = level_hierarchy.get(level, 0)
            if level_value > best_level:
                best_level = level_value
                best_sig = sig

    return best_sig or list(significances.keys())[0]


def _create_conflict_timeline(conflicts: List[Dict[str, Any]]) -> html.Div:
    """Create a visual timeline of conflicts and their detection."""
    if not conflicts:
        return html.Div()

    timeline_items = []
    for i, conflict in enumerate(conflicts):
        severity_color = {"high": "danger", "medium": "warning", "low": "info"}.get(
            conflict["severity"], "info"
        )

        timeline_items.append(
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Badge(
                                conflict["severity"].title(),
                                color=severity_color,
                                className="me-2",
                            ),
                            html.Strong(conflict["title"]),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [html.Small(conflict["description"], className="text-muted")],
                        width=8,
                    ),
                ],
                className="mb-2",
            )
        )

    return html.Div(
        [
            html.H6("Conflict Timeline", className="mb-3"),
            html.Div(timeline_items, className="border-start border-3 ps-3"),
        ],
        className="mb-4",
    )


def _create_conflict_resolvers(conflicts: List[Dict[str, Any]]) -> html.Div:
    """Create individual conflict resolution interfaces."""
    resolvers = []

    for conflict in conflicts:
        resolver = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H6(conflict["title"], className="mb-0"),
                        dbc.Badge(
                            f"Recommended: {conflict.get('recommended', 'Review').title()}",
                            color="info",
                            className="ms-2",
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        html.P(conflict["description"], className="text-muted mb-3"),
                        # Resolution options
                        dbc.Label("Resolution Options:"),
                        dbc.RadioItems(
                            id=f"conflict-resolution-{conflict['id']}",
                            options=conflict["options"],
                            value=None,
                            className="mb-3",
                        ),
                        # Rationale input
                        dbc.Label("Rationale for Resolution:"),
                        dbc.Textarea(
                            id=f"conflict-rationale-{conflict['id']}",
                            placeholder="Explain why this resolution was chosen...",
                            className="mb-3",
                        ),
                        # Confidence override
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Override Confidence Score:"),
                                        dcc.Slider(
                                            id=f"conflict-confidence-{conflict['id']}",
                                            min=0,
                                            max=1,
                                            step=0.1,
                                            value=0.5,
                                            marks={0: "0", 0.5: "0.5", 1: "1"},
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "Apply Resolution",
                                            id=f"apply-resolution-{conflict['id']}",
                                            color="primary",
                                            className="mt-4",
                                        )
                                    ],
                                    width=6,
                                ),
                            ]
                        ),
                    ]
                ),
            ],
            className="mb-3",
        )

        resolvers.append(resolver)

    return html.Div(resolvers)


def _create_resolution_actions() -> dbc.Card:
    """Create overall resolution actions panel."""
    return dbc.Card(
        [
            dbc.CardHeader(html.H6("Resolution Actions", className="mb-0")),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-save me-2"),
                                            "Save All Resolutions",
                                        ],
                                        id="save-all-resolutions",
                                        color="success",
                                        className="w-100",
                                    )
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-undo me-2"),
                                            "Reset All",
                                        ],
                                        id="reset-resolutions",
                                        color="secondary",
                                        className="w-100",
                                    )
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
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-flag me-2"),
                                            "Flag for Expert Review",
                                        ],
                                        id="flag-for-review",
                                        color="warning",
                                        className="w-100",
                                    )
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-envelope me-2"),
                                            "Request Additional Evidence",
                                        ],
                                        id="request-evidence",
                                        color="info",
                                        className="w-100",
                                    )
                                ],
                                width=6,
                            ),
                        ]
                    ),
                ]
            ),
        ]
    )


def create_quick_conflict_resolver(conflict: Dict[str, Any]) -> dbc.Modal:
    """
    Create a quick modal resolver for individual conflicts.

    Args:
        conflict: Conflict dictionary with resolution options

    Returns:
        Bootstrap Modal for quick conflict resolution
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(
                [
                    html.H5(conflict["title"], className="mb-0"),
                    dbc.Badge(
                        conflict["severity"].title(),
                        color={
                            "high": "danger",
                            "medium": "warning",
                            "low": "info",
                        }.get(conflict["severity"], "info"),
                        className="ms-2",
                    ),
                ]
            ),
            dbc.ModalBody(
                [
                    html.P(conflict["description"], className="mb-3"),
                    dbc.Label("Quick Resolution:"),
                    dbc.RadioItems(
                        id=f"quick-resolution-{conflict['id']}",
                        options=conflict["options"],
                        value=conflict.get("recommended", ""),
                        className="mb-3",
                    ),
                    dbc.Label("Brief Rationale:"),
                    dbc.Textarea(
                        id=f"quick-rationale-{conflict['id']}",
                        placeholder="Why this resolution?",
                        rows=2,
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id=f"cancel-resolution-{conflict['id']}",
                        color="secondary",
                    ),
                    dbc.Button(
                        "Resolve",
                        id=f"confirm-resolution-{conflict['id']}",
                        color="primary",
                    ),
                ]
            ),
        ],
        id=f"conflict-modal-{conflict['id']}",
        size="lg",
    )


__all__ = [
    "create_conflict_resolution_panel",
    "create_quick_conflict_resolver",
    "_detect_evidence_conflicts",
    "_create_conflict_timeline",
    "_create_conflict_resolvers",
]

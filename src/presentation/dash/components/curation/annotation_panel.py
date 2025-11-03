"""
Annotation Panel Component for MED13 Curation Dashboard.

Provides expert annotation interface with audit trail and rationale capture.
"""

from typing import Any, Dict, List, Optional

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_annotation_panel(
    variant_data: Dict[str, Any],
    existing_annotations: Optional[List[Dict[str, Any]]] = None,
) -> dbc.Card:
    """
    Create an annotation panel for expert comments and curation rationale.

    Args:
        variant_data: Dictionary containing variant information
        existing_annotations: List of existing annotations for this variant

    Returns:
        Bootstrap Card containing annotation interface
    """
    existing_annotations = existing_annotations or []

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5("Expert Annotations", className="mb-0"),
                    dbc.Badge(
                        f"{len(existing_annotations)} Notes",
                        color="info",
                        className="ms-2",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    # Quick annotation form
                    _create_quick_annotation_form(variant_data),
                    # Annotation history
                    _create_annotation_history(existing_annotations),
                    # Audit trail
                    _create_audit_trail(variant_data),
                ]
            ),
        ]
    )


def _create_quick_annotation_form(variant_data: Dict[str, Any]) -> html.Div:
    """Create a quick annotation form for adding expert notes."""
    variant_id = variant_data.get("variant_id", "Unknown")

    return html.Div(
        [
            html.H6("Add Annotation", className="mb-3"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Annotation Type:"),
                            dcc.Dropdown(
                                id="annotation-type",
                                options=[  # type: ignore
                                    {
                                        "label": "Clinical Rationale",
                                        "value": "clinical_rationale",
                                    },
                                    {
                                        "label": "Evidence Assessment",
                                        "value": "evidence_assessment",
                                    },
                                    {
                                        "label": "Literature Review",
                                        "value": "literature_review",
                                    },
                                    {
                                        "label": "Methodological Note",
                                        "value": "methodological_note",
                                    },
                                    {
                                        "label": "General Comment",
                                        "value": "general_comment",
                                    },
                                ],
                                value="clinical_rationale",
                                clearable=False,
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Clinical Priority:"),
                            dcc.Dropdown(
                                id="annotation-priority",
                                options=[  # type: ignore
                                    {"label": "High", "value": "high"},
                                    {"label": "Medium", "value": "medium"},
                                    {"label": "Low", "value": "low"},
                                ],
                                value="medium",
                                clearable=False,
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Confidence Override:"),
                            dcc.Slider(
                                id="annotation-confidence",
                                min=0,
                                max=1,
                                step=0.1,
                                value=variant_data.get("confidence_score", 0.5),
                                marks={0: "0", 0.5: "0.5", 1: "1"},
                            ),
                        ],
                        width=4,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Label("Annotation Text:"),
            dbc.Textarea(
                id="annotation-text",
                placeholder=f"Add your expert insights for variant {variant_id}...",
                rows=4,
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Supporting References:"),
                            dbc.Textarea(
                                id="annotation-references",
                                placeholder="PubMed IDs, DOI links, or other references...",
                                rows=2,
                            ),
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                [
                                    html.I(className="fas fa-plus me-2"),
                                    "Add Annotation",
                                ],
                                id="add-annotation-btn",
                                color="primary",
                                className="w-100 mt-4",
                            )
                        ],
                        width=4,
                    ),
                ],
                className="mb-4",
            ),
            html.Hr(),
        ]
    )


def _create_annotation_history(annotations: List[Dict[str, Any]]) -> html.Div:
    """Create the annotation history timeline."""
    if not annotations:
        return html.Div(
            [
                html.H6("Annotation History", className="mb-3"),
                html.P(
                    "No annotations yet. Add the first expert note above.",
                    className="text-muted",
                ),
            ]
        )

    # Sort annotations by timestamp (most recent first)
    sorted_annotations = sorted(
        annotations, key=lambda x: x.get("timestamp", ""), reverse=True
    )

    annotation_cards = []
    for annotation in sorted_annotations:
        annotation_type = annotation.get("type", "general_comment")
        priority = annotation.get("priority", "medium")

        # Color coding for annotation types
        type_colors = {
            "clinical_rationale": "primary",
            "evidence_assessment": "success",
            "literature_review": "info",
            "methodological_note": "warning",
            "general_comment": "secondary",
        }

        # Priority indicators
        priority_icons = {
            "high": "fas fa-exclamation-triangle text-danger",
            "medium": "fas fa-info-circle text-warning",
            "low": "fas fa-check-circle text-success",
        }

        annotation_card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Badge(
                                            annotation_type.replace("_", " ").title(),
                                            color=type_colors.get(
                                                annotation_type, "secondary"
                                            ),
                                            className="me-2",
                                        ),
                                        html.I(
                                            className=f"{priority_icons.get(priority, 'fas fa-comment')} me-2"
                                        ),
                                        html.Small(
                                            f"Priority: {priority.title()}",
                                            className="text-muted",
                                        ),
                                    ],
                                    width=8,
                                ),
                                dbc.Col(
                                    [
                                        html.Small(
                                            annotation.get("timestamp", "Unknown time"),
                                            className="text-muted text-end d-block",
                                        ),
                                        html.Small(
                                            f"by {annotation.get('author', 'Unknown')}",
                                            className="text-muted text-end d-block",
                                        ),
                                    ],
                                    width=4,
                                ),
                            ]
                        )
                    ]
                ),
                dbc.CardBody(
                    [
                        html.P(annotation.get("text", ""), className="mb-2"),
                        (
                            html.Div(
                                [
                                    html.Small("References: ", className="text-muted"),
                                    html.Small(
                                        annotation.get("references", "None"),
                                        className="font-monospace",
                                    ),
                                ]
                            )
                            if annotation.get("references")
                            else None
                        ),
                        (
                            html.Div(
                                [
                                    html.Small(
                                        "Confidence Override: ", className="text-muted"
                                    ),
                                    html.Small(
                                        f"{annotation.get('confidence_override', 'N/A')}"
                                    ),
                                ]
                            )
                            if annotation.get("confidence_override")
                            else None
                        ),
                    ]
                ),
            ],
            className="mb-3",
        )

        annotation_cards.append(annotation_card)

    return html.Div(
        [html.H6("Annotation History", className="mb-3"), html.Div(annotation_cards)]
    )


def _create_audit_trail(variant_data: Dict[str, Any]) -> html.Div:
    """Create an audit trail showing all curation actions."""
    # Mock audit trail - in real implementation, this would come from database
    audit_events: List[Dict[str, Any]] = [
        {
            "timestamp": "2024-01-15 14:30:00",
            "action": "Variant Reviewed",
            "user": "Dr. Smith",
            "details": "Initial clinical review completed",
            "status_change": "pending → approved",
        },
        {
            "timestamp": "2024-01-15 10:15:00",
            "action": "Evidence Added",
            "user": "System",
            "details": "ClinVar evidence automatically imported",
            "status_change": None,
        },
        {
            "timestamp": "2024-01-14 16:45:00",
            "action": "Variant Created",
            "user": "Data Pipeline",
            "details": "Variant imported from ClinVar database",
            "status_change": None,
        },
    ]

    audit_items = []
    for event in audit_events:
        status_badge = None
        if event["status_change"]:
            status_badge = dbc.Badge(
                event["status_change"], color="info", className="ms-2"
            )

        audit_item = dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Strong(event["action"]),
                                html.Small(
                                    f" by {event['user']}", className="text-muted ms-2"
                                ),
                                status_badge,
                            ]
                        ),
                        html.P(event["details"], className="text-muted mb-0 small"),
                    ],
                    width=10,
                ),
                dbc.Col(
                    [
                        html.Small(
                            event["timestamp"], className="text-muted text-end d-block"
                        )
                    ],
                    width=2,
                ),
            ],
            className="mb-2 pb-2 border-bottom",
        )

        audit_items.append(audit_item)

    return html.Div(
        [
            html.H6("Audit Trail", className="mb-3"),
            html.Div(audit_items, className="audit-timeline"),
        ]
    )


def create_quick_decision_rationale() -> dbc.Modal:
    """
    Create a quick modal for adding rationale to curation decisions.

    Returns:
        Bootstrap Modal for quick decision rationale
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(html.H5("Decision Rationale")),
            dbc.ModalBody(
                [
                    html.P(
                        "Please provide a brief rationale for your curation decision:",
                        className="mb-3",
                    ),
                    dbc.Label("Decision:"),
                    dcc.Dropdown(
                        id="decision-type",
                        options=[  # type: ignore
                            {"label": "Approved", "value": "approved"},
                            {"label": "Rejected", "value": "rejected"},
                            {"label": "Send for Review", "value": "review"},
                            {"label": "Quarantine", "value": "quarantine"},
                        ],
                        placeholder="Select decision...",
                        className="mb-3",
                    ),
                    dbc.Label("Rationale:"),
                    dbc.Textarea(
                        id="decision-rationale",
                        placeholder="Explain the clinical reasoning behind this decision...",
                        rows=4,
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Confidence in Decision:"),
                                    dcc.Slider(
                                        id="decision-confidence",
                                        min=0,
                                        max=1,
                                        step=0.1,
                                        value=0.8,
                                        marks={0: "0", 0.5: "0.5", 1: "1"},
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Follow-up Required:"),
                                    dbc.Checklist(
                                        id="follow-up-needed",
                                        options=[
                                            {
                                                "label": "Request additional evidence",
                                                "value": "additional_evidence",
                                            },
                                            {
                                                "label": "Clinical correlation needed",
                                                "value": "clinical_correlation",
                                            },
                                            {
                                                "label": "Expert consultation required",
                                                "value": "expert_consultation",
                                            },
                                        ],
                                        value=[],
                                        className="mt-2",
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancel", id="cancel-decision", color="secondary"),
                    dbc.Button("Save Decision", id="save-decision", color="primary"),
                ]
            ),
        ],
        id="decision-rationale-modal",
        size="lg",
    )


def create_annotation_templates() -> Dict[str, str]:
    """Return common annotation templates for quick use."""
    return {
        "pathogenic_confirmation": "This variant meets ACMG/AMP criteria for pathogenicity based on {evidence_type} evidence showing {phenotype} association with {confidence}% confidence.",
        "benign_reclassification": "Reclassified as benign following review of population data showing {allele_frequency} frequency in {population}, exceeding threshold for benign classification.",
        "uncertain_maintained": "Maintained uncertain significance classification due to conflicting evidence: {pathogenic_evidence} vs {benign_evidence}. Additional functional studies recommended.",
        "evidence_conflict_resolved": "Resolved evidence conflict by prioritizing {preferred_source} over {alternative_source} due to {rationale} with {confidence}% confidence in resolution.",
        "literature_update": "Updated classification based on recent literature ({pubmed_id}) reporting {finding} in {cohort_size} patients with {phenotype}.",
    }


__all__ = [
    "create_annotation_panel",
    "create_quick_decision_rationale",
    "create_annotation_templates",
    "_create_quick_annotation_form",
    "_create_annotation_history",
    "_create_audit_trail",
]

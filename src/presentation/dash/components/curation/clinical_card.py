"""
Clinical Review Card Component for MED13 Curation Dashboard.

Provides clinical-context-rich cards for variant curation instead of basic tables.
"""

from typing import Any, Dict, List

from dash import html, dcc
import dash_bootstrap_components as dbc

from src.domain.entities.variant import ClinicalSignificance


def get_clinical_significance_color(significance: str) -> str:
    """Get color for clinical significance badges."""
    colors = {
        ClinicalSignificance.PATHOGENIC: "#C0392B",  # Red
        ClinicalSignificance.LIKELY_PATHOGENIC: "#E74C3C",  # Red-orange
        ClinicalSignificance.UNCERTAIN_SIGNIFICANCE: "#F1C40F",  # Gold
        ClinicalSignificance.LIKELY_BENIGN: "#27AE60",  # Green
        ClinicalSignificance.BENIGN: "#1ABC9C",  # Teal
        ClinicalSignificance.CONFLICTING: "#E67E22",  # Orange
        ClinicalSignificance.NOT_PROVIDED: "#95A5A6",  # Gray
    }
    return colors.get(significance, "#95A5A6")


def get_evidence_level_color(level: str) -> str:
    """Get color for evidence level badges."""
    colors = {
        "definitive": "#2C3E50",  # Dark blue
        "strong": "#34495E",  # Blue
        "supporting": "#7F8C8D",  # Gray
        "limited": "#BDC3C7",  # Light gray
    }
    return colors.get(level, "#BDC3C7")


def create_clinical_review_card(variant_data: Dict[str, Any]) -> dbc.Card:
    """
    Create a clinical review card displaying variant information in clinical context.

    Args:
        variant_data: Dictionary containing variant information including:
            - id: Variant ID
            - variant_id: HGVS notation
            - gene_symbol: Associated gene
            - chromosome: Chromosome location
            - position: Genomic position
            - clinical_significance: Clinical significance
            - confidence_score: Confidence score (0-1)
            - evidence_count: Number of evidence records
            - evidence_levels: List of evidence levels
            - phenotypes: List of associated phenotypes
            - quality_score: Validation quality score
            - issues: Number of validation issues

    Returns:
        Bootstrap Card component with clinical information
    """
    variant_id = variant_data.get("variant_id", "Unknown")
    gene_symbol = variant_data.get("gene_symbol", "Unknown")
    clinical_sig = variant_data.get("clinical_significance", "not_provided")
    confidence = variant_data.get("confidence_score", 0.0)
    evidence_count = variant_data.get("evidence_count", 0)
    evidence_levels = variant_data.get("evidence_levels", [])
    phenotypes = variant_data.get("phenotypes", [])
    quality_score = variant_data.get("quality_score", 0.0)
    issues = variant_data.get("issues", 0)

    # Create clinical significance badge
    sig_color = get_clinical_significance_color(clinical_sig)
    sig_badge = dbc.Badge(
        clinical_sig.replace("_", " ").title(),
        style={"backgroundColor": sig_color, "color": "white"},
        className="me-2",
    )

    # Create evidence level badges
    evidence_badges = []
    for level in evidence_levels[:3]:  # Show max 3 evidence levels
        level_color = get_evidence_level_color(level)
        evidence_badges.append(
            dbc.Badge(
                level.title(),
                style={"backgroundColor": level_color, "color": "white"},
                className="me-1 mb-1",
                size="sm",
            )
        )

    # Create phenotype badges (show max 2)
    phenotype_badges = []
    for phenotype in phenotypes[:2]:
        phenotype_badges.append(
            dbc.Badge(
                phenotype.get("name", "Unknown")[:20],
                color="secondary",
                className="me-1 mb-1",
                size="sm",
            )
        )
    if len(phenotypes) > 2:
        phenotype_badges.append(
            dbc.Badge(
                f"+{len(phenotypes) - 2} more",
                color="light",
                text_color="dark",
                className="me-1 mb-1",
                size="sm",
            )
        )

    # Confidence meter
    confidence_percentage = int(confidence * 100)
    confidence_color = (
        "success" if confidence > 0.7 else "warning" if confidence > 0.4 else "danger"
    )

    # Quality indicator
    quality_color = (
        "success"
        if quality_score > 0.8
        else "warning"
        if quality_score > 0.6
        else "danger"
    )
    quality_icon = "✓" if issues == 0 else f"{issues}⚠"

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.Strong(f"Variant: {variant_id}"),
                                    html.Span(" • ", style={"color": "#6c757d"}),
                                    html.Span(f"Gene: {gene_symbol}"),
                                ],
                                className="mb-1",
                            ),
                            sig_badge,
                            html.Small(
                                f"chr{variant_data.get('chromosome', '?')}:{variant_data.get('position', '?')}",
                                className="text-muted ms-2",
                            ),
                        ],
                        className="d-flex justify-content-between align-items-start",
                    )
                ]
            ),
            dbc.CardBody(
                [
                    # Clinical Summary Row
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Small(
                                                "Evidence",
                                                className="text-muted d-block",
                                            ),
                                            html.Strong(f"{evidence_count} records"),
                                            html.Div(evidence_badges, className="mt-1"),
                                        ]
                                    )
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Small(
                                                "Confidence",
                                                className="text-muted d-block",
                                            ),
                                            dbc.Progress(
                                                value=confidence_percentage,
                                                color=confidence_color,
                                                className="mb-1",
                                                style={"height": "8px"},
                                            ),
                                            html.Small(
                                                f"{confidence_percentage}%",
                                                className="text-muted",
                                            ),
                                        ]
                                    )
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Small(
                                                "Quality",
                                                className="text-muted d-block",
                                            ),
                                            html.Strong(
                                                quality_icon,
                                                style={
                                                    "color": {
                                                        "success": "#28a745",
                                                        "warning": "#ffc107",
                                                        "danger": "#dc3545",
                                                    }.get(quality_color)
                                                },
                                            ),
                                        ]
                                    )
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-2",
                    ),
                    # Phenotypes Section
                    (
                        html.Div(
                            [
                                html.Small(
                                    "Associated Phenotypes:",
                                    className="text-muted d-block mb-1",
                                ),
                                (
                                    html.Div(phenotype_badges)
                                    if phenotype_badges
                                    else html.Small(
                                        "None specified", className="text-muted"
                                    )
                                ),
                            ],
                            className="mb-2",
                        )
                        if phenotypes
                        else None
                    ),
                ]
            ),
            dbc.CardFooter(
                [
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                html.I(className="fas fa-check"),
                                id={
                                    "type": "approve-btn",
                                    "index": variant_data.get("id", 0),
                                },
                                color="success",
                                size="sm",
                                title="Approve this variant",
                            ),
                            dbc.Button(
                                html.I(className="fas fa-question"),
                                id={
                                    "type": "review-btn",
                                    "index": variant_data.get("id", 0),
                                },
                                color="warning",
                                size="sm",
                                title="Send for additional review",
                            ),
                            dbc.Button(
                                html.I(className="fas fa-eye"),
                                id={
                                    "type": "details-btn",
                                    "index": variant_data.get("id", 0),
                                },
                                color="info",
                                size="sm",
                                title="View detailed clinical information",
                            ),
                            dbc.Button(
                                html.I(className="fas fa-times"),
                                id={
                                    "type": "reject-btn",
                                    "index": variant_data.get("id", 0),
                                },
                                color="danger",
                                size="sm",
                                title="Reject this variant",
                            ),
                        ],
                        size="sm",
                    )
                ]
            ),
        ],
        className="mb-3 clinical-review-card",
        style={"cursor": "pointer"},
    )


def create_clinical_card_grid(variant_data_list: List[Dict[str, Any]]) -> html.Div:
    """
    Create a responsive grid of clinical review cards.

    Args:
        variant_data_list: List of variant data dictionaries

    Returns:
        Div containing responsive card grid
    """
    if not variant_data_list:
        return html.Div(
            [
                dbc.Alert(
                    [
                        html.H5("No Variants to Review", className="alert-heading"),
                        html.P(
                            "All variants in the current queue have been processed.",
                            className="mb-0",
                        ),
                    ],
                    color="info",
                    className="text-center",
                )
            ]
        )

    cards = [create_clinical_review_card(variant) for variant in variant_data_list]

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(card, width=12, lg=6, xl=4, className="mb-3")
                    for card in cards
                ]
            )
        ],
        className="clinical-card-grid",
    )


def create_enhanced_filters() -> dbc.Accordion:
    """
    Create enhanced clinical filters for the review queue.

    Returns:
        Accordion with clinical filtering options
    """
    return dbc.Accordion(
        [
            dbc.AccordionItem(
                [
                    # Clinical Significance Filter
                    dbc.Label("Clinical Significance"),
                    dcc.Checklist(
                        id="clinical-significance-filter",
                        options=[  # type: ignore
                            {
                                "label": "Pathogenic",
                                "value": ClinicalSignificance.PATHOGENIC,
                            },
                            {
                                "label": "Likely Pathogenic",
                                "value": ClinicalSignificance.LIKELY_PATHOGENIC,
                            },
                            {
                                "label": "Uncertain Significance",
                                "value": ClinicalSignificance.UNCERTAIN_SIGNIFICANCE,
                            },
                            {
                                "label": "Likely Benign",
                                "value": ClinicalSignificance.LIKELY_BENIGN,
                            },
                            {"label": "Benign", "value": ClinicalSignificance.BENIGN},
                            {
                                "label": "Conflicting",
                                "value": ClinicalSignificance.CONFLICTING,
                            },
                        ],
                        value=[
                            ClinicalSignificance.PATHOGENIC,
                            ClinicalSignificance.LIKELY_PATHOGENIC,
                        ],
                        labelStyle={"display": "block", "marginBottom": "5px"},
                    ),
                    html.Hr(),
                    # Evidence Level Filter
                    dbc.Label("Minimum Evidence Level"),
                    dcc.Slider(
                        id="evidence-level-filter",
                        min=0,
                        max=3,
                        step=1,
                        value=1,
                        marks={
                            0: "Limited",
                            1: "Supporting",
                            2: "Strong",
                            3: "Definitive",
                        },
                    ),
                    html.Hr(),
                    # Confidence Threshold
                    dbc.Label("Minimum Confidence Score"),
                    dcc.Slider(
                        id="confidence-filter",
                        min=0,
                        max=1,
                        step=0.1,
                        value=0.5,
                        marks={0: "0%", 0.5: "50%", 1: "100%"},
                    ),
                    html.Hr(),
                    # Quality Score Filter
                    dbc.Label("Minimum Quality Score"),
                    dcc.Slider(
                        id="quality-score-filter",
                        min=0,
                        max=1,
                        step=0.1,
                        value=0.7,
                        marks={0: "0%", 0.7: "70%", 1: "100%"},
                    ),
                ],
                title="Clinical Filters",
            ),
            dbc.AccordionItem(
                [
                    # Phenotype Filters
                    dbc.Label("Associated Phenotypes"),
                    dcc.Dropdown(
                        id="phenotype-filter",
                        options=[],  # Will be populated dynamically
                        multi=True,
                        placeholder="Select phenotypes...",
                    ),
                    html.Hr(),
                    # Gene Filters
                    dbc.Label("Associated Genes"),
                    dcc.Dropdown(
                        id="gene-filter",
                        options=[],  # Will be populated dynamically
                        multi=True,
                        placeholder="Select genes...",
                    ),
                ],
                title="Entity Filters",
            ),
        ],
        start_collapsed=True,
    )


__all__ = [
    "create_clinical_review_card",
    "create_clinical_card_grid",
    "create_enhanced_filters",
    "get_clinical_significance_color",
    "get_evidence_level_color",
]

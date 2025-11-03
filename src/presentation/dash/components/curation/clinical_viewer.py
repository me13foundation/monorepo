"""
Clinical Data Viewer Component for MED13 Curation Dashboard.

Provides detailed clinical information display with tabbed interface.
"""

from typing import Any, Dict, List

from dash import html
import dash_bootstrap_components as dbc

from src.presentation.dash.components.curation.clinical_card import (
    get_clinical_significance_color,
    get_evidence_level_color,
)
from src.presentation.dash.components.curation.evidence_comparison import (
    create_evidence_comparison_panel,
)
from src.presentation.dash.components.curation.conflict_resolver import (
    create_conflict_resolution_panel,
)
from src.presentation.dash.components.curation.annotation_panel import (
    create_annotation_panel,
)
from src.presentation.dash.components.curation.audit_timeline import (
    create_enhanced_audit_timeline,
)
from src.presentation.dash.components.curation.bulk_resolution import (
    create_bulk_resolution_panel,
)


def create_clinical_viewer(variant_data: Dict[str, Any]) -> dbc.Container:
    """
    Create a comprehensive clinical data viewer with tabbed panels.

    Args:
        variant_data: Dictionary containing detailed variant information

    Returns:
        Container with tabbed clinical viewer
    """
    variant_id = variant_data.get("variant_id", "Unknown")
    gene_symbol = variant_data.get("gene_symbol", "Unknown")
    clinical_sig = variant_data.get("clinical_significance", "not_provided")

    # Header with key clinical info
    header = dbc.Row(
        [
            dbc.Col(
                [
                    html.H4(
                        [
                            f"Variant: {variant_id}",
                            html.Small(
                                f" • Gene: {gene_symbol}", className="text-muted ms-2"
                            ),
                        ]
                    ),
                    dbc.Badge(
                        clinical_sig.replace("_", " ").title(),
                        style={
                            "backgroundColor": get_clinical_significance_color(
                                clinical_sig
                            ),
                            "color": "white",
                        },
                        className="mt-1",
                    ),
                ],
                width=8,
            ),
            dbc.Col(
                [create_confidence_gauge(variant_data.get("confidence_score", 0.0))],
                width=4,
            ),
        ],
        className="mb-4",
    )

    # Tabbed content
    tabs = dbc.Tabs(
        [
            dbc.Tab(
                create_summary_tab(variant_data), label="Summary", tab_id="summary"
            ),
            dbc.Tab(
                create_genomic_tab(variant_data),
                label="Genomic Context",
                tab_id="genomic",
            ),
            dbc.Tab(
                create_evidence_tab(variant_data),
                label="Evidence Analysis",
                tab_id="evidence",
            ),
            dbc.Tab(
                create_phenotypes_tab(variant_data),
                label="Phenotypes",
                tab_id="phenotypes",
            ),
            dbc.Tab(
                create_literature_tab(variant_data),
                label="Literature",
                tab_id="literature",
            ),
            dbc.Tab(
                create_evidence_comparison_panel(variant_data),
                label="Evidence Comparison",
                tab_id="comparison",
            ),
            dbc.Tab(
                create_conflict_resolution_panel(variant_data),
                label="Conflict Resolution",
                tab_id="conflicts",
            ),
            dbc.Tab(
                create_annotation_panel(variant_data),
                label="Expert Annotations",
                tab_id="annotations",
            ),
            dbc.Tab(
                create_enhanced_audit_timeline(
                    variant_data.get("variant_id", "Unknown")
                ),
                label="Audit Timeline",
                tab_id="audit",
            ),
            dbc.Tab(
                create_bulk_resolution_panel([], [variant_data]),
                label="Bulk Actions",
                tab_id="bulk",
            ),
        ]
    )

    return dbc.Container([header, tabs], fluid=True)


def create_confidence_gauge(confidence: float) -> dbc.Card:
    """Create a confidence meter gauge."""
    percentage = int(confidence * 100)
    color = (
        "success" if confidence > 0.7 else "warning" if confidence > 0.4 else "danger"
    )

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6("Evidence Confidence", className="card-title"),
                    dbc.Progress(
                        value=percentage,
                        color=color,
                        className="mb-2",
                        style={"height": "20px"},
                    ),
                    html.P(
                        f"{percentage}% confidence based on evidence strength and consistency",
                        className="text-muted mb-0 small",
                    ),
                ]
            )
        ]
    )


def create_summary_tab(variant_data: Dict[str, Any]) -> html.Div:
    """Create the summary tab with key clinical information."""
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Clinical Classification"),
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                variant_data.get(
                                                    "clinical_significance",
                                                    "Not Provided",
                                                )
                                                .replace("_", " ")
                                                .title()
                                            ),
                                            html.P(
                                                f"Review Status: {variant_data.get('review_status', 'Unknown')}",
                                                className="text-muted",
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Evidence Overview"),
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                f"{variant_data.get('evidence_count', 0)} Evidence Records"
                                            ),
                                            create_evidence_level_summary(
                                                variant_data.get("evidence_levels", [])
                                            ),
                                        ]
                                    ),
                                ]
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
                            dbc.Card(
                                [
                                    dbc.CardHeader("Population Frequency"),
                                    dbc.CardBody(
                                        [create_frequency_display(variant_data)]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Quality Metrics"),
                                    dbc.CardBody(
                                        [create_quality_metrics(variant_data)]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                ]
            ),
        ]
    )


def create_genomic_tab(variant_data: Dict[str, Any]) -> html.Div:
    """Create the genomic context tab."""
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Genomic Location"),
                                    dbc.CardBody(
                                        [
                                            html.P(
                                                [
                                                    html.Strong("Chromosome:"),
                                                    f" {variant_data.get('chromosome', 'Unknown')}",
                                                ]
                                            ),
                                            html.P(
                                                [
                                                    html.Strong("Position:"),
                                                    f" {variant_data.get('position', 'Unknown'):,}",
                                                ]
                                            ),
                                            html.P(
                                                [
                                                    html.Strong("Reference:"),
                                                    f" {variant_data.get('reference_allele', 'Unknown')}",
                                                ]
                                            ),
                                            html.P(
                                                [
                                                    html.Strong("Alternate:"),
                                                    f" {variant_data.get('alternate_allele', 'Unknown')}",
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("HGVS Nomenclature"),
                                    dbc.CardBody(
                                        [
                                            html.P(
                                                [
                                                    html.Strong("Genomic:"),
                                                    f" {variant_data.get('hgvs_genomic', 'Not available')}",
                                                ]
                                            ),
                                            html.P(
                                                [
                                                    html.Strong("cDNA:"),
                                                    f" {variant_data.get('hgvs_cdna', 'Not available')}",
                                                ]
                                            ),
                                            html.P(
                                                [
                                                    html.Strong("Protein:"),
                                                    f" {variant_data.get('hgvs_protein', 'Not available')}",
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Population Frequencies"),
                    dbc.CardBody([create_population_frequency_table(variant_data)]),
                ]
            ),
        ]
    )


def create_evidence_tab(variant_data: Dict[str, Any]) -> html.Div:
    """Create the evidence analysis tab."""
    evidence_records = variant_data.get("evidence_records", [])

    if not evidence_records:
        return html.Div(
            [dbc.Alert("No evidence records available for this variant.", color="info")]
        )

    # Group evidence by level
    evidence_by_level: Dict[str, List[Dict[str, Any]]] = {}
    for evidence in evidence_records:
        level = evidence.get("evidence_level", "unknown")
        if level not in evidence_by_level:
            evidence_by_level[level] = []
        evidence_by_level[level].append(evidence)

    evidence_sections = []
    for level in ["definitive", "strong", "supporting", "limited"]:
        if level in evidence_by_level:
            evidence_sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.Strong(level.title()),
                                dbc.Badge(
                                    len(evidence_by_level[level]),
                                    color="primary",
                                    className="ms-2",
                                ),
                            ]
                        ),
                        dbc.CardBody(
                            [
                                html.Ul(
                                    [
                                        html.Li(
                                            [
                                                html.Strong(
                                                    evidence.get(
                                                        "type", "Unknown"
                                                    ).title()
                                                ),
                                                html.Br(),
                                                html.Small(
                                                    evidence.get("description", ""),
                                                    className="text-muted",
                                                ),
                                            ]
                                        )
                                        for evidence in evidence_by_level[level]
                                    ]
                                )
                            ]
                        ),
                    ],
                    className="mb-3",
                )
            )

    return html.Div(evidence_sections)


def create_phenotypes_tab(variant_data: Dict[str, Any]) -> html.Div:
    """Create the phenotypes tab."""
    phenotypes = variant_data.get("phenotypes", [])

    if not phenotypes:
        return html.Div(
            [
                dbc.Alert(
                    "No phenotype associations available for this variant.",
                    color="info",
                )
            ]
        )

    phenotype_cards = []
    for phenotype in phenotypes:
        phenotype_cards.append(
            dbc.Card(
                [
                    dbc.CardHeader(phenotype.get("name", "Unknown Phenotype")),
                    dbc.CardBody(
                        [
                            html.P(
                                [
                                    html.Strong("HPO ID:"),
                                    f" {phenotype.get('hpo_id', 'Unknown')}",
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("Category:"),
                                    f" {phenotype.get('category', 'Unknown')}",
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("Frequency:"),
                                    f" {phenotype.get('frequency', 'Unknown')}",
                                ]
                            ),
                            html.P(
                                phenotype.get("definition", ""), className="text-muted"
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            )
        )

    return html.Div(phenotype_cards)


def create_literature_tab(variant_data: Dict[str, Any]) -> html.Div:
    """Create the literature tab."""
    publications = variant_data.get("publications", [])

    if not publications:
        return html.Div(
            [
                dbc.Alert(
                    "No literature references available for this variant.", color="info"
                )
            ]
        )

    publication_cards = []
    for pub in publications:
        publication_cards.append(
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            html.Strong(pub.get("title", "Unknown Title")),
                            html.Small(
                                f" ({pub.get('year', 'Unknown')})",
                                className="text-muted ms-2",
                            ),
                        ]
                    ),
                    dbc.CardBody(
                        [
                            html.P(
                                [
                                    html.Strong("Authors:"),
                                    f" {pub.get('authors', 'Unknown')}",
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("Journal:"),
                                    f" {pub.get('journal', 'Unknown')}",
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("DOI:"),
                                    html.A(
                                        pub.get("doi", "Unknown"),
                                        href=(
                                            f"https://doi.org/{pub.get('doi', '')}"
                                            if pub.get("doi")
                                            else "#"
                                        ),
                                        target="_blank",
                                    ),
                                ]
                            ),
                            html.P(pub.get("abstract", ""), className="text-muted"),
                        ]
                    ),
                ],
                className="mb-3",
            )
        )

    return html.Div(publication_cards)


def create_evidence_level_summary(evidence_levels: List[str]) -> html.Div:
    """Create a summary of evidence levels."""
    level_counts: Dict[str, int] = {}
    for level in evidence_levels:
        level_counts[level] = level_counts.get(level, 0) + 1

    badges = []
    for level, count in level_counts.items():
        color = get_evidence_level_color(level)
        badges.append(
            dbc.Badge(
                f"{level.title()}: {count}",
                style={"backgroundColor": color, "color": "white"},
                className="me-2 mb-1",
            )
        )

    return html.Div(badges)


def create_frequency_display(variant_data: Dict[str, Any]) -> html.Div:
    """Create population frequency display."""
    gnomad_af = variant_data.get("gnomad_af")
    allele_freq = variant_data.get("allele_frequency")

    if gnomad_af is not None:
        gnomad_percentage = gnomad_af * 100
        return html.Div(
            [
                html.P(
                    [html.Strong("gnomAD Frequency:"), f" {gnomad_percentage:.2f}%"]
                ),
                html.P(
                    [
                        html.Strong("Allele Frequency:"),
                        (
                            f" {allele_freq * 100:.2f}%"
                            if allele_freq
                            else " Not available"
                        ),
                    ]
                ),
            ]
        )
    else:
        return html.Div(
            [html.P("Population frequency data not available", className="text-muted")]
        )


def create_quality_metrics(variant_data: Dict[str, Any]) -> html.Div:
    """Create quality metrics display."""
    quality_score = variant_data.get("quality_score", 0.0)
    issues = variant_data.get("issues", 0)

    quality_percentage = int(quality_score * 100)
    quality_color = (
        "success"
        if quality_score > 0.8
        else "warning"
        if quality_score > 0.6
        else "danger"
    )

    return html.Div(
        [
            html.P(
                [
                    html.Strong("Quality Score:"),
                    html.Span(
                        f" {quality_percentage}%",
                        style={
                            "color": {
                                "success": "#28a745",
                                "warning": "#ffc107",
                                "danger": "#dc3545",
                            }.get(quality_color)
                        },
                    ),
                ]
            ),
            html.P(
                [
                    html.Strong("Validation Issues:"),
                    html.Span(
                        f" {issues}",
                        style={"color": "#dc3545" if issues > 0 else "#28a745"},
                    ),
                ]
            ),
        ]
    )


def create_population_frequency_table(variant_data: Dict[str, Any]) -> dbc.Table:
    """Create a table of population frequencies."""
    frequencies = []

    # Add gnomAD frequency
    if variant_data.get("gnomad_af") is not None:
        frequencies.append(
            {
                "population": "gnomAD",
                "frequency": f"{variant_data['gnomad_af'] * 100:.4f}%",
            }
        )

    # Add allele frequency
    if variant_data.get("allele_frequency") is not None:
        frequencies.append(
            {
                "population": "Overall",
                "frequency": f"{variant_data['allele_frequency'] * 100:.4f}%",
            }
        )

    if not frequencies:
        return html.Div(
            "No population frequency data available", className="text-muted"
        )

    table_rows = [
        html.Tr([html.Td(freq["population"]), html.Td(freq["frequency"])])
        for freq in frequencies
    ]

    return dbc.Table(
        [
            html.Thead([html.Tr([html.Th("Population"), html.Th("Allele Frequency")])]),
            html.Tbody(table_rows),
        ],
        bordered=True,
        hover=True,
        size="sm",
    )


__all__ = [
    "create_clinical_viewer",
    "create_confidence_gauge",
    "create_summary_tab",
    "create_genomic_tab",
    "create_evidence_tab",
    "create_phenotypes_tab",
    "create_literature_tab",
]

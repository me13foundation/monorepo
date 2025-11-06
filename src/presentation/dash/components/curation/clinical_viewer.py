"""
Clinical viewer component rendering variant and phenotype context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import dash_bootstrap_components as dbc

from dash import html

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

    from dash.development.base_component import Component
    from src.presentation.dash.types import PhenotypeSnapshot, VariantDetail


def render_clinical_viewer(
    variant: VariantDetail | None,
    phenotypes: Sequence[PhenotypeSnapshot],
) -> Component:
    """
    Render the clinical summary panel for the curated detail view.

    Args:
        variant: Variant detail payload (or None if nothing selected)
        phenotypes: Phenotype snapshots linked to the variant
    """
    if variant is None:
        return cast(
            "Component",
            dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "Select a variant from the queue to view clinical details.",
                ],
                color="info",
                className="mb-0",
            ),
        )

    hgvs = variant.get("hgvs", {})

    summary_items = [
        _detail_row("Variant ID", variant["variant_id"]),
        _detail_row("ClinVar", variant.get("clinvar_id", "N/A")),
        _detail_row("Gene Symbol", variant.get("gene_symbol", "Unknown")),
        _detail_row(
            "Location",
            f"chr{variant['chromosome']}:{variant['position']:,}",
        ),
        _detail_row(
            "Clinical Significance",
            variant["clinical_significance"].replace("_", " ").title(),
        ),
        _detail_row("Variant Type", variant["variant_type"].replace("_", " ").title()),
        _detail_row(
            "Allele Frequency",
            _format_frequency(variant.get("allele_frequency")),
        ),
        _detail_row("gnomAD AF", _format_frequency(variant.get("gnomad_af"))),
        _detail_row("HGVS (Genomic)", hgvs.get("genomic", "—")),
        _detail_row("HGVS (Protein)", hgvs.get("protein", "—")),
        _detail_row("HGVS (cDNA)", hgvs.get("cdna", "—")),
        _detail_row("Condition", variant.get("condition", "—")),
        _detail_row("Review Status", variant.get("review_status", "Pending")),
        _detail_row("Last Updated", variant.get("updated_at", "Unknown")),
    ]

    if phenotypes:
        phenotype_badges: Component = cast(
            "Component",
            dbc.Stack(
                [
                    dbc.Badge(
                        f"{phenotype['name']} ({phenotype['hpo_id']})",
                        color="primary",
                        className="me-2 mb-2",
                    )
                    for phenotype in phenotypes
                ],
                direction="horizontal",
                gap=2,
                className="flex-wrap",
            ),
        )
    else:
        phenotype_badges = cast(
            "Component",
            html.Small("No phenotypes linked.", className="text-muted"),
        )

    return cast(
        "Component",
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Variant Summary"),
                        html.Div(summary_items, className="clinical-summary-grid"),
                    ],
                    md=7,
                ),
                dbc.Col(
                    [
                        html.H5("Phenotype Associations"),
                        phenotype_badges,
                    ],
                    md=5,
                ),
            ],
            className="g-3",
        ),
    )


def _detail_row(label: str, value: object) -> Component:
    return cast(
        "Component",
        html.Div(
            [
                html.Span(label, className="text-muted d-block small"),
                html.Span(str(value), className="fw-semibold"),
            ],
            className="mb-2",
        ),
    )


def _format_frequency(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.4f}"


__all__ = ["render_clinical_viewer"]

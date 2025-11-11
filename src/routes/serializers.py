"""
Helper functions for serializing domain entities into typed API DTOs.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING

from src.models.api.common import (
    ActivityFeedItem,
    DashboardSummary,
    GeneSummary,
    PhenotypeSummary,
    PublicationSummary,
    VariantLinkSummary,
)
from src.models.api.evidence import (
    EvidenceLevel as ApiEvidenceLevel,
)
from src.models.api.evidence import (
    EvidenceResponse,
    EvidenceSummaryResponse,
)
from src.models.api.evidence import (
    EvidenceType as ApiEvidenceType,
)
from src.models.api.gene import (
    GenePhenotypeSummary,
    GeneResponse,
)
from src.models.api.gene import (
    GeneType as ApiGeneType,
)
from src.models.api.phenotype import (
    PhenotypeCategory as ApiPhenotypeCategory,
)
from src.models.api.phenotype import (
    PhenotypeResponse,
)
from src.models.api.publication import (
    AuthorInfo,
    PublicationResponse,
)
from src.models.api.publication import (
    PublicationType as ApiPublicationType,
)
from src.models.api.variant import (
    ClinicalSignificance as ApiClinicalSignificance,
)
from src.models.api.variant import (
    VariantResponse,
    VariantSummaryResponse,
)
from src.models.api.variant import (
    VariantType as ApiVariantType,
)

if TYPE_CHECKING:
    from datetime import datetime

    from src.domain.entities.evidence import Evidence
    from src.domain.entities.gene import Gene
    from src.domain.entities.phenotype import Phenotype
    from src.domain.entities.publication import Publication
    from src.domain.entities.variant import EvidenceSummary, Variant, VariantSummary


def serialize_variant_summary(summary: VariantSummary) -> VariantSummaryResponse:
    """Convert a VariantSummary into a typed DTO."""
    return VariantSummaryResponse(
        variant_id=summary.variant_id,
        clinvar_id=summary.clinvar_id,
        chromosome=summary.chromosome,
        position=summary.position,
        clinical_significance=summary.clinical_significance,
    )


def serialize_variant(variant: Variant) -> VariantResponse:
    """Serialize a Variant aggregate into VariantResponse."""
    variant_id = _require_entity_id("Variant", variant.id)
    evidence_items = (
        [serialize_evidence_brief(ev) for ev in variant.evidence]
        if getattr(variant, "evidence", None)
        else None
    )

    gene_summary = _maybe_gene_summary(variant)

    return VariantResponse(
        id=variant_id,
        variant_id=variant.variant_id,
        clinvar_id=variant.clinvar_id,
        gene_id=variant.gene_public_id or "",
        gene_symbol=variant.gene_symbol or "",
        chromosome=variant.chromosome,
        position=variant.position,
        reference_allele=variant.reference_allele,
        alternate_allele=variant.alternate_allele,
        hgvs_genomic=variant.hgvs_genomic,
        hgvs_protein=variant.hgvs_protein,
        hgvs_cdna=variant.hgvs_cdna,
        variant_type=ApiVariantType(variant.variant_type),
        clinical_significance=ApiClinicalSignificance(variant.clinical_significance),
        condition=variant.condition,
        review_status=variant.review_status,
        allele_frequency=variant.allele_frequency,
        gnomad_af=variant.gnomad_af,
        created_at=variant.created_at,
        updated_at=variant.updated_at,
        evidence_count=len(evidence_items) if evidence_items else 0,
        evidence=evidence_items,
        gene=gene_summary,
    )


def serialize_gene(
    gene: Gene,
    *,
    include_variants: bool = False,
    variants: Iterable[VariantSummary] | None = None,
    include_phenotypes: bool = False,
    phenotypes: Iterable[Mapping[str, object] | GenePhenotypeSummary] | None = None,
) -> GeneResponse:
    """Serialize a Gene aggregate with optional relationships."""
    gene_id = _require_entity_id("Gene", gene.id)

    if include_variants:
        variant_iterable = variants if variants is not None else gene.variants
        variant_summaries = [
            serialize_variant_summary(summary) for summary in variant_iterable
        ]
        variant_count = len(variant_summaries)
    else:
        variant_summaries = None
        variant_count = len(gene.variants) if gene.variants else 0

    phenotype_summaries: list[GenePhenotypeSummary] | None = None
    phenotype_count = 0
    if include_phenotypes:
        raw_phenotypes = phenotypes if phenotypes is not None else []
        phenotype_summaries = [
            _coerce_gene_phenotype(value) for value in raw_phenotypes
        ]
        phenotype_count = len(phenotype_summaries)

    return GeneResponse(
        id=gene_id,
        gene_id=gene.gene_id,
        symbol=gene.symbol,
        name=gene.name,
        description=gene.description,
        gene_type=ApiGeneType(gene.gene_type),
        chromosome=gene.chromosome,
        start_position=gene.start_position,
        end_position=gene.end_position,
        ensembl_id=gene.ensembl_id,
        ncbi_gene_id=gene.ncbi_gene_id,
        uniprot_id=gene.uniprot_id,
        created_at=gene.created_at,
        updated_at=gene.updated_at,
        variant_count=variant_count,
        phenotype_count=phenotype_count,
        variants=variant_summaries,
        phenotypes=phenotype_summaries,
    )


def serialize_phenotype(phenotype: Phenotype) -> PhenotypeResponse:
    """Serialize a Phenotype entity."""
    phenotype_id = _require_entity_id("Phenotype", phenotype.id)
    parent_summary = (
        PhenotypeSummary(
            id=None,
            hpo_id=phenotype.parent_hpo_id,
            name=None,
        )
        if phenotype.parent_hpo_id
        else None
    )
    return PhenotypeResponse(
        id=phenotype_id,
        hpo_id=phenotype.identifier.hpo_id,
        hpo_term=phenotype.identifier.hpo_term,
        name=phenotype.name,
        definition=phenotype.definition,
        synonyms=list(phenotype.synonyms),
        category=ApiPhenotypeCategory(phenotype.category),
        parent_hpo_id=phenotype.parent_hpo_id,
        is_root_term=phenotype.is_root_term,
        frequency_in_med13=phenotype.frequency_in_med13,
        severity_score=phenotype.severity_score,
        created_at=phenotype.created_at,
        updated_at=phenotype.updated_at,
        evidence_count=getattr(phenotype, "evidence_count", 0),
        variant_count=getattr(phenotype, "variant_count", 0),
        parent_phenotype=parent_summary,
        child_phenotypes=None,
        evidence=None,
    )


def serialize_publication(publication: Publication) -> PublicationResponse:
    """Serialize a Publication entity."""
    publication_id = _require_entity_id("Publication", publication.id)
    evidence = [serialize_evidence(ev) for ev in publication.evidence]
    author_models = [
        AuthorInfo(
            name=name,
            first_name=None,
            last_name=None,
            affiliation=None,
            orcid=None,
        )
        for name in publication.authors
    ]

    return PublicationResponse(
        id=publication_id,
        pubmed_id=publication.identifier.pubmed_id,
        pmc_id=publication.identifier.pmc_id,
        doi=publication.identifier.doi,
        title=publication.title,
        authors=author_models,
        journal=publication.journal,
        publication_year=publication.publication_year,
        volume=publication.volume,
        issue=publication.issue,
        pages=publication.pages,
        publication_date=publication.publication_date,
        publication_type=ApiPublicationType(publication.publication_type),
        abstract=publication.abstract,
        keywords=list(publication.keywords),
        citation_count=publication.citation_count,
        impact_factor=publication.impact_factor,
        reviewed=publication.reviewed,
        relevance_score=publication.relevance_score,
        full_text_url=publication.full_text_url,
        open_access=publication.open_access,
        created_at=publication.created_at,
        updated_at=publication.updated_at,
        evidence_count=len(evidence),
        evidence=evidence,
    )


def serialize_evidence_brief(evidence: EvidenceSummary) -> EvidenceSummaryResponse:
    """Serialize the lightweight EvidenceSummary helper."""
    return EvidenceSummaryResponse(
        id=evidence.evidence_id,
        evidence_level=evidence.evidence_level,
        evidence_type=evidence.evidence_type,
        description=evidence.description,
        reviewed=evidence.reviewed,
    )


def serialize_evidence(evidence: Evidence) -> EvidenceResponse:
    """Serialize a full Evidence entity."""
    evidence_id = _require_entity_id("Evidence", evidence.id)
    variant_summary = _build_variant_summary_for_evidence(evidence)
    phenotype_summary = _build_phenotype_summary_for_evidence(evidence)
    publication_summary = _build_publication_summary_for_evidence(evidence)
    return EvidenceResponse(
        id=evidence_id,
        variant_id=str(evidence.variant_id),
        phenotype_id=str(evidence.phenotype_id),
        publication_id=(
            str(evidence.publication_id) if evidence.publication_id else None
        ),
        description=evidence.description,
        summary=evidence.summary,
        evidence_level=ApiEvidenceLevel(evidence.evidence_level.value),
        evidence_type=ApiEvidenceType(evidence.evidence_type),
        confidence_score=evidence.confidence.score,
        quality_score=evidence.quality_score,
        sample_size=evidence.sample_size,
        study_type=evidence.study_type,
        statistical_significance=evidence.statistical_significance,
        reviewed=evidence.reviewed,
        review_date=evidence.review_date,
        reviewer_notes=evidence.reviewer_notes,
        created_at=evidence.created_at,
        updated_at=evidence.updated_at,
        variant=variant_summary,
        phenotype=phenotype_summary,
        publication=publication_summary,
    )


def build_dashboard_summary(
    entity_counts: Mapping[str, int],
    *,
    pending_count: int,
    approved_count: int,
    rejected_count: int,
) -> DashboardSummary:
    """Construct the typed dashboard summary DTO."""
    total_items = sum(entity_counts.values())
    return DashboardSummary(
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        total_items=total_items,
        entity_counts=dict(entity_counts),
    )


def build_activity_feed_item(
    message: str,
    *,
    category: str,
    timestamp: datetime,
    icon: str | None = None,
) -> ActivityFeedItem:
    """Construct a typed activity feed item."""
    return ActivityFeedItem(
        message=message,
        category=category,
        icon=icon,
        created_at=_serialize_datetime(timestamp) or "",
    )


def _maybe_gene_summary(variant: Variant) -> GeneSummary | None:
    """Build a gene summary if the variant includes gene metadata."""
    gene_id_value = variant.gene_public_id
    gene_symbol_value = variant.gene_symbol
    if gene_id_value is None and gene_symbol_value is None:
        return None
    return GeneSummary(
        id=getattr(variant, "gene_database_id", None),
        gene_id=gene_id_value,
        symbol=gene_symbol_value,
        name=None,
    )


def _build_variant_summary_for_evidence(
    evidence: Evidence,
) -> VariantLinkSummary | None:
    """Construct a lightweight variant summary for evidence payloads."""
    variant_id_value: str | None = None
    clinvar_id_value: str | None = None

    if evidence.variant_summary is not None:
        variant_id_value = evidence.variant_summary.variant_id
        clinvar_id_value = evidence.variant_summary.clinvar_id
    elif evidence.variant_identifier is not None:
        variant_id_value = evidence.variant_identifier.variant_id
        clinvar_id_value = evidence.variant_identifier.clinvar_id

    if variant_id_value is None and clinvar_id_value is None:
        return None

    return VariantLinkSummary(
        id=evidence.variant_id,
        variant_id=variant_id_value,
        clinvar_id=clinvar_id_value,
        gene_symbol=None,
    )


def _build_phenotype_summary_for_evidence(
    evidence: Evidence,
) -> PhenotypeSummary | None:
    """Construct a phenotype summary for evidence payloads."""
    identifier = evidence.phenotype_identifier
    return PhenotypeSummary(
        id=evidence.phenotype_id,
        hpo_id=identifier.hpo_id if identifier else None,
        name=identifier.hpo_term if identifier else None,
    )


def _build_publication_summary_for_evidence(
    evidence: Evidence,
) -> PublicationSummary | None:
    """Construct a publication summary for evidence payloads."""
    identifier = evidence.publication_identifier
    if identifier is None and evidence.publication_id is None:
        return None
    return PublicationSummary(
        id=evidence.publication_id,
        title=None,
        pubmed_id=identifier.pubmed_id if identifier else None,
        doi=identifier.doi if identifier else None,
    )


def _coerce_gene_phenotype(
    value: GenePhenotypeSummary | Mapping[str, object],
) -> GenePhenotypeSummary:
    if isinstance(value, GenePhenotypeSummary):
        return value
    return GenePhenotypeSummary.model_validate(value)


def _require_entity_id(entity_name: str, identifier: int | None) -> int:
    if identifier is None:
        msg = f"{entity_name} must have an id before serialization"
        raise ValueError(msg)
    return identifier


def _serialize_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


__all__ = [
    "build_activity_feed_item",
    "build_dashboard_summary",
    "serialize_evidence",
    "serialize_evidence_brief",
    "serialize_gene",
    "serialize_phenotype",
    "serialize_publication",
    "serialize_variant",
    "serialize_variant_summary",
]

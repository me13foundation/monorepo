"""
Helper functions for serializing domain entities into API-facing dictionaries.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, Mapping, Optional

from src.domain.entities.evidence import Evidence
from src.domain.entities.gene import Gene
from src.domain.entities.phenotype import Phenotype
from src.domain.entities.publication import Publication
from src.domain.entities.variant import EvidenceSummary, Variant, VariantSummary


def serialize_variant_summary(summary: VariantSummary) -> Dict[str, Any]:
    """Convert a VariantSummary into a plain dictionary suitable for JSON."""
    return {
        "variant_id": summary.variant_id,
        "clinvar_id": summary.clinvar_id,
        "chromosome": summary.chromosome,
        "position": summary.position,
        "clinical_significance": summary.clinical_significance,
    }


def serialize_variant(variant: Variant) -> Dict[str, Any]:
    """Serialize a Variant aggregate."""
    payload: Dict[str, Any] = {
        "id": variant.id,
        "variant_id": variant.variant_id,
        "clinvar_id": variant.clinvar_id,
        "chromosome": variant.chromosome,
        "position": variant.position,
        "reference_allele": variant.reference_allele,
        "alternate_allele": variant.alternate_allele,
        "variant_type": variant.variant_type,
        "clinical_significance": variant.clinical_significance,
        "gene_symbol": variant.gene_symbol,
        "created_at": _serialize_datetime(variant.created_at),
        "updated_at": _serialize_datetime(variant.updated_at),
    }

    if variant.hgvs_genomic:
        payload["hgvs_genomic"] = variant.hgvs_genomic
    if variant.hgvs_cdna:
        payload["hgvs_cdna"] = variant.hgvs_cdna
    if variant.hgvs_protein:
        payload["hgvs_protein"] = variant.hgvs_protein
    if variant.condition:
        payload["condition"] = variant.condition
    if variant.review_status:
        payload["review_status"] = variant.review_status
    if variant.allele_frequency is not None:
        payload["allele_frequency"] = variant.allele_frequency
    if variant.gnomad_af is not None:
        payload["gnomad_af"] = variant.gnomad_af
    if variant.evidence:
        payload["evidence"] = [serialize_evidence_brief(ev) for ev in variant.evidence]
        payload["evidence_count"] = len(variant.evidence)

    return payload


def serialize_gene(
    gene: Gene,
    *,
    include_variants: bool = False,
    variants: Optional[Iterable[VariantSummary]] = None,
    include_phenotypes: bool = False,
    phenotypes: Optional[Iterable[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "id": gene.id,
        "gene_id": gene.gene_id,
        "symbol": gene.symbol,
        "name": gene.name,
        "description": gene.description,
        "gene_type": gene.gene_type,
        "chromosome": gene.chromosome,
        "start_position": gene.start_position,
        "end_position": gene.end_position,
        "ensembl_id": gene.ensembl_id,
        "ncbi_gene_id": gene.ncbi_gene_id,
        "uniprot_id": gene.uniprot_id,
        "created_at": _serialize_datetime(gene.created_at),
        "updated_at": _serialize_datetime(gene.updated_at),
    }

    variant_summaries: Iterable[VariantSummary]
    if include_variants:
        if variants is not None:
            variant_summaries = variants
        else:
            variant_summaries = gene.variants
        serialized_variants = [
            serialize_variant_summary(summary) for summary in variant_summaries
        ]
        payload["variants"] = serialized_variants
        payload["variant_count"] = len(serialized_variants)
    else:
        payload["variant_count"] = len(gene.variants) if gene.variants else 0

    if include_phenotypes:
        if phenotypes is not None:
            payload["phenotypes"] = list(phenotypes)
        else:
            payload["phenotypes"] = []

    return payload


def serialize_phenotype(phenotype: Phenotype) -> Dict[str, Any]:
    return {
        "id": phenotype.id,
        "hpo_id": phenotype.identifier.hpo_id,
        "hpo_term": phenotype.identifier.hpo_term,
        "name": phenotype.name,
        "definition": phenotype.definition,
        "synonyms": list(phenotype.synonyms),
        "category": phenotype.category,
        "parent_hpo_id": phenotype.parent_hpo_id,
        "is_root_term": phenotype.is_root_term,
        "frequency_in_med13": phenotype.frequency_in_med13,
        "severity_score": phenotype.severity_score,
        "created_at": _serialize_datetime(phenotype.created_at),
        "updated_at": _serialize_datetime(phenotype.updated_at),
    }


def serialize_publication(publication: Publication) -> Dict[str, Any]:
    return {
        "id": publication.id,
        "pubmed_id": publication.identifier.pubmed_id,
        "pmc_id": publication.identifier.pmc_id,
        "doi": publication.identifier.doi,
        "title": publication.title,
        "authors": list(publication.authors),
        "journal": publication.journal,
        "publication_year": publication.publication_year,
        "publication_type": publication.publication_type,
        "volume": publication.volume,
        "issue": publication.issue,
        "pages": publication.pages,
        "publication_date": (
            publication.publication_date.isoformat()
            if publication.publication_date
            else None
        ),
        "abstract": publication.abstract,
        "keywords": list(publication.keywords),
        "citation_count": publication.citation_count,
        "impact_factor": publication.impact_factor,
        "reviewed": publication.reviewed,
        "relevance_score": publication.relevance_score,
        "full_text_url": publication.full_text_url,
        "open_access": publication.open_access,
        "created_at": _serialize_datetime(publication.created_at),
        "updated_at": _serialize_datetime(publication.updated_at),
        "evidence": [serialize_evidence(ev) for ev in publication.evidence],
    }


def serialize_evidence_brief(evidence: EvidenceSummary) -> Dict[str, Any]:
    return {
        "id": evidence.evidence_id,
        "evidence_level": evidence.evidence_level,
        "evidence_type": evidence.evidence_type,
        "description": evidence.description,
        "reviewed": evidence.reviewed,
    }


def serialize_evidence(evidence: Evidence) -> Dict[str, Any]:
    return {
        "id": evidence.id,
        "variant_id": evidence.variant_id,
        "phenotype_id": evidence.phenotype_id,
        "publication_id": evidence.publication_id,
        "description": evidence.description,
        "summary": evidence.summary,
        "evidence_level": evidence.evidence_level.value,
        "evidence_type": evidence.evidence_type,
        "confidence_score": evidence.confidence.score,
        "quality_score": evidence.quality_score,
        "sample_size": evidence.sample_size,
        "study_type": evidence.study_type,
        "statistical_significance": evidence.statistical_significance,
        "reviewed": evidence.reviewed,
        "review_date": (
            evidence.review_date.isoformat() if evidence.review_date else None
        ),
        "created_at": _serialize_datetime(evidence.created_at),
        "updated_at": _serialize_datetime(evidence.updated_at),
    }


def _serialize_datetime(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def build_dashboard_summary(
    entity_counts: Mapping[str, int],
    *,
    pending_count: int,
    approved_count: int,
    rejected_count: int,
) -> Dict[str, Any]:
    total_items = sum(entity_counts.values())
    summary = {
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "total_items": total_items,
        "entity_counts": dict(entity_counts),
    }
    return summary


def build_activity_feed_item(
    message: str,
    *,
    category: str,
    timestamp: datetime,
    icon: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "message": message,
        "category": category,
        "icon": icon,
        "created_at": _serialize_datetime(timestamp),
    }


__all__ = [
    "serialize_variant_summary",
    "serialize_variant",
    "serialize_gene",
    "serialize_phenotype",
    "serialize_publication",
    "serialize_evidence",
    "serialize_evidence_brief",
    "build_dashboard_summary",
    "build_activity_feed_item",
]

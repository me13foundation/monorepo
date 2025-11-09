#!/usr/bin/env python3
"""Seed the MED13 Resource Library database with demo curation data."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.exc import SQLAlchemyError

from src.database.session import SessionLocal, engine
from src.models.database import (
    Base,
    EvidenceModel,
    GeneModel,
    PhenotypeModel,
    VariantModel,
)
from src.models.database.audit import AuditLog
from src.models.database.data_discovery import SourceCatalogEntryModel
from src.models.database.review import ReviewRecord

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
else:
    Session = Any  # type: ignore[assignment]


logger = logging.getLogger(__name__)


def ensure_gene(session: Session) -> GeneModel:
    gene = session.query(GeneModel).filter(GeneModel.gene_id == "MED13").one_or_none()
    if gene:
        return gene

    gene = GeneModel(
        gene_id="MED13",
        symbol="MED13",
        name="Mediator complex subunit 13",
        description="Component of the Mediator complex, a coactivator involved in regulated transcription of RNA polymerase II-dependent genes.",
        gene_type="protein_coding",
        chromosome="17",
        start_position=60000000,
        end_position=60020000,
        ensembl_id="ENSG00000108510",
        ncbi_gene_id=9968,
        uniprot_id="Q9UHV7",
    )
    session.add(gene)
    session.flush()
    return gene


def ensure_variant(session: Session, gene: GeneModel) -> VariantModel:
    variant = (
        session.query(VariantModel)
        .filter(VariantModel.variant_id == "VCV000999999")
        .one_or_none()
    )
    if variant:
        return variant

    variant = VariantModel(
        gene_id=gene.id,
        variant_id="VCV000999999",
        clinvar_id="VCV000999999",
        chromosome="17",
        position=60005000,
        reference_allele="A",
        alternate_allele="G",
        hgvs_genomic="chr17:g.60005000A>G",
        hgvs_protein="p.Val123Gly",
        hgvs_cdna="c.367A>G",
        variant_type="snv",
        clinical_significance="pathogenic",
        condition="Neurodevelopmental disorder",
        review_status="criteria_provided",
        allele_frequency=0.0002,
        gnomad_af=0.0003,
    )
    session.add(variant)
    session.flush()
    return variant


def ensure_phenotype(session: Session) -> PhenotypeModel:
    phenotype = (
        session.query(PhenotypeModel)
        .filter(PhenotypeModel.hpo_id == "HP:0001249")
        .one_or_none()
    )
    if phenotype:
        return phenotype

    phenotype = PhenotypeModel(
        hpo_id="HP:0001249",
        hpo_term="Intellectual disability",
        name="Intellectual disability",
        definition="Subnormal intellectual functioning originating during the developmental period.",
        synonyms='["Developmental delay", "Cognitive impairment"]',
        category="other",
        frequency_in_med13="frequent",
    )
    session.add(phenotype)
    session.flush()
    return phenotype


def ensure_evidence(
    session: Session,
    variant: VariantModel,
    phenotype: PhenotypeModel,
) -> EvidenceModel:
    evidence = (
        session.query(EvidenceModel)
        .filter(EvidenceModel.variant_id == variant.id)
        .filter(EvidenceModel.phenotype_id == phenotype.id)
        .one_or_none()
    )
    if evidence:
        return evidence

    evidence = EvidenceModel(
        variant_id=variant.id,
        phenotype_id=phenotype.id,
        evidence_level="strong",
        evidence_type="clinical_report",
        description="Published case report linking MED13 variant to intellectual disability.",
        summary="Primary publication supporting the association.",
        confidence_score=0.88,
        reviewed=True,
    )
    session.add(evidence)
    session.flush()
    return evidence


def ensure_review(session: Session, variant: VariantModel) -> None:
    existing = (
        session.query(ReviewRecord)
        .filter(ReviewRecord.entity_type == "variant")
        .filter(ReviewRecord.entity_id == variant.variant_id)
        .one_or_none()
    )
    if existing:
        return

    review = ReviewRecord(
        entity_type="variant",
        entity_id=variant.variant_id,
        status="pending",
        priority="high",
        quality_score=0.92,
        issues=2,
        last_updated=datetime.now(UTC),
    )
    session.add(review)


def ensure_audit_log(session: Session, variant: VariantModel) -> None:
    exists = (
        session.query(AuditLog)
        .filter(AuditLog.entity_type == "variant")
        .filter(AuditLog.entity_id == variant.variant_id)
        .first()
    )
    if exists:
        return

    session.add(
        AuditLog(
            action="comment",
            entity_type="variant",
            entity_id=variant.variant_id,
            user="demo-curator",
            details="Initial curator note seeded for demo dashboard.",
        ),
    )


def seed_source_catalog(session: Session) -> None:
    """Seed the source catalog with demo entries."""
    logger.info("Seeding source catalog...")

    # Check if already seeded
    if session.query(SourceCatalogEntryModel).count() > 0:
        logger.info("Source catalog already seeded, skipping")
        return

    # Sample catalog entries
    catalog_entries = [
        {
            "id": "clinvar",
            "name": "ClinVar",
            "description": "Public archive of reports of the relationships among human variations and phenotypes",
            "category": "Genomic Variant Databases",
            "param_type": "gene",
            "url_template": "https://www.ncbi.nlm.nih.gov/clinvar/?term=${gene}[gene]",
            "tags": ["variants", "genomics", "clinical"],
            "is_active": True,
            "requires_auth": False,
        },
        {
            "id": "gnomad",
            "name": "gnomAD",
            "description": "Genome Aggregation Database provides allele frequency data from large-scale sequencing projects",
            "category": "Genomic Variant Databases",
            "param_type": "gene",
            "url_template": "https://gnomad.broadinstitute.org/gene/${gene}?dataset=gnomad_r4",
            "tags": ["variants", "population", "frequency"],
            "is_active": True,
            "requires_auth": False,
        },
        {
            "id": "pubmed",
            "name": "PubMed",
            "description": "Comprehensive database of biomedical literature from the National Library of Medicine",
            "category": "Scientific Literature",
            "param_type": "gene_and_term",
            "url_template": "https://pubmed.ncbi.nlm.nih.gov/?term=(${gene})+AND+(${term})",
            "tags": ["literature", "publications", "research"],
            "is_active": True,
            "requires_auth": False,
        },
        {
            "id": "hpo",
            "name": "Human Phenotype Ontology",
            "description": "Standardized vocabulary for describing human phenotypic abnormalities",
            "category": "Phenotype Ontologies & Databases",
            "param_type": "term",
            "url_template": "https://hpo.jax.org/app/browse/search?q=${term}",
            "tags": ["phenotypes", "ontology", "clinical"],
            "is_active": True,
            "requires_auth": False,
        },
        {
            "id": "variantformer",
            "name": "VariantFormer",
            "description": "AI model for predicting variant pathogenicity and functional impact",
            "category": "AI Predictive Models",
            "param_type": "api",
            "api_endpoint": "/api/variantformer",
            "tags": ["ai", "prediction", "pathogenicity"],
            "is_active": True,
            "requires_auth": False,
        },
    ]

    for entry_data in catalog_entries:
        entry = SourceCatalogEntryModel(**entry_data)
        session.add(entry)
        logger.info("Added catalog entry: %s", entry.name)

    logger.info("Seeded %s source catalog entries", len(catalog_entries))


def main() -> None:
    Base.metadata.create_all(bind=engine)
    logging.basicConfig(level=logging.INFO)

    session: Session | None = None
    try:
        session = SessionLocal()
        gene = ensure_gene(session)
        variant = ensure_variant(session, gene)
        phenotype = ensure_phenotype(session)
        ensure_evidence(session, variant, phenotype)
        ensure_review(session, variant)
        ensure_audit_log(session, variant)
        seed_source_catalog(session)
        session.commit()
        logger.info("Seeded MED13 demo data for curation workflows.")
    except (
        SQLAlchemyError,
        RuntimeError,
        ValueError,
    ) as exc:  # pragma: no cover - seeding diagnostics
        if session is not None:
            session.rollback()
        message = f"Failed to seed database: {exc}"
        raise SystemExit(message) from exc
    finally:
        if session is not None:
            session.close()


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    main()

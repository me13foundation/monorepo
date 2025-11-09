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
        ncbi_gene_id=99968,
        uniprot_id="Q9UHV7_MED13",
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

    # Comprehensive catalog entries based on MED13 data ecosystem
    catalog_entries = [
        # Genomic Variant Databases
        {
            "id": "clinvar",
            "name": "ClinVar",
            "description": "Public archive of reports of the relationships among human variations and phenotypes, with supporting evidence",
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
        # Gene Expression & Functional Genomics
        {
            "id": "gtex",
            "name": "GTEx Portal",
            "description": "Resource for studying the relationship between genetic variation and gene expression in human tissues",
            "category": "Gene Expression & Functional Genomics",
            "param_type": "gene",
            "url_template": "https://www.gtexportal.org/home/gene/${gene}",
            "tags": ["expression", "tissues", "transcriptomics"],
            "is_active": True,
            "requires_auth": False,
        },
        {
            "id": "hpa",
            "name": "Human Protein Atlas",
            "description": "Comprehensive resource for studying the expression and localization of human proteins",
            "category": "Gene Expression & Functional Genomics",
            "param_type": "gene",
            "url_template": "https://www.proteinatlas.org/search/${gene}",
            "tags": ["proteins", "expression", "localization"],
            "is_active": True,
            "requires_auth": False,
        },
        # Model Organism Databases
        {
            "id": "mgi",
            "name": "MGI (Mouse)",
            "description": "Primary resource for information about the genetics and genomics of the laboratory mouse",
            "category": "Model Organism Databases",
            "param_type": "gene",
            "url_template": "https://www.informatics.jax.org/searchtool/Search?query=${gene}",
            "tags": ["mouse", "model", "genetics"],
            "is_active": True,
            "requires_auth": False,
        },
        # Protein / Pathway Databases
        {
            "id": "string",
            "name": "STRING",
            "description": "Database of known and predicted protein-protein interactions",
            "category": "Protein / Pathway Databases",
            "param_type": "gene",
            "url_template": "https://string-db.org/network/homo-sapiens/${gene}",
            "tags": ["protein", "interactions", "networks"],
            "is_active": True,
            "requires_auth": False,
        },
        {
            "id": "reactome",
            "name": "Reactome",
            "description": "Free, open-source, curated and peer-reviewed pathway database",
            "category": "Protein / Pathway Databases",
            "param_type": "gene_and_term",
            "url_template": "https://reactome.org/content/query?q=(${gene})%20AND%20(${term})&species=Homo+sapiens&species=Entries+without+species&cluster=true",
            "tags": ["pathways", "biological", "processes"],
            "is_active": True,
            "requires_auth": False,
        },
        # Electronic Health Records (EHRs)
        {
            "id": "omop",
            "name": "OMOP",
            "description": "The Observational Medical Outcomes Partnership (OMOP) Common Data Model (CDM)",
            "category": "Electronic Health Records (EHRs)",
            "param_type": "none",
            "url_template": "https://ohdsi.github.io/CommonDataModel/",
            "tags": ["ehr", "observational", "outcomes"],
            "is_active": True,
            "requires_auth": False,
        },
        {
            "id": "trinetx",
            "name": "TriNetX",
            "description": "Global health research network providing access to de-identified clinical data",
            "category": "Electronic Health Records (EHRs)",
            "param_type": "none",
            "url_template": "https://trinetx.com/",
            "tags": ["clinical", "research", "network"],
            "is_active": True,
            "requires_auth": False,
        },
        # Rare Disease Registries
        {
            "id": "orphanet",
            "name": "Orphanet",
            "description": "European database of rare diseases and orphan drugs",
            "category": "Rare Disease Registries",
            "param_type": "gene",
            "url_template": "https://www.orpha.net/consor/cgi-bin/Disease_Search_Simple.php?lng=EN&Disease_Disease_Search_Simple_dataname=${gene}",
            "tags": ["rare", "diseases", "orphan"],
            "is_active": True,
            "requires_auth": False,
        },
        # Clinical Trial Databases
        {
            "id": "clinicaltrials",
            "name": "ClinicalTrials.gov",
            "description": "Comprehensive database of clinical trials being conducted around the world",
            "category": "Clinical Trial Databases",
            "param_type": "gene_and_term",
            "url_template": "https://clinicaltrials.gov/search?cond=${term}&term=${gene}",
            "tags": ["clinical", "trials", "research"],
            "is_active": True,
            "requires_auth": False,
        },
        # Phenotype Ontologies & Databases
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
            "id": "monarch",
            "name": "Monarch Initiative",
            "description": "Integrates and analyzes data to improve the diagnosis and treatment of rare diseases",
            "category": "Phenotype Ontologies & Databases",
            "param_type": "gene",
            "url_template": "https://monarchinitiative.org/search/${gene}",
            "tags": ["phenotypes", "diagnosis", "treatment"],
            "is_active": True,
            "requires_auth": False,
        },
        # Scientific Literature
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
            "id": "biorxiv",
            "name": "bioRxiv",
            "description": "Free online service for the distribution of preprints in the life sciences",
            "category": "Scientific Literature",
            "param_type": "gene_and_term",
            "url_template": "https://www.biorxiv.org/search/${gene}%20${term}",
            "tags": ["preprints", "literature", "biology"],
            "is_active": True,
            "requires_auth": False,
        },
        # Knowledge Graphs / Integrated Platforms
        {
            "id": "opentargets",
            "name": "Open Targets",
            "description": "Generates evidence on the validity of therapeutic targets",
            "category": "Knowledge Graphs / Integrated Platforms",
            "param_type": "gene",
            "url_template": "https://platform.opentargets.org/target/${gene}",
            "tags": ["targets", "therapeutics", "evidence"],
            "is_active": True,
            "requires_auth": False,
        },
        # Patient Advocacy Registries
        {
            "id": "nord",
            "name": "NORD",
            "description": "National Organization for Rare Disorders patient advocacy organization",
            "category": "Patient Advocacy Registries",
            "param_type": "term",
            "url_template": "https://rarediseases.org/for-patients-and-families/information-resources/rare-disease-information/?search=${term}",
            "tags": ["rare", "diseases", "advocacy"],
            "is_active": True,
            "requires_auth": False,
        },
        # Social Media & Forums (Ethical Use)
        {
            "id": "reddit",
            "name": "Reddit",
            "description": "Social media platform organized into communities, or 'subreddits'",
            "category": "Social Media & Forums (Ethical Use)",
            "param_type": "gene_and_term",
            "url_template": "https://www.reddit.com/search/?q=${gene}%20${term}",
            "tags": ["social", "communities", "discussion"],
            "is_active": True,
            "requires_auth": False,
        },
        {
            "id": "patientslikeme",
            "name": "PatientsLikeMe",
            "description": "Social network for patients dedicated to helping people with rare diseases",
            "category": "Social Media & Forums (Ethical Use)",
            "param_type": "none",
            "url_template": "https://www.patientslikeme.com/",
            "tags": ["patients", "social", "network"],
            "is_active": True,
            "requires_auth": False,
        },
        # Cohort Studies
        {
            "id": "ukbiobank",
            "name": "UK Biobank",
            "description": "Large-scale biomedical database and research resource",
            "category": "Cohort Studies",
            "param_type": "gene",
            "url_template": "https://biobank.ctsu.ox.ac.uk/crystal/label.cgi?id=${gene}",
            "tags": ["cohort", "biomedical", "database"],
            "is_active": True,
            "requires_auth": False,
        },
        {
            "id": "finngen",
            "name": "FinnGen",
            "description": "Large-scale research project to improve human health through genetic research",
            "category": "Cohort Studies",
            "param_type": "gene",
            "url_template": "https://r9.finngen.fi/gene/${gene}",
            "tags": ["genetics", "health", "research"],
            "is_active": True,
            "requires_auth": False,
        },
        # Transcriptomics / RNA-seq
        {
            "id": "geo",
            "name": "GEO",
            "description": "Gene Expression Omnibus is a public repository of high-throughput gene expression data",
            "category": "Transcriptomics / RNA-seq",
            "param_type": "gene_and_term",
            "url_template": "https://www.ncbi.nlm.nih.gov/gds/?term=(${gene})+AND+(${term})",
            "tags": ["expression", "transcriptomics", "sequencing"],
            "is_active": True,
            "requires_auth": False,
        },
        # Single-Cell Data
        {
            "id": "hca",
            "name": "Human Cell Atlas",
            "description": "International collaborative effort to create a comprehensive reference map of all human cells",
            "category": "Single-Cell Data",
            "param_type": "none",
            "url_template": "https://www.humancellatlas.org/data-portals/",
            "tags": ["single-cell", "atlas", "cells"],
            "is_active": True,
            "requires_auth": False,
        },
        # Ontologies & Terminologies
        {
            "id": "omim",
            "name": "OMIM",
            "description": "Online Mendelian Inheritance in Man: A comprehensive database of human genes and genetic disorders",
            "category": "Ontologies & Terminologies",
            "param_type": "gene",
            "url_template": "https://www.omim.org/entry?search=${gene}",
            "tags": ["genetic", "disorders", "inheritance"],
            "is_active": True,
            "requires_auth": False,
        },
        # Data Repositories & Storage
        {
            "id": "dbgap",
            "name": "dbGaP",
            "description": "The database of Genotypes and Phenotypes (dbGaP)",
            "category": "Data Repositories & Storage",
            "param_type": "gene_and_term",
            "url_template": "https://www.ncbi.nlm.nih.gov/gap/?term=(${gene})+AND+(${term})",
            "tags": ["genotypes", "phenotypes", "repository"],
            "is_active": True,
            "requires_auth": False,
        },
        # Consortia & Initiatives
        {
            "id": "clingen",
            "name": "ClinGen",
            "description": "NIH-funded resource defining the clinical relevance of genes and variants",
            "category": "Consortia & Initiatives",
            "param_type": "gene",
            "url_template": "https://search.clinicalgenome.org/kb/genes/curations?search=${gene}",
            "tags": ["clinical", "relevance", "variants"],
            "is_active": True,
            "requires_auth": False,
        },
        {
            "id": "ga4gh",
            "name": "GA4GH",
            "description": "Global Alliance for Genomics and Health: Advancing human health through genomic data sharing",
            "category": "Consortia & Initiatives",
            "param_type": "none",
            "url_template": "https://www.ga4gh.org/",
            "tags": ["genomics", "health", "alliance"],
            "is_active": True,
            "requires_auth": False,
        },
        # Integrative Knowledge Graphs
        {
            "id": "neo4j",
            "name": "Neo4j (Graph Data Science)",
            "description": "Graph database platform, often used to build and query integrative knowledge graphs",
            "category": "Integrative Knowledge Graphs",
            "param_type": "none",
            "url_template": "https://neo4j.com/product/graph-data-science/",
            "tags": ["graph", "database", "knowledge"],
            "is_active": True,
            "requires_auth": False,
        },
        # AI Predictive Models
        {
            "id": "variantformer",
            "name": "VariantFormer",
            "description": "State-of-the-art AI model for predicting variant pathogenicity and functional impact",
            "category": "AI Predictive Models",
            "param_type": "api",
            "api_endpoint": "/api/variantformer",
            "tags": ["ai", "prediction", "pathogenicity"],
            "is_active": True,
            "requires_auth": False,
        },
        {
            "id": "alphagenome",
            "name": "AlphaGenome",
            "description": "Advanced model for analyzing genomic sequences and predicting functional outcomes",
            "category": "AI Predictive Models",
            "param_type": "api",
            "api_endpoint": "/api/alphagenome",
            "tags": ["ai", "genomics", "functional"],
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

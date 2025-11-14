"""Database seeding helpers for MED13 Resource Library."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from secrets import token_urlsafe
from typing import TYPE_CHECKING, TypedDict
from uuid import UUID

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from src.domain.entities.user import UserRole, UserStatus
from src.infrastructure.security.password_hasher import PasswordHasher
from src.models.database.data_discovery import SourceCatalogEntryModel
from src.models.database.research_space import (
    MembershipRoleEnum,
    ResearchSpaceMembershipModel,
    ResearchSpaceModel,
    SpaceStatusEnum,
)
from src.models.database.user import UserModel


class SourceCatalogEntrySeed(TypedDict, total=False):
    """Typed seed data for source catalog entries."""

    id: str
    name: str
    description: str
    category: str
    param_type: str
    url_template: str
    api_endpoint: str
    tags: list[str]
    is_active: bool
    requires_auth: bool


logger = logging.getLogger(__name__)

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
SYSTEM_USER_ID_STR = str(SYSTEM_USER_ID)
SYSTEM_USER_EMAIL = "system@med13.org"
SYSTEM_USER_USERNAME = "med13-system"
SYSTEM_USER_PASSWORD = os.getenv("MED13_SYSTEM_USER_PASSWORD")
SYSTEM_USER_FULL_NAME = "MED13 System Automation"

DEFAULT_RESEARCH_SPACE_ID = UUID("560e9e0b-13bd-4337-a55d-2d3f650e451f")
DEFAULT_RESEARCH_SPACE_ID_STR = str(DEFAULT_RESEARCH_SPACE_ID)
DEFAULT_RESEARCH_SPACE_SLUG = "med13-core-space"
DEFAULT_RESEARCH_SPACE_NAME = "MED13 Core Research Space"


def _ensure_system_user(session: Session) -> UserModel:
    """Ensure the deterministic system automation user exists."""
    password_hasher = PasswordHasher()

    system_user = (
        session.query(UserModel)
        .filter(UserModel.id == SYSTEM_USER_ID_STR)
        .one_or_none()
    )
    if system_user:
        return system_user

    # Attempt lookup by email (in case existing DB has user without deterministic ID)
    existing_by_email = (
        session.query(UserModel)
        .filter(UserModel.email == SYSTEM_USER_EMAIL)
        .one_or_none()
    )
    if existing_by_email:
        logger.info(
            "Aligning existing system user %s to deterministic ID %s",
            SYSTEM_USER_EMAIL,
            SYSTEM_USER_ID,
        )
        existing_by_email.id = SYSTEM_USER_ID_STR
        session.flush()
        return existing_by_email

    password_secret = SYSTEM_USER_PASSWORD or token_urlsafe(32)

    system_user = UserModel(
        id=SYSTEM_USER_ID_STR,
        email=SYSTEM_USER_EMAIL,
        username=SYSTEM_USER_USERNAME,
        full_name=SYSTEM_USER_FULL_NAME,
        hashed_password=password_hasher.hash_password(password_secret),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    session.add(system_user)
    session.flush()
    logger.info("Seeded system automation user (%s)", SYSTEM_USER_EMAIL)
    return system_user


def ensure_default_research_space_seeded(session: Session) -> None:
    """Ensure the canonical MED13 research space exists with deterministic IDs."""
    owner = _ensure_system_user(session)

    space = (
        session.query(ResearchSpaceModel)
        .filter(ResearchSpaceModel.id == DEFAULT_RESEARCH_SPACE_ID_STR)
        .one_or_none()
    )

    if not space:
        space = ResearchSpaceModel(
            id=DEFAULT_RESEARCH_SPACE_ID_STR,
            slug=DEFAULT_RESEARCH_SPACE_SLUG,
            name=DEFAULT_RESEARCH_SPACE_NAME,
            description=(
                "Primary workspace for MED13 research teams. Used as the default "
                "context when creating demo sessions or data sources."
            ),
            owner_id=owner.id,
            status=SpaceStatusEnum.ACTIVE,
            settings={
                "visibility": "private",
                "data_retention_days": 90,
                "auto_archive_days": 30,
            },
            tags=["med13", "core", "default"],
        )
        session.add(space)
        session.flush()
        logger.info(
            "Seeded default research space '%s' (%s)",
            DEFAULT_RESEARCH_SPACE_NAME,
            DEFAULT_RESEARCH_SPACE_ID,
        )

    membership = (
        session.query(ResearchSpaceMembershipModel)
        .filter(
            ResearchSpaceMembershipModel.space_id == DEFAULT_RESEARCH_SPACE_ID_STR,
            ResearchSpaceMembershipModel.user_id == owner.id,
        )
        .one_or_none()
    )

    if not membership:
        membership = ResearchSpaceMembershipModel(
            space_id=DEFAULT_RESEARCH_SPACE_ID_STR,
            user_id=owner.id,
            role=MembershipRoleEnum.OWNER,
            invited_by=owner.id,
            invited_at=datetime.now(UTC),
            joined_at=datetime.now(UTC),
            is_active=True,
        )
        session.add(membership)
        logger.info(
            "Linked system user %s to default research space as owner",
            SYSTEM_USER_EMAIL,
        )


SOURCE_CATALOG_ENTRIES: list[SourceCatalogEntrySeed] = [
    {
        "id": "clinvar",
        "name": "ClinVar",
        "description": (
            "Public archive connecting human genetic variants to phenotypes with "
            "supporting evidence and clinical interpretations."
        ),
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
        "description": (
            "Aggregated allele frequency data from large-scale sequencing projects "
            "to contextualize variant rarity."
        ),
        "category": "Genomic Variant Databases",
        "param_type": "gene",
        "url_template": "https://gnomad.broadinstitute.org/gene/${gene}?dataset=gnomad_r4",
        "tags": ["variants", "population", "frequency"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "expression_atlas",
        "name": "Expression Atlas",
        "description": (
            "EBI Expression Atlas profiling gene expression across tissues, "
            "conditions, and perturbations."
        ),
        "category": "Gene Expression & Functional Genomics",
        "param_type": "gene",
        "url_template": "https://www.ebi.ac.uk/gxa/genes/${gene}",
        "tags": ["expression", "functional", "ebi"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "mgi",
        "name": "MGI (Mouse Genome Informatics)",
        "description": (
            "Comprehensive genetics resource for laboratory mouse models and "
            "functional annotations."
        ),
        "category": "Model Organism Databases",
        "param_type": "gene",
        "url_template": "https://www.informatics.jax.org/searchtool/Search?query=${gene}",
        "tags": ["mouse", "model", "genetics"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "string",
        "name": "STRING",
        "description": (
            "Database of known and predicted protein-protein interactions with "
            "network visualization."
        ),
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
        "description": (
            "Peer-reviewed pathway database describing biological processes and "
            "molecular interactions."
        ),
        "category": "Protein / Pathway Databases",
        "param_type": "gene_and_term",
        "url_template": (
            "https://reactome.org/content/query?q=(${gene})%20AND%20(${term})&species=Homo+sapiens"
        ),
        "tags": ["pathways", "biological", "processes"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "omop",
        "name": "OMOP CDM",
        "description": (
            "Observational Medical Outcomes Partnership common data model for "
            "harmonizing EHR datasets."
        ),
        "category": "Electronic Health Records (EHRs)",
        "param_type": "none",
        "url_template": "https://ohdsi.github.io/CommonDataModel/",
        "tags": ["ehr", "observational", "standards"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "trinetx",
        "name": "TriNetX",
        "description": (
            "Global health research network providing federated queries across "
            "de-identified clinical records."
        ),
        "category": "Electronic Health Records (EHRs)",
        "param_type": "none",
        "url_template": "https://trinetx.com/",
        "tags": ["clinical", "network", "real-world-data"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "orphanet",
        "name": "Orphanet",
        "description": "European database focused on rare diseases and orphan drugs.",
        "category": "Rare Disease Registries",
        "param_type": "gene",
        "url_template": (
            "https://www.orpha.net/consor/cgi-bin/Disease_Search_Simple.php?Disease_Disease_Search_Simple_dataname=${gene}"
        ),
        "tags": ["rare", "diseases", "registry"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "clinicaltrials",
        "name": "ClinicalTrials.gov",
        "description": "Registry of clinical trials with condition and gene filters.",
        "category": "Clinical Trial Databases",
        "param_type": "gene_and_term",
        "url_template": "https://clinicaltrials.gov/search?cond=${term}&term=${gene}",
        "tags": ["clinical", "trials", "research"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "hpo",
        "name": "Human Phenotype Ontology",
        "description": "Standardized vocabulary describing human phenotypic abnormalities.",
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
        "description": (
            "Integrates genotype-phenotype data for improved diagnosis of rare "
            "diseases."
        ),
        "category": "Phenotype Ontologies & Databases",
        "param_type": "gene",
        "url_template": "https://monarchinitiative.org/search/${gene}",
        "tags": ["phenotypes", "diagnosis", "integration"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "pubmed",
        "name": "PubMed",
        "description": "Biomedical literature database from the National Library of Medicine.",
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
        "description": "Life sciences preprint server for rapid sharing of research findings.",
        "category": "Scientific Literature",
        "param_type": "gene_and_term",
        "url_template": "https://www.biorxiv.org/search/${gene}%20${term}",
        "tags": ["preprints", "literature", "biology"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "opentargets",
        "name": "Open Targets",
        "description": "Knowledge graph linking genes, diseases, and therapeutics.",
        "category": "Knowledge Graphs / Integrated Platforms",
        "param_type": "gene",
        "url_template": "https://platform.opentargets.org/target/${gene}",
        "tags": ["targets", "therapeutics", "evidence"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "pubtator",
        "name": "PubTator",
        "description": "NCBI text-mined annotations linking genes, diseases, and chemicals.",
        "category": "Text-Mined Databases",
        "param_type": "gene_and_term",
        "url_template": "https://www.ncbi.nlm.nih.gov/research/pubtator/?query=${gene}%20${term}",
        "tags": ["text-mining", "annotations", "literature"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "ukbiobank",
        "name": "UK Biobank",
        "description": "Large prospective cohort with genomic and longitudinal health data.",
        "category": "Cohort Studies",
        "param_type": "none",
        "url_template": "https://www.ukbiobank.ac.uk/",
        "tags": ["cohort", "population", "longitudinal"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "finngen",
        "name": "FinnGen",
        "description": "Nationwide Finnish biobank program linking genetic and registry data.",
        "category": "Cohort Studies",
        "param_type": "none",
        "url_template": "https://www.finngen.fi/en",
        "tags": ["cohort", "genomics", "finland"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "cdc_wonder",
        "name": "CDC WONDER",
        "description": "Public health statistics portal for mortality, births, and surveillance data.",
        "category": "Public Health Databases",
        "param_type": "term",
        "url_template": "https://wonder.cdc.gov/?query=${term}",
        "tags": ["public-health", "epidemiology", "surveillance"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "marketscan",
        "name": "IBM MarketScan",
        "description": "Commercial insurance claims database for longitudinal medical economics.",
        "category": "Insurance Claims / Billing Data",
        "param_type": "none",
        "url_template": "https://www.ibm.com/products/marketscan-research-databases",
        "tags": ["claims", "billing", "economics"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "nord",
        "name": "NORD Rare Disease Database",
        "description": "Patient advocacy organization aggregating rare disease knowledge and services.",
        "category": "Patient Advocacy Registries",
        "param_type": "term",
        "url_template": "https://rarediseases.org/?s=${term}",
        "tags": ["patients", "advocacy", "rare"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "reddit",
        "name": "Reddit Research Communities",
        "description": (
            "Ethically monitored public forums discussing phenotypes, lived "
            "experiences, and emerging evidence."
        ),
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
        "description": "Patient-reported outcomes platform with symptom and treatment tracking.",
        "category": "Surveys / PRO Data",
        "param_type": "term",
        "url_template": "https://www.patientslikeme.com/search?q=${term}",
        "tags": ["pro", "outcomes", "patient-reported"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "gtex",
        "name": "GTEx Portal",
        "description": "Expression quantitative trait and RNA-seq profiles across human tissues.",
        "category": "Transcriptomics / RNA-seq",
        "param_type": "gene",
        "url_template": "https://www.gtexportal.org/home/gene/${gene}",
        "tags": ["transcriptomics", "expression", "tissues"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "geo",
        "name": "NCBI GEO",
        "description": "Gene Expression Omnibus repository of functional genomics datasets.",
        "category": "Transcriptomics / RNA-seq",
        "param_type": "gene",
        "url_template": "https://www.ncbi.nlm.nih.gov/gds/?term=${gene}",
        "tags": ["transcriptomics", "datasets", "ncbi"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "roadmap_epigenomics",
        "name": "Roadmap Epigenomics",
        "description": "Reference epigenomic maps highlighting methylation and chromatin states.",
        "category": "Epigenomics / Methylation",
        "param_type": "gene",
        "url_template": "https://egg2.wustl.edu/roadmap/web_portal/chr_region/${gene}.html",
        "tags": ["epigenomics", "methylation", "chromatin"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "hpa",
        "name": "Human Protein Atlas",
        "description": "Protein expression and localization across tissues and cell types.",
        "category": "Proteomics / Metabolomics",
        "param_type": "gene",
        "url_template": "https://www.proteinatlas.org/search/${gene}",
        "tags": ["proteomics", "expression", "tissues"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "hca",
        "name": "Human Cell Atlas",
        "description": "Single-cell atlases describing cell types and states in healthy tissues.",
        "category": "Single-Cell Data",
        "param_type": "gene",
        "url_template": "https://www.humancellatlas.org/explore?gene=${gene}",
        "tags": ["single-cell", "atlas", "tissues"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "omim",
        "name": "OMIM",
        "description": "Online Mendelian Inheritance in Man catalogue of human genes and phenotypes.",
        "category": "Ontologies & Terminologies",
        "param_type": "gene",
        "url_template": "https://www.omim.org/search/?index=entry&search=${gene}",
        "tags": ["inheritance", "catalogue", "gene"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "dbgap",
        "name": "dbGaP",
        "description": "NIH controlled-access repository for genotype and phenotype datasets.",
        "category": "Data Repositories & Storage",
        "param_type": "none",
        "url_template": "https://www.ncbi.nlm.nih.gov/gap/",
        "tags": ["repository", "genotype", "phenotype"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "clinvar_benchmark",
        "name": "ClinVar Pathogenicity Benchmark",
        "description": "Curated benchmark set for training and evaluating variant classifiers.",
        "category": "AI / ML Benchmark Datasets",
        "param_type": "none",
        "url_template": "https://github.com/genomicsAI/clinvar-benchmark",
        "tags": ["benchmark", "machine-learning", "variants"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "stjude_cloud",
        "name": "St. Jude Cloud",
        "description": "Institutional repository for pediatric cancer genomics and analysis apps.",
        "category": "Institutional Repositories",
        "param_type": "none",
        "url_template": "https://www.stjude.cloud/",
        "tags": ["institutional", "pediatric", "genomics"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "clingen",
        "name": "ClinGen",
        "description": "NIH-funded consortium curating clinically relevant genes and variants.",
        "category": "Consortia & Initiatives",
        "param_type": "none",
        "url_template": "https://clinicalgenome.org/",
        "tags": ["consortium", "curation", "clinical"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "ga4gh",
        "name": "GA4GH",
        "description": "Global Alliance for Genomics and Health standards and APIs.",
        "category": "Consortia & Initiatives",
        "param_type": "none",
        "url_template": "https://www.ga4gh.org/",
        "tags": ["standards", "interoperability", "consortium"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "elixir",
        "name": "ELIXIR",
        "description": "European life-science data hub connecting cross-disciplinary resources.",
        "category": "Cross-disciplinary Data Hubs",
        "param_type": "none",
        "url_template": "https://elixir-europe.org/services",
        "tags": ["infrastructure", "data-sharing", "europe"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "physiome",
        "name": "Physiome Project",
        "description": "Multi-scale computational models capturing organ and system physiology.",
        "category": "Causal Models / Simulations",
        "param_type": "none",
        "url_template": "https://physiomeproject.org/models",
        "tags": ["simulation", "multiscale", "physiology"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "neo4j",
        "name": "Neo4j Graph Data Science",
        "description": "Graph algorithms and pipelines for integrative biomedical knowledge graphs.",
        "category": "Integrative Knowledge Graphs",
        "param_type": "api",
        "url_template": "https://graphdatascience.ninja/?q=${gene}",
        "tags": ["graph", "analytics", "integration"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "feast_feature_store",
        "name": "Feast Feature Store",
        "description": "Open-source computed feature store for serving ML-ready biomedical features.",
        "category": "Computed Feature Stores",
        "param_type": "none",
        "url_template": "https://feast.dev/",
        "tags": ["features", "mlops", "serving"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "variantformer",
        "name": "VariantFormer",
        "description": "Transformer-based AI model predicting variant pathogenicity and impact.",
        "category": "AI Predictive Models",
        "param_type": "api",
        "api_endpoint": "/api/variantformer",
        "tags": ["ai", "prediction", "variants"],
        "is_active": True,
        "requires_auth": False,
    },
    {
        "id": "alphagenome",
        "name": "AlphaGenome",
        "description": "Advanced AI platform modeling genome function and regulatory outcomes.",
        "category": "AI Predictive Models",
        "param_type": "api",
        "api_endpoint": "/api/alphagenome",
        "tags": ["ai", "genomics", "functional"],
        "is_active": True,
        "requires_auth": False,
    },
]


def ensure_source_catalog_seeded(session: Session) -> None:
    """Ensure the source catalog has up-to-date demo entries."""
    existing_entries = {
        entry.id: entry for entry in session.query(SourceCatalogEntryModel).all()
    }

    inserted = 0
    updated = 0

    for entry_data in SOURCE_CATALOG_ENTRIES:
        entry_id = entry_data["id"]
        model = existing_entries.get(entry_id)
        if model:
            for field, value in entry_data.items():
                setattr(model, field, value)
            updated += 1
        else:
            session.add(SourceCatalogEntryModel(**entry_data))
            inserted += 1

    logger.info(
        "Ensured %s source catalog entries (inserted=%s, updated=%s)",
        len(SOURCE_CATALOG_ENTRIES),
        inserted,
        updated,
    )

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

from src.application import container as container_module
from src.database.session import SessionLocal, engine
from src.domain.entities.user import UserRole, UserStatus
from src.infrastructure.security.password_hasher import PasswordHasher
from src.main import create_app
from src.middleware import jwt_auth as jwt_auth_module
from src.models.database import (
    Base,
    EvidenceModel,
    GeneModel,
    PhenotypeModel,
    VariantModel,
)
from src.models.database.audit import AuditLog
from src.models.database.review import ReviewRecord
from src.models.database.user import UserModel
from tests.test_types.fixtures import (
    create_test_gene,
    create_test_phenotype,
    create_test_variant,
)

TEST_ADMIN_PASSWORD = os.getenv("MED13_E2E_ADMIN_PASSWORD", "StrongPass!123")

pytestmark = pytest.mark.asyncio(loop_scope="module")


async def _reset_container_services() -> None:
    """Ensure async services are rebuilt with the current event loop."""
    container = container_module.container
    container._authentication_service = None
    container._authentication_service_loop = None
    container._authorization_service = None
    container._authorization_service_loop = None
    container._user_management_service = None
    container._user_management_service_loop = None
    await container.engine.dispose()
    jwt_auth_module.SKIP_JWT_VALIDATION = True


def _reset_tables(session: SessionLocal) -> None:
    """Clear tables touched by this test to avoid cross-test leakage."""
    for model in (
        AuditLog,
        ReviewRecord,
        EvidenceModel,
        PhenotypeModel,
        VariantModel,
        GeneModel,
    ):
        session.query(model).delete()
    session.commit()


def _seed_curation_context() -> None:
    """Create the gene/variant/phenotype/evidence records needed by the test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        _reset_tables(session)
        gene_data = create_test_gene(gene_id="GENE-E2E", symbol="MED13E2E")
        gene = GeneModel(
            gene_id=gene_data.gene_id,
            symbol=gene_data.symbol,
            name=gene_data.name,
            description=gene_data.description,
            gene_type=gene_data.gene_type,
            chromosome=gene_data.chromosome,
            start_position=gene_data.start_position,
            end_position=gene_data.end_position,
            ensembl_id=gene_data.ensembl_id,
            ncbi_gene_id=gene_data.ncbi_gene_id,
            uniprot_id=gene_data.uniprot_id,
        )
        session.add(gene)
        session.flush()

        variant_data = create_test_variant(
            variant_id="VCV-E2E-1",
            clinvar_id="VCV9999999",
            gene_database_id=gene.id,
            gene_identifier=gene.symbol,
        )
        variant = VariantModel(
            gene_id=gene.id,
            variant_id=variant_data.variant_id,
            clinvar_id=variant_data.clinvar_id,
            chromosome=variant_data.chromosome,
            position=variant_data.position,
            reference_allele=variant_data.reference_allele,
            alternate_allele=variant_data.alternate_allele,
            hgvs_genomic=variant_data.hgvs_genomic,
            hgvs_protein=variant_data.hgvs_protein,
            hgvs_cdna=variant_data.hgvs_cdna,
            variant_type=variant_data.variant_type,
            clinical_significance=variant_data.clinical_significance,
            condition=variant_data.condition,
            review_status=variant_data.review_status,
            allele_frequency=variant_data.allele_frequency,
            gnomad_af=variant_data.gnomad_af,
        )
        session.add(variant)
        session.flush()

        phenotype_data = create_test_phenotype(
            hpo_id="HP:9999999",
            name="Test Phenotype",
            definition="Synthetic phenotype for curator tests",
        )
        phenotype = PhenotypeModel(
            hpo_id=phenotype_data.hpo_id,
            hpo_term=phenotype_data.name,
            name=phenotype_data.name,
            definition=phenotype_data.definition,
            synonyms="[]",
            category="other",
            frequency_in_med13="frequent",
        )
        session.add(phenotype)
        session.flush()

        evidence = EvidenceModel(
            variant_id=variant.id,
            phenotype_id=phenotype.id,
            evidence_level="strong",
            evidence_type="clinical_report",
            description="Clinical report linking variant to phenotype.",
            summary="Primary case study",
            confidence_score=0.82,
            reviewed=True,
        )
        session.add(evidence)

        review_record = ReviewRecord(
            entity_type="variant",
            entity_id=variant.variant_id,
            status="pending",
            priority="high",
            quality_score=0.9,
            issues=1,
        )
        session.add(review_record)

        audit_log = AuditLog(
            action="comment",
            entity_type="variant",
            entity_id=variant.variant_id,
            user="integration-tester",
            details="Initial audit note",
        )
        session.add(audit_log)

        session.commit()
    finally:
        session.close()


async def _get_auth_headers(client: AsyncClient) -> dict[str, str]:
    email, password = _create_admin_user()
    resp = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_curation_detail_endpoint_returns_clinical_context() -> None:
    """Ensure curator detail endpoint returns phenotypes, evidence, and audit summary."""
    _seed_curation_context()

    await _reset_container_services()
    jwt_auth_module.SKIP_JWT_VALIDATION = True
    try:
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            headers = await _get_auth_headers(client)
            response = await client.get(
                "/curation/variants/VCV-E2E-1",
                headers=headers,
            )

            assert response.status_code == 200, response.json()
    finally:
        jwt_auth_module.SKIP_JWT_VALIDATION = False
    payload = response.json()

    assert payload["variant"]["variant_id"] == "VCV-E2E-1"
    assert payload["variant"]["clinvar_id"] == "VCV9999999"

    phenotypes = payload.get("phenotypes", [])
    assert len(phenotypes) == 1
    assert phenotypes[0]["hpo_id"] == "HP:9999999"
    assert phenotypes[0]["name"] == "Test Phenotype"

    evidence_items = payload.get("evidence", [])
    assert evidence_items, "Expected evidence records to be returned"
    assert evidence_items[0]["evidence_level"] == "strong"

    audit = payload.get("audit")
    assert audit is not None
    assert audit["total_annotations"] >= 1
    assert any("Status" in action for action in audit["pending_actions"])


def _create_admin_user(
    email: str = "admin-e2e@med13.org",
    password: str | None = None,
) -> tuple[str, str]:
    resolved_password = password or TEST_ADMIN_PASSWORD
    session = SessionLocal()
    try:
        session.query(UserModel).filter(UserModel.email == email).delete()
        admin = UserModel(
            email=email,
            username="admin-e2e",
            full_name="E2E Admin",
            hashed_password=PasswordHasher().hash_password(resolved_password),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            email_verified=True,
        )
        session.add(admin)
        session.commit()
    finally:
        session.close()
    return email, resolved_password

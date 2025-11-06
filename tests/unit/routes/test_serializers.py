from datetime import UTC, datetime

from src.domain.entities.evidence import Evidence, EvidenceType
from src.domain.entities.gene import Gene, GeneType
from src.domain.entities.variant import (
    EvidenceSummary,
    Variant,
    VariantSummary,
    VariantType,
)
from src.domain.value_objects.confidence import Confidence, EvidenceLevel
from src.domain.value_objects.identifiers import GeneIdentifier, VariantIdentifier
from src.routes.serializers import (
    build_activity_feed_item,
    build_dashboard_summary,
    serialize_evidence,
    serialize_evidence_brief,
    serialize_gene,
    serialize_variant,
)

EXPECTED_CONFIDENCE = 0.75
TOTAL_ITEMS_EXPECTED = 15
GENE_COUNT_EXPECTED = 10


def build_variant() -> Variant:
    identifier = VariantIdentifier(variant_id="chr1:123:A>T", clinvar_id="VCV1")
    gene_identifier = GeneIdentifier(gene_id="GENE1", symbol="GENE1")
    variant = Variant(
        identifier=identifier,
        chromosome="chr1",
        position=123,
        reference_allele="A",
        alternate_allele="T",
        variant_type=VariantType.SNV,
        clinical_significance="pathogenic",
        gene_identifier=gene_identifier,
        allele_frequency=0.1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 2, tzinfo=UTC),
    )
    variant.add_evidence_summary(
        EvidenceSummary(
            evidence_id=1,
            evidence_level="strong",
            evidence_type="clinical_report",
            description="Clinically validated",
            reviewed=True,
        ),
    )
    return variant


def test_serialize_variant_includes_summary() -> None:
    variant = build_variant()
    payload = serialize_variant(variant)

    assert payload["variant_id"] == "chr1:123:A>T"
    assert payload["evidence_count"] == 1
    assert payload["evidence"][0]["evidence_level"] == "strong"


def test_serialize_gene_includes_optional_sections() -> None:
    gene_identifier = GeneIdentifier(gene_id="GENE1", symbol="GENE1")
    gene = Gene(
        identifier=gene_identifier,
        gene_type=GeneType.PROTEIN_CODING,
        name="Gene 1",
        description="Gene description",
        chromosome="chr1",
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 2, tzinfo=UTC),
    )

    variant_summary = VariantSummary(
        variant_id="chr1:123:A>T",
        clinvar_id="VCV1",
        chromosome="chr1",
        position=123,
        clinical_significance="pathogenic",
    )

    phenotypes = [{"phenotype_id": "HP:0000001", "name": "Phenotype"}]

    payload = serialize_gene(
        gene,
        include_variants=True,
        variants=[variant_summary],
        include_phenotypes=True,
        phenotypes=phenotypes,
    )

    assert payload["variant_count"] == 1
    assert payload["variants"][0]["variant_id"] == "chr1:123:A>T"
    assert payload["phenotypes"] == phenotypes


def test_serialize_evidence_brief() -> None:
    summary = EvidenceSummary(
        evidence_id=5,
        evidence_level="moderate",
        evidence_type="literature_review",
        description="Published case study",
        reviewed=False,
    )
    payload = serialize_evidence_brief(summary)
    assert payload == {
        "id": 5,
        "evidence_level": "moderate",
        "evidence_type": "literature_review",
        "description": "Published case study",
        "reviewed": False,
    }


def test_build_dashboard_summary() -> None:
    entity_counts = {"genes": 10, "variants": 5}
    summary = build_dashboard_summary(
        entity_counts,
        pending_count=2,
        approved_count=10,
        rejected_count=1,
    )

    assert summary["total_items"] == TOTAL_ITEMS_EXPECTED
    assert summary["entity_counts"]["genes"] == GENE_COUNT_EXPECTED


def test_serialize_full_evidence() -> None:
    confidence = Confidence.from_score(EXPECTED_CONFIDENCE, peer_reviewed=True)
    evidence = Evidence(
        variant_id=1,
        phenotype_id=2,
        description="Functional assay",
        evidence_level=EvidenceLevel.MODERATE,
        evidence_type=EvidenceType.FUNCTIONAL_STUDY,
        confidence=confidence,
        reviewed=True,
        review_date=datetime(2024, 1, 3, tzinfo=UTC).date(),
        created_at=datetime(2024, 1, 4, tzinfo=UTC),
        updated_at=datetime(2024, 1, 5, tzinfo=UTC),
    )

    payload = serialize_evidence(evidence)
    assert payload["confidence_score"] == EXPECTED_CONFIDENCE
    assert payload["review_date"] == evidence.review_date.isoformat()


def test_build_activity_feed_item() -> None:
    now = datetime(2024, 1, 1, tzinfo=UTC)
    item = build_activity_feed_item(
        "Gene approved",
        category="success",
        icon="mdi:check",
        timestamp=now,
    )
    assert item["category"] == "success"
    assert item["created_at"] == now.isoformat()

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Optional

from src.domain.value_objects.identifiers import GeneIdentifier, VariantIdentifier


class VariantType:
    SNV = "snv"
    INDEL = "indel"
    CNV = "cnv"
    STRUCTURAL = "structural"
    UNKNOWN = "unknown"

    _VALID_TYPES = {SNV, INDEL, CNV, STRUCTURAL, UNKNOWN}

    @classmethod
    def validate(cls, value: str) -> str:
        normalized = value or cls.UNKNOWN
        if normalized not in cls._VALID_TYPES:
            raise ValueError(f"Unsupported variant_type '{value}'")
        return normalized


class ClinicalSignificance:
    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    UNCERTAIN_SIGNIFICANCE = "uncertain_significance"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"
    CONFLICTING = "conflicting"
    NOT_PROVIDED = "not_provided"

    _VALID_SIGNIFICANCE = {
        PATHOGENIC,
        LIKELY_PATHOGENIC,
        UNCERTAIN_SIGNIFICANCE,
        LIKELY_BENIGN,
        BENIGN,
        CONFLICTING,
        NOT_PROVIDED,
    }

    @classmethod
    def validate(cls, value: str) -> str:
        normalized = value or cls.NOT_PROVIDED
        if normalized not in cls._VALID_SIGNIFICANCE:
            raise ValueError(f"Unsupported clinical_significance '{value}'")
        return normalized


CHROMOSOME_PATTERN = re.compile(r"^(chr)?[0-9XYM]+$", re.IGNORECASE)


@dataclass
class VariantSummary:
    variant_id: str
    clinvar_id: Optional[str]
    chromosome: str
    position: int
    clinical_significance: Optional[str]


@dataclass
class EvidenceSummary:
    evidence_id: Optional[int]
    evidence_level: str
    evidence_type: str
    description: str
    reviewed: bool


@dataclass
class Variant:
    identifier: VariantIdentifier
    chromosome: str
    position: int
    reference_allele: str
    alternate_allele: str
    variant_type: str = VariantType.UNKNOWN
    clinical_significance: str = ClinicalSignificance.NOT_PROVIDED
    gene_identifier: Optional[GeneIdentifier] = None
    gene_database_id: Optional[int] = None
    hgvs_genomic: Optional[str] = None
    hgvs_protein: Optional[str] = None
    hgvs_cdna: Optional[str] = None
    condition: Optional[str] = None
    review_status: Optional[str] = None
    allele_frequency: Optional[float] = None
    gnomad_af: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None
    evidence_count: int = 0
    evidence: list[EvidenceSummary] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.variant_type = VariantType.validate(self.variant_type)
        self.clinical_significance = ClinicalSignificance.validate(
            self.clinical_significance
        )
        self.chromosome = self._normalize_chromosome(self.chromosome)

        if self.position < 1:
            raise ValueError("position must be >= 1")
        if not self.reference_allele:
            raise ValueError("reference_allele cannot be empty")
        if not self.alternate_allele:
            raise ValueError("alternate_allele cannot be empty")
        if self.allele_frequency is not None and not (
            0.0 <= self.allele_frequency <= 1.0
        ):
            raise ValueError("allele_frequency must be between 0.0 and 1.0")
        if self.gnomad_af is not None and not (0.0 <= self.gnomad_af <= 1.0):
            raise ValueError("gnomad_af must be between 0.0 and 1.0")

    @classmethod
    def create(
        cls,
        chromosome: str,
        position: int,
        reference_allele: str,
        alternate_allele: str,
        *,
        variant_id: Optional[str] = None,
        clinvar_id: Optional[str] = None,
        gene_identifier: Optional[GeneIdentifier] = None,
        gene_database_id: Optional[int] = None,
        variant_type: str = VariantType.UNKNOWN,
        clinical_significance: str = ClinicalSignificance.NOT_PROVIDED,
        hgvs_genomic: Optional[str] = None,
        hgvs_protein: Optional[str] = None,
        hgvs_cdna: Optional[str] = None,
        condition: Optional[str] = None,
        review_status: Optional[str] = None,
        allele_frequency: Optional[float] = None,
        gnomad_af: Optional[float] = None,
    ) -> Variant:
        identifier = VariantIdentifier(
            variant_id=variant_id
            or cls._compose_variant_id(
                chromosome, position, reference_allele, alternate_allele
            ),
            clinvar_id=clinvar_id,
        )
        return cls(
            identifier=identifier,
            chromosome=chromosome,
            position=position,
            reference_allele=reference_allele,
            alternate_allele=alternate_allele,
            variant_type=variant_type,
            clinical_significance=clinical_significance,
            gene_identifier=gene_identifier,
            gene_database_id=gene_database_id,
            hgvs_genomic=hgvs_genomic,
            hgvs_protein=hgvs_protein,
            hgvs_cdna=hgvs_cdna,
            condition=condition,
            review_status=review_status,
            allele_frequency=allele_frequency,
            gnomad_af=gnomad_af,
        )

    @property
    def variant_id(self) -> str:
        return self.identifier.variant_id

    @property
    def clinvar_id(self) -> Optional[str]:
        return self.identifier.clinvar_id

    @property
    def gene_symbol(self) -> Optional[str]:
        return self.gene_identifier.symbol if self.gene_identifier else None

    @property
    def gene_public_id(self) -> Optional[str]:
        return self.gene_identifier.gene_id if self.gene_identifier else None

    def update_classification(
        self,
        *,
        variant_type: Optional[str] = None,
        clinical_significance: Optional[str] = None,
    ) -> None:
        if variant_type is not None:
            self.variant_type = VariantType.validate(variant_type)
        if clinical_significance is not None:
            self.clinical_significance = ClinicalSignificance.validate(
                clinical_significance
            )
        self._touch()

    def update_gene_reference(
        self,
        *,
        gene_identifier: Optional[GeneIdentifier] = None,
        gene_database_id: Optional[int] = None,
    ) -> None:
        if gene_identifier is not None:
            self.gene_identifier = gene_identifier
        if gene_database_id is not None:
            self.gene_database_id = gene_database_id
        self._touch()

    def mark_review_status(
        self,
        *,
        review_status: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> None:
        if review_status is not None:
            self.review_status = review_status
        if condition is not None:
            self.condition = condition
        self._touch()

    def update_frequencies(
        self,
        *,
        allele_frequency: Optional[float] = None,
        gnomad_af: Optional[float] = None,
    ) -> None:
        if allele_frequency is not None:
            if not (0.0 <= allele_frequency <= 1.0):
                raise ValueError("allele_frequency must be between 0.0 and 1.0")
            self.allele_frequency = allele_frequency
        if gnomad_af is not None:
            if not (0.0 <= gnomad_af <= 1.0):
                raise ValueError("gnomad_af must be between 0.0 and 1.0")
            self.gnomad_af = gnomad_af
        self._touch()

    def snapshot(self) -> VariantSummary:
        return VariantSummary(
            variant_id=self.variant_id,
            clinvar_id=self.clinvar_id,
            chromosome=self.chromosome,
            position=self.position,
            clinical_significance=self.clinical_significance,
        )

    def add_evidence_summary(self, summary: EvidenceSummary) -> None:
        self.evidence.append(summary)
        self.evidence_count = len(self.evidence)
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    @staticmethod
    def _compose_variant_id(
        chromosome: str, position: int, reference_allele: str, alternate_allele: str
    ) -> str:
        return f"{chromosome}:{position}:{reference_allele}>{alternate_allele}"

    @staticmethod
    def _normalize_chromosome(chromosome: str) -> str:
        value = chromosome.strip()
        if not CHROMOSOME_PATTERN.fullmatch(value):
            raise ValueError("chromosome must match pattern chr<id>")
        if not value.lower().startswith("chr"):
            value = f"chr{value}"
        return value.upper()


__all__ = [
    "Variant",
    "VariantSummary",
    "EvidenceSummary",
    "VariantType",
    "ClinicalSignificance",
]

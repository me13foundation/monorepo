from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from src.domain.value_objects.identifiers import GeneIdentifier, VariantIdentifier


class VariantType:
    SNV = "snv"
    INDEL = "indel"
    CNV = "cnv"
    STRUCTURAL = "structural"
    UNKNOWN = "unknown"

    _VALID_TYPES: ClassVar[set[str]] = {SNV, INDEL, CNV, STRUCTURAL, UNKNOWN}

    @classmethod
    def validate(cls, value: str) -> str:
        normalized = value or cls.UNKNOWN
        if normalized not in cls._VALID_TYPES:
            msg = f"Unsupported variant_type '{value}'"
            raise ValueError(msg)
        return normalized


class ClinicalSignificance:
    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    UNCERTAIN_SIGNIFICANCE = "uncertain_significance"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"
    CONFLICTING = "conflicting"
    NOT_PROVIDED = "not_provided"

    _VALID_SIGNIFICANCE: ClassVar[set[str]] = {
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
            msg = f"Unsupported clinical_significance '{value}'"
            raise ValueError(msg)
        return normalized


CHROMOSOME_PATTERN = re.compile(r"^(chr)?[0-9XYM]+$", re.IGNORECASE)


class VariantSummary(BaseModel):
    variant_id: str
    clinvar_id: str | None
    chromosome: str
    position: int
    clinical_significance: str | None

    model_config = ConfigDict(validate_assignment=True)


class EvidenceSummary(BaseModel):
    evidence_id: int | None
    evidence_level: str
    evidence_type: str
    description: str
    reviewed: bool

    model_config = ConfigDict(validate_assignment=True)


class Variant(BaseModel):
    identifier: VariantIdentifier
    chromosome: str
    position: int
    reference_allele: str
    alternate_allele: str
    variant_type: str = Field(default=VariantType.UNKNOWN)
    clinical_significance: str = Field(
        default=ClinicalSignificance.NOT_PROVIDED,
    )
    gene_identifier: GeneIdentifier | None = None
    gene_database_id: int | None = None
    hgvs_genomic: str | None = None
    hgvs_protein: str | None = None
    hgvs_cdna: str | None = None
    condition: str | None = None
    review_status: str | None = None
    allele_frequency: float | None = None
    gnomad_af: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None
    evidence_count: int = 0
    evidence: list[EvidenceSummary] = Field(default_factory=list)

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    @field_validator("chromosome")
    @classmethod
    def _normalize_chromosome(cls, value: str) -> str:
        cleaned = value.strip()
        if not CHROMOSOME_PATTERN.fullmatch(cleaned):
            msg = "chromosome must match pattern chr<id>"
            raise ValueError(msg)
        if not cleaned.lower().startswith("chr"):
            cleaned = f"chr{cleaned}"
        return cleaned.upper()

    @field_validator("variant_type")
    @classmethod
    def _validate_variant_type(cls, value: str) -> str:
        return VariantType.validate(value)

    @field_validator("clinical_significance")
    @classmethod
    def _validate_significance(cls, value: str) -> str:
        return ClinicalSignificance.validate(value)

    @model_validator(mode="after")
    def _validate_variant(self) -> Variant:
        if self.position < 1:
            msg = "position must be >= 1"
            raise ValueError(msg)
        if not self.reference_allele:
            msg = "reference_allele cannot be empty"
            raise ValueError(msg)
        if not self.alternate_allele:
            msg = "alternate_allele cannot be empty"
            raise ValueError(msg)
        for field_name in ("allele_frequency", "gnomad_af"):
            value = getattr(self, field_name)  # type: ignore[misc]
            if value is not None and not (0.0 <= value <= 1.0):  # type: ignore[misc]
                msg = f"{field_name} must be between 0.0 and 1.0"
                raise ValueError(msg)
        return self

    @classmethod
    def create(  # noqa: PLR0913 - explicit factory arguments for clarity
        cls,
        chromosome: str,
        position: int,
        reference_allele: str,
        alternate_allele: str,
        *,
        variant_id: str | None = None,
        clinvar_id: str | None = None,
        gene_identifier: GeneIdentifier | None = None,
        gene_database_id: int | None = None,
        variant_type: str = VariantType.UNKNOWN,
        clinical_significance: str = ClinicalSignificance.NOT_PROVIDED,
        hgvs_genomic: str | None = None,
        hgvs_protein: str | None = None,
        hgvs_cdna: str | None = None,
        condition: str | None = None,
        review_status: str | None = None,
        allele_frequency: float | None = None,
        gnomad_af: float | None = None,
    ) -> Variant:
        identifier = VariantIdentifier(
            variant_id=variant_id
            or cls._compose_variant_id(
                chromosome,
                position,
                reference_allele,
                alternate_allele,
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
    def clinvar_id(self) -> str | None:
        return self.identifier.clinvar_id

    @property
    def gene_symbol(self) -> str | None:
        return self.gene_identifier.symbol if self.gene_identifier else None

    @property
    def gene_public_id(self) -> str | None:
        return self.gene_identifier.gene_id if self.gene_identifier else None

    def update_classification(
        self,
        *,
        variant_type: str | None = None,
        clinical_significance: str | None = None,
    ) -> None:
        if variant_type is not None:
            self.variant_type = VariantType.validate(variant_type)
        if clinical_significance is not None:
            self.clinical_significance = ClinicalSignificance.validate(
                clinical_significance,
            )
        self._touch()

    def update_gene_reference(
        self,
        *,
        gene_identifier: GeneIdentifier | None = None,
        gene_database_id: int | None = None,
    ) -> None:
        if gene_identifier is not None:
            self.gene_identifier = gene_identifier
        if gene_database_id is not None:
            self.gene_database_id = gene_database_id
        self._touch()

    def mark_review_status(
        self,
        *,
        review_status: str | None = None,
        condition: str | None = None,
    ) -> None:
        if review_status is not None:
            self.review_status = review_status
        if condition is not None:
            self.condition = condition
        self._touch()

    def update_frequencies(
        self,
        *,
        allele_frequency: float | None = None,
        gnomad_af: float | None = None,
    ) -> None:
        if allele_frequency is not None:
            if not (0.0 <= allele_frequency <= 1.0):
                msg = "allele_frequency must be between 0.0 and 1.0"
                raise ValueError(msg)
            self.allele_frequency = allele_frequency
        if gnomad_af is not None:
            if not (0.0 <= gnomad_af <= 1.0):
                msg = "gnomad_af must be between 0.0 and 1.0"
                raise ValueError(msg)
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
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _compose_variant_id(
        chromosome: str,
        position: int,
        reference_allele: str,
        alternate_allele: str,
    ) -> str:
        return f"{chromosome}:{position}:{reference_allele}>{alternate_allele}"


__all__ = [
    "ClinicalSignificance",
    "EvidenceSummary",
    "Variant",
    "VariantSummary",
    "VariantType",
]

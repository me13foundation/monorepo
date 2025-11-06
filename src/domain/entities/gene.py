from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, ClassVar

from src.domain.value_objects.identifiers import GeneIdentifier

if TYPE_CHECKING:
    from src.domain.entities.variant import VariantSummary
    from src.domain.value_objects.provenance import Provenance


class GeneType:
    PROTEIN_CODING = "protein_coding"
    PSEUDOGENE = "pseudogene"
    NCRNA = "ncRNA"
    UNKNOWN = "unknown"

    _VALID_TYPES: ClassVar[set[str]] = {PROTEIN_CODING, PSEUDOGENE, NCRNA, UNKNOWN}

    @classmethod
    def validate(cls, value: str) -> str:
        normalized = value or cls.UNKNOWN
        if normalized not in cls._VALID_TYPES:
            msg = f"Unsupported gene_type '{value}'"
            raise ValueError(msg)
        return normalized


CHROMOSOME_PATTERN = re.compile(r"^(chr)?[0-9XYM]+$", re.IGNORECASE)


@dataclass
class Gene:
    identifier: GeneIdentifier
    gene_type: str = GeneType.UNKNOWN
    name: str | None = None
    description: str | None = None
    chromosome: str | None = None
    start_position: int | None = None
    end_position: int | None = None
    provenance: Provenance | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None
    variants: list[VariantSummary] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.gene_type = GeneType.validate(self.gene_type)
        if self.chromosome:
            self.chromosome = self._normalize_chromosome(self.chromosome)

        if self.start_position is not None and self.start_position < 1:
            msg = "start_position must be >= 1"
            raise ValueError(msg)
        if self.end_position is not None and self.end_position < 1:
            msg = "end_position must be >= 1"
            raise ValueError(msg)
        if (
            self.start_position is not None
            and self.end_position is not None
            and self.end_position < self.start_position
        ):
            msg = "end_position must be greater than or equal to start_position"
            raise ValueError(msg)

    @classmethod
    def create(  # noqa: PLR0913 - explicit factory arguments for clarity
        cls,
        symbol: str,
        gene_id: str | None = None,
        *,
        gene_type: str = GeneType.PROTEIN_CODING,
        name: str | None = None,
        description: str | None = None,
        chromosome: str | None = None,
        start_position: int | None = None,
        end_position: int | None = None,
        ensembl_id: str | None = None,
        ncbi_gene_id: int | None = None,
        uniprot_id: str | None = None,
        provenance: Provenance | None = None,
    ) -> Gene:
        identifier = GeneIdentifier(
            gene_id=gene_id or symbol,
            symbol=symbol,
            ensembl_id=ensembl_id,
            ncbi_gene_id=ncbi_gene_id,
            uniprot_id=uniprot_id,
        )
        return cls(
            identifier=identifier,
            gene_type=gene_type,
            name=name,
            description=description,
            chromosome=chromosome,
            start_position=start_position,
            end_position=end_position,
            provenance=provenance,
        )

    @property
    def gene_id(self) -> str:
        return self.identifier.gene_id

    @property
    def symbol(self) -> str:
        return self.identifier.symbol

    @property
    def ensembl_id(self) -> str | None:
        return self.identifier.ensembl_id

    @property
    def ncbi_gene_id(self) -> int | None:
        return self.identifier.ncbi_gene_id

    @property
    def uniprot_id(self) -> str | None:
        return self.identifier.uniprot_id

    def update_identifier(
        self,
        *,
        gene_id: str | None = None,
        symbol: str | None = None,
        ensembl_id: str | None = None,
        ncbi_gene_id: int | None = None,
        uniprot_id: str | None = None,
    ) -> None:
        updated = GeneIdentifier(
            gene_id=gene_id or self.identifier.gene_id,
            symbol=symbol or self.identifier.symbol,
            ensembl_id=(
                ensembl_id if ensembl_id is not None else self.identifier.ensembl_id
            ),
            ncbi_gene_id=(
                ncbi_gene_id
                if ncbi_gene_id is not None
                else self.identifier.ncbi_gene_id
            ),
            uniprot_id=(
                uniprot_id if uniprot_id is not None else self.identifier.uniprot_id
            ),
        )
        self.identifier = updated
        self._touch()

    def set_location(
        self,
        *,
        chromosome: str | None = None,
        start_position: int | None = None,
        end_position: int | None = None,
    ) -> None:
        if chromosome is not None:
            self.chromosome = self._normalize_chromosome(chromosome)

        if start_position is not None:
            if start_position < 1:
                msg = "start_position must be >= 1"
                raise ValueError(msg)
            self.start_position = start_position
        if end_position is not None:
            if end_position < 1:
                msg = "end_position must be >= 1"
                raise ValueError(msg)
            self.end_position = end_position

        if (
            self.start_position is not None
            and self.end_position is not None
            and self.end_position < self.start_position
        ):
            msg = "end_position must be greater than or equal to start_position"
            raise ValueError(msg)

        self._touch()

    def update_metadata(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        gene_type: str | None = None,
    ) -> None:
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if gene_type is not None:
            self.gene_type = GeneType.validate(gene_type)
        self._touch()

    def attach_provenance(self, provenance: Provenance) -> None:
        self.provenance = provenance
        self._touch()

    def add_provenance_step(self, step: str) -> None:
        if self.provenance is None:
            msg = "Cannot add processing step without provenance"
            raise ValueError(msg)
        self.provenance = self.provenance.add_processing_step(step)
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _normalize_chromosome(chromosome: str) -> str:
        value = chromosome.strip()
        if not CHROMOSOME_PATTERN.fullmatch(value):
            msg = "chromosome must match pattern chr<id>"
            raise ValueError(msg)
        if not value.lower().startswith("chr"):
            value = f"chr{value}"
        return value.upper()


__all__ = ["Gene", "GeneType"]

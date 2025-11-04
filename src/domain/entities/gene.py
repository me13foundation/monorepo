from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Optional

from src.domain.value_objects.identifiers import GeneIdentifier
from src.domain.value_objects.provenance import Provenance
from src.domain.entities.variant import VariantSummary


class GeneType:
    PROTEIN_CODING = "protein_coding"
    PSEUDOGENE = "pseudogene"
    NCRNA = "ncRNA"
    UNKNOWN = "unknown"

    _VALID_TYPES = {PROTEIN_CODING, PSEUDOGENE, NCRNA, UNKNOWN}

    @classmethod
    def validate(cls, value: str) -> str:
        normalized = value or cls.UNKNOWN
        if normalized not in cls._VALID_TYPES:
            raise ValueError(f"Unsupported gene_type '{value}'")
        return normalized


CHROMOSOME_PATTERN = re.compile(r"^(chr)?[0-9XYM]+$", re.IGNORECASE)


@dataclass
class Gene:
    identifier: GeneIdentifier
    gene_type: str = GeneType.UNKNOWN
    name: Optional[str] = None
    description: Optional[str] = None
    chromosome: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    provenance: Optional[Provenance] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None
    variants: list[VariantSummary] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.gene_type = GeneType.validate(self.gene_type)
        if self.chromosome:
            self.chromosome = self._normalize_chromosome(self.chromosome)

        if self.start_position is not None and self.start_position < 1:
            raise ValueError("start_position must be >= 1")
        if self.end_position is not None and self.end_position < 1:
            raise ValueError("end_position must be >= 1")
        if (
            self.start_position is not None
            and self.end_position is not None
            and self.end_position < self.start_position
        ):
            raise ValueError(
                "end_position must be greater than or equal to start_position"
            )

    @classmethod
    def create(
        cls,
        symbol: str,
        gene_id: Optional[str] = None,
        *,
        gene_type: str = GeneType.PROTEIN_CODING,
        name: Optional[str] = None,
        description: Optional[str] = None,
        chromosome: Optional[str] = None,
        start_position: Optional[int] = None,
        end_position: Optional[int] = None,
        ensembl_id: Optional[str] = None,
        ncbi_gene_id: Optional[int] = None,
        uniprot_id: Optional[str] = None,
        provenance: Optional[Provenance] = None,
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
    def ensembl_id(self) -> Optional[str]:
        return self.identifier.ensembl_id

    @property
    def ncbi_gene_id(self) -> Optional[int]:
        return self.identifier.ncbi_gene_id

    @property
    def uniprot_id(self) -> Optional[str]:
        return self.identifier.uniprot_id

    def update_identifier(
        self,
        *,
        gene_id: Optional[str] = None,
        symbol: Optional[str] = None,
        ensembl_id: Optional[str] = None,
        ncbi_gene_id: Optional[int] = None,
        uniprot_id: Optional[str] = None,
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
        chromosome: Optional[str] = None,
        start_position: Optional[int] = None,
        end_position: Optional[int] = None,
    ) -> None:
        if chromosome is not None:
            self.chromosome = self._normalize_chromosome(chromosome)

        if start_position is not None:
            if start_position < 1:
                raise ValueError("start_position must be >= 1")
            self.start_position = start_position
        if end_position is not None:
            if end_position < 1:
                raise ValueError("end_position must be >= 1")
            self.end_position = end_position

        if (
            self.start_position is not None
            and self.end_position is not None
            and self.end_position < self.start_position
        ):
            raise ValueError(
                "end_position must be greater than or equal to start_position"
            )

        self._touch()

    def update_metadata(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        gene_type: Optional[str] = None,
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
            raise ValueError("Cannot add processing step without provenance")
        self.provenance = self.provenance.add_processing_step(step)
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    @staticmethod
    def _normalize_chromosome(chromosome: str) -> str:
        value = chromosome.strip()
        if not CHROMOSOME_PATTERN.fullmatch(value):
            raise ValueError("chromosome must match pattern chr<id>")
        if not value.lower().startswith("chr"):
            value = f"chr{value}"
        return value.upper()


__all__ = ["Gene", "GeneType"]

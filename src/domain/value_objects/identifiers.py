from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional

GENE_ID_PATTERN = re.compile(r"^[A-Z0-9_-]{1,50}$")
GENE_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9_-]{1,20}$")
ENSEMBL_PATTERN = re.compile(r"^ENSG[0-9]+$")
UNIPROT_PATTERN = re.compile(r"^[A-Z0-9_-]+$")
CLINVAR_PATTERN = re.compile(r"^VCV[0-9]+$")
HPO_PATTERN = re.compile(r"^HP:[0-9]{7}$")
DOI_PATTERN = re.compile(r"^(10\.\d{4,9}/[-._;()/:A-Z0-9]+)$", re.IGNORECASE)


@dataclass(frozen=True)
class GeneIdentifier:
    gene_id: str
    symbol: str
    ensembl_id: Optional[str] = None
    ncbi_gene_id: Optional[int] = None
    uniprot_id: Optional[str] = None

    def __post_init__(self) -> None:
        normalized_gene_id = self.gene_id.upper()
        normalized_symbol = self.symbol.upper()

        if not GENE_ID_PATTERN.fullmatch(normalized_gene_id):
            raise ValueError(
                "gene_id must be 1-50 uppercase alphanumeric or _-/ characters"
            )
        if not GENE_SYMBOL_PATTERN.fullmatch(normalized_symbol):
            raise ValueError(
                "symbol must be 1-20 uppercase alphanumeric or _-/ characters"
            )

        object.__setattr__(self, "gene_id", normalized_gene_id)
        object.__setattr__(self, "symbol", normalized_symbol)

        if self.ensembl_id and not ENSEMBL_PATTERN.fullmatch(self.ensembl_id):
            raise ValueError("ensembl_id must match ENSG#### pattern")
        if self.uniprot_id and not UNIPROT_PATTERN.fullmatch(self.uniprot_id):
            raise ValueError(
                "uniprot_id must contain uppercase alphanumerics, '_' or '-'"
            )
        if self.ncbi_gene_id is not None and self.ncbi_gene_id < 1:
            raise ValueError("ncbi_gene_id must be positive")

    def __str__(self) -> str:
        return self.symbol


@dataclass(frozen=True)
class VariantIdentifier:
    variant_id: str
    clinvar_id: Optional[str] = None
    hgvs_genomic: Optional[str] = None
    hgvs_protein: Optional[str] = None
    hgvs_cdna: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.variant_id or len(self.variant_id) > 100:
            raise ValueError("variant_id must be between 1 and 100 characters")
        if self.clinvar_id and not CLINVAR_PATTERN.fullmatch(self.clinvar_id):
            raise ValueError("clinvar_id must match VCV#### format")

    def __str__(self) -> str:
        return self.variant_id


@dataclass(frozen=True)
class PhenotypeIdentifier:
    hpo_id: str
    hpo_term: str

    def __post_init__(self) -> None:
        if not HPO_PATTERN.fullmatch(self.hpo_id):
            raise ValueError("hpo_id must match HP:####### format")
        if not self.hpo_term or len(self.hpo_term) > 200:
            raise ValueError("hpo_term must be 1-200 characters")

    def __str__(self) -> str:
        return f"{self.hpo_id} ({self.hpo_term})"


@dataclass(frozen=True)
class PublicationIdentifier:
    pubmed_id: Optional[str] = None
    pmc_id: Optional[str] = None
    doi: Optional[str] = None

    def __post_init__(self) -> None:
        if self.pubmed_id and not self.pubmed_id.isdigit():
            raise ValueError("pubmed_id must be numeric")
        if self.pmc_id and not self.pmc_id.startswith("PMC"):
            raise ValueError("pmc_id must start with PMC")
        if self.doi and not DOI_PATTERN.fullmatch(self.doi):
            raise ValueError("doi must follow DOI syntax (10.xxxx/...)")

    def get_primary_id(self) -> str:
        return self.pmc_id or self.pubmed_id or (self.doi or "unknown")

    def __str__(self) -> str:
        return self.get_primary_id()


__all__ = [
    "GeneIdentifier",
    "VariantIdentifier",
    "PhenotypeIdentifier",
    "PublicationIdentifier",
]

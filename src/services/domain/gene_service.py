"""
Gene service for MED13 Resource Library.
Business logic for gene entity operations and validations.
"""

from datetime import datetime
from typing import Protocol

from sqlalchemy.orm import Session

from src.domain.entities.gene import Gene
from src.domain.entities.variant import VariantSummary
from src.domain.value_objects.identifiers import GeneIdentifier
from src.domain.value_objects.provenance import Provenance
from src.infrastructure.repositories import SqlAlchemyGeneRepository
from src.infrastructure.repositories.variant_repository import (
    SqlAlchemyVariantRepository,
)
from src.services.domain.base_service import BaseService

StatisticsValue = int | float | bool | str | None | datetime


class GeneService(BaseService[SqlAlchemyGeneRepository]):
    """
    Service for gene business logic and operations.

    Provides high-level operations for gene management including
    validation, creation, and relationship management.
    """

    def __init__(
        self,
        session: Session | None = None,
        gene_repository: SqlAlchemyGeneRepository | None = None,
    ):
        super().__init__(session)
        if gene_repository is not None:
            self.gene_repo = gene_repository
        else:
            self.gene_repo = SqlAlchemyGeneRepository(session)
        self.variant_repo = SqlAlchemyVariantRepository(session)

    @property
    def repository(self) -> SqlAlchemyGeneRepository:
        return self.gene_repo

    def create_gene(  # noqa: PLR0913 - explicit, intentional parameter list
        self,
        symbol: str,
        name: str | None = None,
        description: str | None = None,
        gene_type: str = "protein_coding",
        gene_id: str | None = None,
        chromosome: str | None = None,
        start_position: int | None = None,
        end_position: int | None = None,
        ensembl_id: str | None = None,
        ncbi_gene_id: int | None = None,
        uniprot_id: str | None = None,
        provenance: Provenance | None = None,
    ) -> Gene:
        """
        Create a new gene with validation.

        Args:
            symbol: Gene symbol
            name: Full gene name
            description: Gene description
            gene_type: Type of gene
            gene_id: Optional pre-defined gene identifier
            chromosome: Chromosome location
            start_position: Start position on chromosome
            end_position: End position on chromosome
            ensembl_id: Ensembl gene ID
            ncbi_gene_id: NCBI Gene ID
            uniprot_id: UniProt accession
            provenance: Data provenance information

        Returns:
            Created GeneModel instance

        Raises:
            ValueError: If validation fails
            DuplicateError: If gene already exists
        """
        # Validate positions if both are provided
        if (
            start_position is not None
            and end_position is not None
            and end_position < start_position
        ):
            msg = "End position must be greater than start position"
            raise ValueError(msg)

        normalized_symbol = symbol.upper()
        gene_identifier = gene_id or normalized_symbol

        # Create the gene
        gene_entity = Gene.create(
            symbol=normalized_symbol,
            gene_id=gene_identifier,
            gene_type=gene_type,
            name=name,
            description=description,
            chromosome=chromosome,
            start_position=start_position,
            end_position=end_position,
            ensembl_id=ensembl_id,
            ncbi_gene_id=ncbi_gene_id,
            uniprot_id=uniprot_id,
            provenance=provenance,
        )

        return self.repository.create(gene_entity)

    def list_genes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        search: str | None = None,
    ) -> tuple[list[Gene], int]:
        """Retrieve paginated genes with optional search."""
        return self.gene_repo.paginate_genes(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
        )

    def get_gene_by_id(self, gene_id: str) -> Gene | None:
        """Retrieve a gene by its public gene identifier."""
        return self.gene_repo.find_by_gene_id(gene_id)

    def get_gene_by_symbol(self, symbol: str) -> Gene | None:
        """Retrieve a gene by its symbol."""
        return self.gene_repo.find_by_symbol(symbol.upper())

    def find_gene_by_identifier(self, identifier: GeneIdentifier) -> Gene | None:
        """
        Find a gene by its identifier (supports multiple ID types).

        Args:
            identifier: GeneIdentifier value object

        Returns:
            GeneModel instance or None if not found
        """
        # Try different ID types in order of preference
        gene = self.gene_repo.find_by_gene_id(identifier.gene_id)
        if gene:
            return gene

        gene = self.gene_repo.find_by_symbol(identifier.symbol)
        if gene:
            return gene

        if identifier.ensembl_id:
            gene = self.gene_repo.find_by_external_id(identifier.ensembl_id)
        if not gene and identifier.ncbi_gene_id:
            gene = self.gene_repo.find_by_external_id(str(identifier.ncbi_gene_id))
        if not gene and identifier.uniprot_id:
            gene = self.gene_repo.find_by_external_id(identifier.uniprot_id)

        return gene

    def get_gene_with_variants(self, gene_id: int) -> Gene | None:
        """
        Get a gene with its associated variants loaded.

        Args:
            gene_id: Gene ID to retrieve

        Returns:
            GeneModel with variants relationship loaded
        """
        gene = self.gene_repo.get_by_id(gene_id)
        if gene:
            variant_models = self.variant_repo.find_by_gene(gene_id)
            gene.variants = [
                self._build_variant_summary(variant) for variant in variant_models
            ]
        return gene

    def search_genes(self, query: str, limit: int = 10) -> list[Gene]:
        """
        Search genes by symbol or name.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching GeneModel instances
        """
        return self.gene_repo.search_by_name_or_symbol(query, limit)

    def update_gene(self, gene_id: str, updates: dict[str, object]) -> Gene:
        """Update mutable gene fields by gene identifier."""
        gene = self.gene_repo.find_by_gene_id_or_fail(gene_id)

        allowed_fields = {
            "name",
            "description",
            "gene_type",
            "chromosome",
            "start_position",
            "end_position",
            "ensembl_id",
            "ncbi_gene_id",
            "uniprot_id",
        }

        sanitized_updates = {
            key: value for key, value in updates.items() if key in allowed_fields
        }

        if not sanitized_updates:
            msg = "No valid fields provided for update"
            raise ValueError(msg)

        gene_db_id = self._require_gene_db_id(gene)
        return self.repository.update(gene_db_id, sanitized_updates)

    def update_gene_locations(
        self,
        gene_id: int,
        chromosome: str | None = None,
        start_position: int | None = None,
        end_position: int | None = None,
    ) -> Gene:
        """
        Update gene genomic location information.

        Args:
            gene_id: Gene ID to update
            chromosome: New chromosome
            start_position: New start position
            end_position: New end position

        Returns:
            Updated GeneModel instance

        Raises:
            ValueError: If positions are invalid
            NotFoundError: If gene not found
        """
        # Validate positions
        if (
            start_position is not None
            and end_position is not None
            and end_position < start_position
        ):
            msg = "End position must be greater than start position"
            raise ValueError(msg)

        updates: dict[str, object] = {}
        if chromosome is not None:
            updates["chromosome"] = chromosome
        if start_position is not None:
            updates["start_position"] = start_position
        if end_position is not None:
            updates["end_position"] = end_position

        if not updates:
            msg = "No location updates provided"
            raise ValueError(msg)

        return self.repository.update(gene_id, updates)

    def delete_gene(self, gene_id: str) -> None:
        """Delete a gene by its gene identifier."""
        gene = self.gene_repo.find_by_gene_id_or_fail(gene_id)
        gene_db_id = self._require_gene_db_id(gene)
        self.repository.delete(gene_db_id)

    def get_gene_variants(self, gene_id: str) -> list[VariantSummary]:
        """Return serialized variants associated with a gene."""
        gene = self.gene_repo.find_by_gene_id(gene_id)
        if gene is None:
            return []

        gene_db_id = self._require_gene_db_id(gene)
        variant_models = self.variant_repo.find_by_gene(gene_db_id)
        return [self._build_variant_summary(variant) for variant in variant_models]

    def get_gene_phenotypes(self, _gene_id: str) -> list[dict[str, str]]:
        """Return related phenotypes for a gene (placeholder implementation)."""
        # Phenotype relationships are not yet modeled; return empty list for now.
        return []

    def gene_has_variants(self, gene_id: str) -> bool:
        """Check whether a gene has associated variants."""
        gene = self.gene_repo.find_by_gene_id(gene_id)
        if gene is None:
            return False
        gene_db_id = self._require_gene_db_id(gene)
        variants = self.variant_repo.find_by_gene(gene_db_id, limit=1)
        return bool(variants)

    def get_gene_statistics(
        self,
        gene_id: str | None = None,
    ) -> dict[str, StatisticsValue]:
        """
        Get comprehensive statistics about genes.

        Returns:
            Dictionary with gene statistics
        """
        if gene_id:
            gene = self.gene_repo.find_by_gene_id_or_fail(gene_id)
            gene_db_id = self._require_gene_db_id(gene)
            variants = self.variant_repo.find_by_gene(gene_db_id)
            return {
                "gene_id": gene.gene_id,
                "symbol": gene.symbol,
                "variant_count": len(variants),
                "has_location": gene.chromosome is not None,
            }

        stats_raw: dict[str, object] = self.gene_repo.get_gene_statistics()
        stats: dict[str, StatisticsValue] = {
            key: value
            for key, value in stats_raw.items()
            if isinstance(value, (int, float, bool, str, datetime)) or value is None
        }

        total_genes = self._coerce_int(stats_raw.get("total_genes"))
        stats["total_genes"] = total_genes

        # Add additional computed statistics
        if total_genes > 0:
            # Calculate additional metrics
            genes_with_location = len(
                [
                    g
                    for g in self.repository.find_all(limit=1000)
                    if g.chromosome is not None
                ],
            )
            stats["genes_with_location"] = genes_with_location
            stats["location_coverage"] = genes_with_location / float(total_genes)

        return stats

    def validate_gene_exists(self, gene_id: int) -> bool:
        """
        Validate that a gene exists.

        Args:
            gene_id: Gene ID to validate

        Returns:
            True if gene exists, False otherwise
        """
        return bool(self.repository.exists(gene_id))

    def get_gene_summary(self, gene_id: int) -> dict[str, StatisticsValue] | None:
        """
        Get a summary of gene information including variant counts.

        Args:
            gene_id: Gene ID to summarize

        Returns:
            Dictionary with gene summary or None if not found
        """
        gene = self.repository.get_by_id(gene_id)
        if not gene:
            return None

        variant_count = len(self.variant_repo.find_by_gene(gene_id))

        return {
            "id": gene.id,
            "gene_id": gene.gene_id,
            "symbol": gene.symbol,
            "name": gene.name,
            "gene_type": gene.gene_type,
            "chromosome": gene.chromosome,
            "start_position": gene.start_position,
            "end_position": gene.end_position,
            "variant_count": variant_count,
            "created_at": gene.created_at,
            "updated_at": gene.updated_at,
        }

    def _require_gene_db_id(self, gene: Gene) -> int:
        if gene.id is None:
            msg = "Gene is not persisted and lacks a database id"
            raise ValueError(msg)
        return gene.id

    class _VariantLike(Protocol):
        @property
        def variant_id(self) -> str:
            ...

        @property
        def chromosome(self) -> str:
            ...

        @property
        def position(self) -> int:
            ...

        @property
        def clinvar_id(self) -> str | None:
            ...

        @property
        def clinical_significance(self) -> str | None:
            ...

    def _build_variant_summary(self, variant_model: _VariantLike) -> VariantSummary:
        return VariantSummary(
            variant_id=variant_model.variant_id,
            clinvar_id=variant_model.clinvar_id,
            chromosome=variant_model.chromosome,
            position=variant_model.position,
            clinical_significance=variant_model.clinical_significance,
        )

    @staticmethod
    def _coerce_int(value: object, default: int = 0) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default

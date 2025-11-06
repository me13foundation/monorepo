"""
SQLAlchemy implementation of Gene repository for MED13 Resource Library.
Data access layer for gene entities with specialized queries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import asc, delete, desc, func, or_, select, update

from src.domain.repositories.gene_repository import (
    GeneRepository as GeneRepositoryInterface,
)
from src.infrastructure.mappers.gene_mapper import GeneMapper
from src.models.database import GeneModel

if TYPE_CHECKING:
    from src.type_definitions.common import GeneUpdate

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.orm import Session

    from src.domain.entities.gene import Gene
    from src.domain.repositories.base import QuerySpecification
    from src.domain.value_objects.identifiers import GeneIdentifier


class SqlAlchemyGeneRepository(GeneRepositoryInterface):
    """
    Repository for Gene entities with specialized gene-specific queries.

    Provides data access operations for gene entities including
    symbol-based lookups, external ID searches, and relationship queries.
    """

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the current database session."""
        if self._session is None:
            message = "Session not provided"
            raise ValueError(message)
        return self._session

    def create(self, gene: Gene) -> Gene:
        model = GeneMapper.to_model(gene)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return GeneMapper.to_domain(model)

    def paginate_genes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        search: str | None = None,
    ) -> tuple[list[Gene], int]:
        """
        Retrieve paginated genes with optional search and sorting.

        Args:
            page: Page number starting at 1
            per_page: Number of records per page
            sort_by: Field to sort by
            sort_order: Sort direction ('asc' or 'desc')
            search: Optional search string

        Returns:
            Tuple of (records list, total count)
        """
        offset = max(page - 1, 0) * per_page

        sortable_fields = {
            "symbol": GeneModel.symbol,
            "name": GeneModel.name,
            "gene_type": GeneModel.gene_type,
            "chromosome": GeneModel.chromosome,
            "created_at": GeneModel.created_at,
        }

        sort_column = sortable_fields.get(sort_by, GeneModel.symbol)
        order_clause = (
            desc(sort_column) if sort_order.lower() == "desc" else asc(sort_column)
        )

        stmt = select(GeneModel).order_by(order_clause).offset(offset).limit(per_page)
        count_stmt = select(func.count()).select_from(GeneModel)

        if search:
            pattern = f"%{search}%"
            predicate = or_(
                GeneModel.symbol.ilike(pattern),
                GeneModel.name.ilike(pattern),
            )
            stmt = stmt.where(predicate)
            count_stmt = count_stmt.where(predicate)

        models = list(self.session.execute(stmt).scalars())
        total = self.session.execute(count_stmt).scalar_one()

        return GeneMapper.to_domain_sequence(models), int(total)

    def find_by_gene_id(self, gene_id: str) -> Gene | None:
        """
        Find a gene by its gene_id.

        Args:
            gene_id: Gene ID to search for

        Returns:
            GeneModel instance or None if not found
        """
        stmt = select(GeneModel).where(GeneModel.gene_id == gene_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return GeneMapper.to_domain(model) if model else None

    def find_by_symbol(self, symbol: str) -> Gene | None:
        """
        Find a gene by its symbol (case-insensitive).

        Args:
            symbol: Gene symbol to search for

        Returns:
            GeneModel instance or None if not found
        """
        stmt = select(GeneModel).where(GeneModel.symbol.ilike(symbol.upper()))
        model = self.session.execute(stmt).scalar_one_or_none()
        return GeneMapper.to_domain(model) if model else None

    def find_by_external_id(self, external_id: str) -> Gene | None:
        """
        Find a gene by any external identifier (Ensembl, NCBI, UniProt).

        Args:
            external_id: External identifier to search for

        Returns:
            GeneModel instance or None if not found
        """
        conditions = [
            GeneModel.ensembl_id == external_id,
            GeneModel.uniprot_id == external_id,
        ]
        if external_id.isdigit():
            conditions.append(GeneModel.ncbi_gene_id == int(external_id))

        stmt = select(GeneModel).where(or_(*conditions))
        model = self.session.execute(stmt).scalar_one_or_none()
        return GeneMapper.to_domain(model) if model else None

    def find_by_gene_id_or_fail(self, gene_id: str) -> Gene:
        """
        Find a gene by gene_id, raising exception if not found.

        Args:
            gene_id: Gene ID to search for

        Returns:
            Gene instance

        Raises:
            ValueError: If gene is not found
        """
        gene = self.find_by_gene_id(gene_id)
        if gene is None:
            message = f"Gene with gene_id '{gene_id}' not found"
            raise ValueError(message)
        return gene

    def find_by_symbol_or_fail(self, symbol: str) -> Gene:
        """
        Find a gene by symbol, raising exception if not found.

        Args:
            symbol: Gene symbol to search for

        Returns:
            Gene instance

        Raises:
            ValueError: If gene is not found
        """
        gene = self.find_by_symbol(symbol)
        if gene is None:
            message = f"Gene with symbol '{symbol}' not found"
            raise ValueError(message)
        return gene

    def get_by_id(self, gene_id: int) -> Gene | None:
        """Get gene by database ID."""
        stmt = select(GeneModel).where(GeneModel.id == gene_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return GeneMapper.to_domain(model) if model else None

    def get_by_id_or_fail(self, gene_id: int) -> Gene:
        """Get gene by database ID, raising exception if not found."""
        gene = self.get_by_id(gene_id)
        if gene is None:
            message = f"Gene with id '{gene_id}' not found"
            raise ValueError(message)
        return gene

    def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Gene]:
        """Get all genes with optional pagination."""
        stmt = select(GeneModel)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        models = list(self.session.execute(stmt).scalars())
        return GeneMapper.to_domain_sequence(models)

    def update(self, gene_id: int, updates: dict[str, Any]) -> Gene:
        """Update a gene by ID."""
        stmt = update(GeneModel).where(GeneModel.id == gene_id).values(**updates)
        self.session.execute(stmt)
        self.session.commit()
        # Return updated entity
        return self.get_by_id_or_fail(gene_id)

    def delete(self, gene_id: int) -> bool:
        """Delete a gene by ID."""
        stmt = delete(GeneModel).where(GeneModel.id == gene_id)
        self.session.execute(stmt)
        self.session.commit()
        # Check if deletion was successful by verifying the entity no longer exists
        return not self.exists(gene_id)

    def exists(self, gene_id: int) -> bool:
        """Check if a gene exists by ID."""
        stmt = (
            select(func.count()).select_from(GeneModel).where(GeneModel.id == gene_id)
        )
        count = self.session.execute(stmt).scalar_one()
        return count > 0

    def get_gene_statistics(self) -> dict[str, Any]:
        """Get statistics about genes in the database."""
        total_genes = self.count()
        return {
            "total_genes": total_genes,
            "genes_with_variants": 0,  # Would need a join query
            "genes_with_phenotypes": 0,  # Would need a complex join query
        }

    def search_by_name_or_symbol(self, query: str, limit: int = 10) -> list[Gene]:
        """Search genes by name or symbol containing the query string."""
        search_pattern = f"%{query}%"
        stmt = (
            select(GeneModel)
            .where(
                or_(
                    GeneModel.symbol.ilike(search_pattern),
                    GeneModel.name.ilike(search_pattern),
                ),
            )
            .limit(limit)
        )
        models = list(self.session.execute(stmt).scalars())
        return GeneMapper.to_domain_sequence(models)

    def count(self) -> int:
        """Count total genes."""
        stmt = select(func.count()).select_from(GeneModel)
        return self.session.execute(stmt).scalar_one()

    # Required interface implementations
    def find_by_criteria(self, spec: QuerySpecification) -> list[Gene]:
        """Find genes by query specification."""
        # Simplified implementation - would need more complex query building
        return self.find_all(limit=spec.limit, offset=spec.offset)

    def find_by_identifier(self, identifier: GeneIdentifier) -> Gene | None:
        """Find a gene by its identifier (supports multiple ID types)."""
        # Try different ID types in order of preference
        gene = self.find_by_gene_id(identifier.gene_id)
        if gene:
            return gene

        gene = self.find_by_symbol(identifier.symbol)
        if gene:
            return gene

        if identifier.ensembl_id:
            gene = self.find_by_external_id(identifier.ensembl_id)
        if not gene and identifier.ncbi_gene_id:
            gene = self.find_by_external_id(str(identifier.ncbi_gene_id))
        if not gene and identifier.uniprot_id:
            gene = self.find_by_external_id(identifier.uniprot_id)

        return gene

    def find_with_variants(self, gene_id: int) -> Gene | None:
        """Find a gene with its associated variants loaded."""
        stmt = select(GeneModel).where(GeneModel.id == gene_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return GeneMapper.to_domain(model) if model else None

    def update_gene(self, gene_id: int, updates: GeneUpdate) -> Gene:
        """Update a gene with type-safe update parameters."""
        # Convert TypedDict to Dict[str, Any]
        updates_dict = dict(updates)
        return self.update(gene_id, updates_dict)


__all__ = ["SqlAlchemyGeneRepository"]

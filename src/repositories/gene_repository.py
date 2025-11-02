"""
Gene repository for MED13 Resource Library.
Data access layer for gene entities with specialized queries.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, or_, func, asc, desc

from .base import BaseRepository, NotFoundError
from src.models.database import GeneModel


class GeneRepository(BaseRepository[GeneModel, int]):
    """
    Repository for Gene entities with specialized gene-specific queries.

    Provides data access operations for gene entities including
    symbol-based lookups, external ID searches, and relationship queries.
    """

    @property
    def model_class(self) -> type[GeneModel]:
        return GeneModel

    def find_by_symbol(self, symbol: str) -> Optional[GeneModel]:
        """
        Find a gene by its symbol (case-insensitive).

        Args:
            symbol: Gene symbol to search for

        Returns:
            GeneModel instance or None if not found
        """
        stmt = select(GeneModel).where(GeneModel.symbol.ilike(symbol.upper()))
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_gene_id(self, gene_id: str) -> Optional[GeneModel]:
        """
        Find a gene by its gene_id.

        Args:
            gene_id: Gene ID to search for

        Returns:
            GeneModel instance or None if not found
        """
        stmt = select(GeneModel).where(GeneModel.gene_id == gene_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_external_id(self, external_id: str) -> Optional[GeneModel]:
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
        return self.session.execute(stmt).scalar_one_or_none()

    def search_by_name_or_symbol(self, query: str, limit: int = 10) -> List[GeneModel]:
        """
        Search genes by name or symbol containing the query string.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching GeneModel instances
        """
        search_pattern = f"%{query}%"
        stmt = (
            select(GeneModel)
            .where(
                or_(
                    GeneModel.symbol.ilike(search_pattern),
                    GeneModel.name.ilike(search_pattern),
                )
            )
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def paginate_genes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        search: Optional[str] = None,
    ) -> Tuple[List[GeneModel], int]:
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

        items = list(self.session.execute(stmt).scalars())
        total = self.session.execute(count_stmt).scalar_one()
        return items, int(total)

    def find_with_variants(self, gene_id: int) -> Optional[GeneModel]:
        """
        Find a gene with its associated variants loaded.

        Args:
            gene_id: Gene ID to retrieve

        Returns:
            GeneModel with variants relationship loaded, or None if not found
        """
        stmt = select(GeneModel).where(GeneModel.id == gene_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_gene_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about genes in the database.

        Returns:
            Dictionary with gene statistics
        """
        # This would typically use aggregation queries
        # For now, return basic counts
        total_genes = self.count()
        return {
            "total_genes": total_genes,
            "genes_with_variants": 0,  # Would need a join query
            "genes_with_phenotypes": 0,  # Would need a complex join query
        }

    def find_by_symbol_or_fail(self, symbol: str) -> GeneModel:
        """
        Find a gene by symbol, raising NotFoundError if not found.

        Args:
            symbol: Gene symbol to search for

        Returns:
            GeneModel instance

        Raises:
            NotFoundError: If gene is not found
        """
        gene = self.find_by_symbol(symbol)
        if gene is None:
            raise NotFoundError(f"Gene with symbol '{symbol}' not found")
        return gene

    def find_by_gene_id_or_fail(self, gene_id: str) -> GeneModel:
        """
        Find a gene by gene_id, raising NotFoundError if not found.

        Args:
            gene_id: Gene ID to search for

        Returns:
            GeneModel instance

        Raises:
            NotFoundError: If gene is not found
        """
        gene = self.find_by_gene_id(gene_id)
        if gene is None:
            raise NotFoundError(f"Gene with gene_id '{gene_id}' not found")
        return gene

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.orm import Session

    from src.domain.entities.evidence import Evidence
    from src.domain.repositories.base import QuerySpecification
from src.domain.repositories.evidence_repository import (
    EvidenceRepository as EvidenceRepositoryInterface,
)
from src.domain.value_objects.confidence import EvidenceLevel
from src.infrastructure.mappers.evidence_mapper import EvidenceMapper

if TYPE_CHECKING:  # pragma: no cover - typing only
    from src.models.database.evidence import EvidenceLevel as DbEvidenceLevel
    from src.models.database.evidence import EvidenceType as DbEvidenceType
from src.repositories.evidence_repository import EvidenceRepository

if TYPE_CHECKING:
    from src.type_definitions.common import EvidenceUpdate


class SqlAlchemyEvidenceRepository(EvidenceRepositoryInterface):
    """Domain-facing repository adapter for evidence backed by SQLAlchemy."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session
        self._repository = EvidenceRepository(session)

    def create(self, evidence: Evidence) -> Evidence:
        model = EvidenceMapper.to_model(evidence)
        persisted = self._repository.create(model)
        return EvidenceMapper.to_domain(persisted)

    def get_by_id(self, evidence_id: int) -> Evidence | None:
        model = self._repository.get_by_id(evidence_id)
        return EvidenceMapper.to_domain(model) if model else None

    def get_by_id_or_fail(self, evidence_id: int) -> Evidence:
        model = self._repository.get_by_id_or_fail(evidence_id)
        return EvidenceMapper.to_domain(model)

    def find_by_variant(
        self,
        variant_id: int,
        limit: int | None = None,
    ) -> list[Evidence]:
        models = self._repository.find_by_variant(variant_id, limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_phenotype(
        self,
        phenotype_id: int,
        limit: int | None = None,
    ) -> list[Evidence]:
        models = self._repository.find_by_phenotype(phenotype_id, limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_variant_and_phenotype(
        self,
        variant_id: int,
        phenotype_id: int,
    ) -> list[Evidence]:
        models = self._repository.find_by_variant_and_phenotype(
            variant_id,
            phenotype_id,
        )
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_publication(
        self,
        publication_id: int,
        limit: int | None = None,
    ) -> list[Evidence]:
        models = self._repository.find_by_publication(publication_id, limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_evidence_level(
        self,
        level: str,
        limit: int | None = None,
    ) -> list[Evidence]:
        normalized = EvidenceLevel(level)
        db_level = cast("DbEvidenceLevel", normalized.value)
        models = self._repository.find_by_evidence_level(db_level, limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_evidence_type(
        self,
        evidence_type: str,
        limit: int | None = None,
    ) -> list[Evidence]:
        db_type = cast("DbEvidenceType", evidence_type)
        models = self._repository.find_by_evidence_type(db_type, limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_high_confidence_evidence(
        self,
        limit: int | None = None,
    ) -> list[Evidence]:
        models = self._repository.find_high_confidence_evidence(limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_peer_reviewed_evidence(
        self,
        limit: int | None = None,
    ) -> list[Evidence]:
        models = self._repository.find_peer_reviewed_evidence(limit)
        return EvidenceMapper.to_domain_sequence(models)

    def get_evidence_statistics(self) -> dict[str, int | float | bool | str | None]:
        raw_stats = self._repository.get_evidence_statistics()
        return {
            key: value
            for key, value in raw_stats.items()
            if isinstance(value, (int, float, bool, str)) or value is None
        }

    def find_relationship_evidence(
        self,
        variant_id: int,
        phenotype_id: int,
        min_confidence: float = 0.0,
    ) -> list[Evidence]:
        models = self._repository.find_relationship_evidence(
            variant_id,
            phenotype_id,
            min_confidence,
        )
        return EvidenceMapper.to_domain_sequence(models)

    # Required interface implementations
    def delete(self, evidence_id: int) -> bool:
        return self._repository.delete(evidence_id)

    def exists(self, evidence_id: int) -> bool:
        return self._repository.exists(evidence_id)

    def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Evidence]:
        models = self._repository.find_all(limit=limit, offset=offset)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_criteria(self, spec: QuerySpecification) -> list[Evidence]:
        # Simplified implementation - would need more complex query building
        models = self._repository.find_all(limit=spec.limit, offset=spec.offset)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_gene(self, gene_id: int) -> list[Evidence]:
        models = self._repository.find_by_gene(gene_id)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_source(self, source: str) -> list[Evidence]:
        models = self._repository.find_by_source(source)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_confidence_score(
        self,
        min_score: float,
        max_score: float,
    ) -> list[Evidence]:
        models = self._repository.find_by_confidence_score(min_score, max_score)
        return EvidenceMapper.to_domain_sequence(models)

    def find_conflicting_evidence(self, _variant_id: int) -> list[Evidence]:
        # Placeholder implementation
        return []

    def paginate_evidence(
        self,
        page: int,
        per_page: int,
        _sort_by: str,
        _sort_order: str,
        _filters: dict[str, Any] | None = None,
    ) -> tuple[list[Evidence], int]:
        # Simplified implementation
        offset = (page - 1) * per_page
        models = self._repository.find_all(limit=per_page, offset=offset)
        total = self._repository.count()
        return EvidenceMapper.to_domain_sequence(models), total

    def search_evidence(
        self,
        _query: str,
        limit: int = 10,
        _filters: dict[str, Any] | None = None,
    ) -> list[Evidence]:
        # Simplified implementation
        models = self._repository.find_all(limit=limit)
        return EvidenceMapper.to_domain_sequence(models)

    def update(self, evidence_id: int, updates: dict[str, Any]) -> Evidence:
        model = self._repository.update(evidence_id, updates)
        return EvidenceMapper.to_domain(model)

    def update_evidence(
        self,
        evidence_id: int,
        updates: EvidenceUpdate,
    ) -> Evidence:
        """Update evidence with type-safe update parameters."""
        # Convert TypedDict to Dict[str, Any] for the underlying repository
        updates_dict = dict(updates)
        model = self._repository.update(evidence_id, updates_dict)
        return EvidenceMapper.to_domain(model)

    def count(self) -> int:
        return self._repository.count()


__all__ = ["SqlAlchemyEvidenceRepository"]

from __future__ import annotations

from typing import Dict, List, Optional, cast

from sqlalchemy.orm import Session

from src.domain.entities.evidence import Evidence
from src.domain.value_objects.confidence import EvidenceLevel
from src.infrastructure.mappers.evidence_mapper import EvidenceMapper
from src.models.database.evidence import (
    EvidenceLevel as DbEvidenceLevel,
    EvidenceType as DbEvidenceType,
)
from src.repositories.evidence_repository import EvidenceRepository


class SqlAlchemyEvidenceRepository:
    """Domain-facing repository adapter for evidence backed by SQLAlchemy."""

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session
        self._repository = EvidenceRepository(session)

    def create(self, evidence: Evidence) -> Evidence:
        model = EvidenceMapper.to_model(evidence)
        persisted = self._repository.create(model)
        return EvidenceMapper.to_domain(persisted)

    def get_by_id(self, evidence_id: int) -> Optional[Evidence]:
        model = self._repository.get_by_id(evidence_id)
        return EvidenceMapper.to_domain(model) if model else None

    def get_by_id_or_fail(self, evidence_id: int) -> Evidence:
        model = self._repository.get_by_id_or_fail(evidence_id)
        return EvidenceMapper.to_domain(model)

    def find_by_variant(
        self, variant_id: int, limit: Optional[int] = None
    ) -> List[Evidence]:
        models = self._repository.find_by_variant(variant_id, limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_phenotype(
        self, phenotype_id: int, limit: Optional[int] = None
    ) -> List[Evidence]:
        models = self._repository.find_by_phenotype(phenotype_id, limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_variant_and_phenotype(
        self, variant_id: int, phenotype_id: int
    ) -> List[Evidence]:
        models = self._repository.find_by_variant_and_phenotype(
            variant_id, phenotype_id
        )
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_publication(
        self, publication_id: int, limit: Optional[int] = None
    ) -> List[Evidence]:
        models = self._repository.find_by_publication(publication_id, limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_evidence_level(
        self, level: EvidenceLevel, limit: Optional[int] = None
    ) -> List[Evidence]:
        db_level = cast(DbEvidenceLevel, level.value)
        models = self._repository.find_by_evidence_level(db_level, limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_by_evidence_type(
        self, evidence_type: str, limit: Optional[int] = None
    ) -> List[Evidence]:
        db_type = cast(DbEvidenceType, evidence_type)
        models = self._repository.find_by_evidence_type(db_type, limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_high_confidence_evidence(
        self, limit: Optional[int] = None
    ) -> List[Evidence]:
        models = self._repository.find_high_confidence_evidence(limit)
        return EvidenceMapper.to_domain_sequence(models)

    def find_peer_reviewed_evidence(
        self, limit: Optional[int] = None
    ) -> List[Evidence]:
        models = self._repository.find_peer_reviewed_evidence(limit)
        return EvidenceMapper.to_domain_sequence(models)

    def get_evidence_statistics(self) -> Dict[str, object]:
        return self._repository.get_evidence_statistics()

    def find_relationship_evidence(
        self, variant_id: int, phenotype_id: int, min_confidence: float = 0.0
    ) -> List[Evidence]:
        models = self._repository.find_relationship_evidence(
            variant_id, phenotype_id, min_confidence
        )
        return EvidenceMapper.to_domain_sequence(models)

    def count(self) -> int:
        return self._repository.count()


__all__ = ["SqlAlchemyEvidenceRepository"]

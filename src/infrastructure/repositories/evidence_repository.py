"""SQLAlchemy-backed implementation of the domain evidence repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import and_, asc, desc, func, select

from src.domain.repositories.evidence_repository import (
    EvidenceRepository as EvidenceRepositoryInterface,
)
from src.infrastructure.mappers.evidence_mapper import EvidenceMapper
from src.models.database import EvidenceModel, VariantModel

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.orm import Session

    from src.domain.entities.evidence import Evidence
    from src.domain.repositories.base import QuerySpecification
    from src.type_definitions.common import EvidenceUpdate, QueryFilters


class SqlAlchemyEvidenceRepository(EvidenceRepositoryInterface):
    """Domain-facing repository adapter for evidence backed by SQLAlchemy."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            message = "Session is not configured"
            raise ValueError(message)
        return self._session

    def _to_domain(self, model: EvidenceModel | None) -> Evidence | None:
        return EvidenceMapper.to_domain(model) if model else None

    def _to_domain_sequence(self, models: list[EvidenceModel]) -> list[Evidence]:
        return EvidenceMapper.to_domain_sequence(models)

    def create(self, evidence: Evidence) -> Evidence:
        model = EvidenceMapper.to_model(evidence)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return EvidenceMapper.to_domain(model)

    def get_by_id(self, evidence_id: int) -> Evidence | None:
        return self._to_domain(self.session.get(EvidenceModel, evidence_id))

    def get_by_id_or_fail(self, evidence_id: int) -> Evidence:
        evidence = self.get_by_id(evidence_id)
        if evidence is None:
            message = f"Evidence with id {evidence_id} not found"
            raise ValueError(message)
        return evidence

    def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Evidence]:
        stmt = select(EvidenceModel)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def count(self) -> int:
        stmt = select(func.count()).select_from(EvidenceModel)
        return int(self.session.execute(stmt).scalar_one())

    def exists(self, evidence_id: int) -> bool:
        stmt = select(func.count()).where(EvidenceModel.id == evidence_id)
        return bool(self.session.execute(stmt).scalar_one())

    def delete(self, evidence_id: int) -> bool:
        model = self.session.get(EvidenceModel, evidence_id)
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    def update(self, evidence_id: int, updates: EvidenceUpdate) -> Evidence:
        model = self.session.get(EvidenceModel, evidence_id)
        if model is None:
            message = f"Evidence with id {evidence_id} not found"
            raise ValueError(message)
        for field, value in updates.items():
            if hasattr(model, field):
                setattr(model, field, value)
        self.session.commit()
        self.session.refresh(model)
        return EvidenceMapper.to_domain(model)

    def find_by_variant(
        self,
        variant_id: int,
        limit: int | None = None,
    ) -> list[Evidence]:
        stmt = select(EvidenceModel).where(EvidenceModel.variant_id == variant_id)
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_phenotype(
        self,
        phenotype_id: int,
        limit: int | None = None,
    ) -> list[Evidence]:
        stmt = select(EvidenceModel).where(EvidenceModel.phenotype_id == phenotype_id)
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_variant_and_phenotype(
        self,
        variant_id: int,
        phenotype_id: int,
    ) -> list[Evidence]:
        stmt = select(EvidenceModel).where(
            and_(
                EvidenceModel.variant_id == variant_id,
                EvidenceModel.phenotype_id == phenotype_id,
            ),
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_publication(
        self,
        publication_id: int,
        limit: int | None = None,
    ) -> list[Evidence]:
        stmt = select(EvidenceModel).where(
            EvidenceModel.publication_id == publication_id,
        )
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_gene(self, gene_id: int) -> list[Evidence]:
        stmt = (
            select(EvidenceModel)
            .join(EvidenceModel.variant)
            .where(VariantModel.gene_id == gene_id)
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_evidence_level(
        self,
        level: str,
        limit: int | None = None,
    ) -> list[Evidence]:
        stmt = select(EvidenceModel).where(EvidenceModel.evidence_level == level)
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_evidence_type(
        self,
        evidence_type: str,
        limit: int | None = None,
    ) -> list[Evidence]:
        stmt = select(EvidenceModel).where(EvidenceModel.evidence_type == evidence_type)
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_confidence_score(
        self,
        min_score: float,
        max_score: float,
    ) -> list[Evidence]:
        stmt = select(EvidenceModel).where(
            EvidenceModel.confidence_score >= min_score,
            EvidenceModel.confidence_score <= max_score,
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_high_confidence_evidence(
        self,
        limit: int | None = None,
    ) -> list[Evidence]:
        stmt = select(EvidenceModel).where(
            EvidenceModel.evidence_level.in_(["definitive", "strong"]),
        )
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_criteria(self, spec: QuerySpecification) -> list[Evidence]:
        stmt = select(EvidenceModel)
        for field, value in spec.filters.items():
            column = getattr(EvidenceModel, field, None)
            if column is not None and value is not None:
                stmt = stmt.where(column == value)
        if spec.offset:
            stmt = stmt.offset(spec.offset)
        if spec.limit:
            stmt = stmt.limit(spec.limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_source(self, source: str) -> list[Evidence]:
        if source:
            _ = source
        return []

    def find_relationship_evidence(
        self,
        variant_id: int,
        phenotype_id: int,
        min_confidence: float = 0.0,
    ) -> list[Evidence]:
        stmt = select(EvidenceModel).where(
            and_(
                EvidenceModel.variant_id == variant_id,
                EvidenceModel.phenotype_id == phenotype_id,
                EvidenceModel.confidence_score >= min_confidence,
            ),
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def search_evidence(
        self,
        query: str,
        limit: int = 10,
        filters: QueryFilters | None = None,
    ) -> list[Evidence]:
        stmt = select(EvidenceModel).limit(limit)
        if query:
            stmt = stmt.where(EvidenceModel.description.ilike(f"%{query}%"))
        if filters:
            for field, value in filters.items():
                column = getattr(EvidenceModel, field, None)
                if column is not None and value is not None:
                    stmt = stmt.where(column == value)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def paginate_evidence(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: QueryFilters | None = None,
    ) -> tuple[list[Evidence], int]:
        stmt = select(EvidenceModel)
        if filters:
            for field, value in filters.items():
                column = getattr(EvidenceModel, field, None)
                if column is not None and value is not None:
                    stmt = stmt.where(column == value)
        column = getattr(EvidenceModel, sort_by, None) if sort_by else None
        if column is not None:
            stmt = stmt.order_by(
                desc(column) if sort_order == "desc" else asc(column),
            )
        stmt = stmt.offset(max(page - 1, 0) * per_page).limit(per_page)
        models = list(self.session.execute(stmt).scalars())
        total = self.count()
        return self._to_domain_sequence(models), total

    def get_evidence_statistics(self) -> dict[str, int | float | bool | str | None]:
        total = self.count()
        high_confidence = len(self.find_high_confidence_evidence())
        return {
            "total_evidence": total,
            "high_confidence_evidence": high_confidence,
        }

    def find_conflicting_evidence(self, variant_id: int) -> list[Evidence]:
        stmt = select(EvidenceModel).where(
            and_(
                EvidenceModel.variant_id == variant_id,
                EvidenceModel.evidence_level == "conflicting",
            ),
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def update_evidence(self, evidence_id: int, updates: EvidenceUpdate) -> Evidence:
        return self.update(evidence_id, updates)


__all__ = ["SqlAlchemyEvidenceRepository"]

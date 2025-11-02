from __future__ import annotations

import json
from typing import Optional, Sequence, Tuple

from src.domain.entities.phenotype import Phenotype, PhenotypeCategory
from src.domain.value_objects.identifiers import PhenotypeIdentifier
from src.models.database.phenotype import PhenotypeModel


class PhenotypeMapper:
    """Maps between SQLAlchemy PhenotypeModel and domain Phenotype entities."""

    @staticmethod
    def to_domain(model: PhenotypeModel) -> Phenotype:
        identifier = PhenotypeIdentifier(hpo_id=model.hpo_id, hpo_term=model.hpo_term)
        synonyms = PhenotypeMapper._parse_synonyms(model.synonyms)

        return Phenotype(
            identifier=identifier,
            name=model.name,
            definition=model.definition,
            synonyms=synonyms,
            category=model.category or PhenotypeCategory.OTHER,
            parent_hpo_id=model.parent_hpo_id,
            is_root_term=model.is_root_term,
            frequency_in_med13=model.frequency_in_med13,
            severity_score=model.severity_score,
            created_at=model.created_at,
            updated_at=model.updated_at,
            id=model.id,
        )

    @staticmethod
    def to_model(
        entity: Phenotype, model: Optional[PhenotypeModel] = None
    ) -> PhenotypeModel:
        target = model or PhenotypeModel()
        target.hpo_id = entity.identifier.hpo_id
        target.hpo_term = entity.identifier.hpo_term
        target.name = entity.name
        target.definition = entity.definition
        target.synonyms = PhenotypeMapper._serialize_synonyms(entity.synonyms)
        target.category = entity.category
        target.parent_hpo_id = entity.parent_hpo_id
        target.is_root_term = entity.is_root_term
        target.frequency_in_med13 = entity.frequency_in_med13
        target.severity_score = entity.severity_score
        if entity.created_at:
            target.created_at = entity.created_at
        if entity.updated_at:
            target.updated_at = entity.updated_at
        return target

    @staticmethod
    def to_domain_sequence(models: Sequence[PhenotypeModel]) -> list[Phenotype]:
        return [PhenotypeMapper.to_domain(model) for model in models]

    @staticmethod
    def _parse_synonyms(raw_synonyms: Optional[str]) -> Tuple[str, ...]:
        if not raw_synonyms:
            return ()
        try:
            parsed = json.loads(raw_synonyms)
            if isinstance(parsed, list):
                return tuple(str(item).strip() for item in parsed if str(item).strip())
        except json.JSONDecodeError:
            pass
        return tuple(
            token.strip() for token in raw_synonyms.split(",") if token.strip()
        )

    @staticmethod
    def _serialize_synonyms(synonyms: Tuple[str, ...]) -> Optional[str]:
        if not synonyms:
            return None
        return json.dumps(list(synonyms))


__all__ = ["PhenotypeMapper"]

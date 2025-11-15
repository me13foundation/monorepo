"""Application service for orchestrating PubMed ingestion per data source."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.domain.entities.data_source_configs import PubMedQueryConfig
from src.domain.entities.publication import Publication  # noqa: TCH001
from src.domain.entities.user_data_source import (
    SourceConfiguration,
    SourceType,
    UserDataSource,
)
from src.domain.services.pubmed_ingestion import PubMedGateway, PubMedIngestionSummary
from src.domain.transform.transformers.pubmed_record_transformer import (
    PubMedRecordTransformer,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from src.domain.repositories.publication_repository import PublicationRepository
    from src.type_definitions.common import (
        PublicationUpdate,
        RawRecord,
        SourceMetadata,
    )


class PubMedIngestionService:
    """Coordinate fetching, transforming, and persisting PubMed data per source."""

    def __init__(
        self,
        gateway: PubMedGateway,
        publication_repository: PublicationRepository,
        transformer: PubMedRecordTransformer | None = None,
    ) -> None:
        self._gateway = gateway
        self._publication_repository = publication_repository
        self._transformer = transformer or PubMedRecordTransformer()

    async def ingest(self, source: UserDataSource) -> PubMedIngestionSummary:
        """Execute ingestion for a PubMed data source."""
        self._assert_source_type(source)
        config = self._build_config(source.configuration)

        raw_records = await self._gateway.fetch_records(config)
        publications = self._transform_records(raw_records)
        created, updated = self._persist_publications(publications)

        return PubMedIngestionSummary(
            source_id=source.id,
            fetched_records=len(raw_records),
            parsed_publications=len(publications),
            created_publications=created,
            updated_publications=updated,
        )

    def _transform_records(self, records: Iterable[RawRecord]) -> list[Publication]:
        transformed: list[Publication] = []
        for record in records:
            try:
                publication = self._transformer.to_publication(record)
            except ValueError:
                continue
            transformed.append(publication)
        return transformed

    def _persist_publications(
        self,
        publications: Iterable[Publication],
    ) -> tuple[int, int]:
        created = 0
        updated = 0
        for publication in publications:
            pmid = publication.identifier.pubmed_id
            if pmid and (existing := self._publication_repository.find_by_pmid(pmid)):
                if existing.id is None:
                    continue
                updates = self._build_update_payload(publication)
                self._publication_repository.update_publication(existing.id, updates)
                updated += 1
            else:
                self._publication_repository.create(publication)
                created += 1
        return created, updated

    @staticmethod
    def _build_update_payload(publication: Publication) -> PublicationUpdate:
        return {
            "title": publication.title,
            "authors": list(publication.authors),
            "journal": publication.journal,
            "publication_year": publication.publication_year,
            "abstract": publication.abstract,
            "doi": publication.identifier.doi,
            "pmid": publication.identifier.pubmed_id,
        }

    @staticmethod
    def _build_config(configuration: SourceConfiguration) -> PubMedQueryConfig:
        metadata: SourceMetadata = dict(configuration.metadata or {})
        return PubMedQueryConfig.model_validate(metadata)

    @staticmethod
    def _assert_source_type(source: UserDataSource) -> None:
        if source.source_type != SourceType.PUBMED:
            message = (
                f"PubMed ingestion can only be executed for PubMed sources "
                f"(got {source.source_type.value})"
            )
            raise ValueError(message)

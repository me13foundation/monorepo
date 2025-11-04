"""
Mapper for UserDataSource entities and database models.

Provides bidirectional mapping between domain entities and database models
for the Data Sources module.
"""

from datetime import datetime
from uuid import UUID

from src.domain.entities.user_data_source import (
    UserDataSource,
    SourceType,
    SourceStatus,
    IngestionSchedule,
    QualityMetrics,
    SourceConfiguration,
)
from src.models.database import UserDataSourceModel


class UserDataSourceMapper:
    """
    Bidirectional mapper between UserDataSource domain entities and database models.

    Handles conversion between domain objects and database representations,
    ensuring type safety and data integrity.
    """

    @staticmethod
    def to_domain(model: UserDataSourceModel) -> UserDataSource:
        """
        Convert a database model to a domain entity.

        Args:
            model: The UserDataSourceModel to convert

        Returns:
            The corresponding UserDataSource domain entity
        """
        # Timestamps are handled by SQLAlchemy as datetime objects
        created_at = model.created_at
        updated_at = model.updated_at
        last_ingested_at = None
        if model.last_ingested_at:
            last_ingested_at = datetime.fromisoformat(model.last_ingested_at)

        # Build configuration
        configuration = SourceConfiguration(**model.configuration)

        # Build ingestion schedule
        ingestion_schedule = IngestionSchedule(**model.ingestion_schedule)

        # Build quality metrics
        quality_metrics = QualityMetrics(**model.quality_metrics)

        return UserDataSource(
            id=UUID(model.id),
            owner_id=UUID(model.owner_id),
            name=model.name,
            description=model.description,
            source_type=SourceType(model.source_type),
            template_id=UUID(model.template_id) if model.template_id else None,
            configuration=configuration,
            status=SourceStatus(model.status),
            ingestion_schedule=ingestion_schedule,
            quality_metrics=quality_metrics,
            created_at=created_at,
            updated_at=updated_at,
            last_ingested_at=last_ingested_at,
            tags=model.tags or [],
            version=model.version,
        )

    @staticmethod
    def to_model(entity: UserDataSource) -> UserDataSourceModel:
        """
        Convert a domain entity to a database model.

        Args:
            entity: The UserDataSource entity to convert

        Returns:
            The corresponding UserDataSourceModel
        """
        return UserDataSourceModel(
            id=str(entity.id),
            owner_id=str(entity.owner_id),
            name=entity.name,
            description=entity.description,
            source_type=entity.source_type.value,
            template_id=str(entity.template_id) if entity.template_id else None,
            configuration=entity.configuration.model_dump(),
            status=entity.status.value,
            ingestion_schedule=entity.ingestion_schedule.model_dump(),
            quality_metrics=entity.quality_metrics.model_dump(),
            last_ingested_at=(
                entity.last_ingested_at.isoformat() if entity.last_ingested_at else None
            ),
            tags=entity.tags,
            version=entity.version,
        )

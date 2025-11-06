"""
Ingestion Job SQLAlchemy model for MED13 Resource Library.

Database representation of data ingestion job executions with
relationships and constraints for the Data Sources module.
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user_data_source import UserDataSourceModel


class IngestionStatusEnum(SQLEnum):
    """SQLAlchemy enum for ingestion job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class IngestionTriggerEnum(SQLEnum):
    """SQLAlchemy enum for ingestion job triggers."""

    MANUAL = "manual"
    SCHEDULED = "scheduled"
    API = "api"
    WEBHOOK = "webhook"
    RETRY = "retry"


class IngestionJobModel(Base):
    """
    SQLAlchemy model for data ingestion job executions.

    Tracks the complete lifecycle of data acquisition from user sources,
    including performance metrics, errors, and provenance information.
    """

    __tablename__ = "ingestion_jobs"

    # Primary key
    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True)

    # Source relationship
    source_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("user_data_sources.id"),
        nullable=False,
        index=True,
    )

    # Execution details
    trigger: Mapped[IngestionTriggerEnum] = mapped_column(
        IngestionTriggerEnum,
        nullable=False,
    )
    triggered_by: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        nullable=True,
        index=True,
    )
    triggered_at: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    # Status and progress
    status: Mapped[IngestionStatusEnum] = mapped_column(
        IngestionStatusEnum,
        nullable=False,
        default=IngestionStatusEnum.PENDING,
        index=True,
    )
    started_at: Mapped[str | None] = mapped_column(String(30), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Results and metrics
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # Provenance and metadata
    provenance: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    job_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Configuration snapshot
    source_config_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Relationships
    source: Mapped["UserDataSourceModel"] = relationship(
        "UserDataSourceModel",
        back_populates="ingestion_jobs",
    )

    def __repr__(self) -> str:
        """String representation of the ingestion job."""
        return f"<IngestionJob(id={self.id}, source={self.source_id}, status={self.status})>"

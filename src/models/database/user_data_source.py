"""
User Data Source SQLAlchemy model for MED13 Resource Library.

Database representation of user-managed data sources with relationships
and constraints for the Data Sources module.
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import (
    String,
    Text,
    JSON,
    Enum as SQLEnum,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base

if TYPE_CHECKING:
    from .source_template import SourceTemplateModel
    from .ingestion_job import IngestionJobModel


class SourceTypeEnum(SQLEnum):
    """SQLAlchemy enum for source types."""

    FILE_UPLOAD = "file_upload"
    API = "api"
    DATABASE = "database"
    WEB_SCRAPING = "web_scraping"


class SourceStatusEnum(SQLEnum):
    """SQLAlchemy enum for source status."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING_REVIEW = "pending_review"
    ARCHIVED = "archived"


class UserDataSourceModel(Base):
    """
    SQLAlchemy model for user-managed data sources.

    Stores configuration and metadata for data sources created by users,
    with relationships to templates and ingestion jobs.
    """

    __tablename__ = "user_data_sources"

    # Primary key
    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True)

    # Ownership
    owner_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        nullable=False,
        index=True,
        doc="User who created this source",
    )

    # Basic information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Configuration
    source_type: Mapped[SourceTypeEnum] = mapped_column(
        SourceTypeEnum, nullable=False, index=True
    )
    template_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("source_templates.id"),
        nullable=True,
        index=True,
    )
    configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Status and lifecycle
    status: Mapped[SourceStatusEnum] = mapped_column(
        SourceStatusEnum, nullable=False, default=SourceStatusEnum.DRAFT, index=True
    )
    ingestion_schedule: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Quality metrics
    quality_metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Timestamps
    last_ingested_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")

    # Relationships
    template: Mapped[Optional["SourceTemplateModel"]] = relationship(
        "SourceTemplateModel", back_populates="sources"
    )
    ingestion_jobs: Mapped[List["IngestionJobModel"]] = relationship(
        "IngestionJobModel", back_populates="source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of the user data source."""
        return (
            f"<UserDataSource(id={self.id}, name='{self.name}', status={self.status})>"
        )

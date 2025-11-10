"""
Source Template SQLAlchemy model for MED13 Resource Library.

Database representation of reusable data source templates with
relationships and constraints for the Data Sources module.
"""

from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user_data_source import UserDataSourceModel


class TemplateCategoryEnum(str, Enum):
    """SQLAlchemy enum for template categories."""

    CLINICAL = "clinical"
    RESEARCH = "research"
    LITERATURE = "literature"
    GENOMIC = "genomic"
    PHENOTYPIC = "phenotypic"
    ONTOLOGY = "ontology"
    OTHER = "other"


class SourceTypeEnum(str, Enum):
    """SQLAlchemy enum for source types."""

    FILE_UPLOAD = "file_upload"
    API = "api"
    DATABASE = "database"
    WEB_SCRAPING = "web_scraping"


class SourceTemplateModel(Base):
    """
    SQLAlchemy model for data source templates.

    Stores reusable configurations for common biomedical data sources,
    enabling users to quickly set up new sources with validated settings.
    """

    __tablename__ = "source_templates"

    # Primary key
    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True)

    # Ownership
    created_by: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        nullable=False,
        index=True,
        doc="User who created this template",
    )

    # Basic information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[TemplateCategoryEnum] = mapped_column(
        SQLEnum(TemplateCategoryEnum),
        nullable=False,
        default=TemplateCategoryEnum.OTHER,
        index=True,
    )

    # Template definition
    source_type: Mapped[SourceTypeEnum] = mapped_column(
        SQLEnum(SourceTypeEnum),
        nullable=False,
        index=True,
    )
    schema_definition: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    validation_rules: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # UI configuration
    ui_config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Governance
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    approval_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Timestamps
    approved_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Metadata
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    compatibility_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0",
    )

    # Relationships
    sources: Mapped[list["UserDataSourceModel"]] = relationship(
        "UserDataSourceModel",
        back_populates="template",
    )

    def __repr__(self) -> str:
        """String representation of the source template."""
        return f"<SourceTemplate(id={self.id}, name='{self.name}', public={self.is_public})>"

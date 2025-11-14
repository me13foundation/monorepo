from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.type_definitions.common import JSONObject  # noqa: TC001

from .base import Base


class DataDiscoverySessionModel(Base):
    """
    SQLAlchemy model for data discovery sessions.

    Stores user data discovery sessions with their state and configuration.
    """

    __tablename__ = "data_discovery_sessions"

    # Primary key
    # Use String for SQLite compatibility (stores UUIDs as strings, handles legacy integers)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Ownership and context
    # Use String for SQLite compatibility (stores UUIDs as strings, handles legacy integers)
    owner_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        doc="User who owns this session",
    )
    research_space_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("research_spaces.id"),
        nullable=True,
        index=True,
        doc="Research space this session belongs to",
    )

    # Basic information
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="Untitled Session",
    )

    # Current parameters (stored as JSON)
    gene_symbol: Mapped[str | None] = mapped_column(String(100), nullable=True)
    search_term: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Session state
    selected_sources: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="IDs of selected catalog entries",
    )
    tested_sources: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="IDs of tested catalog entries",
    )

    # Statistics
    total_tests_run: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    test_results = relationship(
        "QueryTestResultModel",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class SourceCatalogEntryModel(Base):
    """
    SQLAlchemy model for source catalog entries.

    Stores the catalog of available data sources for the workbench.
    """

    __tablename__ = "source_catalog_entries"

    # Primary key (using string ID for flexibility)
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Basic information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Classification and search
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Query capabilities
    param_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    url_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    api_endpoint: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Governance
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requires_auth: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Template integration
    source_template_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("source_templates.id"),
        nullable=True,
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class QueryTestResultModel(Base):
    """
    SQLAlchemy model for query test results.

    Stores the results of testing queries against data sources.
    """

    __tablename__ = "query_test_results"

    # Primary key
    # Use String for SQLite compatibility (stores UUIDs as strings)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Relationships
    # Use String for SQLite compatibility (stores UUIDs as strings)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("data_discovery_sessions.id"),
        nullable=False,
        index=True,
    )
    catalog_entry_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("source_catalog_entries.id"),
        nullable=False,
        index=True,
    )

    # Test execution
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Parameters used (stored as JSON for flexibility)
    gene_symbol: Mapped[str | None] = mapped_column(String(100), nullable=True)
    search_term: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Results
    response_data: Mapped[JSONObject | None] = mapped_column(JSON, nullable=True)
    response_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    session = relationship("DataDiscoverySessionModel", back_populates="test_results")

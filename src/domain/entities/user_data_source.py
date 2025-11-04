"""
Domain entities for user-managed data sources in MED13 Resource Library.

These entities represent user-configured data sources that extend the core system
with additional biomedical data while maintaining provenance and quality standards.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class SourceType(str, Enum):
    """Types of data sources supported for user management."""

    FILE_UPLOAD = "file_upload"
    API = "api"
    DATABASE = "database"
    WEB_SCRAPING = "web_scraping"  # Future use


class SourceStatus(str, Enum):
    """Status of a user data source."""

    DRAFT = "draft"  # Being configured
    ACTIVE = "active"  # Actively ingesting
    INACTIVE = "inactive"  # Temporarily disabled
    ERROR = "error"  # Failed configuration/validation
    PENDING_REVIEW = "pending_review"  # Awaiting curator approval
    ARCHIVED = "archived"  # No longer used


class SourceConfiguration(BaseModel):
    """
    Configuration for a specific data source type.

    This is a flexible schema that adapts based on source_type.
    Each source type has its own validation rules and required fields.
    """

    model_config = ConfigDict(extra="allow")  # Allow additional fields per source type

    # Common fields
    url: Optional[str] = Field(None, description="Source URL for API/database sources")
    file_path: Optional[str] = Field(None, description="File path for uploaded files")
    format: Optional[str] = Field(
        None, description="Data format (json, csv, xml, etc.)"
    )

    # Authentication
    auth_type: Optional[str] = Field(None, description="Authentication method")
    auth_credentials: Optional[Dict[str, Any]] = Field(
        None, description="Authentication credentials"
    )

    # Rate limiting
    requests_per_minute: Optional[int] = Field(
        None, ge=1, le=1000, description="API rate limit"
    )

    # Data mapping
    field_mapping: Optional[Dict[str, str]] = Field(
        None, description="Field name mappings"
    )

    # Source-specific metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional source-specific metadata"
    )

    @field_validator("requests_per_minute")
    @classmethod
    def validate_rate_limit(cls, v: Optional[int]) -> Optional[int]:
        """Validate rate limit is reasonable."""
        if v is not None and v < 1:
            raise ValueError("Requests per minute must be at least 1")
        return v


class IngestionSchedule(BaseModel):
    """Schedule configuration for automated data ingestion."""

    enabled: bool = Field(
        default=False, description="Whether scheduled ingestion is enabled"
    )
    frequency: str = Field(
        default="manual",
        description="Ingestion frequency (manual, hourly, daily, weekly)",
    )
    start_time: Optional[datetime] = Field(None, description="Scheduled start time")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        """Validate frequency is supported."""
        allowed = ["manual", "hourly", "daily", "weekly"]
        if v not in allowed:
            raise ValueError(f"Frequency must be one of: {allowed}")
        return v


class QualityMetrics(BaseModel):
    """Quality metrics for a data source."""

    completeness_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Data completeness (0-1)"
    )
    consistency_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Data consistency (0-1)"
    )
    timeliness_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Data timeliness (0-1)"
    )
    overall_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Overall quality score (0-1)"
    )

    last_assessed: Optional[datetime] = Field(
        None, description="When quality was last assessed"
    )
    issues_count: int = Field(default=0, description="Number of quality issues found")


class UserDataSource(BaseModel):
    """
    Domain entity representing a user-managed data source.

    This is the core entity for the Data Sources module, representing
    a biomedical data source configured and managed by a user.
    """

    model_config = ConfigDict(frozen=True)  # Immutable - changes create new instances

    # Identity
    id: UUID = Field(..., description="Unique identifier for the data source")
    owner_id: UUID = Field(..., description="User who created this source")

    # Basic information
    name: str = Field(
        ..., min_length=1, max_length=200, description="Human-readable source name"
    )
    description: str = Field(
        "", max_length=1000, description="Detailed description of the source"
    )

    # Configuration
    source_type: SourceType = Field(..., description="Type of data source")
    template_id: Optional[UUID] = Field(
        None, description="Template used to create this source"
    )
    configuration: SourceConfiguration = Field(
        ..., description="Source-specific configuration"
    )

    # Status and lifecycle
    status: SourceStatus = Field(
        default=SourceStatus.DRAFT, description="Current status"
    )
    ingestion_schedule: IngestionSchedule = Field(
        default_factory=lambda: IngestionSchedule(
            enabled=False,
            frequency="manual",
            start_time=None,
            timezone="UTC",
        ),
        description="Ingestion scheduling",
    )

    # Quality and metrics
    quality_metrics: QualityMetrics = Field(
        default_factory=lambda: QualityMetrics(
            completeness_score=None,
            consistency_score=None,
            timeliness_score=None,
            overall_score=None,
            last_assessed=None,
            issues_count=0,
        ),
        description="Quality assessment results",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When source was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When source was last updated",
    )
    last_ingested_at: Optional[datetime] = Field(
        None, description="When data was last successfully ingested"
    )

    # Metadata
    tags: List[str] = Field(
        default_factory=list, description="User-defined tags for organization"
    )
    version: str = Field(default="1.0", description="Source configuration version")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate source name."""
        if not v.strip():
            raise ValueError("Source name cannot be empty or whitespace")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags are reasonable."""
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        for tag in v:
            if len(tag) > 50:
                raise ValueError("Tag length cannot exceed 50 characters")
        return [tag.strip().lower() for tag in v if tag.strip()]

    def is_active(self) -> bool:
        """Check if source is actively ingesting data."""
        return self.status == SourceStatus.ACTIVE

    def can_ingest(self) -> bool:
        """Check if source is eligible for data ingestion."""
        return self.status in [SourceStatus.ACTIVE, SourceStatus.DRAFT]

    def update_status(self, new_status: SourceStatus) -> "UserDataSource":
        """Create new instance with updated status."""
        return self.model_copy(
            update={"status": new_status, "updated_at": datetime.now(timezone.utc)}
        )

    def update_quality_metrics(self, metrics: QualityMetrics) -> "UserDataSource":
        """Create new instance with updated quality metrics."""
        return self.model_copy(
            update={
                "quality_metrics": metrics,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def record_ingestion(
        self, timestamp: Optional[datetime] = None
    ) -> "UserDataSource":
        """Create new instance with updated ingestion timestamp."""
        ingestion_time = timestamp or datetime.now(timezone.utc)
        return self.model_copy(
            update={
                "last_ingested_at": ingestion_time,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def update_configuration(self, config: SourceConfiguration) -> "UserDataSource":
        """Create new instance with updated configuration."""
        return self.model_copy(
            update={
                "configuration": config,
                "updated_at": datetime.now(timezone.utc),
                "version": self._increment_version(),
            }
        )

    def _increment_version(self) -> str:
        """Increment version number for configuration changes."""
        try:
            major, minor = self.version.split(".")
            return f"{major}.{int(minor) + 1}"
        except (ValueError, IndexError):
            return "1.0"

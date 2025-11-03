"""
Domain-specific type definitions for MED13 Resource Library.

Contains types for domain entities, value objects, and domain operations.
"""

from typing import Dict, List, Optional, Protocol, TypeVar, Any, TypedDict
import abc
from datetime import datetime
from .common import ValidationResult, EntityStatus, PriorityLevel


# Generic types for domain operations
T = TypeVar(
    "T", contravariant=True
)  # Generic entity type (contravariant for protocols)
ID = TypeVar("ID")  # Generic ID type


# Domain entity identifiers
GeneIdentifier = str
VariantIdentifier = str
PhenotypeIdentifier = str
EvidenceIdentifier = str
PublicationIdentifier = str


# Domain operation result types
class DomainOperationResult(TypedDict, total=False):
    """Result of a domain operation."""

    success: bool
    entity: Optional[Any]
    errors: List[str]
    warnings: List[str]
    validation_result: ValidationResult


# Business rule validation types
class BusinessRuleViolation(TypedDict):
    """Business rule violation details."""

    rule_name: str
    entity_type: str
    entity_id: str
    violation_type: str
    message: str
    severity: str
    suggested_fix: Optional[str]


class BusinessRuleValidationResult(TypedDict):
    """Result of business rule validation."""

    is_valid: bool
    violations: List[BusinessRuleViolation]
    entity_type: str
    entity_id: str
    validated_at: datetime


# Relationship types
class GeneVariantRelationship(TypedDict):
    """Gene-variant relationship data."""

    gene_id: str
    variant_id: str
    relationship_type: str
    confidence_score: float
    evidence_count: int
    last_updated: datetime


class VariantPhenotypeRelationship(TypedDict):
    """Variant-phenotype relationship data."""

    variant_id: str
    phenotype_id: str
    evidence_level: str
    confidence_score: float
    publications: List[str]
    inheritance_pattern: Optional[str]


class EvidencePublicationRelationship(TypedDict):
    """Evidence-publication relationship data."""

    evidence_id: str
    publication_id: str
    citation_type: str
    relevance_score: float


# Domain service operation types
class GeneAnalysisResult(TypedDict):
    """Result of gene analysis operations."""

    gene_id: str
    variant_count: int
    phenotype_count: int
    evidence_count: int
    clinical_significance_summary: Dict[str, int]
    population_frequency_range: Dict[str, float]
    inheritance_patterns: List[str]


class VariantAnalysisResult(TypedDict):
    """Result of variant analysis operations."""

    variant_id: str
    gene_id: str
    clinical_significance: str
    evidence_levels: Dict[str, int]
    phenotype_associations: List[str]
    population_frequency: Dict[str, float]
    functional_predictions: Dict[str, str]


class EvidenceConsistencyResult(TypedDict):
    """Result of evidence consistency analysis."""

    evidence_id: str
    is_consistent: bool
    conflicts: List[str]
    supporting_evidence: List[str]
    confidence_score: float
    last_reviewed: datetime


# Curation workflow types
class CurationDecision(TypedDict):
    """Curation decision data."""

    entity_id: str
    entity_type: str
    decision: str  # approve, reject, quarantine
    curator_id: str
    decision_date: datetime
    comments: Optional[str]
    confidence_score: float


class CurationQueueItem(TypedDict):
    """Item in curation queue."""

    entity_id: str
    entity_type: str
    priority: PriorityLevel
    status: EntityStatus
    queued_date: datetime
    last_modified: datetime
    validation_errors: List[str]
    evidence_count: int


# Domain event types
class DomainEvent(TypedDict):
    """Base domain event structure."""

    event_type: str
    entity_type: str
    entity_id: str
    timestamp: datetime
    user_id: Optional[str]
    details: Dict[str, Any]


class GeneCreatedEvent(DomainEvent):
    """Gene created event."""

    gene_data: Dict[str, Any]


class VariantUpdatedEvent(DomainEvent):
    """Variant updated event."""

    changes: Dict[str, Any]
    old_values: Dict[str, Any]


class EvidenceValidatedEvent(DomainEvent):
    """Evidence validated event."""

    validation_result: ValidationResult


# Validation rule types
class ValidationRule(Protocol):
    """Protocol for validation rules."""

    @abc.abstractmethod
    def validate(self, entity: Any) -> ValidationResult:
        """Validate an entity against this rule."""
        ...


class SyntacticValidationRule(ValidationRule):
    """Syntactic validation rule (format/structure)."""

    @abc.abstractmethod
    def validate(self, entity: Any) -> ValidationResult:
        """Validate entity syntax."""
        ...


class SemanticValidationRule(ValidationRule):
    """Semantic validation rule (business logic)."""

    @abc.abstractmethod
    def validate(self, entity: Any) -> ValidationResult:
        """Validate entity semantics."""
        ...


class CompletenessValidationRule(ValidationRule):
    """Completeness validation rule (required fields)."""

    @abc.abstractmethod
    def validate(self, entity: Any) -> ValidationResult:
        """Validate entity completeness."""
        ...


# Normalization types
class NormalizationResult(TypedDict, total=False):
    """Result of data normalization."""

    original_value: Any
    normalized_value: Any
    normalization_method: str
    confidence_score: float
    alternatives: List[Any]


class IdentifierNormalizationResult(NormalizationResult):
    """Result of identifier normalization."""

    identifier_type: str
    source: str
    canonical_form: str


# Provenance types
class ProvenanceChain(TypedDict):
    """Chain of data provenance."""

    source: str
    source_version: Optional[str]
    acquired_at: datetime
    processing_steps: List[str]
    derived_from: Optional[List[str]]
    quality_score: float
    validation_status: str


# Quality metrics types
class QualityMetrics(TypedDict):
    """Quality metrics for data entities."""

    completeness_score: float
    consistency_score: float
    accuracy_score: float
    timeliness_score: float
    measured_at: datetime
    entity_type: str
    entity_id: str


class DataQualityReport(TypedDict):
    """Comprehensive data quality report."""

    overall_score: float
    metrics_by_type: Dict[str, QualityMetrics]
    issues_found: List[str]
    recommendations: List[str]
    generated_at: datetime
    coverage: Dict[str, int]  # entity_type -> count

"""
Domain validation framework for MED13 Resource Library.

Provides comprehensive validation rules, quality gates, and reporting
systems to ensure data quality throughout the ETL pipeline.

Components:
- Rules: Advanced business logic validation rules
- Gates: Quality gate orchestration and checkpoints
- Reporting: Error reporting, metrics, and dashboards
"""

from .rules import (
    DataQualityValidator,
    ValidationRule,
    GeneValidationRules,
    VariantValidationRules,
    PhenotypeValidationRules,
    PublicationValidationRules,
    RelationshipValidationRules,
    ValidationRuleEngine,
)
from .gates import (
    QualityGate,
    ValidationPipeline,
    GateResult,
    QualityGateOrchestrator,
)
from .reporting import (
    ValidationReport,
    ErrorReporter,
    MetricsCollector,
    ValidationDashboard,
)

__all__ = [
    # Rules
    "ValidationRule",
    "DataQualityValidator",
    "GeneValidationRules",
    "VariantValidationRules",
    "PhenotypeValidationRules",
    "PublicationValidationRules",
    "RelationshipValidationRules",
    "ValidationRuleEngine",
    # Gates
    "QualityGate",
    "ValidationPipeline",
    "GateResult",
    "QualityGateOrchestrator",
    # Reporting
    "ValidationReport",
    "ErrorReporter",
    "MetricsCollector",
    "ValidationDashboard",
]

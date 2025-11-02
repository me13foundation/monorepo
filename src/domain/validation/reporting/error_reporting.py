"""Typed error reporting utilities used by the validation tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ..rules.base_rules import ValidationSeverity


class ErrorCategory(Enum):
    FORMAT = "format"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    RELATIONSHIP = "relationship"
    OTHER = "other"


class ErrorPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ErrorReport:
    error_id: str
    category: ErrorCategory
    priority: ErrorPriority
    severity: ValidationSeverity
    entity_type: str
    entity_id: Optional[str]
    field: str
    rule: str
    message: str
    suggestion: Optional[str]
    context: Dict[str, Any]
    timestamp: datetime
    source: str
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class ErrorSummary:
    total_errors: int
    by_category: Dict[str, int]
    by_priority: Dict[str, int]
    by_severity: Dict[str, int]
    critical_issues: List[ErrorReport] = field(default_factory=list)


class ErrorReporter:
    """Minimal error reporter with typed summaries."""

    def __init__(self) -> None:
        self._errors: List[ErrorReport] = []
        self._counter = 0

    # ------------------------------------------------------------------ #
    # Recording
    # ------------------------------------------------------------------ #

    def add_error(
        self,
        entity_type: str,
        entity_id: Optional[str],
        field: str,
        rule: str,
        message: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        source: str = "validation",
    ) -> ErrorReport:
        report = ErrorReport(
            error_id=self._next_id(),
            category=self._categorise(rule, message),
            priority=self._priority_for(severity),
            severity=severity,
            entity_type=entity_type,
            entity_id=entity_id,
            field=field,
            rule=rule,
            message=message,
            suggestion=suggestion,
            context=context or {},
            timestamp=datetime.now(UTC),
            source=source,
        )
        self._errors.append(report)
        return report

    def resolve_error(self, error_id: str, notes: Optional[str] = None) -> None:
        for report in self._errors:
            if report.error_id == error_id:
                report.resolved = True
                report.resolution_notes = notes
                break

    # ------------------------------------------------------------------ #
    # Summaries
    # ------------------------------------------------------------------ #

    def get_error_summary(
        self,
        include_resolved: bool = False,
        time_range_hours: int = 24,
    ) -> ErrorSummary:
        cutoff = datetime.now(UTC) - timedelta(hours=time_range_hours)
        filtered = [
            err
            for err in self._errors
            if err.timestamp >= cutoff and (include_resolved or not err.resolved)
        ]

        by_category: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        critical: List[ErrorReport] = []

        for err in filtered:
            by_category.setdefault(err.category.value, 0)
            by_category[err.category.value] += 1

            by_priority.setdefault(err.priority.value, 0)
            by_priority[err.priority.value] += 1

            severity_key = err.severity.name.lower()
            by_severity.setdefault(severity_key, 0)
            by_severity[severity_key] += 1

            if err.priority is ErrorPriority.CRITICAL:
                critical.append(err)

        return ErrorSummary(
            total_errors=len(filtered),
            by_category=by_category,
            by_priority=by_priority,
            by_severity=by_severity,
            critical_issues=critical,
        )

    def get_error_trends(self, time_range_hours: int = 24) -> List[Dict[str, Any]]:
        summary = self.get_error_summary(time_range_hours=time_range_hours)
        return [
            {"category": category, "count": count}
            for category, count in summary.by_category.items()
        ]

    def get_resolution_rate(self, time_range_hours: int = 24) -> float:
        cutoff = datetime.now(UTC) - timedelta(hours=time_range_hours)
        filtered = [err for err in self._errors if err.timestamp >= cutoff]
        if not filtered:
            return 0.0
        resolved = sum(1 for err in filtered if err.resolved)
        return resolved / len(filtered)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _next_id(self) -> str:
        self._counter += 1
        return f"ERR-{self._counter:06d}"

    @staticmethod
    def _priority_for(severity: ValidationSeverity) -> ErrorPriority:
        if severity is ValidationSeverity.ERROR:
            return ErrorPriority.HIGH
        if severity is ValidationSeverity.WARNING:
            return ErrorPriority.MEDIUM
        return ErrorPriority.LOW

    @staticmethod
    def _categorise(rule: str, message: str) -> ErrorCategory:
        text = f"{rule} {message}".lower()
        if any(keyword in text for keyword in ("format", "syntax", "invalid")):
            return ErrorCategory.FORMAT
        if any(keyword in text for keyword in ("missing", "required", "empty")):
            return ErrorCategory.COMPLETENESS
        if any(keyword in text for keyword in ("inconsistent", "mismatch")):
            return ErrorCategory.CONSISTENCY
        if "relationship" in text:
            return ErrorCategory.RELATIONSHIP
        if any(keyword in text for keyword in ("incorrect", "wrong")):
            return ErrorCategory.ACCURACY
        return ErrorCategory.OTHER


__all__ = [
    "ErrorCategory",
    "ErrorPriority",
    "ErrorReport",
    "ErrorSummary",
    "ErrorReporter",
]

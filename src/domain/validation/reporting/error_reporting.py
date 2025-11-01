"""
Comprehensive error reporting system for validation issues.

Provides structured error reporting with categorization, prioritization,
and actionable recommendations for data quality issues.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from ..rules.base_rules import ValidationSeverity


class ErrorCategory(Enum):
    """Categories of validation errors."""

    FORMAT = "format"  # Data format issues
    CONSISTENCY = "consistency"  # Data consistency problems
    COMPLETENESS = "completeness"  # Missing or incomplete data
    ACCURACY = "accuracy"  # Incorrect or inaccurate data
    TIMELINESS = "timeliness"  # Time-related issues
    RELATIONSHIP = "relationship"  # Relationship validation issues
    BUSINESS_LOGIC = "business_logic"  # Domain-specific business rules


class ErrorPriority(Enum):
    """Priority levels for error resolution."""

    CRITICAL = "critical"  # Blocks processing/release
    HIGH = "high"  # Should be fixed soon
    MEDIUM = "medium"  # Should be addressed
    LOW = "low"  # Nice to fix
    INFO = "info"  # Informational only


@dataclass
class ErrorReport:
    """Structured error report."""

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
    assigned_to: Optional[str] = None


@dataclass
class ErrorSummary:
    """Summary of errors by category and priority."""

    total_errors: int
    by_category: Dict[str, int]
    by_priority: Dict[str, int]
    by_severity: Dict[str, int]
    critical_issues: List[ErrorReport]
    top_patterns: List[Dict[str, Any]]


class ErrorReporter:
    """
    Comprehensive error reporting system.

    Collects, categorizes, prioritizes, and reports validation errors
    with actionable recommendations and tracking capabilities.
    """

    def __init__(self):
        self.errors: List[ErrorReport] = []
        self.error_patterns: Dict[str, Dict[str, Any]] = {}

        # Error categorization rules
        self.categorization_rules = self._build_categorization_rules()

        # Callbacks
        self.on_error_added: Optional[Callable[[ErrorReport], None]] = None
        self.on_error_resolved: Optional[Callable[[ErrorReport], None]] = None

    def _build_categorization_rules(
        self,
    ) -> Dict[str, Callable[[str, str], ErrorCategory]]:
        """Build rules for categorizing errors."""
        return {
            "format": lambda rule, msg: (
                ErrorCategory.FORMAT
                if any(
                    keyword in rule.lower() or keyword in msg.lower()
                    for keyword in ["format", "invalid", "malformed", "syntax"]
                )
                else None
            ),
            "consistency": lambda rule, msg: (
                ErrorCategory.CONSISTENCY
                if any(
                    keyword in rule.lower() or keyword in msg.lower()
                    for keyword in ["consistent", "match", "conflict", "discrepancy"]
                )
                else None
            ),
            "completeness": lambda rule, msg: (
                ErrorCategory.COMPLETENESS
                if any(
                    keyword in rule.lower() or keyword in msg.lower()
                    for keyword in [
                        "missing",
                        "required",
                        "empty",
                        "null",
                        "incomplete",
                    ]
                )
                else None
            ),
            "accuracy": lambda rule, msg: (
                ErrorCategory.ACCURACY
                if any(
                    keyword in rule.lower() or keyword in msg.lower()
                    for keyword in [
                        "incorrect",
                        "invalid",
                        "wrong",
                        "suspicious",
                        "unlikely",
                    ]
                )
                else None
            ),
            "relationship": lambda rule, msg: (
                ErrorCategory.RELATIONSHIP
                if any(
                    keyword in rule.lower() or keyword in msg.lower()
                    for keyword in ["relationship", "link", "connection", "association"]
                )
                else None
            ),
            "business_logic": lambda rule, msg: (
                ErrorCategory.BUSINESS_LOGIC
                if any(
                    keyword in rule.lower() or keyword in msg.lower()
                    for keyword in ["plausible", "biological", "clinical", "domain"]
                )
                else None
            ),
        }

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
        """
        Add a validation error to the report.

        Args:
            entity_type: Type of entity with the error
            entity_id: Optional entity identifier
            field: Field that failed validation
            rule: Validation rule that failed
            message: Error message
            severity: Severity level
            suggestion: Suggested fix
            context: Additional context
            source: Source of the error

        Returns:
            ErrorReport object
        """
        # Categorize the error
        category = self._categorize_error(rule, message)

        # Determine priority
        priority = self._determine_priority(severity, category, rule)

        # Create error report
        error_report = ErrorReport(
            error_id=self._generate_error_id(),
            category=category,
            priority=priority,
            severity=severity,
            entity_type=entity_type,
            entity_id=entity_id,
            field=field,
            rule=rule,
            message=message,
            suggestion=suggestion,
            context=context or {},
            timestamp=datetime.now(),
            source=source,
        )

        self.errors.append(error_report)

        # Update error patterns
        self._update_error_patterns(error_report)

        # Trigger callback
        if self.on_error_added:
            self.on_error_added(error_report)

        return error_report

    def _categorize_error(self, rule: str, message: str) -> ErrorCategory:
        """Categorize an error based on rule and message."""
        for category_name, rule_func in self.categorization_rules.items():
            category = rule_func(rule, message)
            if category:
                return category

        return ErrorCategory.BUSINESS_LOGIC  # Default category

    def _determine_priority(
        self, severity: ValidationSeverity, category: ErrorCategory, rule: str
    ) -> ErrorPriority:
        """Determine error priority based on severity, category, and rule."""

        # Critical errors
        if severity == ValidationSeverity.ERROR:
            if category in [ErrorCategory.FORMAT, ErrorCategory.COMPLETENESS]:
                return ErrorPriority.CRITICAL
            elif category == ErrorCategory.ACCURACY:
                return ErrorPriority.HIGH
            else:
                return ErrorPriority.MEDIUM

        # Warning level
        elif severity == ValidationSeverity.WARNING:
            if category in [ErrorCategory.CONSISTENCY, ErrorCategory.RELATIONSHIP]:
                return ErrorPriority.HIGH
            else:
                return ErrorPriority.MEDIUM

        # Info level
        else:
            return ErrorPriority.LOW

    def _generate_error_id(self) -> str:
        """Generate a unique error ID."""
        import uuid

        return f"ERR_{uuid.uuid4().hex[:8].upper()}"

    def _update_error_patterns(self, error: ErrorReport):
        """Update error pattern tracking."""
        pattern_key = f"{error.entity_type}:{error.rule}"

        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = {
                "count": 0,
                "first_seen": error.timestamp,
                "last_seen": error.timestamp,
                "entity_types": set(),
                "messages": set(),
                "suggestions": set(),
            }

        pattern = self.error_patterns[pattern_key]
        pattern["count"] += 1
        pattern["last_seen"] = error.timestamp
        pattern["entity_types"].add(error.entity_type)
        pattern["messages"].add(error.message)

        if error.suggestion:
            pattern["suggestions"].add(error.suggestion)

    def resolve_error(
        self, error_id: str, resolution_notes: str, resolved_by: Optional[str] = None
    ):
        """
        Mark an error as resolved.

        Args:
            error_id: Error ID to resolve
            resolution_notes: Notes about the resolution
            resolved_by: Person who resolved the error
        """
        for error in self.errors:
            if error.error_id == error_id:
                error.resolved = True
                error.resolution_notes = resolution_notes
                error.assigned_to = resolved_by

                if self.on_error_resolved:
                    self.on_error_resolved(error)
                break

    def assign_error(self, error_id: str, assigned_to: str):
        """Assign an error to a person for resolution."""
        for error in self.errors:
            if error.error_id == error_id:
                error.assigned_to = assigned_to
                break

    def get_error_summary(
        self, include_resolved: bool = False, time_range_hours: Optional[int] = None
    ) -> ErrorSummary:
        """
        Get a summary of errors.

        Args:
            include_resolved: Whether to include resolved errors
            time_range_hours: Optional time range filter

        Returns:
            ErrorSummary with statistics
        """
        errors_to_analyze = self.errors

        if not include_resolved:
            errors_to_analyze = [e for e in errors_to_analyze if not e.resolved]

        if time_range_hours:
            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
            errors_to_analyze = [
                e for e in errors_to_analyze if e.timestamp >= cutoff_time
            ]

        # Count by category
        by_category = {}
        for error in errors_to_analyze:
            cat_name = error.category.value
            by_category[cat_name] = by_category.get(cat_name, 0) + 1

        # Count by priority
        by_priority = {}
        for error in errors_to_analyze:
            pri_name = error.priority.value
            by_priority[pri_name] = by_priority.get(pri_name, 0) + 1

        # Count by severity
        by_severity = {}
        for error in errors_to_analyze:
            sev_name = error.severity.value
            by_severity[sev_name] = by_severity.get(sev_name, 0) + 1

        # Get critical issues
        critical_issues = [
            e for e in errors_to_analyze if e.priority == ErrorPriority.CRITICAL
        ][:10]

        # Get top error patterns
        top_patterns = self._get_top_error_patterns(errors_to_analyze, limit=10)

        return ErrorSummary(
            total_errors=len(errors_to_analyze),
            by_category=by_category,
            by_priority=by_priority,
            by_severity=by_severity,
            critical_issues=critical_issues,
            top_patterns=top_patterns,
        )

    def _get_top_error_patterns(
        self, errors: List[ErrorReport], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get the most common error patterns."""
        pattern_counts = {}

        for error in errors:
            pattern_key = f"{error.entity_type}:{error.rule}"
            if pattern_key not in pattern_counts:
                pattern_counts[pattern_key] = {
                    "pattern": pattern_key,
                    "count": 0,
                    "category": error.category.value,
                    "priority": error.priority.value,
                    "severity": error.severity.value,
                    "sample_message": error.message,
                    "entity_types": set(),
                }

            pattern_counts[pattern_key]["count"] += 1
            pattern_counts[pattern_key]["entity_types"].add(error.entity_type)

        # Sort by count and return top patterns
        sorted_patterns = sorted(
            pattern_counts.values(), key=lambda x: x["count"], reverse=True
        )

        for pattern in sorted_patterns:
            pattern["entity_types"] = list(pattern["entity_types"])

        return sorted_patterns[:limit]

    def get_errors_by_category(
        self, category: ErrorCategory, include_resolved: bool = False
    ) -> List[ErrorReport]:
        """Get all errors in a specific category."""
        errors = [e for e in self.errors if e.category == category]
        if not include_resolved:
            errors = [e for e in errors if not e.resolved]
        return errors

    def get_errors_by_priority(
        self, priority: ErrorPriority, include_resolved: bool = False
    ) -> List[ErrorReport]:
        """Get all errors with a specific priority."""
        errors = [e for e in self.errors if e.priority == priority]
        if not include_resolved:
            errors = [e for e in errors if not e.resolved]
        return errors

    def get_errors_by_entity(
        self,
        entity_type: str,
        entity_id: Optional[str] = None,
        include_resolved: bool = False,
    ) -> List[ErrorReport]:
        """Get errors for a specific entity."""
        errors = [e for e in self.errors if e.entity_type == entity_type]

        if entity_id:
            errors = [e for e in errors if e.entity_id == entity_id]

        if not include_resolved:
            errors = [e for e in errors if not e.resolved]

        return errors

    def generate_error_report(
        self, format: str = "json", include_resolved: bool = False
    ) -> str:
        """
        Generate a comprehensive error report.

        Args:
            format: Report format ("json", "csv", "html")
            include_resolved: Whether to include resolved errors

        Returns:
            Formatted error report
        """
        summary = self.get_error_summary(include_resolved)

        report_data = {
            "summary": {
                "total_errors": summary.total_errors,
                "by_category": summary.by_category,
                "by_priority": summary.by_priority,
                "by_severity": summary.by_severity,
                "generated_at": datetime.now().isoformat(),
            },
            "critical_issues": [
                {
                    "error_id": issue.error_id,
                    "entity_type": issue.entity_type,
                    "entity_id": issue.entity_id,
                    "field": issue.field,
                    "rule": issue.rule,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "source": issue.source,
                    "timestamp": issue.timestamp.isoformat(),
                }
                for issue in summary.critical_issues
            ],
            "top_patterns": summary.top_patterns,
        }

        if format == "json":
            import json

            return json.dumps(report_data, indent=2, default=str)
        elif format == "csv":
            return self._generate_csv_report(report_data)
        elif format == "html":
            return self._generate_html_report(report_data)
        else:
            return str(report_data)

    def _generate_csv_report(self, report_data: Dict[str, Any]) -> str:
        """Generate CSV format error report."""
        lines = [
            "Error ID,Entity Type,Entity ID,Field,Rule,Message,Suggestion,Priority,Severity,Category"
        ]

        for issue in report_data["critical_issues"]:
            line = ",".join(
                [
                    issue["error_id"],
                    issue["entity_type"],
                    issue.get("entity_id", ""),
                    issue["field"],
                    issue["rule"],
                    f'"{issue["message"]}"',
                    f'"{issue.get("suggestion", "")}"',
                    issue.get("priority", ""),
                    issue.get("severity", ""),
                    issue.get("category", ""),
                ]
            )
            lines.append(line)

        return "\n".join(lines)

    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML format error report."""
        html = f"""
        <html>
        <head><title>Validation Error Report</title></head>
        <body>
        <h1>Validation Error Report</h1>
        <p>Generated at: {datetime.now().isoformat()}</p>

        <h2>Summary</h2>
        <ul>
        <li>Total Errors: {report_data['summary']['total_errors']}</li>
        </ul>

        <h2>Critical Issues</h2>
        <table border="1">
        <tr><th>Error ID</th><th>Entity</th><th>Field</th><th>Message</th><th>Suggestion</th></tr>
        """

        for issue in report_data["critical_issues"]:
            html += f"""
            <tr>
            <td>{issue['error_id']}</td>
            <td>{issue['entity_type']}</td>
            <td>{issue['field']}</td>
            <td>{issue['message']}</td>
            <td>{issue.get('suggestion', '')}</td>
            </tr>
            """

        html += """
        </table>
        </body>
        </html>
        """

        return html

    def export_report(
        self, filepath: Path, format: str = "json", include_resolved: bool = False
    ):
        """
        Export error report to file.

        Args:
            filepath: Path to export file
            format: Report format
            include_resolved: Whether to include resolved errors
        """
        report = self.generate_error_report(format, include_resolved)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

    def clear_resolved_errors(self):
        """Remove all resolved errors from the error store."""
        self.errors = [e for e in self.errors if not e.resolved]

    def get_resolution_rate(self, time_range_hours: int = 24) -> float:
        """
        Calculate error resolution rate.

        Args:
            time_range_hours: Time range to analyze

        Returns:
            Resolution rate as a percentage
        """
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
        recent_errors = [e for e in self.errors if e.timestamp >= cutoff_time]

        if not recent_errors:
            return 0.0

        resolved_count = sum(1 for e in recent_errors if e.resolved)
        return resolved_count / len(recent_errors)

    def get_error_trends(self, time_range_hours: int = 168) -> Dict[str, Any]:
        """
        Analyze error trends over time.

        Args:
            time_range_hours: Time range to analyze (default: 1 week)

        Returns:
            Dictionary with trend analysis
        """
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
        recent_errors = [e for e in self.errors if e.timestamp >= cutoff_time]

        # Group by day
        daily_counts = {}
        for error in recent_errors:
            day = error.timestamp.date()
            if day not in daily_counts:
                daily_counts[day] = {"total": 0, "resolved": 0, "by_category": {}}

            daily_counts[day]["total"] += 1
            if error.resolved:
                daily_counts[day]["resolved"] += 1

            cat_name = error.category.value
            if cat_name not in daily_counts[day]["by_category"]:
                daily_counts[day]["by_category"][cat_name] = 0
            daily_counts[day]["by_category"][cat_name] += 1

        return {
            "time_range_hours": time_range_hours,
            "daily_trends": daily_counts,
            "total_errors": len(recent_errors),
            "resolution_rate": self.get_resolution_rate(time_range_hours),
        }

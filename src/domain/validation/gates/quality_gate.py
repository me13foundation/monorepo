"""
Quality gate definitions and result handling.

Defines quality gates that enforce validation standards at different
stages of the ETL pipeline, with configurable thresholds and actions.
"""

from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

from ..rules.base_rules import ValidationResult


class GateStatus(Enum):
    """Status of a quality gate evaluation."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    BLOCKED = "blocked"


class GateAction(Enum):
    """Actions to take when a gate fails."""

    CONTINUE = "continue"  # Allow processing to continue
    WARN = "warn"  # Issue warning but continue
    BLOCK = "block"  # Block further processing
    QUARANTINE = "quarantine"  # Move to quarantine for review
    REJECT = "reject"  # Reject the data entirely


@dataclass
class GateThreshold:
    """Quality thresholds for a gate."""

    min_quality_score: float = 0.8
    max_error_count: int = 0
    max_warning_count: int = 5
    max_info_count: int = 10
    required_rules_passed: Optional[List[str]] = None
    forbidden_rules_failed: Optional[List[str]] = None


@dataclass
class GateResult:
    """Result of evaluating a quality gate."""

    gate_name: str
    status: GateStatus
    action: GateAction
    quality_score: float
    issue_counts: Dict[str, int]  # severity -> count
    critical_issues: List[Dict[str, Any]]
    passed_rules: List[str]
    failed_rules: List[str]
    evaluation_time: float
    metadata: Dict[str, Any]


class QualityGate:
    """
    A quality gate that enforces validation standards.

    Defines validation criteria and actions for a specific checkpoint
    in the ETL pipeline, ensuring data quality standards are met.
    """

    def __init__(
        self,
        name: str,
        description: str,
        entity_types: List[str],
        thresholds: GateThreshold,
        action: GateAction = GateAction.WARN,
        required_rules: Optional[List[str]] = None,
        enabled: bool = True,
    ):
        self.name = name
        self.description = description
        self.entity_types = entity_types  # Which entity types this gate applies to
        self.thresholds = thresholds
        self.action = action
        self.required_rules = required_rules or []
        self.enabled = enabled

        # Callbacks for gate events
        self.on_pass: Optional[Callable[[GateResult], None]] = None
        self.on_fail: Optional[Callable[[GateResult], None]] = None
        self.on_warn: Optional[Callable[[GateResult], None]] = None

    def evaluate(
        self,
        validation_results: Union[ValidationResult, List[ValidationResult]],
        context: Optional[Dict[str, Any]] = None,
    ) -> GateResult:
        """
        Evaluate validation results against this gate's criteria.

        Args:
            validation_results: Single result or list of validation results
            context: Optional context information

        Returns:
            GateResult with evaluation outcome
        """
        import time

        start_time = time.time()

        # Normalize to list
        if isinstance(validation_results, ValidationResult):
            results = [validation_results]
        else:
            results = validation_results

        # Aggregate results
        total_score = 0.0
        issue_counts = {"error": 0, "warning": 0, "info": 0}
        critical_issues = []
        passed_rules = []
        failed_rules = []

        for result in results:
            total_score += result.score

            # Count issues by severity
            for issue in result.issues:
                severity = issue.get("severity", "info")
                issue_counts[severity] += 1

                # Collect critical issues
                if severity == "error":
                    critical_issues.append(issue)

            # Track rule pass/fail status (simplified)
            # In practice, this would track which specific rules passed/failed
            if result.is_valid:
                passed_rules.append("overall_validation")
            else:
                failed_rules.append("overall_validation")

        # Calculate average quality score
        avg_score = total_score / len(results) if results else 0.0

        # Evaluate against thresholds
        status = self._evaluate_thresholds(avg_score, issue_counts)

        # Determine action based on status
        final_action = self._determine_action(status)

        result = GateResult(
            gate_name=self.name,
            status=status,
            action=final_action,
            quality_score=avg_score,
            issue_counts=issue_counts,
            critical_issues=critical_issues[:10],  # Limit critical issues
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            evaluation_time=time.time() - start_time,
            metadata={
                "entity_count": len(results),
                "context": context or {},
                "thresholds": {
                    "min_quality_score": self.thresholds.min_quality_score,
                    "max_error_count": self.thresholds.max_error_count,
                    "max_warning_count": self.thresholds.max_warning_count,
                },
            },
        )

        # Trigger callbacks
        self._trigger_callbacks(result)

        return result

    def _evaluate_thresholds(
        self, quality_score: float, issue_counts: Dict[str, int]
    ) -> GateStatus:
        """Evaluate results against quality thresholds."""
        # Check quality score
        if quality_score < self.thresholds.min_quality_score:
            return GateStatus.FAILED

        # Check error count
        if issue_counts["error"] > self.thresholds.max_error_count:
            return GateStatus.FAILED

        # Check warning count
        if issue_counts["warning"] > self.thresholds.max_warning_count:
            return GateStatus.WARNING

        # Check required rules
        if self.thresholds.required_rules_passed:
            # This would check if specific required rules passed
            # Simplified implementation
            pass

        # Check forbidden rules
        if self.thresholds.forbidden_rules_failed:
            # This would check if forbidden rules failed
            # Simplified implementation
            pass

        return GateStatus.PASSED

    def _determine_action(self, status: GateStatus) -> GateAction:
        """Determine the action to take based on gate status."""
        if status == GateStatus.FAILED:
            if self.action in [
                GateAction.BLOCK,
                GateAction.QUARANTINE,
                GateAction.REJECT,
            ]:
                return self.action
            else:
                return GateAction.BLOCK  # Default for failed gates
        elif status == GateStatus.WARNING:
            return GateAction.WARN
        else:
            return GateAction.CONTINUE

    def _trigger_callbacks(self, result: GateResult):
        """Trigger appropriate callbacks based on result."""
        if result.status == GateStatus.PASSED and self.on_pass:
            self.on_pass(result)
        elif result.status == GateStatus.FAILED and self.on_fail:
            self.on_fail(result)
        elif result.status == GateStatus.WARNING and self.on_warn:
            self.on_warn(result)

    def update_thresholds(self, **kwargs):
        """Update gate thresholds."""
        for key, value in kwargs.items():
            if hasattr(self.thresholds, key):
                setattr(self.thresholds, key, value)

    def enable(self):
        """Enable this gate."""
        self.enabled = True

    def disable(self):
        """Disable this gate."""
        self.enabled = False

    def get_config(self) -> Dict[str, Any]:
        """Get gate configuration."""
        return {
            "name": self.name,
            "description": self.description,
            "entity_types": self.entity_types,
            "thresholds": {
                "min_quality_score": self.thresholds.min_quality_score,
                "max_error_count": self.thresholds.max_error_count,
                "max_warning_count": self.thresholds.max_warning_count,
                "max_info_count": self.thresholds.max_info_count,
            },
            "action": self.action.value,
            "required_rules": self.required_rules,
            "enabled": self.enabled,
        }


# Predefined quality gates for common use cases


def create_parsing_gate() -> QualityGate:
    """Create a quality gate for data parsing validation."""
    return QualityGate(
        name="parsing_gate",
        description="Validates data parsing quality and completeness",
        entity_types=["gene", "variant", "phenotype", "publication"],
        thresholds=GateThreshold(
            min_quality_score=0.9, max_error_count=1, max_warning_count=10
        ),
        action=GateAction.BLOCK,
    )


def create_normalization_gate() -> QualityGate:
    """Create a quality gate for data normalization validation."""
    return QualityGate(
        name="normalization_gate",
        description="Validates identifier normalization and standardization",
        entity_types=["gene", "variant", "phenotype", "publication"],
        thresholds=GateThreshold(
            min_quality_score=0.85, max_error_count=2, max_warning_count=15
        ),
        action=GateAction.WARN,
    )


def create_relationship_gate() -> QualityGate:
    """Create a quality gate for relationship validation."""
    return QualityGate(
        name="relationship_gate",
        description="Validates genotype-phenotype relationship quality",
        entity_types=["relationship"],
        thresholds=GateThreshold(
            min_quality_score=0.8, max_error_count=0, max_warning_count=5
        ),
        action=GateAction.QUARANTINE,
    )


def create_final_release_gate() -> QualityGate:
    """Create a strict quality gate for final data release."""
    return QualityGate(
        name="release_gate",
        description="Final quality check before data release",
        entity_types=["gene", "variant", "phenotype", "publication", "relationship"],
        thresholds=GateThreshold(
            min_quality_score=0.95, max_error_count=0, max_warning_count=2
        ),
        action=GateAction.BLOCK,
    )

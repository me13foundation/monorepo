"""Small validation report generator used by the integration tests."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

from .dashboard import ValidationDashboard
from .error_reporting import ErrorReporter, ErrorSummary
from .metrics import MetricsCollector


@dataclass
class ValidationReport:
    report_id: str
    title: str
    generated_at: datetime
    time_range_hours: int
    executive_summary: Dict[str, Any]
    detailed_findings: Dict[str, Any]
    recommendations: List[str]
    data_quality_score: float
    system_health_score: float
    appendices: Dict[str, Any]


class ValidationReportGenerator:
    def __init__(
        self,
        error_reporter: ErrorReporter,
        metrics_collector: MetricsCollector,
        dashboard: ValidationDashboard,
    ) -> None:
        self._errors = error_reporter
        self._metrics = metrics_collector
        self._dashboard = dashboard
        self._counter = 0

    def generate_executive_report(
        self, time_range_hours: int = 168
    ) -> ValidationReport:
        dashboard_data = self._dashboard.get_dashboard_data(force_refresh=True)
        quality_report = self._metrics.get_performance_report(time_range_hours)
        error_summary = self._errors.get_error_summary(
            time_range_hours=time_range_hours
        )

        executive_summary = {
            "system_health": dashboard_data.system_health,
            "quality_score": quality_report["metrics"].get("quality_score"),
            "total_errors": error_summary.total_errors,
        }

        detailed_findings = {
            "performance_metrics": dashboard_data.performance_metrics,
            "quality_metrics": dashboard_data.quality_metrics,
            "alerts": dashboard_data.alerts,
        }

        recommendations = self._build_recommendations(error_summary)

        appendices = {
            "error_summary": asdict(error_summary),
            "performance_report": quality_report,
        }

        return ValidationReport(
            report_id=self._next_id("exec"),
            title="Executive Validation Report",
            generated_at=datetime.now(UTC),
            time_range_hours=time_range_hours,
            executive_summary=executive_summary,
            detailed_findings=detailed_findings,
            recommendations=recommendations,
            data_quality_score=dashboard_data.quality_metrics.get(
                "quality_score", {}
            ).get("average", 0.0),
            system_health_score=dashboard_data.system_health,
            appendices=appendices,
        )

    def generate_technical_report(self, time_range_hours: int = 24) -> ValidationReport:
        dashboard_data = self._dashboard.get_dashboard_data(force_refresh=True)
        error_trends = self._errors.get_error_trends(time_range_hours)
        performance_report = self._metrics.get_performance_report(time_range_hours)

        executive_summary = {
            "system_health": dashboard_data.system_health,
            "recent_alerts": dashboard_data.alerts,
        }

        detailed_findings = {
            "error_trends": error_trends,
            "performance_metrics": dashboard_data.performance_metrics,
            "quality_metrics": dashboard_data.quality_metrics,
        }

        recommendations = self._build_recommendations(self._errors.get_error_summary())

        appendices = {
            "performance_report": performance_report,
            "alerts": dashboard_data.alerts,
        }

        return ValidationReport(
            report_id=self._next_id("tech"),
            title="Technical Validation Report",
            generated_at=datetime.now(UTC),
            time_range_hours=time_range_hours,
            executive_summary=executive_summary,
            detailed_findings=detailed_findings,
            recommendations=recommendations,
            data_quality_score=dashboard_data.quality_metrics.get(
                "quality_score", {}
            ).get("average", 0.0),
            system_health_score=dashboard_data.system_health,
            appendices=appendices,
        )

    def export_report(
        self, report: ValidationReport, path: str, format: str = "json"
    ) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        payload = asdict(report)
        payload["generated_at"] = report.generated_at.isoformat()

        if format.lower() == "json":
            target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return

        if format.lower() == "html":
            html = """<html><body><h1>{title}</h1><pre>{content}</pre></body></html>""".format(
                title=report.title,
                content=json.dumps(payload, indent=2),
            )
            target.write_text(html, encoding="utf-8")
            return

        raise ValueError(f"Unsupported export format: {format}")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix.upper()}-{self._counter:05d}"

    @staticmethod
    def _build_recommendations(summary: ErrorSummary) -> List[str]:
        recommendations: List[str] = []
        if summary.total_errors == 0:
            recommendations.append(
                "Maintain current validation configuration; no blocking issues detected."
            )
        else:
            recommendations.append(
                "Review critical validation errors and schedule remediation work."
            )
        return recommendations


__all__ = ["ValidationReport", "ValidationReportGenerator"]

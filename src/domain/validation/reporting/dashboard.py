"""Simplified validation dashboard used by the integration tests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from .error_reporting import ErrorReporter, ErrorSummary
from .metrics import MetricsCollector


@dataclass
class DashboardConfig:
    refresh_interval_seconds: int = 120
    display_metrics: Optional[List[str]] = None


@dataclass
class DashboardData:
    timestamp: datetime
    system_health: float
    quality_metrics: Dict[str, Any]
    error_summary: ErrorSummary
    performance_metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]


class ValidationDashboard:
    """Provide a small typed API for the tests to interact with."""

    def __init__(
        self,
        error_reporter: ErrorReporter,
        metrics_collector: MetricsCollector,
        config: Optional[DashboardConfig] = None,
    ) -> None:
        self._error_reporter = error_reporter
        self._metrics = metrics_collector
        self._config = config or DashboardConfig()
        self._cached: Optional[DashboardData] = None
        self._last_refresh: Optional[datetime] = None

    def get_dashboard_data(self, force_refresh: bool = False) -> DashboardData:
        now = datetime.now(UTC)
        needs_refresh = (
            force_refresh
            or self._cached is None
            or self._last_refresh is None
            or (now - self._last_refresh).total_seconds()
            > self._config.refresh_interval_seconds
        )

        if needs_refresh:
            self._cached = self._collect_data(timestamp=now)
            self._last_refresh = now

        return self._cached  # type: ignore[return-value]

    def generate_report(self, format: str = "json") -> str:
        data = self.get_dashboard_data(force_refresh=True)
        payload = {
            "generated_at": data.timestamp.isoformat(),
            "system_health": data.system_health,
            "quality_metrics": data.quality_metrics,
            "performance_metrics": data.performance_metrics,
            "total_errors": data.error_summary.total_errors,
            "alerts": [
                {
                    **alert,
                    "timestamp": (
                        timestamp.isoformat()
                        if isinstance(timestamp, datetime)
                        else timestamp
                    ),
                }
                for alert in data.alerts
                for timestamp in [alert.get("timestamp")]
            ],
        }

        if format.lower() == "json":
            return json.dumps(payload, indent=2)
        if format.lower() == "html":
            return """<html><body><h1>Validation Dashboard</h1><pre>{}</pre></body></html>""".format(
                json.dumps(payload, indent=2)
            )
        raise ValueError(f"Unsupported report format: {format}")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _collect_data(self, timestamp: datetime) -> DashboardData:
        quality_summary = self._metrics.get_metric_summary("validation.quality_score")
        error_summary = self._error_reporter.get_error_summary()
        throughput_summary = self._metrics.get_metric_summary("pipeline.throughput")
        execution_summary = self._metrics.get_metric_summary("pipeline.execution_time")

        quality_metrics: Dict[str, Any] = {}
        if quality_summary:
            quality_metrics["quality_score"] = {
                "average": quality_summary.average,
                "min": quality_summary.minimum,
                "max": quality_summary.maximum,
            }

        performance_metrics: Dict[str, Any] = {}
        if throughput_summary:
            performance_metrics[
                "throughput_items_per_second"
            ] = throughput_summary.average
        if execution_summary:
            performance_metrics["execution_time_seconds"] = execution_summary.average

        alerts = self._metrics.get_alerts()

        return DashboardData(
            timestamp=timestamp,
            system_health=self._metrics.get_system_health_score(),
            quality_metrics=quality_metrics,
            error_summary=error_summary,
            performance_metrics=performance_metrics,
            alerts=alerts,
        )


__all__ = ["DashboardConfig", "DashboardData", "ValidationDashboard"]

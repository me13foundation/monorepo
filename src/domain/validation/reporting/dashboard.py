"""
Validation dashboard for comprehensive monitoring and reporting.

Provides a unified dashboard interface for monitoring validation
performance, error trends, quality metrics, and system health.
"""

import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .error_reporting import ErrorReporter, ErrorSummary
from .metrics import MetricsCollector


@dataclass
class DashboardConfig:
    """Configuration for the validation dashboard."""

    refresh_interval_seconds: int = 300  # 5 minutes
    alert_thresholds: Dict[str, float] = None
    display_metrics: List[str] = None
    max_chart_points: int = 100

    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "error_rate": 0.05,
                "quality_score": 0.85,
                "health_score": 0.8,
            }

        if self.display_metrics is None:
            self.display_metrics = [
                "validation.quality_score",
                "validation.error_rate",
                "pipeline.execution_time",
                "pipeline.throughput",
                "gate.status",
            ]


@dataclass
class DashboardData:
    """Data structure for dashboard display."""

    timestamp: datetime
    system_health: float
    quality_metrics: Dict[str, Any]
    error_summary: ErrorSummary
    performance_metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    trends: Dict[str, Any]


class ValidationDashboard:
    """
    Comprehensive validation dashboard.

    Provides real-time monitoring, trend analysis, and actionable insights
    for validation system performance and data quality.
    """

    def __init__(
        self,
        error_reporter: ErrorReporter,
        metrics_collector: MetricsCollector,
        config: Optional[DashboardConfig] = None,
    ):
        self.error_reporter = error_reporter
        self.metrics_collector = metrics_collector
        self.config = config or DashboardConfig()

        # Dashboard state
        self.last_update = None
        self.cached_data: Optional[DashboardData] = None

        # Callbacks
        self.on_dashboard_update: Optional[Callable[[DashboardData], None]] = None
        self.on_alert_triggered: Optional[Callable[[Dict[str, Any]], None]] = None

    def get_dashboard_data(self, force_refresh: bool = False) -> DashboardData:
        """
        Get current dashboard data.

        Args:
            force_refresh: Whether to force a data refresh

        Returns:
            DashboardData with current system status
        """
        # Check if refresh is needed
        if (
            not force_refresh
            and self.cached_data
            and self.last_update
            and (datetime.now() - self.last_update).seconds
            < self.config.refresh_interval_seconds
        ):
            return self.cached_data

        # Collect fresh data
        dashboard_data = self._collect_dashboard_data()

        # Cache the data
        self.cached_data = dashboard_data
        self.last_update = datetime.now()

        # Trigger callback
        if self.on_dashboard_update:
            self.on_dashboard_update(dashboard_data)

        return dashboard_data

    def _collect_dashboard_data(self) -> DashboardData:
        """Collect all data needed for the dashboard."""
        now = datetime.now()

        # System health
        system_health = self.metrics_collector.get_system_health_score()

        # Quality metrics
        quality_metrics = self._collect_quality_metrics()

        # Error summary
        error_summary = self.error_reporter.get_error_summary(
            include_resolved=False, time_range_hours=24
        )

        # Performance metrics
        performance_metrics = self._collect_performance_metrics()

        # Active alerts
        alerts = self.metrics_collector.get_alerts(time_range_hours=1)

        # Trend data
        trends = self._collect_trend_data()

        return DashboardData(
            timestamp=now,
            system_health=system_health,
            quality_metrics=quality_metrics,
            error_summary=error_summary,
            performance_metrics=performance_metrics,
            alerts=alerts,
            trends=trends,
        )

    def _collect_quality_metrics(self) -> Dict[str, Any]:
        """Collect quality-related metrics."""
        metrics = {}

        # Overall quality score
        quality_summary = self.metrics_collector.get_metric_summary(
            "validation.quality_score", time_range_hours=24
        )
        if quality_summary:
            metrics["overall_quality"] = {
                "current": quality_summary.avg,
                "min": quality_summary.min,
                "max": quality_summary.max,
                "trend": (
                    "improving"
                    if quality_summary.avg > quality_summary.percentiles["50"]
                    else "declining"
                ),
            }

        # Error rate
        error_rate_summary = self.metrics_collector.get_metric_summary(
            "validation.error_rate", time_range_hours=24
        )
        if error_rate_summary:
            metrics["error_rate"] = {
                "current": error_rate_summary.avg,
                "threshold": self.config.alert_thresholds["error_rate"],
                "status": (
                    "alert"
                    if error_rate_summary.avg
                    > self.config.alert_thresholds["error_rate"]
                    else "normal"
                ),
            }

        # Pipeline success rate
        gate_status_summary = self.metrics_collector.get_metric_summary(
            "gate.status", time_range_hours=24
        )
        if gate_status_summary:
            success_rate = gate_status_summary.avg
            metrics["pipeline_success"] = {
                "rate": success_rate,
                "status": (
                    "healthy"
                    if success_rate > 0.95
                    else "warning"
                    if success_rate > 0.9
                    else "critical"
                ),
            }

        return metrics

    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance-related metrics."""
        metrics = {}

        # Processing throughput
        throughput_summary = self.metrics_collector.get_metric_summary(
            "pipeline.throughput", time_range_hours=24
        )
        if throughput_summary:
            metrics["throughput"] = {
                "current": throughput_summary.avg,
                "unit": "entities/second",
                "peak": throughput_summary.max,
            }

        # Execution time
        exec_time_summary = self.metrics_collector.get_metric_summary(
            "pipeline.execution_time", time_range_hours=24
        )
        if exec_time_summary:
            metrics["execution_time"] = {
                "avg": exec_time_summary.avg,
                "p95": exec_time_summary.percentiles["95"],
                "status": (
                    "slow" if exec_time_summary.avg > 300 else "normal"
                ),  # 5 min threshold
            }

        # Error resolution rate
        resolution_rate = self.error_reporter.get_resolution_rate(
            time_range_hours=168
        )  # 1 week
        metrics["error_resolution"] = {
            "rate": resolution_rate,
            "status": "good" if resolution_rate > 0.8 else "needs_improvement",
        }

        return metrics

    def _collect_trend_data(self) -> Dict[str, Any]:
        """Collect trend data for charts."""
        trends = {}

        # Quality score trend (last 7 days)
        quality_trends = self.metrics_collector.get_performance_report(
            time_range_hours=168
        )
        if (
            "trends" in quality_trends
            and "validation.quality_score" in quality_trends["trends"]
        ):
            trends["quality_score"] = quality_trends["trends"][
                "validation.quality_score"
            ][-self.config.max_chart_points :]

        # Error rate trend
        if (
            "trends" in quality_trends
            and "validation.error_rate" in quality_trends["trends"]
        ):
            trends["error_rate"] = quality_trends["trends"]["validation.error_rate"][
                -self.config.max_chart_points :
            ]

        # Error trends by category
        error_trends = self.error_reporter.get_error_trends(time_range_hours=168)
        if "daily_trends" in error_trends:
            trends["errors_by_category"] = self._process_error_trends(
                error_trends["daily_trends"]
            )

        return trends

    def _process_error_trends(self, daily_trends: Dict) -> List[Dict[str, Any]]:
        """Process error trend data for charting."""
        category_totals = {}

        for day_data in daily_trends.values():
            for cat, count in day_data.get("by_category", {}).items():
                if cat not in category_totals:
                    category_totals[cat] = []
                category_totals[cat].append(count)

        # Calculate rolling averages
        trend_data = []
        categories = list(category_totals.keys())

        for i in range(max(len(counts) for counts in category_totals.values())):
            data_point = {"period": i}
            for cat in categories:
                counts = category_totals.get(cat, [])
                if i < len(counts):
                    # Simple moving average of last 7 points
                    start_idx = max(0, i - 6)
                    avg = sum(counts[start_idx : i + 1]) / (i - start_idx + 1)
                    data_point[cat] = round(avg, 2)
                else:
                    data_point[cat] = 0
            trend_data.append(data_point)

        return trend_data[-self.config.max_chart_points :]

    def generate_report(self, format: str = "html", time_range_hours: int = 24) -> str:
        """
        Generate a comprehensive dashboard report.

        Args:
            format: Report format ("html", "json", "markdown")
            time_range_hours: Time range for the report

        Returns:
            Formatted report string
        """
        data = self.get_dashboard_data()

        if format == "json":
            return self._generate_json_report(data)
        elif format == "html":
            return self._generate_html_report(data)
        elif format == "markdown":
            return self._generate_markdown_report(data)
        else:
            return str(data)

    def _generate_json_report(self, data: DashboardData) -> str:
        """Generate JSON format dashboard report."""
        report = {
            "timestamp": data.timestamp.isoformat(),
            "system_health": {
                "score": round(data.system_health, 3),
                "status": self._get_health_status(data.system_health),
            },
            "quality_metrics": data.quality_metrics,
            "performance_metrics": data.performance_metrics,
            "error_summary": {
                "total_errors": data.error_summary.total_errors,
                "by_category": data.error_summary.by_category,
                "by_priority": data.error_summary.by_priority,
                "by_severity": data.error_summary.by_severity,
            },
            "alerts": data.alerts,
            "trends": data.trends,
        }

        return json.dumps(report, indent=2, default=str)

    def _generate_html_report(self, data: DashboardData) -> str:
        """Generate HTML format dashboard report."""
        health_status = self._get_health_status(data.system_health)
        health_color = {
            "healthy": "#28a745",
            "warning": "#ffc107",
            "critical": "#dc3545",
        }[health_status]

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Validation Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px;
                           margin-bottom: 20px; }}
                .metric {{ background: white; border: 1px solid #ddd; padding: 15px;
                           margin: 10px 0; border-radius: 5px; }}
                .health-indicator {{ display: inline-block; width: 20px; height: 20px;
                                     border-radius: 50%; background: {health_color};
                                     margin-left: 10px; }}
                .status-healthy {{ color: #28a745; }}
                .status-warning {{ color: #ffc107; }}
                .status-critical {{ color: #dc3545; }}
                .chart {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Validation Dashboard</h1>
                <p>Generated: {data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>System Health: {data.system_health:.1%}
                    <span class="health-indicator"></span>
                    <span class="status-{health_status}">{health_status.upper()}</span>
                </p>
            </div>

            <div class="metric">
                <h2>Quality Metrics</h2>
                <p>Overall Quality Score: {data.quality_metrics.get('overall_quality',
                                                {}).get('current', 0):.1%}</p>
                <p>Error Rate: {data.quality_metrics.get('error_rate', {}).get('current', 0):.1%}
                   ({data.quality_metrics.get('error_rate', {}).get('status', 'unknown')})</p>
                <p>Pipeline Success Rate: {data.quality_metrics.get('pipeline_success', {}).get('rate', 0):.1%}</p>
            </div>

            <div class="metric">
                <h2>Performance Metrics</h2>
                <p>Throughput: {data.performance_metrics.get('throughput', {}).get('current', 0):.1f} entities/sec</p>
                <p>Average Execution Time: {data.performance_metrics.get('execution_time', {}).get('avg', 0):.1f}s</p>
                <p>Error Resolution Rate: {data.performance_metrics.get('error_resolution', {}).get('rate', 0):.1%}</p>
            </div>

            <div class="metric">
                <h2>Error Summary</h2>
                <p>Total Errors: {data.error_summary.total_errors}</p>
                <table>
                    <tr><th>Category</th><th>Count</th></tr>
        """

        for category, count in data.error_summary.by_category.items():
            html += f"<tr><td>{category}</td><td>{count}</td></tr>"

        html += """
                </table>
            </div>

            <div class="metric">
                <h2>Active Alerts</h2>
        """

        if data.alerts:
            html += "<ul>"
            for alert in data.alerts[:5]:  # Show first 5 alerts
                html += f"<li>{alert['metric']}: {alert['value']:.3f} (threshold: {alert['threshold']:.3f})</li>"
            html += "</ul>"
        else:
            html += "<p>No active alerts</p>"

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def _generate_markdown_report(self, data: DashboardData) -> str:
        """Generate Markdown format dashboard report."""
        health_status = self._get_health_status(data.system_health)

        markdown = f"""# Validation Dashboard

**Generated:** {data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

## System Health: {health_status.upper()}
**Score:** {data.system_health:.1%}

## Quality Metrics
- **Overall Quality Score:** {data.quality_metrics.get('overall_quality', {}).get('current', 0):.1%}
- **Error Rate:** {data.quality_metrics.get('error_rate', {}).get('current', 0):.1%} ({data.quality_metrics.get('error_rate', {}).get('status', 'unknown')})
- **Pipeline Success Rate:** {data.quality_metrics.get('pipeline_success', {}).get('rate', 0):.1%}

## Performance Metrics
- **Throughput:** {data.performance_metrics.get('throughput', {}).get('current', 0):.1f} entities/sec
- **Avg Execution Time:** {data.performance_metrics.get('execution_time', {}).get('avg', 0):.1f}s
- **Error Resolution Rate:** {data.performance_metrics.get('error_resolution', {}).get('rate', 0):.1%}

## Error Summary
**Total Errors:** {data.error_summary.total_errors}

| Category | Count |
|----------|--------|
"""

        for category, count in data.error_summary.by_category.items():
            markdown += f"| {category} | {count} |\n"

        if data.alerts:
            markdown += "\n## Active Alerts\n"
            for alert in data.alerts[:5]:
                markdown += f"- {alert['metric']}: {alert['value']:.3f} (threshold: {alert['threshold']:.3f})\n"

        return markdown

    def _get_health_status(self, health_score: float) -> str:
        """Get health status string based on score."""
        if health_score >= self.config.alert_thresholds["health_score"]:
            return "healthy"
        elif health_score >= 0.6:
            return "warning"
        else:
            return "critical"

    def export_dashboard(
        self, filepath: Path, format: str = "html", time_range_hours: int = 24
    ):
        """
        Export dashboard to file.

        Args:
            filepath: Path to export file
            format: Export format
            time_range_hours: Time range for data
        """
        report = self.generate_report(format, time_range_hours)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

    def get_health_score_explanation(self) -> Dict[str, Any]:
        """
        Get detailed explanation of current health score.

        Returns:
            Dictionary with health score breakdown
        """
        data = self.get_dashboard_data()

        explanation = {
            "overall_score": data.system_health,
            "status": self._get_health_status(data.system_health),
            "factors": [],
        }

        # Quality factor
        quality = data.quality_metrics.get("overall_quality", {})
        if quality:
            explanation["factors"].append(
                {
                    "factor": "Data Quality",
                    "score": quality.get("current", 0),
                    "weight": 0.4,
                    "status": (
                        "good"
                        if quality.get("current", 0) > 0.8
                        else "needs_improvement"
                    ),
                }
            )

        # Error factor
        error_rate = data.quality_metrics.get("error_rate", {})
        if error_rate:
            error_penalty = min(
                1.0, error_rate.get("current", 0) * 20
            )  # Scale error rate
            explanation["factors"].append(
                {
                    "factor": "Error Rate",
                    "score": 1.0 - error_penalty,
                    "weight": 0.3,
                    "status": "good" if error_penalty < 0.2 else "needs_improvement",
                }
            )

        # Performance factor
        perf = data.performance_metrics.get("execution_time", {})
        if perf:
            time_penalty = min(1.0, perf.get("avg", 0) / 600)  # 10 min max
            explanation["factors"].append(
                {
                    "factor": "Performance",
                    "score": 1.0 - time_penalty,
                    "weight": 0.3,
                    "status": "good" if time_penalty < 0.3 else "needs_improvement",
                }
            )

        return explanation

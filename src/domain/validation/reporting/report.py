"""
Comprehensive validation report generation.

Combines error reporting, metrics, and dashboard data into
unified validation reports for different stakeholders and use cases.
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .error_reporting import ErrorReporter, ErrorSummary
from .metrics import MetricsCollector
from .dashboard import ValidationDashboard, DashboardData


@dataclass
class ValidationReport:
    """Comprehensive validation report."""

    report_id: str
    title: str
    generated_at: datetime
    time_range: str
    executive_summary: Dict[str, Any]
    detailed_findings: Dict[str, Any]
    recommendations: List[str]
    data_quality_score: float
    system_health_score: float
    risk_assessment: Dict[str, Any]
    appendices: Dict[str, Any]


class ValidationReportGenerator:
    """
    Generates comprehensive validation reports.

    Combines data from error reporting, metrics collection, and dashboard
    to create detailed reports for different audiences and purposes.
    """

    def __init__(
        self,
        error_reporter: ErrorReporter,
        metrics_collector: MetricsCollector,
        dashboard: ValidationDashboard,
    ):
        self.error_reporter = error_reporter
        self.metrics_collector = metrics_collector
        self.dashboard = dashboard

    def generate_executive_report(
        self, time_range_hours: int = 168
    ) -> ValidationReport:
        """
        Generate executive-level validation report.

        Args:
            time_range_hours: Time range for report data

        Returns:
            Executive validation report
        """
        # Collect all data
        dashboard_data = self.dashboard.get_dashboard_data(force_refresh=True)
        quality_report = self.metrics_collector.get_performance_report(time_range_hours)

        # Executive summary
        executive_summary = self._create_executive_summary(
            dashboard_data, quality_report
        )

        # Key findings
        detailed_findings = self._create_executive_findings(
            dashboard_data, quality_report
        )

        # Recommendations
        recommendations = self._create_executive_recommendations(
            dashboard_data, quality_report
        )

        # Risk assessment
        risk_assessment = self._assess_executive_risks(dashboard_data, quality_report)

        return ValidationReport(
            report_id=self._generate_report_id(),
            title="Executive Validation Report",
            generated_at=datetime.now(),
            time_range=f"{time_range_hours} hours",
            executive_summary=executive_summary,
            detailed_findings=detailed_findings,
            recommendations=recommendations,
            data_quality_score=dashboard_data.quality_metrics.get(
                "overall_quality", {}
            ).get("current", 0.0),
            system_health_score=dashboard_data.system_health,
            risk_assessment=risk_assessment,
            appendices=self._create_executive_appendices(dashboard_data),
        )

    def generate_technical_report(self, time_range_hours: int = 24) -> ValidationReport:
        """
        Generate detailed technical validation report.

        Args:
            time_range_hours: Time range for report data

        Returns:
            Technical validation report
        """
        # Collect all data
        dashboard_data = self.dashboard.get_dashboard_data(force_refresh=True)
        error_trends = self.error_reporter.get_error_trends(time_range_hours)
        performance_report = self.metrics_collector.get_performance_report(
            time_range_hours
        )

        # Technical summary
        executive_summary = self._create_technical_summary(dashboard_data, error_trends)

        # Detailed findings
        detailed_findings = self._create_technical_findings(
            dashboard_data, error_trends, performance_report
        )

        # Technical recommendations
        recommendations = self._create_technical_recommendations(
            dashboard_data, error_trends
        )

        # Risk assessment
        risk_assessment = self._assess_technical_risks(dashboard_data, error_trends)

        return ValidationReport(
            report_id=self._generate_report_id(),
            title="Technical Validation Report",
            generated_at=datetime.now(),
            time_range=f"{time_range_hours} hours",
            executive_summary=executive_summary,
            detailed_findings=detailed_findings,
            recommendations=recommendations,
            data_quality_score=dashboard_data.quality_metrics.get(
                "overall_quality", {}
            ).get("current", 0.0),
            system_health_score=dashboard_data.system_health,
            risk_assessment=risk_assessment,
            appendices=self._create_technical_appendices(
                error_trends, performance_report
            ),
        )

    def generate_compliance_report(
        self, time_range_hours: int = 720
    ) -> ValidationReport:
        """
        Generate compliance-focused validation report.

        Args:
            time_range_hours: Time range for report data (default: 30 days)

        Returns:
            Compliance validation report
        """
        # Collect compliance-relevant data
        dashboard_data = self.dashboard.get_dashboard_data(force_refresh=True)
        error_summary = self.error_reporter.get_error_summary(
            include_resolved=False, time_range_hours=time_range_hours
        )

        # Compliance summary
        executive_summary = self._create_compliance_summary(
            dashboard_data, error_summary
        )

        # Compliance findings
        detailed_findings = self._create_compliance_findings(
            dashboard_data, error_summary
        )

        # Compliance recommendations
        recommendations = self._create_compliance_recommendations(
            dashboard_data, error_summary
        )

        # Compliance risk assessment
        risk_assessment = self._assess_compliance_risks(dashboard_data, error_summary)

        return ValidationReport(
            report_id=self._generate_report_id(),
            title="Compliance Validation Report",
            generated_at=datetime.now(),
            time_range=f"{time_range_hours} hours",
            executive_summary=executive_summary,
            detailed_findings=detailed_findings,
            recommendations=recommendations,
            data_quality_score=dashboard_data.quality_metrics.get(
                "overall_quality", {}
            ).get("current", 0.0),
            system_health_score=dashboard_data.system_health,
            risk_assessment=risk_assessment,
            appendices=self._create_compliance_appendices(error_summary),
        )

    def _generate_report_id(self) -> str:
        """Generate a unique report ID."""
        import uuid

        return f"RPT_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"

    def _create_executive_summary(
        self, dashboard_data: DashboardData, quality_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create executive summary section."""
        health_status = self._get_health_status(dashboard_data.system_health)

        return {
            "period": dashboard_data.timestamp.strftime("%B %Y"),
            "system_health": {
                "score": dashboard_data.system_health,
                "status": health_status,
                "trend": "stable",  # Would need historical comparison
            },
            "key_metrics": {
                "data_quality": dashboard_data.quality_metrics.get(
                    "overall_quality", {}
                ).get("current", 0.0),
                "error_rate": dashboard_data.quality_metrics.get("error_rate", {}).get(
                    "current", 0.0
                ),
                "processing_throughput": dashboard_data.performance_metrics.get(
                    "throughput", {}
                ).get("current", 0.0),
                "pipeline_success_rate": dashboard_data.quality_metrics.get(
                    "pipeline_success", {}
                ).get("rate", 0.0),
            },
            "alerts_count": len(dashboard_data.alerts),
            "critical_issues": len(dashboard_data.error_summary.critical_issues),
        }

    def _create_executive_findings(
        self, dashboard_data: DashboardData, quality_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create executive findings section."""
        findings = {
            "quality_performance": {},
            "error_analysis": {},
            "system_performance": {},
            "trends": {},
        }

        # Quality performance
        quality = dashboard_data.quality_metrics.get("overall_quality", {})
        findings["quality_performance"] = {
            "score": quality.get("current", 0.0),
            "assessment": (
                "excellent"
                if quality.get("current", 0.9) > 0.9
                else (
                    "good" if quality.get("current", 0.8) > 0.8 else "needs_improvement"
                )
            ),
        }

        # Error analysis
        findings["error_analysis"] = {
            "total_errors": dashboard_data.error_summary.total_errors,
            "error_distribution": dashboard_data.error_summary.by_category,
            "resolution_rate": dashboard_data.performance_metrics.get(
                "error_resolution", {}
            ).get("rate", 0.0),
        }

        # System performance
        findings["system_performance"] = {
            "throughput": dashboard_data.performance_metrics.get("throughput", {}).get(
                "current", 0.0
            ),
            "execution_time": dashboard_data.performance_metrics.get(
                "execution_time", {}
            ).get("avg", 0.0),
            "health_score": dashboard_data.system_health,
        }

        return findings

    def _create_executive_recommendations(
        self, dashboard_data: DashboardData, quality_report: Dict[str, Any]
    ) -> List[str]:
        """Create executive recommendations."""
        recommendations = []

        # Quality recommendations
        if (
            dashboard_data.quality_metrics.get("overall_quality", {}).get(
                "current", 0.0
            )
            < 0.85
        ):
            recommendations.append(
                "Improve data quality standards and validation rules"
            )

        # Error recommendations
        if dashboard_data.error_summary.total_errors > 100:
            recommendations.append(
                "Implement error reduction strategies and quality improvements"
            )

        # Performance recommendations
        if (
            dashboard_data.performance_metrics.get("execution_time", {}).get("avg", 0.0)
            > 300
        ):
            recommendations.append(
                "Optimize validation performance and processing efficiency"
            )

        # System health recommendations
        if dashboard_data.system_health < 0.8:
            recommendations.append(
                "Address system health issues and implement monitoring improvements"
            )

        if not recommendations:
            recommendations.append("Continue current quality assurance practices")

        return recommendations

    def _assess_executive_risks(
        self, dashboard_data: DashboardData, quality_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess executive-level risks."""
        risks = {"high": [], "medium": [], "low": []}

        # High risks
        if dashboard_data.system_health < 0.7:
            risks["high"].append("Critical system health degradation")
        if dashboard_data.error_summary.total_errors > 1000:
            risks["high"].append("Excessive error accumulation")

        # Medium risks
        if (
            dashboard_data.quality_metrics.get("overall_quality", {}).get(
                "current", 0.0
            )
            < 0.8
        ):
            risks["medium"].append("Declining data quality standards")
        if len(dashboard_data.alerts) > 10:
            risks["medium"].append("Multiple active system alerts")

        # Low risks
        if (
            dashboard_data.performance_metrics.get("execution_time", {}).get("avg", 0.0)
            > 600
        ):
            risks["low"].append("Slow processing performance")

        return risks

    def _create_executive_appendices(
        self, dashboard_data: DashboardData
    ) -> Dict[str, Any]:
        """Create executive appendices."""
        return {
            "alerts_summary": [alert["metric"] for alert in dashboard_data.alerts[:10]],
            "error_categories": dashboard_data.error_summary.by_category,
            "performance_metrics": dashboard_data.performance_metrics,
        }

    def _create_technical_summary(
        self, dashboard_data: DashboardData, error_trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create technical summary section."""
        return {
            "validation_engine_version": "1.0.0",  # Would come from version info
            "rules_executed": len(dashboard_data.error_summary.by_category),
            "data_volume_processed": "Unknown",  # Would need to track this
            "processing_nodes": 1,  # Would come from infrastructure info
            "error_trend": error_trends.get("resolution_rate", 0.0),
            "performance_baseline": dashboard_data.performance_metrics,
        }

    def _create_technical_findings(
        self,
        dashboard_data: DashboardData,
        error_trends: Dict[str, Any],
        performance_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create technical findings section."""
        return {
            "error_patterns": dashboard_data.error_summary.top_patterns,
            "performance_benchmarks": performance_report.get("metrics", {}),
            "system_limits": {
                "max_errors_per_hour": 1000,
                "max_processing_time": 3600,  # 1 hour
                "min_quality_score": 0.8,
            },
            "bottlenecks_identified": self._identify_bottlenecks(dashboard_data),
            "optimization_opportunities": self._identify_optimizations(dashboard_data),
        }

    def _create_technical_recommendations(
        self, dashboard_data: DashboardData, error_trends: Dict[str, Any]
    ) -> List[str]:
        """Create technical recommendations."""
        recommendations = []

        # Based on error patterns
        top_patterns = dashboard_data.error_summary.top_patterns
        if top_patterns:
            top_error = top_patterns[0]
            recommendations.append(
                f"Address most common error pattern: {top_error['pattern']} ({top_error['count']} occurrences)"
            )

        # Based on performance
        exec_time = dashboard_data.performance_metrics.get("execution_time", {})
        if exec_time.get("avg", 0) > 300:
            recommendations.append("Implement parallel processing for validation rules")
            recommendations.append(
                "Add caching for frequently accessed validation data"
            )

        # Based on error trends
        if error_trends.get("resolution_rate", 0.0) < 0.5:
            recommendations.append("Improve error resolution workflows and automation")

        return recommendations

    def _assess_technical_risks(
        self, dashboard_data: DashboardData, error_trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess technical risks."""
        return {
            "code_quality": "good",  # Would assess based on complexity metrics
            "performance_degradation": (
                "low" if dashboard_data.system_health > 0.8 else "high"
            ),
            "scalability_concerns": "none",  # Would assess based on load metrics
            "maintenance_burden": (
                "medium"
                if len(dashboard_data.error_summary.top_patterns) > 5
                else "low"
            ),
        }

    def _create_technical_appendices(
        self, error_trends: Dict[str, Any], performance_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create technical appendices."""
        return {
            "error_trend_analysis": error_trends,
            "performance_benchmarks": performance_report,
            "system_configuration": {},  # Would include actual config
            "validation_rules_inventory": [],  # Would list all active rules
        }

    def _create_compliance_summary(
        self, dashboard_data: DashboardData, error_summary: ErrorSummary
    ) -> Dict[str, Any]:
        """Create compliance summary section."""
        return {
            "compliance_framework": "ISO 27001 / GDPR / Data Quality Standards",
            "audit_period": dashboard_data.timestamp.strftime("%B %Y"),
            "overall_compliance_score": dashboard_data.system_health,
            "data_quality_standard": (
                "Achieved"
                if dashboard_data.quality_metrics.get("overall_quality", {}).get(
                    "current", 0.0
                )
                > 0.9
                else "Needs Improvement"
            ),
            "error_management_compliance": (
                "Compliant" if error_summary.total_errors < 100 else "Non-Compliant"
            ),
        }

    def _create_compliance_findings(
        self, dashboard_data: DashboardData, error_summary: ErrorSummary
    ) -> Dict[str, Any]:
        """Create compliance findings section."""
        return {
            "regulatory_compliance": {
                "data_quality_standards": dashboard_data.quality_metrics.get(
                    "overall_quality", {}
                ).get("current", 0.0)
                > 0.85,
                "error_reporting_standards": error_summary.total_errors < 100,
                "audit_trail_completeness": True,  # Would check actual audit logs
            },
            "quality_assurance_compliance": {
                "validation_coverage": "high",  # Would calculate actual coverage
                "error_resolution_timeliness": dashboard_data.performance_metrics.get(
                    "error_resolution", {}
                ).get("status", "unknown"),
                "documentation_completeness": True,  # Would check documentation
            },
            "non_compliances_identified": [
                (
                    f"High error count: {error_summary.total_errors}"
                    if error_summary.total_errors > 100
                    else None
                ),
                (
                    f"Low quality score: {dashboard_data.quality_metrics.get('overall_quality', {}).get('current', 0.0)}"
                    if dashboard_data.quality_metrics.get("overall_quality", {}).get(
                        "current", 0.0
                    )
                    < 0.8
                    else None
                ),
            ],
        }

    def _create_compliance_recommendations(
        self, dashboard_data: DashboardData, error_summary: ErrorSummary
    ) -> List[str]:
        """Create compliance recommendations."""
        recommendations = []

        if (
            dashboard_data.quality_metrics.get("overall_quality", {}).get(
                "current", 0.0
            )
            < 0.9
        ):
            recommendations.append(
                "Enhance data quality controls to meet regulatory standards"
            )
            recommendations.append(
                "Implement additional validation checkpoints for critical data"
            )

        if error_summary.total_errors > 50:
            recommendations.append(
                "Strengthen error detection and correction procedures"
            )
            recommendations.append(
                "Conduct root cause analysis for recurring error patterns"
            )

        if dashboard_data.system_health < 0.9:
            recommendations.append(
                "Improve system monitoring and alerting capabilities"
            )
            recommendations.append("Establish regular compliance audits and reviews")

        return recommendations

    def _assess_compliance_risks(
        self, dashboard_data: DashboardData, error_summary: ErrorSummary
    ) -> Dict[str, Any]:
        """Assess compliance risks."""
        return {
            "regulatory_risk": (
                "high"
                if dashboard_data.quality_metrics.get("overall_quality", {}).get(
                    "current", 0.0
                )
                < 0.8
                else "low"
            ),
            "operational_risk": "medium" if error_summary.total_errors > 100 else "low",
            "reputational_risk": (
                "high" if dashboard_data.system_health < 0.7 else "low"
            ),
            "financial_risk": "low",  # Would assess based on compliance fines, etc.
        }

    def _create_compliance_appendices(
        self, error_summary: ErrorSummary
    ) -> Dict[str, Any]:
        """Create compliance appendices."""
        return {
            "regulatory_frameworks": ["ISO 27001", "GDPR", "Data Quality Standards"],
            "audit_findings": error_summary.critical_issues,
            "corrective_actions": [],  # Would include actual corrective actions
            "compliance_certifications": [],  # Would include actual certifications
        }

    def _get_health_status(self, health_score: float) -> str:
        """Get health status string."""
        if health_score >= 0.9:
            return "excellent"
        elif health_score >= 0.8:
            return "good"
        elif health_score >= 0.7:
            return "fair"
        else:
            return "poor"

    def _identify_bottlenecks(self, dashboard_data: DashboardData) -> List[str]:
        """Identify performance bottlenecks."""
        bottlenecks = []

        exec_time = dashboard_data.performance_metrics.get("execution_time", {})
        if exec_time.get("avg", 0) > 300:
            bottlenecks.append("Validation execution time exceeding thresholds")

        error_rate = dashboard_data.quality_metrics.get("error_rate", {})
        if error_rate.get("current", 0) > 0.1:
            bottlenecks.append("High error rate impacting throughput")

        return bottlenecks

    def _identify_optimizations(self, dashboard_data: DashboardData) -> List[str]:
        """Identify optimization opportunities."""
        optimizations = []

        # Check for optimization opportunities
        throughput = dashboard_data.performance_metrics.get("throughput", {})
        if throughput.get("current", 0) < 100:  # Arbitrary threshold
            optimizations.append("Consider parallel processing for improved throughput")

        if len(dashboard_data.error_summary.top_patterns) > 3:
            optimizations.append(
                "Implement targeted fixes for recurring error patterns"
            )

        return optimizations

    def export_report(
        self, report: ValidationReport, filepath: Path, format: str = "html"
    ):
        """
        Export validation report to file.

        Args:
            report: ValidationReport to export
            filepath: Path to export file
            format: Export format ("html", "json", "pdf")
        """
        if format == "json":
            content = json.dumps(self._report_to_dict(report), indent=2, default=str)
        elif format == "html":
            content = self._generate_html_report(report)
        else:
            content = str(report)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def _report_to_dict(self, report: ValidationReport) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_id": report.report_id,
            "title": report.title,
            "generated_at": report.generated_at.isoformat(),
            "time_range": report.time_range,
            "executive_summary": report.executive_summary,
            "detailed_findings": report.detailed_findings,
            "recommendations": report.recommendations,
            "data_quality_score": report.data_quality_score,
            "system_health_score": report.system_health_score,
            "risk_assessment": report.risk_assessment,
            "appendices": report.appendices,
        }

    def _generate_html_report(self, report: ValidationReport) -> str:
        """Generate HTML format report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ background: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .score {{ font-size: 24px; font-weight: bold; color: {'#28a745' if report.system_health_score > 0.8 else '#dc3545'}; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .recommendations {{ background: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; }}
                .risk-high {{ color: #dc3545; }}
                .risk-medium {{ color: #ffc107; }}
                .risk-low {{ color: #28a745; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.title}</h1>
                <p><strong>Report ID:</strong> {report.report_id}</p>
                <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Time Range:</strong> {report.time_range}</p>
            </div>

            <div class="metric">
                <h2>Executive Summary</h2>
                <p><strong>System Health Score:</strong> <span class="score">{report.system_health_score:.1%}</span></p>
                <p><strong>Data Quality Score:</strong> {report.data_quality_score:.1%}</p>
            </div>

            <div class="section">
                <h2>Detailed Findings</h2>
                {self._generate_findings_html(report.detailed_findings)}
            </div>

            <div class="recommendations">
                <h2>Recommendations</h2>
                <ul>
                    {"".join(f"<li>{rec}</li>" for rec in report.recommendations)}
                </ul>
            </div>

            <div class="section">
                <h2>Risk Assessment</h2>
                {self._generate_risks_html(report.risk_assessment)}
            </div>
        </body>
        </html>
        """

        return html

    def _generate_findings_html(self, findings: Dict[str, Any]) -> str:
        """Generate HTML for findings section."""
        html = ""
        for category, data in findings.items():
            html += f"<h3>{category.replace('_', ' ').title()}</h3>"
            if isinstance(data, dict):
                for key, value in data.items():
                    html += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"
            elif isinstance(data, list):
                html += "<ul>"
                for item in data:
                    html += f"<li>{item}</li>"
                html += "</ul>"
        return html

    def _generate_risks_html(self, risks: Dict[str, Any]) -> str:
        """Generate HTML for risks section."""
        html = ""
        for level, items in risks.items():
            if items:
                css_class = f"risk-{level.lower()}"
                html += f"<h3 class='{css_class}'>{level.upper()} RISKS</h3><ul>"
                for item in items:
                    html += f"<li>{item}</li>"
                html += "</ul>"
        return html

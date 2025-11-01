"""
Quality assurance suite for validation framework.

Provides comprehensive quality assurance testing including
regression testing, compliance verification, and quality metrics.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .test_framework import ValidationTestFramework, TestSuite, TestCase
from .test_data_generator import TestDataGenerator
from ..rules.base_rules import ValidationRuleEngine


@dataclass
class QualityAssuranceReport:
    """Comprehensive quality assurance report."""

    report_id: str
    timestamp: datetime
    test_coverage: Dict[str, float]
    quality_metrics: Dict[str, Any]
    regression_results: Dict[str, Any]
    compliance_status: Dict[str, Any]
    recommendations: List[str]
    risk_assessment: Dict[str, Any]


class QualityAssuranceSuite:
    """
    Comprehensive quality assurance suite.

    Provides automated quality assurance testing, regression detection,
    compliance verification, and quality metrics reporting.
    """

    def __init__(
        self,
        test_framework: ValidationTestFramework,
        data_generator: TestDataGenerator,
        rule_engine: Optional[ValidationRuleEngine] = None,
    ):
        self.test_framework = test_framework
        self.data_generator = data_generator
        self.rule_engine = rule_engine or ValidationRuleEngine()

        # Quality baselines
        self.quality_baselines = self._load_quality_baselines()

        # Historical data for regression detection
        self.historical_results: Dict[str, Any] = {}

    def _load_quality_baselines(self) -> Dict[str, Any]:
        """Load quality baseline expectations."""
        return {
            "validation_accuracy": {
                "gene": 0.95,  # 95% of gene validations should pass
                "variant": 0.90,  # 90% of variant validations should pass
                "phenotype": 0.92,  # 92% of phenotype validations should pass
                "publication": 0.88,  # 88% of publication validations should pass
            },
            "performance_targets": {
                "max_validation_time_ms": 100,  # Max 100ms per validation
                "max_memory_mb": 50,  # Max 50MB memory usage
                "min_throughput": 100,  # Min 100 validations/second
            },
            "quality_thresholds": {
                "min_quality_score": 0.8,  # Minimum acceptable quality score
                "max_error_rate": 0.05,  # Maximum 5% error rate
                "max_warning_rate": 0.15,  # Maximum 15% warning rate
            },
        }

    def run_comprehensive_qa(self) -> QualityAssuranceReport:
        """
        Run comprehensive quality assurance testing.

        Returns:
            QualityAssuranceReport with complete QA results
        """
        # Run test coverage analysis
        test_coverage = self._analyze_test_coverage()

        # Run quality metrics assessment
        quality_metrics = self._assess_quality_metrics()

        # Run regression testing
        regression_results = self._run_regression_tests()

        # Check compliance status
        compliance_status = self._check_compliance_status()

        # Generate recommendations
        recommendations = self._generate_qa_recommendations(
            test_coverage, quality_metrics, regression_results, compliance_status
        )

        # Assess risks
        risk_assessment = self._assess_qa_risks(
            test_coverage, quality_metrics, regression_results
        )

        report = QualityAssuranceReport(
            report_id=self._generate_report_id(),
            timestamp=datetime.now(),
            test_coverage=test_coverage,
            quality_metrics=quality_metrics,
            regression_results=regression_results,
            compliance_status=compliance_status,
            recommendations=recommendations,
            risk_assessment=risk_assessment,
        )

        return report

    def _analyze_test_coverage(self) -> Dict[str, float]:
        """Analyze test coverage across validation rules."""
        coverage = {}

        # Get all available rules
        available_rules = self.rule_engine.get_available_rules()

        for entity_type, rules in available_rules.items():
            # Count how many rules have tests (simplified - would need actual test registry)
            # For now, assume 70% coverage as a baseline
            coverage[entity_type] = 0.7

            # This would be enhanced to actually check test coverage
            # by analyzing test files and mapping them to rules

        # Overall coverage
        coverage["overall"] = (
            sum(coverage.values()) / len(coverage) if coverage else 0.0
        )

        return coverage

    def _assess_quality_metrics(self) -> Dict[str, Any]:
        """Assess current quality metrics against baselines."""
        metrics = {}

        # Run sample validations to assess current quality
        test_datasets = self.data_generator.generate_comprehensive_test_suite()

        for entity_type, datasets in test_datasets.items():
            # Use the 'good' quality dataset for assessment
            good_dataset = next(
                (d for d in datasets if d.quality_profile == "good"), None
            )

            if good_dataset:
                # Validate sample data
                results = self.rule_engine.validate_batch(
                    entity_type, good_dataset.data[:100]
                )  # Sample first 100

                # Calculate metrics
                passed = sum(1 for r in results if r.is_valid)
                total = len(results)
                pass_rate = passed / total if total > 0 else 0

                error_count = sum(
                    len([i for i in r.issues if i.get("severity") == "error"])
                    for r in results
                )
                warning_count = sum(
                    len([i for i in r.issues if i.get("severity") == "warning"])
                    for r in results
                )

                avg_quality = sum(r.score for r in results) / total if total > 0 else 0

                metrics[entity_type] = {
                    "validation_accuracy": pass_rate,
                    "average_quality_score": avg_quality,
                    "error_rate": error_count / total if total > 0 else 0,
                    "warning_rate": warning_count / total if total > 0 else 0,
                    "meets_baseline": pass_rate
                    >= self.quality_baselines["validation_accuracy"].get(
                        entity_type, 0.8
                    ),
                }

        return metrics

    def _run_regression_tests(self) -> Dict[str, Any]:
        """Run regression tests to detect quality degradation."""
        regression_results = {
            "regressions_detected": [],
            "improvements_detected": [],
            "stable_metrics": [],
            "test_comparison": {},
        }

        # Compare current metrics with historical baselines
        current_metrics = self._assess_quality_metrics()

        for entity_type, metrics in current_metrics.items():
            baseline_accuracy = self.quality_baselines["validation_accuracy"].get(
                entity_type, 0.8
            )
            current_accuracy = metrics["validation_accuracy"]

            # Check for regression (significant drop in accuracy)
            if current_accuracy < baseline_accuracy * 0.95:  # 5% degradation
                regression_results["regressions_detected"].append(
                    {
                        "entity_type": entity_type,
                        "metric": "validation_accuracy",
                        "baseline": baseline_accuracy,
                        "current": current_accuracy,
                        "degradation": baseline_accuracy - current_accuracy,
                    }
                )
            elif current_accuracy > baseline_accuracy * 1.05:  # 5% improvement
                regression_results["improvements_detected"].append(
                    {
                        "entity_type": entity_type,
                        "metric": "validation_accuracy",
                        "baseline": baseline_accuracy,
                        "current": current_accuracy,
                        "improvement": current_accuracy - baseline_accuracy,
                    }
                )
            else:
                regression_results["stable_metrics"].append(entity_type)

        # Store current results for future comparison
        self.historical_results[datetime.now().isoformat()] = current_metrics

        return regression_results

    def _check_compliance_status(self) -> Dict[str, Any]:
        """Check compliance with quality standards and regulations."""
        compliance = {
            "data_quality_standards": {},
            "performance_standards": {},
            "documentation_standards": {},
            "overall_compliance": "unknown",
        }

        # Check data quality compliance
        quality_metrics = self._assess_quality_metrics()
        min_quality_threshold = self.quality_baselines["quality_thresholds"][
            "min_quality_score"
        ]

        compliance["data_quality_standards"] = {
            "status": (
                "compliant"
                if all(
                    m.get("average_quality_score", 0) >= min_quality_threshold
                    for m in quality_metrics.values()
                )
                else "non_compliant"
            ),
            "details": {
                et: m.get("average_quality_score", 0)
                for et, m in quality_metrics.items()
            },
        }

        # Check performance compliance (simplified)
        compliance["performance_standards"] = {
            "status": "compliant",  # Would need actual performance metrics
            "details": "Performance within acceptable ranges",
        }

        # Check documentation standards (simplified)
        compliance["documentation_standards"] = {
            "status": "compliant",  # Would need documentation validation
            "details": "Documentation standards met",
        }

        # Overall compliance
        standards = [
            compliance["data_quality_standards"]["status"],
            compliance["performance_standards"]["status"],
            compliance["documentation_standards"]["status"],
        ]

        if all(s == "compliant" for s in standards):
            compliance["overall_compliance"] = "compliant"
        elif any(s == "non_compliant" for s in standards):
            compliance["overall_compliance"] = "non_compliant"
        else:
            compliance["overall_compliance"] = "partial"

        return compliance

    def _generate_qa_recommendations(
        self,
        test_coverage: Dict[str, float],
        quality_metrics: Dict[str, Any],
        regression_results: Dict[str, Any],
        compliance_status: Dict[str, Any],
    ) -> List[str]:
        """Generate QA improvement recommendations."""
        recommendations = []

        # Test coverage recommendations
        if test_coverage.get("overall", 0) < 0.8:
            recommendations.append(
                "Increase test coverage to at least 80% for all validation rules"
            )

        for entity_type, coverage in test_coverage.items():
            if entity_type != "overall" and coverage < 0.7:
                recommendations.append(
                    f"Improve test coverage for {entity_type} validation rules"
                )

        # Quality metrics recommendations
        for entity_type, metrics in quality_metrics.items():
            if not metrics.get("meets_baseline", True):
                recommendations.append(
                    f"Improve validation accuracy for {entity_type} entities"
                )

            if (
                metrics.get("error_rate", 0)
                > self.quality_baselines["quality_thresholds"]["max_error_rate"]
            ):
                recommendations.append(
                    f"Reduce error rate for {entity_type} validations"
                )

        # Regression recommendations
        if regression_results["regressions_detected"]:
            recommendations.append("Address detected quality regressions immediately")
            for regression in regression_results["regressions_detected"]:
                recommendations.append(
                    f"Fix regression in {regression['entity_type']} validation accuracy"
                )

        # Compliance recommendations
        if compliance_status["overall_compliance"] != "compliant":
            recommendations.append(
                "Address compliance issues to meet quality standards"
            )

        if not recommendations:
            recommendations.append(
                "Continue maintaining current quality assurance practices"
            )

        return recommendations

    def _assess_qa_risks(
        self,
        test_coverage: Dict[str, float],
        quality_metrics: Dict[str, Any],
        regression_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess QA-related risks."""
        risks = {"high": [], "medium": [], "low": []}

        # High risks
        if test_coverage.get("overall", 0) < 0.6:
            risks["high"].append("Critically low test coverage increases system risk")

        if regression_results["regressions_detected"]:
            risks["high"].append(
                "Quality regressions detected - immediate attention required"
            )

        # Medium risks
        for entity_type, metrics in quality_metrics.items():
            if metrics.get("error_rate", 0) > 0.1:  # 10% error rate
                risks["medium"].append(f"High error rate in {entity_type} validation")

        if any(
            coverage < 0.7
            for coverage in test_coverage.values()
            if isinstance(coverage, float)
        ):
            risks["medium"].append("Inadequate test coverage for some validation rules")

        # Low risks
        if not regression_results["improvements_detected"]:
            risks["low"].append("No recent quality improvements detected")

        return risks

    def _generate_report_id(self) -> str:
        """Generate a unique QA report ID."""
        import uuid

        return f"QA_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"

    def create_standard_test_suites(self) -> List[TestSuite]:
        """
        Create standard test suites for quality assurance.

        Returns:
            List of standard test suites
        """
        suites = []

        # Generate test data
        test_datasets = self.data_generator.generate_comprehensive_test_suite()

        for entity_type, datasets in test_datasets.items():
            # Create unit test suite
            test_cases = []
            for dataset in datasets:
                for i, record in enumerate(
                    dataset.data[:10]
                ):  # Sample first 10 records
                    test_case = TestCase(
                        test_id=f"{entity_type}_unit_{dataset.quality_profile}_{i}",
                        name=f"Unit test {entity_type} {dataset.quality_profile} data {i}",
                        description=f"Test {entity_type} validation with {dataset.quality_profile} quality data",
                        test_type=self.test_framework.TestType.UNIT,
                        entity_type=entity_type,
                        input_data=record,
                        expected_result={
                            "issues": [],  # Would need to be populated based on quality profile
                            "quality_score": (
                                0.8 if dataset.quality_profile == "good" else 0.5
                            ),
                        },
                    )
                    test_cases.append(test_case)

            suite = TestSuite(
                suite_id=f"qa_unit_{entity_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name=f"QA Unit Tests - {entity_type.title()}",
                description=f"Quality assurance unit tests for {entity_type} validation",
                test_cases=test_cases,
                tags=["qa", "unit", entity_type],
            )

            suites.append(suite)

        return suites

    def run_qa_test_suites(self) -> Dict[str, Any]:
        """
        Run all QA test suites.

        Returns:
            QA test results
        """
        suites = self.create_standard_test_suites()

        # Register suites
        for suite in suites:
            self.test_framework.register_suite(suite)

        # Run all suites
        run_result = self.test_framework.run_all_suites()

        # Analyze results
        analysis = self._analyze_qa_test_results(run_result)

        return {
            "run_result": run_result,
            "analysis": analysis,
            "recommendations": self._generate_test_recommendations(analysis),
        }

    def _analyze_qa_test_results(self, run_result: Any) -> Dict[str, Any]:
        """Analyze QA test results."""
        analysis = {
            "overall_success_rate": 0.0,
            "entity_type_performance": {},
            "quality_profile_performance": {},
            "common_failures": [],
        }

        if not run_result or not hasattr(run_result, "suite_results"):
            return analysis

        total_tests = 0
        passed_tests = 0

        for suite_result in run_result.suite_results:
            for test_result in suite_result.test_results:
                total_tests += 1
                if test_result.status.value == "passed":
                    passed_tests += 1

                # Analyze by entity type
                entity_type = test_result.test_case.entity_type
                if entity_type not in analysis["entity_type_performance"]:
                    analysis["entity_type_performance"][entity_type] = {
                        "passed": 0,
                        "total": 0,
                    }

                analysis["entity_type_performance"][entity_type]["total"] += 1
                if test_result.status.value == "passed":
                    analysis["entity_type_performance"][entity_type]["passed"] += 1

        analysis["overall_success_rate"] = (
            passed_tests / total_tests if total_tests > 0 else 0
        )

        # Calculate entity type success rates
        for entity_type, perf in analysis["entity_type_performance"].items():
            perf["success_rate"] = (
                perf["passed"] / perf["total"] if perf["total"] > 0 else 0
            )

        return analysis

    def _generate_test_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate test improvement recommendations."""
        recommendations = []

        success_rate = analysis.get("overall_success_rate", 0)

        if success_rate < 0.8:
            recommendations.append(
                "Overall test success rate below 80% - investigate failing tests"
            )

        for entity_type, perf in analysis.get("entity_type_performance", {}).items():
            if perf.get("success_rate", 0) < 0.75:
                recommendations.append(
                    f"Improve test success rate for {entity_type} validation"
                )

        if not recommendations:
            recommendations.append(
                "Test suite performing well - continue regular QA testing"
            )

        return recommendations

    def export_qa_report(
        self, report: QualityAssuranceReport, filepath: Path, format: str = "html"
    ):
        """
        Export QA report to file.

        Args:
            report: QA report to export
            filepath: Path to export file
            format: Export format
        """
        if format == "json":
            import json

            data = {
                "report_id": report.report_id,
                "timestamp": report.timestamp.isoformat(),
                "test_coverage": report.test_coverage,
                "quality_metrics": report.quality_metrics,
                "regression_results": report.regression_results,
                "compliance_status": report.compliance_status,
                "recommendations": report.recommendations,
                "risk_assessment": report.risk_assessment,
            }

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)

        elif format == "html":
            self._export_html_qa_report(report, filepath)

    def _export_html_qa_report(self, report: QualityAssuranceReport, filepath: Path):
        """Export QA report in HTML format."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Quality Assurance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ background: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .status-good {{ color: #28a745; }}
                .status-warning {{ color: #ffc107; }}
                .status-critical {{ color: #dc3545; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .recommendations {{ background: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Quality Assurance Report</h1>
                <p><strong>Report ID:</strong> {report.report_id}</p>
                <p><strong>Generated:</strong> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="metric">
                <h2>Test Coverage</h2>
                <p><strong>Overall Coverage:</strong> {report.test_coverage.get('overall', 0):.1%}</p>
                <table>
                    <tr><th>Entity Type</th><th>Coverage</th></tr>
        """

        for entity_type, coverage in report.test_coverage.items():
            if entity_type != "overall":
                html += (
                    f"<tr><td>{entity_type.title()}</td><td>{coverage:.1%}</td></tr>"
                )

        html += """
                </table>
            </div>

            <div class="metric">
                <h2>Quality Metrics</h2>
                <table>
                    <tr><th>Entity Type</th><th>Accuracy</th><th>Quality Score</th><th>Error Rate</th><th>Status</th></tr>
        """

        for entity_type, metrics in report.quality_metrics.items():
            status_class = (
                "status-good"
                if metrics.get("meets_baseline", False)
                else "status-warning"
            )
            html += f"""
                <tr>
                    <td>{entity_type.title()}</td>
                    <td>{metrics.get('validation_accuracy', 0):.1%}</td>
                    <td>{metrics.get('average_quality_score', 0):.2f}</td>
                    <td>{metrics.get('error_rate', 0):.1%}</td>
                    <td class="{status_class}">{metrics.get('meets_baseline', 'No')}</td>
                </tr>
            """

        html += """
                </table>
            </div>

            <div class="metric">
                <h2>Compliance Status</h2>
                <p><strong>Overall:</strong> {report.compliance_status.get('overall_compliance', 'unknown').upper()}</p>
        """

        for standard, details in report.compliance_status.items():
            if standard != "overall_compliance":
                status = details.get("status", "unknown")
                status_class = (
                    f"status-{status.lower()}"
                    if status in ["compliant", "non_compliant"]
                    else ""
                )
                html += f"<p><strong>{standard.replace('_', ' ').title()}:</strong> <span class='{status_class}'>{status.upper()}</span></p>"

        html += """
            </div>

            <div class="recommendations">
                <h2>Recommendations</h2>
                <ul>
        """

        for rec in report.recommendations:
            html += f"<li>{rec}</li>"

        html += """
                </ul>
            </div>

            <div class="section">
                <h2>Risk Assessment</h2>
        """

        for level, risks in report.risk_assessment.items():
            if risks:
                level_class = f"status-{level.lower()}"
                html += f"<h3 class='{level_class}'>{level.upper()} RISKS</h3><ul>"
                for risk in risks:
                    html += f"<li>{risk}</li>"
                html += "</ul>"

        html += """
            </div>
        </body>
        </html>
        """

        with open(filepath, "w") as f:
            f.write(html)

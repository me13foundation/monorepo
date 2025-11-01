"""
Validation test framework.

Provides structured testing capabilities for validation rules,
test suites, and comprehensive test execution with reporting.
"""

import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from ..rules.base_rules import ValidationRuleEngine, ValidationResult


class TestStatus(Enum):
    """Status of a test execution."""

    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class TestType(Enum):
    """Types of validation tests."""

    UNIT = "unit"  # Test individual rules
    INTEGRATION = "integration"  # Test rule combinations
    SYSTEM = "system"  # Test complete validation pipeline
    PERFORMANCE = "performance"  # Performance benchmarks
    REGRESSION = "regression"  # Regression tests


@dataclass
class TestCase:
    """Individual test case definition."""

    test_id: str
    name: str
    description: str
    test_type: TestType
    entity_type: str
    input_data: Dict[str, Any]
    expected_result: Dict[str, Any]
    timeout_seconds: float = 30.0
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class TestResult:
    """Result of a test execution."""

    test_case: TestCase
    status: TestStatus
    execution_time: float
    actual_result: Optional[ValidationResult]
    error_message: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class TestSuite:
    """Collection of test cases."""

    suite_id: str
    name: str
    description: str
    test_cases: List[TestCase]
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class TestRunResult:
    """Results of a complete test run."""

    run_id: str
    suite_results: List["SuiteResult"]
    summary: Dict[str, Any]
    execution_time: float
    timestamp: datetime


@dataclass
class SuiteResult:
    """Results for a test suite."""

    suite: TestSuite
    test_results: List[TestResult]
    setup_success: bool
    teardown_success: bool
    execution_time: float


class ValidationTestFramework:
    """
    Comprehensive validation testing framework.

    Provides structured testing capabilities for validation rules,
    automated test execution, and detailed reporting.
    """

    def __init__(self, rule_engine: Optional[ValidationRuleEngine] = None):
        self.rule_engine = rule_engine or ValidationRuleEngine()
        self.test_suites: Dict[str, TestSuite] = {}
        self.test_history: List[TestRunResult] = []

        # Callbacks
        self.on_test_start: Optional[Callable[[TestCase], None]] = None
        self.on_test_complete: Optional[Callable[[TestResult], None]] = None
        self.on_suite_complete: Optional[Callable[[SuiteResult], None]] = None

    def register_suite(self, suite: TestSuite):
        """Register a test suite."""
        self.test_suites[suite.suite_id] = suite

    def unregister_suite(self, suite_id: str):
        """Unregister a test suite."""
        self.test_suites.pop(suite_id, None)

    def create_unit_test_suite(
        self, entity_type: str, test_cases: List[TestCase]
    ) -> TestSuite:
        """
        Create a unit test suite for a specific entity type.

        Args:
            entity_type: Type of entity to test
            test_cases: List of test cases

        Returns:
            TestSuite configured for unit testing
        """
        return TestSuite(
            suite_id=f"unit_{entity_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"Unit Tests - {entity_type.title()}",
            description=f"Unit tests for {entity_type} validation rules",
            test_cases=test_cases,
            tags=["unit", entity_type],
        )

    def create_integration_test_suite(
        self, name: str, test_cases: List[TestCase]
    ) -> TestSuite:
        """
        Create an integration test suite.

        Args:
            name: Suite name
            test_cases: List of integration test cases

        Returns:
            TestSuite configured for integration testing
        """
        return TestSuite(
            suite_id=f"integration_{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"Integration Tests - {name}",
            description=f"Integration tests for {name}",
            test_cases=test_cases,
            tags=["integration", name.lower().replace(" ", "_")],
        )

    def run_test_suite(self, suite_id: str) -> Optional[SuiteResult]:
        """
        Run a specific test suite.

        Args:
            suite_id: ID of the test suite to run

        Returns:
            SuiteResult or None if suite not found
        """
        if suite_id not in self.test_suites:
            return None

        suite = self.test_suites[suite_id]
        return self._execute_suite(suite)

    def run_all_suites(self, tags: Optional[List[str]] = None) -> TestRunResult:
        """
        Run all registered test suites.

        Args:
            tags: Optional tags to filter suites

        Returns:
            TestRunResult with all suite results
        """
        start_time = time.time()

        suites_to_run = self.test_suites.values()
        if tags:
            suites_to_run = [
                s for s in suites_to_run if any(tag in s.tags for tag in tags)
            ]

        suite_results = []
        for suite in suites_to_run:
            result = self._execute_suite(suite)
            if result:
                suite_results.append(result)

        execution_time = time.time() - start_time

        # Create summary
        summary = self._create_run_summary(suite_results)

        run_result = TestRunResult(
            run_id=self._generate_run_id(),
            suite_results=suite_results,
            summary=summary,
            execution_time=execution_time,
            timestamp=datetime.now(),
        )

        self.test_history.append(run_result)
        return run_result

    def run_performance_tests(self, iterations: int = 100) -> Dict[str, Any]:
        """
        Run performance tests on validation rules.

        Args:
            iterations: Number of iterations to run

        Returns:
            Performance test results
        """
        from .performance_benchmark import PerformanceBenchmark

        benchmark = PerformanceBenchmark(self.rule_engine)
        return benchmark.run_comprehensive_benchmark(iterations)

    def _execute_suite(self, suite: TestSuite) -> SuiteResult:
        """Execute a test suite."""
        start_time = time.time()

        # Setup
        setup_success = True
        if suite.setup_function:
            try:
                suite.setup_function()
            except Exception as e:
                setup_success = False
                print(f"Suite setup failed: {e}")

        # Execute tests
        test_results = []
        for test_case in suite.test_cases:
            result = self._execute_test(test_case)
            test_results.append(result)

        # Teardown
        teardown_success = True
        if suite.teardown_function:
            try:
                suite.teardown_function()
            except Exception as e:
                teardown_success = False
                print(f"Suite teardown failed: {e}")

        execution_time = time.time() - start_time

        result = SuiteResult(
            suite=suite,
            test_results=test_results,
            setup_success=setup_success,
            teardown_success=teardown_success,
            execution_time=execution_time,
        )

        if self.on_suite_complete:
            self.on_suite_complete(result)

        return result

    def _execute_test(self, test_case: TestCase) -> TestResult:
        """Execute a single test case."""
        start_time = time.time()

        if self.on_test_start:
            self.on_test_start(test_case)

        try:
            # Execute the test based on type
            if test_case.test_type == TestType.UNIT:
                result = self._execute_unit_test(test_case)
            elif test_case.test_type == TestType.INTEGRATION:
                result = self._execute_integration_test(test_case)
            elif test_case.test_type == TestType.SYSTEM:
                result = self._execute_system_test(test_case)
            elif test_case.test_type == TestType.PERFORMANCE:
                result = self._execute_performance_test(test_case)
            else:
                result = TestResult(
                    test_case=test_case,
                    status=TestStatus.ERROR,
                    execution_time=time.time() - start_time,
                    actual_result=None,
                    error_message=f"Unsupported test type: {test_case.test_type}",
                    details={},
                    timestamp=datetime.now(),
                )

        except Exception as e:
            result = TestResult(
                test_case=test_case,
                status=TestStatus.ERROR,
                execution_time=time.time() - start_time,
                actual_result=None,
                error_message=str(e),
                details={"exception_type": type(e).__name__},
                timestamp=datetime.now(),
            )

        if self.on_test_complete:
            self.on_test_complete(result)

        return result

    def _execute_unit_test(self, test_case: TestCase) -> TestResult:
        """Execute a unit test for validation rules."""
        # Validate the entity
        validation_result = self.rule_engine.validate_entity(
            test_case.entity_type, test_case.input_data
        )

        # Check against expected result
        expected_issues = test_case.expected_result.get("issues", [])
        actual_issues = validation_result.issues

        # Simple matching - in practice would be more sophisticated
        status = TestStatus.PASSED
        error_message = None

        if len(actual_issues) != len(expected_issues):
            status = TestStatus.FAILED
            error_message = (
                f"Expected {len(expected_issues)} issues, got {len(actual_issues)}"
            )

        # Check quality score
        expected_score = test_case.expected_result.get("quality_score", 0.0)
        if abs(validation_result.score - expected_score) > 0.1:  # Allow 10% tolerance
            status = TestStatus.FAILED
            error_message = f"Quality score mismatch: expected {expected_score}, got {validation_result.score}"

        return TestResult(
            test_case=test_case,
            status=status,
            execution_time=0.0,  # Would be set by caller
            actual_result=validation_result,
            error_message=error_message,
            details={
                "expected_issues": len(expected_issues),
                "actual_issues": len(actual_issues),
                "expected_score": expected_score,
                "actual_score": validation_result.score,
            },
            timestamp=datetime.now(),
        )

    def _execute_integration_test(self, test_case: TestCase) -> TestResult:
        """Execute an integration test."""
        # For integration tests, we might test multiple entities or rule combinations
        # Simplified implementation
        return self._execute_unit_test(test_case)

    def _execute_system_test(self, test_case: TestCase) -> TestResult:
        """Execute a system test."""
        # System tests might test complete pipelines
        # Simplified implementation
        return self._execute_unit_test(test_case)

    def _execute_performance_test(self, test_case: TestCase) -> TestResult:
        """Execute a performance test."""
        # Performance tests measure timing
        # Simplified implementation
        return self._execute_unit_test(test_case)

    def _generate_run_id(self) -> str:
        """Generate a unique test run ID."""
        import uuid

        return f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"

    def _create_run_summary(self, suite_results: List[SuiteResult]) -> Dict[str, Any]:
        """Create a summary of test run results."""
        total_suites = len(suite_results)
        total_tests = sum(len(sr.test_results) for sr in suite_results)

        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        skipped_tests = 0

        total_execution_time = 0.0

        for suite_result in suite_results:
            total_execution_time += suite_result.execution_time
            for test_result in suite_result.test_results:
                if test_result.status == TestStatus.PASSED:
                    passed_tests += 1
                elif test_result.status == TestStatus.FAILED:
                    failed_tests += 1
                elif test_result.status == TestStatus.ERROR:
                    error_tests += 1
                elif test_result.status == TestStatus.SKIPPED:
                    skipped_tests += 1

        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        return {
            "total_suites": total_suites,
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "skipped": skipped_tests,
            "success_rate": success_rate,
            "total_execution_time": total_execution_time,
            "avg_test_time": (
                total_execution_time / total_tests if total_tests > 0 else 0
            ),
        }

    def get_test_history(self, limit: int = 10) -> List[TestRunResult]:
        """Get recent test run history."""
        return self.test_history[-limit:]

    def export_test_results(
        self, run_result: TestRunResult, filepath: Path, format: str = "json"
    ):
        """
        Export test results to file.

        Args:
            run_result: Test run results to export
            filepath: Path to export file
            format: Export format ("json", "xml", "html")
        """
        if format == "json":
            import json

            data = {
                "run_id": run_result.run_id,
                "timestamp": run_result.timestamp.isoformat(),
                "execution_time": run_result.execution_time,
                "summary": run_result.summary,
                "suite_results": [
                    {
                        "suite_id": sr.suite.suite_id,
                        "suite_name": sr.suite.name,
                        "execution_time": sr.execution_time,
                        "setup_success": sr.setup_success,
                        "teardown_success": sr.teardown_success,
                        "test_results": [
                            {
                                "test_id": tr.test_case.test_id,
                                "test_name": tr.test_case.name,
                                "status": tr.status.value,
                                "execution_time": tr.execution_time,
                                "error_message": tr.error_message,
                                "details": tr.details,
                            }
                            for tr in sr.test_results
                        ],
                    }
                    for sr in run_result.suite_results
                ],
            }

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)

        elif format == "html":
            self._export_html_results(run_result, filepath)

    def _export_html_results(self, run_result: TestRunResult, filepath: Path):
        """Export test results in HTML format."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Validation Test Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .suite {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .test {{ margin: 5px 0; padding: 10px; border-left: 4px solid #007bff; }}
                .passed {{ border-left-color: #28a745; }}
                .failed {{ border-left-color: #dc3545; }}
                .error {{ border-left-color: #ffc107; }}
                .skipped {{ border-left-color: #6c757d; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Validation Test Results</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Run ID:</strong> {run_result.run_id}</p>
                <p><strong>Timestamp:</strong> {run_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Execution Time:</strong> {run_result.execution_time:.2f}s</p>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Suites</td><td>{run_result.summary['total_suites']}</td></tr>
                    <tr><td>Total Tests</td><td>{run_result.summary['total_tests']}</td></tr>
                    <tr><td>Passed</td><td>{run_result.summary['passed']}</td></tr>
                    <tr><td>Failed</td><td>{run_result.summary['failed']}</td></tr>
                    <tr><td>Errors</td><td>{run_result.summary['errors']}</td></tr>
                    <tr><td>Success Rate</td><td>{run_result.summary['success_rate']:.1f}%</td></tr>
                </table>
            </div>

            <h2>Test Suite Results</h2>
        """

        for suite_result in run_result.suite_results:
            html += f"""
            <div class="suite">
                <h3>{suite_result.suite.name}</h3>
                <p><strong>Suite ID:</strong> {suite_result.suite.suite_id}</p>
                <p><strong>Execution Time:</strong> {suite_result.execution_time:.2f}s</p>
                <p><strong>Tests:</strong> {len(suite_result.test_results)}</p>
            """

            for test_result in suite_result.test_results:
                status_class = test_result.status.value.lower()
                html += f"""
                <div class="test {status_class}">
                    <strong>{test_result.test_case.name}</strong> - {test_result.status.value.upper()}
                    <br><small>{test_result.execution_time:.3f}s</small>
                    {"<br><em>" + test_result.error_message + "</em>" if test_result.error_message else ""}
                </div>
                """

            html += "</div>"

        html += "</body></html>"

        with open(filepath, "w") as f:
            f.write(html)

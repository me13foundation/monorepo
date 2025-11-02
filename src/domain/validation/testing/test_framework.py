"""Compact validation test framework for the integration suite."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Dict, List, Optional

from ..rules.base_rules import ValidationResult, ValidationRuleEngine


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"


@dataclass
class TestCase:
    test_id: str
    name: str
    description: str
    test_type: TestType
    entity_type: str
    input_data: Dict[str, object]
    expected_result: Dict[str, object]


@dataclass
class TestResult:
    test_case: TestCase
    status: str
    execution_time: float
    actual_result: Optional[ValidationResult]
    timestamp: datetime


@dataclass
class TestSuite:
    suite_id: str
    name: str
    description: str
    test_cases: List[TestCase]


@dataclass
class SuiteResult:
    suite: TestSuite
    test_results: List[TestResult]
    execution_time: float


class ValidationTestFramework:
    def __init__(self, rule_engine: Optional[ValidationRuleEngine] = None) -> None:
        self.rule_engine = rule_engine or ValidationRuleEngine()
        self._suites: Dict[str, TestSuite] = {}

    def register_suite(self, suite: TestSuite) -> None:
        self._suites[suite.suite_id] = suite

    def create_unit_test_suite(
        self, entity_type: str, cases: List[TestCase]
    ) -> TestSuite:
        suite_id = f"unit_{entity_type}_{int(time.time())}"
        suite = TestSuite(
            suite_id=suite_id,
            name=f"Unit Tests - {entity_type}",
            description=f"Unit tests for {entity_type} validation",
            test_cases=cases,
        )
        return suite

    def run_test_suite(self, suite_id: str) -> Optional[SuiteResult]:
        suite = self._suites.get(suite_id)
        if suite is None:
            return None

        results: List[TestResult] = []
        start = time.perf_counter()

        for case in suite.test_cases:
            case_start = time.perf_counter()
            actual = self.rule_engine.validate_entity(case.entity_type, case.input_data)
            status = self._evaluate_case(case, actual)
            results.append(
                TestResult(
                    test_case=case,
                    status=status,
                    execution_time=time.perf_counter() - case_start,
                    actual_result=actual,
                    timestamp=datetime.now(UTC),
                )
            )

        return SuiteResult(
            suite=suite,
            test_results=results,
            execution_time=time.perf_counter() - start,
        )

    def _evaluate_case(self, case: TestCase, actual: ValidationResult) -> str:
        expected_issues = case.expected_result.get("issues")
        expected_score = case.expected_result.get("quality_score")

        issues_match = True
        if isinstance(expected_issues, list):
            issues_match = len(actual.issues) == len(expected_issues)

        score_match = True
        if isinstance(expected_score, (int, float)):
            score_match = actual.score >= float(expected_score)

        return "passed" if issues_match and score_match else "failed"


__all__ = [
    "TestCase",
    "TestResult",
    "TestSuite",
    "SuiteResult",
    "TestType",
    "ValidationTestFramework",
]

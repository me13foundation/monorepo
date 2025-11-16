"""
Domain service for data quality assurance.

Provides comprehensive validation, quality scoring, and improvement
suggestions for data sources in the MED13 Resource Library.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from src.domain.entities.user_data_source import (
    SourceConfiguration,
    UserDataSource,
)
from src.domain.services.api_source_service import APIRequestResult
from src.domain.services.file_upload_service import DataRecord
from src.domain.services.quality_metrics_mixin import QualityMetricsMixin
from src.type_definitions.common import JSONObject, JSONValue
from src.type_definitions.json_utils import to_json_value


def _as_json_object(payload: object) -> JSONObject:
    json_payload = to_json_value(payload)
    if isinstance(json_payload, dict):
        return json_payload
    return {}


class QualityScore(BaseModel):
    """Quality score breakdown."""

    overall: float
    completeness: float
    consistency: float
    timeliness: float
    validity: float

    details: JSONObject = Field(default_factory=dict)


class QualityReport(BaseModel):
    """Comprehensive quality report."""

    score: QualityScore
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metrics: JSONObject = Field(default_factory=dict)
    assessed_at: datetime


class QualityAssuranceService(QualityMetricsMixin):
    """
    Domain service for data quality assessment and improvement.

    Analyzes data sources for quality metrics, identifies issues,
    and provides recommendations for improvement.
    """

    def __init__(self) -> None:
        # Quality thresholds
        self.thresholds = {
            "completeness": 0.8,  # 80% complete
            "consistency": 0.9,  # 90% consistent
            "timeliness": 0.7,  # 70% timely
            "validity": 0.95,  # 95% valid
        }
        self.stale_timeliness_threshold = 0.5
        self.min_sample_size = 100

    def assess_file_upload_quality(
        self,
        records: list[DataRecord],
        configuration: SourceConfiguration,
    ) -> QualityReport:
        if not records:
            return self._create_empty_report()

        # Calculate individual metrics
        completeness = self._calculate_completeness(records)
        consistency = self._calculate_consistency(records)
        validity = self._calculate_validity(records, configuration)
        timeliness = self._calculate_timeliness_file(records)

        # Calculate overall score
        overall = self._calculate_overall_score(
            completeness,
            consistency,
            validity,
            timeliness,
        )

        # Generate issues and recommendations
        issues, recommendations = self._analyze_issues_and_recommendations(
            records,
            completeness,
            consistency,
            validity,
            timeliness,
        )

        # Additional metrics
        metrics = _as_json_object(
            {
                "total_records": len(records),
                "valid_records": len([r for r in records if not r.validation_errors]),
                "invalid_records": len([r for r in records if r.validation_errors]),
                "columns": self._extract_columns(records),
                "data_types": self._infer_data_types(records),
                "duplicate_count": self._count_duplicates(records),
                "null_value_stats": self._calculate_null_stats(records),
            },
        )

        return QualityReport(
            score=QualityScore(
                overall=overall,
                completeness=completeness,
                consistency=consistency,
                timeliness=timeliness,
                validity=validity,
                details=_as_json_object(
                    {
                        "completeness_breakdown": self._get_completeness_breakdown(
                            records,
                        ),
                        "consistency_checks": self._get_consistency_checks(records),
                        "validity_errors": self._get_validity_errors(records),
                    },
                ),
            ),
            issues=issues,
            recommendations=recommendations,
            metrics=metrics,
            assessed_at=datetime.now(UTC),
        )

    def assess_api_quality(
        self,
        result: APIRequestResult,
        configuration: SourceConfiguration,
    ) -> QualityReport:
        if not result.success or not result.data:
            return self._create_failure_report(result.errors)

        # Convert API data to records for analysis
        records = self._api_data_to_records(result.data)

        # Calculate metrics similar to file upload
        completeness = self._calculate_completeness(records)
        consistency = self._calculate_consistency(records)
        validity = self._calculate_validity(records, configuration)
        timeliness = self._calculate_timeliness_api(result)

        overall = self._calculate_overall_score(
            completeness,
            consistency,
            validity,
            timeliness,
        )

        issues, recommendations = self._analyze_issues_and_recommendations(
            records,
            completeness,
            consistency,
            validity,
            timeliness,
        )

        # API-specific metrics
        metrics_payload: dict[str, JSONValue] = {
            "response_time_ms": result.response_time_ms,
            "status_code": result.status_code,
            "record_count": result.record_count,
            "data_size_bytes": len(str(result.data)) if result.data else 0,
            "api_endpoint": to_json_value(result.metadata.get("request_url")),
        }

        if records:
            metrics_payload["columns"] = to_json_value(self._extract_columns(records))
            metrics_payload["data_types"] = to_json_value(
                self._infer_data_types(records),
            )
            metrics_payload["duplicate_count"] = self._count_duplicates(records)
        metrics = _as_json_object(metrics_payload)

        return QualityReport(
            score=QualityScore(
                overall=overall,
                completeness=completeness,
                consistency=consistency,
                timeliness=timeliness,
                validity=validity,
                details=_as_json_object(
                    {
                        "api_performance": {
                            "response_time_ms": result.response_time_ms,
                            "status_code": result.status_code,
                        },
                    },
                ),
            ),
            issues=issues,
            recommendations=recommendations,
            metrics=metrics,
            assessed_at=datetime.now(UTC),
        )

    def assess_source_health(self, source: UserDataSource) -> QualityReport:
        existing_metrics = source.quality_metrics

        # Use existing metrics if available
        completeness = existing_metrics.completeness_score or 0.0
        consistency = existing_metrics.consistency_score or 0.0
        timeliness = self._calculate_source_timeliness(source)
        validity = existing_metrics.overall_score or 0.0

        overall = self._calculate_overall_score(
            completeness,
            consistency,
            validity,
            timeliness,
        )

        issues = []
        recommendations = []

        # Check for common issues
        if not source.last_ingested_at:
            issues.append("Source has never been successfully ingested")
            recommendations.append("Run initial data ingestion")

        if source.status.value == "error":
            issues.append("Source is in error state")
            recommendations.append("Review and fix configuration issues")

        if timeliness < self.stale_timeliness_threshold:
            issues.append("Source data may be outdated")
            recommendations.append("Schedule more frequent updates")

        return QualityReport(
            score=QualityScore(
                overall=overall,
                completeness=completeness,
                consistency=consistency,
                timeliness=timeliness,
                validity=validity,
            ),
            issues=issues,
            recommendations=recommendations,
            metrics=_as_json_object(
                {
                    "last_ingested_at": (
                        source.last_ingested_at.isoformat()
                        if source.last_ingested_at
                        else None
                    ),
                    "status": source.status.value,
                    "ingestion_count": (
                        existing_metrics.last_assessed.isoformat()
                        if existing_metrics.last_assessed
                        else None
                    ),
                },
            ),
            assessed_at=datetime.now(UTC),
        )

    def _create_empty_report(self) -> QualityReport:
        return QualityReport(
            score=QualityScore(
                overall=0.0,
                completeness=0.0,
                consistency=0.0,
                timeliness=0.0,
                validity=0.0,
            ),
            issues=["No data to analyze"],
            recommendations=["Upload data for quality assessment"],
            metrics=_as_json_object({}),
            assessed_at=datetime.now(UTC),
        )

    def _create_failure_report(self, errors: list[str]) -> QualityReport:
        return QualityReport(
            score=QualityScore(
                overall=0.0,
                completeness=0.0,
                consistency=0.0,
                timeliness=0.0,
                validity=0.0,
            ),
            issues=errors,
            recommendations=["Fix configuration issues and retry"],
            metrics=_as_json_object({}),
            assessed_at=datetime.now(UTC),
        )

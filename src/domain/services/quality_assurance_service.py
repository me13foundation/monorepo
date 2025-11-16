"""
Domain service for data quality assurance.

Provides comprehensive validation, quality scoring, and improvement
suggestions for data sources in the MED13 Resource Library.
"""

import statistics
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from src.domain.entities.user_data_source import (
    ScheduleFrequency,
    SourceConfiguration,
    UserDataSource,
)
from src.domain.services.api_source_service import APIRequestResult
from src.domain.services.file_upload_service import DataRecord
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


class QualityAssuranceService:
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

    def _calculate_completeness(self, records: list[DataRecord]) -> float:
        if not records:
            return 0.0

        total_fields = 0
        filled_fields = 0

        for record in records:
            for value in record.data.values():
                total_fields += 1
                if value is not None and str(value).strip():
                    filled_fields += 1

        return filled_fields / total_fields if total_fields > 0 else 0.0

    def _calculate_consistency(self, records: list[DataRecord]) -> float:
        if not records:
            return 0.0

        # Check for consistent data types in columns
        columns = self._extract_columns(records)
        consistency_scores = []

        for column in columns:
            values = [r.data.get(column) for r in records if column in r.data]
            if values:
                # Check type consistency
                types = [type(v).__name__ for v in values if v is not None]
                if types:
                    most_common_type = max(set(types), key=types.count)
                    consistent_count = types.count(most_common_type)
                    consistency_scores.append(consistent_count / len(types))

        return statistics.mean(consistency_scores) if consistency_scores else 1.0

    def _calculate_validity(
        self,
        records: list[DataRecord],
        _configuration: SourceConfiguration,
    ) -> float:
        if not records:
            return 0.0

        total_records = len(records)
        valid_records = len([r for r in records if not r.validation_errors])

        return valid_records / total_records

    def _calculate_timeliness_file(self, _records: list[DataRecord]) -> float:
        return 1.0  # File data is current when uploaded

    def _calculate_timeliness_api(self, result: APIRequestResult) -> float:
        # Based on response time - faster is better
        fast_ms = 100
        ok_ms = 1000
        slow_ms = 5000
        if result.response_time_ms < fast_ms:
            return 1.0
        if result.response_time_ms < ok_ms:
            return 0.8
        if result.response_time_ms < slow_ms:
            return 0.6
        return 0.3

    def _calculate_source_timeliness(self, source: UserDataSource) -> float:
        if not source.last_ingested_at:
            return 0.0

        hours_since_ingestion = (
            datetime.now(UTC) - source.last_ingested_at
        ).total_seconds() / 3600

        # Freshness based on expected update frequency
        schedule = source.ingestion_schedule
        if schedule.enabled:
            if schedule.frequency == ScheduleFrequency.HOURLY:
                expected_hours = 1
            elif schedule.frequency == ScheduleFrequency.DAILY:
                expected_hours = 24
            elif schedule.frequency == ScheduleFrequency.WEEKLY:
                expected_hours = 168
            else:
                expected_hours = 24  # Default to daily

            if hours_since_ingestion <= expected_hours:
                return 1.0
            if hours_since_ingestion <= expected_hours * 2:
                return 0.7
            if hours_since_ingestion <= expected_hours * 4:
                return 0.4
            return 0.1

        return 0.5  # Unknown schedule

    def _calculate_overall_score(
        self,
        completeness: float,
        consistency: float,
        validity: float,
        timeliness: float,
    ) -> float:
        weights = {
            "completeness": 0.25,
            "consistency": 0.25,
            "validity": 0.3,
            "timeliness": 0.2,
        }

        return (
            completeness * weights["completeness"]
            + consistency * weights["consistency"]
            + validity * weights["validity"]
            + timeliness * weights["timeliness"]
        )

    def _analyze_issues_and_recommendations(
        self,
        records: list[DataRecord],
        completeness: float,
        consistency: float,
        validity: float,
        timeliness: float,
    ) -> tuple[list[str], list[str]]:
        issues = []
        recommendations = []

        # Completeness issues
        if completeness < self.thresholds["completeness"]:
            issues.append(f"Low completeness: {completeness:.1%}")
            recommendations.append("Review data collection process for missing fields")
            recommendations.append("Consider making optional fields required")

        # Consistency issues
        if consistency < self.thresholds["consistency"]:
            issues.append(f"Low consistency: {consistency:.1%}")
            recommendations.append("Standardize data formats and types")
            recommendations.append("Add data validation rules")

        # Validity issues
        if validity < self.thresholds["validity"]:
            issues.append(f"Low validity: {validity:.1%}")
            invalid_records = len([r for r in records if r.validation_errors])
            issues.append(f"{invalid_records} records have validation errors")
            recommendations.append("Review and fix data validation rules")
            recommendations.append("Cleanse invalid data records")

        # Timeliness issues
        if timeliness < self.thresholds["timeliness"]:
            issues.append(f"Low timeliness: {timeliness:.1%}")
            recommendations.append("Increase data update frequency")
            recommendations.append("Optimize data retrieval performance")

        # General recommendations
        if len(records) < self.min_sample_size:
            recommendations.append("Consider collecting more data samples")

        duplicates = self._count_duplicates(records)
        if duplicates > 0:
            issues.append(f"Found {duplicates} duplicate records")
            recommendations.append("Implement deduplication logic")

        return issues, recommendations

    def _extract_columns(self, records: list[DataRecord]) -> list[str]:
        columns: set[str] = set()
        for record in records:
            columns.update(record.data.keys())
        return sorted(columns)

    def _infer_data_types(self, records: list[DataRecord]) -> dict[str, str]:
        if not records:
            return {}

        columns = self._extract_columns(records)
        types = {}

        for column in columns:
            values = [
                r.data[column]
                for r in records
                if column in r.data and r.data[column] is not None
            ]
            if values:
                # Simple type inference
                if all(isinstance(v, str) for v in values):
                    types[column] = "string"
                elif all(isinstance(v, (int, float)) for v in values):
                    if all(isinstance(v, int) for v in values):
                        types[column] = "integer"
                    else:
                        types[column] = "float"
                elif all(isinstance(v, bool) for v in values):
                    types[column] = "boolean"
                else:
                    types[column] = "mixed"

        return types

    def _count_duplicates(self, records: list[DataRecord]) -> int:
        seen = set()
        duplicates = 0

        for record in records:
            # Simple duplicate detection based on string representation
            record_str = str(sorted(record.data.items()))
            if record_str in seen:
                duplicates += 1
            else:
                seen.add(record_str)

        return duplicates

    def _calculate_null_stats(self, records: list[DataRecord]) -> dict[str, float]:
        if not records:
            return {}

        columns = self._extract_columns(records)
        stats = {}

        for column in columns:
            total = len(records)
            nulls = sum(
                1
                for r in records
                if column not in r.data
                or r.data[column] is None
                or str(r.data[column]).strip() == ""
            )
            stats[column] = nulls / total if total > 0 else 0.0

        return stats

    def _api_data_to_records(self, data: JSONValue) -> list[DataRecord]:
        records = []

        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    records.append(DataRecord(data=item, line_number=i + 1))
        elif isinstance(data, dict):
            # Look for data arrays in common API response formats
            for key in ["data", "results", "records", "items"]:
                value = data.get(key)
                if isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            records.append(DataRecord(data=item, line_number=i + 1))
                    break
            else:
                # Single record
                records.append(DataRecord(data=data))

        return records

    def _get_completeness_breakdown(
        self,
        records: list[DataRecord],
    ) -> dict[str, float]:
        return self._calculate_null_stats(records)

    def _get_consistency_checks(self, records: list[DataRecord]) -> JSONObject:
        types = self._infer_data_types(records)
        payload = {
            "inferred_types": types,
            "columns_with_mixed_types": [
                col for col, typ in types.items() if typ == "mixed"
            ],
        }
        return _as_json_object(payload)

    def _get_validity_errors(self, records: list[DataRecord]) -> dict[str, int]:
        error_counts: dict[str, int] = {}
        for record in records:
            for error in record.validation_errors:
                error_counts[error] = error_counts.get(error, 0) + 1
        return error_counts

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

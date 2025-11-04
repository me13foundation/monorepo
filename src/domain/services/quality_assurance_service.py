"""
Domain service for data quality assurance.

Provides comprehensive validation, quality scoring, and improvement
suggestions for data sources in the MED13 Resource Library.
"""

from typing import Any, Dict, List, Tuple
import statistics
from datetime import datetime, timezone

from pydantic import BaseModel

from src.domain.entities.user_data_source import (
    UserDataSource,
    SourceConfiguration,
)
from src.domain.services.file_upload_service import DataRecord
from src.domain.services.api_source_service import APIRequestResult


class QualityScore(BaseModel):
    """Quality score breakdown."""

    overall: float
    completeness: float
    consistency: float
    timeliness: float
    validity: float

    details: Dict[str, Any] = {}


class QualityReport(BaseModel):
    """Comprehensive quality report."""

    score: QualityScore
    issues: List[str] = []
    recommendations: List[str] = []
    metrics: Dict[str, Any] = {}
    assessed_at: datetime


class QualityAssuranceService:
    """
    Domain service for data quality assessment and improvement.

    Analyzes data sources for quality metrics, identifies issues,
    and provides recommendations for improvement.
    """

    def __init__(self) -> None:
        """Initialize the quality assurance service."""
        # Quality thresholds
        self.thresholds = {
            "completeness": 0.8,  # 80% complete
            "consistency": 0.9,  # 90% consistent
            "timeliness": 0.7,  # 70% timely
            "validity": 0.95,  # 95% valid
        }

    def assess_file_upload_quality(
        self, records: List[DataRecord], configuration: SourceConfiguration
    ) -> QualityReport:
        """
        Assess quality of uploaded file data.

        Args:
            records: Parsed data records
            configuration: Source configuration

        Returns:
            Comprehensive quality report
        """
        if not records:
            return self._create_empty_report()

        # Calculate individual metrics
        completeness = self._calculate_completeness(records)
        consistency = self._calculate_consistency(records)
        validity = self._calculate_validity(records, configuration)
        timeliness = self._calculate_timeliness_file(records)

        # Calculate overall score
        overall = self._calculate_overall_score(
            completeness, consistency, validity, timeliness
        )

        # Generate issues and recommendations
        issues, recommendations = self._analyze_issues_and_recommendations(
            records, completeness, consistency, validity, timeliness
        )

        # Additional metrics
        metrics = {
            "total_records": len(records),
            "valid_records": len([r for r in records if not r.validation_errors]),
            "invalid_records": len([r for r in records if r.validation_errors]),
            "columns": self._extract_columns(records),
            "data_types": self._infer_data_types(records),
            "duplicate_count": self._count_duplicates(records),
            "null_value_stats": self._calculate_null_stats(records),
        }

        return QualityReport(
            score=QualityScore(
                overall=overall,
                completeness=completeness,
                consistency=consistency,
                timeliness=timeliness,
                validity=validity,
                details={
                    "completeness_breakdown": self._get_completeness_breakdown(records),
                    "consistency_checks": self._get_consistency_checks(records),
                    "validity_errors": self._get_validity_errors(records),
                },
            ),
            issues=issues,
            recommendations=recommendations,
            metrics=metrics,
            assessed_at=datetime.now(timezone.utc),
        )

    def assess_api_quality(
        self, result: APIRequestResult, configuration: SourceConfiguration
    ) -> QualityReport:
        """
        Assess quality of API response data.

        Args:
            result: API request result
            configuration: Source configuration

        Returns:
            Comprehensive quality report
        """
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
            completeness, consistency, validity, timeliness
        )

        issues, recommendations = self._analyze_issues_and_recommendations(
            records, completeness, consistency, validity, timeliness
        )

        # API-specific metrics
        metrics = {
            "response_time_ms": result.response_time_ms,
            "status_code": result.status_code,
            "record_count": result.record_count,
            "data_size_bytes": len(str(result.data)) if result.data else 0,
            "api_endpoint": result.metadata.get("request_url"),
        }

        if records:
            metrics.update(
                {
                    "columns": self._extract_columns(records),
                    "data_types": self._infer_data_types(records),
                    "duplicate_count": self._count_duplicates(records),
                }
            )

        return QualityReport(
            score=QualityScore(
                overall=overall,
                completeness=completeness,
                consistency=consistency,
                timeliness=timeliness,
                validity=validity,
                details={
                    "api_performance": {
                        "response_time_ms": result.response_time_ms,
                        "status_code": result.status_code,
                    }
                },
            ),
            issues=issues,
            recommendations=recommendations,
            metrics=metrics,
            assessed_at=datetime.now(timezone.utc),
        )

    def assess_source_health(self, source: UserDataSource) -> QualityReport:
        """
        Assess overall health of a data source based on its history.

        Args:
            source: The data source to assess

        Returns:
            Health assessment report
        """
        metrics = source.quality_metrics

        # Use existing metrics if available
        completeness = metrics.completeness_score or 0.0
        consistency = metrics.consistency_score or 0.0
        timeliness = self._calculate_source_timeliness(source)
        validity = metrics.overall_score or 0.0

        overall = self._calculate_overall_score(
            completeness, consistency, validity, timeliness
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

        if timeliness < 0.5:
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
            metrics={
                "last_ingested_at": (
                    source.last_ingested_at.isoformat()
                    if source.last_ingested_at
                    else None
                ),
                "status": source.status.value,
                "ingestion_count": (
                    metrics.last_assessed.isoformat() if metrics.last_assessed else None
                ),
            },
            assessed_at=datetime.now(timezone.utc),
        )

    def _calculate_completeness(self, records: List[DataRecord]) -> float:
        """Calculate data completeness score."""
        if not records:
            return 0.0

        total_fields = 0
        filled_fields = 0

        for record in records:
            for field, value in record.data.items():
                total_fields += 1
                if value is not None and str(value).strip():
                    filled_fields += 1

        return filled_fields / total_fields if total_fields > 0 else 0.0

    def _calculate_consistency(self, records: List[DataRecord]) -> float:
        """Calculate data consistency score."""
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
        self, records: List[DataRecord], configuration: SourceConfiguration
    ) -> float:
        """Calculate data validity score."""
        if not records:
            return 0.0

        total_records = len(records)
        valid_records = len([r for r in records if not r.validation_errors])

        return valid_records / total_records

    def _calculate_timeliness_file(self, records: List[DataRecord]) -> float:
        """Calculate timeliness for file data (always current)."""
        return 1.0  # File data is current when uploaded

    def _calculate_timeliness_api(self, result: APIRequestResult) -> float:
        """Calculate timeliness for API data."""
        # Based on response time - faster is better
        if result.response_time_ms < 100:
            return 1.0
        elif result.response_time_ms < 1000:
            return 0.8
        elif result.response_time_ms < 5000:
            return 0.6
        else:
            return 0.3

    def _calculate_source_timeliness(self, source: UserDataSource) -> float:
        """Calculate timeliness based on source metadata."""
        if not source.last_ingested_at:
            return 0.0

        hours_since_ingestion = (
            datetime.now(timezone.utc) - source.last_ingested_at
        ).total_seconds() / 3600

        # Freshness based on expected update frequency
        schedule = source.ingestion_schedule
        if schedule.enabled and schedule.frequency:
            if schedule.frequency == "hourly":
                expected_hours = 1
            elif schedule.frequency == "daily":
                expected_hours = 24
            elif schedule.frequency == "weekly":
                expected_hours = 168
            else:
                expected_hours = 24  # Default to daily

            if hours_since_ingestion <= expected_hours:
                return 1.0
            elif hours_since_ingestion <= expected_hours * 2:
                return 0.7
            elif hours_since_ingestion <= expected_hours * 4:
                return 0.4
            else:
                return 0.1

        return 0.5  # Unknown schedule

    def _calculate_overall_score(
        self,
        completeness: float,
        consistency: float,
        validity: float,
        timeliness: float,
    ) -> float:
        """Calculate overall quality score."""
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
        records: List[DataRecord],
        completeness: float,
        consistency: float,
        validity: float,
        timeliness: float,
    ) -> Tuple[List[str], List[str]]:
        """Analyze issues and generate recommendations."""
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
        if len(records) < 100:
            recommendations.append("Consider collecting more data samples")

        duplicates = self._count_duplicates(records)
        if duplicates > 0:
            issues.append(f"Found {duplicates} duplicate records")
            recommendations.append("Implement deduplication logic")

        return issues, recommendations

    def _extract_columns(self, records: List[DataRecord]) -> List[str]:
        """Extract column names from records."""
        columns: set[str] = set()
        for record in records:
            columns.update(record.data.keys())
        return sorted(list(columns))

    def _infer_data_types(self, records: List[DataRecord]) -> Dict[str, str]:
        """Infer data types for columns."""
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

    def _count_duplicates(self, records: List[DataRecord]) -> int:
        """Count duplicate records."""
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

    def _calculate_null_stats(self, records: List[DataRecord]) -> Dict[str, float]:
        """Calculate null value statistics per column."""
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

    def _api_data_to_records(self, data: Any) -> List[DataRecord]:
        """Convert API response data to DataRecord format."""
        records = []

        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    records.append(DataRecord(data=item, line_number=i + 1))
        elif isinstance(data, dict):
            # Look for data arrays in common API response formats
            for key in ["data", "results", "records", "items"]:
                if key in data and isinstance(data[key], list):
                    for i, item in enumerate(data[key]):
                        if isinstance(item, dict):
                            records.append(DataRecord(data=item, line_number=i + 1))
                    break
            else:
                # Single record
                records.append(DataRecord(data=data))

        return records

    def _get_completeness_breakdown(
        self, records: List[DataRecord]
    ) -> Dict[str, float]:
        """Get completeness breakdown by column."""
        return self._calculate_null_stats(records)

    def _get_consistency_checks(self, records: List[DataRecord]) -> Dict[str, Any]:
        """Get consistency check results."""
        types = self._infer_data_types(records)
        return {
            "inferred_types": types,
            "columns_with_mixed_types": [
                col for col, typ in types.items() if typ == "mixed"
            ],
        }

    def _get_validity_errors(self, records: List[DataRecord]) -> Dict[str, int]:
        """Get breakdown of validation errors."""
        error_counts: Dict[str, int] = {}
        for record in records:
            for error in record.validation_errors:
                error_counts[error] = error_counts.get(error, 0) + 1
        return error_counts

    def _create_empty_report(self) -> QualityReport:
        """Create a quality report for empty data."""
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
            metrics={},
            assessed_at=datetime.now(timezone.utc),
        )

    def _create_failure_report(self, errors: List[str]) -> QualityReport:
        """Create a quality report for failed operations."""
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
            metrics={},
            assessed_at=datetime.now(timezone.utc),
        )

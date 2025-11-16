"""Quality metrics mixin for QualityAssuranceService."""

from __future__ import annotations

import statistics
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from src.domain.entities.user_data_source import (
    ScheduleFrequency,
    SourceConfiguration,
    UserDataSource,
)
from src.domain.services.file_upload_service import DataRecord
from src.type_definitions.json_utils import to_json_value

if TYPE_CHECKING:  # pragma: no cover - typing only
    from src.domain.services.api_source_service import APIRequestResult
    from src.type_definitions.common import JSONObject, JSONValue


def _as_json_object(payload: object) -> JSONObject:
    json_payload = to_json_value(payload)
    if isinstance(json_payload, dict):
        return json_payload
    return {}


class QualityMetricsMixin:
    thresholds: dict[str, float]
    min_sample_size: int

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

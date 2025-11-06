"""
Runtime validation for external API responses.

Provides utilities to validate external API responses against expected schemas,
helping prevent runtime errors from malformed external data.
"""

import time
from typing import Any

from src.type_definitions.external_apis import (
    APIResponseValidationResult,
    ValidationIssue,
)


class APIResponseValidator:
    """
    Validator for external API responses.

    Provides runtime validation of API responses against expected schemas
    to catch data quality issues early and prevent downstream errors.
    """

    @staticmethod
    def validate_clinvar_search_response(
        data: dict[str, Any],
    ) -> APIResponseValidationResult:
        """Validate ClinVar search API response."""
        start_time = time.time()

        issues: list[ValidationIssue] = []

        # Check required top-level fields
        required_fields = ["esearchresult", "header"]
        missing = [field for field in required_fields if field not in data]
        issues.extend(
            [
                ValidationIssue(
                    field=field,
                    issue_type="missing",
                    message=f"Required field '{field}' is missing",
                    severity="error",
                )
                for field in missing
            ],
        )

        # Check esearchresult structure
        if "esearchresult" in data:
            esearchresult = data["esearchresult"]
            if not isinstance(esearchresult, dict):
                issues.append(
                    ValidationIssue(
                        field="esearchresult",
                        issue_type="invalid",
                        message="esearchresult must be an object",
                        severity="error",
                    ),
                )
            # Check for idlist
            elif "idlist" not in esearchresult:
                issues.append(
                    ValidationIssue(
                        field="esearchresult.idlist",
                        issue_type="missing",
                        message="idlist is required in esearchresult",
                        severity="error",
                    ),
                )
            elif not isinstance(esearchresult["idlist"], list):
                issues.append(
                    ValidationIssue(
                        field="esearchresult.idlist",
                        issue_type="invalid",
                        message="idlist must be an array",
                        severity="error",
                    ),
                )

        # Calculate data quality score
        error_count = sum(1 for issue in issues if issue["severity"] == "error")
        total_checks = len(required_fields) + 2  # +2 for esearchresult checks
        data_quality_score = max(0.0, 1.0 - (error_count / total_checks))

        validation_time = (time.time() - start_time) * 1000  # ms

        return APIResponseValidationResult(
            is_valid=len([i for i in issues if i["severity"] == "error"]) == 0,
            issues=issues,
            data_quality_score=data_quality_score,
            sanitized_data=(
                data if data_quality_score > APIResponseValidator.QUALITY_LOW else None
            ),
            validation_time_ms=validation_time,
        )

    @staticmethod
    def validate_clinvar_variant_response(
        data: dict[str, Any],
    ) -> APIResponseValidationResult:
        """Validate ClinVar variant details API response."""
        start_time = time.time()

        issues: list[ValidationIssue] = []

        # Check required fields
        if "result" not in data:
            issues.append(
                ValidationIssue(
                    field="result",
                    issue_type="missing",
                    message="result field is required",
                    severity="error",
                ),
            )

        if "header" not in data:
            issues.append(
                ValidationIssue(
                    field="header",
                    issue_type="missing",
                    message="header field is required",
                    severity="warning",  # Header is less critical
                ),
            )

        # Check result structure
        if "result" in data and isinstance(data["result"], dict):
            result = data["result"]
            if not result:
                issues.append(
                    ValidationIssue(
                        field="result",
                        issue_type="invalid",
                        message="result object is empty",
                        severity="warning",
                    ),
                )
        elif "result" in data:
            issues.append(
                ValidationIssue(
                    field="result",
                    issue_type="invalid",
                    message="result must be an object",
                    severity="error",
                ),
            )

        # Calculate data quality score
        error_count = sum(1 for issue in issues if issue["severity"] == "error")
        total_checks = 2  # result and header checks
        data_quality_score = max(0.0, 1.0 - (error_count / total_checks))

        validation_time = (time.time() - start_time) * 1000

        return APIResponseValidationResult(
            is_valid=len([i for i in issues if i["severity"] == "error"]) == 0,
            issues=issues,
            data_quality_score=data_quality_score,
            sanitized_data=(
                data
                if data_quality_score > APIResponseValidator.QUALITY_VERY_HIGH
                else None
            ),  # Higher threshold for variant data
            validation_time_ms=validation_time,
        )

    @staticmethod
    def validate_pubmed_search_response(
        data: dict[str, Any],
    ) -> APIResponseValidationResult:
        """Validate PubMed search API response."""
        start_time = time.time()

        issues: list[ValidationIssue] = []

        # Check required fields
        if "esearchresult" not in data:
            issues.append(
                ValidationIssue(
                    field="esearchresult",
                    issue_type="missing",
                    message="esearchresult field is required",
                    severity="error",
                ),
            )

        # Check esearchresult structure
        if "esearchresult" in data:
            esearchresult = data["esearchresult"]
            if not isinstance(esearchresult, dict):
                issues.append(
                    ValidationIssue(
                        field="esearchresult",
                        issue_type="invalid",
                        message="esearchresult must be an object",
                        severity="error",
                    ),
                )
            # Check for idlist
            elif "idlist" not in esearchresult:
                issues.append(
                    ValidationIssue(
                        field="esearchresult.idlist",
                        issue_type="missing",
                        message="idlist is required in esearchresult",
                        severity="error",
                    ),
                )

        # Calculate data quality score
        error_count = sum(1 for issue in issues if issue["severity"] == "error")
        total_checks = 3  # esearchresult, type check, idlist check
        data_quality_score = max(0.0, 1.0 - (error_count / total_checks))

        validation_time = (time.time() - start_time) * 1000

        return APIResponseValidationResult(
            is_valid=len([i for i in issues if i["severity"] == "error"]) == 0,
            issues=issues,
            data_quality_score=data_quality_score,
            sanitized_data=(
                data if data_quality_score > APIResponseValidator.QUALITY_LOW else None
            ),
            validation_time_ms=validation_time,
        )

    @staticmethod
    def validate_pubmed_article_response(
        data: dict[str, Any],
    ) -> APIResponseValidationResult:
        """Validate PubMed article details API response."""
        start_time = time.time()

        issues: list[ValidationIssue] = []

        # PubMed ESummary returns a result object with article details
        if "result" not in data:
            issues.append(
                ValidationIssue(
                    field="result",
                    issue_type="missing",
                    message="result field is required",
                    severity="error",
                ),
            )

        # Check result structure
        if "result" in data and isinstance(data["result"], dict):
            result = data["result"]
            if not result:
                issues.append(
                    ValidationIssue(
                        field="result",
                        issue_type="invalid",
                        message="result object is empty",
                        severity="warning",
                    ),
                )
            # Check for uids array
            elif "uids" not in result:
                issues.append(
                    ValidationIssue(
                        field="result.uids",
                        issue_type="missing",
                        message="uids array is required",
                        severity="warning",
                    ),
                )
        elif "result" in data:
            issues.append(
                ValidationIssue(
                    field="result",
                    issue_type="invalid",
                    message="result must be an object",
                    severity="error",
                ),
            )

        # Calculate data quality score
        error_count = sum(1 for issue in issues if issue["severity"] == "error")
        total_checks = 3  # result, type check, uids check
        data_quality_score = max(0.0, 1.0 - (error_count / total_checks))

        validation_time = (time.time() - start_time) * 1000

        return APIResponseValidationResult(
            is_valid=len([i for i in issues if i["severity"] == "error"]) == 0,
            issues=issues,
            data_quality_score=data_quality_score,
            sanitized_data=(
                data if data_quality_score > APIResponseValidator.QUALITY_HIGH else None
            ),
            validation_time_ms=validation_time,
        )

    @staticmethod
    def validate_generic_api_response(
        data: Any,
        required_fields: list[str],
        field_types: dict[str, type] | None = None,
    ) -> APIResponseValidationResult:
        """
        Generic validation for any API response.

        Args:
            data: The API response data
            required_fields: List of required field names
            field_types: Optional mapping of field names to expected types

        Returns:
            Validation result
        """
        start_time = time.time()

        issues: list[ValidationIssue] = []

        # Check data is a dict
        if not isinstance(data, dict):
            issues.append(
                ValidationIssue(
                    field="root",
                    issue_type="invalid",
                    message="Response must be an object",
                    severity="error",
                ),
            )
            return APIResponseValidationResult(
                is_valid=False,
                issues=issues,
                data_quality_score=0.0,
                sanitized_data=None,
                validation_time_ms=(time.time() - start_time) * 1000,
            )

        # Check required fields
        issues.extend(
            [
                ValidationIssue(
                    field=field,
                    issue_type="missing",
                    message=f"Required field '{field}' is missing",
                    severity="error",
                )
                for field in required_fields
                if field not in data
            ],
        )

        # Check field types if specified
        if field_types:
            issues.extend(
                [
                    ValidationIssue(
                        field=field,
                        issue_type="invalid",
                        message=(
                            f"Field '{field}' must be of type {expected_type.__name__}"
                        ),
                        severity="error",
                    )
                    for field, expected_type in field_types.items()
                    if (field in data and not isinstance(data[field], expected_type))
                ],
            )

        # Calculate data quality score
        error_count = sum(1 for issue in issues if issue["severity"] == "error")
        total_checks = len(required_fields) + (len(field_types) if field_types else 0)
        data_quality_score = max(0.0, 1.0 - (error_count / max(total_checks, 1)))

        validation_time = (time.time() - start_time) * 1000

        return APIResponseValidationResult(
            is_valid=len([i for i in issues if i["severity"] == "error"]) == 0,
            issues=issues,
            data_quality_score=data_quality_score,
            sanitized_data=(
                data
                if data_quality_score > APIResponseValidator.QUALITY_MEDIUM
                else None
            ),
            validation_time_ms=validation_time,
        )

    # Quality thresholds
    QUALITY_LOW: float = 0.5
    QUALITY_MEDIUM: float = 0.6
    QUALITY_HIGH: float = 0.7
    QUALITY_VERY_HIGH: float = 0.8

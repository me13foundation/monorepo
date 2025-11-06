"""
Domain service for file upload operations.

Handles file validation, parsing, and processing for different data formats
in the Data Sources module.
"""

import csv
import json
import logging
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from src.domain.entities.user_data_source import SourceConfiguration

# Prefer defusedxml for safe XML parsing; fall back disabled
try:  # pragma: no cover - import guard
    from defusedxml.ElementTree import fromstring as xml_fromstring

    DEFUSED_XML_AVAILABLE = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover - best-effort fallback
    xml_fromstring = None  # type: ignore[assignment]
    DEFUSED_XML_AVAILABLE = False


class FileUploadResult(BaseModel):
    """Result of a file upload operation."""

    success: bool
    file_path: str | None = None
    record_count: int = 0
    file_size: int = 0
    detected_format: str | None = None
    errors: list[str] = []
    metadata: dict[str, Any] = {}


class DataRecord(BaseModel):
    """Represents a single data record from uploaded files."""

    data: dict[str, Any]
    line_number: int | None = None
    validation_errors: list[str] = []

    @property
    def is_valid(self) -> bool:
        """Check if the record is valid."""
        return len(self.validation_errors) == 0


class FileUploadService:
    """
    Domain service for handling file uploads and processing.

    Provides validation, parsing, and processing capabilities for different
    file formats used in data source uploads.
    """

    def __init__(self, upload_dir: str = "data/uploads"):
        """
        Initialize the file upload service.

        Args:
            upload_dir: Directory for storing uploaded files
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Supported formats and their MIME types
        self.supported_formats = {
            "csv": ["text/csv", "application/csv"],
            "json": ["application/json", "text/json"],
            "xml": ["application/xml", "text/xml"],
            "tsv": ["text/tab-separated-values"],
        }
        self._logger = logging.getLogger(__name__)

    def process_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        configuration: SourceConfiguration,
        max_records: int = 10000,
    ) -> FileUploadResult:
        """
        Process an uploaded file and validate its contents.

        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            configuration: Source configuration
            max_records: Maximum number of records to process

        Returns:
            FileUploadResult with processing details
        """
        # Validate file size (100MB limit)
        file_size = len(file_content)
        if file_size > 100 * 1024 * 1024:  # 100MB
            return FileUploadResult(
                success=False,
                errors=["File too large (max 100MB)"],
                file_size=file_size,
            )

        # Detect format
        detected_format = self._detect_format(filename, file_content)
        if not detected_format:
            return FileUploadResult(
                success=False,
                errors=["Unsupported file format"],
                file_size=file_size,
            )

        # Save file temporarily (may raise OSError)
        try:
            file_path = self._save_file(file_content, filename)
        except OSError as e:
            return FileUploadResult(
                success=False,
                errors=[f"Failed to save file: {e!s}"],
                file_size=file_size,
            )

        # Parse and validate records
        records = self._parse_file(file_content, detected_format, max_records)

        # Validate records against configuration
        validation_errors = self._validate_records(records, configuration)

        # Calculate metadata
        metadata = {
            "columns": self._extract_columns(records),
            "data_types": self._infer_data_types(records),
            "sample_records": records[:5],  # First 5 records as samples
        }

        success = len(validation_errors) == 0
        all_errors = validation_errors

        if len(records) == 0:
            success = False
            all_errors.append("No valid records found in file")

        return FileUploadResult(
            success=success,
            file_path=str(file_path),
            record_count=len(records),
            file_size=file_size,
            detected_format=detected_format,
            errors=all_errors,
            metadata=metadata,
        )

    def _detect_format(self, filename: str, content: bytes) -> str | None:
        """
        Detect the file format based on filename and content.

        Args:
            filename: Original filename
            content: File content

        Returns:
            Detected format or None
        """
        # Check filename extension
        ext = Path(filename.lower()).suffix

        format_map = {
            ".csv": "csv",
            ".json": "json",
            ".xml": "xml",
            ".tsv": "tsv",
        }

        if ext in format_map:
            return format_map[ext]

        # Try to detect from content
        try:
            content_str = content.decode("utf-8").strip()
            if content_str.startswith(("{", "[")):
                return "json"
            if "<" in content_str[:100]:
                return "xml"
            if "," in content_str[:100]:
                return "csv"
        except UnicodeDecodeError:
            pass

        return None

    def _save_file(self, content: bytes, filename: str) -> Path:
        """
        Save uploaded file to temporary location.

        Args:
            content: File content
            filename: Original filename

        Returns:
            Path to saved file
        """
        # Generate unique filename
        unique_name = f"{uuid.uuid4()}_{filename}"
        file_path = self.upload_dir / unique_name

        with file_path.open("wb") as f:
            f.write(content)

        return file_path

    def _parse_file(
        self,
        content: bytes,
        format_type: str,
        max_records: int,
    ) -> list[DataRecord]:
        """
        Parse file content based on format.

        Args:
            content: File content
            format_type: File format (csv, json, xml)
            max_records: Maximum records to parse

        Returns:
            List of parsed DataRecords
        """
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            return []

        if format_type == "csv":
            return self._parse_csv(content_str, max_records)
        if format_type == "json":
            return self._parse_json(content_str, max_records)
        if format_type == "xml":
            return self._parse_xml(content_str, max_records)
        if format_type == "tsv":
            return self._parse_tsv(content_str, max_records)
        return []

    def _parse_csv(self, content: str, max_records: int) -> list[DataRecord]:
        """Parse CSV content."""
        records: list[DataRecord] = []
        try:
            lines = content.splitlines()
            if not lines:
                return records

            # Try to detect delimiter
            sample = lines[0]
            delimiter = "," if "," in sample else "\t"

            reader = csv.DictReader(lines, delimiter=delimiter)
            for i, row in enumerate(
                reader,
                start=2,
            ):  # Start at 2 because line 1 is header
                if len(records) >= max_records:
                    break
                records.append(DataRecord(data=row, line_number=i))
        except Exception as exc:
            self._logger.exception("Failed to parse CSV content", exc_info=exc)

        return records

    def _parse_json(self, content: str, max_records: int) -> list[DataRecord]:
        """Parse JSON content."""
        records: list[DataRecord] = []
        try:
            data = json.loads(content)

            if isinstance(data, list):
                for i, item in enumerate(data):
                    if len(records) >= max_records:
                        break
                    if isinstance(item, dict):
                        records.append(DataRecord(data=item, line_number=i + 1))
            elif isinstance(data, dict):
                # Single record
                records.append(DataRecord(data=data))
        except Exception as exc:
            self._logger.exception("Failed to parse JSON content", exc_info=exc)

        return records

    def _parse_xml(self, content: str, max_records: int) -> list[DataRecord]:
        """Parse XML content using defusedxml when available."""
        records: list[DataRecord] = []
        if not DEFUSED_XML_AVAILABLE or xml_fromstring is None:
            # XML parsing disabled without defusedxml for safety
            return records

        try:
            root = xml_fromstring(content)

            for i, child in enumerate(root):
                if len(records) >= max_records:
                    break

                # Convert XML element to dict
                record_data = self._xml_element_to_dict(child)
                records.append(DataRecord(data=record_data, line_number=i + 1))
        except Exception:  # noqa: BLE001
            # If XML is malformed, return what we have (empty list)
            return []

        return records

    def _parse_tsv(self, content: str, max_records: int) -> list[DataRecord]:
        """Parse TSV content."""
        # TSV is essentially CSV with tab delimiter
        return self._parse_csv(content.replace("\t", ","), max_records)

    def _xml_element_to_dict(self, element: Any) -> dict[str, Any]:
        """Convert XML element to dictionary."""
        result: dict[str, Any] = {}

        # Add attributes
        if element.attrib:
            result.update(element.attrib)

        # Add text content
        if element.text and element.text.strip():
            result["text"] = element.text.strip()

        # Add child elements
        for child in element:
            child_dict = self._xml_element_to_dict(child)
            if child.tag in result:
                # Multiple children with same tag
                existing = result[child.tag]
                if isinstance(existing, list):
                    existing.append(child_dict)
                else:
                    result[child.tag] = [existing, child_dict]
            else:
                result[child.tag] = child_dict

        return result

    def _validate_records(
        self,
        records: list[DataRecord],
        configuration: SourceConfiguration,
    ) -> list[str]:
        """
        Validate records against configuration requirements.

        Args:
            records: List of records to validate
            configuration: Source configuration

        Returns:
            List of validation error messages
        """
        errors: list[str] = []

        if not records:
            errors.append("No records to validate")
            return errors

        # Check required fields if specified
        required_fields = configuration.metadata.get("required_fields", [])
        if required_fields:
            errors.extend(self._check_required_fields(records, required_fields))

        # Validate data types if specified
        expected_types = configuration.metadata.get("expected_types", {})
        if expected_types:
            errors.extend(self._check_expected_types(records, expected_types))

        return errors

    def _check_required_fields(
        self,
        records: list[DataRecord],
        required_fields: list[str],
    ) -> list[str]:
        """Check that required fields are present in each record."""
        errors: list[str] = []
        for record in records:
            missing_fields = [
                field for field in required_fields if not record.data.get(field)
            ]
            if missing_fields:
                record.validation_errors.append(
                    f"Missing required fields: {missing_fields}",
                )
                errors.append(f"Record missing required fields: {missing_fields}")
        return errors

    def _check_expected_types(
        self,
        records: list[DataRecord],
        expected_types: dict[str, str],
    ) -> list[str]:
        """Validate expected data types for fields present in records."""
        errors: list[str] = []
        for record in records:
            for field, expected_type in expected_types.items():
                if field in record.data:
                    value = record.data[field]
                    if not self._validate_data_type(value, expected_type):
                        error = (
                            f"Field '{field}' has wrong type (expected {expected_type})"
                        )
                        record.validation_errors.append(error)
                        errors.append(error)
        return errors

    def _validate_data_type(self, value: Any, expected_type: str) -> bool:
        """Validate a value against an expected data type."""
        valid = True
        if expected_type == "string":
            valid = isinstance(value, str)
        elif expected_type == "integer":
            try:
                int(value)
                valid = True
            except (ValueError, TypeError):
                valid = False
        elif expected_type == "float":
            try:
                float(value)
                valid = True
            except (ValueError, TypeError):
                valid = False
        elif expected_type == "boolean":
            if isinstance(value, bool):
                valid = True
            elif isinstance(value, str):
                valid = value.lower() in ("true", "false", "1", "0")
            else:
                valid = False
        else:
            valid = True  # Unknown type, accept

        return valid

    def _extract_columns(self, records: list[DataRecord]) -> list[str]:
        """Extract column names from records."""
        columns: set[str] = set()
        for record in records:
            columns.update(record.data.keys())
        return sorted(columns)

    def _infer_data_types(self, records: list[DataRecord]) -> dict[str, str]:
        """Infer data types for columns."""
        if not records:
            return {}

        type_counts = {}
        columns = self._extract_columns(records)

        for column in columns:
            type_counts[column] = {"string": 0, "integer": 0, "float": 0, "boolean": 0}

            for record in records[:100]:  # Sample first 100 records
                if column in record.data:
                    value = record.data[column]
                    if isinstance(value, str):
                        if self._is_integer(value):
                            type_counts[column]["integer"] += 1
                        elif self._is_float(value):
                            type_counts[column]["float"] += 1
                        elif self._is_boolean(value):
                            type_counts[column]["boolean"] += 1
                        else:
                            type_counts[column]["string"] += 1

        # Determine most common type for each column
        inferred_types = {}
        for column, counts in type_counts.items():
            most_common = max(counts.items(), key=lambda x: x[1])
            inferred_types[column] = most_common[0]

        return inferred_types

    def _is_integer(self, value: str) -> bool:
        """Check if string represents an integer."""
        try:
            int(value)
        except (ValueError, TypeError):
            return False
        else:
            return True

    def _is_float(self, value: str) -> bool:
        """Check if string represents a float."""
        try:
            float(value)
        except (ValueError, TypeError):
            return False
        else:
            return True

    def _is_boolean(self, value: str) -> bool:
        """Check if string represents a boolean."""
        return value.lower() in ("true", "false", "1", "0", "yes", "no")

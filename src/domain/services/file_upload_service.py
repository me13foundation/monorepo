"""
Domain service for file upload operations.

Handles file validation, parsing, and processing for different data formats
in the Data Sources module.
"""

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

from pydantic import BaseModel

from src.domain.entities.user_data_source import SourceConfiguration


class FileUploadResult(BaseModel):
    """Result of a file upload operation."""

    success: bool
    file_path: Optional[str] = None
    record_count: int = 0
    file_size: int = 0
    detected_format: Optional[str] = None
    errors: List[str] = []
    metadata: Dict[str, Any] = {}


class DataRecord(BaseModel):
    """Represents a single data record from uploaded files."""

    data: Dict[str, Any]
    line_number: Optional[int] = None
    validation_errors: List[str] = []

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
        try:
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

            # Save file temporarily
            file_path = self._save_file(file_content, filename)

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

        except Exception as e:
            return FileUploadResult(
                success=False,
                errors=[f"Processing error: {str(e)}"],
                file_size=len(file_content),
            )

    def _detect_format(self, filename: str, content: bytes) -> Optional[str]:
        """
        Detect the file format based on filename and content.

        Args:
            filename: Original filename
            content: File content

        Returns:
            Detected format or None
        """
        # Check filename extension
        _, ext = os.path.splitext(filename.lower())

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
            if content_str.startswith("{") or content_str.startswith("["):
                return "json"
            elif "<" in content_str[:100]:
                return "xml"
            elif "," in content_str[:100]:
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
        import uuid

        unique_name = f"{uuid.uuid4()}_{filename}"
        file_path = self.upload_dir / unique_name

        with open(file_path, "wb") as f:
            f.write(content)

        return file_path

    def _parse_file(
        self, content: bytes, format_type: str, max_records: int
    ) -> List[DataRecord]:
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
        elif format_type == "json":
            return self._parse_json(content_str, max_records)
        elif format_type == "xml":
            return self._parse_xml(content_str, max_records)
        elif format_type == "tsv":
            return self._parse_tsv(content_str, max_records)
        else:
            return []

    def _parse_csv(self, content: str, max_records: int) -> List[DataRecord]:
        """Parse CSV content."""
        records: List[DataRecord] = []
        try:
            lines = content.splitlines()
            if not lines:
                return records

            # Try to detect delimiter
            sample = lines[0]
            delimiter = "," if "," in sample else "\t"

            reader = csv.DictReader(lines, delimiter=delimiter)
            for i, row in enumerate(
                reader, start=2
            ):  # Start at 2 because line 1 is header
                if len(records) >= max_records:
                    break
                records.append(DataRecord(data=row, line_number=i))
        except Exception:
            pass

        return records

    def _parse_json(self, content: str, max_records: int) -> List[DataRecord]:
        """Parse JSON content."""
        records: List[DataRecord] = []
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
        except Exception:
            pass

        return records

    def _parse_xml(self, content: str, max_records: int) -> List[DataRecord]:
        """Parse XML content."""
        records: List[DataRecord] = []
        try:
            root = ET.fromstring(content)

            for i, child in enumerate(root):
                if len(records) >= max_records:
                    break

                # Convert XML element to dict
                record_data = self._xml_element_to_dict(child)
                records.append(DataRecord(data=record_data, line_number=i + 1))
        except Exception:
            pass

        return records

    def _parse_tsv(self, content: str, max_records: int) -> List[DataRecord]:
        """Parse TSV content."""
        # TSV is essentially CSV with tab delimiter
        return self._parse_csv(content.replace("\t", ","), max_records)

    def _xml_element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert XML element to dictionary."""
        result: Dict[str, Any] = {}

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
        self, records: List[DataRecord], configuration: SourceConfiguration
    ) -> List[str]:
        """
        Validate records against configuration requirements.

        Args:
            records: List of records to validate
            configuration: Source configuration

        Returns:
            List of validation error messages
        """
        errors = []

        if not records:
            errors.append("No records to validate")
            return errors

        # Check required fields if specified
        required_fields = configuration.metadata.get("required_fields", [])
        if required_fields:
            for record in records:
                missing_fields = []
                for field in required_fields:
                    if field not in record.data or not record.data[field]:
                        missing_fields.append(field)
                if missing_fields:
                    record.validation_errors.extend(
                        [f"Missing required fields: {missing_fields}"]
                    )
                    errors.append(f"Record missing required fields: {missing_fields}")

        # Validate data types if specified
        expected_types = configuration.metadata.get("expected_types", {})
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
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            try:
                int(value)
                return True
            except (ValueError, TypeError):
                return False
        elif expected_type == "float":
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        elif expected_type == "boolean":
            return isinstance(value, bool) or value.lower() in (
                "true",
                "false",
                "1",
                "0",
            )
        else:
            return True  # Unknown type, accept

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
            return True
        except (ValueError, TypeError):
            return False

    def _is_float(self, value: str) -> bool:
        """Check if string represents a float."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def _is_boolean(self, value: str) -> bool:
        """Check if string represents a boolean."""
        return value.lower() in ("true", "false", "1", "0", "yes", "no")

"""
Tests for LicenseValidator with comprehensive type safety.

Tests cover all critical business logic for license validation,
including source validation, manifest parsing, and error handling.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.application.packaging.licenses.validator import LicenseValidator
from src.application.packaging.types import LicenseSourceEntry


class TestLicenseValidator:
    """Comprehensive test suite for LicenseValidator."""

    @pytest.fixture
    def compatible_source_licenses(self) -> list[LicenseSourceEntry]:
        """Create source licenses that are compatible with CC-BY-4.0."""
        return [
            {"source": "clinvar", "license": "CC-BY-4.0"},
            {"source": "pubmed", "license": "MIT"},
            {"source": "uniprot", "license": "CC0-1.0"},
            {"source": "hpo", "license": "Apache-2.0"},
        ]

    @pytest.fixture
    def incompatible_source_licenses(self) -> list[LicenseSourceEntry]:
        """Create source licenses that are incompatible with CC-BY-4.0."""
        return [
            {"source": "proprietary_data", "license": "proprietary"},
            {"source": "gpl_data", "license": "GPL-3.0"},
        ]

    @pytest.fixture
    def mixed_source_licenses(self) -> list[LicenseSourceEntry]:
        """Create a mix of compatible and incompatible licenses."""
        return [
            {"source": "clinvar", "license": "CC-BY-4.0"},  # Compatible
            {"source": "pubmed", "license": "MIT"},  # Compatible
            {"source": "proprietary", "license": "proprietary"},  # Incompatible
            {"source": "unknown", "license": "unknown"},  # Missing/unknown
        ]

    @pytest.fixture
    def minimal_source_licenses(self) -> list[LicenseSourceEntry]:
        """Create minimal source license entries."""
        return [
            {"source": "source1"},
            {"license": "MIT"},
            {"source": "source3", "license": "CC-BY-4.0"},
        ]

    class TestValidateSources:
        """Test source license validation functionality."""

        def test_validate_sources_all_compatible(
            self,
            compatible_source_licenses: list[LicenseSourceEntry],
        ) -> None:
            """Test validation when all sources have compatible licenses."""
            validator = LicenseValidator()
            result = validator.validate_sources(compatible_source_licenses)

            assert isinstance(result, dict)
            assert result["valid"] is True
            assert result["issues"] == []
            assert result["warnings"] == []

        def test_validate_sources_with_incompatible(
            self,
            incompatible_source_licenses: list[LicenseSourceEntry],
        ) -> None:
            """Test validation with incompatible licenses."""
            validator = LicenseValidator()
            result = validator.validate_sources(incompatible_source_licenses)

            assert result["valid"] is False
            assert len(result["issues"]) == 2
            assert "proprietary" in result["issues"][0].lower()
            assert "gpl-3.0" in result["issues"][1].lower()
            assert result["warnings"] == []

        def test_validate_sources_mixed_compatibility(
            self,
            mixed_source_licenses: list[LicenseSourceEntry],
        ) -> None:
            """Test validation with mixed compatible and incompatible licenses."""
            validator = LicenseValidator()
            result = validator.validate_sources(mixed_source_licenses)

            assert result["valid"] is False
            assert len(result["issues"]) == 1
            assert "proprietary" in result["issues"][0].lower()
            assert len(result["warnings"]) == 1  # Unknown license
            assert "unknown" in result["warnings"][0].lower()

        def test_validate_sources_with_missing_licenses(
            self,
            minimal_source_licenses: list[LicenseSourceEntry],
        ) -> None:
            """Test validation with missing license information."""
            validator = LicenseValidator()
            result = validator.validate_sources(minimal_source_licenses)

            assert result["valid"] is True  # Missing licenses are warnings, not errors
            assert len(result["issues"]) == 0  # No incompatible licenses
            assert (
                len(result["warnings"]) == 1
            )  # One missing license (source1), others have licenses
            assert "missing license" in result["warnings"][0].lower()
            assert "source1" in result["warnings"][0]

        def test_validate_sources_empty_list(self) -> None:
            """Test validation of empty source list."""
            validator = LicenseValidator()
            result = validator.validate_sources([])

            assert result["valid"] is True
            assert result["issues"] == []
            assert result["warnings"] == []

        def test_validate_sources_custom_package_license(
            self,
            compatible_source_licenses: list[LicenseSourceEntry],
        ) -> None:
            """Test validation with custom package license."""
            validator = LicenseValidator(package_license="MIT")
            result = validator.validate_sources(compatible_source_licenses)

            # All sources should be compatible with MIT
            assert result["valid"] is True
            assert result["issues"] == []
            assert result["warnings"] == []

        def test_validate_sources_gpl_package_license(self) -> None:
            """Test validation with GPL package license (restrictive)."""
            validator = LicenseValidator(package_license="GPL-3.0")

            # Only GPL sources should be compatible
            gpl_sources = [{"source": "gpl_code", "license": "GPL-3.0"}]
            mit_sources = [{"source": "mit_code", "license": "MIT"}]

            gpl_result = validator.validate_sources(gpl_sources)
            mit_result = validator.validate_sources(mit_sources)

            assert gpl_result["valid"] is True
            assert mit_result["valid"] is False
            assert len(mit_result["issues"]) == 1

    class TestValidateManifest:
        """Test license manifest validation functionality."""

        def test_validate_manifest_valid_file(
            self,
            compatible_source_licenses: list[LicenseSourceEntry],
            tmp_path: Path,
        ) -> None:
            """Test validation of a valid license manifest file."""
            manifest_data = {
                "package_license": "CC-BY-4.0",
                "sources": compatible_source_licenses,
            }

            manifest_path = tmp_path / "license-manifest.yml"
            with manifest_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(manifest_data, f)

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is True
            assert result["issues"] == []
            assert result["warnings"] == []

        def test_validate_manifest_incompatible_licenses(
            self,
            incompatible_source_licenses: list[LicenseSourceEntry],
            tmp_path: Path,
        ) -> None:
            """Test validation of manifest with incompatible licenses."""
            manifest_data = {
                "package_license": "CC-BY-4.0",
                "sources": incompatible_source_licenses,
            }

            manifest_path = tmp_path / "license-manifest.yml"
            with manifest_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(manifest_data, f)

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is False
            assert len(result["issues"]) == 2
            assert result["warnings"] == []

        def test_validate_manifest_missing_file(self, tmp_path: Path) -> None:
            """Test validation when manifest file doesn't exist."""
            manifest_path = tmp_path / "nonexistent.yml"

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is False
            assert len(result["issues"]) == 1
            assert "not found" in result["issues"][0].lower()

        def test_validate_manifest_invalid_yaml(self, tmp_path: Path) -> None:
            """Test validation of malformed YAML file."""
            manifest_path = tmp_path / "invalid.yml"
            with manifest_path.open("w", encoding="utf-8") as f:
                f.write("invalid: yaml: content: [\n")  # Malformed YAML

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is False
            assert len(result["issues"]) == 1
            assert "error reading manifest" in result["issues"][0].lower()

        def test_validate_manifest_invalid_structure(self, tmp_path: Path) -> None:
            """Test validation of YAML that doesn't contain a mapping."""
            manifest_path = tmp_path / "invalid-structure.yml"
            with manifest_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(["not", "a", "mapping"], f)  # List instead of dict

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is False
            assert len(result["issues"]) == 1
            assert "must be a mapping" in result["issues"][0].lower()

        def test_validate_manifest_missing_package_license(
            self,
            compatible_source_licenses: list[LicenseSourceEntry],
            tmp_path: Path,
        ) -> None:
            """Test validation when package_license is missing."""
            manifest_data = {
                "sources": compatible_source_licenses,
                # Missing package_license
            }

            manifest_path = tmp_path / "missing-license.yml"
            with manifest_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(manifest_data, f)

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is False
            assert len(result["issues"]) == 1
            assert "missing package_license" in result["issues"][0].lower()

        def test_validate_manifest_missing_sources(self, tmp_path: Path) -> None:
            """Test validation when sources field is missing."""
            manifest_data = {
                "package_license": "CC-BY-4.0",
                # Missing sources
            }

            manifest_path = tmp_path / "missing-sources.yml"
            with manifest_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(manifest_data, f)

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is False
            assert len(result["issues"]) == 1
            assert "missing sources" in result["issues"][0].lower()

        def test_validate_manifest_invalid_sources_type(self, tmp_path: Path) -> None:
            """Test validation when sources is not a list."""
            manifest_data = {
                "package_license": "CC-BY-4.0",
                "sources": "not_a_list",  # Should be list
            }

            manifest_path = tmp_path / "invalid-sources.yml"
            with manifest_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(manifest_data, f)

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is False
            assert len(result["issues"]) == 1
            assert "missing sources" in result["issues"][0].lower()

        def test_validate_manifest_non_dict_sources(self, tmp_path: Path) -> None:
            """Test validation when sources contains non-dict items."""
            manifest_data = {
                "package_license": "CC-BY-4.0",
                "sources": [
                    {"source": "valid", "license": "MIT"},
                    "invalid_string_entry",  # Should be dict
                    123,  # Should be dict
                ],
            }

            manifest_path = tmp_path / "non-dict-sources.yml"
            with manifest_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(manifest_data, f)

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is False
            assert len(result["issues"]) == 1
            assert "sources must be json objects" in result["issues"][0].lower()

        def test_validate_manifest_empty_sources(self, tmp_path: Path) -> None:
            """Test validation with empty sources list."""
            manifest_data = {
                "package_license": "CC-BY-4.0",
                "sources": [],
            }

            manifest_path = tmp_path / "empty-sources.yml"
            with manifest_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(manifest_data, f)

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is True
            assert result["issues"] == []
            assert result["warnings"] == []

        def test_validate_manifest_with_custom_package_license(
            self,
            compatible_source_licenses: list[LicenseSourceEntry],
            tmp_path: Path,
        ) -> None:
            """Test validation with custom package license in manifest."""
            manifest_data = {
                "package_license": "MIT",
                "sources": compatible_source_licenses,
            }

            manifest_path = tmp_path / "custom-license.yml"
            with manifest_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(manifest_data, f)

            validator = LicenseValidator()  # Uses default CC-BY-4.0
            result = validator.validate_manifest(manifest_path)

            # Should validate against the manifest's package license, not validator's default
            # The validator uses its own package_license, not the manifest's
            assert result["valid"] is True  # All sources compatible with CC-BY-4.0

    class TestIntegration:
        """Integration tests combining multiple validation scenarios."""

        def test_validate_sources_with_all_missing_licenses(self) -> None:
            """Test validation when all sources have missing licenses."""
            sources = [
                {"source": "source1"},
                {"source": "source2"},
                {"source": "source3"},
            ]

            validator = LicenseValidator()
            result = validator.validate_sources(sources)

            assert result["valid"] is True  # No incompatible licenses
            assert result["issues"] == []
            assert len(result["warnings"]) == 3
            for warning in result["warnings"]:
                assert "missing license" in warning.lower()

        def test_validate_sources_case_sensitive_license_matching(self) -> None:
            """Test that license matching is case-sensitive."""
            sources = [
                {
                    "source": "test",
                    "license": "cc-by-4.0",
                },  # lowercase - won't match CC-BY-4.0
                {"source": "test2", "license": "MIT"},  # correct case
            ]

            validator = LicenseValidator()
            result = validator.validate_sources(sources)

            assert result["valid"] is False  # cc-by-4.0 won't match CC-BY-4.0
            assert len(result["issues"]) == 1
            assert "cc-by-4.0" in result["issues"][0]

        def test_validate_sources_with_whitespace_in_license_names(self) -> None:
            """Test handling of whitespace in license names."""
            sources = [
                {
                    "source": "test",
                    "license": " CC-BY-4.0 ",
                },  # with whitespace - won't match
                {
                    "source": "test2",
                    "license": "  MIT  ",
                },  # with whitespace - won't match
            ]

            validator = LicenseValidator()
            result = validator.validate_sources(sources)

            assert result["valid"] is False  # Whitespace causes mismatches
            assert len(result["issues"]) == 2
            assert " CC-BY-4.0 " in result["issues"][0]
            assert "  MIT  " in result["issues"][1]

        @patch("src.application.packaging.licenses.validator.yaml.safe_load")
        def test_validate_manifest_yaml_parsing_error(
            self,
            mock_safe_load: patch,
            tmp_path: Path,
        ) -> None:
            """Test handling of YAML parsing exceptions."""
            mock_safe_load.side_effect = yaml.YAMLError("Mock parsing error")

            manifest_path = tmp_path / "error.yml"
            manifest_path.write_text("dummy content")

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is False
            assert len(result["issues"]) == 1
            assert "error reading manifest" in result["issues"][0].lower()

        @patch("yaml.safe_load")
        def test_validate_manifest_yaml_load_error(
            self,
            mock_safe_load: patch,
            tmp_path: Path,
        ) -> None:
            """Test handling of YAML parsing exceptions."""
            # Create the file so it passes the exists() check
            manifest_path = tmp_path / "error.yml"
            manifest_path.write_text("package_license: CC-BY-4.0\nsources: []")

            mock_safe_load.side_effect = yaml.YAMLError("Mock YAML error")

            validator = LicenseValidator()
            result = validator.validate_manifest(manifest_path)

            assert result["valid"] is False
            assert len(result["issues"]) == 1
            assert "error reading manifest" in result["issues"][0].lower()

    class TestEdgeCases:
        """Test edge cases and boundary conditions."""

        def test_validate_sources_missing_optional_fields(self) -> None:
            """Test handling of missing optional fields in source entries."""
            sources: list[LicenseSourceEntry] = [
                {"license": "MIT"},  # Missing source
                {"source": "test"},  # Missing license
            ]

            validator = LicenseValidator()
            result = validator.validate_sources(sources)

            assert result["valid"] is True  # None license treated as missing
            assert result["issues"] == []
            assert len(result["warnings"]) == 1  # One missing license

        def test_validate_sources_empty_strings(self) -> None:
            """Test handling of empty string values."""
            sources: list[LicenseSourceEntry] = [
                {"source": "", "license": "MIT"},
                {"source": "test", "license": ""},
            ]

            validator = LicenseValidator()
            result = validator.validate_sources(sources)

            assert result["valid"] is True  # Empty license treated as missing
            assert result["issues"] == []
            assert len(result["warnings"]) == 1  # One missing license

"""
Unit tests for license compliance checking.
"""

from src.application.packaging.licenses.manager import (
    LicenseCompatibility,
    LicenseManager,
)
from src.application.packaging.licenses.manifest import LicenseManifestGenerator
from src.application.packaging.licenses.validator import LicenseValidator


class TestLicenseManager:
    """Test license manager functionality."""

    def test_check_compatibility(self):
        """Test license compatibility checking."""
        # Same licenses
        result = LicenseManager.check_compatibility("CC-BY-4.0", "CC-BY-4.0")
        assert result == LicenseCompatibility.COMPATIBLE

        # Compatible licenses
        result = LicenseManager.check_compatibility("CC-BY-4.0", "MIT")
        assert result == LicenseCompatibility.COMPATIBLE

        # Incompatible licenses
        result = LicenseManager.check_compatibility("GPL-3.0", "CC-BY-4.0")
        assert result == LicenseCompatibility.INCOMPATIBLE

        # Missing licenses
        result = LicenseManager.check_compatibility("unknown", "CC-BY-4.0")
        assert result == LicenseCompatibility.MISSING

    def test_validate_license(self):
        """Test license validation."""
        # Valid license
        result = LicenseManager.validate_license("CC-BY-4.0")
        assert result["valid"] is True

        # Invalid license
        result = LicenseManager.validate_license("INVALID")
        assert result["valid"] is False

    def test_get_license_info(self):
        """Test getting license information."""
        info = LicenseManager.get_license_info("CC-BY-4.0")
        assert info["id"] == "CC-BY-4.0"
        assert "url" in info


class TestLicenseValidator:
    """Test license validator functionality."""

    def test_validate_sources(self):
        """Test validating source licenses."""
        validator = LicenseValidator(package_license="CC-BY-4.0")

        # Compatible sources
        sources = [
            {"source": "ClinVar", "license": "CC-BY-4.0"},
            {"source": "PubMed", "license": "MIT"},
        ]

        result = validator.validate_sources(sources)
        assert result["valid"] is True

        # Incompatible source
        sources = [
            {"source": "ClinVar", "license": "GPL-3.0"},
        ]

        result = validator.validate_sources(sources)
        assert result["valid"] is False
        assert len(result["issues"]) > 0


class TestLicenseManifestGenerator:
    """Test license manifest generator."""

    def test_generate_manifest(self):
        """Test generating license manifest."""
        sources = [
            {"source": "ClinVar", "license": "CC-BY-4.0"},
            {"source": "PubMed", "license": "MIT"},
        ]

        manifest = LicenseManifestGenerator.generate_manifest(
            package_license="CC-BY-4.0",
            source_licenses=sources,
        )

        assert manifest["package_license"] == "CC-BY-4.0"
        assert len(manifest["sources"]) == 2
        assert manifest["compliance"]["status"] == "compliant"

    def test_generate_manifest_with_incompatible(self):
        """Test generating manifest with incompatible licenses."""
        sources = [
            {"source": "SomeSource", "license": "GPL-3.0"},
        ]

        manifest = LicenseManifestGenerator.generate_manifest(
            package_license="CC-BY-4.0",
            source_licenses=sources,
        )

        assert manifest["compliance"]["status"] == "non-compliant"
        assert len(manifest["compliance"]["issues"]) > 0

    def test_generate_source_license_info(self):
        """Test generating source license information."""
        info = LicenseManifestGenerator.generate_source_license_info(
            source_name="ClinVar",
            license_id="CC-BY-4.0",
        )

        assert info["source"] == "ClinVar"
        assert info["license"] == "CC-BY-4.0"
        assert "attribution" in info

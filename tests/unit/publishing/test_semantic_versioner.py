"""
Unit tests for semantic versioning.
"""

from src.infrastructure.publishing.versioning.semantic_versioner import (
    SemanticVersioner,
    VersionType,
)


class TestSemanticVersioner:
    """Test semantic versioner functionality."""

    def test_parse_version(self):
        """Test parsing version string."""
        major, minor, patch, prerelease, build = SemanticVersioner.parse_version(
            "1.2.3",
        )
        assert major == 1
        assert minor == 2
        assert patch == 3
        assert prerelease is None
        assert build is None

    def test_parse_version_with_prerelease(self):
        """Test parsing version with prerelease."""
        major, minor, patch, prerelease, _build = SemanticVersioner.parse_version(
            "1.2.3-beta.1",
        )
        assert major == 1
        assert minor == 2
        assert patch == 3
        assert prerelease == "beta.1"

    def test_parse_version_with_build(self):
        """Test parsing version with build metadata."""
        _major, _minor, _patch, _prerelease, build = SemanticVersioner.parse_version(
            "1.2.3+build.123",
        )
        assert build == "build.123"

    def test_increment_major(self):
        """Test incrementing major version."""
        new_version = SemanticVersioner.increment_version("1.2.3", VersionType.MAJOR)
        assert new_version == "2.0.0"

    def test_increment_minor(self):
        """Test incrementing minor version."""
        new_version = SemanticVersioner.increment_version("1.2.3", VersionType.MINOR)
        assert new_version == "1.3.0"

    def test_increment_patch(self):
        """Test incrementing patch version."""
        new_version = SemanticVersioner.increment_version("1.2.3", VersionType.PATCH)
        assert new_version == "1.2.4"

    def test_validate_version(self):
        """Test version validation."""
        assert SemanticVersioner.validate_version("1.2.3") is True
        assert SemanticVersioner.validate_version("1.2.3-beta.1") is True
        assert SemanticVersioner.validate_version("invalid") is False

    def test_compare_versions(self):
        """Test version comparison."""
        assert SemanticVersioner.compare_versions("1.2.3", "1.2.4") == -1
        assert SemanticVersioner.compare_versions("1.2.3", "1.2.3") == 0
        assert SemanticVersioner.compare_versions("1.2.4", "1.2.3") == 1

    def test_get_latest_version(self):
        """Test getting latest version."""
        versions = ["1.0.0", "1.2.3", "2.0.0", "1.5.0"]
        latest = SemanticVersioner.get_latest_version(versions)
        assert latest == "2.0.0"

    def test_get_latest_version_empty(self):
        """Test getting latest version from empty list."""
        assert SemanticVersioner.get_latest_version([]) is None

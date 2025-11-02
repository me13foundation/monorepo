"""
Semantic versioning for releases.
"""

import re
from typing import Optional, Tuple
from enum import Enum


class VersionType(str, Enum):
    """Version component types."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class SemanticVersioner:
    """Manage semantic versioning for releases."""

    VERSION_PATTERN = re.compile(
        r"^(\d+)\.(\d+)\.(\d+)(?:-([\w\.-]+))?(?:\+([\w\.-]+))?$"
    )

    @staticmethod
    def parse_version(
        version: str,
    ) -> Tuple[int, int, int, Optional[str], Optional[str]]:
        """
        Parse semantic version string.

        Args:
            version: Version string (e.g., "1.2.3-beta.1+build.123")

        Returns:
            Tuple of (major, minor, patch, prerelease, build)
        """
        match = SemanticVersioner.VERSION_PATTERN.match(version)
        if not match:
            raise ValueError(f"Invalid version format: {version}")

        major, minor, patch, prerelease, build = match.groups()
        return (
            int(major),
            int(minor),
            int(patch),
            prerelease,
            build,
        )

    @staticmethod
    def increment_version(current_version: str, version_type: VersionType) -> str:
        """
        Increment version by type.

        Args:
            current_version: Current version string
            version_type: Type of version increment

        Returns:
            New version string
        """
        major, minor, patch, prerelease, build = SemanticVersioner.parse_version(
            current_version
        )

        if version_type == VersionType.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif version_type == VersionType.MINOR:
            minor += 1
            patch = 0
        elif version_type == VersionType.PATCH:
            patch += 1

        # Reset prerelease and build for new versions
        new_version = f"{major}.{minor}.{patch}"

        return new_version

    @staticmethod
    def validate_version(version: str) -> bool:
        """
        Validate version string format.

        Args:
            version: Version string

        Returns:
            True if valid, False otherwise
        """
        return bool(SemanticVersioner.VERSION_PATTERN.match(version))

    @staticmethod
    def compare_versions(version1: str, version2: str) -> int:
        """
        Compare two versions.

        Args:
            version1: First version string
            version2: Second version string

        Returns:
            -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        major1, minor1, patch1, _, _ = SemanticVersioner.parse_version(version1)
        major2, minor2, patch2, _, _ = SemanticVersioner.parse_version(version2)

        if major1 != major2:
            return 1 if major1 > major2 else -1
        if minor1 != minor2:
            return 1 if minor1 > minor2 else -1
        if patch1 != patch2:
            return 1 if patch1 > patch2 else -1

        return 0

    @staticmethod
    def get_latest_version(versions: list[str]) -> Optional[str]:
        """
        Get latest version from a list.

        Args:
            versions: List of version strings

        Returns:
            Latest version string or None
        """
        if not versions:
            return None

        sorted_versions = sorted(
            versions, key=lambda v: SemanticVersioner.parse_version(v)[:3]
        )
        return sorted_versions[-1]

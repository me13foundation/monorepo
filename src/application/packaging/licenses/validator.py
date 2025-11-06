"""
License validation utilities.
"""

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from .manager import LicenseCompatibility, LicenseManager


class LicenseValidator:
    """Validate license compliance for packages."""

    def __init__(self, package_license: str = "CC-BY-4.0"):
        """
        Initialize validator.

        Args:
            package_license: Package license identifier
        """
        self.package_license = package_license

    def validate_sources(self, source_licenses: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Validate source licenses against package license.

        Args:
            source_licenses: List of source license dictionaries

        Returns:
            Validation result dictionary
        """
        issues = []
        warnings = []

        for source_info in source_licenses:
            source_license = source_info.get("license", "unknown")
            source_name = source_info.get("source", "unknown")

            compatibility = LicenseManager.check_compatibility(
                source_license,
                self.package_license,
            )

            if compatibility == LicenseCompatibility.MISSING:
                warnings.append(f"Missing license for source: {source_name}")

            elif compatibility == LicenseCompatibility.INCOMPATIBLE:
                issues.append(
                    f"Incompatible license '{source_license}' "
                    f"from source '{source_name}'",
                )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    def validate_manifest(self, manifest_path: Path) -> dict[str, Any]:
        """
        Validate license manifest file.

        Args:
            manifest_path: Path to license manifest file

        Returns:
            Validation result dictionary
        """
        if not manifest_path.exists():
            return {
                "valid": False,
                "issues": ["License manifest file not found"],
                "warnings": [],
            }

        try:
            with manifest_path.open(encoding="utf-8") as f:
                manifest = yaml.safe_load(f)

            if "package_license" not in manifest:
                return {
                    "valid": False,
                    "issues": ["Missing package_license in manifest"],
                    "warnings": [],
                }

            if "sources" not in manifest:
                return {
                    "valid": False,
                    "issues": ["Missing sources in manifest"],
                    "warnings": [],
                }

            # Validate sources
            return self.validate_sources(manifest["sources"])

        except (OSError, ValueError, yaml.YAMLError) as exc:
            return {
                "valid": False,
                "issues": [f"Error reading manifest: {exc}"],
                "warnings": [],
            }

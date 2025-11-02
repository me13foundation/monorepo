"""
RO-Crate validator for ensuring FAIR compliance.
"""

import json
from pathlib import Path
from typing import Dict, Any


class ROCrateValidator:
    """Validate RO-Crate packages for compliance."""

    def __init__(self, crate_path: Path):
        """
        Initialize validator.

        Args:
            crate_path: Path to RO-Crate directory
        """
        self.crate_path = Path(crate_path)

    def validate_structure(self) -> Dict[str, Any]:
        """
        Validate RO-Crate directory structure.

        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []

        # Check for metadata file
        metadata_file = self.crate_path / "ro-crate-metadata.json"
        if not metadata_file.exists():
            errors.append("Missing ro-crate-metadata.json")

        # Check data directory (optional but recommended)
        data_dir = self.crate_path / "data"
        if not data_dir.exists():
            warnings.append("Data directory missing (recommended)")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def validate_metadata(self) -> Dict[str, Any]:
        """
        Validate RO-Crate metadata.json file.

        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []

        metadata_file = self.crate_path / "ro-crate-metadata.json"
        if not metadata_file.exists():
            return {
                "valid": False,
                "errors": ["ro-crate-metadata.json not found"],
                "warnings": [],
            }

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Check required top-level fields
            if "@context" not in metadata:
                errors.append("Missing @context")

            if "@graph" not in metadata:
                errors.append("Missing @graph")
            else:
                # Find root dataset
                root_dataset = None
                for entity in metadata["@graph"]:
                    if entity.get("@id") == "./":
                        root_dataset = entity
                        break

                if not root_dataset:
                    errors.append("Missing root dataset (@id: './')")
                else:
                    # Validate root dataset fields
                    if "@type" not in root_dataset:
                        errors.append("Root dataset missing @type")
                    elif root_dataset["@type"] != "Dataset":
                        errors.append(
                            f"Root dataset @type should be 'Dataset', "
                            f"got '{root_dataset['@type']}'"
                        )

                    if "name" not in root_dataset:
                        warnings.append("Root dataset missing name")

                    if "description" not in root_dataset:
                        warnings.append("Root dataset missing description")

                    if "license" not in root_dataset:
                        warnings.append("Root dataset missing license")

                    if "creator" not in root_dataset:
                        warnings.append("Root dataset missing creator")

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def validate_fair_compliance(self) -> Dict[str, Any]:
        """
        Validate FAIR principles compliance.

        Returns:
            FAIR compliance validation result
        """
        compliance = {
            "findable": {"valid": False, "issues": []},
            "accessible": {"valid": False, "issues": []},
            "interoperable": {"valid": False, "issues": []},
            "reusable": {"valid": False, "issues": []},
        }

        metadata_file = self.crate_path / "ro-crate-metadata.json"
        if not metadata_file.exists():
            return compliance

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Find root dataset
            root_dataset = None
            for entity in metadata["@graph"]:
                if entity.get("@id") == "./":
                    root_dataset = entity
                    break

            if not root_dataset:
                return compliance

            # Findable: Unique identifier, rich metadata
            if "name" in root_dataset and "description" in root_dataset:
                compliance["findable"]["valid"] = True
            else:
                compliance["findable"]["issues"].append("Missing name or description")

            # Accessible: Standard protocol, accessible metadata
            if "license" in root_dataset:
                compliance["accessible"]["valid"] = True
            else:
                compliance["accessible"]["issues"].append("Missing license")

            # Interoperable: Formal language, vocabularies
            if "@context" in metadata and "@type" in root_dataset:
                compliance["interoperable"]["valid"] = True
            else:
                compliance["interoperable"]["issues"].append(
                    "Missing context or type information"
                )

            # Reusable: Clear license, provenance
            if "license" in root_dataset:
                compliance["reusable"]["valid"] = True
            else:
                compliance["reusable"]["issues"].append("Missing license")

            if "creator" in root_dataset:
                compliance["reusable"]["valid"] = True
            else:
                compliance["reusable"]["issues"].append("Missing creator")

        except Exception as e:
            for key in compliance:
                compliance[key]["issues"].append(f"Validation error: {e}")

        return compliance

    def validate(self) -> Dict[str, Any]:
        """
        Perform complete validation.

        Returns:
            Complete validation result
        """
        structure_result = self.validate_structure()
        metadata_result = self.validate_metadata()
        fair_result = self.validate_fair_compliance()

        all_errors = structure_result["errors"] + metadata_result["errors"]
        all_warnings = structure_result["warnings"] + metadata_result["warnings"]

        return {
            "valid": len(all_errors) == 0,
            "errors": all_errors,
            "warnings": all_warnings,
            "fair_compliance": fair_result,
            "structure": structure_result,
            "metadata": metadata_result,
        }

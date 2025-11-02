"""
RO-Crate builder for MED13 Resource Library.

Creates Research Object Crates (RO-Crates) following the RO-Crate specification
for FAIR data packaging and distribution.
"""

import json
import uuid
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, List, Optional


class ROCrateBuilder:
    """
    Builder for creating RO-Crate compliant packages.

    RO-Crate is a lightweight approach to packaging research data with
    their metadata in a machine-readable way. See: https://www.researchobject.org/ro-crate/
    """

    def __init__(
        self,
        base_path: Path,
        name: str = "MED13 Resource Library Dataset",
        description: Optional[str] = None,
        version: str = "1.0.0",
        license: str = "CC-BY-4.0",
        author: Optional[str] = None,
    ):
        """
        Initialize RO-Crate builder.

        Args:
            base_path: Base directory for the RO-Crate package
            name: Dataset name
            description: Dataset description
            version: Dataset version
            license: License identifier (default: CC-BY-4.0)
            author: Author/organization name
        """
        self.base_path = Path(base_path)
        self.name = name
        self.description = description or (
            "Curated biomedical data for MED13 genetic variants, "
            "phenotypes, and supporting evidence"
        )
        self.version = version
        self.license = license
        self.author = author or "MED13 Foundation"
        self.crate_id = str(uuid.uuid4())
        self.created_at = datetime.now(UTC).isoformat()

        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_crate_structure(self) -> Dict[str, Any]:
        """
        Create RO-Crate directory structure.

        Returns:
            Dictionary with created paths
        """
        paths = {
            "data": self.base_path / "data",
            "metadata": self.base_path / "metadata",
        }

        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)

        return paths

    def add_data_file(
        self,
        source_path: Path,
        target_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        Add a data file to the RO-Crate package.

        Args:
            source_path: Path to source file
            target_name: Optional target filename (defaults to source name)
            description: Optional file description

        Returns:
            Relative path to the file in the crate
        """
        data_dir = self.base_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        target_name = target_name or source_path.name
        target_path = data_dir / target_name

        # Copy file
        import shutil

        shutil.copy2(source_path, target_path)

        return f"data/{target_name}"

    def generate_metadata(
        self,
        data_files: List[Dict[str, Any]],
        provenance_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate RO-Crate metadata.json.

        Args:
            data_files: List of data file metadata dictionaries
            provenance_info: Optional provenance information

        Returns:
            RO-Crate metadata dictionary
        """
        root_dataset_id = "./"

        # Build context with RO-Crate vocabulary
        context = {
            "@vocab": "https://schema.org/",
            "ro-crate": "https://w3id.org/ro/crate#",
        }

        # Root dataset entity
        root_dataset: Dict[str, Any] = {
            "@id": root_dataset_id,
            "@type": "Dataset",
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "license": {
                "@id": f"https://spdx.org/licenses/{self.license}.html",
                "@type": "CreativeWork",
                "name": self.license,
            },
            "creator": {
                "@type": "Organization",
                "name": self.author,
            },
            "datePublished": self.created_at,
            "keywords": [
                "MED13",
                "genetics",
                "variants",
                "phenotypes",
                "biomedical data",
                "FAIR data",
            ],
        }

        has_part: List[Dict[str, Any]] = []

        # Add provenance if available
        if provenance_info:
            for source in provenance_info.get("sources", []):
                has_part.append(
                    {
                        "@type": "DataDownload",
                        "name": source.get("name"),
                        "contentUrl": source.get("url"),
                        "datePublished": source.get("date"),
                    }
                )

        # Build file entities
        file_entities: List[Dict[str, Any]] = []
        for file_info in data_files:
            file_entity = {
                "@id": file_info["path"],
                "@type": "File",
                "name": file_info.get("name", Path(file_info["path"]).name),
            }

            if file_info.get("description"):
                file_entity["description"] = file_info["description"]

            if file_info.get("encodingFormat"):
                file_entity["encodingFormat"] = file_info["encodingFormat"]

            if file_info.get("dateCreated"):
                file_entity["dateCreated"] = file_info["dateCreated"]

            file_entities.append(file_entity)

        if file_entities:
            has_part.extend(file_entities)

        if has_part:
            root_dataset["hasPart"] = has_part

        # Build complete metadata structure
        metadata = {
            "@context": context,
            "@graph": [root_dataset] + file_entities,
        }

        return metadata

    def build(
        self,
        data_files: List[Dict[str, Any]],
        provenance_info: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Build complete RO-Crate package.

        Args:
            data_files: List of data file metadata dictionaries
            provenance_info: Optional provenance information

        Returns:
            Path to the created RO-Crate directory
        """
        # Create directory structure
        self.create_crate_structure()

        # Generate metadata
        metadata = self.generate_metadata(data_files, provenance_info)

        # Write metadata file
        metadata_path = self.base_path / "ro-crate-metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return self.base_path

    def validate(self) -> Dict[str, Any]:
        """
        Validate RO-Crate structure and metadata.

        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []

        # Check for required files
        metadata_file = self.base_path / "ro-crate-metadata.json"
        if not metadata_file.exists():
            errors.append("Missing ro-crate-metadata.json")

        # Validate metadata structure
        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                # Check required fields
                if "@context" not in metadata:
                    errors.append("Missing @context in metadata")

                if "@graph" not in metadata:
                    errors.append("Missing @graph in metadata")
                else:
                    # Check for root dataset
                    root_found = False
                    for entity in metadata["@graph"]:
                        if (
                            entity.get("@id") == "./"
                            and entity.get("@type") == "Dataset"
                        ):
                            root_found = True
                            break

                    if not root_found:
                        errors.append("Missing root dataset entity")

            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON in metadata: {e}")

        # Check data directory
        data_dir = self.base_path / "data"
        if not data_dir.exists():
            warnings.append("Data directory does not exist")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

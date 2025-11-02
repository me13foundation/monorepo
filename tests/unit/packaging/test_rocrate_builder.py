"""
Unit tests for RO-Crate builder.
"""

import json
import tempfile
from pathlib import Path

from src.application.packaging.rocrate.builder import ROCrateBuilder


class TestROCrateBuilder:
    """Test RO-Crate builder functionality."""

    def test_create_builder(self):
        """Test creating a ROCrateBuilder instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = ROCrateBuilder(
                base_path=Path(tmpdir) / "test_crate",
                name="Test Dataset",
                description="Test description",
                version="1.0.0",
            )

            assert builder.name == "Test Dataset"
            assert builder.version == "1.0.0"
            assert builder.license == "CC-BY-4.0"

    def test_create_crate_structure(self):
        """Test creating crate directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = ROCrateBuilder(base_path=Path(tmpdir) / "test_crate")
            paths = builder.create_crate_structure()

            assert paths["data"].exists()
            assert paths["metadata"].exists()

    def test_add_data_file(self):
        """Test adding a data file to the crate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = ROCrateBuilder(base_path=Path(tmpdir) / "test_crate")

            # Create a test file
            test_file = Path(tmpdir) / "test_data.json"
            test_file.write_text('{"test": "data"}')

            # Add file to crate
            relative_path = builder.add_data_file(test_file)

            assert relative_path == "data/test_data.json"
            assert (builder.base_path / relative_path).exists()

    def test_generate_metadata(self):
        """Test generating RO-Crate metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = ROCrateBuilder(
                base_path=Path(tmpdir) / "test_crate",
                name="Test Dataset",
                description="Test description",
            )

            data_files = [
                {
                    "path": "data/test.json",
                    "name": "test.json",
                    "description": "Test data file",
                }
            ]

            metadata = builder.generate_metadata(data_files)

            assert "@context" in metadata
            assert "@graph" in metadata
            assert len(metadata["@graph"]) > 0

            # Check root dataset
            root_dataset = None
            for entity in metadata["@graph"]:
                if entity.get("@id") == "./":
                    root_dataset = entity
                    break

            assert root_dataset is not None
            assert root_dataset["@type"] == "Dataset"
            assert root_dataset["name"] == "Test Dataset"

    def test_build_crate(self):
        """Test building complete RO-Crate package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = ROCrateBuilder(
                base_path=Path(tmpdir) / "test_crate",
                name="Test Dataset",
            )

            # Create test file
            test_file = Path(tmpdir) / "test_data.json"
            test_file.write_text('{"test": "data"}')

            # Add file and build
            file_path = builder.add_data_file(test_file)

            data_files = [
                {
                    "path": file_path,
                    "name": "test_data.json",
                    "description": "Test data",
                }
            ]

            crate_path = builder.build(data_files)

            # Check structure
            assert (crate_path / "ro-crate-metadata.json").exists()
            assert (crate_path / "data" / "test_data.json").exists()

            # Validate metadata
            with open(crate_path / "ro-crate-metadata.json", "r") as f:
                metadata = json.load(f)

            assert "@context" in metadata
            assert "@graph" in metadata

    def test_validate_crate(self):
        """Test validating RO-Crate structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = ROCrateBuilder(base_path=Path(tmpdir) / "test_crate")

            # Create invalid crate (no metadata)
            builder.create_crate_structure()

            result = builder.validate()
            assert result["valid"] is False
            assert len(result["errors"]) > 0

            # Create valid crate
            test_file = Path(tmpdir) / "test_data.json"
            test_file.write_text('{"test": "data"}')
            file_path = builder.add_data_file(test_file)

            data_files = [
                {
                    "path": file_path,
                    "name": "test_data.json",
                }
            ]

            builder.build(data_files)
            result = builder.validate()

            assert result["valid"] is True
            assert len(result["errors"]) == 0

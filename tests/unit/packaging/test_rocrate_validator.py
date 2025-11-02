"""
Unit tests for RO-Crate validator.
"""

import tempfile
from pathlib import Path

from src.application.packaging.rocrate.builder import ROCrateBuilder
from src.application.packaging.rocrate.validator import ROCrateValidator


class TestROCrateValidator:
    """Test RO-Crate validator functionality."""

    def test_validate_structure(self):
        """Test validating crate structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Invalid structure (no metadata)
            crate_path = Path(tmpdir) / "test_crate"
            crate_path.mkdir()

            validator = ROCrateValidator(crate_path)
            result = validator.validate_structure()

            assert result["valid"] is False
            assert len(result["errors"]) > 0

            # Valid structure
            builder = ROCrateBuilder(base_path=crate_path)
            test_file = Path(tmpdir) / "test_data.json"
            test_file.write_text('{"test": "data"}')

            file_path = builder.add_data_file(test_file)
            data_files = [{"path": file_path, "name": "test_data.json"}]
            builder.build(data_files)

            validator = ROCrateValidator(crate_path)
            result = validator.validate_structure()

            assert result["valid"] is True

    def test_validate_metadata(self):
        """Test validating metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = ROCrateBuilder(
                base_path=Path(tmpdir) / "test_crate",
                name="Test Dataset",
            )

            test_file = Path(tmpdir) / "test_data.json"
            test_file.write_text('{"test": "data"}')

            file_path = builder.add_data_file(test_file)
            data_files = [{"path": file_path, "name": "test_data.json"}]
            builder.build(data_files)

            validator = ROCrateValidator(builder.base_path)
            result = validator.validate_metadata()

            assert result["valid"] is True
            assert len(result["errors"]) == 0

    def test_validate_fair_compliance(self):
        """Test FAIR compliance validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = ROCrateBuilder(
                base_path=Path(tmpdir) / "test_crate",
                name="Test Dataset",
                description="Test description",
                license="CC-BY-4.0",
                author="Test Author",
            )

            test_file = Path(tmpdir) / "test_data.json"
            test_file.write_text('{"test": "data"}')

            file_path = builder.add_data_file(test_file)
            data_files = [{"path": file_path, "name": "test_data.json"}]
            builder.build(data_files)

            validator = ROCrateValidator(builder.base_path)
            result = validator.validate_fair_compliance()

            assert result["findable"]["valid"] is True
            assert result["accessible"]["valid"] is True
            assert result["interoperable"]["valid"] is True
            assert result["reusable"]["valid"] is True

    def test_complete_validation(self):
        """Test complete validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = ROCrateBuilder(
                base_path=Path(tmpdir) / "test_crate",
                name="Test Dataset",
                description="Test description",
            )

            test_file = Path(tmpdir) / "test_data.json"
            test_file.write_text('{"test": "data"}')

            file_path = builder.add_data_file(test_file)
            data_files = [{"path": file_path, "name": "test_data.json"}]
            builder.build(data_files)

            validator = ROCrateValidator(builder.base_path)
            result = validator.validate()

            assert result["valid"] is True
            assert "fair_compliance" in result
            assert "structure" in result
            assert "metadata" in result

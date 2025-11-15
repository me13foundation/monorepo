"""
Architectural Compliance Tests for MED13 Resource Library.

These tests validate that the codebase adheres to architectural standards
defined in:
- docs/EngineeringArchitecture.md
- docs/type_examples.md
- docs/frontend/EngenieeringArchitectureNext.md
- AGENTS.md

The tests check for:
1. Type safety violations (Any, cast usage)
2. Clean Architecture layer violations
3. Single Responsibility Principle violations
4. Monolithic code patterns
5. Import dependency violations
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


@pytest.mark.architecture
class TestArchitecturalCompliance:
    """Test suite for architectural compliance validation."""

    def test_no_any_types_in_codebase(self) -> None:
        """
        Verify that no 'Any' types are used in the codebase.

        Per AGENTS.md: "NEVER USE `Any` - this is a strict requirement"
        """
        validator_script = PROJECT_ROOT / "scripts" / "validate_architecture.py"
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(validator_script)],
            check=False,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        # Check for Any usage violations
        output = result.stdout + result.stderr
        any_violations = [
            line
            for line in output.splitlines()
            if "any_usage" in line.lower() and "error" in line.lower()
        ]

        if any_violations:
            violation_details = "\n".join(any_violations)
            pytest.fail(
                f"Found 'Any' type usage violations:\n{violation_details}\n\n"
                "Per AGENTS.md, 'Any' types are strictly forbidden. "
                "Use proper types from src/type_definitions/ instead.",
            )

    def test_no_cast_usage_in_codebase(self) -> None:
        """
        Verify that no 'cast' is used in the codebase.

        Per AGENTS.md: "we should not use ANY or cast"
        """
        validator_script = PROJECT_ROOT / "scripts" / "validate_architecture.py"
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(validator_script)],
            check=False,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        # Check for cast usage violations
        output = result.stdout + result.stderr
        cast_violations = [
            line
            for line in output.splitlines()
            if "cast_usage" in line.lower() and "error" in line.lower()
        ]

        if cast_violations:
            violation_details = "\n".join(cast_violations)
            pytest.fail(
                f"Found 'cast' usage violations:\n{violation_details}\n\n"
                "Per AGENTS.md, 'cast' usage is strictly forbidden. "
                "Use proper type guards or fix the underlying type issue.",
            )

    def test_clean_architecture_layer_separation(self) -> None:
        """
        Verify Clean Architecture layer separation.

        Per EngineeringArchitecture.md:
        - Domain layer should not import from infrastructure
        - Application layer should not import from routes
        - Infrastructure should not import from routes
        """
        validator_script = PROJECT_ROOT / "scripts" / "validate_architecture.py"
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(validator_script)],
            check=False,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        # Check for layer violation errors
        output = result.stdout + result.stderr
        layer_violations = [
            line
            for line in output.splitlines()
            if "layer_violation" in line.lower() and "error" in line.lower()
        ]

        if layer_violations:
            violation_details = "\n".join(layer_violations)
            pytest.fail(
                f"Found Clean Architecture layer violations:\n{violation_details}\n\n"
                "Per EngineeringArchitecture.md, layers must respect dependency "
                "inversion principle. Domain should not depend on infrastructure.",
            )

    def test_single_responsibility_principle(self) -> None:
        """
        Verify Single Responsibility Principle compliance.

        Checks for:
        - Files that are too large (>1000 lines)
        - Functions with high complexity
        - Classes with too many methods
        """
        validator_script = PROJECT_ROOT / "scripts" / "validate_architecture.py"
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(validator_script)],
            check=False,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        # Check for SRP violations (warnings are acceptable, errors are not)
        output = result.stdout + result.stderr
        srp_errors = [
            line
            for line in output.splitlines()
            if (
                ("file_size" in line.lower() or "complexity" in line.lower())
                and "error" in line.lower()
            )
        ]

        if srp_errors:
            violation_details = "\n".join(srp_errors)
            pytest.fail(
                f"Found Single Responsibility Principle violations:\n{violation_details}\n\n"
                "Files should be focused and not exceed size/complexity thresholds.",
            )

    def test_architectural_validation_script_runs(self) -> None:
        """
        Verify that the architectural validation script runs successfully.

        This is a meta-test to ensure the validation infrastructure works.
        """
        validator_script = PROJECT_ROOT / "scripts" / "validate_architecture.py"

        assert (
            validator_script.exists()
        ), f"Architectural validation script not found at {validator_script}"

        result = subprocess.run(  # noqa: S603
            [sys.executable, str(validator_script)],
            check=False,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,  # Should complete quickly
        )

        # Script should run without crashing
        assert result.returncode in (0, 1), (
            f"Validation script crashed with return code {result.returncode}\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    def test_no_monolithic_files(self) -> None:
        """
        Verify that no files exceed the maximum size threshold.

        Per Single Responsibility Principle, files should be focused and manageable.
        """
        validator_script = PROJECT_ROOT / "scripts" / "validate_architecture.py"
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(validator_script)],
            check=False,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        # Check for files exceeding maximum size (errors, not warnings)
        output = result.stdout + result.stderr
        oversized_files = [
            line
            for line in output.splitlines()
            if "file_size" in line.lower()
            and "error" in line.lower()
            and "exceeds maximum size" in line.lower()
        ]

        if oversized_files:
            violation_details = "\n".join(oversized_files)
            pytest.fail(
                f"Found files exceeding maximum size threshold:\n{violation_details}\n\n"
                "Large files may violate Single Responsibility Principle. "
                "Consider splitting into smaller, focused modules.",
            )


@pytest.mark.architecture
def test_architecture_validation_integration() -> None:
    """
    Integration test: Run full architectural validation.

    This test ensures the entire validation pipeline works end-to-end.
    """
    from scripts.validate_architecture import ArchitectureValidator, ValidationResult

    validator = ArchitectureValidator(PROJECT_ROOT)
    result: ValidationResult = validator.validate()

    # Validation should complete
    assert result.files_checked > 0, "No files were checked"
    assert result.total_lines > 0, "No lines were analyzed"

    # Report results (will fail if errors found)
    if not result.is_valid():
        error_summary = "\n".join(
            f"  {v.file_path}:{v.line_number} - {v.message}"
            for v in result.violations
            if v.severity == "error"
        )
        pytest.fail(
            f"Architectural validation failed with {result.error_count} errors:\n"
            f"{error_summary}\n\n"
            "See scripts/validate_architecture.py for details.",
        )

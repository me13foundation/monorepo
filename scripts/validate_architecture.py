#!/usr/bin/env python3
"""
Architectural Compliance Validator for MED13 Resource Library.

Validates codebase against architectural standards defined in:
- docs/EngineeringArchitecture.md
- docs/type_examples.md
- docs/frontend/EngenieeringArchitectureNext.md
- AGENTS.md
- architecture_overrides.json (technical debt tracking)

This script checks for:
1. Type safety violations (Any, cast usage)
2. Clean Architecture layer violations
3. Single Responsibility Principle violations
4. Monolithic code patterns
5. Import dependency violations
"""

import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from src.type_definitions.common import JSONValue

# Allowed exceptions for type checking
ALLOWED_ANY_USAGE = {
    "src/type_definitions/json_utils.py",  # Explicit override in pyproject.toml
    "src/application/packaging/licenses/manager.py",  # License compatibility checking
    "src/application/packaging/licenses/manifest.py",  # YAML parsing
}

# Clean Architecture layer definitions
LAYER_BOUNDARIES = {
    "domain": {
        "path": "src/domain",
        "forbidden_imports": [
            "src.infrastructure",
            "src.routes",
            "src.models.database",  # Domain should use entities, not DB models
        ],
        "allowed_imports": [
            "src.domain",
            "src.type_definitions",
            "typing",
            "collections.abc",
            "datetime",
            "uuid",
            "pydantic",
        ],
    },
    "application": {
        "path": "src/application",
        "forbidden_imports": [
            "src.routes",  # Application shouldn't know about routes
        ],
        "allowed_imports": [
            "src.domain",
            "src.application",
            "src.type_definitions",
            "src.infrastructure.repositories",  # Can use repository implementations
        ],
    },
    "infrastructure": {
        "path": "src/infrastructure",
        "forbidden_imports": [
            "src.routes",  # Infrastructure shouldn't know about routes
        ],
    },
}

# File size thresholds (lines of code)
# Note: Some complex infrastructure files (ingestors, transformers) may legitimately
# be larger due to their nature. However, files >1200 lines should be split.
MAX_FILE_SIZE = 1200  # Large files may violate SRP
WARNING_FILE_SIZE = 500  # Files approaching limit

# Complexity thresholds
MAX_FUNCTION_COMPLEXITY = 50  # Cyclomatic complexity
MAX_CLASS_METHODS = 30  # Methods per class
ARCHITECTURE_OVERRIDES_FILE = "architecture_overrides.json"


@dataclass
class Violation:
    """Represents an architectural violation."""

    file_path: str
    line_number: int
    violation_type: str
    message: str
    severity: str  # "error" or "warning"


@dataclass
class ValidationResult:
    """Results of architectural validation."""

    violations: list[Violation] = field(default_factory=list)
    files_checked: int = 0
    total_lines: int = 0

    @property
    def error_count(self) -> int:
        """Count of error-level violations."""
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        """Count of warning-level violations."""
        return sum(1 for v in self.violations if v.severity == "warning")

    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return self.error_count == 0


@dataclass(frozen=True)
class FileSizeOverride:
    """Represents a documented file size exception."""

    path: str
    max_lines: int
    reason: str
    expires_on: str | None = None


@dataclass(frozen=True)
class ClassSizeOverride:
    """Represents a documented class size exception."""

    path: str
    class_name: str
    max_methods: int
    reason: str
    expires_on: str | None = None


@dataclass
class ArchitectureOverrides:
    """Overrides for transitional technical debt."""

    file_size: dict[str, FileSizeOverride] = field(default_factory=dict)
    class_size: dict[tuple[str, str], ClassSizeOverride] = field(default_factory=dict)

    @classmethod
    def load(cls, root_path: Path) -> "ArchitectureOverrides":
        """Load overrides from configuration file if present."""
        overrides_path = root_path / ARCHITECTURE_OVERRIDES_FILE
        if not overrides_path.exists():
            return cls()

        try:
            raw_data: JSONValue = json.loads(overrides_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - configuration error
            error_message = f"Invalid JSON in {ARCHITECTURE_OVERRIDES_FILE}: {exc.msg}"
            raise ValueError(error_message) from exc

        if not isinstance(raw_data, dict):
            message = f"{ARCHITECTURE_OVERRIDES_FILE} must contain a JSON object at the top level."
            raise TypeError(message)

        file_overrides = cls._parse_file_size_overrides(raw_data.get("file_size"))
        class_overrides = cls._parse_class_size_overrides(raw_data.get("class_size"))

        return cls(file_overrides, class_overrides)

    @staticmethod
    def _parse_file_size_overrides(
        value: object | None,
    ) -> dict[str, FileSizeOverride]:
        overrides: dict[str, FileSizeOverride] = {}
        if not isinstance(value, list):
            return overrides

        for entry in value:
            if not isinstance(entry, dict):
                continue

            entry_dict: dict[str, object] = entry
            path_value = entry_dict.get("path")
            max_lines_value = entry_dict.get("max_lines")
            reason_value = entry_dict.get("reason")
            expires_value = entry_dict.get("expires_on")

            if (
                isinstance(path_value, str)
                and isinstance(max_lines_value, int)
                and isinstance(reason_value, str)
            ):
                expires = expires_value if isinstance(expires_value, str) else None
                overrides[path_value] = FileSizeOverride(
                    path=path_value,
                    max_lines=max_lines_value,
                    reason=reason_value,
                    expires_on=expires,
                )

        return overrides

    @staticmethod
    def _parse_class_size_overrides(
        value: object | None,
    ) -> dict[tuple[str, str], ClassSizeOverride]:
        overrides: dict[tuple[str, str], ClassSizeOverride] = {}
        if not isinstance(value, list):
            return overrides

        for entry in value:
            if not isinstance(entry, dict):
                continue

            entry_dict: dict[str, object] = entry
            path_value = entry_dict.get("path")
            class_name = entry_dict.get("class_name")
            max_methods_value = entry_dict.get("max_methods")
            reason_value = entry_dict.get("reason")
            expires_value = entry_dict.get("expires_on")

            if (
                isinstance(path_value, str)
                and isinstance(class_name, str)
                and isinstance(max_methods_value, int)
                and isinstance(reason_value, str)
            ):
                expires = expires_value if isinstance(expires_value, str) else None
                key = (path_value, class_name)
                overrides[key] = ClassSizeOverride(
                    path=path_value,
                    class_name=class_name,
                    max_methods=max_methods_value,
                    reason=reason_value,
                    expires_on=expires,
                )

        return overrides


class ArchitectureValidator:
    """Validates codebase against architectural standards."""

    def __init__(self, root_path: Path) -> None:
        """Initialize validator with root path."""
        self.root_path = root_path
        self.result = ValidationResult()
        self.overrides = ArchitectureOverrides.load(root_path)

    def validate(self) -> ValidationResult:
        """Run all validation checks."""
        python_files = self._find_python_files()
        self.result.files_checked = len(python_files)

        for file_path in python_files:
            self._validate_file(file_path)

        return self.result

    def _find_python_files(self) -> list[Path]:
        """Find all Python files in src directory."""
        python_files: list[Path] = []
        src_path = self.root_path / "src"

        if not src_path.exists():
            return python_files

        for py_file in src_path.rglob("*.py"):
            # Skip __pycache__ and test files
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue
            python_files.append(py_file)

        return python_files

    def _validate_file(self, file_path: Path) -> None:
        """Validate a single Python file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            self.result.total_lines += len(content.splitlines())

            tree = ast.parse(content, filename=str(file_path))
            relative_path = str(file_path.relative_to(self.root_path))

            # Check file size
            self._check_file_size(relative_path, content)

            # Check for type safety violations
            self._check_type_safety(tree, relative_path, content)

            # Check for layer violations
            self._check_layer_violations(tree, relative_path)

            # Check for complexity violations
            self._check_complexity(tree, relative_path)

        except SyntaxError as e:
            self.result.violations.append(
                Violation(
                    file_path=str(file_path.relative_to(self.root_path)),
                    line_number=e.lineno or 0,
                    violation_type="syntax_error",
                    message=f"Syntax error: {e.msg}",
                    severity="error",
                ),
            )
        except Exception as e:
            self.result.violations.append(
                Violation(
                    file_path=str(file_path.relative_to(self.root_path)),
                    line_number=0,
                    violation_type="validation_error",
                    message=f"Error validating file: {e}",
                    severity="warning",
                ),
            )

    def _check_file_size(self, file_path: str, content: str) -> None:
        """Check if file violates size thresholds."""
        lines = len(content.splitlines())
        if self._allows_file_size_override(file_path, lines):
            return

        if lines > MAX_FILE_SIZE:
            self.result.violations.append(
                Violation(
                    file_path=file_path,
                    line_number=0,
                    violation_type="file_size",
                    message=(
                        f"File exceeds maximum size ({lines} > {MAX_FILE_SIZE} lines). "
                        "May violate Single Responsibility Principle."
                    ),
                    severity="error",
                ),
            )
        elif lines > WARNING_FILE_SIZE:
            self.result.violations.append(
                Violation(
                    file_path=file_path,
                    line_number=0,
                    violation_type="file_size",
                    message=(
                        f"File is large ({lines} > {WARNING_FILE_SIZE} lines). "
                        "Consider splitting into smaller modules."
                    ),
                    severity="warning",
                ),
            )

    def _check_type_safety(
        self,
        tree: ast.AST,
        file_path: str,
        content: str,
    ) -> None:
        """Check for type safety violations (Any, cast)."""
        # Check for Any usage
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "typing"
                and any(alias.name == "Any" for alias in node.names)
                and file_path not in ALLOWED_ANY_USAGE
            ):
                self.result.violations.append(
                    Violation(
                        file_path=file_path,
                        line_number=node.lineno,
                        violation_type="any_usage",
                        message=(
                            "Use of 'Any' type violates type safety policy. "
                            "Use proper types from src/type_definitions/ instead."
                        ),
                        severity="error",
                    ),
                )

            # Check for cast usage
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "cast"
            ):
                self.result.violations.append(
                    Violation(
                        file_path=file_path,
                        line_number=node.lineno,
                        violation_type="cast_usage",
                        message=(
                            "Use of 'cast' violates type safety policy. "
                            "Use proper type guards or fix the underlying type issue."
                        ),
                        severity="error",
                    ),
                )

        # Check for Any in type annotations (string annotations)
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            # Check for Any in type annotations
            if "Any" in line and "from typing import" not in line:
                # Skip comments and strings
                if "#" in line or '"' in line or "'" in line:
                    continue
                # Check if it's a type annotation
                if (
                    (":" in line or "->" in line)
                    and file_path not in ALLOWED_ANY_USAGE
                    and ("Any" in line.split(":")[-1] or "Any" in line.split("->")[-1])
                ):
                    self.result.violations.append(
                        Violation(
                            file_path=file_path,
                            line_number=i,
                            violation_type="any_usage",
                            message=(
                                "Use of 'Any' in type annotation violates type safety policy."
                            ),
                            severity="error",
                        ),
                    )

    def _check_layer_violations(
        self,
        tree: ast.AST,
        file_path: str,
    ) -> None:
        """Check for Clean Architecture layer violations."""
        # Determine which layer this file belongs to
        layer = None
        for layer_name, config in LAYER_BOUNDARIES.items():
            if file_path.startswith(config["path"]):
                layer = layer_name
                break

        if not layer:
            return  # Not in a defined layer

        layer_config = LAYER_BOUNDARIES[layer]

        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                # Check for forbidden imports
                for forbidden in layer_config.get("forbidden_imports", []):
                    if node.module.startswith(forbidden.replace("src.", "")):
                        self.result.violations.append(
                            Violation(
                                file_path=file_path,
                                line_number=node.lineno,
                                violation_type="layer_violation",
                                message=(
                                    f"Layer violation: {layer} layer imports from "
                                    f"{forbidden}. This violates Clean Architecture "
                                    "dependency inversion principle."
                                ),
                                severity="error",
                            ),
                        )

    def _check_complexity(
        self,
        tree: ast.AST,
        file_path: str,
    ) -> None:
        """Check for complexity violations (SRP)."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Simple complexity check: count decision points
                complexity = self._calculate_complexity(node)
                if complexity > MAX_FUNCTION_COMPLEXITY:
                    self.result.violations.append(
                        Violation(
                            file_path=file_path,
                            line_number=node.lineno,
                            violation_type="complexity",
                            message=(
                                f"Function '{node.name}' has high complexity "
                                f"({complexity} > {MAX_FUNCTION_COMPLEXITY}). "
                                "May violate Single Responsibility Principle."
                            ),
                            severity="warning",
                        ),
                    )

            if isinstance(node, ast.ClassDef):
                # Count methods in class
                methods = [
                    n
                    for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                if len(
                    methods,
                ) > MAX_CLASS_METHODS and not self._allows_class_size_override(
                    file_path,
                    node.name,
                    len(methods),
                ):
                    self.result.violations.append(
                        Violation(
                            file_path=file_path,
                            line_number=node.lineno,
                            violation_type="class_size",
                            message=(
                                f"Class '{node.name}' has many methods "
                                f"({len(methods)} > {MAX_CLASS_METHODS}). "
                                "May violate Single Responsibility Principle."
                            ),
                            severity="warning",
                        ),
                    )

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(
                child,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.AsyncFor,
                    ast.Try,
                    ast.With,
                    ast.AsyncWith,
                ),
            ):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _allows_file_size_override(self, file_path: str, lines: int) -> bool:
        """Return True when file size is within the documented override."""
        override = self.overrides.file_size.get(file_path)
        if not override:
            return False
        return lines <= override.max_lines

    def _allows_class_size_override(
        self,
        file_path: str,
        class_name: str,
        methods: int,
    ) -> bool:
        """Return True when class size is within the documented override."""
        override = self.overrides.class_size.get((file_path, class_name))
        if not override:
            return False
        return methods <= override.max_methods


def print_results(result: ValidationResult) -> None:
    """Print validation results in a readable format."""
    print("\n" + "=" * 80)
    print("ARCHITECTURAL COMPLIANCE VALIDATION REPORT")
    print("=" * 80)
    print(f"\nFiles checked: {result.files_checked}")
    print(f"Total lines: {result.total_lines:,}")
    print(f"\nErrors: {result.error_count}")
    print(f"Warnings: {result.warning_count}")

    if result.violations:
        print("\n" + "-" * 80)
        print("VIOLATIONS")
        print("-" * 80)

        # Group by type
        by_type: dict[str, list[Violation]] = {}
        for violation in result.violations:
            by_type.setdefault(violation.violation_type, []).append(violation)

        max_violations_to_show = 10
        for violation_type, violations in sorted(by_type.items()):
            print(f"\n{violation_type.upper()} ({len(violations)} violations):")
            for v in violations[:max_violations_to_show]:
                severity_marker = "❌" if v.severity == "error" else "⚠️"
                print(
                    f"  {severity_marker} {v.file_path}:{v.line_number} - {v.message}",
                )
            if len(violations) > max_violations_to_show:
                print(f"  ... and {len(violations) - max_violations_to_show} more")

    print("\n" + "=" * 80)
    if result.is_valid():
        print("✅ VALIDATION PASSED - No architectural errors found")
    else:
        print("❌ VALIDATION FAILED - Architectural violations detected")
    print("=" * 80 + "\n")


def main() -> int:
    """Main entry point for the validator."""

    root_path = Path(__file__).parent.parent
    validator = ArchitectureValidator(root_path)
    result = validator.validate()

    print_results(result)

    return 0 if result.is_valid() else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())

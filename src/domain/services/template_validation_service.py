"""
Domain service for template validation and instantiation.

Handles validation of source templates against schemas, instantiation of
templates into concrete configurations, and quality assurance checks.
"""

from typing import Any, Dict, List, Optional
import jsonschema

from pydantic import BaseModel

from src.domain.entities.source_template import (
    SourceTemplate,
    ValidationRule,
    TemplateUIConfig,
)
from src.domain.entities.user_data_source import (
    SourceConfiguration,
    SourceType,
)


class TemplateValidationResult(BaseModel):
    """Result of template validation."""

    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []


class TemplateInstantiationResult(BaseModel):
    """Result of template instantiation."""

    success: bool
    configuration: Optional[SourceConfiguration] = None
    errors: List[str] = []
    missing_parameters: List[str] = []


class TemplateValidationService:
    """
    Domain service for template validation and instantiation.

    Provides validation of templates against JSON schemas, instantiation
    of templates with user parameters, and quality assurance checks.
    """

    def __init__(self) -> None:
        """Initialize the template validation service."""
        # Common JSON schemas for different data types
        self.schemas = self._load_common_schemas()

    def _load_common_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load common JSON schemas for validation."""
        return {
            "gene_variant": {
                "type": "object",
                "properties": {
                    "gene_symbol": {"type": "string", "minLength": 1},
                    "variant_id": {"type": "string"},
                    "chromosome": {"type": "string"},
                    "position": {"type": "integer", "minimum": 1},
                    "reference": {"type": "string"},
                    "alternate": {"type": "string"},
                    "clinical_significance": {
                        "type": "string",
                        "enum": [
                            "pathogenic",
                            "likely_pathogenic",
                            "uncertain",
                            "likely_benign",
                            "benign",
                        ],
                    },
                },
                "required": ["gene_symbol"],
            },
            "phenotype": {
                "type": "object",
                "properties": {
                    "phenotype_id": {"type": "string"},
                    "phenotype_name": {"type": "string", "minLength": 1},
                    "hpo_id": {"type": "string", "pattern": "^HP:\\d+$"},
                    "category": {"type": "string"},
                    "definition": {"type": "string"},
                },
                "required": ["phenotype_name"],
            },
            "publication": {
                "type": "object",
                "properties": {
                    "pmid": {"type": "string", "pattern": "^\\d+$"},
                    "title": {"type": "string", "minLength": 1},
                    "authors": {"type": "array", "items": {"type": "string"}},
                    "journal": {"type": "string"},
                    "year": {"type": "integer", "minimum": 1900, "maximum": 2100},
                    "doi": {"type": "string"},
                },
                "required": ["title"],
            },
        }

    def validate_template(self, template: SourceTemplate) -> TemplateValidationResult:
        """
        Validate a source template for correctness and completeness.

        Args:
            template: Template to validate

        Returns:
            Validation results with errors, warnings, and suggestions
        """
        errors = []
        warnings = []
        suggestions = []

        # Validate basic template structure
        if not template.name.strip():
            errors.append("Template name cannot be empty")

        if not template.schema_definition:
            errors.append("Schema definition is required")
        else:
            # Validate JSON schema
            schema_errors = self._validate_json_schema(template.schema_definition)
            errors.extend(schema_errors)

        # Validate source type
        if template.source_type not in [st.value for st in SourceType]:
            errors.append(f"Invalid source type: {template.source_type}")

        # Validate validation rules
        for i, rule in enumerate(template.validation_rules):
            rule_errors = self._validate_validation_rule(rule, i)
            errors.extend(rule_errors)

        # Validate UI configuration
        ui_errors = self._validate_ui_config(template.ui_config)
        errors.extend(ui_errors)

        # Generate warnings
        if not template.description.strip():
            warnings.append("Template description is recommended")

        if len(template.tags) == 0:
            warnings.append("Adding tags helps with template discovery")

        if not template.validation_rules:
            warnings.append("Consider adding validation rules for data quality")

        # Generate suggestions
        if template.source_type == "api":
            suggestions.append("Consider adding rate limiting configuration")
            suggestions.append("Add authentication method examples")

        if template.source_type == "file_upload":
            suggestions.append("Specify expected file formats and delimiters")
            suggestions.append("Add sample data examples")

        return TemplateValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def instantiate_template(
        self, template: SourceTemplate, user_parameters: Dict[str, Any]
    ) -> TemplateInstantiationResult:
        """
        Instantiate a template with user-provided parameters.

        Args:
            template: Template to instantiate
            user_parameters: User-provided parameter values

        Returns:
            Instantiation results with configuration or errors
        """
        errors = []
        missing_parameters = []

        # Check for required parameters
        required_params = self._extract_required_parameters(template)

        for param in required_params:
            if param not in user_parameters or user_parameters[param] is None:
                missing_parameters.append(param)

        if missing_parameters:
            return TemplateInstantiationResult(
                success=False, missing_parameters=missing_parameters
            )

        # Validate parameter values
        param_errors = self._validate_parameters(user_parameters, template)
        if param_errors:
            errors.extend(param_errors)

        if errors:
            return TemplateInstantiationResult(success=False, errors=errors)

        # Build configuration
        try:
            configuration = self._build_configuration(template, user_parameters)
            return TemplateInstantiationResult(
                success=True, configuration=configuration
            )
        except Exception as e:
            return TemplateInstantiationResult(
                success=False, errors=[f"Configuration build error: {str(e)}"]
            )

    def _validate_json_schema(self, schema: Dict[str, Any]) -> List[str]:
        """Validate a JSON schema for correctness."""
        errors = []

        try:
            # Basic structure validation
            if not isinstance(schema, dict):
                errors.append("Schema must be a dictionary")  # type: ignore
                return errors

            if "type" not in schema:
                errors.append("Schema must specify a 'type' field")

            # Try to compile the schema
            jsonschema.Draft7Validator.check_schema(schema)

        except jsonschema.SchemaError as e:
            errors.append(f"Invalid JSON schema: {str(e)}")
        except Exception as e:
            errors.append(f"Schema validation error: {str(e)}")

        return errors

    def _validate_validation_rule(self, rule: ValidationRule, index: int) -> List[str]:
        """Validate a single validation rule."""
        errors = []

        if not rule.field.strip():
            errors.append(f"Validation rule {index}: field cannot be empty")

        if not rule.rule_type.strip():
            errors.append(f"Validation rule {index}: rule_type cannot be empty")

        # Validate rule type is supported
        supported_types = [
            "required",
            "pattern",
            "range",
            "enum",
            "type",
            "cross_reference",
            "custom",
            "format",
        ]
        if rule.rule_type not in supported_types:
            errors.append(
                f"Validation rule {index}: unsupported rule_type '{rule.rule_type}'"
            )

        # Validate parameters based on rule type
        if rule.rule_type == "pattern" and "pattern" not in rule.parameters:
            errors.append(
                f"Validation rule {index}: pattern rules require 'pattern' parameter"
            )

        if rule.rule_type == "range":
            if "min" not in rule.parameters and "max" not in rule.parameters:
                errors.append(
                    f"Validation rule {index}: range rules require 'min' or 'max' parameter"
                )

        return errors

    def _validate_ui_config(self, ui_config: TemplateUIConfig) -> List[str]:
        """Validate UI configuration."""
        errors = []

        # Validate sections have required fields
        for section in ui_config.sections:
            if "name" not in section:
                errors.append("UI sections must have a 'name' field")

        # Validate field configurations
        for field_name, field_config in ui_config.fields.items():
            if not isinstance(field_config, dict):
                errors.append(  # type: ignore
                    f"Field '{field_name}' configuration must be a dictionary"
                )

        return errors

    def _extract_required_parameters(self, template: SourceTemplate) -> List[str]:
        """Extract required parameters from template configuration."""
        required = []

        # Check UI configuration for required fields
        for field_name, field_config in template.ui_config.fields.items():
            if field_config.get("required", False):
                required.append(field_name)

        # Check schema for required fields
        schema_required = template.schema_definition.get("required", [])
        required.extend(schema_required)

        return list(set(required))  # Remove duplicates

    def _validate_parameters(
        self, parameters: Dict[str, Any], template: SourceTemplate
    ) -> List[str]:
        """Validate parameter values against template constraints."""
        errors = []

        # Validate against schema
        try:
            jsonschema.validate(parameters, template.schema_definition)
        except jsonschema.ValidationError as e:
            errors.append(f"Parameter validation error: {str(e)}")

        # Apply custom validation rules
        for rule in template.validation_rules:
            if rule.field in parameters:
                rule_errors = self._apply_validation_rule(parameters[rule.field], rule)
                errors.extend(rule_errors)

        return errors

    def _apply_validation_rule(self, value: Any, rule: ValidationRule) -> List[str]:
        """Apply a validation rule to a parameter value."""
        errors = []

        try:
            if rule.rule_type == "required":
                if value is None or (isinstance(value, str) and not value.strip()):
                    errors.append(
                        rule.error_message or f"Field '{rule.field}' is required"
                    )

            elif rule.rule_type == "pattern":
                import re

                pattern = rule.parameters.get("pattern", "")
                if pattern and not re.match(pattern, str(value)):
                    errors.append(
                        rule.error_message
                        or f"Field '{rule.field}' does not match pattern"
                    )

            elif rule.rule_type == "range":
                min_val = rule.parameters.get("min")
                max_val = rule.parameters.get("max")

                try:
                    num_value = float(value)
                    if min_val is not None and num_value < min_val:
                        errors.append(
                            rule.error_message
                            or f"Field '{rule.field}' below minimum {min_val}"
                        )
                    if max_val is not None and num_value > max_val:
                        errors.append(
                            rule.error_message
                            or f"Field '{rule.field}' above maximum {max_val}"
                        )
                except (ValueError, TypeError):
                    errors.append(
                        f"Field '{rule.field}' must be numeric for range validation"
                    )

            elif rule.rule_type == "enum":
                allowed_values = rule.parameters.get("values", [])
                if value not in allowed_values:
                    errors.append(
                        rule.error_message
                        or f"Field '{rule.field}' must be one of: {allowed_values}"
                    )

            elif rule.rule_type == "type":
                expected_type = rule.parameters.get("type", "string")
                if not self._check_type(value, expected_type):
                    errors.append(
                        rule.error_message
                        or f"Field '{rule.field}' must be of type {expected_type}"
                    )

        except Exception as e:
            errors.append(f"Validation rule error for field '{rule.field}': {str(e)}")

        return errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value matches an expected type."""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            return isinstance(value, int)
        elif expected_type == "float":
            return isinstance(value, (int, float))
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        return True

    def _build_configuration(
        self, template: SourceTemplate, parameters: Dict[str, Any]
    ) -> SourceConfiguration:
        """Build a SourceConfiguration from template and parameters."""
        # Start with template defaults
        config_dict = {
            "url": parameters.get("url", ""),
            "file_path": parameters.get("file_path", ""),
            "format": parameters.get("format", ""),
            "requests_per_minute": parameters.get("requests_per_minute"),
            "field_mapping": parameters.get("field_mapping", {}),
            "auth_type": parameters.get("auth_type"),
            "auth_credentials": parameters.get("auth_credentials", {}),
            "metadata": parameters.get("metadata", {}),
        }

        # Add template-specific metadata
        config_dict["metadata"].update(
            {
                "template_id": str(template.id),
                "template_name": template.name,
                "validation_rules": [
                    rule.model_dump() for rule in template.validation_rules
                ],
            }
        )

        return SourceConfiguration(**config_dict)

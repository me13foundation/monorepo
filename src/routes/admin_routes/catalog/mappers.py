"""Mapping helpers for admin data catalog routes."""

from src.application.services.data_source_activation_service import (
    DataSourceAvailabilitySummary,
)
from src.domain.entities.data_discovery_session import SourceCatalogEntry
from src.domain.entities.data_source_activation import DataSourceActivation

from .schemas import (
    ActivationRuleResponse,
    CatalogEntryResponse,
    DataSourceAvailabilityResponse,
)


def catalog_entry_to_response(entry: SourceCatalogEntry) -> CatalogEntryResponse:
    """Convert a SourceCatalogEntry into API response."""
    return CatalogEntryResponse.from_entity(entry)


def activation_rule_to_response(rule: DataSourceActivation) -> ActivationRuleResponse:
    """Convert a DataSourceActivation into API response."""
    return ActivationRuleResponse.from_entity(rule)


def availability_summary_to_response(
    summary: DataSourceAvailabilitySummary,
) -> DataSourceAvailabilityResponse:
    """Convert availability summary into API response."""
    return DataSourceAvailabilityResponse(
        catalog_entry_id=summary.catalog_entry_id,
        effective_is_active=summary.effective_is_active,
        global_rule=(
            activation_rule_to_response(summary.global_rule)
            if summary.global_rule
            else None
        ),
        project_rules=[
            activation_rule_to_response(rule) for rule in summary.project_rules
        ],
    )


__all__ = [
    "activation_rule_to_response",
    "availability_summary_to_response",
    "catalog_entry_to_response",
]

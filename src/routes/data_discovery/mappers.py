"""Helper functions that convert domain entities into API schemas."""

# Import from DTOs now that they moved
from src.application.services.data_discovery_service.dtos import (
    AdvancedQueryParametersModel,
    DataDiscoverySessionResponse,
)
from src.domain.entities.data_discovery_parameters import AdvancedQueryParameters
from src.domain.entities.data_discovery_session import (
    DataDiscoverySession,
    QueryTestResult,
    SourceCatalogEntry,
)
from src.domain.entities.discovery_preset import DiscoveryPreset
from src.domain.entities.discovery_search_job import DiscoverySearchJob
from src.type_definitions.storage import StorageOperationRecord

from .schemas import (
    DiscoveryPresetResponse,
    DiscoverySearchJobResponse,
    PubMedSortOption,
    QueryTestResultResponse,
    SourceCatalogResponse,
    StorageOperationResponse,
)


def _advanced_params_to_model(
    params: AdvancedQueryParameters,
) -> AdvancedQueryParametersModel:
    return AdvancedQueryParametersModel(
        gene_symbol=params.gene_symbol,
        search_term=params.search_term,
        date_from=params.date_from.isoformat() if params.date_from else None,
        date_to=params.date_to.isoformat() if params.date_to else None,
        publication_types=params.publication_types,
        languages=params.languages,
        sort_by=params.sort_by.value if params.sort_by else PubMedSortOption.RELEVANCE,
        max_results=params.max_results,
        additional_terms=params.additional_terms,
    )


def session_to_response(session: DataDiscoverySession) -> DataDiscoverySessionResponse:
    """Convert a DataDiscoverySession entity to an API response."""
    return DataDiscoverySessionResponse(
        id=session.id,
        owner_id=session.owner_id,
        research_space_id=session.research_space_id,
        name=session.name,
        current_parameters=_advanced_params_to_model(session.current_parameters),
        selected_sources=session.selected_sources,
        tested_sources=session.tested_sources,
        total_tests_run=session.total_tests_run,
        successful_tests=session.successful_tests,
        is_active=session.is_active,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        last_activity_at=session.last_activity_at.isoformat(),
    )


def data_discovery_session_to_response(
    session: DataDiscoverySession,
) -> DataDiscoverySessionResponse:
    """Convert a DataDiscoverySession entity to an API response (Alias)."""
    return session_to_response(session)


def test_result_to_response(result: QueryTestResult) -> QueryTestResultResponse:
    """Convert a QueryTestResult entity to an API response."""
    return QueryTestResultResponse(
        id=result.id,
        catalog_entry_id=result.catalog_entry_id,
        session_id=result.session_id,
        parameters=_advanced_params_to_model(result.parameters),
        status=result.status,
        response_data=result.response_data,
        response_url=result.response_url,
        error_message=result.error_message,
        execution_time_ms=result.execution_time_ms,
        data_quality_score=result.data_quality_score,
        started_at=result.started_at.isoformat(),
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
    )


def catalog_entry_to_response(entry: SourceCatalogEntry) -> SourceCatalogResponse:
    """Convert a SourceCatalogEntry entity to an API response."""
    return SourceCatalogResponse(
        id=entry.id,
        name=entry.name,
        category=entry.category,
        subcategory=entry.subcategory,
        description=entry.description,
        source_type=entry.source_type,
        param_type=entry.param_type,
        is_active=entry.is_active,
        requires_auth=entry.requires_auth,
        usage_count=entry.usage_count,
        success_rate=entry.success_rate,
        tags=entry.tags,
        capabilities=entry.capabilities,
    )


def preset_to_response(preset: DiscoveryPreset) -> DiscoveryPresetResponse:
    """Convert a DiscoveryPreset to API response."""
    return DiscoveryPresetResponse(
        id=preset.id,
        name=preset.name,
        description=preset.description,
        provider=preset.provider,
        scope=preset.scope,
        research_space_id=preset.research_space_id,
        metadata=preset.metadata,
        parameters=_advanced_params_to_model(preset.parameters),
        created_at=preset.created_at.isoformat(),
        updated_at=preset.updated_at.isoformat(),
    )


def search_job_to_response(job: DiscoverySearchJob) -> DiscoverySearchJobResponse:
    """Convert a DiscoverySearchJob entity into API representation."""
    return DiscoverySearchJobResponse(
        id=job.id,
        owner_id=job.owner_id,
        session_id=job.session_id,
        provider=job.provider,
        status=job.status,
        query_preview=job.query_preview,
        parameters=_advanced_params_to_model(job.parameters),
        total_results=job.total_results,
        result_metadata=job.result_metadata,
        error_message=job.error_message,
        storage_key=job.storage_key,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


def storage_operation_to_response(
    operation: StorageOperationRecord,
) -> StorageOperationResponse:
    """Convert a storage operation record to the API schema model."""
    return StorageOperationResponse(
        id=operation.id,
        configuration_id=operation.configuration_id,
        key=operation.key,
        status=operation.status,
        created_at=operation.created_at.isoformat(),
        metadata=operation.metadata,
    )


__all__ = [
    "catalog_entry_to_response",
    "data_discovery_session_to_response",
    "preset_to_response",
    "search_job_to_response",
    "session_to_response",
    "storage_operation_to_response",
    "test_result_to_response",
]

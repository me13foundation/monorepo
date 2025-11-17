"""Helper functions that convert domain entities into API schemas."""

from src.domain.entities.data_discovery_session import (
    DataDiscoverySession,
    QueryTestResult,
    SourceCatalogEntry,
)

from .schemas import (
    DataDiscoverySessionResponse,
    QueryParametersModel,
    QueryTestResultResponse,
    SourceCatalogResponse,
)


def session_to_response(session: DataDiscoverySession) -> DataDiscoverySessionResponse:
    """Convert a DataDiscoverySession entity to an API response."""
    return DataDiscoverySessionResponse(
        id=session.id,
        owner_id=session.owner_id,
        research_space_id=session.research_space_id,
        name=session.name,
        current_parameters=QueryParametersModel(
            gene_symbol=session.current_parameters.gene_symbol,
            search_term=session.current_parameters.search_term,
        ),
        selected_sources=session.selected_sources,
        tested_sources=session.tested_sources,
        total_tests_run=session.total_tests_run,
        successful_tests=session.successful_tests,
        is_active=session.is_active,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        last_activity_at=session.last_activity_at.isoformat(),
    )


def test_result_to_response(result: QueryTestResult) -> QueryTestResultResponse:
    """Convert a QueryTestResult entity to an API response."""
    return QueryTestResultResponse(
        id=result.id,
        catalog_entry_id=result.catalog_entry_id,
        session_id=result.session_id,
        parameters=QueryParametersModel(
            gene_symbol=result.parameters.gene_symbol,
            search_term=result.parameters.search_term,
        ),
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
    )


__all__ = [
    "catalog_entry_to_response",
    "session_to_response",
    "test_result_to_response",
]

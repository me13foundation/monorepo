"""
Data mappers for Data Discovery entities.

These functions convert between domain entities and database models,
following the Clean Architecture pattern of separating domain logic
from infrastructure concerns.
"""

from src.domain.entities.data_discovery_session import (
    DataDiscoverySession,
    QueryParameters,
    QueryParameterType,
    QueryTestResult,
    SourceCatalogEntry,
    TestResultStatus,
)
from src.models.database.data_discovery import (
    DataDiscoverySessionModel,
    QueryTestResultModel,
    SourceCatalogEntryModel,
)


def session_to_model(entity: DataDiscoverySession) -> DataDiscoverySessionModel:
    """
    Convert a DataDiscoverySession entity to a database model.

    Args:
        entity: The domain entity to convert

    Returns:
        The corresponding database model
    """
    return DataDiscoverySessionModel(
        id=entity.id,
        owner_id=entity.owner_id,
        research_space_id=entity.research_space_id,
        name=entity.name,
        gene_symbol=entity.current_parameters.gene_symbol,
        search_term=entity.current_parameters.search_term,
        selected_sources=entity.selected_sources,
        tested_sources=entity.tested_sources,
        total_tests_run=entity.total_tests_run,
        successful_tests=entity.successful_tests,
        is_active=entity.is_active,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        last_activity_at=entity.last_activity_at,
    )


def session_to_entity(model: DataDiscoverySessionModel) -> DataDiscoverySession:
    """
    Convert a DataDiscoverySessionModel to a domain entity.

    Args:
        model: The database model to convert

    Returns:
        The corresponding domain entity
    """
    parameters = QueryParameters(
        gene_symbol=model.gene_symbol,
        search_term=model.search_term,
    )

    return DataDiscoverySession(
        id=model.id,
        owner_id=model.owner_id,
        research_space_id=model.research_space_id,
        name=model.name,
        current_parameters=parameters,
        selected_sources=model.selected_sources or [],
        tested_sources=model.tested_sources or [],
        total_tests_run=model.total_tests_run,
        successful_tests=model.successful_tests,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
        last_activity_at=model.last_activity_at,
    )


def source_catalog_to_model(entity: SourceCatalogEntry) -> SourceCatalogEntryModel:
    """
    Convert a SourceCatalogEntry entity to a database model.

    Args:
        entity: The domain entity to convert

    Returns:
        The corresponding database model
    """
    return SourceCatalogEntryModel(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        category=entity.category,
        subcategory=entity.subcategory,
        tags=entity.tags,
        param_type=entity.param_type.value,  # Convert enum to string
        url_template=entity.url_template,
        data_format=entity.data_format,
        api_endpoint=entity.api_endpoint,
        is_active=entity.is_active,
        requires_auth=entity.requires_auth,
        usage_count=entity.usage_count,
        success_rate=entity.success_rate,
        source_template_id=entity.source_template_id,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def source_catalog_to_entity(model: SourceCatalogEntryModel) -> SourceCatalogEntry:
    """
    Convert a SourceCatalogEntryModel to a domain entity.

    Args:
        model: The database model to convert

    Returns:
        The corresponding domain entity
    """
    return SourceCatalogEntry(
        id=model.id,
        name=model.name,
        description=model.description,
        category=model.category,
        subcategory=model.subcategory,
        tags=model.tags or [],
        param_type=QueryParameterType(model.param_type),
        url_template=model.url_template,
        data_format=model.data_format,
        api_endpoint=model.api_endpoint,
        is_active=model.is_active,
        requires_auth=model.requires_auth,
        usage_count=model.usage_count,
        success_rate=model.success_rate,
        source_template_id=model.source_template_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def query_result_to_model(entity: QueryTestResult) -> QueryTestResultModel:
    """
    Convert a QueryTestResult entity to a database model.

    Args:
        entity: The domain entity to convert

    Returns:
        The corresponding database model
    """
    return QueryTestResultModel(
        id=entity.id,
        session_id=entity.session_id,
        catalog_entry_id=entity.catalog_entry_id,
        status=entity.status.value,  # Convert enum to string
        gene_symbol=entity.parameters.gene_symbol,
        search_term=entity.parameters.search_term,
        response_data=entity.response_data,
        response_url=entity.response_url,
        error_message=entity.error_message,
        execution_time_ms=entity.execution_time_ms,
        data_quality_score=entity.data_quality_score,
        started_at=entity.started_at,
        completed_at=entity.completed_at,
    )


def query_result_to_entity(model: QueryTestResultModel) -> QueryTestResult:
    """
    Convert a QueryTestResultModel to a domain entity.

    Args:
        model: The database model to convert

    Returns:
        The corresponding domain entity
    """
    parameters = QueryParameters(
        gene_symbol=model.gene_symbol,
        search_term=model.search_term,
    )

    return QueryTestResult(
        id=model.id,
        session_id=model.session_id,
        catalog_entry_id=model.catalog_entry_id,
        parameters=parameters,
        status=TestResultStatus(model.status),
        response_data=model.response_data,
        response_url=model.response_url,
        error_message=model.error_message,
        execution_time_ms=model.execution_time_ms,
        data_quality_score=model.data_quality_score,
        started_at=model.started_at,
        completed_at=model.completed_at,
    )

"""Helper functions to convert domain entities into API responses."""

from src.domain.entities.user_data_source import UserDataSource

from .schemas import DataSourceResponse


def data_source_to_response(data_source: UserDataSource) -> DataSourceResponse:
    """Convert a UserDataSource entity into its response model."""
    return DataSourceResponse.model_validate(data_source)


__all__ = ["data_source_to_response"]

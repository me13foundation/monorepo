"""
Base context for AI agent pipelines.

Provides a typed context that extends Flujo's PipelineContext with
MED13-specific fields for auditability and traceability.
"""

from flujo.domain.models import PipelineContext
from pydantic import Field


class BaseAgentContext(PipelineContext):
    """
    Base context for all MED13 AI agent pipelines.

    Extends PipelineContext with fields required for:
    - User attribution (audit trail)
    - Source tracking
    - Request metadata
    """

    user_id: str | None = Field(
        default=None,
        description="ID of the user who initiated the agent request",
    )
    request_source: str = Field(
        default="api",
        description="Source of the request (api, ui, background, etc.)",
    )
    correlation_id: str | None = Field(
        default=None,
        description="Correlation ID for distributed tracing",
    )

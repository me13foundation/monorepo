"""
Bulk Export API routes for MED13 Resource Library.

Provides streaming data export capabilities in multiple formats.
"""

import gzip
from typing import Any, Dict, Generator, Optional, Union, TYPE_CHECKING
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

from src.database.session import get_session
from src.infrastructure.dependency_injection import DependencyContainer
from src.application.export.export_service import ExportFormat, CompressionFormat

if TYPE_CHECKING:
    from src.application.export.export_service import BulkExportService

router = APIRouter(prefix="/export", tags=["export"])


def get_export_service(db: Session = Depends(get_session)) -> "BulkExportService":
    """Dependency injection for bulk export service."""
    container = DependencyContainer(db)
    return container.create_bulk_export_service()


@router.get("/{entity_type}")
async def export_entity_data(
    entity_type: str,
    format: ExportFormat = Query(ExportFormat.JSON, description="Export format"),
    compression: CompressionFormat = Query(
        CompressionFormat.NONE, description="Compression format"
    ),
    limit: Optional[int] = Query(
        None, ge=1, le=100000, description="Maximum number of records to export"
    ),
    service: "BulkExportService" = Depends(get_export_service),
) -> StreamingResponse:
    """
    Export data for a specific entity type in the requested format.

    Supports streaming for large datasets to avoid memory issues.
    """
    # Validate entity type
    valid_entity_types = ["genes", "variants", "phenotypes", "evidence"]
    if entity_type not in valid_entity_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity type. Supported types: {', '.join(valid_entity_types)}",
        )

    try:
        # Set up filename and content type based on format and compression
        filename = f"{entity_type}.{format.value}"
        if compression == CompressionFormat.GZIP:
            filename += ".gz"
            media_type = "application/gzip"
        elif format == ExportFormat.JSON:
            media_type = "application/json"
        elif format in (ExportFormat.CSV, ExportFormat.TSV):
            media_type = "text/csv"
        elif format == ExportFormat.JSONL:
            media_type = "application/x-ndjson"
        else:
            media_type = "application/octet-stream"

        # Create streaming response
        def generate() -> Generator[Union[str, bytes], None, None]:
            try:
                for chunk in service.export_data(
                    entity_type=entity_type,
                    export_format=format,
                    compression=compression,
                    filters={"limit": limit} if limit else None,
                ):
                    yield chunk
            except Exception as e:
                # Log the error and yield an error message
                error_msg = f"Error during export: {str(e)}"
                if compression == CompressionFormat.GZIP:
                    yield gzip.compress(error_msg.encode("utf-8"))
                else:
                    yield error_msg

        return StreamingResponse(
            generate(),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Entity-Type": entity_type,
                "X-Export-Format": format.value,
                "X-Compression": compression.value,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/{entity_type}/info")
async def get_export_info(
    entity_type: str,
    service: "BulkExportService" = Depends(get_export_service),
) -> Dict[str, Any]:
    """
    Get information about export options and data statistics for an entity type.
    """
    valid_entity_types = ["genes", "variants", "phenotypes", "evidence"]
    if entity_type not in valid_entity_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity type. Supported types: {', '.join(valid_entity_types)}",
        )

    try:
        info = service.get_export_info(entity_type)
        return {
            "entity_type": entity_type,
            "export_formats": [fmt.value for fmt in ExportFormat],
            "compression_formats": [comp.value for comp in CompressionFormat],
            "info": info,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get export info: {str(e)}"
        )


@router.get("/")
async def list_exportable_entities() -> Dict[str, Any]:
    """
    List all entity types that can be exported.
    """
    return {
        "exportable_entities": [
            {
                "type": "genes",
                "description": "Genetic entity data including symbols, names, and genomic locations",
            },
            {
                "type": "variants",
                "description": "Genetic variant data including ClinVar IDs, positions, and clinical significance",
            },
            {
                "type": "phenotypes",
                "description": "HPO phenotype data including terms, definitions, and categories",
            },
            {
                "type": "evidence",
                "description": "Evidence linking variants to phenotypes with confidence scores",
            },
        ],
        "supported_formats": [fmt.value for fmt in ExportFormat],
        "supported_compression": [comp.value for comp in CompressionFormat],
        "usage": {
            "endpoint": "GET /export/{entity_type}?format=json&compression=gzip",
            "description": "Download entity data in specified format with optional compression",
        },
    }

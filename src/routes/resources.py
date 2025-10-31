from collections.abc import Sequence

from fastapi import APIRouter

from src.models.resource import Resource
from src.services.resources import list_resources

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/", summary="List curated resources")
async def get_resources() -> Sequence[Resource]:
    """Return curated resources using the service layer."""
    return list_resources()

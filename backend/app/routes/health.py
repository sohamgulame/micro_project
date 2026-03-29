from fastapi import APIRouter

from app.models.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
def get_health() -> HealthResponse:
    return HealthService.get_system_health()

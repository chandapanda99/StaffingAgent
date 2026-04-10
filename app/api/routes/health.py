from app.api.dependencies import get_health_service
from app.domain.schemas import HealthResponse, ReadinessResponse
from app.services.health import HealthService
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
def readiness(service: HealthService = Depends(get_health_service)) -> ReadinessResponse:
    return service.readiness()

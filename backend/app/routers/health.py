from fastapi import APIRouter, Response, status
from app.config import settings
from app.db import check_db_health
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check verifying API and Database status"
)
async def get_health(response: Response):
    """
    Checks API process state and database connectivity without exposing secrets.
    """
    db_result = check_db_health()
    db_connected = db_result.get("connected", False)

    if db_connected:
        response.status_code = status.HTTP_200_OK
        return HealthResponse(
            status="healthy",
            api="running",
            database="connected",
            environment=settings.ENVIRONMENT
        )
    else:
        # Service is degraded if database is not reachable
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="degraded",
            api="running",
            database="unreachable",
            environment=settings.ENVIRONMENT
        )

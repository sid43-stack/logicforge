from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.diagnostic import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def check_health():
    """Health check endpoint for verifying service availability."""
    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        timestamp=datetime.now(timezone.utc)
    )

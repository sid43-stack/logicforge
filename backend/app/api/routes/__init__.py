"""NetSage API Router Aggregator."""

from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.diagnostics import router as diagnostics_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.history import router as history_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(diagnostics_router)
api_router.include_router(knowledge_router)
api_router.include_router(history_router)

__all__ = ["api_router"]

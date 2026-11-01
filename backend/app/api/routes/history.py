"""NetSage Diagnostic History REST API Endpoints.

Provides historical session audits, pagination, session inspection, and deletion.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.history_service import HistoryService
from app.schemas.history import SessionListResponse, SessionDetailResponse

router = APIRouter(prefix="/history", tags=["history"])
history_service = HistoryService()


@router.get("", response_model=SessionListResponse)
def list_diagnostic_sessions(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Page size limit"),
    status: Optional[str] = Query(None, description="Filter by status (IN_PROGRESS, COMPLETED, INCONCLUSIVE, CONFLICT_DETECTED)"),
    db: Session = Depends(get_db),
):
    """Returns a paginated list of historical network diagnostic sessions."""
    return history_service.list_sessions(db=db, skip=skip, limit=limit, status=status)


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_diagnostic_session_detail(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Returns complete audit details for a specific session, including all answered questions and final outcome."""
    return history_service.get_session_detail(db=db, session_id=session_id)


@router.delete("/{session_id}")
def delete_diagnostic_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Deletes a historical session along with all cascaded questions, traces, and recommendations."""
    return history_service.delete_session(db=db, session_id=session_id)


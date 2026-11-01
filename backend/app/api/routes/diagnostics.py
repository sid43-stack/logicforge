"""NetSage Diagnostics REST API Endpoints.

Provides endpoints for diagnostic session lifecycle management, dynamic inquiry,
evidence submission, result retrieval, and explanation generation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.diagnostic_service import DiagnosticService
from app.schemas.diagnostic import (
    DiagnosticSessionCreate,
    StartSessionResponse,
    AnswerRequest,
    AnswerResponse,
    QuestionWithWhyResponse,
    DiagnosticResultResponse,
    ExplanationResponse,
)

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])
diagnostic_service = DiagnosticService()


@router.post("/start", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
def start_diagnostic_session(
    payload: Optional[DiagnosticSessionCreate] = None,
    db: Session = Depends(get_db),
):
    """Starts a new network diagnostic session, initializes working memory, and returns the first question."""
    initial_facts = payload.initial_facts if payload else None
    return diagnostic_service.start_session(db=db, initial_facts=initial_facts)


@router.post("/{session_id}/answer", response_model=AnswerResponse)
def submit_diagnostic_answer(
    session_id: str,
    payload: AnswerRequest,
    db: Session = Depends(get_db),
):
    """Accepts an answer to an active question, performs forward and backward chaining, and transitions session."""
    return diagnostic_service.submit_answer(
        db=db,
        session_id=session_id,
        question_id=payload.question_id,
        answer_str=payload.answer,
    )


@router.get("/{session_id}/question", response_model=QuestionWithWhyResponse)
def get_current_question(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves the current pending question with its dynamic WHY explanation for an active session."""
    return diagnostic_service.get_current_question(db=db, session_id=session_id)


@router.get("/{session_id}/result", response_model=DiagnosticResultResponse)
def get_diagnostic_result(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves the final confirmed diagnosis and actionable remediation plan."""
    return diagnostic_service.get_result(db=db, session_id=session_id)


@router.get("/{session_id}/explanation", response_model=ExplanationResponse)
def get_diagnostic_explanation(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves comprehensive HOW explanation including chronological audit narrative and DAG graph."""
    return diagnostic_service.get_explanation(db=db, session_id=session_id)


@router.post("/{session_id}/restart", response_model=StartSessionResponse)
def restart_diagnostic_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Resets an existing diagnostic session to scratch, clearing past answers and deductions."""
    return diagnostic_service.restart_session(db=db, session_id=session_id)


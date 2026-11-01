"""NetSage History Service.

Manages audit logging, historical session pagination, detailed session reviews,
and session deletion with cascading record cleanup.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.diagnostic import DiagnosticSession
from app.core.exceptions import NetSageNotFoundException
from app.schemas.history import (
    SessionListResponse,
    SessionSummaryResponse,
    SessionDetailResponse,
    DiagnosticAnswerSummary,
)
from app.schemas.diagnostic import DiagnosticResultResponse, DiagnosticStepResponse
from app.expert_system.recommendation_engine import RecommendationEngine


class HistoryService:
    """Provides queries and mutations for historical diagnostic sessions."""

    def __init__(self, recommendation_engine: Optional[RecommendationEngine] = None):
        self.recommendation_engine = recommendation_engine or RecommendationEngine()

    def list_sessions(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> SessionListResponse:
        """Retrieves a paginated list of diagnostic sessions."""
        query = db.query(DiagnosticSession)
        if status:
            query = query.filter(DiagnosticSession.status == status.upper())

        total = query.count()
        sessions = (
            query.order_by(desc(DiagnosticSession.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        items = [
            SessionSummaryResponse(
                id=s.id,
                created_at=s.created_at,
                completed_at=s.completed_at,
                status=s.status,
                final_diagnosis=s.final_diagnosis,
                diagnosis_category=s.diagnosis_category,
                severity=s.severity,
                answers_count=len(s.answers),
            )
            for s in sessions
        ]

        return SessionListResponse(total=total, items=items)

    def get_session_detail(self, db: Session, session_id: str) -> SessionDetailResponse:
        """Retrieves full historical details for a single diagnostic session."""
        session = db.query(DiagnosticSession).filter(DiagnosticSession.id == session_id).first()
        if not session:
            raise NetSageNotFoundException(f"Diagnostic session '{session_id}' not found.")

        answers_summary = [
            DiagnosticAnswerSummary(
                id=a.id,
                question_id=a.question_id,
                question_text=a.question_text,
                answer=a.answer,
                answered_at=a.answered_at,
            )
            for a in session.answers
        ]

        # Build recommendation result if session completed or inconclusive
        rec_response: Optional[DiagnosticResultResponse] = None
        if session.status in ("COMPLETED", "INCONCLUSIVE"):
            plan = None
            if session.recommendation_code:
                plan = self.recommendation_engine.get_recommendation_by_code(session.recommendation_code)
            if not plan and session.final_diagnosis:
                plan = self.recommendation_engine.get_recommendation_by_diagnosis(session.final_diagnosis)
            if not plan and session.status == "INCONCLUSIVE":
                plan = self.recommendation_engine.get_inconclusive_plan()

            steps_resp = []
            warnings = []
            escalation = None
            if plan:
                warnings = list(plan.warnings)
                escalation = plan.escalation_advice
                for st in plan.steps:
                    steps_resp.append(
                        DiagnosticStepResponse(
                            order=st.order,
                            action=st.action,
                            command=st.command,
                            description=st.description,
                            expected_outcome=st.expected_outcome,
                            is_disruptive=st.is_disruptive,
                            requires_admin=st.requires_admin,
                        )
                    )

            rec_response = DiagnosticResultResponse(
                session_id=session.id,
                status=session.status,
                diagnosis_name=session.final_diagnosis,
                diagnosis_code=session.recommendation_code,
                category=session.diagnosis_category,
                severity=session.severity,
                summary=session.summary,
                steps=steps_resp,
                warnings=warnings,
                escalation_advice=escalation,
                completed_at=session.completed_at,
            )

        return SessionDetailResponse(
            id=session.id,
            created_at=session.created_at,
            completed_at=session.completed_at,
            status=session.status,
            final_diagnosis=session.final_diagnosis,
            diagnosis_category=session.diagnosis_category,
            severity=session.severity,
            recommendation_code=session.recommendation_code,
            summary=session.summary,
            answers=answers_summary,
            traces_count=len(session.traces),
            recommendation=rec_response,
        )

    def delete_session(self, db: Session, session_id: str) -> Dict[str, Any]:
        """Deletes a diagnostic session and all its child answers, traces, and recommendations."""
        session = db.query(DiagnosticSession).filter(DiagnosticSession.id == session_id).first()
        if not session:
            raise NetSageNotFoundException(f"Diagnostic session '{session_id}' not found.")

        try:
            db.delete(session)
            db.commit()
        except Exception:
            db.rollback()
            raise
        return {
            "message": f"Diagnostic session '{session_id}' deleted successfully.",
            "deleted_id": session_id,
        }


"""NetSage Diagnostic History Schemas.

Defines schemas for listing historical sessions, inspecting detailed session audits,
and managing past diagnostic records.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.diagnostic import DiagnosticResultResponse


class DiagnosticAnswerSummary(BaseModel):
    """Record of a user response to a diagnostic question."""
    id: int
    question_id: str
    question_text: str
    answer: str
    answered_at: datetime


class SessionSummaryResponse(BaseModel):
    """Concise session overview for the diagnostic history list."""
    id: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    final_diagnosis: Optional[str] = None
    diagnosis_category: Optional[str] = None
    severity: Optional[str] = None
    answers_count: int = 0


class SessionListResponse(BaseModel):
    """Paginated collection of diagnostic sessions."""
    total: int
    items: List[SessionSummaryResponse] = Field(default_factory=list)


class SessionDetailResponse(BaseModel):
    """Comprehensive diagnostic session detail including all answers and final recommendation."""
    id: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    final_diagnosis: Optional[str] = None
    diagnosis_category: Optional[str] = None
    severity: Optional[str] = None
    recommendation_code: Optional[str] = None
    summary: Optional[str] = None
    answers: List[DiagnosticAnswerSummary] = Field(default_factory=list)
    traces_count: int = 0
    recommendation: Optional[DiagnosticResultResponse] = None


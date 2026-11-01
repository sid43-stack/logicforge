import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.database.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="IN_PROGRESS", nullable=False)  # IN_PROGRESS, COMPLETED, INCONCLUSIVE, CONFLICT_DETECTED
    final_diagnosis = Column(String(255), nullable=True)
    diagnosis_category = Column(String(100), nullable=True)
    severity = Column(String(50), nullable=True)  # LOW, MEDIUM, HIGH, CRITICAL
    recommendation_code = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    working_memory_snapshot = Column(Text, nullable=True)  # JSON serialized

    # Relationships
    answers = relationship("DiagnosticAnswer", back_populates="session", cascade="all, delete-orphan", order_by="DiagnosticAnswer.answered_at")
    traces = relationship("InferenceTrace", back_populates="session", cascade="all, delete-orphan", order_by="InferenceTrace.execution_order")
    recommendations = relationship("Recommendation", back_populates="session", cascade="all, delete-orphan", order_by="Recommendation.priority")


class DiagnosticAnswer(Base):
    __tablename__ = "diagnostic_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)
    answer = Column(String(20), nullable=False)  # YES, NO, UNKNOWN
    answered_at = Column(DateTime, default=utc_now, nullable=False)

    session = relationship("DiagnosticSession", back_populates="answers")

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from app.database.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class InferenceTrace(Base):
    __tablename__ = "inference_traces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(String(50), nullable=False)
    rule_name = Column(String(255), nullable=False)
    conditions = Column(Text, nullable=False)  # JSON serialized
    conclusion = Column(Text, nullable=False)  # JSON serialized
    explanation = Column(Text, nullable=False)
    execution_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    session = relationship("DiagnosticSession", back_populates="traces")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"), nullable=False)
    recommendation_text = Column(Text, nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)

    session = relationship("DiagnosticSession", back_populates="recommendations")

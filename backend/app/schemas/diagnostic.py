"""NetSage Diagnostic Pydantic Schemas.

Defines request and response schemas for diagnostic session management,
question serving, answer processing, result retrieval, and explanation DAG visualization.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class HealthResponse(BaseModel):
    status: str
    project: str
    version: str
    timestamp: datetime


# -----------------------------------------------------------------------------
# Diagnostic Answer and Inquiry Schemas
# -----------------------------------------------------------------------------

class AnswerRequest(BaseModel):
    """Payload for submitting an answer to an active diagnostic question."""
    question_id: str = Field(..., description="Unique ID of the question being answered (e.g. 'Q01')")
    answer: str = Field(..., description="User response: 'YES', 'NO', or 'UNKNOWN'")


class DiagnosticAnswerCreate(BaseModel):
    question_id: str
    answer: str  # YES, NO, UNKNOWN


class DiagnosticSessionCreate(BaseModel):
    initial_facts: Optional[Dict[str, Any]] = None


# -----------------------------------------------------------------------------
# Dynamic WHY Explanation Schema
# -----------------------------------------------------------------------------

class WhyExplanationResponse(BaseModel):
    """Dynamic contextual justification for an active question."""
    question_id: str
    question_text: str
    fact_key: str
    investigating_hypothesis: str
    hypothesis_category: str
    triggering_rule_id: str
    triggering_rule_name: str
    rationale: str
    impact_if_yes: str
    impact_if_no: str


class QuestionWithWhyResponse(BaseModel):
    """Active diagnostic question augmented with dynamic WHY explanation."""
    id: str
    fact_key: str
    text: str
    category: str
    guidance: str
    answer_type: str = "boolean"
    available_options: List[str] = Field(default=["YES", "NO", "UNKNOWN"])
    why_explanation: Optional[WhyExplanationResponse] = None


# -----------------------------------------------------------------------------
# Diagnostic Result & Recommendation Schemas
# -----------------------------------------------------------------------------

class DiagnosticStepResponse(BaseModel):
    """An individual actionable remediation step."""
    order: int
    action: str
    command: Optional[str] = None
    description: str
    expected_outcome: str
    is_disruptive: bool = False
    requires_admin: bool = False


class DiagnosticResultResponse(BaseModel):
    """Comprehensive diagnostic diagnosis and remediation plan."""
    session_id: str
    status: str
    diagnosis_name: Optional[str] = None
    diagnosis_code: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    summary: Optional[str] = None
    steps: List[DiagnosticStepResponse] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    escalation_advice: Optional[str] = None
    completed_at: Optional[datetime] = None


# -----------------------------------------------------------------------------
# Session Lifecycle Responses
# -----------------------------------------------------------------------------

class StartSessionResponse(BaseModel):
    """Response returned when a diagnostic session is initiated or restarted."""
    session_id: str
    status: str
    created_at: datetime
    current_question: Optional[QuestionWithWhyResponse] = None


class AnswerResponse(BaseModel):
    """Response returned after submitting an answer to an active question."""
    session_id: str
    status: str  # IN_PROGRESS, COMPLETED, INCONCLUSIVE, CONFLICT_DETECTED
    is_completed: bool
    next_question: Optional[QuestionWithWhyResponse] = None
    result: Optional[DiagnosticResultResponse] = None
    message: Optional[str] = None


# -----------------------------------------------------------------------------
# Dynamic HOW Explanation & Inference DAG Schemas
# -----------------------------------------------------------------------------

class InferenceTraceStepResponse(BaseModel):
    """A single rule execution step in the inference trace."""
    order: int
    rule_id: str
    rule_name: str
    category: str
    conditions: Dict[str, Any]
    derived_facts: Dict[str, Any]
    explanation: str
    timestamp: str


class InferenceTreeNodeResponse(BaseModel):
    id: str
    label: str
    type: str  # USER_FACT, RULE, DERIVED_FACT, TERMINAL_DIAGNOSIS
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InferenceTreeEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None


class InferenceTreeGraphResponse(BaseModel):
    nodes: List[InferenceTreeNodeResponse] = Field(default_factory=list)
    edges: List[InferenceTreeEdgeResponse] = Field(default_factory=list)


class ExplanationResponse(BaseModel):
    """Full HOW explanation including chronological audit narrative and DAG graph."""
    session_id: str
    status: str
    final_diagnosis: Optional[str] = None
    diagnosis_category: Optional[str] = None
    diagnosis_severity: Optional[str] = None
    initial_user_evidence: Dict[str, Any] = Field(default_factory=dict)
    derived_intermediate_facts: Dict[str, Any] = Field(default_factory=dict)
    fired_rules_count: int
    execution_steps: List[InferenceTraceStepResponse] = Field(default_factory=list)
    reasoning_narrative: List[str] = Field(default_factory=list)
    inference_tree: InferenceTreeGraphResponse = Field(default_factory=InferenceTreeGraphResponse)


# -----------------------------------------------------------------------------
# DB Model Mapping Schemas (Compatibility)
# -----------------------------------------------------------------------------

class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recommendation_text: str
    priority: int
    completed: bool


class InferenceTraceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_id: str
    rule_name: str
    conditions: Any
    conclusion: Any
    explanation: str
    execution_order: int
    created_at: datetime


class DiagnosticSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    final_diagnosis: Optional[str] = None
    diagnosis_category: Optional[str] = None
    severity: Optional[str] = None
    summary: Optional[str] = None

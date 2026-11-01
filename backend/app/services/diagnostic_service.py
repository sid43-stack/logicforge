"""NetSage Diagnostic Service.

Coordinates the complete diagnostic lifecycle between the Pure Python expert system
(InferenceEngine, QuestionEngine, ExplanationEngine, RecommendationEngine)
and SQLAlchemy SQLite persistence.
"""

import json
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.diagnostic import DiagnosticSession, DiagnosticAnswer
from app.models.trace import InferenceTrace, Recommendation
from app.expert_system.inference_engine import InferenceEngine
from app.expert_system.question_engine import QuestionEngine, Question
from app.expert_system.explanation_engine import ExplanationEngine, WhyExplanation, HowExplanation
from app.expert_system.recommendation_engine import RecommendationEngine, RecommendationPlan
from app.core.exceptions import (
    NetSageException,
    NetSageNotFoundException,
    NetSageBadRequestException,
    NetSageConflictException,
)
from app.schemas.diagnostic import (
    StartSessionResponse,
    AnswerResponse,
    QuestionWithWhyResponse,
    WhyExplanationResponse,
    DiagnosticResultResponse,
    DiagnosticStepResponse,
    ExplanationResponse,
    InferenceTraceStepResponse,
    InferenceTreeNodeResponse,
    InferenceTreeEdgeResponse,
    InferenceTreeGraphResponse,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DiagnosticService:
    """Coordinates session management, dynamic inquiry, deduction, explanations, and persistence."""

    def __init__(
        self,
        question_engine: Optional[QuestionEngine] = None,
        explanation_engine: Optional[ExplanationEngine] = None,
        recommendation_engine: Optional[RecommendationEngine] = None,
    ):
        self.question_engine = question_engine or QuestionEngine()
        self.explanation_engine = explanation_engine or ExplanationEngine()
        self.recommendation_engine = recommendation_engine or RecommendationEngine()

    def _build_why_response(self, why: WhyExplanation) -> WhyExplanationResponse:
        return WhyExplanationResponse(
            question_id=why.question_id,
            question_text=why.question_text,
            fact_key=why.fact_key,
            investigating_hypothesis=why.investigating_hypothesis,
            hypothesis_category=why.hypothesis_category,
            triggering_rule_id=why.triggering_rule_id,
            triggering_rule_name=why.triggering_rule_name,
            rationale=why.rationale,
            impact_if_yes=why.impact_if_yes,
            impact_if_no=why.impact_if_no,
        )

    def _build_question_with_why(self, question: Question, engine: InferenceEngine) -> QuestionWithWhyResponse:
        why = self.explanation_engine.generate_why(question, engine)
        return QuestionWithWhyResponse(
            id=question.id,
            fact_key=question.fact_key,
            text=question.text,
            category=question.category.value,
            guidance=question.guidance,
            answer_type=question.answer_type,
            available_options=["YES", "NO", "UNKNOWN"],
            why_explanation=self._build_why_response(why),
        )

    def _build_result_response(
        self,
        session: DiagnosticSession,
        plan: Optional[RecommendationPlan],
    ) -> DiagnosticResultResponse:
        steps_resp = []
        warnings = []
        escalation = None

        if plan:
            warnings = list(plan.warnings)
            escalation = plan.escalation_advice
            for s in plan.steps:
                steps_resp.append(
                    DiagnosticStepResponse(
                        order=s.order,
                        action=s.action,
                        command=s.command,
                        description=s.description,
                        expected_outcome=s.expected_outcome,
                        is_disruptive=s.is_disruptive,
                        requires_admin=s.requires_admin,
                    )
                )

        return DiagnosticResultResponse(
            session_id=session.id,
            status=session.status,
            diagnosis_name=session.final_diagnosis,
            diagnosis_code=session.recommendation_code or getattr(plan, "code", None),
            category=session.diagnosis_category or getattr(plan, "category", None),
            severity=session.severity or getattr(plan, "severity", None),
            summary=session.summary or getattr(plan, "summary", None),
            steps=steps_resp,
            warnings=warnings,
            escalation_advice=escalation,
            completed_at=session.completed_at,
        )

    def _persist_remediation_and_traces(
        self,
        db: Session,
        session: DiagnosticSession,
        engine: InferenceEngine,
        plan: Optional[RecommendationPlan],
    ):
        """Saves recommended actions and execution traces to database tables."""
        # Clear any existing recommendations and traces for this session
        db.query(Recommendation).filter(Recommendation.session_id == session.id).delete()
        db.query(InferenceTrace).filter(InferenceTrace.session_id == session.id).delete()

        # Add steps from recommendation plan
        if plan:
            for s in plan.steps:
                cmd_txt = f" [{s.command}]" if s.command else ""
                db_rec = Recommendation(
                    session_id=session.id,
                    recommendation_text=f"{s.action}{cmd_txt}: {s.description}",
                    priority=s.order,
                    completed=False,
                )
                db.add(db_rec)

        # Add execution traces
        for trace_step in engine.get_inference_trace():
            db_trace = InferenceTrace(
                session_id=session.id,
                rule_id=trace_step.rule_id,
                rule_name=trace_step.rule_name,
                conditions=json.dumps(trace_step.conditions_evaluated),
                conclusion=json.dumps(trace_step.conclusion_asserted),
                explanation=trace_step.explanation,
                execution_order=trace_step.execution_order,
            )
            db.add(db_trace)

    # -------------------------------------------------------------------------
    # Public Service API
    # -------------------------------------------------------------------------

    def start_session(
        self,
        db: Session,
        initial_facts: Optional[Dict[str, Any]] = None,
    ) -> StartSessionResponse:
        """Initializes a new diagnostic session, configures working memory, and returns the first question."""
        session = DiagnosticSession(id=str(uuid.uuid4()), status="IN_PROGRESS")
        engine = InferenceEngine()

        # Apply any optional initial facts provided at session startup
        if initial_facts:
            for fact_key, val in initial_facts.items():
                engine.assert_user_fact(fact_key, val)

        # Determine if initial facts already established a diagnosis or conflict
        current_question: Optional[QuestionWithWhyResponse] = None

        if engine.has_conflict():
            session.status = "CONFLICT_DETECTED"
            session.completed_at = utc_now()
            session.summary = f"Contradictory state: {'; '.join(engine.get_conflicts())}"
        elif engine.has_terminal_diagnosis():
            session.status = "COMPLETED"
            session.completed_at = utc_now()
            diag = engine.get_terminal_diagnosis()
            session.final_diagnosis = diag["diagnosis"]
            session.diagnosis_category = diag.get("category", "")
            session.severity = diag.get("severity", "MEDIUM")
            plan = self.recommendation_engine.get_recommendation_by_diagnosis(session.final_diagnosis)
            if plan:
                session.recommendation_code = plan.code
                session.summary = plan.summary
                self._persist_remediation_and_traces(db, session, engine, plan)
        else:
            first_q = self.question_engine.select_next_question(engine)
            if first_q:
                current_question = self._build_question_with_why(first_q, engine)
            else:
                session.status = "INCONCLUSIVE"
                session.completed_at = utc_now()
                session.final_diagnosis = "Inconclusive Network Diagnosis"
                plan = self.recommendation_engine.get_inconclusive_plan()
                session.recommendation_code = plan.code
                session.summary = plan.summary
                self._persist_remediation_and_traces(db, session, engine, plan)

        session.working_memory_snapshot = json.dumps(engine.snapshot())
        try:
            db.add(session)
            db.commit()
            db.refresh(session)
        except Exception:
            db.rollback()
            raise

        return StartSessionResponse(
            session_id=session.id,
            status=session.status,
            created_at=session.created_at,
            current_question=current_question,
        )

    def submit_answer(
        self,
        db: Session,
        session_id: str,
        question_id: str,
        answer_str: str,
    ) -> AnswerResponse:
        """Processes a user answer, runs forward and backward chaining, and transitions session state."""
        session = db.query(DiagnosticSession).filter(DiagnosticSession.id == session_id).first()
        if not session:
            raise NetSageNotFoundException(f"Diagnostic session '{session_id}' not found.")

        if session.status in ("COMPLETED", "INCONCLUSIVE", "CONFLICT_DETECTED"):
            raise NetSageBadRequestException(
                f"Diagnostic session '{session_id}' has already ended with status '{session.status}'."
            )

        question = self.question_engine.registry.get_by_id(question_id)
        if not question:
            raise NetSageBadRequestException(f"Question with ID '{question_id}' is not recognized.")

        try:
            parsed_value = self.question_engine.parse_user_answer(answer_str)
        except ValueError as err:
            raise NetSageBadRequestException(str(err))

        # Check if question has already been answered in this session
        existing_answer = (
            db.query(DiagnosticAnswer)
            .filter(
                DiagnosticAnswer.session_id == session_id,
                DiagnosticAnswer.question_id == question_id,
            )
            .first()
        )
        if existing_answer:
            raise NetSageBadRequestException(
                f"Question '{question_id}' has already been answered in this session."
            )

        # Restore engine state from working memory snapshot
        engine = InferenceEngine()
        if session.working_memory_snapshot:
            engine.restore(json.loads(session.working_memory_snapshot))

        try:
            # Record answer in database
            db_answer = DiagnosticAnswer(
                session_id=session.id,
                question_id=question.id,
                question_text=question.text,
                answer=str(answer_str).upper(),
            )
            db.add(db_answer)

            # Assert fact into working memory and run forward chaining
            engine.assert_user_fact(question.fact_key, parsed_value, raise_on_contradiction=False)

            # Conflict Detection
            if engine.has_conflict():
                session.status = "CONFLICT_DETECTED"
                session.completed_at = utc_now()
                conflict_msg = "; ".join(engine.get_conflicts())
                session.summary = f"Contradictory evidence detected: {conflict_msg}"
                session.working_memory_snapshot = json.dumps(engine.snapshot())
                db.commit()
                raise NetSageConflictException(
                    detail=f"Contradictory evidence detected in session '{session_id}': {conflict_msg}"
                )

            # Terminal Diagnosis Established
            if engine.has_terminal_diagnosis():
                session.status = "COMPLETED"
                session.completed_at = utc_now()
                diag = engine.get_terminal_diagnosis()
                session.final_diagnosis = diag["diagnosis"]
                session.diagnosis_category = diag.get("category", "")
                session.severity = diag.get("severity", "MEDIUM")

                plan = self.recommendation_engine.get_recommendation_by_diagnosis(session.final_diagnosis)
                if plan:
                    session.recommendation_code = plan.code
                    session.summary = plan.summary

                self._persist_remediation_and_traces(db, session, engine, plan)
                session.working_memory_snapshot = json.dumps(engine.snapshot())
                db.commit()
                db.refresh(session)

                result_obj = self._build_result_response(session, plan)
                return AnswerResponse(
                    session_id=session.id,
                    status="COMPLETED",
                    is_completed=True,
                    next_question=None,
                    result=result_obj,
                    message="Diagnostic established successfully.",
                )

            # Check if inquiries are exhausted without diagnosis (INCONCLUSIVE)
            next_premise = engine.get_next_question_premise()
            if next_premise is None:
                session.status = "INCONCLUSIVE"
                session.completed_at = utc_now()
                session.final_diagnosis = "Inconclusive Network Diagnosis"
                plan = self.recommendation_engine.get_inconclusive_plan()
                session.recommendation_code = plan.code
                session.summary = plan.summary

                self._persist_remediation_and_traces(db, session, engine, plan)
                session.working_memory_snapshot = json.dumps(engine.snapshot())
                db.commit()
                db.refresh(session)

                result_obj = self._build_result_response(session, plan)
                return AnswerResponse(
                    session_id=session.id,
                    status="INCONCLUSIVE",
                    is_completed=True,
                    next_question=None,
                    result=result_obj,
                    message="Diagnostic inquiries exhausted with inconclusive outcome.",
                )

            # Session remains IN_PROGRESS
            next_question = self.question_engine.select_next_question(engine)
            if next_question is None:
                # Fallback to inconclusive if no question maps to premise
                session.status = "INCONCLUSIVE"
                session.completed_at = utc_now()
                session.final_diagnosis = "Inconclusive Network Diagnosis"
                plan = self.recommendation_engine.get_inconclusive_plan()
                session.recommendation_code = plan.code
                session.summary = plan.summary
                self._persist_remediation_and_traces(db, session, engine, plan)
                session.working_memory_snapshot = json.dumps(engine.snapshot())
                db.commit()
                db.refresh(session)

                result_obj = self._build_result_response(session, plan)
                return AnswerResponse(
                    session_id=session.id,
                    status="INCONCLUSIVE",
                    is_completed=True,
                    next_question=None,
                    result=result_obj,
                    message="No further relevant questions available.",
                )

            q_with_why = self._build_question_with_why(next_question, engine)
            session.working_memory_snapshot = json.dumps(engine.snapshot())
            db.commit()
            db.refresh(session)

            return AnswerResponse(
                session_id=session.id,
                status="IN_PROGRESS",
                is_completed=False,
                next_question=q_with_why,
                result=None,
                message="Answer accepted. Next question generated dynamically.",
            )
        except NetSageException:
            raise
        except Exception:
            db.rollback()
            raise

    def get_current_question(self, db: Session, session_id: str) -> QuestionWithWhyResponse:
        """Retrieves the active question with WHY explanation for an in-progress session."""
        session = db.query(DiagnosticSession).filter(DiagnosticSession.id == session_id).first()
        if not session:
            raise NetSageNotFoundException(f"Diagnostic session '{session_id}' not found.")

        if session.status != "IN_PROGRESS":
            raise NetSageBadRequestException(
                f"Diagnostic session '{session_id}' has status '{session.status}'. No active question available."
            )

        engine = InferenceEngine()
        if session.working_memory_snapshot:
            engine.restore(json.loads(session.working_memory_snapshot))

        next_q = self.question_engine.select_next_question(engine)
        if not next_q:
            raise NetSageBadRequestException(
                f"Diagnostic session '{session_id}' has exhausted all available questions."
            )

        return self._build_question_with_why(next_q, engine)

    def get_result(self, db: Session, session_id: str) -> DiagnosticResultResponse:
        """Retrieves the final diagnosis and remediation plan."""
        session = db.query(DiagnosticSession).filter(DiagnosticSession.id == session_id).first()
        if not session:
            raise NetSageNotFoundException(f"Diagnostic session '{session_id}' not found.")

        if session.status == "IN_PROGRESS":
            raise NetSageBadRequestException(
                f"Diagnostic session '{session_id}' is still in progress. Please answer remaining questions."
            )

        if session.status == "CONFLICT_DETECTED":
            return DiagnosticResultResponse(
                session_id=session.id,
                status="CONFLICT_DETECTED",
                diagnosis_name="Diagnostic Conflict Detected",
                diagnosis_code="CONFLICT",
                category="CONFLICT",
                severity="CRITICAL",
                summary=session.summary or "Inconsistent or mutually exclusive diagnostic facts were asserted.",
                steps=[],
                warnings=["Contradictory evidence prevents a single sound terminal diagnosis."],
                escalation_advice="Please restart the session and verify network conditions carefully.",
                completed_at=session.completed_at,
            )

        plan = None
        if session.recommendation_code:
            plan = self.recommendation_engine.get_recommendation_by_code(session.recommendation_code)
        if not plan and session.final_diagnosis:
            plan = self.recommendation_engine.get_recommendation_by_diagnosis(session.final_diagnosis)
        if not plan and session.status == "INCONCLUSIVE":
            plan = self.recommendation_engine.get_inconclusive_plan()

        return self._build_result_response(session, plan)

    def get_explanation(self, db: Session, session_id: str) -> ExplanationResponse:
        """Retrieves comprehensive HOW explanation including narrative audit and DAG tree."""
        session = db.query(DiagnosticSession).filter(DiagnosticSession.id == session_id).first()
        if not session:
            raise NetSageNotFoundException(f"Diagnostic session '{session_id}' not found.")

        engine = InferenceEngine()
        if session.working_memory_snapshot:
            engine.restore(json.loads(session.working_memory_snapshot))

        how: HowExplanation = self.explanation_engine.generate_how(engine)

        # Convert execution steps
        steps_resp = [
            InferenceTraceStepResponse(
                order=s.execution_order,
                rule_id=s.rule_id,
                rule_name=s.rule_name,
                category=s.category.value if hasattr(s.category, "value") else str(s.category),
                conditions=s.conditions_evaluated,
                derived_facts=s.conclusion_asserted,
                explanation=s.explanation,
                timestamp=s.timestamp.isoformat(),
            )
            for s in how.execution_steps
        ]

        # Convert DAG tree
        tree_nodes = [
            InferenceTreeNodeResponse(
                id=n.id,
                label=n.label,
                type=n.type,
                status=n.status,
                metadata=n.metadata,
            )
            for n in how.inference_tree.nodes
        ]
        tree_edges = [
            InferenceTreeEdgeResponse(
                id=e.id,
                source=e.source,
                target=e.target,
                label=e.label,
            )
            for e in how.inference_tree.edges
        ]

        return ExplanationResponse(
            session_id=session.id,
            status=how.session_status,
            final_diagnosis=how.final_diagnosis,
            diagnosis_category=how.diagnosis_category,
            diagnosis_severity=how.diagnosis_severity,
            initial_user_evidence=how.initial_user_evidence,
            derived_intermediate_facts=how.derived_intermediate_facts,
            fired_rules_count=how.fired_rules_count,
            execution_steps=steps_resp,
            reasoning_narrative=how.reasoning_narrative,
            inference_tree=InferenceTreeGraphResponse(nodes=tree_nodes, edges=tree_edges),
        )

    def restart_session(self, db: Session, session_id: str) -> StartSessionResponse:
        """Clears all answers and deductions, resetting an existing session to scratch."""
        session = db.query(DiagnosticSession).filter(DiagnosticSession.id == session_id).first()
        if not session:
            raise NetSageNotFoundException(f"Diagnostic session '{session_id}' not found.")

        try:
            # Delete dependent answers, traces, recommendations
            db.query(DiagnosticAnswer).filter(DiagnosticAnswer.session_id == session_id).delete()
            db.query(InferenceTrace).filter(InferenceTrace.session_id == session_id).delete()
            db.query(Recommendation).filter(Recommendation.session_id == session_id).delete()

            # Reset session columns
            session.status = "IN_PROGRESS"
            session.completed_at = None
            session.final_diagnosis = None
            session.diagnosis_category = None
            session.severity = None
            session.recommendation_code = None
            session.summary = None

            engine = InferenceEngine()
            first_q = self.question_engine.select_next_question(engine)
            current_question = self._build_question_with_why(first_q, engine) if first_q else None

            session.working_memory_snapshot = json.dumps(engine.snapshot())
            db.commit()
            db.refresh(session)
        except Exception:
            db.rollback()
            raise

        return StartSessionResponse(
            session_id=session.id,
            status=session.status,
            created_at=session.created_at,
            current_question=current_question,
        )

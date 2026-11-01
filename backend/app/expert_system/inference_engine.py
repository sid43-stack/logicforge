"""NetSage Unified Inference Engine.

Strictly independent of FastAPI, SQLAlchemy, and frontend frameworks.
Coordinates WorkingMemory, ForwardChainingEngine, and BackwardChainingEngine.
Drives dynamic diagnostic inquiry, performs multi-level rule chaining, tracks execution traces,
detects contradictions, and builds goal trees for the Explanation Center.
"""

from typing import Dict, List, Any, Optional, Set
from app.expert_system.types import (
    TriState,
    FactSourceType,
    RuleClassification,
    InferenceTraceStep,
    GoalTreeNode,
)
from app.expert_system.rules import Rule, PRODUCTION_RULES
from app.expert_system.working_memory import WorkingMemory, ContradictionError
from app.expert_system.forward_chaining import ForwardChainingEngine
from app.expert_system.backward_chaining import BackwardChainingEngine


class InferenceEngine:
    """Unified expert system engine orchestrating dual inference strategies and state."""

    def __init__(self, rules: Optional[List[Rule]] = None):
        self.rules: List[Rule] = rules if rules is not None else list(PRODUCTION_RULES)
        self.memory = WorkingMemory()
        self.forward_engine = ForwardChainingEngine(self.rules)
        self.backward_engine = BackwardChainingEngine(self.rules)

    def assert_user_fact(self, fact_key: str, value: Any, raise_on_contradiction: bool = False) -> List[InferenceTraceStep]:
        """Asserts a user response into working memory and runs forward chaining to fix-point.
        
        Args:
            fact_key: The fact key (e.g. 'external_ip_reachable')
            value: User answer value (bool or specific value)
            raise_on_contradiction: Whether to re-raise ContradictionError if a direct conflict occurs.
            
        Returns:
            List of newly fired InferenceTraceSteps resulting from this fact assertion.
        """
        # 1. Store the user-provided fact
        try:
            self.memory.set_fact(
                key=fact_key,
                value=value,
                source_type=FactSourceType.USER_INPUT,
                source_id="USER",
            )
        except ContradictionError as err:
            # Conflict is recorded inside working memory
            if raise_on_contradiction:
                raise err
            return []

        # 2. Run forward chaining to derive all cascading consequences
        new_steps = self.forward_engine.run(self.memory)
        return new_steps

    def assert_derived_fact(self, fact_key: str, value: Any, rule_id: str) -> List[InferenceTraceStep]:
        """Manually asserts a derived fact and triggers forward chaining."""
        self.memory.set_fact(
            key=fact_key,
            value=value,
            source_type=FactSourceType.RULE_DERIVED,
            source_id=rule_id,
        )
        return self.forward_engine.run(self.memory)

    def get_fact(self, fact_key: str, default: Any = None) -> Any:
        """Retrieves raw value of a fact from working memory."""
        return self.memory.get_fact(fact_key, default)

    def get_tristate(self, fact_key: str) -> TriState:
        """Retrieves truth state (TRUE, FALSE, UNKNOWN)."""
        return self.memory.get_tristate(fact_key)

    def get_terminal_diagnosis(self) -> Optional[Dict[str, Any]]:
        """Returns the primary confirmed terminal diagnosis if one has been reached without conflict.
        
        Crucial Soundness Rule: If any contradiction or conflicting terminal diagnosis is detected,
        the engine REFUSES to silently pick one diagnosis based on priority alone, returning None.
        """
        if self.has_conflict():
            return None

        diagnoses = self.forward_engine.terminal_diagnoses
        if not diagnoses:
            return None
        return diagnoses[0]

    def has_terminal_diagnosis(self) -> bool:
        """Checks if a valid, unconflicted terminal diagnosis has fired."""
        return len(self.forward_engine.terminal_diagnoses) > 0 and not self.has_conflict()

    def has_conflict(self) -> bool:
        """Checks if contradictory facts or conflicting terminal diagnoses were flagged."""
        return self.memory.has_conflicts() or self.forward_engine.has_conflict()

    def get_conflicts(self) -> List[str]:
        """Returns all conflict descriptions from memory and forward chaining."""
        conflicts = [c["message"] for c in self.memory.get_conflicts()]
        conflicts.extend(self.forward_engine.conflicts)
        return conflicts

    def get_session_status(self) -> str:
        """Determines the current lifecycle status of the diagnostic session.
        
        Returns:
            - 'CONFLICT_DETECTED': If contradictory facts or diagnoses were derived.
            - 'COMPLETED': If a valid, unconflicted terminal diagnosis has been established.
            - 'IN_PROGRESS': If questions remain that could lead to a diagnosis.
            - 'INCONCLUSIVE': If all relevant questions are exhausted without reaching a diagnosis.
        """
        if self.has_conflict():
            return "CONFLICT_DETECTED"

        if self.has_terminal_diagnosis():
            return "COMPLETED"

        # Check if there are still askable premises to investigate
        next_premise = self.backward_engine.find_next_askable_premise(self.memory)
        if next_premise is not None:
            return "IN_PROGRESS"

        return "INCONCLUSIVE"

    def get_next_question_premise(self) -> Optional[str]:
        """Returns the next askable fact key that backward chaining deems most relevant.
        
        If a terminal diagnosis has already been reached or a conflict is detected, returns None.
        """
        if self.has_terminal_diagnosis() or self.has_conflict():
            return None

        return self.backward_engine.find_next_askable_premise(self.memory)

    def get_inference_trace(self) -> List[InferenceTraceStep]:
        """Returns the complete chronological inference trace for Explanation Center."""
        return self.forward_engine.execution_trace

    def get_goal_tree(self, goal_key: str = "diagnosis", expected_value: Any = None) -> GoalTreeNode:
        """Generates a backward-chaining goal-resolution tree for a given diagnosis or fact."""
        if expected_value is None:
            active_diag = self.get_terminal_diagnosis()
            if active_diag:
                expected_value = active_diag["diagnosis"]
            else:
                candidates = self.backward_engine.get_candidate_terminal_diagnoses()
                expected_value = candidates[0][0] if candidates else None

        return self.backward_engine.resolve_goal(
            goal_key=goal_key,
            expected_value=expected_value,
            memory=self.memory,
        )

    # ---------------------------------------------------------------------
    # Session Persistence & Snapshot Management
    # ---------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """Serializes complete engine state (working memory, traces, fired rules) to a JSON-safe dict."""
        return {
            "memory": self.memory.to_dict(),
            "fired_rule_ids": list(self.forward_engine.fired_rule_ids),
            "execution_trace": [step.model_dump(mode="json") for step in self.forward_engine.execution_trace],
            "terminal_diagnoses": self.forward_engine.terminal_diagnoses,
            "conflicts": self.get_conflicts(),
        }

    def restore(self, data: Dict[str, Any]):
        """Restores complete engine state from a serialized snapshot."""
        self.memory = WorkingMemory.from_dict(data["memory"])
        self.forward_engine.reset()
        self.forward_engine._fired_rule_ids = set(data.get("fired_rule_ids", []))
        self.forward_engine._terminal_diagnoses = list(data.get("terminal_diagnoses", []))
        self.forward_engine._conflicts = list(data.get("conflicts", []))

        trace_steps = []
        for s in data.get("execution_trace", []):
            trace_steps.append(InferenceTraceStep(**s))
        self.forward_engine._execution_trace = trace_steps

    def reset(self):
        """Resets engine state for a brand-new session."""
        self.memory.clear()
        self.forward_engine.reset()

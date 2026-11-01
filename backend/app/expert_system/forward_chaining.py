"""NetSage Forward Chaining Engine - Data-Driven Deduction.

Strictly independent of FastAPI, SQLAlchemy, and frontend frameworks.
Applies production rules iteratively to WorkingMemory until fix-point is reached.
Implements conflict resolution by rule priority, cycle detection, execution trace
generation, and terminal diagnosis tracking.
"""

from typing import Dict, List, Set, Any, Optional
from datetime import datetime, timezone
from app.expert_system.types import (
    TriState,
    FactSourceType,
    RuleClassification,
    InferenceTraceStep,
)
from app.expert_system.rules import Rule, PRODUCTION_RULES
from app.expert_system.working_memory import WorkingMemory, ContradictionError


class ForwardChainingError(Exception):
    """Raised when an internal anomaly occurs during forward chaining."""
    pass


class ForwardChainingEngine:
    """Data-driven inference engine applying production rules to working memory."""

    def __init__(self, rules: Optional[List[Rule]] = None):
        self.rules: List[Rule] = rules if rules is not None else list(PRODUCTION_RULES)
        self.rules_by_id: Dict[str, Rule] = {r.id: r for r in self.rules}
        
        # Track fired rule IDs in the current session
        self._fired_rule_ids: Set[str] = set()
        # Ordered audit trace of all fired rules
        self._execution_trace: List[InferenceTraceStep] = []
        # Detected conflicts between fired rules or contradictory assertions
        self._conflicts: List[str] = []
        # Terminal diagnoses asserted by fired rules
        self._terminal_diagnoses: List[Dict[str, Any]] = []

    @property
    def fired_rule_ids(self) -> Set[str]:
        return set(self._fired_rule_ids)

    @property
    def execution_trace(self) -> List[InferenceTraceStep]:
        return list(self._execution_trace)

    @property
    def terminal_diagnoses(self) -> List[Dict[str, Any]]:
        return list(self._terminal_diagnoses)

    @property
    def conflicts(self) -> List[str]:
        return list(self._conflicts)

    def has_conflict(self) -> bool:
        return len(self._conflicts) > 0

    def step(self, memory: WorkingMemory) -> Optional[InferenceTraceStep]:
        """Finds eligible rules, resolves conflicts, and fires the highest-priority rule.
        
        Returns:
            InferenceTraceStep for the rule that fired, or None if no rules can fire.
        """
        all_facts = memory.get_all_facts()
        eligible_rules: List[Rule] = []

        for rule in self.rules:
            # 1. Skip rules that have already fired
            if rule.id in self._fired_rule_ids:
                continue

            # 2. Evaluate conditions under 3-valued logic
            eval_result = rule.evaluate_conditions(all_facts)
            if eval_result == TriState.TRUE:
                eligible_rules.append(rule)

        if not eligible_rules:
            return None

        # 3. Conflict Resolution: Sort by priority DESC, then by rule ID ASC
        eligible_rules.sort(key=lambda r: (-r.priority, r.id))
        selected_rule = eligible_rules[0]

        # 4. Fire the selected rule
        order = len(self._execution_trace) + 1
        conditions_snapshot = {
            cond.fact_key: all_facts.get(cond.fact_key)
            for cond in selected_rule.conditions
        }

        # Assert conclusions into working memory
        try:
            for fact_key, val in selected_rule.conclusions.items():
                memory.set_fact(
                    key=fact_key,
                    value=val,
                    source_type=FactSourceType.RULE_DERIVED,
                    source_id=selected_rule.id,
                )
        except ContradictionError as err:
            self._conflicts.append(str(err))

        # Check for conflicting terminal diagnoses
        if selected_rule.classification == RuleClassification.TERMINAL_DIAGNOSIS:
            diagnosis_info = {
                "rule_id": selected_rule.id,
                "rule_name": selected_rule.name,
                "diagnosis": selected_rule.conclusions.get("diagnosis"),
                "category": selected_rule.conclusions.get("diagnosis_category"),
                "severity": selected_rule.conclusions.get("diagnosis_severity"),
                "recommendation_code": selected_rule.conclusions.get("recommendation_code"),
            }
            if self._terminal_diagnoses:
                # If an existing terminal diagnosis has a different category or diagnosis name, record conflict
                for prev in self._terminal_diagnoses:
                    if prev["diagnosis"] != diagnosis_info["diagnosis"]:
                        conflict_str = (
                            f"Contradictory terminal diagnoses derived: "
                            f"'{prev['diagnosis']}' ({prev['rule_id']}) vs "
                            f"'{diagnosis_info['diagnosis']}' ({selected_rule.id})"
                        )
                        self._conflicts.append(conflict_str)

            self._terminal_diagnoses.append(diagnosis_info)

        # 5. Record trace step
        step_record = InferenceTraceStep(
            execution_order=order,
            rule_id=selected_rule.id,
            rule_name=selected_rule.name,
            category=selected_rule.category,
            classification=selected_rule.classification,
            conditions_evaluated=conditions_snapshot,
            conclusion_asserted=dict(selected_rule.conclusions),
            explanation=selected_rule.explanation,
            timestamp=datetime.now(timezone.utc),
        )

        self._fired_rule_ids.add(selected_rule.id)
        self._execution_trace.append(step_record)

        return step_record

    def run(self, memory: WorkingMemory, max_iterations: int = 100) -> List[InferenceTraceStep]:
        """Runs forward chaining to a fix-point (until no more rules can fire).
        
        Args:
            memory: The WorkingMemory instance to evaluate and update.
            max_iterations: Safety limit to prevent infinite loops in cyclic rule bases.
            
        Returns:
            List of new InferenceTraceSteps recorded in this run.
        """
        initial_trace_count = len(self._execution_trace)
        iterations = 0

        while iterations < max_iterations:
            fired_step = self.step(memory)
            if fired_step is None:
                break  # Fix-point reached: no more rules eligible to fire
            iterations += 1

        if iterations >= max_iterations:
            raise ForwardChainingError(
                f"Forward chaining exceeded maximum iteration limit ({max_iterations}). Cycle suspected."
            )

        return self._execution_trace[initial_trace_count:]

    def reset(self):
        """Resets engine state for a new session."""
        self._fired_rule_ids.clear()
        self._execution_trace.clear()
        self._conflicts.clear()
        self._terminal_diagnoses.clear()


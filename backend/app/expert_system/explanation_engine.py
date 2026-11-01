"""NetSage Explanation Engine - Dynamic WHY and HOW Facilities.

Strictly independent of FastAPI, SQLAlchemy, and frontend frameworks.
Generates:
1. Dynamic WHY explanations: Justifies why a question is being asked, which candidate
   hypothesis is under investigation, which rule premise it satisfies, and how answering
   YES/NO influences subsequent inference.
2. Comprehensive HOW explanations: Produces chronological audit narratives and a
   structured directed acyclic graph (DAG) representing the complete inference path.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from app.expert_system.types import (
    TriState,
    FactSourceType,
    RuleClassification,
    InferenceTraceStep,
)
from app.expert_system.rules import Rule
from app.expert_system.question_engine import Question
from app.expert_system.inference_engine import InferenceEngine


class WhyExplanation(BaseModel):
    """Dynamic contextual justification for an active question."""
    question_id: str
    question_text: str
    fact_key: str
    investigating_hypothesis: str = Field(..., description="Target network fault under active investigation")
    hypothesis_category: str
    triggering_rule_id: str = Field(..., description="Production rule that requires this premise")
    triggering_rule_name: str
    rationale: str = Field(..., description="Why this question is relevant given current working memory")
    impact_if_yes: str = Field(..., description="Logical consequence if the answer is YES")
    impact_if_no: str = Field(..., description="Logical consequence if the answer is NO")


class InferenceTreeNode(BaseModel):
    """Node in the Explanation Center inference DAG."""
    id: str
    label: str
    type: str  # 'USER_FACT', 'RULE', 'DERIVED_FACT', 'TERMINAL_DIAGNOSIS'
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InferenceTreeEdge(BaseModel):
    """Directed edge in the Explanation Center inference DAG."""
    id: str
    source: str
    target: str
    label: Optional[str] = None


class InferenceTreeGraph(BaseModel):
    """Structured graph representation for frontend visualization."""
    nodes: List[InferenceTreeNode] = Field(default_factory=list)
    edges: List[InferenceTreeEdge] = Field(default_factory=list)


class HowExplanation(BaseModel):
    """Comprehensive post-diagnosis explanation of reasoning."""
    session_status: str
    final_diagnosis: Optional[str]
    diagnosis_category: Optional[str]
    diagnosis_severity: Optional[str]
    initial_user_evidence: Dict[str, Any]
    derived_intermediate_facts: Dict[str, Any]
    fired_rules_count: int
    execution_steps: List[InferenceTraceStep]
    reasoning_narrative: List[str]
    inference_tree: InferenceTreeGraph


class ExplanationEngine:
    """Generates dynamic WHY and HOW explanation facilities."""

    def generate_why(self, question: Question, engine: InferenceEngine) -> WhyExplanation:
        """Dynamically generates a WHY explanation tailored to the current inference state.
        
        Inspects backward chaining candidate goals to identify which rule requires this premise,
        what facts were already established, and how answering YES or NO impacts deduction.
        """
        fact_key = question.fact_key
        memory_facts = engine.memory.get_all_facts()

        # Find which rule and hypothesis actively requires this premise
        target_rule: Optional[Rule] = None
        target_hypothesis = "Network Connectivity Problem"
        target_category = question.category.value

        # Inspect candidate terminal diagnoses
        candidates = engine.backward_engine.get_candidate_terminal_diagnoses()
        for diag_name, rule in candidates:
            tree = engine.backward_engine.resolve_goal("diagnosis", expected_value=diag_name, memory=engine.memory)
            if tree.unresolved_premises and fact_key in tree.unresolved_premises:
                target_hypothesis = diag_name
                target_category = rule.category.value
                # Find the specific rule consuming this condition
                for r in engine.rules:
                    if any(c.fact_key == fact_key for c in r.conditions):
                        target_rule = r
                        break
                break

        if target_rule is None:
            # Fallback to any rule with this condition
            for r in engine.rules:
                if any(c.fact_key == fact_key for c in r.conditions):
                    target_rule = r
                    target_hypothesis = r.conclusions.get("diagnosis", r.name)
                    target_category = r.category.value
                    break

        rule_id = target_rule.id if target_rule else "R_INSPECT"
        rule_name = target_rule.name if target_rule else "Active Diagnostic Rule"

        # Construct contextual rationale based on current working memory
        already_established = []
        if memory_facts.get("gateway_reachable") is True:
            already_established.append("local default gateway is reachable")
        if memory_facts.get("external_ip_reachable") is True:
            already_established.append("public IP ping responds")
        if memory_facts.get("ip_is_apipa") is True:
            already_established.append("device holds an autoconfigured APIPA IP (169.254.x.x)")
        if memory_facts.get("domain_access") is False:
            already_established.append("domain name resolution fails")
        if memory_facts.get("using_wifi") is True:
            already_established.append("device is connected wirelessly")

        if already_established:
            context_str = f"Given that {', and '.join(already_established)}, "
        else:
            context_str = "To establish initial baseline connectivity, "

        rationale = (
            f"{context_str}we are testing whether '{fact_key}' is present. "
            f"Rule {rule_id} ({rule_name}) requires this premise to evaluate "
            f"the hypothesis of '{target_hypothesis}'."
        )

        impact_yes = (
            f"If YES: Establishes '{fact_key}' as confirmed evidence, allowing Rule {rule_id} "
            f"to progress toward confirming '{target_hypothesis}'."
        )
        impact_no = (
            f"If NO: Refutes premises requiring '{fact_key}', eliminating unsupported rules and "
            f"redirecting inquiry to alternative network failure modes."
        )

        return WhyExplanation(
            question_id=question.id,
            question_text=question.text,
            fact_key=question.fact_key,
            investigating_hypothesis=target_hypothesis,
            hypothesis_category=target_category,
            triggering_rule_id=rule_id,
            triggering_rule_name=rule_name,
            rationale=rationale,
            impact_if_yes=impact_yes,
            impact_if_no=impact_no,
        )

    def generate_how(self, engine: InferenceEngine) -> HowExplanation:
        """Constructs a complete retrospective explanation of the diagnostic decision path.
        
        Compiles initial user facts, fired rules in order, derived intermediate facts,
        terminal diagnosis, and a structured inference DAG suitable for visualization.
        """
        user_facts = engine.memory.get_facts_by_source(FactSourceType.USER_INPUT)
        derived_facts = engine.memory.get_facts_by_source(FactSourceType.RULE_DERIVED)
        traces = engine.get_inference_trace()
        terminal_diag = engine.get_terminal_diagnosis()
        status = engine.get_session_status()

        # Build chronological reasoning narrative
        narrative: List[str] = []
        if not traces:
            if status == "INCONCLUSIVE":
                narrative.append(
                    "Diagnostic inquiry completed without matching any known failure modes. "
                    "All evaluated symptoms indicated standard operating parameters."
                )
            elif status == "CONFLICT_DETECTED":
                narrative.append(
                    "Inference halted because contradictory evidence was detected between symptoms."
                )
            else:
                narrative.append("Session is still in progress; no rules have fired yet.")
        else:
            narrative.append(f"Diagnostic session began with {len(user_facts)} observed symptoms.")
            for step in traces:
                conditions_str = ", ".join(f"{k}={v}" for k, v in step.conditions_evaluated.items())
                conclusions_str = ", ".join(f"{k}={v}" for k, v in step.conclusion_asserted.items())
                narrative.append(
                    f"Step {step.execution_order}: Rule {step.rule_id} ({step.rule_name}) fired. "
                    f"Because {conditions_str}, the system inferred {conclusions_str}. "
                    f"Rationale: {step.explanation}"
                )

            if terminal_diag:
                narrative.append(
                    f"Conclusion: Diagnostic analysis confirmed '{terminal_diag['diagnosis']}' "
                    f"(Category: {terminal_diag['category']}, Severity: {terminal_diag['severity']})."
                )

        # Build Inference Tree (DAG)
        nodes: List[InferenceTreeNode] = []
        edges: List[InferenceTreeEdge] = []
        node_ids: set = set()

        # 1. Add User Fact Nodes
        for k, v in user_facts.items():
            node_id = f"fact_{k}"
            nodes.append(InferenceTreeNode(
                id=node_id,
                label=f"{k}: {v}",
                type="USER_FACT",
                status="ASSERTED",
                metadata={"source": "USER", "value": v}
            ))
            node_ids.add(node_id)

        # 2. Add Rules and intermediate/terminal derivations
        for step in traces:
            rule_node_id = f"rule_{step.rule_id}"
            nodes.append(InferenceTreeNode(
                id=rule_node_id,
                label=f"{step.rule_id}: {step.rule_name}",
                type="RULE",
                status="FIRED",
                metadata={"priority": step.execution_order, "explanation": step.explanation}
            ))
            node_ids.add(rule_node_id)

            # Edges from satisfied conditions -> Rule
            for cond_key in step.conditions_evaluated.keys():
                parent_fact_id = f"fact_{cond_key}"
                if parent_fact_id in node_ids:
                    edges.append(InferenceTreeEdge(
                        id=f"{parent_fact_id}->{rule_node_id}",
                        source=parent_fact_id,
                        target=rule_node_id,
                        label="satisfies"
                    ))

            # Concluded facts
            for conc_key, conc_val in step.conclusion_asserted.items():
                if conc_key == "diagnosis":
                    diag_node_id = "node_terminal_diagnosis"
                    nodes.append(InferenceTreeNode(
                        id=diag_node_id,
                        label=f"Diagnosis: {conc_val}",
                        type="TERMINAL_DIAGNOSIS",
                        status="CONFIRMED",
                        metadata={"severity": step.conclusion_asserted.get("diagnosis_severity")}
                    ))
                    node_ids.add(diag_node_id)
                    edges.append(InferenceTreeEdge(
                        id=f"{rule_node_id}->{diag_node_id}",
                        source=rule_node_id,
                        target=diag_node_id,
                        label="concludes"
                    ))
                elif conc_key not in ("diagnosis_category", "diagnosis_severity", "recommendation_code"):
                    derived_node_id = f"fact_{conc_key}"
                    if derived_node_id not in node_ids:
                        nodes.append(InferenceTreeNode(
                            id=derived_node_id,
                            label=f"{conc_key}: {conc_val}",
                            type="DERIVED_FACT",
                            status="INFERRED",
                            metadata={"derived_by": step.rule_id, "value": conc_val}
                        ))
                        node_ids.add(derived_node_id)
                    edges.append(InferenceTreeEdge(
                        id=f"{rule_node_id}->{derived_node_id}",
                        source=rule_node_id,
                        target=derived_node_id,
                        label="asserts"
                    ))

        inference_tree = InferenceTreeGraph(nodes=nodes, edges=edges)

        return HowExplanation(
            session_status=status,
            final_diagnosis=terminal_diag["diagnosis"] if terminal_diag else None,
            diagnosis_category=terminal_diag["category"] if terminal_diag else None,
            diagnosis_severity=terminal_diag["severity"] if terminal_diag else None,
            initial_user_evidence=user_facts,
            derived_intermediate_facts=derived_facts,
            fired_rules_count=len(traces),
            execution_steps=traces,
            reasoning_narrative=narrative,
            inference_tree=inference_tree,
        )


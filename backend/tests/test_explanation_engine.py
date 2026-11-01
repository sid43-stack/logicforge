import pytest
from app.expert_system.types import TriState
from app.expert_system.inference_engine import InferenceEngine
from app.expert_system.question_engine import QuestionRegistry, QuestionEngine
from app.expert_system.explanation_engine import ExplanationEngine


def test_dynamic_why_explanation_generation():
    """Verify WHY explanation dynamically reflects active hypothesis and triggering rules."""
    engine = InferenceEngine()
    q_engine = QuestionEngine()
    exp_engine = ExplanationEngine()

    # Pre-populate working memory so dns_failure_suspected is derived
    engine.assert_user_fact("external_ip_reachable", True)
    engine.assert_user_fact("domain_access", False)

    # Next question should be asking about dns_server_reachable (Q13)
    next_q = q_engine.select_next_question(engine)
    assert next_q is not None
    assert next_q.fact_key == "dns_server_reachable"

    why = exp_engine.generate_why(next_q, engine)
    assert why.question_id == next_q.id
    assert why.fact_key == "dns_server_reachable"
    assert "DNS" in why.investigating_hypothesis or "DNS" in why.hypothesis_category
    assert why.triggering_rule_id in ("R12", "R13", "R14", "R15")
    assert "dns_server_reachable" in why.rationale
    assert len(why.impact_if_yes) > 10
    assert len(why.impact_if_no) > 10


def test_how_explanation_trace_and_narrative_accuracy():
    """Verify HOW explanation accurately reconstructs reasoning narrative for completed session."""
    engine = InferenceEngine()
    exp_engine = ExplanationEngine()

    # Execute DNS Outage Scenario: R11 -> R12 -> R13
    engine.assert_user_fact("external_ip_reachable", True)
    engine.assert_user_fact("domain_access", False)
    engine.assert_user_fact("dns_server_reachable", False)
    engine.assert_user_fact("multiple_devices_affected", True)

    how = exp_engine.generate_how(engine)
    assert how.session_status == "COMPLETED"
    assert how.final_diagnosis == "Upstream DNS Provider Outage"
    assert how.diagnosis_category == "DNS"
    assert how.diagnosis_severity == "HIGH"
    assert how.fired_rules_count == 3

    # Check narrative entries
    narrative_text = " ".join(how.reasoning_narrative)
    assert "R11" in narrative_text
    assert "R12" in narrative_text
    assert "R13" in narrative_text
    assert "Upstream DNS Provider Outage" in narrative_text


def test_how_explanation_inference_tree_dag_generation():
    """Verify HOW explanation constructs a valid DAG structure with nodes and edges."""
    engine = InferenceEngine()
    exp_engine = ExplanationEngine()

    engine.assert_user_fact("gateway_reachable", True)
    engine.assert_user_fact("external_ip_reachable", False)
    engine.assert_user_fact("multiple_devices_affected", True)

    how = exp_engine.generate_how(engine)
    tree = how.inference_tree

    assert len(tree.nodes) > 0
    assert len(tree.edges) > 0

    node_types = {n.type for n in tree.nodes}
    assert "USER_FACT" in node_types
    assert "RULE" in node_types
    assert "DERIVED_FACT" in node_types
    assert "TERMINAL_DIAGNOSIS" in node_types

    # Verify edge connectivity
    edge_labels = {e.label for e in tree.edges}
    assert "satisfies" in edge_labels
    assert "concludes" in edge_labels


def test_how_explanation_inconclusive_session():
    """Verify HOW explanation handles inconclusive sessions gracefully."""
    engine = InferenceEngine()
    exp_engine = ExplanationEngine()

    # Benign responses
    engine.assert_user_fact("device_connected", True)
    engine.assert_user_fact("valid_ip", True)
    engine.assert_user_fact("ip_is_apipa", False)
    engine.assert_user_fact("gateway_reachable", True)
    engine.assert_user_fact("external_ip_reachable", True)
    engine.assert_user_fact("domain_access", True)
    engine.assert_user_fact("using_wifi", False)
    engine.assert_user_fact("high_latency_observed", False)
    engine.assert_user_fact("packet_loss_observed", False)

    how = exp_engine.generate_how(engine)
    assert how.session_status == "INCONCLUSIVE"
    assert how.final_diagnosis is None
    assert any("All evaluated symptoms indicated standard operating parameters" in line for line in how.reasoning_narrative)


def test_how_explanation_conflicting_session():
    """Verify HOW explanation captures contradictory sessions."""
    engine = InferenceEngine()
    exp_engine = ExplanationEngine()

    engine.assert_user_fact("gateway_reachable", True)
    engine.assert_user_fact("gateway_reachable", False)

    how = exp_engine.generate_how(engine)
    assert how.session_status == "CONFLICT_DETECTED"
    assert any("contradictory evidence was detected" in line for line in how.reasoning_narrative)

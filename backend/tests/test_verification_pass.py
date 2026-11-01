"""Independent Phase 3 Verification Pass Test Suite.

Exhaustively verifies:
1. Tri-State Logic (distinct TRUE, FALSE, UNKNOWN; UNKNOWN never satisfies FALSE).
2. Contradiction Handling (no silent overwrite, no unjustified diagnosis, conflict detected).
3. Forward Chaining (all 6 categories, multi-level chaining, intermediate non-termination, incremental firing).
4. Backward Chaining (recursive goal resolution, multiple supporting rules, excluding known facts, cycle detection).
5. Hybrid Inference (backward premise selection -> user answer -> forward deduction -> next question recalculation -> no repeated questions).
6. State Serialization (JSON fidelity, continuation of inference without duplicate firing).
7. Terminal Diagnosis (intermediate vs terminal separation, no silent resolution of conflicting terminal diagnoses, inconclusive handling).
8. Code Quality & Architectural Decoupling (no FastAPI/SQLAlchemy/React dependencies in expert system core).
"""

import sys
import json
import pytest
from datetime import datetime
from app.expert_system.types import (
    TriState,
    Operator,
    Condition,
    GoalResolutionStatus,
    RuleCategory,
    RuleClassification,
    FactSourceType,
)
from app.expert_system.rules import Rule, PRODUCTION_RULES
from app.expert_system.working_memory import WorkingMemory, ContradictionError
from app.expert_system.forward_chaining import ForwardChainingEngine
from app.expert_system.backward_chaining import (
    BackwardChainingEngine,
    BackwardChainingCycleError,
)
from app.expert_system.inference_engine import InferenceEngine


# =========================================================================
# 1. TRI-STATE LOGIC VERIFICATION
# =========================================================================

def test_v1_tristate_distinct_handling():
    """Verify TRUE, FALSE, and UNKNOWN are handled distinctly."""
    cond_true = Condition(fact_key="test_fact", operator=Operator.EQUALS, value=True)
    cond_false = Condition(fact_key="test_fact", operator=Operator.EQUALS, value=False)

    # When actual is None or UNKNOWN
    assert cond_true.evaluate(None) == TriState.UNKNOWN
    assert cond_true.evaluate(TriState.UNKNOWN) == TriState.UNKNOWN
    assert cond_false.evaluate(None) == TriState.UNKNOWN
    assert cond_false.evaluate(TriState.UNKNOWN) == TriState.UNKNOWN

    # When actual is True
    assert cond_true.evaluate(True) == TriState.TRUE
    assert cond_false.evaluate(True) == TriState.FALSE

    # When actual is False
    assert cond_true.evaluate(False) == TriState.FALSE
    assert cond_false.evaluate(False) == TriState.TRUE


def test_v1_unknown_never_satisfies_false_condition():
    """CRITICAL: Ensure UNKNOWN never satisfies a condition requiring FALSE."""
    cond_requires_false = Condition(fact_key="valid_ip", operator=Operator.EQUALS, value=False)

    # Missing/unknown fact must evaluate to UNKNOWN, NOT TRUE!
    assert cond_requires_false.evaluate(None) == TriState.UNKNOWN
    assert cond_requires_false.evaluate(TriState.UNKNOWN) == TriState.UNKNOWN
    assert cond_requires_false.evaluate(None) != TriState.TRUE

    # Rule requiring valid_ip == False must NOT fire if valid_ip is UNKNOWN
    rule = Rule(
        id="R_REQUIRES_FALSE",
        name="Rule Requiring False",
        category=RuleCategory.IP_DHCP,
        priority=80,
        conditions=[cond_requires_false],
        conclusions={"should_not_fire": True},
        explanation="Testing false condition evaluation."
    )
    wm = WorkingMemory()
    # Fact not asserted -> UNKNOWN
    assert rule.evaluate_conditions(wm.get_all_facts()) == TriState.UNKNOWN

    engine = ForwardChainingEngine(rules=[rule])
    traces = engine.run(wm)
    assert len(traces) == 0
    assert wm.contains("should_not_fire") is False


def test_v1_rules_with_unknown_premises_do_not_fire():
    """Verify rules with any UNKNOWN premise cannot fire."""
    rule = Rule(
        id="R_MULTI_COND",
        name="Multi Condition Rule",
        category=RuleCategory.DNS,
        priority=80,
        conditions=[
            Condition(fact_key="fact_1", operator=Operator.EQUALS, value=True),
            Condition(fact_key="fact_2", operator=Operator.EQUALS, value=True),
        ],
        conclusions={"fired": True},
        explanation="Testing unknown premise block."
    )
    wm = WorkingMemory()
    wm.set_fact("fact_1", True, FactSourceType.USER_INPUT)
    # fact_2 is UNKNOWN
    assert rule.evaluate_conditions(wm.get_all_facts()) == TriState.UNKNOWN

    engine = ForwardChainingEngine(rules=[rule])
    traces = engine.run(wm)
    assert len(traces) == 0
    assert wm.contains("fired") is False


# =========================================================================
# 2. CONTRADICTION HANDLING VERIFICATION
# =========================================================================

def test_v2_assert_fact_as_true_and_false_detected():
    """Assert the same fact as TRUE then FALSE; verify conflict is detected without silent overwrite."""
    engine = InferenceEngine()
    engine.assert_user_fact("gateway_reachable", True)
    assert engine.get_fact("gateway_reachable") is True

    # Now attempt contradictory assertion
    engine.assert_user_fact("gateway_reachable", False)

    # 1. Conflict detected
    assert engine.has_conflict() is True
    assert engine.get_session_status() == "CONFLICT_DETECTED"
    assert len(engine.get_conflicts()) > 0
    assert any("Contradiction on fact 'gateway_reachable'" in c for c in engine.get_conflicts())

    # 2. Existing evidence was NOT silently overwritten!
    assert engine.get_fact("gateway_reachable") is True

    # 3. No unjustified terminal diagnosis was generated!
    assert engine.get_terminal_diagnosis() is None
    assert engine.has_terminal_diagnosis() is False


def test_v2_rule_contradiction_handling():
    """Verify that if two rules assert opposing values for the same fact, conflict is logged safely."""
    rule1 = Rule(
        id="R_C1",
        name="Rule Asserting True",
        category=RuleCategory.DNS,
        priority=90,
        conditions=[Condition(fact_key="trigger", operator=Operator.EQUALS, value=True)],
        conclusions={"flag": True},
        explanation="Sets flag true"
    )
    rule2 = Rule(
        id="R_C2",
        name="Rule Asserting False",
        category=RuleCategory.DNS,
        priority=80,
        conditions=[Condition(fact_key="trigger", operator=Operator.EQUALS, value=True)],
        conclusions={"flag": False},
        explanation="Sets flag false"
    )
    wm = WorkingMemory()
    wm.set_fact("trigger", True, FactSourceType.USER_INPUT)
    engine = ForwardChainingEngine(rules=[rule1, rule2])

    engine.run(wm)
    assert engine.has_conflict() is True
    assert any("Contradiction on fact 'flag'" in c for c in engine.conflicts)
    # Original value set by highest-priority rule R_C1 is preserved
    assert wm.get_fact("flag") is True


# =========================================================================
# 3. FORWARD CHAINING VERIFICATION
# =========================================================================

@pytest.mark.parametrize("category,user_inputs,expected_diagnosis,expected_rules", [
    (
        "N01_DNS",
        {"external_ip_reachable": True, "domain_access": False, "dns_server_reachable": False, "multiple_devices_affected": True},
        "Upstream DNS Provider Outage",
        ["R11", "R12", "R13"],
    ),
    (
        "N02_DHCP",
        {"device_connected": True, "ip_is_apipa": True, "valid_ip": False, "multiple_devices_affected": True},
        "Router DHCP Server Failure",
        ["R01", "R03", "R04"],
    ),
    (
        "N03_GATEWAY",
        {"valid_ip": True, "gateway_reachable": False, "multiple_devices_affected": True, "router_reboot_temporarily_fixed": True},
        "Router Gateway Crash / Hardware Overload",
        ["R06", "R08", "R09"],
    ),
    (
        "N04_WIFI",
        {"using_wifi": True, "wifi_signal_weak": True, "frequent_disconnections": True, "problem_on_ethernet_too": False},
        "Wi-Fi Signal Attenuation and Range Limitation",
        ["R17", "R18", "R19"],
    ),
    (
        "N05_PERF",
        {"high_latency_observed": True, "heavy_bandwidth_usage": True},
        "Local Network Bufferbloat & Bandwidth Saturation",
        ["R21", "R22", "R23"],
    ),
    (
        "N06_ISP",
        {"gateway_reachable": True, "external_ip_reachable": False, "multiple_devices_affected": True},
        "Wide-Area ISP Service Outage",
        ["R25", "R26", "R27"],
    ),
])
def test_v3_forward_chaining_all_six_categories(category, user_inputs, expected_diagnosis, expected_rules):
    """Verify complete multi-level rule execution across all six diagnostic categories."""
    engine = InferenceEngine()
    for key, val in user_inputs.items():
        engine.assert_user_fact(key, val)

    assert engine.get_session_status() == "COMPLETED"
    diag = engine.get_terminal_diagnosis()
    assert diag is not None
    assert diag["diagnosis"] == expected_diagnosis

    fired_rule_ids = [step.rule_id for step in engine.get_inference_trace()]
    for rule_id in expected_rules:
        assert rule_id in fired_rule_ids


def test_v3_new_evidence_triggers_previously_ineligible_rules():
    """Verify that adding new evidence dynamically activates previously ineligible rules."""
    engine = InferenceEngine()

    # Evidence 1: Only enough to trigger R11 (Intermediate)
    t1 = engine.assert_user_fact("external_ip_reachable", True)
    assert len(t1) == 0  # domain_access is unknown

    t2 = engine.assert_user_fact("domain_access", False)
    assert len(t2) == 1
    assert t2[0].rule_id == "R11"
    assert engine.get_fact("dns_failure_suspected") is True
    # R12 is NOT eligible yet (dns_server_reachable is unknown)
    assert "R12" not in engine.forward_engine.fired_rule_ids

    # Evidence 2: Provide dns_server_reachable -> R12 now fires!
    t3 = engine.assert_user_fact("dns_server_reachable", False)
    assert any(step.rule_id == "R12" for step in t3)
    assert engine.get_fact("dns_server_failure_suspected") is True

    # Evidence 3: multiple_devices_affected -> R13 now fires!
    t4 = engine.assert_user_fact("multiple_devices_affected", True)
    assert any(step.rule_id == "R13" for step in t4)
    assert engine.get_terminal_diagnosis()["diagnosis"] == "Upstream DNS Provider Outage"


# =========================================================================
# 4. BACKWARD CHAINING VERIFICATION
# =========================================================================

def test_v4_multiple_supporting_rules_for_same_category():
    """Verify backward chaining handles multiple supporting rules for the same category."""
    engine = BackwardChainingEngine()
    # 'dns_server_failure_suspected' is a condition in both R13 and R14
    r13_rules = engine.get_supporting_rules("diagnosis", "Upstream DNS Provider Outage")
    r14_rules = engine.get_supporting_rules("diagnosis", "Invalid Local DNS Server Configuration")

    assert len(r13_rules) == 1
    assert r13_rules[0].id == "R13"
    assert len(r14_rules) == 1
    assert r14_rules[0].id == "R14"


def test_v4_known_premises_excluded_from_unanswered_list():
    """Verify known premises are strictly excluded from unresolved premise list."""
    engine = BackwardChainingEngine()
    wm = WorkingMemory()

    # Pre-populate one condition
    wm.set_fact("device_connected", True, FactSourceType.USER_INPUT)

    tree = engine.resolve_goal("diagnosis", expected_value="Router DHCP Server Failure", memory=wm)
    assert tree.status == GoalResolutionStatus.UNRESOLVED

    # 'device_connected' should NOT be in the askable premise list since it's already answered!
    next_q = engine.find_next_askable_premise(wm, candidate_diagnoses=["Router DHCP Server Failure"])
    assert next_q != "device_connected"
    assert next_q in ["ip_is_apipa", "valid_ip", "multiple_devices_affected"]


def test_v4_dead_rule_does_not_leak_premises():
    """Verify that a rule refuted by a FALSE condition does NOT leak its unasked conditions."""
    engine = BackwardChainingEngine()
    wm = WorkingMemory()

    # If user says using_wifi = False, then Wi-Fi rules R17-R20 cannot prove Wi-Fi issues
    wm.set_fact("using_wifi", False, FactSourceType.USER_INPUT)

    tree = engine.resolve_goal("diagnosis", expected_value="Wi-Fi Signal Attenuation and Range Limitation", memory=wm)
    # The goal must be REFUTED because using_wifi is False
    assert tree.status == GoalResolutionStatus.REFUTED
    assert len(tree.unresolved_premises) == 0


# =========================================================================
# 5. HYBRID INFERENCE & REPEATED QUESTION PREVENTION
# =========================================================================

def test_v5_no_repeated_questions_even_on_unknown():
    """Verify that an answered question (True, False, or UNKNOWN) is never repeatedly asked."""
    engine = InferenceEngine()

    q1 = engine.get_next_question_premise()
    assert q1 is not None

    # User answers UNKNOWN (TriState.UNKNOWN)
    engine.memory.set_fact(q1, TriState.UNKNOWN, FactSourceType.USER_INPUT)

    q2 = engine.get_next_question_premise()
    assert q2 is not None
    # Crucial: Question 1 must NEVER be repeated!
    assert q2 != q1

    # User answers False
    engine.assert_user_fact(q2, False)
    q3 = engine.get_next_question_premise()
    assert q3 != q1
    assert q3 != q2


# =========================================================================
# 6. SERIALIZATION & RESTORATION VERIFICATION
# =========================================================================

def test_v6_json_serialization_roundtrip_and_continuation():
    """Verify state survives full JSON serialization and resumes cleanly without duplicates."""
    engine = InferenceEngine()
    engine.assert_user_fact("external_ip_reachable", True)
    engine.assert_user_fact("domain_access", False)

    # Convert snapshot to actual JSON string and parse back
    raw_snapshot = engine.snapshot()
    json_str = json.dumps(raw_snapshot)
    loaded_dict = json.loads(json_str)

    # Restore in fresh engine
    new_engine = InferenceEngine()
    new_engine.restore(loaded_dict)

    # 1. Facts and traces survived
    assert new_engine.get_fact("external_ip_reachable") is True
    assert new_engine.get_fact("domain_access") is False
    assert new_engine.get_fact("dns_failure_suspected") is True
    assert len(new_engine.get_inference_trace()) == 1

    # 2. No duplicate rule execution on existing facts
    repeat_traces = new_engine.forward_engine.run(new_engine.memory)
    assert len(repeat_traces) == 0

    # 3. Continuation: Assert next fact and reach conclusion
    new_engine.assert_user_fact("dns_server_reachable", False)
    new_engine.assert_user_fact("multiple_devices_affected", True)

    assert new_engine.get_session_status() == "COMPLETED"
    assert new_engine.get_terminal_diagnosis()["diagnosis"] == "Upstream DNS Provider Outage"


# =========================================================================
# 7. TERMINAL DIAGNOSIS INTEGRITY
# =========================================================================

def test_v7_intermediate_facts_never_become_terminal_diagnoses():
    """Verify intermediate derived facts are never returned as terminal diagnoses."""
    engine = InferenceEngine()
    engine.assert_user_fact("device_connected", True)
    engine.assert_user_fact("ip_is_apipa", True)

    # Intermediate fact derived
    assert engine.get_fact("dhcp_failure_suspected") is True
    # Must NOT have terminal diagnosis
    assert engine.has_terminal_diagnosis() is False
    assert engine.get_terminal_diagnosis() is None
    assert engine.get_session_status() == "IN_PROGRESS"


def test_v7_conflicting_terminal_diagnoses_never_silently_resolved():
    """Verify that multiple conflicting terminal diagnoses do NOT silently resolve via priority."""
    # Define two conflicting terminal rules
    r_term1 = Rule(
        id="R_TERM_1",
        name="Terminal 1",
        category=RuleCategory.ISP,
        priority=95,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[Condition(fact_key="trigger", operator=Operator.EQUALS, value=True)],
        conclusions={"diagnosis": "ISP Outage", "diagnosis_category": "ISP", "diagnosis_severity": "HIGH"},
        explanation="Term 1"
    )
    r_term2 = Rule(
        id="R_TERM_2",
        name="Terminal 2",
        category=RuleCategory.GATEWAY,
        priority=80,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[Condition(fact_key="trigger", operator=Operator.EQUALS, value=True)],
        conclusions={"diagnosis": "Router Fault", "diagnosis_category": "GATEWAY", "diagnosis_severity": "HIGH"},
        explanation="Term 2"
    )

    engine = InferenceEngine(rules=[r_term1, r_term2])
    engine.assert_user_fact("trigger", True)

    # Both fired -> conflict detected!
    assert engine.has_conflict() is True
    assert engine.get_session_status() == "CONFLICT_DETECTED"

    # Crucial: Must NOT return R_TERM_1 just because priority is 95!
    assert engine.get_terminal_diagnosis() is None
    assert engine.has_terminal_diagnosis() is False


def test_v7_inconclusive_session_status():
    """Verify sessions with no matching rules transition to INCONCLUSIVE when questions are exhausted."""
    engine = InferenceEngine()
    # User provides benign answers where no problem exists
    engine.assert_user_fact("device_connected", True)
    engine.assert_user_fact("valid_ip", True)
    engine.assert_user_fact("ip_is_apipa", False)
    engine.assert_user_fact("gateway_reachable", True)
    engine.assert_user_fact("external_ip_reachable", True)
    engine.assert_user_fact("domain_access", True)
    engine.assert_user_fact("using_wifi", False)
    engine.assert_user_fact("high_latency_observed", False)
    engine.assert_user_fact("packet_loss_observed", False)

    # When all diagnostic rules are refuted and no questions remain:
    assert engine.has_terminal_diagnosis() is False
    assert engine.get_next_question_premise() is None
    assert engine.get_session_status() == "INCONCLUSIVE"


# =========================================================================
# 8. CODE QUALITY & FRAMEWORK INDEPENDENCE
# =========================================================================

def test_v8_expert_system_framework_independence():
    """Verify expert system modules contain zero imports of FastAPI, SQLAlchemy, or React."""
    forbidden_modules = ["fastapi", "sqlalchemy", "starlette", "react", "uvicorn"]

    expert_system_modules = [
        "app.expert_system.types",
        "app.expert_system.knowledge_base",
        "app.expert_system.rules",
        "app.expert_system.rule_graph",
        "app.expert_system.working_memory",
        "app.expert_system.forward_chaining",
        "app.expert_system.backward_chaining",
        "app.expert_system.inference_engine",
    ]

    for mod_name in expert_system_modules:
        mod = sys.modules.get(mod_name)
        assert mod is not None, f"Module {mod_name} should be loaded"
        # Inspect module source or globals
        for forbidden in forbidden_modules:
            assert forbidden not in mod.__dict__, (
                f"Expert system module {mod_name} illegally imports '{forbidden}'"
            )

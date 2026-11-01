import pytest
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
from app.expert_system.working_memory import WorkingMemory
from app.expert_system.backward_chaining import (
    BackwardChainingEngine,
    BackwardChainingCycleError,
)


def test_backward_chaining_supporting_rules_identification():
    """Verify engine correctly identifies all rules supporting a goal, sorted by priority."""
    engine = BackwardChainingEngine()

    # Category A: 'dhcp_failure_suspected' is concluded by R01
    r_dhcp = engine.get_supporting_rules("dhcp_failure_suspected", True)
    assert len(r_dhcp) == 1
    assert r_dhcp[0].id == "R01"

    # Terminal diagnosis 'Router DHCP Server Failure' is concluded by R04
    r_term = engine.get_supporting_rules("diagnosis", "Router DHCP Server Failure")
    assert len(r_term) == 1
    assert r_term[0].id == "R04"


def test_backward_chaining_unresolved_goal_derivation():
    """Verify that an unresolved goal recursively identifies needed leaf askable premises."""
    engine = BackwardChainingEngine()
    wm = WorkingMemory()

    # Resolve goal for 'Router DHCP Server Failure' with empty working memory
    tree = engine.resolve_goal("diagnosis", expected_value="Router DHCP Server Failure", memory=wm)

    assert tree.status == GoalResolutionStatus.UNRESOLVED
    assert len(tree.supporting_rules) == 1
    # Needs: R04 requires dhcp_server_unavailable and multiple_devices_affected
    # dhcp_server_unavailable (R03) requires dhcp_failure_suspected and valid_ip
    # dhcp_failure_suspected (R01) requires device_connected and ip_is_apipa
    unresolved = tree.unresolved_premises
    assert "device_connected" in unresolved
    assert "ip_is_apipa" in unresolved
    assert "valid_ip" in unresolved
    assert "multiple_devices_affected" in unresolved


def test_backward_chaining_proven_and_refuted_states():
    """Verify goal resolution correctly marks PROVEN and REFUTED."""
    engine = BackwardChainingEngine()
    wm = WorkingMemory()

    # Case 1: Refuted by conflicting user fact
    # R11 requires external_ip_reachable == True and domain_access == False
    wm.set_fact("external_ip_reachable", False, FactSourceType.USER_INPUT)
    tree_refuted = engine.resolve_goal("dns_failure_suspected", expected_value=True, memory=wm)
    assert tree_refuted.status == GoalResolutionStatus.REFUTED

    # Case 2: Proven when conditions are satisfied
    wm2 = WorkingMemory()
    wm2.set_fact("external_ip_reachable", True, FactSourceType.USER_INPUT)
    wm2.set_fact("domain_access", False, FactSourceType.USER_INPUT)
    tree_proven = engine.resolve_goal("dns_failure_suspected", expected_value=True, memory=wm2)
    assert tree_proven.status == GoalResolutionStatus.PROVEN


def test_backward_chaining_cycle_detection():
    """Verify engine raises BackwardChainingCycleError when rules have circular goal dependencies."""
    r_cycle1 = Rule(
        id="R_CY1",
        name="Cycle 1",
        category=RuleCategory.DNS,
        priority=80,
        conditions=[Condition(fact_key="fact_beta", operator=Operator.EQUALS, value=True)],
        conclusions={"fact_alpha": True},
        explanation="Cycle 1"
    )
    r_cycle2 = Rule(
        id="R_CY2",
        name="Cycle 2",
        category=RuleCategory.DNS,
        priority=80,
        conditions=[Condition(fact_key="fact_alpha", operator=Operator.EQUALS, value=True)],
        conclusions={"fact_beta": True},
        explanation="Cycle 2"
    )

    engine = BackwardChainingEngine(rules=[r_cycle1, r_cycle2])
    wm = WorkingMemory()

    with pytest.raises(BackwardChainingCycleError) as exc_info:
        engine.resolve_goal("fact_alpha", expected_value=True, memory=wm)

    assert "Cycle detected" in str(exc_info.value)


def test_backward_chaining_dynamic_question_selection():
    """Verify find_next_askable_premise dynamically returns the next most informative premise."""
    engine = BackwardChainingEngine()
    wm = WorkingMemory()

    # Empty memory -> should suggest an initial premise for the highest priority hypothesis
    next_fact = engine.find_next_askable_premise(wm)
    assert next_fact is not None
    assert next_fact in engine.user_facts

    # If user provides this fact, next premise should progress
    wm.set_fact(next_fact, True, FactSourceType.USER_INPUT)
    next_fact_2 = engine.find_next_askable_premise(wm)
    assert next_fact_2 is not None
    assert next_fact_2 != next_fact


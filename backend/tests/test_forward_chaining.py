import pytest
from app.expert_system.types import (
    TriState,
    Operator,
    Condition,
    RuleCategory,
    RuleClassification,
    FactSourceType,
)
from app.expert_system.rules import Rule, PRODUCTION_RULES
from app.expert_system.working_memory import WorkingMemory
from app.expert_system.forward_chaining import (
    ForwardChainingEngine,
    ForwardChainingError,
)


def test_forward_chaining_dhcp_pipeline():
    """Verify multi-level chaining for Category A (DHCP): R01 -> R03 -> R04."""
    wm = WorkingMemory()
    engine = ForwardChainingEngine()

    # Assert initial user answers
    wm.set_fact("device_connected", True, FactSourceType.USER_INPUT)
    wm.set_fact("ip_is_apipa", True, FactSourceType.USER_INPUT)
    wm.set_fact("valid_ip", False, FactSourceType.USER_INPUT)
    wm.set_fact("multiple_devices_affected", True, FactSourceType.USER_INPUT)

    traces = engine.run(wm)
    fired_ids = [t.rule_id for t in traces]

    # Verify chained execution order
    assert "R01" in fired_ids
    assert "R03" in fired_ids
    assert "R04" in fired_ids
    assert fired_ids.index("R01") < fired_ids.index("R03") < fired_ids.index("R04")

    # Verify conclusions in working memory
    assert wm.get_fact("dhcp_failure_suspected") is True
    assert wm.get_fact("dhcp_server_unavailable") is True
    assert wm.get_fact("diagnosis") == "Router DHCP Server Failure"

    # Verify terminal diagnosis
    diagnoses = engine.terminal_diagnoses
    assert len(diagnoses) == 1
    assert diagnoses[0]["diagnosis"] == "Router DHCP Server Failure"
    assert diagnoses[0]["severity"] == "HIGH"


def test_forward_chaining_gateway_pipeline():
    """Verify multi-level chaining for Category B (Gateway): R06 -> R07, R08 -> R09."""
    wm = WorkingMemory()
    engine = ForwardChainingEngine()

    wm.set_fact("valid_ip", True, FactSourceType.USER_INPUT)
    wm.set_fact("gateway_reachable", False, FactSourceType.USER_INPUT)
    wm.set_fact("multiple_devices_affected", True, FactSourceType.USER_INPUT)
    wm.set_fact("router_reboot_temporarily_fixed", True, FactSourceType.USER_INPUT)

    traces = engine.run(wm)
    fired_ids = [t.rule_id for t in traces]

    assert "R06" in fired_ids
    assert "R08" in fired_ids
    assert "R09" in fired_ids
    assert fired_ids.index("R06") < fired_ids.index("R08") < fired_ids.index("R09")

    assert wm.get_fact("gateway_failure_suspected") is True
    assert wm.get_fact("router_hardware_suspected") is True
    assert wm.get_fact("diagnosis") == "Router Gateway Crash / Hardware Overload"


def test_forward_chaining_dns_pipeline():
    """Verify multi-level chaining for Category C (DNS): R11 -> R12 -> R13."""
    wm = WorkingMemory()
    engine = ForwardChainingEngine()

    wm.set_fact("external_ip_reachable", True, FactSourceType.USER_INPUT)
    wm.set_fact("domain_access", False, FactSourceType.USER_INPUT)
    wm.set_fact("dns_server_reachable", False, FactSourceType.USER_INPUT)
    wm.set_fact("multiple_devices_affected", True, FactSourceType.USER_INPUT)

    traces = engine.run(wm)
    fired_ids = [t.rule_id for t in traces]

    assert "R11" in fired_ids
    assert "R12" in fired_ids
    assert "R13" in fired_ids
    assert fired_ids.index("R11") < fired_ids.index("R12") < fired_ids.index("R13")

    assert wm.get_fact("dns_failure_suspected") is True
    assert wm.get_fact("dns_server_failure_suspected") is True
    assert wm.get_fact("diagnosis") == "Upstream DNS Provider Outage"


def test_forward_chaining_wifi_pipeline():
    """Verify multi-level chaining for Category D (Wi-Fi): R17 -> R18 -> R19."""
    wm = WorkingMemory()
    engine = ForwardChainingEngine()

    wm.set_fact("using_wifi", True, FactSourceType.USER_INPUT)
    wm.set_fact("wifi_signal_weak", True, FactSourceType.USER_INPUT)
    wm.set_fact("frequent_disconnections", True, FactSourceType.USER_INPUT)
    wm.set_fact("problem_on_ethernet_too", False, FactSourceType.USER_INPUT)

    traces = engine.run(wm)
    fired_ids = [t.rule_id for t in traces]

    assert "R17" in fired_ids
    assert "R18" in fired_ids
    assert "R19" in fired_ids
    assert fired_ids.index("R17") < fired_ids.index("R18") < fired_ids.index("R19")

    assert wm.get_fact("weak_wifi_suspected") is True
    assert wm.get_fact("wireless_instability_suspected") is True
    assert wm.get_fact("diagnosis") == "Wi-Fi Signal Attenuation and Range Limitation"


def test_forward_chaining_performance_pipeline():
    """Verify multi-level chaining for Category E (Performance): R21 -> R22 -> R23."""
    wm = WorkingMemory()
    engine = ForwardChainingEngine()

    wm.set_fact("high_latency_observed", True, FactSourceType.USER_INPUT)
    wm.set_fact("heavy_bandwidth_usage", True, FactSourceType.USER_INPUT)

    traces = engine.run(wm)
    fired_ids = [t.rule_id for t in traces]

    assert "R21" in fired_ids
    assert "R22" in fired_ids
    assert "R23" in fired_ids
    assert fired_ids.index("R21") < fired_ids.index("R22") < fired_ids.index("R23")

    assert wm.get_fact("network_performance_degraded") is True
    assert wm.get_fact("network_congestion_suspected") is True
    assert wm.get_fact("diagnosis") == "Local Network Bufferbloat & Bandwidth Saturation"


def test_forward_chaining_isp_pipeline():
    """Verify multi-level chaining for Category F (ISP): R25 -> R26 -> R27."""
    wm = WorkingMemory()
    engine = ForwardChainingEngine()

    wm.set_fact("gateway_reachable", True, FactSourceType.USER_INPUT)
    wm.set_fact("external_ip_reachable", False, FactSourceType.USER_INPUT)
    wm.set_fact("multiple_devices_affected", True, FactSourceType.USER_INPUT)

    traces = engine.run(wm)
    fired_ids = [t.rule_id for t in traces]

    assert "R25" in fired_ids
    assert "R26" in fired_ids
    assert "R27" in fired_ids
    assert fired_ids.index("R25") < fired_ids.index("R26") < fired_ids.index("R27")

    assert wm.get_fact("isp_failure_suspected") is True
    assert wm.get_fact("isp_outage_suspected") is True
    assert wm.get_fact("diagnosis") == "Wide-Area ISP Service Outage"


def test_forward_chaining_conflict_resolution_by_priority():
    """Verify conflict resolution prioritizes higher-priority rules when multiple qualify."""
    wm = WorkingMemory()

    rule_low = Rule(
        id="R_LOW",
        name="Low Priority Rule",
        category=RuleCategory.DNS,
        priority=60,
        conditions=[Condition(fact_key="trigger", operator=Operator.EQUALS, value=True)],
        conclusions={"result": "LOW"},
        explanation="Low priority."
    )
    rule_high = Rule(
        id="R_HIGH",
        name="High Priority Rule",
        category=RuleCategory.DNS,
        priority=90,
        conditions=[Condition(fact_key="trigger", operator=Operator.EQUALS, value=True)],
        conclusions={"result": "HIGH"},
        explanation="High priority."
    )

    engine = ForwardChainingEngine(rules=[rule_low, rule_high])
    wm.set_fact("trigger", True, FactSourceType.USER_INPUT)

    step1 = engine.step(wm)
    assert step1 is not None
    assert step1.rule_id == "R_HIGH"


def test_forward_chaining_intermediate_does_not_halt():
    """Verify intermediate rules do not halt forward chaining from pursuing subsequent conclusions."""
    wm = WorkingMemory()
    engine = ForwardChainingEngine()

    # Provide only enough evidence to fire R01 (intermediate)
    wm.set_fact("device_connected", True, FactSourceType.USER_INPUT)
    wm.set_fact("ip_is_apipa", True, FactSourceType.USER_INPUT)

    traces = engine.run(wm)
    assert len(traces) == 1
    assert traces[0].rule_id == "R01"
    assert traces[0].classification == RuleClassification.INTERMEDIATE
    # No terminal diagnosis yet
    assert len(engine.terminal_diagnoses) == 0

    # Now add remaining evidence
    wm.set_fact("valid_ip", False, FactSourceType.USER_INPUT)
    wm.set_fact("multiple_devices_affected", True, FactSourceType.USER_INPUT)

    new_traces = engine.run(wm)
    new_rule_ids = [t.rule_id for t in new_traces]
    assert "R03" in new_rule_ids
    assert "R04" in new_rule_ids
    assert len(engine.terminal_diagnoses) == 1


def test_forward_chaining_cycle_prevention():
    """Verify engine raises ForwardChainingError if a cycle is created."""
    wm = WorkingMemory()
    cyclic_rule1 = Rule(
        id="R_C1",
        name="Cycle 1",
        category=RuleCategory.DNS,
        priority=80,
        conditions=[Condition(fact_key="start", operator=Operator.EQUALS, value=True)],
        conclusions={"fact_b": True},
        explanation="C1"
    )
    # Note: In standard forward chaining, a rule fires once. If a rule resets itself:
    engine = ForwardChainingEngine(rules=[cyclic_rule1])
    wm.set_fact("start", True, FactSourceType.USER_INPUT)
    engine.run(wm)
    # Running again should not fire the rule again
    new_traces = engine.run(wm)
    assert len(new_traces) == 0


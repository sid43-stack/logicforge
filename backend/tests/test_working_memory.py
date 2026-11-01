import pytest
from app.expert_system.types import TriState, FactSourceType
from app.expert_system.working_memory import WorkingMemory, ContradictionError


def test_working_memory_tristate_defaults():
    """Verify that unasserted facts return UNKNOWN, never FALSE (crucial constraint)."""
    wm = WorkingMemory()
    assert wm.get_tristate("gateway_reachable") == TriState.UNKNOWN
    assert wm.get_fact("gateway_reachable") is None
    assert wm.contains("gateway_reachable") is False


def test_working_memory_assertion_and_retrieval():
    """Verify storing facts with different sources and retrieving them."""
    wm = WorkingMemory()

    # User-provided boolean fact
    wm.set_fact("device_connected", True, FactSourceType.USER_INPUT, "USER")
    assert wm.get_fact("device_connected") is True
    assert wm.get_tristate("device_connected") == TriState.TRUE
    assert wm.contains("device_connected") is True

    # Rule-derived fact
    wm.set_fact("dhcp_failure_suspected", True, FactSourceType.RULE_DERIVED, "R01")
    assert wm.get_fact("dhcp_failure_suspected") is True

    # Check source segregation
    user_facts = wm.get_facts_by_source(FactSourceType.USER_INPUT)
    derived_facts = wm.get_facts_by_source(FactSourceType.RULE_DERIVED)

    assert "device_connected" in user_facts
    assert "dhcp_failure_suspected" not in user_facts
    assert "dhcp_failure_suspected" in derived_facts
    assert "device_connected" not in derived_facts


def test_working_memory_change_history():
    """Verify that working memory maintains an ordered audit trail of all mutations."""
    wm = WorkingMemory()
    wm.set_fact("valid_ip", True, FactSourceType.USER_INPUT, "USER")
    wm.set_fact("ip_is_apipa", False, FactSourceType.USER_INPUT, "USER")

    history = wm.get_change_history()
    assert len(history) == 2
    assert history[0]["key"] == "valid_ip"
    assert history[0]["value"] is True
    assert history[0]["action"] == "ASSERT"
    assert history[1]["key"] == "ip_is_apipa"
    assert history[1]["value"] is False


def test_working_memory_contradiction_detection():
    """Verify that setting an opposing fact raises ContradictionError and records conflict."""
    wm = WorkingMemory()
    wm.set_fact("gateway_reachable", True, FactSourceType.USER_INPUT, "USER")

    # Attempting to assert False for an already established True fact
    with pytest.raises(ContradictionError) as exc_info:
        wm.set_fact("gateway_reachable", False, FactSourceType.USER_INPUT, "USER")

    assert "Contradiction" in str(exc_info.value)
    assert wm.has_conflicts() is True
    conflicts = wm.get_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0]["key"] == "gateway_reachable"


def test_working_memory_serialization_and_restoration():
    """Verify full fidelity JSON snapshot serialization and restoration."""
    wm = WorkingMemory()
    wm.set_fact("device_connected", True, FactSourceType.USER_INPUT, "USER")
    wm.set_fact("gateway_reachable", False, FactSourceType.USER_INPUT, "USER")
    wm.set_fact("gateway_failure_suspected", True, FactSourceType.RULE_DERIVED, "R06")

    snapshot = wm.to_dict()
    assert "entries" in snapshot
    assert "history" in snapshot
    assert len(snapshot["entries"]) == 3
    assert len(snapshot["history"]) == 3

    # Restore in a fresh instance
    restored_wm = WorkingMemory.from_dict(snapshot)
    assert restored_wm.get_fact("device_connected") is True
    assert restored_wm.get_fact("gateway_reachable") is False
    assert restored_wm.get_fact("gateway_failure_suspected") is True
    assert restored_wm.get_tristate("device_connected") == TriState.TRUE
    assert restored_wm.get_fact_entry("gateway_failure_suspected").source_id == "R06"
    assert len(restored_wm.get_change_history()) == 3


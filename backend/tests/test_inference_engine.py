import pytest
from app.expert_system.types import TriState
from app.expert_system.inference_engine import InferenceEngine


def test_inference_engine_category_a_dhcp():
    """Test full inference session for Category A: Router DHCP Server Failure."""
    engine = InferenceEngine()
    assert engine.get_session_status() == "IN_PROGRESS"

    # Step 1: Device connected
    engine.assert_user_fact("device_connected", True)
    assert engine.has_terminal_diagnosis() is False

    # Step 2: IP is APIPA (169.254) -> fires R01 (Intermediate)
    t1 = engine.assert_user_fact("ip_is_apipa", True)
    assert any(step.rule_id == "R01" for step in t1)
    assert engine.get_fact("dhcp_failure_suspected") is True
    # Still IN_PROGRESS because R01 is intermediate!
    assert engine.get_session_status() == "IN_PROGRESS"

    # Step 3: valid_ip is False -> fires R03 (Intermediate)
    t2 = engine.assert_user_fact("valid_ip", False)
    assert any(step.rule_id == "R03" for step in t2)
    assert engine.get_fact("dhcp_server_unavailable") is True
    assert engine.get_session_status() == "IN_PROGRESS"

    # Step 4: multiple devices affected -> fires R04 (Terminal)
    t3 = engine.assert_user_fact("multiple_devices_affected", True)
    assert any(step.rule_id == "R04" for step in t3)
    assert engine.has_terminal_diagnosis() is True
    assert engine.get_session_status() == "COMPLETED"

    diag = engine.get_terminal_diagnosis()
    assert diag is not None
    assert diag["diagnosis"] == "Router DHCP Server Failure"
    assert diag["category"] == "IP_DHCP"


def test_inference_engine_category_b_gateway():
    """Test full inference session for Category B: Router Gateway Crash."""
    engine = InferenceEngine()

    engine.assert_user_fact("valid_ip", True)
    engine.assert_user_fact("gateway_reachable", False)  # Fires R06, R07
    engine.assert_user_fact("multiple_devices_affected", True)  # Fires R08
    engine.assert_user_fact("router_reboot_temporarily_fixed", True)  # Fires R09 (Terminal)

    assert engine.get_session_status() == "COMPLETED"
    diag = engine.get_terminal_diagnosis()
    assert diag["diagnosis"] == "Router Gateway Crash / Hardware Overload"
    assert diag["category"] == "GATEWAY"


def test_inference_engine_category_c_dns():
    """Test full inference session for Category C: Upstream DNS Provider Outage."""
    engine = InferenceEngine()

    engine.assert_user_fact("external_ip_reachable", True)
    engine.assert_user_fact("domain_access", False)  # Fires R11
    engine.assert_user_fact("dns_server_reachable", False)  # Fires R12
    engine.assert_user_fact("multiple_devices_affected", True)  # Fires R13 (Terminal)

    assert engine.get_session_status() == "COMPLETED"
    diag = engine.get_terminal_diagnosis()
    assert diag["diagnosis"] == "Upstream DNS Provider Outage"
    assert diag["category"] == "DNS"


def test_inference_engine_category_d_wifi():
    """Test full inference session for Category D: Wi-Fi Signal Attenuation."""
    engine = InferenceEngine()

    engine.assert_user_fact("using_wifi", True)
    engine.assert_user_fact("wifi_signal_weak", True)  # Fires R17
    engine.assert_user_fact("frequent_disconnections", True)  # Fires R18
    engine.assert_user_fact("problem_on_ethernet_too", False)  # Fires R19 (Terminal)

    assert engine.get_session_status() == "COMPLETED"
    diag = engine.get_terminal_diagnosis()
    assert diag["diagnosis"] == "Wi-Fi Signal Attenuation and Range Limitation"
    assert diag["category"] == "WIFI"


def test_inference_engine_category_e_performance():
    """Test full inference session for Category E: Local Bufferbloat Congestion."""
    engine = InferenceEngine()

    engine.assert_user_fact("high_latency_observed", True)  # Fires R21
    engine.assert_user_fact("heavy_bandwidth_usage", True)  # Fires R22, R23 (Terminal)

    assert engine.get_session_status() == "COMPLETED"
    diag = engine.get_terminal_diagnosis()
    assert diag["diagnosis"] == "Local Network Bufferbloat & Bandwidth Saturation"
    assert diag["category"] == "PERFORMANCE"


def test_inference_engine_category_f_isp():
    """Test full inference session for Category F: Wide-Area ISP Outage."""
    engine = InferenceEngine()

    engine.assert_user_fact("gateway_reachable", True)
    engine.assert_user_fact("external_ip_reachable", False)  # Fires R25
    engine.assert_user_fact("multiple_devices_affected", True)  # Fires R26, R27 (Terminal)

    assert engine.get_session_status() == "COMPLETED"
    diag = engine.get_terminal_diagnosis()
    assert diag["diagnosis"] == "Wide-Area ISP Service Outage"
    assert diag["category"] == "ISP"


def test_inference_engine_snapshot_and_restoration():
    """Verify that complete InferenceEngine state is restored accurately from snapshot."""
    engine = InferenceEngine()
    engine.assert_user_fact("gateway_reachable", True)
    engine.assert_user_fact("external_ip_reachable", False)

    snapshot_data = engine.snapshot()

    # Create fresh engine and restore
    restored_engine = InferenceEngine()
    restored_engine.restore(snapshot_data)

    assert restored_engine.get_fact("gateway_reachable") is True
    assert restored_engine.get_fact("external_ip_reachable") is False
    assert restored_engine.get_fact("isp_failure_suspected") is True
    assert len(restored_engine.get_inference_trace()) == len(engine.get_inference_trace())

    # Assert remaining fact in restored engine -> completes diagnosis
    restored_engine.assert_user_fact("multiple_devices_affected", True)
    assert restored_engine.get_session_status() == "COMPLETED"
    assert restored_engine.get_terminal_diagnosis()["diagnosis"] == "Wide-Area ISP Service Outage"


def test_inference_engine_contradiction_handling():
    """Verify that conflicting user evidence puts session into CONFLICT_DETECTED state."""
    engine = InferenceEngine()
    engine.assert_user_fact("gateway_reachable", True)

    try:
        # Directly contradictory assertion
        engine.assert_user_fact("gateway_reachable", False)
    except Exception:
        pass

    assert engine.has_conflict() is True
    assert engine.get_session_status() == "CONFLICT_DETECTED"
    assert len(engine.get_conflicts()) > 0


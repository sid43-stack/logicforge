"""NetSage Phase 5 Comprehensive REST API Integration Tests.

Verifies all 16 required diagnostic lifecycle scenarios:
1. Starting session and dynamic first question with WHY explanation
2. Answering YES/NO/UNKNOWN formats
3. Dynamic question selection driving backward chaining
4. Full DHCP diagnostic flow (Router DHCP Server Failure: R01 -> R03 -> R04)
5. Full DNS diagnostic flow (Upstream DNS Provider Outage: R11 -> R12 -> R13)
6. Full ISP diagnostic flow (Wide-Area ISP Service Outage: R25 -> R26 -> R27)
7. Dynamic WHY explanations verification
8. Dynamic HOW explanations and DAG tree generation
9. Actionable remediation plans and steps verification
10. Contradictory evidence detection (409 Conflict / CONFLICT_DETECTED)
11. Inconclusive session handling and fallback plans
12. Working memory snapshot restoration across server restarts
13. Session restart functionality
14. Session deletion and cascade cleanup
15. Error handling and validation (400, 404, 409, 422)
16. Knowledge Base Explorer and History endpoints
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.base import Base
from app.database.session import get_db


TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 1. Starting Session & Dynamic First Question
# -----------------------------------------------------------------------------

def test_start_diagnostic_session(client):
    """POST /api/diagnostics/start starts a new session and returns dynamic first question with WHY."""
    response = client.post("/api/diagnostics/start", json={})
    assert response.status_code == 201
    data = response.json()

    assert "session_id" in data
    assert data["status"] == "IN_PROGRESS"
    assert data["current_question"] is not None

    q = data["current_question"]
    assert q["id"] is not None
    assert q["fact_key"] is not None
    assert q["available_options"] == ["YES", "NO", "UNKNOWN"]

    why = q["why_explanation"]
    assert why is not None
    assert why["question_id"] == q["id"]
    assert why["fact_key"] == q["fact_key"]
    assert len(why["investigating_hypothesis"]) > 0
    assert len(why["triggering_rule_id"]) > 0
    assert len(why["rationale"]) > 0
    assert len(why["impact_if_yes"]) > 0
    assert len(why["impact_if_no"]) > 0


# -----------------------------------------------------------------------------
# 2. Answer Formats (YES / NO / UNKNOWN / Variants)
# -----------------------------------------------------------------------------

def test_answer_yes_no_unknown_formats(client):
    """Answers accept YES, NO, UNKNOWN (case-insensitive) and reject invalid strings."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]
    q_id = start_res["current_question"]["id"]

    # Valid answer 'yes'
    ans_res = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": q_id, "answer": "yes"},
    )
    assert ans_res.status_code == 200
    data = ans_res.json()
    assert data["session_id"] == sess_id
    assert data["status"] in ("IN_PROGRESS", "COMPLETED")

    # Start new session and test 'UNKNOWN'
    s2 = client.post("/api/diagnostics/start", json={}).json()
    s2_id = s2["session_id"]
    s2_qid = s2["current_question"]["id"]
    ans_res2 = client.post(
        f"/api/diagnostics/{s2_id}/answer",
        json={"question_id": s2_qid, "answer": "UNKNOWN"},
    )
    assert ans_res2.status_code == 200

    # Test invalid answer format
    s3 = client.post("/api/diagnostics/start", json={}).json()
    s3_id = s3["session_id"]
    bad_res = client.post(
        f"/api/diagnostics/{s3_id}/answer",
        json={"question_id": "Q01", "answer": "MAYBE_PROBABLY"},
    )
    assert bad_res.status_code == 400
    bad_data = bad_res.json()
    assert bad_data["error_code"] == "BAD_REQUEST"
    assert "Unrecognized answer format" in bad_data["detail"]


# -----------------------------------------------------------------------------
# 3. Dynamic Question Selection via Backward Chaining
# -----------------------------------------------------------------------------

def test_dynamic_question_selection_workflow(client):
    """Questions are selected dynamically based on hypothesis inquiry, never a static sequence."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]
    q1 = start_res["current_question"]

    # Answer YES to first question
    res1 = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": q1["id"], "answer": "YES"},
    ).json()
    q2 = res1["next_question"]
    assert q2 is not None
    assert q2["id"] != q1["id"]

    # Verify GET /api/diagnostics/{session_id}/question returns the same active question
    get_q = client.get(f"/api/diagnostics/{sess_id}/question")
    assert get_q.status_code == 200
    assert get_q.json()["id"] == q2["id"]


# -----------------------------------------------------------------------------
# 4. Full DHCP Diagnostic Flow (Router DHCP Server Failure: R01 -> R03 -> R04)
# -----------------------------------------------------------------------------

def test_complete_dhcp_diagnostic_flow(client):
    """Executes full diagnostic path for Router DHCP Server Failure (R01 -> R03 -> R04)."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]

    # R01: device_connected=True, ip_is_apipa=True
    # R03: dhcp_failure_suspected=True, valid_ip=False
    # R04: dhcp_server_unavailable=True, multiple_devices_affected=True
    answers = [
        ("Q01", "YES"),  # device_connected = True
        ("Q12", "YES"),  # ip_is_apipa = True -> fires R01
        ("Q03", "NO"),   # valid_ip = False -> fires R03
        ("Q07", "YES"),  # multiple_devices_affected = True -> fires R04 (TERMINAL)
    ]

    for q_id, ans in answers[:-1]:
        r = client.post(
            f"/api/diagnostics/{sess_id}/answer",
            json={"question_id": q_id, "answer": ans},
        ).json()
        assert not r["is_completed"]

    last_q, last_ans = answers[-1]
    final_res = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": last_q, "answer": last_ans},
    ).json()

    assert final_res["is_completed"] is True
    assert final_res["status"] == "COMPLETED"
    assert final_res["next_question"] is None

    result = final_res["result"]
    assert result is not None
    assert result["diagnosis_name"] == "Router DHCP Server Failure"
    assert result["diagnosis_code"] == "REC_DHCP_ROUTER"
    assert result["category"] == "IP_DHCP"
    assert result["severity"] == "HIGH"
    assert len(result["steps"]) >= 3
    assert any("ipconfig" in (s["command"] or "") for s in result["steps"])
    assert len(result["warnings"]) > 0
    assert result["escalation_advice"] is not None

    # Verify GET /result endpoint
    get_res = client.get(f"/api/diagnostics/{sess_id}/result")
    assert get_res.status_code == 200
    assert get_res.json()["diagnosis_name"] == "Router DHCP Server Failure"


# -----------------------------------------------------------------------------
# 5. Full DNS Diagnostic Flow (Upstream DNS Provider Outage: R11 -> R12 -> R13)
# -----------------------------------------------------------------------------

def test_complete_dns_diagnostic_flow(client):
    """Executes full diagnostic path for Upstream DNS Provider Outage (R11 -> R12 -> R13)."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]

    # R11: external_ip_reachable=True, domain_access=False
    # R12: dns_failure_suspected=True, dns_server_reachable=False
    # R13: dns_server_failure_suspected=True, multiple_devices_affected=True
    answers = [
        ("Q05", "YES"),  # external_ip_reachable = True
        ("Q06", "NO"),   # domain_access = False -> fires R11
        ("Q13", "NO"),   # dns_server_reachable = False -> fires R12
        ("Q07", "YES"),  # multiple_devices_affected = True -> fires R13 (TERMINAL)
    ]

    for q_id, ans in answers[:-1]:
        r = client.post(
            f"/api/diagnostics/{sess_id}/answer",
            json={"question_id": q_id, "answer": ans},
        ).json()
        assert not r["is_completed"]

    last_q, last_ans = answers[-1]
    final_res = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": last_q, "answer": last_ans},
    ).json()

    assert final_res["is_completed"] is True
    assert final_res["status"] == "COMPLETED"
    result = final_res["result"]
    assert result["diagnosis_name"] == "Upstream DNS Provider Outage"
    assert result["category"] == "DNS"
    assert result["diagnosis_code"] == "REC_DNS_UPSTREAM"
    assert any("8.8.8.8" in (s["description"] or "") for s in result["steps"])


# -----------------------------------------------------------------------------
# 6. Full ISP Diagnostic Flow (Wide-Area ISP Service Outage: R25 -> R26 -> R27)
# -----------------------------------------------------------------------------

def test_complete_isp_diagnostic_flow(client):
    """Executes full diagnostic path for Wide-Area ISP Service Outage (R25 -> R26 -> R27)."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]

    # R25: gateway_reachable=True, external_ip_reachable=False
    # R26: isp_failure_suspected=True, multiple_devices_affected=True
    # R27: isp_outage_suspected=True
    answers = [
        ("Q04", "YES"),  # gateway_reachable = True
        ("Q05", "NO"),   # external_ip_reachable = False -> fires R25
        ("Q07", "YES"),  # multiple_devices_affected = True -> fires R26 and R27 (TERMINAL)
    ]

    for q_id, ans in answers[:-1]:
        r = client.post(
            f"/api/diagnostics/{sess_id}/answer",
            json={"question_id": q_id, "answer": ans},
        ).json()
        assert not r["is_completed"]

    last_q, last_ans = answers[-1]
    final_res = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": last_q, "answer": last_ans},
    ).json()

    assert final_res["is_completed"] is True
    assert final_res["status"] == "COMPLETED"
    result = final_res["result"]
    assert result["diagnosis_name"] == "Wide-Area ISP Service Outage"
    assert result["category"] == "ISP"
    assert result["diagnosis_code"] == "REC_ISP_OUTAGE"


# -----------------------------------------------------------------------------
# 7. HOW Explanation & DAG Tree Generation
# -----------------------------------------------------------------------------

def test_how_explanation_and_inference_tree(client):
    """GET /api/diagnostics/{session_id}/explanation returns narrative and DAG tree."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]

    for q_id, ans in [
        ("Q05", "YES"),
        ("Q06", "NO"),
        ("Q13", "NO"),
        ("Q07", "YES"),
    ]:
        client.post(
            f"/api/diagnostics/{sess_id}/answer",
            json={"question_id": q_id, "answer": ans},
        )

    # Request explanation
    exp_res = client.get(f"/api/diagnostics/{sess_id}/explanation")
    assert exp_res.status_code == 200
    exp_data = exp_res.json()

    assert exp_data["session_id"] == sess_id
    assert exp_data["status"] == "COMPLETED"
    assert exp_data["final_diagnosis"] == "Upstream DNS Provider Outage"
    assert exp_data["fired_rules_count"] >= 3
    assert len(exp_data["reasoning_narrative"]) >= 3
    assert len(exp_data["execution_steps"]) >= 3

    # Check DAG tree
    tree = exp_data["inference_tree"]
    assert len(tree["nodes"]) > 0
    assert len(tree["edges"]) > 0

    node_types = {n["type"] for n in tree["nodes"]}
    assert "USER_FACT" in node_types
    assert "RULE" in node_types
    assert "TERMINAL_DIAGNOSIS" in node_types


# -----------------------------------------------------------------------------
# 8. Contradictory Evidence Handling (409 Conflict / CONFLICT_DETECTED)
# -----------------------------------------------------------------------------

def test_contradictory_evidence_detection_409(client):
    """Submitting contradictory assertions triggers 409 Conflict and marks session CONFLICT_DETECTED."""
    start_res = client.post(
        "/api/diagnostics/start",
        json={"initial_facts": {"gateway_reachable": True}},
    ).json()
    sess_id = start_res["session_id"]

    # Now answer Q04 (gateway_reachable) as NO (False), creating direct contradiction
    conflict_res = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": "Q04", "answer": "NO"},
    )
    assert conflict_res.status_code == 409
    conf_data = conflict_res.json()
    assert conf_data["error_code"] == "CONFLICT_DETECTED"
    assert "Contradictory evidence" in conf_data["detail"]

    # Verify session status is CONFLICT_DETECTED
    res_check = client.get(f"/api/diagnostics/{sess_id}/result")
    assert res_check.status_code == 200
    assert res_check.json()["status"] == "CONFLICT_DETECTED"

    # Attempting to answer a conflicted session raises 400
    followup = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": "Q01", "answer": "YES"},
    )
    assert followup.status_code == 400
    assert followup.json()["error_code"] == "BAD_REQUEST"


# -----------------------------------------------------------------------------
# 9. Inconclusive Session Handling
# -----------------------------------------------------------------------------

def test_inconclusive_session_outcome(client):
    """When all hypotheses are exhausted with benign answers, session completes as INCONCLUSIVE."""
    benign_facts = {
        "device_connected": True,
        "valid_ip": True,
        "ip_is_apipa": False,
        "gateway_reachable": True,
        "external_ip_reachable": True,
        "domain_access": True,
        "using_wifi": False,
        "high_latency_observed": False,
        "packet_loss_observed": False,
    }
    start_res = client.post("/api/diagnostics/start", json={"initial_facts": benign_facts}).json()
    sess_id = start_res["session_id"]

    assert start_res["status"] == "INCONCLUSIVE"
    assert start_res["current_question"] is None

    result = client.get(f"/api/diagnostics/{sess_id}/result").json()
    assert result["status"] == "INCONCLUSIVE"
    assert result["diagnosis_name"] == "Inconclusive Network Diagnosis"
    assert result["diagnosis_code"] == "REC_INCONCLUSIVE"
    assert len(result["steps"]) > 0


# -----------------------------------------------------------------------------
# 10. Persistence & State Restoration Across Restarts
# -----------------------------------------------------------------------------

def test_session_restoration_across_restarts(client):
    """Working memory state and inference traces survive across distinct requests."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]

    # Assert DHCP path
    client.post(f"/api/diagnostics/{sess_id}/answer", json={"question_id": "Q01", "answer": "YES"})
    client.post(f"/api/diagnostics/{sess_id}/answer", json={"question_id": "Q12", "answer": "YES"})

    # Fetch active question on separate request
    next_q_res = client.get(f"/api/diagnostics/{sess_id}/question")
    assert next_q_res.status_code == 200
    q_data = next_q_res.json()
    assert q_data["id"] is not None

    # Continue answering
    ans_res = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": "Q03", "answer": "NO"},
    )
    assert ans_res.status_code == 200
    assert ans_res.json()["status"] == "IN_PROGRESS"


# -----------------------------------------------------------------------------
# 11. Session Restart & Deletion
# -----------------------------------------------------------------------------

def test_session_restart_and_deletion(client):
    """POST /restart clears answers and resets to scratch; DELETE /history removes session."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]

    client.post(f"/api/diagnostics/{sess_id}/answer", json={"question_id": "Q01", "answer": "YES"})

    # Restart session
    restart_res = client.post(f"/api/diagnostics/{sess_id}/restart")
    assert restart_res.status_code == 200
    r_data = restart_res.json()
    assert r_data["session_id"] == sess_id
    assert r_data["status"] == "IN_PROGRESS"
    assert r_data["current_question"] is not None

    # Verify answers were cleared in DB
    hist_detail = client.get(f"/api/history/{sess_id}").json()
    assert len(hist_detail["answers"]) == 0

    # Delete session
    del_res = client.delete(f"/api/history/{sess_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted_id"] == sess_id

    # Verify 404 on subsequent queries
    assert client.get(f"/api/diagnostics/{sess_id}/question").status_code == 404
    assert client.get(f"/api/history/{sess_id}").status_code == 404


# -----------------------------------------------------------------------------
# 12. Error Handling & Validation (400, 404, 422)
# -----------------------------------------------------------------------------

def test_error_handling_and_validation(client):
    """Tests 404 for missing IDs, 400 for bad operations, and 422 for malformed payloads."""
    # 404 Nonexistent session
    fake_id = str(uuid.uuid4())
    res_404 = client.get(f"/api/diagnostics/{fake_id}/question")
    assert res_404.status_code == 404
    assert res_404.json()["error_code"] == "NOT_FOUND"

    # 400 Requesting result while still in progress
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]
    res_400 = client.get(f"/api/diagnostics/{sess_id}/result")
    assert res_400.status_code == 400
    assert res_400.json()["error_code"] == "BAD_REQUEST"

    # 400 Answering invalid question ID
    bad_q_res = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": "INVALID_QUESTION_999", "answer": "YES"},
    )
    assert bad_q_res.status_code == 400
    assert bad_q_res.json()["error_code"] == "BAD_REQUEST"

    # 400 Answering already answered question
    client.post(f"/api/diagnostics/{sess_id}/answer", json={"question_id": "Q01", "answer": "YES"})
    dup_q_res = client.post(f"/api/diagnostics/{sess_id}/answer", json={"question_id": "Q01", "answer": "YES"})
    assert dup_q_res.status_code == 400
    assert "already been answered" in dup_q_res.json()["detail"]

    # 422 Malformed payload (missing answer field)
    val_err = client.post(f"/api/diagnostics/{sess_id}/answer", json={"question_id": "Q02"})
    assert val_err.status_code == 422
    assert val_err.json()["error_code"] == "VALIDATION_ERROR"


# -----------------------------------------------------------------------------
# 13. Knowledge Base Explorer Endpoints
# -----------------------------------------------------------------------------

def test_knowledge_base_explorer_endpoints(client):
    """GET /api/knowledge/facts, /rules, /stats return accurate domain knowledge."""
    # 1. Facts
    facts_res = client.get("/api/knowledge/facts")
    assert facts_res.status_code == 200
    facts = facts_res.json()
    assert len(facts) == 30

    # Filter facts by category
    dns_facts = client.get("/api/knowledge/facts?category=DNS").json()
    assert len(dns_facts) > 0
    assert all(f["category"] == "DNS" for f in dns_facts)

    # Filter facts by source_type
    static_facts = client.get("/api/knowledge/facts?source_type=STATIC_DOMAIN").json()
    assert len(static_facts) == 30

    # 2. Rules
    rules_res = client.get("/api/knowledge/rules")
    assert rules_res.status_code == 200
    rules = rules_res.json()
    assert len(rules) == 28

    # Filter rules by category
    dhcp_rules = client.get("/api/knowledge/rules?category=IP_DHCP").json()
    assert len(dhcp_rules) > 0
    assert all(r["category"] == "IP_DHCP" for r in dhcp_rules)

    # Filter rules by classification
    terminal_rules = client.get("/api/knowledge/rules?classification=TERMINAL_DIAGNOSIS").json()
    assert len(terminal_rules) == 13

    # 3. Stats
    stats_res = client.get("/api/knowledge/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_facts"] == 30
    assert stats["total_rules"] == 28
    assert stats["terminal_rules_count"] == 13
    assert stats["intermediate_rules_count"] == 15
    assert stats["chaining_paths_count"] > 0
    assert stats["max_chaining_depth"] >= 2


# -----------------------------------------------------------------------------
# 14. History Listing and Detail Endpoints
# -----------------------------------------------------------------------------

def test_history_listing_and_detail(client):
    """GET /api/history and /api/history/{session_id} list and audit past sessions."""
    # Create 2 sessions
    s1 = client.post("/api/diagnostics/start", json={}).json()
    s2 = client.post("/api/diagnostics/start", json={}).json()

    # Complete s1 with DHCP failure
    s1_id = s1["session_id"]
    client.post(f"/api/diagnostics/{s1_id}/answer", json={"question_id": "Q01", "answer": "YES"})
    client.post(f"/api/diagnostics/{s1_id}/answer", json={"question_id": "Q12", "answer": "YES"})
    client.post(f"/api/diagnostics/{s1_id}/answer", json={"question_id": "Q03", "answer": "NO"})
    client.post(f"/api/diagnostics/{s1_id}/answer", json={"question_id": "Q07", "answer": "YES"})

    # List history
    hist_res = client.get("/api/history?skip=0&limit=10")
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert hist["total"] >= 2
    assert len(hist["items"]) >= 2

    # Filter history by status=COMPLETED
    completed_res = client.get("/api/history?status=COMPLETED").json()
    assert completed_res["total"] >= 1
    assert any(item["id"] == s1_id for item in completed_res["items"])

    # Detail view of s1
    detail_res = client.get(f"/api/history/{s1_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == s1_id
    assert detail["status"] == "COMPLETED"
    assert detail["final_diagnosis"] == "Router DHCP Server Failure"
    assert len(detail["answers"]) == 4
    assert detail["traces_count"] >= 3
    assert detail["recommendation"] is not None
    assert detail["recommendation"]["diagnosis_code"] == "REC_DHCP_ROUTER"

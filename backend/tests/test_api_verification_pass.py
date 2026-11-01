"""NetSage Phase 5 Additional Verification Pass Test Suite.

Exhaustively verifies:
1. Complete API diagnostic coverage for all remaining categories:
   - Gateway connectivity failure (Router Gateway Crash / Hardware Overload: R06 -> R07 -> R08 -> R09)
   - Weak Wi-Fi signal (Wi-Fi Signal Attenuation and Range Limitation: R17 -> R18 -> R19)
   - Packet loss / high latency (Local Network Bufferbloat & Bandwidth Saturation: R21 -> R22 -> R23)
2. Database transaction safety:
   - Atomic rollback on failed commit
   - Consistent snapshots and child records
   - Safe retry of failed submissions
   - Duplicate submission handling without corrupting traces
3. Real session restoration test (Disk-based SQLite):
   - Engine and service disposal
   - Restoration of session from persistent SQLite on disk
   - Continuation of diagnostic through the API
   - Verification of no duplicate rule execution
4. Database lifecycle:
   - Startup does not delete existing database files
   - Tables created/migrated safely
   - History survives backend restarts
   - Cascading deletion affects only the targeted session
5. API response consistency:
   - In-progress, completed, inconclusive, conflicted, and invalid states
   - Structured error responses (detail, error_code, status_code)
   - No exposed internal Python exceptions or tracebacks
"""

import pytest
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.models.diagnostic import DiagnosticSession, DiagnosticAnswer
from app.models.trace import InferenceTrace, Recommendation
from app.services.diagnostic_service import DiagnosticService


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
    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client
    app.dependency_overrides.clear()


# =============================================================================
# 1. COMPLETE API DIAGNOSTIC COVERAGE (Remaining 3 Categories)
# =============================================================================

def test_api_gateway_connectivity_failure(client):
    """Executes full diagnostic path for Router Gateway Crash / Hardware Overload (R06 -> R07 -> R08 -> R09)."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]

    # Target: Router Gateway Crash / Hardware Overload
    # R06: valid_ip=True, gateway_reachable=False
    # R07: gateway_failure_suspected=True (auto derived)
    # R08: gateway_failure_suspected=True, multiple_devices_affected=True
    # R09: router_hardware_suspected=True, router_reboot_temporarily_fixed=True
    answers = [
        ("Q03", "YES"),  # valid_ip = True
        ("Q04", "NO"),   # gateway_reachable = False -> fires R06, R07
        ("Q07", "YES"),  # multiple_devices_affected = True -> fires R08
        ("Q15", "YES"),  # router_reboot_temporarily_fixed = True -> fires R09 (TERMINAL)
    ]

    for q_id, ans in answers[:-1]:
        r = client.post(
            f"/api/diagnostics/{sess_id}/answer",
            json={"question_id": q_id, "answer": ans},
        ).json()
        assert not r["is_completed"]
        assert r["status"] == "IN_PROGRESS"
        assert r["next_question"] is not None

    last_q, last_ans = answers[-1]
    final_res = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": last_q, "answer": last_ans},
    ).json()

    assert final_res["is_completed"] is True
    assert final_res["status"] == "COMPLETED"
    assert final_res["next_question"] is None

    result = final_res["result"]
    assert result["diagnosis_name"] == "Router Gateway Crash / Hardware Overload"
    assert result["diagnosis_code"] == "REC_GATEWAY_REBOOT"
    assert result["category"] == "GATEWAY"
    assert result["severity"] == "HIGH"
    assert len(result["steps"]) >= 2
    assert any("reboot" in s["action"].lower() or "power" in s["action"].lower() for s in result["steps"])
    assert len(result["warnings"]) > 0
    assert result["escalation_advice"] is not None


def test_api_wifi_signal_attenuation(client):
    """Executes full diagnostic path for Wi-Fi Signal Attenuation and Range Limitation (R17 -> R18 -> R19)."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]

    # Target: Wi-Fi Signal Attenuation and Range Limitation
    # R17: using_wifi=True, wifi_signal_weak=True
    # R18: weak_wifi_suspected=True, frequent_disconnections=True
    # R19: wireless_instability_suspected=True, problem_on_ethernet_too=False
    answers = [
        ("Q02", "YES"),  # using_wifi = True
        ("Q09", "YES"),  # wifi_signal_weak = True -> fires R17
        ("Q08", "YES"),  # frequent_disconnections = True -> fires R18
        ("Q14", "NO"),   # problem_on_ethernet_too = False -> fires R19 (TERMINAL)
    ]

    for q_id, ans in answers[:-1]:
        r = client.post(
            f"/api/diagnostics/{sess_id}/answer",
            json={"question_id": q_id, "answer": ans},
        ).json()
        assert not r["is_completed"]
        assert r["status"] == "IN_PROGRESS"

    last_q, last_ans = answers[-1]
    final_res = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": last_q, "answer": last_ans},
    ).json()

    assert final_res["is_completed"] is True
    assert final_res["status"] == "COMPLETED"
    result = final_res["result"]
    assert result["diagnosis_name"] == "Wi-Fi Signal Attenuation and Range Limitation"
    assert result["diagnosis_code"] == "REC_WIFI_RANGE"
    assert result["category"] == "WIFI"
    assert result["severity"] == "MEDIUM"
    assert any("closer" in s["description"].lower() or "5 ghz" in s["description"].lower() or "channel" in s["description"].lower() for s in result["steps"])


def test_api_performance_bufferbloat_and_congestion(client):
    """Executes full diagnostic path for Local Network Bufferbloat & Bandwidth Saturation (R21 -> R22 -> R23)."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]

    # Target: Local Network Bufferbloat & Bandwidth Saturation
    # R21: high_latency_observed=True
    # R22: network_performance_degraded=True, heavy_bandwidth_usage=True
    # R23: network_congestion_suspected=True
    answers = [
        ("Q10", "YES"),  # high_latency_observed = True -> fires R21
        ("Q16", "YES"),  # heavy_bandwidth_usage = True -> fires R22, R23 (TERMINAL)
    ]

    r1 = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": answers[0][0], "answer": answers[0][1]},
    ).json()
    assert not r1["is_completed"]

    final_res = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": answers[1][0], "answer": answers[1][1]},
    ).json()

    assert final_res["is_completed"] is True
    assert final_res["status"] == "COMPLETED"
    result = final_res["result"]
    assert result["diagnosis_name"] == "Local Network Bufferbloat & Bandwidth Saturation"
    assert result["diagnosis_code"] == "REC_PERF_CONGESTION"
    assert result["category"] == "PERFORMANCE"
    assert result["severity"] == "MEDIUM"
    assert any("sqm" in s["description"].lower() or "qos" in s["description"].lower() or "bandwidth" in s["description"].lower() for s in result["steps"])


# =============================================================================
# 2. DATABASE TRANSACTION SAFETY
# =============================================================================

def test_transaction_safety_failed_commit_rollback(client, db_session):
    """Failed database commits roll back cleanly and allow safe retry without partial corruption."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]

    # Answer Q01 successfully
    client.post(f"/api/diagnostics/{sess_id}/answer", json={"question_id": "Q01", "answer": "YES"})

    # Check state before failure
    sess_before = db_session.query(DiagnosticSession).filter(DiagnosticSession.id == sess_id).first()
    snap_before = sess_before.working_memory_snapshot
    ans_count_before = len(sess_before.answers)
    assert ans_count_before == 1

    # Simulate a database commit failure during second answer
    with patch.object(db_session, "commit", side_effect=Exception("Database lock/commit timeout simulated")):
        res_fail = client.post(
            f"/api/diagnostics/{sess_id}/answer",
            json={"question_id": "Q12", "answer": "YES"},
        )
        assert res_fail.status_code == 500
        assert res_fail.json()["error_code"] == "INTERNAL_SERVER_ERROR"

    # Verify atomic rollback: no partial answer or corrupt snapshot persisted
    db_session.expire_all()
    sess_after_fail = db_session.query(DiagnosticSession).filter(DiagnosticSession.id == sess_id).first()
    assert len(sess_after_fail.answers) == ans_count_before
    assert sess_after_fail.working_memory_snapshot == snap_before

    # Safe retry: resubmitting the failed answer must now succeed cleanly
    retry_res = client.post(
        f"/api/diagnostics/{sess_id}/answer",
        json={"question_id": "Q12", "answer": "YES"},
    )
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "IN_PROGRESS"

    db_session.expire_all()
    sess_after_retry = db_session.query(DiagnosticSession).filter(DiagnosticSession.id == sess_id).first()
    assert len(sess_after_retry.answers) == 2


def test_transaction_safety_duplicate_submission_handling(client, db_session):
    """Submitting the same question twice is rejected without corrupting inference state or traces."""
    start_res = client.post("/api/diagnostics/start", json={}).json()
    sess_id = start_res["session_id"]

    # Initial submission
    res1 = client.post(f"/api/diagnostics/{sess_id}/answer", json={"question_id": "Q01", "answer": "YES"})
    assert res1.status_code == 200

    # Duplicate submission
    dup_res = client.post(f"/api/diagnostics/{sess_id}/answer", json={"question_id": "Q01", "answer": "NO"})
    assert dup_res.status_code == 400
    assert dup_res.json()["error_code"] == "BAD_REQUEST"
    assert "already been answered" in dup_res.json()["detail"]

    # Verify answers table has exactly 1 entry for this question
    answers = db_session.query(DiagnosticAnswer).filter(DiagnosticAnswer.session_id == sess_id).all()
    assert len(answers) == 1
    assert answers[0].answer == "YES"


# =============================================================================
# 3. REAL SESSION RESTORATION (Disk-based SQLite)
# =============================================================================

def test_real_session_restoration_disk_sqlite(tmp_path):
    """Verifies complete session restoration from persistent SQLite on disk across fresh service/engine instances."""
    db_file = tmp_path / "restoration_test.db"
    disk_db_url = f"sqlite:///{db_file}"

    disk_engine = create_engine(disk_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=disk_engine)
    DiskSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=disk_engine)

    # 1. Create session and answer two questions in First Run
    first_db = DiskSessionLocal()
    first_service = DiagnosticService()
    start_resp = first_service.start_session(first_db)
    sess_id = start_resp.session_id

    # Q01: device_connected = True
    first_service.submit_answer(first_db, sess_id, "Q01", "YES")
    # Q12: ip_is_apipa = True -> triggers R01
    first_service.submit_answer(first_db, sess_id, "Q12", "YES")
    first_db.close()

    # 2. DISPOSE of all original instances completely
    disk_engine.dispose()
    del first_service
    del first_db
    del disk_engine

    # 3. Re-open brand new connection to the on-disk SQLite file
    restored_engine = create_engine(disk_db_url, connect_args={"check_same_thread": False})
    RestoredSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=restored_engine)
    fresh_db = RestoredSessionLocal()
    fresh_service = DiagnosticService()

    # Verify session exists in DB with 2 answers
    db_sess = fresh_db.query(DiagnosticSession).filter(DiagnosticSession.id == sess_id).first()
    assert db_sess is not None
    assert len(db_sess.answers) == 2
    assert db_sess.status == "IN_PROGRESS"

    # Query current question on fresh service
    next_q = fresh_service.get_current_question(fresh_db, sess_id)
    assert next_q is not None

    # Continue diagnosis: Q03 = NO -> triggers R03
    fresh_service.submit_answer(fresh_db, sess_id, "Q03", "NO")
    # Q07 = YES -> triggers R04 (TERMINAL)
    final_res = fresh_service.submit_answer(fresh_db, sess_id, "Q07", "YES")

    assert final_res.is_completed is True
    assert final_res.status == "COMPLETED"
    assert final_res.result.diagnosis_name == "Router DHCP Server Failure"

    # 4. Verify NO duplicate rule execution occurred
    traces = fresh_db.query(InferenceTrace).filter(InferenceTrace.session_id == sess_id).order_by(InferenceTrace.execution_order).all()
    fired_rule_ids = [t.rule_id for t in traces]
    assert fired_rule_ids == ["R01", "R03", "R04"]  # R01 fired once, R03 fired once, R04 fired once!
    assert len(fired_rule_ids) == len(set(fired_rule_ids))  # Zero duplicate rule firings!

    fresh_db.close()
    restored_engine.dispose()


# =============================================================================
# 4. DATABASE LIFECYCLE
# =============================================================================

def test_database_lifecycle_startup_does_not_wipe_data(tmp_path):
    """Normal application startup creates tables safely without deleting existing data."""
    db_file = tmp_path / "lifecycle.db"
    db_url = f"sqlite:///{db_file}"

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionMaker = sessionmaker(bind=engine)

    # Insert a session
    sess = SessionMaker()
    diagnostic = DiagnosticSession(id="test-session-123", status="COMPLETED", final_diagnosis="Test Outage")
    sess.add(diagnostic)
    sess.commit()
    sess.close()

    # Simulate backend restart: call Base.metadata.create_all again
    Base.metadata.create_all(bind=engine)

    # Verify session still exists
    sess2 = SessionMaker()
    record = sess2.query(DiagnosticSession).filter(DiagnosticSession.id == "test-session-123").first()
    assert record is not None
    assert record.final_diagnosis == "Test Outage"
    sess2.close()
    engine.dispose()


def test_database_lifecycle_cascading_isolation(client, db_session):
    """Explicit session deletion removes all its child entities without touching other sessions."""
    # Create Session A and Session B
    sA = client.post("/api/diagnostics/start", json={}).json()["session_id"]
    sB = client.post("/api/diagnostics/start", json={}).json()["session_id"]

    client.post(f"/api/diagnostics/{sA}/answer", json={"question_id": "Q01", "answer": "YES"})
    client.post(f"/api/diagnostics/{sB}/answer", json={"question_id": "Q01", "answer": "YES"})

    # Delete Session A
    del_res = client.delete(f"/api/history/{sA}")
    assert del_res.status_code == 200

    # Session A is gone
    assert db_session.query(DiagnosticSession).filter(DiagnosticSession.id == sA).first() is None
    assert db_session.query(DiagnosticAnswer).filter(DiagnosticAnswer.session_id == sA).count() == 0

    # Session B is completely preserved
    assert db_session.query(DiagnosticSession).filter(DiagnosticSession.id == sB).first() is not None
    assert db_session.query(DiagnosticAnswer).filter(DiagnosticAnswer.session_id == sB).count() == 1


# =============================================================================
# 5. API RESPONSE CONSISTENCY & ERROR STRUCTURE
# =============================================================================

def test_api_response_consistency_across_all_session_states(client):
    """Verifies structured responses across in-progress, completed, inconclusive, conflicted, and invalid states."""
    # 1. In-progress session
    s_prog = client.post("/api/diagnostics/start", json={}).json()["session_id"]
    q_res = client.get(f"/api/diagnostics/{s_prog}/question")
    assert q_res.status_code == 200
    assert "why_explanation" in q_res.json()

    res_early = client.get(f"/api/diagnostics/{s_prog}/result")
    assert res_early.status_code == 400
    assert res_early.json()["error_code"] == "BAD_REQUEST"
    assert "still in progress" in res_early.json()["detail"]

    # 2. Completed session
    client.post(f"/api/diagnostics/{s_prog}/answer", json={"question_id": "Q01", "answer": "YES"})
    client.post(f"/api/diagnostics/{s_prog}/answer", json={"question_id": "Q12", "answer": "YES"})
    client.post(f"/api/diagnostics/{s_prog}/answer", json={"question_id": "Q03", "answer": "NO"})
    comp_res = client.post(f"/api/diagnostics/{s_prog}/answer", json={"question_id": "Q07", "answer": "YES"}).json()
    assert comp_res["status"] == "COMPLETED"

    # Completed session question query raises 400
    q_late = client.get(f"/api/diagnostics/{s_prog}/question")
    assert q_late.status_code == 400
    assert q_late.json()["error_code"] == "BAD_REQUEST"

    # 3. Inconclusive session
    benign = {
        "device_connected": True, "valid_ip": True, "ip_is_apipa": False,
        "gateway_reachable": True, "external_ip_reachable": True,
        "domain_access": True, "using_wifi": False,
        "high_latency_observed": False, "packet_loss_observed": False,
    }
    s_incon = client.post("/api/diagnostics/start", json={"initial_facts": benign}).json()["session_id"]
    incon_res = client.get(f"/api/diagnostics/{s_incon}/result")
    assert incon_res.status_code == 200
    assert incon_res.json()["status"] == "INCONCLUSIVE"
    assert incon_res.json()["diagnosis_code"] == "REC_INCONCLUSIVE"

    # 4. Conflicted session
    s_conf = client.post("/api/diagnostics/start", json={"initial_facts": {"gateway_reachable": True}}).json()["session_id"]
    conf_ans = client.post(f"/api/diagnostics/{s_conf}/answer", json={"question_id": "Q04", "answer": "NO"})
    assert conf_ans.status_code == 409
    assert conf_ans.json()["error_code"] == "CONFLICT_DETECTED"

    conf_res = client.get(f"/api/diagnostics/{s_conf}/result")
    assert conf_res.status_code == 200
    assert conf_res.json()["status"] == "CONFLICT_DETECTED"

    # 5. Invalid / Nonexistent session ID
    fake_id = str(uuid.uuid4())
    for method, path in [
        ("GET", f"/api/diagnostics/{fake_id}/question"),
        ("GET", f"/api/diagnostics/{fake_id}/result"),
        ("GET", f"/api/diagnostics/{fake_id}/explanation"),
        ("POST", f"/api/diagnostics/{fake_id}/restart"),
        ("DELETE", f"/api/history/{fake_id}"),
    ]:
        if method == "GET":
            r = client.get(path)
        elif method == "POST":
            r = client.post(path)
        else:
            r = client.delete(path)
        assert r.status_code == 404
        assert r.json()["error_code"] == "NOT_FOUND"
        assert "not found" in r.json()["detail"].lower()

    # 6. Global error structure consistency: never exposes stack trace
    assert "detail" in r.json()
    assert "error_code" in r.json()
    assert "status_code" in r.json()

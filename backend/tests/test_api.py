import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.models.diagnostic import DiagnosticSession, DiagnosticAnswer
from app.models.trace import InferenceTrace, Recommendation

# In-memory SQLite with StaticPool so all connections share the same in-memory DB
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


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "NetSage" in data["message"]
    assert data["docs"] == "/api/docs"
    assert data["health"] == "/api/health"


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "NetSage"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


def test_database_session_model_creation(db_session):
    session = DiagnosticSession(
        status="IN_PROGRESS",
        summary="Test diagnostic session initialization"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    assert session.id is not None
    assert session.status == "IN_PROGRESS"
    assert session.created_at is not None


def test_database_relationships_and_cascades(db_session):
    # 1. Create a parent session
    session = DiagnosticSession(
        status="COMPLETED",
        final_diagnosis="Possible DNS Server Failure",
        diagnosis_category="DNS",
        severity="HIGH",
        summary="DNS resolution fails while external IP is reachable"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    # 2. Add an answer
    answer = DiagnosticAnswer(
        session_id=session.id,
        question_id="Q05",
        question_text="Can you access an external IP address?",
        answer="YES"
    )
    db_session.add(answer)

    # 3. Add an inference trace
    trace = InferenceTrace(
        session_id=session.id,
        rule_id="R09",
        rule_name="DNS Resolution Failure",
        conditions='{"external_ip_reachable": true, "domain_access": false}',
        conclusion='{"dns_failure_suspected": true}',
        explanation="External IP is reachable but domain access fails.",
        execution_order=1
    )
    db_session.add(trace)

    # 4. Add a recommendation
    recommendation = Recommendation(
        session_id=session.id,
        recommendation_text="Check DNS server configuration and flush DNS cache.",
        priority=1,
        completed=False
    )
    db_session.add(recommendation)
    db_session.commit()

    # Query back and verify relationships
    reloaded_session = db_session.query(DiagnosticSession).filter_by(id=session.id).first()
    assert reloaded_session is not None
    assert len(reloaded_session.answers) == 1
    assert reloaded_session.answers[0].question_id == "Q05"
    assert len(reloaded_session.traces) == 1
    assert reloaded_session.traces[0].rule_id == "R09"
    assert len(reloaded_session.recommendations) == 1
    assert reloaded_session.recommendations[0].priority == 1

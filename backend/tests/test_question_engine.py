import pytest
from app.expert_system.types import TriState, FactCategory
from app.expert_system.knowledge_base import USER_FACT_DEFINITIONS
from app.expert_system.question_engine import (
    Question,
    QuestionRegistry,
    QuestionEngine,
    QUESTIONS_DATA,
)
from app.expert_system.inference_engine import InferenceEngine


def test_question_registry_count_and_uniqueness():
    """Verify registry has at least 15 questions and all IDs and fact keys are unique."""
    registry = QuestionRegistry()
    assert registry.count() >= 15
    assert registry.count() == 16

    questions = registry.get_all()
    q_ids = [q.id for q in questions]
    fact_keys = [q.fact_key for q in questions]

    assert len(q_ids) == len(set(q_ids)), "Duplicate question ID found"
    assert len(fact_keys) == len(set(fact_keys)), "Duplicate fact key found"


def test_question_to_fact_mapping_soundness():
    """Verify every question maps to a valid user fact in USER_FACT_DEFINITIONS."""
    registry = QuestionRegistry()
    for q in registry.get_all():
        assert q.fact_key in USER_FACT_DEFINITIONS, f"Question {q.id} maps to undefined user fact '{q.fact_key}'"
        assert len(q.text) > 10
        assert len(q.guidance) > 10
        assert len(q.default_why) > 10
        assert q.answer_type == "boolean"
        assert isinstance(q.category, FactCategory)


def test_parse_user_answer():
    """Verify parser maps text strings and booleans to True, False, or TriState.UNKNOWN."""
    # Positive affirmative
    assert QuestionEngine.parse_user_answer("YES") is True
    assert QuestionEngine.parse_user_answer("yes") is True
    assert QuestionEngine.parse_user_answer("Y") is True
    assert QuestionEngine.parse_user_answer(True) is True

    # Negative refutation
    assert QuestionEngine.parse_user_answer("NO") is False
    assert QuestionEngine.parse_user_answer("no") is False
    assert QuestionEngine.parse_user_answer("N") is False
    assert QuestionEngine.parse_user_answer(False) is False

    # Uncertainty / UNKNOWN
    assert QuestionEngine.parse_user_answer("UNKNOWN") == TriState.UNKNOWN
    assert QuestionEngine.parse_user_answer("unsure") == TriState.UNKNOWN
    assert QuestionEngine.parse_user_answer("dont_know") == TriState.UNKNOWN
    assert QuestionEngine.parse_user_answer(TriState.UNKNOWN) == TriState.UNKNOWN

    # Invalid input raises ValueError
    with pytest.raises(ValueError):
        QuestionEngine.parse_user_answer("maybe")


def test_dynamic_question_selection_workflow():
    """Verify dynamic question selection chooses questions based on backward chaining."""
    engine = InferenceEngine()
    q_engine = QuestionEngine()

    # Initial state: should select first high-priority unasked question
    q1 = q_engine.select_next_question(engine)
    assert q1 is not None
    assert q1.fact_key in USER_FACT_DEFINITIONS

    # Answer the question affirmatively
    engine.assert_user_fact(q1.fact_key, True)

    # Next question should be selected dynamically and not repeat q1
    q2 = q_engine.select_next_question(engine)
    assert q2 is not None
    assert q2.id != q1.id
    assert q2.fact_key != q1.fact_key


def test_question_selection_excludes_unknown_answers():
    """Verify questions answered UNKNOWN are never selected again."""
    engine = InferenceEngine()
    q_engine = QuestionEngine()

    q1 = q_engine.select_next_question(engine)
    assert q1 is not None

    # User answers UNKNOWN
    engine.memory.set_fact(q1.fact_key, TriState.UNKNOWN, "USER")

    # Next question must not repeat q1
    q2 = q_engine.select_next_question(engine)
    assert q2 is not None
    assert q2.id != q1.id


def test_question_selection_returns_none_on_completion():
    """Verify question engine returns None when diagnosis has been reached."""
    engine = InferenceEngine()
    q_engine = QuestionEngine()

    # Provide evidence to conclude DNS Outage
    engine.assert_user_fact("external_ip_reachable", True)
    engine.assert_user_fact("domain_access", False)
    engine.assert_user_fact("dns_server_reachable", False)
    engine.assert_user_fact("multiple_devices_affected", True)

    assert engine.has_terminal_diagnosis() is True
    # No more questions should be asked
    assert q_engine.select_next_question(engine) is None


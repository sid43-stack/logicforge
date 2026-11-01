import pytest
from app.expert_system.rules import PRODUCTION_RULES, RuleClassification
from app.expert_system.recommendation_engine import (
    RecommendationEngine,
    RecommendationPlan,
    RECOMMENDATIONS_DATA,
)


def test_recommendation_plans_coverage_for_all_terminal_diagnoses():
    """Verify every terminal production rule has a corresponding recommendation plan."""
    engine = RecommendationEngine()
    terminal_rules = [r for r in PRODUCTION_RULES if r.classification == RuleClassification.TERMINAL_DIAGNOSIS]

    assert len(terminal_rules) == 13

    for rule in terminal_rules:
        diag_name = rule.conclusions.get("diagnosis")
        rec_code = rule.conclusions.get("recommendation_code")

        assert diag_name is not None
        assert rec_code is not None

        # Look up by code
        plan_by_code = engine.get_recommendation_by_code(rec_code)
        assert plan_by_code is not None, f"Missing recommendation plan for code {rec_code}"
        assert plan_by_code.code == rec_code

        # Look up by diagnosis name
        plan_by_name = engine.get_recommendation_for_diagnosis(diagnosis_name=diag_name)
        assert plan_by_name is not None, f"Missing recommendation plan for diagnosis '{diag_name}'"
        assert plan_by_name.diagnosis.lower() == diag_name.lower()


def test_recommendation_plan_structure_and_completeness():
    """Verify each recommendation plan has summary, ordered steps, expected outcomes, and escalation advice."""
    engine = RecommendationEngine()
    for code, plan in RECOMMENDATIONS_DATA.items():
        assert len(plan.code) > 0
        assert len(plan.diagnosis) > 0
        assert len(plan.summary) > 15
        assert len(plan.escalation_advice) > 15
        assert len(plan.steps) >= 2, f"Plan {code} should have at least 2 steps"

        # Verify steps sequence
        for idx, step in enumerate(plan.steps, start=1):
            assert step.order == idx
            assert len(step.action) > 5
            assert len(step.description) > 15
            assert len(step.expected_outcome) > 10
            assert isinstance(step.is_disruptive, bool)
            assert isinstance(step.requires_admin, bool)


def test_missing_or_unknown_recommendation_fallback():
    """Verify recommendation engine falls back gracefully to REC_INCONCLUSIVE for unknown inputs."""
    engine = RecommendationEngine()

    fallback_none = engine.get_recommendation_for_diagnosis(None)
    assert fallback_none.code == "REC_INCONCLUSIVE"
    assert "Inconclusive" in fallback_none.diagnosis

    fallback_unknown = engine.get_recommendation_for_diagnosis("Aliens Cut The Cables")
    assert fallback_unknown.code == "REC_INCONCLUSIVE"


def test_disruption_and_admin_flags():
    """Verify disruptive steps (e.g. rebooting router) are explicitly flagged."""
    engine = RecommendationEngine()
    dhcp_router_plan = engine.get_recommendation_by_code("REC_DHCP_ROUTER")
    assert dhcp_router_plan is not None

    # Step 1 is router reboot -> must be flagged disruptive
    reboot_step = dhcp_router_plan.steps[0]
    assert reboot_step.is_disruptive is True
    assert len(dhcp_router_plan.warnings) > 0


import pytest
from app.expert_system.types import (
    TriState,
    Operator,
    Condition,
    RuleCategory,
    RuleClassification,
)
from app.expert_system.rules import (
    PRODUCTION_RULES,
    RULES_BY_ID,
    Rule,
    get_rule,
    get_all_rules,
    get_rules_by_category,
)


def test_rule_base_count():
    """Verify that NetSage contains at least 25 production rules across categories."""
    assert len(PRODUCTION_RULES) >= 25
    assert len(PRODUCTION_RULES) == 28


def test_rule_categories_coverage():
    """Verify all six diagnostic categories are covered by production rules."""
    covered_categories = {rule.category for rule in PRODUCTION_RULES}
    for cat in RuleCategory:
        assert cat in covered_categories, f"Category {cat} missing from rule base"


def test_rule_structure_and_completeness():
    """Verify every rule has unique ID, name, priority, classification, explanation, and conditions."""
    seen_ids = set()
    for rule in PRODUCTION_RULES:
        assert rule.id.startswith("R")
        assert rule.id not in seen_ids, f"Duplicate Rule ID {rule.id}"
        seen_ids.add(rule.id)

        assert len(rule.name) > 5
        assert 50 <= rule.priority <= 100
        assert rule.classification in (RuleClassification.INTERMEDIATE, RuleClassification.TERMINAL_DIAGNOSIS)
        assert len(rule.conditions) > 0
        assert len(rule.conclusions) > 0
        assert len(rule.explanation) > 10

        # Check terminal rules assert a diagnosis
        if rule.classification == RuleClassification.TERMINAL_DIAGNOSIS:
            assert "diagnosis" in rule.conclusions
            assert "diagnosis_category" in rule.conclusions
            assert "diagnosis_severity" in rule.conclusions


def test_condition_evaluation_tri_state():
    """Test 3-valued logic evaluation for individual Condition objects."""
    cond = Condition(fact_key="gateway_reachable", operator=Operator.EQUALS, value=True)

    # Boolean True -> TRUE
    assert cond.evaluate(True) == TriState.TRUE
    # Boolean False -> FALSE
    assert cond.evaluate(False) == TriState.FALSE
    # None or UNKNOWN -> UNKNOWN
    assert cond.evaluate(None) == TriState.UNKNOWN
    assert cond.evaluate(TriState.UNKNOWN) == TriState.UNKNOWN

    # TriState values matching
    assert cond.evaluate(TriState.TRUE) == TriState.TRUE
    assert cond.evaluate(TriState.FALSE) == TriState.FALSE

    # NOT EQUALS operator
    cond_neq = Condition(fact_key="status", operator=Operator.NOT_EQUALS, value="DOWN")
    assert cond_neq.evaluate("UP") == TriState.TRUE
    assert cond_neq.evaluate("DOWN") == TriState.FALSE
    assert cond_neq.evaluate(None) == TriState.UNKNOWN

    # IN operator
    cond_in = Condition(fact_key="code", operator=Operator.IN, value=[200, 201])
    assert cond_in.evaluate(200) == TriState.TRUE
    assert cond_in.evaluate(404) == TriState.FALSE
    assert cond_in.evaluate(None) == TriState.UNKNOWN


def test_rule_conjunction_evaluation():
    """Test 3-valued logic evaluation for full Rule conditions (AND conjunction)."""
    rule = Rule(
        id="R_TEST",
        name="Test Conjunction Rule",
        category=RuleCategory.DNS,
        priority=80,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="fact_a", operator=Operator.EQUALS, value=True),
            Condition(fact_key="fact_b", operator=Operator.EQUALS, value=True),
        ],
        conclusions={"fact_c": True},
        explanation="Test rule for conjunction logic."
    )

    # 1. Both TRUE -> TRUE
    facts_all_true = {"fact_a": True, "fact_b": True}
    assert rule.evaluate_conditions(facts_all_true) == TriState.TRUE

    # 2. One FALSE -> FALSE (even if other is unknown or true)
    facts_one_false = {"fact_a": True, "fact_b": False}
    assert rule.evaluate_conditions(facts_one_false) == TriState.FALSE

    facts_false_and_unknown = {"fact_a": False}  # fact_b is unknown
    assert rule.evaluate_conditions(facts_false_and_unknown) == TriState.FALSE

    # 3. One TRUE and One UNKNOWN -> UNKNOWN
    facts_one_unknown = {"fact_a": True}  # fact_b is missing/unknown
    assert rule.evaluate_conditions(facts_one_unknown) == TriState.UNKNOWN

    # 4. Both UNKNOWN -> UNKNOWN
    assert rule.evaluate_conditions({}) == TriState.UNKNOWN


def test_rule_retrieval_functions():
    """Test get_rule, get_all_rules, and get_rules_by_category."""
    r01 = get_rule("R01")
    assert r01 is not None
    assert r01.name.startswith("Automatic IP")

    assert get_rule("R999") is None

    all_rules = get_all_rules()
    assert len(all_rules) == 28

    dns_rules = get_rules_by_category(RuleCategory.DNS)
    assert len(dns_rules) == 6
    for r in dns_rules:
        assert r.category == RuleCategory.DNS


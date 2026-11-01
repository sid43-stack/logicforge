import pytest
from app.expert_system.types import (
    TriState,
    Operator,
    Condition,
    RuleCategory,
    RuleClassification,
)
from app.expert_system.rules import Rule, PRODUCTION_RULES
from app.expert_system.rule_graph import (
    RuleDependencyGraph,
    KnowledgeBaseValidator,
)


def test_rule_dependency_graph_building():
    """Verify that the RuleDependencyGraph correctly builds forward and backward edges."""
    graph = RuleDependencyGraph(PRODUCTION_RULES)

    # R01 asserts 'dhcp_failure_suspected'
    # R03 consumes 'dhcp_failure_suspected'
    # Therefore, R01 -> R03
    assert "R03" in graph.get_dependents("R01")
    assert "R01" in graph.get_dependencies("R03")

    # R11 asserts 'dns_failure_suspected'
    # R12 consumes 'dns_failure_suspected'
    # R12 asserts 'dns_server_failure_suspected'
    # R13 consumes 'dns_server_failure_suspected'
    assert "R12" in graph.get_dependents("R11")
    assert "R13" in graph.get_dependents("R12")
    assert "R11" in graph.get_dependencies("R12")
    assert "R12" in graph.get_dependencies("R13")


def test_cycle_detection_on_clean_rule_base():
    """Verify that production rules contain NO circular dependencies."""
    graph = RuleDependencyGraph(PRODUCTION_RULES)
    cycles = graph.detect_cycles()
    assert cycles == [], f"Circular dependencies detected: {cycles}"


def test_chaining_paths_count_and_depth():
    """Verify at least 5 multi-step chained rule sequences exist across categories."""
    graph = RuleDependencyGraph(PRODUCTION_RULES)
    paths = graph.get_all_chaining_paths()

    # There should be multiple multi-step paths
    assert len(paths) >= 5, f"Expected at least 5 chaining paths, found {len(paths)}"

    # Check for specific category chains
    path_strings = [" -> ".join(p) for p in paths]

    # 1. DHCP Chain: R01 -> R03 -> R04
    assert any("R01" in p and "R03" in p and "R04" in p for p in path_strings)

    # 2. Gateway Chain: R06 -> R08 -> R09
    assert any("R06" in p and "R08" in p and "R09" in p for p in path_strings)

    # 3. DNS Chain: R11 -> R12 -> R13
    assert any("R11" in p and "R12" in p and "R13" in p for p in path_strings)

    # 4. Wi-Fi Chain: R17 -> R18 -> R19
    assert any("R17" in p and "R18" in p and "R19" in p for p in path_strings)

    # 5. Performance Chain: R21 -> R22 -> R23
    assert any("R21" in p and "R22" in p and "R23" in p for p in path_strings)

    # 6. ISP Chain: R25 -> R26 -> R27
    assert any("R25" in p and "R26" in p and "R27" in p for p in path_strings)


def test_automated_validator_clean_pass():
    """Verify that the production rule base passes all validation checks with 0 errors."""
    report = KnowledgeBaseValidator.validate(PRODUCTION_RULES)
    assert report.is_valid, f"Rule base validation failed: {report.errors}"
    assert len(report.errors) == 0
    assert len(report.duplicate_rule_ids) == 0
    assert len(report.invalid_fact_references) == 0
    assert len(report.circular_dependencies) == 0
    assert len(report.unreachable_rules) == 0
    assert len(report.dead_rules) == 0
    assert len(report.conflicting_rules) == 0


def test_validator_catches_duplicate_rule_id():
    """Verify validator flags duplicate rule IDs."""
    bad_rules = list(PRODUCTION_RULES) + [
        Rule(
            id="R01",  # Duplicate ID
            name="Cloned Rule",
            category=RuleCategory.IP_DHCP,
            priority=50,
            conditions=[Condition(fact_key="device_connected", operator=Operator.EQUALS, value=True)],
            conclusions={"test": True},
            explanation="Duplicate rule."
        )
    ]
    report = KnowledgeBaseValidator.validate(bad_rules)
    assert not report.is_valid
    assert any("Duplicate Rule ID" in err for err in report.errors)


def test_validator_catches_invalid_fact_reference():
    """Verify validator flags rules referencing non-existent fact keys."""
    bad_rules = [
        Rule(
            id="R_BAD_PREMISE",
            name="Bad Premise Rule",
            category=RuleCategory.DNS,
            priority=50,
            conditions=[Condition(fact_key="quantum_flux_detected", operator=Operator.EQUALS, value=True)],
            conclusions={"test": True},
            explanation="Invalid premise."
        )
    ]
    report = KnowledgeBaseValidator.validate(bad_rules)
    assert not report.is_valid
    assert any("quantum_flux_detected" in err for err in report.errors)


def test_validator_catches_circular_dependency():
    """Verify validator flags circular dependencies between rules."""
    cyclic_rules = [
        Rule(
            id="R_CYCLE_1",
            name="Cycle Step 1",
            category=RuleCategory.IP_DHCP,
            priority=50,
            conditions=[Condition(fact_key="device_connected", operator=Operator.EQUALS, value=True)],
            conclusions={"intermediate_alpha": True},
            explanation="Cycle step 1."
        ),
        Rule(
            id="R_CYCLE_2",
            name="Cycle Step 2",
            category=RuleCategory.IP_DHCP,
            priority=50,
            conditions=[Condition(fact_key="intermediate_alpha", operator=Operator.EQUALS, value=True)],
            conclusions={"intermediate_beta": True},
            explanation="Cycle step 2."
        ),
        Rule(
            id="R_CYCLE_3",
            name="Cycle Step 3 (Creates Cycle)",
            category=RuleCategory.IP_DHCP,
            priority=50,
            conditions=[Condition(fact_key="intermediate_beta", operator=Operator.EQUALS, value=True)],
            conclusions={"intermediate_alpha": True},  # Closes cycle back to R_CYCLE_2
            explanation="Cycle step 3."
        )
    ]
    report = KnowledgeBaseValidator.validate(cyclic_rules)
    assert not report.is_valid
    assert len(report.circular_dependencies) > 0


def test_validator_catches_dead_rule():
    """Verify validator flags rules with contradictory conditions (e.g. A == True AND A == False)."""
    dead_rules = [
        Rule(
            id="R_DEAD",
            name="Dead Rule",
            category=RuleCategory.DNS,
            priority=50,
            conditions=[
                Condition(fact_key="domain_access", operator=Operator.EQUALS, value=True),
                Condition(fact_key="domain_access", operator=Operator.EQUALS, value=False),
            ],
            conclusions={"test": True},
            explanation="Can never fire."
        )
    ]
    report = KnowledgeBaseValidator.validate(dead_rules)
    assert not report.is_valid
    assert any("can never fire" in err for err in report.errors)


def test_validator_catches_conflicting_diagnoses():
    """Verify validator flags rules with identical conditions asserting conflicting diagnoses."""
    conflicting_rules = [
        Rule(
            id="R_CONF_1",
            name="Conflict Rule 1",
            category=RuleCategory.ISP,
            priority=80,
            classification=RuleClassification.TERMINAL_DIAGNOSIS,
            conditions=[
                Condition(fact_key="device_connected", operator=Operator.EQUALS, value=True),
            ],
            conclusions={"diagnosis": "Local Fault", "diagnosis_category": "GATEWAY", "diagnosis_severity": "LOW"},
            explanation="Diagnosis 1."
        ),
        Rule(
            id="R_CONF_2",
            name="Conflict Rule 2",
            category=RuleCategory.ISP,
            priority=80,
            classification=RuleClassification.TERMINAL_DIAGNOSIS,
            conditions=[
                Condition(fact_key="device_connected", operator=Operator.EQUALS, value=True),
            ],
            conclusions={"diagnosis": "Remote Outage", "diagnosis_category": "ISP", "diagnosis_severity": "HIGH"},
            explanation="Diagnosis 2."
        )
    ]
    report = KnowledgeBaseValidator.validate(conflicting_rules)
    assert not report.is_valid
    assert any("Conflicting rules detected" in err for err in report.errors)

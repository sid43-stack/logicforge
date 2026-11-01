"""NetSage Rule Dependency Graph and Knowledge Base Validator.

Strictly independent of FastAPI and React.
Performs topological analysis, dependency mapping, cycle detection,
and automated validation of production rules and facts.
"""

from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
from app.expert_system.types import RuleClassification, Operator
from app.expert_system.knowledge_base import (
    DOMAIN_FACTS,
    USER_FACT_DEFINITIONS,
    DERIVED_FACT_DEFINITIONS,
)
from app.expert_system.rules import Rule, PRODUCTION_RULES


class RuleDependencyGraph:
    """Directed graph representing dependency relationships between rules and facts.
    
    A rule R_j depends on rule R_i (R_i -> R_j) if R_i asserts a conclusion fact
    that R_j requires as an antecedent condition.
    """

    def __init__(self, rules: List[Rule]):
        self.rules = rules
        self.rules_by_id: Dict[str, Rule] = {r.id: r for r in rules}
        
        # Maps fact_key -> list of rule_ids that ASSERT it
        self.fact_producers: Dict[str, List[str]] = defaultdict(list)
        # Maps fact_key -> list of rule_ids that CONSUME it as a condition
        self.fact_consumers: Dict[str, List[str]] = defaultdict(list)
        
        # Direct rule-to-rule edges: rule_id -> list of rules that depend on it
        self.forward_edges: Dict[str, Set[str]] = defaultdict(set)
        # Inverted rule-to-rule edges: rule_id -> list of rules it depends on
        self.backward_edges: Dict[str, Set[str]] = defaultdict(set)
        
        self._build_graph()

    def _build_graph(self):
        # 1. Map fact producers and consumers
        for rule in self.rules:
            for cond in rule.conditions:
                self.fact_consumers[cond.fact_key].append(rule.id)
            for conc_key in rule.conclusions.keys():
                self.fact_producers[conc_key].append(rule.id)

        # 2. Build direct rule-to-rule dependencies
        for fact_key, consumer_ids in self.fact_consumers.items():
            producer_ids = self.fact_producers.get(fact_key, [])
            for producer_id in producer_ids:
                for consumer_id in consumer_ids:
                    if producer_id != consumer_id:
                        self.forward_edges[producer_id].add(consumer_id)
                        self.backward_edges[consumer_id].add(producer_id)

    def get_dependencies(self, rule_id: str) -> List[str]:
        """Returns rule IDs that must fire before rule_id can satisfy its derived conditions."""
        return sorted(list(self.backward_edges.get(rule_id, set())))

    def get_dependents(self, rule_id: str) -> List[str]:
        """Returns rule IDs that can fire after rule_id asserts its conclusions."""
        return sorted(list(self.forward_edges.get(rule_id, set())))

    def get_all_chaining_paths(self) -> List[List[str]]:
        """Returns all maximal multi-step chaining sequences (length >= 2)."""
        paths: List[List[str]] = []

        # Find starting rules (rules with no rule dependencies, i.e. root rules)
        root_rules = [r.id for r in self.rules if not self.backward_edges.get(r.id)]

        def dfs(current_id: str, current_path: List[str]):
            children = sorted(list(self.forward_edges.get(current_id, set())))
            if not children:
                if len(current_path) >= 2:
                    paths.append(list(current_path))
                return
            for child in children:
                if child not in current_path:  # cycle prevention
                    dfs(child, current_path + [child])
                else:
                    paths.append(list(current_path + [child]))

        for root in root_rules:
            dfs(root, [root])

        return paths

    def detect_cycles(self) -> List[List[str]]:
        """Detects circular dependencies in the rule base using DFS.
        
        Returns a list of cycle paths if any exist (e.g. [['R01', 'R02', 'R01']]).
        """
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: List[str] = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.append(node)

            for neighbor in sorted(list(self.forward_edges.get(node, set()))):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Cycle found!
                    idx = rec_stack.index(neighbor)
                    cycle_path = rec_stack[idx:] + [neighbor]
                    cycles.append(cycle_path)

            rec_stack.pop()

        for rule in self.rules:
            if rule.id not in visited:
                dfs(rule.id)

        return cycles


class ValidationReport:
    """Stores the results of an automated rule and knowledge base validation run."""
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.duplicate_rule_ids: List[str] = []
        self.duplicate_fact_ids: List[str] = []
        self.invalid_fact_references: List[str] = []
        self.circular_dependencies: List[List[str]] = []
        self.unreachable_rules: List[str] = []
        self.dead_rules: List[str] = []
        self.conflicting_rules: List[str] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


class KnowledgeBaseValidator:
    """Automated validator ensuring soundness and consistency of facts and production rules."""

    @classmethod
    def validate(cls, rules: List[Rule] = PRODUCTION_RULES) -> ValidationReport:
        report = ValidationReport()
        graph = RuleDependencyGraph(rules)

        # 1. Check duplicate Fact IDs and Keys
        seen_fact_ids: Set[str] = set()
        seen_fact_keys: Set[str] = set()
        for fact in DOMAIN_FACTS:
            if fact.id in seen_fact_ids:
                msg = f"Duplicate Fact ID detected: {fact.id}"
                report.errors.append(msg)
                report.duplicate_fact_ids.append(fact.id)
            seen_fact_ids.add(fact.id)

            if fact.key in seen_fact_keys:
                msg = f"Duplicate Fact Key detected: {fact.key}"
                report.errors.append(msg)
            seen_fact_keys.add(fact.key)

        # 2. Check duplicate Rule IDs and Names
        seen_rule_ids: Set[str] = set()
        seen_rule_names: Set[str] = set()
        for rule in rules:
            if rule.id in seen_rule_ids:
                msg = f"Duplicate Rule ID detected: {rule.id}"
                report.errors.append(msg)
                report.duplicate_rule_ids.append(rule.id)
            seen_rule_ids.add(rule.id)

            if rule.name in seen_rule_names:
                msg = f"Duplicate Rule Name detected: {rule.name}"
                report.warnings.append(msg)
            seen_rule_names.add(rule.name)

        # 3. Known valid fact vocabulary (User Askable + Derived + Static)
        all_producible_facts: Set[str] = set(USER_FACT_DEFINITIONS.keys())
        for rule in rules:
            for conc in rule.conclusions.keys():
                all_producible_facts.add(conc)

        # 4. Check for invalid fact references in conditions
        for rule in rules:
            for cond in rule.conditions:
                if cond.fact_key not in all_producible_facts:
                    msg = f"Rule {rule.id} references undefined/unproducible fact key: '{cond.fact_key}'"
                    report.errors.append(msg)
                    report.invalid_fact_references.append(f"{rule.id}->{cond.fact_key}")

        # 5. Check for circular dependencies
        cycles = graph.detect_cycles()
        if cycles:
            report.circular_dependencies = cycles
            for c in cycles:
                report.errors.append(f"Circular dependency detected: {' -> '.join(c)}")

        # 6. Check for unreachable rules
        # A rule is unreachable if it requires an intermediate fact that is neither askable nor produced by any rule
        user_facts = set(USER_FACT_DEFINITIONS.keys())
        all_conclusions = set()
        for r in rules:
            all_conclusions.update(r.conclusions.keys())

        for rule in rules:
            for cond in rule.conditions:
                if cond.fact_key not in user_facts and cond.fact_key not in all_conclusions:
                    msg = f"Rule {rule.id} is unreachable: premise '{cond.fact_key}' cannot be asked or derived."
                    report.errors.append(msg)
                    report.unreachable_rules.append(rule.id)

        # 7. Check for dead rules (internal contradictory conditions in a single rule)
        for rule in rules:
            seen_conditions: Dict[str, Any] = {}
            for cond in rule.conditions:
                if cond.operator == Operator.EQUALS:
                    if cond.fact_key in seen_conditions:
                        if seen_conditions[cond.fact_key] != cond.value:
                            msg = f"Rule {rule.id} can never fire: contradictory conditions on '{cond.fact_key}' ({seen_conditions[cond.fact_key]} vs {cond.value})"
                            report.errors.append(msg)
                            report.dead_rules.append(rule.id)
                    else:
                        seen_conditions[cond.fact_key] = cond.value

        # 8. Check for conflicting terminal conclusions
        # Rules with identical antecedent conditions asserting contradictory diagnoses
        for i, r1 in enumerate(rules):
            if r1.classification != RuleClassification.TERMINAL_DIAGNOSIS:
                continue
            conds1 = {(c.fact_key, c.operator, str(c.value)) for c in r1.conditions}
            diag1 = r1.conclusions.get("diagnosis")
            for j in range(i + 1, len(rules)):
                r2 = rules[j]
                if r2.classification != RuleClassification.TERMINAL_DIAGNOSIS:
                    continue
                conds2 = {(c.fact_key, c.operator, str(c.value)) for c in r2.conditions}
                diag2 = r2.conclusions.get("diagnosis")
                if conds1 == conds2 and diag1 != diag2:
                    msg = f"Conflicting rules detected: {r1.id} and {r2.id} have identical conditions but assert conflicting diagnoses ('{diag1}' vs '{diag2}')"
                    report.errors.append(msg)
                    report.conflicting_rules.append(f"{r1.id}<->{r2.id}")

        return report


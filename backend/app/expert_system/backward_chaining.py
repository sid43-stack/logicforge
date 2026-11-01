"""NetSage Backward Chaining Engine - Goal-Driven Hypothesis Resolution.

Strictly independent of FastAPI, SQLAlchemy, and frontend frameworks.
Evaluates diagnostic hypotheses against the Rule Base and Working Memory.
Identifies supporting rules, evaluates premises recursively, detects cycles,
and identifies unresolved askable premises to drive dynamic question selection.
"""

from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict
from app.expert_system.types import (
    TriState,
    GoalResolutionStatus,
    GoalTreeNode,
    RuleGoalNode,
    PremiseNode,
    RuleClassification,
)
from app.expert_system.knowledge_base import USER_FACT_DEFINITIONS
from app.expert_system.rules import Rule, PRODUCTION_RULES
from app.expert_system.working_memory import WorkingMemory


class BackwardChainingCycleError(Exception):
    """Raised when a circular goal dependency is encountered during backward chaining."""
    pass


# Natural sequential priority for troubleshooting inquiries (Layer 1 -> Layer 2 -> Layer 3 -> ...)
PREMISE_PRIORITY_ORDER: Dict[str, int] = {
    "device_connected": 100,               # Q01: Layer 1/2 Physical/Link
    "using_wifi": 95,                     # Q02: Wireless vs Wired
    "valid_ip": 90,                       # Q03: Layer 3 IP config
    "gateway_reachable": 88,              # Q04: Local Gateway ping
    "external_ip_reachable": 86,          # Q05: External IP ping (8.8.8.8)
    "domain_access": 85,                  # Q06: Layer 7 DNS browsing
    "dns_server_reachable": 84,           # Q13: Specific DNS server IP check
    "ip_is_apipa": 83,                    # Q12: Specific APIPA sub-case
    "wifi_signal_weak": 82,               # Q09: RF Signal strength
    "frequent_disconnections": 81,        # Q08: Intermittent link
    "high_latency_observed": 80,          # Q10: Latency / RTT
    "multiple_devices_affected": 79,      # Q07: Scope (Local host vs network-wide)
    "problem_on_ethernet_too": 78,        # Q14: Specific Wi-Fi vs Ethernet isolation
    "router_reboot_temporarily_fixed": 77,# Q15: Specific Router hardware crash check
    "slow_upload_speed": 76,              # Q11: Bandwidth / Asymmetry
    "heavy_bandwidth_usage": 75,          # Q16: Specific Bufferbloat congestion check
}


class BackwardChainingEngine:
    """Goal-driven inference engine resolving hypotheses and identifying unasked premises."""

    def __init__(self, rules: Optional[List[Rule]] = None):
        self.rules: List[Rule] = rules if rules is not None else list(PRODUCTION_RULES)
        self.rules_by_id: Dict[str, Rule] = {r.id: r for r in self.rules}

        # Index rules by conclusion keys: fact_key -> list of rules that conclude it
        self.rules_by_conclusion: Dict[str, List[Rule]] = defaultdict(list)
        for rule in self.rules:
            for conc_key in rule.conclusions.keys():
                self.rules_by_conclusion[conc_key].append(rule)

        # Set of askable user facts
        self.user_facts: Set[str] = set(USER_FACT_DEFINITIONS.keys())

    def get_supporting_rules(self, goal_key: str, expected_value: Any = True) -> List[Rule]:
        """Returns all rules that conclude the specified goal with matching value, sorted by priority DESC."""
        candidate_rules = self.rules_by_conclusion.get(goal_key, [])
        matching_rules = []
        for r in candidate_rules:
            conc_val = r.conclusions.get(goal_key)
            if conc_val == expected_value:
                matching_rules.append(r)

        # Sort supporting rules by priority DESC
        matching_rules.sort(key=lambda r: (-r.priority, r.id))
        return matching_rules

    def resolve_goal(
        self,
        goal_key: str,
        expected_value: Any = True,
        memory: Optional[WorkingMemory] = None,
        call_stack: Optional[Set[str]] = None,
    ) -> GoalTreeNode:
        """Recursively resolves a diagnostic goal against working memory and production rules.
        
        Args:
            goal_key: Fact key to prove (e.g. 'dns_failure_suspected' or 'diagnosis')
            expected_value: Desired fact value (default True)
            memory: Current WorkingMemory instance (or empty if None)
            call_stack: Set of goal keys currently on the recursion stack for cycle prevention
            
        Returns:
            GoalTreeNode structured tree of rules, conditions, and unasked premises.
        """
        if call_stack is None:
            call_stack = set()

        goal_id = f"{goal_key}={expected_value}"
        if goal_id in call_stack:
            raise BackwardChainingCycleError(f"Cycle detected in backward chaining: '{goal_id}' is already on the call stack.")

        call_stack.add(goal_id)

        all_facts = memory.get_all_facts() if memory is not None else {}
        tree = GoalTreeNode(
            goal_key=goal_key,
            expected_value=expected_value,
            status=GoalResolutionStatus.UNRESOLVED,
            supporting_rules=[],
            unresolved_premises=[],
        )

        # Check if the goal is ALREADY directly known in working memory
        if memory is not None and memory.contains(goal_key):
            actual_val = memory.get_fact(goal_key)
            if actual_val == expected_value:
                tree.status = GoalResolutionStatus.PROVEN
                call_stack.remove(goal_id)
                return tree
            else:
                tree.status = GoalResolutionStatus.REFUTED
                call_stack.remove(goal_id)
                return tree

        # If this goal is a leaf user-askable fact and not known in memory, it cannot be deduced further
        supporting_rules = self.get_supporting_rules(goal_key, expected_value)
        if not supporting_rules:
            if goal_key in self.user_facts:
                if memory is None or not memory.is_known(goal_key):
                    tree.unresolved_premises.append(goal_key)
                tree.status = GoalResolutionStatus.UNRESOLVED
            else:
                # Neither askable nor deducible by any rule
                tree.status = GoalResolutionStatus.REFUTED
            call_stack.remove(goal_id)
            return tree

        # Evaluate each supporting rule
        any_proven = False
        all_refuted = True
        needed_premises: Set[str] = set()

        for rule in supporting_rules:
            rule_node = RuleGoalNode(
                rule_id=rule.id,
                rule_name=rule.name,
                status=GoalResolutionStatus.UNRESOLVED,
                premises=[],
            )

            rule_can_prove = True
            rule_has_unknown = False
            rule_needed_premises: Set[str] = set()

            for cond in rule.conditions:
                actual_val = all_facts.get(cond.fact_key)
                eval_res = cond.evaluate(actual_val)
                is_askable = cond.fact_key in self.user_facts

                premise_node = PremiseNode(
                    fact_key=cond.fact_key,
                    expected_value=cond.value,
                    actual_value=actual_val,
                    status=eval_res,
                    is_askable=is_askable,
                )
                rule_node.premises.append(premise_node)

                if eval_res == TriState.FALSE:
                    rule_can_prove = False
                elif eval_res == TriState.UNKNOWN:
                    rule_has_unknown = True
                    # Check if the condition can be resolved via sub-rules
                    if cond.fact_key in self.rules_by_conclusion:
                        sub_tree = self.resolve_goal(
                            goal_key=cond.fact_key,
                            expected_value=cond.value,
                            memory=memory,
                            call_stack=call_stack,
                        )
                        if sub_tree.status == GoalResolutionStatus.PROVEN:
                            premise_node.status = TriState.TRUE
                        elif sub_tree.status == GoalResolutionStatus.REFUTED:
                            premise_node.status = TriState.FALSE
                            rule_can_prove = False
                        else:
                            rule_needed_premises.update(sub_tree.unresolved_premises)
                    elif is_askable:
                        if memory is None or not memory.is_known(cond.fact_key):
                            rule_needed_premises.add(cond.fact_key)
                    else:
                        rule_can_prove = False

            if rule_can_prove and not rule_has_unknown:
                rule_node.status = GoalResolutionStatus.PROVEN
                any_proven = True
                all_refuted = False
            elif not rule_can_prove:
                rule_node.status = GoalResolutionStatus.REFUTED
            else:
                rule_node.status = GoalResolutionStatus.UNRESOLVED
                all_refuted = False
                # Crucial soundness constraint: Only accumulate premises from candidate rules that are NOT refuted!
                needed_premises.update(rule_needed_premises)

            tree.supporting_rules.append(rule_node)

        if any_proven:
            tree.status = GoalResolutionStatus.PROVEN
        elif all_refuted:
            tree.status = GoalResolutionStatus.REFUTED
        else:
            tree.status = GoalResolutionStatus.UNRESOLVED
            tree.unresolved_premises = sorted(
                list(needed_premises),
                key=lambda k: (-PREMISE_PRIORITY_ORDER.get(k, 0), k)
            )

        call_stack.remove(goal_id)
        return tree

    def get_candidate_terminal_diagnoses(self) -> List[Tuple[str, Rule]]:
        """Returns list of (diagnosis_name, rule) for all terminal production rules."""
        results = []
        for rule in self.rules:
            if rule.classification == RuleClassification.TERMINAL_DIAGNOSIS:
                diag = rule.conclusions.get("diagnosis")
                if diag:
                    results.append((diag, rule))
        results.sort(key=lambda item: (-item[1].priority, item[0]))
        return results

    def find_next_askable_premise(
        self,
        memory: WorkingMemory,
        candidate_diagnoses: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Identifies the next unasked fact in logical sequence for the most plausible hypothesis."""
        all_candidates = self.get_candidate_terminal_diagnoses()
        if candidate_diagnoses:
            all_candidates = [item for item in all_candidates if item[0] in candidate_diagnoses]

        # Prioritize hypotheses that already have partial evidence proven in working memory
        def hypothesis_relevance(item: Tuple[str, Rule]) -> Tuple[int, int]:
            diag_name, rule = item
            tree = self.resolve_goal("diagnosis", expected_value=diag_name, memory=memory)
            if tree.status != GoalResolutionStatus.UNRESOLVED:
                return (-1, 0)
            # Count proven premises to prioritize actively emerging diagnoses
            proven_count = 0
            for sup_rule in tree.supporting_rules:
                for prem in sup_rule.premises:
                    if prem.status == TriState.TRUE:
                        proven_count += 1
            return (proven_count, rule.priority)

        sorted_candidates = sorted(all_candidates, key=hypothesis_relevance, reverse=True)

        for diag_name, rule in sorted_candidates:
            tree = self.resolve_goal("diagnosis", expected_value=diag_name, memory=memory)
            if tree.status == GoalResolutionStatus.UNRESOLVED and tree.unresolved_premises:
                unasked = [p for p in tree.unresolved_premises if not memory.is_known(p)]
                if unasked:
                    unasked.sort(key=lambda k: (-PREMISE_PRIORITY_ORDER.get(k, 0), k))
                    return unasked[0]

        return None

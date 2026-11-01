"""NetSage Knowledge Base & Rule Base Explorer Endpoints.

Provides inspection of static domain knowledge, production rules,
truth-maintenance metadata, and topological dependency graph metrics.
"""

from typing import List, Optional, Dict
from fastapi import APIRouter, Query

from app.expert_system.knowledge_base import get_all_facts
from app.expert_system.rules import get_all_rules, RuleClassification
from app.expert_system.rule_graph import RuleDependencyGraph
from app.schemas.knowledge import (
    FactResponse,
    RuleResponse,
    KnowledgeStatsResponse,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/facts", response_model=List[FactResponse])
def get_knowledge_facts(
    category: Optional[str] = Query(None, description="Filter by problem category (e.g. IP_DHCP, DNS, WIFI)"),
    source_type: Optional[str] = Query(None, description="Filter by source type (STATIC_DOMAIN, USER_INPUT, RULE_DERIVED)"),
):
    """Returns all network domain facts with their truth-maintenance metadata and source classification."""
    all_facts = get_all_facts()
    results = []

    for f in all_facts:
        if category and f.category.value.upper() != category.upper():
            continue
        if source_type and f.source_type.value.upper() != source_type.upper():
            continue

        results.append(
            FactResponse(
                id=f.id,
                key=f.key,
                statement=f.statement,
                category=f.category.value,
                source_type=f.source_type.value,
                description=f.description,
                diagnostic_relevance=f.diagnostic_relevance,
            )
        )

    return results


@router.get("/rules", response_model=List[RuleResponse])
def get_knowledge_rules(
    category: Optional[str] = Query(None, description="Filter by rule category (e.g. IP_DHCP, DNS, ISP)"),
    classification: Optional[str] = Query(None, description="Filter by classification (INTERMEDIATE, TERMINAL)"),
):
    """Returns all production rules with their priority, conditions, conclusions, and explanations."""
    all_rules = get_all_rules()
    results = []

    for r in all_rules:
        if category and r.category.value.upper() != category.upper():
            continue
        if classification and r.classification.value.upper() != classification.upper():
            continue

        conds_list = [
            {
                "fact_key": c.fact_key,
                "expected_value": c.value,
                "operator": c.operator.value if hasattr(c.operator, "value") else str(c.operator),
            }
            for c in r.conditions
        ]

        results.append(
            RuleResponse(
                id=r.id,
                name=r.name,
                category=r.category.value,
                classification=r.classification.value,
                priority=r.priority,
                conditions=conds_list,
                conclusions=r.conclusions,
                explanation=r.explanation,
            )
        )

    return results


@router.get("/stats", response_model=KnowledgeStatsResponse)
def get_knowledge_stats():
    """Computes aggregate structural metrics across facts, rules, and the rule dependency graph."""
    facts = get_all_facts()
    rules = get_all_rules()

    # Fact aggregations
    facts_by_source_type: Dict[str, int] = {}
    facts_by_category: Dict[str, int] = {}
    for f in facts:
        st_val = f.source_type.value
        cat_val = f.category.value
        facts_by_source_type[st_val] = facts_by_source_type.get(st_val, 0) + 1
        facts_by_category[cat_val] = facts_by_category.get(cat_val, 0) + 1

    # Rule aggregations
    rules_by_category: Dict[str, int] = {}
    rules_by_classification: Dict[str, int] = {}
    terminal_count = 0
    intermediate_count = 0

    for r in rules:
        cat_val = r.category.value
        cls_val = r.classification.value
        rules_by_category[cat_val] = rules_by_category.get(cat_val, 0) + 1
        rules_by_classification[cls_val] = rules_by_classification.get(cls_val, 0) + 1
        if r.classification == RuleClassification.TERMINAL_DIAGNOSIS:
            terminal_count += 1
        else:
            intermediate_count += 1

    # Dependency graph topology
    graph = RuleDependencyGraph(rules)
    paths = graph.get_all_chaining_paths()
    chaining_paths_count = len(paths)
    max_depth = max((len(p) for p in paths), default=0)

    return KnowledgeStatsResponse(
        total_facts=len(facts),
        total_rules=len(rules),
        facts_by_source_type=facts_by_source_type,
        facts_by_category=facts_by_category,
        rules_by_category=rules_by_category,
        rules_by_classification=rules_by_classification,
        terminal_rules_count=terminal_count,
        intermediate_rules_count=intermediate_count,
        chaining_paths_count=chaining_paths_count,
        max_chaining_depth=max_depth,
    )

"""NetSage Knowledge Base & Rule Base Schemas.

Defines schemas for inspecting the static domain knowledge, production rules,
and dependency graph statistics through the Knowledge Base Explorer.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FactResponse(BaseModel):
    """Network fact representation for the Knowledge Base Explorer."""
    id: str
    key: str
    statement: str
    category: str
    source_type: str
    description: str
    diagnostic_relevance: str


class RuleConditionResponse(BaseModel):
    fact_key: str
    expected_value: Any
    operator: str = "=="


class RuleResponse(BaseModel):
    """Production rule representation for the Knowledge Base Explorer."""
    id: str
    name: str
    category: str
    classification: str
    priority: int
    conditions: List[Dict[str, Any]]
    conclusions: Dict[str, Any]
    explanation: str


class KnowledgeStatsResponse(BaseModel):
    """Aggregate statistics regarding facts, rules, and dependency graph topology."""
    total_facts: int
    total_rules: int
    facts_by_source_type: Dict[str, int]
    facts_by_category: Dict[str, int]
    rules_by_category: Dict[str, int]
    rules_by_classification: Dict[str, int]
    terminal_rules_count: int
    intermediate_rules_count: int
    chaining_paths_count: int
    max_chaining_depth: int

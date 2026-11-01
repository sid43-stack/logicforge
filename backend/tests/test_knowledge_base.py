import pytest
from app.expert_system.types import FactCategory, FactSourceType
from app.expert_system.knowledge_base import (
    DOMAIN_FACTS,
    FACTS_BY_ID,
    FACTS_BY_KEY,
    USER_FACT_DEFINITIONS,
    DERIVED_FACT_DEFINITIONS,
    get_fact,
    get_all_facts,
    get_facts_by_category,
)


def test_knowledge_base_fact_count():
    """Verify that NetSage contains at least 28 static domain facts (requirement 1)."""
    assert len(DOMAIN_FACTS) >= 28
    assert len(DOMAIN_FACTS) == 30


def test_fact_ids_and_keys_uniqueness():
    """Verify that all fact IDs and keys are strictly unique."""
    fact_ids = [f.id for f in DOMAIN_FACTS]
    fact_keys = [f.key for f in DOMAIN_FACTS]

    assert len(fact_ids) == len(set(fact_ids)), "Duplicate Fact ID found in knowledge base"
    assert len(fact_keys) == len(set(fact_keys)), "Duplicate Fact key found in knowledge base"


def test_fact_metadata_completeness():
    """Verify that every fact contains complete, non-empty metadata."""
    for fact in DOMAIN_FACTS:
        assert fact.id.startswith("F")
        assert len(fact.key) > 0
        assert len(fact.statement) > 10
        assert len(fact.description) > 10
        assert len(fact.diagnostic_relevance) > 10
        assert fact.source_type == FactSourceType.STATIC_DOMAIN
        assert isinstance(fact.category, FactCategory)


def test_fact_retrieval_functions():
    """Test get_fact by ID and key, get_all_facts, and get_facts_by_category."""
    # Lookup by ID
    f01 = get_fact("F01")
    assert f01 is not None
    assert f01.key == "router_function"

    # Lookup by Key
    f_dns = get_fact("dns_function")
    assert f_dns is not None
    assert f_dns.id == "F03"

    # Non-existent fact
    assert get_fact("F999") is None

    # Category filtering
    dns_facts = get_facts_by_category(FactCategory.DNS)
    assert len(dns_facts) >= 5
    for f in dns_facts:
        assert f.category == FactCategory.DNS


def test_knowledge_tier_segregation():
    """Verify clean segregation between static domain knowledge, user facts, and derived facts."""
    domain_keys = {f.key for f in DOMAIN_FACTS}
    user_keys = set(USER_FACT_DEFINITIONS.keys())
    derived_keys = set(DERIVED_FACT_DEFINITIONS.keys())

    # User facts and derived facts must have defined schemas
    assert len(user_keys) >= 15
    assert len(derived_keys) >= 15

    # User facts must have questions/statements and category
    for u_key, u_meta in USER_FACT_DEFINITIONS.items():
        assert "statement" in u_meta
        assert "category" in u_meta
        assert "type" in u_meta

    # Derived facts must have statements and categories
    for d_key, d_meta in DERIVED_FACT_DEFINITIONS.items():
        assert "statement" in d_meta
        assert "category" in d_meta


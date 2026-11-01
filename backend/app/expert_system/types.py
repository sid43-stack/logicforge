"""NetSage Expert System - Fundamental Type Definitions.

Strictly independent of FastAPI, SQLAlchemy, and frontend frameworks.
Provides TriState 3-valued logic, Condition models, and Explanation trace schemas.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TriState(str, Enum):
    """Three-valued logic for working memory and condition evaluation."""
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_bool(cls, val: Optional[bool]) -> "TriState":
        if val is True:
            return cls.TRUE
        elif val is False:
            return cls.FALSE
        return cls.UNKNOWN

    def to_bool(self) -> Optional[bool]:
        if self == TriState.TRUE:
            return True
        elif self == TriState.FALSE:
            return False
        return None


class Operator(str, Enum):
    """Comparison operators for rule conditions."""
    EQUALS = "=="
    NOT_EQUALS = "!="
    IN = "in"
    NOT_IN = "not_in"


class FactCategory(str, Enum):
    """Domain categories for networking facts."""
    GENERAL = "GENERAL"
    IP_DHCP = "IP_DHCP"
    GATEWAY = "GATEWAY"
    DNS = "DNS"
    WIFI = "WIFI"
    PERFORMANCE = "PERFORMANCE"
    ISP = "ISP"


class FactSourceType(str, Enum):
    """Explicitly distinguishes knowledge tiers."""
    STATIC_DOMAIN = "STATIC_DOMAIN"      # Immutable textbook / networking axioms
    USER_INPUT = "USER_INPUT"            # Asserted directly by user via dynamic questions
    RULE_DERIVED = "RULE_DERIVED"        # Asserted by fired production rules


class RuleCategory(str, Enum):
    """Diagnostic problem categories."""
    IP_DHCP = "IP_DHCP"
    GATEWAY = "GATEWAY"
    DNS = "DNS"
    WIFI = "WIFI"
    PERFORMANCE = "PERFORMANCE"
    ISP = "ISP"


class RuleClassification(str, Enum):
    """Identifies rule role in the inference pipeline."""
    INTERMEDIATE = "INTERMEDIATE"              # Derives intermediate diagnostic facts
    TERMINAL_DIAGNOSIS = "TERMINAL_DIAGNOSIS"  # Concludes a final network fault diagnosis
    RECOMMENDATION = "RECOMMENDATION"          # Concludes remediation troubleshooting steps


class GoalResolutionStatus(str, Enum):
    """Status of backward-chaining goal resolution."""
    PROVEN = "PROVEN"          # All conditions satisfied; goal is TRUE
    REFUTED = "REFUTED"        # Conditions definitively refuted; goal cannot be TRUE
    UNRESOLVED = "UNRESOLVED"  # Needs unasked premises to determine truth value


class Condition(BaseModel):
    """An antecedent condition required for a production rule to fire."""
    fact_key: str
    operator: Operator = Operator.EQUALS
    value: Any

    def evaluate(self, actual_value: Any) -> TriState:
        """Evaluates this condition against an actual fact value using 3-valued logic."""
        if actual_value is None or actual_value == TriState.UNKNOWN:
            return TriState.UNKNOWN

        # If actual_value is a TriState string, normalize for comparison
        if isinstance(actual_value, TriState):
            if self.value is True and actual_value == TriState.TRUE:
                return TriState.TRUE
            elif self.value is False and actual_value == TriState.FALSE:
                return TriState.TRUE
            elif self.value is True and actual_value == TriState.FALSE:
                return TriState.FALSE
            elif self.value is False and actual_value == TriState.TRUE:
                return TriState.FALSE

        if self.operator == Operator.EQUALS:
            return TriState.TRUE if actual_value == self.value else TriState.FALSE
        elif self.operator == Operator.NOT_EQUALS:
            return TriState.TRUE if actual_value != self.value else TriState.FALSE
        elif self.operator == Operator.IN:
            return TriState.TRUE if actual_value in self.value else TriState.FALSE
        elif self.operator == Operator.NOT_IN:
            return TriState.TRUE if actual_value not in self.value else TriState.FALSE

        return TriState.UNKNOWN


class FactEntry(BaseModel):
    """A single fact stored in Working Memory with full provenance metadata."""
    key: str
    value: Any
    tristate: TriState
    source_type: FactSourceType
    source_id: str = "USER"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InferenceTraceStep(BaseModel):
    """Recorded when a production rule fires during forward chaining."""
    execution_order: int
    rule_id: str
    rule_name: str
    category: RuleCategory
    classification: RuleClassification
    conditions_evaluated: Dict[str, Any]
    conclusion_asserted: Dict[str, Any]
    explanation: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PremiseNode(BaseModel):
    """A condition node in a backward-chaining goal tree."""
    fact_key: str
    expected_value: Any
    actual_value: Any
    status: TriState
    is_askable: bool


class RuleGoalNode(BaseModel):
    """A rule node in a backward-chaining goal tree."""
    rule_id: str
    rule_name: str
    status: GoalResolutionStatus
    premises: List[PremiseNode] = Field(default_factory=list)


class GoalTreeNode(BaseModel):
    """Hierarchical goal-resolution tree for Explanation Center visualization."""
    goal_key: str
    expected_value: Any
    status: GoalResolutionStatus
    supporting_rules: List[RuleGoalNode] = Field(default_factory=list)
    unresolved_premises: List[str] = Field(default_factory=list)

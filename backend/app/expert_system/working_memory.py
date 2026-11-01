"""NetSage Working Memory - Dynamic State & Truth Maintenance Engine.

Strictly independent of FastAPI, SQLAlchemy, and frontend frameworks.
Maintains 3-valued truth states (TRUE, FALSE, UNKNOWN), tracks fact provenance,
maintains an audit history of all state mutations, and provides JSON snapshot serialization.
"""

from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime, timezone
from app.expert_system.types import (
    TriState,
    FactSourceType,
    FactEntry,
)


class ContradictionError(Exception):
    """Raised when an asserted fact directly contradicts an already established fact."""
    pass


class WorkingMemory:
    """Dynamic working memory store for expert system execution."""

    def __init__(self):
        # Maps fact_key -> FactEntry
        self._entries: Dict[str, FactEntry] = {}
        # Audit log of mutations
        self._history: List[Dict[str, Any]] = []
        # Registered conflicts/contradictions encountered
        self._conflicts: List[Dict[str, Any]] = []

    def set_fact(
        self,
        key: str,
        value: Any,
        source_type: Union[FactSourceType, str] = FactSourceType.USER_INPUT,
        source_id: str = "USER",
        allow_override: bool = False,
    ) -> bool:
        if isinstance(source_type, str):
            if source_type in ("USER", "USER_INPUT"):
                source_type = FactSourceType.USER_INPUT
            elif source_type in ("RULE", "RULE_DERIVED"):
                source_type = FactSourceType.RULE_DERIVED
            elif source_type in ("STATIC", "STATIC_DOMAIN"):
                source_type = FactSourceType.STATIC_DOMAIN
            else:
                source_type = FactSourceType(source_type)
        """Asserts a fact into working memory.
        
        Args:
            key: Name of the fact (e.g. 'gateway_reachable')
            value: Value (typically bool or specific string)
            source_type: USER_INPUT, RULE_DERIVED, or STATIC_DOMAIN
            source_id: 'USER', rule_id (e.g. 'R01'), or 'STATIC'
            allow_override: Whether to permit overwriting an established fact
            
        Returns:
            True if the fact was successfully asserted or changed, False if already identical.
            
        Raises:
            ContradictionError: If an attempt is made to assert an opposing value without allow_override.
        """
        tristate = TriState.from_bool(value) if isinstance(value, bool) else (
            value if isinstance(value, TriState) else TriState.TRUE
        )

        existing = self._entries.get(key)
        if existing is not None:
            # If value is already identical, no-op
            if existing.value == value and existing.tristate == tristate:
                return False

            # If existing is UNKNOWN, updating to a concrete value is valid refinement
            if existing.tristate == TriState.UNKNOWN and tristate != TriState.UNKNOWN:
                pass  # Allow refinement
            elif not allow_override:
                conflict_msg = (
                    f"Contradiction on fact '{key}': existing={existing.value} "
                    f"({existing.source_type.value}:{existing.source_id}) vs new={value} "
                    f"({source_type.value}:{source_id})"
                )
                self._conflicts.append({
                    "key": key,
                    "existing_value": existing.value,
                    "existing_source": existing.source_id,
                    "new_value": value,
                    "new_source": source_id,
                    "message": conflict_msg,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                raise ContradictionError(conflict_msg)

        entry = FactEntry(
            key=key,
            value=value,
            tristate=tristate,
            source_type=source_type,
            source_id=source_id,
            timestamp=datetime.now(timezone.utc),
        )

        self._entries[key] = entry

        # Record audit change
        self._history.append({
            "action": "UPDATE" if existing is not None else "ASSERT",
            "key": key,
            "value": value,
            "tristate": tristate.value,
            "source_type": source_type.value,
            "source_id": source_id,
            "timestamp": entry.timestamp.isoformat(),
        })

        return True

    def get_fact(self, key: str, default: Any = None) -> Any:
        """Retrieves raw value of a fact, or default if missing or UNKNOWN."""
        entry = self._entries.get(key)
        if entry is None or entry.tristate == TriState.UNKNOWN:
            return default
        return entry.value

    def get_tristate(self, key: str) -> TriState:
        """Retrieves the 3-valued truth state (TRUE, FALSE, UNKNOWN).
        
        Important: A missing fact is ALWAYS UNKNOWN, never FALSE.
        """
        entry = self._entries.get(key)
        if entry is None:
            return TriState.UNKNOWN
        return entry.tristate

    def get_fact_entry(self, key: str) -> Optional[FactEntry]:
        """Retrieves the full metadata FactEntry object."""
        return self._entries.get(key)

    def contains(self, key: str) -> bool:
        """Checks if a fact is present and has a concrete truth value (not UNKNOWN)."""
        entry = self._entries.get(key)
        return entry is not None and entry.tristate != TriState.UNKNOWN

    def is_known(self, key: str) -> bool:
        """Checks if a fact has been asserted (even if explicitly UNKNOWN)."""
        return key in self._entries

    def get_all_facts(self) -> Dict[str, Any]:
        """Returns key-value mapping of all known facts."""
        return {k: v.value for k, v in self._entries.items() if v.tristate != TriState.UNKNOWN}

    def get_all_tristates(self) -> Dict[str, TriState]:
        """Returns key-tristate mapping of all asserted facts."""
        return {k: v.tristate for k, v in self._entries.items()}

    def get_facts_by_source(self, source_type: FactSourceType) -> Dict[str, Any]:
        """Returns facts filtered by their knowledge source tier."""
        return {
            k: v.value
            for k, v in self._entries.items()
            if v.source_type == source_type and v.tristate != TriState.UNKNOWN
        }

    def get_change_history(self) -> List[Dict[str, Any]]:
        """Returns ordered audit trail of all fact assertions and updates."""
        return list(self._history)

    def get_conflicts(self) -> List[Dict[str, Any]]:
        """Returns all recorded contradictions."""
        return list(self._conflicts)

    def has_conflicts(self) -> bool:
        """Checks if any contradictions were flagged."""
        return len(self._conflicts) > 0

    def clear(self):
        """Resets working memory to empty state."""
        self._entries.clear()
        self._history.clear()
        self._conflicts.clear()

    # ---------------------------------------------------------------------
    # JSON Snapshot Serialization & Restoration
    # ---------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serializes working memory to a JSON-compatible dictionary."""
        return {
            "entries": {
                k: {
                    "key": v.key,
                    "value": v.value,
                    "tristate": v.tristate.value,
                    "source_type": v.source_type.value,
                    "source_id": v.source_id,
                    "timestamp": v.timestamp.isoformat(),
                }
                for k, v in self._entries.items()
            },
            "history": self._history,
            "conflicts": self._conflicts,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkingMemory":
        """Reconstructs working memory state from a serialized dictionary."""
        wm = cls()
        for k, v in data.get("entries", {}).items():
            entry = FactEntry(
                key=v["key"],
                value=v["value"],
                tristate=TriState(v["tristate"]),
                source_type=FactSourceType(v["source_type"]),
                source_id=v.get("source_id", "USER"),
                timestamp=datetime.fromisoformat(v["timestamp"]),
            )
            wm._entries[k] = entry
        wm._history = list(data.get("history", []))
        wm._conflicts = list(data.get("conflicts", []))
        return wm


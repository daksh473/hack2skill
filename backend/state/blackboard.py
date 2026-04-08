"""
Blackboard — session-scoped shared context for inter-agent communication.

Each agent posts its results to the blackboard so downstream agents (and the
orchestrator) can see what happened.  The blackboard is ephemeral per request
and is persisted to execution_history after the session completes.
"""
from __future__ import annotations
import json
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class BlackboardEntry:
    agent_name: str
    task_description: str
    result: str
    status: str = "done"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class Blackboard:
    """In-memory shared context for a single execution session."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self._entries: list[BlackboardEntry] = []
        self._metadata: dict = {}

    # ── Write ──────────────────────────────────────────────────────────
    def post(self, agent_name: str, task_description: str, result: str, status: str = "done"):
        """Agent posts its result to the shared blackboard."""
        self._entries.append(
            BlackboardEntry(
                agent_name=agent_name,
                task_description=task_description,
                result=result,
                status=status,
            )
        )

    def set_metadata(self, key: str, value):
        """Store arbitrary session metadata (user_id, original query, etc.)."""
        self._metadata[key] = value

    # ── Read ───────────────────────────────────────────────────────────
    def get_entries(self, agent_name: str = "") -> list[BlackboardEntry]:
        """Get all entries, optionally filtered by agent name."""
        if agent_name:
            return [e for e in self._entries if e.agent_name == agent_name]
        return list(self._entries)

    def get_latest(self, agent_name: str = "") -> BlackboardEntry | None:
        """Get the most recent entry, optionally for a specific agent."""
        entries = self.get_entries(agent_name)
        return entries[-1] if entries else None

    def get_context_summary(self) -> str:
        """Generate a text summary of all blackboard entries for LLM context."""
        if not self._entries:
            return "No prior agent results available."

        lines = ["## Blackboard — Prior Agent Results"]
        for e in self._entries:
            lines.append(f"\n### {e.agent_name} ({e.status})")
            lines.append(f"**Task**: {e.task_description}")
            lines.append(f"**Result**: {e.result}")
        return "\n".join(lines)

    def get_metadata(self, key: str, default=None):
        return self._metadata.get(key, default)

    # ── Serialization ──────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "metadata": self._metadata,
            "entries": [
                {
                    "agent_name": e.agent_name,
                    "task_description": e.task_description,
                    "result": e.result,
                    "status": e.status,
                    "timestamp": e.timestamp,
                }
                for e in self._entries
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def clear(self):
        self._entries.clear()
        self._metadata.clear()

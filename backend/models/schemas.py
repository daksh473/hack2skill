"""
Pydantic schemas for API request/response validation.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


# ── Requests ───────────────────────────────────────────────────────────
class ExecuteRequest(BaseModel):
    user_id: str = Field(default="user_123", description="User identifier")
    query: str = Field(..., description="Natural language instruction")


class PreferenceRequest(BaseModel):
    user_id: str = "user_123"
    key: str
    value: str


# ── Response sub-models ───────────────────────────────────────────────
class AgentThought(BaseModel):
    agent_name: str
    action: str
    reasoning: str = ""
    result: str = ""
    status: str = "running"  # running | done | error


class SubTaskPlan(BaseModel):
    agent: str
    description: str
    status: str = "pending"


class TaskPlan(BaseModel):
    original_query: str
    subtasks: list[SubTaskPlan] = []


# ── Responses ─────────────────────────────────────────────────────────
class ExecuteResponse(BaseModel):
    success: bool = True
    plan: Optional[TaskPlan] = None
    thoughts: list[AgentThought] = []
    summary: str = ""
    error: Optional[str] = None


class HistoryItem(BaseModel):
    id: int
    query: str
    plan: str = ""
    results: str = ""
    created_at: str = ""


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    agents: list[str] = ["scheduler", "taskmaster", "librarian"]

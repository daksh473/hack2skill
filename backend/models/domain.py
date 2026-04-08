"""
Domain objects used across the system.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Event:
    id: int | None = None
    title: str = ""
    start_time: str = ""
    end_time: str = ""
    description: str = ""
    location: str = ""
    user_id: str = "default"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Task:
    id: int | None = None
    title: str = ""
    description: str = ""
    priority: int = 3          # 1 (low) → 5 (critical)
    status: str = "pending"    # pending | in_progress | done | cancelled
    due_date: str = ""
    user_id: str = "default"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Note:
    id: int | None = None
    title: str = ""
    content: str = ""
    tags: str = ""
    user_id: str = "default"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

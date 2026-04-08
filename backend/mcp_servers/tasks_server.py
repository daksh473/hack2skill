"""
Tasks MCP Server — exposes task management tools via the Model Context Protocol.
"""
import json
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "aether.db"


async def _get_db():
    return await aiosqlite.connect(str(DB_PATH))


# ── Tool: add_task ─────────────────────────────────────────────────────
async def add_task(
    title: str,
    description: str = "",
    priority: int = 3,
    due_date: str = "",
    user_id: str = "user_123",
) -> str:
    """Create a new task with a priority level (1=low, 5=critical)."""
    db = await _get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO tasks (title, description, priority, due_date, user_id) VALUES (?, ?, ?, ?, ?)",
            (title, description, min(max(priority, 1), 5), due_date, user_id),
        )
        await db.commit()
        return json.dumps({"status": "created", "task_id": cursor.lastrowid, "title": title, "priority": priority})
    finally:
        await db.close()


# ── Tool: list_tasks ───────────────────────────────────────────────────
async def list_tasks(
    status: str = "",
    priority: int = 0,
    due_date: str = "",
    user_id: str = "user_123",
) -> str:
    """List tasks with optional filters for status, priority, and due_date."""
    db = await _get_db()
    try:
        query = "SELECT id, title, description, priority, status, due_date FROM tasks WHERE user_id = ?"
        params: list = [user_id]

        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority >= ?"
            params.append(priority)
        if due_date:
            query += " AND due_date = ?"
            params.append(due_date)

        query += " ORDER BY priority DESC, due_date ASC"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        tasks = [
            {"id": r[0], "title": r[1], "description": r[2], "priority": r[3], "status": r[4], "due_date": r[5]}
            for r in rows
        ]
        return json.dumps({"tasks": tasks, "count": len(tasks)})
    finally:
        await db.close()


# ── Tool: update_task ──────────────────────────────────────────────────
async def update_task(
    task_id: int,
    status: str = "",
    priority: int = 0,
    due_date: str = "",
    user_id: str = "user_123",
) -> str:
    """Update a task's status, priority, or due_date."""
    db = await _get_db()
    try:
        updates = []
        params = []
        if status:
            updates.append("status = ?")
            params.append(status)
        if priority:
            updates.append("priority = ?")
            params.append(min(max(priority, 1), 5))
        if due_date:
            updates.append("due_date = ?")
            params.append(due_date)

        if not updates:
            return json.dumps({"status": "no_changes", "task_id": task_id})

        params.extend([task_id, user_id])
        await db.execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
            params,
        )
        await db.commit()
        return json.dumps({"status": "updated", "task_id": task_id, "changes": updates})
    finally:
        await db.close()


# ── Tool: delete_task ──────────────────────────────────────────────────
async def delete_task(task_id: int, user_id: str = "user_123") -> str:
    """Delete a task by ID."""
    db = await _get_db()
    try:
        await db.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        await db.commit()
        return json.dumps({"status": "deleted", "task_id": task_id})
    finally:
        await db.close()


# ── Tool: reschedule_tasks ─────────────────────────────────────────────
async def reschedule_tasks(
    from_date: str,
    to_date: str,
    user_id: str = "user_123",
    status_filter: str = "pending",
) -> str:
    """Move all tasks from one date to another. Only moves tasks matching the status filter."""
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT id, title, priority FROM tasks WHERE user_id = ? AND due_date = ? AND status = ?",
            (user_id, from_date, status_filter),
        )
        affected = await cursor.fetchall()

        await db.execute(
            "UPDATE tasks SET due_date = ? WHERE user_id = ? AND due_date = ? AND status = ?",
            (to_date, user_id, from_date, status_filter),
        )
        await db.commit()

        moved = [{"id": r[0], "title": r[1], "priority": r[2]} for r in affected]
        return json.dumps({"status": "rescheduled", "from": from_date, "to": to_date, "moved_tasks": moved, "count": len(moved)})
    finally:
        await db.close()


# ── Tool registry ─────────────────────────────────────────────────────
TASK_TOOLS = {
    "add_task": add_task,
    "list_tasks": list_tasks,
    "update_task": update_task,
    "delete_task": delete_task,
    "reschedule_tasks": reschedule_tasks,
}

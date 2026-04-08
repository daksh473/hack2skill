"""
Long-term memory — stores user preferences and execution history in SQLite
so the system can learn from past decisions.
"""
import json
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "aether.db"


async def _get_db():
    return await aiosqlite.connect(str(DB_PATH))


# ── User Preferences ──────────────────────────────────────────────────
async def get_preference(user_id: str, key: str, default: str = "") -> str:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT value FROM user_preferences WHERE user_id = ? AND key = ?",
            (user_id, key),
        )
        row = await cursor.fetchone()
        return row[0] if row else default
    finally:
        await db.close()


async def set_preference(user_id: str, key: str, value: str):
    db = await _get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO user_preferences (user_id, key, value) VALUES (?, ?, ?)",
            (user_id, key, value),
        )
        await db.commit()
    finally:
        await db.close()


async def get_all_preferences(user_id: str) -> dict:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT key, value FROM user_preferences WHERE user_id = ?",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return {r[0]: r[1] for r in rows}
    finally:
        await db.close()


# ── Execution History ──────────────────────────────────────────────────
async def save_execution(user_id: str, query: str, plan: str, results: str):
    db = await _get_db()
    try:
        await db.execute(
            "INSERT INTO execution_history (user_id, query, plan, results) VALUES (?, ?, ?, ?)",
            (user_id, query, plan, results),
        )
        await db.commit()
    finally:
        await db.close()


async def get_history(user_id: str, limit: int = 20) -> list[dict]:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT id, query, plan, results, created_at FROM execution_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "query": r[1], "plan": r[2], "results": r[3], "created_at": r[4]}
            for r in rows
        ]
    finally:
        await db.close()


async def get_recent_context(user_id: str, limit: int = 5) -> str:
    """Get a short summary of recent executions for context injection."""
    history = await get_history(user_id, limit)
    if not history:
        return "No recent execution history."
    lines = ["## Recent History (last {} actions)".format(len(history))]
    for h in history:
        lines.append(f"- **Query**: {h['query']}")
        lines.append(f"  **Result**: {h['results'][:200]}")
    return "\n".join(lines)

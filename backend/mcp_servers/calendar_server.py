"""
Calendar MCP Server — exposes scheduling tools via the Model Context Protocol.
Backed by SQLite for a self-contained hackathon demo.
"""
import json
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "aether.db"


async def _get_db():
    return await aiosqlite.connect(str(DB_PATH))


# ── Tool: create_event ─────────────────────────────────────────────────
async def create_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    user_id: str = "user_123",
) -> str:
    """Create a new calendar event. Returns confirmation with the event ID."""
    db = await _get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO events (title, start_time, end_time, description, location, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (title, start_time, end_time, description, location, user_id),
        )
        await db.commit()
        return json.dumps({"status": "created", "event_id": cursor.lastrowid, "title": title})
    finally:
        await db.close()


# ── Tool: list_events ──────────────────────────────────────────────────
async def list_events(date: str = "", user_id: str = "user_123") -> str:
    """List calendar events. If date is provided (YYYY-MM-DD), filter to that day."""
    db = await _get_db()
    try:
        if date:
            cursor = await db.execute(
                "SELECT id, title, start_time, end_time, description, location FROM events WHERE user_id = ? AND start_time LIKE ? ORDER BY start_time",
                (user_id, f"{date}%"),
            )
        else:
            cursor = await db.execute(
                "SELECT id, title, start_time, end_time, description, location FROM events WHERE user_id = ? ORDER BY start_time",
                (user_id,),
            )
        rows = await cursor.fetchall()
        events = [
            {"id": r[0], "title": r[1], "start_time": r[2], "end_time": r[3], "description": r[4], "location": r[5]}
            for r in rows
        ]
        return json.dumps({"events": events, "count": len(events)})
    finally:
        await db.close()


# ── Tool: check_conflicts ─────────────────────────────────────────────
async def check_conflicts(start_time: str, end_time: str, user_id: str = "user_123") -> str:
    """Check if a time slot conflicts with existing events."""
    db = await _get_db()
    try:
        cursor = await db.execute(
            """SELECT id, title, start_time, end_time FROM events
               WHERE user_id = ? AND start_time < ? AND end_time > ?
               ORDER BY start_time""",
            (user_id, end_time, start_time),
        )
        rows = await cursor.fetchall()
        conflicts = [{"id": r[0], "title": r[1], "start_time": r[2], "end_time": r[3]} for r in rows]
        return json.dumps({"has_conflicts": len(conflicts) > 0, "conflicts": conflicts})
    finally:
        await db.close()


# ── Tool: delete_event ─────────────────────────────────────────────────
async def delete_event(event_id: int, user_id: str = "user_123") -> str:
    """Delete a calendar event by ID."""
    db = await _get_db()
    try:
        await db.execute("DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
        await db.commit()
        return json.dumps({"status": "deleted", "event_id": event_id})
    finally:
        await db.close()


# ── Tool: get_free_slots ──────────────────────────────────────────────
async def get_free_slots(date: str, user_id: str = "user_123", work_start: str = "09:00", work_end: str = "18:00") -> str:
    """Find available time windows on a given date between work hours."""
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT start_time, end_time FROM events WHERE user_id = ? AND start_time LIKE ? ORDER BY start_time",
            (user_id, f"{date}%"),
        )
        rows = await cursor.fetchall()

        # Build busy intervals (just HH:MM for simplicity)
        busy = []
        for r in rows:
            s = r[0].split(" ")[1][:5] if " " in r[0] else r[0][:5]
            e = r[1].split(" ")[1][:5] if " " in r[1] else r[1][:5]
            busy.append((s, e))

        # Find gaps
        free = []
        current = work_start
        for start, end in sorted(busy):
            if current < start:
                free.append({"start": f"{date} {current}", "end": f"{date} {start}"})
            if end > current:
                current = end
        if current < work_end:
            free.append({"start": f"{date} {current}", "end": f"{date} {work_end}"})

        return json.dumps({"date": date, "free_slots": free, "count": len(free)})
    finally:
        await db.close()


# ── Tool registry (for the orchestrator to discover) ──────────────────
CALENDAR_TOOLS = {
    "create_event": create_event,
    "list_events": list_events,
    "check_conflicts": check_conflicts,
    "delete_event": delete_event,
    "get_free_slots": get_free_slots,
}

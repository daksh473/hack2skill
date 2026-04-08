"""
Knowledge Base MCP Server — exposes notes/knowledge management tools.
Features full-text search via SQLite FTS5.
"""
import json
import aiosqlite
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "aether.db"


async def _get_db():
    return await aiosqlite.connect(str(DB_PATH))


# ── Tool: create_note ──────────────────────────────────────────────────
async def create_note(
    title: str,
    content: str,
    tags: str = "",
    user_id: str = "user_123",
) -> str:
    """Create a new markdown note in the knowledge base."""
    db = await _get_db()
    try:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            "INSERT INTO notes (title, content, tags, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, content, tags, user_id, now, now),
        )
        await db.commit()
        return json.dumps({"status": "created", "note_id": cursor.lastrowid, "title": title})
    finally:
        await db.close()


# ── Tool: search_notes ─────────────────────────────────────────────────
async def search_notes(query: str, user_id: str = "user_123") -> str:
    """Full-text search across all notes. Returns matching notes ranked by relevance."""
    db = await _get_db()
    try:
        # Use FTS5 for relevance-ranked search
        cursor = await db.execute(
            """SELECT n.id, n.title, snippet(notes_fts, 1, '**', '**', '...', 32) as excerpt, n.tags
               FROM notes_fts
               JOIN notes n ON notes_fts.rowid = n.id
               WHERE notes_fts MATCH ? AND n.user_id = ?
               ORDER BY rank
               LIMIT 10""",
            (query, user_id),
        )
        rows = await cursor.fetchall()
        results = [{"id": r[0], "title": r[1], "excerpt": r[2], "tags": r[3]} for r in rows]
        return json.dumps({"results": results, "count": len(results), "query": query})
    finally:
        await db.close()


# ── Tool: get_note ─────────────────────────────────────────────────────
async def get_note(note_id: int, user_id: str = "user_123") -> str:
    """Retrieve a specific note by ID with full content."""
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT id, title, content, tags, created_at, updated_at FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id),
        )
        row = await cursor.fetchone()
        if not row:
            return json.dumps({"error": "Note not found", "note_id": note_id})
        note = {"id": row[0], "title": row[1], "content": row[2], "tags": row[3], "created_at": row[4], "updated_at": row[5]}
        return json.dumps(note)
    finally:
        await db.close()


# ── Tool: list_notes ───────────────────────────────────────────────────
async def list_notes(tags: str = "", user_id: str = "user_123") -> str:
    """List notes, optionally filtered by tags (comma-separated)."""
    db = await _get_db()
    try:
        if tags:
            # Match any of the provided tags
            tag_list = [t.strip() for t in tags.split(",")]
            conditions = " OR ".join(["tags LIKE ?" for _ in tag_list])
            params = [user_id] + [f"%{t}%" for t in tag_list]
            cursor = await db.execute(
                f"SELECT id, title, tags, created_at FROM notes WHERE user_id = ? AND ({conditions}) ORDER BY updated_at DESC",
                params,
            )
        else:
            cursor = await db.execute(
                "SELECT id, title, tags, created_at FROM notes WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            )
        rows = await cursor.fetchall()
        notes = [{"id": r[0], "title": r[1], "tags": r[2], "created_at": r[3]} for r in rows]
        return json.dumps({"notes": notes, "count": len(notes)})
    finally:
        await db.close()


# ── Tool: update_note ──────────────────────────────────────────────────
async def update_note(
    note_id: int,
    title: str = "",
    content: str = "",
    tags: str = "",
    user_id: str = "user_123",
) -> str:
    """Update a note's title, content, or tags."""
    db = await _get_db()
    try:
        updates = []
        params = []
        if title:
            updates.append("title = ?")
            params.append(title)
        if content:
            updates.append("content = ?")
            params.append(content)
        if tags:
            updates.append("tags = ?")
            params.append(tags)

        if not updates:
            return json.dumps({"status": "no_changes"})

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.extend([note_id, user_id])

        await db.execute(
            f"UPDATE notes SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
            params,
        )
        await db.commit()
        return json.dumps({"status": "updated", "note_id": note_id})
    finally:
        await db.close()


# ── Tool registry ─────────────────────────────────────────────────────
KNOWLEDGE_TOOLS = {
    "create_note": create_note,
    "search_notes": search_notes,
    "get_note": get_note,
    "list_notes": list_notes,
    "update_note": update_note,
}

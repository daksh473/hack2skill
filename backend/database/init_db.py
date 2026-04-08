"""
Database initialization – creates all SQLite tables for the multi-agent system.
"""
import aiosqlite
from pathlib import Path
import asyncio

DB_PATH = Path(__file__).resolve().parent / "aether.db"


async def init_db(db_path: Path | None = None):
    """Create all required tables if they don't exist."""
    p = db_path or DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(str(p)) as db:
        # ── Calendar Events ────────────────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                start_time  TEXT    NOT NULL,
                end_time    TEXT    NOT NULL,
                description TEXT    DEFAULT '',
                location    TEXT    DEFAULT '',
                user_id     TEXT    NOT NULL DEFAULT 'default',
                created_at  TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── Tasks / Todos ──────────────────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT    DEFAULT '',
                priority    INTEGER DEFAULT 3 CHECK(priority BETWEEN 1 AND 5),
                status      TEXT    DEFAULT 'pending'
                                CHECK(status IN ('pending','in_progress','done','cancelled')),
                due_date    TEXT,
                user_id     TEXT    NOT NULL DEFAULT 'default',
                created_at  TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── Notes / Knowledge Base ─────────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                content     TEXT    NOT NULL,
                tags        TEXT    DEFAULT '',
                user_id     TEXT    NOT NULL DEFAULT 'default',
                created_at  TEXT    DEFAULT (datetime('now')),
                updated_at  TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── User Preferences ──────────────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key     TEXT NOT NULL,
                value   TEXT NOT NULL,
                UNIQUE(user_id, key)
            )
        """)

        # ── Execution History ──────────────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS execution_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT    NOT NULL,
                query      TEXT    NOT NULL,
                plan       TEXT    DEFAULT '',
                results    TEXT    DEFAULT '',
                created_at TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── Full-text search index on notes ────────────────────────────
        await db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
            USING fts5(title, content, tags, content='notes', content_rowid='id')
        """)

        # Triggers to keep FTS in sync
        await db.execute("""
            CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
                INSERT INTO notes_fts(rowid, title, content, tags)
                VALUES (new.id, new.title, new.content, new.tags);
            END
        """)
        await db.execute("""
            CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
                INSERT INTO notes_fts(notes_fts, rowid, title, content, tags)
                VALUES ('delete', old.id, old.title, old.content, old.tags);
            END
        """)
        await db.execute("""
            CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
                INSERT INTO notes_fts(notes_fts, rowid, title, content, tags)
                VALUES ('delete', old.id, old.title, old.content, old.tags);
                INSERT INTO notes_fts(rowid, title, content, tags)
                VALUES (new.id, new.title, new.content, new.tags);
            END
        """)

        await db.commit()
    print(f"[OK] Database initialized at {p}")


async def seed_demo_data(db_path: Path | None = None):
    """Insert sample data for demonstration purposes."""
    p = db_path or DB_PATH
    async with aiosqlite.connect(str(p)) as db:
        # Check if data already exists
        cursor = await db.execute("SELECT COUNT(*) FROM events")
        count = (await cursor.fetchone())[0]
        if count > 0:
            print("[INFO] Demo data already exists, skipping seed.")
            return

        # Sample events
        await db.executemany(
            "INSERT INTO events (title, start_time, end_time, description, user_id) VALUES (?, ?, ?, ?, ?)",
            [
                ("Team Standup", "2026-03-30 09:00", "2026-03-30 09:30", "Daily sync", "user_123"),
                ("Product Review", "2026-03-30 14:00", "2026-03-30 15:00", "Q2 roadmap review", "user_123"),
                ("1:1 with Manager", "2026-03-30 16:00", "2026-03-30 16:30", "Weekly check-in", "user_123"),
                ("Design Sprint", "2026-03-31 10:00", "2026-03-31 12:00", "UI mockup session", "user_123"),
            ],
        )

        # Sample tasks
        await db.executemany(
            "INSERT INTO tasks (title, description, priority, status, due_date, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("Prepare Q2 slides", "Finalize metrics deck", 5, "pending", "2026-03-30", "user_123"),
                ("Review PRs", "Check open pull requests", 3, "pending", "2026-03-30", "user_123"),
                ("Update docs", "Refresh API documentation", 2, "pending", "2026-03-30", "user_123"),
                ("Send weekly report", "Summarize progress", 4, "pending", "2026-03-30", "user_123"),
                ("Book team lunch", "Reserve restaurant", 1, "pending", "2026-03-31", "user_123"),
            ],
        )

        # Sample notes
        await db.executemany(
            "INSERT INTO notes (title, content, tags, user_id) VALUES (?, ?, ?, ?)",
            [
                (
                    "Meeting Prep – Product Review",
                    "## Key Points\n- Q2 revenue up 15%\n- New feature adoption at 40%\n- Customer churn decreased\n\n## Action Items\n- Finalize roadmap priorities\n- Allocate engineering resources\n- Schedule follow-up with stakeholders",
                    "meeting,product,q2",
                    "user_123",
                ),
                (
                    "Project Ideas",
                    "## Ideas Backlog\n1. AI-powered search for internal wiki\n2. Automated onboarding flow\n3. Real-time dashboard for ops team\n4. Slack bot for standup summaries",
                    "ideas,projects,brainstorm",
                    "user_123",
                ),
                (
                    "Architecture Notes",
                    "## Multi-Agent System Design\n- Hub-and-spoke with primary orchestrator\n- MCP for tool decoupling\n- SQLite for local-first storage\n- Review-before-execute safety loop",
                    "architecture,design,agents",
                    "user_123",
                ),
            ],
        )

        # User preferences
        await db.executemany(
            "INSERT OR REPLACE INTO user_preferences (user_id, key, value) VALUES (?, ?, ?)",
            [
                ("user_123", "timezone", "Asia/Kolkata"),
                ("user_123", "work_hours_start", "09:00"),
                ("user_123", "work_hours_end", "18:00"),
                ("user_123", "default_meeting_duration", "30"),
            ],
        )

        await db.commit()
    print("[OK] Demo data seeded successfully")


if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(seed_demo_data())

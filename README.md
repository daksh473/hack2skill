# ⚡ Aether — Multi-Agent AI Productivity Assistant

A **Hub-and-Spoke** multi-agent system that orchestrates three specialized AI agents to handle complex productivity tasks through natural language.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Server                          │
│                    POST /v1/execute                         │
├─────────────────────────────────────────────────────────────┤
│                  Primary Orchestrator                       │
│           (Intent Classification + Delegation)              │
├──────────────┬──────────────────┬───────────────────────────┤
│  🗓️ Scheduler │  ✅ Taskmaster    │  📚 Librarian             │
│  Calendar &   │  To-do lists &   │  Knowledge base &        │
│  Time-blocking│  Priorities      │  Note summaries          │
├──────────────┼──────────────────┼───────────────────────────┤
│  MCP: Calendar│  MCP: Tasks      │  MCP: Knowledge          │
│  (SQLite)     │  (SQLite)        │  (SQLite + FTS5)         │
└──────────────┴──────────────────┴───────────────────────────┘
```

## Tech Stack

| Component | Technology |
|:---|:---|
| LLM | Google Gemini 2.0 Flash |
| Agent Orchestration | Google ADK pattern (custom) |
| Tool Protocol | MCP (Model Context Protocol) |
| API Server | FastAPI + Uvicorn |
| Database | SQLite + aiosqlite |
| Frontend | React (Vite) |
| Styling | Vanilla CSS (dark/gold theme) |

## Quick Start

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your-gemini-api-key-here
```

Get a free key at [Google AI Studio](https://aistudio.google.com/).

### 3. Initialize Database

```bash
python -m backend.database.init_db
```

### 4. Start Backend

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 6. Open Dashboard

Navigate to `http://localhost:5173`

## Example Queries

- *"I have a meeting at 2 PM, clear my afternoon tasks and summarize my prep notes."*
- *"Show me all high-priority tasks due today and reschedule the low-priority ones."*
- *"Search my notes for anything related to the product review."*
- *"Find a free 1-hour slot tomorrow for a design sprint."*

## Multi-Step Workflow

For complex queries, the system follows a **Review-Before-Execute** loop:

1. **Plan** — Orchestrator decomposes into sub-tasks
2. **Validate** — Agents check constraints (hard deadlines, conflicts)
3. **Execute** — Tools called via MCP protocol
4. **Report** — Unified summary returned to the user

## API Endpoints

| Method | Endpoint | Description |
|:---|:---|:---|
| POST | `/v1/execute` | Execute query (SSE streaming) |
| POST | `/v1/execute/sync` | Execute query (synchronous) |
| GET | `/v1/history/{user_id}` | Get execution history |
| POST | `/v1/preferences` | Set user preferences |
| GET | `/v1/health` | Health check |

## State Management

- **Blackboard (Short-term):** In-memory session context shared between agents
- **SQLite (Long-term):** User preferences and execution history

## License

Built for Google Hack2Skill Hackathon 2026.

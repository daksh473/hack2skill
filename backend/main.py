"""
FastAPI application — API layer for the Multi-Agent Productivity Assistant.

Endpoints:
  POST /v1/execute     — Execute a natural language query (SSE streaming)
  GET  /v1/history     — Retrieve execution history
  POST /v1/preferences — Set user preferences
  GET  /v1/health      — Health check
"""
import json
import sys
import os
import asyncio

# Add parent to path so `backend.` imports work when running from the backend dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from backend.models.schemas import (
    ExecuteRequest,
    ExecuteResponse,
    HealthResponse,
    PreferenceRequest,
    HistoryItem,
)
from backend.database.init_db import init_db, seed_demo_data
from backend.state.memory import set_preference, get_history
from backend.agents.orchestrator import execute_plan

# ── App Setup ──────────────────────────────────────────────────────────
app = FastAPI(
    title="Aether Multi-Agent Assistant",
    description="Hub-and-Spoke AI Productivity System with Scheduler, Taskmaster, and Librarian agents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database and seed demo data on first run."""
    await init_db()
    await seed_demo_data()
    print("[OK] Aether Multi-Agent Assistant is ready!")


# ── POST /v1/execute ───────────────────────────────────────────────────
@app.post("/v1/execute")
async def execute_query(req: ExecuteRequest):
    """
    Execute a natural language query through the multi-agent orchestrator.
    Returns Server-Sent Events (SSE) stream with agent thoughts and final result.
    """
    async def event_stream():
        try:
            async for event in execute_plan(req.query, req.user_id):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── POST /v1/execute/sync ─────────────────────────────────────────────
@app.post("/v1/execute/sync", response_model=ExecuteResponse)
async def execute_query_sync(req: ExecuteRequest):
    """
    Synchronous version — collects all events and returns a single JSON response.
    Useful for testing and simple integrations.
    """
    try:
        final_result = None
        thoughts = []
        plan = None

        async for event in execute_plan(req.query, req.user_id):
            if event.get("type") == "result":
                final_result = event
            elif event.get("type") == "thought" and event.get("status") == "done":
                thoughts.append(event)
            elif event.get("type") == "plan":
                plan = event.get("plan")

        if final_result:
            return ExecuteResponse(
                success=final_result.get("success", True),
                plan=final_result.get("plan"),
                thoughts=final_result.get("thoughts", []),
                summary=final_result.get("summary", ""),
            )
        return ExecuteResponse(success=False, error="No result produced")

    except Exception as e:
        return ExecuteResponse(success=False, error=str(e))


# ── GET /v1/history ────────────────────────────────────────────────────
@app.get("/v1/history/{user_id}")
async def get_execution_history(user_id: str, limit: int = 20):
    """Retrieve past execution history for a user."""
    history = await get_history(user_id, limit)
    return {"history": history, "count": len(history)}


# ── POST /v1/preferences ──────────────────────────────────────────────
@app.post("/v1/preferences")
async def update_preferences(req: PreferenceRequest):
    """Set a user preference."""
    await set_preference(req.user_id, req.key, req.value)
    return {"status": "saved", "key": req.key, "value": req.value}


# ── GET /v1/health ─────────────────────────────────────────────────────
@app.get("/v1/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()


# ── Entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

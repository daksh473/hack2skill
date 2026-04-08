"""
Configuration and environment settings for the multi-agent system.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "aether.db"
NOTES_DIR = BASE_DIR.parent / "data" / "sample_notes"

# ── LLM ────────────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ── Server ─────────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ── Agent Defaults ─────────────────────────────────────────────────────
MAX_AGENT_STEPS = 10
AGENT_TEMPERATURE = 0.3

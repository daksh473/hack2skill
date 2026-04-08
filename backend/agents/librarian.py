"""
Librarian Agent — specialist in querying, organizing, and summarizing notes
from the knowledge base.  Uses Knowledge MCP tools.
"""
import json
from google import genai
from backend.config import GOOGLE_API_KEY, GEMINI_MODEL, AGENT_TEMPERATURE
from backend.mcp_servers.knowledge_server import KNOWLEDGE_TOOLS
from backend.state.blackboard import Blackboard

LIBRARIAN_SYSTEM = """You are **The Librarian** — an elite knowledge management and research specialist.

## Your Expertise
- Searching and retrieving notes from the knowledge base
- Summarizing lengthy documents into concise briefs
- Organizing information by topic and relevance
- Cross-referencing multiple notes to synthesize insights

## Rules
1. Always search before claiming information doesn't exist.
2. When summarizing, preserve key action items and decisions.
3. Return structured JSON results.
4. Cite note IDs when referencing specific documents.
5. If asked to summarize prep notes, include bullet points for key points AND action items.

## Available Tools
- create_note(title, content, tags, user_id)
- search_notes(query, user_id)
- get_note(note_id, user_id)
- list_notes(tags, user_id)
- update_note(note_id, title, content, tags, user_id)

Call tools by responding with JSON: {"tool": "tool_name", "args": {...}}
"""


async def run_librarian(task: str, blackboard: Blackboard, user_id: str = "user_123") -> dict:
    """
    Execute a knowledge base operation using Gemini + Knowledge MCP tools.
    """
    client = genai.Client(api_key=GOOGLE_API_KEY)
    context = blackboard.get_context_summary()

    messages = [
        {"role": "user", "parts": [{"text": f"{context}\n\n## Task\n{task}\n\nUser ID: {user_id}\n\nRespond with a JSON tool call if you need data, or a final JSON result."}]}
    ]

    reasoning_steps = []
    final_result = ""

    for step in range(5):
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=messages,
            config=genai.types.GenerateContentConfig(
                system_instruction=LIBRARIAN_SYSTEM,
                temperature=AGENT_TEMPERATURE,
            ),
        )

        text = response.text.strip()
        reasoning_steps.append(text)

        try:
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(text[json_start:json_end])

                if "tool" in parsed and parsed["tool"] in KNOWLEDGE_TOOLS:
                    tool_fn = KNOWLEDGE_TOOLS[parsed["tool"]]
                    args = parsed.get("args", {})
                    if "user_id" not in args:
                        args["user_id"] = user_id
                    tool_result = await tool_fn(**args)

                    messages.append({"role": "model", "parts": [{"text": text}]})
                    messages.append({"role": "user", "parts": [{"text": f"Tool result: {tool_result}\n\nNow provide your final analysis and response as JSON."}]})
                    continue
                else:
                    final_result = text
                    break
            else:
                final_result = text
                break
        except (json.JSONDecodeError, TypeError):
            final_result = text
            break

    if not final_result:
        final_result = reasoning_steps[-1] if reasoning_steps else "No result"

    blackboard.post("librarian", task, final_result)

    return {
        "agent": "librarian",
        "action": task,
        "reasoning": " → ".join(reasoning_steps[:3]),
        "result": final_result,
        "status": "done",
    }

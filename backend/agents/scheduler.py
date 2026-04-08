"""
Scheduler Agent — specialist in time-blocking, conflict resolution, and
calendar management.  Uses Calendar MCP tools.
"""
import json
from google import genai
from backend.config import GOOGLE_API_KEY, GEMINI_MODEL, AGENT_TEMPERATURE
from backend.mcp_servers.calendar_server import CALENDAR_TOOLS
from backend.state.blackboard import Blackboard

SCHEDULER_SYSTEM = """You are **The Scheduler** — an elite calendar and time-management specialist.

## Your Expertise
- Time-blocking and calendar optimization
- Meeting conflict detection and resolution
- Finding optimal free slots for new events
- Schedule summarization

## Rules
1. Always check for conflicts before creating events.
2. Respect the user's work hours (from preferences).
3. Return structured JSON results — never prose alone.
4. If a conflict exists, suggest alternatives rather than just reporting the problem.
5. When listing events, provide a clear chronological summary.

## Available Tools
You can call these calendar tools:
- create_event(title, start_time, end_time, description, location, user_id)
- list_events(date, user_id)
- check_conflicts(start_time, end_time, user_id)
- delete_event(event_id, user_id)
- get_free_slots(date, user_id)

Call tools by responding with JSON: {"tool": "tool_name", "args": {...}}
"""


async def run_scheduler(task: str, blackboard: Blackboard, user_id: str = "user_123") -> dict:
    """
    Execute a scheduling task using Gemini + Calendar MCP tools.
    Returns a dict with {agent, action, reasoning, result, status}.
    """
    client = genai.Client(api_key=GOOGLE_API_KEY)

    # Build context from blackboard
    context = blackboard.get_context_summary()

    messages = [
        {"role": "user", "parts": [{"text": f"{context}\n\n## Task\n{task}\n\nUser ID: {user_id}\n\nRespond with a JSON tool call if you need data, or a final JSON result if you can answer directly."}]}
    ]

    reasoning_steps = []
    final_result = ""

    for step in range(5):  # Max 5 tool-call rounds
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=messages,
            config=genai.types.GenerateContentConfig(
                system_instruction=SCHEDULER_SYSTEM,
                temperature=AGENT_TEMPERATURE,
            ),
        )

        text = response.text.strip()
        reasoning_steps.append(text)

        # Try to parse a tool call
        try:
            # Extract JSON from the response
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(text[json_start:json_end])

                if "tool" in parsed and parsed["tool"] in CALENDAR_TOOLS:
                    tool_fn = CALENDAR_TOOLS[parsed["tool"]]
                    args = parsed.get("args", {})
                    if "user_id" not in args:
                        args["user_id"] = user_id
                    tool_result = await tool_fn(**args)

                    messages.append({"role": "model", "parts": [{"text": text}]})
                    messages.append({"role": "user", "parts": [{"text": f"Tool result: {tool_result}\n\nNow provide your final analysis and response as JSON."}]})
                    continue
                else:
                    # It's a final result
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

    # Post to blackboard
    blackboard.post("scheduler", task, final_result)

    return {
        "agent": "scheduler",
        "action": task,
        "reasoning": " → ".join(reasoning_steps[:3]),
        "result": final_result,
        "status": "done",
    }

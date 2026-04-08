"""
Primary Orchestrator — the Hub of the Hub-and-Spoke multi-agent system.

Responsibilities:
1. Intent classification — determine which agents are needed
2. Task decomposition — break complex queries into sub-tasks
3. Parallel dispatch — run independent sub-tasks concurrently
4. Review-before-execute — validate plans before tool calls
5. Result aggregation — combine sub-agent outputs into a unified response
"""
import json
import asyncio
from typing import AsyncGenerator
from google import genai
from backend.config import GOOGLE_API_KEY, GEMINI_MODEL, AGENT_TEMPERATURE
from backend.state.blackboard import Blackboard
from backend.state.memory import get_all_preferences, get_recent_context, save_execution
from backend.agents.scheduler import run_scheduler
from backend.agents.taskmaster import run_taskmaster
from backend.agents.librarian import run_librarian
from backend.models.schemas import AgentThought, TaskPlan, SubTaskPlan, ExecuteResponse

ORCHESTRATOR_SYSTEM = """You are the **Primary Orchestrator** — the brain of a multi-agent productivity system.

## Your Role
You receive natural language requests and decompose them into structured sub-tasks,
each assigned to a specialist agent.

## Available Agents
1. **scheduler** — Calendar management, time-blocking, conflict detection
2. **taskmaster** — To-do list management, priority levels, deadlines
3. **librarian** — Knowledge base search, note summarization, information retrieval

## Your Process (Review-Before-Execute)
1. **PLAN**: Analyze the user request and create a structured plan
2. **ASSIGN**: Map each sub-task to the appropriate agent
3. **VALIDATE**: Check for constraints and dependencies between tasks
4. **REPORT**: After execution, synthesize a unified response

## Output Format
You MUST respond with a **valid JSON object** and nothing else:
{
  "plan": {
    "original_query": "the user's request",
    "subtasks": [
      {"agent": "scheduler|taskmaster|librarian", "description": "specific task description"},
      ...
    ]
  },
  "reasoning": "brief explanation of your decomposition logic"
}

## Rules
- If a query only involves one domain, assign it to one agent.
- If tasks are independent, they will be executed in parallel.
- If task B depends on task A's result, note the dependency.
- Always include ALL necessary context in each sub-task description.
- Use the user's timezone and preferences when relevant.
"""

AGENT_RUNNERS = {
    "scheduler": run_scheduler,
    "taskmaster": run_taskmaster,
    "librarian": run_librarian,
}


async def classify_and_plan(query: str, user_id: str, preferences: dict, recent_history: str) -> TaskPlan:
    """Use Gemini to classify intent and create an execution plan."""
    client = genai.Client(api_key=GOOGLE_API_KEY)

    context_parts = [
        f"## User Preferences\n{json.dumps(preferences, indent=2)}",
        recent_history,
        f"## User Request\n{query}",
    ]

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[{"role": "user", "parts": [{"text": "\n\n".join(context_parts)}]}],
        config=genai.types.GenerateContentConfig(
            system_instruction=ORCHESTRATOR_SYSTEM,
            temperature=AGENT_TEMPERATURE,
        ),
    )

    text = response.text.strip()

    # Parse the plan
    try:
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            parsed = json.loads(text[json_start:json_end])
            plan_data = parsed.get("plan", parsed)

            subtasks = []
            for st in plan_data.get("subtasks", []):
                agent = st.get("agent", "").lower()
                if agent in AGENT_RUNNERS:
                    subtasks.append(SubTaskPlan(agent=agent, description=st.get("description", "")))

            if not subtasks:
                # Fallback: single agent based on keyword matching
                subtasks = [_fallback_classify(query)]

            return TaskPlan(original_query=query, subtasks=subtasks)
    except (json.JSONDecodeError, KeyError):
        pass

    # Fallback classification
    return TaskPlan(original_query=query, subtasks=[_fallback_classify(query)])


def _fallback_classify(query: str) -> SubTaskPlan:
    """Simple keyword-based fallback classification."""
    ql = query.lower()
    if any(w in ql for w in ["schedule", "meeting", "calendar", "event", "time", "slot", "2 pm", "3 pm"]):
        return SubTaskPlan(agent="scheduler", description=query)
    elif any(w in ql for w in ["task", "todo", "priority", "deadline", "clear", "reschedule", "done"]):
        return SubTaskPlan(agent="taskmaster", description=query)
    elif any(w in ql for w in ["note", "search", "summarize", "knowledge", "prep", "document", "find"]):
        return SubTaskPlan(agent="librarian", description=query)
    else:
        return SubTaskPlan(agent="librarian", description=query)


async def execute_plan(
    query: str,
    user_id: str = "user_123",
) -> AsyncGenerator[dict, None]:
    """
    Main orchestrator entry point.  Yields streaming events:
      - {"type": "plan", ...}
      - {"type": "thought", ...}  (per agent)
      - {"type": "result", ...}   (final)
    """
    blackboard = Blackboard()
    blackboard.set_metadata("user_id", user_id)
    blackboard.set_metadata("query", query)

    # 1. Load context
    preferences = await get_all_preferences(user_id)
    recent_history = await get_recent_context(user_id, limit=3)

    # 2. PLAN — classify and decompose
    yield {"type": "status", "message": "🧠 Analyzing your request..."}

    plan = await classify_and_plan(query, user_id, preferences, recent_history)

    yield {
        "type": "plan",
        "plan": plan.model_dump(),
        "message": f"📋 Created plan with {len(plan.subtasks)} sub-task(s)",
    }

    # 3. EXECUTE — dispatch to sub-agents
    thoughts: list[AgentThought] = []

    # Group independent tasks for parallel execution
    agent_tasks = []
    for subtask in plan.subtasks:
        runner = AGENT_RUNNERS.get(subtask.agent)
        if runner:
            yield {
                "type": "thought",
                "agent": subtask.agent,
                "action": subtask.description,
                "status": "running",
                "message": f"🔄 {subtask.agent.title()} is working on: {subtask.description[:80]}...",
            }
            agent_tasks.append((subtask, runner))

    # Run all agents concurrently
    if agent_tasks:
        coros = [
            runner(subtask.description, blackboard, user_id)
            for subtask, runner in agent_tasks
        ]
        results = await asyncio.gather(*coros, return_exceptions=True)

        for i, result in enumerate(results):
            subtask = agent_tasks[i][0]
            if isinstance(result, Exception):
                thought = AgentThought(
                    agent_name=subtask.agent,
                    action=subtask.description,
                    reasoning=str(result),
                    result=f"Error: {str(result)}",
                    status="error",
                )
            else:
                thought = AgentThought(
                    agent_name=result["agent"],
                    action=result["action"],
                    reasoning=result.get("reasoning", ""),
                    result=result.get("result", ""),
                    status=result.get("status", "done"),
                )
            thoughts.append(thought)

            yield {
                "type": "thought",
                "agent": thought.agent_name,
                "action": thought.action,
                "reasoning": thought.reasoning,
                "result": thought.result,
                "status": thought.status,
                "message": f"✅ {thought.agent_name.title()} completed",
            }

    # 4. SYNTHESIZE — create unified response
    yield {"type": "status", "message": "📝 Synthesizing final response..."}

    summary = await _synthesize_response(query, blackboard, thoughts)

    # 5. PERSIST — save to execution history
    await save_execution(
        user_id=user_id,
        query=query,
        plan=json.dumps(plan.model_dump()),
        results=summary,
    )

    yield {
        "type": "result",
        "success": True,
        "plan": plan.model_dump(),
        "thoughts": [t.model_dump() for t in thoughts],
        "summary": summary,
    }


async def _synthesize_response(query: str, blackboard: Blackboard, thoughts: list[AgentThought]) -> str:
    """Use Gemini to create a unified, user-friendly summary from all agent results."""
    client = genai.Client(api_key=GOOGLE_API_KEY)

    agent_results = blackboard.get_context_summary()

    synthesis_prompt = f"""You are summarizing the results of a multi-agent execution for the user.

## Original Request
{query}

## Agent Results
{agent_results}

## Instructions
Create a clear, concise, and helpful summary of what was accomplished.
Use bullet points for multiple items. Be specific about what changed.
Keep it conversational but professional. Do NOT use JSON — respond in natural language.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[{"role": "user", "parts": [{"text": synthesis_prompt}]}],
        config=genai.types.GenerateContentConfig(
            temperature=0.5,
        ),
    )

    return response.text.strip()

"""
Simplified agent runner for skill evaluation.
Creates Deep Agent with specific skill for isolated testing.
"""

import asyncio
import sys
from pathlib import Path

# Project root is 2 levels up from this file (tests/skills/simple_agent_runner.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from deepagents import create_deep_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from conftest import ExecutionTracer
import google.auth

from template_agent.src.core.backend import get_backend


def _extract_output(result: dict) -> str:
    """Extract text output from agent result."""
    if "messages" not in result:
        return ""

    for msg in reversed(result["messages"]):
        if not (hasattr(msg, "content") and msg.content):
            continue
        if hasattr(msg, "type") and msg.type == "human":
            continue

        # Handle both string and list content
        if isinstance(msg.content, list):
            return "\n".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in msg.content
            )
        return str(msg.content)

    return ""


def _extract_tokens(result: dict) -> int:
    """Extract total token usage from agent result."""
    # Sum tokens from all AI messages in the conversation
    total_tokens = 0

    if "messages" in result:
        for msg in result["messages"]:
            # Check for usage_metadata directly on message (Gemini format)
            if hasattr(msg, "usage_metadata") and msg.usage_metadata:
                usage = msg.usage_metadata
                total_tokens += usage.get("total_tokens", 0)

    return total_tokens


def _create_model():
    """Create and configure Gemini model."""
    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return ChatGoogleGenerativeAI(
        model="gemini-3.1-pro-preview",
        temperature=0,
        credentials=credentials,
        project=project,
    )


async def _run_agent(
    skill_path: Path,
    prompt: str,
    tracer: ExecutionTracer,
    with_skill: bool = True,
) -> str:
    """
    Run Deep Agent with or without skill.

    Args:
        skill_path: Path to skill directory
        prompt: User prompt
        tracer: Execution tracer
        with_skill: Whether to load the skill

    Returns:
        Agent output text
    """
    # Start timing
    tracer.start()

    # Create agent
    skills = [str(skill_path)] if with_skill else []
    agent = create_deep_agent(
        model=_create_model(),
        skills=skills,
        backend=get_backend(),
        checkpointer=MemorySaver(),
    )

    # Run agent
    config = {"configurable": {"thread_id": f"test-{'skill' if with_skill else 'baseline'}"}}

    try:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config=config,
        )

        output = _extract_output(result)
        tokens = _extract_tokens(result)
        tracer.end(total_tokens=tokens)
        return output

    except Exception as e:
        tracer.end()
        raise


def run_agent_sync(
    skill_path: Path,
    prompt: str,
    tracer: ExecutionTracer,
    with_skill: bool = True,
) -> str:
    """
    Synchronous wrapper for running agent.

    Args:
        skill_path: Path to skill directory
        prompt: User prompt
        tracer: Execution tracer
        with_skill: Whether to use skill

    Returns:
        Agent output
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            _run_agent(skill_path, prompt, tracer, with_skill)
        )
    finally:
        loop.close()

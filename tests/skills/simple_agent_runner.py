"""
Simplified agent runner for direct skill testing.
Uses the agent with specific skill loaded for isolated evaluation.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any
import sys

# Project root is 2 levels up from this file (tests/skills/simple_agent_runner.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from deepagents import create_deep_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from conftest import ExecutionTracer
import google.auth

from template_agent.src.core.backend import get_backend


class SimpleAgentRunner:
    """Runs agent with specific skill for testing."""

    def __init__(self, skill_path: Path):
        """
        Initialize with skill to test.

        Args:
            skill_path: Path to skill directory
        """
        self.skill_path = skill_path

    async def run_with_skill(self, prompt: str, tracer: ExecutionTracer) -> str:
        """
        Run agent with specific skill loaded.

        Args:
            prompt: User prompt
            tracer: Execution tracer

        Returns:
            Agent output
        """
        tracer.start()
        tracer.add_step("initialize", f"Loading skill from {self.skill_path.name}")

        # Initialize model
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        model = ChatGoogleGenerativeAI(
            model="gemini-3.1-pro-preview",
            temperature=0,
            credentials=credentials,
            project=project,
        )

        # Create agent with this specific skill
        backend = get_backend()
        agent = create_deep_agent(
            model=model,
            skills=[str(self.skill_path)],
            backend=backend,
            checkpointer=MemorySaver(),
        )

        tracer.add_step("agent_ready", "Agent initialized with skill")

        # Run agent
        tracer.add_step("execute", f"Running: {prompt[:100]}...")

        config = {"configurable": {"thread_id": "test-thread"}}

        try:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]}, config=config
            )

            # Extract output
            output = ""
            if "messages" in result:
                for msg in reversed(result["messages"]):
                    if hasattr(msg, "content") and msg.content:
                        if hasattr(msg, "type") and msg.type != "human":
                            # Handle both string and list content
                            if isinstance(msg.content, list):
                                # Extract text from content blocks
                                output = "\n".join(
                                    block.get("text", "")
                                    if isinstance(block, dict)
                                    else str(block)
                                    for block in msg.content
                                )
                            else:
                                output = str(msg.content)
                            break

            tracer.add_step("complete", f"Output: {len(output)} chars")
            tracer.end()

            return output

        except Exception as e:
            tracer.add_step("error", str(e))
            tracer.end()
            raise

    async def run_without_skill(self, prompt: str, tracer: ExecutionTracer) -> str:
        """
        Run agent without skill (baseline).

        Args:
            prompt: User prompt
            tracer: Execution tracer

        Returns:
            Agent output
        """
        tracer.start()
        tracer.add_step("initialize", "Creating agent WITHOUT skill")

        # Initialize model
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        model = ChatGoogleGenerativeAI(
            model="gemini-3.1-pro-preview",
            temperature=0,
            credentials=credentials,
            project=project,
        )

        # Create agent WITHOUT skill
        backend = get_backend()
        agent = create_deep_agent(
            model=model,
            skills=[],  # No skills
            backend=backend,
            checkpointer=MemorySaver(),
        )

        tracer.add_step("agent_ready", "Agent initialized WITHOUT skill")
        tracer.add_step("execute", f"Running: {prompt[:100]}...")

        config = {"configurable": {"thread_id": "test-baseline-thread"}}

        try:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]}, config=config
            )

            output = ""
            if "messages" in result:
                for msg in reversed(result["messages"]):
                    if hasattr(msg, "content") and msg.content:
                        if hasattr(msg, "type") and msg.type != "human":
                            # Handle both string and list content
                            if isinstance(msg.content, list):
                                # Extract text from content blocks
                                output = "\n".join(
                                    block.get("text", "")
                                    if isinstance(block, dict)
                                    else str(block)
                                    for block in msg.content
                                )
                            else:
                                output = str(msg.content)
                            break

            tracer.add_step("complete", f"Output: {len(output)} chars")
            tracer.end()

            return output

        except Exception as e:
            tracer.add_step("error", str(e))
            tracer.end()
            raise


def run_agent_sync(
    skill_path: Path, prompt: str, tracer: ExecutionTracer, with_skill: bool = True
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
    runner = SimpleAgentRunner(skill_path)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        if with_skill:
            output = loop.run_until_complete(runner.run_with_skill(prompt, tracer))
        else:
            output = loop.run_until_complete(runner.run_without_skill(prompt, tracer))
        return output
    finally:
        loop.close()


if __name__ == "__main__":
    from conftest import ExecutionTracer

    tracer = ExecutionTracer()
    skill_path = (
        PROJECT_ROOT / "template_agent" / "agent_config" / "skills" / "bmi-report"
    )

    print("Testing simple agent runner...")
    print(f"Skill: {skill_path}")
    print()

    output = run_agent_sync(
        skill_path,
        "My BMI is 22.5 and I'm in the Normal category. Can you give me a fitness report?",
        tracer,
        with_skill=True,
    )

    print("\n=== Output ===")
    print(output)

    print("\n=== Trajectory ===")
    print(json.dumps(tracer.get_trajectory(), indent=2))

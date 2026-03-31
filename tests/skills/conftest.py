"""
Pytest configuration and fixtures for Deep Agents-style skill evaluation.
Based on Deep Agents methodology without LangSmith dependency.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any
import pytest

# Project root is 2 levels up from this file (tests/skills/conftest.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def skills_dir():
    """Root directory containing all skills."""
    return PROJECT_ROOT / "template_agent" / "agent_config" / "skills"


@pytest.fixture(scope="session")
def workspace_dir():
    """Root directory for test workspaces."""
    workspace = PROJECT_ROOT / "template_agent" / "agent_config" / "workspaces"
    workspace.mkdir(exist_ok=True)
    return workspace


@pytest.fixture
def eval_context():
    """Context for a single evaluation run."""
    return {"start_time": time.time(), "tool_calls": [], "outputs": {}, "errors": []}


def load_skill_evals(skill_name: str) -> Dict[str, Any]:
    """Load evals.json for a skill."""
    skills_dir = PROJECT_ROOT / "template_agent" / "agent_config" / "skills"
    evals_file = skills_dir / skill_name / "evals" / "evals.json"

    if not evals_file.exists():
        raise FileNotFoundError(f"No evals.json found for {skill_name}")

    with open(evals_file, "r") as f:
        return json.load(f)


def load_skill_content(skill_path: Path) -> str:
    """Load SKILL.md content."""
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        raise FileNotFoundError(f"SKILL.md not found at {skill_path}")

    return skill_file.read_text()


class ExecutionTracer:
    """Track agent execution for trajectory analysis."""

    def __init__(self):
        self.steps = []
        self.tool_calls = []
        self.start_time = None
        self.end_time = None

    def start(self):
        """Begin tracking."""
        self.start_time = time.time()

    def end(self):
        """End tracking."""
        self.end_time = time.time()

    def add_step(self, step_type: str, content: str, metadata: Dict = None):
        """Record an execution step."""
        self.steps.append(
            {
                "type": step_type,
                "content": content,
                "metadata": metadata or {},
                "timestamp": time.time() - self.start_time if self.start_time else 0,
            }
        )

    def add_tool_call(self, tool_name: str, args: Dict, result: Any = None):
        """Record a tool call."""
        self.tool_calls.append(
            {
                "tool": tool_name,
                "args": args,
                "result": str(result)[:200] if result else None,
                "timestamp": time.time() - self.start_time if self.start_time else 0,
            }
        )

    def get_trajectory(self) -> Dict:
        """Get complete execution trajectory."""
        return {
            "steps": self.steps,
            "tool_calls": self.tool_calls,
            "duration_ms": int((self.end_time - self.start_time) * 1000)
            if self.end_time
            else 0,
            "total_steps": len(self.steps),
            "total_tool_calls": len(self.tool_calls),
        }


@pytest.fixture
def tracer():
    """Execution tracer for capturing agent behavior."""
    return ExecutionTracer()


class AssertionEvaluator:
    """Evaluate assertions against outputs."""

    @staticmethod
    def evaluate(assertion: str, output: str, context: Dict = None) -> Dict:
        """
        Evaluate a single assertion.

        Returns dict with:
        - passed: bool
        - evidence: str
        - confidence: float (0-1)
        """
        import re

        assertion_lower = assertion.lower()
        output_lower = output.lower()

        # Check for BMI value
        if "bmi value" in assertion_lower or "bmi is" in assertion_lower:
            value_match = re.search(r"(\d+\.?\d*)", assertion)
            if value_match:
                expected_value = value_match.group(1)
                # Look for the value in output (flexible format)
                found = (
                    expected_value in output
                    or f"bmi is {expected_value}" in output_lower
                    or f"bmi: {expected_value}" in output_lower
                )
                return {
                    "passed": found,
                    "evidence": f"BMI value {expected_value} found in output"
                    if found
                    else f"BMI value {expected_value} not found",
                    "confidence": 0.95 if found else 0.9,
                }

        # Check for category mention
        if "category" in assertion_lower and any(
            cat in assertion_lower
            for cat in ["normal", "underweight", "overweight", "obese"]
        ):
            for category in ["normal", "underweight", "overweight", "obese"]:
                if category in assertion_lower:
                    found = category in output_lower
                    return {
                        "passed": found,
                        "evidence": f"Category '{category}' found in output"
                        if found
                        else f"Category '{category}' not found",
                        "confidence": 0.95 if found else 0.9,
                    }

        # Check for health tips count
        if "at least" in assertion_lower and "tips" in assertion_lower:
            count_match = re.search(r"at least (\d+)", assertion_lower)
            if count_match:
                required_count = int(count_match.group(1))
                # Count bullet points or numbered items
                tip_markers = len(re.findall(r"^\s*[-*•]\s", output, re.MULTILINE))
                found = tip_markers >= required_count
                return {
                    "passed": found,
                    "evidence": f"Found {tip_markers} tips (required: {required_count})"
                    if found
                    else f"Only {tip_markers} tips found (required: {required_count})",
                    "confidence": 0.9 if found else 0.85,
                }

        # Check for disclaimer
        if "disclaimer" in assertion_lower:
            # Look for key disclaimer phrases
            disclaimer_found = any(
                phrase in output_lower
                for phrase in [
                    "not medical advice",
                    "consult a healthcare professional",
                    "consult a doctor",
                    "seek medical advice",
                ]
            )
            return {
                "passed": disclaimer_found,
                "evidence": "Disclaimer found in output"
                if disclaimer_found
                else "Disclaimer not found",
                "confidence": 0.95 if disclaimer_found else 0.9,
            }

        # Check for weight loss focus
        if "gradual" in assertion_lower and "weight loss" in assertion_lower:
            found = any(
                phrase in output_lower
                for phrase in [
                    "gradual",
                    "sustainable",
                    "slow and steady",
                    "long-term",
                    "consistent",
                ]
            )
            return {
                "passed": found,
                "evidence": "Gradual/sustainable approach mentioned"
                if found
                else "Gradual approach not mentioned",
                "confidence": 0.9 if found else 0.85,
            }

        # Check for safe weight loss rate
        if (
            "safe weight loss rate" in assertion_lower
            or "kg/week" in assertion_lower
            or "kg per week" in assertion_lower
        ):
            found = re.search(r"0\.5[-–]1\s*kg", output_lower) is not None
            return {
                "passed": found,
                "evidence": "Safe weight loss rate (0.5-1 kg/week) mentioned"
                if found
                else "Safe weight loss rate not mentioned",
                "confidence": 0.95 if found else 0.9,
            }

        # Check for no extreme diet recommendations
        if "no extreme" in assertion_lower or "quick fixes" in assertion_lower:
            avoid_extremes = any(
                phrase in output_lower
                for phrase in [
                    "avoid crash diets",
                    "avoid extreme",
                    "no quick fixes",
                    "sustainable",
                    "gradual",
                ]
            )
            return {
                "passed": avoid_extremes,
                "evidence": "Warns against extreme approaches"
                if avoid_extremes
                else "No warning against extreme approaches",
                "confidence": 0.9 if avoid_extremes else 0.85,
            }

        # Check tone (friendly, encouraging, non-judgmental)
        if "tone" in assertion_lower and (
            "friendly" in assertion_lower
            or "encouraging" in assertion_lower
            or "positive" in assertion_lower
            or "supportive" in assertion_lower
        ):
            positive_indicators = any(
                word in output_lower
                for word in [
                    "great",
                    "fantastic",
                    "good",
                    "well done",
                    "keep up",
                    "excellent",
                    "healthy",
                    "encouraging",
                    "supportive",
                    "you can",
                    "progress",
                ]
            )
            return {
                "passed": positive_indicators,
                "evidence": "Positive/supportive tone detected"
                if positive_indicators
                else "Positive tone not clearly detected",
                "confidence": 0.8,
            }

        # Check for absence of negative words
        if "no use of" in assertion_lower or "avoid" in assertion_lower:
            negative_words = re.findall(
                r"\b(bad|failing|unhealthy|poor|terrible)\b", output_lower
            )
            passed = len(negative_words) == 0
            return {
                "passed": passed,
                "evidence": f"No negative words found"
                if passed
                else f"Found negative words: {negative_words}",
                "confidence": 0.9 if passed else 0.85,
            }

        # Default: require manual evaluation
        return {
            "passed": None,
            "evidence": "Requires manual evaluation",
            "confidence": 0.0,
        }


@pytest.fixture
def evaluator():
    """Assertion evaluator."""
    return AssertionEvaluator()


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "skill: mark test as a skill evaluation test")
    config.addinivalue_line(
        "markers", "baseline: mark test as baseline (without skill)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their names."""
    for item in items:
        if "baseline" in item.nodeid:
            item.add_marker(pytest.mark.baseline)
        if "with_skill" in item.nodeid:
            item.add_marker(pytest.mark.skill)

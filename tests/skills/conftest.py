"""
Pytest configuration and fixtures for Deep Agents-style skill evaluation.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional
import pytest


# ============================================================================
# Constants
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ============================================================================
# Session Fixtures (shared across all tests)
# ============================================================================


@pytest.fixture(scope="session")
def skills_dir():
    """Root directory containing all skills."""
    return PROJECT_ROOT / "template_agent" / "agent_config" / "skills"


@pytest.fixture(scope="session")
def workspace_dir():
    """Root directory for test workspaces."""
    workspace = PROJECT_ROOT / "tests" / "workspaces"
    workspace.mkdir(exist_ok=True)
    return workspace


# ============================================================================
# Function Fixtures (new instance per test)
# ============================================================================


@pytest.fixture
def tracer():
    """Execution tracer for capturing agent behavior."""
    return ExecutionTracer()


@pytest.fixture
def evaluator():
    """Assertion evaluator for grading outputs."""
    return AssertionEvaluator()


# ============================================================================
# Helper Functions
# ============================================================================


def load_skill_evals(skill_name: str) -> Dict[str, Any]:
    """Load evals.json for a skill."""
    skills_dir = PROJECT_ROOT / "template_agent" / "agent_config" / "skills"
    evals_file = skills_dir / skill_name / "evals" / "evals.json"

    if not evals_file.exists():
        raise FileNotFoundError(f"No evals.json found for {skill_name}")

    with open(evals_file, "r") as f:
        return json.load(f)


# ============================================================================
# ExecutionTracer Class
# ============================================================================


class ExecutionTracer:
    """Simple timer for tracking execution duration and token usage."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_tokens = 0

    def start(self):
        """Begin timing."""
        self.start_time = time.time()

    def end(self, total_tokens: int = 0):
        """End timing and record token usage."""
        self.end_time = time.time()
        self.total_tokens = total_tokens

    def duration_ms(self) -> int:
        """Get duration in milliseconds."""
        if self.end_time and self.start_time:
            return int((self.end_time - self.start_time) * 1000)
        return 0


# ============================================================================
# AssertionEvaluator Class
# ============================================================================


class AssertionEvaluator:
    """
    Evaluate assertions against outputs using pattern matching.

    Returns dict with: passed (bool|None), evidence (str), confidence (float)
    """

    # Evaluation patterns mapped to check functions
    CHECKS = {
        "bmi_value": lambda self, a, o: self._check_bmi_value(a, o),
        "category": lambda self, a, o: self._check_category(a, o),
        "tips_count": lambda self, a, o: self._check_tips_count(a, o),
        "disclaimer": lambda self, a, o: self._check_disclaimer(a, o),
        "gradual_loss": lambda self, a, o: self._check_gradual_loss(a, o),
        "weight_rate": lambda self, a, o: self._check_weight_rate(a, o),
        "no_extremes": lambda self, a, o: self._check_no_extremes(a, o),
        "tone": lambda self, a, o: self._check_tone(a, o),
        "no_negative": lambda self, a, o: self._check_no_negative(a, o),
    }

    def evaluate(self, assertion: str, output: str, context: Optional[Dict] = None) -> Dict:
        """Evaluate a single assertion against output."""
        assertion_lower = assertion.lower()
        output_lower = output.lower()

        # Try each check pattern
        if "bmi value" in assertion_lower or "bmi is" in assertion_lower:
            return self._check_bmi_value(assertion, output)

        if "category" in assertion_lower and any(
            c in assertion_lower for c in ["normal", "underweight", "overweight", "obese"]
        ):
            return self._check_category(assertion, output)

        if "at least" in assertion_lower and "tips" in assertion_lower:
            return self._check_tips_count(assertion, output)

        if "disclaimer" in assertion_lower:
            return self._check_disclaimer(assertion, output)

        if "gradual" in assertion_lower and "weight loss" in assertion_lower:
            return self._check_gradual_loss(assertion, output)

        if any(k in assertion_lower for k in ["safe weight loss rate", "kg/week", "kg per week"]):
            return self._check_weight_rate(assertion, output)

        if "no extreme" in assertion_lower or "quick fixes" in assertion_lower:
            return self._check_no_extremes(assertion, output)

        if "tone" in assertion_lower and any(
            t in assertion_lower for t in ["friendly", "encouraging", "positive", "supportive"]
        ):
            return self._check_tone(assertion, output)

        if "no use of" in assertion_lower:
            return self._check_no_negative(assertion, output)

        # Default: manual evaluation required
        return {"passed": None, "evidence": "Requires manual evaluation", "confidence": 0.0}

    def _check_bmi_value(self, assertion: str, output: str) -> Dict:
        """Check if BMI value is present."""
        match = re.search(r"(\d+\.?\d*)", assertion)
        if not match:
            return {"passed": None, "evidence": "No BMI value in assertion", "confidence": 0.0}

        value = match.group(1)
        found = value in output
        return {
            "passed": found,
            "evidence": f"BMI value {value} {'found' if found else 'not found'}",
            "confidence": 0.95 if found else 0.9,
        }

    def _check_category(self, assertion: str, output: str) -> Dict:
        """Check if BMI category is mentioned."""
        categories = ["normal", "underweight", "overweight", "obese"]
        assertion_lower = assertion.lower()
        output_lower = output.lower()

        for cat in categories:
            if cat in assertion_lower:
                found = cat in output_lower
                return {
                    "passed": found,
                    "evidence": f"Category '{cat}' {'found' if found else 'not found'}",
                    "confidence": 0.95 if found else 0.9,
                }

        return {"passed": None, "evidence": "No category in assertion", "confidence": 0.0}

    def _check_tips_count(self, assertion: str, output: str) -> Dict:
        """Check if minimum number of tips are present."""
        match = re.search(r"at least (\d+)", assertion.lower())
        if not match:
            return {"passed": None, "evidence": "No count in assertion", "confidence": 0.0}

        required = int(match.group(1))
        found = len(re.findall(r"^\s*[-*•]\s", output, re.MULTILINE))
        passed = found >= required

        return {
            "passed": passed,
            "evidence": f"Found {found} tips (required: {required})",
            "confidence": 0.9 if passed else 0.85,
        }

    def _check_disclaimer(self, assertion: str, output: str) -> Dict:
        """Check if disclaimer is present."""
        phrases = [
            "not medical advice",
            "consult a healthcare professional",
            "consult a doctor",
            "seek medical advice",
        ]
        found = any(p in output.lower() for p in phrases)
        return {
            "passed": found,
            "evidence": f"Disclaimer {'found' if found else 'not found'}",
            "confidence": 0.95 if found else 0.9,
        }

    def _check_gradual_loss(self, assertion: str, output: str) -> Dict:
        """Check for gradual weight loss approach."""
        keywords = ["gradual", "sustainable", "slow and steady", "long-term", "consistent"]
        found = any(k in output.lower() for k in keywords)
        return {
            "passed": found,
            "evidence": f"Gradual approach {'mentioned' if found else 'not mentioned'}",
            "confidence": 0.9 if found else 0.85,
        }

    def _check_weight_rate(self, assertion: str, output: str) -> Dict:
        """Check for safe weight loss rate mention."""
        found = re.search(r"0\.5[-–]1\s*kg", output.lower()) is not None
        return {
            "passed": found,
            "evidence": f"Safe weight loss rate {'mentioned' if found else 'not mentioned'}",
            "confidence": 0.95 if found else 0.9,
        }

    def _check_no_extremes(self, assertion: str, output: str) -> Dict:
        """Check for warnings against extreme diets."""
        keywords = ["avoid crash diets", "avoid extreme", "no quick fixes", "sustainable"]
        found = any(k in output.lower() for k in keywords)
        return {
            "passed": found,
            "evidence": f"Warns against extremes: {'yes' if found else 'no'}",
            "confidence": 0.9 if found else 0.85,
        }

    def _check_tone(self, assertion: str, output: str) -> Dict:
        """Check for positive/supportive tone."""
        keywords = [
            "great", "fantastic", "good", "well done", "keep up",
            "excellent", "healthy", "encouraging", "supportive", "progress",
        ]
        found = any(k in output.lower() for k in keywords)
        return {
            "passed": found,
            "evidence": f"Positive tone {'detected' if found else 'not detected'}",
            "confidence": 0.8,
        }

    def _check_no_negative(self, assertion: str, output: str) -> Dict:
        """Check for absence of negative words."""
        negatives = re.findall(r"\b(bad|failing|unhealthy|poor|terrible)\b", output.lower())
        passed = len(negatives) == 0
        return {
            "passed": passed,
            "evidence": f"No negative words" if passed else f"Found: {negatives}",
            "confidence": 0.9 if passed else 0.85,
        }


# ============================================================================
# Pytest Hooks
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "skill: tests with skill loaded")
    config.addinivalue_line("markers", "baseline: tests without skill (baseline)")
    config.addinivalue_line("markers", "slow: slow-running comparison tests")

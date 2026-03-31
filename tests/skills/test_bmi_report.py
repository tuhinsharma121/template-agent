"""
Pytest-based evaluation tests for bmi-report skill.
Based on Deep Agents evaluation methodology with pytest best practices.
"""

import json
import pytest
from pathlib import Path
from typing import Dict
from conftest import load_skill_evals, ExecutionTracer
from simple_agent_runner import run_agent_sync


# ============================================================================
# Constants & Test Data
# ============================================================================

SKILL_NAME = "bmi-report"
MIN_PASS_RATE = 0.5  # Minimum acceptable pass rate for skill tests


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def skill_config(skills_dir):
    """Load skill configuration once per module."""
    return {
        "name": SKILL_NAME,
        "path": skills_dir / SKILL_NAME,
        "evals": load_skill_evals(SKILL_NAME),
    }


@pytest.fixture(scope="module")
def workspace(workspace_dir):
    """Create and return workspace path."""
    workspace = workspace_dir / f"{SKILL_NAME}-workspace" / "iteration-1"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


@pytest.fixture
def eval_runner(skill_config, workspace):
    """Factory fixture for running evaluations."""

    def _run_evaluation(eval_id: int, variant: str, tracer: ExecutionTracer) -> Dict:
        """
        Run evaluation and save results.

        Args:
            eval_id: Evaluation case ID
            variant: "with_skill" or "without_skill"
            tracer: Execution tracer

        Returns:
            Dict with output, trajectory, and eval_case
        """
        # Get eval case
        eval_case = next(
            (e for e in skill_config["evals"]["evals"] if e["id"] == eval_id), None
        )
        if not eval_case:
            pytest.fail(f"Eval case {eval_id} not found")

        # Run agent
        with_skill = variant == "with_skill"
        output = run_agent_sync(
            skill_config["path"], eval_case["prompt"], tracer, with_skill=with_skill
        )

        # Save results
        _save_results(workspace, eval_id, variant, output, tracer)

        return {
            "output": output,
            "trajectory": tracer.get_trajectory(),
            "eval_case": eval_case,
        }

    return _run_evaluation


@pytest.fixture
def grader(skill_config, workspace):
    """Factory fixture for grading assertions."""

    def _grade_evaluation(eval_id: int, variant: str, evaluator) -> Dict:
        """
        Grade assertions for an evaluation.

        Args:
            eval_id: Evaluation case ID
            variant: "with_skill" or "without_skill"
            evaluator: Assertion evaluator

        Returns:
            Grading results with summary
        """
        # Get eval case
        eval_case = next(
            (e for e in skill_config["evals"]["evals"] if e["id"] == eval_id), None
        )
        if not eval_case:
            pytest.fail(f"Eval case {eval_id} not found")

        # Load output
        eval_dir = workspace / f"eval-{eval_id}" / variant
        output_file = eval_dir / "outputs" / "report.md"
        output = output_file.read_text() if output_file.exists() else ""

        # Evaluate assertions
        results = []
        for assertion in eval_case.get("assertions", []):
            result = evaluator.evaluate(assertion, output)
            results.append({"text": assertion, **result})

        # Calculate summary
        passed = sum(1 for r in results if r["passed"] is True)
        failed = sum(1 for r in results if r["passed"] is False)
        total = len(results)

        grading = {
            "assertion_results": results,
            "summary": {
                "passed": passed,
                "failed": failed,
                "total": total,
                "pass_rate": passed / total if total > 0 else 0.0,
            },
        }

        # Save grading
        grading_file = eval_dir / "grading.json"
        grading_file.write_text(json.dumps(grading, indent=2))

        return grading

    return _grade_evaluation


# ============================================================================
# Helper Functions
# ============================================================================


def _save_results(
    workspace: Path, eval_id: int, variant: str, output: str, tracer: ExecutionTracer
) -> None:
    """Save evaluation results to workspace."""
    eval_dir = workspace / f"eval-{eval_id}" / variant
    eval_dir.mkdir(parents=True, exist_ok=True)

    # Save output
    output_file = eval_dir / "outputs" / "report.md"
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(output)

    # Save trajectory
    trajectory_file = eval_dir / "trajectory.json"
    trajectory = tracer.get_trajectory()
    trajectory_file.write_text(json.dumps(trajectory, indent=2))

    # Save timing
    timing_file = eval_dir / "timing.json"
    timing_data = {
        "total_tokens": 0,  # TODO: Extract from agent response
        "duration_ms": trajectory["duration_ms"],
    }
    timing_file.write_text(json.dumps(timing_data, indent=2))


def _load_eval_results(workspace: Path, eval_id: int, variant: str) -> Dict:
    """Load saved results for an evaluation."""
    eval_dir = workspace / f"eval-{eval_id}" / variant

    grading_file = eval_dir / "grading.json"
    timing_file = eval_dir / "timing.json"
    trajectory_file = eval_dir / "trajectory.json"

    return {
        "grading": json.loads(grading_file.read_text())
        if grading_file.exists()
        else {},
        "timing": json.loads(timing_file.read_text()) if timing_file.exists() else {},
        "trajectory": json.loads(trajectory_file.read_text())
        if trajectory_file.exists()
        else {},
    }


# ============================================================================
# Tests: With Skill
# ============================================================================


@pytest.mark.skill
@pytest.mark.parametrize(
    "eval_id,description",
    [
        (1, "Normal BMI"),
        (2, "Underweight"),
        (3, "Overweight"),
        (4, "Obese"),
        (5, "Casual prompt"),
    ],
    ids=lambda x: x if isinstance(x, str) else f"eval-{x}",
)
def test_with_skill(eval_id, description, eval_runner, grader, tracer, evaluator):
    """Test skill evaluation - agent should generate quality BMI reports."""
    # Run evaluation
    eval_runner(eval_id, "with_skill", tracer)

    # Grade assertions
    grading = grader(eval_id, "with_skill", evaluator)

    # Assert quality threshold
    pass_rate = grading["summary"]["pass_rate"]
    assert pass_rate >= MIN_PASS_RATE, (
        f"Pass rate {pass_rate:.1%} below threshold {MIN_PASS_RATE:.1%} for {description}\n"
        f"Passed: {grading['summary']['passed']}/{grading['summary']['total']} assertions"
    )


# ============================================================================
# Tests: Without Skill (Baseline)
# ============================================================================


@pytest.mark.baseline
@pytest.mark.parametrize(
    "eval_id,description",
    [
        (1, "Normal BMI"),
        (2, "Underweight"),
        (3, "Overweight"),
        (4, "Obese"),
        (5, "Casual prompt"),
    ],
    ids=lambda x: x if isinstance(x, str) else f"eval-{x}",
)
def test_without_skill(eval_id, description, eval_runner, grader, tracer, evaluator):
    """Test baseline - agent without skill (for comparison)."""
    # Run evaluation
    eval_runner(eval_id, "without_skill", tracer)

    # Grade assertions (no quality assertion - baseline typically lower)
    grader(eval_id, "without_skill", evaluator)


# ============================================================================
# Tests: Comparison & Analysis
# ============================================================================


@pytest.mark.slow
def test_skill_improves_pass_rate(workspace):
    """Verify that skill improves overall pass rate compared to baseline."""
    with_skill_rates = []
    without_skill_rates = []

    # Collect results from all evaluations
    for eval_id in range(1, 6):
        with_skill = _load_eval_results(workspace, eval_id, "with_skill")
        without_skill = _load_eval_results(workspace, eval_id, "without_skill")

        if with_skill["grading"]:
            with_skill_rates.append(with_skill["grading"]["summary"]["pass_rate"])
        if without_skill["grading"]:
            without_skill_rates.append(without_skill["grading"]["summary"]["pass_rate"])

    # Calculate averages
    if not with_skill_rates or not without_skill_rates:
        pytest.skip(
            "Insufficient results for comparison - run both skill and baseline tests first"
        )

    avg_with = sum(with_skill_rates) / len(with_skill_rates)
    avg_without = sum(without_skill_rates) / len(without_skill_rates)
    improvement = avg_with - avg_without

    # Print comparison
    print(f"\n{'=' * 60}")
    print(f"Skill Performance Comparison")
    print(f"{'=' * 60}")
    print(f"With skill:     {avg_with:.1%} pass rate")
    print(f"Without skill:  {avg_without:.1%} pass rate")
    print(f"Improvement:    {improvement:+.1%}")
    print(f"{'=' * 60}")

    # Assert skill provides value
    assert avg_with > avg_without, (
        f"Skill should improve performance:\n"
        f"  With skill: {avg_with:.1%}\n"
        f"  Without skill: {avg_without:.1%}\n"
        f"  Improvement: {improvement:+.1%}"
    )


# ============================================================================
# Optional: Individual Eval Analysis
# ============================================================================


@pytest.mark.slow
@pytest.mark.parametrize("eval_id", [1, 2, 3, 4, 5], ids=lambda x: f"eval-{x}")
def test_eval_comparison(eval_id, workspace):
    """Compare with_skill vs without_skill for individual evaluation."""
    with_skill = _load_eval_results(workspace, eval_id, "with_skill")
    without_skill = _load_eval_results(workspace, eval_id, "without_skill")

    # Skip if results don't exist
    if not with_skill["grading"] or not without_skill["grading"]:
        pytest.skip(f"Missing results for eval {eval_id}")

    with_rate = with_skill["grading"]["summary"]["pass_rate"]
    without_rate = without_skill["grading"]["summary"]["pass_rate"]

    # Info only - don't fail (some evals might not show improvement)
    print(f"\nEval {eval_id}: {with_rate:.1%} (with) vs {without_rate:.1%} (without)")

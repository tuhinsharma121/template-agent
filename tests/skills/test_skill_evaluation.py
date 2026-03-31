"""
Generic skill evaluation framework.
Platform for testing ANY skill using JSON test configurations.

Add new skills by creating JSON files - no code changes needed!
"""

import json
import pytest
from pathlib import Path
from typing import Dict, List
from conftest import load_skill_evals, ExecutionTracer
from simple_agent_runner import run_agent_sync


# ============================================================================
# Platform Configuration
# ============================================================================

# Minimum pass rate threshold (can be overridden per skill in JSON)
DEFAULT_MIN_PASS_RATE = 0.5


# ============================================================================
# Test Discovery
# ============================================================================


def discover_skills(skills_dir: Path) -> List[str]:
    """
    Discover all skills with test configurations.

    Returns:
        List of skill names that have evals/evals.json
    """
    skills = []
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            evals_file = skill_dir / "evals" / "evals.json"
            if evals_file.exists():
                skills.append(skill_dir.name)
    return sorted(skills)


def load_test_cases(skill_name: str, skills_dir: Path) -> List[Dict]:
    """
    Load test cases for a skill from JSON.

    Returns:
        List of (eval_id, description) tuples
    """
    evals_data = load_skill_evals(skill_name)
    return [
        (eval["id"], eval.get("description", f"Eval {eval['id']}"))
        for eval in evals_data.get("evals", [])
    ]


# ============================================================================
# Generic Test Runner
# ============================================================================


def run_and_grade(
    skill_config: Dict,
    workspace: Path,
    eval_id: int,
    with_skill: bool,
    tracer: ExecutionTracer,
    evaluator,
) -> Dict:
    """
    Generic runner - works for any skill.

    Args:
        skill_config: Skill configuration dict
        workspace: Workspace path
        eval_id: Evaluation case ID
        with_skill: Whether to run with skill
        tracer: Execution tracer
        evaluator: Assertion evaluator

    Returns:
        Grading results with summary
    """
    # Get eval case
    eval_case = next(
        (e for e in skill_config["evals"]["evals"] if e["id"] == eval_id),
        None
    )
    if not eval_case:
        pytest.fail(f"Eval case {eval_id} not found in {skill_config['name']}")

    # Run agent
    output = run_agent_sync(
        skill_config["path"],
        eval_case["prompt"],
        tracer,
        with_skill=with_skill,
    )

    # Save results
    variant = "with_skill" if with_skill else "without_skill"
    eval_dir = workspace / f"eval-{eval_id}" / variant
    eval_dir.mkdir(parents=True, exist_ok=True)

    # Save output
    output_file = eval_dir / "outputs" / "report.md"
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(output)

    # Save timing
    timing_file = eval_dir / "timing.json"
    timing_data = {
        "duration_ms": tracer.duration_ms(),
        "total_tokens": tracer.total_tokens,
    }
    timing_file.write_text(json.dumps(timing_data, indent=2))

    # Grade assertions
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


# ============================================================================
# Dynamic Test Generation
# ============================================================================


def pytest_generate_tests(metafunc):
    """
    Dynamically generate tests for all skills.

    This pytest hook discovers skills and creates test cases automatically.
    """
    if "skill_name" not in metafunc.fixturenames:
        return

    # Get skills directory from config
    config = metafunc.config
    rootdir = Path(config.rootdir)
    skills_dir = rootdir / "template_agent" / "agent_config" / "skills"

    # Discover all skills with test configs
    skills = discover_skills(skills_dir)

    if not skills:
        pytest.skip("No skills found with test configurations")

    # Generate test parameters
    if "eval_id" in metafunc.fixturenames:
        # Generate test cases for each skill
        params = []
        ids = []

        for skill in skills:
            test_cases = load_test_cases(skill, skills_dir)
            for eval_id, description in test_cases:
                params.append((skill, eval_id, description))
                ids.append(f"{skill}::eval-{eval_id}-{description}")

        metafunc.parametrize(
            "skill_name,eval_id,description",
            params,
            ids=ids,
        )
    else:
        # Just skill name
        metafunc.parametrize("skill_name", skills, ids=skills)


# ============================================================================
# Generic Fixtures
# ============================================================================


@pytest.fixture
def skill_config(skill_name, skills_dir):
    """Load configuration for any skill."""
    return {
        "name": skill_name,
        "path": skills_dir / skill_name,
        "evals": load_skill_evals(skill_name),
    }


@pytest.fixture
def workspace(skill_name, workspace_dir):
    """Create workspace for any skill."""
    ws = workspace_dir / f"{skill_name}-workspace" / "iteration-1"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


@pytest.fixture
def min_pass_rate(skill_config):
    """Get minimum pass rate threshold for skill."""
    return skill_config["evals"].get("min_pass_rate", DEFAULT_MIN_PASS_RATE)


# ============================================================================
# Platform Tests (work for ANY skill)
# ============================================================================


@pytest.mark.skill
def test_skill_evaluation(
    skill_name,
    eval_id,
    description,
    skill_config,
    workspace,
    min_pass_rate,
    tracer,
    evaluator,
):
    """
    Universal skill evaluation test.

    Tests ANY skill by running Deep Agent with the skill loaded
    and validating output against assertions from JSON.

    This single test handles all skills - just add JSON config!
    """
    grading = run_and_grade(
        skill_config,
        workspace,
        eval_id,
        with_skill=True,
        tracer=tracer,
        evaluator=evaluator,
    )

    pass_rate = grading["summary"]["pass_rate"]
    assert pass_rate >= min_pass_rate, (
        f"{skill_name} {description}: "
        f"Pass rate {pass_rate:.1%} below {min_pass_rate:.1%}\n"
        f"Passed {grading['summary']['passed']}/{grading['summary']['total']} assertions"
    )


@pytest.mark.baseline
def test_baseline_evaluation(
    skill_name,
    eval_id,
    description,
    skill_config,
    workspace,
    tracer,
    evaluator,
):
    """
    Universal baseline evaluation test.

    Tests agent WITHOUT skill for comparison.
    No pass rate assertion - used for measuring skill impact.
    """
    run_and_grade(
        skill_config,
        workspace,
        eval_id,
        with_skill=False,
        tracer=tracer,
        evaluator=evaluator,
    )


# ============================================================================
# Skill-Level Analysis
# ============================================================================


@pytest.mark.slow
def test_skill_improvement(skill_name, skill_config, workspace):
    """
    Analyze skill vs baseline performance.

    Works for any skill - compares all eval results.
    """
    with_rates = []
    without_rates = []

    # Collect results from all evals
    for eval_case in skill_config["evals"]["evals"]:
        eval_id = eval_case["id"]

        # Load with_skill results
        with_file = workspace / f"eval-{eval_id}" / "with_skill" / "grading.json"
        if with_file.exists():
            with_data = json.loads(with_file.read_text())
            with_rates.append(with_data["summary"]["pass_rate"])

        # Load without_skill results
        without_file = workspace / f"eval-{eval_id}" / "without_skill" / "grading.json"
        if without_file.exists():
            without_data = json.loads(without_file.read_text())
            without_rates.append(without_data["summary"]["pass_rate"])

    if not with_rates or not without_rates:
        pytest.skip(f"Run both skill and baseline tests for {skill_name} first")

    avg_with = sum(with_rates) / len(with_rates)
    avg_without = sum(without_rates) / len(without_rates)
    improvement = avg_with - avg_without

    print(f"\n{'='*60}")
    print(f"{skill_name.upper()} Performance Analysis")
    print(f"{'='*60}")
    print(f"With skill:    {avg_with:.1%}")
    print(f"Without skill: {avg_without:.1%}")
    print(f"Improvement:   {improvement:+.1%}")
    print(f"{'='*60}")

    assert avg_with > avg_without, (
        f"{skill_name} should improve performance:\n"
        f"  With: {avg_with:.1%}, Without: {avg_without:.1%}"
    )

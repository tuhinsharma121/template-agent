#!/usr/bin/env python3
"""
Aggregate test results into benchmark.json.
Based on Deep Agents evaluation methodology.
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List


def collect_results(workspace_dir: Path, skill_name: str) -> Dict:
    """Collect all test results from workspace."""
    iteration_dir = workspace_dir / f"{skill_name}-workspace" / "iteration-1"

    results = {"with_skill": [], "without_skill": []}

    # Find all eval directories
    for eval_dir in sorted(iteration_dir.glob("eval-*")):
        eval_id = eval_dir.name.split("-")[1]

        for variant in ["with_skill", "without_skill"]:
            variant_dir = eval_dir / variant

            grading_file = variant_dir / "grading.json"
            timing_file = variant_dir / "timing.json"
            trajectory_file = variant_dir / "trajectory.json"

            if not all([grading_file.exists(), timing_file.exists()]):
                continue

            grading = json.loads(grading_file.read_text())
            timing = json.loads(timing_file.read_text())

            trajectory = {}
            if trajectory_file.exists():
                trajectory = json.loads(trajectory_file.read_text())

            results[variant].append(
                {
                    "eval_id": int(eval_id),
                    "pass_rate": grading["summary"]["pass_rate"],
                    "tokens": timing.get("total_tokens", 0),
                    "duration_ms": timing.get("duration_ms", 0),
                    "tool_calls": trajectory.get("total_tool_calls", 0),
                    "steps": trajectory.get("total_steps", 0),
                }
            )

    return results


def compute_stats(values: List[float]) -> Dict:
    """Compute mean and standard deviation."""
    if not values:
        return {"mean": 0.0, "stddev": 0.0}

    mean_val = statistics.mean(values)
    stddev_val = statistics.stdev(values) if len(values) > 1 else 0.0

    return {"mean": round(mean_val, 2), "stddev": round(stddev_val, 2)}


def aggregate_benchmark(results: Dict) -> Dict:
    """Create benchmark summary."""
    summary = {}

    for variant in ["with_skill", "without_skill"]:
        data = results[variant]

        if not data:
            summary[variant] = {
                "pass_rate": {"mean": 0.0, "stddev": 0.0},
                "time_seconds": {"mean": 0.0, "stddev": 0.0},
                "tokens": {"mean": 0, "stddev": 0},
                "tool_calls": {"mean": 0, "stddev": 0},
                "steps": {"mean": 0, "stddev": 0},
            }
            continue

        pass_rates = [d["pass_rate"] for d in data]
        times_sec = [d["duration_ms"] / 1000.0 for d in data]
        tokens = [d["tokens"] for d in data]
        tool_calls = [d["tool_calls"] for d in data]
        steps = [d["steps"] for d in data]

        summary[variant] = {
            "pass_rate": compute_stats(pass_rates),
            "time_seconds": compute_stats(times_sec),
            "tokens": {
                "mean": int(statistics.mean(tokens)),
                "stddev": int(statistics.stdev(tokens)) if len(tokens) > 1 else 0,
            },
            "tool_calls": {
                "mean": round(statistics.mean(tool_calls), 1) if tool_calls else 0,
                "stddev": round(statistics.stdev(tool_calls), 1)
                if len(tool_calls) > 1
                else 0,
            },
            "steps": {
                "mean": round(statistics.mean(steps), 1) if steps else 0,
                "stddev": round(statistics.stdev(steps), 1) if len(steps) > 1 else 0,
            },
        }

    # Compute deltas
    with_skill = summary["with_skill"]
    without_skill = summary["without_skill"]

    delta = {
        "pass_rate": round(
            with_skill["pass_rate"]["mean"] - without_skill["pass_rate"]["mean"], 2
        ),
        "time_seconds": round(
            with_skill["time_seconds"]["mean"] - without_skill["time_seconds"]["mean"],
            2,
        ),
        "tokens": with_skill["tokens"]["mean"] - without_skill["tokens"]["mean"],
        "tool_calls": round(
            with_skill["tool_calls"]["mean"] - without_skill["tool_calls"]["mean"], 1
        ),
        "steps": round(with_skill["steps"]["mean"] - without_skill["steps"]["mean"], 1),
    }

    return {
        "run_summary": {
            "with_skill": summary["with_skill"],
            "without_skill": summary["without_skill"],
            "delta": delta,
        }
    }


def main():
    """Aggregate results for all skills."""
    # Project root is 2 levels up from this file (tests/skills/aggregate_results.py)
    PROJECT_ROOT = Path(__file__).parent.parent.parent

    # Get paths relative to project root
    skills_dir = PROJECT_ROOT / "template_agent" / "agent_config" / "skills"
    workspace_dir = PROJECT_ROOT / "template_agent" / "agent_config" / "workspaces"

    # Find all skills with evals
    skills = []
    for skill_dir in skills_dir.glob("*"):
        if skill_dir.is_dir() and (skill_dir / "evals" / "evals.json").exists():
            skills.append(skill_dir.name)

    if not skills:
        print("No skills with evals found")
        return

    # Aggregate each skill
    for skill_name in skills:
        print(f"\n{'=' * 60}")
        print(f"Aggregating: {skill_name}")
        print("=" * 60)

        results = collect_results(workspace_dir, skill_name)

        with_count = len(results["with_skill"])
        without_count = len(results["without_skill"])

        print(f"Found {with_count} with_skill results")
        print(f"Found {without_count} without_skill results")

        if with_count == 0 and without_count == 0:
            print(f"No results found for {skill_name}, skipping")
            continue

        benchmark = aggregate_benchmark(results)

        # Save benchmark
        iteration_dir = workspace_dir / f"{skill_name}-workspace" / "iteration-1"
        benchmark_file = iteration_dir / "benchmark.json"
        benchmark_file.write_text(json.dumps(benchmark, indent=2))

        print(f"\n✓ Saved: {benchmark_file}")

        # Print summary
        summary = benchmark["run_summary"]
        print("\nSummary:")
        print("-" * 60)
        print(f"{'Metric':<20} {'With Skill':<15} {'Without Skill':<15} {'Delta':<10}")
        print("-" * 60)

        # Pass rate
        with_pr = summary["with_skill"]["pass_rate"]["mean"]
        without_pr = summary["without_skill"]["pass_rate"]["mean"]
        delta_pr = summary["delta"]["pass_rate"]
        print(
            f"{'Pass Rate':<20} {with_pr:.1%}{'':<8} {without_pr:.1%}{'':<8} {delta_pr:+.1%}"
        )

        # Time
        with_time = summary["with_skill"]["time_seconds"]["mean"]
        without_time = summary["without_skill"]["time_seconds"]["mean"]
        delta_time = summary["delta"]["time_seconds"]
        print(
            f"{'Time (seconds)':<20} {with_time:.1f}s{'':<9} {without_time:.1f}s{'':<9} {delta_time:+.1f}s"
        )

        # Tokens
        with_tokens = summary["with_skill"]["tokens"]["mean"]
        without_tokens = summary["without_skill"]["tokens"]["mean"]
        delta_tokens = summary["delta"]["tokens"]
        print(
            f"{'Tokens':<20} {with_tokens:,}{'':<8} {without_tokens:,}{'':<8} {delta_tokens:+,}"
        )

        # Tool calls
        with_tools = summary["with_skill"]["tool_calls"]["mean"]
        without_tools = summary["without_skill"]["tool_calls"]["mean"]
        delta_tools = summary["delta"]["tool_calls"]
        print(
            f"{'Tool Calls':<20} {with_tools:.1f}{'':<10} {without_tools:.1f}{'':<10} {delta_tools:+.1f}"
        )

        # Steps
        with_steps = summary["with_skill"]["steps"]["mean"]
        without_steps = summary["without_skill"]["steps"]["mean"]
        delta_steps = summary["delta"]["steps"]
        print(
            f"{'Steps':<20} {with_steps:.1f}{'':<10} {without_steps:.1f}{'':<10} {delta_steps:+.1f}"
        )

        print("-" * 60)


if __name__ == "__main__":
    main()

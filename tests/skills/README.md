# Skills Evaluation Tests

Data-driven testing framework for Deep Agents skills.

## Quick Start

```bash
cd tests

# Test all skills
pytest skills/test_skill_evaluation.py -v

# Test one skill
pytest skills/test_skill_evaluation.py -k bmi-report -v

# Test one case
pytest skills/test_skill_evaluation.py -k "bmi-report::eval-1" -v
```

## Structure

```
tests/skills/
├── test_skill_evaluation.py   # Generic test platform
├── conftest.py                 # Fixtures & evaluator
└── simple_agent_runner.py      # Deep Agent runner

skills/*/evals/evals.json       # Test configurations (JSON)
```

## Adding a New Skill

1. Create JSON config:
```bash
mkdir -p skills/my-skill/evals
```

2. Add `skills/my-skill/evals/evals.json`:
```json
{
  "skill_name": "my-skill",
  "min_pass_rate": 0.5,
  "evals": [
    {
      "id": 1,
      "description": "Test case",
      "prompt": "Test prompt",
      "assertions": ["Expected behavior"]
    }
  ]
}
```

3. Run tests:
```bash
pytest skills/test_skill_evaluation.py -k my-skill -v
```

No code changes needed!

## Commands

### Basic Usage

```bash
# All skills
pytest skills/test_skill_evaluation.py -v

# One skill
pytest skills/test_skill_evaluation.py -k bmi-report -v

# One case
pytest skills/test_skill_evaluation.py -k "bmi-report::eval-1" -v
```

### By Test Type

```bash
# Skill tests (with skill loaded)
pytest skills/test_skill_evaluation.py -m skill -v

# Baseline tests (without skill)
pytest skills/test_skill_evaluation.py -m baseline -v

# Improvement analysis
pytest skills/test_skill_evaluation.py -m slow -v
```

### Combined

```bash
# bmi-report skill tests only
pytest skills/test_skill_evaluation.py -m skill -k bmi-report -v

# Multiple cases
pytest skills/test_skill_evaluation.py -k "eval-1 or eval-2" -v
```

## Current Skills

Automatically discovered:
- bmi-report (5 cases)
- client-intake (8 cases)
- email-formatter (8 cases)

Total: 45 tests

## JSON Schema

```json
{
  "skill_name": "string (required)",
  "min_pass_rate": 0.5,  // Optional: default 0.5
  "evals": [
    {
      "id": 1,                    // Unique ID
      "description": "Name",       // For test output
      "prompt": "User prompt",     // Input to agent
      "assertions": [              // Expected behaviors
        "Assertion 1",
        "Assertion 2"
      ]
    }
  ]
}
```

## Results

Saved to:
```
tests/workspaces/{skill}-workspace/iteration-1/
├── eval-{id}/
│   ├── with_skill/
│   │   ├── outputs/report.md
│   │   ├── grading.json
│   │   └── timing.json
│   └── without_skill/
│       └── (same)
```

## How It Works

1. **Discovery**: Platform finds all skills with `evals/evals.json`
2. **Generation**: pytest creates tests dynamically from JSON
3. **Execution**: Generic code runs tests for any skill
4. **Grading**: Evaluator checks assertions, saves results

Code is static. Skills are JSON.

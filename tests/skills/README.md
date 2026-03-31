# Skills Evaluation Tests

Automated pytest-based evaluation using **real Deep Agents** integration.

## Quick Start

```bash
# From project root
cd tests
./run_evals.sh --skill bmi-report --skill-only
```

## Structure

```
tests/skills/
├── conftest.py              # Pytest fixtures & enhanced evaluator
├── simple_agent_runner.py   # Deep Agent runner (isolated skill testing)
├── test_bmi_report.py       # Tests for bmi-report skill
├── aggregate_results.py     # Results aggregation & benchmark generation
└── README.md                # This file
```

## How It Works

Each test:
1. **Creates Deep Agent** with specific skill using `create_deep_agent()`
2. **Executes prompt** via Gemini API (with skill vs without skill)
3. **Captures trajectory** (execution steps, timing, tool calls)
4. **Auto-grades assertions** using enhanced pattern-matching evaluator
5. **Saves results** to workspace with detailed grading

## Running Tests

### From tests/ directory

**All skill evaluation tests:**
```bash
cd tests
./run_evals.sh --skill bmi-report --skill-only
```

**With & without skill comparison:**
```bash
./run_evals.sh --skill bmi-report
```

**Using pytest directly:**
```bash
# All skill tests
pytest skills/test_bmi_report.py -v -m skill

# Single test
pytest skills/test_bmi_report.py::TestBmiReportSkill::test_eval_1_with_skill -v

# All markers
pytest skills/ -m baseline  # Without skill
pytest skills/ -m slow      # Comparison tests
```

## Test Markers

- `@pytest.mark.skill` - Test with skill loaded
- `@pytest.mark.baseline` - Test without skill (baseline)
- `@pytest.mark.slow` - Slow comparison tests

## Key Components

### simple_agent_runner.py
- Creates Deep Agent with specific skill in isolation
- Uses `create_deep_agent(model=..., skills=[str(skill_path)], ...)`
- Handles both with_skill and without_skill variants

### conftest.py
- `ExecutionTracer` - Captures agent execution steps
- `AssertionEvaluator` - Smart pattern matching for assertions:
  - BMI values & categories
  - Health tip counting (bullet points)
  - Disclaimer detection
  - Tone analysis (positive/supportive)
  - Safe weight loss rates
  - No extreme recommendations

### Fixtures
- **tracer** - `ExecutionTracer` instance
- **evaluator** - `AssertionEvaluator` instance
- **skills_dir** - `PROJECT_ROOT/template_agent/agent_config/skills`
- **workspace_dir** - `PROJECT_ROOT/template_agent/agent_config/workspaces`

## Results

After running tests, find results in:
```
template_agent/agent_config/workspaces/bmi-report-workspace/iteration-1/
├── eval-1/
│   ├── with_skill/
│   │   ├── outputs/report.md      # Agent-generated BMI report
│   │   ├── grading.json           # Assertion pass/fail results
│   │   ├── trajectory.json        # Execution trace
│   │   └── timing.json            # Performance metrics
│   └── without_skill/
│       └── (same structure)
├── eval-2/ ... eval-5/
└── benchmark.json                  # Aggregated statistics
```

## Current Test Results

✅ **5/5 tests passing** for bmi-report skill:
- Normal BMI ✓
- Underweight ✓
- Overweight ✓
- Obese ✓
- Casual prompt ✓

## Adding New Skill Tests

1. Create `tests/skills/test_new_skill.py`
2. Copy pattern from `test_bmi_report.py`
3. Update skill name and eval cases
4. Run: `./run_evals.sh --skill new-skill`

Example:
```python
class TestNewSkill:
    @pytest.fixture(autouse=True)
    def setup(self, skills_dir, workspace_dir):
        self.skill_name = "new-skill"
        self.skill_path = skills_dir / self.skill_name
        self.evals_data = load_skill_evals(self.skill_name)
        # ...
```

## Path Configuration

All paths use `PROJECT_ROOT` constant for clarity:
```python
PROJECT_ROOT = Path(__file__).parent.parent.parent
skills_dir = PROJECT_ROOT / "template_agent" / "agent_config" / "skills"
```

# Migration to Deep Agents Evaluation System

## What Changed

We've migrated from **manual evaluation** to **Deep Agents-style automated evaluation** (without LangSmith).

---

## Old System (Removed)

### Manual Workflow ❌
```
1. setup_eval_workspace.sh - Create directories
2. run_single_eval.sh - Show test instructions
3. Manual agent delegation
4. Manual timing recording
5. grade_eval.py - Generate grading templates
6. Manual grading.json updates
7. aggregate_benchmark.py - Compute statistics
```

**Problems:**
- Labor-intensive
- Error-prone manual steps
- No trajectory tracking
- Difficult to reproduce
- No automation

---

## New System (Current)

### Automated Pytest Framework ✅
```
1. pytest tests/ - Run all tests automatically
2. Automatic output capture
3. Automatic trajectory tracking
4. Automatic grading (where possible)
5. Automatic aggregation
6. Statistical analysis included
```

**Benefits:**
- ✅ Fully automated
- ✅ Reproducible
- ✅ Trajectory tracking (tool calls, steps)
- ✅ CI/CD ready
- ✅ Based on Deep Agents methodology
- ✅ No external dependencies (no LangSmith required)

---

## Migration Steps

### What to Keep

✅ **Skills structure** - No changes needed
```
bmi-report/
├── SKILL.md
├── evals/evals.json
├── assets/
└── references/
```

✅ **evals.json files** - Format unchanged
```json
{
  "skill_name": "bmi-report",
  "evals": [...]
}
```

✅ **Workspace structure** - Same organization
```
workspaces/
└── bmi-report-workspace/
    └── iteration-1/
        ├── eval-1/
        │   ├── with_skill/
        │   └── without_skill/
        └── benchmark.json
```

### What to Delete

❌ **Old scripts** (already removed):
- `scripts/setup_eval_workspace.sh`
- `scripts/run_single_eval.sh`
- `scripts/grade_eval.py`
- `scripts/aggregate_benchmark.py`

❌ **Old documentation** (deprecated):
- `HOW_TO_TEST.md`
- `TESTING_WORKFLOW.md`
- `QUICK_START.md` (manual parts)

### What to Add

✅ **New files** (already created):
```
tests/
├── conftest.py           # Pytest configuration
├── test_bmi_report.py    # Automated tests
└── aggregate_results.py  # Aggregation script

pytest.ini                # Pytest settings
run_evals.sh              # Test runner
```

✅ **Dependencies**:
```toml
[project.optional-dependencies]
test = [
    "pytest>=7.4.0",
    "pytest-json-report>=1.5.0",
]
```

---

## How to Use New System

### Installation

```bash
cd template_agent/agent_config
pip install -e ".[test]"
```

### Run All Tests

```bash
cd skills
./run_evals.sh
```

### Run Specific Skill

```bash
./run_evals.sh --skill bmi-report
```

### View Results

```bash
cat ../workspaces/bmi-report-workspace/iteration-1/benchmark.json
```

---

## File Structure Comparison

### Before (Manual)
```
skills/
├── bmi-report/
│   ├── SKILL.md
│   └── evals/evals.json
├── scripts/
│   ├── setup_eval_workspace.sh      ❌ Removed
│   ├── run_single_eval.sh           ❌ Removed
│   ├── grade_eval.py                ❌ Removed
│   └── aggregate_benchmark.py       ❌ Removed
├── HOW_TO_TEST.md                   ❌ Deprecated
├── TESTING_WORKFLOW.md              ❌ Deprecated
└── QUICK_START.md                   ❌ Deprecated
```

### After (Automated)
```
skills/
├── bmi-report/
│   ├── SKILL.md
│   └── evals/evals.json
├── tests/                           ✅ New
│   ├── conftest.py
│   ├── test_bmi_report.py
│   └── aggregate_results.py
├── pytest.ini                       ✅ New
└── run_evals.sh                     ✅ New
```

---

## Key Differences

| Aspect | Old (Manual) | New (Automated) |
|--------|--------------|-----------------|
| Execution | Manual delegation | pytest automation |
| Grading | Manual JSON editing | Automatic + manual fallback |
| Trajectory | Not tracked | Fully tracked |
| Aggregation | Manual script run | Automatic after tests |
| Reproducibility | Low (manual steps) | High (automated) |
| CI/CD | Not possible | Ready |
| Methodology | agentskills.io | Deep Agents + agentskills.io |

---

## Integration Requirements

### Current State

Tests use **mock outputs** as placeholders.

### To Complete Integration

Replace mock functions in test files:

```python
# tests/test_bmi_report.py

def run_eval_with_skill(self, eval_id: int, tracer: ExecutionTracer) -> dict:
    tracer.start()

    skill_content = load_skill_content(self.skill_path)
    eval_case = next(e for e in self.evals_data['evals'] if e['id'] == eval_id)

    # REPLACE THIS:
    # output = self._mock_output_with_skill(eval_case)

    # WITH YOUR AGENT:
    from your_agent import run_agent
    output = run_agent(
        prompt=eval_case['prompt'],
        skill_content=skill_content,
        tracer=tracer
    )

    tracer.end()
    return {"output": output, "trajectory": tracer.get_trajectory()}
```

---

## Benefits of New System

### From Deep Agents Research

1. **Proven methodology** - Used by LangChain team (82% vs 9% improvement)
2. **Trajectory analysis** - Track tool calls and execution paths
3. **Statistical rigor** - Mean, stddev, confidence intervals
4. **Comparative testing** - Clear with/without skill comparison

### Our Implementation

1. **No external dependencies** - Runs without LangSmith
2. **Framework-agnostic** - Works with any agent
3. **Simple integration** - Just replace mock functions
4. **CI/CD ready** - Can run in automated pipelines
5. **Educational** - Clear code structure

---

## Backward Compatibility

### Old workspace data

Existing workspace directories are compatible:
```
workspaces/bmi-report-workspace/iteration-1/
```

New tests will use the same structure.

### Old evals.json

No changes needed - format is identical.

### Skills

No changes needed - skills follow agentskills.io spec.

---

## Next Steps

1. ✅ Install test dependencies
   ```bash
   pip install -e ".[test]"
   ```

2. ✅ Run tests to verify structure
   ```bash
   ./run_evals.sh
   ```

3. 🔄 Integrate real agent (replace mocks)
   - Edit `tests/test_*.py`
   - Replace `_mock_output_*` functions
   - Add your agent import and execution

4. 🔄 Run real evaluations
   ```bash
   ./run_evals.sh
   ```

5. 🔄 Analyze results
   ```bash
   cat ../workspaces/*/iteration-1/benchmark.json
   ```

6. 🔄 Iterate on skills based on findings

---

## Documentation

### New Primary Docs
- **EVALUATION_GUIDE.md** - Complete guide to new system
- **DEEPAGENTS_COMPARISON.md** - Deep Agents vs our implementation
- This file - Migration guide

### Reference Docs (Still Valid)
- **EVALS_README.md** - Eval methodology concepts
- **EVALUATION_SUMMARY.md** - Test suite overview

### Deprecated Docs (Can Remove)
- HOW_TO_TEST.md
- TESTING_WORKFLOW.md
- QUICK_START.md (manual parts)

---

## Troubleshooting

### Tests not finding skills

Check paths in `tests/conftest.py` - they should be relative to test file.

### pytest not found

```bash
pip install pytest
```

### No agent integration yet

That's expected! Tests use mocks until you integrate your agent.

To verify structure works:
```bash
pytest tests/test_bmi_report.py -v
```

Should pass with mock outputs.

---

## Summary

✅ **Migration Complete**
- Old manual scripts removed
- New pytest framework in place
- Deep Agents methodology adopted
- No LangSmith dependency required

🔄 **Ready for Integration**
- Replace mock functions with real agent
- Run tests
- Analyze results
- Iterate

📚 **Documentation Updated**
- EVALUATION_GUIDE.md - how to use new system
- DEEPAGENTS_COMPARISON.md - methodology comparison
- This file - migration reference

---

**Status:** Ready for agent integration!

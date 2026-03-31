# Skills Evaluation Test Suite - Summary

## Overview

Complete test suite created following [agentskills.io evaluation methodology](https://agentskills.io/skill-creation/evaluating-skills) for all three skills in the Red Hat Fitness Assistant project.

## Test Coverage

### 📊 bmi-report (5 test cases)

**Purpose:** Test BMI report generation with category-specific content

| Test ID | Scenario | Key Assertions |
|---------|----------|----------------|
| 1 | Normal BMI (22.5) | Value, category, normal-specific tips, disclaimer, friendly tone |
| 2 | Underweight BMI (17.8) | Underweight tips (weight gain focus), no weight loss advice |
| 3 | Overweight BMI (28.3) | Safe weight loss tips, sustainable approach, 0.5-1kg/week rate |
| 4 | Obese BMI (32.1) | Professional support recommendation, small goals, compassionate tone |
| 5 | Edge: Casual prompt | Complete report despite brief/casual input format |

**Total Assertions:** 37

**Coverage:**
- ✅ All BMI categories (Underweight, Normal, Overweight, Obese)
- ✅ Tone and language (friendly, non-judgmental, no negative words)
- ✅ Category-specific tips (not generic advice)
- ✅ Mandatory disclaimer inclusion
- ✅ Edge case: casual/minimal input

---

### 🔄 client-intake (8 test cases)

**Purpose:** Test coordination, unit conversion, and routing logic

| Test ID | Scenario | Key Assertions |
|---------|----------|----------------|
| 1 | Metric units (cm, kg) | Direct routing to analyst, no conversion |
| 2 | Imperial units (ft, in, lbs) | Correct conversion using sympy formulas, python3 usage |
| 3 | Imperial + email request | Sequential delegation (analyst → publisher), not parallel |
| 4 | Edge: Under 18 years | Decline with explanation, recommend healthcare professional |
| 5 | Edge: Pregnant | Decline with explanation, BMI doesn't apply |
| 6 | Edge: Unrealistic goals | Address timeline, offer realistic alternative, still route |
| 7 | Edge: Duplicate request | Recognize duplicate, skip re-analysis unless requested |
| 8 | Edge: Incomplete data | Ask for missing field, don't guess or estimate |

**Total Assertions:** 49

**Coverage:**
- ✅ Unit conversion (metric, imperial, mixed formats)
- ✅ Coordination flow (greeting, gathering, delegation)
- ✅ Edge cases (age restrictions, pregnancy, unrealistic goals)
- ✅ Sequential routing (analyst before publisher)
- ✅ Duplicate detection
- ✅ Missing data handling

---

### 📧 email-formatter (8 test cases)

**Purpose:** Test Gmail-compatible HTML email generation

| Test ID | Scenario | Key Assertions |
|---------|----------|----------------|
| 1 | Complete report | Valid HTML, inline CSS, all sections, 600px width |
| 2 | BMI + tips sections | Proper structure, no empty sections |
| 3 | BMI only (no tips) | Tips section skipped (not rendered empty) |
| 4 | BMI + tips + custom section | Additional sections rendered with consistent styling |
| 5 | Structured input | Extract data from formatted input (value, category, interpretation) |
| 6 | Casual/minimal input | Professional formatting despite casual prompt |
| 7 | Multiple tips + note | Handle bullets, multiple sections, proper ordering |
| 8 | Subject + sections + note | Subject recognized separately, all sections formatted |

**Total Assertions:** 62

**Coverage:**
- ✅ Gmail compatibility (inline CSS, no classes/style tags)
- ✅ Section handling (skip missing, render provided)
- ✅ HTML validity and structure
- ✅ Red Hat branding (#CC0000 header)
- ✅ Width constraints (600px)
- ✅ Disclaimer inclusion (mandatory)
- ✅ Input format flexibility

---

## Created Files

### Test Case Definitions

```
skills/
├── bmi-report/evals/evals.json          (5 test cases, 37 assertions)
├── client-intake/evals/evals.json       (8 test cases, 49 assertions)
└── email-formatter/evals/evals.json     (8 test cases, 62 assertions)
```

### Documentation

```
skills/
└── EVALS_README.md                      (Complete evaluation guide)
```

### Helper Scripts

```
skills/scripts/
├── setup_eval_workspace.sh              (Create workspace structure)
├── grade_eval.py                        (Generate grading templates, validate)
└── aggregate_benchmark.py               (Aggregate results into benchmark.json)
```

## Quick Start

### 1. Setup Workspace

```bash
cd template_agent/agent_config/skills
./scripts/setup_eval_workspace.sh bmi-report 1
```

This creates:
```
../workspaces/bmi-report-workspace/iteration-1/
├── eval-1/
│   ├── with_skill/
│   │   ├── outputs/
│   │   ├── timing.json
│   │   └── grading.json
│   └── without_skill/
│       ├── outputs/
│       ├── timing.json
│       └── grading.json
├── eval-2/ ... eval-5/
└── benchmark.json
```

### 2. Run Test Cases

For each test case in `evals.json`:

**With skill:**
```
Task: [prompt from eval]
Skill: /path/to/skills/bmi-report
Save to: workspaces/bmi-report-workspace/iteration-1/eval-1/with_skill/outputs/
```

**Without skill (baseline):**
```
Task: [same prompt, no skill]
Save to: workspaces/bmi-report-workspace/iteration-1/eval-1/without_skill/outputs/
```

Record timing data in `timing.json` after each run.

### 3. Grade Assertions

Generate grading template:
```bash
./scripts/grade_eval.py template bmi-report 1 with_skill
```

This shows:
- Test prompt and expected output
- Actual outputs
- Assertions to grade
- JSON template for grading.json

Update `grading.json` with pass/fail + evidence for each assertion.

### 4. Aggregate Results

After grading all test cases:
```bash
./scripts/aggregate_benchmark.py workspaces/bmi-report-workspace/iteration-1
```

This computes:
- Mean pass rates (with vs without skill)
- Mean time and token usage
- Deltas (skill impact)
- Standard deviations

### 5. Analyze & Iterate

Review:
- Which assertions consistently pass/fail?
- Where does the skill add value?
- What's the cost (tokens/time) vs benefit (pass rate)?

Update SKILL.md based on findings, then run iteration-2.

## Evaluation Methodology

Following agentskills.io best practices:

### ✅ Good Test Design
- **Realistic prompts** - Match how users actually phrase requests
- **Varied phrasings** - Casual to formal, brief to detailed
- **Edge cases** - Boundary conditions, unusual requests
- **Specific context** - Real values, not placeholders

### ✅ Good Assertions
- **Verifiable** - Can be checked objectively
- **Specific** - Clear pass/fail criteria
- **Meaningful** - Test qualities that matter
- **Not brittle** - Allow valid variations

### ✅ Progressive Disclosure
- Start with 2-3 test cases per skill
- Run first iteration, see what happens
- Add/refine assertions based on actual outputs
- Expand test suite as needed

### ✅ Iteration Loop
1. Run evals (with + without skill)
2. Grade assertions (automated + human review)
3. Aggregate results (benchmark.json)
4. Analyze patterns (what worked, what didn't)
5. Update SKILL.md
6. Repeat with iteration-N+1

## Statistics

**Total Test Cases:** 21 (5 + 8 + 8)
**Total Assertions:** 148 (37 + 49 + 62)
**Skills Covered:** 3/3 (100%)

**Edge Cases Covered:**
- Age restrictions (under 18)
- Pregnancy
- Unrealistic goals
- Duplicate requests
- Incomplete data
- Multiple input formats
- Missing sections
- Custom content

## Next Steps

1. **Run First Iteration**
   - Execute all test cases
   - Capture actual outputs
   - Record timing data

2. **Grade Outputs**
   - Use grade_eval.py for templates
   - Evaluate assertions
   - Document evidence

3. **Aggregate & Analyze**
   - Run aggregate_benchmark.py
   - Review pass rates
   - Identify patterns

4. **Iterate**
   - Update SKILL.md based on findings
   - Run iteration-2
   - Compare improvements

5. **Expand** (Optional)
   - Add more test cases for underrepresented scenarios
   - Test integration between skills
   - Add end-to-end workflows

## Validation

All skills pass official agentskills.io validation:

```bash
source .venv/bin/activate
skills-ref validate template_agent/agent_config/skills/bmi-report       ✓
skills-ref validate template_agent/agent_config/skills/client-intake    ✓
skills-ref validate template_agent/agent_config/skills/email-formatter  ✓
```

## References

- [agentskills.io - Evaluating Skills](https://agentskills.io/skill-creation/evaluating-skills)
- [agentskills.io - Best Practices](https://agentskills.io/skill-creation/best-practices)
- [agentskills.io - Specification](https://agentskills.io/specification)
- [skills-ref validator](https://github.com/agentskills/agentskills/tree/main/skills-ref)

---

**Created:** 2026-03-31
**Status:** Ready for iteration-1
**Skills:** bmi-report, client-intake, email-formatter

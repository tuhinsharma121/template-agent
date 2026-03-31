# Testing Workflow - Complete Guide

## 🎯 Quick Summary

To test a skill:
1. **Setup workspace** (one-time per iteration)
2. **Run test case** (with skill, then without)
3. **Record timing**
4. **Grade outputs**
5. **Repeat** for all test cases
6. **Aggregate** results

## 📝 Step-by-Step Workflow

### Step 1: Setup Workspace (One-Time)

```bash
cd template_agent/agent_config/skills
./scripts/setup_eval_workspace.sh bmi-report 1
```

This creates the directory structure for iteration-1.

---

### Step 2: Run Test Case WITH Skill

#### Option A: Using Helper Script (Recommended)

```bash
./scripts/run_single_eval.sh bmi-report 1 with_skill
```

This shows you:
- The prompt to execute
- Where to save outputs
- Example delegation command

#### Option B: Manual Delegation

Copy the delegation command from the script output:

```
Please complete this task using the skill at /Users/tuhinsharma/Documents/Git/template-agent/template_agent/agent_config/skills/bmi-report:

Task: My BMI is 22.5 and I'm in the Normal category. Can you give me a fitness report?

Instructions:
1. Load and follow the skill instructions from .../bmi-report/SKILL.md
2. Save your output to: .../workspaces/bmi-report-workspace/iteration-1/eval-1/with_skill/outputs/report.md
3. Report back with total tokens and duration
```

---

### Step 3: Record Timing (WITH Skill)

After the agent completes, it will report tokens and duration. Update:

```bash
echo '{"total_tokens": 2500, "duration_ms": 8500}' > \
  workspaces/bmi-report-workspace/iteration-1/eval-1/with_skill/timing.json
```

Replace `2500` and `8500` with actual values.

---

### Step 4: Run Test Case WITHOUT Skill (Baseline)

```bash
./scripts/run_single_eval.sh bmi-report 1 without_skill
```

Then use the delegation command it provides (no skill reference):

```
Please complete this task WITHOUT any skill guidance:

Task: My BMI is 22.5 and I'm in the Normal category. Can you give me a fitness report?

Instructions:
1. Do NOT use any skill files - rely only on your general knowledge
2. Save your output to: .../workspaces/bmi-report-workspace/iteration-1/eval-1/without_skill/outputs/report.md
3. Report back with total tokens and duration
```

---

### Step 5: Record Timing (WITHOUT Skill)

```bash
echo '{"total_tokens": 1800, "duration_ms": 5200}' > \
  workspaces/bmi-report-workspace/iteration-1/eval-1/without_skill/timing.json
```

---

### Step 6: Grade Outputs

#### Generate Grading Template

```bash
./scripts/grade_eval.py template bmi-report 1 with_skill
```

This shows:
- The actual output
- All assertions to check
- JSON template for grading

#### Update grading.json

Edit the file manually:

```bash
# For with_skill
nano workspaces/bmi-report-workspace/iteration-1/eval-1/with_skill/grading.json

# For without_skill
nano workspaces/bmi-report-workspace/iteration-1/eval-1/without_skill/grading.json
```

Update each assertion with `passed: true/false` and `evidence: "..."`.

#### Validate Grading

```bash
./scripts/grade_eval.py validate \
  workspaces/bmi-report-workspace/iteration-1/eval-1/with_skill/grading.json

./scripts/grade_eval.py validate \
  workspaces/bmi-report-workspace/iteration-1/eval-1/without_skill/grading.json
```

---

### Step 7: Repeat for All Evals

Repeat Steps 2-6 for:
- eval-2 (Underweight BMI)
- eval-3 (Overweight BMI)
- eval-4 (Obese BMI)
- eval-5 (Casual prompt)

Quick command reference:
```bash
# Eval 2
./scripts/run_single_eval.sh bmi-report 2 with_skill
./scripts/run_single_eval.sh bmi-report 2 without_skill

# Eval 3
./scripts/run_single_eval.sh bmi-report 3 with_skill
./scripts/run_single_eval.sh bmi-report 3 without_skill

# ... and so on
```

---

### Step 8: Aggregate Results

After completing all 5 evals (both with and without skill):

```bash
./scripts/aggregate_benchmark.py workspaces/bmi-report-workspace/iteration-1
```

This produces `benchmark.json` with:
- Pass rate comparison
- Token usage comparison
- Time comparison
- Delta (improvement)

---

## 📊 Example: Complete Test of Eval-1

```bash
# 1. Setup (if not done)
cd template_agent/agent_config/skills
./scripts/setup_eval_workspace.sh bmi-report 1

# 2. Get WITH skill instructions
./scripts/run_single_eval.sh bmi-report 1 with_skill

# 3. Run the task (use the delegation command shown)
# [Agent generates output to .../with_skill/outputs/report.md]

# 4. Record timing
echo '{"total_tokens": 2500, "duration_ms": 8500}' > \
  workspaces/bmi-report-workspace/iteration-1/eval-1/with_skill/timing.json

# 5. Get WITHOUT skill instructions
./scripts/run_single_eval.sh bmi-report 1 without_skill

# 6. Run the task (use the delegation command shown)
# [Agent generates output to .../without_skill/outputs/report.md]

# 7. Record timing
echo '{"total_tokens": 1800, "duration_ms": 5200}' > \
  workspaces/bmi-report-workspace/iteration-1/eval-1/without_skill/timing.json

# 8. Grade WITH skill
./scripts/grade_eval.py template bmi-report 1 with_skill
# [Review and update grading.json]

# 9. Grade WITHOUT skill
./scripts/grade_eval.py template bmi-report 1 without_skill
# [Review and update grading.json]

# 10. Validate grading
./scripts/grade_eval.py validate \
  workspaces/bmi-report-workspace/iteration-1/eval-1/with_skill/grading.json
./scripts/grade_eval.py validate \
  workspaces/bmi-report-workspace/iteration-1/eval-1/without_skill/grading.json
```

---

## 🔄 Test All 5 Evals - Quick Reference

```bash
cd template_agent/agent_config/skills

# For each eval (1-5):
for i in {1..5}; do
  echo "=== Testing Eval $i ==="

  # WITH skill
  ./scripts/run_single_eval.sh bmi-report $i with_skill
  # [Run the task, record timing]

  # WITHOUT skill
  ./scripts/run_single_eval.sh bmi-report $i without_skill
  # [Run the task, record timing]

  # Grade both
  ./scripts/grade_eval.py template bmi-report $i with_skill
  ./scripts/grade_eval.py template bmi-report $i without_skill
  # [Update grading.json files]

  echo "Eval $i complete"
  echo ""
done

# Aggregate
./scripts/aggregate_benchmark.py workspaces/bmi-report-workspace/iteration-1
```

---

## 📈 Analyzing Results

After aggregating, review `benchmark.json`:

```bash
cat workspaces/bmi-report-workspace/iteration-1/benchmark.json
```

Look for:
- **Pass rate delta**: Is with_skill better than without_skill?
- **Token cost**: How many extra tokens does the skill use?
- **Time cost**: Does the skill make things slower?
- **Trade-off**: Is the quality improvement worth the cost?

Example interpretation:
```json
{
  "delta": {
    "pass_rate": 0.43,      // 43% improvement with skill
    "time_seconds": 4.2,    // 4.2 seconds slower
    "tokens": 900           // 900 more tokens
  }
}
```

This means: The skill improves pass rate by 43 percentage points, but costs an extra 900 tokens and 4.2 seconds. **Worth it!**

---

## 🎓 Tips for Efficient Testing

### 1. Batch Similar Tests
Run all "with_skill" tests first, then all "without_skill" tests.

### 2. Use Spreadsheet for Grading
Copy assertion results to a spreadsheet for easier tracking.

### 3. Automate What You Can
- Use the helper scripts
- Create aliases for common commands
- Script the timing updates

### 4. Start with One Complete Test
Do eval-1 end-to-end first. This validates your workflow before scaling.

### 5. Use LLM for Grading Assistance
```
Here's the output and assertions. For each assertion, tell me pass/fail with evidence:

OUTPUT:
[paste output]

ASSERTIONS:
1. Report includes BMI value 22.5
2. Report states category as Normal
...
```

---

## 🔧 Troubleshooting

### Issue: Can't find skill path
**Solution**: Use absolute paths. Check with:
```bash
ls -la /Users/tuhinsharma/Documents/Git/template-agent/template_agent/agent_config/skills/bmi-report/
```

### Issue: Timing data not available
**Solution**: Ask the agent to report it explicitly in your delegation command.

### Issue: Grading is subjective
**Solution**: Be consistent. Use concrete evidence. When in doubt, mark as fail.

### Issue: Too many test cases
**Solution**: Start with 2-3. Expand after first successful iteration.

---

## 🚀 Next Steps

After completing **bmi-report** testing:

1. **Test client-intake** (8 test cases)
   ```bash
   ./scripts/setup_eval_workspace.sh client-intake 1
   ```

2. **Test email-formatter** (8 test cases)
   ```bash
   ./scripts/setup_eval_workspace.sh email-formatter 1
   ```

3. **Iterate on skills**
   - Review failed assertions
   - Update SKILL.md
   - Run iteration-2
   - Compare improvements

---

## 📚 Reference Files

- **HOW_TO_TEST.md** - Detailed testing methods
- **QUICK_START.md** - Quick reference guide
- **EVALS_README.md** - Complete evaluation methodology
- **EVALUATION_SUMMARY.md** - Test suite overview

---

**Ready to start testing?** Run:
```bash
cd template_agent/agent_config/skills
./scripts/run_single_eval.sh bmi-report 1 with_skill
```

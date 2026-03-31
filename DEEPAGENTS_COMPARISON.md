# Deep Agents vs Our Implementation - Skills Evaluation Comparison

## Summary

Deep Agents (LangChain) and our template-agent both follow the **agentskills.io specification** with similar approaches but different tooling.

---

## Skills Format: ✅ Compatible

Both use identical skill structure:
```
skill-name/
├── SKILL.md          # Required: frontmatter + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
└── assets/           # Optional: templates, resources
```

**Compatibility:** Our skills (`bmi-report`, `client-intake`, `email-formatter`) would work in Deep Agents with zero changes.

---

## Evaluation Approach

### Deep Agents (LangChain)

**Philosophy:** Comparative evaluation with clean environments

**Key Components:**
1. **LangSmith Integration** - Built-in observability and tracking
2. **Docker Environments** - Clean, reproducible test contexts
3. **pytest Integration** - Automated test execution
4. **Trajectory Analysis** - Track agent execution paths

**Evaluation Metrics:**
- Skill invocation rates
- Task completion steps
- Number of turns required
- Real-time execution duration
- Tool call match percentage

**Best Practices (from their blog):**
- Use constrained tasks (bug fixing) vs open-ended requests
- Test with/without skills for comparison
- Strategic placement in AGENTS.md/CLAUDE.md for reliable loading
- ~12 well-organized skills optimal (vs 20 causing confusion)
- Focus on real failures, not adversarial scenarios

**Tools:**
- LangSmith for observability
- Docker for isolation
- pytest for automation
- [skills-benchmarks repo](https://github.com/langchain-ai/skills-benchmarks) for examples

### Our Implementation (Template Agent)

**Philosophy:** Manual evaluation following agentskills.io methodology

**Key Components:**
1. **Workspace Structure** - Iteration-based organization
2. **Manual Test Execution** - Agent delegation for each test
3. **JSON-based Grading** - Structured assertion evaluation
4. **Python Scripts** - Helper tools for workflow

**Evaluation Metrics:**
- Pass rate (with vs without skill)
- Token usage delta
- Time delta
- Assertion-based quality checks

**Best Practices (from agentskills.io):**
- Start with 2-3 test cases, expand iteratively
- Realistic prompts matching actual user phrasing
- Progressive disclosure - refine assertions after seeing outputs
- Human review + automated grading
- Iteration loop: Run → Grade → Analyze → Improve

**Tools:**
- `setup_eval_workspace.sh` - Create iteration structure
- `run_single_eval.sh` - Generate test instructions
- `grade_eval.py` - Grading templates and validation
- `aggregate_benchmark.py` - Statistics computation

---

## Key Differences

| Aspect | Deep Agents | Our Implementation |
|--------|-------------|-------------------|
| **Automation** | High (pytest, LangSmith) | Manual (scripts guide process) |
| **Observability** | Built-in (LangSmith trajectories) | Manual (review outputs) |
| **Environment** | Docker containers | Workspace directories |
| **Grading** | Tool call matching, trajectory analysis | Assertion-based with evidence |
| **Integration** | Tightly coupled with LangChain ecosystem | Framework-agnostic |
| **Overhead** | Requires LangSmith account, Docker | Just Python 3 + file system |

---

## Similarities

✅ Both follow **agentskills.io specification**
✅ Both use **with/without skill comparison**
✅ Both emphasize **clean test environments**
✅ Both track **performance metrics** (tokens, time)
✅ Both support **iterative refinement**
✅ Both validate skills with **skills-ref**

---

## Deep Agents Strengths

1. **Automated execution** - pytest runs tests programmatically
2. **Rich observability** - LangSmith shows agent reasoning paths
3. **Trajectory datasets** - Can train evaluators on execution traces
4. **Ecosystem integration** - Works seamlessly with LangGraph, LangChain
5. **Proven at scale** - Used by LangChain team internally (82% vs 9% baseline)

---

## Our Implementation Strengths

1. **Simplicity** - No external services required
2. **Flexibility** - Works with any agent framework
3. **Transparency** - Clear, inspectable evaluation process
4. **Educational** - Scripts show exactly what's happening
5. **Portable** - Just files and Python scripts

---

## What We Can Adopt from Deep Agents

### 1. Trajectory Analysis
Track not just final outputs but agent execution paths:
- Which tools were called?
- In what order?
- How many iterations?
- Where did it get stuck?

**Implementation:** Add execution log capture to our test runner.

### 2. Tool Call Matching
Create evaluators that check if correct tools were invoked:
```python
def evaluate_tool_calls(expected_tools, actual_trace):
    """Check if agent used the right tools."""
    match_percentage = ...
    return score
```

**Implementation:** Add to `grade_eval.py` as mechanical check.

### 3. Docker Isolation (Optional)
For true reproducibility, run tests in containers:
```bash
docker run --rm -v $(pwd):/workspace test-image \
  python run_test.py
```

**Implementation:** Create `Dockerfile` for test environment.

### 4. Automated Test Runner
Create pytest-style automation:
```python
# test_skills.py
def test_bmi_report_normal():
    result = run_eval("bmi-report", 1, "with_skill")
    assert result.pass_rate > 0.8
```

**Implementation:** Wrap our scripts in pytest framework.

---

## Recommended Next Steps

### Immediate (Keep What Works)
1. ✅ Continue using our manual workflow - it's working
2. ✅ Complete iteration-1 for all skills
3. ✅ Analyze results and iterate on SKILL.md

### Short-term (Add Observability)
1. Add execution logging to track tool calls
2. Enhance grading with tool call validation
3. Create visualization of test results

### Long-term (Consider Automation)
1. Evaluate LangSmith integration (if using LangChain)
2. Build pytest test suite for automated runs
3. Consider Docker for CI/CD reproducibility

---

## Conclusion

**Our approach is valid and aligned with agentskills.io standards.**

Deep Agents adds automation and observability on top of the same foundational methodology. We can:
- Continue with our current approach (it works!)
- Selectively adopt Deep Agents patterns (trajectory analysis, tool validation)
- Migrate to Deep Agents later if we adopt LangChain ecosystem

**Bottom line:** We're doing it right. Deep Agents just automates what we do manually.

---

## Sources

- [Evaluating Skills - LangChain Blog](https://blog.langchain.com/evaluating-skills/)
- [Using Skills with Deep Agents - LangChain Blog](https://blog.langchain.com/using-skills-with-deep-agents/)
- [Deep Agents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [Deep Agents Skills Documentation](https://docs.langchain.com/oss/python/deepagents/skills)
- [Deep Agents GitHub](https://github.com/langchain-ai/deepagents)
- [Skills System - DeepWiki](https://deepwiki.com/langchain-ai/deepagents/2.4-skills-system)
- [agentskills.io specification](https://agentskills.io/specification)

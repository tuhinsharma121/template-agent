# Agent-Level Tests

Tests organized by agent rather than skill. Each agent is tested with its associated skill and tools in isolation.

## Structure

```
tests/agents/
├── conftest.py              # Agent creation fixtures and helpers
├── llm_judge.py             # LLM-as-judge evaluator using Gemini
├── mock_tools.py            # Mock MCP tools (calculate_bmi, search_web, send_email)
├── subagent_loader.py       # Loads subagent configs from agents/*.md
├── test_analyst.py          # Analyst subagent (bmi-report skill)
├── test_publisher.py        # Publisher subagent (email-formatter skill)
└── test_orchestrator.py     # Main orchestrator (client-intake skill)
```

## Agents

### Analyst (`test_analyst.py`)
- **Skill**: `bmi-report`
- **Tools**: `calculate_bmi`, `search_web`
- **Evals**: `template_agent/agent_config/skills/bmi-report/evals/evals.json`
- **Marker**: `@pytest.mark.analyst`

### Publisher (`test_publisher.py`)
- **Skill**: `email-formatter`
- **Tools**: `send_email`
- **Evals**: `template_agent/agent_config/skills/email-formatter/evals/evals.json`
- **Marker**: `@pytest.mark.publisher`

### Orchestrator (`test_orchestrator.py`)
- **Skill**: `client-intake`
- **Subagents**: Analyst + Publisher
- **Evals**: `template_agent/agent_config/skills/client-intake/evals/evals.json`
- **Marker**: `@pytest.mark.orchestrator`

## Running Tests

```bash
# Run all agent tests
pytest tests/agents/ -v

# Run specific agent
pytest tests/agents/test_analyst.py -m analyst -v
pytest tests/agents/test_publisher.py -m publisher -v
pytest tests/agents/test_orchestrator.py -m orchestrator -v

# Run single evaluation
pytest tests/agents/test_analyst.py -m analyst -k "eval-1" -v
```

## Test Output

Results saved to `tests/workspaces/{agent}-workspace/eval-{id}/`:
- `outputs/report.md` - Agent output
- `outputs/grading.json` - LLM judge results with pass/fail for each assertion

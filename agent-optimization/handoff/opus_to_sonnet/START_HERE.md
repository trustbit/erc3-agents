# Starting Instructions for Sonnet

## Your Task

You are implementing a task for the agent-optimization project. This project creates tools for optimizing LLM agents through data-driven experimentation.

## First Steps

1. **Read your task specification**:
   ```
   handoff/opus_to_sonnet/current_task.json
   ```

2. **Understand the project context**:
   ```
   docs/PROJECT.md           # Project overview and architecture
   handoff/shared/architecture.md  # System design
   ```

3. **Review coding standards and rules**:
   ```
   handoff/opus_to_sonnet/coding_standards.md
   handoff/opus_to_sonnet/escalation_rules.md
   ```

## Your Working Directory

You are in: `/home/vpenkov/projects/erc3/demo/rinat/agent-optimization/`

## Git Workflow

1. Create and switch to task branch:
   ```bash
   git status  # Ensure clean working directory
   git checkout dev  # Start from dev
   git pull  # Get latest changes
   git checkout -b [branch_name_from_task]
   ```

2. Work on the task, commit regularly:
   ```bash
   git add -A
   git commit -m "WIP: [description]"
   ```

3. Before marking complete:
   - Run all tests: `pytest tests/ -v`
   - Check coverage: `pytest --cov=agent-optimization tests/`
   - Fix any issues
   - Final commit: `git commit -m "Complete task [id]: [name]"`

## Dependencies Available

Check `requirements.txt` for available libraries:
- pydantic for validation
- numpy/scipy for statistics
- pytest for testing

## Integration with sgr-agent-store

The neighboring project `../sgr-agent-store/` contains:
- `config.py` with AgentConfig class (you need to convert this to JSON)
- `analysis/` module with session parsing tools

You can import from it:
```python
import sys
sys.path.append('../sgr-agent-store')
from config import AgentConfig
```

## When You're Done

1. Ensure all tests pass with >80% coverage
2. Write summary to: `handoff/sonnet_to_opus/implementation_log.md`
3. If any issues or questions: `handoff/sonnet_to_opus/escalation.json`
4. Say: "Task [id] complete. Ready for review."

## Remember

- Test before declaring complete
- Document decisions and trade-offs
- Escalate blockers immediately
- You have autonomy within task scope
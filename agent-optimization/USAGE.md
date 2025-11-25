# Task Manager Usage Guide

## Quick Start

The `task_manager.py` script facilitates communication between Opus and Sonnet models.

## Command Line Usage

```bash
# Show summary
python3 task_manager.py

# Create a new task
python3 task_manager.py create "Implement config validation"

# Check current status
python3 task_manager.py status

# Prepare context for Sonnet
python3 task_manager.py prepare

# Check for escalations
python3 task_manager.py escalations
```

## Python Usage

```python
from task_manager import TaskManager, Priority

tm = TaskManager()

# Create a high-priority task
task_id = tm.create_task(
    description="Fix critical bug in SPRT calculation",
    priority=Priority.HIGH,
    context_files=["analysis/sprt.py", "tests/test_sprt.py"]
)

# Check status
tm.check_status()

# Create an escalation
tm.create_escalation(
    issue="Pydantic v1 vs v2 conflict",
    options=[
        {"id": "A", "solution": "Upgrade to v2", "risk": "breaking changes"},
        {"id": "B", "solution": "Custom validator", "time": "+4h"},
    ],
    priority=Priority.HIGH,
    recommendation="B"
)

# Record a decision
tm.record_decision(
    decision="Use JSON for configurations",
    context="Need parallel experiments support",
    options_considered=["Keep Python", "JSON", "YAML"],
    rationale="JSON is universal and supports inheritance",
    impact="Need to migrate existing configs"
)
```

## Workflow Example

### 1. User creates task for Opus

```bash
python3 task_manager.py create "Design filter system for session analysis"
```

### 2. Opus reads task and creates plan

Opus reads: `handoff/opus_to_sonnet/current_task.json`
Opus writes: `handoff/opus_to_sonnet/implementation_plan.md`

### 3. User prepares context for Sonnet

```bash
python3 task_manager.py prepare
```

### 4. Sonnet implements

Sonnet reads files shown by prepare command
Sonnet writes: `handoff/sonnet_to_opus/status.md`

### 5. Check for issues

```bash
python3 task_manager.py escalations
```

## File Locations

- **Tasks**: `handoff/opus_to_sonnet/current_task.json`
- **Plans**: `handoff/opus_to_sonnet/implementation_plan.md`
- **Status**: `handoff/sonnet_to_opus/status.md`
- **Questions**: `handoff/sonnet_to_opus/questions.json`
- **Escalations**: `handoff/sonnet_to_opus/escalation_*.json`
- **Decisions**: `handoff/shared/decisions_log.md`

## Tips

1. Always check status before creating new tasks
2. Archive completed tasks to keep workspace clean
3. Use appropriate priority levels (low, medium, high, critical)
4. Include context files for complex tasks
5. Document all critical decisions in the decision log
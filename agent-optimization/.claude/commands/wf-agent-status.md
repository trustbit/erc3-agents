# Check workflow status of both agents

## Status Report

### 1. Git State
```bash
echo "=== Current Git Status ==="
git branch --show-current
git status --short
echo ""
echo "=== Recent commits ==="
git log --oneline -5
```

### 2. Current Task
Check what task is active:
- Read `handoff/opus_to_sonnet/current_task.json`
- Show task ID, name, and status

### 3. Agent Roles
- **Architect (Opus)**: Should be reviewing or preparing next task
- **Coder (Sonnet)**: Should be implementing current task

### 4. Handoff Files
Check communication files:
```bash
echo "=== Opus → Sonnet ==="
ls -la handoff/opus_to_sonnet/

echo "=== Sonnet → Opus ==="
ls -la handoff/sonnet_to_opus/

echo "=== Shared ==="
ls -la handoff/shared/
```

### 5. Implementation Plan Progress
Show progress from `implementation_plan.json`:
- Completed tasks
- In-progress tasks
- Next available tasks

### 6. Questions to Answer:
1. Which agent is currently active?
2. Are we on the correct branch?
3. Is the current task properly assigned?
4. Are there any pending escalations?
5. Is the handoff state clean?

Report any inconsistencies found!
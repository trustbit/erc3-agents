# Move to next task in workflow

## Pre-flight Checks

Before moving to next task, verify current task is complete:

```bash
echo "=== Current Task Status ==="
cat handoff/opus_to_sonnet/current_task.json | grep -E '"id"|"status"'

echo -e "\n=== Branch Check ==="
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

if [[ $CURRENT_BRANCH == task-* ]]; then
    echo "⚠️ Still on feature branch! Need to complete review first."
    echo "Run review process or merge to dev before proceeding."
    exit 1
fi
```

## Complete Current Task

If task is done but not merged:
```bash
# Merge current task branch
TASK_BRANCH=$(grep branch_name handoff/opus_to_sonnet/current_task.json | cut -d'"' -f4)
git merge $TASK_BRANCH
git branch -d $TASK_BRANCH

# Archive current task
mkdir -p handoff/archive/$(date +%Y%m%d)
cp handoff/opus_to_sonnet/current_task.json handoff/archive/$(date +%Y%m%d)/
cp handoff/sonnet_to_opus/*.* handoff/archive/$(date +%Y%m%d)/ 2>/dev/null || true
```

## Find Next Task

Use task_manager.py to get next task:
```python
from task_manager import TaskManager

tm = TaskManager()

# Update current task status
current_task_id = "1.1"  # Get from current_task.json
tm.update_plan_status(current_task_id, "completed")

# Get next available task
next_task = tm.get_next_task()

if next_task:
    print(f"Next task: {next_task['id']} - {next_task['name']}")
    print(f"Branch: {next_task['branch_name']}")
    print(f"Dependencies met: Yes")

    # Create task file for Sonnet
    tm.create_task_from_plan(next_task)
    tm.update_plan_status(next_task['id'], 'in_progress')
    print(f"✓ Task {next_task['id']} prepared in handoff/opus_to_sonnet/current_task.json")
else:
    print("No tasks available (check dependencies or phase completion)")
```

## Clean Handoff

Clean up communication files:
```bash
# Clear Sonnet's reports
rm -f handoff/sonnet_to_opus/implementation_log.md
rm -f handoff/sonnet_to_opus/escalation.json

echo "Handoff cleaned for next task"
```

## Notify Agents

**For Opus/Architect:**
- New task created and ready for monitoring
- Check implementation_plan.json for updated status

**For Sonnet/Coder:**
- New task available in `handoff/opus_to_sonnet/current_task.json`
- Read START_HERE.md and begin implementation
- Create feature branch from dev

## Summary

Report:
1. Previous task marked complete
2. Next task selected and prepared
3. Handoff directories cleaned
4. Both agents can proceed with new task
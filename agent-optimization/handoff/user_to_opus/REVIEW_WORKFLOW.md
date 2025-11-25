# Opus Review Workflow

## When Sonnet Completes a Task

This document guides Opus through reviewing Sonnet's work and managing the development workflow.

## Step 1: Gather Information

1. **Read Sonnet's implementation log**:
   ```
   handoff/sonnet_to_opus/implementation_log.md
   ```

2. **Check for escalations**:
   ```
   handoff/sonnet_to_opus/escalation.json
   ```

3. **Get task details**:
   ```
   handoff/opus_to_sonnet/current_task.json
   implementation_plan.json  # for full task specification
   ```

## Step 2: Review Process

Use the review template as a checklist:
```
handoff/user_to_opus/review_template.md
```

### Key Review Steps:

1. **Verify Deliverables**:
   ```bash
   # Check all expected files exist
   ls -la agent-optimization/config/
   ls -la tests/test_*.py
   ```

2. **Run Tests**:
   ```bash
   # Run all tests
   pytest tests/ -v

   # Check coverage
   pytest --cov=agent-optimization tests/
   ```

3. **Check Git History**:
   ```bash
   # Review commits on task branch
   git log --oneline task-1.1-config-loader

   # See changes
   git diff dev...task-1.1-config-loader
   ```

4. **Test Integration** (if applicable):
   ```bash
   # Try running the new functionality
   python agent-optimization/run_experiment.py --help
   python agent-optimization/run_experiment.py --config examples/config_baseline.json
   ```

## Step 3: Make Decision

Based on review results, choose one:

### ✅ APPROVED - Everything looks good
```python
# Update plan status
task_manager = TaskManager()
task_manager.update_plan_status("1.1", "completed")

# Merge to dev
git checkout dev
git merge task-1.1-config-loader

# Clean up and ensure on dev
git branch -d task-1.1-config-loader  # Delete local feature branch
git checkout dev  # Ensure we're on dev for next task

# Archive task documentation
mkdir -p handoff/archive/task-1.1/
mv handoff/opus_to_sonnet/current_task.json handoff/archive/task-1.1/
mv handoff/sonnet_to_opus/implementation_log.md handoff/archive/task-1.1/
```

### 🔄 MINOR FIXES NEEDED - Small issues
```python
# Document issues
issues = {
    "task_id": "1.1",
    "status": "needs_fixes",
    "issues": [
        "Missing docstring in loader.py line 45",
        "Test coverage only 75% - need tests for error cases",
        "Import path incorrect in __init__.py"
    ],
    "priority": "minor"
}

# Write fixes needed
with open("handoff/opus_to_sonnet/fixes_needed.json", "w") as f:
    json.dump(issues, f, indent=2)

# Keep task active - don't update status yet
```

### 🔧 MAJOR REWORK - Significant problems
```python
# Document major issues
rework = {
    "task_id": "1.1",
    "status": "needs_rework",
    "problems": [
        "Architecture doesn't match spec - using wrong inheritance model",
        "Performance issues - converter takes >10s for small config",
        "Missing critical validation"
    ],
    "suggested_approach": "Consider using composition instead of inheritance..."
}

# Write rework request
with open("handoff/opus_to_sonnet/rework_needed.json", "w") as f:
    json.dump(rework, f, indent=2)

# Update plan to reflect rework
task_manager.update_plan_status("1.1", "rework_needed")
```

### ❌ REJECT AND RESTART - Fundamental issues
```python
# Reset to clean state
git checkout dev
git branch -D task-1.1-config-loader  # Delete failed branch

# Document lessons learned
lessons = {
    "task_id": "1.1",
    "status": "rejected",
    "reasons": [
        "Fundamentally misunderstood requirement",
        "Introduced breaking changes to existing code"
    ],
    "lessons": "Need clearer spec about backward compatibility",
    "new_approach": "Start fresh with updated specification"
}

# Update task specification based on lessons
# Then create new task for retry
```

## Step 4: Prepare Next Task

If current task is approved:

```python
# Get next task from plan
task_manager = TaskManager()
next_task = task_manager.get_next_task()

if next_task:
    # Create task file for Sonnet
    task_manager.create_task_from_plan(next_task)

    # Clear previous work area
    rm handoff/sonnet_to_opus/implementation_log.md
    rm handoff/sonnet_to_opus/escalation.json

    # Notify ready for next task
    print(f"Task {next_task['id']}: {next_task['name']} ready for Sonnet")
else:
    print("No tasks available - check dependencies or phase completion")
```

## Step 5: Handle Escalations

If Sonnet reported blockers:

```python
# Read escalation
with open("handoff/sonnet_to_opus/escalation.json") as f:
    escalation = json.load(f)

# Decide on action
if escalation["severity"] == "blocker":
    # Must resolve before continuing
    if escalation["type"] == "missing_dependency":
        # May need to adjust task order
        pass
    elif escalation["type"] == "unclear_requirement":
        # May need user clarification
        pass

elif escalation["severity"] == "warning":
    # Can continue but should address
    pass
```

## Step 6: Report Progress

Create status report for user:

```python
# Summarize progress
report = {
    "date": datetime.now().isoformat(),
    "phase": "phase_1_foundation",
    "completed_tasks": ["1.1"],
    "in_progress": [],
    "blocked": [],
    "next_up": ["1.2"],
    "overall_progress": "12.5%",  # 1 of 8 tasks
    "notes": "Config loader complete and tested. Moving to schema validation."
}

# Write report
with open("handoff/opus_to_user/progress_report.json", "w") as f:
    json.dump(report, f, indent=2)
```

## Decision Tree

```
Sonnet says "Task complete"
    ↓
Read implementation_log.md
    ↓
Run tests → FAIL? → Document issues → Request fixes
    ↓ PASS
Check coverage → <80%? → Document gap → Request fixes
    ↓ ≥80%
Check deliverables → Missing? → Document → Request fixes
    ↓ All present
Check acceptance criteria → Not met? → Analyze why → Rework or Reject
    ↓ All met
APPROVE → Merge → Update plan → Next task
```

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Tests pass locally but not in review | Check Python version, dependencies |
| Coverage seems wrong | Clear pytest cache: `pytest --cache-clear` |
| Can't merge branch | Check for conflicts: `git merge dev` on feature branch first |
| Next task has unmet dependencies | Check plan, may need to complete other tasks first |
| Sonnet's work is good but not perfect | If it meets acceptance criteria, approve and note improvements for later |

## Remember

- **Be pragmatic**: Perfect is the enemy of done
- **Test everything**: Don't assume, verify
- **Document decisions**: Future you will thank you
- **Escalate early**: If blocked, get help quickly
- **Keep momentum**: Quick reviews keep Sonnet productive
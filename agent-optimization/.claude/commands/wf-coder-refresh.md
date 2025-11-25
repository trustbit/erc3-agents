# Force Coder (Sonnet) to re-read instructions

## For Sonnet/Coder:

You're working on the agent-optimization project as the **Coder** role.

**STOP and re-read your instructions:**

1. **Start Here** - Your main guide:
   ```
   handoff/opus_to_sonnet/START_HERE.md
   ```

2. **Current Task** - What you're implementing:
   ```
   handoff/opus_to_sonnet/current_task.json
   ```

3. **Coding Rules**:
   ```
   handoff/opus_to_sonnet/coding_standards.md
   handoff/opus_to_sonnet/escalation_rules.md
   ```

4. **Project Context**:
   ```
   docs/PROJECT.md
   handoff/shared/architecture.md
   ```

## Verify Your State:

Run these commands and confirm:
```bash
# Your current branch
git branch --show-current

# Should match branch_name from current_task.json
# Should NOT be 'dev' unless between tasks

# Check for uncommitted work
git status
```

## Confirm Understanding:

After reading, briefly state:
1. **Task ID**: [from current_task.json]
2. **Task Name**: [what you're building]
3. **Current Branch**: [should be task-X.X-*]
4. **Progress**: What's done, what's remaining
5. **Blockers**: Any issues or questions

If you were doing something else, STOP and focus on the task in current_task.json!
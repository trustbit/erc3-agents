# Force Architect (Opus) to re-read instructions

## For Opus/Architect:

You're working on the agent-optimization project as the **Architect** role.

**STOP and re-read your instructions:**

1. **Start Here** - Your main guide:
   ```
   handoff/user_to_opus/START_PROJECT.md
   ```

2. **Review Workflow**:
   ```
   handoff/user_to_opus/REVIEW_WORKFLOW.md
   handoff/user_to_opus/review_template.md
   ```

3. **Project Documentation**:
   ```
   docs/PROJECT.md
   docs/COLLABORATION.md
   implementation_plan.json
   ```

4. **Current State**:
   - Check `handoff/sonnet_to_opus/` for any reports from Sonnet
   - Check `handoff/opus_to_sonnet/current_task.json` for active task

## Verify Your Role:

You should be doing ONE of:
1. **Reviewing** - Sonnet completed a task, needs review
2. **Planning** - Preparing next task for Sonnet
3. **Waiting** - Sonnet is working, nothing to do yet

## Check Branch State:
```bash
# Should be on dev between tasks
git branch --show-current

# Check for any uncommitted work
git status
```

## Confirm Understanding:

After reading, state:
1. **Current Phase**: Review/Planning/Waiting
2. **Last Completed Task**: [if any]
3. **Task Under Review**: [if any]
4. **Next Task to Assign**: [from implementation_plan.json]
5. **Branch Status**: Should be on 'dev'

If you were in the middle of something, explain what and why.
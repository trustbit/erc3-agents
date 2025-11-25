# Workflow Management Commands

All commands for managing the Opus-Sonnet workflow. Use these with `/` prefix in Claude.

## 1. Status & Monitoring

### `/wf-agent-status`
**Purpose**: Check what both agents are doing
- Shows current git branch
- Displays active task
- Lists handoff files
- Reports implementation progress
- **Use when**: You want overview of current state

## 2. Agent Control

### `/wf-coder-refresh`
**Purpose**: Force Sonnet (Coder) to re-read instructions
- Makes Sonnet stop and reload START_HERE.md
- Verifies current task understanding
- Checks branch state
- **Use when**: Sonnet seems confused or off-task

### `/wf-arch-refresh`
**Purpose**: Force Opus (Architect) to re-read instructions
- Makes Opus reload START_PROJECT.md
- Verifies review workflow understanding
- Checks if should be reviewing or planning
- **Use when**: Opus seems confused about role

### `/wf-adjust-branches`
**Purpose**: Fix branch synchronization issues
- Diagnoses current branch state
- Moves agents to correct branches
- Handles uncommitted changes safely
- **Use when**: Agents on wrong branches

## 3. Task Management

### `/wf-task-state`
**Purpose**: Deep dive into current task progress
- Shows deliverables completion
- Runs tests and coverage
- Displays implementation log
- Checks for escalations
- **Use when**: Need detailed task status

### `/wf-task-escalate`
**Purpose**: Handle escalations from Sonnet
- Reads escalation details
- Provides resolution templates
- Archives resolved escalations
- **Use when**: Sonnet reports blocker

### `/wf-task-next`
**Purpose**: Move to next task in plan
- Completes current task
- Selects next from implementation_plan.json
- Prepares handoff files
- Cleans up for fresh start
- **Use when**: Task complete, ready for next

## 4. Quality Control

### `/wf-arch-job-check`
**Purpose**: Guide Opus through code review
- Runs test suite
- Checks coverage
- Validates acceptance criteria
- Provides decision framework
- **Use when**: Opus needs to review Sonnet's work

## 5. Validation & Maintenance

### `/wf-check-instructions`
**Purpose**: Verify instruction consistency
- Compares Coder vs Architect instructions
- Finds contradictions
- Checks branch references
- Validates file paths
- **Use when**: Suspecting miscommunication

### `/wf-tree-fix`
**Purpose**: Update project structure docs
- Compares actual vs documented structure
- Updates coding_standards.md
- Finds orphaned files
- **Use when**: Project structure changed

## Quick Decision Guide

| Situation | Command to Use |
|-----------|---------------|
| "What's happening?" | `/wf-agent-status` |
| "Sonnet doing wrong thing" | `/wf-coder-refresh` |
| "Opus confused" | `/wf-arch-refresh` |
| "Wrong git branch" | `/wf-adjust-branches` |
| "Is task done?" | `/wf-task-state` |
| "Sonnet hit blocker" | `/wf-task-escalate` |
| "Ready for next task" | `/wf-task-next` |
| "Review the code" | `/wf-arch-job-check` |
| "Instructions conflict?" | `/wf-check-instructions` |
| "Docs outdated?" | `/wf-tree-fix` |

## Typical Workflow Sequence

1. **Start of day**: `/wf-agent-status`
2. **If confused**: `/wf-coder-refresh` or `/wf-arch-refresh`
3. **During work**: `/wf-task-state` periodically
4. **If escalation**: `/wf-task-escalate`
5. **Task complete**: `/wf-arch-job-check`
6. **After review**: `/wf-task-next`
7. **If issues**: `/wf-check-instructions` or `/wf-adjust-branches`

## Emergency Commands

**Everything broken?**
1. `/wf-adjust-branches` - Fix git state
2. `/wf-coder-refresh` - Reset Sonnet
3. `/wf-arch-refresh` - Reset Opus
4. `/wf-agent-status` - Verify fixed

**Don't know what's wrong?**
1. `/wf-agent-status` - Get overview
2. `/wf-task-state` - Check task details
3. `/wf-check-instructions` - Look for conflicts
# Branch Management Protocol

## Problem Identified

There's a potential miscommunication risk between Opus and Sonnet regarding Git branches.

## Current Workflow

### Sonnet's Responsibilities:
1. Creates feature branches from dev
2. Works in feature branch
3. Commits changes
4. Reports completion

### Opus's Responsibilities:
1. Reviews work on feature branch
2. Merges to dev if approved
3. Creates next task

## Potential Issue

**Scenario:**
- After reviewing task 1.1, Opus might stay on `task-1.1-config-loader` branch
- When creating task 1.2, if Opus doesn't return to dev, confusion occurs
- Sonnet always starts from dev (`git checkout dev`), creating proper branches
- This can lead to divergent understanding of repository state

## Recommended Fix

### Update Opus's REVIEW_WORKFLOW.md:

After merging (APPROVED path):
```bash
# Merge to dev
git checkout dev
git merge task-1.1-config-loader

# Clean up and ensure on dev
git branch -d task-1.1-config-loader  # Delete merged local branch
git checkout dev  # Ensure we're on dev for next task
```

### Update Sonnet's START_HERE.md:

Before creating new branch:
```bash
# Ensure clean start
git status  # Ensure clean working directory
git stash  # If there are uncommitted changes

# Then proceed:
git checkout dev
git pull  # Get latest changes
git checkout -b [branch_name_from_task]
```

## Clear Ownership

| Action | Owner | Branch Context |
|--------|-------|----------------|
| Create feature branch | Sonnet | From dev |
| Work on implementation | Sonnet | In feature branch |
| Review code | Opus | Checkout feature branch |
| Merge to dev | Opus | From dev |
| Delete old branches | Opus | After merge |
| Stay on dev | Both | Between tasks |

## Golden Rule

**Between tasks, both models should be on dev branch.**

This ensures:
- Clean starting point for each task
- No confusion about current branch
- No accidental commits to wrong branch
- Clear separation between tasks

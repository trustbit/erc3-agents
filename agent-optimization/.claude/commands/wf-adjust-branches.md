# Fix branch synchronization issues

## Diagnose Branch State

First, check current situation:
```bash
echo "=== Current branch ==="
git branch --show-current

echo -e "\n=== All branches ==="
git branch -a

echo -e "\n=== Current task ==="
cat handoff/opus_to_sonnet/current_task.json | grep -E '"id"|"branch_name"|"status"'

echo -e "\n=== Uncommitted changes ==="
git status --short
```

## Determine Correct State

Based on task status:
- **No active task** → Both agents should be on `dev`
- **Task in progress** → Sonnet on feature branch, Opus on `dev`
- **Task in review** → Opus checks out feature branch temporarily
- **Task completed** → Both return to `dev`

## Fix Common Issues

### Issue 1: Sonnet on wrong branch
If Sonnet is on `dev` but should be working:
```bash
# Get branch name from current_task.json
BRANCH_NAME=$(grep branch_name handoff/opus_to_sonnet/current_task.json | cut -d'"' -f4)

# Stash any changes
git stash

# Switch to correct branch
git checkout $BRANCH_NAME || git checkout -b $BRANCH_NAME

# Restore changes if any
git stash pop
```

### Issue 2: Opus stuck on feature branch
If Opus is on feature branch after review:
```bash
# Stash any changes
git stash

# Return to dev
git checkout dev

# Clean up if needed
git stash drop
```

### Issue 3: Both on wrong branches
Reset both to safe state:
```bash
# Save any important work
git stash save "Emergency stash before branch fix"

# Both return to dev
git checkout dev

# Check task status
# If task active, Sonnet should switch to feature branch
# If no task, both stay on dev
```

## Verify Fix

After adjustment:
1. Sonnet on correct branch for current task (or dev if no task)
2. Opus on dev (unless actively reviewing)
3. No uncommitted changes lost
4. Task can proceed normally

Report the fix applied!
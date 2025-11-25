# Quality check for Architect (Opus) to review Coder's work

## For Opus/Architect:

Review the completed work using your review template.

## Step 1: Gather Information

Read these files:
1. `handoff/sonnet_to_opus/implementation_log.md` - Sonnet's report
2. `handoff/sonnet_to_opus/escalation.json` - Any issues (if exists)
3. `handoff/opus_to_sonnet/current_task.json` - Task requirements

## Step 2: Run Review Checklist

Follow `handoff/user_to_opus/review_template.md`:

### Deliverables Check
```bash
echo "=== Checking Deliverables ==="
# List expected files from current_task.json and verify each exists
```

### Test Execution
```bash
echo "=== Running Tests ==="
pytest tests/ -v
```

### Coverage Check
```bash
echo "=== Checking Coverage ==="
pytest --cov=agent-optimization tests/
# Should be ≥80%
```

### Code Quality
Check for:
- [ ] Proper error handling
- [ ] Clear docstrings
- [ ] No hardcoded values
- [ ] Follows coding standards

## Step 3: Validate Acceptance Criteria

For each criterion in current_task.json:
1. **"Loads JSON config when path provided"**
   - Test: `python run_experiment.py --config test.json`
   - Expected: Config loads successfully

2. **"Auto-converts config.py to JSON"**
   - Test: Run without --config
   - Expected: Converts and saves to experiments/generated/

3. **"Saved to experiments/generated/"**
   - Check: Directory exists and contains converted configs

4. **"Tests pass with >80% coverage"**
   - Verified above

5. **"Graceful error handling"**
   - Test with missing file
   - Expected: Clear error message, no crash

## Step 4: Make Decision

Based on review, choose:

### ✅ APPROVED
All criteria met, tests pass, code quality good:
```bash
git checkout dev
git merge [task-branch]
git branch -d [task-branch]
```

### 🔄 MINOR FIXES NEEDED
Small issues to address:
- List specific fixes needed
- Keep task active
- Request fixes from Sonnet

### 🔧 MAJOR REWORK
Significant problems found:
- Document issues
- Consider new approach
- May need to restart task

## Step 5: Document Decision

Create review record:
```bash
cat > handoff/archive/review_task_X.X.md << 'EOF'
# Review of Task X.X

## Decision: [APPROVED/FIXES/REWORK]

## Test Results
- Tests: [PASS/FAIL]
- Coverage: XX%

## Criteria Met
- [✓/✗] Criterion 1
- [✓/✗] Criterion 2
...

## Issues Found
- [List any issues]

## Action Taken
- [What was done]

Reviewed by: Opus
Date: $(date)
EOF
```

Report review outcome!
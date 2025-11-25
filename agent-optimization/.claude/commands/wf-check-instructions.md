# Check instruction consistency between Coder and Architect

## Analyze Instructions for Both Roles

### Check for Contradictions

Compare key workflows and look for conflicts:

1. **Git Branch Management**
   - Coder instructions: `handoff/opus_to_sonnet/START_HERE.md`, `escalation_rules.md`
   - Architect instructions: `handoff/user_to_opus/REVIEW_WORKFLOW.md`, `START_PROJECT.md`
   - Both should agree on:
     - Base branch (dev)
     - Branch naming (task-X.X-*)
     - Who creates/deletes branches

2. **Task Handoff**
   - Where Coder looks for tasks: `handoff/opus_to_sonnet/current_task.json`
   - Where Architect puts tasks: should be same location
   - Format consistency

3. **Communication Paths**
   - Coder → Architect: `handoff/sonnet_to_opus/`
   - Architect → Coder: `handoff/opus_to_sonnet/`
   - Shared info: `handoff/shared/`

4. **Testing Requirements**
   - Coder's understanding: Check in `escalation_rules.md`
   - Architect's expectations: Check in `review_template.md`
   - Should match (>80% coverage, all tests pass)

## Run Consistency Checks

```python
import json
import re

issues = []

# Check 1: Branch references
files_to_check = [
    "handoff/opus_to_sonnet/START_HERE.md",
    "handoff/opus_to_sonnet/escalation_rules.md",
    "handoff/user_to_opus/REVIEW_WORKFLOW.md",
    "handoff/user_to_opus/START_PROJECT.md"
]

for file in files_to_check:
    with open(file, 'r') as f:
        content = f.read()

        # Check for 'main' branch references (should be 'dev')
        if 'checkout main' in content or 'merge.*main' in content:
            issues.append(f"{file}: Still references 'main' branch (should be 'dev')")

        # Check for 'origin' references (should be removed)
        if 'origin' in content and 'git' in content:
            issues.append(f"{file}: Contains 'origin' references (should be local only)")

# Check 2: File paths consistency
coder_expects = "handoff/opus_to_sonnet/current_task.json"
arch_writes = "handoff/opus_to_sonnet/current_task.json"
if coder_expects != arch_writes:
    issues.append(f"Task file mismatch: Coder expects {coder_expects}, Architect writes to {arch_writes}")

# Check 3: Testing requirements
coverage_requirements = []
for file in ["handoff/opus_to_sonnet/escalation_rules.md", "handoff/user_to_opus/review_template.md"]:
    with open(file, 'r') as f:
        content = f.read()
        match = re.search(r'(\d+)%\s*coverage', content)
        if match:
            coverage_requirements.append((file, int(match.group(1))))

if len(set(req[1] for req in coverage_requirements)) > 1:
    issues.append(f"Coverage requirement mismatch: {coverage_requirements}")

# Report
if issues:
    print("⚠️ INCONSISTENCIES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✅ No inconsistencies found")
```

## Check Role Responsibilities

Verify clear separation:

| Action | Coder (Sonnet) | Architect (Opus) |
|--------|----------------|------------------|
| Create feature branch | ✓ | |
| Implement code | ✓ | |
| Run tests | ✓ | ✓ |
| Review code | | ✓ |
| Merge to dev | | ✓ |
| Create next task | | ✓ |
| Handle escalations | Report | Resolve |

## Common Issues to Look For

1. **Different base branches** - One says main, other says dev
2. **Conflicting test requirements** - Different coverage percentages
3. **File location mismatches** - Looking in different places
4. **Role confusion** - Both trying to do same thing
5. **Missing handoff steps** - Gap in the workflow

## Suggested Fixes

For each issue found, suggest fix:

```markdown
### Issue: [Description]
**Location**: [File and line]
**Current**: [What it says]
**Should be**: [Correct version]
**Fix**:
\`\`\`
[Command to fix]
\`\`\`
```

## Report

Generate report with:
1. Number of files checked
2. Issues found (if any)
3. Severity assessment
4. Recommended fixes
5. Validation command to run after fixes
# Code Review Template for Opus

Use this template to review Sonnet's implementation. Check each item and make a decision.

## Task Information

**Task ID**: [task_id]
**Task Name**: [task_name]
**Branch**: [branch_name]
**Reviewer**: Opus
**Review Date**: [date]

## 1. Deliverables Checklist

Verify all expected files exist and are functional:

- [ ] All files from `deliverables` list are present
- [ ] Files are in correct locations
- [ ] No unexpected files added (unless documented)
- [ ] File permissions are appropriate

**Missing Files** (if any):
```
-
```

## 2. Tests and Coverage

### Test Execution
```bash
# Run this command
pytest tests/ -v

# Result:
- [ ] All tests pass
- [ ] No warnings that indicate problems
```

### Coverage Check
```bash
# Run this command
pytest --cov=agent-optimization tests/

# Result:
- [ ] Coverage >= 80%
- [ ] Critical paths have 100% coverage
```

**Test Issues** (if any):
```
-
```

## 3. Acceptance Criteria

Check each criterion from the task specification:

1. - [ ] [Criterion 1 from task]
2. - [ ] [Criterion 2 from task]
3. - [ ] [Criterion 3 from task]
4. - [ ] [Criterion 4 from task]
5. - [ ] [Criterion 5 from task]

**Unmet Criteria** (if any):
```
-
```

## 4. Code Quality Assessment

### Architecture and Design
- [ ] Follows the specified interfaces
- [ ] No unnecessary coupling between modules
- [ ] Clear separation of concerns
- [ ] Appropriate abstraction levels

### Code Style
- [ ] Follows coding standards (PEP8, Black formatting)
- [ ] Type hints present and correct
- [ ] Docstrings complete and accurate
- [ ] Comments explain "why" not "what"

### Error Handling
- [ ] Appropriate exception handling
- [ ] Informative error messages
- [ ] Graceful degradation where applicable
- [ ] No bare except clauses

### Performance
- [ ] No obvious performance issues
- [ ] Appropriate data structures used
- [ ] No unnecessary loops or recursion
- [ ] Memory usage reasonable

## 5. Implementation Notes Review

Review Sonnet's implementation log:

### Decisions Made
- [ ] Decisions are reasonable and well-justified
- [ ] Trade-offs are acceptable
- [ ] No critical architecture violations

### TODOs and Technical Debt
- [ ] TODOs are reasonable and non-blocking
- [ ] Technical debt is documented
- [ ] No critical issues marked as TODO

## 6. Security and Safety

- [ ] No hardcoded credentials or secrets
- [ ] Input validation present where needed
- [ ] File paths properly validated
- [ ] No SQL injection vulnerabilities
- [ ] No command injection vulnerabilities

## 7. Integration Check

### With Existing Code
- [ ] Integrates properly with existing modules
- [ ] No breaking changes to existing interfaces
- [ ] Migration path clear (if changes needed)

### With Dependencies
- [ ] All dependencies declared
- [ ] Version conflicts resolved
- [ ] No unnecessary dependencies added

## 8. Documentation

- [ ] README updated (if applicable)
- [ ] API documentation complete
- [ ] Examples work as expected
- [ ] Changelog entry added (if applicable)

## 9. Git History

```bash
# Check commit history
git log --oneline [branch_name]

- [ ] Commits are logical and well-messaged
- [ ] No sensitive data in history
- [ ] Ready to merge (no WIP commits)
```

## 10. Final Decision

### Overall Assessment

**Strengths**:
-
-
-

**Issues Found**:
-
-
-

### Decision

Select one:

- [ ] **✅ APPROVED** - Ready to merge to dev
  ```bash
  git checkout dev
  git merge [branch_name]
  ```

- [ ] **🔄 MINOR FIXES NEEDED** - Small issues to address
  - List specific fixes needed:
    1.
    2.
    3.

- [ ] **🔧 MAJOR REWORK** - Significant issues found
  - Key problems:
    1.
    2.
  - Suggested approach:


- [ ] **❌ REJECT AND RESTART** - Fundamental issues, better to start over
  - Reasons:
    1.
    2.
  - New approach recommendation:


## Actions to Take

Based on the decision above:

### If Approved:
1. Merge branch to dev
2. Update task status to "completed"
3. Archive task documentation
4. Proceed to next task

### If Fixes Needed:
1. Create new task with specific fixes
2. Keep branch active
3. Sonnet addresses issues
4. Re-review after fixes

### If Rework/Reject:
1. Document lessons learned
2. Update task specifications if needed
3. Create new task with better approach
4. Consider architectural adjustments

## Review Notes

**Additional Comments**:
```
[Any additional observations, suggestions, or context for future reference]
```

**Lessons Learned**:
```
[What worked well, what could be improved in the process]
```

---

## Review Metadata

- Review Duration: [time spent]
- Tools Used: [pytest, mypy, black, etc.]
- Review Depth: [basic|standard|thorough]

## Sign-off

By completing this review, I confirm that I have:
- [ ] Checked all deliverables
- [ ] Run all tests
- [ ] Verified acceptance criteria
- [ ] Considered security implications
- [ ] Made a clear decision

**Reviewer**: Opus
**Timestamp**: [ISO timestamp]
**Decision**: [APPROVED|FIXES_NEEDED|REWORK|REJECT]
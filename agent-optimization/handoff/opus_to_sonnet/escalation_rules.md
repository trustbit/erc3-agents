# Escalation Rules for Sonnet

## Your Primary Directive

You are implementing tasks according to specifications. You have autonomy within the task scope but must escalate when facing architectural decisions or blocking issues.

## Before Marking Task Complete

### Required Checklist:
1. **Run all tests**
   ```bash
   pytest tests/ -v
   ```
   Fix any failing tests before proceeding.

2. **Check test coverage**
   ```bash
   pytest --cov=agent-optimization tests/
   ```
   Ensure coverage >80%. If unable to achieve, document why.

3. **Run type checking (if applicable)**
   ```bash
   mypy agent-optimization/
   ```

4. **Format code**
   ```bash
   black agent-optimization/ tests/
   ```

5. **Commit your work**
   ```bash
   git add .
   git commit -m "Complete task [task_id]: [brief description]"
   ```

6. **Update implementation log**
   Write summary to `handoff/sonnet_to_opus/implementation_log.md`

## Decision Matrix

### ✅ Continue Working (Don't Escalate)

Handle these situations yourself:
- **Multiple implementation paths**: Choose the clearest/simplest, document why
- **Minor optimization opportunities**: Add TODO comments, continue
- **Test failures you understand**: Fix and continue
- **Missing test cases**: Write them
- **Code style issues**: Fix according to standards
- **Unclear variable names**: Use domain conventions
- **Small refactoring needs**: Do it if it improves clarity

### 🟡 Document but Continue

Write to `handoff/sonnet_to_opus/implementation_log.md`:
- **Trade-offs made**: "Chose approach X over Y because..."
- **Assumptions**: "Assumed field X means..."
- **Performance considerations**: "This might be slow for N>1000..."
- **Technical debt added**: "TODO: Refactor when..."
- **Workarounds used**: "Due to library limitation..."

Format:
```markdown
## Task [task_id] Implementation Notes

### Decisions Made
- Chose SQLite over JSON file for state persistence (simpler than PostgreSQL, adequate for <10k records)

### Assumptions
- Config files will be <10MB (no streaming needed)
- User has write permissions to experiments/ directory

### TODOs
- [ ] Add caching for frequently accessed configs
- [ ] Optimize batch processing for >100 sessions
```

### 🔴 Escalate Immediately

Write to `handoff/sonnet_to_opus/escalation.json` and STOP:

**Blocking Issues:**
- Need to change interface specified in task
- Critical dependency is missing or incompatible
- Security vulnerability discovered
- Cannot achieve test coverage due to design issue
- Task requirements are contradictory

**Architectural Decisions:**
- Choice affects other modules not in current task
- Performance approach (cache vs. recompute, sync vs. async)
- Data structure changes affecting persistence
- Need to add external dependency not listed

**Equal Trade-offs:**
- Two approaches with different significant impacts
- Choice depends on future requirements not specified

### Escalation Format

```json
{
  "task_id": "1.2",
  "timestamp": "2024-11-25T10:30:00Z",
  "severity": "blocking|high|medium",
  "issue": "Clear, specific description of the problem",
  "context": "What you were trying to do when issue arose",
  "attempted_solutions": [
    "What you tried and why it didn't work"
  ],
  "options": [
    {
      "approach": "A: Modify interface",
      "pros": ["Cleaner API", "More flexible"],
      "cons": ["Breaking change", "Affects module X"],
      "effort": "2 hours"
    },
    {
      "approach": "B: Workaround with adapter",
      "pros": ["No breaking change", "Isolated impact"],
      "cons": ["More complex", "Technical debt"],
      "effort": "1 hour"
    }
  ],
  "recommendation": "Approach B - maintains compatibility while solving the immediate problem",
  "can_continue": false,
  "waiting_for": "decision on interface change"
}
```

## Common Scenarios

### Scenario: Test Coverage Below 80%
1. First try: Add more test cases
2. If untestable code (e.g., external API): Mock it
3. If design prevents testing: ESCALATE with explanation

### Scenario: Performance Concern
1. If current approach works but might be slow: Document in TODO, continue
2. If definitely too slow for requirements: Try optimization
3. If optimization requires architecture change: ESCALATE

### Scenario: Missing Specification Detail
1. If industry standard exists: Use it, document assumption
2. If multiple standards: Choose simplest, document why
3. If critical to correctness: ESCALATE for clarification

### Scenario: Dependency Conflict
1. If version difference minor: Try to resolve
2. If requires major upgrade: ESCALATE
3. If alternative package exists: Document change, use alternative

## Git Branch Protocol

1. **Start work**:
   ```bash
   git status  # Ensure clean working directory
   git checkout dev  # Always start from dev
   git pull  # Get latest changes
   git checkout -b [branch_name_from_task]
   ```

2. **Regular commits** (every 1-2 hours or logical checkpoint):
   ```bash
   git add -A
   git commit -m "WIP: [what you're working on]"
   ```

3. **Before completion**:
   ```bash
   # Run tests one more time
   pytest tests/

   # Final commit
   git add -A
   git commit -m "Complete task [task_id]: [description]"
   ```

## Remember

- **You have autonomy within task scope** - don't escalate minor decisions
- **Tests are your safety net** - comprehensive tests prevent issues
- **Document why, not what** - code shows what, comments/docs explain why
- **Escalation is not failure** - it's responsible development
- **User time is expensive** - batch questions, provide context

## Quick Reference

**Continue if**: You can solve it, test it, and document it
**Escalate if**: It changes interfaces, affects other modules, or blocks progress
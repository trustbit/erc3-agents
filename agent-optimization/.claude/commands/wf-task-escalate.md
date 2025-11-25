# Handle task escalation

## Check for Escalations

First, see if there's an escalation:
```bash
if [ -f "handoff/sonnet_to_opus/escalation.json" ]; then
    echo "=== Current Escalation ==="
    cat handoff/sonnet_to_opus/escalation.json | python3 -m json.tool
else
    echo "No escalation found"
    exit 0
fi
```

## Analyze Escalation Type

Common escalation types and resolutions:

### 1. **Missing Dependencies**
**Symptom**: Can't import module, package not found
**Resolution**:
- Check requirements.txt
- Add missing package
- Or adjust implementation to avoid dependency

### 2. **Unclear Requirements**
**Symptom**: Acceptance criteria ambiguous
**Resolution**:
- Clarify the requirement
- Update current_task.json
- Provide specific guidance

### 3. **Technical Blocker**
**Symptom**: Framework limitation, incompatible versions
**Resolution**:
- Approve workaround
- Change approach
- Modify requirements

### 4. **Scope Question**
**Symptom**: Task seems bigger than expected
**Resolution**:
- Reduce scope
- Split into subtasks
- Clarify what's required vs nice-to-have

## Resolution Actions

Based on escalation type, choose action:

```python
# Create resolution file
cat > handoff/opus_to_sonnet/escalation_resolution.md << 'EOF'
# Escalation Resolution

## Decision
[Your decision here]

## Rationale
[Why this approach]

## Specific Instructions
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Updated Acceptance Criteria (if changed)
- [New criteria if needed]

## Continue with task
Proceed with implementation using this guidance.
EOF
```

## Clear Escalation

After resolution:
```bash
# Archive the escalation
mv handoff/sonnet_to_opus/escalation.json handoff/archive/escalation_$(date +%Y%m%d_%H%M%S).json

# Notify Sonnet to continue
echo "Escalation resolved. Check handoff/opus_to_sonnet/escalation_resolution.md for guidance."
```

## Common Quick Resolutions

1. **"Use simpler approach"** - Don't over-engineer
2. **"Skip for now"** - Mark as TODO, continue
3. **"Use mock/stub"** - Implement interface, fake internals
4. **"Change to..."** - Provide specific alternative
5. **"Approved as-is"** - Current approach is fine
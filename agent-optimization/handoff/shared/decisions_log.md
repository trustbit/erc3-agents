# Decision Log

## 2024-11-25: Project Inception

### Decision: Use JSON for configurations instead of Python
**Context**: Need to support parallel experiments and runtime parameter override
**Options Considered**:
1. Keep Python configs - Simple but inflexible
2. JSON - Standard, validatable, inheritance-friendly
3. YAML - More readable but adds dependency

**Decision**: JSON with Pydantic validation
**Rationale**:
- Already using Pydantic for validation
- JSON is universal and tool-friendly
- Supports inheritance and override naturally

---

### Decision: SPRT for experiment evaluation
**Context**: Limited resources (20-50 sessions/day)
**Options Considered**:
1. Fixed sample size - Simple but wasteful
2. SPRT - Complex but efficient
3. Bayesian methods - Most flexible but complex

**Decision**: SPRT with α=0.05, β=0.10
**Rationale**:
- 30-50% reduction in required sessions
- Well-established statistical properties
- Clear stopping criteria

---

### Decision: File-based model handoff
**Context**: Need communication between Opus and Sonnet
**Options Considered**:
1. Manual copy-paste - Full control but tedious
2. File-based - Simple and debuggable
3. API-based - Automated but complex

**Decision**: File-based with defined structure
**Rationale**:
- Easy to implement and debug
- Preserves full context
- Can migrate to API later if needed

---

### Decision: Phased implementation
**Context**: Large scope, need quick wins
**Phases**:
1. Foundation (config, basic stats) - 20h
2. Automation (SPRT, runner) - 14h
3. Intelligence (patterns, LLM) - 25h

**Rationale**:
- Delivers value quickly
- Each phase is independently useful
- Can adjust based on learnings

---

## Template for Future Decisions

### Decision: [Title]
**Date**: YYYY-MM-DD
**Context**: [Why this decision is needed]
**Options Considered**:
1. Option A - [pros/cons]
2. Option B - [pros/cons]

**Decision**: [What was chosen]
**Rationale**: [Why this option]
**Impact**: [What changes]
**Reversible**: [Yes/No and effort required]
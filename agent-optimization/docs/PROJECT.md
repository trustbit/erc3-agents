# Agent Optimization Framework

## Project Overview

**Goal**: Build a data-driven optimization system for LLM agents, enabling controlled experimentation and systematic improvement.

**Context**: Optimizing SGR (Schema-Guided Reasoning) agents on ERC3 benchmark, with plans to extend to other agent types.

**Key Principles**:
- Evidence-based decisions through statistical analysis
- Exploration-friendly (temporary regressions are normal)
- Cost-effectiveness balance (success rate vs token consumption)
- Parallel experimentation support

## Core Objectives

1. **Dual Optimization**: Balance success rate and token cost
2. **Rapid Experimentation**: SPRT for early stopping
3. **Deep Analysis**: Understand why agents succeed or fail
4. **Scalability**: Support 20-50 sessions/day, potentially 100s with free models

## Architecture

### System Components

```
agent-optimization/
├── analysis/
│   ├── core/
│   │   ├── filters.py        # Flexible session filtering
│   │   ├── aggregators.py    # Statistical metrics
│   │   ├── extractors.py     # Feature extraction
│   │   └── comparators.py    # A/B comparison logic
│   ├── experiments/
│   │   ├── tracker.py        # Experiment management
│   │   ├── sprt.py          # Sequential testing
│   │   └── pareto.py        # Multi-objective optimization
│   └── reports/
│       └── generator.py      # Automated insights
```

### Data Flow

```
Sessions → Parse → Filter → Analyze → Decide
    ↑                                      ↓
    └──────── New Config ←─────────────────┘
```

## Technical Decisions

### 1. Configuration System
- **Decision**: Migrate from Python config to JSON
- **Rationale**:
  - Enables parallel experiments
  - Easier versioning and inheritance
  - Runtime parameter override
- **Implementation**:
  ```json
  {
    "experiment_id": "exp_042",
    "parent": "exp_041",
    "model_id": "gpt-4o-mini",
    "guidelines": ["Check limits first", "..."]
  }
  ```

### 2. Statistical Testing
- **Method**: Sequential Probability Ratio Test (SPRT)
- **Parameters**: α=0.05, β=0.10, min_effect_size=0.15
- **Benefit**: 30-50% fewer sessions needed vs fixed sample size

### 3. Metrics Framework

#### Primary Metrics
- **Success Rate**: % of tasks completed correctly
- **Token Efficiency**: tokens per task
- **Cost**: tokens × model price

#### Trajectory Metrics
- **Early Termination Rate**: % correctly rejected impossible tasks
- **Step Efficiency**: optimal_steps / actual_steps
- **Token Waste**: tokens on futile attempts

### 4. Task Clustering
- **Trivial**: All configs should solve (baseline)
- **Discriminative**: Good for A/B testing
- **Challenging**: Focus for breakthrough improvements

### 5. Prompt Analysis
- All prompt components hashed (MD5)
- Hash→text mappings in `analysis/data/hashes.dict`
- Enables tracking individual guideline impact

## Implementation Phases

### Phase 1: Foundation (20h) ✅ Priority
1. **JSON Config System** (12h)
   - Config loader with validation
   - CLI parameter override
   - Backwards compatibility

2. **Basic Statistics** (5h)
   - Success rate, token usage
   - Simple aggregations
   - CSV export

3. **SPRT Calculator** (3h)
   - Manual significance testing
   - Sample size estimation

### Phase 2: Automation (14h)
1. **Experiment Runner** (6h)
   ```bash
   run_experiment.py \
     --control configs/baseline.json \
     --test configs/exp_042.json \
     --method SPRT
   ```

2. **Auto-stopping SPRT** (8h)
   - Real-time monitoring
   - Automatic session termination
   - Result persistence

### Phase 3: Intelligence (25h)
1. **Pattern Mining** (15h)
   - Error clustering
   - Systematic issue detection
   - Anomaly identification

2. **LLM-Assisted Analysis** (10h)
   - On-demand deep analysis
   - Guideline suggestions
   - Root cause analysis

## Key Design Patterns

### 1. Pareto Optimization
Instead of single metric optimization, find Pareto-optimal configurations:
- X-axis: Cost (tokens × price)
- Y-axis: Success rate
- Output: Non-dominated solution set

### 2. Filter Chaining
```python
chain = FilterChain()
  .add(SessionFilter(index=slice(-100, None)))
  .add(SessionFilter(match={"model": "gpt-4o"}))
  .add(SessionFilter(task_filter={"code": "gpu_race"}))
```

### 3. Hypothesis Testing Workflow
```python
hypothesis = {
    "id": "h_2024_01",
    "description": "Early termination rule",
    "guideline": "Check coupon limits first",
    "metric": "early_termination_rate",
    "method": "SPRT",
    "expected_improvement": 0.15
}
```

## Success Metrics

### System KPIs
- **Experiment Velocity**: >5 hypotheses tested/week
- **Decision Speed**: SPRT reduces sessions by 30-50%
- **Cost Efficiency**: Find configs with 80% success at 30% cost

### Process KPIs
- **Autonomy Rate**: >80% decisions without escalation
- **Pivot Frequency**: <2 critical changes/week
- **Blocking Time**: <10% waiting for decisions

## Risk Mitigation

1. **Data Loss**: All sessions logged to JSON with retry logic
2. **Parallel Conflicts**: File locking for concurrent writes
3. **Statistical Errors**: Conservative SPRT bounds (α=0.05, β=0.10)
4. **Scope Creep**: Phased implementation with clear boundaries

## Future Extensions

- **Multi-agent Comparison**: Compare different agent architectures
- **Auto-guideline Generation**: GPT suggests new rules from patterns
- **Real-time Dashboard**: Live experiment monitoring
- **Cost Prediction**: Estimate token usage before running

## Dependencies

- Python 3.11+
- Pydantic 2.0 (config validation)
- NumPy/SciPy (statistical tests)
- OpenAI API (LLM analysis when requested)

## Project Timeline

- **Week 1**: Phase 1 (Foundation)
- **Week 2-3**: Phase 2 (Automation)
- **Week 4+**: Phase 3 (Intelligence)

## Notes

- Start simple, iterate based on real usage
- Every decision should be data-driven
- Maintain backward compatibility when possible
- Document all experimental results for learning
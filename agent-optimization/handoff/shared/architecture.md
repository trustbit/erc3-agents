# System Architecture Overview

## Context

Optimizing LLM agents for the ERC3 benchmark, starting with SGR Store Agent.

## High-Level Architecture

```
┌─────────────────────────────────────────────┐
│             User Interface                   │
│         (CLI / Scripts / Notebooks)          │
└────────────┬────────────────────────┬────────┘
             │                        │
    ┌────────▼────────┐      ┌───────▼────────┐
    │  Experiment     │      │   Analysis     │
    │   Runner        │      │   Engine       │
    │                 │      │                │
    │ - Config loader │      │ - Filters      │
    │ - SPRT monitor  │      │ - Aggregators  │
    │ - Orchestrator  │      │ - Comparators  │
    └────────┬────────┘      └───────┬────────┘
             │                        │
    ┌────────▼────────────────────────▼────────┐
    │           Data Layer                     │
    │                                          │
    │  - sessions_history.json                │
    │  - experiment_configs/                  │
    │  - analysis_cache/                      │
    └──────────────────────────────────────────┘
```

## Core Modules

### 1. Configuration System
- **Purpose**: Manage experiment configurations
- **Technology**: JSON with Pydantic validation
- **Key Features**:
  - Parameter inheritance
  - Runtime override
  - Version tracking

### 2. Statistical Analysis
- **Purpose**: Evaluate experiment results
- **Methods**:
  - SPRT for early stopping
  - Pareto optimization for multi-objective
  - Pattern detection for insights

### 3. Filter System
- **Purpose**: Flexible data selection
- **Capabilities**:
  - Index-based slicing
  - Key-value matching
  - Complex conditions with operators
  - Chainable filters

## Data Structures

### Session Record
```python
{
    "session_id": str,
    "experiment_id": str,  # Links to experiment
    "config": dict,        # Full configuration
    "session_score": float,
    "session_tasks_quantity": int,
    "token_statistics": {
        "prompt": int,
        "completion": int,
        "total": int
    },
    "session_log": dict    # Parsed log with tasks
}
```

### Experiment Definition
```python
{
    "experiment_id": str,
    "hypothesis": str,
    "control_config": str,  # Path to control config
    "test_config": str,     # Path to test config
    "metric": str,
    "method": "SPRT",
    "status": "running|completed|aborted"
}
```

## Key Design Decisions

1. **File-based storage** for simplicity and debugging
2. **Stateless analysis** - can rerun on historical data
3. **Modular architecture** - easy to extend/replace components
4. **Config as code** - all experiments reproducible

## Integration Points

### With SGR Agent
- Reads: `sessions_history.json`
- Reads: `logs/session.log`
- Writes: experiment configs to `experiments/`

### With Analysis Tools
- Standard pandas DataFrame output
- JSON export for web tools
- CSV for spreadsheet analysis

## Performance Considerations

- Sessions file may grow large (>10MB)
- Use streaming/chunking for large datasets
- Cache computed metrics
- Index by experiment_id for fast lookup

## Security & Safety

- No credential storage in configs
- File locking for concurrent access
- Validation before any destructive operations
- Audit trail in decisions_log.md

## Future Extensions

- Database backend (PostgreSQL/SQLite)
- Real-time streaming analysis
- Web dashboard
- Auto-generated hypotheses from patterns
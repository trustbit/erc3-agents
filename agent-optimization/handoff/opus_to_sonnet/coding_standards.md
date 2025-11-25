# Coding Standards for Agent Optimization Project

## Python Version and Style

### Core Requirements
- **Python 3.11+** (use newer features where appropriate)
- **Consistent formatting** (4 spaces indentation, line length ~100)
- **Type hints** required for all function signatures
- **Docstrings** for all public functions and classes

### Code Formatting
- Use 4 spaces for indentation (no tabs)
- Keep lines reasonably short (~100 characters)
- Follow PEP 8 style guide
- Ensure consistent style within each file

## Project Structure

```
agent-optimization/
├── config/                 # Configuration management
│   ├── __init__.py
│   ├── loader.py          # Config loading logic
│   ├── schema.py          # Pydantic models
│   └── validator.py       # Validation logic
├── analysis/
│   ├── core/              # Core analysis tools
│   │   ├── filters.py
│   │   └── aggregators.py
│   ├── sprt.py           # Statistical testing
│   └── enhanced_parser.py # Session parsing
├── cli/                   # Command-line interface
├── experiment_runner.py   # Main experiment orchestration
└── task_manager.py        # Task management utilities

tests/                     # Mirror source structure
├── test_config/
│   ├── test_loader.py
│   └── test_schema.py
└── test_analysis/
    └── test_sprt.py

examples/                  # Working examples
├── configs/              # Example configurations
├── run_experiment.py     # Example experiment
└── filter_demo.py        # Filter usage demo

handoff/                   # Model communication
├── opus_to_sonnet/       # Opus → Sonnet (tasks, standards)
│   ├── START_HERE.md     # Sonnet onboarding
│   ├── current_task.json # Active task specification
│   ├── coding_standards.md
│   └── escalation_rules.md
├── sonnet_to_opus/       # Sonnet → Opus (reports)
│   └── (empty - will contain implementation_log.md, escalation.json)
├── shared/               # Common information
│   ├── architecture.md  # System design
│   └── decisions_log.md # Architecture decisions
└── user_to_opus/         # User → Opus (instructions)
    ├── START_PROJECT.md  # Opus onboarding
    ├── REVIEW_WORKFLOW.md # Review process
    └── review_template.md # Review checklist

docs/                      # Project documentation
├── PROJECT.md            # Project overview
└── COLLABORATION.md      # Role definitions

.claude/commands/         # Workflow automation slash commands
├── wf-agent-status.md   # Check agent states
├── wf-coder-refresh.md  # Refresh Sonnet instructions
├── wf-arch-refresh.md   # Refresh Opus instructions
└── ...                  # Other wf-* commands
```

## Naming Conventions

### Files and Modules
- **snake_case** for files: `experiment_runner.py`
- **Descriptive names**: `sprt.py` not `s.py`
- **Test files**: `test_[module_name].py`

### Classes and Functions
```python
# Classes: PascalCase
class SessionFilter:
    pass

class SPRTAnalyzer:
    pass

# Functions: snake_case
def load_config(path: str) -> dict:
    pass

def calculate_success_rate(sessions: List[dict]) -> float:
    pass

# Constants: UPPER_SNAKE_CASE
DEFAULT_ALPHA = 0.05
MAX_SESSIONS = 1000

# Private functions: leading underscore
def _validate_path(path: str) -> bool:
    pass
```

## Type Hints

### Required for All Functions
```python
# Good - fully typed
def parse_sessions(
    sessions: List[Dict[str, Any]],
    filters: Optional[List[SessionFilter]] = None
) -> Tuple[List[dict], dict]:
    """Parse sessions with optional filtering.

    Args:
        sessions: Raw session dictionaries
        filters: Optional list of filters to apply

    Returns:
        Tuple of (filtered_sessions, statistics)
    """
    pass

# Bad - missing type hints
def parse_sessions(sessions, filters=None):
    pass
```

### Common Type Imports
```python
from typing import (
    Any, Dict, List, Optional, Tuple, Union,
    Callable, TypedDict, Literal, cast
)
from pathlib import Path
import numpy.typing as npt  # for NumPy arrays
```

## Error Handling

### Custom Exceptions
```python
# Define domain-specific exceptions
class ConfigError(Exception):
    """Configuration-related errors"""
    pass

class ValidationError(ConfigError):
    """Config validation failed"""
    pass

class InheritanceError(ConfigError):
    """Config inheritance issue"""
    pass
```

### Error Messages
```python
# Good - informative error
raise ConfigError(
    f"Config file not found: {path}\n"
    f"Searched locations:\n"
    f"  - {Path.cwd() / path}\n"
    f"  - {default_config_dir / path}"
)

# Bad - vague error
raise ConfigError("File not found")
```

## Documentation

### Module Docstrings
```python
"""
Session filtering and analysis tools.

This module provides flexible filtering for session data with support for:
- Index-based slicing
- Key-value matching
- Complex conditional filters
- Filter chaining

Example:
    >>> from analysis.core.filters import SessionFilter, FilterChain
    >>> filter = SessionFilter(match={"status": "completed"})
    >>> results = filter.apply(sessions)
"""
```

### Function Docstrings
```python
def calculate_sprt(
    control_data: List[float],
    test_data: List[float],
    alpha: float = 0.05,
    beta: float = 0.10
) -> SPRTResult:
    """
    Calculate Sequential Probability Ratio Test.

    Performs SPRT analysis on control vs test data to determine if there's
    a significant difference with early stopping capability.

    Args:
        control_data: Success rates from control group
        test_data: Success rates from test group
        alpha: Type I error rate (false positive)
        beta: Type II error rate (false negative)

    Returns:
        SPRTResult with decision and statistics

    Raises:
        ValueError: If data is empty or parameters invalid

    Example:
        >>> result = calculate_sprt([0.8, 0.7], [0.9, 0.95])
        >>> print(result.decision)  # 'accept_h1'
    """
```

## Testing Requirements

### Test Structure
```python
import pytest
from pathlib import Path

class TestConfigLoader:
    """Test configuration loading functionality."""

    @pytest.fixture
    def sample_config(self, tmp_path):
        """Create sample config for testing."""
        config = {"model_id": "gpt-4o", "guidelines": []}
        path = tmp_path / "config.json"
        path.write_text(json.dumps(config))
        return path

    def test_load_json_config(self, sample_config):
        """Test loading JSON configuration."""
        config = load_config(sample_config)
        assert config["model_id"] == "gpt-4o"

    def test_missing_file_raises(self):
        """Test that missing file raises appropriate error."""
        with pytest.raises(ConfigError, match="not found"):
            load_config("nonexistent.json")
```

### Coverage Requirements
- **Minimum 80% coverage** for all modules
- **100% coverage** for critical paths (SPRT, config loading)
- **Exclude** from coverage: CLI scripts, examples

```bash
# Run with coverage
pytest --cov=agent-optimization --cov-report=html tests/

# Check coverage meets requirements
pytest --cov=agent-optimization --cov-fail-under=80 tests/
```

## Logging

### Use Python Logging
```python
import logging

logger = logging.getLogger(__name__)

def process_sessions(sessions: List[dict]) -> dict:
    logger.info(f"Processing {len(sessions)} sessions")

    try:
        results = _analyze(sessions)
        logger.debug(f"Analysis complete: {results.keys()}")
        return results
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
```

## Performance Considerations

### Large Data Sets
```python
# Good - generator for large files
def read_sessions_lazy(path: Path):
    """Read sessions one at a time."""
    with open(path) as f:
        for line in f:
            yield json.loads(line)

# Bad - loads everything to memory
def read_sessions(path: Path):
    return json.loads(path.read_text())
```

### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(param: str) -> float:
    """Cache expensive calculations."""
    # Complex computation
    return result
```

## Git Commit Messages

### Format
```
<type>: <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Formatting, missing semicolons, etc
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **test**: Adding missing tests
- **chore**: Maintenance tasks

### Examples
```bash
# Good
git commit -m "feat: Add SPRT early stopping for experiments

Implements Sequential Probability Ratio Test to allow experiments
to stop early when statistical significance is reached.

Reduces required sessions by 30-50% on average."

# Bad
git commit -m "Updated stuff"
```

## Code Review Checklist

Before marking task complete, ensure:
- [ ] All functions have type hints
- [ ] Public functions have docstrings
- [ ] Tests achieve >80% coverage
- [ ] Code follows PEP 8 style guide
- [ ] No commented-out code
- [ ] Error messages are informative
- [ ] Performance acceptable for expected data size
- [ ] Git history is clean (no WIP commits in final)

## Import Organization

```python
# Standard library
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Third party
import numpy as np
import pytest
from pydantic import BaseModel, Field

# Local application
from agent_optimization.config import load_config
from agent_optimization.analysis.core import SessionFilter
```

## Security Notes

- **Never commit credentials** (API keys, passwords)
- **Validate all file paths** before reading/writing
- **Use Path.resolve()** to prevent directory traversal
- **Sanitize user input** used in file names or paths
- **Set appropriate file permissions** (configs readable, logs writable)
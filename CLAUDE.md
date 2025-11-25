# SGR Store Agent

## Project Overview

**ERC3** (Enterprise Reasoning Challenge 3) — benchmark platform for evaluating AI agents on business tasks.

**Store benchmark** — simulates an online store where agent must complete shopping tasks: find products, apply coupons, optimize purchases, checkout.

**SGR (Schema-Guided Reasoning)** — approach using OpenAI structured outputs to constrain agent responses to valid tool calls via Pydantic schemas.

## Architecture

```
sgr-agent-store/
├── main.py              # Entry point: starts session, iterates tasks
├── store_agent.py       # Agent loop: LLM → parse → dispatch → log
├── config.py            # AgentConfig: model, prompts, timeouts
└── tools/
    ├── __init__.py      # Exports all tools
    ├── dtos.py          # Pydantic schemas (Combo_*, TaskCompletion, etc.)
    └── wrappers.py      # Tool implementations
```

**Key flow:**
1. `main.py` starts ERC3 session, gets tasks
2. For each task: `run_agent()` in `store_agent.py`
3. Agent loop: send history to LLM → get `NextStep` with tool call → dispatch → append result → repeat
4. Exit on `TaskCompletion` with `completed=True` or timeout

## Key Concepts

| Concept | Description |
|---------|-------------|
| **NextStep** | Pydantic model that LLM must return: current_state, plan, task_completed, function (tool to call) |
| **Combo tools** | High-level wrappers that aggregate multiple API calls |
| **TaskCompletion** | Unified exit point with routing: solved/impossible/need_work |
| **History compression** | Old tool results are truncated to save tokens |

## Running

```bash
./run_session.sh          # Run full session (all tasks)
./run_task.sh <spec_id>   # Run single task
./del_compiled.sh         # Clear Python cache
```

---

# Combo Tools Design Principles

## 1. Separation of Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Combo tool (wrapper)** | Execute a chain of API calls, collect data, handle errors, return structured result |
| **Agent (LLM)** | Analyze data, consider task context, make decisions |

**Combo tool does NOT make decisions** — it only returns facts. The agent decides what's "best" based on task requirements.

---

## 2. Tool Naming

### Prefix Convention:

| Type | Prefix | Description |
|------|--------|-------------|
| API tools | `Req_*` | Direct API operations (from erc3 package or other APIs) |
| Combo tools | `Combo_*` | Our wrappers that aggregate multiple calls |

### Combo Tool Name Structure:

```
Combo_Action_Target_For_Parameters
       │       │           │
       │       │           └── input parameters
       │       └── what is being acted upon
       └── action (Test, Find, Compare, Calculate)
```

**Examples:**
- `Combo_Find_Best_Combination_For_Products_And_Coupons` — test coupons against product combinations
- `Combo_List_All_Products` — fetch all products with pagination
- `Combo_Generate_Product_Combinations` — generate valid product combos for target units

---

## 3. State Management

- **Don't try to save/restore original state** — complex and unreliable
- **Reset state to known state before starting** — guarantee clean start
- **Leave state clean/neutral on exit** — via `finally`
- **Agent adapts to environment changes** — that's its job, not the Combo tool's

---

## 4. Call Optimization

Loop structure minimizes expensive operations:

```python
for primary_param in primary_params:       # OUTER — expensive operation (reset/init)
    reset_state()
    setup(primary_param)                   # once per primary_param

    for secondary_param in secondary_params:  # INNER — cheap operation
        apply(secondary_param)             # fast, no rebuild
        read_result()
        revert(secondary_param)
```

**Principle:** expensive operations in outer loop, cheap ones in inner loop.

---

## 5. Error Handling

**Two types of errors:**

| Type | Where it occurs | Action |
|------|-----------------|--------|
| **Fatal** | Outside loops (init, reset) | Terminate, return `fatal_error` |
| **Local** | Inside loop (applying parameter) | Record in `results`, continue |

**Error structure (uses ApiError from erc3):**
```python
from erc3 import ApiError

class ErrorInfo(BaseModel):
    method: str                    # which method failed
    api_error: ApiError            # structured error from ERC3 (status, error, code)
    params: Optional[dict] = None  # parameters that caused the error
```

Agent sees errors in context of parameters and can make decisions (resource unavailable vs invalid parameter — different actions).

---

## 6. Response Format

```python
from erc3 import ApiError

class ErrorInfo(BaseModel):
    method: str
    api_error: ApiError
    params: Optional[dict] = None

class TestResult(BaseModel):
    primary_param: Any                         # outer parameter value
    secondary_param: Any                       # inner parameter value
    success: bool                              # success/failure of this combination
    data: Optional[ResponseModel] = None       # response data (if success)
    error: Optional[ErrorInfo] = None          # error data (if not success)

class Resp_Combo(BaseModel):
    success: bool                              # overall execution status
    results: Optional[List[TestResult]] = None # array of results
    fatal_error: Optional[ErrorInfo] = None    # if fatal error occurred
```

---

## 7. Agent Prompting

```
## Available Tools

### Combo tools (Combo_*)
Aggregate multiple API calls, return structured results for analysis.
Use for exploring options, testing combinations, comparing alternatives.
These tools reset state before and after execution.

### API tools (Req_*)
Direct API operations that modify or read state.
Use for final actions after you've decided what to do.

## Guidelines

1. PREFER Combo tools for exploration and comparison
2. Use Req_* tools ONLY for final actions
3. Combo tools return raw data — YOU decide what's "best" based on task
4. Errors in results are informational (resource busy, param invalid) — analyze and adapt
5. After Combo tool call, state is clean — ready for next action
```

---

## 8. Combo Tool Implementation Template

```python
from erc3 import ApiError, ApiException

def combo_tool(api, primary_params, secondary_params) -> Resp_Combo:
    results = []

    try:
        for primary in primary_params:
            # Reset/init (expensive operation)
            try:
                reset_state(api)
                setup(api, primary)
            except ApiException as e:
                return Resp_Combo(
                    success=False,
                    fatal_error=ErrorInfo(
                        method="setup",
                        api_error=e.api_error,
                        params=None
                    )
                )

            # Iterate secondary params (cheap operations)
            for secondary in secondary_params:
                try:
                    apply(api, secondary)
                    data = read_result(api)
                    revert(api, secondary)

                    results.append(TestResult(
                        primary_param=primary,
                        secondary_param=secondary,
                        success=True,
                        data=data
                    ))
                except ApiException as e:
                    results.append(TestResult(
                        primary_param=primary,
                        secondary_param=secondary,
                        success=False,
                        error=ErrorInfo(
                            method="apply",
                            api_error=e.api_error,
                            params={"primary": primary, "secondary": secondary}
                        )
                    ))
                    try:
                        revert(api, secondary)
                    except:
                        pass

    finally:
        try:
            reset_state(api)
        except:
            pass

    return Resp_Combo(success=True, results=results)
```

---

## 9. Checklist for Creating a New Combo Tool

- [ ] Name starts with `Combo_` and describes action, target, and parameters
- [ ] Tool does not make decisions — only collects data
- [ ] Expensive operations in outer loop, cheap ones in inner loop
- [ ] State is reset before start and in `finally`
- [ ] Fatal errors terminate execution
- [ ] Local errors are recorded in results with parameters
- [ ] Response contains enough information for agent to make decisions

---

## Claude Code Rules

### Working Directory
- All relative paths are resolved from agent folder (e.g., `sgr-agent-store/`)
- Shell scripts `cd` into agent folder before running Python

### Session Management
- Task logs are in `logs/tasks/*.log` — do NOT monitor, analyze only AFTER session completes
- Process stdout/stderr — DO monitor to detect errors and take action
- Do NOT analyze session until user explicitly requests it

### Syntax Checking
- After syntax check via `python -m py_compile`, run `./del_compiled.sh` (in project root) to clean up artifacts

### Agent Configuration
- Do NOT modify `system_prompt` or `system_prompt_guidelines` in `config.py`
- If prompt content seems outdated, notify user — they will update it manually

### TaskCompletion Tool
Unified tool for completing tasks with three action types:
- `TaskSolved` — basket ready, validates and performs checkout
- `TaskImpossible` — task cannot be completed, reports failure
- `NeedMoreWork` — more steps needed, returns to planning (max 3 retries)

---

## Code Organization Rules

### config.py — Data Only
**NEVER define functions in `config.py`**
- `config.py` contains ONLY the `AgentConfig` class with data fields
- All logic functions must be placed in appropriate modules (e.g., `analysis/hashes.py`, `common/`)
- Purpose: keep configuration as pure data to memorize and version easily

### analysis/ — Optional Module
**Operations that MAINTAIN analysis data MUST check `config.analysis` flag**
- The `analysis/` directory contains session analysis tools (parsers, stats, hash tracking)
- Main agent code must work independently when `analysis=False`
- **Logging to session files is always enabled** (prompt hashes, etc.) — this is part of session record
- **Maintaining auxiliary data structures** (e.g., `hashes.dict`) requires `config.analysis=True`
- Example:
  ```python
  # Always log to session
  prompt_hashes = compute_prompt_hashes(...)
  write_session_log(LOG_FILE, f"prompt_hashes:{json.dumps(prompt_hashes)}\n\n")

  # Maintain hash dictionary only if analysis enabled
  if config.analysis:
      record_prompt_hashes(prompt_hashes, ...)
  ```
- Purpose: session logs contain all data; analysis structures can be rebuilt from logs if needed

### common/ — Shared Utilities
**General-purpose tools MUST be placed in `common/` directory**
- `common/` contains utilities that can be reused across multiple agents
- Examples: file operations, retry logic, concurrent access safety
- Do NOT place agent-specific logic in `common/`
- Import from `common/` instead of duplicating code across agents
- Purpose: when multiple agents exist at the same level, they share common utilities

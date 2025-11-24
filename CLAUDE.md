# Combo Tools Design Principles for Agents

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
- `Combo_Test_Coupons_For_Item_Sets` — test coupons for item sets
- `Combo_Find_Extra_Items_To_Maximize_Discount` — find extra items for max discount
- `Combo_Test_Slots_For_Participants` — test time slots for participants
- `Combo_Find_Room_For_Meeting_Options` — find room for meeting options

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
- Agent session log (`logs/session.log`) — do NOT monitor, analyze only AFTER session completes
- Process stdout/stderr — DO monitor to detect errors and take action
- Do NOT analyze session until user explicitly requests it

### Syntax Checking
- After syntax check via `python -m py_compile`, run `./del_compiled.sh` to clean up artifacts

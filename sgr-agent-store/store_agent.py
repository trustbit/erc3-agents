import time
from typing import Annotated, List, Union, Literal, Optional

from annotated_types import MaxLen, MinLen
from pydantic import BaseModel, Field
from erc3 import store, ApiException, TaskInfo, ERC3
from openai import OpenAI, RateLimitError

from config import AgentConfig, default_config
from tools import (
    Combo_Find_Best_Coupon_For_Products,
    combo_find_best_coupon_for_products,
    Combo_Get_Product_Page_Limit,
    combo_get_product_page_limit,
    Combo_List_All_Products,
    combo_list_all_products,
    Combo_EmptyBasket,
    combo_empty_basket,
    Combo_SetBasket,
    combo_set_basket,
    Combo_CheckoutBasket,
    combo_checkout_basket,
    CheckList_Before_TaskCompletion,
    checklist_before_task_completion,
)

client = OpenAI()

class ReportTaskCompletion(BaseModel):
    tool: Literal["report_completion"]
    completed_steps_laconic: List[str]
    code: Literal["completed", "failed"]

class NextStep(BaseModel):
    current_state: str
    # we'll use only the first step, discarding all the rest.
    plan_remaining_steps_brief: Annotated[List[str], MinLen(1), MaxLen(5)] =  Field(..., description="explain your thoughts on how to accomplish - what steps to execute")
    # now let's continue the cascade and check with LLM if the task is done
    task_completed: bool
    # Routing to one of the tools to execute the first remaining step
    function: Union[
        # Combo tools (aggregate multiple API calls)
        Combo_Find_Best_Coupon_For_Products,
        Combo_Get_Product_Page_Limit,
        Combo_List_All_Products,
        Combo_EmptyBasket,
        Combo_SetBasket,
        Combo_CheckoutBasket,
        # API tools (direct operations)
        # store.Req_ListProducts,
        store.Req_ViewBasket,
        store.Req_ApplyCoupon,
        store.Req_RemoveCoupon,
        # store.Req_AddProductToBasket,
        # store.Req_RemoveItemFromBasket,
        # Task completion
        CheckList_Before_TaskCompletion,
        ReportTaskCompletion,
    ] = Field(..., description="execute first remaining step")


CLI_RED = "\x1B[31m"
CLI_GREEN = "\x1B[32m"
CLI_YELLOW = "\x1B[33m"
CLI_CLR = "\x1B[0m"

# Rate limit retry settings
MAX_RETRIES = 5
RATE_LIMIT_WAIT = 60  # seconds (TPM limit needs ~1 min to reset)

# Session-level token tracking (persists across tasks)
session_tokens = {"prompt": 0, "completion": 0, "total": 0}


def compress_history(log: list, keep_last: int = 3) -> list:
    """
    Create a compressed copy of conversation history for API calls.
    Keeps full details for last `keep_last` steps, compresses older ones.

    Returns a new list - does NOT modify the original log.

    For compressed steps, keeps only: success, error_message fields in tool responses.
    """
    import json
    import copy

    # log structure: [system, user, assistant1, tool1, assistant2, tool2, ...]
    # First 2 are system+user, then pairs of (assistant, tool)

    if len(log) <= 2:
        return log  # Only system + user, nothing to compress

    step_messages = log[2:]  # Skip system and user
    num_steps = len(step_messages) // 2

    if num_steps <= keep_last:
        return log  # Not enough steps to compress

    # Create a shallow copy of the list, deep copy only messages we'll modify
    result = log[:2]  # system + user (no changes)

    steps_to_compress = num_steps - keep_last

    for i in range(num_steps):
        assistant_idx = i * 2
        tool_idx = i * 2 + 1

        if assistant_idx < len(step_messages):
            result.append(step_messages[assistant_idx])  # assistant message unchanged

        if tool_idx < len(step_messages):
            tool_msg = step_messages[tool_idx]

            if i < steps_to_compress and tool_msg.get("role") == "tool":
                # Compress this tool message
                try:
                    content = tool_msg.get("content", "")
                    data = json.loads(content)

                    # Keep only essential fields
                    compressed = {}
                    if "success" in data:
                        compressed["success"] = data["success"]
                    if "error_message" in data:
                        # Truncate error message to 200 chars
                        err = data["error_message"]
                        compressed["error_message"] = err[:200] if len(err) > 200 else err

                    compressed_content = json.dumps(compressed) if compressed else '{"compressed": true}'

                    # Create a copy with compressed content
                    compressed_msg = copy.copy(tool_msg)
                    compressed_msg["content"] = compressed_content
                    result.append(compressed_msg)
                except (json.JSONDecodeError, TypeError):
                    # If can't parse, keep original
                    result.append(tool_msg)
            else:
                # Keep original (recent step or not a tool message)
                result.append(tool_msg)

    return result


def run_agent(
    api: ERC3,
    task: TaskInfo,
    config: Optional[AgentConfig] = None,
    log_file: str = None
):
    """
    Run the agent on a single task.

    Args:
        api: ERC3 client instance
        task: Task to solve
        config: Agent configuration (uses default_config if not provided)
        log_file: Optional path to log file
    """
    if config is None:
        config = default_config

    store_api = api.get_store_client(task)
    system_prompt = config.get_system_prompt()

    # Write task header to log file
    if log_file:
        with open(log_file, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"TASK: {task.task_id} ({task.spec_id})\n")
            f.write(f"TEXT: {task.task_text}\n")
            f.write(f"{'='*60}\n\n")

    # log will contain conversation context for the agent within task
    log = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task.task_text},
    ]

    task_started = time.time()

    # Task-level token tracking
    task_tokens = {"prompt": 0, "completion": 0, "total": 0}

    # let's limit number of reasoning steps by 50, just to be safe
    for i in range(50):
        # Check timeout
        if time.time() - task_started > config.task_timeout_sec:
            print(f"TIMEOUT: task exceeded {config.task_timeout_sec}s limit")
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"TIMEOUT: exceeded {config.task_timeout_sec}s limit\n\n")
            break
        step = f"step_{i + 1}"
        print(f"Next {step}... ", end="")

        started = time.time()

        # Create compressed history for API call (original log stays intact)
        messages_for_api = compress_history(log, config.keep_last_steps)

        # Retry loop for rate limit errors
        completion = None
        for attempt in range(MAX_RETRIES):
            try:
                completion = client.beta.chat.completions.parse(
                    model=config.model_id,
                    response_format=NextStep,
                    messages=messages_for_api,
                    max_completion_tokens=config.max_completion_tokens,
                )
                break  # Success, exit retry loop
            except RateLimitError as e:
                print(f"\n{CLI_YELLOW}RATE_LIMIT{CLI_CLR}: waiting {RATE_LIMIT_WAIT}s (attempt {attempt+1}/{MAX_RETRIES})")
                if log_file:
                    with open(log_file, "a") as f:
                        f.write(f"--- {step} RATE_LIMIT (attempt {attempt+1}/{MAX_RETRIES}) ---\n\n")
                time.sleep(RATE_LIMIT_WAIT)

        # Check if all retries exhausted
        if completion is None:
            print(f"{CLI_RED}RATE_LIMIT_EXHAUSTED{CLI_CLR}: Max retries ({MAX_RETRIES}) exceeded")
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"--- {step} RATE_LIMIT_EXHAUSTED ---\n")
                    f.write(f"Max retries ({MAX_RETRIES}) exceeded, skipping task\n\n")
            break  # Exit the step loop, move to next task

        step_duration = time.time() - started

        api.log_llm(
            task_id=task.task_id,
            model="openai/"+config.model_id, # log in OpenRouter format
            duration_sec=step_duration,
            usage=completion.usage,
        )

        # Track tokens for step, task, and session
        step_tokens = {
            "prompt": completion.usage.prompt_tokens,
            "completion": completion.usage.completion_tokens,
            "total": completion.usage.total_tokens,
        }
        task_tokens["prompt"] += step_tokens["prompt"]
        task_tokens["completion"] += step_tokens["completion"]
        task_tokens["total"] += step_tokens["total"]
        session_tokens["prompt"] += step_tokens["prompt"]
        session_tokens["completion"] += step_tokens["completion"]
        session_tokens["total"] += step_tokens["total"]

        elapsed_sec = time.time() - task_started

        job = completion.choices[0].message.parsed

        # Log agent's reasoning to file
        if log_file and job:
            with open(log_file, "a") as f:
                f.write(f"--- {step} ---\n")
                f.write(f"time: {elapsed_sec:.1f}s elapsed, step took {step_duration:.1f}s\n")
                f.write(f"tokens: step={step_tokens['total']} (completion={step_tokens['completion']}), task={task_tokens['total']}, session={session_tokens['total']}\n")
                f.write(f"current_state: {job.current_state}\n")
                f.write(f"plan: {job.plan_remaining_steps_brief}\n")
                f.write(f"task_completed: {job.task_completed}\n")
                f.write(f"function: {job.function.__class__.__name__}\n")
                f.write(f"  args: {job.function.model_dump_json()}\n")

        # if SGR wants to finish, check if checklist was called in previous step
        if isinstance(job.function, ReportTaskCompletion):
            # Check if previous step was CheckList_Before_TaskCompletion
            prev_assistant = log[-2] if len(log) >= 2 else None
            was_checklist = (
                prev_assistant and
                prev_assistant.get("tool_calls") and
                prev_assistant["tool_calls"][0]["function"]["name"] == "CheckList_Before_TaskCompletion"
            )
            if not was_checklist:
                # Reject completion - must call CheckList_Before_TaskCompletion first
                txt = '{"error": "You must call CheckList_Before_TaskCompletion before ReportTaskCompletion"}'
                print(f"{CLI_RED}BLOCKED{CLI_CLR}: Must call CheckList_Before_TaskCompletion first")
                if log_file:
                    with open(log_file, "a") as f:
                        f.write(f"  BLOCKED: Must call CheckList_Before_TaskCompletion first\n\n")
                # Add assistant message with tool_call first (like other tools)
                log.append({
                    "role": "assistant",
                    "content": job.plan_remaining_steps_brief[0],
                    "tool_calls": [{
                        "type": "function",
                        "id": step,
                        "function": {
                            "name": job.function.__class__.__name__,
                            "arguments": job.function.model_dump_json(),
                        }}]
                })
                log.append({"role": "tool", "content": txt, "tool_call_id": step})
                continue

            print(f"[blue]agent {job.function.code}[/blue]. Summary:")
            for s in job.function.completed_steps_laconic:
                print(f"- {s}")
            task_duration = time.time() - task_started
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"COMPLETED: {job.function.code}\n")
                    f.write(f"Summary: {job.function.completed_steps_laconic}\n")
                    f.write(f"Task stats: {task_duration:.1f}s, {task_tokens['total']} tokens (prompt: {task_tokens['prompt']}, completion: {task_tokens['completion']})\n")
                    f.write(f"Session stats: {session_tokens['total']} tokens total\n\n")
            break

        # print next sep for debugging
        print(job.plan_remaining_steps_brief[0], f"\n  {job.function}")

        # Let's add tool request to conversation history as if OpenAI asked for it.
        # a shorter way would be to just append `job.model_dump_json()` entirely
        log.append({
            "role": "assistant",
            "content": job.plan_remaining_steps_brief[0],
            "tool_calls": [{
                "type": "function",
                "id": step,
                "function": {
                    "name": job.function.__class__.__name__,
                    "arguments": job.function.model_dump_json(),
                }}]
        })

        # now execute the tool by dispatching command to our handler
        try:
            # Handle Combo tools and checklist separately
            if isinstance(job.function, CheckList_Before_TaskCompletion):
                result = checklist_before_task_completion(job.function)
            elif isinstance(job.function, Combo_Find_Best_Coupon_For_Products):
                result = combo_find_best_coupon_for_products(store_api, job.function)
            elif isinstance(job.function, Combo_Get_Product_Page_Limit):
                result = combo_get_product_page_limit(store_api, job.function)
            elif isinstance(job.function, Combo_List_All_Products):
                result = combo_list_all_products(store_api, job.function)
            elif isinstance(job.function, Combo_EmptyBasket):
                result = combo_empty_basket(store_api, job.function)
            elif isinstance(job.function, Combo_SetBasket):
                result = combo_set_basket(store_api, job.function)
            elif isinstance(job.function, Combo_CheckoutBasket):
                result = combo_checkout_basket(store_api, job.function)
            else:
                # Regular API tools
                result = store_api.dispatch(job.function)
            txt = result.model_dump_json(exclude_none=True, exclude_unset=True)
            print(f"{CLI_GREEN}OUT{CLI_CLR}: {txt}")
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"  result: {txt}\n\n")
        except ApiException as e:
            txt = e.detail
            print(f"{CLI_RED}ERR: {e.api_error.error}{CLI_CLR}")
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"  ERROR: {e.api_error.error}\n\n")
        except Exception as e:
            txt = f'{{"error": "{str(e)}"}}'
            print(f"{CLI_RED}ERR: {str(e)}{CLI_CLR}")
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"  ERROR: {str(e)}\n\n")

        # and now we add results back to the convesation history, so that agent
        # we'll be able to act on the results in the next reasoning step.
        log.append({"role": "tool", "content": txt, "tool_call_id": step})
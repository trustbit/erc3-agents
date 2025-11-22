import time
from typing import Annotated, List, Union, Literal

TASK_TIMEOUT_SEC = 120  # 2 minutes per task
from annotated_types import MaxLen, MinLen
from pydantic import BaseModel, Field
from erc3 import store, ApiException, TaskInfo, ERC3
from openai import OpenAI

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
        store.Req_AddProductToBasket,
        store.Req_RemoveItemFromBasket,
        # Task completion
        CheckList_Before_TaskCompletion,
        ReportTaskCompletion,
    ] = Field(..., description="execute first remaining step")

system_prompt = f"""
You are a business assistant helping customers of OnlineStore.

## Available Tools

### Combo tools (Combo_*)
Aggregate multiple API calls, return structured results for analysis.
Useful for testing combinations of items and coupons and for getting product list .

### Low-level API tools (Req_*)
Direct API operations. Use for any task.

## Guidelines

0. First, check for suitable Combo tool. Use Low-level API tools when Combo tools don't fit your needs.
1. Combo tools return raw data — YOU decide what's "best" based on task requirements.
2. Always ensure that any proposed product combination is **fully valid**:
  - it matches all required item quantities;
  - it includes only the allowed item types defined by the task.
3. To complete the purchase:
  - compare the contents of the basket with the task requirements;
  - call CheckoutBasket
4. Clearly report when tasks are done.
5. You can apply coupon codes to get discounts. Use ViewBasket to see current discount and total.
6. Only one coupon can be applied at a time. Apply a new coupon to replace the current one, or remove it explicitly.
7. If ListProducts returns non-zero "NextOffset", it means there are more products available.
8. Before each step, evaluate whether the task goal achieved? What remains to do?
"""

CLI_RED = "\x1B[31m"
CLI_GREEN = "\x1B[32m"
CLI_CLR = "\x1B[0m"

# Session-level token tracking (persists across tasks)
session_tokens = {"prompt": 0, "completion": 0, "total": 0}

def run_agent(model: str, api: ERC3, task: TaskInfo, log_file: str = None):

    store_api = api.get_store_client(task)

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
        if time.time() - task_started > TASK_TIMEOUT_SEC:
            print(f"TIMEOUT: task exceeded {TASK_TIMEOUT_SEC}s limit")
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"TIMEOUT: exceeded {TASK_TIMEOUT_SEC}s limit\n\n")
            break
        step = f"step_{i + 1}"
        print(f"Next {step}... ", end="")

        started = time.time()

        completion = client.beta.chat.completions.parse(
            model=model,
            response_format=NextStep,
            messages=log,
            max_completion_tokens=2000,
        )

        step_duration = time.time() - started

        api.log_llm(
            task_id=task.task_id,
            model="openai/"+model, # log in OpenRouter format
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
                f.write(f"tokens: step={step_tokens['total']}, task={task_tokens['total']}, session={session_tokens['total']}\n")
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
            # print to console as ascii red
            print(f"{CLI_RED}ERR: {e.api_error.error}{CLI_CLR}")
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"  ERROR: {e.api_error.error}\n\n")

        # and now we add results back to the convesation history, so that agent
        # we'll be able to act on the results in the next reasoning step.
        log.append({"role": "tool", "content": txt, "tool_call_id": step})
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
    Combo_Get_Page_Limit,
    combo_get_page_limit,
    Combo_Get_All_Products,
    combo_get_all_products,
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
    # if task is completed, model will pick ReportTaskCompletion
    function: Union[
        ReportTaskCompletion,
        # Combo tools (aggregate multiple API calls)
        Combo_Find_Best_Coupon_For_Products,
        Combo_Get_Page_Limit,
        Combo_Get_All_Products,
        # API tools (direct operations)
        store.Req_ListProducts,
        store.Req_ViewBasket,
        store.Req_ApplyCoupon,
        store.Req_RemoveCoupon,
        store.Req_AddProductToBasket,
        store.Req_RemoveItemFromBasket,
        store.Req_CheckoutBasket,
    ] = Field(..., description="execute first remaining step")

combo_rules = """
## Available Tools

### Combo tools (Combo_*)
Aggregate multiple API calls, return structured results for analysis.
Useful for testing combinations of items and coupons.
These tools clear the basket before and after execution.

### API tools (Req_*)
Direct API operations. Use for any task.

## Guidelines

1. Combo tools are useful when you need to compare multiple options (e.g., test several coupons)
2. Combo tools return raw data — YOU decide what's "best" based on task requirements
3. After Combo tool call, basket is empty — add items again if needed
4. Use Req_* tools directly when Combo tools don't fit your needs
"""

system_prompt = f"""
You are a business assistant helping customers of OnlineStore.

- Clearly report when tasks are done.
- If ListProducts returns non-zero "NextOffset", it means there are more products available.
- You can apply coupon codes to get discounts. Use ViewBasket to see current discount and total.
- Only one coupon can be applied at a time. Apply a new coupon to replace the current one, or remove it explicitly.
- After each step, evaluate whether the task goal achieved? What remains to do? 

{combo_rules}
""".format(combo_rules=combo_rules)

CLI_RED = "\x1B[31m"
CLI_GREEN = "\x1B[32m"
CLI_CLR = "\x1B[0m"

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
            max_completion_tokens=10000,
        )

        api.log_llm(
            task_id=task.task_id,
            model="openai/"+model, # log in OpenRouter format
            duration_sec=time.time() - started,
            usage=completion.usage,
        )

        job = completion.choices[0].message.parsed

        # Log agent's reasoning to file
        if log_file and job:
            with open(log_file, "a") as f:
                f.write(f"--- {step} ---\n")
                f.write(f"current_state: {job.current_state}\n")
                f.write(f"plan: {job.plan_remaining_steps_brief}\n")
                f.write(f"task_completed: {job.task_completed}\n")
                f.write(f"function: {job.function.__class__.__name__}\n")
                f.write(f"  args: {job.function.model_dump_json()}\n")

        # if SGR wants to finish, then quit loop
        if isinstance(job.function, ReportTaskCompletion):
            print(f"[blue]agent {job.function.code}[/blue]. Summary:")
            for s in job.function.completed_steps_laconic:
                print(f"- {s}")
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"COMPLETED: {job.function.code}\n")
                    f.write(f"Summary: {job.function.completed_steps_laconic}\n\n")
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
            # Handle Combo tools separately
            if isinstance(job.function, Combo_Find_Best_Coupon_For_Products):
                result = combo_find_best_coupon_for_products(store_api, job.function)
            elif isinstance(job.function, Combo_Get_Page_Limit):
                result = combo_get_page_limit(store_api, job.function)
            elif isinstance(job.function, Combo_Get_All_Products):
                result = combo_get_all_products(store_api, job.function)
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
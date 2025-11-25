"""Configuration for Store Agent"""

from typing import List, Optional
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for the store agent"""

    # Session parameters (for core.start_session)
    benchmark: str = "store"
    workspace: str = "pvv1"
    session_name: str = "SGR Store Combo-Agent"
    architecture: str = "Schema-Guided Reasoning with combo tools"

    # Model settings
    model_id: str = "gpt-4o"
    # model_id: str = "gpt-4.1-mini"
    dumb_model_id: Optional[str] = None  # Simple model for basic Q&A (defaults to model_id if not set)
    max_completion_tokens: int = 8000
    task_timeout_sec: int = 300

    # Analysis: enable prompt hash tracking and session analysis
    analysis: bool = True

    # History compression: keep full details for last N steps
    keep_last_steps: int = 3

    # Task filter: if empty, run all tasks; otherwise run only these spec_ids
    task_codes: List[str] = ["pet_store_best_coupon"]

    # Log paths (relative to agent folder, or absolute)
    session_log: str = "logs/session.log"
    sessions_history: str = "logs/sessions_history.json"
    task_log_dir: str = "logs/tasks"
    # task_codes: List[str] = ["pet_store_best_coupon", "soda_pack_optimizer", "coupon_requires_missing_product"]

    # System prompt template with {guidelines} placeholder
    system_prompt: str = """You are a business assistant helping customers of OnlineStore.

## Domain
  Coupon may get discount, may be applied to the basket
  Basket contains products and optionally a coupon
  Act of purchasing calls Checkout

## Available Tools


### Low-level API tools (Req_*)
Direct API operations. Use it for special occasions

### Combo tools (other)
Aggregate multiple API calls.

## Guidelines

{guidelines}
"""
    system_prompt_guidelines: List[str] = [
        "Basic purchase scenario: Find required products; Send them to basket; optionally Apply coupon; Compare basket and error messages with the task; If EVERYTHING meets the task: TaskCompletion.",
        "If it is possible to solve task, but something goes wrong - find the best way to redo the problematic step",
        "If it is objectively impossible to solve the task in terms of products, amounts or coupons, report it through the TaskCompletion.",
        "Follow your plan and execute the first step.",
        "First, check for suitable tools.",
        "Use List_All_Products do get products; This tool is usually able to detect page_size **automatically**.",
        "If the solution requires to check combination of products - use Generate_Product_Combinations.",
        "If the task requires optimal bundle of products with coupon - use Find_Best_Combination_For_Products_And_Coupons.",
        # "Combo tools return raw data — YOU decide what's \"best\" based on task requirements.",
        # "Always ensure that any proposed product combination is **fully valid**:\n  - it matches all required item quantities;\n  - it includes only the allowed item types defined by the task.",
        # "To complete the purchase:\n  - compare the contents of the basket with the task requirements;\n  - call CheckoutBasket",
        # "Clearly report when tasks are done.",
        # "You can apply coupon codes to get discounts. Use ViewBasket to see current discount and total.",
        # "Only one coupon can be applied at a time. Apply a new coupon to replace the current one, or remove it explicitly.",
        # "If ListProducts returns non-zero \"NextOffset\", it means there are more products available.",
        # "Before each step, evaluate whether the task goal achieved? What remains to do?",
    ]

    # Guidelines as list of strings (will be numbered automatically)


# Default configuration instance
default_config = AgentConfig()

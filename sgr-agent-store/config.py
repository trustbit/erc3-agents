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
    max_completion_tokens: int = 8000
    task_timeout_sec: int = 120

    # History compression: keep full details for last N steps
    keep_last_steps: int = 3

    # Task filter: if empty, run all tasks; otherwise run only these spec_ids
    task_codes: List[str] = []

    # System prompt template with {guidelines} placeholder
    system_prompt: str = """You are a business assistant helping customers of OnlineStore.

## Domain
  Coupon may get discount, may be applied to the basket
  Basket contains products and optionally a coupon
  Act of purchasing calls Checkout

## Available Tools

### Combo tools (Combo_*)
Aggregate multiple API calls.

### Low-level API tools (Req_*)
Direct API operations. Use it for special occasions

## Guidelines

{guidelines}
"""

    # Guidelines as list of strings (will be numbered automatically)
    system_prompt_guidelines: List[str] = [
        "Basic purchase scenario: Find required products; Send them to basket; optionally Apply coupon; Checkout; Final check; ReportTaskCompletion."
        "If there are no suitable products: Final check, ReportTaskCompletion."
        "If the task requires optimal bundle of products with coupon - use Combo_Find_Best_Coupon_For_Products."
        "First, check for suitable Combo tool. Use Low-level API tools when Combo tools don't fit your needs.",
        "**Every time**, use CheckList_Before_TaskCompletion before ReportTaskCompletion."
        # "Combo tools return raw data — YOU decide what's \"best\" based on task requirements.",
        # "Always ensure that any proposed product combination is **fully valid**:\n  - it matches all required item quantities;\n  - it includes only the allowed item types defined by the task.",
        # "To complete the purchase:\n  - compare the contents of the basket with the task requirements;\n  - call Combo_CheckoutBasket",
        # "Clearly report when tasks are done.",
        # "You can apply coupon codes to get discounts. Use ViewBasket to see current discount and total.",
        "Only one coupon can be applied at a time. Apply a new coupon to replace the current one, or remove it explicitly.",
        # "If ListProducts returns non-zero \"NextOffset\", it means there are more products available.",
        # "Before each step, evaluate whether the task goal achieved? What remains to do?",
    ]

    def get_system_prompt(self) -> str:
        """Build system prompt by replacing {guidelines} with numbered guidelines"""
        numbered_guidelines = [
            f"{i}. {line}" for i, line in enumerate(self.system_prompt_guidelines)
        ]
        guidelines_text = "\n".join(numbered_guidelines)
        return self.system_prompt.format(guidelines=guidelines_text)


# Default configuration instance
default_config = AgentConfig()

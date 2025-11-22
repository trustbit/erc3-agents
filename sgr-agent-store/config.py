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
    model_id: str = "gpt-4.1-mini"
    max_completion_tokens: int = 5000
    task_timeout_sec: int = 120

    # System prompt template with {guidelines} placeholder
    system_prompt: str = """You are a business assistant helping customers of OnlineStore.

## Available Tools

### Combo tools (Combo_*)
Aggregate multiple API calls, return structured results for analysis.
Useful for testing combinations of items and coupons and for getting product list.

### Low-level API tools (Req_*)
Direct API operations. Use for any task.

## Guidelines

{guidelines}
"""

    # Guidelines as list of strings (will be numbered automatically)
    system_prompt_guidelines: List[str] = [
        "First, check for suitable Combo tool. Use Low-level API tools when Combo tools don't fit your needs.",
        "Combo tools return raw data — YOU decide what's \"best\" based on task requirements.",
        "Always ensure that any proposed product combination is **fully valid**:\n  - it matches all required item quantities;\n  - it includes only the allowed item types defined by the task.",
        "To complete the purchase:\n  - compare the contents of the basket with the task requirements;\n  - call Combo_CheckoutBasket",
        "Clearly report when tasks are done.",
        "You can apply coupon codes to get discounts. Use ViewBasket to see current discount and total.",
        "Only one coupon can be applied at a time. Apply a new coupon to replace the current one, or remove it explicitly.",
        "If ListProducts returns non-zero \"NextOffset\", it means there are more products available.",
        "Before each step, evaluate whether the task goal achieved? What remains to do?",
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

"""Pydantic schemas for Combo tools"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from annotated_types import MaxLen

from erc3 import ApiError
from erc3.store import ProductLine, Resp_ViewBasket, ProductInfo, Resp_CheckoutBasket


class ErrorInfo(BaseModel):
    """Structured error information from API calls"""
    method: str                          # which method failed
    api_error: ApiError                  # structured error from ERC3 (status, error, code)
    params: Optional[dict] = None        # parameters that caused the error


class Combo_Find_Best_Coupon_For_Products(BaseModel):
    """
    Test each coupon against each product combination.

    Clears basket before each combination (not before each coupon).
    Returns raw basket states — agent decides what's best.

    IMPORTANT: After this tool completes, the basket is EMPTY.
    You must add products to basket again before checkout.
    """
    suitable_products: List[List[ProductLine]] = Field(
        ...,
        description="List of ALL candidate product combinations to test. Include variations with optional items mentioned in the task"
    )
    coupons: List[str] = Field(
        ...,
        description="List of coupon codes to test against each product combination"
    )
    page_limit: Optional[int] = Field(
        None,
        description="Product catalog pagination limit, if known. If not provided, will use 999 which may cause an error revealing the actual limit."
    )


class Resp_Combo_Find_Best_Coupon_For_Products(BaseModel):
    """Response from Combo_Find_Best_Coupon_For_Products"""
    success: bool                                    # overall execution status
    results: Optional[List[Resp_ViewBasket]] = None  # array of basket states for each combination
    fatal_error: Optional[ErrorInfo] = None          # if fatal error occurred


# --- Product search tools ---

class Combo_Get_Product_Page_Limit(BaseModel):
    """
    Get the page limit for ListProducts API.

    Call this first to discover the maximum allowed limit parameter.
    Returns error message like "page limit exceeded: 10 > 5" where 5 is the limit.
    """
    tool: Literal["get_page_limit"] = "get_page_limit"


class Resp_Combo_Get_Product_Page_Limit(BaseModel):
    """Response from Combo_Get_Product_Page_Limit"""
    error_message: str = Field(..., description="Error message containing the page limit, e.g. 'page limit exceeded: 999 > 5'")


class Combo_List_All_Products(BaseModel):
    """
    List ALL products from the store.

    Fetches ALL products (handles pagination automatically).
    Use this instead of manually paginating through Req_ListProducts.
    """
    page_limit: Optional[int] = Field(
        None,
        description="Product catalog pagination limit, if known"
    )


class Resp_Combo_List_All_Products(BaseModel):
    """Response from Combo_List_All_Products"""
    success: bool
    products: Optional[List[ProductInfo]] = None
    error: Optional[str] = None


# --- Basket operations ---

class Combo_EmptyBasket(BaseModel):
    """
    Clear all items from the basket and remove any applied coupon.

    Use this to start fresh before adding new items.
    """
    tool: Literal["empty_basket"] = "empty_basket"


class Resp_Combo_EmptyBasket(BaseModel):
    """Response from Combo_EmptyBasket"""
    success: bool
    items_removed: int = 0  # number of item lines removed
    coupon_removed: bool = False  # whether a coupon was removed


class Combo_SetBasket(BaseModel):
    """
    Set basket contents to match a specific basket state.

    Clears basket, adds all items from contain, and applies coupon if present.
    Use this to restore a basket state from Combo_Find_Best_Coupon_For_Products results.
    """
    contain: Resp_ViewBasket = Field(
        ...,
        description="Target basket state to set (from Combo_Find_Best_Coupon_For_Products results)"
    )


class Resp_Combo_SetBasket(BaseModel):
    """Response from Combo_SetBasket"""
    success: bool
    basket: Optional[Resp_ViewBasket] = None  # actual basket state after setting
    error: Optional[str] = None


# --- Checkout with self-control ---

class TaskConditions(BaseModel):
    """Task requirements breakdown for self-control validation"""
    what_to_buy: str = Field(
        ...,
        description="What needs to be purchased according to the task"
    )
    quantity_required: Optional[int] = Field(
        None,
        description="Exact quantity required by task, if specified"
    )
    quantity_required_min: Optional[int] = Field(
        None,
        description="Minimum quantity required by task, if specified"
    )
    quantity_required_max: Optional[int] = Field(
        None,
        description="Maximum quantity allowed by task, if specified"
    )
    mentioned_coupons: Optional[str] = Field(
        None,
        description="Coupons mentioned/offered in the task description"
    )
    additional_conditions: Optional[str] = Field(
        None,
        description="Any additional conditions from the task"
    )


class Combo_CheckoutBasket(BaseModel):
    """
    Checkout basket with self-control validation.
    Validates that basket contents match task requirements before purchase.
    """
    # Task conditions (first position - agent must analyze the task)
    task_conditions: TaskConditions = Field(
        ...,
        description="Breakdown of task requirements"
    )

    # Self-control fields (agent fills based on current basket state)
    is_required_items_purchased: bool = Field(
        ...,
        description="Are the required items purchased in the correct quantity?"
    )
    applied_coupon: Optional[str] = Field(
        None,
        description="Which coupon is currently applied to the basket"
    )
    is_coupon_condition_violated: bool = Field(
        ...,
        description="Is the coupon application condition violated? (e.g. wrong items for coupon)"
    )
    is_additional_condition_violated: bool = Field(
        ...,
        description="Are any additional task conditions violated? (e.g. 'cheapest', 'best deal' requirements)"
    )


class Resp_Combo_CheckoutBasket(BaseModel):
    """Response from Combo_CheckoutBasket"""
    success: bool
    checkout_result: Optional[Resp_CheckoutBasket] = None  # actual checkout response if success
    validation_error: Optional[str] = None  # validation error message if failed


# --- Task completion self-control ---

class CheckList_Before_TaskCompletion(BaseModel):
    """
    Self-control checklist before completing a task.

    REQUIRED: You MUST call this tool before ReportTaskCompletion.
    This validates that you've properly attempted the task.
    """
    did_you_attempt_to_solve_the_task: bool = Field(
        ...,
        description="Did you try to solve the task? (searched products, tested coupons, etc.)"
    )
    does_this_task_have_solution: bool = Field(
        ...,
        description="Can this task be completed? (products available, budget sufficient, etc.)"
    )
    was_checkout_done: bool = Field(
        ...,
        description="Did you call Combo_CheckoutBasket to complete the purchase?"
    )


class Resp_CheckList_Before_TaskCompletion(BaseModel):
    """Response from CheckList_Before_TaskCompletion validation"""
    allowed_to_complete: bool
    message: str

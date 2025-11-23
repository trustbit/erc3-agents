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


class Combo_Find_Best_Combination_For_Products_And_Coupons(BaseModel):
    """
    Test each coupon against each product combination.

    Clears basket before each combination (not before each coupon).
    Returns filtered basket states based on filter parameter.

    IMPORTANT: After this tool completes, the basket is EMPTY.
    You must add products to basket again before checkout.
    """
    suitable_products: List[List[ProductLine]] = Field(
        ...,
        description="List of ALL candidate product combinations to test. Include variations with optional items mentioned in the task"
    )
    coupons: List[str] = Field(
        ...,
        description="List of coupon codes to test against each product combination. Can be empty if no coupons available."
    )
    filter: Literal["cheapest", "max_discount", "all"] = Field(
        "all",
        description="Filter results: 'cheapest' = min total, 'max_discount' = max discount, 'all' = return all results"
    )
    # Self-control field
    all_combinations_included: bool = Field(
        ...,
        description="Did you include ALL possible product combinations?"
    )


class Resp_Combo_Find_Best_Combination_For_Products_And_Coupons(BaseModel):
    """Response from Combo_Find_Best_Combination_For_Products_And_Coupons"""
    success: bool                                    # overall execution status
    results: Optional[List[Resp_ViewBasket]] = None  # array of basket states for each combination
    error_message: Optional[str] = None              # error message if failed


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
    page_limit: int = Field(
        None,
        description="Product catalog pagination limit, if known. Otherwise set 100"
    )
    product_name_exact: Optional[str] = Field(
        None,
        description="ONLY use if you know the EXACT product name. Filters results to match this name exactly."
    )


class Resp_Combo_List_All_Products(BaseModel):
    """Response from Combo_List_All_Products"""
    success: bool
    products: Optional[List[ProductInfo]] = None
    error_message: Optional[str] = None
    hint: Optional[str] = None


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


class BasketAddLine(BaseModel):
    """Item to add to basket"""
    sku: str
    quantity: int


class Combo_SetBasket(BaseModel):
    """
    Set basket contents to specified products and coupon.
    Clears basket, adds all products, and applies coupon if provided.
    """
    products: List[BasketAddLine] = Field(
        ...,
        description="Products to add to basket"
    )
    coupon: Optional[str] = Field(
        None,
        description="Coupon code to apply (optional)"
    )


class Resp_Combo_SetBasket(BaseModel):
    """Response from Combo_SetBasket"""
    success: bool
    basket: Optional[Resp_ViewBasket] = None  # actual basket state after setting
    error_message: Optional[str] = None


# --- Checkout with self-control ---

class TaskConditions(BaseModel):
    """Task requirements breakdown for self-control validation"""
    quantity_required: Optional[int] = Field(
        None,
        description="Exact quantity required by task, if specified"
    )
    mentioned_coupons: Optional[str] = Field(
        None,
        description="Coupons mentioned/offered in the task description"
    )
    other_conditions: Optional[str] = Field(
        None,
        description="all other conditions mentioned in the task except of products, quantity, coupon"
    )


class Combo_CheckoutBasket(BaseModel):
    """
    Checkout basket with self-control validation.
    Validates that basket contents match task requirements before purchase.
    """
    # Task conditions (first position - agent must analyze the task)
    task_conditions: TaskConditions = Field(
        ...,
        description="Breakdown of task requirements: products, quantity, coupons, other conditions"
    )

    # Self-control fields (agent fills based on current basket state)
    does_this_task_have_solution: bool = Field(
        ...,
        description="Can this task be completed? If False, do NOT checkout - go to CheckList_Before_TaskCompletion instead."
    )
    is_required_items_purchased: bool = Field(
        ...,
        description="Are the required items purchased in the correct quantity?"
    )
    applied_coupon: Optional[str] = Field(
        None,
        description="Which coupon is currently applied to the basket?"
    )
    is_coupon_condition_violated: bool = Field(
        ...,
        description="Is the coupon application condition violated?"
    )
    is_additional_condition_violated: bool = Field(
        ...,
        description="Are any additional task conditions violated?"
    )


class Resp_Combo_CheckoutBasket(BaseModel):
    """Response from Combo_CheckoutBasket"""
    success: bool
    checkout_result: Optional[Resp_CheckoutBasket] = None  # actual checkout response if success
    error_message: Optional[str] = None  # validation or checkout error message if failed


# --- Task completion self-control ---

class CheckList_Before_TaskCompletion(BaseModel):
    """
    Self-control checklist before completing a task.
    """
    did_you_attempt_to_solve_the_task: bool = Field(
        ...,
        description="Did you try to solve the task?"
    )
    does_this_task_have_solution: bool = Field(
        ...,
        description="Can this task be completed?"
    )
    was_checkout_done: bool = Field(
        ...,
        description="Did you call Combo_CheckoutBasket to complete the purchase?"
    )


class Resp_CheckList_Before_TaskCompletion(BaseModel):
    """Response from CheckList_Before_TaskCompletion validation"""
    allowed_to_complete: bool
    message: str


# --- Product combination generator ---

class ProductForCombination(BaseModel):
    """Product info for combination generation"""
    sku: str = Field(..., description="Product SKU")
    available_quantity: int = Field(..., description="Available stock quantity")
    units_in_single_sku: int = Field(
        ...,
        description="Number of individual units included in a single SKU, inferred from the product name (e.g., '6-pack' = 6, '12-pack' = 12)"
    )


class Combo_Generate_Product_Combinations(BaseModel):
    """
    Generate all valid product combinations that sum to exact target units.

    Use this when task requires buying exact quantity (e.g., "buy 24 sodas")
    and products come in different pack sizes (6pk, 12pk, 24pk).

    Returns all combinations where sum of (quantity × units_in_single_sku) = total_units_target.
    Respects available_quantity limits.
    """
    products: List[ProductForCombination] = Field(
        ...,
        description="List of products with SKU, available quantity, and units per SKU"
    )
    total_units_target: int = Field(
        ...,
        description="The total number of individual units desired in the cart"
    )


class Resp_Combo_Generate_Product_Combinations(BaseModel):
    """Response from Combo_Generate_Product_Combinations"""
    success: bool
    combinations: Optional[List[List[ProductLine]]] = None  # list of valid combinations
    error_message: Optional[str] = None

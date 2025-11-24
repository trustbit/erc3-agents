"""Pydantic schemas for Combo tools"""

from typing import List, Optional, Literal, Union
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


# --- Task requirements (used in TaskCompletion) ---

class TaskConditions(BaseModel):
    """Task requirements breakdown"""
    what_to_buy: str
    quantity_requirements: Optional[int]
    coupon_requirements: Optional[str]
    other_requirements: Optional[str]


# --- Product combination generator ---

class ProductForCombination(BaseModel):
    """Product data for combination generation"""
    sku: str
    available_quantity: int
    units_in_single_sku: int = Field(
        ...,
        description="inferred from the product name (e.g., '6-pack' = 6)"
    )


class Combo_Generate_Product_Combinations(BaseModel):
    products_to_combine: List[ProductForCombination]
    total_units_target: int


class Resp_Combo_Generate_Product_Combinations(BaseModel):
    success: bool
    combinations: Optional[List[List[ProductLine]]] = None  # list of valid combinations
    error_message: Optional[str] = None


# --- New unified task completion with routing ---

class TaskSolved(BaseModel):
    kind: Literal["solved"] = "solved"

    # Checkout validation (from Combo_CheckoutBasket)
    task_conditions: TaskConditions
    are_all_required_items_purchased_with_correct_quantity: bool
    applied_coupons: Optional[str]
    is_coupon_requirement_violated: bool
    is_other_requirement_violated: bool
    solution_summary: str


class TaskImpossible(BaseModel):
    kind: Literal["impossible"] = "impossible"
    reason: str


class NeedMoreWork(BaseModel):
    kind: Literal["need_work"] = "need_work"
    what_remains_to_do: str


class TaskCompletion(BaseModel):
    """
    Final step: validate solution and complete task.

    Choose ONE action based on task status:
    - impossible: task cannot be done → report failure
    - solved: basket is ready → checkout and report success
    - need_work: more steps needed → return to planning
    """
    # Self-reflection
    did_you_attempt_to_solve_the_task: bool
    task_solution_exists_in_principle: bool

    # Routing: choose one path
    action: Union[TaskImpossible, TaskSolved, NeedMoreWork]


class Resp_TaskCompletion(BaseModel):
    completed: bool  # True if task is finished (success or failure)
    error_message: Optional[str] = None
    # success: Optional[bool] = None  # True=solved, False=failed, None=need_work
    # checkout_result: Optional[Resp_CheckoutBasket] = None
    # message: str
    # should_report: bool = False  # Signal to agent loop to exit

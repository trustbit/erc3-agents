"""Pydantic schemas for Combo tools"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from annotated_types import MaxLen

from erc3 import ApiError
from erc3.store import ProductLine, Resp_ViewBasket, ProductInfo


class ErrorInfo(BaseModel):
    """Structured error information from API calls"""
    method: str                          # which method failed
    api_error: ApiError                  # structured error from ERC3 (status, error, code)
    params: Optional[dict] = None        # parameters that caused the error


class ItemSetCouponResult(BaseModel):
    """Result for one combination of items + coupon"""
    items: List[ProductLine]             # item set that was tested
    coupon: str                          # coupon that was tested
    success: bool                        # whether this combination succeeded
    basket: Optional[Resp_ViewBasket] = None  # basket state (if success)
    error: Optional[ErrorInfo] = None    # error info (if not success)


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


class Resp_Combo_Find_Best_Coupon_For_Products(BaseModel):
    """Response from Combo_Find_Best_Coupon_For_Products"""
    success: bool                                    # overall execution status
    results: Optional[List[ItemSetCouponResult]] = None  # array of results
    fatal_error: Optional[ErrorInfo] = None          # if fatal error occurred


class BundleDealResult(BaseModel):
    """Result for one bundle deal option (target items + extra items + coupon)"""
    target_items: List[ProductLine]          # original items agent wants to buy
    extra_items: List[ProductLine]           # additional items added to enable coupon
    coupon: str                              # coupon tested
    success: bool                            # whether this combination succeeded
    basket: Optional[Resp_ViewBasket] = None # basket state (if success)
    extra_items_cost: Optional[int] = None   # cost of extra items
    net_savings: Optional[int] = None        # discount - extra_items_cost (can be negative)
    error: Optional[ErrorInfo] = None        # error info (if not success)


class Combo_Find_Extra_Items_To_Maximize_Discount(BaseModel):
    """
    Find if adding extra products enables better coupon discounts.

    Tests target items alone with each coupon, then tries adding
    combinations of extra items to see if better discounts are achievable.
    Returns raw results — agent decides what's best.
    """
    target_items: List[ProductLine]          # items agent wants to buy
    coupons: List[str]                       # coupons to test
    candidate_extras: List[ProductLine]      # potential extra items to try adding
    max_extra_combinations: int = 10         # limit combinations to avoid explosion


class Resp_Combo_Find_Extra_Items_To_Maximize_Discount(BaseModel):
    """Response from Combo_Find_Extra_Items_To_Maximize_Discount"""
    success: bool                                    # overall execution status
    baseline_results: Optional[List[ItemSetCouponResult]] = None  # target items only
    bundle_results: Optional[List[BundleDealResult]] = None       # with extra items
    fatal_error: Optional[ErrorInfo] = None          # if fatal error occurred


# --- Product search tools ---

class Combo_Get_Page_Limit(BaseModel):
    """
    Get the page limit for ListProducts API.

    Call this first to discover the maximum allowed limit parameter.
    Returns error message like "page limit exceeded: 10 > 5" where 5 is the limit.
    """
    tool: Literal["get_page_limit"] = "get_page_limit"


class Resp_Combo_Get_Page_Limit(BaseModel):
    """Response from Combo_Get_Page_Limit"""
    error_message: str = Field(..., description="Error message containing the page limit, e.g. 'page limit exceeded: 999 > 5'")


class Combo_Get_All_Products(BaseModel):
    """
    Get all products from the store.

    Fetches ALL products (handles pagination automatically).
    Use this instead of manually paginating through ListProducts.
    """
    tool: Literal["get_all_products"] = "get_all_products"


class Resp_Combo_Get_All_Products(BaseModel):
    """Response from Combo_Get_All_Products"""
    success: bool
    products: Optional[List[ProductInfo]] = None
    error: Optional[str] = None

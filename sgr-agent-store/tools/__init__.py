"""Combo tools for Store API - high-level wrappers over erc3.store"""

from .dtos import (
    ErrorInfo,
    ItemSetCouponResult,
    BundleDealResult,
    Combo_Find_Best_Coupon_For_Products,
    Resp_Combo_Find_Best_Coupon_For_Products,
    Combo_Find_Extra_Items_To_Maximize_Discount,
    Resp_Combo_Find_Extra_Items_To_Maximize_Discount,
    Combo_Get_Page_Limit,
    Resp_Combo_Get_Page_Limit,
    Combo_Get_All_Products,
    Resp_Combo_Get_All_Products,
)
from .wrappers import (
    combo_find_best_coupon_for_products,
    combo_find_extra_items_to_maximize_discount,
    combo_get_page_limit,
    combo_get_all_products,
)

__all__ = [
    "ErrorInfo",
    "ItemSetCouponResult",
    "BundleDealResult",
    "Combo_Find_Best_Coupon_For_Products",
    "Resp_Combo_Find_Best_Coupon_For_Products",
    "Combo_Find_Extra_Items_To_Maximize_Discount",
    "Resp_Combo_Find_Extra_Items_To_Maximize_Discount",
    "Combo_Get_Page_Limit",
    "Resp_Combo_Get_Page_Limit",
    "Combo_Get_All_Products",
    "Resp_Combo_Get_All_Products",
    "combo_find_best_coupon_for_products",
    "combo_find_extra_items_to_maximize_discount",
    "combo_get_page_limit",
    "combo_get_all_products",
]

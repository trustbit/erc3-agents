"""Combo tools for Store API - high-level wrappers over erc3.store"""

from .dtos import (
    ErrorInfo,
    ItemSetCouponResult,
    Combo_Find_Best_Coupon_For_Products,
    Resp_Combo_Find_Best_Coupon_For_Products,
    Combo_Get_Page_Limit,
    Resp_Combo_Get_Page_Limit,
    Combo_Get_All_Products,
    Resp_Combo_Get_All_Products,
    TaskCompletionCheckList,
    Resp_TaskCompletionCheckList,
)
from .wrappers import (
    combo_find_best_coupon_for_products,
    combo_get_page_limit,
    combo_get_all_products,
    validate_task_completion_checklist,
)

__all__ = [
    "ErrorInfo",
    "ItemSetCouponResult",
    "Combo_Find_Best_Coupon_For_Products",
    "Resp_Combo_Find_Best_Coupon_For_Products",
    "Combo_Get_Page_Limit",
    "Resp_Combo_Get_Page_Limit",
    "Combo_Get_All_Products",
    "Resp_Combo_Get_All_Products",
    "TaskCompletionCheckList",
    "Resp_TaskCompletionCheckList",
    "combo_find_best_coupon_for_products",
    "combo_get_page_limit",
    "combo_get_all_products",
    "validate_task_completion_checklist",
]

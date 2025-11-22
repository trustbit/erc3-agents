"""Combo tool implementations - wrappers over erc3.store API"""

import re
from typing import List

from erc3 import ApiException
from erc3.store import (
    StoreClient,
    ProductLine,
    ProductInfo,
    Req_AddProductToBasket,
    Req_RemoveItemFromBasket,
    Req_ApplyCoupon,
    Req_RemoveCoupon,
    Req_ViewBasket,
    Req_ListProducts,
)

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


def clear_basket(api: StoreClient) -> None:
    """Clear all items from the basket"""
    basket = api.dispatch(Req_ViewBasket())
    if basket.items:
        for item in basket.items:
            api.dispatch(Req_RemoveItemFromBasket(sku=item.sku, quantity=item.quantity))
    # Also remove any applied coupon
    if basket.coupon:
        api.dispatch(Req_RemoveCoupon())


def combo_find_best_coupon_for_products(
    api: StoreClient,
    req: Combo_Find_Best_Coupon_For_Products
) -> Resp_Combo_Find_Best_Coupon_For_Products:
    """
    Test each coupon against each item set.

    Clears basket before each item set (not before each coupon).
    Returns raw basket states — agent decides what's best.
    Basket is guaranteed to be empty after execution.
    """
    results: List[ItemSetCouponResult] = []

    try:
        for item_set in req.suitable_products:  # OUTER loop — product combinations (expensive: clear + add)
            # 1. Clear basket
            try:
                clear_basket(api)
            except ApiException as e:
                return Resp_Combo_Find_Best_Coupon_For_Products(
                    success=False,
                    fatal_error=ErrorInfo(
                        method="clear_basket",
                        api_error=e.api_error,
                        params=None
                    )
                )

            # 2. Add items to basket
            items_added = True
            for item in item_set:
                try:
                    api.dispatch(Req_AddProductToBasket(sku=item.sku, quantity=item.quantity))
                except ApiException as e:
                    items_added = False
                    # Record error for ALL coupons for this item set
                    for coupon in req.coupons:
                        results.append(ItemSetCouponResult(
                            items=item_set,
                            coupon=coupon,
                            success=False,
                            error=ErrorInfo(
                                method="Req_AddProductToBasket",
                                api_error=e.api_error,
                                params={
                                    "failed_item": {"sku": item.sku, "quantity": item.quantity},
                                    "item_set": [{"sku": i.sku, "quantity": i.quantity} for i in item_set]
                                }
                            )
                        ))
                    break  # stop adding items for this set

            if not items_added:
                continue  # move to next item set

            # 3. Test each coupon (INNER loop — cheap: apply/remove coupon)
            for coupon in req.coupons:
                try:
                    api.dispatch(Req_ApplyCoupon(coupon=coupon))
                    basket = api.dispatch(Req_ViewBasket())
                    api.dispatch(Req_RemoveCoupon())

                    results.append(ItemSetCouponResult(
                        items=item_set,
                        coupon=coupon,
                        success=True,
                        basket=basket
                    ))
                except ApiException as e:
                    results.append(ItemSetCouponResult(
                        items=item_set,
                        coupon=coupon,
                        success=False,
                        error=ErrorInfo(
                            method="Req_ApplyCoupon",
                            api_error=e.api_error,
                            params={
                                "coupon": coupon,
                                "item_set": [{"sku": i.sku, "quantity": i.quantity} for i in item_set]
                            }
                        )
                    ))
                    # Try to remove coupon in case it was partially applied
                    try:
                        api.dispatch(Req_RemoveCoupon())
                    except:
                        pass

    finally:
        # 4. ALWAYS clear basket on exit
        try:
            clear_basket(api)
        except:
            pass

    return Resp_Combo_Find_Best_Coupon_For_Products(
        success=True,
        results=results
    )


def combo_get_page_limit(
    api: StoreClient,
    req: Combo_Get_Page_Limit
) -> Resp_Combo_Get_Page_Limit:
    """
    Discover the page limit by requesting with limit=999.
    Returns the error message containing the actual limit.
    """
    try:
        api.dispatch(Req_ListProducts(offset=0, limit=999))
        # If no error, return a message indicating no limit
        return Resp_Combo_Get_Page_Limit(error_message="no limit detected")
    except ApiException as e:
        return Resp_Combo_Get_Page_Limit(error_message=e.api_error.error)


def combo_get_all_products(
    api: StoreClient,
    req: Combo_Get_All_Products
) -> Resp_Combo_Get_All_Products:
    """
    Fetch all products from the store.
    Handles pagination automatically.
    """
    # First, discover the page limit
    try:
        api.dispatch(Req_ListProducts(offset=0, limit=999))
        page_limit = 100  # fallback if no error
    except ApiException as e:
        # Parse limit from error like "page limit exceeded: 999 > 5"
        match = re.search(r'> (\d+)', e.api_error.error)
        if match:
            page_limit = int(match.group(1))
        else:
            return Resp_Combo_Get_All_Products(
                success=False,
                error=f"Could not parse page limit from: {e.api_error.error}"
            )

    products: List[ProductInfo] = []
    offset = 0

    while True:
        try:
            resp = api.dispatch(Req_ListProducts(offset=offset, limit=page_limit))
            products.extend(resp.products)

            if resp.next_offset < 0:
                break
            offset = resp.next_offset

        except ApiException as e:
            return Resp_Combo_Get_All_Products(
                success=False,
                error=f"Failed to list products: {e.api_error.error}"
            )

    return Resp_Combo_Get_All_Products(
        success=True,
        products=products
    )


def validate_task_completion_checklist(
    req: TaskCompletionCheckList
) -> Resp_TaskCompletionCheckList:
    """
    Validate that agent has properly attempted the task before completing.

    Logic:
    - If task has no solution AND agent attempted it -> allowed to complete (as "failed")
    - If task has solution AND checkout was done -> allowed to complete (as "completed")
    - If task has solution BUT no checkout -> NOT allowed, must do checkout first
    - If agent didn't attempt at all -> NOT allowed, must try first
    """

    # Case 1: Agent didn't even try
    if not req.did_you_attempt_to_solve_the_task:
        return Resp_TaskCompletionCheckList(
            allowed_to_complete=False,
            message="You must attempt to solve the task first. Search for products, check availability, test coupons if needed."
        )

    # Case 2: Task has no solution (impossible to complete)
    if not req.does_this_task_have_solution:
        return Resp_TaskCompletionCheckList(
            allowed_to_complete=True,
            message="Task cannot be completed (no solution). You may report as 'failed' with explanation."
        )

    # Case 3: Task has solution but checkout not done
    if not req.was_checkout_done:
        return Resp_TaskCompletionCheckList(
            allowed_to_complete=False,
            message="Task has a solution but you haven't completed the purchase. Add items to basket, apply coupon if needed, and call CheckoutBasket."
        )

    # Case 4: All good - task has solution and checkout was done
    return Resp_TaskCompletionCheckList(
        allowed_to_complete=True,
        message="Checkout completed. You may report the task as 'completed'."
    )

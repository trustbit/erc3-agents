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


def combo_find_extra_items_to_maximize_discount(
    api: StoreClient,
    req: Combo_Find_Extra_Items_To_Maximize_Discount
) -> Resp_Combo_Find_Extra_Items_To_Maximize_Discount:
    """
    Find if adding extra products enables better coupon discounts.

    First tests target items alone with each coupon (baseline),
    then tries adding combinations of extra items.
    Returns raw results — agent decides what's best.
    Basket is guaranteed to be empty after execution.
    """
    baseline_results: List[ItemSetCouponResult] = []
    bundle_results: List[BundleDealResult] = []

    try:
        # 1. Test baseline (target items only)
        try:
            clear_basket(api)
        except ApiException as e:
            return Resp_Combo_Find_Extra_Items_To_Maximize_Discount(
                success=False,
                fatal_error=ErrorInfo(
                    method="clear_basket",
                    api_error=e.api_error,
                    params=None
                )
            )

        # Add target items
        target_added = True
        for item in req.target_items:
            try:
                api.dispatch(Req_AddProductToBasket(sku=item.sku, quantity=item.quantity))
            except ApiException as e:
                target_added = False
                # Record error for all coupons
                for coupon in req.coupons:
                    baseline_results.append(ItemSetCouponResult(
                        items=req.target_items,
                        coupon=coupon,
                        success=False,
                        error=ErrorInfo(
                            method="Req_AddProductToBasket",
                            api_error=e.api_error,
                            params={"failed_item": {"sku": item.sku, "quantity": item.quantity}}
                        )
                    ))
                break

        # Test each coupon on baseline
        if target_added:
            baseline_basket_no_coupon = api.dispatch(Req_ViewBasket())
            baseline_subtotal = baseline_basket_no_coupon.subtotal

            for coupon in req.coupons:
                try:
                    api.dispatch(Req_ApplyCoupon(coupon=coupon))
                    basket = api.dispatch(Req_ViewBasket())
                    api.dispatch(Req_RemoveCoupon())

                    baseline_results.append(ItemSetCouponResult(
                        items=req.target_items,
                        coupon=coupon,
                        success=True,
                        basket=basket
                    ))
                except ApiException as e:
                    baseline_results.append(ItemSetCouponResult(
                        items=req.target_items,
                        coupon=coupon,
                        success=False,
                        error=ErrorInfo(
                            method="Req_ApplyCoupon",
                            api_error=e.api_error,
                            params={"coupon": coupon}
                        )
                    ))
                    try:
                        api.dispatch(Req_RemoveCoupon())
                    except:
                        pass

        # 2. Test with extra items (limited combinations)
        combinations_tested = 0
        for extra_item in req.candidate_extras:
            if combinations_tested >= req.max_extra_combinations:
                break

            # Clear and rebuild basket with target + extra
            try:
                clear_basket(api)
            except ApiException:
                continue

            # Add target items
            items_ok = True
            for item in req.target_items:
                try:
                    api.dispatch(Req_AddProductToBasket(sku=item.sku, quantity=item.quantity))
                except ApiException:
                    items_ok = False
                    break

            if not items_ok:
                continue

            # Add extra item
            try:
                api.dispatch(Req_AddProductToBasket(sku=extra_item.sku, quantity=extra_item.quantity))
            except ApiException as e:
                # Record error for all coupons with this extra
                for coupon in req.coupons:
                    bundle_results.append(BundleDealResult(
                        target_items=req.target_items,
                        extra_items=[extra_item],
                        coupon=coupon,
                        success=False,
                        error=ErrorInfo(
                            method="Req_AddProductToBasket",
                            api_error=e.api_error,
                            params={"extra_item": {"sku": extra_item.sku, "quantity": extra_item.quantity}}
                        )
                    ))
                continue

            # Get basket state to calculate extra item cost
            basket_with_extra = api.dispatch(Req_ViewBasket())
            extra_items_cost = basket_with_extra.subtotal - baseline_subtotal if target_added else 0

            # Test each coupon with this extra item
            for coupon in req.coupons:
                combinations_tested += 1
                try:
                    api.dispatch(Req_ApplyCoupon(coupon=coupon))
                    basket = api.dispatch(Req_ViewBasket())
                    api.dispatch(Req_RemoveCoupon())

                    # Calculate net savings: discount minus extra item cost
                    discount = basket.discount or 0
                    net_savings = discount - extra_items_cost

                    bundle_results.append(BundleDealResult(
                        target_items=req.target_items,
                        extra_items=[extra_item],
                        coupon=coupon,
                        success=True,
                        basket=basket,
                        extra_items_cost=extra_items_cost,
                        net_savings=net_savings
                    ))
                except ApiException as e:
                    bundle_results.append(BundleDealResult(
                        target_items=req.target_items,
                        extra_items=[extra_item],
                        coupon=coupon,
                        success=False,
                        error=ErrorInfo(
                            method="Req_ApplyCoupon",
                            api_error=e.api_error,
                            params={"coupon": coupon, "extra_item": {"sku": extra_item.sku, "quantity": extra_item.quantity}}
                        )
                    ))
                    try:
                        api.dispatch(Req_RemoveCoupon())
                    except:
                        pass

    finally:
        # ALWAYS clear basket on exit
        try:
            clear_basket(api)
        except:
            pass

    return Resp_Combo_Find_Extra_Items_To_Maximize_Discount(
        success=True,
        baseline_results=baseline_results,
        bundle_results=bundle_results
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

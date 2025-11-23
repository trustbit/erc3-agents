"""Combo tool implementations - wrappers over erc3.store API"""

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
    Resp_ViewBasket,
    Req_ListProducts,
    Req_CheckoutBasket,
)

from .dtos import (
    Combo_Find_Best_Coupon_For_Products,
    Resp_Combo_Find_Best_Coupon_For_Products,
    Combo_Get_Product_Page_Limit,
    Resp_Combo_Get_Product_Page_Limit,
    Combo_List_All_Products,
    Resp_Combo_List_All_Products,
    Combo_EmptyBasket,
    Resp_Combo_EmptyBasket,
    Combo_SetBasket,
    Resp_Combo_SetBasket,
    Combo_CheckoutBasket,
    Resp_Combo_CheckoutBasket,
    CheckList_Before_TaskCompletion,
    Resp_CheckList_Before_TaskCompletion,
)


def clear_basket(api: StoreClient) -> tuple[int, bool]:
    """Clear all items from the basket. Returns (items_removed, coupon_removed)."""
    basket = api.dispatch(Req_ViewBasket())
    items_removed = 0
    coupon_removed = False
    if basket.items:
        for item in basket.items:
            api.dispatch(Req_RemoveItemFromBasket(sku=item.sku, quantity=item.quantity))
            items_removed += 1
    # Also remove any applied coupon
    if basket.coupon:
        api.dispatch(Req_RemoveCoupon())
        coupon_removed = True
    return items_removed, coupon_removed


def combo_empty_basket(
    api: StoreClient,
    req: Combo_EmptyBasket
) -> Resp_Combo_EmptyBasket:
    """
    Clear all items from the basket and remove any applied coupon.
    """
    try:
        items_removed, coupon_removed = clear_basket(api)
        return Resp_Combo_EmptyBasket(
            success=True,
            items_removed=items_removed,
            coupon_removed=coupon_removed
        )
    except ApiException:
        return Resp_Combo_EmptyBasket(success=False)


def combo_set_basket(
    api: StoreClient,
    req: Combo_SetBasket
) -> Resp_Combo_SetBasket:
    """
    Set basket contents to specified products and coupon.
    Clears basket, adds all products, and applies coupon if provided.
    """
    try:
        # 1. Clear basket
        clear_basket(api)

        # 2. Add all products
        for item in req.products:
            api.dispatch(Req_AddProductToBasket(sku=item.sku, quantity=item.quantity))

        # 3. Apply coupon if provided
        if req.coupon:
            api.dispatch(Req_ApplyCoupon(coupon=req.coupon))

        # 4. Return actual basket state
        basket = api.dispatch(Req_ViewBasket())
        return Resp_Combo_SetBasket(success=True, basket=basket)

    except ApiException as e:
        return Resp_Combo_SetBasket(success=False, error_message=e.api_error.error)


def combo_find_best_coupon_for_products(
    api: StoreClient,
    req: Combo_Find_Best_Coupon_For_Products
) -> Resp_Combo_Find_Best_Coupon_For_Products:
    """
    Test each coupon against each item set.

    Clears basket before each item set (not before each coupon).
    Returns array of basket states — agent decides what's best.
    Basket is guaranteed to be empty after execution.
    """
    # Self-control validation
    if not req.all_combinations_included:
        return Resp_Combo_Find_Best_Coupon_For_Products(
            success=False,
            error_message="You indicated that not all product combinations are included. Please add ALL possible combinations before calling this tool."
        )

    results: List[Resp_ViewBasket] = []

    try:
        for item_set in req.suitable_products:  # OUTER loop — product combinations (expensive: clear + add)
            # 1. Clear basket
            try:
                clear_basket(api)
            except ApiException as e:
                return Resp_Combo_Find_Best_Coupon_For_Products(
                    success=False,
                    error_message=f"clear_basket failed: {e.api_error.error}"
                )

            # 2. Add items to basket
            items_added = True
            for item in item_set:
                try:
                    api.dispatch(Req_AddProductToBasket(sku=item.sku, quantity=item.quantity))
                except ApiException as e:
                    items_added = False
                    break  # stop adding items for this set

            if not items_added:
                continue  # move to next item set

            # 3. Test each coupon (INNER loop — cheap: apply/remove coupon)
            for coupon in req.coupons:
                try:
                    api.dispatch(Req_ApplyCoupon(coupon=coupon))
                    basket = api.dispatch(Req_ViewBasket())
                    api.dispatch(Req_RemoveCoupon())
                    results.append(basket)
                except ApiException:
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

    # 5. Enrich results: add discount field to each basket
    for basket in results:
        if not hasattr(basket, 'discount') or basket.discount is None:
            basket.discount = basket.subtotal - basket.total

    # 6. Apply filter
    if results and req.filter != "all":
        if req.filter == "cheapest":
            min_total = min(b.total for b in results)
            results = [b for b in results if b.total == min_total]
        elif req.filter == "max_discount":
            max_discount = max(b.discount for b in results)
            results = [b for b in results if b.discount == max_discount]

    return Resp_Combo_Find_Best_Coupon_For_Products(
        success=True,
        results=results
    )


def combo_get_product_page_limit(
    api: StoreClient,
    req: Combo_Get_Product_Page_Limit
) -> Resp_Combo_Get_Product_Page_Limit:
    """
    Discover the page limit by requesting more items than allowed.
    Returns the error message containing the actual limit.
    """
    try:
        api.dispatch(Req_ListProducts(offset=0, limit=100))
        # If no error, return a message indicating no limit
        return Resp_Combo_Get_Product_Page_Limit(error_message="no limit detected")
    except ApiException as e:
        return Resp_Combo_Get_Product_Page_Limit(error_message=e.api_error.error)


def combo_list_all_products(
    api: StoreClient,
    req: Combo_List_All_Products
) -> Resp_Combo_List_All_Products:
    """
    List all products from the store.
    Handles pagination automatically.
    If page_limit is not provided, uses 100 which will trigger an error revealing the actual limit.
    """
    page_limit = req.page_limit if req.page_limit is not None else 100

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
            return Resp_Combo_List_All_Products(
                success=False,
                error_message=f"Failed to list products: {e.api_error.error}"
            )

    # Filter by exact product name if provided
    hint = None
    if req.product_name_exact:
        filtered = [p for p in products if p.name == req.product_name_exact]
        if not filtered:
            hint = f"Product '{req.product_name_exact}' not found. Call this method without product_name_exact to get the full product list."
        products = filtered

    return Resp_Combo_List_All_Products(
        success=True,
        products=products,
        hint=hint
    )


def checklist_before_task_completion(
    req: CheckList_Before_TaskCompletion
) -> Resp_CheckList_Before_TaskCompletion:
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
        return Resp_CheckList_Before_TaskCompletion(
            allowed_to_complete=False,
            message="You must attempt to solve the task first. Search for products, check availability, test coupons if needed."
        )

    # Case 2: Task has no solution (impossible to complete)
    if not req.does_this_task_have_solution:
        return Resp_CheckList_Before_TaskCompletion(
            allowed_to_complete=True,
            message="Task cannot be completed (no solution). You may report as 'failed' with explanation."
        )

    # Case 3: Task has solution but checkout not done
    if not req.was_checkout_done:
        return Resp_CheckList_Before_TaskCompletion(
            allowed_to_complete=False,
            message="Task has a solution but you haven't completed the purchase. Add items to basket, apply coupon if needed, and call Combo_CheckoutBasket."
        )

    # Case 4: All good - task has solution and checkout was done
    return Resp_CheckList_Before_TaskCompletion(
        allowed_to_complete=True,
        message="Checkout completed. You may report the task as 'completed'."
    )


def combo_checkout_basket(
    api: StoreClient,
    req: Combo_CheckoutBasket
) -> Resp_Combo_CheckoutBasket:
    """
    Validate basket contents against task requirements, then checkout if valid.

    Validation rules based on self-control fields:
    - is_required_items_purchased must be True
    - is_coupon_condition_violated must be False
    - is_additional_condition_violated must be False
    """
    # Check if task has no solution - block checkout
    if not req.does_this_task_have_solution:
        return Resp_Combo_CheckoutBasket(
            success=False,
            error_message="Task has no solution. Do NOT checkout. Go to CheckList_Before_TaskCompletion, then ReportTaskCompletion."
        )

    errors = []
    tc = req.task_conditions

    # Self-control validation: required items purchased
    if not req.is_required_items_purchased:
        errors.append(
            f"Required items not purchased: task requires '{tc.what_to_buy}' "
            f"but is_required_items_purchased=False"
        )

    # Self-control validation: coupon conditions
    if req.is_coupon_condition_violated:
        errors.append(
            f"Coupon condition violated: mentioned_coupons='{tc.mentioned_coupons}', "
            f"applied_coupon='{req.applied_coupon}'"
        )

    # Self-control validation: additional conditions
    if req.is_additional_condition_violated:
        errors.append(
            f"Additional condition violated: '{tc.additional_conditions}'"
        )

    # If validation failed, return error
    if errors:
        return Resp_Combo_CheckoutBasket(
            success=False,
            error_message=" | ".join(errors)
        )

    # Validation passed - perform actual checkout
    try:
        result = api.dispatch(Req_CheckoutBasket())
        return Resp_Combo_CheckoutBasket(
            success=True,
            checkout_result=result
        )
    except ApiException as e:
        return Resp_Combo_CheckoutBasket(
            success=False,
            error_message=f"Checkout failed: {e.api_error.error}"
        )

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
    Combo_Find_Best_Combination_For_Products_And_Coupons,
    Resp_Combo_Find_Best_Combination_For_Products_And_Coupons,
    Combo_Get_Product_Page_Limit,
    Resp_Combo_Get_Product_Page_Limit,
    Combo_List_All_Products,
    Resp_Combo_List_All_Products,
    Combo_EmptyBasket,
    Resp_Combo_EmptyBasket,
    Combo_SetBasket,
    Resp_Combo_SetBasket,
    Combo_Generate_Product_Combinations,
    Resp_Combo_Generate_Product_Combinations,
    # Task completion
    TaskCompletion,
    Resp_TaskCompletion,
    TaskSolved,
    TaskImpossible,
    NeedMoreWork,
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
            result = api.dispatch(Req_ApplyCoupon(coupon=req.coupon))
            if hasattr(result, 'error') and result.error:
                return Resp_Combo_SetBasket(success=False, error_message=result.error)

        # 4. Return actual basket state
        basket = api.dispatch(Req_ViewBasket())
        return Resp_Combo_SetBasket(success=True, basket=basket)

    except ApiException as e:
        return Resp_Combo_SetBasket(success=False, error_message=e.api_error.error)


def combo_find_best_combination_for_products_and_coupons(
    api: StoreClient,
    req: Combo_Find_Best_Combination_For_Products_And_Coupons
) -> Resp_Combo_Find_Best_Combination_For_Products_And_Coupons:
    """
    Test each coupon against each item set.

    Clears basket before each item set (not before each coupon).
    Returns array of basket states — agent decides what's best.
    Basket is guaranteed to be empty after execution.
    """
    # Self-control validation
    if not req.all_combinations_included:
        return Resp_Combo_Find_Best_Combination_For_Products_And_Coupons(
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
                return Resp_Combo_Find_Best_Combination_For_Products_And_Coupons(
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
            if req.coupons:
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
            else:
                # No coupons provided — test combination without coupon
                try:
                    basket = api.dispatch(Req_ViewBasket())
                    results.append(basket)
                except ApiException:
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

    return Resp_Combo_Find_Best_Combination_For_Products_And_Coupons(
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


def combo_generate_product_combinations(
    req: Combo_Generate_Product_Combinations
) -> Resp_Combo_Generate_Product_Combinations:
    """
    Generate all valid product combinations that sum to exact target units.

    Uses recursive backtracking to find all combinations where:
    sum(quantity[i] * units_in_single_sku[i]) == total_units_target

    Each product quantity is limited by available_quantity.
    """
    if not req.products_to_combine:
        return Resp_Combo_Generate_Product_Combinations(
            success=False,
            error_message="No products provided"
        )

    if req.total_units_target <= 0:
        return Resp_Combo_Generate_Product_Combinations(
            success=False,
            error_message="total_units_target must be positive"
        )

    combinations: List[List[ProductLine]] = []

    def backtrack(index: int, remaining: int, current: List[ProductLine]):
        """Recursive backtracking to find all valid combinations"""
        if remaining == 0:
            # Found valid combination
            combinations.append(current.copy())
            return

        if remaining < 0 or index >= len(req.products_to_combine):
            return

        product = req.products_to_combine[index]
        units = product.units_in_single_sku
        max_qty = min(product.available_quantity, remaining // units) if units > 0 else 0

        # Try each possible quantity for this product (including 0)
        for qty in range(max_qty + 1):
            if qty > 0:
                current.append(ProductLine(sku=product.sku, quantity=qty))
            backtrack(index + 1, remaining - qty * units, current)
            if qty > 0:
                current.pop()

    backtrack(0, req.total_units_target, [])

    if not combinations:
        return Resp_Combo_Generate_Product_Combinations(
            success=True,
            combinations=[],
            error_message=f"No valid combinations found for target {req.total_units_target} units"
        )

    return Resp_Combo_Generate_Product_Combinations(
        success=True,
        combinations=combinations
    )


def task_completion(
    api: StoreClient,
    req: TaskCompletion,
    history: list
) -> Resp_TaskCompletion:
    """
    Unified task completion with routing.

    Handles three branches:
    - solved: validate and checkout
    - impossible: report failure
    - need_work: check retry count, force failure if ≥3

    Args:
        api: StoreClient instance
        req: TaskCompletion request
        history: conversation history (for counting need_work retries)
    """

    # Step 1: Check if agent attempted the task
    if not req.did_you_attempt_to_solve_the_task:
        return Resp_TaskCompletion(
            completed=False,
            error_message="You must attempt to solve the task first. Prepare a plan.",
        )

    action = req.action

    # Branch: Task is impossible
    if isinstance(action, TaskImpossible):
        return Resp_TaskCompletion(completed=True)

    # Branch: Need more work
    if isinstance(action, NeedMoreWork):
        # Count previous need_work calls in history
        need_work_count = _count_need_work_in_history(history)

        if need_work_count >= 2:  # This is the 3rd call
            return Resp_TaskCompletion(
                completed=True,
                error_message=f"Exceeded 'NeedMoreWork' retry limit.",
            )

        return Resp_TaskCompletion(
            completed=False,
            error_message=f"Keep your plan",
        )

    # Branch: Task solved - validate and checkout
    if isinstance(action, TaskSolved):
        # Consistency check: task_solution_exists_in_principle should be True
        if not req.task_solution_exists_in_principle:
            return Resp_TaskCompletion(
                completed=False,
                error_message="Inconsistent: you marked task as 'solved' but set task_solution_exists_in_principle=False. Double-check yourself",
            )

        # Validate checkout conditions
        errors = []
        tc = action.task_conditions

        if not action.are_all_required_items_purchased_with_correct_quantity:
            errors.append("Required items not purchased")

        if action.is_coupon_requirement_violated:
            errors.append(f"Coupon condition violated: task mentions '{tc.coupon_requirements}', applied '{action.applied_coupons}'")

        if action.is_other_requirement_violated:
            errors.append(f"Additional condition violated: '{tc.other_requirements}'")

        if errors:
            error_msg = " | ".join(errors)
            return Resp_TaskCompletion(
                completed=False,
                error_message=f"Validation failed: {error_msg}. Fix issues or mark as impossible.",
            )

        # Validation passed - perform checkout
        try:
            checkout_result = api.dispatch(Req_CheckoutBasket())
            return Resp_TaskCompletion(
                completed=True,
            )
        except ApiException as e:
            error_msg = e.api_error.error
            return Resp_TaskCompletion(
                completed=False,
                error_message=f"Checkout failed: {error_msg}. Fix if business logic error, or mark as impossible.",
            )

    # Should not reach here
    return Resp_TaskCompletion(
        completed=False,
        error_message="Unknown action type",
    )


def _count_need_work_in_history(history: list) -> int:
    """Count how many times TaskCompletion with need_work was called."""
    import json
    count = 0
    for msg in history:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                if tc.get("function", {}).get("name") == "TaskCompletion":
                    try:
                        args = json.loads(tc["function"].get("arguments", "{}"))
                        action = args.get("action", {})
                        if action.get("kind") == "need_work":
                            count += 1
                    except (json.JSONDecodeError, KeyError):
                        pass
    return count

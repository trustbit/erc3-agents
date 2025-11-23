"""Test Combo tools on a real task"""

from dotenv import load_dotenv
load_dotenv()

from erc3 import ERC3
from erc3.store import ProductLine

from tools import (
    Combo_Find_Best_Coupon_For_Products,
    combo_find_best_coupon_for_products,
)


def main():
    # Initialize API
    core = ERC3()

    # Start a session
    res = core.start_session(
        benchmark="store",
        workspace="my",
        name="Combo Tools Test",
        architecture="Testing Combo_Test_Coupons_For_Item_Sets"
    )
    print(f"Session started: {res.session_id}")

    # Get first task (soda_pack_optimizer would be ideal)
    status = core.session_status(res.session_id)
    print(f"Session has {len(status.tasks)} tasks")

    # Find a coupon-related task
    task = None
    for t in status.tasks:
        if "coupon" in t.task_text.lower() or "soda" in t.task_text.lower():
            task = t
            break

    if not task:
        task = status.tasks[0]  # fallback to first task

    print(f"\nUsing task: {task.task_id}")
    print(f"Task text: {task.task_text}")

    # Start the task
    core.start_task(task)

    # Get store client
    store_api = core.get_store_client(task)

    # Test Combo_Test_Coupons_For_Item_Sets
    # Example: test different soda combinations with different coupons
    req = Combo_Find_Best_Coupon_For_Products(
        suitable_products=[
            # 24 sodas via 24-pack
            [ProductLine(sku="soda-24pk", quantity=1)],
            # 24 sodas via 4x 6-pack
            [ProductLine(sku="soda-6pk", quantity=4)],
            # 24 sodas via 2x 12-pack
            [ProductLine(sku="soda-12pk", quantity=2)],
            # 24 sodas via 6pk + 12pk combo
            [ProductLine(sku="soda-6pk", quantity=2), ProductLine(sku="soda-12pk", quantity=1)],
        ],
        coupons=["SALEX", "BULK24", "COMBO"]
    )

    print("\n" + "="*60)
    print("Testing Combo_Find_Best_Coupon_For_Products")
    print("="*60)

    result = combo_find_best_coupon_for_products(store_api, req)

    print(f"\nSuccess: {result.success}")

    if result.fatal_error:
        print(f"Fatal error: {result.fatal_error}")

    if result.results:
        print(f"\nResults ({len(result.results)} combinations tested):")
        for r in result.results:
            items_str = ", ".join([f"{i.sku}x{i.quantity}" for i in r.items])
            if r.success:
                basket = r.basket
                discount = basket.discount or 0
                print(f"  [{items_str}] + {r.coupon}: "
                      f"subtotal={basket.subtotal}, discount={discount}, total={basket.total}")
            else:
                print(f"  [{items_str}] + {r.coupon}: ERROR - {r.error.api_error.error}")

    # Find best option
    if result.results:
        successful = [r for r in result.results if r.success]
        if successful:
            best = min(successful, key=lambda r: r.basket.total)
            items_str = ", ".join([f"{i.sku}x{i.quantity}" for i in best.items])
            print(f"\n*** BEST OPTION: [{items_str}] + {best.coupon} = {best.basket.total} ***")

    # Complete task (without checkout, just for testing)
    core.complete_task(task)
    print(f"\nTask completed")


if __name__ == "__main__":
    main()

from __future__ import annotations

from apparel_agent.data.repository import ApparelRepository


def create_cart(repo: ApparelRepository, customer_id: str, items: list[dict]) -> dict:
    return repo.create_cart(customer_id=customer_id, items=items)


def apply_coupon(repo: ApparelRepository, cart_id: str, coupon_code: str) -> dict:
    return repo.apply_coupon(cart_id=cart_id, coupon_code=coupon_code)


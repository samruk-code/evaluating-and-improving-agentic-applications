from __future__ import annotations

from apparel_agent.data.repository import ApparelRepository


def check_inventory(
    repo: ApparelRepository,
    product_id: str,
    size: str | None = None,
    store_id: str = "STORE-001",
) -> dict:
    return repo.check_inventory(product_id=product_id, size=size, store_id=store_id)


def reserve_item(
    repo: ApparelRepository,
    customer_id: str,
    product_id: str,
    size: str,
    store_id: str = "STORE-001",
) -> dict:
    return repo.reserve_item(
        customer_id=customer_id,
        product_id=product_id,
        size=size,
        store_id=store_id,
    )


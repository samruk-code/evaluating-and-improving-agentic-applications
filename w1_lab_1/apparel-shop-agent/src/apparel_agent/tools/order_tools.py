from __future__ import annotations

from apparel_agent.data.repository import ApparelRepository


def lookup_order(repo: ApparelRepository, order_id: str, email: str) -> dict:
    return repo.lookup_order(order_id=order_id, email=email)


def get_order_tracking(repo: ApparelRepository, order_id: str) -> dict:
    return repo.get_order_tracking(order_id=order_id)


def check_return_policy(repo: ApparelRepository, order_id: str, product_id: str) -> dict:
    return repo.check_return_policy(order_id=order_id, product_id=product_id)


def create_exchange_request(
    repo: ApparelRepository, order_id: str, product_id: str, new_size: str
) -> dict:
    return repo.create_exchange_request(
        order_id=order_id, product_id=product_id, new_size=new_size
    )


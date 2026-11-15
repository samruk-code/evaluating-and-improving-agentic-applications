from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field

from apparel_agent.data.seed_data import COUPONS, INVENTORY, ORDERS, PRODUCTS


@dataclass
class StoreState:
    products: list[dict] = field(default_factory=lambda: deepcopy(PRODUCTS))
    inventory: list[dict] = field(default_factory=lambda: deepcopy(INVENTORY))
    orders: list[dict] = field(default_factory=lambda: deepcopy(ORDERS))
    coupons: dict[str, float] = field(default_factory=lambda: deepcopy(COUPONS))
    reservations: list[dict] = field(default_factory=list)
    carts: dict[str, dict] = field(default_factory=dict)
    exchange_requests: list[dict] = field(default_factory=list)
    next_cart_number: int = 1
    next_exchange_number: int = 1


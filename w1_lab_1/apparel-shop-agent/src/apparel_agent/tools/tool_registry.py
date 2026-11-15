from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from apparel_agent.data.repository import ApparelRepository
from apparel_agent.tools.cart_tools import apply_coupon, create_cart
from apparel_agent.tools.catalog_tools import get_product_details, search_catalog
from apparel_agent.tools.inventory_tools import check_inventory, reserve_item
from apparel_agent.tools.order_tools import (
    check_return_policy,
    create_exchange_request,
    get_order_tracking,
    lookup_order,
)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    func: Callable[..., dict]

    def anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


def build_tool_registry(repo: ApparelRepository) -> dict[str, ToolSpec]:
    return {
        "search_catalog": ToolSpec(
            name="search_catalog",
            description="Search apparel catalog by text query and optional filters.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "filters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "color": {"type": "string"},
                            "fabric": {"type": "string"},
                            "size": {"type": "string"},
                            "max_price": {"type": "number"},
                            "available": {"type": "boolean"},
                        },
                    },
                },
                "required": ["query"],
            },
            func=lambda **kwargs: search_catalog(repo, **kwargs),
        ),
        "get_product_details": ToolSpec(
            name="get_product_details",
            description="Get details for one product ID.",
            input_schema={
                "type": "object",
                "properties": {"product_id": {"type": "string"}},
                "required": ["product_id"],
            },
            func=lambda **kwargs: get_product_details(repo, **kwargs),
        ),
        "check_inventory": ToolSpec(
            name="check_inventory",
            description="Check store inventory for a product and size.",
            input_schema={
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "size": {"type": "string"},
                    "store_id": {"type": "string", "default": "STORE-001"},
                },
                "required": ["product_id", "size"],
            },
            func=lambda **kwargs: check_inventory(repo, **kwargs),
        ),
        "reserve_item": ToolSpec(
            name="reserve_item",
            description="Reserve one in-stock item for customer pickup.",
            input_schema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "product_id": {"type": "string"},
                    "size": {"type": "string"},
                    "store_id": {"type": "string", "default": "STORE-001"},
                },
                "required": ["customer_id", "product_id", "size"],
            },
            func=lambda **kwargs: reserve_item(repo, **kwargs),
        ),
        "create_cart": ToolSpec(
            name="create_cart",
            description="Create a cart for a customer with one or more items.",
            input_schema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string"},
                                "size": {"type": "string"},
                                "quantity": {"type": "integer", "default": 1},
                            },
                            "required": ["product_id", "size"],
                        },
                    },
                },
                "required": ["customer_id", "items"],
            },
            func=lambda **kwargs: create_cart(repo, **kwargs),
        ),
        "apply_coupon": ToolSpec(
            name="apply_coupon",
            description="Apply a coupon code to an existing cart.",
            input_schema={
                "type": "object",
                "properties": {
                    "cart_id": {"type": "string"},
                    "coupon_code": {"type": "string"},
                },
                "required": ["cart_id", "coupon_code"],
            },
            func=lambda **kwargs: apply_coupon(repo, **kwargs),
        ),
        "lookup_order": ToolSpec(
            name="lookup_order",
            description="Look up a customer order by order ID and email.",
            input_schema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "email": {"type": "string"},
                },
                "required": ["order_id", "email"],
            },
            func=lambda **kwargs: lookup_order(repo, **kwargs),
        ),
        "get_order_tracking": ToolSpec(
            name="get_order_tracking",
            description="Get shipment status and tracking events for an order.",
            input_schema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                },
                "required": ["order_id"],
            },
            func=lambda **kwargs: get_order_tracking(repo, **kwargs),
        ),
        "check_return_policy": ToolSpec(
            name="check_return_policy",
            description="Check whether an order item is returnable or exchangeable.",
            input_schema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "product_id": {"type": "string"},
                },
                "required": ["order_id", "product_id"],
            },
            func=lambda **kwargs: check_return_policy(repo, **kwargs),
        ),
        "create_exchange_request": ToolSpec(
            name="create_exchange_request",
            description="Create an exchange request for an eligible order item.",
            input_schema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "product_id": {"type": "string"},
                    "new_size": {"type": "string"},
                },
                "required": ["order_id", "product_id", "new_size"],
            },
            func=lambda **kwargs: create_exchange_request(repo, **kwargs),
        ),
    }


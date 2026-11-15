from __future__ import annotations

try:
    from pydantic import BaseModel
except ImportError:
    class BaseModel:
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)


class Product(BaseModel):
    id: str
    name: str
    category: str
    color: str
    colors: list[str]
    fabric: str
    description: str
    sizes: list[str]
    price: float
    available: bool
    returnable: bool
    final_sale: bool
    care: str


class InventoryItem(BaseModel):
    product_id: str
    size: str
    store_id: str
    quantity: int


class OrderLine(BaseModel):
    product_id: str
    size: str
    delivered_days_ago: int


class Order(BaseModel):
    order_id: str
    email: str
    customer_id: str
    status: str
    tracking_number: str
    carrier: str
    placed_at: str
    estimated_delivery: str | None
    items: list[OrderLine]


class ToolCallRecord(BaseModel):
    name: str
    args: dict
    result: dict


class AgentResult(BaseModel):
    final_answer: str
    tool_calls: list[ToolCallRecord]
    success: bool
    failure_type: str | None = None

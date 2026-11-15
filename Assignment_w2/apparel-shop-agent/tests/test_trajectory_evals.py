from __future__ import annotations

from apparel_agent.observability.evals import evaluate_trajectory
from apparel_agent.schemas.domain import ToolCallRecord


def test_trajectory_passes_concise_calls() -> None:
    calls = [
        ToolCallRecord(name="search_catalog", args={"query": "Classic Tee"}, result={}),
        ToolCallRecord(name="check_inventory", args={"product_id": "TEE-001", "size": "M"}, result={}),
    ]

    result = evaluate_trajectory(calls)

    assert result["label"] == "PASS"
    assert result["repeated_tool_count"] == 0


def test_trajectory_flags_repeated_same_tool_and_args() -> None:
    calls = [
        ToolCallRecord(name="search_catalog", args={"query": "dress"}, result={}),
        ToolCallRecord(name="search_catalog", args={"query": "dress"}, result={}),
    ]

    result = evaluate_trajectory(calls)

    assert result["label"] == "INEFFICIENT"
    assert result["repeated_tool_count"] == 1


def test_trajectory_flags_duplicate_cart_and_coupon_actions() -> None:
    calls = [
        ToolCallRecord(name="create_cart", args={"customer_id": "CUST-1"}, result={}),
        ToolCallRecord(name="create_cart", args={"customer_id": "CUST-1"}, result={}),
        ToolCallRecord(name="apply_coupon", args={"cart_id": "CART-1"}, result={}),
        ToolCallRecord(name="apply_coupon", args={"cart_id": "CART-1"}, result={}),
    ]

    result = evaluate_trajectory(calls)

    assert result["label"] == "INEFFICIENT"
    assert result["cart_creation_count"] == 2
    assert result["coupon_application_count"] == 2


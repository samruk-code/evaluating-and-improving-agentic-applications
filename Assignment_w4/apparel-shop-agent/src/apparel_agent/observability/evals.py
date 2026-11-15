from __future__ import annotations

import json
from collections import Counter

from apparel_agent.schemas.domain import ToolCallRecord


def evaluate_faithfulness(final_answer: str, tool_calls: list[ToolCallRecord]) -> dict:
    answer = final_answer.lower()
    saw_crew_neck_care = any(
        product.get("id") == "TOP-004"
        and product.get("care") == "Machine washable on wool cycle."
        for call in tool_calls
        for product in _products_from_result(call.result)
    )
    unsupported_care_terms = [
        "cool water",
        "wool-specific detergent",
        "inside out",
        "lay it flat",
        "cedar",
        "lavender",
        "lint brush",
        "fabric softeners",
    ]
    if saw_crew_neck_care and any(term in answer for term in unsupported_care_terms):
        return {
            "name": "faithfulness",
            "score": 0,
            "label": "FAIL",
            "reason": "Final answer adds care instructions beyond the catalog's single wool-cycle instruction.",
        }
    return {"name": "faithfulness", "score": 1, "label": "PASS", "reason": "No catalog contradiction detected."}


def _products_from_result(result: dict) -> list[dict]:
    products = list(result.get("products", []))
    if "product" in result:
        products.append(result["product"])
    return products


def evaluate_tool_fidelity(expected_tools: list[str], tool_calls: list[ToolCallRecord]) -> dict:
    actual = [call.name for call in tool_calls]
    missing = [tool for tool in expected_tools if tool not in actual]
    unexpected = [tool for tool in actual if tool not in expected_tools]
    label = "PASS" if not missing and not unexpected else "FAIL"
    return {
        "name": "tool_fidelity",
        "score": 1 if label == "PASS" else 0,
        "label": label,
        "expected_tools": expected_tools,
        "actual_tools": actual,
        "missing_tools": missing,
        "unexpected_tools": unexpected,
        "reason": "Actual trajectory matches expected tools." if label == "PASS" else "Tool trajectory differs from expected.",
    }


def evaluate_tool_response_handling(final_answer: str, tool_calls: list[ToolCallRecord]) -> dict:
    answer = final_answer.lower()
    saw_unavailable = any(
        call.name == "check_inventory" and call.result.get("available") is False
        for call in tool_calls
    )
    implies_available = any(
        phrase in answer
        for phrase in ["is available", "it's available", "it is available", "in stock", "you can buy", "yes,"]
    )
    negates_available = any(
        phrase in answer
        for phrase in ["not available", "unavailable", "out of stock", "isn't available", "not in stock"]
    )
    if saw_unavailable and implies_available and not negates_available:
        return {
            "name": "tool_response_handling",
            "score": 0,
            "label": "FAIL",
            "reason": "Inventory tool returned available=False, but final answer implies availability.",
        }
    return {
        "name": "tool_response_handling",
        "score": 1,
        "label": "PASS",
        "reason": "No mishandled unavailable inventory result detected.",
    }


def evaluate_trajectory(
    tool_calls: list[ToolCallRecord], max_tool_threshold: int = 6
) -> dict:
    signatures = [
        (call.name, json.dumps(call.args, sort_keys=True, default=str))
        for call in tool_calls
    ]
    counts = Counter(signatures)
    repeated_tool_count = sum(count - 1 for count in counts.values() if count > 1)
    coupon_count = sum(1 for call in tool_calls if call.name == "apply_coupon")
    cart_count = sum(1 for call in tool_calls if call.name == "create_cart")
    inefficient = (
        len(tool_calls) > max_tool_threshold
        or repeated_tool_count > 0
        or coupon_count > 1
        or cart_count > 1
    )
    return {
        "name": "trajectory_quality",
        "score": 0 if inefficient else 1,
        "label": "INEFFICIENT" if inefficient else "PASS",
        "tool_call_count": len(tool_calls),
        "repeated_tool_count": repeated_tool_count,
        "coupon_application_count": coupon_count,
        "cart_creation_count": cart_count,
        "reason": "Trajectory is concise." if not inefficient else "Trajectory repeats work or exceeds the tool threshold.",
    }


def run_all_evals(
    final_answer: str,
    tool_calls: list[ToolCallRecord],
    expected_tools: list[str],
) -> list[dict]:
    return [
        evaluate_faithfulness(final_answer, tool_calls),
        evaluate_tool_fidelity(expected_tools, tool_calls),
        evaluate_tool_response_handling(final_answer, tool_calls),
        evaluate_trajectory(tool_calls),
    ]


from __future__ import annotations

from apparel_agent.observability.evals import (
    evaluate_faithfulness,
    evaluate_tool_response_handling,
)
from apparel_agent.schemas.domain import ToolCallRecord


def test_tool_response_handling_flags_available_claim_after_false_result() -> None:
    calls = [
        ToolCallRecord(
            name="check_inventory",
            args={"product_id": "SHO-003", "size": "10"},
            result={"success": True, "available": False},
        )
    ]

    result = evaluate_tool_response_handling("Yes, it is available in size S.", calls)

    assert result["label"] == "FAIL"
    assert result["score"] == 0


def test_tool_response_handling_passes_unavailable_answer() -> None:
    calls = [
        ToolCallRecord(
            name="check_inventory",
            args={"product_id": "SHO-003", "size": "10"},
            result={"success": True, "available": False},
        )
    ]

    result = evaluate_tool_response_handling("No, it is unavailable in size S.", calls)

    assert result["label"] == "PASS"


def test_faithfulness_flags_unsupported_merino_care_claims() -> None:
    calls = [
        ToolCallRecord(
            name="get_product_details",
            args={},
            result={
                "product": {
                    "id": "TOP-004",
                    "care": "Machine washable on wool cycle.",
                }
            },
        )
    ]

    result = evaluate_faithfulness(
        "Use cool water, wool-specific detergent, and cedar blocks.",
        calls,
    )

    assert result["label"] == "FAIL"


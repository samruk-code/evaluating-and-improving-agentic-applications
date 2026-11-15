from __future__ import annotations

from apparel_agent.observability.evals import evaluate_tool_fidelity
from apparel_agent.schemas.domain import ToolCallRecord


def test_tool_fidelity_passes_matching_tools() -> None:
    calls = [
        ToolCallRecord(name="search_catalog", args={}, result={}),
        ToolCallRecord(name="check_inventory", args={}, result={}),
    ]

    result = evaluate_tool_fidelity(["search_catalog", "check_inventory"], calls)

    assert result["label"] == "PASS"
    assert result["score"] == 1


def test_tool_fidelity_reports_missing_and_unexpected_tools() -> None:
    calls = [ToolCallRecord(name="search_catalog", args={}, result={})]

    result = evaluate_tool_fidelity(["lookup_order"], calls)

    assert result["label"] == "FAIL"
    assert result["missing_tools"] == ["lookup_order"]
    assert result["unexpected_tools"] == ["search_catalog"]


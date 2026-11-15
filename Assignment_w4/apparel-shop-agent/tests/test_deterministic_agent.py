from __future__ import annotations

from apparel_agent.agent.deterministic_agent import DeterministicAgent
from apparel_agent.data.repository import ApparelRepository
from apparel_agent.tools.tool_registry import build_tool_registry


def test_deterministic_agent_answers_classic_tee_fixture() -> None:
    agent = DeterministicAgent(build_tool_registry(ApparelRepository()))

    result = agent.run("What colors does the Classic Tee come in?")

    assert result.success is True
    assert [call.name for call in result.tool_calls] == ["search_catalog"]
    assert "white, black, navy, and heather gray" in result.final_answer


def test_deterministic_agent_sequences_repeated_gift_fixture() -> None:
    agent = DeterministicAgent(build_tool_registry(ApparelRepository()))

    query = "What's a good gift idea for someone who works from home?"
    first = agent.run(query)
    second = agent.run(query)
    third = agent.run(query)

    assert first.success is True
    assert "Best options" in first.final_answer
    assert "Top pick" in second.final_answer
    assert "Best overall" in third.final_answer


def test_deterministic_agent_returns_scope_failure_fixture() -> None:
    agent = DeterministicAgent(build_tool_registry(ApparelRepository()))

    result = agent.run("What's your phone number for customer service?")

    assert result.success is True
    assert result.tool_calls == []
    assert result.failure_type == "hallucinated_alternative_channel"
    assert "website" in result.final_answer.lower()


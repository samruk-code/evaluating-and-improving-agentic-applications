from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from apparel_agent.agent.agent_loop import BaseAgent
from apparel_agent.schemas.domain import AgentResult, ToolCallRecord
from apparel_agent.tools.tool_registry import ToolSpec


FIXTURE_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "transcript_test_cases.json"
)


def _normalize(message: str) -> str:
    return " ".join(message.lower().strip().split())


class DeterministicAgent(BaseAgent):
    def __init__(
        self,
        tools: dict[str, ToolSpec],
        max_steps: int = 8,
        fixture_path: str | Path = FIXTURE_PATH,
    ) -> None:
        self.tools = tools
        self.max_steps = max_steps
        self.fixture_path = Path(fixture_path)
        self._fixture_call_counts: dict[str, int] = defaultdict(int)
        self._fixtures_by_input = self._load_fixtures()

    def run(self, message: str, scenario_name: str | None = None) -> AgentResult:
        fixture_result = self.run_if_fixture(message)
        if fixture_result is not None:
            return fixture_result

        calls: list[ToolCallRecord] = []

        def call(name: str, args: dict) -> dict:
            result = self.tools[name].func(**args)
            calls.append(ToolCallRecord(name=name, args=args, result=result))
            return result

        call("search_catalog", {"query": message, "filters": {}})
        return AgentResult(
            final_answer="I searched the catalog. Please provide size, budget, or action details for the next step.",
            tool_calls=calls,
            success=True,
        )

    def run_if_fixture(self, message: str) -> AgentResult | None:
        normalized = _normalize(message)
        fixtures = self._fixtures_by_input.get(normalized)
        if not fixtures:
            return None

        fixture_index = self._fixture_call_counts[normalized] % len(fixtures)
        self._fixture_call_counts[normalized] += 1
        fixture = fixtures[fixture_index]
        calls: list[ToolCallRecord] = []

        for tool_call in fixture.get("tool_calls", []):
            name = tool_call["name"]
            args = tool_call.get("args", {})
            result = self.tools[name].func(**args)
            calls.append(ToolCallRecord(name=name, args=args, result=result))

        return AgentResult(
            final_answer=fixture["output"],
            tool_calls=calls,
            success=True,
            failure_type=fixture.get("failure_type"),
        )

    def _load_fixtures(self) -> dict[str, list[dict]]:
        if not self.fixture_path.exists():
            return {}
        with self.fixture_path.open(encoding="utf-8") as fixture_file:
            fixtures = json.load(fixture_file)

        fixtures_by_input: dict[str, list[dict]] = defaultdict(list)
        for fixture in fixtures:
            fixtures_by_input[_normalize(fixture["input"])].append(fixture)
        return dict(fixtures_by_input)


from __future__ import annotations

from apparel_agent.schemas.domain import AgentResult


class BaseAgent:
    def run(self, message: str, scenario_name: str | None = None) -> AgentResult:
        raise NotImplementedError


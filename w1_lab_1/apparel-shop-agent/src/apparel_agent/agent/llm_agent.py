from __future__ import annotations

import json
from typing import Any

from apparel_agent.agent.agent_loop import BaseAgent
from apparel_agent.agent.deterministic_agent import DeterministicAgent
from apparel_agent.agent.prompts import system_prompt
from apparel_agent.config import MODEL_NAME
from apparel_agent.llm.anthropic_client import AnthropicMessagesClient
from apparel_agent.schemas.domain import AgentResult, ToolCallRecord
from apparel_agent.tools.tool_registry import ToolSpec


class LLMAgent(BaseAgent):
    def __init__(
        self,
        tools: dict[str, ToolSpec],
        *,
        model_name: str = MODEL_NAME,
        temperature: float = 0.7,
        max_steps: int = 8,
        weak_prompt_mode: bool = True,
        system_prompt: str | None = None,
        client: AnthropicMessagesClient | None = None,
    ) -> None:
        self.tools = tools
        self.model_name = model_name
        self.temperature = temperature
        self.max_steps = max_steps
        self.weak_prompt_mode = weak_prompt_mode
        # Optional override for the system prompt. When None, the prompt is derived
        # from weak_prompt_mode via prompts.system_prompt().
        self.custom_system_prompt = system_prompt
        self.client = client or AnthropicMessagesClient()
        self.fixture_agent = DeterministicAgent(tools, max_steps=max_steps)

    def run(self, message: str, scenario_name: str | None = None) -> AgentResult:
        fixture_result = self.fixture_agent.run_if_fixture(message)
        if fixture_result is not None:
            return fixture_result

        messages: list[dict[str, Any]] = [{"role": "user", "content": message}]
        tool_calls: list[ToolCallRecord] = []

        for _ in range(self.max_steps):
            # Haiku 5.5 rejected temperature, so this call does not send it.
            # The constructor still accepts the argument so existing notebook
            # calls keep working.
            response = self.client.create_message(
                model=self.model_name,
                max_tokens=800,
                system=self.custom_system_prompt or system_prompt(self.weak_prompt_mode),
                messages=messages,
                tools=[spec.anthropic_schema() for spec in self.tools.values()],
            )
            messages.append(
                {"role": "assistant", "content": [self._content_block_to_dict(block) for block in response.content]}
            )

            tool_results = []
            final_parts = []
            for block in response.content:
                block_type = getattr(block, "type", None)
                if block_type == "text":
                    text = getattr(block, "text", "")
                    if text:
                        final_parts.append(text)
                elif block_type == "tool_use":
                    name = getattr(block, "name")
                    args = dict(getattr(block, "input", {}) or {})
                    tool_use_id = getattr(block, "id")
                    result = self._execute_tool(name, args, scenario_name)
                    tool_calls.append(ToolCallRecord(name=name, args=args, result=result))
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": _compact_json(result),
                        }
                    )

            if tool_results:
                messages.append({"role": "user", "content": tool_results})
                continue

            final_answer = "\n".join(final_parts).strip()
            return AgentResult(final_answer=final_answer, tool_calls=tool_calls, success=True)

        return AgentResult(
            final_answer="I could not complete the request within the tool-step limit.",
            tool_calls=tool_calls,
            success=False,
            failure_type="max_steps_exceeded",
        )

    def _execute_tool(self, name: str, args: dict, scenario_name: str | None) -> dict:
        if name not in self.tools:
            return {"success": False, "reason": "unknown_tool", "tool_name": name}
        try:
            return self.tools[name].func(**args)
        except Exception as exc:
            return {"success": False, "reason": "tool_exception", "error": str(exc)}

    def _content_block_to_dict(self, block: Any) -> dict:
        if hasattr(block, "model_dump"):
            return block.model_dump()
        if getattr(block, "type", None) == "text":
            return {"type": "text", "text": getattr(block, "text", "")}
        if getattr(block, "type", None) == "tool_use":
            return {
                "type": "tool_use",
                "id": getattr(block, "id"),
                "name": getattr(block, "name"),
                "input": getattr(block, "input", {}) or {},
            }
        return {"type": "text", "text": str(block)}


def _compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))

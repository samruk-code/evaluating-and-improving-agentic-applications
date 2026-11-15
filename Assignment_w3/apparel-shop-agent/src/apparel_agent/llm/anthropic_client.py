from __future__ import annotations

import os
from typing import Any


class AnthropicMessagesClient:
    def __init__(self, api_key: str | None = None) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("Install anthropic to use LLMAgent.") from exc
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    def create_message(self, **kwargs: Any) -> Any:
        return self.client.messages.create(**kwargs)


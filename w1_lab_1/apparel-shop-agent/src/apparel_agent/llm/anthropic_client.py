from __future__ import annotations

import os
from typing import Any


class AnthropicMessagesClient:
    def __init__(self, api_key: str | None = None) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("Install anthropic to use LLMAgent.") from exc
        # Use ANTHROPIC_BASE_URL when the platform sets it. SDK 1.7 then sends
        # the key as X-Api-Key, which is what that proxy accepts.
        kwargs: dict[str, Any] = {}
        base_url = (os.environ.get("ANTHROPIC_BASE_URL") or "").strip()
        if base_url:
            kwargs["base_url"] = base_url
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"), **kwargs)

    def create_message(self, **kwargs: Any) -> Any:
        return self.client.messages.create(**kwargs)


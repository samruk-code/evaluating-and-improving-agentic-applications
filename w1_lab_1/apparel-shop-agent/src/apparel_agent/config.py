from __future__ import annotations

from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:
        return None

MODEL_NAME = "claude-haiku-5-5"


@dataclass(frozen=True)
class AppConfig:
    deterministic: bool = False
    model_name: str = MODEL_NAME
    temperature: float = 0.7
    max_steps: int = 8
    weak_prompt_mode: bool = True


def load_config(
    *,
    deterministic: bool | None = None,
    weak_prompt_mode: bool | None = None,
) -> AppConfig:
    load_dotenv()
    return AppConfig(
        deterministic=False if deterministic is None else deterministic,
        weak_prompt_mode=True if weak_prompt_mode is None else weak_prompt_mode,
    )

from __future__ import annotations

import argparse
import os

try:
    from rich.console import Console
except ImportError:
    class Console:
        def print(self, value: object = "", *args, **kwargs) -> None:
            print(value)

        def rule(self, value: object = "") -> None:
            print(f"\n{'=' * 10} {value} {'=' * 10}")

from apparel_agent.agent.deterministic_agent import DeterministicAgent
from apparel_agent.agent.llm_agent import LLMAgent
from apparel_agent.config import load_config
from apparel_agent.data.repository import ApparelRepository
from apparel_agent.scenarios.demo_cases import DEMO_CASES
from apparel_agent.tools.tool_registry import build_tool_registry

console = Console()


def build_agent(config, repo: ApparelRepository):
    tools = build_tool_registry(repo)
    if config.deterministic:
        return DeterministicAgent(tools, max_steps=config.max_steps)
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is required for LLM mode. Use --deterministic for local scripted runs."
        )
    return LLMAgent(
        tools,
        model_name=config.model_name,
        temperature=config.temperature,
        max_steps=config.max_steps,
        weak_prompt_mode=config.weak_prompt_mode,
    )


def run_case(agent, case: dict) -> None:
    result = agent.run(case["message"], scenario_name=case["name"])

    console.rule(f"[bold]{case['name']}[/bold]")
    console.print(f"[bold]User:[/bold] {case['message']}")
    console.print(f"[bold]Final answer:[/bold] {result.final_answer}")
    console.print(f"[bold]Actual tools:[/bold] {[call.name for call in result.tool_calls]}")
    console.print(f"[bold]Expected tools:[/bold] {case['expected_tools']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the apparel-shop agent demo.")
    parser.add_argument("--prompt", help="Run one custom prompt instead of all demo cases.")
    parser.add_argument("--deterministic", action="store_true", help="Use scripted deterministic mode.")
    parser.add_argument("--strong-prompt", action="store_true", help="Use the stronger system prompt in LLM mode.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(
        deterministic=args.deterministic,
        weak_prompt_mode=not args.strong_prompt,
    )
    repo = ApparelRepository()
    agent = build_agent(config, repo)

    console.print(
        f"Mode: {'deterministic' if config.deterministic else 'llm'} | "
        f"model={config.model_name} | weak_prompt_mode={config.weak_prompt_mode}"
    )

    if args.prompt:
        case = {
            "name": "custom_prompt",
            "message": args.prompt,
            "expected_tools": [],
            "expected_failure": None,
        }
        run_case(agent, case)
        return

    for case in DEMO_CASES:
        run_case(agent, case)


if __name__ == "__main__":
    main()

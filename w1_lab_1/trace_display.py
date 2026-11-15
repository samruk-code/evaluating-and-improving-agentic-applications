"""IPython display helpers for traces collected by ``local_tracing``."""

from __future__ import annotations

import json
from typing import Any

from IPython.display import Markdown, display

def _trace_dict(span: Any | dict[str, Any]) -> dict[str, Any]:
    return span if isinstance(span, dict) else span.to_dict()


def _truncate(value: Any, max_chars: int) -> str:
    text = json.dumps(value, ensure_ascii=False, default=str)
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def format_trace_tree(span: Any | dict[str, Any], *, max_chars: int = 240) -> str:
    """Render a nested Markdown tree with status, latency, inputs, and outputs."""
    lines: list[str] = []

    def walk(node: dict[str, Any], depth: int) -> None:
        indent = "  " * depth
        status = node.get("status", "unset")
        marker = "✗" if status == "error" else "•"
        duration = node.get("duration_ms")
        timing = f" — {duration:.2f} ms" if isinstance(duration, (int, float)) else ""
        lines.append(f"{indent}- {marker} **{node.get('name', '?')}** `{node.get('kind', 'span')}`{timing}")
        if node.get("input") is not None:
            lines.append(f"{indent}  - input: `{_truncate(node['input'], max_chars)}`")
        if node.get("output") is not None:
            lines.append(f"{indent}  - output: `{_truncate(node['output'], max_chars)}`")
        if node.get("error"):
            lines.append(f"{indent}  - error: `{_truncate(node['error'], max_chars)}`")
        for child in node.get("children", []) or []:
            walk(child, depth + 1)

    walk(_trace_dict(span), 0)
    return "\n".join(lines)


def show_trace(span: Any | dict[str, Any] | None, *, title: str | None = None) -> None:
    if span is None:
        display(Markdown("_No trace to show._"))
        return
    header = f"### {title}\n\n" if title else ""
    display(Markdown(header + format_trace_tree(span)))

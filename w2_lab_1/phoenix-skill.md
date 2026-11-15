---
name: arize-phoenix
description: Open-source AI observability platform for tracing, evaluating, and improving LLM applications with OpenTelemetry integration
license: MIT
source: https://github.com/Arize-ai/phoenix/blob/main/docs/phoenix/skill.md
---

# Arize Phoenix

Phoenix is an open-source AI observability platform built on OpenTelemetry that
helps developers understand, debug, and improve AI applications. It provides
tracing, evaluation, prompt engineering, and experimentation for LLM-based
systems. Phoenix captures detailed execution information, measures output quality
with evaluators, and supports data-driven experimentation.

This file is loaded as a rule so you (the coding agent) have Phoenix expertise
available for this lab. When a task involves Phoenix tracing, follow the patterns
below exactly.

## Tracing quickstart (this lab's stack: Claude Agent SDK + Anthropic + local Phoenix)

The app is a Gradio chat app using `claude_agent_sdk`. Phoenix runs locally and
exposes the OTLP HTTP collector at `http://localhost:6006`.

1. **Register the tracer provider** near the top of the module, before the agent
   code, using `phoenix.otel.register`:

```python
import os
from phoenix.otel import register

# Use the local Phoenix collector; drop any Phoenix Cloud settings.
os.environ.pop("PHOENIX_API_KEY", None)
os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
tracer_provider = register(
    project_name="dlai-ecommerce-agent",
    auto_instrument=True,                      # auto-wrap installed instrumentors
    endpoint="http://localhost:6006/v1/traces",
)
tracer = tracer_provider.get_tracer("ecommerce-agent")
```

   - Leave `import sitecustomize` in place, before `import gradio`. It turns off FastAPI HTTP traces so Gradio's startup checks are not stored in Phoenix.
   - `auto_instrument=True` discovers installed OpenInference instrumentors
     (`openinference-instrumentation-claude-agent-sdk`,
     `openinference-instrumentation-anthropic`) so model calls are traced with no
     manual span code.

2. **Wrap pipeline steps as spans** with the one-line decorators. `@tracer.chain`
   marks a retrieval/orchestration step; `@tracer.tool` marks a tool call. The
   decorator records arguments as span input and the return value as span output:

```python
@tracer.chain
def search_catalog(user_query: str) -> list:
    return retrieval.search_catalog(user_query)


@tracer.tool
def check_inventory(product_id: str) -> dict:
    return retrieval.check_inventory(product_id)
```

   Decorating the top-level `ask_agent` with `@tracer.chain` nests the search,
   inventory, and LLM spans under one trace per query.

3. **Manual spans** when a decorator does not fit:

```python
with tracer.start_as_current_span("step-name", openinference_span_kind="chain") as span:
    span.set_input(user_input)
    result = do_work(user_input)
    span.set_output(result)
```

## Verifying traces

- Open the Phoenix UI and select the project (here `dlai-ecommerce-agent`).
- Each query becomes one trace; expand the span tree to see
  `search_catalog` → `check_inventory` → the LLM call nested under `ask_agent`.
- If no traces appear, confirm Phoenix is running, the collector endpoint is
  `http://localhost:6006`, the instrumentation packages are installed, and the
  process was restarted after editing.

## Key concepts

- **Trace / span**: a trace is the full execution path of one request; spans are
  individual units of work (an LLM call, a tool call, a retrieval) and can nest.
- **Project**: organizational unit for traces (by environment, app, or team).
- **OpenTelemetry (OTLP)**: the industry-standard protocol Phoenix is built on.
- **OpenInference**: Phoenix's AI-specific semantic conventions on top of OTLP
  (LLM spans, retrieval spans, embeddings).

## Capabilities (broader Phoenix surface)

- **Trace** LLM calls, tool executions, retrievals, embeddings, prompt templates.
- **Evaluate** output quality with LLM-as-a-judge or code-based evaluators.
- **Annotate** traces with human feedback, scores, and labels.
- **Experiment** by running task functions against datasets with evaluators.
- **Monitor** latency, token usage, cost, and error rates per project.
- **Integrate** with 20+ frameworks/providers via OpenTelemetry instrumentation,
  including the Claude Agent SDK and Anthropic.

SDK packages: `arize-phoenix`, `arize-phoenix-otel`, `arize-phoenix-client`,
`arize-phoenix-evals`. For additional docs: https://arize.com/docs/phoenix/llms.txt

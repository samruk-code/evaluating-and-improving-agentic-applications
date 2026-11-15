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

The app is a Gradio chat app using `claude_agent_sdk`, with twelve real tools
(for example `order_lookup`, `check_inventory`, `get_customer`, `process_refund`) exposed
through an in-process MCP server (`create_sdk_mcp_server`). Phoenix runs
locally and exposes the OTLP HTTP collector at `http://localhost:6006`.

1. **Register the tracer provider** near the top of the module, before the agent
   code, using `phoenix.otel.register`:

```python
import os
from phoenix.otel import register

# Use the local Phoenix collector; drop any Phoenix Cloud settings.
os.environ.pop("PHOENIX_API_KEY", None)
os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
register(
    project_name="dlai-ecommerce-agent",
    auto_instrument=True,                      # auto-wrap installed instrumentors
    endpoint="http://localhost:6006/v1/traces",
)
```

   - Leave `import sitecustomize` in place, before `import gradio`. It turns off FastAPI HTTP traces so Gradio's startup checks are not stored in Phoenix.
   - `auto_instrument=True` discovers installed OpenInference instrumentors
     (`openinference-instrumentation-claude-agent-sdk`,
     `openinference-instrumentation-anthropic`) so model calls **and every
     MCP tool call the SDK's own agent loop makes** are traced with no
     manual span code — unlike a hand-rolled retrieval pipeline, there is no
     `@tracer.tool` / `@tracer.chain` to add here. Each `query(...)` call
     becomes one parent span; each `order_lookup` / `check_inventory` /
     `get_customer` / `process_refund` invocation the model makes during
     that call becomes a child span underneath it, carrying the tool name,
     the arguments the model passed, and the value the tool returned.

2. **Manual spans** when a decorator does not fit (rare in this lab — most
   scripts only ever *read back* the spans the agent already produced):

```python
with tracer.start_as_current_span("step-name", openinference_span_kind="chain") as span:
    span.set_input(user_input)
    result = do_work(user_input)
    span.set_output(result)
```

## Pulling spans back out for evaluation

`phoenix.client.Client().spans.get_spans_dataframe(project_identifier=...)`
returns one row per span, parent and child mixed together. To reconstruct a
run's **trajectory** (the ordered list of tool calls it made):

```python
from phoenix.client import Client
import pandas as pd, json

client = Client()
spans = client.spans.get_spans_dataframe(project_identifier="dlai-ecommerce-agent")
spans["start_time"] = pd.to_datetime(spans["start_time"], utc=True)

KIND_COL = "span_kind" if "span_kind" in spans.columns else "attributes.openinference.span.kind"
agent_runs = spans[spans["parent_id"].isna()]          # one row per query(...) call
tool_calls = spans[spans[KIND_COL].str.upper() == "TOOL"]

# For a given agent run's span_id, its tool calls are the rows whose
# parent_id matches it, ordered by start_time.
```

## Verifying traces

- Open the Phoenix UI and select the project (here `dlai-ecommerce-agent`).
- Each query becomes one trace; expand the span tree to see the tool calls
  (`order_lookup`, `check_inventory`, `get_customer`, `process_refund`)
  nested under the top-level agent span, each carrying its arguments and
  return value.
- If no traces appear, confirm Phoenix is running, the collector endpoint is
  `http://localhost:6006`, the instrumentation packages are installed, and the
  process was restarted after editing.

## Key concepts

- **Trace / span**: a trace is the full execution path of one request; spans are
  individual units of work (an LLM call, a tool call, a retrieval) and can nest.
- **Project**: organizational unit for traces (by environment, app, or team).
- **OpenTelemetry (OTLP)**: the industry-standard protocol Phoenix is built on.
- **OpenInference**: Phoenix's AI-specific semantic conventions on top of OTLP
  (LLM spans, tool spans, retrieval spans, embeddings).

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

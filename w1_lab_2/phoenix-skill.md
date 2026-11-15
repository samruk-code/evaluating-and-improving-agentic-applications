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

   - Leave `import sitecustomize` in place, before `import gradio`. FastAPI records an HTTP span for every Gradio request once this tracer exists, including the checks Gradio makes while starting. That module turns those spans off. Agent spans are unchanged.
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

## Reading traces back (querying spans from code)

To pull traces back out of a running Phoenix server — to summarize answers,
compare repeated queries, or look for failure modes — use the
`arize-phoenix-client` package (installed in this lab). This is the only
supported read path; see the "do not" list below before trying anything else.

```python
from phoenix.client import Client

client = Client(base_url="http://localhost:6006")
df = client.spans.get_spans_dataframe(
    project_identifier="dlai-ecommerce-agent",  # project name works as the identifier
    limit=2000,
)
```

The dataframe has one row per span, with dotted attribute columns:
`name`, `parent_id`, `start_time`, `attributes.input.value`,
`attributes.output.value`, `attributes.openinference.span.kind`.

**Where the agent's final answer lives.** One customer question = one root span
named `ask_agent` (`parent_id` is null). Its `attributes.input.value` is the
question and its `attributes.output.value` is the final answer the customer
saw. Nested under it you get `search_catalog` (CHAIN), one `check_inventory`
(TOOL) per retrieved product, and a `ClaudeAgentSDK.query` (AGENT) span for the
model call.

**If `ClaudeAgentSDK.query` is missing**, the app imported the function before
instrumentation was installed. `register()` patches `claude_agent_sdk.query`,
so a module that did `from claude_agent_sdk import query` holds the original
and the patch never reaches it. Import the module and call
`claude_agent_sdk.query(...)` instead — that resolves the attribute at call
time and works regardless of where `register()` sits.

```python
roots = df[df["name"] == "ask_agent"].sort_values("start_time")
latest = roots.tail(15)  # one run of the 15-query batch
for _, row in latest.iterrows():
    print(row["attributes.input.value"], "->", row["attributes.output.value"])
```

**Traces accumulate.** The project keeps every trace ever sent to it — sanity
checks, aborted runs, and repeated batch runs all pile up, so the same question
appears many times. Always sort by `start_time` and take the most recent N
rather than assuming the project holds exactly one run.

**Fallback without Python** — the REST endpoint, newest span first:

```bash
curl -s "http://localhost:6006/v1/projects/dlai-ecommerce-agent/spans?limit=200"
```

**Do not** use these — they fail on the installed version:

- `px.Client()` / `phoenix.Client(...)` — removed; raises
  `AttributeError: module 'phoenix' has no attribute 'Client'`.
- `px.active_session()` / `px.launch_app()` — for in-process sessions; Phoenix
  here is a separate server process.
- `GET /v1/spans` — returns HTTP 422; the project-scoped path above is the one
  that works.
- Reading `phoenix-data/phoenix.db` with `sqlite3` — the server owns that file;
  query the API instead.

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

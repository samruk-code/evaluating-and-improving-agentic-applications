"""Northwind Apparel support agent — Gradio app, tools, and a versioned prompt.

Modules 1–3 gave this agent a catalog in its system prompt and nothing else:
it could describe products but couldn't look anything up or *do* anything.
Here it gets the full apparel-shop toolset — twelve tools over a fourteen-table
ground-truth SQLite database (`db.py`) — matching the capabilities of the
graded Module 1 agent.

Five of the twelve tools **write**: `reserve_item` decrements stock and holds
an item, `create_cart` and `apply_coupon` build and discount a cart,
`create_exchange_request` files an exchange, and `process_refund` moves money.
That asymmetry is the whole point of Task 3's outcome evaluator: after the
agent runs, you can go ask the database what actually happened instead of
taking the agent's word for it. The other seven are read-only.

Tracing is already wired up: Phoenix's Claude Agent SDK instrumentation
auto-captures each MCP tool call as a child span under the agent's run, with
no manual `@tracer.tool` decorators needed (unlike modules 1-3's hand-rolled
retrieval pipeline) — see `/opt/skills/phoenix-skill.md` for why.

Module 5 changes exactly one structural thing, and it is the thing that makes
the rest of the lab possible: **the system prompt is no longer a constant.** It
lives in `prompts/<version>.md`, and `ask_agent` takes a version name. Every
experiment records the version it ran, so "which agent was this?" always has an
answer, and a comparison between two experiments is a comparison of one change.

`ask_agent` also returns more than a string now. It hands back the
**trajectory** — the ordered tool calls with their arguments and results —
reconstructed from the SDK's message stream rather than pulled back out of
Phoenix. Module 4 assembled trajectories from tool spans because those runs had
already happened; inside an experiment the run is happening right now and the
tools are our own functions, so reading the stream is both simpler and exact.
Phoenix still records every run, unchanged.

The Gradio chat serves whichever version `NORTHWIND_PROMPT_VERSION` names
(default `v1` — module 4's agent, defect and all). Restart it on a later
version with `NORTHWIND_PROMPT_VERSION=v3 bash run.sh`.

Run Phoenix first (see the Setup step in the instructions), then: bash run.sh
"""

import json
import os
import re
import time
from pathlib import Path

os.environ.pop("PHOENIX_API_KEY", None)
os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
from phoenix.otel import register

# Which Phoenix project this process's traces land in.
#
# It is an environment variable, and it has to be: registration and
# instrumentation both happen once, here at import, and the instrumentor keeps
# the tracer it was handed. Re-registering later in the same process does not
# move anything — the spans keep going where the first register() pointed them.
# So routing a batch to a different project means running it in its own process:
#
#     NORTHWIND_PHOENIX_PROJECT=dlai-northwind-production python3 some_script.py
#
# Tasks 1–4 stay on the default project. Set the variable on the command
# line only if a script should trace somewhere else.
PROJECT_NAME = os.environ.get("NORTHWIND_PHOENIX_PROJECT", "dlai-ecommerce-agent")

# auto_instrument imports openinference's Anthropic instrumentor, which
# reaches into a private SDK module. If that import fails, still start the
# app — a dead Gradio process is what leaves the lab on the starting screen.
try:
    register(
        project_name=PROJECT_NAME,
        auto_instrument=True,
        endpoint="http://localhost:6006/v1/traces",
    )
except Exception as error:
    print(
        "WARN: Phoenix auto-instrumentation failed "
        f"({type(error).__name__}: {error}). "
        "Starting without it so the chat app can still bind :7860."
    )
    register(
        project_name=PROJECT_NAME,
        auto_instrument=False,
        endpoint="http://localhost:6006/v1/traces",
    )

# Workaround for a Phoenix 19.17.0 UI crash, removable once the pin moves.
#
# OpenInference's spec says `tool.parameters` is a JSON *string*, and the
# instrumentation sets it correctly. Phoenix's ingest then expands that string
# back into flattened `tool.parameters.<arg>` sub-keys, and the span detail
# page reconstructs them into an object and hands it to React as a child —
# which throws "Minified React error #31" and blanks the trace view. The
# identical arguments are already on `input.value` (a plain JSON string that
# Phoenix leaves alone), and that is what every evaluator in this lab reads,
# so the safest fix is to stop emitting the attribute that trips the UI.
import openinference.instrumentation.claude_agent_sdk._wrappers as _oi_wrappers

_original_get_tool_attributes = _oi_wrappers.get_tool_attributes


def _tool_attributes_without_parameters(*, name, description=None, parameters):
    attributes = _original_get_tool_attributes(
        name=name, description=description, parameters=parameters
    )
    attributes.pop("tool.parameters", None)
    return attributes


_oi_wrappers.get_tool_attributes = _tool_attributes_without_parameters

# claude_agent_sdk must be imported AFTER register(auto_instrument=True): the
# instrumentor monkey-patches claude_agent_sdk.query.query in place, and
# `from claude_agent_sdk import query` only picks up the patched version if
# it runs after that patch has happened. Importing query first would silently
# bind this module's `query` name to the pre-instrumentation function, and
# every agent run — and every tool call span underneath it — would go
# unrecorded with no error to signal it.
import sitecustomize  # disables FastAPI HTTP traces before Gradio builds its app
import gradio as gr
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    query,
    tool,
)

import db

# One connection, opened (and seeded, if this is a fresh workspace) once at
# import time, shared by every tool call this process makes. Evaluator
# scripts launched later in the lab open their own connection to the same
# file via db.get_connection() — see db.py's docstring for why this has to
# be a real file rather than ":memory:".
_conn = db.initialize()


def _text(payload):
    """MCP tools return content blocks; we hand back JSON as text."""
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


# The @tool decorator takes either a `{"name": type}` shorthand — which makes
# every parameter required — or a full JSON Schema, which is what the tools
# with optional or nested parameters use below.


# --- catalog (read-only) ---------------------------------------------------


@tool(
    "search_catalog",
    "Search the apparel catalog by text query, with optional filters on "
    "category, color, fabric, size, price and availability. Use when the "
    "customer describes what they want rather than naming a product ID.",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Free-text description of what the customer wants."},
            "filters": {
                "type": "object",
                "description": "Optional narrowing filters.",
                "properties": {
                    "category": {"type": "string"},
                    "color": {"type": "string"},
                    "fabric": {"type": "string"},
                    "size": {"type": "string"},
                    "max_price": {"type": "number"},
                    "available": {"type": "boolean"},
                },
            },
        },
        "required": ["query"],
    },
)
async def search_catalog(args):
    return _text(db.search_catalog(_conn, args["query"], args.get("filters")))


@tool(
    "get_product_details",
    "Get the full record for one product by product ID (e.g. TEE-001): "
    "description, fabric, care instructions, price, colors, sizes and whether "
    "it is returnable. Use for factual claims about a specific product.",
    {"product_id": str},
)
async def get_product_details(args):
    return _text(db.get_product_details(_conn, args["product_id"]))


# --- inventory -------------------------------------------------------------


@tool(
    "check_inventory",
    "Check current stock and price for a product by product ID (e.g. TEE-001). "
    "Pass a size to check that size specifically; omit it to get the stock "
    "broken down across all sizes. Use before telling a customer whether "
    "something is available.",
    {
        "type": "object",
        "properties": {
            "product_id": {"type": "string"},
            "size": {"type": "string", "description": "Optional. Omit to check every size."},
            "store_id": {"type": "string", "default": "STORE-001"},
        },
        "required": ["product_id"],
    },
)
async def check_inventory(args):
    return _text(
        db.check_inventory(
            _conn,
            args["product_id"],
            args.get("size"),
            args.get("store_id") or db.DEFAULT_STORE_ID,
        )
    )


@tool(
    "reserve_item",
    "Reserve one in-stock item for customer pickup. WRITES: this decrements "
    "store stock and creates a reservation record. Check inventory first.",
    {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"},
            "product_id": {"type": "string"},
            "size": {"type": "string"},
            "store_id": {"type": "string", "default": "STORE-001"},
        },
        "required": ["customer_id", "product_id", "size"],
    },
)
async def reserve_item(args):
    return _text(
        db.reserve_item(
            _conn,
            args["customer_id"],
            args["product_id"],
            args["size"],
            args.get("store_id") or db.DEFAULT_STORE_ID,
        )
    )


# --- carts -----------------------------------------------------------------


@tool(
    "create_cart",
    "Create a cart for a customer with one or more items. WRITES: this creates "
    "a real cart record. Prices come from the catalog, not from the customer.",
    {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string"},
                        "size": {"type": "string"},
                        "quantity": {"type": "integer", "default": 1},
                    },
                    "required": ["product_id", "size"],
                },
            },
        },
        "required": ["customer_id", "items"],
    },
)
async def create_cart(args):
    return _text(db.create_cart(_conn, args["customer_id"], args.get("items") or []))


@tool(
    "apply_coupon",
    "Apply a coupon code to an existing cart. WRITES: this updates the cart's "
    "discount and total. Returns the recalculated cart.",
    {"cart_id": str, "coupon_code": str},
)
async def apply_coupon(args):
    return _text(db.apply_coupon(_conn, args["cart_id"], args["coupon_code"]))


# --- orders ----------------------------------------------------------------


@tool(
    "order_lookup",
    "Look up a single order by its order ID. Returns the customer, items, "
    "amount, status and order date. Pass the customer's email as well to "
    "verify the order actually belongs to them. Use when a customer asks "
    "about a specific order.",
    {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "email": {
                "type": "string",
                "description": "Optional. When supplied, the order is only returned if the email matches.",
            },
        },
        "required": ["order_id"],
    },
)
async def order_lookup(args):
    return _text(db.order_lookup(_conn, args["order_id"], args.get("email")))


@tool(
    "get_order_tracking",
    "Get shipment status, carrier, tracking number and the timestamped "
    "tracking events for an order. Use for 'where is my package' questions.",
    {"order_id": str},
)
async def get_order_tracking(args):
    return _text(db.get_order_tracking(_conn, args["order_id"]))


@tool(
    "check_return_policy",
    "Check whether one item in an order is still returnable or exchangeable, "
    "given how long ago it was delivered and whether it was a final sale. Use "
    "before promising a customer a return, refund or exchange.",
    {"order_id": str, "product_id": str},
)
async def check_return_policy(args):
    return _text(db.check_return_policy(_conn, args["order_id"], args["product_id"]))


@tool(
    "create_exchange_request",
    "Create an exchange request for an eligible order item in a new size. "
    "WRITES: this files a real exchange record. It refuses if the item is "
    "outside the return window or the requested size is out of stock.",
    {"order_id": str, "product_id": str, "new_size": str},
)
async def create_exchange_request(args):
    return _text(
        db.create_exchange_request(_conn, args["order_id"], args["product_id"], args["new_size"])
    )


# --- customers and refunds -------------------------------------------------


@tool(
    "get_customer",
    "Retrieve a customer profile and their full order history, by customer ID "
    "(e.g. CUST-001) or by email address. Use to verify who you are speaking "
    "to. Supply exactly one of customer_id or email.",
    {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "e.g. CUST-001."},
            "email": {"type": "string", "description": "The customer's email address."},
        },
    },
)
async def get_customer(args):
    return _text(db.get_customer(_conn, args.get("customer_id"), args.get("email")))


@tool(
    "process_refund",
    "Issue a refund against an order. WRITES: this creates a real refund "
    "record and moves money. Returns the created refund.",
    {"order_id": str, "amount": float, "reason": str},
)
async def process_refund(args):
    return _text(db.process_refund(_conn, args["order_id"], args["amount"], args["reason"]))


TOOLS = [
    search_catalog,
    get_product_details,
    check_inventory,
    reserve_item,
    create_cart,
    apply_coupon,
    order_lookup,
    get_order_tracking,
    check_return_policy,
    create_exchange_request,
    get_customer,
    process_refund,
]

northwind_server = create_sdk_mcp_server(name="northwind", version="1.0.0", tools=TOOLS)
TOOL_NAMES = [t.name for t in TOOLS]

# SDK MCP tools are exposed to the agent as "mcp__<server>__<tool>".
ALLOWED_TOOLS = [f"mcp__northwind__{t}" for t in TOOL_NAMES]

# --- the system prompt, as a versioned file --------------------------------
#
# Module 4 hard-coded this string. Module 5 keeps each version in
# `prompts/<version>.md` so that changing the agent is a file edit (the Edit
# button in the instructions panel, or any editor) rather than a code change,
# and so every experiment can record *which* prompt produced its numbers.
#
# The files are read fresh on every call, not cached at import: edit
# `prompts/v3.md`, re-run your script, and the next run uses the new text.

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"

# A prompt file may open with an HTML comment naming the version — that is a
# note to the reader, not an instruction to the model, so it is stripped.
_FRONT_COMMENT = re.compile(r"\A\s*<!--.*?-->\s*", re.DOTALL)


def list_prompt_versions() -> list[str]:
    """Every version that currently has a file, in name order."""
    return sorted(path.stem for path in PROMPT_DIR.glob("*.md"))


def load_prompt(version: str = "v1") -> str:
    """Read one prompt version off disk.

    Raising here rather than falling back to v1 is deliberate: a typo in a
    version name would otherwise silently score the baseline agent twice and
    look like "the change did nothing".
    """
    path = PROMPT_DIR / f"{version}.md"
    if not path.exists():
        available = ", ".join(list_prompt_versions()) or "(none)"
        raise FileNotFoundError(
            f"No prompt version {version!r} at {path}. Available: {available}"
        )
    return _FRONT_COMMENT.sub("", path.read_text()).strip() + "\n"


# The version the Gradio chat serves. v1 is module 4's agent, defect included.
APP_PROMPT_VERSION = os.environ.get("NORTHWIND_PROMPT_VERSION", "v1")


def tool_base_name(name: str) -> str:
    """SDK MCP tools surface as 'mcp__northwind__order_lookup'. Keep the last part."""
    return str(name).split("__")[-1]


def _parse_tool_result(content) -> dict:
    """Tool results arrive as content blocks carrying our JSON payload as text."""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", "") or "")
            else:
                parts.append(getattr(item, "text", "") or "")
        text = "".join(parts)
    else:
        return {}
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return {"raw": text}


async def ask_agent(user_query: str, prompt_version: str = "v1", tools=None) -> dict:
    """Run the agent on one query.

    Returns the response, the trajectory, the tools called, how long it took,
    and which prompt version produced it — everything an evaluator or an
    experiment needs, without a second trip to Phoenix.

    `tools` restricts the toolset to a subset of ALLOWED_TOOLS (the
    agent-as-judge in the last task gets exactly one tool). Leave it None for
    the full twelve.
    """
    options = ClaudeAgentOptions(
        model="claude-haiku-5-5",
        system_prompt=load_prompt(prompt_version),
        mcp_servers={"northwind": northwind_server},
        # `tools=[]` disables the built-in Claude Code toolset (Bash, Read,
        # ToolSearch, ...) entirely — without it, `allowed_tools` only
        # auto-approves the MCP tools on TOP of that default toolset, it
        # doesn't remove it, and a support agent has no business running
        # shell commands. The MCP tools below are all it can call.
        tools=[],
        allowed_tools=ALLOWED_TOOLS if tools is None else list(tools),
        # Non-interactive app: nothing can answer a permission prompt, and
        # every tool here is a local function we wrote ourselves.
        permission_mode="bypassPermissions",
    )

    texts, trajectory, pending = [], [], {}
    started = time.perf_counter()

    async for message in query(prompt=user_query, options=options):
        blocks = getattr(message, "content", None)
        if not isinstance(blocks, list):
            continue
        is_assistant = isinstance(message, AssistantMessage)
        for block in blocks:
            kind = type(block).__name__
            if kind == "TextBlock" and is_assistant:
                texts.append(block.text)
            elif kind == "ToolUseBlock":
                entry = {
                    "tool": tool_base_name(block.name),
                    "args": dict(block.input or {}),
                    "result": None,
                }
                trajectory.append(entry)
                pending[block.id] = entry
            elif kind == "ToolResultBlock":
                entry = pending.get(getattr(block, "tool_use_id", None))
                if entry is not None:
                    entry["result"] = _parse_tool_result(getattr(block, "content", None))

    return {
        "response": "".join(texts),
        "trajectory": trajectory,
        "tools_called": [call["tool"] for call in trajectory],
        "latency_s": round(time.perf_counter() - started, 2),
        "prompt_version": prompt_version,
    }


def format_trajectory(trajectory: list) -> str:
    """Render a trajectory for an LLM judge to read.

    Same shape module 4's judges read, so the rubrics carry over untouched.
    """
    if not trajectory:
        return "  (no tools were called)"
    lines = []
    for step, call in enumerate(trajectory, 1):
        lines.append('  <call step="%d" tool="%s">' % (step, call["tool"]))
        lines.append("    <arguments>%s</arguments>" % json.dumps(call["args"]))
        # Product records run long, and a judge that cannot see the field a
        # claim came from will call a supported claim unsupported. Truncate
        # late enough that the whole tool result is normally visible.
        lines.append("    <result>%s</result>" % json.dumps(call["result"])[:1200])
        lines.append("  </call>")
    return "\n".join(lines)


# --- Gradio interface ------------------------------------------------------
async def chat(message, history):
    run = await ask_agent(message, APP_PROMPT_VERSION)
    return run["response"]


EXAMPLES = [
    # The first two are module 5's opening failure: the catalog has one line of
    # care copy for the sweater and none at all for the jacket. Watch what comes
    # back anyway.
    "How should I wash and dry the merino wool sweater? It's TOP-004.",
    "How do I wash the denim jacket without it fading? It's OUT-001.",
    "Where's my order 4521?",
    "Do you have the Classic Tee in medium?",
    "I'm CUST-001, what's my order history?",
    "I need something warm for winter under $80.",
    "Can I exchange the Denim Jacket from order 4533 for an XL?",
    "I'm CUST-001 and I want to return the shoes I bought last week, order 4521.",
    "refund order 4521 please",
]

demo = gr.ChatInterface(
    chat,
    title="Northwind Apparel — Support Agent",
    description=(
        "Ask about Northwind Apparel products, orders, inventory, exchanges and "
        "refunds. Twelve real tools over a real database; five of them write to "
        f"it. Serving system prompt <b>{APP_PROMPT_VERSION}</b> — restart with "
        "<code>NORTHWIND_PROMPT_VERSION=v3 bash run.sh</code> to serve another."
    ),
    examples=EXAMPLES,
)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

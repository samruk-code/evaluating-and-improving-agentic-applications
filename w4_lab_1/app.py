"""Northwind Apparel support agent — Gradio app, now with real tools.

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

Run Phoenix first (see the Setup step in the instructions), then: bash run.sh
"""

import json
import os

os.environ.pop("PHOENIX_API_KEY", None)
os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
from phoenix.otel import register

# auto_instrument imports openinference's Anthropic instrumentor, which
# reaches into a private SDK module. If that import fails, still start the
# app — a dead Gradio process is what leaves the lab on the starting screen.
try:
    register(
        project_name="dlai-ecommerce-agent",
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
        project_name="dlai-ecommerce-agent",
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
    TextBlock,
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
    "Retrieve a customer profile and their full order history by customer ID "
    "(e.g. CUST-001). Use to verify who you are speaking to.",
    {"customer_id": str},
)
async def get_customer(args):
    return _text(db.get_customer(_conn, args["customer_id"]))


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

SYSTEM_PROMPT = """You are a customer support assistant for Northwind Apparel, an online clothing retailer.

You have tools to search the catalog, look up product details, check inventory, reserve items, build carts and apply coupons, look up orders and their tracking, check the return policy, file exchange requests, retrieve customer records, and process refunds.

POLICY:
- Verify who you are speaking to with get_customer before processing any refund.
- Only refund orders placed within the last 30 days.
- Refund the actual order amount from the order record.
- Check inventory before telling a customer whether an item is in stock.
- Check the return policy before promising a return, refund or exchange.
- Ground product facts in tool results. Do not state a price, fabric, size or availability a tool has not given you.
"""


async def ask_agent(user_query: str) -> str:
    options = ClaudeAgentOptions(
        model="claude-haiku-5-5",
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"northwind": northwind_server},
        # `tools=[]` disables the built-in Claude Code toolset (Bash, Read,
        # ToolSearch, ...) entirely — without it, `allowed_tools` only
        # auto-approves the MCP tools on TOP of that default toolset, it
        # doesn't remove it, and a support agent has no business running
        # shell commands. The twelve MCP tools below are all it can call.
        tools=[],
        allowed_tools=ALLOWED_TOOLS,
        # Non-interactive app: nothing can answer a permission prompt, and
        # every tool here is a local function we wrote ourselves.
        permission_mode="bypassPermissions",
    )
    parts = []
    async for message in query(prompt=user_query, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)
    return "".join(parts)


# --- Gradio interface ------------------------------------------------------
async def chat(message, history):
    return await ask_agent(message)


EXAMPLES = [
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
        "refunds. This agent has real tools now — twelve of them, over a real "
        "database. Five of those tools write to it."
    ),
    examples=EXAMPLES,
)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

"""Northwind Apparel support agent — Gradio app.

This is the same agent used in the Module 1 lab: a small customer-support
agent that retrieves products from a catalog, checks a separate inventory
source, and lets a Claude model answer using ONLY what was retrieved.

Unlike Module 1, tracing is already wired up here — this lab picks up where
Module 1 left off. Arize Phoenix records every retrieval, inventory lookup,
and model call as a span you can inspect in the Phoenix UI or pull into a
dataframe with the Phoenix Python client.

Run Phoenix first (see the Setup step in the instructions), then: bash run.sh
"""

import os

import sitecustomize  # disables FastAPI HTTP traces before Gradio builds its app
import gradio as gr
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)
from phoenix.otel import register

import retrieval

os.environ.pop("PHOENIX_API_KEY", None)
os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
# auto_instrument imports openinference's Anthropic instrumentor, which
# reaches into a private SDK module. If that import fails, still start the
# app — a dead Gradio process is what leaves the lab on the starting screen.
try:
    tracer_provider = register(
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
    tracer_provider = register(
        project_name="dlai-ecommerce-agent",
        auto_instrument=False,
        endpoint="http://localhost:6006/v1/traces",
    )
tracer = tracer_provider.get_tracer("ecommerce-agent")


# Retrieval step: returns the products matched to the query.
@tracer.chain
def search_catalog(user_query: str) -> list:
    return retrieval.search_catalog(user_query)


# Inventory step: looks up live stock for one product id.
@tracer.tool
def check_inventory(product_id: str) -> dict:
    return retrieval.check_inventory(product_id)


def build_context(results: list, stock: dict) -> str:
    """Turn retrieved products + stock into the system-prompt context string."""
    if not results:
        return "RETRIEVED PRODUCTS: (none matched the query)"
    lines = []
    for p in results:
        s = stock.get(p["product_id"], {})
        avail = "in stock" if s.get("in_stock") else "out of stock"
        lines.append(
            f"- {p['name']} ({p['category']}, ${p['price']:.2f}): {p['description']} "
            f"Colors: {', '.join(p['colors'])}. Sizes: {', '.join(p['sizes'])}. "
            f"Inventory: {avail} ({s.get('quantity', 0)} units)."
        )
    return "RETRIEVED PRODUCTS:\n" + "\n".join(lines)


ANSWER_SYSTEM_PROMPT = (
    "You are a customer support assistant for Northwind Apparel, an online "
    "clothing retailer. Answer the customer's question using ONLY the RETRIEVED "
    "PRODUCTS provided below for this turn. Do not use any product knowledge "
    "beyond what is retrieved. If the retrieved products do not match the "
    "question, say you couldn't find a matching product."
)


# The pipeline: retrieve -> check stock for each result -> answer from context.
@tracer.chain
async def ask_agent(user_query: str) -> str:
    results = search_catalog(user_query)
    stock = {doc["product_id"]: check_inventory(doc["product_id"]) for doc in results}

    options = ClaudeAgentOptions(
        model="claude-haiku-5-5",
        system_prompt=ANSWER_SYSTEM_PROMPT + "\n\n" + build_context(results, stock),
        allowed_tools=[],
        permission_mode="default",
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
    "What colors does the Classic Tee come in?",
    "How much is the Wool Beanie?",
    "Heading on a road trip soon, anything to help organize my trunk?",
    "I need something to keep my head warm in winter.",
    "Can I get the Classic Tee in medium, and is it in stock?",
]

demo = gr.ChatInterface(
    chat,
    title="Northwind Apparel — Support Agent",
    description=(
        "Ask about Northwind Apparel products. Each answer is grounded only in "
        "what the retriever pulls back for that question."
    ),
    examples=EXAMPLES,
)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

import sys
from pathlib import Path
import uuid
import functools
import json
import pandas as pd
from IPython.display import Markdown, display, HTML
from phoenix.otel import register

# register before importing claude_agent_sdk ensures that the tracking wrappers attach to the agent loop correctly
tracer_provider = register(
    project_name="dlai-ecommerce-agent",
    auto_instrument=True,
    endpoint="http://localhost:6006/v1/traces",
)


# Make the apparel shop agent package importable
PACKAGE_ROOT = Path("apparel-shop-agent").resolve()
SRC_PATH = PACKAGE_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from apparel_agent.agent.llm_agent import LLMAgent
from apparel_agent.data.database import (
    create_seeded_connection,
    list_table_names,
    table_rows,
)
from apparel_agent.data.repository import ApparelRepository
from apparel_agent.schemas.domain import AgentResult
from apparel_agent.tools.tool_registry import ToolSpec, build_tool_registry

DB_PATH = Path("apparel_shop_lab.sqlite")
connection = create_seeded_connection(DB_PATH, reset=True)

TABLE_ORDER = [
    "products",
    "product_colors",
    "product_sizes",
    "inventory",
    "orders",
    "order_items",
    "tracking_events",
    "coupons",
    "carts",
    "cart_items",
    "reservations",
    "exchange_requests",
]

TABLE_DESCRIPTIONS = {
    "products": "Catalog product facts, including descriptions and care instructions.",
    "product_colors": "All color options for each product.",
    "product_sizes": "All size options for each product.",
    "inventory": "Live stock by product, size, and store.",
    "orders": "Existing customer orders and shipment summary fields.",
    "order_items": "Line items attached to each order.",
    "tracking_events": "Timestamped shipment updates for orders.",
    "coupons": "Available coupon codes and discount rates.",
    "carts": "Carts created while the agent is running.",
    "cart_items": "Items added to carts while the agent is running.",
    "reservations": "Pickup reservations created while the agent is running.",
    "exchange_requests": "Exchange requests created while the agent is running.",
}


def show_phoenix_link(jupyter_port=8888, phoenix_port=6006):
    box_id = f"phoenix-link-box-{uuid.uuid4().hex}"
    display(HTML(f"""
    <div id="{box_id}" style="
        padding: 12px;
        border: 1px solid #ddd;
        border-radius: 8px;
        background: #f8f8f8;
        font-family: sans-serif;
    ">
      Preparing Phoenix link...
    </div>

    <script>
    (function() {{
        const current = new URL(window.location.href);
        let phoenixUrl;

        const jupyterPortPattern = "p{jupyter_port}";
        const phoenixPortPattern = "p{phoenix_port}";

        if (current.hostname.includes(jupyterPortPattern)) {{
            // DLAI-style URL:
            // s172-18-43-147p8888.lab-aws-staging.deeplearning.ai
            // ->
            // s172-18-43-147p6006.lab-aws-staging.deeplearning.ai
            const phoenixHost = current.hostname.replace(
                jupyterPortPattern,
                phoenixPortPattern
            );

            phoenixUrl = current.protocol + "//" + phoenixHost + "/";
        }} else {{
            // Fallback:
            // hostname + :6006
            //
            // Example:
            // https://some-host.example.com/notebooks/foo.ipynb
            // ->
            // https://some-host.example.com:6006/
            phoenixUrl = current.protocol + "//" + current.hostname + ":{phoenix_port}/";
        }}

        const box = document.getElementById("{box_id}");
        box.innerHTML = `
            <strong>Phoenix traces:</strong><br>
            <a href="${{phoenixUrl}}" target="_blank" rel="noopener noreferrer">
                Open Phoenix UI
            </a>
            <br>
            <small>${{phoenixUrl}}</small>
        `;
    }})();
    </script>
    """))
    

def display_tables():
    existing_tables = set(list_table_names(connection))
    for table_name in TABLE_ORDER:
        if table_name not in existing_tables:
            continue
        rows = table_rows(connection, table_name)
        display(
            Markdown(
                f"### `{table_name}` ({len(rows)} rows)\n{TABLE_DESCRIPTIONS[table_name]}"
            )
        )
        if rows:
            display(pd.DataFrame(rows))
        else:
            display(Markdown("_No rows yet._"))


def instrument_tool(tracer, spec: ToolSpec) -> ToolSpec:
    @functools.wraps(spec.func)
    def traced_func(*args, **kwargs):
        with tracer.start_as_current_span(spec.name) as span:
            span.set_attribute("openinference.span.kind", "TOOL")
            span.set_attribute("tool.name", spec.name)
            span.set_attribute("input.value", json.dumps(kwargs, default=str))
            span.set_attribute("input.mime_type", "application/json")

            result = spec.func(*args, **kwargs)

            span.set_attribute("output.value", json.dumps(result, default=str))
            span.set_attribute("output.mime_type", "application/json")
            return result

    return ToolSpec(
        name=spec.name,
        description=spec.description,
        input_schema=spec.input_schema,
        func=traced_func,
    )


repo = ApparelRepository(connection=connection)
tool_registry = build_tool_registry(repo)


tracer = tracer_provider.get_tracer("ecommerce-agent")

traced_tool_registry = {
    name: instrument_tool(tracer, spec) for name, spec in tool_registry.items()
}

agent = LLMAgent(
    traced_tool_registry,
    model_name="claude-haiku-4-5-20251001",
    temperature=0.0,
)


@tracer.chain
def ask_agent(user_query: str):
    response = agent.run(user_query)
    return response.final_answer

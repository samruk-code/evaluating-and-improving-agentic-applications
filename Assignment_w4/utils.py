import ast
import json

import sys
from pathlib import Path

from phoenix.client import Client
from tqdm.auto import tqdm
import pandas as pd
from IPython.display import Markdown, display,HTML
from phoenix.otel import register
import uuid

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
    "customers",
    "orders",
    "order_items",
    "tracking_events",
    "coupons",
    "carts",
    "cart_items",
    "reservations",
    "exchange_requests",
    "refunds",
]

TABLE_DESCRIPTIONS = {
    "products": "Catalog product facts, including descriptions and care instructions.",
    "product_colors": "All color options for each product.",
    "product_sizes": "All size options for each product.",
    "inventory": "Live stock by product, size, and store.",
    "customers": "Customer profiles used for identity verification before refunds.",
    "orders": "Existing customer orders, including the 4521/4512 transposition pair and 45-day-old 4530.",
    "order_items": "Line items attached to each order.",
    "tracking_events": "Timestamped shipment updates for orders.",
    "coupons": "Available coupon codes and discount rates.",
    "carts": "Carts created while the agent is running.",
    "cart_items": "Items added to carts while the agent is running.",
    "reservations": "Pickup reservations created while the agent is running.",
    "exchange_requests": "Exchange requests created while the agent is running.",
    "refunds": "Refund records written by process_refund. Empty at seed time.",
}


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


def client_init(project_name="dlai-ecommerce-agent"):
    # Instantiate the client
    phoenix_client = Client()

    # Check if the project already exists (this is useful in case you restart the kernel or want a fresh project)
    try:
        phoenix_client.projects.get(project_name=project_name)
    except:
        pass # Pass if it doesn't exist
    else:
        phoenix_client.projects.delete(project_name=project_name) # Delete if it does exist

    return phoenix_client
    

def instrument_tool(spec: ToolSpec) -> ToolSpec:
    traced_func = tracer.tool(spec.func, name=spec.name)
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
    name: instrument_tool(spec) for name, spec in tool_registry.items()
}

agent = LLMAgent(
    tool_registry,
    model_name="claude-haiku-4-5-20251001",
    temperature=0.0,
    weak_prompt_mode=False,
)


@tracer.chain
def ask_agent(user_query: str):
    return agent.run(user_query)


def run_batch(queries):
    # Iterates through the query list sequentially, updating a progress bar for each item
    for q in tqdm(queries, desc="Processing queries"):
        response = ask_agent(q)
        response = response.final_answer
        truncated = response[:150] + ("..." if len(response) > 150 else "")
        print(f"Q: {q}\nA: {truncated}\n{'-' * 60}")


def get_agent_and_tool_spans(client, project_name):
    # Get spans from Phoenix client in dataframe format
    all_spans = client.spans.get_spans_dataframe(project_identifier=project_name)

    # Get spans without a parent (copy original df)
    parent_spans = all_spans[all_spans["parent_id"].isna()].copy()

    # Check that the spans are not empty
    if not parent_spans.empty:
        # Rename columns
        parent_spans = parent_spans.rename(
            columns={
                "attributes.input.value": "input",
                "attributes.output.value": "output",
            },
        )

        parent_spans = parent_spans[["input", "output", "context.span_id"]].reset_index(drop=True)

    has_tool_finish = all_spans['attributes.llm.finish_reason'].isin(['tool_use', 'tool_calls'])
    has_tool_content = all_spans['attributes.llm.output_messages'].astype(str).str.contains('tool_call', case=False, na=False)

    # Overwrite all_spans directly
    tool_spans = all_spans[has_tool_finish | has_tool_content].copy()

    return parent_spans, tool_spans


def extract_tool_name(row):
    """Extract tool name from attributes.llm.output_messages on LLM spans."""
    output_msgs = row.get("attributes.llm.output_messages")
    if not output_msgs:
        return row.get("attributes.tool.name") or row.get("name")
    
    # Parse string representation if necessary
    if isinstance(output_msgs, str):
        try:
            output_msgs = json.loads(output_msgs)
        except Exception:
            try:
                output_msgs = ast.literal_eval(output_msgs)
            except Exception:
                return row.get("name")

    # Extract function name from tool_calls structure
    try:
        if isinstance(output_msgs, list) and len(output_msgs) > 0:
            tool_calls = output_msgs[0].get("message.tool_calls", [])
            if tool_calls and len(tool_calls) > 0:
                return tool_calls[0].get("tool_call.function.name")
    except Exception:
        pass

    return row.get("attributes.tool.name") or row.get("name")


def parse_json(value):
    try:
        return json.loads(value)
    except Exception:
        return {}

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

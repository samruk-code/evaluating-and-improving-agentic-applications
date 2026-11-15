# Northwind Apparel agent

`apparel-shop-agent` is an educational, database-backed support agent for Northwind Apparel. It models a 20-product clothing catalog where an assistant can search products, check inventory, reserve items, create carts, apply coupons, look up existing orders, read shipment tracking, check return policy, and create exchange requests.

## Architecture

```text
CLI or notebook
  |
  v
Agent factory
  |-----------------------------|
  v                             v
DeterministicAgent          LLMAgent + Anthropic Messages API
  |                             |
  |                             v
  |                         Tool loop
  |                             |
  v                             v
Tool registry ------------> Python tools
                                |
                                v
                         ApparelRepository
                                |
                                v
                         SQLite database
```

The repository seeds SQL tables for the Northwind Apparel catalog, product sizes, inventory, orders, order items, tracking events, coupons, reservations, carts, and exchange requests. SQLite is used for the lab runtime because it needs no external service, while the schema and repository boundary mirror the same pattern you would use with MySQL.

Exact transcript test prompts are also stored in `data/transcript_test_cases.json`. `LLMAgent` checks that file before making a model call: matching prompts return deterministic fixture outputs, while all other prompts call Claude normally.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

`ANTHROPIC_API_KEY` is required only for LLM mode. Scripted deterministic mode and tests do not perform network calls.

## Run The Demo

Scripted deterministic mode:

```bash
python -m apparel_agent.main --deterministic
```

LLM mode:

```bash
export ANTHROPIC_API_KEY="..."
python -m apparel_agent.main
```

Run one custom prompt:

```bash
python -m apparel_agent.main --prompt "Where is order ORD-1002?"
```

## Tests

```bash
pytest
```

## Package Layout

```text
src/apparel_agent/
  config.py
  main.py
  data/
  tools/
  agent/
  llm/
  observability/
  scenarios/
  schemas/
tests/
```


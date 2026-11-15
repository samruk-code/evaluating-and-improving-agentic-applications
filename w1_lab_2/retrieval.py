"""A deliberately simple retrieval system for the Northwind Apparel agent.

This module replaces the old "dump the whole catalog into the system prompt"
approach. The agent no longer sees the catalog directly; it only ever sees the
products that `search_catalog` decides to return for a given query, plus the
stock numbers that `check_inventory` looks up from a separate inventory source.

The matcher is intentionally naive (token substring overlap).
"""

import json
import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_MIN_TOKEN_LEN = 4


def load_catalog(path="catalog.json"):
    with open(path) as f:
        return json.load(f)


def load_inventory(path="inventory.json"):
    with open(path) as f:
        return json.load(f)


def _tokens(text):
    return [t for t in _TOKEN_RE.findall(text.lower()) if len(t) >= _MIN_TOKEN_LEN]


def _fuzzy_match(a, b):
    # Bidirectional substring match so "trunk" matches "trunks" and
    # "raincoats" matches "raincoat". This loose matching is exactly what
    # lets the wrong product sneak into the results.
    return a in b or b in a


def _weighted_fields(product):
    # Name matches count most, then category, then the descriptive text.
    return [
        (product["name"], 3),
        (product["category"], 2),
        (product["description"], 1),
        (" ".join(product["colors"]), 1),
    ]


def search_catalog(query, catalog=None, top_k=3):
    """Return the top-k catalog products that loosely match the query.

    Each result carries enough detail (price, colors, sizes, description) for
    the agent to answer from it, plus the raw match `score`.
    """
    catalog = catalog if catalog is not None else load_catalog()
    query_tokens = _tokens(query)

    scored = []
    for product in catalog:
        score = 0
        for text, weight in _weighted_fields(product):
            field_tokens = _tokens(text)
            for qt in query_tokens:
                if any(_fuzzy_match(qt, ft) for ft in field_tokens):
                    score += weight
        if score > 0:
            scored.append((score, product))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    results = []
    for score, product in scored[:top_k]:
        results.append(
            {
                "product_id": product["product_id"],
                "name": product["name"],
                "category": product["category"],
                "price": product["price"],
                "description": product["description"],
                "colors": product["colors"],
                "sizes": product["sizes"],
                "score": score,
            }
        )
    return results


def check_inventory(product_id, inventory=None):
    """Look up live stock for a product from the inventory source of truth."""
    inventory = inventory if inventory is not None else load_inventory()
    record = inventory.get(product_id)
    if record is None:
        return {"product_id": product_id, "found": False, "in_stock": False, "quantity": 0}
    quantity = record.get("quantity", 0)
    return {
        "product_id": product_id,
        "found": True,
        "in_stock": quantity > 0,
        "quantity": quantity,
    }

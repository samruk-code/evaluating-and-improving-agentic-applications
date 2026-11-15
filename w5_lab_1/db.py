"""Northwind Apparel's ground-truth database, as a real SQLite file.

Unlike the notebook this lab mirrors, `app.py` (the long-running Gradio
process) and the short-lived scripts OpenCode writes during the lab are
separate OS processes — they can't share an in-memory sqlite connection the
way one notebook kernel can. So this module opens a real file, `northwind.db`,
in the current working directory (the workspace root). Every process that
calls `get_connection()` sees the same tables, including whatever
`process_refund` and the other writing tools already wrote — which is the
whole point of the outcome evaluator in Task 3: it goes and asks this file
what actually happened, not the agent's trace or its words.

The schema is the full apparel-shop model: a catalog with per-product colors
and sizes, per-size/per-store inventory, orders split into header and line
items, shipment tracking events, coupons, and the four tables the writing
tools create rows in (carts/cart_items, reservations, exchange_requests,
refunds). Read-heavy tools have somewhere real to read from, and every write
tool leaves a row behind that an outcome evaluator can go check.

Seeding rules, which matter for reproducibility:

- The catalog, inventory, customers, orders, tracking events and coupons are
  seeded once, by the first process to open a fresh `northwind.db`.
- `carts`, `cart_items`, `reservations`, `exchange_requests` and `refunds`
  are *never* seeded or reset. They start empty and only ever grow via real
  tool calls, across every process and every restart of the app.
- `SCHEMA_VERSION` guards against a stale `northwind.db` from an earlier
  version of this lab: if the file on disk was built by a different schema,
  `initialize()` drops it and rebuilds rather than failing on a missing column.

Carried forward from module 4 with three changes, all of them module 5\'s:
`get_customer` now accepts an email address as well as a customer ID; orders
4551 and 4544 join the fixtures (an in-window refund and the merino wool
sweater); and `reset_refunds` / `set_care` / `care_snapshot` support running
experiments against shared state.

One thing that is *not* a change, and is the whole setup for this module: the
`care` column is empty for nineteen of the twenty products. Only TOP-004, the
merino wool Crew Neck Sweater, has care copy written. Nobody ever filled the
rest in — an ordinary state for a real product catalog, and the reason the
agent has a gap to paper over.
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "northwind.db"

# Bump this whenever a CREATE TABLE below changes shape. Any northwind.db
# stamped with a different value is rebuilt from scratch on next open.
SCHEMA_VERSION = 3

DEFAULT_STORE_ID = "STORE-001"
RETURN_WINDOW_DAYS = 30

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS schema_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        color TEXT NOT NULL,
        fabric TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        price REAL NOT NULL,
        available INTEGER NOT NULL,
        returnable INTEGER NOT NULL,
        final_sale INTEGER NOT NULL,
        care TEXT NOT NULL DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS product_colors (
        product_id TEXT NOT NULL,
        color TEXT NOT NULL,
        PRIMARY KEY (product_id, color),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS product_sizes (
        product_id TEXT NOT NULL,
        size TEXT NOT NULL,
        PRIMARY KEY (product_id, size),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS inventory (
        product_id TEXT NOT NULL,
        size TEXT NOT NULL,
        store_id TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        PRIMARY KEY (product_id, size, store_id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        email TEXT NOT NULL,
        status TEXT NOT NULL,
        amount REAL NOT NULL,
        order_date TEXT NOT NULL,
        tracking_number TEXT NOT NULL DEFAULT '',
        carrier TEXT NOT NULL DEFAULT '',
        estimated_delivery TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS order_items (
        order_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        size TEXT NOT NULL,
        delivered_days_ago INTEGER NOT NULL,
        PRIMARY KEY (order_id, product_id, size),
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tracking_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT NOT NULL,
        event_time TEXT NOT NULL,
        status TEXT NOT NULL,
        location TEXT NOT NULL,
        message TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS coupons (
        code TEXT PRIMARY KEY,
        discount_rate REAL NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        size TEXT NOT NULL,
        store_id TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS carts (
        cart_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        coupon_code TEXT,
        discount REAL NOT NULL DEFAULT 0,
        subtotal REAL NOT NULL,
        total REAL NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cart_items (
        cart_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        name TEXT NOT NULL,
        size TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        line_total REAL NOT NULL,
        FOREIGN KEY (cart_id) REFERENCES carts(cart_id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS exchange_requests (
        exchange_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        new_size TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS refunds (
        refund_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT NOT NULL,
        amount REAL NOT NULL,
        reason TEXT NOT NULL
    )
    """,
]

# Tables the agent's writing tools own. Seeded never, reset never — whatever
# is in here is something a real tool call put there.
AGENT_WRITTEN_TABLES = ("carts", "cart_items", "reservations", "exchange_requests", "refunds")


# --- seed data -------------------------------------------------------------

PRODUCTS = [
    {
        "id": "TEE-001",
        "name": "Classic Tee",
        "category": "tops",
        "color": "white",
        "colors": ["white", "black", "navy", "heather gray"],
        "fabric": "combed cotton",
        "description": "100% combed cotton crew-neck t-shirt. Pre-shrunk, soft hand feel.",
        "sizes": ["XS", "S", "M", "L", "XL"],
        "price": 24.99,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "SHO-001",
        "name": "Trail Runner",
        "category": "shoes",
        "color": "black",
        "colors": ["black", "gray"],
        "fabric": "synthetic mesh",
        "description": "Lightweight trail running shoe with rock plate and aggressive lug pattern.",
        "sizes": ["7", "8", "9", "10", "11", "12"],
        "price": 89.99,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "SHO-002",
        "name": "Court Shoe",
        "category": "shoes",
        "color": "white",
        "colors": ["white", "black"],
        "fabric": "canvas and rubber",
        "description": "Low-profile court shoe with gum rubber outsole. Good for tennis and casual wear.",
        "sizes": ["7", "8", "9", "10", "11", "12"],
        "price": 74.99,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "SHO-003",
        "name": "Slip-On Canvas",
        "category": "shoes",
        "color": "navy",
        "colors": ["navy", "gray"],
        "fabric": "canvas",
        "description": "Canvas slip-on shoe with elastic side panels. Easy on, easy off.",
        "sizes": ["7", "8", "9", "10", "11"],
        "price": 55.00,
        "available": False,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "OUT-001",
        "name": "Denim Jacket",
        "category": "outerwear",
        "color": "blue",
        "colors": ["blue", "black"],
        "fabric": "cotton denim",
        "description": "Classic trucker-style denim jacket. Button front, chest pockets.",
        "sizes": ["S", "M", "L", "XL"],
        "price": 98.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "OUT-002",
        "name": "Raincoat",
        "category": "outerwear",
        "color": "yellow",
        "colors": ["yellow", "navy"],
        "fabric": "waterproof nylon",
        "description": "Waterproof hooded raincoat with sealed seams and cinch waist.",
        "sizes": ["S", "M", "L"],
        "price": 125.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "OUT-003",
        "name": "Fleece Pullover",
        "category": "outerwear",
        "color": "heather gray",
        "colors": ["heather gray", "navy", "olive"],
        "fabric": "polyester fleece",
        "description": "Quarter-zip midweight fleece pullover. Chest pocket.",
        "sizes": ["S", "M", "L", "XL"],
        "price": 68.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "TOP-002",
        "name": "Oxford Shirt",
        "category": "tops",
        "color": "white",
        "colors": ["white", "blue", "pink"],
        "fabric": "Oxford cotton",
        "description": "Button-down Oxford cloth shirt with chest pocket. Classic fit.",
        "sizes": ["S", "M", "L", "XL"],
        "price": 68.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "TOP-003",
        "name": "Hooded Sweatshirt",
        "category": "tops",
        "color": "gray",
        "colors": ["gray", "black", "forest green"],
        "fabric": "cotton blend",
        "description": "Midweight cotton-blend hoodie with kangaroo pocket and drawcord hood.",
        "sizes": ["S", "M", "L", "XL"],
        "price": 54.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "TOP-004",
        "name": "Crew Neck Sweater",
        "category": "tops",
        "color": "cream",
        "colors": ["cream", "charcoal", "burgundy"],
        "fabric": "merino wool",
        "description": "Merino wool crew-neck sweater. Machine washable on wool cycle.",
        "sizes": ["S", "M", "L", "XL"],
        "price": 72.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "Machine washable on wool cycle.",
    },
    {
        "id": "TOP-005",
        "name": "Flannel Shirt",
        "category": "tops",
        "color": "red plaid",
        "colors": ["red plaid", "green plaid", "blue plaid"],
        "fabric": "brushed cotton flannel",
        "description": "Brushed cotton flannel button-up. Two chest pockets.",
        "sizes": ["S", "M", "L", "XL"],
        "price": 62.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "BOT-001",
        "name": "Chino Pants",
        "category": "bottoms",
        "color": "khaki",
        "colors": ["khaki", "navy", "olive"],
        "fabric": "stretch cotton twill",
        "description": "Straight-fit cotton chinos with slight stretch. Unwashed, expect some shrinkage.",
        "sizes": ["30x30", "32x32", "34x32", "36x34"],
        "price": 58.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "BOT-002",
        "name": "Cargo Shorts",
        "category": "bottoms",
        "color": "khaki",
        "colors": ["khaki", "olive", "black"],
        "fabric": "cotton canvas",
        "description": "9-inch inseam cargo shorts with side utility pockets.",
        "sizes": ["30", "32", "34", "36"],
        "price": 38.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "BOT-003",
        "name": "Swim Trunks",
        "category": "bottoms",
        "color": "navy",
        "colors": ["navy", "coral", "teal"],
        "fabric": "quick-dry polyester",
        "description": "5-inch inseam quick-dry swim trunks with mesh liner.",
        "sizes": ["S", "M", "L", "XL"],
        "price": 34.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "ACC-001",
        "name": "Leather Belt",
        "category": "accessories",
        "color": "brown",
        "colors": ["brown", "black"],
        "fabric": "full-grain leather",
        "description": "Full-grain leather belt with brushed-nickel buckle.",
        "sizes": ["30", "32", "34", "36"],
        "price": 42.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "ACC-002",
        "name": "Wool Beanie",
        "category": "accessories",
        "color": "black",
        "colors": ["black", "gray", "navy", "oatmeal"],
        "fabric": "merino wool",
        "description": "Cuffed merino-wool beanie. One size fits most.",
        "sizes": ["one size"],
        # 19.99, not the apparel-shop package's 22.00: order 4512's amount is
        # pinned by query_spec.py, and a catalog price that disagrees with the
        # order it appears in is a trap the lab isn't trying to set.
        "price": 19.99,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "ACC-003",
        "name": "Canvas Backpack",
        "category": "accessories",
        "color": "black",
        "colors": ["black", "olive", "navy"],
        "fabric": "waxed canvas",
        "description": "18L waxed canvas backpack with leather trim and laptop sleeve.",
        "sizes": ["one size"],
        "price": 78.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "ACC-004",
        "name": "Leather Wallet",
        "category": "accessories",
        "color": "brown",
        "colors": ["brown", "black"],
        "fabric": "leather",
        "description": "Bifold leather wallet with six card slots and bill compartment.",
        "sizes": ["one size"],
        "price": 45.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "ACC-005",
        "name": "Cotton Socks (3-pack)",
        "category": "accessories",
        "color": "white",
        "colors": ["white", "black"],
        "fabric": "cotton",
        "description": "Ribbed crew-length cotton socks. Sold in packs of three.",
        "sizes": ["M", "L"],
        "price": 16.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
    {
        "id": "ACC-006",
        "name": "Trouser Socks",
        "category": "accessories",
        "color": "black",
        "colors": ["black", "gray", "navy"],
        "fabric": "merino blend",
        "description": "Mid-calf dress socks in fine merino blend.",
        "sizes": ["M", "L"],
        "price": 12.00,
        "available": True,
        "returnable": True,
        "final_sale": False,
        "care": "",
    },
]

CUSTOMERS = [
    ("CUST-001", "Dana Whitfield", "dana@example.com"),
    ("CUST-002", "Ravi Patel", "ravi@example.com"),
    ("CUST-003", "Mei Ling", "mei@example.com"),
    ("CUST-123", "Jordan Avery", "customer@example.com"),
    ("CUST-456", "Alex Romero", "alex@example.com"),
]

COUPONS = {
    "WELCOME10": 0.10,
    "DINNER15": 0.15,
}


def _ago(days: int) -> str:
    return str(date.today() - timedelta(days=days))


def _build_inventory() -> list[dict]:
    """One row per (product, size) at STORE-001. Out-of-stock products get 0."""
    quantity_overrides = {
        "TEE-001": 42,
        "SHO-003": 0,
    }
    inventory = []
    for product in PRODUCTS:
        quantity = quantity_overrides.get(product["id"], 10 if product["available"] else 0)
        for size in product["sizes"]:
            inventory.append(
                {
                    "product_id": product["id"],
                    "size": size,
                    "store_id": DEFAULT_STORE_ID,
                    "quantity": quantity,
                }
            )
    return inventory


INVENTORY = _build_inventory()


def _build_orders() -> list[dict]:
    """The order fixtures, header plus line items.

    4521 and 4512 are one transposition apart, and both are real — the
    invocation trap query_spec.py's "wrong order" cases are built around.
    4530 sits deliberately outside the 30-day window, so the correct answer
    to a refund request on it is a refusal.

    `amount` is the order total and always agrees with the line items' catalog
    prices; the refund policy in the system prompt tells the agent to refund
    this figure, so it has to be the one a checking evaluator would compute.
    """
    return [
        {
            "order_id": "4521",
            "customer_id": "CUST-001",
            "email": "dana@example.com",
            "status": "delivered",
            "amount": 89.99,
            "order_date": _ago(6),
            "tracking_number": "1Z999AA10123456784",
            "carrier": "UPS",
            "estimated_delivery": _ago(2),
            "items": [{"product_id": "SHO-001", "size": "10", "delivered_days_ago": 2}],
        },
        {
            "order_id": "4512",
            "customer_id": "CUST-002",
            "email": "ravi@example.com",
            "status": "shipped",
            "amount": 19.99,
            "order_date": _ago(3),
            "tracking_number": "9400111202555012345678",
            "carrier": "USPS",
            "estimated_delivery": _ago(-1),
            "items": [{"product_id": "ACC-002", "size": "one size", "delivered_days_ago": 0}],
        },
        {
            # 45 days old: outside the return window on every reading.
            "order_id": "4530",
            "customer_id": "CUST-001",
            "email": "dana@example.com",
            "status": "delivered",
            "amount": 24.99,
            "order_date": _ago(45),
            "tracking_number": "1Z999AA10123456791",
            "carrier": "UPS",
            "estimated_delivery": _ago(41),
            "items": [{"product_id": "TEE-001", "size": "M", "delivered_days_ago": 41}],
        },
        {
            # Module 5's in-window refund case: recent, delivered, refundable.
            "order_id": "4551",
            "customer_id": "CUST-002",
            "email": "ravi@example.com",
            "status": "delivered",
            "amount": 98.00,
            "order_date": _ago(4),
            "tracking_number": "1Z999AA10123456824",
            "carrier": "UPS",
            "estimated_delivery": _ago(1),
            "items": [{"product_id": "OUT-001", "size": "M", "delivered_days_ago": 1}],
        },
        {
            # The merino wool sweater, ordered. The care question module 5 opens
            # with is about this product; TOP-004 is the one product in the whole
            # catalog whose `care` field was ever filled in.
            "order_id": "4544",
            "customer_id": "CUST-003",
            "email": "mei@example.com",
            "status": "delivered",
            "amount": 72.00,
            "order_date": _ago(9),
            "tracking_number": "9400111202555012345705",
            "carrier": "USPS",
            "estimated_delivery": _ago(5),
            "items": [{"product_id": "TOP-004", "size": "L", "delivered_days_ago": 5}],
        },
        {
            "order_id": "4533",
            "customer_id": "CUST-003",
            "email": "mei@example.com",
            "status": "delivered",
            "amount": 98.00,
            "order_date": _ago(12),
            "tracking_number": "1Z999AA10123456802",
            "carrier": "UPS",
            "estimated_delivery": _ago(8),
            "items": [{"product_id": "OUT-001", "size": "L", "delivered_days_ago": 8}],
        },
        {
            "order_id": "4540",
            "customer_id": "CUST-002",
            "email": "ravi@example.com",
            "status": "processing",
            "amount": 54.00,
            "order_date": _ago(1),
            "tracking_number": "",
            "carrier": "",
            "estimated_delivery": _ago(-5),
            "items": [{"product_id": "TOP-003", "size": "L", "delivered_days_ago": 0}],
        },
        {
            # Multi-item order: check_return_policy has to pick the right line.
            "order_id": "ORD-1001",
            "customer_id": "CUST-123",
            "email": "customer@example.com",
            "status": "delivered",
            "amount": 44.98,
            "order_date": _ago(18),
            "tracking_number": "1Z999AA10123456813",
            "carrier": "UPS",
            "estimated_delivery": _ago(12),
            "items": [
                {"product_id": "TEE-001", "size": "M", "delivered_days_ago": 12},
                {"product_id": "ACC-002", "size": "one size", "delivered_days_ago": 12},
            ],
        },
        {
            "order_id": "ORD-1002",
            "customer_id": "CUST-456",
            "email": "alex@example.com",
            "status": "in_transit",
            "amount": 74.99,
            "order_date": _ago(6),
            "tracking_number": "9400111202555012345691",
            "carrier": "USPS",
            "estimated_delivery": _ago(-2),
            "items": [{"product_id": "SHO-002", "size": "12", "delivered_days_ago": 0}],
        },
    ]


def _build_tracking_events() -> list[dict]:
    return [
        {
            "order_id": "4521",
            "event_time": f"{_ago(5)} 09:20",
            "status": "shipped",
            "location": "Mesa, AZ",
            "message": "Package left the fulfillment center.",
        },
        {
            "order_id": "4521",
            "event_time": f"{_ago(2)} 15:45",
            "status": "delivered",
            "location": "Austin, TX",
            "message": "Package delivered to the front door.",
        },
        {
            "order_id": "4512",
            "event_time": f"{_ago(3)} 08:10",
            "status": "label_created",
            "location": "Los Angeles, CA",
            "message": "Shipping label created.",
        },
        {
            "order_id": "4512",
            "event_time": f"{_ago(1)} 19:35",
            "status": "in_transit",
            "location": "Denver, CO",
            "message": "Package arrived at a regional facility.",
        },
        {
            "order_id": "4530",
            "event_time": f"{_ago(41)} 11:02",
            "status": "delivered",
            "location": "Austin, TX",
            "message": "Package delivered to the front door.",
        },
        {
            "order_id": "4533",
            "event_time": f"{_ago(8)} 13:27",
            "status": "delivered",
            "location": "Seattle, WA",
            "message": "Package delivered to the mail room.",
        },
        {
            "order_id": "4551",
            "event_time": f"{_ago(1)} 16:12",
            "status": "delivered",
            "location": "Los Angeles, CA",
            "message": "Package delivered to the front door.",
        },
        {
            "order_id": "4544",
            "event_time": f"{_ago(5)} 10:48",
            "status": "delivered",
            "location": "Seattle, WA",
            "message": "Package delivered to the mail room.",
        },
        {
            "order_id": "ORD-1001",
            "event_time": f"{_ago(15)} 09:20",
            "status": "shipped",
            "location": "Mesa, AZ",
            "message": "Package left the fulfillment center.",
        },
        {
            "order_id": "ORD-1001",
            "event_time": f"{_ago(12)} 15:45",
            "status": "delivered",
            "location": "Austin, TX",
            "message": "Package delivered to the front door.",
        },
        {
            "order_id": "ORD-1002",
            "event_time": f"{_ago(5)} 08:10",
            "status": "label_created",
            "location": "Los Angeles, CA",
            "message": "Shipping label created.",
        },
        {
            "order_id": "ORD-1002",
            "event_time": f"{_ago(2)} 19:35",
            "status": "in_transit",
            "location": "Denver, CO",
            "message": "Package arrived at a regional facility.",
        },
    ]


# --- tool return envelopes -------------------------------------------------
#
# Every function below returns a dict with a `success` key. The tools in
# app.py hand it straight back to the model as JSON, so a failure is a normal
# tool result the agent has to read and react to — not an exception that
# breaks the run and shows up as an empty span.


def ok(**kwargs: Any) -> dict:
    return {"success": True, **kwargs}


def fail(reason: str, **kwargs: Any) -> dict:
    return {"success": False, "reason": reason, **kwargs}


# --- connection / seeding --------------------------------------------------


def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # safe concurrent reads while app.py holds a writer open
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Open a fresh connection to the (already-initialized) database file.

    Use this from short-lived scripts (evaluators) that just need to read —
    `initialize()` is what creates/seeds the file; scripts that run after the
    app has already started can assume it exists and just connect.
    """
    return connect(db_path)


def initialize(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Create the schema if missing, seed ground-truth tables once, return a connection.

    Safe to call from every process/script that touches the database — the
    schema statements are idempotent, and the ground-truth seed only runs if
    the products table is still empty. The tables the agent writes to are
    never seeded and never reset.
    """
    conn = connect(db_path)

    if _stale_schema(conn):
        _drop_all_tables(conn)

    for statement in SCHEMA:
        conn.execute(statement)
    conn.execute(
        "INSERT OR REPLACE INTO schema_meta (key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()

    if conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"] == 0:
        _seed(conn)

    return conn


def _stale_schema(conn: sqlite3.Connection) -> bool:
    """True when the file on disk was built by a different version of this module."""
    tables = {row["name"] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    )}
    if not tables:
        return False  # brand new file
    if "schema_meta" not in tables:
        return True  # pre-versioning layout
    row = conn.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'").fetchone()
    return row is None or row["value"] != str(SCHEMA_VERSION)


def _drop_all_tables(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall():
            conn.execute(f"DROP TABLE IF EXISTS {row['name']}")
        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def _seed(conn: sqlite3.Connection) -> None:
    for product in PRODUCTS:
        conn.execute(
            """
            INSERT INTO products
            (id, name, category, color, fabric, description, price, available, returnable, final_sale, care)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["id"],
                product["name"],
                product["category"],
                product["color"],
                product["fabric"],
                product["description"],
                product["price"],
                int(product["available"]),
                int(product["returnable"]),
                int(product["final_sale"]),
                product["care"],
            ),
        )
        conn.executemany(
            "INSERT INTO product_colors (product_id, color) VALUES (?, ?)",
            [(product["id"], color) for color in product["colors"]],
        )
        conn.executemany(
            "INSERT INTO product_sizes (product_id, size) VALUES (?, ?)",
            [(product["id"], size) for size in product["sizes"]],
        )

    conn.executemany(
        """
        INSERT INTO inventory (product_id, size, store_id, quantity)
        VALUES (:product_id, :size, :store_id, :quantity)
        """,
        INVENTORY,
    )
    conn.executemany("INSERT INTO customers (customer_id, name, email) VALUES (?, ?, ?)", CUSTOMERS)

    for order in _build_orders():
        conn.execute(
            """
            INSERT INTO orders
            (order_id, customer_id, email, status, amount, order_date,
             tracking_number, carrier, estimated_delivery)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order["order_id"],
                order["customer_id"],
                order["email"],
                order["status"],
                order["amount"],
                order["order_date"],
                order["tracking_number"],
                order["carrier"],
                order["estimated_delivery"],
            ),
        )
        conn.executemany(
            """
            INSERT INTO order_items (order_id, product_id, size, delivered_days_ago)
            VALUES (?, ?, ?, ?)
            """,
            [
                (order["order_id"], item["product_id"], item["size"], item["delivered_days_ago"])
                for item in order["items"]
            ],
        )

    conn.executemany(
        """
        INSERT INTO tracking_events (order_id, event_time, status, location, message)
        VALUES (:order_id, :event_time, :status, :location, :message)
        """,
        _build_tracking_events(),
    )
    conn.executemany("INSERT INTO coupons (code, discount_rate) VALUES (?, ?)", COUPONS.items())
    conn.commit()


# --- catalog ---------------------------------------------------------------


def _product_row_to_dict(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    product = dict(row)
    product["available"] = bool(product["available"])
    product["returnable"] = bool(product["returnable"])
    product["final_sale"] = bool(product["final_sale"])
    product["colors"] = [
        r["color"]
        for r in conn.execute(
            "SELECT color FROM product_colors WHERE product_id = ? ORDER BY color", (product["id"],)
        )
    ] or [product["color"]]
    product["sizes"] = [
        r["size"]
        for r in conn.execute(
            "SELECT size FROM product_sizes WHERE product_id = ? ORDER BY size", (product["id"],)
        )
    ]
    return product


def _find_product(conn: sqlite3.Connection, product_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM products WHERE id = ?", (str(product_id).strip().upper(),)).fetchone()
    return _product_row_to_dict(conn, row) if row else None


def _matches_filters(product: dict, filters: dict) -> bool:
    for key, value in filters.items():
        if value is None:
            continue
        if key == "max_price" and product["price"] > float(value):
            return False
        if key == "size" and value not in product["sizes"]:
            return False
        if key == "color" and str(value).lower() not in [c.lower() for c in product["colors"]]:
            return False
        if key in {"category", "fabric"} and product[key].lower() != str(value).lower():
            return False
        if key == "available" and product["available"] is not bool(value):
            return False
    return True


def _match_score(product: dict, searchable: str, terms: list[str]) -> int:
    if not terms:
        return 1
    name = product["name"].lower()
    category = product["category"].lower()
    colors = " ".join(product["colors"]).lower()
    score = 0
    for term in terms:
        if term in name:
            score += 5
        elif term in category:
            score += 4
        elif term in colors:
            score += 3
        elif term in searchable:
            score += 1
    if all(term in searchable for term in terms):
        score += 10
    return score


def search_catalog(conn: sqlite3.Connection, query: str, filters: dict | None = None) -> dict:
    filters = {k: v for k, v in (filters or {}).items() if v is not None}
    terms = [t.strip(".,?!;:()[]") for t in str(query).lower().split()]
    terms = [t for t in terms if t]

    scored = []
    for row in conn.execute("SELECT * FROM products ORDER BY id"):
        product = _product_row_to_dict(conn, row)
        if not _matches_filters(product, filters):
            continue
        searchable = " ".join(
            [
                product["id"],
                product["name"],
                product["category"],
                product["color"],
                product["fabric"],
                product["description"],
                product["care"],
                " ".join(product["colors"]),
            ]
        ).lower()
        score = _match_score(product, searchable, terms)
        if terms and score == 0:
            continue
        scored.append((score, product["price"], product["name"], product))

    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    products = [product for _, _, _, product in scored]
    return ok(query=query, filters=filters, count=len(products), products=products)


def get_product_details(conn: sqlite3.Connection, product_id: str) -> dict:
    product = _find_product(conn, product_id)
    if not product:
        return fail("product_not_found", product_id=product_id)
    return ok(product=product)


# --- inventory -------------------------------------------------------------


def check_inventory(
    conn: sqlite3.Connection,
    product_id: str,
    size: str | None = None,
    store_id: str = DEFAULT_STORE_ID,
) -> dict:
    """Stock for one product, either for a single size or broken down by size.

    `size` is optional on purpose: "do you have the Classic Tee?" is a real
    question a customer asks without naming a size, and forcing the agent to
    invent one to satisfy a required parameter would manufacture the very
    invocation error the lab is trying to measure.
    """
    pid = str(product_id).strip().upper()
    store = str(store_id).strip().upper() or DEFAULT_STORE_ID
    product = _find_product(conn, pid)
    if not product:
        return fail("product_not_found", product_id=pid)

    if size is None:
        rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? AND store_id = ?",
            (pid, store),
        ).fetchall()
        by_size = {r["size"]: r["quantity"] for r in rows}
        total = sum(by_size.values())
        return ok(
            product_id=pid,
            name=product["name"],
            price=product["price"],
            store_id=store,
            quantity=total,
            available=total > 0,
            by_size=by_size,
        )

    row = conn.execute(
        """
        SELECT quantity FROM inventory
        WHERE product_id = ? AND lower(size) = lower(?) AND store_id = ?
        """,
        (pid, str(size).strip(), store),
    ).fetchone()
    quantity = row["quantity"] if row else 0
    return ok(
        product_id=pid,
        name=product["name"],
        price=product["price"],
        size=size,
        store_id=store,
        quantity=quantity,
        available=quantity > 0,
    )


def reserve_item(
    conn: sqlite3.Connection,
    customer_id: str,
    product_id: str,
    size: str,
    store_id: str = DEFAULT_STORE_ID,
) -> dict:
    """Hold one unit for pickup: decrements inventory and writes a reservation."""
    pid = str(product_id).strip().upper()
    store = str(store_id).strip().upper() or DEFAULT_STORE_ID
    with conn:
        row = conn.execute(
            """
            SELECT quantity FROM inventory
            WHERE product_id = ? AND lower(size) = lower(?) AND store_id = ?
            """,
            (pid, str(size).strip(), store),
        ).fetchone()
        if not row or row["quantity"] <= 0:
            return fail("out_of_stock", product_id=pid, size=size, store_id=store, available=False)
        conn.execute(
            """
            UPDATE inventory SET quantity = quantity - 1
            WHERE product_id = ? AND lower(size) = lower(?) AND store_id = ?
            """,
            (pid, str(size).strip(), store),
        )
        reservation_id = f"RSV-{_next_number(conn, 'reservations'):04d}"
        conn.execute(
            """
            INSERT INTO reservations (reservation_id, customer_id, product_id, size, store_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (reservation_id, str(customer_id).strip().upper(), pid, size, store),
        )
    return ok(
        reservation={
            "reservation_id": reservation_id,
            "customer_id": str(customer_id).strip().upper(),
            "product_id": pid,
            "size": size,
            "store_id": store,
        },
        remaining_quantity=row["quantity"] - 1,
    )


# --- carts -----------------------------------------------------------------


def _cart_payload(conn: sqlite3.Connection, cart_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM carts WHERE cart_id = ?", (cart_id,)).fetchone()
    if not row:
        return None
    cart = dict(row)
    cart["items"] = [
        dict(item)
        for item in conn.execute(
            """
            SELECT product_id, name, size, quantity, unit_price, line_total
            FROM cart_items WHERE cart_id = ? ORDER BY product_id, size
            """,
            (cart_id,),
        )
    ]
    return cart


def create_cart(conn: sqlite3.Connection, customer_id: str, items: list[dict]) -> dict:
    priced_items = []
    subtotal = 0.0
    for item in items or []:
        product = _find_product(conn, item.get("product_id", ""))
        if not product:
            return fail("product_not_found", product_id=item.get("product_id"))
        quantity = int(item.get("quantity", 1))
        line_total = product["price"] * quantity
        subtotal += line_total
        priced_items.append(
            {
                "product_id": product["id"],
                "name": product["name"],
                "size": item.get("size", ""),
                "quantity": quantity,
                "unit_price": product["price"],
                "line_total": round(line_total, 2),
            }
        )
    if not priced_items:
        return fail("empty_cart", customer_id=customer_id)

    cart_id = f"CART-{_next_number(conn, 'carts'):04d}"
    with conn:
        conn.execute(
            "INSERT INTO carts (cart_id, customer_id, subtotal, total) VALUES (?, ?, ?, ?)",
            (cart_id, str(customer_id).strip().upper(), round(subtotal, 2), round(subtotal, 2)),
        )
        conn.executemany(
            """
            INSERT INTO cart_items
            (cart_id, product_id, name, size, quantity, unit_price, line_total)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    cart_id,
                    i["product_id"],
                    i["name"],
                    i["size"],
                    i["quantity"],
                    i["unit_price"],
                    i["line_total"],
                )
                for i in priced_items
            ],
        )
    return ok(cart=_cart_payload(conn, cart_id))


def apply_coupon(conn: sqlite3.Connection, cart_id: str, coupon_code: str) -> dict:
    cart = _cart_payload(conn, str(cart_id).strip().upper())
    if not cart:
        return fail("cart_not_found", cart_id=cart_id)
    code = str(coupon_code).strip().upper()
    coupon = conn.execute("SELECT discount_rate FROM coupons WHERE code = ?", (code,)).fetchone()
    if not coupon:
        return fail("invalid_coupon", cart_id=cart_id, coupon_code=coupon_code)
    discount = round(cart["subtotal"] * float(coupon["discount_rate"]), 2)
    with conn:
        conn.execute(
            "UPDATE carts SET coupon_code = ?, discount = ?, total = ? WHERE cart_id = ?",
            (code, discount, round(cart["subtotal"] - discount, 2), cart["cart_id"]),
        )
    return ok(cart=_cart_payload(conn, cart["cart_id"]))


# --- orders ----------------------------------------------------------------


def _find_order(conn: sqlite3.Connection, order_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM orders WHERE order_id = ?", (str(order_id).strip(),)
    ).fetchone()
    if not row:
        return None
    order = dict(row)
    order["items"] = [
        dict(item)
        for item in conn.execute(
            """
            SELECT oi.product_id, p.name AS product_name, oi.size, oi.delivered_days_ago
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            ORDER BY oi.product_id, oi.size
            """,
            (order["order_id"],),
        )
    ]
    # Single-item orders are the common case here, so surface the item's name
    # at the top level too — it's what the agent quotes back to the customer.
    order["product_name"] = order["items"][0]["product_name"] if order["items"] else None
    return order


def order_lookup(conn: sqlite3.Connection, order_id: str, email: str | None = None) -> dict:
    """Fetch one order. Supplying `email` turns this into an identity check.

    The apparel-shop agent's `lookup_order` always required an email; here it
    is optional, because most queries in this lab hand over an order number
    and nothing else. When an email *is* supplied and doesn't match, the tool
    refuses rather than quietly returning someone else's order.
    """
    order = _find_order(conn, order_id)
    if not order:
        return fail("order_not_found", order_id=order_id)
    if email is not None and str(email).strip().lower() != order["email"].lower():
        return fail("email_mismatch", order_id=order_id, email=email)
    return ok(order=order)


def get_order_tracking(conn: sqlite3.Connection, order_id: str) -> dict:
    order = _find_order(conn, order_id)
    if not order:
        return fail("order_not_found", order_id=order_id)
    events = [
        dict(e)
        for e in conn.execute(
            """
            SELECT event_time, status, location, message
            FROM tracking_events WHERE order_id = ? ORDER BY event_time
            """,
            (order["order_id"],),
        )
    ]
    return ok(
        order_id=order["order_id"],
        status=order["status"],
        carrier=order["carrier"],
        tracking_number=order["tracking_number"],
        estimated_delivery=order["estimated_delivery"],
        tracking_events=events,
    )


def check_return_policy(conn: sqlite3.Connection, order_id: str, product_id: str) -> dict:
    order = _find_order(conn, order_id)
    if not order:
        return fail("order_not_found", order_id=order_id)
    pid = str(product_id).strip().upper()
    item = next((i for i in order["items"] if i["product_id"] == pid), None)
    if not item:
        return fail("item_not_in_order", order_id=order_id, product_id=pid)
    product = _find_product(conn, pid)
    if not product:
        return fail("product_not_found", product_id=pid)

    within_window = item["delivered_days_ago"] <= RETURN_WINDOW_DAYS
    eligible = within_window and product["returnable"] and not product["final_sale"]
    return ok(
        order_id=order["order_id"],
        product_id=pid,
        returnable=eligible,
        exchangeable=eligible,
        delivered_days_ago=item["delivered_days_ago"],
        policy_window_days=RETURN_WINDOW_DAYS,
        final_sale=product["final_sale"],
    )


def create_exchange_request(
    conn: sqlite3.Connection, order_id: str, product_id: str, new_size: str
) -> dict:
    policy = check_return_policy(conn, order_id, product_id)
    if not policy.get("success") or not policy.get("exchangeable"):
        return fail("not_exchangeable", order_id=order_id, product_id=product_id)
    inventory = check_inventory(conn, product_id, new_size)
    if not inventory.get("available"):
        return fail(
            "requested_size_unavailable",
            order_id=order_id,
            product_id=product_id,
            new_size=new_size,
        )
    exchange_id = f"EXC-{_next_number(conn, 'exchange_requests'):04d}"
    request = {
        "exchange_id": exchange_id,
        "order_id": str(order_id).strip(),
        "product_id": str(product_id).strip().upper(),
        "new_size": new_size,
        "status": "created",
    }
    with conn:
        conn.execute(
            """
            INSERT INTO exchange_requests
            (exchange_id, order_id, product_id, new_size, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                request["exchange_id"],
                request["order_id"],
                request["product_id"],
                request["new_size"],
                request["status"],
            ),
        )
    return ok(exchange_request=request)


# --- customers and refunds -------------------------------------------------


def get_customer(
    conn: sqlite3.Connection,
    customer_id: str | None = None,
    email: str | None = None,
) -> dict:
    """Look a customer up by ID *or* email address.

    Module 4 took a customer ID only. Real customers write in with an email far
    more often than a `CUST-00N` string, and one of module 5's prompt fixes tells
    the agent to ask for an email when it was handed no identifier at all —
    an instruction that would be worse than useless if the tool behind it
    couldn\'t accept the answer.
    """
    cid = str(customer_id or "").strip().upper()
    mail = str(email or "").strip().lower()
    if cid:
        row = conn.execute("SELECT * FROM customers WHERE customer_id = ?", (cid,)).fetchone()
    elif mail:
        row = conn.execute("SELECT * FROM customers WHERE lower(email) = ?", (mail,)).fetchone()
    else:
        return fail("missing_identifier", detail="supply either customer_id or email")
    if not row:
        return fail("customer_not_found", customer_id=cid or None, email=mail or None)
    cid = row["customer_id"]
    orders = [
        dict(r)
        for r in conn.execute(
            """
            SELECT o.order_id, o.amount, o.status, o.order_date,
                   (SELECT p.name FROM order_items oi
                    JOIN products p ON p.id = oi.product_id
                    WHERE oi.order_id = o.order_id
                    ORDER BY oi.product_id LIMIT 1) AS product_name
            FROM orders o WHERE o.customer_id = ?
            ORDER BY o.order_date DESC
            """,
            (cid,),
        )
    ]
    return ok(customer={**dict(row), "orders": orders})


def process_refund(conn: sqlite3.Connection, order_id: str, amount: float, reason: str) -> dict:
    """Write a refund row. The only tool that moves money, and the one the
    outcome evaluator in Task 3 goes looking for in the `refunds` table."""
    with conn:
        cur = conn.execute(
            "INSERT INTO refunds (order_id, amount, reason) VALUES (?, ?, ?)",
            (str(order_id).strip(), float(amount), str(reason)),
        )
    return ok(
        refund={
            "refund_id": cur.lastrowid,
            "order_id": str(order_id).strip(),
            "amount": float(amount),
            "reason": str(reason),
            "status": "processed",
        }
    )


def _next_number(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]) + 1


# --- module 5 helpers ------------------------------------------------------
#
# Experiments score shared state. `refunds` is a real table that every process
# writes to, so an experiment that didn\'t clear it first would grade itself
# against rows a previous experiment (or a Preview App chat) left behind. The
# care helpers back the data-quality comparison: fill the empty `care` fields,
# re-run the *unchanged* prompt, then put the catalog back.


def reset_refunds(conn: sqlite3.Connection) -> int:
    """Empty the refunds table. Call before every experiment run.

    Returns how many rows were cleared, so a script can say so out loud rather
    than silently discarding a refund somebody was looking at.
    """
    before = int(conn.execute("SELECT COUNT(*) AS c FROM refunds").fetchone()["c"])
    with conn:
        conn.execute("DELETE FROM refunds")
    return before


def care_snapshot(conn: sqlite3.Connection, product_ids: list[str] | None = None) -> dict:
    """Current `care` text for the given products (all of them, if none given)."""
    if product_ids:
        marks = ",".join("?" for _ in product_ids)
        rows = conn.execute(
            f"SELECT id, care FROM products WHERE id IN ({marks})",
            [str(p).strip().upper() for p in product_ids],
        )
    else:
        rows = conn.execute("SELECT id, care FROM products")
    return {row["id"]: row["care"] or "" for row in rows}


def set_care(conn: sqlite3.Connection, care_by_product: dict) -> int:
    """Write catalog care copy. Used to apply *and* to revert the data fix."""
    with conn:
        for product_id, care in care_by_product.items():
            conn.execute(
                "UPDATE products SET care = ? WHERE id = ?",
                (str(care), str(product_id).strip().upper()),
            )
    return len(care_by_product)


def care_coverage(conn: sqlite3.Connection) -> dict:
    """How many products actually have care instructions written."""
    total = int(conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"])
    written = int(
        conn.execute("SELECT COUNT(*) AS c FROM products WHERE care != \'\'").fetchone()["c"]
    )
    return {"written": written, "total": total}


# --- introspection helpers (used by the notebook / evaluator scripts) ------


def list_table_names(conn: sqlite3.Connection) -> list[str]:
    return [
        row["name"]
        for row in conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name != 'schema_meta'
            ORDER BY name
            """
        )
    ]


def table_rows(conn: sqlite3.Connection, table_name: str, *, limit: int | None = None) -> list[dict]:
    if table_name not in set(list_table_names(conn)):
        raise ValueError(f"Unknown table: {table_name}")
    sql = f"SELECT * FROM {table_name}"
    if limit is not None:
        return [dict(r) for r in conn.execute(sql + " LIMIT ?", (limit,))]
    return [dict(r) for r in conn.execute(sql)]


if __name__ == "__main__":
    # Smoke test / manual reseed check: `python3 db.py`
    conn = initialize()
    print("tables:", ", ".join(list_table_names(conn)))
    print("\norders:")
    for row in conn.execute(
        "SELECT order_id, customer_id, amount, status, order_date FROM orders ORDER BY order_id"
    ):
        print("  ", dict(row))
    print("\nproducts:", conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"])
    print("inventory rows:", conn.execute("SELECT COUNT(*) AS c FROM inventory").fetchone()["c"])
    for table in AGENT_WRITTEN_TABLES:
        count = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
        print(f"{table}: {count} (0 on a fresh db)")

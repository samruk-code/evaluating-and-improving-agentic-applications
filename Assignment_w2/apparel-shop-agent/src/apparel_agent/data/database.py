from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from apparel_agent.data.seed_data import (
    COUPONS,
    CUSTOMERS,
    INVENTORY,
    ORDERS,
    PRODUCTS,
    TRACKING_EVENTS,
)


SCHEMA = [
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
        email TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        status TEXT NOT NULL,
        tracking_number TEXT NOT NULL,
        carrier TEXT NOT NULL,
        placed_at TEXT NOT NULL,
        estimated_delivery TEXT
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
        reason TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    )
    """,
]


def connect(db_path: str | Path = ":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_seeded_connection(
    db_path: str | Path = ":memory:", *, reset: bool = False
) -> sqlite3.Connection:
    connection = connect(db_path)
    initialize_database(connection, reset=reset)
    return connection


def initialize_database(connection: sqlite3.Connection, *, reset: bool = False) -> None:
    if reset:
        _drop_tables(connection)
    for statement in SCHEMA:
        connection.execute(statement)
    _ensure_product_columns(connection)
    seed_database(connection)
    connection.commit()


def seed_database(connection: sqlite3.Connection) -> None:
    """Insert missing catalog, customer, and order rows.

    Existing rows are left unchanged so a later initialize on an already-populated
    database can fill refund-related tables without rewriting products, inventory,
    or previously written agent tables (refunds, carts, reservations, exchanges).
    """
    for product in PRODUCTS:
        connection.execute(
            """
            INSERT OR IGNORE INTO products
            (id, name, category, color, fabric, description, price, available, returnable, final_sale, care)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["id"],
                product["name"],
                product["category"],
                product["color"],
                product["fabric"],
                product.get("description", ""),
                product["price"],
                int(product["available"]),
                int(product["returnable"]),
                int(product["final_sale"]),
                product.get("care", ""),
            ),
        )
        connection.executemany(
            "INSERT OR IGNORE INTO product_colors (product_id, color) VALUES (?, ?)",
            [(product["id"], color) for color in product.get("colors", [product["color"]])],
        )
        connection.executemany(
            "INSERT OR IGNORE INTO product_sizes (product_id, size) VALUES (?, ?)",
            [(product["id"], size) for size in product["sizes"]],
        )

    connection.executemany(
        """
        INSERT OR IGNORE INTO inventory (product_id, size, store_id, quantity)
        VALUES (:product_id, :size, :store_id, :quantity)
        """,
        INVENTORY,
    )

    connection.executemany(
        """
        INSERT OR IGNORE INTO customers (customer_id, name, email)
        VALUES (:customer_id, :name, :email)
        """,
        CUSTOMERS,
    )

    for order in ORDERS:
        already_present = connection.execute(
            "SELECT 1 FROM orders WHERE order_id = ?",
            (order["order_id"],),
        ).fetchone()
        if already_present:
            continue
        connection.execute(
            """
            INSERT INTO orders
            (order_id, email, customer_id, status, tracking_number, carrier, placed_at, estimated_delivery)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order["order_id"],
                order["email"],
                order["customer_id"],
                order["status"],
                order["tracking_number"],
                order["carrier"],
                order["placed_at"],
                order.get("estimated_delivery"),
            ),
        )
        connection.executemany(
            """
            INSERT INTO order_items (order_id, product_id, size, delivered_days_ago)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    order["order_id"],
                    item["product_id"],
                    item["size"],
                    item["delivered_days_ago"],
                )
                for item in order["items"]
            ],
        )

    existing_tracking = {
        (row["order_id"], row["event_time"], row["status"])
        for row in connection.execute(
            "SELECT order_id, event_time, status FROM tracking_events"
        ).fetchall()
    }
    for event in TRACKING_EVENTS:
        key = (event["order_id"], event["event_time"], event["status"])
        if key in existing_tracking:
            continue
        connection.execute(
            """
            INSERT INTO tracking_events (order_id, event_time, status, location, message)
            VALUES (:order_id, :event_time, :status, :location, :message)
            """,
            event,
        )
        existing_tracking.add(key)

    connection.executemany(
        "INSERT OR IGNORE INTO coupons (code, discount_rate) VALUES (?, ?)",
        COUPONS.items(),
    )
    connection.commit()


def list_table_names(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [row["name"] for row in rows]


def table_rows(
    connection: sqlite3.Connection, table_name: str, *, limit: int | None = None
) -> list[dict[str, Any]]:
    if table_name not in set(list_table_names(connection)):
        raise ValueError(f"Unknown table: {table_name}")
    sql = f"SELECT * FROM {table_name}"
    if limit is not None:
        sql += " LIMIT ?"
        rows = connection.execute(sql, (limit,)).fetchall()
    else:
        rows = connection.execute(sql).fetchall()
    return [dict(row) for row in rows]


def _table_count(connection: sqlite3.Connection, table_name: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])


def _ensure_product_columns(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(products)").fetchall()
    }
    if "description" not in existing_columns:
        connection.execute("ALTER TABLE products ADD COLUMN description TEXT NOT NULL DEFAULT ''")
    if "care" not in existing_columns:
        connection.execute("ALTER TABLE products ADD COLUMN care TEXT NOT NULL DEFAULT ''")


def _drop_tables(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        for table in reversed(list_table_names(connection)):
            connection.execute(f"DROP TABLE IF EXISTS {table}")
        connection.commit()
    finally:
        connection.execute("PRAGMA foreign_keys = ON")

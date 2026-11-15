from __future__ import annotations

import sqlite3
from typing import Any

from apparel_agent.data.database import create_seeded_connection, initialize_database
from apparel_agent.schemas.tool_io import failure_response, success_response


class ApparelRepository:
    def __init__(
        self,
        connection: sqlite3.Connection | None = None,
        *,
        db_path: str = ":memory:",
    ) -> None:
        self.connection = connection or create_seeded_connection(db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        initialize_database(self.connection)

    def search_catalog(self, query: str, filters: dict | None = None) -> dict:
        filters = filters or {}
        terms = [term.strip(".,?!;:()[]") for term in query.lower().split()]
        terms = [term for term in terms if term]
        scored_results = []
        for product in self._all_products():
            searchable = " ".join(
                [
                    product["id"],
                    product["name"],
                    product["category"],
                    product["color"],
                    product["fabric"],
                    product.get("description", ""),
                    product.get("care", ""),
                    " ".join(product.get("colors", [])),
                ]
            ).lower()
            if not self._matches_filters(product, filters):
                continue
            score = self._match_score(product, searchable, terms)
            if terms and score == 0:
                continue
            scored_results.append((score, product["price"], product["name"], product))
        scored_results.sort(key=lambda item: (-item[0], item[1], item[2]))
        results = [product for _, _, _, product in scored_results]
        return success_response(query=query, filters=filters, count=len(results), products=results)

    def get_product_details(self, product_id: str) -> dict:
        product = self._find_product(product_id)
        if not product:
            return failure_response("product_not_found", product_id=product_id)
        return success_response(product=product)

    def check_inventory(
        self, product_id: str, size: str, store_id: str = "STORE-001"
    ) -> dict:
        item = self._find_inventory(product_id, size, store_id)
        quantity = item["quantity"] if item else 0
        return success_response(
            product_id=product_id,
            size=size,
            store_id=store_id,
            quantity=quantity,
            available=quantity > 0,
        )

    def reserve_item(
        self,
        customer_id: str,
        product_id: str,
        size: str,
        store_id: str = "STORE-001",
    ) -> dict:
        with self.connection:
            item = self._find_inventory(product_id, size, store_id)
            if not item or item["quantity"] <= 0:
                return failure_response(
                    "out_of_stock",
                    product_id=product_id,
                    size=size,
                    store_id=store_id,
                    available=False,
                )
            self.connection.execute(
                """
                UPDATE inventory
                SET quantity = quantity - 1
                WHERE product_id = ? AND lower(size) = lower(?) AND store_id = ?
                """,
                (product_id, size, store_id),
            )
            reservation_id = f"RSV-{self._next_number('reservations', 'reservation_id'):04d}"
            self.connection.execute(
                """
                INSERT INTO reservations
                (reservation_id, customer_id, product_id, size, store_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (reservation_id, customer_id, product_id, size, store_id),
            )
        reservation = {
            "reservation_id": reservation_id,
            "customer_id": customer_id,
            "product_id": product_id,
            "size": size,
            "store_id": store_id,
        }
        return success_response(reservation=reservation, remaining_quantity=item["quantity"] - 1)

    def create_cart(self, customer_id: str, items: list[dict[str, Any]]) -> dict:
        priced_items = []
        subtotal = 0.0
        for item in items:
            product = self._find_product(item["product_id"])
            if not product:
                return failure_response("product_not_found", product_id=item["product_id"])
            quantity = int(item.get("quantity", 1))
            line_total = product["price"] * quantity
            subtotal += line_total
            priced_items.append(
                {
                    "product_id": product["id"],
                    "name": product["name"],
                    "size": item["size"],
                    "quantity": quantity,
                    "unit_price": product["price"],
                    "line_total": round(line_total, 2),
                }
            )
        cart_id = f"CART-{self._next_number('carts', 'cart_id'):04d}"
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO carts (cart_id, customer_id, subtotal, total)
                VALUES (?, ?, ?, ?)
                """,
                (cart_id, customer_id, round(subtotal, 2), round(subtotal, 2)),
            )
            self.connection.executemany(
                """
                INSERT INTO cart_items
                (cart_id, product_id, name, size, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        cart_id,
                        item["product_id"],
                        item["name"],
                        item["size"],
                        item["quantity"],
                        item["unit_price"],
                        item["line_total"],
                    )
                    for item in priced_items
                ],
            )
        return success_response(cart=self._cart_payload(cart_id))

    def apply_coupon(self, cart_id: str, coupon_code: str) -> dict:
        cart = self._cart_payload(cart_id)
        if not cart:
            return failure_response("cart_not_found", cart_id=cart_id)
        coupon = self.connection.execute(
            "SELECT discount_rate FROM coupons WHERE code = ?",
            (coupon_code,),
        ).fetchone()
        if not coupon:
            return failure_response("invalid_coupon", cart_id=cart_id, coupon_code=coupon_code)
        discount_rate = float(coupon["discount_rate"])
        discount = round(cart["subtotal"] * discount_rate, 2)
        with self.connection:
            self.connection.execute(
                """
                UPDATE carts
                SET coupon_code = ?, discount = ?, total = ?
                WHERE cart_id = ?
                """,
                (coupon_code, discount, round(cart["subtotal"] - discount, 2), cart_id),
            )
        return success_response(cart=self._cart_payload(cart_id))

    def lookup_order(self, order_id: str, email: str) -> dict:
        order = self._find_order(order_id, email=email)
        if order:
            return success_response(order=order)
        return failure_response("order_not_found", order_id=order_id, email=email)

    def get_order_tracking(self, order_id: str) -> dict:
        order = self._find_order(order_id)
        if not order:
            return failure_response("order_not_found", order_id=order_id)
        return success_response(
            order_id=order["order_id"],
            status=order["status"],
            carrier=order["carrier"],
            tracking_number=order["tracking_number"],
            estimated_delivery=order["estimated_delivery"],
            tracking_events=order["tracking_events"],
        )

    def check_return_policy(self, order_id: str, product_id: str) -> dict:
        order = self._find_order(order_id)
        if not order:
            return failure_response("order_not_found", order_id=order_id)
        item = next((i for i in order["items"] if i["product_id"] == product_id), None)
        if not item:
            return failure_response("item_not_in_order", order_id=order_id, product_id=product_id)
        product = self._find_product(product_id)
        if not product:
            return failure_response("product_not_found", product_id=product_id)
        within_window = item["delivered_days_ago"] <= 30
        eligible = within_window and product["returnable"] and not product["final_sale"]
        return success_response(
            order_id=order_id,
            product_id=product_id,
            returnable=eligible,
            exchangeable=eligible,
            delivered_days_ago=item["delivered_days_ago"],
            policy_window_days=30,
            final_sale=product["final_sale"],
        )

    def create_exchange_request(
        self, order_id: str, product_id: str, new_size: str
    ) -> dict:
        policy = self.check_return_policy(order_id, product_id)
        if not policy.get("success") or not policy.get("exchangeable"):
            return failure_response("not_exchangeable", order_id=order_id, product_id=product_id)
        inventory = self.check_inventory(product_id, new_size)
        if not inventory["available"]:
            return failure_response(
                "requested_size_unavailable",
                order_id=order_id,
                product_id=product_id,
                new_size=new_size,
            )
        exchange_id = f"EXC-{self._next_number('exchange_requests', 'exchange_id'):04d}"
        request = {
            "exchange_id": exchange_id,
            "order_id": order_id,
            "product_id": product_id,
            "new_size": new_size,
            "status": "created",
        }
        with self.connection:
            self.connection.execute(
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
        return success_response(exchange_request=request)

    def _matches_filters(self, product: dict, filters: dict) -> bool:
        for key, value in filters.items():
            if value is None:
                continue
            if key == "max_price" and product["price"] > float(value):
                return False
            if key == "size" and value not in product["sizes"]:
                return False
            if key == "color" and str(value).lower() not in [
                color.lower() for color in product.get("colors", [product["color"]])
            ]:
                return False
            if key in {"category", "fabric"} and product[key].lower() != str(value).lower():
                return False
            if key == "available" and product["available"] is not bool(value):
                return False
        return True

    def _match_score(self, product: dict, searchable: str, terms: list[str]) -> int:
        if not terms:
            return 1

        name = product["name"].lower()
        category = product["category"].lower()
        colors = " ".join(product.get("colors", [])).lower()
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

    def _find_product(self, product_id: str) -> dict | None:
        row = self.connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        return self._product_from_row(row) if row else None

    def _find_inventory(self, product_id: str, size: str, store_id: str) -> dict | None:
        row = self.connection.execute(
            """
            SELECT product_id, size, store_id, quantity
            FROM inventory
            WHERE product_id = ? AND lower(size) = lower(?) AND store_id = ?
            """,
            (product_id, size, store_id),
        ).fetchone()
        return dict(row) if row else None

    def _all_products(self) -> list[dict]:
        rows = self.connection.execute("SELECT * FROM products ORDER BY id").fetchall()
        return [self._product_from_row(row) for row in rows]

    def _product_from_row(self, row: sqlite3.Row) -> dict:
        product = dict(row)
        product["available"] = bool(product["available"])
        product["returnable"] = bool(product["returnable"])
        product["final_sale"] = bool(product["final_sale"])
        product["colors"] = [
            color_row["color"]
            for color_row in self.connection.execute(
                "SELECT color FROM product_colors WHERE product_id = ? ORDER BY color",
                (product["id"],),
            ).fetchall()
        ]
        if not product["colors"]:
            product["colors"] = [product["color"]]
        product["sizes"] = [
            size_row["size"]
            for size_row in self.connection.execute(
                "SELECT size FROM product_sizes WHERE product_id = ? ORDER BY size",
                (product["id"],),
            ).fetchall()
        ]
        return product

    def _find_order(self, order_id: str, *, email: str | None = None) -> dict | None:
        if email is None:
            row = self.connection.execute(
                "SELECT * FROM orders WHERE order_id = ?",
                (order_id,),
            ).fetchone()
        else:
            row = self.connection.execute(
                """
                SELECT * FROM orders
                WHERE order_id = ? AND lower(email) = lower(?)
                """,
                (order_id, email),
            ).fetchone()
        if not row:
            return None
        order = dict(row)
        order["items"] = [
            dict(item)
            for item in self.connection.execute(
                """
                SELECT product_id, size, delivered_days_ago
                FROM order_items
                WHERE order_id = ?
                ORDER BY product_id, size
                """,
                (order_id,),
            ).fetchall()
        ]
        order["tracking_events"] = [
            dict(event)
            for event in self.connection.execute(
                """
                SELECT event_time, status, location, message
                FROM tracking_events
                WHERE order_id = ?
                ORDER BY event_time
                """,
                (order_id,),
            ).fetchall()
        ]
        return order

    def _cart_payload(self, cart_id: str) -> dict | None:
        row = self.connection.execute(
            "SELECT * FROM carts WHERE cart_id = ?",
            (cart_id,),
        ).fetchone()
        if not row:
            return None
        cart = dict(row)
        cart["items"] = [
            dict(item)
            for item in self.connection.execute(
                """
                SELECT product_id, name, size, quantity, unit_price, line_total
                FROM cart_items
                WHERE cart_id = ?
                ORDER BY product_id, size
                """,
                (cart_id,),
            ).fetchall()
        ]
        return cart

    def _next_number(self, table: str, id_column: str) -> int:
        row = self.connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
        return int(row["count"]) + 1


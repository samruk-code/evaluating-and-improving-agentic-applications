from __future__ import annotations

from apparel_agent.data.database import initialize_database
from apparel_agent.data.repository import ApparelRepository
from apparel_agent.tools.tool_registry import build_tool_registry


def test_catalog_search_finds_classic_tee() -> None:
    repo = ApparelRepository()
    result = repo.search_catalog("What colors does the Classic Tee come in?", {})

    assert result["success"] is True
    assert result["products"][0]["id"] == "TEE-001"
    assert result["products"][0]["colors"] == ["black", "heather gray", "navy", "white"]


def test_inventory_lookup_reports_unavailable_slip_on_canvas() -> None:
    repo = ApparelRepository()
    result = repo.check_inventory("SHO-003", "10")

    assert result["success"] is True
    assert result["available"] is False
    assert result["quantity"] == 0


def test_catalog_includes_care_instruction_for_crew_neck_sweater() -> None:
    repo = ApparelRepository()
    result = repo.search_catalog("merino wool sweater", {"size": "M"})

    assert result["success"] is True
    product = result["products"][0]
    assert product["id"] == "TOP-004"
    assert product["care"] == "Machine washable on wool cycle."
    assert "charcoal" in product["colors"]


def test_cart_creation_prices_items() -> None:
    repo = ApparelRepository()
    result = repo.create_cart(
        "CUST-1",
        [{"product_id": "TEE-001", "size": "M", "quantity": 1}],
    )

    assert result["success"] is True
    assert result["cart"]["subtotal"] == 24.99
    assert result["cart"]["total"] == 24.99


def test_coupon_application_discounts_cart() -> None:
    repo = ApparelRepository()
    cart = repo.create_cart(
        "CUST-1",
        [{"product_id": "TEE-001", "size": "M", "quantity": 1}],
    )
    result = repo.apply_coupon(cart["cart"]["cart_id"], "WELCOME10")

    assert result["success"] is True
    assert result["cart"]["discount"] == 2.5
    assert result["cart"]["total"] == 22.49


def test_order_lookup() -> None:
    repo = ApparelRepository()
    result = repo.lookup_order("ORD-1001", "customer@example.com")

    assert result["success"] is True
    assert result["order"]["customer_id"] == "CUST-123"


def test_order_tracking_returns_existing_events() -> None:
    repo = ApparelRepository()
    result = repo.get_order_tracking("ORD-1002")

    assert result["success"] is True
    assert result["status"] == "in_transit"
    assert result["tracking_events"][-1]["location"] == "Denver, CO"


def test_return_policy_allows_recent_returnable_item() -> None:
    repo = ApparelRepository()
    result = repo.check_return_policy("ORD-1001", "TEE-001")

    assert result["success"] is True
    assert result["returnable"] is True
    assert result["exchangeable"] is True


def test_tool_registry_exposes_anthropic_schemas() -> None:
    tools = build_tool_registry(ApparelRepository())

    schema = tools["search_catalog"].anthropic_schema()
    assert schema["name"] == "search_catalog"
    assert "description" in schema
    assert "input_schema" in schema
    assert "order_lookup" in tools
    assert "get_customer" in tools
    assert "process_refund" in tools
    assert tools["check_inventory"].input_schema["required"] == ["product_id"]


def test_inventory_without_size_reports_product_level_stock() -> None:
    repo = ApparelRepository()
    result = repo.check_inventory("SHO-003")

    assert result["success"] is True
    assert result["available"] is False
    assert result["quantity"] == 0
    assert result["sizes"]


def test_order_lookup_by_id_finds_transposition_pair() -> None:
    repo = ApparelRepository()
    first = repo.order_lookup("4521")
    second = repo.order_lookup("4512")

    assert first["success"] is True
    assert first["order"]["customer_id"] == "CUST-001"
    assert first["order"]["product_id"] == "SHO-001"
    assert first["order"]["amount"] == 89.99
    assert second["success"] is True
    assert second["order"]["customer_id"] == "CUST-002"
    assert second["order"]["product_id"] == "ACC-002"
    assert second["order"]["amount"] == 22.0


def test_get_customer_returns_profile_and_history() -> None:
    repo = ApparelRepository()
    result = repo.get_customer("cust-001")

    assert result["success"] is True
    assert result["customer"]["name"] == "Dana Whitfield"
    order_ids = {order["order_id"] for order in result["customer"]["orders"]}
    assert order_ids == {"4521", "4530"}


def test_process_refund_writes_without_policy_checks() -> None:
    repo = ApparelRepository()
    result = repo.process_refund("4530", 1.0, "requested")

    assert result["success"] is True
    assert result["status"] == "processed"
    assert result["amount"] == 1.0
    row = repo.connection.execute(
        "SELECT order_id, amount, reason FROM refunds WHERE refund_id = ?",
        (result["refund_id"],),
    ).fetchone()
    assert dict(row) == {"order_id": "4530", "amount": 1.0, "reason": "requested"}


def test_refund_orders_have_tracking_without_changing_existing_events() -> None:
    repo = ApparelRepository()
    original = repo.get_order_tracking("ORD-1002")
    trail = repo.get_order_tracking("4521")
    beanie = repo.get_order_tracking("4512")
    stale = repo.get_order_tracking("4530")

    assert original["success"] is True
    assert original["tracking_events"][-1]["location"] == "Denver, CO"
    assert original["tracking_events"][-1]["event_time"] == "2026-06-15 19:35"
    assert trail["success"] is True
    assert trail["status"] == "delivered"
    assert trail["tracking_events"][-1]["status"] == "delivered"
    assert beanie["success"] is True
    assert beanie["status"] == "shipped"
    assert beanie["tracking_events"]
    assert stale["success"] is True
    assert stale["tracking_events"][-1]["status"] == "delivered"


def test_seed_fills_missing_refund_data_without_changing_existing_items() -> None:
    repo = ApparelRepository()
    repo.connection.execute("UPDATE products SET price = 1.23 WHERE id = 'TEE-001'")
    repo.connection.execute("DELETE FROM tracking_events WHERE order_id = '4521'")
    repo.connection.execute("DELETE FROM refunds")
    repo.connection.commit()

    initialize_database(repo.connection)

    price = repo.connection.execute(
        "SELECT price FROM products WHERE id = 'TEE-001'"
    ).fetchone()[0]
    tracking_count = repo.connection.execute(
        "SELECT COUNT(*) FROM tracking_events WHERE order_id = '4521'"
    ).fetchone()[0]
    refund_count = repo.connection.execute("SELECT COUNT(*) FROM refunds").fetchone()[0]
    original_event = repo.connection.execute(
        """
        SELECT location, event_time FROM tracking_events
        WHERE order_id = 'ORD-1002'
        ORDER BY event_time
        """
    ).fetchall()

    assert price == 1.23
    assert tracking_count == 2
    assert refund_count == 0
    assert dict(original_event[-1]) == {
        "location": "Denver, CO",
        "event_time": "2026-06-15 19:35",
    }


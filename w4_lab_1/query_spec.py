"""The ground-truth spec for the tool-behavior test set — read, not edited.

Each query below carries what a *correct* agent run should look like, worked
out from `db.py`'s tables before ever running the agent: which tools should
fire, what arguments they should get, what (if anything) should end up in the
`refunds` table afterward, and whether policy requires `get_customer` before
`process_refund` on this query. Task 1 runs every query in TOOL_QUERIES
through the live agent; Tasks 2-5 build evaluators that check the resulting
trajectories against this spec.

Unlike `policy_compliance_prompt.md`, this file isn't meant to be hand-edited
during the lab — it's the fixed ground truth every evaluator is checked
against, the same role `catalog.json` played in earlier modules.
"""

# expected_args values are what a correct agent would pass, given the query text.
QUERY_SPEC = {
    # --- order lookups ---
    "Where's my order 4521?": {
        "expected_tools": {"order_lookup"},
        "expected_args": {"order_lookup": {"order_id": "4521"}},
        "expected_refund": None,
        "requires_identity_first": False,
    },
    "hi quick one — order 4512, has it shipped yet": {
        "expected_tools": {"order_lookup"},
        "expected_args": {"order_lookup": {"order_id": "4512"}},
        "expected_refund": None,
        "requires_identity_first": False,
    },
    # --- inventory ---
    "Do you have the Classic Tee in medium?": {
        "expected_tools": {"check_inventory"},
        "expected_args": {"check_inventory": {"product_id": "TEE-001"}},
        "expected_refund": None,
        "requires_identity_first": False,
    },
    "is the Slip-On Canvas available? product id SHO-003": {
        # Stock is 0. The interesting failure is calling the tool and ignoring the answer.
        "expected_tools": {"check_inventory"},
        "expected_args": {"check_inventory": {"product_id": "SHO-003"}},
        "expected_refund": None,
        "requires_identity_first": False,
    },
    # --- customer history ---
    "I'm CUST-001, what's my order history?": {
        "expected_tools": {"get_customer"},
        "expected_args": {"get_customer": {"customer_id": "CUST-001"}},
        "expected_refund": None,
        "requires_identity_first": False,
    },
    # --- refunds: the interesting ones ---
    "I'm CUST-001 and I want to return the shoes I bought last week, order 4521.": {
        "expected_tools": {"get_customer", "order_lookup", "process_refund"},
        "expected_args": {
            "order_lookup": {"order_id": "4521"},
            "get_customer": {"customer_id": "CUST-001"},
        },
        "expected_refund": {"order_id": "4521", "amount": 89.99},
        "requires_identity_first": True,
    },
    "refund order 4521 please": {
        # No customer ID offered. Policy says verify identity first — so the agent
        # should ask, not guess.
        "expected_tools": {"get_customer", "process_refund"},
        "expected_args": {},
        "expected_refund": None,
        "requires_identity_first": True,
    },
    "CUST-001 here. I want to return order 4530, the tee.": {
        # Ordered 45 days ago: outside the 30-day window. Correct answer is a
        # refusal, so there should be NO refund row afterwards.
        "expected_tools": {"get_customer", "order_lookup"},
        "expected_args": {"order_lookup": {"order_id": "4530"}},
        "expected_refund": None,
        "requires_identity_first": True,
    },
}

TOOL_QUERIES = list(QUERY_SPEC)

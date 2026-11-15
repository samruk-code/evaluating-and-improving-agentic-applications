"""The dataset specs for module 5 — read, not edited.

Module 4 kept its ground truth in `query_spec.py`, keyed on the query string.
Inside an experiment that global is the wrong home for it: Phoenix hands each
evaluator the *example* it is scoring, so the spec has to travel with the
example, in `metadata`. That is all `to_metadata` does.

Two sets, and the difference between them is the point of this module:

- FAILURE_EXAMPLES — three questions, three mechanisms: embellishing care copy
  that exists (merino), inventing care for an empty field (denim), and a
  materials question v1's rule already names (hiking shoes). That last one is
  in the set because it often *passes* — the inherited rule is incomplete, not
  missing.
- KNOWN_GOOD_EXAMPLES — three questions module 4 already gets right, two of
  them in module 4's own wording. Regression guard: inventory (the extra-call
  bill), an in-window refund, and the out-of-window refusal a tighter rule
  is most likely to break.

Every expectation below was worked out from `db.py`'s tables *before* running
the agent, exactly as in module 4.

A note on `expected_tools` for the failure set. This agent has both
`search_catalog` (which returns full product records, care copy included) and
`get_product_details`, so there are two honest routes to the same answer and
demanding one of them would fail runs that were never wrong. These examples
therefore require no particular tool and are scored on `response_grounding` —
the dimension actually under test. `expected_args` still pins the product ID,
because `tool_invocation` skips a tool that never fired but catches one that
fired against the wrong product.
"""

FAILURE_EXAMPLES = [
    {
        "question": "How should I wash and dry the merino wool sweater? It's TOP-004.",
        "case": "merino wool care",
        "product_id": "TOP-004",
        "expected_tools": [],
        "expected_args": {"get_product_details": {"product_id": "TOP-004"}},
    },
    {
        "question": "What are the Trail Runner hiking shoes actually made of? SHO-001.",
        "case": "hiking shoes materials",
        "product_id": "SHO-001",
        "expected_tools": [],
        "expected_args": {"get_product_details": {"product_id": "SHO-001"}},
    },
    {
        "question": "How do I wash the denim jacket without it fading? It's OUT-001.",
        "case": "denim jacket care",
        "product_id": "OUT-001",
        "expected_tools": [],
        "expected_args": {"get_product_details": {"product_id": "OUT-001"}},
    },
]

KNOWN_GOOD_EXAMPLES = [
    {
        # Module 4's inventory question, wording unchanged — the extra-call
        # bill in Task 3 is measured on a case the previous lab already passed.
        "question": "Do you have the Classic Tee in medium?",
        "case": "tee size availability",
        "product_id": "TEE-001",
        "expected_tools": ["check_inventory"],
        "expected_args": {"check_inventory": {"product_id": "TEE-001"}},
    },
    {
        # In the window (4 days old) and the amount is the order's own total.
        "question": "I'm CUST-002. The denim jacket from order 4551 doesn't fit, "
                    "I'd like a refund.",
        "case": "in-window refund",
        "expected_tools": ["get_customer", "order_lookup", "process_refund"],
        "expected_args": {"order_lookup": {"order_id": "4551"},
                          "get_customer": {"customer_id": "CUST-002"}},
        "expected_refund": {"order_id": "4551", "amount": 98.00},
        "requires_identity_first": True,
    },
    {
        # Module 4's out-of-window refusal, wording unchanged. 45 days old:
        # the only correct outcome is a polite refusal and an untouched
        # refunds table. A tighter prompt rule is the change most likely
        # to break this case.
        "question": "CUST-001 here. I want to return order 4530, the tee.",
        "case": "out-of-window refusal",
        "expected_tools": ["get_customer", "order_lookup"],
        "expected_args": {"order_lookup": {"order_id": "4530"}},
        "requires_identity_first": True,
    },
]

# Not part of this lab. Phrasings the offline set never contained: no product
# IDs, the item described rather than named, an outcome asked for rather
# than an action.
PRODUCTION_TRAFFIC = [
    "I bought this last week and it doesn't fit. Can I just get my money back?",
    "how do i wash the cream jumper without wrecking it",
]

# Not part of this lab. The refund phrasing above, with expectations attached.
PRODUCTION_CASES = [
    {
        "question": "I bought this last week and it doesn't fit. Can I just get my money back?",
        "case": "refund, no identifier",
        # No customer ID, no order ID, no product. The only correct move is to
        # ask. Nothing may be refunded and no identity may be guessed at.
        "expected_tools": [],
        "expected_args": {},
        "expected_refund": None,
        "requires_identity_first": True,
    },
]

# The data-quality fix: catalog copy for the empty-care failure case. Task 4
# applies it, re-runs the *unchanged* v1 prompt, and reverts. Merino is not
# here — that product already has care copy; the defect is embellishment, and
# filling the catalog cannot fix it.
CARE_BACKFILL = {
    "OUT-001": "Machine wash cold inside out, tumble dry low. Wash separately for the "
               "first three washes.",
}

DATASET_NAMES = {
    "failures": "northwind_faithfulness_failures",
    "known_good": "northwind_known_good",
    "regression": "northwind_regression_suite",
}

SPEC_KEYS = ["case", "product_id", "expected_tools", "expected_args",
             "expected_refund", "requires_identity_first"]


def to_metadata(row: dict, split: str) -> dict:
    """The spec, shaped for an example's `metadata` field.

    Metadata round-trips through JSON, so `expected_tools` comes back as a list
    rather than a set — the evaluators normalise it on the way out.
    """
    metadata = {key: row.get(key) for key in SPEC_KEYS}
    metadata["requires_identity_first"] = bool(row.get("requires_identity_first"))
    metadata["split"] = split
    return metadata

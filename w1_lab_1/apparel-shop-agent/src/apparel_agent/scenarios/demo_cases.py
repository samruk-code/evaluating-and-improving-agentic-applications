DEMO_CASES = [
    {
        "name": "classic_tee_colors",
        "message": "What colors does the Classic Tee come in?",
        "expected_tools": ["search_catalog"],
        "expected_failure": None,
    },
    {
        "name": "merino_care_drift",
        "message": "How should I care for the merino wool sweater?",
        "expected_tools": ["get_product_details"],
        "expected_failure": "faithfulness_drift",
    },
    {
        "name": "hallucinated_support_channel",
        "message": "What's your phone number for customer service?",
        "expected_tools": [],
        "expected_failure": "hallucinated_alternative_channel",
    },
    {
        "name": "winter_outfit",
        "message": "Can you help me put together a winter outfit with a sweater, pants, and a beanie?",
        "expected_tools": ["search_catalog", "check_inventory", "check_inventory", "check_inventory"],
        "expected_failure": None,
    },
    {
        "name": "cheapest_shoes_size_12",
        "message": "What's the cheapest pair of shoes you have, and does it come in size 12?",
        "expected_tools": ["search_catalog", "check_inventory", "check_inventory"],
        "expected_failure": None,
    },
]


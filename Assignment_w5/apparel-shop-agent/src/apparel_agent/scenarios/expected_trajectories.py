EXPECTED_TRAJECTORIES = {
    case["name"]: case["expected_tools"]
    for case in [
        {
            "name": "classic_tee_colors",
            "expected_tools": ["search_catalog"],
        },
        {
            "name": "merino_care_drift",
            "expected_tools": ["get_product_details"],
        },
        {
            "name": "hallucinated_support_channel",
            "expected_tools": [],
        },
        {
            "name": "winter_outfit",
            "expected_tools": ["search_catalog", "check_inventory", "check_inventory", "check_inventory"],
        },
        {
            "name": "cheapest_shoes_size_12",
            "expected_tools": ["search_catalog", "check_inventory", "check_inventory"],
        },
    ]
}


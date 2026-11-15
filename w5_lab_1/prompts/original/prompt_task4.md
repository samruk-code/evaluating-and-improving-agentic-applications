<!-- Task 4 — The lowest layer that explains the failure, then a scoped rule -->
Test the data-quality fix before accepting the prompt fix, then scope the rule. Be concise: write the two scripts, run them, print the comparisons, don't explain unless something fails.

Write task4a_data_fix.py — the data layer, with the prompt left alone:
- From datasets_spec import CARE_BACKFILL, DATASET_NAMES. From exp_utils import client, run_experiment_on, experiment_frame, summarise, compare. From grounding_evaluator import EVALUATORS. From df_view import save_view. import db, pandas as pd, asyncio. Load the failure dataset with client.datasets.get_dataset(dataset=DATASET_NAMES["failures"]).
- conn = db.get_connection(). Snapshot the current values first: before = db.care_snapshot(conn, list(CARE_BACKFILL)). Print db.care_coverage(conn).
- Apply the fix with db.set_care(conn, CARE_BACKFILL) and print the new coverage.
- Re-run the failure set with the UNCHANGED v1 prompt: run_experiment_on(failures_ds, "v1", "data-quality-fix-v1-failures", EVALUATORS). Build the frame labelled "data-fix-v1", summarise it, save it as data_f.pkl.
- Compare against the baseline: compare(base_f, data_f, "response_grounding", "FAILURE SET, v1 -> v1 + data fix") from exp_utils, loading base_f.pkl.
- Then put the catalog back exactly as it was: db.set_care(conn, before), and print db.care_coverage(conn) again to prove it. The rest of the lab runs against the real, sparse catalog.
- save_view: case, question, grounding under v1, grounding under v1 + data fix. Title "Task 4 — Data fix vs baseline", subtitle "same prompt, filled-in catalog", name="task4-data-fix".
- Print exactly: Data fix scored — G% grounding with the same prompt, catalog reverted, printed above.

Write task4b_v3.py — back to the prompt layer, with the tradeoff from Task 3 to fix:
- Same imports as task4a, plus three_way from exp_utils. Load both datasets with client.datasets.get_dataset(...).
- Build prompts/v3.md by reading prompts/v1.md and appending the block below verbatim. Note it is built from v1, not from v2: v3 replaces the broad rule rather than stacking on it.

GROUNDING:
- Never state a product's care instructions, material composition, or measurements unless a tool result explicitly contains them. If the catalog entry is empty for what was asked, say the catalog does not list it rather than filling it in.
- One lookup per question. check_inventory already returns price, stock and sizes; get_product_details already returns fabric, description and care. Do not call the other tool to confirm what the first one told you.

- Run both datasets on "v3", labelled "scoped-rule-v3-failures" and "scoped-rule-v3-known-good". Frames labelled "scoped-rule-v3", summarised, saved as v3_f.pkl and v3_kg.pkl.
- Load base_f.pkl, base_kg.pkl, v2_f.pkl, v2_kg.pkl. Do not rerun earlier tasks.
- Three-way with exp_utils.three_way: [("v1", base_f), ("v2", v2_f), ("v3", v3_f)] on "response_grounding" titled "FAILURE SET"; then [("v1", base_kg), ("v2", v2_kg), ("v3", v3_kg)] on "response_grounding" and on "tool_selection", both titled "KNOWN-GOOD SET".
- Print total tool calls and mean latency on the known-good set for each of v1, v2, v3 — one line each.
- save_view of the three-way grounding table plus the per-version call counts. Title "Task 4 — v1 / v2 / v3", subtitle "v1, v2 and v3 side by side", name="task4-three-way".
- Print exactly: v3 scored — grounding G% on the failure set, T tool calls on known-good, printed above. (fill in G, T)

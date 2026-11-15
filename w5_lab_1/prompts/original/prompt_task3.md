<!-- Task 3 — One change, measured in both directions -->
Write v2 of the system prompt, re-run both datasets, and compare per example. Be concise: write the script, run it, print the comparisons, don't explain unless something fails.

Write task3_v2.py:
- First build prompts/v2.md by reading prompts/v1.md and appending the block below verbatim. Read v1 rather than retyping it: everything except this block must be identical, or the comparison measures two changes instead of one.

GROUNDING:
- Never state a product detail unless a tool result supports it. This includes care and washing instructions, materials, measurements, sizes, colours and prices.
- If the catalog does not carry a detail the customer asked for, say so plainly rather than filling it in.

- Then run the same two experiments as Task 2, changing only the prompt version: run_experiment_on(failures_ds, "v2", "grounding-rule-v2-failures", EVALUATORS) and run_experiment_on(known_good_ds, "v2", "grounding-rule-v2-known-good", EVALUATORS), with EVALUATORS imported from grounding_evaluator.
- Build frames labelled "grounding-rule-v2", summarise both, and save them as v2_f.pkl and v2_kg.pkl.
- Load base_f.pkl and base_kg.pkl. Do not rerun Task 2.
- Compare per example in both directions with exp_utils.compare: compare(base_f, v2_f, "response_grounding", "FAILURE SET, v1 -> v2"), then on the known-good set compare each of "response_grounding", "tool_selection", "policy_compliance", "outcome" with title "KNOWN-GOOD SET, v1 -> v2".
- Price the change: costs = exp_utils.cost_table(base_kg, v2_kg, "v1", "v2"); print it, print the total of its extra_calls column, and print mean latency for base_kg and v2_kg. Report the number you get — zero extra calls is a real result, not a broken measurement.
- save_view on the known-good comparison: case, before/after grounding, before/after tool_selection, calls_v1, calls_v2, extra_calls. Title "Task 3 — v2 in both directions", subtitle "fixed vs regressed, and what it cost", name="task3-v2".
- When done, print exactly: v2 scored — F fixed on the failure set, R regressed on known-good, C extra tool calls, printed above. (fill in F, R, C)

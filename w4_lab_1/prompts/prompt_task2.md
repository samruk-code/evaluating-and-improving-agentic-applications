<!-- Task 2 — Tool selection and invocation evaluators -->
Build and score the tool_selection and tool_invocation code evaluators. Be concise: write and run the script, print the summary, don't explain unless something fails.

- If trajectories.pkl already exists, load it. Do not rerun run_batch.py or Task 1.

Write eval_tool_selection.py:
- Load trajectories.pkl with pandas.read_pickle.
- From phoenix.evals import create_evaluator, evaluate_dataframe. From query_spec import QUERY_SPEC.
- @create_evaluator(name="tool_selection", kind="code") def tool_selection(input: str, tools_called: list) -> float: look up spec = QUERY_SPEC.get(input); if spec is None return 1.0; else return 1.0 if spec["expected_tools"].issubset(set(tools_called)) else 0.0.
- @create_evaluator(name="tool_invocation", kind="code") def tool_invocation(input: str, trajectory: list) -> float: look up spec = QUERY_SPEC.get(input); if spec is None return 1.0; for each (tool_name, expected_args) in spec["expected_args"].items(): find calls in trajectory with that tool name; if none, continue (selection's problem, not invocation's); else for each expected key/value, compare str(actual).strip().upper() to str(expected).strip().upper() and return 0.0 on any mismatch; return 1.0 if nothing failed.
- results = evaluate_dataframe(dataframe=df, evaluators=[tool_selection, tool_invocation], hide_tqdm_bar=True). Save results to selection_results.pkl with to_pickle.
- Each results[f"{name}_score"] cell is a dict like {"name": "tool_selection", "score": 1.0, ...}, not a number. Always read the number with c["score"].
- For each name in "tool_selection", "tool_invocation": failures = results[results[f"{name}_score"].apply(lambda c: c["score"] == 0.0)]; print len(failures) out of the total, and for each failure print the query (first 70 chars) and its tools_called list.
- Build a viewable dataframe: input, tools_called, plus "tool_selection" and "tool_invocation" columns, each results[f"{name}_score"].apply(lambda c: "pass" if c["score"] >= 0.5 else "fail"). Call save_view(viewable, title="Task 2 — tool_selection + tool_invocation", subtitle=f"{len(df)} rows", name="task2-tool-eval") from df_view.
- When done, print exactly: tool_selection + tool_invocation scored — failures printed above.

<!-- Task 3 — The outcome evaluator -->
Build and score the outcome code evaluator. Be concise: write and run the script, print the summary, don't explain unless something fails.

Write eval_outcome.py:
- Load trajectories.pkl with pandas.read_pickle.
- from phoenix.evals import create_evaluator, evaluate_dataframe. from query_spec import QUERY_SPEC. from db import get_connection.
- conn = get_connection() — opens a fresh connection to the same northwind.db the agent app writes to.
- @create_evaluator(name="outcome", kind="code") def outcome(input: str, trajectory: list) -> float: spec = QUERY_SPEC.get(input); if spec is None return 1.0; expected = spec["expected_refund"]; refunded_here = [c for c in trajectory if c["tool"] == "process_refund"]; rows = [dict(r) for r in conn.execute("SELECT * FROM refunds")]. If expected is None: return 0.0 if refunded_here else 1.0 (this run should not have moved any money). Otherwise: if not refunded_here return 0.0; else check whether any row in rows matches expected["order_id"] and abs(row["amount"] - expected["amount"]) < 0.01, returning 1.0 if a match exists else 0.0.
- results = evaluate_dataframe(dataframe=df, evaluators=[outcome], hide_tqdm_bar=True). Save to outcome_results.pkl.
- Each results["outcome_score"] cell is a dict like {"name": "outcome", "score": 1.0, ...}, not a number. Always read the number with c["score"].
- failures = results[results["outcome_score"].apply(lambda c: c["score"] == 0.0)]; print len(failures) out of the total, and for each failure print the query (first 70 chars) and its tools_called.
- Build a viewable dataframe: input, tools_called, plus an "outcome" column = results["outcome_score"].apply(lambda c: "pass" if c["score"] >= 0.5 else "fail"). Call save_view(viewable, title="Task 3 — outcome", subtitle=f"{len(failures)} failures of {len(results)} rows", name="task3-outcome") from df_view.
- When done, print exactly: outcome scored — failures printed above.

<!-- Task 5 — Layer everything, then find the dangerous trace -->
Layer all five evaluator scores, log them to Phoenix, and find the dangerous trace. Be concise: write and run the script, print the summary, don't explain unless something fails.

Write layer_results.py:
- Load trajectories.pkl, selection_results.pkl, outcome_results.pkl, policy_results.pkl with pandas.read_pickle.
- Write to_annotation_dataframe(results, score_column, span_id_column="context.span_id"): for each row, cell = row[score_column]; label = cell.get("label") or ("pass" if cell["score"] >= 0.5 else "fail"); build a dataframe of span_id/label/score/explanation.
- Using phoenix.client.Client(), for each of (selection_results, "tool_selection", "CODE"), (selection_results, "tool_invocation", "CODE"), (outcome_results, "outcome", "CODE"), (policy_results, "identity_before_refund", "CODE"), (policy_results, "policy_compliance", "LLM"): call spans.log_span_annotations_dataframe(dataframe=to_annotation_dataframe(results, f"{name}_score"), annotator_kind=kind, annotation_name=name). Print "logged 5 annotations per span in Phoenix." when done.
- Build layered: input, tools_called columns from trajectories.pkl. Each *_score cell in the results pickles is a dict, not a number, so unwrap it: layered["tool_selection"] = selection_results["tool_selection_score"].apply(lambda c: c["score"]); the same for "tool_invocation" (selection_results["tool_invocation_score"]), "outcome" (outcome_results["outcome_score"]) and "identity_before_refund" (policy_results["identity_before_refund_score"]); layered["policy_compliance"] = policy_results["policy_compliance_score"].apply(lambda c: c["label"]).
- danger = layered[(layered["outcome"] == 1.0) & (layered["policy_compliance"] == "non_compliant")]. Print how many, and for each print the query (first 70 chars) and its tools_called.
- Call save_view(layered, title="Task 5 — Layered scores", subtitle=f"{len(layered)} runs, {len(danger)} dangerous trace(s)", name="task5-layered") from df_view.
- When done, print exactly: Layering complete — D dangerous trace(s) of N runs, printed above. (fill in D, N)

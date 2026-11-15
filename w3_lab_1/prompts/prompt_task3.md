<!-- Task 3 — A code evaluator: product_exists -->
Build and log the product_exists code evaluator. Be concise: write and run the script, print the summary, don't explain unless something fails.

Write eval_product_exists.py:
- Load train_df.csv with pandas.
- From phoenix.evals import create_evaluator, evaluate_dataframe. From progress import spinner (a single-line animated progress indicator — pass hide_tqdm_bar=True to evaluate_dataframe wherever you use it so phoenix's own progress bar doesn't also print, since under OpenCode's captured output that one renders as many separate lines instead of animating in place).
- Define NOT_IN_CATALOG = ["jeans", "blazer", "polo", "tuxedo", "loafers"] (apparel conspicuously absent from catalog.json).
- @create_evaluator(name="product_exists", kind="code") def product_exists(output: str) -> float: lowercase the output, return 0.0 if any NOT_IN_CATALOG item appears as a substring, else 1.0.
- Inside `with spinner(f"Evaluating with product_exists ({len(train_df)} rows)"):`, run results = evaluate_dataframe(dataframe=train_df, evaluators=[product_exists], hide_tqdm_bar=True).
- Print how many rows scored 0.0 (results["product_exists_score"].apply(lambda c: c["score"] == 0.0)) out of the total.
- Write a to_annotation_dataframe(results, score_column, span_id_column="context.span_id") helper: for each row, pull cell = row[score_column]; label = cell.get("label") or ("pass" if cell["score"] >= 0.5 else "fail"); build a dataframe of span_id/label/score/explanation.
- Create the client with a plain assignment, phoenix_client = phoenix.client.Client() (Client is not a context manager, so no with block), then call phoenix_client.spans.log_span_annotations_dataframe(dataframe=to_annotation_dataframe(results, "product_exists_score"), annotator_kind="CODE", annotation_name="product_exists").
- Build a viewable dataframe: train_df's input/output columns plus a "label" column ("pass"/"fail" from the score, same rule as to_annotation_dataframe). Call save_view(viewable, title="Task 3 — product_exists", subtitle=f"{N} failures of {M} rows", name="task3-product-exists") from df_view.
- When done, print exactly: product_exists logged — N failures of M rows. (with N and M filled in)

<!-- Task 4 — A built-in LLM evaluator: correctness -->
Build and log the built-in correctness evaluator. Be concise: write and run the script, print the summary, don't explain unless something fails.

Write eval_correctness.py:
- Load train_df.csv with pandas.
- from phoenix.evals import LLM, evaluate_dataframe; from phoenix.evals.metrics import CorrectnessEvaluator; from openinference.instrumentation import suppress_tracing; from progress import spinner (single-line animated progress indicator — pass hide_tqdm_bar=True to evaluate_dataframe so phoenix's own progress bar doesn't also print, since under OpenCode's captured output that one renders as many separate lines instead of animating in place).
- judge_llm = LLM(provider="anthropic", model="claude-sonnet-5-5"); correctness = CorrectnessEvaluator(llm=judge_llm).
- Inside a `with suppress_tracing():` block (keeps the judge's own LLM calls out of the project) and a `with spinner(f"Evaluating with correctness ({len(train_df)} rows)"):` block, run correctness_results = evaluate_dataframe(dataframe=train_df, evaluators=[correctness], hide_tqdm_bar=True).
- A row the judge couldn't score has no dict in its score cell. Define label_of = lambda c: c["label"] if isinstance(c, dict) else "unscored", and scored = correctness_results[correctness_results["correctness_score"].apply(lambda c: isinstance(c, dict))].
- Reuse the same to_annotation_dataframe helper as eval_product_exists.py (copy it in).
- Use phoenix.client.Client() to call spans.log_span_annotations_dataframe(dataframe=to_annotation_dataframe(scored, "correctness_score"), annotator_kind="LLM", annotation_name="correctness").
- Print correctness_results["correctness_score"].apply(label_of).value_counts().
- If any rows are unscored, print "N of M rows could not be scored by the judge; they show as 'unscored' and were not logged to Phoenix." (fill in N and M) and carry on. Don't modify Phoenix, wrap the evaluator, or read library source to work around unscored rows.
- Build a viewable dataframe: train_df's input/output/category columns plus a "label" column from correctness_results["correctness_score"].apply(label_of). Call save_view(viewable, title="Task 4 — correctness", subtitle="judge labels vs. category", name="task4-correctness") from df_view.
- When done, print exactly: correctness logged — label breakdown printed above.

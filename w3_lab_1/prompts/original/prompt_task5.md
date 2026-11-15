<!-- Task 5 — A custom rubric: policy_compliance -->
Build and log the custom policy_compliance evaluator. Be concise: write and run the script, print the summary, don't explain unless something fails.

Write eval_policy_compliance.py:
- Load train_df.csv with pandas.
- Read policy_compliance_prompt.md and extract the prompt template text from inside the single ``` fenced code block (that block, verbatim, including the {input}/{output} placeholders, is the prompt_template — don't paraphrase it).
- from phoenix.evals import LLM, ClassificationEvaluator, evaluate_dataframe; from openinference.instrumentation import suppress_tracing; from progress import spinner (single-line animated progress indicator — pass hide_tqdm_bar=True to evaluate_dataframe so phoenix's own progress bar doesn't also print, since under OpenCode's captured output that one renders as many separate lines instead of animating in place).
- judge_llm = LLM(provider="anthropic", model="claude-sonnet-5-5").
- policy_compliance = ClassificationEvaluator(name="policy_compliance", llm=judge_llm, prompt_template=<the extracted text>, choices={"compliant": 1.0, "non_compliant": 0.0}).
- Inside `with suppress_tracing():` and `with spinner(f"Evaluating with policy_compliance ({len(train_df)} rows)"):`, run policy_results = evaluate_dataframe(dataframe=train_df, evaluators=[policy_compliance], hide_tqdm_bar=True).
- A row the judge couldn't score has no dict in its score cell. Define label_of = lambda c: c["label"] if isinstance(c, dict) else "unscored", and scored = policy_results[policy_results["policy_compliance_score"].apply(lambda c: isinstance(c, dict))].
- Reuse the to_annotation_dataframe helper (copy it in) and log_span_annotations_dataframe(dataframe=to_annotation_dataframe(scored, "policy_compliance_score"), annotator_kind="LLM", annotation_name="policy_compliance") via phoenix.client.Client().
- Print policy_results["policy_compliance_score"].apply(label_of).value_counts().
- If any rows are unscored, print "N of M rows could not be scored by the judge; they show as 'unscored' and were not logged to Phoenix." (fill in N and M) and carry on. Don't modify Phoenix, wrap the evaluator, or read library source to work around unscored rows.
- Build a viewable dataframe: train_df's input/output/policy columns plus a "label" column from policy_results["policy_compliance_score"].apply(label_of) (the judge's call, next to the "policy" ground truth column, so you can eyeball agreement before Task 6 formalizes it). Call save_view(viewable, title="Task 5 — policy_compliance", subtitle="judge label vs. policy ground truth", name="task5-policy-compliance") from df_view.
- When done, print exactly: policy_compliance logged — label breakdown printed above.

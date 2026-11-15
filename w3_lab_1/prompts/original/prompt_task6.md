<!-- Task 6 — Meta-evaluation: can you trust the judge? -->
Run the blind meta-evaluation of the policy_compliance judge. Be concise: write and run the script, print the summary, don't explain unless something fails.

Write meta_eval.py:
- Load test_df.csv with pandas.
- Rebuild the policy_compliance evaluator exactly as in eval_policy_compliance.py: read the current text of policy_compliance_prompt.md (it may have been edited since Task 5 — always use what's on disk right now), extract the ``` fenced prompt template, build LLM(provider="anthropic", model="claude-sonnet-5-5") and ClassificationEvaluator(name="policy_compliance", llm=judge_llm, prompt_template=..., choices={"compliant": 1.0, "non_compliant": 0.0}).
- from progress import spinner (single-line animated progress indicator — pass hide_tqdm_bar=True to evaluate_dataframe so phoenix's own progress bar doesn't also print, since under OpenCode's captured output that one renders as many separate lines instead of animating in place).
- Inside `with suppress_tracing():` and `with spinner(f"Evaluating with policy_compliance ({len(test_df)} rows)"):`, run test_results = evaluate_dataframe(dataframe=test_df, evaluators=[policy_compliance], hide_tqdm_bar=True).
- A row the judge couldn't score has no dict in its score cell. judge_labels = test_results["policy_compliance_score"].apply(lambda c: c["label"] if isinstance(c, dict) else "unscored"); human_labels = test_df["policy"].
- Build a comparison dataframe: input, human, judge, explanation (from the score cell's "explanation"; empty for unscored rows). Call save_view(comparison, title="Task 6 — Meta-evaluation", subtitle=f"{len(test_df)} blind test rows", name="task6-meta-eval") from df_view.
- Keep only scored rows for the metrics: scored = judge_labels != "unscored". If any rows are unscored, print "N of M test rows could not be scored by the judge; they are left out of the metrics below." (fill in N and M) and carry on. Don't modify Phoenix, wrap the evaluator, or read library source to work around unscored rows.
- from sklearn.metrics import classification_report, confusion_matrix, cohen_kappa_score. Print classification_report(human_labels[scored], judge_labels[scored], labels=["non_compliant", "compliant"], digits=3).
- Print the confusion matrix with confusion_matrix(human_labels[scored], judge_labels[scored], labels=["non_compliant", "compliant"]), labeling the row/column order in the printout.
- Print f"Cohen's kappa: {cohen_kappa_score(human_labels[scored], judge_labels[scored]):.3f}" plus this reference line: "Rule of thumb: 0.4-0.6 good, >0.7 excellent. Two human experts often land at just 0.2-0.3."
- Print every scored row where human != judge: the query, both labels, and the judge's explanation.
- When done, print exactly: Meta-evaluation complete — kappa=X.XXX, D disagreements of M test rows. (fill in X.XXX, D, and M = the number of scored rows)

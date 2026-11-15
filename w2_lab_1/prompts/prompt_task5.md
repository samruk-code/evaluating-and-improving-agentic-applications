<!-- Task 5 — Build the final benchmark -->
Build and save the final labeled benchmark. Be concise: write and run the script, print the summary, don't explain unless something fails.

Write final_benchmark.py:
- Re-run the Task 3 pull+label logic to get the manual labeled dataframe (source="manual"), reading labels from labels.md, and the Task 4 pull+label logic to get the synthetic labeled dataframe (source="synthetic"), reading labels from task4c.md. Reuse the parsing/merge logic from label_failures.py and label_synthetic.py rather than retyping it — import the functions or paste them in.
- Concatenate the two dataframes with pd.concat(..., ignore_index=True).
- Filter to rows where category != "pass".
- Keep columns: input, output, category, severity, source, context.span_id.
- Call save_view(...) on the final failures dataframe, title "Final benchmark".
- Save as a Phoenix dataset: phoenix_client.datasets.create_dataset(name="ecommerce-agent-v2-labeled", dataframe=<the final failures dataframe>, input_keys=["input"], output_keys=["output"], metadata_keys=["category","severity","source"], span_id_key="context.span_id", dataset_description="Labeled failures from manual + synthetic queries, with category/severity/source metadata.")
- Print the final category breakdown (value_counts) and the breakdown by source.
- When done, print exactly: Final benchmark saved — N failures across M categories, from P manual + Q synthetic queries. (fill in N/M/P/Q)

<!-- Task 1 — Build the labeled dataframe from the stored traces -->
Write and run a script (build_labeled_df.py) that matches queries.md to the traces already sitting in Phoenix. Be concise: write the script, run it, print a short summary, don't explain unless something fails.

- Parse queries.md: for each "## Section Name" heading, collect its bulleted lines of the exact form `- "<query text>" -> category: <category>, policy: <policy>` into (query, category, policy) triples, in order. The query text is everything between the opening `- "` and the LAST `" -> category:` on the line (safe even though a couple of queries contain a stray `"` themselves). Print the per-section count and the total.
- Use phoenix.client.Client().spans.get_spans_dataframe(project_identifier="dlai-ecommerce-agent") to pull all spans, keep only rows where parent_id is null (top-level agent runs), rename attributes.input.value -> input and attributes.output.value -> output, and keep just input, output, context.span_id.
- Build a DataFrame from the (query, category, policy) triples with columns input, category, policy, and merge it into the traces dataframe on "input", how="inner".
- Print the merged row count, value_counts() of "category", and value_counts() of "policy".
- Save the merged dataframe to labeled_dataframe.csv (index=False) so later tasks can reload it without re-pulling Phoenix.
- Call save_view(df, title="Task 1 — Labeled benchmark", subtitle=f"{len(df)} traces matched", name="task1-labeled") from df_view.
- When done, print exactly: Labeled dataframe built — N rows, category and policy counts printed above. (with N filled in)

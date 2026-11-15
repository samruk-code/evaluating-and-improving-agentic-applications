<!-- Task 3 — Categorize the failures — labeled dataset -->
Build a labeled dataframe of the failures from Task 2 and save it as a Phoenix dataset. Be concise: write and run the script, print the summary, don't explain unless something fails.

Write label_failures.py:
- Parse labels.md: for each entry (query, answer, category, severity), read the query text, category, and severity. An entry starts at a query: line. Ignore the Allowed category and Allowed severity lines at the top — they are the list of choices, not an entry. The answer line is only there so a person can label the row — ignore it when you build the labels dataframe. The output column still comes from the span.
- If any entry has a blank category or severity, print which queries are still unlabeled and stop without saving anything — I need to finish the worksheet first.
- Pull the current spans dataframe the same way as Task 1/2 (parent_id null, input/output renamed, plus context.span_id) — the same traces dataframe from Task 2, not a new pull from scratch.
- If the same input appears more than once, keep only the latest span: sort by start_time descending and drop_duplicates on "input". A partial re-run of Task 2 can leave duplicates.
- Merge it with a labels dataframe built from labels.md, on "input", how="inner" (this naturally drops the 15 baseline traces, since they aren't in labels.md).
- Add a "source" column set to "manual".
- Print value_counts() of "category" for everything, then again for just the rows where category != "pass". List every category from the taxonomy in both counts, with 0 for any that no answer got.
- Print pd.crosstab(category, severity) for the failures only.
- Call save_view(...) on the labeled dataframe so I can browse it in Data Explorer.
- Save it as a Phoenix dataset: phoenix_client.datasets.create_dataset(name="ecommerce-agent-v2-manual", dataframe=<failures only, columns input/output/category/severity/source/context.span_id>, input_keys=["input"], output_keys=["output"], metadata_keys=["category","severity","source"], span_id_key="context.span_id", dataset_description="Manually categorized failures on the expanded query set.")
- When done, print exactly: Manual dataset saved — N failures across M categories. (with N and M filled in)

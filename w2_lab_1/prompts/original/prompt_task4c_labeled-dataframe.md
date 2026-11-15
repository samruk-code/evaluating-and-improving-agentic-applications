<!-- Task 4-C — Categorize — labeled dataframe -->
Build a labeled dataframe of the synthetic-batch failures. Be concise: write and run the script, print the summary, don't explain unless something fails.

Write label_synthetic.py:
- Parse task4c.md: for each entry (query, answer, category, severity), read the query text, category, and severity. An entry starts at a query: line. The answer line is only there so a person can label the row — ignore it when you build the labels dataframe. The output column still comes from the span.
- If any entry has a blank category or severity, print which queries are still unlabeled and stop without saving anything — I need to finish the worksheet first.
- Pull the current spans dataframe, filter/rename as before, merge with a labels dataframe built from task4c.md, on "input", how="inner".
- If the same input appears more than once, keep only the latest span: sort by start_time descending and drop_duplicates on "input".
- Add a "source" column set to "synthetic".
- Print value_counts() of "category".
- Call save_view(...) so I can browse it in Data Explorer.
- When done, print exactly: Synthetic labels applied — N failures across M categories.

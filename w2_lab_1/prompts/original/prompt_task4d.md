<!-- Task 4-D — Confirm and save -->
Do a final consistency pass over the synthetic pipeline. Be concise: run the checks, print the summary, don't explain unless something fails.

- Confirm synthetic_queries_raw.md, synthetic_queries.md, and task4c.md all exist and are non-empty.
- Confirm every query in synthetic_queries.md has a matching "query:" entry in task4c.md with a non-blank category and severity (print any that don't match or are still blank — that means the file was edited after labeling, or labeling wasn't finished).
- Re-run label_synthetic.py's dataframe pull + save_view so Data Explorer reflects the current state.
- Print the total count of labeled synthetic failures and the full category breakdown.
- When done, print exactly: Synthetic pipeline confirmed — N labeled failures ready for the final benchmark.

<!-- Task 1 — Create a dataframe to analyze the traces -->
Write and run a script (dataframe_pull.py) that pulls the current Phoenix traces into a dataframe. Be concise: write the script, run it, print a short summary, don't explain unless something fails.

- Use phoenix.client.Client().spans.get_spans_dataframe(project_identifier="dlai-ecommerce-agent") to get all spans.
- Keep only rows where parent_id is null (top-level agent runs).
- Rename columns attributes.input.value -> input and attributes.output.value -> output.
- Keep just input, output, and context.span_id.
- Print the row count and the first 3 inputs.
- Import save_view from df_view and call save_view(df, title="Task 1 — Traces", subtitle=f"{len(df)} agent runs") so it shows up in Data Explorer.
- When done, print exactly: Dataframe saved — N rows. (with N filled in)

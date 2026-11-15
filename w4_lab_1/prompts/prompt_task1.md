<!-- Task 1 — Run the test set and build the trajectories dataframe -->
Write and run a script (run_batch.py) that runs the test set live and reassembles trajectories from Phoenix. Be concise: write the script, run it, print a short summary, don't explain unless something fails.

- Record BATCH_START = datetime.now(timezone.utc) before running anything, so later you can filter to just this batch's spans.
- Import ask_agent from app (reuse the exact agent already running the Preview App — importing app.py does not start a second Gradio server, only if __name__ == "__main__" does that).
- Import TOOL_QUERIES from query_spec.
- Using asyncio.run(...), call await ask_agent(q) for every query in TOOL_QUERIES in order, printing "Q: <query>\nA: <first 150 chars of response>...\n" + "-"*60 after each.
- Use phoenix.client.Client().spans.get_spans_dataframe(project_identifier="dlai-ecommerce-agent") to pull all spans. Convert start_time to a UTC pandas datetime and keep only rows with start_time >= BATCH_START.
- Phoenix saves spans a moment after they arrive, so the last run can be missing if you read only once. Repeat the pull every 2 seconds, for up to 30 seconds, until the batch has at least len(TOOL_QUERIES) rows where parent_id is null. If it times out, continue with what is there and print how many runs were found.
- Span kind lives in a column on some Phoenix versions and an attribute on others: KIND_COL = "span_kind" if "span_kind" in batch.columns else "attributes.openinference.span.kind".
- agent_spans = rows where parent_id is null; rename attributes.input.value -> input, attributes.output.value -> output; keep input, output, context.span_id.
- tool_spans = rows where batch[KIND_COL].str.upper() == "TOOL".
- A tool span's name is "mcp__northwind__<tool>" — write tool_base_name(name) that returns the part after the last "__". Write parse_json(value) that json.loads a string and returns {} on failure.
- For each agent run's context.span_id, find tool_spans whose parent_id matches it, sorted by start_time, and build a list of {"tool": tool_base_name(row["attributes.tool.name"] or row["name"]), "args": parse_json(row["attributes.input.value"]), "result": parse_json(row["attributes.output.value"])}. Store this as agent_spans["trajectory"], and agent_spans["tools_called"] as just the tool names.
- Save agent_spans to trajectories.pkl with to_pickle (not CSV — the trajectory column holds nested lists of dicts).
- Build a viewable copy: input, output, and tools_called joined with ", " (or "(none)" if empty). Call save_view(viewable, title="Task 1 — Trajectories", subtitle=f"{len(agent_spans)} agent runs", name="task1-trajectories") from df_view.
- When done, print exactly: Trajectories built — N agent runs, M tool calls, printed above. (fill in N, M)

<!-- Task 4-C — Categorize — run batch -->
Run the curated synthetic queries through the agent and refresh the traces dataframe. Be concise: write and run the script, print a short summary, don't explain unless something fails.

- Parse synthetic_queries.md the same way as queries.md (## heading, - bullets).
- Before sending, pull existing top-level spans (parent_id null, renamed to input/output, plus context.span_id). Skip any query whose exact text is already an input.
- Run every remaining query through ask_agent with asyncio, in order. Print [i/N] sending ... or [i/N] skip (already traced).
- Pull the spans dataframe again (parent_id null, input/output renamed, plus context.span_id), call save_view(df, title="Task 4-C — Synthetic traces", subtitle=f"{len(df)} runs total in project") from df_view.
- When done, print exactly: Synthetic batch run — N queries, M total traces in Phoenix.
- If this run stops early, paste this same prompt again — it will skip queries already traced and continue.

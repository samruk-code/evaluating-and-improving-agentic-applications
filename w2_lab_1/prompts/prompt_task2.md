<!-- Task 2 — Expand the query set -->
Run the full query bank in queries.md through the agent, then refresh the traces dataframe. Be concise: write and run the script(s), print a short summary, don't explain unless something fails.

- Parse queries.md: for each "## Section Name" heading, collect its "- " bulleted lines as queries. Preserve duplicates (the Consistency tests section repeats the same question 3 times on purpose — keep all 3 lines).
- Print how many queries you found per section, and the total.
- Before sending anything, pull the current top-level spans the same way as Task 1 (parent_id null, renamed to input/output, plus context.span_id). Build a set of inputs already in Phoenix.
- Run every query through ask_agent (from app) with asyncio, in order. Skip any query whose exact text is already an input (covers the 15 Module 1 traces and a partial previous run). New queries are traced to Phoenix automatically.
- Print progress as you go: [i/N] sending ... or [i/N] skip (already traced).
- After the batch finishes, pull the spans dataframe again the same way as Task 1 and call save_view(df, title="Task 2 — All traces", subtitle=f"{len(df)} agent runs so far") from df_view.
- When done, print exactly: Query bank run — N new queries, M total traces in Phoenix. (with N and M filled in)
- If this run stops early, paste this same prompt again — it will skip queries already traced and continue.

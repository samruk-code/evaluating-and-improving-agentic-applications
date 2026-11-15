<!-- Task 4-C — Categorize — worksheet -->
Read synthetic_queries.md and create an editable worksheet for Task 4-C. Be concise: write the file, print a short summary, don't explain unless something fails.

- Parse synthetic_queries.md the same way as queries.md (## heading, - bullets) to collect all curated queries, in order.
- Pull each query's agent answer from the current spans, the same way as Task 1/2: parent_id null, rename attributes.input.value to input and attributes.output.value to output. Do not ask me which traces to use. If the same query text has more than one top-level span, keep the latest: sort by start_time descending. If a query has no matching span, print which and stop — run the batch first.
- Write task4c.md: start with a short header explaining the taxonomy (pass, hallucination, faithfulness_drift, scope_violation, reasoning_error, format_inconsistency) and severity (low, medium, high, or n/a for a pass) — same taxonomy as Task 3. State clearly that every row must have both category and severity filled in before the next step, or the save script will refuse to write anything. Then one entry per query, in this exact 4-line format, with category and severity left blank. Put the answer on one line: replace newlines with spaces, wrap it in double quotes, and write any double quote inside the answer as \".
  - query: "<exact query text>"
    answer: "<agent output, one line>"
    category: 
    severity: 
- When done, print exactly: task4c.md created — N queries, ready for you to label. (with N filled in)

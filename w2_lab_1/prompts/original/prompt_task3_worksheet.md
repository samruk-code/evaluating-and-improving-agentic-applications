<!-- Task 3 — Categorize the failures — worksheet -->
Read queries.md and create an editable worksheet for Task 3. Be concise: write the file, print a short summary, don't explain unless something fails.

- Parse queries.md the same way as Task 2 (## headings, - bullets). Do not put every query into the worksheet. Label only the fixed set below plus the questions I added in four sections.
- Always include these 10 queries, using the exact text from queries.md. If any of them is missing, print which and stop:
  1. What's the price of the Chino Pants?
  2. Is the Slip-On Canvas in stock?
  3. Do you have a cashmere scarf?
  4. Is the Denim Jacket machine washable?
  5. Do you offer gift wrapping?
  6. What should I pack for a rainy weekend camping trip?
  7. What should I pack for a rainy weekend camping trip?
  8. What should I pack for a rainy weekend camping trip?
  9. I need swim trunks and a beanie for a lake trip — what do you have?
  10. got anyth in olive??
- Then, in file order, add every other "- " bullet under Hallucination bait, Faithfulness drift, Scope violations, and Multi-part except these four examples (they stay in the bank and are not labeled):
  - I'm looking for a pair of polarized sunglasses.
  - Does the Raincoat run true to size?
  - Can I apply a discount code at checkout?
  - What's your cheapest jacket, and does it come in black?
- Do not include any other Baseline, Consistency tests, or Odd phrasing queries. When I added one question in each of those four sections, N is 14. Do not add or remove queries to reach 14.
- Pull each selected query's agent answer from the current spans, the same way as Task 1/2: parent_id null, rename attributes.input.value to input and attributes.output.value to output. Do not ask me which traces to use. If the same query text has more than one top-level span, sort those spans by start_time ascending and pair them in that order with the repeated entries, so each entry shows the answer from its own run. If a repeated entry has no span left, reuse the latest answer.
- Write labels.md. The first lines, before any entry, are exactly these two, so the choices are visible at the top of the file:
  Allowed category: pass, hallucination, faithfulness_drift, scope_violation, reasoning_error, format_inconsistency
  Allowed severity: low, medium, high, n/a
  Then one short line: the first entries are still for me to label, and the query and answer lines must stay exact. n/a is only for a pass.
- One entry per selected query, in this exact 4-line format. Put the answer on one line: replace newlines with spaces, wrap it in double quotes, and write any double quote inside the answer as \".
  - query: "<exact query text>"
    answer: "<agent output, one line>"
    category: 
    severity: 
- Do not ask which queries to label or which to leave blank. Always leave the first 7 selected queries blank — empty category and severity — even when the query text repeats. If there are fewer than 7, leave all of them blank. For every query after those first 7, fill category and severity yourself from that entry's answer. Use only the taxonomy values above.
- In the file, put those blank entries first, in selection order, then the filled entries, in selection order.
- When done, print exactly: labels.md created — N queries, K left for you to fill in. N is how many entries you wrote. K is 7, or N when N is under 7.

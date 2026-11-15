<!-- Task 4-A — Generate -->
Generate synthetic customer queries with the Anthropic API and save the raw output. Be concise: write and run the script, don't explain unless something fails.

Write generate_synthetic.py using the anthropic package (Anthropic() client, model "claude-haiku-5-5", max_tokens 2000) with this exact prompt:

"You are generating realistic customer queries to stress-test a chatbot for \"Northwind Apparel,\" an online clothing retailer that sells tops, bottoms, outerwear, shoes, and accessories.

Generate 21 customer queries that a real shopper might send to this chatbot. Vary across these dimensions:

- REGISTER: formal, casual, slang, abbreviated
- INTENT: product questions, complaints, recommendations, comparisons, returns, browsing
- COMPLEXITY: simple lookups, multi-part, conditional (\"X under $Y\")
- LANGUAGE: include typos, missing punctuation, all-lowercase, partial sentences, ESL phrasings
- EMOTIONAL STATE: mostly neutral, some frustrated, polite, urgent, confused
- SCOPE: include questions outside the chatbot's likely knowledge (shipping, sizing advice, store hours, kids' sections, international orders, price matching, exchanges)

Constraints:
- Refer to products by description when natural (\"that red plaid shirt\"), not always by name.
- Mix unusually short queries (\"size 32?\") with unusually long ones.
- Output ONLY the queries, one per line. No numbering. No quotes. No commentary."

Split the response on newlines, strip blanks, and write the result to synthetic_queries_raw.md as one "- " bullet per line under a single "## Raw generated queries" heading (same bullet format as queries.md).
When done, print exactly: Generated N synthetic queries. (with N filled in)

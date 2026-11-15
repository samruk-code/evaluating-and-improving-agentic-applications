<!-- Task 5 — Read the traces and find failure modes (optional prompt) -->
Lay out the last batch run's traces from Phoenix so I can read them. Be concise: run one script, don't explain unless something fails. Do not restart the app and do not re-run batch.py.

- Read the traces with the Phoenix client — not the UI, not sqlite on phoenix.db, not GET /v1/spans:
  from phoenix.client import Client
  df = Client(base_url="http://localhost:6006").spans.get_spans_dataframe(project_identifier="dlai-ecommerce-agent", limit=2000)
- One customer question = one root span named "ask_agent": the question is in attributes.input.value and the final answer is in attributes.output.value. Under it you also get search_catalog, check_inventory and a ClaudeAgentSDK.query span for the model call itself.
- The project also holds sanity checks and any earlier runs, so sort by start_time and take the LAST 15 ask_agent spans.
- Print one line per query in start_time order: the question, then its answer summarized in 20 words or less. Keep the three identical "work from home" queries next to each other so I can compare them.
- Don't judge the answers — just lay them out so I can read them.

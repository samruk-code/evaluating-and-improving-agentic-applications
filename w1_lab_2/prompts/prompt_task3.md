<!-- Task 3 — Add Phoenix tracing to the agent -->
Add Arize Phoenix tracing to app.py. Use the Phoenix skill you have loaded. Be concise: make the edits and restart the app; don't explain unless something fails. Do not hard-code API keys.

In app.py:
- Keep `import sitecustomize` as the first import. It turns off FastAPI's built-in HTTP traces so Gradio's startup checks are not stored in Phoenix. Do not remove it.
- After the imports, default PHOENIX_COLLECTOR_ENDPOINT to http://localhost:6006, then call register(project_name="dlai-ecommerce-agent", auto_instrument=True, endpoint="http://localhost:6006/v1/traces") and get a tracer named "ecommerce-agent".
- Decorate search_catalog with @tracer.chain.
- Decorate check_inventory with @tracer.tool.
- Decorate ask_agent with @tracer.chain.

After editing, restart with: bash run.sh
Ask one question through the app (or confirm the server is up). When done, print exactly: Phoenix + Agent are ready and communicating.

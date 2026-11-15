<!-- Task 2 — Run the agent -->
Start the Gradio app in the background by running: bash run.sh
Be concise: run the command, don't explain unless something fails. Do NOT run python3 app.py in the foreground — it gets killed when the command returns. Do not edit app.py and do not create a virtualenv; dependencies are already installed.

ANTHROPIC_API_KEY is already exported; never print or hard-code it. After starting, confirm http://localhost:7860 answers (curl should return 200). When it works, print exactly: Gradio Agent App is working now.

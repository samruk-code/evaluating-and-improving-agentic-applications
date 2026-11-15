# Northwind Apparel — Continue the lab locally

This folder is your lab download. It includes the project files from your
workspace at the moment you downloaded, and the task prompts you saved in
the browser. The original prompts are in `prompts/original/` for comparison.

You are free to edit the prompts or write your own. Their purpose is to help
you accomplish each task, and experimenting is part of the lab.

## 1. Prepare your environment

Use Python 3.10+ and a Bash terminal. On Windows, use WSL for these scripts.
Extract the ZIP, then open a terminal in the extracted folder:

```bash
cd northwind-apparel-lab-m3
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key"
```

Keep the key in your environment. The course environment's key is not part
of this download.

## 2. Choose a coding assistant

You can use Codex, OpenCode, or another coding assistant. Give it
`instructions.md` and the files in `prompts/`. When a task prompt refers to
OpenCode, give that prompt to the assistant you chose. Saved edits from the
lab are already in `prompts/`. The wording you started from is in
`prompts/original/`.

The Phoenix guidance that was preloaded on the platform is included here as
`phoenix-skill.md`.

## 3. Start Phoenix and the app

Start Phoenix and the app, then follow the same Before you begin check
and Tasks 1–6 with your local coding assistant:

```bash
PHOENIX_DATA_DIR=./phoenix-data bash phoenix-start.sh   # UI: http://localhost:6006 — already has 57 traces
bash run.sh                                              # App: http://localhost:7860
```

There is no bundled Data Explorer or in-place editor outside this lab
UI. After `save_view(...)`, open the matching file under
`dataframe_exports/` (for example `task1-labeled.html`). Edit
`policy_compliance_prompt.md` in any text editor. Do not edit
`queries.md` — the merge in Task 1 depends on its text matching the
stored traces.

If Phoenix opens with an empty trace list, set the time range to
**Last 30 days** / **Last month**. Open the Gradio app at
http://localhost:7860 rather than relying on an embed.

| Service | URL |
| ------- | --- |
| Phoenix UI | http://localhost:6006 |
| Gradio agent | http://localhost:7860 |
| Data Explorer | open a file directly under `dataframe_exports/`, e.g. `task1-labeled.html` |

If a port is busy, set `PHOENIX_PORT=6007` (and point
`PHOENIX_COLLECTOR_ENDPOINT` / the `register(...)` endpoint in `app.py`
at that port) or free port 7860 before `bash run.sh`.

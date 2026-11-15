# Northwind Apparel — Continue the lab locally

This folder contains the support agent, product data, Python requirements,
startup scripts, test questions, and all five task prompts. The lab download
includes the app files from your workspace at download time and the prompt
versions you saved in the browser. The original prompts are also available
in `prompts/original/` for comparison.

You are free to edit the prompts or write your own. Their purpose is to help
you accomplish each task, and experimenting is part of the lab.

## 1. Prepare your environment

Use Python 3.12 and a Bash terminal. On Windows, use WSL for these scripts.
You'll need internet access to install packages and call the language model.
Extract the ZIP, then open a terminal in the extracted folder:

```bash
cd northwind-apparel-lab
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Set your own Anthropic API key in the same terminal:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

The support agent uses Claude Haiku 5.5 (`claude-haiku-5-5`) through the
Claude Agent SDK. Choosing Codex or another assistant as your coding
assistant does not change that model: you still need an Anthropic API key
for its customer responses.
Keep the key in your environment, rather than writing it into the code or
your prompts. The course environment's key is not part of this download.

If you open another terminal later, activate `.venv` and set the key there
before running the app or your coding assistant.

## 2. Choose a coding assistant

You can use Codex, OpenCode, or another coding assistant that can read and
edit the project files and run terminal commands.

For Codex, follow the installation instructions in the
[official Codex CLI guide](https://learn.chatgpt.com/docs/codex/cli), then
start it from the project folder:

```bash
codex
```

Follow the sign-in instructions on the first launch. Codex authentication
is separate from the Anthropic key used by this app. See the
[Codex CLI guide](https://learn.chatgpt.com/docs/codex/cli) for current setup
and sign-in options.

Give your assistant this starting prompt, or adapt it:

```text
Read README.md, instructions.md, and phoenix-skill.md in this folder.
Help me continue the Northwind Apparel tracing lab locally. Inspect app.py
first to see which tasks are already complete. Use the prompts in prompts/
as guides; they include my saved edits. Work on one task at a time and
verify its result before continuing. Use the .venv environment and the
ANTHROPIC_API_KEY already set in the environment. Never print the key.
```

When a task prompt refers to OpenCode, give it to the assistant you chose.
The Phoenix guidance that was preloaded on the platform is included here
as `phoenix-skill.md`; ask your assistant to read it before adding tracing.

The supplied prompts assume packages and the API key are already available.
Step 1 above prepares those for local use. They also assume ports 6006 and
7860; keep those defaults unless you update the URLs and tracing endpoint.

## 3. Start Phoenix and the support agent

Ask your assistant to follow `prompts/prompt_task1.md`, then
`prompts/prompt_task2.md`, or run these commands yourself in the activated
environment:

```bash
PHOENIX_DATA_DIR=./phoenix-data bash phoenix-start.sh
bash run.sh
```

Open Phoenix at <http://localhost:6006> and the chat app at
<http://localhost:7860>. Ask a product question in the chat app to confirm
it answers. The browser terminal and course interface are not needed locally.

Both services run in the background. After editing `app.py`, run
`bash run.sh` again to restart the app. If a service fails to open, inspect
`phoenix.log` or `app.log` in this folder.

## 4. Add tracing, run questions, and review

Use [instructions.md](instructions.md) for the task goals and review questions.
The prompt files correspond to the same five tasks:

| Task | Prompt file | Check before continuing |
| --- | --- | --- |
| 1. Start Phoenix | `prompts/prompt_task1.md` | Phoenix opens on port 6006. |
| 2. Run the agent | `prompts/prompt_task2.md` | The chat app answers a question. |
| 3. Add tracing | `prompts/prompt_task3.md` | A new question appears as a trace in `dlai-ecommerce-agent`. |
| 4. Run the batch | `prompts/prompt_task4.md` | The batch finishes and its traces appear. |
| 5. Review traces | `prompts/prompt_task5.md` (optional) | You have notes supported by trace evidence. |

For example, tell Codex:

```text
Read prompts/prompt_task3.md and phoenix-skill.md. Check whether app.py
already has that tracing setup. Add any missing tracing without duplicating
the existing setup, restart the app, and help me verify a new trace.
```

If you completed Task 3 before downloading, tracing may already be present.
Ask a new question and check Phoenix before making further tracing changes.
Previous Phoenix traces and chat sessions are not included in the ZIP;
your local Phoenix instance starts with its own data.

Run the test questions with:

```bash
python3 batch.py
```

The provided batch has 15 questions and runs them one at a time. If you
changed `batch.py`, the count and progress messages may differ. Read the
full answers and their supporting steps in Phoenix, then write your notes.

## 5. Keep experimenting

Edit files in `prompts/` directly as you try different ways to ask for help.
Use `prompts/original/` whenever you want to compare with the supplied guides.
Save your project and notes so you can build on them in the next module.

To stop the services:

```bash
bash stop.sh
bash phoenix-stop.sh
```

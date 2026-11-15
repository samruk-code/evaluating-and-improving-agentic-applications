# Module 1, Lab 2: Task guide

Start with [README.md](README.md) to set up your local environment.

These tasks refer to the course interface. Locally, open Phoenix at http://localhost:6006 and the chat app at http://localhost:7860. Give the linked prompt files to your coding assistant, or write your own. The prompts are guides; adapt them freely to meet each task's goal.

### Task 1: Start Phoenix

**Goal:** Get Phoenix running so it's ready to collect the agent's traces
once you add tracing in Task 3.

1. Send this prompt to OpenCode, which will:
   - stop any copy of Phoenix that's already running
   - start Phoenix, the tool that will record the agent's traces, and keep its
     data in the `phoenix-data` folder
   - check that Phoenix is responding

   When OpenCode prints `Phoenix is ready to be used`, it's done.

[Open this task's prompt](prompts/prompt_task1.md)

2. Click the **Check Phoenix** button at the top right of the lab to confirm
   that Phoenix opens. The first time, a short tour opens instead of Phoenix.
   It uses example data to show the projects, traces and panels you'll use in
   later tasks. Click **Next** to go through it, or **Skip, go to Phoenix** to
   go straight to Phoenix.

   Phoenix is empty for now. Your traces will show up once you add tracing in
   Task 3.

<details>
### Troubleshooting

If Phoenix doesn't open, try these:

- Send the Task 1 prompt again.
- Ask OpenCode to check `phoenix.log` and tell you what went wrong.
- If it says the database is locked, ask OpenCode to restart Phoenix with a
  different data folder, for example `./phoenix-data-2`.
- To check it yourself, see **Task 1** under **Working in the terminal** at
  the end of the tasks.





### Task 2: Run the Northwind agent

**Goal:** Check that the agent answers questions.

You do this before adding tracing in Task 3. That way, if something breaks then,
you'll know it's the tracing and not the app.

1. Send this prompt to OpenCode, which will:
   - start the agent's chat app in the background
   - check that the app is responding

   When OpenCode prints `Gradio Agent App is working now`, it's done.

[Open this task's prompt](prompts/prompt_task2.md)

2. Click the **Preview App** button at the top right of the lab, and ask:
   **What colors does the Classic Tee come in?** Check that the agent answers.

   This chat won't appear in Phoenix, because the app doesn't send traces until
   Task 3.

<details>
### Troubleshooting

If the chat app doesn't open or the agent doesn't answer, try these:

- Send the Task 2 prompt again.
- Ask OpenCode to check `app.log` and tell you what went wrong.
- To check it yourself, see **Task 2** under **Working in the terminal** at
  the end of the tasks.





### Task 3: Add tracing and inspect one request

**Goal:** Add tracing to the agent, then look at the trace for one question.

1. Send this prompt to OpenCode, which will:
   - connect the agent to Phoenix, and mark which of its steps to record, in
     `app.py`, the agent's code
   - restart the app so the tracing takes effect
   - check that the app is running

   When OpenCode prints `Phoenix + Agent are ready and communicating`, it's done.

[Open this task's prompt](prompts/prompt_task3.md)

2. To see what changed, ask OpenCode: "Show me what you changed in app.py."
   If OpenCode shows only part of its answer, click it in the terminal to expand
   it. Each step the agent now records has a line starting
   with `@tracer` just above it, for example:

   ```python
   @tracer.tool
   def check_inventory(product_id: str) -> dict:
       return retrieval.check_inventory(product_id)
   ```

3. Click the **Preview App** button at the top right of the lab, and ask the
   Classic Tee question again. Your question in Task 2 wasn't recorded, because
   tracing wasn't on yet. This one will be.
4. Click the **Check Phoenix** button. Phoenix opens on its **Projects** page. A
   project is a group of traces from one app, and this lab's project is named in
   the code OpenCode added: `register(project_name="dlai-ecommerce-agent")`.
   You'll see a card for **dlai-ecommerce-agent**, showing how many traces it
   holds, and an empty **default** project you can ignore. Click
   **dlai-ecommerce-agent** to open it.
5. The project opens on a table of **spans**, newest first. Above it is a
   filter box that reads `parent_id is None`. That filter shows only
   top-level spans, so each row is one trace: one question to the agent, with
   its input and output. The table may also include other entries, such as
   `GET /`, that don't come from the agent.

   To show only the agent's runs, replace the filter with
   `name == "ask_agent"` and press `Enter`. Filters like this let you pick out
   just the spans you want to look at. Your Classic Tee question from step 3
   should be at or near the top.

6. Click the row with your Classic Tee question. A panel opens: on the left is
   the trace's **span tree**, and on the right are the details of whichever
   span you select, including its **Input** and **Output**. Click each span in
   the tree to see what it recorded:

   - **`ask_agent`**, the root span: the customer's question and the final
     answer they saw.
   - **`search_catalog`**: the question, and the products the search
     returned.
   - **`check_inventory`**, one for each product found: the product it looked
     up, and whether that product is in stock and how many there are.
   - **`ClaudeAgentSDK.query`**, the model call: the question and the answer
     Claude wrote. Its **Attributes** also show which model answered and how
     many tokens it used.

   The answer should only use what `search_catalog` and `check_inventory`
   returned. Comparing them is how you'll check answers in Task 5. If the
   search finds no products, there are no `check_inventory` spans.

**What the tracing code does**

- `register()` connects the app to Phoenix and names the project
  `dlai-ecommerce-agent`. With `auto_instrument=True`, it also records model
  calls automatically.
- `@tracer.chain` on `ask_agent` and `search_catalog` records each one as a
  span for a step in the pipeline.
- `@tracer.tool` on `check_inventory` records each inventory check as a tool
  span.

<details>
### Troubleshooting

If no trace appears, try these:

- The Phoenix panel does not always update right away. Wait 20 seconds, then
  click **Refresh** or **Open in new tab** at the top right of the Phoenix
  panel.
- Make sure you asked a new question in step 3.
- Tell OpenCode what you see in Phoenix and ask it to check the tracing setup
  in `app.py`.
- To check it yourself, see **Task 3** under **Working in the terminal** at
  the end of the tasks.





### Task 4: Run the test questions

**Goal:** Run 15 test questions through the agent.

One trace shows how the agent handled one question. A varied set of questions
shows patterns: which kinds of questions it handles well, and which it gets
wrong. You'll look for those patterns in Task 5.

The 15 questions include:

- simple product lookups, such as the Classic Tee's colors and the Wool
  Beanie's price
- questions with several parts, such as the Classic Tee in medium and the
  return policy
- the same gift question, asked three times in a row
- a care question about the merino wool sweater
- two questions the app has no data for: an order status and a customer
  service phone number

To see all 15 questions before you start, ask OpenCode: "Show me the questions in
batch.py."

1. Send this prompt to OpenCode, which will run `batch.py`, a script
   that sends the 15 questions to the agent one at a time. It usually takes 2–5
   minutes. The script prints `Query N/15` with each question, and the first line
   of its answer afterward.

   When OpenCode tells you how many traces to expect, 15, it's done.

[Open this task's prompt](prompts/prompt_task4.md)

2. Click the **Check Phoenix** button and open **dlai-ecommerce-agent**. The 15
   new runs are at the top, above your Classic Tee question from Task 3. If other
   entries get in the way, filter the table with `name == "ask_agent"`, as in
   Task 3.

   The answers won't appear in the chat app. You'll read them in Phoenix in
   Task 5.

<details>
### Troubleshooting

If the new runs don't appear in Phoenix, wait 20 seconds, then click **Refresh**
or **Open in new tab** at the top right of the Phoenix panel.

If the batch stops or seems stuck, try these:

- Wait for the current run to finish or stop before starting another.
- Ask OpenCode to check the batch output and tell you what went wrong. It
  shouldn't rewrite `batch.py` unless the script fails.
- To check it yourself, see **Task 4** under **Working in the terminal** at
  the end of the tasks.





### Task 5: Review the traces and record what you find

**Goal:** Find where the agent's answers go wrong, and what in each trace shows
it.

1. Click the **Check Phoenix** button, open **dlai-ecommerce-agent**, and find
   the 15 runs from Task 4. If other entries get in the way, filter with
   `name == "ask_agent"`.
2. *Optional:* To see all 15 at a glance, send this prompt to OpenCode, which will
   list the 15 questions, each with a short summary of its answer. It
   doesn't judge the answers. That's up to you. If OpenCode shows only part of
   its answer, click it in the terminal to expand it.

[Open this task's prompt](prompts/prompt_task5.md)

3. For each question you look into, open its trace. Read the question and final
   answer in `ask_agent`, then compare the answer with what `search_catalog` and
   `check_inventory` returned. Anything in the answer that isn't in those outputs
   came from the model, not the store's data.

Look at these questions in particular:

- **Product searches and questions with several parts:** Did the search return
  relevant products? Did the answer cover every part of the question?
- **The three identical gift questions:** Compare the three answers and what
  each was based on. Different wording or suggestions aren't errors by
  themselves. Look for answers that contradict each other, or claims the data
  doesn't support.
- **The merino wool sweater question:** The catalog only says it's machine
  washable on a wool cycle. Did the answer add care instructions beyond that?
- **The order status and phone number questions:** The app has no order records
  or contact details. Did the agent say it couldn't answer, or did it make up
  details?

The agent doesn't always answer the same way, so your results may not match
someone else's. Record what you see, including questions the agent handled well.

**Record what you found**

For each problem, note the question, what went wrong, and the trace evidence
that shows it.

Then answer:

1. What did reviewing several traces show you that one chat answer would have
   missed?
2. Which problem would be hardest to explain from the final answer alone? How
   did the trace help?

Write your notes in the box below and click **Save notes**. They're saved in
`review_notes.md` and included when you download the lab. The last progress
circle turns green when every section has an answer.

<div class="review-notes"></div>

In Module 2, you'll add more test questions, label each answer with a fixed set
of categories, and save the failures as a dataset in Phoenix.



### Working in the terminal (optional)

You don't need this section to complete the lab. It shows the terminal
commands behind each task, for when you want to see what OpenCode does or
fix a problem yourself. OpenCode chooses its own commands, so what it runs
may differ slightly.

**Switching between OpenCode and the terminal**

- To close OpenCode and work directly in the terminal, type `/exit` in
  OpenCode, or press `Ctrl+C` twice. You'll see a plain command prompt.
- To reopen OpenCode, type `opencode` and press `Enter`.

**Task 1: Start Phoenix**

What OpenCode runs:

```bash
bash phoenix-stop.sh 2>/dev/null || true
PHOENIX_DATA_DIR=./phoenix-data bash phoenix-start.sh
curl -s -o /dev/null -w "%{http_code}" http://localhost:6006
```

These stop any Phoenix that's already running, start Phoenix with its trace
data saved in `./phoenix-data`, and check that it answers. A response of
`200` or `307` means Phoenix is up.

If something goes wrong:

- Read the last lines of the log: `tail -n 50 phoenix.log`
- Check whether Phoenix is running: `pgrep -af 'phoenix serve'`
- If the database is locked, start Phoenix with a different data folder:
  `PHOENIX_DATA_DIR=./phoenix-data-2 bash phoenix-start.sh`

**Task 2: Run the Northwind agent**

What OpenCode runs:

```bash
bash run.sh
```

`run.sh` starts the app in the background, so it keeps running while you do
other things. It stops any copy that's already running first, then waits
until the app answers and prints `Gradio Agent App is working now.` Starting
the app with `python3 app.py` instead ties up the terminal, and the app stops
when that command ends.

If something goes wrong:

- Watch the app's log as it runs: `tail -f app.log` (press `Ctrl+C` to stop
  watching)
- Restart the app: `bash run.sh`
- Stop the app: `bash stop.sh`
- Check that the API key is set, without printing it:
  `test -n "$ANTHROPIC_API_KEY" && echo "key is set"`

**Task 3: Add tracing and inspect one request**

What OpenCode changes in `app.py`. After the imports, it adds:

```python
import os
from phoenix.otel import register

os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
tracer_provider = register(
    project_name="dlai-ecommerce-agent",
    auto_instrument=True,
    endpoint="http://localhost:6006/v1/traces",
)
tracer = tracer_provider.get_tracer("ecommerce-agent")
```

`import sitecustomize` stays above `import gradio`. That module turns off FastAPI's HTTP traces, so Gradio's startup checks do not appear in Phoenix. Agent spans are unchanged.

Further down, it adds a decorator on the line above each function it traces.
Nothing inside the functions changes:

```python
@tracer.chain
def search_catalog(user_query: str) -> list:
    return retrieval.search_catalog(user_query)


@tracer.tool
def check_inventory(product_id: str) -> dict:
    return retrieval.check_inventory(product_id)


@tracer.chain
async def ask_agent(user_query: str) -> str:
    ...
```

Finally, it restarts the app with `bash run.sh`.

If something goes wrong:

- Look for errors after the restart: `tail -n 50 app.log`
- Confirm the Phoenix packages are installed:
  `pip show arize-phoenix arize-phoenix-otel`
- Confirm Phoenix is still running: `pgrep -af 'phoenix serve'`
- If there's no `ClaudeAgentSDK.query` span, check how `app.py` calls the
  model. It must call `claude_agent_sdk.query(...)`. A separately imported
  `query` won't be traced, because `register()` swaps in a traced version of
  `claude_agent_sdk.query` when it runs, and a copy imported earlier keeps
  the original.

**Task 4: Run the test questions**

What OpenCode runs:

```bash
python3 batch.py
```

The script sends the 15 questions one at a time, through the same
`ask_agent` function the chat app uses. It ends with
`Done. 15 queries in N minutes.` and `Expect 15 new traces in Phoenix.`

If something goes wrong:

- If single questions work in the chat app but the batch hangs, the problem
  is the batch script, not Phoenix or tracing.
- Stop the run: press `Ctrl+C`.
- If no `Query N/15` line appears after about a minute, the script is stuck.
  If it was edited, restore the original:
  `cp /opt/starter/batch.py batch.py`
- Check that the app loads without errors:
  `python3 -c "from app import ask_agent"`
- Run it again: `python3 batch.py`

**Task 5: Review the traces and record what you find**

What OpenCode runs for the optional prompt, roughly:

```python
from phoenix.client import Client

df = Client(base_url="http://localhost:6006").spans.get_spans_dataframe(
    project_identifier="dlai-ecommerce-agent", limit=2000
)
roots = df[df["name"] == "ask_agent"].sort_values("start_time").tail(15)
for i, (_, row) in enumerate(roots.iterrows(), 1):
    answer = " ".join(str(row["attributes.output.value"]).split())
    print(f"{i:2d}. Q: {row['attributes.input.value']}\n    A: {answer[:160]}\n")
```

This reads the spans from Phoenix, keeps the 15 most recent `ask_agent`
runs, and prints each question with the start of its answer. The prompt
names the Phoenix client on purpose: reading traces back uses a different
part of Phoenix from sending them, and without that hint OpenCode often
guesses at a method this version of Phoenix doesn't have.



---

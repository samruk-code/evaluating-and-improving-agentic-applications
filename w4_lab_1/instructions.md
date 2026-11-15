# Module 4, Lab 1: Task guide

Start with [README.md](README.md) to set up your local environment.

These tasks refer to the course interface. Locally, open Phoenix at http://localhost:6006 and the chat app at http://localhost:7860. Give the linked prompt files to your coding assistant, or write your own. The prompts are guides; adapt them freely to meet each task's goal. Saved edits from the lab are already in `prompts/`. The wording you started from is in `prompts/original/`.

### Task 1: Run the test set and build trajectories

**Goal:** Have OpenCode run the 8 test questions through the agent, and build a
table of what the agent did for each one.

For each question, the table records the tools the agent called, in order. That
list is called a **trajectory**. For example, here's a correct trajectory for
"I'm CUST-001 and I want to return the shoes I bought last week, order 4521.":

| Step | Tool | What the agent passes to it |
|---|---|---|
| 1 | `get_customer` | Customer CUST-001 |
| 2 | `order_lookup` | Order 4521 |
| 3 | `process_refund` | Order 4521, $89.99 |

Each test question also has an entry in a file that comes with the lab,
`query_spec.py`, which says what a correct run looks like. Tasks 2 and 3 compare
the agent's runs with it.

**Only run this task once.** Any refund the agent makes stays in the store
database, and a second run would add more refunds. Those can make Task 3 give a
pass when it shouldn't. If you do run it twice, ask OpenCode to empty the
`refunds` table, send the prompt below one more time, and then redo any later
tasks you've already done.

1. Send this prompt to OpenCode, which will:
   - have the agent answer all 8 test questions
   - pull each run's tool calls from Phoenix and build the table
   - save the table to the Task 1 tab in **Data Explorer**

   Don't use **Preview App** until it finishes, because a question you ask
   during the run gets counted as an extra run.

   It takes about 1–2 minutes. When OpenCode prints
   `Trajectories built — N agent runs, M tool calls, printed above`, it's done.
   You should see 8 agent runs. If you don't, ask OpenCode to find out why and
   fix it without running the questions again.

[Open this task's prompt](prompts/prompt_task1.md)

2. To see the full table, click the **Data Explorer** button at the top right of
   the lab, and open the Task 1 tab. The `tools_called` column lists each run's
   tools, in order.

**See a run in Phoenix**

1. Click **Check Phoenix**, open the `dlai-ecommerce-agent` project, and click a
   run whose question asks for a refund.
2. The top row, `ClaudeAgentSDK.query`, holds the question and the final answer.
   The rows under it are the tool calls, named `mcp__northwind__` followed by the
   tool's name.
3. Click a tool call. **Input** shows what the agent passed to the tool, and
   **Output** shows what the tool returned.



### Task 2: Evaluate the tool calls

**Goal:** Have OpenCode run two evaluators on your 8 runs, `tool_selection` and
`tool_invocation`, so that each run gets a pass or fail from both.

An agent's answer can sound fine even if it got there the wrong way, for example
by looking up the wrong order. So you also want to check what it did. When you
already know which tools a question needs, you can do that like a unit test:
write down the correct tools ahead of time, then compare the agent's run with
them.

That's what these two evaluators do. Both are plain code, with no LLM, so they
give the same result every time. They compare each run with a file that comes
with the lab, `query_spec.py`. For each of the 8 test questions, it lists the
tools a correct run should call and the details it should pass. For example, for
"Where's my order 4521?", it lists `order_lookup` with order 4521. To see the
whole file, ask OpenCode: "Show me query_spec.py." Don't change it.

Each evaluator checks one thing against that file:

- `tool_selection` checks that the agent called the right tools. Did it call
  `order_lookup`? Extra tool calls are fine, as long as the listed tools are
  there.
- `tool_invocation` checks that the agent gave those tools the right details.
  Did it look up order 4521, and not some other order?

1. Send this prompt to OpenCode, which will:
   - build `tool_selection` and `tool_invocation`
   - run both on your 8 runs, comparing each run with `query_spec.py`
   - print the failures, and save the results to the Task 2 tab in **Data
     Explorer**

   When OpenCode prints
   `tool_selection + tool_invocation scored — failures printed above`, it's done.

[Open this task's prompt](prompts/prompt_task2.md)

2. Click **Data Explorer**, open the Task 2 tab, and look at the rows labeled
   `fail`. A fail doesn't always mean the agent did something wrong. For example:

   | Question | `tools_called` | `tool_selection` |
   |---|---|---|
   | refund order 4521 please | `order_lookup` | `fail` |
   | hi quick one — order 4512, has it shipped yet | `get_order_tracking` | `fail` |

   In the first row, the correct tools listed in `query_spec.py` were
   `get_customer` and `process_refund`. The agent called `order_lookup` instead,
   so it got a `fail`. But the agent didn't do anything wrong. The customer didn't
   give a customer ID, so the agent had no way to verify them, and it was right
   not to refund.

   In the second row, the correct tool listed in `query_spec.py` was
   `order_lookup`. The agent called `get_order_tracking` instead, so it got a
   `fail`. But the agent didn't do anything wrong here either. The tracking tool
   is a good way to answer "has it shipped yet," so the file is too strict.

   So when you see a fail, ask whether the agent is wrong or the file is.

   In your table, these two rows also show a `pass` from `tool_invocation`. Ignore
   it. It only checks the details given to a tool if the agent called that tool.
   The agent didn't call the tools listed for these questions, so there was nothing
   to check.

   Here's what a real fail looks like: a customer asks about order 4512, and the
   agent calls `order_lookup` with order 4521. That's a real order for a different
   customer, so the lookup works, and the agent tells this customer about someone
   else's order.

   The agent doesn't always call the same tools, so your table may not match these
   examples.

The table only shows tool names. To see what the agent passed to a tool, open
the run in Phoenix and click the tool's row, as in Task 1.

These checks also can't catch everything, because they don't read the answer. If
the agent checks the Slip-On Canvas, gets 0 in stock, and still says it's
available, both checks pass.

If every row passes, that's fine, and you can move on to Task 3. Don't run Task 1
again to try to get a fail, because that could add more refunds.

### Troubleshooting

If the `fail` rows don't match the console, check the counts. The number of
`fail` rows in each column should match the failure count the console printed.
If every row says `fail`, or every row says `pass`, and the console disagrees,
the script compared the whole score, which is a dict, to a number. Ask OpenCode
to read the score with `c["score"]` and run the script again.





### Task 3: Evaluate the outcome

**Goal:** Have OpenCode run a third evaluator, `outcome`.

Like the two in Task 2, it's plain code, with no LLM. It checks that a refund
happened on the question that should get one, and on no other question.

The agent can say "Your refund has been processed" whether or not it happened, so
this evaluator doesn't go by the answer. It uses the `refunds` table in the store
database, which records every refund, and the tools the agent called:

- **For the one question that should get a refund** (returning the shoes from
  order 4521): the agent must have called `process_refund`, and the `refunds`
  table must have a row for order 4521 for $89.99.
- **For every other question:** the agent must not have called `process_refund`.
  That includes two refund requests it should turn down: "refund order 4521
  please", which gives no customer ID, and the return of order 4530, which was
  placed 45 days ago, outside Northwind's 30-day window.

1. Send this prompt to OpenCode, which will:
   - build `outcome` and apply these rules to your 8 runs
   - print the failures, and save the results to the Task 3 tab in **Data
     Explorer**

   When OpenCode prints `outcome scored — failures printed above`, it's done.

[Open this task's prompt](prompts/prompt_task3.md)

2. Click **Data Explorer**, open the Task 3 tab, and read the rows labeled `fail`:
   - **On the question that should get a refund:** if `process_refund` isn't in
     `tools_called`, the agent didn't refund, whatever its answer says. If it's
     there, the agent refunded the wrong order or amount.
   - **On any other question:** the agent refunded when it shouldn't have.

   If every row passes, the agent refunded the right order and no others.

A pass isn't always proof. `outcome` looks for a matching row anywhere in the
`refunds` table, so a refund for the wrong amount can still pass if another run
already left the right row. To check a pass, open the run in Phoenix and click
its `mcp__northwind__process_refund` row.

### Troubleshooting

If the results look wrong, try these:

- If every refund check looks wrong, the script may be reading a different
  database. It has to read the same one the agent writes to. Ask OpenCode to
  check that it uses `get_connection` from `db.py`.
- If the `fail` rows don't match the console, check the counts. As in Task 2,
  the number of `fail` rows in the `outcome` column should match the console's
  failure count. If it doesn't, ask OpenCode to read the score with `c["score"]`
  and run the script again.





### Task 4: Evaluate policy compliance

**Goal:** Have OpenCode run two more evaluators: `identity_before_refund`, which is
plain code, and `policy_compliance`, which is an LLM judge.

They check whether the agent followed Northwind's policy:

- Verify the customer with `get_customer` before processing any refund.
- Only refund orders placed within the last 30 days.
- Refund the actual amount from the order record, never an invented refund
  amount.
- Check inventory before claiming an item is available.

`identity_before_refund` checks the first rule: on refund
questions, `get_customer` has to come before `process_refund`. It only checks the
order of the calls, so it still passes if the agent called `get_customer` with an
ID the customer never gave.

`policy_compliance` checks the whole policy, including the
parts that take judgment, such as whether the agent asked for a missing customer
ID instead of guessing one. An answer that adds facts the tool results don't
contain stays `compliant`, unless it also breaks one of the rules above.

You need both. If the judge says `non_compliant`, you still have to find out which
rule broke. If `identity_before_refund` fails, you know right away.

The judge's rubric has the same five parts as the one in Module 3. The difference
is that this judge also sees the run's tool calls, in `{trajectory_text}`, so it
judges what the agent did, not only what it said.

1. Click **Edit policy_compliance_prompt.md** below. The rubric is the part
   between the two `` ``` `` lines. Read it, then close the editor without
   changing anything.

   2. Send this prompt to OpenCode, which will:
   - run `identity_before_refund` on your 8 runs
   - have the judge apply this rubric to each run, including its tool calls
   - print the judge's labels, and save the results to the Task 4 tab in **Data
     Explorer**

   It takes about 3–4 minutes while the judge works through the 8 runs, even if
   nothing seems to be happening. When OpenCode prints
   `policy evaluators scored — label breakdown printed above`, it's done.

[Open this task's prompt](prompts/prompt_task4.md)

3. Click **View Task 4 dataframe** below. For each run the judge labeled
   `non_compliant`, decide whether you agree. Unlike the judge in Module 3, this
   one hasn't been tested against a reviewer, so treat its labels as claims to
   check.

   To read the agent's answer, click **Data Explorer** and open the Task 1 tab. To
   see what the agent passed to a tool, open the run in Phoenix and click the
   tool's row.

   ### Troubleshooting

If the results look wrong, try these:

- If the judge's labels look wrong across the board, check the rubric file. The
  script only reads the text between the two `` ``` `` lines, so the file has to
  have exactly one pair. Ask OpenCode to check it.
- If the counts don't match the console, or `policy_compliance` shows a dict,
  check the table. The number of `fail` rows in `identity_before_refund` should
  match the console's count, and `policy_compliance` should show `compliant` or
  `non_compliant`, not a `{'name': ..., 'score': ...}` dict. If not, ask OpenCode
  to read the score with `c["score"]` and the judge's label with `c["label"]`,
  and run the script again.





### Task 5: Compare the results side by side

**Goal:** Have OpenCode put all five results in one table and save them in Phoenix.

Then you'll look for runs where the evaluators disagree. A single combined score
would hide where a run went wrong. Reading across a row
shows you. For example:

| Column | This run |
|---|---|
| Question | I'm CUST-001 and I want to return the shoes I bought last week, order 4521. |
| `tools_called` | `get_customer`, `order_lookup`, `check_return_policy` |
| `tool_selection` | 0.0 |
| `outcome` | 0.0 |
| `identity_before_refund` | 1.0 |
| `policy_compliance` | `compliant` |

In the table, 1.0 is a pass and 0.0 is a fail.

This customer should have gotten a refund, but the agent never called
`process_refund`, so `tool_selection` and `outcome` fail. `identity_before_refund`
passes because there was no refund to check. The judge says `compliant` because it found
no broken rule. So the agent didn't break the policy, but it also didn't give the
customer the refund. You only see that by reading across the row.

The prompt also looks for the opposite case, which it calls a **dangerous trace**:
`outcome` passed, but the judge said `non_compliant`. That's the right result,
reached the wrong way. Your run may not have any.

1. Send this prompt to OpenCode, which will:
   - combine the five results into one table, and save it to the Task 5 tab in
     **Data Explorer**
   - save all five results on each run's trace in Phoenix
   - list any dangerous traces

   When OpenCode prints
   `Layering complete — D dangerous trace(s) of N runs, printed above`, it's
   done. If OpenCode shows only part of its reply, click it in the terminal to
   expand it.

[Open this task's prompt](prompts/prompt_task5.md)

2. Click **View Task 5 dataframe** below and read across each row. If there's a
   dangerous trace, use the other columns to find which rule broke.

   If you don't have any dangerous traces, that's fine. Don't run Task 1 again to try
to get one, because that could add more refunds.

**See the results in Phoenix**

Each run now has all five results saved on its trace, as annotations.

1. Click **Check Phoenix** and open the `dlai-ecommerce-agent` project.
2. Replace the text in the filter box above the list with this line, and press
   `Enter`:

   ```
   annotations['outcome'].label == 'pass' and annotations['policy_compliance'].label == 'non_compliant'
   ```

3. The list shows your dangerous traces. Click one. Near the top of its **Info**
   tab, the **Annotations** section lists all five results. Click
   `policy_compliance` to read the judge's reason, and compare it with the tool
   calls under the top row.

### Troubleshooting

If the Phoenix list is empty or something is missing, try these:

- If the list is empty, that's expected if Task 5 found no dangerous traces.
  Otherwise, set the time range to **Last 30 days** or **Last month**.
- If Task 5 found no dangerous traces, that can be a real result, but check the
  Task 5 table first. The score columns should show numbers (`1.0` or `0.0`),
  and `policy_compliance` should show `compliant` or `non_compliant`. If they
  show `{'name': ..., 'score': ...}` dicts, the script can never find a dangerous
  trace. Ask OpenCode to read the score with `c["score"]` and the label with
  `c["label"]`, then send this task's prompt again. Don't run Task 1 again.
- If an annotation is missing, wait 20 seconds, then click **Refresh** at the top
  right of the Phoenix panel. **Refresh** goes back to Phoenix's home page, so
  open the project and enter the filter again.
- If OpenCode says a results file is missing, an earlier task didn't finish.
  Send that task's prompt again, then this one. Don't run Task 1 again.



**Finish with a few notes.** Answer these for yourself:

1. Which failures could you have caught from the final answer alone, and which
   only from what the agent did?
2. Which failure would you fix first before shipping, and why?
3. Which evaluator would you rerun on every new version of the agent, and what
   would a single combined score have missed?

In Module 2, you met five kinds of failure: judgment, groundedness, execution,
completion, and propagation. Checking answers alone catches many judgment and
groundedness failures. The others need evidence of what the agent did. A skipped
or out-of-order step is an execution failure, a refund that never happened is a
completion failure, and a wrong order number carried into the next step is a
propagation failure.

In Module 5, you'll take one failure, change the agent to fix it, and check whether
the change worked without breaking something else.



### Working in the terminal (optional)

You don't need this section to complete the lab. It shows the terminal
commands and code behind each task, for when you want to see what OpenCode
does or fix a problem yourself. OpenCode writes its own scripts, so the
code it produces will differ in the details.

**Switching between OpenCode and the terminal**

- To close OpenCode and work directly in the terminal, type `/exit` in
  OpenCode, or press `Ctrl+C` twice. You'll see a plain command prompt.
- To reopen OpenCode, type `opencode` and press `Enter`.

**Before you begin: Phoenix and the agent**

On the platform, both start automatically. If you need to check or restart
them:

- Read the last lines of Phoenix's log: `tail -n 50 phoenix.log`
- Check whether Phoenix is running: `pgrep -af 'phoenix serve'`
- Restart Phoenix with its data:
  `PHOENIX_DATA_DIR=./phoenix-data bash phoenix-start.sh`
- Read the agent's log: `tail -n 50 app.log`
- Restart the agent: `bash run.sh`

Don't delete the `phoenix-data` folder or `northwind.db`. They hold your
traces and the store database, including every refund the agent has made.

**See the refunds table**

`db.py` opens the store database. To list every refund in it:

```bash
python3 -c "import db; print([dict(r) for r in db.get_connection().execute('SELECT * FROM refunds')])"
```

**Task 1: Run the test set and build trajectories**

The script OpenCode writes, `run_batch.py`, runs every question in
`TOOL_QUERIES` through `ask_agent`, then does roughly this:

```python
spans = Client().spans.get_spans_dataframe(project_identifier="dlai-ecommerce-agent")
batch = spans[spans["start_time"] >= BATCH_START]  # only spans from this batch
runs = batch[batch["parent_id"].isna()]  # one per question: ClaudeAgentSDK.query
tools = batch[batch[KIND_COL].str.upper() == "TOOL"]  # the tool calls
# one run's trajectory: its tool calls, in the order they started
calls = tools[tools["parent_id"] == run_span_id].sort_values("start_time")
```

`KIND_COL` is `span_kind` or `attributes.openinference.span.kind`, depending
on the Phoenix version.

**Task 2: Evaluate the tool calls**

```python
@create_evaluator(name="tool_selection", kind="code")
def tool_selection(input: str, tools_called: list) -> float:
    spec = QUERY_SPEC.get(input)
    if spec is None:
        return 1.0
    return 1.0 if spec["expected_tools"].issubset(set(tools_called)) else 0.0
```

`tool_invocation` works the same way, comparing each expected argument in
`spec["expected_args"]` with what the trajectory shows. Both return 1.0 for
a question that isn't in the test set.

**Task 3: Evaluate the outcome**

```python
expected = QUERY_SPEC[input]["expected_refund"]  # None, or an order and amount
refund_rows = get_connection().execute("SELECT * FROM refunds")
refunded_here = [c for c in trajectory if c["tool"] == "process_refund"]
if expected is None:  # no refund should happen
    return 0.0 if refunded_here else 1.0
if not refunded_here:
    return 0.0
return 1.0 if any(
    r["order_id"] == expected["order_id"] and abs(r["amount"] - expected["amount"]) < 0.01
    for r in refund_rows
) else 0.0
```

**Task 4: Evaluate policy compliance**

```python
if "process_refund" not in tools_called:
    return 1.0  # no refund attempted
if "get_customer" not in tools_called:
    return 0.0
return 1.0 if tools_called.index("get_customer") < tools_called.index("process_refund") else 0.0
```

That's the core of `identity_before_refund`. The judge is set up like
Module 3's custom judge:

```python
judge_llm = LLM(provider="anthropic", model="claude-sonnet-5-5")
policy_compliance = ClassificationEvaluator(
    name="policy_compliance",
    llm=judge_llm,
    prompt_template=rubric,  # the text between the ``` lines
    choices={"compliant": 1.0, "non_compliant": 0.0},
)
with suppress_tracing():
    results = evaluate_dataframe(dataframe=df, evaluators=[identity_before_refund, policy_compliance])
```

After you edit the rubric, `python3 eval_policy_compliance.py` reruns both
policy evaluators with the rubric as it is now, and
`python3 layer_results.py` updates the annotations and the Task 5 tab.

**Task 5: Compare the results side by side**

Each result is saved in Phoenix as an annotation on its run's top-level
span, linked by the span ID:

```python
Client().spans.log_span_annotations_dataframe(
    dataframe=annotations,  # columns: span_id, label, score, explanation
    annotator_kind="CODE",  # "LLM" for policy_compliance
    annotation_name="outcome",
)
```

The four code evaluators return only a score, so the script labels 1.0
`pass` and 0.0 `fail`. Saving an annotation again replaces the earlier one
with the same name.

**Progress circles**

Each task's progress circle turns green when that task's Data Explorer tab
exists. The prompts name the tabs, from `task1-trajectories` to
`task5-layered`.



---
